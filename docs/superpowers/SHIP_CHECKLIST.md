# Quipu Ship Checklist

> Status: v0.14.8 release checklist — Apache-2.0 licensed, documentation and repository presentation current
> Date: 2026-07-16
> Owner: chquan
> Release: v0.14.8

## Scope

Included:

- FastAPI ingest API.
- SQLite persistence.
- Deterministic sample fleet data.
- Rule-based fleet and investigation projections.
- Investigation queue and detail API.
- React investigation-first UI.
- Korean default README, English README, and Simplified Chinese README.
- Korean user manual for operators and first-time users.
- GitHub Actions CI.
- GitHub Actions runtime version patch.
- Read-only Linux collector.
- Persistent intervention records.
- Intervention recording UI.
- Before/after intervention verification.
- Verification result UI.
- Command Center first viewport and hover/focus expansion panels.
- High-contrast dark command theme.
- Core signal console for CPU package temperature, 1-minute/5-minute/15-minute
  load average, NVMe temperature, and Wi-Fi signal.
- Telemetry Matrix for CPU Profile, Memory Used, Network Events, Reconnect
  History, Thermal Throttling, Fan RPM, NVMe Health, NVMe Capacity, NVMe I/O,
  Disk Health, Battery Power, Wi-Fi Link, Kernel Warnings, and Agent Freshness.
- Hover/focus metric explanations for CPU package temperature, load average,
  NVMe temperature, and Wi-Fi signal.
- Best-effort collector summaries for kernel thermal throttling and
  NetworkManager reconnect/disconnect events.
- Event-specific findings for thermal throttling and network reconnects.
- Root filesystem usage, battery capacity, and AC online collector metrics.
- Best-effort kernel storage and power warning summaries.
- Event-specific findings for storage health and battery/power issues.
- Fan RPM and NVMe SMART-lite health collector metrics.
- Storage findings for NVMe critical-warning, spare, lifetime usage, and media
  error signals.
- Collector dry-run mode.
- Collector interval and iterations mode for lightweight supervised operation.
- Structured collector JSON error output.
- Collector systemd service and five-minute timer files.
- Collector environment example and wrapper script.
- Dry-run install and uninstall scripts for collector systemd files.
- Collector offline local ring buffer, flush-before-current-send, flush limit,
  and retry backoff.
- Expanded collector markers for graphics, memory, update, and reboot events.
- Device enrollment API.
- Device display aliases stored as `display_name` and shown beside hostnames.
- CPU model stored as `cpu_model` and shown through CPU Profile telemetry.
- Device-bound ingest tokens.
- Token rotation and revocation APIs.
- Schema version endpoint.
- Team handoff notes API and UI.
- Pattern overview API and Pattern Explorer UI grouped by category, model, and
  kernel.
- Operations Rail for agent freshness, offline buffering, enrollment guard,
  and pattern radar.
- Metric Ledger breakdown chips for load average, CPU package/core sensors,
  NVMe devices/capacity/I/O, and Wi-Fi interfaces/link bitrate.
- Intel Core Ultra 5 125H CPU core grouping for P, E, and LP-E core
  temperature sensors when the observed sensor IDs match that topology.
- Collector CPU topology, Wi-Fi Rx/Tx link bitrate, NVMe namespace capacity,
  and NVMe read/write bytes/sec telemetry.
- Collector state directory for sample-to-sample NVMe throughput calculation.
- Local-notebook-only collector workflow documented after deleting sample data.
- Multi-notebook collector workflow documented for LAN server collection.
- Unified `Project info` metadata chip.
- Consistent hover/focus explanation popovers across status, metric, coverage,
  operations, telemetry, workflow, and fleet surfaces.
- Device-first `Devices` list with alias/hostname, hardware label, metric/event
  counts, last-seen time, issue summary, and risk.
- `Device Issues` list scoped to the selected device.
- Healthy device detail view with no active investigation item required.
- Fleet Brief `Open issues` wording instead of `Queue cases`.
- Compatible Windows collector documentation and manual verification command.
- Best-effort Windows collector metrics for CPU core/thread counts, memory
  usage, battery charge/AC state, Wi-Fi signal/link speed, NVMe capacity, and
  ACPI thermal zones when exposed by Windows.
- Windows Intel Core i5-1340P P/E topology mapping.
- Windows Wi-Fi signal fallback through direct/full-path/PowerShell `netsh`
  and WMI `MSNdis_80211_ReceivedSignalStrength`.
- Windows LibreHardwareMonitor/OpenHardwareMonitor WMI temperature fallback for
  CPU package/core and NVMe/SSD sensors.
- Windows Storage Reliability Counter fallback for NVMe temperature.
- Windows LibreHardwareMonitor/OpenHardwareMonitor WMI fan RPM fallback.
- Windows Event Log ingestion and category classification for recent
  System/Application events.
- Windows NVMe R/W bytes/sec from
  `Win32_PerfFormattedData_PerfDisk_PhysicalDisk` mapped to `Get-PhysicalDisk`.
- Windows native temperature probe fallback through `Win32_TemperatureProbe`.
- Windows native fan/tachometer fallback through `Win32_Fan` and
  `Win32_Tachometer`.
- Windows LibreHardwareMonitor/OpenHardwareMonitor CPU P-core/E-core/LP-E core
  temperature mapping.
- Windows LibreHardwareMonitor/OpenHardwareMonitor total and per-core CPU load
  percentage collection.
- Windows direct LibreHardwareMonitor DLL probing from the running GUI process
  path, Program Files, LocalAppData, and nested WinGet package directories.
- Windows-specific CPU Cores and CPU Core Load UI rows that avoid Linux-only
  placeholders when Windows does not report load average or CPU package.
- Windows CPU Cores row remains visible when package temperature and P/E core
  temperature metrics are present together.
- Documentation that distinguishes Windows CPU core load, CPU core temperature,
  and ACPI thermal-zone values.
- Windows troubleshooting commands for LibreHardwareMonitor WMI
  `Load`/`Temperature` sensors, collector `--dry-run`, scheduled-task
  `RunLevel`, and explicit hardware-monitor DLL configuration.
- UI fallback for garbled localized Windows Event Log summaries.
- Private LAN CORS allowance for Vite UI origins on ports `5173` and `5174`.
- Preservation of existing `display_name` and `cpu_model` when later batches
  omit optional metadata.
- Removed duplicate creator/reference image drawer from the working UI.
- Visible Made by, About, and Version metadata in one compact chip.
- Project docs, GitHub templates, contribution notes, and security policy.
- Horizontal device status transitions and Smart Advisor/Actions left tabs
  (v0.14.5).
- No automatic demo seeding; documented manual sample-fleet seeding via
  `python -m quipu_server.seed` (v0.14.5 behavior, documented in v0.14.6).
- Documentation rework: all three READMEs, user manual, CONTRIBUTING, and
  SECURITY rewritten against the current implementation (v0.14.6).
- Apache-2.0 license: LICENSE and NOTICE files, SPDX metadata in both
  `pyproject.toml` files and `package.json`, dynamic README badges, dashboard
  screenshot, and repository description/topics (v0.14.7).
- License visibility: `Project info` chip shows `License: Apache-2.0`, and
  every README edition has a License section (v0.14.8).

Excluded:

- Actual host systemd service/timer installation during verification.
- Remote repair or remote command execution.
- AI-generated conclusions.
- Package publishing.
- Production deployment.

## Tests

- Server tests: `.venv/bin/python -m pytest` -> 38 passed, 1 Starlette deprecation warning.
- Collector tests: `.venv/bin/python -m pytest` -> 28 passed.
- Web tests: `npm test -- --run` -> 3 passed.
- Web build: `npm run build` -> succeeded.
- Whitespace check: `git diff --check` -> passed.
- Browser DOM smoke check: `Version v0.14.8`, `License: Apache-2.0`, `Devices`,
  `Device Issues`, `우분투 · chquan-17ZD90SP-GX56K`, `윈도우 · DOGU_CHQUAN`, and
  `Telemetry Matrix` rendered from the local UI without `Failed to fetch`.
- Installed package metadata check: `License-Expression: Apache-2.0`.
- GitHub license detection check: repository reports `Apache License 2.0`.
- Live Windows batch check: `윈도우 · DOGU_CHQUAN` reports `cpu.load_percent`,
  `cpu.core_<n>.load_percent`, `cpu.package_temp_c`, `cpu.p_core_1..4.temp_c`,
  and `cpu.e_core_1..8.temp_c`.

Evidence source:

- Latest verified release: v0.14.8 (`36f4f9d`), CI success on GitHub Actions.

## Risks

Known risks:

- Collector coverage is best-effort because Linux sensor exposure varies by
  machine.
- Wi-Fi link bitrate depends on `iw` availability and an active wireless link;
  it is not an internet speed test.
- NVMe read/write throughput requires at least two collector samples for the
  same device.
- Fan RPM and NVMe SMART-lite coverage are best-effort because Linux hardware
  exposure varies by machine.
- systemd operations files are included, but CI does not mutate host systemd.
- Offline buffering is local-file based and bounded; production retention
  policy still needs team configuration.
- Enrollment tokens are stored as hashes, but role-aware admin auth is still a
  future hardening item.
- Current analysis is deterministic and intentionally conservative.
- Windows telemetry coverage depends on the Windows task running the v0.14.8
  collector package. The current observed Windows device is visible, but an
  older task may keep sending only smoke-level telemetry until the release is
  installed and the task is restarted on that machine.
- Windows fan RPM and CPU/NVMe hardware-monitor temperatures still depend on
  Windows, firmware, run level, and LibreHardwareMonitor/OpenHardwareMonitor
  exposing the relevant sensors to the collector context. The connected Windows
  device currently exposes CPU load plus CPU package/P-core/E-core temperature.
- Verification uses a fixed 30-minute window.
- `npm ci` reports existing transitive web dependency vulnerabilities; no public
  production deployment is included in this release.
- Public creator/reference images are not shown in the working UI; provenance
  remains in compact metadata.

Approved risks:

- User explicitly requested autonomous continuation; this release follows the
  approved commit, tag, push, and release flow.
- GitHub release is approved for this release cycle.
- Public repository visibility is approved after sensitive-content audit.

Unapproved risks:

- Package publishing.
- Production deployment.
- Remote execution on team machines.

## Rollback

Rollback method:

- Delete or supersede the private GitHub release if the release note is wrong.
- Move forward with a patch tag such as `v0.14.9` for code or documentation fixes.
- Avoid force-push and history rewrite.

Rollback owner:

- chquan.

Rollback conditions:

- Release points to the wrong commit.
- Security-sensitive content is accidentally included.
- Verification fails after push.

## Monitoring

Check after release:

- GitHub repository URL resolves.
- `main` branch is pushed.
- New release tag exists locally and remotely.
- GitHub release exists for the new tag.
- Repository visibility is public after audit.

## Documents

- README: rewritten in all three editions with the current UI layout, quick
  start (manual seeding), collector CLI/API/environment tables, dashboard
  screenshot, dynamic badges, and a License section.
- User manual: current tabbed screen guide, manual seeding, Windows collector
  verification, hardware-monitor CPU load/temperature metric names, and
  scheduled-task diagnostics.
- Dashboard: v0.14.8 release state recorded.
- Roadmap: device-first, Windows telemetry, and connected-laptop rollout tracks
  recorded.
- Changelog: entries through `v0.14.8`; GitHub releases exist for v0.14.3
  through v0.14.8.
- Contributing: first-time setup and CI runtime versions documented.
- Security policy: current auth model documented; LICENSE and NOTICE present.

## Final Judgment

`v0.14.8` is released: local test/build/browser checks passed, CI succeeded,
and the GitHub release is published. The project is Apache-2.0 licensed, and
the connected Windows laptop reports CPU load plus CPU package/P-core/E-core
temperatures.

Public repository visibility is allowed after sensitive-content audit.
Package publishing, production deployment, destructive git operations, and
remote repair remain outside this approval.
