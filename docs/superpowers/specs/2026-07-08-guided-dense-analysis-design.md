# Guided Dense Analysis Design

Date: 2026-07-08

## Problem

The Command Center shows the right investigation pieces, but too much screen
area is still spent on raw signal cards such as CPU, Load, NVMe, and Wi-Fi. The
DTIHAVR stage list can also consume space without changing the operator's next
decision when it is shown as seven large fixed labels. The
product should not feel like another dashboard wall. It should answer:

- What is the problem?
- Why does Quipu think it matters?
- What should I do next?
- Which deeper pattern explains recurrence across devices?

## Decision

Use a compact `Problem Guide` as the first visual anchor. Core metrics collapse
into one `Telemetry Brief`, and detailed metric explanations move into a
row-based `Metric Ledger`. Fleet totals collapse into a `Fleet Brief` with the
same visual density. The workflow becomes a `Workflow Rail` that shows current
stage, next stage, and next action instead of a seven-box step strip, while
preserving compact `D T I H A V R` initials with hover/focus definitions.
Pattern Explorer also adds component signatures so repeated graphics, Wi-Fi,
and NVMe issues are grouped by actionable subsystem, not only by
category/model/kernel.

## UI Shape

- `Problem Guide`: three compact blocks for problem, first evidence, and next
  action.
- Existing answer cards stay as secondary detail, with lower height and smaller
  typography.
- CPU/Load/NVMe/Wi-Fi signal chips become one `Telemetry Brief`.
- Total/Critical/Warning/Queue become one `Fleet Brief`.
- DTIHAVR fixed labels become a thin `Workflow Rail` with small stage initials
  and hover/focus explanations for Detect through Report.
- Core metric explanations become one row-based `Metric Ledger`.
- Telemetry tiles use smaller stable dimensions.
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
