# Fan And NVMe SMART-Lite Telemetry Design

Date: 2026-07-08
Release target: v0.6.0

## Decision

Quipu v0.6.0 adds two lightweight hardware-health slots:

- Fan RPM: read the first available `fan*_input` value from hwmon.
- NVMe SMART-lite: read optional NVMe health fields when exposed by sysfs-like
  text files, without requiring `smartctl`, `nvme-cli`, root privileges, or a
  background daemon.

The release continues the v0.5.0 principle: Quipu should surface useful
evidence when Linux exposes it, but missing hardware signals must not break the
collector or make the UI noisy.

## Why This Matters

Thermal symptoms are often ambiguous. A hot laptop with no visible fan signal,
a normal NVMe temperature with a storage warning, or an NVMe critical-warning
flag can change the next investigation step. These are not primary charts; they
are supporting evidence for the problem-solving flow.

## Scope

Collector:

- Emit `fan.rpm` with unit `rpm` from the first readable hwmon `fan*_input`.
- Emit optional NVMe SMART-lite metrics:
  - `nvme.critical_warning` with unit `boolean`
  - `nvme.available_spare_percent` with unit `percent`
  - `nvme.percentage_used_percent` with unit `percent`
  - `nvme.media_errors` with unit `count`
- Parse values from direct files under `/sys/class/nvme/nvme*` when present.
- Parse equivalent key/value lines from an optional `smart_log` text file when
  present in the same directory.

Server:

- Treat `nvme.critical_warning >= 1` as a high-confidence storage finding.
- Treat low available spare, high percentage used, or media errors as storage
  warnings.
- Keep fan RPM as context in v0.6.0 rather than a queue-driving finding.

Web:

- Add `Fan RPM` and `NVMe Health` tiles to the Telemetry Matrix.
- Show fan as a cooling signal and NVMe health as a storage signal.
- Keep the summary-first layout and responsive one-column behavior on narrow
  screens.

## Non-Goals

- No external SMART or NVMe CLI dependency.
- No privileged disk probes.
- No device serial/model upload.
- No automatic repair or fan-control action.

## Risk Controls

- Missing fan or NVMe SMART-lite files produce `Unavailable`, not a collection
  failure.
- A stopped fan is not automatically a failure unless paired with other thermal
  evidence in later releases.
- NVMe health thresholds are conservative and rule-based; raw SMART logs are
  not uploaded.
