from pathlib import Path

from fastapi.testclient import TestClient

from quipu_server.app import create_app


def _payload(device_id: str = "thinkpad-p1") -> dict:
    return {
        "batch_id": f"batch-{device_id}",
        "observed_at": "2026-07-07T03:00:00+00:00",
        "device": {
            "device_id": device_id,
            "hostname": device_id,
            "model": "ThinkPad P1",
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


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(database_path=tmp_path / "test.sqlite3", dev_agent_token="secret"))


def test_enrolled_device_token_can_ingest_only_bound_device(tmp_path: Path) -> None:
    client = _client(tmp_path)

    created = client.post(
        "/api/enrollment/tokens",
        json={"device_id": "thinkpad-p1", "label": "P1 collector"},
        headers={"X-Quipu-Agent-Token": "secret"},
    )
    token = created.json()["token"]
    accepted = client.post(
        "/api/ingest/batches",
        json=_payload("thinkpad-p1"),
        headers={"X-Quipu-Agent-Token": token},
    )
    rejected = client.post(
        "/api/ingest/batches",
        json=_payload("other-device"),
        headers={"X-Quipu-Agent-Token": token},
    )
    listed = client.get("/api/enrollment/tokens", headers={"X-Quipu-Agent-Token": "secret"})

    assert created.status_code == 201
    assert token.startswith("quipu_agent_")
    assert accepted.status_code == 201
    assert rejected.status_code == 401
    assert listed.status_code == 200
    assert listed.json()["tokens"][0]["device_id"] == "thinkpad-p1"
    assert "token" not in listed.json()["tokens"][0]


def test_token_rotation_invalidates_old_token_and_revoke_blocks_new_token(tmp_path: Path) -> None:
    client = _client(tmp_path)
    created = client.post(
        "/api/enrollment/tokens",
        json={"device_id": "thinkpad-p1", "label": "P1 collector"},
        headers={"X-Quipu-Agent-Token": "secret"},
    ).json()
    old_token = created["token"]

    rotated = client.post(
        f"/api/enrollment/tokens/{created['id']}/rotate",
        headers={"X-Quipu-Agent-Token": "secret"},
    )
    new_token = rotated.json()["token"]
    old_rejected = client.post(
        "/api/ingest/batches",
        json=_payload("thinkpad-p1"),
        headers={"X-Quipu-Agent-Token": old_token},
    )
    new_accepted = client.post(
        "/api/ingest/batches",
        json={**_payload("thinkpad-p1"), "batch_id": "batch-new-token"},
        headers={"X-Quipu-Agent-Token": new_token},
    )
    revoked = client.post(
        f"/api/enrollment/tokens/{created['id']}/revoke",
        headers={"X-Quipu-Agent-Token": "secret"},
    )
    revoked_rejected = client.post(
        "/api/ingest/batches",
        json={**_payload("thinkpad-p1"), "batch_id": "batch-revoked-token"},
        headers={"X-Quipu-Agent-Token": new_token},
    )

    assert rotated.status_code == 200
    assert new_token.startswith("quipu_agent_")
    assert new_token != old_token
    assert old_rejected.status_code == 401
    assert new_accepted.status_code == 201
    assert revoked.status_code == 200
    assert revoked.json()["active"] is False
    assert revoked_rejected.status_code == 401
