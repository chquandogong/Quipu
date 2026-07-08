from __future__ import annotations

from pathlib import Path

from quipu_collector.spool import SpoolStore


def _batch(batch_id: str) -> dict:
    return {
        "batch_id": batch_id,
        "observed_at": f"2026-07-08T00:00:0{batch_id[-1]}+00:00",
        "device": {
            "device_id": "device-1",
            "hostname": "test-host",
            "model": None,
            "os_name": "Ubuntu",
            "kernel_version": "6.14.0",
        },
        "metrics": [{"name": "cpu.load_1m", "value": 0.5, "unit": "load", "observed_at": "2026-07-08T00:00:00+00:00"}],
        "events": [],
    }


def test_spool_enqueue_prunes_oldest_batches(tmp_path: Path) -> None:
    store = SpoolStore(tmp_path, max_batches=2)

    first = store.enqueue(_batch("batch-1"))
    second = store.enqueue(_batch("batch-2"))
    third = store.enqueue(_batch("batch-3"))

    assert not first.exists()
    assert second.exists()
    assert third.exists()
    assert [batch["batch_id"] for batch in store.list_batches()] == ["batch-2", "batch-3"]


def test_spool_flush_deletes_successfully_sent_batches(tmp_path: Path) -> None:
    store = SpoolStore(tmp_path, max_batches=10)
    store.enqueue(_batch("batch-1"))
    store.enqueue(_batch("batch-2"))
    sent: list[str] = []

    def fake_send(batch, *, server_url, token):
        sent.append(batch["batch_id"])
        return {"inserted": True}

    result = store.flush(send=fake_send, server_url="http://127.0.0.1:8000", token="token")

    assert result == {"attempted": 2, "sent": 2, "remaining": 0, "failed": False}
    assert sent == ["batch-1", "batch-2"]
    assert store.list_batches() == []


def test_spool_flush_stops_on_failure_and_keeps_unsent_batches(tmp_path: Path) -> None:
    store = SpoolStore(tmp_path, max_batches=10)
    store.enqueue(_batch("batch-1"))
    store.enqueue(_batch("batch-2"))

    def fake_send(batch, *, server_url, token):
        if batch["batch_id"] == "batch-1":
            raise RuntimeError("server unavailable")
        return {"inserted": True}

    result = store.flush(send=fake_send, server_url="http://127.0.0.1:8000", token="token")

    assert result == {"attempted": 1, "sent": 0, "remaining": 2, "failed": True}
    assert [batch["batch_id"] for batch in store.list_batches()] == ["batch-1", "batch-2"]
