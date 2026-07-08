# Collector Systemd Operations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight, testable systemd operations kit for running the
Quipu collector on Linux team workstations.

**Architecture:** Keep collector behavior in the existing Python CLI. Add
repo-contained operations assets under `apps/collector/ops`, root-level
install/uninstall scripts that can run in dry-run mode, and tests that validate
the files without mutating the host.

**Tech Stack:** Bash, systemd unit/timer files, Python pytest, existing Quipu
collector CLI.

---

## Files

- Create: `apps/collector/ops/bin/quipu-collector-run`
- Create: `apps/collector/ops/collector.env.example`
- Create: `apps/collector/ops/systemd/quipu-collector.service`
- Create: `apps/collector/ops/systemd/quipu-collector.timer`
- Create: `scripts/install-collector-systemd.sh`
- Create: `scripts/uninstall-collector-systemd.sh`
- Create: `apps/collector/tests/test_ops_packaging.py`
- Modify: `apps/collector/pyproject.toml`
- Modify: `apps/collector/src/quipu_collector/__init__.py`
- Modify: `apps/server/pyproject.toml`
- Modify: `apps/server/src/quipu_server/app.py`
- Modify: `apps/web/package.json`
- Modify: `apps/web/package-lock.json`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `README.md`, `README.en.md`, `README.zh-CN.md`
- Modify: `CHANGELOG.md`, `docs/superpowers/DASHBOARD.md`,
  `docs/superpowers/ROADMAP.md`, `docs/superpowers/SHIP_CHECKLIST.md`

## Checklist

- [ ] Add failing ops packaging tests for service, timer, env example, wrapper,
      and dry-run scripts.
- [ ] Run collector tests and confirm the new ops tests fail because files do
      not exist.
- [ ] Add systemd unit, timer, env example, wrapper, install script, and
      uninstall script.
- [ ] Run collector tests and confirm ops packaging tests pass.
- [ ] Bump server, collector, and web versions to `0.8.0`.
- [ ] Update README translations with systemd operations examples.
- [ ] Update changelog, dashboard, roadmap, and ship checklist.
- [ ] Run server tests, collector tests, web tests, web build, diff check,
      sensitive-content scan, CLI smoke, and browser screenshot.
- [ ] Commit, push, tag `v0.8.0`, and publish GitHub release.

## Verification Commands

```bash
.venv/bin/python -m pytest apps/collector/tests
.venv/bin/python -m pytest apps/server/tests
cd apps/web && npm test -- --run && npm run build
git diff --check
```
