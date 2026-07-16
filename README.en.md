# Quipu

<p align="center">
  <img alt="CI" src="https://github.com/chquandogong/Quipu/actions/workflows/ci.yml/badge.svg">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.14.6-2f6f7e">
  <img alt="Status" src="https://img.shields.io/badge/status-local--first%20workstation%20health-5b6b73">
  <img alt="License" src="https://img.shields.io/badge/license-not%20selected-lightgrey">
</p>

<p align="center">
  <strong>Workstation health investigation</strong><br>
  Quipu is not a metrics dashboard. It is a local-first operations tool that finds problems across laptops and workstations, investigates them with evidence, and records what the fix did.
</p>

<p align="center">
  <a href="README.md">한국어</a> | English | <a href="README.zh-CN.md">简体中文</a>
</p>

---

## What It Is

Quipu gathers thermal issues, graphics errors, Wi-Fi instability, storage
warnings, power problems, and reboot traces from laptops and developer
workstations into one screen. The bundled collector is read-only: on Linux it
reads sysfs and procfs; on Windows it reads best-effort signals exposed by
PowerShell/CIM/netsh/LibreHardwareMonitor. Collectors for other operating
systems appear in the same UI when they post the same ingest API contract.

The first question is not "what is the CPU temperature?" but "what should we
investigate right now, and what is the evidence?" The core workflow is:

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

Three components:

- `apps/server`: FastAPI ingest/query API + SQLite (WAL) storage + rule-based analysis.
- `apps/collector`: read-only signal collector CLI (`quipu-collector`) for Linux/Windows.
- `apps/web`: Vite + React investigation UI.

See the [CHANGELOG](CHANGELOG.md) for recent changes.

## UI Layout

The top row is the **Devices** list: every reporting machine with its
alias/hostname, hardware label, metric/event counts, last-seen time, and status
transitions (e.g. `previous ➔ current`). Healthy devices are selectable and
still show full telemetry detail.

The left workspace has two tabs:

- **🚨 Prevention Guide (Smart Advisor)**: active investigation issues for the
  selected device, plus Smart Advisor alert cards (memory, thermal, graphics)
  generated from live telemetry, each with a checklist.
- **🛠️ Actions & Collaboration**: the intervention guide, an action-plan form
  for recording interventions, the recorded-intervention journal, and team
  handoff notes.

The right explorer has four tabs:

- **Vitals**: the **Metric Ledger** (CPU, Load, NVMe, Wi-Fi detail rows) and
  the **Telemetry Matrix** (coverage across CPU profile, memory, disk, NVMe
  health/capacity/I/O, fan, thermal, battery, Wi-Fi link, network, kernel, and
  agent freshness).
- **Diagnosis**: rule-based top hypotheses, before/after verification, and a
  handoff report draft.
- **Timeline**: the evidence timeline of observed events.
- **Operations**: stale-device operational cards and the **Pattern Explorer**
  (repeated signals by category, component, model, and kernel).

When you record an intervention, the server compares the before/after
telemetry windows and returns a `helped / worse / unclear / insufficient_data`
verdict.

## Quick Start

Start the API server. The script creates the virtualenv, installs
dependencies, and binds to `0.0.0.0:8000` so collectors on other machines can
reach it. The database is `data/quipu.sqlite3`.

```bash
scripts/dev-server.sh
```

In another terminal, run the web UI:

```bash
cd apps/web
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

The server does not create data on startup — an empty device list on first
run is expected. Add data one of two ways.

### Option 1: Seed The Sample Fleet

To explore the UI first, manually seed the deterministic sample fixture
(three devices: `thinkpad-p1`, `xps-13`, `framework-13`):

```bash
cd apps/server
. .venv/bin/activate
python -m quipu_server.seed ../../fixtures/ingest/team-sample.json \
  --database ../../data/quipu.sqlite3
```

To remove the sample devices, stop the server and delete the database files:

```bash
rm -f data/quipu.sqlite3 data/quipu.sqlite3-wal data/quipu.sqlite3-shm
```

### Option 2: Connect This Notebook

Run the collector once from another terminal:

```bash
sudo apt-get install smartmontools   # optional, for NVMe SMART
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

`scripts/dev-server.sh` already binds to `0.0.0.0`, so other machines on the
LAN can reach `http://<server-ip>:8000`. Allow TCP `8000` through the firewall
if you run one.

Install the collector on each Linux laptop and post to the same server:

```bash
cd apps/collector
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
quipu-collector \
  --server-url http://<server-ip>:8000 \
  --token dev-token \
  --device-id office-gram \
  --device-alias "Office Gram"
```

- Keep `--device-id` unique per machine and stable over time.
- `--device-alias` is the friendly UI name; devices show as `alias · hostname`.
- `dev-token` is fine for quick tests; use per-device enrollment tokens for
  repeated operation (see [Tokens And Auth](#tokens-and-auth)).

### Connect A Windows Workstation

Windows runs the same collector package through a PowerShell scheduled-task
wrapper. After installing or updating a release, reinstall the virtualenv and
re-register the task:

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

- `-InstallSensorTools` installs the official sensor packages
  (LibreHardwareMonitor and related tools).
- `-Highest` enables sensors that require administrator access (CPU core
  temperatures, fan RPM).

The scheduled task starts hidden at user logon, prevents duplicate collector
loops, keeps the offline buffer enabled, and posts every five minutes by
default. See the [User Manual](USER_MANUAL.md) for diagnosing missing Windows
metrics.

## Collector Signals

The collector reads system signals read-only. There is no remote command
execution and no automatic repair. It only stores previous sector counters in
its state directory to compute NVMe read/write rates.

| Category            | Representative metrics                                                                                                                                                                                                                                    | Source (Linux / Windows)                                             |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| CPU load            | `cpu.load_1m/5m/15m` (Linux); `cpu.load_percent`, `cpu.core_<n>.load_percent` (Windows)                                                                                                                                                                   | `/proc/loadavg` / hardware-monitor `Load` sensors                    |
| CPU topology        | `cpu.physical_cores`, `cpu.logical_threads`, `cpu.performance_cores`, `cpu.efficient_cores`, `cpu.low_power_efficient_cores`                                                                                                                              | `/proc/cpuinfo` / CIM                                                |
| CPU temperature     | `cpu.package_temp_c`, `cpu.core_<n>.temp_c`, `cpu.p_core_<n>.temp_c`, `cpu.e_core_<n>.temp_c`                                                                                                                                                             | hwmon coretemp / LibreHardwareMonitor·OpenHardwareMonitor            |
| Thermal zones       | `thermal.<sensor>.temp_c`, `thermal.windows_zone_<n>.temp_c`                                                                                                                                                                                              | sysfs thermal / ACPI & performance counters                          |
| NVMe temp & SMART   | `nvme.temp_c`, `nvme.smart_passed`, `nvme.critical_warning`, `nvme.available_spare_percent`, `nvme.percentage_used_percent`, `nvme.media_errors`, `nvme.power_on_hours`, `nvme.unsafe_shutdowns`, `nvme.error_log_entries` + per-device `nvme.<device>.*` | hwmon, sysfs, `smartctl --json` / reliability counters, smartctl     |
| NVMe capacity & I/O | `nvme.capacity_bytes`, `nvme.read_bytes_per_sec`, `nvme.write_bytes_per_sec` + per-device                                                                                                                                                                 | sysfs block (delta between samples) / performance counters           |
| Wi-Fi               | `wifi.signal_dbm`, `wifi.rx_bitrate_mbps`, `wifi.tx_bitrate_mbps`, `wifi.link_bitrate_mbps` + per-interface                                                                                                                                               | `/proc/net/wireless`, `iw`, `iwconfig` / `netsh`, WMI                |
| Memory, disk, power | `memory.used_percent`, `disk.root_used_percent`, `battery.capacity_percent`, `battery.ac_online`                                                                                                                                                          | procfs, sysfs / CIM                                                  |
| Fans                | `fan.rpm`, `fan.<sensor>.rpm`                                                                                                                                                                                                                             | hwmon (every readable fan) / hardware-monitor sensors                |
| Events              | thermal, storage, power, graphics, memory, network, reboot, update                                                                                                                                                                                        | kern.log, journalctl, etc. / Windows Event Log (System, Application) |

Core numbers follow the sensor/core ids the OS exposes; missing numbers are
never invented. Wi-Fi bitrate is the AP link bitrate, not an internet speed
test. NVMe read/write rates need two samples, so the first sample can be
empty.

If Windows shows `cpu.core_<n>.load_percent` but no `cpu.*.temp_c`, that is
not a UI bug — the hardware-monitor `Temperature` sensors are not visible to
the collector. See the [User Manual](USER_MANUAL.md) for the diagnosis steps.

## Collector CLI

```bash
quipu-collector --dry-run                          # print JSON, send nothing
quipu-collector --server-url URL --token TOKEN     # collect and send once
quipu-collector --dry-run --interval 60 --iterations 3   # three 60s samples
```

| Option                              | Default                                | Purpose                                           |
| ----------------------------------- | -------------------------------------- | ------------------------------------------------- |
| `--server-url`                      | (none)                                 | omit to print JSON to stdout                      |
| `--token`                           | (none)                                 | required with `--server-url` (except `--dry-run`) |
| `--device-id` / `--device-alias`    | generated / (none)                     | stable unique ID / friendly UI name               |
| `--interval` / `--iterations`       | (none)                                 | repeat interval in seconds / run count            |
| `--offline-buffer`                  | off                                    | spool failed sends locally, flush on next success |
| `--spool-dir`                       | `~/.local/state/quipu/collector-spool` | spool location                                    |
| `--spool-max-batches`               | `288`                                  | spool retention (~one day at 5-minute batches)    |
| `--state-dir`                       | `~/.local/state/quipu/collector-state` | state for NVMe rate deltas                        |
| `--flush-limit` / `--retry-backoff` | (none) / `0`                           | flush cap / sleep after buffered failure          |

## Server API Summary

All routes live under `/api`. The auth header is `X-Quipu-Agent-Token`.

| Route                                                                             | Purpose                                              | Auth         |
| --------------------------------------------------------------------------------- | ---------------------------------------------------- | ------------ |
| `GET /api/health`                                                                 | liveness check                                       | none         |
| `POST /api/ingest/batches`                                                        | ingest an observation batch (201 new, 200 duplicate) | ingest token |
| `GET /api/fleet/overview`                                                         | fleet device summary                                 | none         |
| `GET /api/investigations/queue`                                                   | prioritized investigation queue                      | none         |
| `GET /api/investigations/{id}`                                                    | investigation detail incl. interventions             | none         |
| `GET·POST /api/investigations/{id}/notes`                                         | read/write handoff notes                             | none         |
| `POST /api/investigations/{id}/interventions`                                     | record an intervention                               | none         |
| `GET /api/patterns/overview`                                                      | repeated-signal patterns                             | none         |
| `POST·GET /api/enrollment/tokens`, `POST .../{id}/rotate`, `POST .../{id}/revoke` | issue/list/rotate/revoke per-device tokens           | dev token    |
| `GET /api/admin/schema`                                                           | schema version and tables                            | dev token    |

## Tokens And Auth

- The development token defaults to `dev-token` and can be changed with the
  `QUIPU_DEV_AGENT_TOKEN` environment variable.
- Ingest accepts the dev token or an active enrollment token issued for that
  `device_id`. Per-device tokens are stored as SHA-256 hashes only.

```bash
curl -sS -X POST http://127.0.0.1:8000/api/enrollment/tokens \
  -H "Content-Type: application/json" \
  -H "X-Quipu-Agent-Token: dev-token" \
  -d '{"device_id":"office-gram","label":"Office Gram collector"}'
```

Put the returned `token` into that machine's collector `--token`.

## Environment Variables

| Variable                                                                                                                                                                                                             | Component              | Default                 | Purpose                                                   |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | ----------------------- | --------------------------------------------------------- |
| `QUIPU_DATABASE_PATH`                                                                                                                                                                                                | server                 | `data/quipu.sqlite3`    | SQLite path                                               |
| `QUIPU_DEV_AGENT_TOKEN`                                                                                                                                                                                              | server                 | `dev-token`             | development/admin token                                   |
| `QUIPU_SERVER_URL`, `QUIPU_AGENT_TOKEN`, `QUIPU_COLLECTOR_DEVICE_ID`, `QUIPU_COLLECTOR_DEVICE_ALIAS`, `QUIPU_SPOOL_DIR`, `QUIPU_SPOOL_MAX_BATCHES`, `QUIPU_STATE_DIR`, `QUIPU_COLLECTOR_BIN`, `QUIPU_COLLECTOR_ROOT` | collector ops wrappers | —                       | translated into CLI flags by the systemd/Windows wrappers |
| `QUIPU_COLLECTOR_INTERVAL`, `QUIPU_COLLECTOR_ENV`                                                                                                                                                                    | Windows wrapper        | `300` / —               | collection interval (seconds) / config file path          |
| `QUIPU_SMARTCTL_BIN`                                                                                                                                                                                                 | collector              | auto-detected           | explicit smartctl path                                    |
| `QUIPU_LIBRE_HARDWARE_MONITOR_DLL`                                                                                                                                                                                   | collector (Windows)    | auto-detected           | explicit LibreHardwareMonitorLib.dll path                 |
| `VITE_API_BASE_URL`                                                                                                                                                                                                  | web                    | `http://127.0.0.1:8000` | API base URL for the web UI                               |

## Operational Install

On Linux, a systemd timer runs the collector once every five minutes:

```bash
scripts/install-collector-systemd.sh --dry-run   # preview
sudo scripts/install-collector-systemd.sh --no-enable
sudo systemctl enable --now quipu-collector.timer
```

Configuration lives in `/etc/quipu/collector.env`. The full operational
procedures — Windows scheduled-task install, environment files, uninstall —
are in the [User Manual](USER_MANUAL.md).

## Architecture

```text
Linux collector / Windows collector / compatible external collector
      |
      v
FastAPI ingest API  (X-Quipu-Agent-Token)
      |
      v
SQLite WAL store
      |
      v
Rule-based analysis engine
      |
      v
React investigation UI
```

## Verification

CI runs the same checks on Python 3.12 and Node 24.

```bash
cd apps/server && . .venv/bin/activate && pytest -v
cd apps/collector && . .venv/bin/activate && pytest -v
cd apps/web && npm test && npm run build
```

## Repository Layout

```text
apps/
  collector/     Read-only collector CLI (Linux/Windows) + systemd/scheduled-task ops scripts
  server/        FastAPI API, SQLite persistence, rule-based analysis, manual seed CLI
  web/           Vite React investigation UI
data/            Local SQLite DB (used by dev-server.sh)
docs/
  superpowers/   Product decisions, dashboard, roadmap, ship checklist
fixtures/
  ingest/        Deterministic sample batches (team-sample.json)
scripts/
  dev-server.sh                          Local API server (0.0.0.0:8000)
  install-collector-systemd.sh           Linux collector install/uninstall
  install-collector-scheduled-task.ps1   Windows collector install/uninstall
```

## Docs

- [User Manual](USER_MANUAL.md) — setup, operations, reading the UI, troubleshooting
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Project dashboard](docs/superpowers/DASHBOARD.md)
- [Roadmap](docs/superpowers/ROADMAP.md)
- [Ship checklist](docs/superpowers/SHIP_CHECKLIST.md)

## Boundaries

Not included in this release:

- remote repair command execution
- production deployment
- package publishing
- AI-only conclusions
- raw log warehouse behavior

Quipu defaults to local-first, read-only, evidence-based operation.
