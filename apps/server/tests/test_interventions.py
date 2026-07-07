from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from quipu_server.app import create_app
from quipu_server.contracts import DeviceIn, EventIn, InterventionIn, MetricSampleIn, ObservationBatchIn
from quipu_server.repository import ingest_batch, list_interventions_for_item, record_intervention
from quipu_server.seed import load_fixture


def _thermal_batch(
    *,
    batch_id: str,
    observed_at: datetime,
    package_temp: float,
    load_1m: float = 1.0,
    event: bool = False,
) -> ObservationBatchIn:
    return ObservationBatchIn(
        batch_id=batch_id,
        observed_at=observed_at,
        device=DeviceIn(
            device_id="thinkpad-p1",
            hostname="dev-p1",
            model="ThinkPad P1",
            os_name="Ubuntu 24.04",
            kernel_version="6.14.0",
        ),
        metrics=[
            MetricSampleIn(
                name="cpu.package_temp_c",
                value=package_temp,
                unit="celsius",
                observed_at=observed_at,
            ),
            MetricSampleIn(
                name="cpu.load_1m",
                value=load_1m,
                unit="load",
                observed_at=observed_at,
            ),
        ],
        events=[
            EventIn(
                category="thermal",
                severity="warning",
                source="kernel",
                message_summary="CPU thermal threshold event reported during compile workload.",
                raw_ref="journalctl:-k:thermal",
                observed_at=observed_at,
                fingerprint=f"thermal-{batch_id}",
            )
        ]
        if event
        else [],
    )


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


def test_list_observations_for_intervention_splits_before_and_after_windows(conn) -> None:
    from quipu_server import repository

    ingest_batch(
        conn,
        _thermal_batch(
            batch_id="before-001",
            observed_at=datetime(2026, 7, 7, 3, 0, tzinfo=timezone.utc),
            package_temp=86.4,
            load_1m=1.2,
            event=True,
        ),
        received_at=datetime(2026, 7, 7, 3, 1, tzinfo=timezone.utc),
    )
    ingest_batch(
        conn,
        _thermal_batch(
            batch_id="after-001",
            observed_at=datetime(2026, 7, 7, 3, 20, tzinfo=timezone.utc),
            package_temp=69.0,
            load_1m=1.4,
        ),
        received_at=datetime(2026, 7, 7, 3, 21, tzinfo=timezone.utc),
    )
    intervention = record_intervention(
        conn,
        investigation_id="thinkpad-p1:thermal",
        device_id="thinkpad-p1",
        category="thermal",
        intervention=InterventionIn(
            label="Raised rear edge",
            description="Lifted one side of the laptop to improve bottom airflow.",
            recorded_at=datetime(2026, 7, 7, 3, 5, tzinfo=timezone.utc),
        ),
    )

    window = repository.list_observations_for_intervention(conn, intervention, window_minutes=30)

    assert window["window_minutes"] == 30
    assert [sample["value"] for sample in window["metrics"]["before"] if sample["name"] == "cpu.package_temp_c"] == [86.4]
    assert [sample["value"] for sample in window["metrics"]["after"] if sample["name"] == "cpu.package_temp_c"] == [69.0]
    assert len(window["events"]["before"]) == 1
    assert window["events"]["after"] == []


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
    assert detail.json()["verification"]["status"] == "Needs after data"
    assert detail.json()["interventions"][0]["verification_result"]["status"] == "insufficient_data"


def test_intervention_api_detail_includes_before_after_verification(tmp_path: Path) -> None:
    app = create_app(database_path=tmp_path / "test.sqlite3", dev_agent_token="secret")
    client = TestClient(app)

    for batch in [
        _thermal_batch(
            batch_id="before-001",
            observed_at=datetime(2026, 7, 7, 3, 0, tzinfo=timezone.utc),
            package_temp=86.4,
            load_1m=1.2,
            event=True,
        ),
        _thermal_batch(
            batch_id="after-001",
            observed_at=datetime(2026, 7, 7, 3, 20, tzinfo=timezone.utc),
            package_temp=69.0,
            load_1m=1.4,
        ),
    ]:
        response = client.post(
            "/api/ingest/batches",
            json=batch.model_dump(mode="json"),
            headers={"X-Quipu-Agent-Token": "secret"},
        )
        assert response.status_code == 201

    created = client.post(
        "/api/investigations/thinkpad-p1:thermal/interventions",
        json={
            "label": "Raised rear edge",
            "description": "Lifted one side of the laptop to improve bottom airflow.",
            "expected_effect": "CPU package temperature should drop in the next observation window.",
            "recorded_at": "2026-07-07T03:05:00+00:00",
        },
    )
    detail = client.get("/api/investigations/thinkpad-p1:thermal")

    assert created.status_code == 201
    assert detail.status_code == 200
    result = detail.json()["interventions"][0]["verification_result"]
    assert result["status"] == "helped"
    assert result["checks"][0]["name"] == "CPU package temperature"
    assert result["checks"][0]["delta"] == "-17.4C"
