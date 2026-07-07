# Quipu Project Dashboard

> Status: draft direction set
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
| In progress | Design spec | `docs/superpowers/specs/2026-07-07-team-health-investigator-design.md` |
| Pending | Implementation plan | Wait for user review of spec |
| Pending | App scaffold | Do after design/spec approval |
| Pending | Remote push | User said later; no remote configured yet |

## Open Decisions

| Decision | Default | Why |
| --- | --- | --- |
| MVP storage | SQLite WAL on one server | Light enough for a first self-hosted team version |
| Future storage | Postgres adapter | Useful if fleet size or concurrency grows |
| Agent language | Rust or Go | Static binary, low overhead, good system integration |
| Server/UI stack | Decide in implementation plan | Avoid premature framework lock-in |
| AI analysis | Optional, evidence-gated | Rule-based findings must work without AI |

## Gate

Do not scaffold the app or implement collectors until the written design spec is
reviewed and approved.
