from pathlib import Path

from fastapi.testclient import TestClient

from quipu_server.app import create_app


def _payload(*, device_id: str, hostname: str, category: str, severity: str, summary: str) -> dict:
    return {
        "batch_id": f"batch-{device_id}-{category}",
        "observed_at": "2026-07-07T03:00:00+00:00",
        "device": {
            "device_id": device_id,
            "hostname": hostname,
            "model": "XPS 13",
            "os_name": "Ubuntu 24.04",
            "kernel_version": "6.14.0",
        },
        "metrics": [
            {
                "name": "cpu.package_temp_c",
                "value": 82.0,
                "unit": "celsius",
                "observed_at": "2026-07-07T03:00:00+00:00",
            }
        ],
        "events": [
            {
                "category": category,
                "severity": severity,
                "source": "kernel",
                "message_summary": summary,
                "raw_ref": "journalctl",
                "observed_at": "2026-07-07T03:00:00+00:00",
                "fingerprint": f"{category}-{device_id}",
            }
        ],
    }


def _client(tmp_path: Path) -> TestClient:
    client = TestClient(create_app(database_path=tmp_path / "test.sqlite3", dev_agent_token="secret"))
    for payload in (
        _payload(
            device_id="xps-a",
            hostname="xps-a",
            category="thermal",
            severity="warning",
            summary="CPU0: Core temperature above threshold, cpu clock throttled",
        ),
        _payload(
            device_id="xps-b",
            hostname="xps-b",
            category="graphics",
            severity="warning",
            summary="i915 0000:00:02.0: GPU HANG detected",
        ),
    ):
        response = client.post("/api/ingest/batches", json=payload, headers={"X-Quipu-Agent-Token": "secret"})
        assert response.status_code == 201
    return client


def test_schema_version_endpoint_is_admin_gated(tmp_path: Path) -> None:
    client = _client(tmp_path)

    rejected = client.get("/api/admin/schema")
    accepted = client.get("/api/admin/schema", headers={"X-Quipu-Agent-Token": "secret"})

    assert rejected.status_code == 401
    assert accepted.status_code == 200
    assert accepted.json()["schema_version"] == "0.14.3"
    assert "agent_tokens" in accepted.json()["tables"]


def test_pattern_overview_groups_by_category_model_and_kernel(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/api/patterns/overview")
    body = response.json()

    assert response.status_code == 200
    assert body["category_groups"][0]["category"] in {"graphics", "thermal"}
    assert {group["category"] for group in body["category_groups"]} == {"graphics", "thermal"}
    assert body["model_groups"][0]["model"] == "XPS 13"
    assert body["model_groups"][0]["count"] == 2
    assert body["kernel_groups"][0]["kernel_version"] == "6.14.0"
    assert body["kernel_groups"][0]["count"] == 2


def test_investigation_notes_attach_team_handoff_to_queue_item(tmp_path: Path) -> None:
    client = _client(tmp_path)
    item_id = "xps-a:thermal"

    created = client.post(
        f"/api/investigations/{item_id}/notes",
        json={"author": "ops", "body": "Raised the rear edge and will compare the next two batches."},
    )
    listed = client.get(f"/api/investigations/{item_id}/notes")

    assert created.status_code == 201
    assert created.json()["investigation_id"] == item_id
    assert created.json()["author"] == "ops"
    assert listed.status_code == 200
    assert listed.json()["notes"][0]["body"].startswith("Raised the rear edge")
