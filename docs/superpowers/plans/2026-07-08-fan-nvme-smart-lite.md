# Fan And NVMe SMART-Lite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add lightweight fan RPM and NVMe SMART-lite telemetry to Quipu v0.6.0.

**Architecture:** The collector reads only sysfs/hwmon style files and emits
numeric metrics. The analysis layer turns risky NVMe health values into storage
findings. The web UI adds two compact Telemetry Matrix tiles without changing
the main Command Center workflow.

**Tech Stack:** Python collector, FastAPI analysis helpers, Vite React UI,
pytest, Vitest.

---

## Files

- Modify: `apps/collector/src/quipu_collector/collect.py`
- Modify: `apps/collector/tests/test_collect.py`
- Modify: `apps/server/src/quipu_server/analysis.py`
- Modify: `apps/server/tests/test_analysis.py`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `fixtures/ingest/team-sample.json`
- Modify: `README.md`, `README.en.md`, `README.zh-CN.md`
- Modify: `CHANGELOG.md`, `docs/superpowers/DASHBOARD.md`,
  `docs/superpowers/ROADMAP.md`, `docs/superpowers/SHIP_CHECKLIST.md`
- Modify version files for server, collector, and web.

## Checklist

- [x] Write collector failing test for `fan.rpm` and NVMe SMART-lite metrics.
- [x] Run collector test and confirm it fails on missing metrics.
- [x] Implement fan and NVMe SMART-lite metric readers.
- [x] Run collector test and confirm it passes.
- [x] Write server failing tests for NVMe health findings.
- [x] Run server analysis test and confirm it fails on generic/no findings.
- [x] Implement NVMe storage findings.
- [x] Run server analysis test and confirm it passes.
- [x] Write web failing assertions for `Fan RPM`, `NVMe Health`, and v0.6.0.
- [x] Implement web tiles, formatting, and statuses.
- [x] Run web test and confirm it passes.
- [x] Update fixture data, versions, README translations, changelog, dashboard,
      roadmap, and ship checklist.
- [x] Run full server tests, collector tests, web tests, web build,
      `git diff --check`, sensitive-content scan, and browser screenshots.
- [ ] Commit, push, tag `v0.6.0`, and publish GitHub release.

## Verification Commands

```bash
.venv/bin/python -m pytest apps/collector/tests
.venv/bin/python -m pytest apps/server/tests
cd apps/web && npm test -- --run && npm run build
git diff --check
```
