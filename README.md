# Quipu

Team-first workstation health investigator for Linux laptops and developer
workstations.

Quipu is not just a system monitor. It is a problem-solving workflow for teams
that need to detect workstation instability, narrow likely causes, act on
evidence, and verify whether the fix worked.

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

## Status

Quipu is an early local-first prototype.

Implemented:

- FastAPI ingest API.
- SQLite persistence.
- Rule-based fleet overview.
- Deterministic three-device sample data.
- Vite React team dashboard.

Next product direction:

- Replace the generic fleet-first UI with an investigation-first workflow.
- Make the first screen an Investigation Queue.
- Add incident timeline, hypothesis board, intervention tracking, and
  before/after verification.

## Why Quipu Exists

Developer machines fail in ways that are hard to diagnose from one metric:
thermal pressure, graphics/session errors, storage warnings, Wi-Fi instability,
updates, reboots, and physical setup changes can all overlap.

Quipu turns sensor readings, system logs, and user interventions from multiple
machines into investigation records:

- Current state.
- Incident timeline.
- Likely causes.
- Supporting and contradicting evidence.
- Suggested next checks.
- Actions taken.
- Before/after verification.
- Team-readable report.

## Core Product Principle

Quipu optimizes for the problem-solving process, not for metric density.

The product should answer:

- Which machine or incident should the team inspect first?
- Why is it risky right now?
- What are the top cause hypotheses?
- What evidence supports or weakens each hypothesis?
- What should a human check next?
- What intervention was tried?
- Did the intervention improve the situation?
- Is the same pattern recurring across other machines?

## Differentiation

Quipu should compete on investigation quality rather than chart quantity.

1. **Investigation first, metrics second.**
   Quipu starts from a machine, incident, or team problem, then exposes the
   metrics needed to explain it.

2. **Evidence-linked conclusions.**
   Every finding should show supporting evidence, contradicting evidence,
   confidence level, and raw source reference.

3. **Team-level pattern memory.**
   Quipu should identify repeated issues across models, kernels, GPU drivers,
   SSDs, Wi-Fi devices, workloads, and physical setups.

4. **Intervention verification.**
   Quipu should track actions like lifting a laptop, changing power profiles, or
   updating drivers, then compare before/after health windows.

5. **Read-only, local-first trust.**
   The first product should be safe to run on team machines: read-only agents,
   self-hosted storage, minimal log excerpts, and no remote repair actions.

## DTIHAVR Workflow

The primary UI/UX flow is DTIHAVR:

| Stage | Purpose |
| --- | --- |
| Detect | Identify machines, incidents, and patterns that need attention. |
| Triage | Rank urgency and route the issue to the right investigation. |
| Investigate | Inspect timeline, sensors, logs, updates, and user notes. |
| Hypothesize | List likely causes with evidence and counter-evidence. |
| Act | Record a human-approved intervention or next check. |
| Verify | Compare before/after windows to decide whether the action helped. |
| Report | Produce a concise, evidence-linked summary for the team. |

## Investigation Queue

The first screen should become an investigation queue, not a generic dashboard.

Example queue items:

| Priority | Item | Why now | Next step |
| --- | --- | --- | --- |
| High | `build-xps` thermal risk | CPU package at 86.4C with thermal warning during compile workload | Compare cooling and workload windows |
| Medium | `dev-p1` unclean shutdown | Previous boot ended without clean shutdown marker | Inspect pre-reboot graphics, thermal, and storage evidence |
| Medium | `ops-framework` graphics warning | Kernel graphics warning before visible stutter | Check i915/session timeline and repeated signatures |

Each queue item should open into an incident detail view with timeline, evidence,
hypotheses, actions, verification, and report sections.

## Architecture

```text
Quipu Agent/Future Collector
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

- Self-hosted by default.
- Read-only collection.
- No remote command execution.
- No automatic repair.
- No cloud dependency.
- No full raw-log warehouse.

## Local Development

Run the server:

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

Useful checks:

```bash
cd apps/server
. .venv/bin/activate
pytest -v

cd ../web
npm test
npm run build
```

## Repository Layout

```text
apps/
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
- [Team health investigator design](docs/superpowers/specs/2026-07-07-team-health-investigator-design.md)
- [Problem-solving flow UX design](docs/superpowers/specs/2026-07-07-problem-solving-flow-ux-design.md)
- [First implementation plan](docs/superpowers/plans/2026-07-07-team-ingest-vertical-slice.md)
- [Roadmap](docs/superpowers/ROADMAP.md)

## License

No license has been selected yet. Do not assume redistribution rights until a
license is explicitly added.
