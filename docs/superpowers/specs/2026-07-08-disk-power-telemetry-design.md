# Disk And Battery Telemetry Design

Date: 2026-07-08
Release target: v0.5.0

## Decision

Quipu v0.5.0 adds two practical extension slots to the existing telemetry
matrix:

- Disk Health: root filesystem usage plus recent kernel storage warning events.
- Battery Power: battery capacity, AC online state, and recent kernel power
  warning events.

This release stays read-only and lightweight. It does not require SMART tools,
root permissions, persistent daemons, fan drivers, or vendor SDKs.

## Why This Matters

The original freeze investigation started from thermal symptoms, but team
workstation failures often look similar from the user's point of view:

- Storage stalls can freeze the desktop even when CPU temperature is normal.
- Battery or AC power transitions can throttle a laptop or trigger instability.
- Disk fullness can make builds, package updates, browsers, and logging fail in
  misleading ways.

The competitive point is not collecting every possible signal. It is showing
the next likely failure domain in the same problem-solving flow: detect,
triage, investigate, hypothesize, act, verify, report.

## Scope

Collector:

- Read `shutil.disk_usage(root)` and emit `disk.root_used_percent`.
- Read `/sys/class/power_supply/*/type`, `capacity`, `status`, and `online`.
- Emit `battery.capacity_percent` for the first readable battery.
- Emit `battery.ac_online` as `1` or `0` for the first readable mains or USB
  power source.
- Parse recent kernel text for storage and power warnings.

Server:

- Turn storage warnings into `Storage health event reported`.
- Turn power warnings into `Battery power issue reported`.
- Provide category-specific next steps and actions.

Web:

- Add `Disk Health` and `Battery Power` tiles to Telemetry Matrix.
- Keep summary-first behavior: the user sees the answer first, then detail on
  demand.
- Preserve compact dark command-center density.

## Non-Goals

- No SMART/NVMe CLI dependency in v0.5.0.
- No fan RPM collection yet.
- No raw log upload beyond the existing short `message_summary` and `raw_ref`.
- No remote repair actions.

## Risk Controls

- Missing files must degrade to `Unavailable`, not fail collection.
- Battery and AC state are useful context, not automatically a fault unless a
  power warning exists or battery capacity is low.
- Storage event matching avoids generic `nvme` text to reduce false positives
  from normal temperature or enumeration messages.
