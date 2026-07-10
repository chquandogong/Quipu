# Quipu

<p align="center">
  <img alt="CI" src="https://github.com/chquandogong/Quipu/actions/workflows/ci.yml/badge.svg">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.14.4-2f6f7e">
  <img alt="Status" src="https://img.shields.io/badge/status-local--first%20workstation%20health-5b6b73">
  <img alt="License" src="https://img.shields.io/badge/license-not%20selected-lightgrey">
</p>

<p align="center">
  <strong>Workstation health investigation</strong><br>
  Quipu turns read-only workstation signals into evidence, actions, verification, and team handoff.
</p>

<p align="center">
  <a href="README.md">한국어</a> | English | <a href="README.zh-CN.md">简体中文</a>
</p>

---

## What It Is

Quipu is a local-first tool for investigating laptop and workstation health.
The bundled collector is read-only. On Linux it reads procfs/sysfs signals; on
Windows it reads best-effort PowerShell/CIM/netsh/Get-NetAdapter signals when
the OS exposes them. Other collectors can appear in the same UI when they post
the same ingest API contract. Quipu collects thermal, load, NVMe, Wi-Fi, memory,
disk, battery, fan, kernel, graphics, reboot, and update signals when the
collector reports them, then presents them as a workflow:

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

The product is not a remote repair tool. The collector is read-only and the
server uses deterministic rule-based analysis.

## v0.14.4 Highlights

- Documentation has been reset around the current implementation: README,
  user manual, ship checklist, dashboard, and roadmap now explain which Windows
  metrics are actually received and why some rows can be absent.
- The connected Windows device now reports CPU load as `cpu.load_percent` and
  `cpu.core_<n>.load_percent`; the UI shows those values as `CPU Core Load`.
- After LibreHardwareMonitor `Temperature` sensors became visible, the same
  device also reports `cpu.package_temp_c`, `cpu.p_core_1..4.temp_c`, and
  `cpu.e_core_1..8.temp_c`.
- Windows CPU core temperature only appears when the collector receives
  `cpu.*.temp_c` metrics. `thermal.windows_zone_*.temp_c` is an ACPI thermal
  zone and is not converted into CPU core temperature.
- If Windows core load is visible but core temperature is missing, verify
  LibreHardwareMonitor/OpenHardwareMonitor `Temperature` sensors from an
  elevated PowerShell session and collector `--dry-run`.
- The Windows collector no longer skips direct LibreHardwareMonitor DLL probing
  when the LibreHardwareMonitor GUI is already running; it now discovers
  `LibreHardwareMonitorLib.dll` from the running process, Program Files, and
  WinGet package paths.
- Windows LibreHardwareMonitor/OpenHardwareMonitor CPU P-core/E-core/LP-E core
  temperatures and per-core load percentages are collected and displayed as
  Windows-specific `CPU Cores` and `CPU Core Load` rows.
- Windows detail views now show the metrics the Windows collector actually
  reports instead of forcing Linux-only load-average or CPU-package rows when
  those signals are absent.
- Garbled localized Windows Event Log text is hidden in the UI and replaced
  with readable category/source-oriented fallback copy.
- Cross-platform `smartctl --json` discovery reports aggregate and per-device
  NVMe temperature, SMART pass/fail, critical warning, spare, lifetime usage,
  media errors, power-on hours, unsafe shutdowns, and error-log entries.
- Windows Thermal Zone performance counters provide firmware-exposed system
  temperature without requiring an elevated collector task.
- Windows can query the official LibreHardwareMonitor library directly for CPU
  package/core and storage temperatures plus exposed fan RPM sensors.
- Linux hwmon collection reports every readable fan instead of only the first.
- The Windows task installer supports `-InstallSensorTools` for the official
  sensor packages and `-Highest` for sensors that require administrator access.

- Windows NVMe R/W rate collection now maps
  `Win32_PerfFormattedData_PerfDisk_PhysicalDisk` to NVMe devices from
  `Get-PhysicalDisk`, reporting aggregate and per-device read/write bytes/sec.
- Windows native WMI fallback now also reads `Win32_TemperatureProbe`,
  `Win32_Fan`, and `Win32_Tachometer` when firmware exposes those classes.
- Windows NVMe temperature collection now uses the
  `Get-PhysicalDisk | Get-StorageReliabilityCounter` path when available and
  reports `nvme.temp_c` plus `nvme.<device>.temp_c`.
- Windows fan RPM collection now reads LibreHardwareMonitor/OpenHardwareMonitor
  WMI fan sensors when those tools expose them.
- Windows Event Log collection now classifies recent System/Application events
  into storage, network, graphics, thermal, memory, power, reboot, and update
  investigation events.
- Windows Intel Core i5-1340P devices now report `P 4 / E 8 / 16 threads`
  topology.
- Windows Wi-Fi collection tries direct `netsh`, system-path `netsh`,
  PowerShell `netsh`, and WMI RSSI fallback paths.
- Windows temperature collection can read LibreHardwareMonitor or
  OpenHardwareMonitor WMI sensors for CPU package/core and NVMe/SSD
  temperatures when those tools expose them.
- Windows collector compatibility is improved with longer PowerShell/CIM
  command timeouts, localized `netsh` Wi-Fi parsing, and `Get-PhysicalDisk`
  NVMe capacity detection.
- The left side of the UI is now device-first: `Devices` lists every reporting
  machine, including healthy machines with no active investigation item.
- `Device Issues` shows only the active issues for the selected device.
- Fleet Brief now says `Open issues` instead of `Queue cases`.
- The server preserves an existing display alias and CPU model when a later
  batch for the same `device-id` omits those optional fields.
- Windows collector operations and best-effort telemetry are packaged beside
  the Ubuntu systemd collector: environment file, startup wrapper,
  scheduled-task install script, and uninstall script.
- The Windows startup wrapper runs hidden at user logon, prevents duplicate
  collector loops, keeps the offline buffer enabled, and posts every five
  minutes by default.
- The Windows collector now reports best-effort CPU core/thread, memory,
  battery, Wi-Fi, NVMe capacity, and thermal-zone metrics through CIM, netsh,
  and Get-NetAdapter when Windows exposes them.
- Browser UI sessions opened from private LAN Vite origins on ports 5173 or
  5174 can read the API without the previous local-only CORS failure.
- Version metadata across the collector, server, schema, and web app is now
  `0.14.4`.

## v0.11.0 Highlights

- Multiple laptops can report to the same server; use `--device-id` for a
  stable unique ID and `--device-alias` for a friendly UI name.
- Device labels appear as `alias · hostname` when an alias is present.
- Header metadata is consolidated into one `Project info` hover/focus chip.
- Explanations now use one consistent hover/focus popover pattern.
- Documentation rewritten from the ground up.
- New [User Manual](USER_MANUAL.md).
- Load average is shown as `1m / 5m / 15m`.
- CPU package detail shows only real core sensors exposed by Linux.
- Intel Core Ultra 5 125H sensor patterns are grouped as `P`, `E`, and `LP-E`.
- NVMe and Wi-Fi always show per-device or per-interface chips, even when only
  one device is present.
- The collector now reports CPU model/topology, Wi-Fi Rx/Tx link bitrate, NVMe
  capacity, and NVMe read/write throughput calculated between collector samples.

## Run With Sample Data

```bash
scripts/dev-server.sh
```

In another terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Run With This Notebook Only

Stop the API server, delete the sample database, and start an empty server:

```bash
rm -f data/quipu.sqlite3 data/quipu.sqlite3-wal data/quipu.sqlite3-shm
cd apps/server
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
QUIPU_DATABASE_PATH=../../data/quipu.sqlite3 uvicorn quipu_server.app:app --host 127.0.0.1 --port 8000 --reload
```

Send one local collector batch:

```bash
sudo apt-get install smartmontools
cd apps/collector
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
quipu-collector \
  --server-url http://127.0.0.1:8000 \
  --token dev-token \
  --device-id local-computer \
  --device-alias "My notebook"
```

Refresh the web UI.

## Connect Another Laptop Or Computer

Run the server on a LAN-reachable address, then send collector batches from each
Linux laptop:

```bash
quipu-collector \
  --server-url http://<server-ip>:8000 \
  --token dev-token \
  --device-id office-gram \
  --device-alias "Office Gram"
```

Use a different `--device-id` per machine. Use enrollment tokens instead of
`dev-token` for repeated operation.

## Connect A Windows Workstation

Create `apps/collector/ops/windows/collector.env.ps1` from the example, then
register the collector at user logon:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\install-collector-scheduled-task.ps1 `
  -InstallSensorTools `
  -Highest `
  -ServerUrl http://<server-ip>:8000 `
  -Token dev-token `
  -DeviceId windows `
  -DeviceAlias "Windows"
```

The scheduled task starts `apps/collector/ops/windows/start-quipu-collector.ps1`
hidden in the background. It keeps the offline buffer enabled and sends a batch
every five minutes.

The Windows flow uses the same Python collector package through the scheduled
task wrapper. After installing or updating this release on the Windows machine,
reinstall the collector package and register or restart the scheduled task:

```powershell
cd C:\path\to\Quipu\apps\collector
py -3 -m venv .venv
.\.venv\Scripts\pip.exe install -e .
cd C:\path\to\Quipu
powershell.exe -ExecutionPolicy Bypass -File scripts\install-collector-scheduled-task.ps1 `
  -InstallSensorTools `
  -Highest `
  -ServerUrl http://<server-ip>:8000 `
  -Token dev-token `
  -DeviceId windows `
  -DeviceAlias "Windows"
```

External Windows collectors can also post the same observation batch contract
to the ingest API. Use a stable `device_id`, a friendly `display_name` or alias,
and metric names that match Quipu's telemetry matrix where possible. Missing
Windows rows usually mean the current Windows task is still running an older
collector or has not reported those metric names yet.

## Main Surfaces

- Command Center: selected case, priority, risk, next action.
- Problem Guide: what is wrong, what evidence matters, what to do next.
- Telemetry Brief: CPU, Load, NVMe, Wi-Fi representative values.
- Metric Ledger: detailed core/load/device/interface chips and help tooltips.
- Telemetry Matrix: coverage across CPU profile, memory, disk, fan, NVMe
  health/capacity/I/O, power, Wi-Fi link, network, thermal, kernel, and
  freshness.
- Devices: connected machines, alias/hostname, hardware label, telemetry count,
  last seen time, issue summary, and risk.
- Device Issues: active issues scoped to the selected device.
- Pattern Explorer: repeated signals by category, component, model, and kernel.

## Collector Signals

- CPU model and core/thread counts come from `/proc/cpuinfo`; Intel Core Ultra
  5 125H is shown as 4P/8E/2LP-E/18 threads when detected.
- Wi-Fi link speed comes from `iw dev <interface> link` Rx/Tx bitrate, with
  `iwconfig` Bit Rate as a fallback. This is not an internet speed test result.
- NVMe capacity comes from sysfs block namespaces.
- NVMe read/write speed is bytes/sec calculated from sector-counter deltas
  between collector samples. The first sample can show `Needs 2 samples`.

## Verification

```bash
cd apps/server && . .venv/bin/activate && pytest -v
cd apps/collector && . .venv/bin/activate && pytest -v
cd apps/web && npm test && npm run build
```

## Docs

- [User Manual](USER_MANUAL.md)
- [Changelog](CHANGELOG.md)
- [Dashboard](docs/superpowers/DASHBOARD.md)
- [Ship Checklist](docs/superpowers/SHIP_CHECKLIST.md)
- [Roadmap](docs/superpowers/ROADMAP.md)
- [Security Policy](SECURITY.md)

## Boundaries

Not included in this release:

- remote command execution
- automatic repair
- production deployment
- package publishing
- AI-only conclusions
- raw log warehouse behavior
