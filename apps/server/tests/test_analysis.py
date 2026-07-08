from datetime import datetime, timezone

from quipu_server.analysis import build_fleet_overview, build_investigation_queue


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


def test_thermal_throttling_event_gets_specific_finding() -> None:
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
                    "value": 72.0,
                    "unit": "celsius",
                    "observed_at": "2026-07-07T03:04:00+00:00",
                }
            },
            "recent_events": [
                {
                    "category": "thermal",
                    "severity": "warning",
                    "source": "kernel",
                    "message_summary": "CPU0: Core temperature above threshold, cpu clock throttled",
                    "raw_ref": "journalctl -k --since -60min",
                    "observed_at": "2026-07-07T03:03:00+00:00",
                    "fingerprint": "thermal-kernel-test",
                }
            ],
        }
    ]

    overview = build_fleet_overview(snapshots, now=now)
    queue = build_investigation_queue(snapshots, now=now)

    assert overview["summary"]["warning"] == 1
    assert overview["devices"][0]["findings"][0]["title"] == "Thermal throttling reported"
    assert overview["devices"][0]["findings"][0]["confidence"] == "high"
    assert queue[0]["id"] == "hot:thermal"
    assert queue[0]["why_now"] == "Thermal throttling reported"


def test_network_reconnect_event_gets_specific_finding() -> None:
    now = datetime(2026, 7, 7, 3, 5, tzinfo=timezone.utc)
    snapshots = [
        {
            "device": {
                "device_id": "wifi",
                "hostname": "wifi-dev",
                "model": "Laptop",
                "os_name": "Ubuntu",
                "kernel_version": "6.14.0",
                "first_seen_at": "2026-07-07T02:55:00+00:00",
                "last_seen_at": "2026-07-07T03:04:00+00:00",
            },
            "latest_metrics": {
                "wifi.signal_dbm": {
                    "value": -58.0,
                    "unit": "dbm",
                    "observed_at": "2026-07-07T03:04:00+00:00",
                }
            },
            "recent_events": [
                {
                    "category": "network",
                    "severity": "warning",
                    "source": "NetworkManager",
                    "message_summary": "wlp0s20f3: state change: activated -> disconnected",
                    "raw_ref": "journalctl -u NetworkManager --since -60min",
                    "observed_at": "2026-07-07T03:03:00+00:00",
                    "fingerprint": "network-networkmanager-test",
                }
            ],
        }
    ]

    overview = build_fleet_overview(snapshots, now=now)
    queue = build_investigation_queue(snapshots, now=now)

    assert overview["summary"]["warning"] == 1
    assert overview["devices"][0]["findings"][0]["title"] == "Network reconnect reported"
    assert overview["devices"][0]["findings"][0]["category"] == "network"
    assert queue[0]["id"] == "wifi:network"
    assert queue[0]["next_step"] == "Review reconnects, signal changes, and driver messages."
