from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from quipu_server.app import create_app
from quipu_server.contracts import InterventionIn
from quipu_server.repository import ingest_batch, list_interventions_for_item, record_intervention
from quipu_server.seed import load_fixture


def test_record_intervention_persists_human_action(conn, sample_batch) -> None:
    ingest_batch(conn, sample_batch, received_at=datetime(2026, 7, 7, 3, 1, tzinfo=timezone.utc))
    intervention = InterventionIn(
        label="Raised rear edge",
        description="Lifted one side of the laptop to improve bottom airflow.",
        expected_effect="CPU package temperature should drop during the next compile window.",
        recorded_at=datetime(2026, 7, 7, 3, 5, tzinfo=timezone.utc),
    )

    stored = record_intervention(
        conn,
        investigation_id="thinkpad-p1:thermal",
        device_id="thinkpad-p1",
        category="thermal",
        intervention=intervention,
    )
    interventions = list_interventions_for_item(conn, "thinkpad-p1:thermal")

    assert stored["id"] == interventions[0]["id"]
    assert interventions[0]["label"] == "Raised rear edge"
    assert interventions[0]["verification_status"] == "pending"
    assert interventions[0]["expected_effect"].startswith("CPU package")


def test_intervention_api_records_action_and_updates_detail(tmp_path: Path) -> None:
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

    created = client.post(
        "/api/investigations/xps-13:thermal/interventions",
        json={
            "label": "Raised rear edge",
            "description": "Lifted one side of the laptop to improve bottom airflow.",
            "expected_effect": "CPU package temperature should drop in the next observation window.",
            "recorded_at": "2026-07-07T03:05:00+00:00",
        },
    )
    detail = client.get("/api/investigations/xps-13:thermal")

    assert created.status_code == 201
    assert created.json()["investigation_id"] == "xps-13:thermal"
    assert detail.status_code == 200
    assert detail.json()["interventions"][0]["label"] == "Raised rear edge"
    assert detail.json()["verification"]["status"] == "Waiting for after window"
