# Quipu Project Dashboard

> Status: v0.9.0 operations resilience release track
> Date: 2026-07-08
> Owner: chquan

## Current Decision

Quipu starts as a multi-device, team-oriented workstation health investigator,
not as a single-laptop utility.

## Scope

- Initial users: one technical team.
- Initial fleet: 3-20 Linux laptops or developer workstations.
- Deployment: self-hosted team server on LAN or private network.
- Collection: lightweight read-only agent per machine.
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
