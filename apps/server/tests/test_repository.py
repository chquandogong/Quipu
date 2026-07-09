from datetime import datetime, timezone
import sqlite3

from quipu_server.contracts import DeviceIn, EventIn, MetricSampleIn, ObservationBatchIn
from quipu_server.db import connect, initialize
from quipu_server.repository import ingest_batch, list_device_snapshots


def test_ingest_batch_persists_device_metrics_and_events(conn, sample_batch) -> None:
    result = ingest_batch(conn, sample_batch, received_at=datetime(2026, 7, 7, 3, 1, tzinfo=timezone.utc))

    assert result.inserted is True
    assert result.metrics_inserted == 2
    assert result.events_inserted == 1

    snapshots = list_device_snapshots(conn)
    assert len(snapshots) == 1
    assert snapshots[0]["device"]["device_id"] == "thinkpad-p1"
    assert snapshots[0]["device"]["display_name"] == "Dev P1"
    assert snapshots[0]["device"]["cpu_model"] == "Intel Core Ultra 5 125H"
    assert snapshots[0]["latest_metrics"]["cpu.package_temp_c"]["value"] == 63.2
    assert snapshots[0]["recent_events"][0]["category"] == "thermal"


def test_ingest_batch_preserves_existing_alias_when_next_batch_omits_it(conn, sample_batch) -> None:
    first_received_at = datetime(2026, 7, 7, 3, 1, tzinfo=timezone.utc)
    second_observed_at = datetime(2026, 7, 7, 3, 6, tzinfo=timezone.utc)

    ingest_batch(conn, sample_batch, received_at=first_received_at)
    ingest_batch(
        conn,
        ObservationBatchIn(
            batch_id="batch-002",
            observed_at=second_observed_at,
            device=DeviceIn(
                device_id="thinkpad-p1",
                display_name=None,
                hostname="dev-p1-renamed",
                model=None,
                cpu_model=None,
                os_name="Ubuntu 24.04",
                kernel_version="6.14.1",
            ),
            metrics=[
                MetricSampleIn(
                    name="cpu.load_1m",
                    value=0.42,
                    unit="load",
                    observed_at=second_observed_at,
                )
            ],
            events=[],
        ),
        received_at=second_observed_at,
    )

    snapshot = list_device_snapshots(conn)[0]

    assert snapshot["device"]["display_name"] == "Dev P1"
    assert snapshot["device"]["model"] == "ThinkPad P1"
    assert snapshot["device"]["cpu_model"] == "Intel Core Ultra 5 125H"
    assert snapshot["device"]["hostname"] == "dev-p1-renamed"
    assert snapshot["device"]["kernel_version"] == "6.14.1"


def test_initialize_adds_display_name_to_existing_device_table(tmp_path) -> None:
    db_path = tmp_path / "legacy.sqlite3"
    legacy = sqlite3.connect(db_path)
    legacy.execute(
        """
        CREATE TABLE devices (
          device_id TEXT PRIMARY KEY,
          hostname TEXT NOT NULL,
          model TEXT,
          os_name TEXT,
          kernel_version TEXT,
          first_seen_at TEXT NOT NULL,
          last_seen_at TEXT NOT NULL
        )
        """
    )
    legacy.close()

    migrated = initialize(connect(db_path))
    try:
        columns = {row["name"] for row in migrated.execute("PRAGMA table_info(devices)").fetchall()}
    finally:
        migrated.close()

    assert "display_name" in columns
    assert "cpu_model" in columns


def test_ingest_batch_is_idempotent_by_device_and_batch_id(conn, sample_batch) -> None:
    received_at = datetime(2026, 7, 7, 3, 1, tzinfo=timezone.utc)

    first = ingest_batch(conn, sample_batch, received_at=received_at)
    second = ingest_batch(conn, sample_batch, received_at=received_at)

    assert first.inserted is True
    assert second.inserted is False
    assert second.metrics_inserted == 0
    assert second.events_inserted == 0


def test_device_snapshot_keeps_actionable_warning_when_info_events_are_newer(conn) -> None:
    warning_time = datetime(2026, 7, 7, 3, 0, tzinfo=timezone.utc)
    info_time = datetime(2026, 7, 8, 3, 0, tzinfo=timezone.utc)
    batch = ObservationBatchIn(
        batch_id="batch-actionable-events",
        observed_at=info_time,
        device=DeviceIn(
            device_id="local-computer",
            display_name="Local notebook",
            hostname="local-host",
            model="Laptop",
            cpu_model="Intel Core i7",
            os_name="Ubuntu",
            kernel_version="6.17.0",
        ),
        metrics=[
            MetricSampleIn(
                name="cpu.package_temp_c",
                value=65.0,
                unit="celsius",
                observed_at=info_time,
            )
        ],
        events=[
            EventIn(
                category="thermal",
                severity="warning",
                source="kernel",
                message_summary="CPU package temperature was above threshold.",
                raw_ref="journalctl -k",
                observed_at=warning_time,
                fingerprint="thermal-warning-actionable",
            ),
            *[
                EventIn(
                    category="update",
                    severity="info",
                    source="apt",
                    message_summary=f"Upgrade package set {index}",
                    raw_ref="var/log/apt/history.log",
                    observed_at=info_time,
                    fingerprint=f"update-info-{index}",
                )
                for index in range(8)
            ],
        ],
    )

    ingest_batch(conn, batch, received_at=info_time)
    snapshot = list_device_snapshots(conn, recent_event_limit=3)[0]

    assert snapshot["recent_events"][0]["severity"] == "warning"
    assert snapshot["recent_events"][0]["fingerprint"] == "thermal-warning-actionable"
