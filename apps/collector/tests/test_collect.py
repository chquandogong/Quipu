from datetime import datetime, timezone

from quipu_collector.collect import collect_observation


def _write(path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_collect_observation_reads_linux_signals_without_raw_machine_id(tmp_path) -> None:
    root = tmp_path
    _write(root / "etc/machine-id", "0123456789abcdef0123456789abcdef\n")
    _write(root / "etc/hostname", "build-xps\n")
    _write(root / "etc/os-release", 'PRETTY_NAME="Ubuntu 24.04 LTS"\n')
    _write(root / "proc/loadavg", "0.47 0.66 0.91 1/812 4412\n")
    _write(
        root / "proc/meminfo",
        "\n".join(
            [
                "MemTotal:        8000000 kB",
                "MemAvailable:    6000000 kB",
            ]
        ),
    )
    _write(root / "proc/net/wireless", "Inter-| sta\nwlp0s20f3: 0000   64.  -43.  -256        0      0      0      0      0        0\n")
    _write(root / "sys/devices/virtual/dmi/id/product_name", "XPS 13\n")
    _write(root / "sys/class/thermal/thermal_zone0/type", "x86_pkg_temp\n")
    _write(root / "sys/class/thermal/thermal_zone0/temp", "63000\n")
    _write(root / "sys/class/hwmon/hwmon0/name", "nvme\n")
    _write(root / "sys/class/hwmon/hwmon0/temp1_input", "42000\n")
    _write(
        root / "var/log/quipu/kernel.log",
        "2026-07-07T05:22:10+00:00 kernel: CPU0: Core temperature above threshold, cpu clock throttled\n",
    )
    _write(
        root / "var/log/quipu/networkmanager.log",
        "2026-07-07T05:24:00+00:00 NetworkManager: wlp0s20f3: state change: activated -> disconnected (reason 'supplicant-disconnect')\n",
    )

    observed_at = datetime(2026, 7, 7, 5, 30, tzinfo=timezone.utc)
    batch = collect_observation(root=root, observed_at=observed_at)

    assert batch["batch_id"].startswith("collector-")
    assert batch["observed_at"] == "2026-07-07T05:30:00+00:00"
    assert batch["device"]["hostname"] == "build-xps"
    assert batch["device"]["device_id"].startswith("host-")
    assert batch["device"]["device_id"] != "0123456789abcdef0123456789abcdef"
    assert batch["device"]["model"] == "XPS 13"
    assert batch["device"]["os_name"] == "Ubuntu 24.04 LTS"

    metrics = {metric["name"]: metric for metric in batch["metrics"]}
    assert metrics["cpu.load_1m"]["value"] == 0.47
    assert metrics["memory.used_percent"]["value"] == 25.0
    assert metrics["cpu.package_temp_c"]["value"] == 63.0
    assert metrics["nvme.temp_c"]["value"] == 42.0
    assert metrics["wifi.signal_dbm"]["value"] == -43.0
    events = {(event["category"], event["source"]): event for event in batch["events"]}
    assert events[("thermal", "kernel")]["severity"] == "warning"
    assert "cpu clock throttled" in events[("thermal", "kernel")]["message_summary"]
    assert events[("thermal", "kernel")]["raw_ref"] == "var/log/quipu/kernel.log"
    assert events[("thermal", "kernel")]["fingerprint"].startswith("thermal-kernel-")
    assert events[("network", "NetworkManager")]["severity"] == "warning"
    assert "disconnected" in events[("network", "NetworkManager")]["message_summary"]
    assert events[("network", "NetworkManager")]["raw_ref"] == "var/log/quipu/networkmanager.log"
    assert events[("network", "NetworkManager")]["fingerprint"].startswith("network-networkmanager-")
