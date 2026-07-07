from datetime import datetime, timezone

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
