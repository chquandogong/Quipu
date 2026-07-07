# Changelog

All notable changes to Quipu are documented in this file.

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
