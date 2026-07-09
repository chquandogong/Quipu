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

Status: operations-resilience slice implemented.

Goal: make the product feel like a guided diagnostic workflow.

Implemented:

- Device-first `Devices` list.
- `Device Issues` scoped to the selected device.
- Incident detail surface.
- Evidence timeline.
- Hypothesis board.
- Suggested actions.
- Verification summary.
- Report draft.
- Investigation Lens focus board.
- Command Center first viewport with inspect/why/action/proof answers.
- Problem Guide that highlights what is wrong, first evidence, and the next
  action before raw metrics.
- High-contrast dark command theme.
- Telemetry Brief that collapses CPU, Load, NVMe, and Wi-Fi into one compact
  line.
- Workflow Rail that replaces the seven large DTIHAVR boxes with current stage,
  next stage, and next action.
- Compact `D T I H A V R` stage initials with hover/focus definitions for
  Detect through Report.
- Fleet Brief that collapses Total, Critical, Warning, and Open issues into the same
  compact density as Telemetry Brief.
- Source-linked risk labels so `Warning` points to the device/category and
  selected investigation instead of standing alone.
- Consistent caution color mapping across priority and risk chips.
- Scoped Telemetry Matrix event counts such as `kernel events` and `thermal
  events` instead of unqualified `warnings`.
- Metric Ledger that keeps core metric explanations in one dense row-based box.
- Telemetry Matrix for Memory, Fan RPM, NVMe Health, Network Events,
  Reconnect History, Thermal Throttling, Disk Health, Battery Power, Kernel
  Warnings, and Agent Freshness.
- Metric help tooltips for definition, time window, reading guidance, and next
  check.
- CTA routing to evidence, action recording, and verification.
- Hover/focus expansion for detailed panels.
- Removed creator/reference image drawer from the working UI.
- Visible Made by, About, and Version metadata chips.
- Operations Rail for agent freshness, offline buffering, enrollment guard,
  and pattern radar.
- Team Handoff notes attached to each investigation item.
- Pattern Explorer grouped by category, component, model, and kernel.
- Healthy device overview detail that still shows telemetry, verification
  status, and report text even when no active investigation item exists.

Remaining:

- Assignee, owner, and role-aware workflow states.

## Phase 3: Native Read-Only Agent

Status: systemd operations, offline-buffer kit, and best-effort Windows
telemetry implemented; connected Windows laptop rollout in progress.

Goal: collect real workstation signals safely. The bundled collector focuses on
Linux, and compatible external collectors can post the same ingest API contract
for other operating systems.

Implemented:

- One-shot Python collector.
- Load and memory pressure, including Linux 1/5/15-minute load windows.
- CPU/package thermal metrics when exposed by sysfs.
- Per-core CPU temperature metrics when exposed by hwmon CPU sensors.
- Representative and per-device NVMe temperature when exposed by hwmon.
- Representative and per-interface Wi-Fi signal level when exposed by `/proc/net/wireless`.
- Best-effort kernel thermal throttling event summaries.
- Best-effort NetworkManager reconnect/disconnect event summaries.
- Root filesystem usage.
- Battery capacity and AC online state from `/sys/class/power_supply`.
- Best-effort kernel storage and power warning event summaries.
- Fan RPM where available through hwmon.
- NVMe SMART-lite health where available through sysfs-style files.
- Optional POST to the ingest API.
- CLI dry-run mode.
- CLI interval and iteration controls for supervised repeated collection.
- Structured JSON error output for collection and send failures.
- systemd oneshot service and five-minute timer files.
- Environment file example and wrapper for safe collector invocation.
- Dry-run install and uninstall scripts.
- Offline local ring buffer for temporary server or network outage.
- Flush-before-current-send path with bounded spool depth.
- UI metric breakdown rows for CPU cores, load windows, NVMe devices, and Wi-Fi interfaces.
- Telemetry Matrix coverage wording that separates observed-signal coverage from risk status.
- Best-effort graphics/session, memory, update, and reboot markers.
- Preservation of stable device alias and CPU model when later batches omit
  those optional metadata fields.
- Windows best-effort metric collection through PowerShell/CIM, netsh, and
  Get-NetAdapter for CPU core/thread counts, memory, battery, Wi-Fi link,
  NVMe capacity, and ACPI thermal zones when exposed by Windows.
- Windows compatibility patch for longer PowerShell/CIM collection timeout,
  localized `netsh` Wi-Fi output, `Get-PhysicalDisk` NVMe fallback, and model
  preservation when later batches omit it.
- Private LAN UI/API access from Vite origins on ports 5173 and 5174.

Remaining:

- Install v0.13.1 on the currently connected Windows laptop and restart the
  scheduled task so partial Windows telemetry is replaced by the patched metric
  set.
- CPU/core/package thermals with richer sensor naming.
- Richer multi-fan naming.
- Deeper SMART/NVMe health where available without external dependencies.

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

Status: first slice implemented.

Goal: identify repeated signatures across a fleet.

Implemented:

- API grouping repeated events by category.
- API grouping repeated events by component signature.
- API grouping repeated events by model.
- API grouping repeated events by kernel.
- React Pattern Explorer compact panel.

Remaining:

- Better GPU driver and Wi-Fi device extraction where logs expose driver names.
- Same SSD or Wi-Fi hardware identity when the collector can expose it without
  elevated privileges.
- Same workload window.
- Same physical setup.

## Phase 6: Hardening

Status: first hardening slice implemented; product hardening roadmap drafted in
`docs/superpowers/PRODUCT_HARDENING.md`.

Goal: make Quipu trustworthy for real team use.

Implemented:

- Device enrollment API.
- Device-bound collector tokens.
- Token rotation.
- Token revocation.
- Schema version endpoint.

Remaining:

- Redaction controls.
- Retention policy.
- Role-aware UI.
- Local image asset strategy or cache for public reference visuals.
- Backup and restore guide.
- Optional Postgres adapter.
