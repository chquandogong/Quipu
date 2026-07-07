from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from quipu_server.analysis import build_investigation_detail, build_investigation_queue
from quipu_server.app import create_app
from quipu_server.repository import ingest_batch, list_device_snapshots
from quipu_server.seed import load_fixture


def test_build_investigation_queue_prioritizes_findings(conn, sample_batch) -> None:
    ingest_batch(conn, sample_batch, received_at=datetime(2026, 7, 7, 3, 1, tzinfo=timezone.utc))
    snapshots = list_device_snapshots(conn)

    queue = build_investigation_queue(snapshots, now=datetime(2026, 7, 7, 3, 2, tzinfo=timezone.utc))

    assert len(queue) == 1
    assert queue[0]["id"] == "thinkpad-p1:thermal"
    assert queue[0]["priority"] == "Medium"
    assert queue[0]["stage"] == "Triage"
    assert queue[0]["device_hostname"] == "dev-p1"
    assert queue[0]["why_now"] == "Warning event reported"
    assert queue[0]["next_step"] == "Inspect thermal evidence and compare cooling or workload windows."


def test_build_investigation_detail_contains_workflow_sections(conn, sample_batch) -> None:
    ingest_batch(conn, sample_batch, received_at=datetime(2026, 7, 7, 3, 1, tzinfo=timezone.utc))
    snapshots = list_device_snapshots(conn)

    detail = build_investigation_detail(
        snapshots,
        "thinkpad-p1:thermal",
        now=datetime(2026, 7, 7, 3, 2, tzinfo=timezone.utc),
    )

    assert detail is not None
    assert detail["item"]["id"] == "thinkpad-p1:thermal"
    assert detail["timeline"][0]["category"] == "thermal"
    assert detail["hypotheses"][0]["category"] == "thermal"
    assert detail["actions"][0]["label"] == "Check cooling and workload"
    assert detail["verification"]["status"] == "Needs before/after data"
    assert "dev-p1" in detail["report"]["summary"]


def test_investigation_api_returns_queue_and_detail(tmp_path: Path) -> None:
    app = create_app(database_path=tmp_path / "test.sqlite3", dev_agent_token="secret")
    client = TestClient(app)
    fixture_path = Path(__file__).parents[3] / "fixtures" / "ingest" / "team-sample.json"

    for batch in load_fixture(fixture_path):
        response = client.post(
            "/api/ingest/batches",
            json=batch.model_dump(mode="json"),
            headers={"X-Quipu-Agent-Token": "secret"},
        )
        assert response.status_code == 201

    queue = client.get("/api/investigations/queue")

    assert queue.status_code == 200
    assert queue.json()["items"][0]["id"] == "xps-13:thermal"

    detail = client.get("/api/investigations/xps-13:thermal")

    assert detail.status_code == 200
    assert detail.json()["item"]["device_hostname"] == "build-xps"
    assert detail.json()["hypotheses"][0]["category"] == "thermal"


def test_investigation_api_returns_404_for_unknown_item(tmp_path: Path) -> None:
    app = create_app(database_path=tmp_path / "test.sqlite3", dev_agent_token="secret")
    client = TestClient(app)

    response = client.get("/api/investigations/missing:thermal")

    assert response.status_code == 404
