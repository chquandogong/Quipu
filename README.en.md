# Quipu

<p align="center">
  <img alt="CI" src="https://github.com/chquandogong/Quipu/actions/workflows/ci.yml/badge.svg">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.3.0-2f6f7e">
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

Quipu does not open every log and metric at once. The primary surface keeps
three questions visible:

- What should we inspect first?
- What action should we record now?
- Did that action actually help?

Detailed evidence stays compact until hover, keyboard focus, or button-driven
navigation expands it. The main CTAs are fixed as `Review evidence`,
`Record action`, and `Verify result` so the next move stays obvious.

Public Dogu Robotics, Dogu X, and Physical AI references plus creator details
sit in a collapsed secondary drawer: useful context without interrupting the
investigation workflow.

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
- Read-only one-shot Linux collector
- Intervention records for investigation items
- Before/after verification results for interventions
- Vite React investigation-first UI
- Summary-first focus board with hover/focus expansion panels
- Collapsed creator and Physical AI reference drawer
- GitHub Actions CI for server, collector, and web checks

Next direction:

- A supervised local-agent version of the collector
- Team pattern exploration by model, kernel, driver, storage, Wi-Fi, workload,
  and physical setup
- Role-aware team workflows, redaction controls, and retention policy

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

The collector is a one-shot Linux signal reader. It does not require root, does
not execute repair commands, and does not upload full raw logs.

Print a local observation batch:

```bash
cd apps/collector
python -m venv .venv
. .venv/bin/activate
pip install -e .
quipu-collector
```

Send one batch to a local Quipu server:

```bash
quipu-collector --server-url http://127.0.0.1:8000 --token dev-local-token
```

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
  collector/     Read-only one-shot Linux observation collector
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
