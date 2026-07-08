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
        root / "proc/cpuinfo",
        "\n\n".join(
            [
                "\n".join(
                    [
                        f"processor\t: {index}",
                        "model name\t: Intel(R) Core(TM) Ultra 5 125H",
                    ]
                )
                for index in range(18)
            ]
        )
        + "\n",
    )
    _write(
        root / "proc/meminfo",
        "\n".join(
            [
                "MemTotal:        8000000 kB",
                "MemAvailable:    6000000 kB",
            ]
        ),
    )
    _write(
        root / "proc/net/wireless",
        "\n".join(
            [
                "Inter-| sta",
                "wlp0s20f3: 0000   64.  -43.  -256        0      0      0      0      0        0",
                "wlan0: 0000   50.  -61.  -256        0      0      0      0      0        0",
            ]
        )
        + "\n",
    )
    _write(root / "sys/devices/virtual/dmi/id/product_name", "XPS 13\n")
    _write(root / "sys/class/thermal/thermal_zone0/type", "x86_pkg_temp\n")
    _write(root / "sys/class/thermal/thermal_zone0/temp", "63000\n")
    _write(root / "sys/class/hwmon/hwmon0/name", "nvme\n")
    _write(root / "sys/class/hwmon/hwmon0/temp1_input", "42000\n")
    _write(root / "sys/class/hwmon/hwmon1/name", "nvme\n")
    _write(root / "sys/class/hwmon/hwmon1/temp1_input", "44000\n")
    _write(root / "sys/class/hwmon/hwmon2/name", "coretemp\n")
    _write(root / "sys/class/hwmon/hwmon2/temp1_label", "Package id 0\n")
    _write(root / "sys/class/hwmon/hwmon2/temp1_input", "63000\n")
    _write(root / "sys/class/hwmon/hwmon2/temp2_label", "Core 0\n")
    _write(root / "sys/class/hwmon/hwmon2/temp2_input", "61000\n")
    _write(root / "sys/class/hwmon/hwmon2/temp3_label", "Core 1\n")
    _write(root / "sys/class/hwmon/hwmon2/temp3_input", "62000\n")
    _write(root / "sys/class/hwmon/hwmon3/name", "thinkpad\n")
    _write(root / "sys/class/hwmon/hwmon3/fan1_input", "2840\n")
    _write(root / "sys/class/block/nvme0n1/size", "2000000000\n")
    _write(root / "sys/class/block/nvme0n1/stat", "1 0 1000 0 1 0 2000 0 0 0 0\n")
    _write(
        root / "sys/class/nvme/nvme0/smart_log",
        "\n".join(
            [
                "critical_warning : 1",
                "available_spare : 9%",
                "percentage_used : 12%",
                "media_errors : 2",
            ]
        )
        + "\n",
    )
    _write(
        root / "var/log/quipu/kernel.log",
        "\n".join(
                [
                    "2026-07-07T05:22:10+00:00 kernel: CPU0: Core temperature above threshold, cpu clock throttled",
                    "2026-07-07T05:23:10+00:00 kernel: nvme0n1: I/O timeout, reset controller",
                    "2026-07-07T05:25:00+00:00 kernel: ACPI: battery discharge rate high while AC offline",
                    "2026-07-07T05:25:30+00:00 kernel: i915 0000:00:02.0: Using 41-bit DMA addresses",
                    "2026-07-07T05:26:00+00:00 kernel: i915 0000:00:02.0: GPU HANG detected",
                    "2026-07-07T05:27:00+00:00 kernel: Out of memory: Killed process 1234 chrome",
                    "2026-07-07T05:28:00+00:00 systemd: Rebooting.",
                ]
        )
        + "\n",
    )
    _write(
        root / "var/log/apt/history.log",
        "2026-07-07T05:20:00+00:00 apt: Upgrade: linux-image-generic:amd64\n",
    )
    _write(
        root / "var/log/quipu/networkmanager.log",
        "\n".join(
            [
                "2026-07-07T05:23:30+00:00 NetworkManager: wpa_supplicant: WPA: Group rekeying completed with 24:4b:fe:27:e6:34",
                "2026-07-07T05:24:00+00:00 NetworkManager: wlp0s20f3: state change: activated -> disconnected (reason 'supplicant-disconnect')",
            ]
        )
        + "\n",
    )
    _write(root / "sys/class/power_supply/BAT0/type", "Battery\n")
    _write(root / "sys/class/power_supply/BAT0/capacity", "37\n")
    _write(root / "sys/class/power_supply/BAT0/status", "Discharging\n")
    _write(root / "sys/class/power_supply/AC/type", "Mains\n")
    _write(root / "sys/class/power_supply/AC/online", "0\n")

    def fake_command_runner(args: list[str]) -> str | None:
        if args == ["iw", "dev", "wlp0s20f3", "link"]:
            return "Connected to 24:4b:fe:27:e6:34\n\trx bitrate: 866.7 MBit/s\n\ttx bitrate: 144.4 MBit/s\n"
        if args == ["iw", "dev", "wlan0", "link"]:
            return "Connected to 24:4b:fe:27:e6:35\n\trx bitrate: 72.2 MBit/s\n\ttx bitrate: 58.5 MBit/s\n"
        return None

    state_dir = tmp_path / "state"
    collect_observation(
        root=root,
        observed_at=datetime(2026, 7, 7, 5, 25, tzinfo=timezone.utc),
        device_alias="Build laptop",
        state_dir=state_dir,
        command_runner=fake_command_runner,
    )
    _write(root / "sys/class/block/nvme0n1/stat", "1 0 1300 0 1 0 2600 0 0 0 0\n")

    observed_at = datetime(2026, 7, 7, 5, 30, tzinfo=timezone.utc)
    batch = collect_observation(
        root=root,
        observed_at=observed_at,
        device_alias="Build laptop",
        state_dir=state_dir,
        command_runner=fake_command_runner,
    )

    assert batch["batch_id"].startswith("collector-")
    assert batch["observed_at"] == "2026-07-07T05:30:00+00:00"
    assert batch["device"]["hostname"] == "build-xps"
    assert batch["device"]["display_name"] == "Build laptop"
    assert batch["device"]["device_id"].startswith("host-")
    assert batch["device"]["device_id"] != "0123456789abcdef0123456789abcdef"
    assert batch["device"]["model"] == "XPS 13"
    assert batch["device"]["cpu_model"] == "Intel(R) Core(TM) Ultra 5 125H"
    assert batch["device"]["os_name"] == "Ubuntu 24.04 LTS"

    metrics = {metric["name"]: metric for metric in batch["metrics"]}
    assert metrics["cpu.load_1m"]["value"] == 0.47
    assert metrics["cpu.load_5m"]["value"] == 0.66
    assert metrics["cpu.load_15m"]["value"] == 0.91
    assert metrics["cpu.physical_cores"]["value"] == 14.0
    assert metrics["cpu.logical_threads"]["value"] == 18.0
    assert metrics["cpu.performance_cores"]["value"] == 4.0
    assert metrics["cpu.efficient_cores"]["value"] == 8.0
    assert metrics["cpu.low_power_efficient_cores"]["value"] == 2.0
    assert metrics["memory.used_percent"]["value"] == 25.0
    assert metrics["cpu.package_temp_c"]["value"] == 63.0
    assert metrics["cpu.core_0.temp_c"]["value"] == 61.0
    assert metrics["cpu.core_1.temp_c"]["value"] == 62.0
    assert metrics["nvme.temp_c"]["value"] == 42.0
    assert metrics["nvme.nvme0.temp_c"]["value"] == 42.0
    assert metrics["nvme.nvme1.temp_c"]["value"] == 44.0
    assert metrics["nvme.capacity_bytes"]["value"] == 1024000000000.0
    assert metrics["nvme.nvme0n1.capacity_bytes"]["value"] == 1024000000000.0
    assert metrics["nvme.read_bytes_per_sec"]["value"] == 512.0
    assert metrics["nvme.write_bytes_per_sec"]["value"] == 1024.0
    assert metrics["nvme.nvme0n1.read_bytes_per_sec"]["value"] == 512.0
    assert metrics["nvme.nvme0n1.write_bytes_per_sec"]["value"] == 1024.0
    assert metrics["wifi.signal_dbm"]["value"] == -43.0
    assert metrics["wifi.wlp0s20f3.signal_dbm"]["value"] == -43.0
    assert metrics["wifi.wlan0.signal_dbm"]["value"] == -61.0
    assert metrics["wifi.rx_bitrate_mbps"]["value"] == 866.7
    assert metrics["wifi.tx_bitrate_mbps"]["value"] == 144.4
    assert metrics["wifi.wlp0s20f3.rx_bitrate_mbps"]["value"] == 866.7
    assert metrics["wifi.wlp0s20f3.tx_bitrate_mbps"]["value"] == 144.4
    assert metrics["wifi.wlan0.rx_bitrate_mbps"]["value"] == 72.2
    assert metrics["wifi.wlan0.tx_bitrate_mbps"]["value"] == 58.5
    assert metrics["battery.capacity_percent"]["value"] == 37.0
    assert metrics["battery.capacity_percent"]["unit"] == "percent"
    assert metrics["battery.ac_online"]["value"] == 0.0
    assert metrics["battery.ac_online"]["unit"] == "boolean"
    assert metrics["fan.rpm"]["value"] == 2840.0
    assert metrics["fan.rpm"]["unit"] == "rpm"
    assert metrics["nvme.critical_warning"]["value"] == 1.0
    assert metrics["nvme.critical_warning"]["unit"] == "boolean"
    assert metrics["nvme.available_spare_percent"]["value"] == 9.0
    assert metrics["nvme.percentage_used_percent"]["value"] == 12.0
    assert metrics["nvme.media_errors"]["value"] == 2.0
    assert metrics["nvme.media_errors"]["unit"] == "count"
    events = {(event["category"], event["source"]): event for event in batch["events"]}
    assert events[("thermal", "kernel")]["severity"] == "warning"
    assert "cpu clock throttled" in events[("thermal", "kernel")]["message_summary"]
    assert events[("thermal", "kernel")]["raw_ref"] == "var/log/quipu/kernel.log"
    assert events[("thermal", "kernel")]["fingerprint"].startswith("thermal-kernel-")
    assert events[("network", "NetworkManager")]["severity"] == "warning"
    assert "disconnected" in events[("network", "NetworkManager")]["message_summary"]
    assert events[("network", "NetworkManager")]["raw_ref"] == "var/log/quipu/networkmanager.log"
    assert events[("network", "NetworkManager")]["fingerprint"].startswith("network-networkmanager-")
    assert events[("storage", "kernel")]["severity"] == "warning"
    assert "I/O timeout" in events[("storage", "kernel")]["message_summary"]
    assert events[("storage", "kernel")]["fingerprint"].startswith("storage-kernel-")
    assert events[("power", "kernel")]["severity"] == "warning"
    assert "battery discharge" in events[("power", "kernel")]["message_summary"]
    assert events[("power", "kernel")]["fingerprint"].startswith("power-kernel-")
    assert events[("graphics", "kernel")]["severity"] == "warning"
    assert "GPU HANG" in events[("graphics", "kernel")]["message_summary"]
    assert not any("Using 41-bit DMA addresses" in event["message_summary"] for event in batch["events"])
    assert events[("memory", "kernel")]["severity"] == "critical"
    assert "Killed process" in events[("memory", "kernel")]["message_summary"]
    assert events[("reboot", "systemd")]["severity"] == "info"
    assert "Rebooting" in events[("reboot", "systemd")]["message_summary"]
    assert events[("update", "apt")]["severity"] == "info"
    assert "Upgrade" in events[("update", "apt")]["message_summary"]
    assert not any("Group rekeying completed" in event["message_summary"] for event in batch["events"])


def test_collect_observation_reads_iwconfig_bitrate_fallback(tmp_path) -> None:
    root = tmp_path
    _write(root / "etc/hostname", "wifi-host\n")
    _write(root / "proc/loadavg", "0.10 0.20 0.30 1/100 42\n")
    _write(
        root / "proc/net/wireless",
        "\n".join(
            [
                "Inter-| sta",
                "wlp0s20f3: 0000   56.  -54.  -256        0      0      0      0      0        0",
            ]
        )
        + "\n",
    )

    def fake_command_runner(args: list[str]) -> str | None:
        if args == ["iwconfig", "wlp0s20f3"]:
            return "wlp0s20f3  IEEE 802.11  ESSID:\"AP\"\n          Bit Rate=720.6 Mb/s\n"
        return None

    batch = collect_observation(
        root=root,
        observed_at=datetime(2026, 7, 7, 5, 30, tzinfo=timezone.utc),
        command_runner=fake_command_runner,
    )

    metrics = {metric["name"]: metric for metric in batch["metrics"]}
    assert metrics["wifi.link_bitrate_mbps"]["value"] == 720.6
    assert metrics["wifi.wlp0s20f3.link_bitrate_mbps"]["value"] == 720.6
