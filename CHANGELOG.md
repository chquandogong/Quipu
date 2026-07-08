# Changelog

All notable changes to Quipu are documented in this file.

## v0.10.0 - 2026-07-08

Hardware-aware Metric Ledger and documentation reset release.

### Added

- Korean user manual covering sample mode, local-notebook-only mode, collector
  commands, systemd operation, UI interpretation, and troubleshooting.
- Metric Ledger grouping for Intel Core Ultra 5 125H CPU temperature sensors:
  performance cores, efficient cores, and low-power efficient cores are shown
  separately when the observed sensor layout matches the processor topology.
- Per-device Metric Ledger chips for NVMe and Wi-Fi telemetry so single and
  multiple devices/interfaces use the same display model.
- Documentation for removing the sample SQLite database and collecting fresh
  telemetry from the current notebook.

### Changed

- Rewrote the Korean README from the beginning and refreshed the English and
  Simplified Chinese editions for the current product shape.
- Load average now appears as 1-minute, 5-minute, and 15-minute values instead
  of a single ambiguous reading.
- CPU core temperature chips now show only real observed core sensor IDs, with
  no gap-filling placeholder cores.
- CPU core chip labels no longer repeat the word `Core`; the group label gives
  the context and each chip shows the numeric sensor ID.
- Updated package, app, API, schema, and UI versions to `0.10.0`.

### Verified

- Server test suite: 35 tests passed, 1 Starlette deprecation warning.
- Collector test suite: 17 tests passed.
- Web test suite: 3 tests passed.
- Web production build succeeded.
- Browser verification confirmed `Version v0.10.0`, grouped Ultra 5 125H core
  telemetry, 1m/5m/15m load average chips, and per-device NVMe/Wi-Fi chips.
- Local notebook-only run confirmed the sample database can be removed and
  replaced with telemetry collected from this machine.

## v0.9.0 - 2026-07-08

Operations resilience MVP covering the remaining eight team-operations tracks.

### Added

- Collector offline local ring buffer with bounded spool depth, flush before
  current send, flush limits, and retry backoff.
- systemd wrapper defaults that enable collector offline buffering without
  mutating the host during verification.
- Best-effort collector summaries for graphics, memory, update, and reboot
  markers.
- Device enrollment API with per-device agent tokens.
- Token rotation and revocation APIs; ingest accepts either the development
  token or an active device-bound token.
- Schema version endpoint for operational verification.
- Investigation handoff notes API for team context.
- Pattern overview API grouped by category, model, and kernel.
- React Operations Rail, Team Handoff, and Pattern Explorer surfaces.
- v0.9.0 operations-resilience design and implementation plan documents.

### Changed

- README editions now document offline buffering, enrollment tokens, and the
  new operations/team/pattern UI surfaces.
- Updated package and app versions to `0.9.0`.

### Verified

- Server test suite: 32 tests passed.
- Collector test suite: 17 tests passed.
- Web test suite: 1 test passed.
- Web production build succeeded.
- Collector CLI smoke commands covered one-shot dry-run and offline buffering.
- Browser screenshot confirmed `Version v0.9.0` in the running app.

## v0.8.0 - 2026-07-08

Collector systemd operations release.

### Added

- Repo-contained collector operations kit under `apps/collector/ops`.
- systemd `quipu-collector.service` for one-shot read-only collection.
- systemd `quipu-collector.timer` for five-minute scheduled collection.
- `/etc/quipu/collector.env` example for server URL, token, root, optional
  device ID, and collector binary override.
- `quipu-collector-run` wrapper that validates required environment values and
  builds collector CLI arguments safely.
- Dry-run capable install and uninstall scripts for systemd collector files.
- Ops packaging tests that validate unit files, timer settings, env examples,
  wrapper behavior, script syntax, and dry-run behavior without mutating the
  host.
- v0.8.0 collector systemd operations design and implementation plan
  documents.

### Changed

- README editions now document systemd dry-run preview, install, timer enable,
  list-timers check, and uninstall flows.
- Updated package and app versions to `0.8.0`.

### Verified

- Server test suite: 27 tests passed.
- Collector test suite: 12 tests passed.
- Web test suite: 1 test passed.
- Web production build succeeded.
- Collector CLI smoke command produced one-shot and repeated local observation
  batches.
- systemd installer and uninstaller dry-run checks passed.
- Browser screenshot confirmed `Version v0.8.0` in the running app.

## v0.7.0 - 2026-07-08

Collector operation loop release.

### Added

- Collector CLI `--dry-run` mode that prints observation batches and skips
  posting even when `--server-url` is present.
- Collector CLI `--interval` and `--iterations` controls for lightweight
  repeated collection under a supervisor.
- Structured JSON error output for collection and send failures.
- CLI tests covering one-shot output, POST behavior, dry-run behavior,
  interval iteration behavior, invalid loop options, and collection failure
  output.
- v0.7.0 collector operation-loop design and implementation plan documents.

### Changed

- The collector remains one-shot by default, but can now run as a lightweight
  loop without adding daemon, systemd, or external runtime dependencies.
- README editions now document one-shot dry-run, one-shot POST, repeated smoke
  tests, and simple supervised-loop examples.
- Updated package and app versions to `0.7.0`.

### Verified

- Server test suite: 27 tests passed.
- Collector test suite: 7 tests passed.
- Web test suite: 1 test passed.
- Web production build succeeded.
- CLI smoke command produced a local observation batch.
- Browser screenshot confirmed `Version v0.7.0` in the running app.

## v0.6.0 - 2026-07-08

Fan and NVMe SMART-lite telemetry release.

### Added

- Read-only collector metric for `fan.rpm` from the first readable hwmon
  `fan*_input` value.
- Read-only collector metrics for `nvme.critical_warning`,
  `nvme.available_spare_percent`, `nvme.percentage_used_percent`, and
  `nvme.media_errors` from sysfs-style NVMe health files or an optional
  `smart_log` text file.
- Rule-based storage findings for NVMe critical-warning flags, low available
  spare, high percentage used, and media errors.
- Telemetry Matrix tiles for `Fan RPM` and `NVMe Health`.
- v0.6.0 fan/NVMe SMART-lite design and implementation plan documents.

### Changed

- Expanded sample team fixture data with fan RPM and NVMe SMART-lite health
  metrics across the demo fleet.
- Updated package and app versions to `0.6.0`.

### Verified

- Server test suite: 27 tests passed.
- Collector test suite: 1 test passed.
- Web test suite: 1 test passed.
- Web production build succeeded.
- Browser screenshot confirmed `Version v0.6.0`, `Fan RPM`, `NVMe Health`, and
  `10/10 signals` in the running app.

## v0.5.0 - 2026-07-08

Disk and battery telemetry expansion release.

### Added

- Read-only collector metric for `disk.root_used_percent`.
- Read-only collector metrics for `battery.capacity_percent` and
  `battery.ac_online` from `/sys/class/power_supply`.
- Best-effort kernel storage warning parsing for I/O timeout, I/O error,
  controller reset, SMART, media, and filesystem error signatures.
- Best-effort kernel power warning parsing for battery, AC offline, AC adapter,
  low-battery, discharge-rate, and power-management signatures.
- Rule-based analysis findings for `Storage health event reported` and
  `Battery power issue reported`.
- Telemetry Matrix tiles for `Disk Health` and `Battery Power`.
- v0.5.0 disk/battery telemetry design and implementation plan documents.

### Changed

- Expanded sample team fixture data with disk usage, battery capacity, AC
  online state, and storage/power warning events.
- Updated package and app versions to `0.5.0`.

### Verified

- Server test suite: 25 tests passed.
- Collector test suite: 1 test passed.
- Web test suite: 1 test passed.
- Web production build succeeded.
- Browser screenshot confirmed `Version v0.5.0`, `Disk Health`,
  `Battery Power`, and `8/8 signals` in the running app.

## v0.4.0 - 2026-07-08

Thermal and network event collection release.

### Added

- Best-effort read-only collector parsing for kernel thermal throttling,
  package threshold, CPU clock throttling, and critical thermal messages.
- Best-effort read-only collector parsing for NetworkManager reconnect,
  disconnect, carrier, supplicant, DHCP, and link-state events.
- Compact event summaries with source, observed time, raw reference, and stable
  fingerprints; raw logs are not uploaded.
- Rule-based analysis for `Thermal throttling reported` and
  `Network reconnect reported` findings.
- Telemetry Matrix tiles for `Thermal Throttling` and `Reconnect History`.
- v0.4.0 design and implementation plan documents.

### Changed

- Updated sample team fixture events to use realistic thermal throttling and
  NetworkManager reconnect signatures.
- Updated package and app versions to `0.4.0`.

### Verified

- Server test suite: 23 tests passed.
- Collector test suite: 1 test passed.
- Web focused test: 1 test passed.
- Web production build succeeded.
- Browser screenshot confirmed `Version v0.4.0`, `Reconnect History`,
  `Thermal Throttling`, and `6/6 signals` in the running app.

## v0.3.3 - 2026-07-07

Dark telemetry expansion release.

### Changed

- Reworked the first viewport into a high-contrast dark command theme so the
  active case, risk, action, and proof surfaces stand out more clearly.
- Promoted Wi-Fi signal strength into the core metric set alongside CPU
  package temperature, 1-minute load average, and NVMe temperature.
- Added a first-glance signal console for core telemetry.
- Added a `Telemetry Matrix` for Memory Used, Network Events, Kernel Warnings,
  and Agent Freshness so the UI shows which categories are covered and which
  signals can expand next.
- Updated sample team fixture data with memory, Wi-Fi, and NVMe readings across
  the demo fleet.
- Updated package and app versions to `0.3.3`.

### Verified

- Server test suite: 21 tests passed.
- Collector test suite: 1 test passed.
- Web test suite: 1 test passed.
- Web production build succeeded.
- Browser screenshot confirmed the dark command theme, signal console, and
  Telemetry Matrix render in the running app.

## v0.3.2 - 2026-07-07

Command-center UI redesign.

### Changed

- Replaced the separate flow rail, fleet summary cards, and focus-board stack
  with a single `Command Center` first viewport.
- Added four first-glance answers: `Inspect now`, `Why it matters`, `Do next`,
  and `Proof needed`.
- Reworked metric help to use Korean explanation with English technical terms
  for CPU package temperature, 1-minute load average, and NVMe temperature.
- Removed the large creator/reference image drawer because it duplicated header
  metadata and did not support investigation decisions.
- Updated package and app versions to `0.3.2`.

### Research

- Compared Carbon dashboard hierarchy, Material tooltip behavior, Fluent
  responsive layout, Primer progressive disclosure, and 2026 SaaS command-style
  workflow patterns.

## v0.3.1 - 2026-07-07

Metadata, metric explanation, and visual investigation-lens patch after the
v0.3.0 tag.

### Changed

- Kept `Made by`, `About`, and `Version` visible in the header as compact
  metadata chips.
- Reworked the first viewport toward an `Investigation Lens` visual treatment:
  stronger fleet summary cards, a clearer current-incident focus board, and a
  more distinctive selected-investigation panel.
- Added hover/focus metric help for CPU package temperature, 1-minute load
  average, and NVMe temperature with definition, time window, reading guidance,
  and next-check text.
- Kept large creator/reference images in the collapsed secondary drawer so they
  do not compete with the investigation workflow.
- Updated package and app versions to `0.3.1`.

### Verified

- Server test suite: 21 tests passed.
- Collector test suite: 1 test passed.
- Web test suite: 1 test passed.
- Web production build succeeded.

## v0.3.0 - 2026-07-07

Evidence-backed intervention verification release.

### Added

- SQLite-backed observation window queries around recorded interventions.
- Deterministic before/after verification results for investigation details.
- Thermal comparison for `cpu.package_temp_c` averages.
- Load context comparison for `cpu.load_1m`.
- Warning/critical event recurrence comparison for the intervention category.
- UI rendering for verification result status, window length, checks, and deltas.
- Summary-first focus board with `Review evidence`, `Record action`, and
  `Verify result` CTAs.
- Hover/focus expansion panels for evidence, hypotheses, interventions,
  verification, and report detail.
- Collapsed creator/reference drawer using public Dogu Robotics, Dogu X, and
  Physical AI portfolio assets.
- Lucide icon treatment for action buttons and signal surfaces.
- v0.3.0 design and implementation plan documents.

### Changed

- Investigation verification now summarizes the latest intervention result when
  before/after data exists.
- Interventions in the detail API may include a derived `verification_result`.
- Investigation UI now leads with what to inspect, what to do, and how to
  verify, instead of presenting every panel at full height.
- Creator/reference visuals now stay secondary so they do not compete with
  investigation decisions.
- README editions now list intervention verification as implemented.

### Fixed

- Serialized access to the local SQLite connection so concurrent dashboard
  requests do not intermittently fail with `sqlite3.InterfaceError`.

### Verified

- Server test suite: 21 tests passed.
- Collector test suite: 1 test passed.
- Web test suite: 1 test passed.
- Web production build succeeded.
- Remote GitHub Actions CI is the release gate after push.

### Known Gaps

- Collector is still one-shot, not a daemon.
- Verification uses a fixed 30-minute window.
- Verification is deterministic and rule-based; no AI-generated conclusions.
- Reference visuals are loaded from public GitHub raw URLs to avoid bundling
  heavy image assets.
- Long-term baseline analytics remain deferred.

## v0.2.1 - 2026-07-07

Patch release for CI runtime hygiene after `v0.2.0`.

### Changed

- Reworked the default README into Korean and added English and Simplified
  Chinese README editions.
- Polished repository presentation with badges, clearer quick-start sections,
  multilingual documentation links, PR checklist coverage, and release note
  categorization.
- Updated GitHub Actions workflow actions to current major versions:
  `actions/checkout@v7`, `actions/setup-python@v6`, and
  `actions/setup-node@v6`.
- Updated the web CI runtime from Node 20 to Node 24.

### Verified

- Server test suite passed.
- Collector test suite passed.
- Web test suite passed.
- Web production build succeeded.
- Remote GitHub Actions CI is the release gate after push.

## v0.2.0 - 2026-07-07

Foundation release for real local collection and human action tracking.

### Added

- GitHub Actions CI for server tests, collector tests, web tests, and web build.
- `apps/collector`, a stdlib-only read-only one-shot Linux collector.
- Collector JSON output using the existing observation batch ingest contract.
- Optional collector POST to the Quipu ingest API.
- SQLite intervention records tied to investigation item IDs.
- `POST /api/investigations/{item_id}/interventions`.
- Investigation detail projection now includes recorded interventions.
- React UI action form for recording interventions.
- React UI panel for recorded intervention history.

### Changed

- Investigation verification now moves to `Waiting for after window` after a
  human intervention is recorded.
- README and roadmap now describe the collector and intervention loop as
  implemented foundations.

### Verified

- Server test suite: 16 tests passed.
- Collector test suite: 1 test passed.
- Web test suite: 1 test passed.
- Web production build succeeded.

### Known Gaps

- Collector is one-shot, not a daemon.
- Before/after comparison windows are not computed yet.
- Collector skips unavailable hardware signals instead of forcing complete
  device coverage.

## v0.1.0 - 2026-07-07

Initial local-first prototype for team workstation health investigation.

### Added

- FastAPI ingest API with token-protected observation batch ingestion.
- SQLite WAL persistence for devices, metrics, and event summaries.
- Rule-based fleet analysis for thermal, stale-agent, reboot, storage, and
  graphics/session signals.
- Investigation workflow API:
  - `GET /api/investigations/queue`
  - `GET /api/investigations/{item_id}`
- Vite React UI centered on the DTIHAVR flow:
  Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report.
- Investigation Queue, evidence timeline, hypotheses, suggested actions,
  verification summary, and report draft surfaces.
- Deterministic three-device sample fixture for local development.
- GitHub issue templates, pull request template, contribution notes, and
  security policy.

### Verified

- Server test suite: 14 tests passed.
- Web test suite: 1 test passed.
- Web production build succeeded.

### Known Gaps

- Native Linux collector is not implemented yet.
- Intervention records are suggested, not persisted yet.
- Before/after verification windows are not persisted yet.
- AI-assisted analysis is intentionally deferred; current findings are
  deterministic and rule-based.
