# Before/After Intervention Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add evidence-backed before/after verification for recorded Quipu interventions.

**Architecture:** Keep verification as a derived projection. Add repository window reads for metrics and events, compute deterministic comparison results in `analysis.py`, and expose them through the existing investigation detail API and React UI.

**Tech Stack:** Python 3.12, FastAPI, SQLite, pytest, React, TypeScript, Vitest.

---

## File Structure

- Modify `apps/server/src/quipu_server/repository.py`: add read-only observation window queries.
- Modify `apps/server/src/quipu_server/analysis.py`: add deterministic comparison helpers and attach results to interventions.
- Modify `apps/server/src/quipu_server/app.py`: pass observation windows into detail projection.
- Modify `apps/server/tests/test_interventions.py`: cover repository query and API detail projection.
- Modify `apps/server/tests/test_investigations.py`: cover pure analysis statuses.
- Modify `apps/web/src/types.ts`: add verification result types.
- Modify `apps/web/src/App.tsx`: render verification result details.
- Modify `apps/web/src/App.test.tsx`: assert comparison result rendering.
- Modify `apps/web/src/styles.css`: add compact comparison styling.
- Modify release docs and package versions for `v0.3.0`.

## Tasks

### Task 1: Server Observation Window Query

- [x] Write a failing repository test that ingests before/after metric samples and expects `list_observations_for_intervention()` to return samples split by side.
- [x] Run `cd apps/server && .venv/bin/python -m pytest tests/test_interventions.py::test_list_observations_for_intervention_splits_before_and_after_windows -v` and confirm it fails because the function is missing.
- [x] Add `list_observations_for_intervention(conn, intervention, window_minutes=30)` to `repository.py`.
- [x] Run the focused repository test and confirm it passes.

### Task 2: Analysis Verification Projection

- [x] Write failing analysis tests for `helped` and `insufficient_data` results.
- [x] Run `cd apps/server && .venv/bin/python -m pytest tests/test_investigations.py::test_intervention_verification_marks_thermal_improvement_helped tests/test_investigations.py::test_intervention_verification_requires_before_and_after_samples -v` and confirm both fail because the projection is missing.
- [x] Add verification helpers in `analysis.py` using the 30-minute window rules from the spec.
- [x] Attach `verification_result` to each intervention and make the top-level `verification` panel summarize the latest result.
- [x] Run the focused analysis tests and confirm they pass.

### Task 3: API Detail Integration

- [x] Write a failing API test that records an intervention between two observation batches and expects detail JSON to include `interventions[0].verification_result.status == "helped"`.
- [x] Run `cd apps/server && .venv/bin/python -m pytest tests/test_interventions.py::test_intervention_api_detail_includes_before_after_verification -v` and confirm it fails.
- [x] Update `app.py` to fetch observation windows for listed interventions and pass them into `build_investigation_detail()`.
- [x] Run the focused API test and confirm it passes.

### Task 4: Web Rendering

- [x] Write a failing Vitest assertion that the UI renders `Helped`, `CPU package temperature`, and a negative temperature delta.
- [x] Run `cd apps/web && npm test` and confirm the test fails for missing UI text.
- [x] Add TypeScript types and render verification result cards in `App.tsx`.
- [x] Add CSS for comparison rows and status badges.
- [x] Run `cd apps/web && npm test` and confirm it passes.

### Task 5: Release Prep

- [x] Bump server, collector, and web versions to `0.3.0`.
- [x] Update `CHANGELOG.md`, `README.md`, `README.en.md`, `README.zh-CN.md`, `docs/superpowers/DASHBOARD.md`, `docs/superpowers/ROADMAP.md`, and `docs/superpowers/SHIP_CHECKLIST.md`.
- [x] Run full local verification:
  - `cd apps/server && .venv/bin/python -m pytest -v`
  - `cd apps/collector && .venv/bin/python -m pytest -v`
  - `cd apps/web && npm test`
  - `cd apps/web && npm run build`
  - `git diff --check`
- [ ] Merge to `main`, tag `v0.3.0`, push to the existing private remote, watch GitHub Actions, and create the private release if all verification passes.

## Self-Review

- Spec coverage: repository query, analysis projection, API detail, UI display, docs, and release are all covered.
- Placeholder scan: no placeholder tasks remain.
- Type consistency: `verification_result` is the single added API/UI field name.
