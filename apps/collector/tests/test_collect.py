from datetime import datetime, timezone

from quipu_collector.collect import (
    _smartctl_metrics,
    _windows_hardware_monitor_library_metrics,
    _windows_performance_thermal_metrics,
    collect_observation,
)


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
    assert metrics["fan.thinkpad_fan1.rpm"]["value"] == 2840.0
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


def test_collect_observation_reads_windows_signals(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("quipu_collector.collect.platform.system", lambda: "Windows")

    def fake_command_runner(args: list[str]) -> str | None:
        if args == ["netsh", "wlan", "show", "interfaces"]:
            return "\n".join(
                [
                    "Name                   : Wi-Fi",
                    "Signal                 : 82%",
                    "Receive rate (Mbps)    : 866.7",
                    "Transmit rate (Mbps)   : 144.4",
                ]
            )
        if args[:4] != ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass"]:
            return None
        script = args[-1]
        if "Win32_ComputerSystem" in script:
            return '{"Model":"17ZD90SP-GX56K","OsName":"Microsoft Windows 11 Pro","CpuModel":"Intel(R) Core(TM) Ultra 5 125H"}'
        if "Win32_Processor" in script:
            return '{"Name":"Intel(R) Core(TM) Ultra 5 125H","NumberOfCores":14,"NumberOfLogicalProcessors":18}'
        if "Win32_OperatingSystem" in script:
            return '{"TotalVisibleMemorySize":16000000,"FreePhysicalMemory":4000000}'
        if "Win32_Battery" in script:
            return '{"EstimatedChargeRemaining":73,"BatteryStatus":2}'
        if "Get-NetAdapter" in script:
            return '{"Name":"Wi-Fi","InterfaceDescription":"Intel(R) Wi-Fi 6E","LinkSpeed":"1.2 Gbps"}'
        if "Win32_DiskDrive" in script:
            return '{"Index":0,"Model":"Samsung NVMe SSD","InterfaceType":"NVMe","MediaType":"SSD","Size":512000000000}'
        if "MSAcpi_ThermalZoneTemperature" in script:
            return '{"CurrentTemperature":3012}'
        return None

    batch = collect_observation(
        root=tmp_path,
        observed_at=datetime(2026, 7, 9, 2, 45, tzinfo=timezone.utc),
        device_id="windows",
        device_alias="윈도우",
        command_runner=fake_command_runner,
    )

    assert batch["device"]["device_id"] == "windows"
    assert batch["device"]["display_name"] == "윈도우"
    assert batch["device"]["model"] == "17ZD90SP-GX56K"
    assert batch["device"]["cpu_model"] == "Intel(R) Core(TM) Ultra 5 125H"
    assert batch["device"]["os_name"] == "Microsoft Windows 11 Pro"

    metrics = {metric["name"]: metric for metric in batch["metrics"]}
    assert metrics["cpu.physical_cores"]["value"] == 14.0
    assert metrics["cpu.logical_threads"]["value"] == 18.0
    assert metrics["cpu.performance_cores"]["value"] == 4.0
    assert metrics["cpu.efficient_cores"]["value"] == 8.0
    assert metrics["cpu.low_power_efficient_cores"]["value"] == 2.0
    assert metrics["memory.used_percent"]["value"] == 75.0
    assert metrics["battery.capacity_percent"]["value"] == 73.0
    assert metrics["battery.ac_online"]["value"] == 1.0
    assert metrics["wifi.signal_dbm"]["value"] == -59.0
    assert metrics["wifi.wi_fi.signal_dbm"]["value"] == -59.0
    assert metrics["wifi.rx_bitrate_mbps"]["value"] == 866.7
    assert metrics["wifi.tx_bitrate_mbps"]["value"] == 144.4
    assert metrics["wifi.wi_fi.link_bitrate_mbps"]["value"] == 1200.0
    assert metrics["nvme.capacity_bytes"]["value"] == 512000000000.0
    assert metrics["nvme.samsung_nvme_ssd.capacity_bytes"]["value"] == 512000000000.0
    assert metrics["thermal.windows_zone_0.temp_c"]["value"] == 28.05


def test_collect_observation_reads_localized_windows_wifi_and_physical_disk(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("quipu_collector.collect.platform.system", lambda: "Windows")

    def fake_command_runner(args: list[str]) -> str | None:
        if args == ["netsh", "wlan", "show", "interfaces"]:
            return "\n".join(
                [
                    "이름                   : Wi-Fi",
                    "신호                   : 78%",
                    "수신 속도(Mbps)        : 650",
                    "전송 속도(Mbps)        : 390",
                ]
            )
        if args[:4] != ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass"]:
            return None
        script = args[-1]
        if "Win32_ComputerSystem" in script:
            return '{"Model":"Windows Laptop","OsName":"Microsoft Windows 11 Pro","CpuModel":"13th Gen Intel(R) Core(TM) i5-1340P"}'
        if "Win32_Processor" in script:
            return '{"Name":"13th Gen Intel(R) Core(TM) i5-1340P","NumberOfCores":12,"NumberOfLogicalProcessors":16}'
        if "Win32_OperatingSystem" in script:
            return '{"TotalVisibleMemorySize":32000000,"FreePhysicalMemory":8000000}'
        if "Win32_Battery" in script:
            return None
        if "Get-NetAdapter" in script:
            return '{"Name":"무선랜","InterfaceDescription":"Intel(R) Wireless-AC","Status":"Up","LinkSpeed":"866.7 Mbps","NdisPhysicalMedium":9}'
        if "Win32_DiskDrive" in script:
            return '{"Index":0,"Model":"Samsung MZVL","InterfaceType":"SCSI","MediaType":"SSD","Size":1024000000000}'
        if "Get-PhysicalDisk" in script:
            return '{"DeviceId":0,"FriendlyName":"Samsung MZVL","BusType":"NVMe","MediaType":"SSD","Size":1024000000000}'
        return None

    batch = collect_observation(
        root=tmp_path,
        observed_at=datetime(2026, 7, 9, 4, 20, tzinfo=timezone.utc),
        device_id="windows",
        device_alias="윈도우",
        command_runner=fake_command_runner,
    )

    metrics = {metric["name"]: metric for metric in batch["metrics"]}
    assert metrics["cpu.performance_cores"]["value"] == 4.0
    assert metrics["cpu.efficient_cores"]["value"] == 8.0
    assert metrics["cpu.physical_cores"]["value"] == 12.0
    assert metrics["cpu.logical_threads"]["value"] == 16.0
    assert metrics["wifi.signal_dbm"]["value"] == -61.0
    assert metrics["wifi.wifi0.signal_dbm"]["value"] == -61.0
    assert metrics["wifi.rx_bitrate_mbps"]["value"] == 650.0
    assert metrics["wifi.tx_bitrate_mbps"]["value"] == 390.0
    assert metrics["wifi.wifi0.rx_bitrate_mbps"]["value"] == 650.0
    assert metrics["wifi.wifi0.tx_bitrate_mbps"]["value"] == 390.0
    assert metrics["wifi.wifi0.link_bitrate_mbps"]["value"] == 866.7
    assert metrics["nvme.capacity_bytes"]["value"] == 1024000000000.0
    assert metrics["nvme.samsung_mzvl.capacity_bytes"]["value"] == 1024000000000.0


def test_collect_observation_reads_windows_wmi_wifi_signal_and_monitor_temperatures(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("quipu_collector.collect.platform.system", lambda: "Windows")

    def fake_command_runner(args: list[str]) -> str | None:
        if args[:3] == ["netsh", "wlan", "show"] or args[:3] == [r"C:\Windows\System32\netsh.exe", "wlan", "show"]:
            return None
        if args[:4] != ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass"]:
            return None
        script = args[-1]
        if "netsh.exe" in script:
            return None
        if "Win32_ComputerSystem" in script:
            return '{"Model":"Windows Laptop","OsName":"Microsoft Windows 11 Pro","CpuModel":"13th Gen Intel(R) Core(TM) i5-1340P"}'
        if "Win32_Processor" in script:
            return '{"Name":"13th Gen Intel(R) Core(TM) i5-1340P","NumberOfCores":12,"NumberOfLogicalProcessors":16}'
        if "Win32_OperatingSystem" in script:
            return '{"TotalVisibleMemorySize":32000000,"FreePhysicalMemory":16000000}'
        if "MSNdis_80211_ReceivedSignalStrength" in script:
            return '{"InstanceName":"Intel(R) Wi-Fi 6E","Ndis80211ReceivedSignalStrength":-52}'
        if "Get-NetAdapter" in script:
            return '{"Name":"Wi-Fi","InterfaceDescription":"Intel(R) Wi-Fi 6E","Status":"Up","LinkSpeed":"961 Mbps","NdisPhysicalMedium":9}'
        if "Win32_DiskDrive" in script or "Get-PhysicalDisk" in script:
            return None
        if "MSAcpi_ThermalZoneTemperature" in script:
            return None
        if "root/LibreHardwareMonitor" in script and "SensorType -eq 'Fan'" in script:
            return None
        if "root/LibreHardwareMonitor" in script and "SensorType -eq 'Load'" in script:
            return (
                "["
                '{"Name":"CPU Total","Parent":"Intel Core i5-1340P","Value":32.0},'
                '{"Name":"P-Core #1","Parent":"Intel Core i5-1340P","Value":41.5},'
                '{"Name":"E-Core #2","Parent":"Intel Core i5-1340P","Value":18.0}'
                "]"
            )
        if "root/LibreHardwareMonitor" in script and "SensorType -eq 'Temperature'" in script:
            return (
                "["
                '{"Name":"CPU Package","Parent":"Intel Core i5-1340P","Value":58.5},'
                '{"Name":"P-Core #1","Parent":"Intel Core i5-1340P","Value":55.0},'
                '{"Name":"E-Core #2","Parent":"Intel Core i5-1340P","Value":49.0},'
                '{"Name":"Temperature","Parent":"Samsung SSD 980 PRO 1TB","Value":42.0}'
                "]"
            )
        return None

    batch = collect_observation(
        root=tmp_path,
        observed_at=datetime(2026, 7, 9, 4, 40, tzinfo=timezone.utc),
        device_id="windows",
        device_alias="윈도우",
        command_runner=fake_command_runner,
    )

    metrics = {metric["name"]: metric for metric in batch["metrics"]}
    assert metrics["cpu.performance_cores"]["value"] == 4.0
    assert metrics["cpu.efficient_cores"]["value"] == 8.0
    assert metrics["wifi.signal_dbm"]["value"] == -52.0
    assert metrics["wifi.intel_r_wi_fi_6e.signal_dbm"]["value"] == -52.0
    assert metrics["wifi.link_bitrate_mbps"]["value"] == 961.0
    assert metrics["cpu.package_temp_c"]["value"] == 58.5
    assert metrics["cpu.p_core_1.temp_c"]["value"] == 55.0
    assert metrics["cpu.e_core_2.temp_c"]["value"] == 49.0
    assert metrics["cpu.load_percent"]["value"] == 32.0
    assert metrics["cpu.p_core_1.load_percent"]["value"] == 41.5
    assert metrics["cpu.e_core_2.load_percent"]["value"] == 18.0
    assert metrics["nvme.temp_c"]["value"] == 42.0
    assert metrics["nvme.samsung_ssd_980_pro_1tb_temperature.temp_c"]["value"] == 42.0


def test_collect_observation_reads_windows_reliability_fans_and_events(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("quipu_collector.collect.platform.system", lambda: "Windows")

    def fake_command_runner(args: list[str]) -> str | None:
        if args[:3] == ["netsh", "wlan", "show"] or args[:3] == [r"C:\Windows\System32\netsh.exe", "wlan", "show"]:
            return None
        if args[:4] != ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass"]:
            return None
        script = args[-1]
        if "netsh.exe" in script:
            return None
        if "Win32_ComputerSystem" in script:
            return '{"Model":"Windows Laptop","OsName":"Microsoft Windows 11 Pro","CpuModel":"13th Gen Intel(R) Core(TM) i5-1340P"}'
        if "Win32_Processor" in script:
            return '{"Name":"13th Gen Intel(R) Core(TM) i5-1340P","NumberOfCores":12,"NumberOfLogicalProcessors":16}'
        if "Win32_OperatingSystem" in script:
            return '{"TotalVisibleMemorySize":32000000,"FreePhysicalMemory":16000000}'
        if "Get-StorageReliabilityCounter" in script:
            return (
                '{"DeviceId":0,"FriendlyName":"Samsung PM9A1","BusType":"NVMe","MediaType":"SSD",'
                '"Size":1024000000000,"HealthStatus":"Healthy","OperationalStatus":"OK",'
                '"Temperature":47,"Wear":7,"PowerOnHours":321,"ReadErrorsUncorrected":1,'
                '"WriteErrorsUncorrected":2}'
            )
        if "Win32_PerfFormattedData_PerfDisk_PhysicalDisk" in script:
            return (
                "["
                '{"DeviceId":"0","Name":"0 C:","FriendlyName":"Samsung PM9A1","BusType":"NVMe","MediaType":"SSD",'
                '"DiskReadBytesPersec":4096,"DiskWriteBytesPersec":8192},'
                '{"DeviceId":"1","Name":"1 D:","FriendlyName":"USB Disk","BusType":"USB","MediaType":"SSD",'
                '"DiskReadBytesPersec":9999,"DiskWriteBytesPersec":9999}'
                "]"
            )
        if "Get-PhysicalDisk" in script:
            return '{"DeviceId":0,"FriendlyName":"Samsung PM9A1","BusType":"NVMe","MediaType":"SSD","Size":1024000000000}'
        if "Win32_TemperatureProbe" in script:
            return '{"Name":"CPU Package","DeviceID":"CPU0","CurrentReading":3315}'
        if "root/LibreHardwareMonitor" in script and "SensorType -eq 'Fan'" in script:
            return '{"Name":"CPU Fan","Parent":"Embedded Controller","Value":2410}'
        if "Get-WinEvent" in script:
            return (
                "["
                '{"TimeCreated":"2026-07-09T05:10:00.0000000Z","ProviderName":"stornvme","Id":129,'
                '"Level":3,"LevelDisplayName":"Warning","LogName":"System",'
                '"Message":"Reset to device, \\\\Device\\\\RaidPort0, was issued."},'
                '{"TimeCreated":"2026-07-09T05:11:00Z","ProviderName":"Microsoft-Windows-WLAN-AutoConfig","Id":11004,'
                '"Level":3,"LevelDisplayName":"Warning","LogName":"System",'
                '"Message":"Wireless network disconnected."},'
                '{"TimeCreated":"2026-07-09T05:12:00Z","ProviderName":"Microsoft-Windows-Kernel-Power","Id":41,'
                '"Level":1,"LevelDisplayName":"Critical","LogName":"System",'
                '"Message":"The system has rebooted without cleanly shutting down first."}'
                "]"
            )
        return None

    batch = collect_observation(
        root=tmp_path,
        observed_at=datetime(2026, 7, 9, 5, 15, tzinfo=timezone.utc),
        device_id="windows",
        device_alias="윈도우",
        command_runner=fake_command_runner,
    )

    metrics = {metric["name"]: metric for metric in batch["metrics"]}
    assert metrics["nvme.capacity_bytes"]["value"] == 1024000000000.0
    assert metrics["nvme.samsung_pm9a1.capacity_bytes"]["value"] == 1024000000000.0
    assert metrics["nvme.temp_c"]["value"] == 47.0
    assert metrics["nvme.samsung_pm9a1.temp_c"]["value"] == 47.0
    assert metrics["nvme.read_bytes_per_sec"]["value"] == 4096.0
    assert metrics["nvme.write_bytes_per_sec"]["value"] == 8192.0
    assert metrics["nvme.samsung_pm9a1.read_bytes_per_sec"]["value"] == 4096.0
    assert metrics["nvme.samsung_pm9a1.write_bytes_per_sec"]["value"] == 8192.0
    assert metrics["nvme.smart_passed"]["value"] == 1.0
    assert metrics["nvme.percentage_used_percent"]["value"] == 7.0
    assert metrics["nvme.media_errors"]["value"] == 3.0
    assert metrics["nvme.power_on_hours"]["value"] == 321.0
    assert metrics["cpu.package_temp_c"]["value"] == 58.35
    assert metrics["fan.rpm"]["value"] == 2410.0
    assert metrics["fan.embedded_controller_cpu_fan.rpm"]["value"] == 2410.0

    events = {(event["category"], event["source"]): event for event in batch["events"]}
    assert events[("storage", "stornvme")]["severity"] == "warning"
    assert events[("network", "Microsoft-Windows-WLAN-AutoConfig")]["severity"] == "warning"
    assert events[("reboot", "Microsoft-Windows-Kernel-Power")]["severity"] == "critical"


def test_collect_observation_reads_windows_native_fan(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("quipu_collector.collect.platform.system", lambda: "Windows")

    def fake_command_runner(args: list[str]) -> str | None:
        if args[:3] == ["netsh", "wlan", "show"] or args[:3] == [r"C:\Windows\System32\netsh.exe", "wlan", "show"]:
            return None
        if args[:4] != ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass"]:
            return None
        script = args[-1]
        if "netsh.exe" in script:
            return None
        if "Win32_ComputerSystem" in script:
            return '{"Model":"Windows Laptop","OsName":"Microsoft Windows 11 Pro","CpuModel":"13th Gen Intel(R) Core(TM) i5-1340P"}'
        if "Win32_Processor" in script:
            return '{"Name":"13th Gen Intel(R) Core(TM) i5-1340P","NumberOfCores":12,"NumberOfLogicalProcessors":16}'
        if "Win32_OperatingSystem" in script:
            return '{"TotalVisibleMemorySize":32000000,"FreePhysicalMemory":16000000}'
        if "Win32_Fan" in script:
            return '{"Name":"System Fan","DeviceID":"Fan0","CurrentReading":1820,"DesiredSpeed":0}'
        return None

    batch = collect_observation(
        root=tmp_path,
        observed_at=datetime(2026, 7, 9, 5, 25, tzinfo=timezone.utc),
        device_id="windows",
        device_alias="윈도우",
        command_runner=fake_command_runner,
    )

    metrics = {metric["name"]: metric for metric in batch["metrics"]}
    assert metrics["fan.rpm"]["value"] == 1820.0
    assert metrics["fan.system_fan_fan0.rpm"]["value"] == 1820.0


def test_smartctl_metrics_collects_per_device_and_worst_case_nvme_health() -> None:
    def fake_command_runner(args: list[str]) -> str | None:
        if args == ["smartctl", "--scan-open", "--json"]:
            return (
                '{"devices":['
                '{"name":"/dev/nvme0","type":"nvme","protocol":"NVMe"},'
                '{"name":"/dev/nvme1","type":"nvme","protocol":"NVMe"}'
                ']}'
            )
        if args[-1:] == ["/dev/nvme0"]:
            return (
                '{"model_name":"Fast Disk","smart_status":{"passed":true},'
                '"temperature":{"current":42},"nvme_smart_health_information_log":{'
                '"critical_warning":0,"available_spare":100,"percentage_used":4,'
                '"media_errors":0,"power_on_hours":100,"unsafe_shutdowns":2,'
                '"num_err_log_entries":1}}'
            )
        if args[-1:] == ["/dev/nvme1"]:
            return (
                '{"model_name":"Warm Disk","smart_status":{"passed":false},'
                '"temperature":{"current":61},"nvme_smart_health_information_log":{'
                '"critical_warning":1,"available_spare":8,"percentage_used":91,'
                '"media_errors":3,"power_on_hours":200,"unsafe_shutdowns":4,'
                '"num_err_log_entries":5}}'
            )
        return None

    metrics = {
        metric["name"]: metric
        for metric in _smartctl_metrics("2026-07-10T03:00:00+00:00", fake_command_runner)
    }

    assert metrics["nvme.temp_c"]["value"] == 61.0
    assert metrics["nvme.smart_passed"]["value"] == 0.0
    assert metrics["nvme.critical_warning"]["value"] == 1.0
    assert metrics["nvme.available_spare_percent"]["value"] == 8.0
    assert metrics["nvme.percentage_used_percent"]["value"] == 91.0
    assert metrics["nvme.media_errors"]["value"] == 3.0
    assert metrics["nvme.power_on_hours"]["value"] == 200.0
    assert metrics["nvme.unsafe_shutdowns"]["value"] == 6.0
    assert metrics["nvme.error_log_entries"]["value"] == 6.0
    assert metrics["nvme.fast_disk.smart_passed"]["value"] == 1.0
    assert metrics["nvme.warm_disk.smart_passed"]["value"] == 0.0


def test_windows_hardware_monitor_library_maps_temperature_and_fan_sensors() -> None:
    def fake_command_runner(args: list[str]) -> str | None:
        if args[:4] != ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass"]:
            return None
        if "LibreHardwareMonitor.Hardware.Computer" not in args[-1]:
            return None
        return (
            "["
            '{"Hardware":"Intel Core i5","HardwareType":"Cpu","Name":"CPU Package",'
            '"SensorType":"Temperature","Value":62.5,"Identifier":"/intelcpu/0/temperature/14"},'
            '{"Hardware":"Intel Core i5","HardwareType":"Cpu","Name":"P-Core #1",'
            '"SensorType":"Temperature","Value":58.0,"Identifier":"/intelcpu/0/temperature/2"},'
            '{"Hardware":"Intel Core i5","HardwareType":"Cpu","Name":"E-Core #2",'
            '"SensorType":"Temperature","Value":52.0,"Identifier":"/intelcpu/0/temperature/8"},'
            '{"Hardware":"Intel Core i5","HardwareType":"Cpu","Name":"CPU Total",'
            '"SensorType":"Load","Value":27.0,"Identifier":"/intelcpu/0/load/0"},'
            '{"Hardware":"Intel Core i5","HardwareType":"Cpu","Name":"P-Core #1",'
            '"SensorType":"Load","Value":35.0,"Identifier":"/intelcpu/0/load/2"},'
            '{"Hardware":"Intel Core i5","HardwareType":"Cpu","Name":"E-Core #2",'
            '"SensorType":"Load","Value":12.0,"Identifier":"/intelcpu/0/load/8"},'
            '{"Hardware":"Samsung SSD","HardwareType":"Storage","Name":"Temperature",'
            '"SensorType":"Temperature","Value":44.0,"Identifier":"/nvme/0/temperature/0"},'
            '{"Hardware":"Embedded Controller","HardwareType":"Motherboard","Name":"CPU Fan",'
            '"SensorType":"Fan","Value":2350,"Identifier":"/lpc/ec/fan/0"}'
            "]"
        )

    metrics = {
        metric["name"]: metric
        for metric in _windows_hardware_monitor_library_metrics(
            "2026-07-10T03:00:00+00:00", fake_command_runner
        )
    }

    assert metrics["cpu.package_temp_c"]["value"] == 62.5
    assert metrics["cpu.p_core_1.temp_c"]["value"] == 58.0
    assert metrics["cpu.e_core_2.temp_c"]["value"] == 52.0
    assert metrics["cpu.load_percent"]["value"] == 27.0
    assert metrics["cpu.p_core_1.load_percent"]["value"] == 35.0
    assert metrics["cpu.e_core_2.load_percent"]["value"] == 12.0
    assert metrics["nvme.temp_c"]["value"] == 44.0
    assert metrics["nvme.samsung_ssd_temperature.temp_c"]["value"] == 44.0
    assert metrics["fan.rpm"]["value"] == 2350.0
    assert metrics["fan.embedded_controller_cpu_fan.rpm"]["value"] == 2350.0


def test_windows_performance_counter_maps_thermal_zone_kelvin() -> None:
    def fake_command_runner(args: list[str]) -> str | None:
        if args[:4] != ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass"]:
            return None
        if "Win32_PerfFormattedData_Counters_ThermalZoneInformation" not in args[-1]:
            return None
        return '{"Name":"\\\\_TZ.TZ00","Temperature":305,"HighPrecisionTemperature":3052}'

    metrics = _windows_performance_thermal_metrics(
        "2026-07-10T04:00:00+00:00", fake_command_runner
    )

    assert metrics == [
        {
            "name": "thermal.windows_zone_tz_tz00.temp_c",
            "value": 32.05,
            "unit": "celsius",
            "observed_at": "2026-07-10T04:00:00+00:00",
        }
    ]
