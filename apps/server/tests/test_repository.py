from datetime import datetime, timezone

from quipu_server.contracts import DeviceIn, EventIn, MetricSampleIn, ObservationBatchIn
from quipu_server.repository import ingest_batch, list_device_snapshots


def test_ingest_batch_persists_device_metrics_and_events(conn, sample_batch) -> None:
    result = ingest_batch(conn, sample_batch, received_at=datetime(2026, 7, 7, 3, 1, tzinfo=timezone.utc))

    assert result.inserted is True
    assert result.metrics_inserted == 2
    assert result.events_inserted == 1

    snapshots = list_device_snapshots(conn)
    assert len(snapshots) == 1
    assert snapshots[0]["device"]["device_id"] == "thinkpad-p1"
    assert snapshots[0]["latest_metrics"]["cpu.package_temp_c"]["value"] == 63.2
    assert snapshots[0]["recent_events"][0]["category"] == "thermal"


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
            hostname="local-host",
            model="Laptop",
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
