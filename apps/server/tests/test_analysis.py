from datetime import datetime, timezone

from quipu_server.analysis import build_fleet_overview, build_investigation_queue, build_pattern_overview


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


def test_storage_health_event_gets_specific_finding() -> None:
    now = datetime(2026, 7, 7, 3, 5, tzinfo=timezone.utc)
    snapshots = [
        {
            "device": {
                "device_id": "disk",
                "hostname": "disk-dev",
                "model": "Laptop",
                "os_name": "Ubuntu",
                "kernel_version": "6.14.0",
                "first_seen_at": "2026-07-07T02:55:00+00:00",
                "last_seen_at": "2026-07-07T03:04:00+00:00",
            },
            "latest_metrics": {
                "disk.root_used_percent": {
                    "value": 78.2,
                    "unit": "percent",
                    "observed_at": "2026-07-07T03:04:00+00:00",
                }
            },
            "recent_events": [
                {
                    "category": "storage",
                    "severity": "warning",
                    "source": "kernel",
                    "message_summary": "nvme0n1: I/O timeout, reset controller",
                    "raw_ref": "journalctl -k --since -60min",
                    "observed_at": "2026-07-07T03:03:00+00:00",
                    "fingerprint": "storage-kernel-test",
                }
            ],
        }
    ]

    overview = build_fleet_overview(snapshots, now=now)
    queue = build_investigation_queue(snapshots, now=now)

    assert overview["summary"]["warning"] == 1
    assert overview["devices"][0]["findings"][0]["title"] == "Storage health event reported"
    assert overview["devices"][0]["findings"][0]["category"] == "storage"
    assert queue[0]["id"] == "disk:storage"
    assert queue[0]["next_step"] == "Check storage warnings, NVMe health, and I/O stall evidence."


def test_battery_power_event_gets_specific_finding() -> None:
    now = datetime(2026, 7, 7, 3, 5, tzinfo=timezone.utc)
    snapshots = [
        {
            "device": {
                "device_id": "battery",
                "hostname": "battery-dev",
                "model": "Laptop",
                "os_name": "Ubuntu",
                "kernel_version": "6.14.0",
                "first_seen_at": "2026-07-07T02:55:00+00:00",
                "last_seen_at": "2026-07-07T03:04:00+00:00",
            },
            "latest_metrics": {
                "battery.capacity_percent": {
                    "value": 37.0,
                    "unit": "percent",
                    "observed_at": "2026-07-07T03:04:00+00:00",
                },
                "battery.ac_online": {
                    "value": 0.0,
                    "unit": "boolean",
                    "observed_at": "2026-07-07T03:04:00+00:00",
                },
            },
            "recent_events": [
                {
                    "category": "power",
                    "severity": "warning",
                    "source": "kernel",
                    "message_summary": "ACPI: battery discharge rate high while AC offline",
                    "raw_ref": "journalctl -k --since -60min",
                    "observed_at": "2026-07-07T03:03:00+00:00",
                    "fingerprint": "power-kernel-test",
                }
            ],
        }
    ]

    overview = build_fleet_overview(snapshots, now=now)
    queue = build_investigation_queue(snapshots, now=now)

    assert overview["summary"]["warning"] == 1
    assert overview["devices"][0]["findings"][0]["title"] == "Battery power issue reported"
    assert overview["devices"][0]["findings"][0]["category"] == "power"
    assert queue[0]["id"] == "battery:power"
    assert queue[0]["next_step"] == "Check battery state, AC connection, and power-management events."


def test_nvme_critical_warning_gets_storage_finding() -> None:
    now = datetime(2026, 7, 7, 3, 5, tzinfo=timezone.utc)
    snapshots = [
        {
            "device": {
                "device_id": "nvme",
                "hostname": "nvme-dev",
                "model": "Laptop",
                "os_name": "Ubuntu",
                "kernel_version": "6.14.0",
                "first_seen_at": "2026-07-07T02:55:00+00:00",
                "last_seen_at": "2026-07-07T03:04:00+00:00",
            },
            "latest_metrics": {
                "nvme.critical_warning": {
                    "value": 1.0,
                    "unit": "boolean",
                    "observed_at": "2026-07-07T03:04:00+00:00",
                },
                "nvme.available_spare_percent": {
                    "value": 9.0,
                    "unit": "percent",
                    "observed_at": "2026-07-07T03:04:00+00:00",
                },
                "nvme.media_errors": {
                    "value": 2.0,
                    "unit": "count",
                    "observed_at": "2026-07-07T03:04:00+00:00",
                },
            },
            "recent_events": [],
        }
    ]

    overview = build_fleet_overview(snapshots, now=now)
    queue = build_investigation_queue(snapshots, now=now)

    assert overview["summary"]["critical"] == 1
    assert overview["devices"][0]["findings"][0]["title"] == "NVMe critical warning reported"
    assert overview["devices"][0]["findings"][0]["category"] == "storage"
    assert queue[0]["id"] == "nvme:storage"
    assert queue[0]["priority"] == "High"


def test_low_nvme_available_spare_gets_storage_warning() -> None:
    now = datetime(2026, 7, 7, 3, 5, tzinfo=timezone.utc)
    snapshots = [
        {
            "device": {
                "device_id": "spare",
                "hostname": "spare-dev",
                "model": "Laptop",
                "os_name": "Ubuntu",
                "kernel_version": "6.14.0",
                "first_seen_at": "2026-07-07T02:55:00+00:00",
                "last_seen_at": "2026-07-07T03:04:00+00:00",
            },
            "latest_metrics": {
                "nvme.available_spare_percent": {
                    "value": 15.0,
                    "unit": "percent",
                    "observed_at": "2026-07-07T03:04:00+00:00",
                }
            },
            "recent_events": [],
        }
    ]

    overview = build_fleet_overview(snapshots, now=now)
    queue = build_investigation_queue(snapshots, now=now)

    assert overview["summary"]["warning"] == 1
    assert overview["devices"][0]["findings"][0]["title"] == "NVMe available spare is low"
    assert overview["devices"][0]["findings"][0]["evidence"] == "Latest NVMe available spare is 15.0%."
    assert queue[0]["id"] == "spare:storage"


def test_hot_cpu_with_idle_fan_prioritizes_cooling_response() -> None:
    now = datetime(2026, 7, 7, 3, 5, tzinfo=timezone.utc)
    snapshots = [
        {
            "device": {
                "device_id": "fan",
                "hostname": "fan-dev",
                "model": "Thin Laptop",
                "os_name": "Ubuntu",
                "kernel_version": "6.14.0",
                "first_seen_at": "2026-07-07T02:55:00+00:00",
                "last_seen_at": "2026-07-07T03:04:00+00:00",
            },
            "latest_metrics": {
                "cpu.package_temp_c": {
                    "value": 84.0,
                    "unit": "celsius",
                    "observed_at": "2026-07-07T03:04:00+00:00",
                },
                "fan.rpm": {
                    "value": 0.0,
                    "unit": "rpm",
                    "observed_at": "2026-07-07T03:04:00+00:00",
                },
            },
            "recent_events": [],
        }
    ]

    overview = build_fleet_overview(snapshots, now=now)
    queue = build_investigation_queue(snapshots, now=now)

    assert overview["summary"]["warning"] == 1
    assert overview["devices"][0]["findings"][0]["title"] == "Cooling response needs inspection"
    assert overview["devices"][0]["findings"][0]["evidence"] == "CPU package is 84.0C while fan RPM is 0."
    assert queue[0]["why_now"] == "Cooling response needs inspection"
    assert queue[0]["next_step"] == "Check fan readings, airflow clearance, and workload before repeating load."


def test_pattern_overview_groups_gpu_wifi_and_nvme_components() -> None:
    snapshots = [
        {
            "device": {
                "device_id": "dev-a",
                "hostname": "dev-a",
                "model": "Laptop",
                "os_name": "Ubuntu",
                "kernel_version": "6.14.0",
                "first_seen_at": "2026-07-07T02:55:00+00:00",
                "last_seen_at": "2026-07-07T03:04:00+00:00",
            },
            "latest_metrics": {},
            "recent_events": [
                {
                    "category": "graphics",
                    "severity": "warning",
                    "source": "kernel",
                    "message_summary": "i915 0000:00:02.0: [drm] *ERROR* Atomic update failure",
                    "raw_ref": "journalctl -k",
                    "observed_at": "2026-07-07T03:00:00+00:00",
                    "fingerprint": "graphics-dev-a",
                },
                {
                    "category": "network",
                    "severity": "warning",
                    "source": "NetworkManager",
                    "message_summary": "wlp0s20f3: state change: activated -> disconnected",
                    "raw_ref": "journalctl -u NetworkManager",
                    "observed_at": "2026-07-07T03:01:00+00:00",
                    "fingerprint": "network-dev-a",
                },
                {
                    "category": "storage",
                    "severity": "warning",
                    "source": "kernel",
                    "message_summary": "nvme0n1: I/O timeout, reset controller",
                    "raw_ref": "journalctl -k",
                    "observed_at": "2026-07-07T03:02:00+00:00",
                    "fingerprint": "storage-dev-a",
                },
            ],
        }
    ]

    overview = build_pattern_overview(snapshots)

    components = {group["component"] for group in overview["component_groups"]}
    assert {"gpu:i915", "wifi:wlp0s20f3", "nvme:nvme0n1"}.issubset(components)
