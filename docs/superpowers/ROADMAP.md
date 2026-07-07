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

Remaining:

- Persistent action recording.
- Before/after verification windows.
- Assignee, owner, and team handoff states.

## Phase 3: Native Read-Only Agent

Goal: collect real Linux workstation signals safely.

- CPU/core/package thermals.
- Load and memory pressure.
- NVMe and disk health where available.
- Wi-Fi state and reconnects.
- Thermal throttling events.
- Kernel, graphics/session, storage, update, reboot markers.
- Local ring buffer for offline periods.

## Phase 4: Intervention Verification

Goal: prove whether a human action helped.

- Before/after comparison windows.
- Load-adjusted thermal comparison.
- Event recurrence comparison.
- Action history.
- Verification result: helped, unclear, or worse.

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
- Backup and restore guide.
- Optional Postgres adapter.
