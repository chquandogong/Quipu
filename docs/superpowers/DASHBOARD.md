# Quipu Project Dashboard

> Status: v0.14.5 documentation release track for current Windows collector behavior
> Date: 2026-07-10
> Owner: chquan

## Current Decision

Quipu starts as a multi-device, team-oriented workstation health investigator,
not as a single-laptop utility. The bundled collector has the richest Linux
coverage and a best-effort Windows path; the ingest API also accepts compatible
collectors from other operating systems.

## Scope

- Initial users: one technical team.
- Initial fleet: 3-20 Linux laptops, Windows laptops, or developer workstations.
- Deployment: self-hosted team server on LAN or private network.
- Collection: lightweight read-only agent per machine. Linux uses procfs/sysfs;
  Windows uses the bundled best-effort PowerShell/CIM/netsh/Get-NetAdapter
  collection path when the OS exposes those signals. Compatible external
  collectors can also post the same ingest contract.
- Primary value: explain incidents and recurring patterns across devices.

## Current Wedge

The first valuable question is:

> Which machines are unstable, why, and what evidence supports the next action?

The second valuable question is:

> Did a physical or configuration intervention improve health over time?

## Work Board

| State | Item | Notes |
| --- | --- | --- |
| Done | Project directory and Git repo | `/home/chquan/Quipu`, branch `main` |
| Done | Team direction selected | User selected multi-device/team scope |
| Done | Design spec | `docs/superpowers/specs/2026-07-07-team-health-investigator-design.md` |
| Done | Implementation plan | `docs/superpowers/plans/2026-07-07-team-ingest-vertical-slice.md` |
| Done | First vertical slice execution | Server ingest, SQLite, fixtures, fleet overview UI |
| Done | Problem-solving UX redefinition | `docs/superpowers/specs/2026-07-07-problem-solving-flow-ux-design.md` |
| Done | Investigation-first UI implementation | Queue, incident detail, hypotheses, action, verification, report |
| Done | Release prep | `CHANGELOG.md`, `docs/superpowers/SHIP_CHECKLIST.md`, `docs/superpowers/RETRO.md` |
| Done | Repository presentation | Korean default README plus English and Chinese editions |
| Done | CI workflow | Server, collector, web tests/build |
| Done | CI runtime patch | GitHub Actions major versions updated for v0.2.1 |
| Done | Read-only collector foundation | `apps/collector` one-shot Linux observation batch |
| Done | Intervention records | API, SQLite persistence, investigation detail, React UI |
| Done | Before/after intervention verification | 30-minute metric/event windows, deterministic result, UI comparison |
| Done | Investigation Lens UI polish | Stronger first viewport, CTA routing, hover/focus expansion panels |
| Done | Metric explanation tooltips | CPU package, 1-minute load average, and NVMe cards explain definition/window/reading/next check |
| Done | Command Center redesign | One first viewport answers inspect/why/action/proof and removes reference image drawer |
| Done | Dark telemetry expansion | Dark command theme, core signal console, Wi-Fi core metric, and Telemetry Matrix |
| Done | Thermal/network event collection | Collector summaries, event-specific findings, throttling/reconnect matrix tiles |
| Done | Disk/battery telemetry expansion | Root filesystem usage, battery/AC metrics, storage/power findings, and matrix tiles |
| Done | Fan/NVMe SMART-lite telemetry | Fan RPM, NVMe health metrics, storage findings, and matrix tiles |
| Done | Collector operation loop | CLI dry-run, interval, iterations, injected test seams, and structured error output |
| Done | Collector systemd operations kit | service, timer, env example, wrapper, dry-run install/uninstall scripts, and ops tests |
| Done | Operations resilience MVP plan | `docs/superpowers/plans/2026-07-08-operations-resilience-mvp.md` |
| Done | Collector offline buffer | bounded spool, flush-before-current-send, retry backoff, wrapper/env integration |
| Done | Expanded event markers | graphics, memory, update, and reboot marker parsing |
| Done | Device enrollment hardening | per-device tokens, token rotation/revocation, device-bound ingest validation |
| Done | Team workflow notes | investigation handoff note API and UI |
| Done | Pattern Explorer | category/model/kernel overview API and compact UI |
| Done | Visible metadata chips | Made by, About, and Version remain visible without dominating the first viewport |
| Done | Guided dense analysis UI | Problem Guide first, Telemetry Brief, Fleet Brief, Workflow Rail with DTIHAVR hover stages, Metric Ledger, smaller telemetry tiles |
| Done | Component pattern grouping | `gpu:*`, `wifi:*`, and `nvme:*` signatures added to Pattern Explorer |
| Done | Product hardening roadmap | Collector rollout, retention, backup/restore, RBAC, packaging, production, Postgres, analytics, AI |
| Done | Documentation reset | Korean README rewritten, English and Chinese editions refreshed, Korean user manual added |
| Done | Hardware-aware Metric Ledger | Load average 1m/5m/15m chips, real CPU core IDs only, Ultra 5 125H P/E/LP-E grouping, per-device NVMe/Wi-Fi chips |
| Done | Multi-device naming | Collector `--device-alias`, systemd alias env, API persistence, and `alias · hostname` UI labels |
| Done | Hardware detail telemetry | CPU model/topology, Wi-Fi link bitrate, NVMe capacity, and sample-to-sample NVMe I/O rate |
| Done | Explanation consistency | Unified hover/focus popover behavior and single Project info metadata chip |
| Done | Device-first fleet UI | `Devices` is the primary list; `Device Issues` is scoped to the selected device; healthy devices still show telemetry detail |
| Done | Optional metadata preservation | Existing `display_name` and `cpu_model` survive later batches that omit those optional fields |
| Done | Windows best-effort telemetry collector | CPU core/thread, memory, battery, Wi-Fi, NVMe capacity, and ACPI thermal-zone metrics are collected when Windows exposes them |
| Done | Windows telemetry fallback expansion | i5-1340P P/E topology, WMI Wi-Fi RSSI, multi-path netsh, and LibreHardwareMonitor/OpenHardwareMonitor WMI temperatures |
| Done | Windows missing telemetry patch | Storage Reliability Counter NVMe temperature, hardware-monitor fan RPM, and Windows Event Log classification |
| Done | Windows native fallback patch | NVMe R/W bytes/sec from performance counters plus Win32 temperature probe and fan/tachometer fallbacks |
| Done | Private LAN UI/API access | Vite UI origins on private LAN ports 5173/5174 can read the API without CORS failure |
| Done | Windows hardware-monitor CPU load display | LibreHardwareMonitor/OpenHardwareMonitor P/E/LP-E core temperatures and core load percentages are collected and shown in Windows-specific rows |
| Done | Windows LibreHardwareMonitor running-process probe | Direct library probing no longer exits just because the LibreHardwareMonitor GUI is already running |
| Done | Windows Event Log text cleanup | Garbled localized Event Log summaries are hidden behind readable category/source fallback text |
| Done | Windows sensor visibility documentation | README and manual now distinguish CPU core load, CPU core temperature, and ACPI thermal-zone values with concrete diagnostic commands |
| Done | Windows connected laptop telemetry check | `윈도우 · DOGU_CHQUAN` now reports CPU core load plus CPU package, P-core, and E-core temperatures |
| Approved | Private remote push and release | User requested commit, tag, push, and release on 2026-07-07 |
| Approved | Public repository visibility after audit | User approved public visibility on 2026-07-07 |

## Open Decisions

| Decision | Default | Why |
| --- | --- | --- |
| MVP storage | SQLite WAL on one server | Light enough for a first self-hosted team version |
| Future storage | Postgres adapter | Useful if fleet size or concurrency grows |
| Agent language | Rust or Go | Static binary, low overhead, good system integration |
| First slice stack | Python FastAPI server + Vite React UI | Fastest small-team end-to-end slice |
| AI analysis | Optional, evidence-gated | Rule-based findings must work without AI |

## Gate

Actual host systemd installation, package publishing, production deployment,
destructive git operations, and any remote repair capability remain gated.
Public repository visibility is allowed only after a final sensitive-content
audit passes.

The v0.14.5 documentation release is allowed after local test/build/browser verification.
Full Windows telemetry for the currently connected laptop is now visible for
CPU load and CPU package/P-core/E-core temperatures. Future rollout checks
should still verify sensor visibility from the scheduled-task context when a
machine reports only ACPI thermal-zone values.
