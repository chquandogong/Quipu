# Dark Telemetry Expansion

> Date: 2026-07-07
> Status: implementation track
> Release target: v0.3.3

## Problem

The `v0.3.2` Command Center clarified the investigation flow, but the visible
telemetry still felt too narrow. CPU package temperature, 1-minute load average,
and NVMe temperature are useful for thermal triage, but not enough for a team
tool that must explain Wi-Fi instability, memory pressure, kernel warnings,
agent freshness, and future device-specific signals.

The light visual theme also lacked command-surface contrast. It did not make the
active incident, risk, and next action stand out strongly enough.

## Chosen Design

Use a dark command theme and split telemetry into two layers:

- First viewport `signal console`: CPU, Load, NVMe, and Wi-Fi signal. These are
  the fast-read signals that help the user decide whether the selected case is
  thermal, workload, storage, or network shaped.
- Detail `Telemetry Matrix`: Memory Used, Network Events, Kernel Warnings, and
  Agent Freshness. This shows category coverage and creates a clear extension
  point for battery, fan, disk health, reconnect history, and thermal
  throttling events.

The design keeps the Command Center's four answers: `Inspect now`,
`Why it matters`, `Do next`, and `Proof needed`.

## UI Rules

- Dark theme by default for the working UI.
- Use multiple status colors, not a one-hue palette:
  - teal for primary command/action,
  - amber for watch states,
  - red for critical states,
  - green for nominal/improved states,
  - blue/cyan for network and information surfaces.
- Keep metadata small. Creator, About, and Version remain header chips only.
- Keep explanations compact: Korean explanation plus English technical term
  when precision matters.

## Data Boundaries

- No API contract change is required.
- Use existing `latest_metrics` for CPU, Load, NVMe, Wi-Fi, and Memory.
- Use existing event timelines for Network Events and Kernel Warnings.
- Use existing `last_seen_at` plus fleet `generated_at` for Agent Freshness.
- Fixture data is expanded so the local demo shows the intended multi-signal
  coverage.

## Verification

- Web test must fail before implementation and pass after implementation.
- Test must assert the dark theme class, Wi-Fi metric help, Telemetry Matrix,
  Memory Used, Network Events, and Kernel Warnings.
- Full verification must include server tests, collector tests, web tests, web
  build, and whitespace check before release.
