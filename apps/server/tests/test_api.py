from pathlib import Path

from fastapi.testclient import TestClient

from quipu_server.app import create_app


def _payload() -> dict:
    return {
        "batch_id": "batch-001",
        "observed_at": "2026-07-07T03:00:00+00:00",
        "device": {
            "device_id": "thinkpad-p1",
            "display_name": "Dev P1",
            "hostname": "dev-p1",
            "model": "ThinkPad P1",
            "cpu_model": "Intel Core Ultra 5 125H",
            "os_name": "Ubuntu 24.04",
            "kernel_version": "6.14.0",
        },
        "metrics": [
            {
                "name": "cpu.package_temp_c",
                "value": 63.2,
                "unit": "celsius",
                "observed_at": "2026-07-07T03:00:00+00:00",
            }
        ],
        "events": [],
    }


def test_ingest_requires_dev_token(tmp_path: Path) -> None:
    client = TestClient(create_app(database_path=tmp_path / "test.sqlite3", dev_agent_token="secret"))

    response = client.post("/api/ingest/batches", json=_payload())

    assert response.status_code == 401


def test_ingest_then_fleet_overview(tmp_path: Path) -> None:
    client = TestClient(create_app(database_path=tmp_path / "test.sqlite3", dev_agent_token="secret"))

    ingest = client.post(
        "/api/ingest/batches",
        json=_payload(),
        headers={"X-Quipu-Agent-Token": "secret"},
    )
    overview = client.get("/api/fleet/overview")

    assert ingest.status_code == 201
    assert ingest.json()["inserted"] is True
    assert overview.status_code == 200
    assert overview.json()["summary"]["total"] == 1
    assert overview.json()["devices"][0]["device"]["display_name"] == "Dev P1"
    assert overview.json()["devices"][0]["device"]["hostname"] == "dev-p1"
    assert overview.json()["devices"][0]["device"]["cpu_model"] == "Intel Core Ultra 5 125H"
