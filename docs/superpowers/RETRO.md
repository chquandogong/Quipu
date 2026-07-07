# Quipu Retro

> Status: v0.1.0 cycle retro
> Date: 2026-07-07
> Owner: chquan

## What Shipped

- A local-first FastAPI + SQLite backend.
- A deterministic sample data path for three team devices.
- A React UI that starts from an Investigation Queue rather than a generic
  metric dashboard.
- DTIHAVR workflow surfaces for triage, evidence, hypotheses, action,
  verification, and reporting.
- Project documentation and GitHub collaboration templates.

## What Worked

- The product direction became clearer after shifting from "show system state"
  to "guide the problem-solving flow."
- Keeping analysis rule-based made the first slice testable without relying on
  AI output.
- The queue/detail split gives the UI a practical team workflow while staying
  lightweight.

## What To Improve

- Add a real read-only Linux collector so the product can move beyond seeded
  fixtures.
- Persist interventions and before/after windows so verification becomes real,
  not just suggested.
- Add a compact pattern explorer once several machines have real observations.
- Add CI so server tests, web tests, and builds are enforced before future tags.

## Not Shipped

- Native collector.
- Persistent action history.
- AI-assisted investigation summaries.
- Public release.
- Production deployment.

## Next Cycle

- Build the read-only local collector.
- Define the persisted intervention model.
- Add a release CI workflow before `v0.2.0`.
