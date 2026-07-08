# Quipu

<p align="center">
  <img alt="CI" src="https://github.com/chquandogong/Quipu/actions/workflows/ci.yml/badge.svg">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.12.0-2f6f7e">
  <img alt="Status" src="https://img.shields.io/badge/status-local--first%20workstation%20health-5b6b73">
  <img alt="License" src="https://img.shields.io/badge/license-not%20selected-lightgrey">
</p>

<p align="center">
  <strong>Linux workstation health investigation</strong><br>
  Quipu turns read-only Linux signals into evidence, actions, verification, and team handoff.
</p>

<p align="center">
  <a href="README.md">한국어</a> | English | <a href="README.zh-CN.md">简体中文</a>
</p>

---

## What It Is

Quipu is a local-first tool for investigating Linux laptop and workstation
health. It collects thermal, load, NVMe, Wi-Fi, memory, disk, battery, fan,
kernel, graphics, reboot, and update signals, then presents them as a workflow:

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

The product is not a remote repair tool. The collector is read-only and the
server uses deterministic rule-based analysis.

## v0.12.0 Highlights

- Windows collector operations are now packaged beside the Ubuntu systemd
  collector: environment file, startup wrapper, scheduled-task install script,
  and uninstall script.
- The Windows startup wrapper runs hidden at user logon, prevents duplicate
  collector loops, keeps the offline buffer enabled, and posts every five
  minutes by default.
- Version metadata across the collector, server, schema, and web app is now
  `0.12.0`.

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

## Connect Another Laptop

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
  -ServerUrl http://<server-ip>:8000 `
  -Token dev-token `
  -DeviceId windows `
  -DeviceAlias "Windows"
```

The scheduled task starts `apps/collector/ops/windows/start-quipu-collector.ps1`
hidden in the background. It keeps the offline buffer enabled and sends a batch
every five minutes.

## Main Surfaces

- Command Center: selected case, priority, risk, next action.
- Problem Guide: what is wrong, what evidence matters, what to do next.
- Telemetry Brief: CPU, Load, NVMe, Wi-Fi representative values.
- Metric Ledger: detailed core/load/device/interface chips and help tooltips.
- Telemetry Matrix: coverage across CPU profile, memory, disk, fan, NVMe
  health/capacity/I/O, power, Wi-Fi link, network, thermal, kernel, and
  freshness.
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
