# Guided Dense Analysis Design

Date: 2026-07-08

## Problem

The Command Center shows the right investigation pieces, but too much screen
area is still spent on raw signal cards such as CPU, Load, NVMe, and Wi-Fi. The
product should not feel like another dashboard wall. It should answer:

- What is the problem?
- Why does Quipu think it matters?
- What should I do next?
- Which deeper pattern explains recurrence across devices?

## Decision

Use a compact `Problem Guide` as the first visual anchor. Metrics become a
dense instrument strip, not the main story. Pattern Explorer also adds
component signatures so repeated graphics, Wi-Fi, and NVMe issues are grouped
by actionable subsystem, not only by category/model/kernel.

## UI Shape

- `Problem Guide`: three compact blocks for problem, first evidence, and next
  action.
- Existing answer cards stay as secondary detail, with lower height and smaller
  typography.
- CPU/Load/NVMe/Wi-Fi signal chips become a single-row instrument strip.
- Metric and telemetry tiles use smaller stable dimensions.
- Pattern Explorer gains `By component` for signatures such as `gpu:i915`,
  `wifi:wlp0s20f3`, and `nvme:nvme0n1`.

## Analysis Shape

- Hot CPU plus very low fan RPM becomes a specific thermal finding:
  `Cooling response needs inspection`.
- Graphics events are grouped by GPU/session component when recognizable.
- Network events are grouped by Wi-Fi interface when recognizable.
- Storage events are grouped by NVMe device or storage signature when
  recognizable.

## Non-Goals

- No `smartctl`, `nvme-cli`, vendor SDK, fan control, or root-only dependency.
- No automatic repair action.
- No production deployment, package publishing, or host systemd mutation in
  this implementation pass.

## Validation

- Server unit tests cover cooling-response finding and component signature
  grouping.
- Web tests cover the Problem Guide and `By component` UI.
- Build verification must pass before committing.
