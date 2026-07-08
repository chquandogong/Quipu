# Collector Operation Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add operation-friendly collector CLI modes for v0.7.0 while keeping
the collector read-only, stdlib-only, and one-shot by default.

**Architecture:** `apps/collector/src/quipu_collector/__main__.py` owns CLI
parsing and the operation loop. Tests inject fake collect/send/sleep functions
so interval behavior is deterministic and fast. No server schema, web UI, or
collector signal contract changes are required.

**Tech Stack:** Python stdlib argparse/json/time, pytest, existing Quipu
collector package.

---

## Files

- Modify: `apps/collector/src/quipu_collector/__main__.py`
- Create: `apps/collector/tests/test_cli.py`
- Modify: `apps/collector/pyproject.toml`
- Modify: `apps/collector/src/quipu_collector/__init__.py`
- Modify: `apps/server/pyproject.toml`
- Modify: `apps/server/src/quipu_server/app.py`
- Modify: `apps/web/package.json`
- Modify: `apps/web/package-lock.json`
- Modify: `apps/web/src/App.tsx`
- Modify: `README.md`, `README.en.md`, `README.zh-CN.md`
- Modify: `CHANGELOG.md`, `docs/superpowers/DASHBOARD.md`,
  `docs/superpowers/ROADMAP.md`, `docs/superpowers/SHIP_CHECKLIST.md`

## Checklist

- [x] Add failing CLI tests for default one-shot output, dry-run skip-send,
      interval iteration count, and structured error output.
- [x] Run collector CLI tests and confirm they fail for missing options.
- [x] Implement CLI loop with injected collect/send/sleep callables.
- [x] Run collector tests and confirm CLI tests pass.
- [x] Bump server, collector, and web versions to `0.7.0`.
- [x] Update README translations with collector operation examples.
- [x] Update changelog, dashboard, roadmap, and ship checklist.
- [x] Run server tests, collector tests, web tests, web build, diff check,
      sensitive-content scan, and CLI smoke commands.
- [ ] Commit, push, tag `v0.7.0`, and publish GitHub release.

## Verification Commands

```bash
.venv/bin/python -m pytest apps/collector/tests
.venv/bin/python -m pytest apps/server/tests
cd apps/web && npm test -- --run && npm run build
git diff --check
```
