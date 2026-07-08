# Changelog

All notable changes to Quipu are documented in this file.

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
