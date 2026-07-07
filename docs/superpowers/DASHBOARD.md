# Quipu Project Dashboard

> Status: v0.2.0 release candidate
> Date: 2026-07-07
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
| Done | CI workflow | Server, collector, web tests/build |
| Done | Read-only collector foundation | `apps/collector` one-shot Linux observation batch |
| Done | Intervention records | API, SQLite persistence, investigation detail, React UI |
| Approved | Private remote push and release | User requested commit, tag, push, and release on 2026-07-07 |

## Open Decisions

| Decision | Default | Why |
| --- | --- | --- |
| MVP storage | SQLite WAL on one server | Light enough for a first self-hosted team version |
| Future storage | Postgres adapter | Useful if fleet size or concurrency grows |
| Agent language | Rust or Go | Static binary, low overhead, good system integration |
| First slice stack | Python FastAPI server + Vite React UI | Fastest small-team end-to-end slice |
| AI analysis | Optional, evidence-gated | Rule-based findings must work without AI |

## Gate

Collector daemonization, before/after verification windows, public release,
package publishing, production deployment, destructive git operations, and any
remote repair capability remain gated.
