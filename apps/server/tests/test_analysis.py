from datetime import datetime, timezone

from quipu_server.analysis import build_fleet_overview


def test_fleet_overview_marks_hot_device_warning() -> None:
    now = datetime(2026, 7, 7, 3, 5, tzinfo=timezone.utc)
    snapshots = [
        {
            "device": {
                "device_id": "hot",
                "hostname": "hotbox",
                "model": "Thin Laptop",
                "os_name": "Ubuntu",
                "kernel_version": "6.14.0",
                "first_seen_at": "2026-07-07T02:55:00+00:00",
                "last_seen_at": "2026-07-07T03:04:00+00:00",
            },
            "latest_metrics": {
                "cpu.package_temp_c": {
                    "value": 82.0,
                    "unit": "celsius",
                    "observed_at": "2026-07-07T03:04:00+00:00",
                }
            },
            "recent_events": [],
        }
    ]

    overview = build_fleet_overview(snapshots, now=now)

    assert overview["summary"]["warning"] == 1
    assert overview["devices"][0]["risk_level"] == "warning"
    assert overview["devices"][0]["findings"][0]["category"] == "thermal"


def test_fleet_overview_marks_stale_device() -> None:
    now = datetime(2026, 7, 7, 3, 30, tzinfo=timezone.utc)
    snapshots = [
        {
            "device": {
                "device_id": "stale",
                "hostname": "offline-dev",
                "model": None,
                "os_name": "Ubuntu",
                "kernel_version": "6.14.0",
                "first_seen_at": "2026-07-07T02:55:00+00:00",
                "last_seen_at": "2026-07-07T03:00:00+00:00",
            },
            "latest_metrics": {},
            "recent_events": [],
        }
    ]

    overview = build_fleet_overview(snapshots, now=now)

    assert overview["summary"]["stale"] == 1
    assert overview["devices"][0]["risk_level"] == "stale"
