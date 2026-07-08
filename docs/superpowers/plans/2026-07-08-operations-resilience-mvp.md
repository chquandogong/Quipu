# Operations Resilience MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the v0.9.0 operations-resilience MVP covering the eight
requested remaining tracks.

**Architecture:** Extend the existing Python collector with a file spool and
retry flush path, extend the FastAPI/SQLite server with enrollment tokens,
team notes, schema version, and pattern overview, then add compact React
surfaces for operations, handoff, and patterns. Keep all host mutations out of
tests and verification.

**Tech Stack:** Python stdlib, FastAPI, SQLite, pytest, Vite React, Vitest,
systemd file templates.

---

## Files

- Create: `apps/collector/src/quipu_collector/spool.py`
- Create: `apps/collector/tests/test_spool.py`
- Modify: `apps/collector/src/quipu_collector/__main__.py`
- Modify: `apps/collector/src/quipu_collector/collect.py`
- Modify: `apps/collector/tests/test_cli.py`
- Modify: `apps/collector/tests/test_collect.py`
- Modify: `apps/collector/ops/bin/quipu-collector-run`
- Modify: `apps/collector/ops/collector.env.example`
- Modify: `apps/server/src/quipu_server/db.py`
- Modify: `apps/server/src/quipu_server/contracts.py`
- Modify: `apps/server/src/quipu_server/repository.py`
- Modify: `apps/server/src/quipu_server/analysis.py`
- Modify: `apps/server/src/quipu_server/app.py`
- Create: `apps/server/tests/test_enrollment.py`
- Create: `apps/server/tests/test_workflow_patterns.py`
- Modify: `apps/web/src/types.ts`
- Modify: `apps/web/src/api.ts`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/styles.css`
- Modify: package/app versions and release docs.

## Checklist

- [x] Add failing collector spool and CLI offline-buffer tests.
- [x] Implement collector spool, CLI flags, wrapper/env integration, and
      expanded marker parsing.
- [x] Run collector tests and keep them green.
- [x] Add failing server enrollment, workflow note, schema version, and pattern
      overview tests.
- [x] Implement server schema, repository, API, and analysis changes.
- [x] Run server tests and keep them green.
- [x] Add web types/API/UI and focused render assertions for Operations Rail,
      Team Handoff, and Pattern Explorer.
- [x] Update versions to `0.9.0`.
- [x] Update README translations, changelog, dashboard, roadmap, and ship
      checklist.
- [ ] Run full verification, commit, push, tag `v0.9.0`, and publish release.

## Verification Commands

```bash
.venv/bin/python -m pytest apps/collector/tests
.venv/bin/python -m pytest apps/server/tests
cd apps/web && npm test -- --run && npm run build
git diff --check
```
