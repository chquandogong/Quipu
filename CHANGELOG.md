# Changelog

All notable changes to Quipu are documented in this file.

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
