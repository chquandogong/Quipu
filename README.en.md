# Quipu

<p align="center">
  <img alt="CI" src="https://github.com/chquandogong/Quipu/actions/workflows/ci.yml/badge.svg">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.9.0-2f6f7e">
  <img alt="Status" src="https://img.shields.io/badge/status-local--first%20prototype-5b6b73">
  <img alt="License" src="https://img.shields.io/badge/license-not%20selected-lightgrey">
</p>

<p align="center">
  <strong>Team workstation health investigation for Linux laptops and developer machines.</strong><br>
  Quipu is not a metrics dashboard. It is a local-first tool for the problem-solving workflow.
</p>

<p align="center">
  <a href="README.md">한국어</a> | English | <a href="README.zh-CN.md">简体中文</a>
</p>

---

## At A Glance

Quipu helps teams investigate thermal pressure, reboots, graphics/session
errors, storage warnings, Wi-Fi instability, and physical setup changes across
multiple Linux laptops and developer workstations.

The product is designed to answer practical investigation questions:

- Which machine should the team inspect first?
- Why is it risky right now?
- What are the strongest cause hypotheses?
- Which evidence supports or weakens each hypothesis?
- What should a human check or change next?
- Did the intervention actually improve health?
- Is the same pattern recurring across other machines?

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

## UI/UX Principle

Quipu does not open every log and metric at once. After comparing current
dashboard, design-system, and progressive-disclosure patterns, Quipu uses a
dark `Command Center`. The first visual anchor is not a wide metric card; it is
a compact `Problem Guide` that answers what is wrong, which evidence to inspect
first, and what to do next. CPU/Load/NVMe/Wi-Fi collapse into one
`Telemetry Brief` as supporting signals. DTIHAVR is not shown as seven large
fixed boxes; it becomes a thin `Workflow Rail` focused on the current stage,
next stage, and next action. The `D T I H A V R` initials remain visible as a
compact stage rail, with hover/focus tooltips for Detect through Report.
Fleet Total/Critical/Warning/Queue also moves into a compact `Fleet Brief`
instead of a large number block.

- What should we inspect now?
- Why does it matter?
- What should we do next?
- What proof is needed before calling it fixed?

Detailed evidence stays compact until hover, keyboard focus, or button-driven
navigation expands it. The main CTAs stay fixed as `Review evidence`,
`Record action`, and `Verify result`.

Short status words such as `Medium`, `Warning`, and `Triage` remain compact
status chips instead of permanent explanatory text. Hover and keyboard focus
reveal what each chip means, so new operators can interpret priority, risk,
and the DTIHAVR workflow stage with the same rubric.

Key metrics such as CPU package temperature, Load Average, and NVMe temperature
do not stand alone as unexplained numbers. The detailed `Metric Ledger` keeps
core metrics in one row-based box, and each help button explains the Korean
meaning together with the English technical term, time window, reading guidance,
and next check. For example, Load is explicitly described as the Linux
1-minute load average, not instant CPU utilization.

CPU, Load, and NVMe are useful for thermal triage, but they are not enough for
team-level root-cause work. Quipu now promotes Wi-Fi signal into the core
signals and uses a `Telemetry Matrix` for Memory, Fan RPM, NVMe Health, Disk
Health, Battery Power, Network Events, Reconnect History, Thermal Throttling,
Kernel Warnings, and Agent Freshness. Quipu now raises hot-CPU plus low-fan-RPM
as a cooling-response finding and groups component signatures such as
`gpu:i915`, `wifi:wlp0s20f3`, and `nvme:nvme0n1` in Pattern Explorer. Deeper
SMART/NVMe health can expand through the same rule-based structure later.

v0.9.0 adds an `Operations Rail`, `Team Handoff`, and `Pattern Explorer`.
The operations rail surfaces agent freshness, offline buffering, enrollment
guardrails, and pattern radar; handoff notes attach team context to each
investigation; pattern exploration groups repeated signals by category,
component, model, and kernel.

Creator and version information stays as compact header metadata. The large
creator/reference image drawer was removed because it did not help the
investigation decision.

## Why Quipu Exists

Developer-machine failures rarely come from one isolated metric. CPU
temperature, kernel logs, GPU driver warnings, SSD health, Wi-Fi quality,
updates, boot history, workload, and physical desk setup can overlap.

Quipu turns sensor values, system events, and human interventions into
investigation records:

- Current state
- Incident timeline
- Cause hypotheses
- Supporting and contradicting evidence
- Next checks
- Actions taken
- Before/after verification
- Team-readable report

## Differentiation

1. **Investigation first, metrics second**
   Quipu starts from a machine, incident, or team problem, then exposes the
   metrics needed to explain it.

2. **Evidence-linked conclusions**
   Every finding should show supporting evidence, contradicting evidence,
   confidence, and source references.

3. **Team-level pattern memory**
   Quipu is designed to find recurring issues across models, kernels, GPU
   drivers, SSDs, Wi-Fi devices, workloads, and physical setups.

4. **Intervention verification**
   Quipu tracks actions such as lifting a laptop, changing a power profile, or
   updating a driver, then compares before/after health windows.

5. **Read-only, local-first trust**
   The first product must be safe to run on team machines: read-only agents,
   self-hosted storage, minimal log excerpts, and no remote repair actions.

## Current Status

Quipu is an early local-first prototype.

Implemented:

- FastAPI ingest API
- SQLite WAL persistence
- Rule-based fleet overview
- Deterministic sample fleet data
- Investigation queue/detail API
- Read-only Linux collector
- Best-effort collector summaries for kernel thermal throttling and
  NetworkManager reconnect events
- Collector metrics for root filesystem usage, battery capacity, and AC online
  state
- Best-effort collector summaries for kernel storage and power warning events
- Collector metrics for hwmon Fan RPM and sysfs NVMe SMART-lite health
- Lightweight collector operation loop with dry-run, interval, and iteration
  controls
- Offline local ring buffer with spool flushing, flush limits, and retry
  backoff
- Collector systemd service/timer, environment example, wrapper, and dry-run
  install/uninstall scripts
- Collector marker summaries for graphics, memory, update, and reboot events
- Device enrollment, per-device ingest tokens, token rotation, and token
  revocation APIs
- Schema version endpoint and team handoff notes per investigation
- Pattern Explorer API grouped by category, component, model, and kernel
- Intervention records for investigation items
- Before/after verification results for interventions
- Vite React investigation-first UI
- High-contrast dark Command Center, Problem Guide, dense signal console, and
  hover/focus expansion panels
- Per-metric Korean explanation, English technical term, time window, reading
  guidance, and next-check tooltip for CPU, Load, NVMe, and Wi-Fi
- Telemetry Matrix for Memory, Fan RPM, NVMe Health, Disk Health, Battery Power,
  Network Events, Reconnect History, Thermal Throttling, Kernel Warnings, and
  Agent Freshness
- Operations Rail, Team Handoff, and Pattern Explorer UI
- Compact Made by, About, and Version metadata chips
- Product hardening roadmap for collector rollout, retention, backup/restore,
  RBAC, package publishing, production deployment, Postgres, analytics, and AI
  layer
- GitHub Actions CI for server, collector, and web checks

Next direction:

- Role-aware team workflows, redaction controls, and retention policy
- Postgres adapter, backup/restore, and longer-term baseline analytics
- Package publishing and production deployment preparation

## Quick Start

Run the seeded local API server:

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

## Collector

The collector reads Linux signals without root. It runs once by default, and
`--interval` turns it into a lightweight collection loop. It does not execute
repair commands and does not upload full raw logs.

Current key signals:

- `cpu.load_1m`: Linux 1-minute load average
- `memory.used_percent`: memory usage derived from `/proc/meminfo`
- `disk.root_used_percent`: root filesystem usage
- `cpu.package_temp_c`, `thermal.*.temp_c`: sysfs thermal zone temperatures
- `nvme.temp_c`: NVMe temperature exposed through hwmon
- `fan.rpm`: first fan RPM exposed through hwmon
- `nvme.critical_warning`, `nvme.available_spare_percent`,
  `nvme.percentage_used_percent`, `nvme.media_errors`: NVMe SMART-lite health
  exposed through sysfs-style files
- `wifi.signal_dbm`: Wi-Fi signal from `/proc/net/wireless`
- `battery.capacity_percent`, `battery.ac_online`: battery and AC state from
  `/sys/class/power_supply`
- Kernel thermal, storage, power, graphics, and memory warning summaries,
  update/reboot markers, plus NetworkManager reconnect summaries

Print a local observation batch:

```bash
cd apps/collector
python -m venv .venv
. .venv/bin/activate
pip install -e .
quipu-collector --dry-run
```

Send one batch to a local Quipu server:

```bash
quipu-collector --server-url http://127.0.0.1:8000 --token dev-token
```

Buffer batches locally when the server or network is temporarily unavailable:

```bash
quipu-collector \
  --server-url http://127.0.0.1:8000 \
  --token "$QUIPU_AGENT_TOKEN" \
  --offline-buffer \
  --spool-dir ~/.local/state/quipu/collector-spool
```

Create a per-device collector token with the development/admin token, then use
the returned token only for that device's ingest requests:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/enrollment/tokens \
  -H "Content-Type: application/json" \
  -H "X-Quipu-Agent-Token: dev-token" \
  -d '{"device_id":"thinkpad-p1","label":"ThinkPad P1 collector"}'
```

Run a repeated smoke test:

```bash
quipu-collector --dry-run --interval 60 --iterations 3
```

Run a simple supervised loop:

```bash
quipu-collector --server-url http://127.0.0.1:8000 --token dev-token --interval 300
```

Use a systemd timer for fixed five-minute collection. The example below is for
this development machine path (`/home/chquan/Quipu`) and the local API
(`http://127.0.0.1:8000`). On another team device, change the repository path,
device id, and token.

Prepare the collector executable:

```bash
cd /home/chquan/Quipu/apps/collector
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

Preview systemd timer installation:

```bash
cd /home/chquan/Quipu
scripts/install-collector-systemd.sh --dry-run
```

Install for real:

```bash
sudo scripts/install-collector-systemd.sh --no-enable
```

Configure the collector environment file:

```bash
sudo tee /etc/quipu/collector.env >/dev/null <<EOF
QUIPU_SERVER_URL=http://127.0.0.1:8000
QUIPU_AGENT_TOKEN=dev-token
QUIPU_COLLECTOR_ROOT=/
QUIPU_COLLECTOR_DEVICE_ID=local-computer
QUIPU_COLLECTOR_BIN=/home/chquan/Quipu/apps/collector/.venv/bin/quipu-collector
QUIPU_SPOOL_DIR=/var/lib/quipu/collector-spool
QUIPU_SPOOL_MAX_BATCHES=288
EOF
sudo chmod 600 /etc/quipu/collector.env
```

Run one manual service execution to check permissions, paths, and server
connectivity:

```bash
sudo systemctl start quipu-collector.service
systemctl status quipu-collector.service --no-pager
journalctl -u quipu-collector.service -n 80 --no-pager
```

Enable five-minute automatic collection:

```bash
sudo systemctl enable --now quipu-collector.timer
systemctl list-timers quipu-collector.timer
```

Disable it:

```bash
sudo systemctl disable --now quipu-collector.timer
```

Uninstall completely:

```bash
sudo scripts/uninstall-collector-systemd.sh
```

The installer assumes the `quipu-collector` executable is already installed on
the target machine. In production, use a per-device enrollment token instead of
`dev-token`. Package publishing and production deployment are not included yet.

## Architecture

```text
Linux collector
      |
      v
FastAPI ingest API
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

MVP boundaries:

- Self-hosted by default
- Read-only collection
- No remote command execution
- No automatic repair
- No cloud dependency
- No full raw-log warehouse

## Verification

Server:

```bash
cd apps/server
. .venv/bin/activate
pytest -v
```

Collector:

```bash
cd apps/collector
python -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
pytest -v
```

Web:

```bash
cd apps/web
npm test
npm run build
```

## Repository Layout

```text
apps/
  collector/     Read-only Linux observation collector
  server/        FastAPI API, SQLite persistence, rule-based analysis
  web/           Vite React UI
docs/
  superpowers/   Product decisions, specs, plans, dashboard
fixtures/
  ingest/        Deterministic sample health batches
scripts/
  dev-server.sh  Local seeded API server
```

## Key Documents

- [Project dashboard](docs/superpowers/DASHBOARD.md)
- [Decision log](docs/superpowers/DECISION_LOG.md)
- [Roadmap](docs/superpowers/ROADMAP.md)
- [Ship checklist](docs/superpowers/SHIP_CHECKLIST.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## Safety Boundaries

Current and near-future defaults:

- Read-only data collection
- Self-hosted storage
- Minimal log excerpts
- No remote command execution
- No automatic repair
- AI conclusions are not authoritative without evidence links

## License

No license has been selected yet. Do not assume redistribution rights until a
license is explicitly added.
