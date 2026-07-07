from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import sqlite3
from typing import Any

from quipu_server.contracts import EventIn, InterventionIn, ObservationBatchIn


@dataclass(frozen=True)
class IngestResult:
    inserted: bool
    metrics_inserted: int
    events_inserted: int


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _event_fingerprint(event: EventIn) -> str:
    if event.fingerprint:
        return event.fingerprint
    raw = "|".join(
        [
            event.category,
            event.severity,
            event.source,
            event.message_summary,
            _iso(event.observed_at),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def ingest_batch(
    conn: sqlite3.Connection,
    batch: ObservationBatchIn,
    *,
    received_at: datetime | None = None,
) -> IngestResult:
    received_at = received_at or datetime.now(timezone.utc)
    received_iso = _iso(received_at)
    observed_iso = _iso(batch.observed_at)

    with conn:
        conn.execute(
            """
            INSERT INTO devices (
              device_id, hostname, model, os_name, kernel_version, first_seen_at, last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(device_id) DO UPDATE SET
              hostname = excluded.hostname,
              model = excluded.model,
              os_name = excluded.os_name,
              kernel_version = excluded.kernel_version,
              last_seen_at = excluded.last_seen_at
            """,
            (
                batch.device.device_id,
                batch.device.hostname,
                batch.device.model,
                batch.device.os_name,
                batch.device.kernel_version,
                received_iso,
                received_iso,
            ),
        )

        batch_cursor = conn.execute(
            """
            INSERT OR IGNORE INTO batches (device_id, batch_id, observed_at, received_at)
            VALUES (?, ?, ?, ?)
            """,
            (batch.device.device_id, batch.batch_id, observed_iso, received_iso),
        )
        if batch_cursor.rowcount == 0:
            return IngestResult(inserted=False, metrics_inserted=0, events_inserted=0)

        metrics_inserted = 0
        for metric in batch.metrics:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO metric_samples (
                  device_id, batch_id, name, value, unit, observed_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    batch.device.device_id,
                    batch.batch_id,
                    metric.name,
                    metric.value,
                    metric.unit,
                    _iso(metric.observed_at),
                ),
            )
            metrics_inserted += cursor.rowcount

        events_inserted = 0
        for event in batch.events:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO events (
                  device_id, batch_id, category, severity, source, message_summary,
                  raw_ref, observed_at, fingerprint
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch.device.device_id,
                    batch.batch_id,
                    event.category,
                    event.severity,
                    event.source,
                    event.message_summary,
                    event.raw_ref,
                    _iso(event.observed_at),
                    _event_fingerprint(event),
                ),
            )
            events_inserted += cursor.rowcount

    return IngestResult(
        inserted=True,
        metrics_inserted=metrics_inserted,
        events_inserted=events_inserted,
    )


def list_device_snapshots(conn: sqlite3.Connection, *, recent_event_limit: int = 8) -> list[dict[str, Any]]:
    devices = conn.execute(
        """
        SELECT device_id, hostname, model, os_name, kernel_version, first_seen_at, last_seen_at
        FROM devices
        ORDER BY hostname ASC
        """
    ).fetchall()

    snapshots: list[dict[str, Any]] = []
    for device in devices:
        device_id = device["device_id"]
        metric_rows = conn.execute(
            """
            SELECT ms.name, ms.value, ms.unit, ms.observed_at
            FROM metric_samples ms
            INNER JOIN (
              SELECT name, MAX(observed_at) AS observed_at
              FROM metric_samples
              WHERE device_id = ?
              GROUP BY name
            ) latest
              ON latest.name = ms.name AND latest.observed_at = ms.observed_at
            WHERE ms.device_id = ?
            ORDER BY ms.name ASC
            """,
            (device_id, device_id),
        ).fetchall()
        event_rows = conn.execute(
            """
            SELECT category, severity, source, message_summary, raw_ref, observed_at, fingerprint
            FROM events
            WHERE device_id = ?
            ORDER BY observed_at DESC
            LIMIT ?
            """,
            (device_id, recent_event_limit),
        ).fetchall()
        snapshots.append(
            {
                "device": dict(device),
                "latest_metrics": {
                    row["name"]: {
                        "value": row["value"],
                        "unit": row["unit"],
                        "observed_at": row["observed_at"],
                    }
                    for row in metric_rows
                },
                "recent_events": [dict(row) for row in event_rows],
            }
        )
    return snapshots


def _intervention_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "investigation_id": row["investigation_id"],
        "device_id": row["device_id"],
        "category": row["category"],
        "label": row["label"],
        "description": row["description"],
        "expected_effect": row["expected_effect"],
        "recorded_at": row["recorded_at"],
        "verification_status": row["verification_status"],
    }


def record_intervention(
    conn: sqlite3.Connection,
    *,
    investigation_id: str,
    device_id: str,
    category: str,
    intervention: InterventionIn,
) -> dict[str, Any]:
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO interventions (
              investigation_id, device_id, category, label, description,
              expected_effect, recorded_at, verification_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                investigation_id,
                device_id,
                category,
                intervention.label,
                intervention.description,
                intervention.expected_effect,
                _iso(intervention.recorded_at),
            ),
        )
        row = conn.execute(
            """
            SELECT id, investigation_id, device_id, category, label, description,
                   expected_effect, recorded_at, verification_status
            FROM interventions
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return _intervention_row_to_dict(row)


def list_interventions_for_item(conn: sqlite3.Connection, investigation_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, investigation_id, device_id, category, label, description,
               expected_effect, recorded_at, verification_status
        FROM interventions
        WHERE investigation_id = ?
        ORDER BY recorded_at ASC, id ASC
        """,
        (investigation_id,),
    ).fetchall()
    return [_intervention_row_to_dict(row) for row in rows]


def list_observations_for_intervention(
    conn: sqlite3.Connection,
    intervention: dict[str, Any],
    *,
    window_minutes: int = 30,
) -> dict[str, Any]:
    recorded_at = _parse_time(intervention["recorded_at"])
    before_start = recorded_at - timedelta(minutes=window_minutes)
    after_end = recorded_at + timedelta(minutes=window_minutes)
    device_id = intervention["device_id"]
    category = intervention["category"]

    def metric_rows(start: datetime, end: datetime, *, include_start: bool, include_end: bool) -> list[dict[str, Any]]:
        start_op = ">=" if include_start else ">"
        end_op = "<=" if include_end else "<"
        rows = conn.execute(
            f"""
            SELECT name, value, unit, observed_at
            FROM metric_samples
            WHERE device_id = ?
              AND observed_at {start_op} ?
              AND observed_at {end_op} ?
            ORDER BY observed_at ASC, name ASC
            """,
            (device_id, _iso(start), _iso(end)),
        ).fetchall()
        return [dict(row) for row in rows]

    def event_rows(start: datetime, end: datetime, *, include_start: bool, include_end: bool) -> list[dict[str, Any]]:
        start_op = ">=" if include_start else ">"
        end_op = "<=" if include_end else "<"
        rows = conn.execute(
            f"""
            SELECT category, severity, source, message_summary, raw_ref, observed_at, fingerprint
            FROM events
            WHERE device_id = ?
              AND category = ?
              AND severity IN ('warning', 'critical')
              AND observed_at {start_op} ?
              AND observed_at {end_op} ?
            ORDER BY observed_at ASC, fingerprint ASC
            """,
            (device_id, category, _iso(start), _iso(end)),
        ).fetchall()
        return [dict(row) for row in rows]

    return {
        "window_minutes": window_minutes,
        "metrics": {
            "before": metric_rows(before_start, recorded_at, include_start=True, include_end=False),
            "after": metric_rows(recorded_at, after_end, include_start=True, include_end=True),
        },
        "events": {
            "before": event_rows(before_start, recorded_at, include_start=True, include_end=False),
            "after": event_rows(recorded_at, after_end, include_start=True, include_end=True),
        },
    }
