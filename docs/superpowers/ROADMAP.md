# Quipu Roadmap

> Status: draft
> Date: 2026-07-07
> Owner: chquan

## North Star

Quipu should become the problem-solving layer for team workstation health:

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

## Phase 1: First Vertical Slice

Status: implemented.

- FastAPI ingest API.
- SQLite persistence.
- Rule-based fleet overview.
- Deterministic three-device fixture.
- Vite React dashboard.

## Phase 2: Investigation-First UI

Status: first slice implemented.

Goal: make the product feel like a guided diagnostic workflow.

Implemented:

- Investigation Queue.
- Incident detail surface.
- Evidence timeline.
- Hypothesis board.
- Suggested actions.
- Verification summary.
- Report draft.
- Investigation Lens focus board.
- Command Center first viewport with inspect/why/action/proof answers.
- High-contrast dark command theme.
- Core signal console for CPU, Load, NVMe, and Wi-Fi.
- Telemetry Matrix for Memory, Fan RPM, NVMe Health, Network Events,
  Reconnect History, Thermal Throttling, Disk Health, Battery Power, Kernel
  Warnings, and Agent Freshness.
- Metric help tooltips for definition, time window, reading guidance, and next
  check.
- CTA routing to evidence, action recording, and verification.
- Hover/focus expansion for detailed panels.
- Removed creator/reference image drawer from the working UI.
- Visible Made by, About, and Version metadata chips.

Remaining:

- Assignee, owner, and team handoff states.

## Phase 3: Native Read-Only Agent

Status: one-shot collector foundation implemented.

Goal: collect real Linux workstation signals safely.

Implemented:

- One-shot Python collector.
- Load and memory pressure.
- CPU/package thermal metrics when exposed by sysfs.
- NVMe temperature when exposed by hwmon.
- Wi-Fi signal level when exposed by `/proc/net/wireless`.
- Best-effort kernel thermal throttling event summaries.
- Best-effort NetworkManager reconnect/disconnect event summaries.
- Root filesystem usage.
- Battery capacity and AC online state from `/sys/class/power_supply`.
- Best-effort kernel storage and power warning event summaries.
- Fan RPM where available through hwmon.
- NVMe SMART-lite health where available through sysfs-style files.
- Optional POST to the ingest API.

Remaining:

- CPU/core/package thermals with richer sensor naming.
- Richer multi-fan naming and fan-context analysis.
- Deeper SMART/NVMe health where available without external dependencies.
- Kernel, graphics/session, update, reboot markers.
- Local ring buffer for offline periods.

## Phase 4: Intervention Verification

Status: deterministic verification slice implemented.

Goal: prove whether a human action helped.

Implemented:

- Persistent action history.
- Investigation detail includes recorded interventions.
- UI form for recording human actions.
- 30-minute before/after metric and event windows.
- CPU package temperature comparison.
- Load context comparison.
- Warning recurrence comparison.
- Verification result: helped, unclear, worse, or insufficient data.

Remaining:

- Configurable verification windows.
- Materialized historical verification audit trail.
- Longer-term baseline and recurrence analytics.

## Phase 5: Team Pattern Explorer

Goal: identify repeated signatures across a fleet.

- Same model.
- Same kernel.
- Same GPU driver.
- Same SSD or Wi-Fi device.
- Same workload window.
- Same physical setup.

## Phase 6: Hardening

Goal: make Quipu trustworthy for real team use.

- Device enrollment.
- Token rotation.
- Redaction controls.
- Retention policy.
- Role-aware UI.
- Local image asset strategy or cache for public reference visuals.
- Backup and restore guide.
- Optional Postgres adapter.
