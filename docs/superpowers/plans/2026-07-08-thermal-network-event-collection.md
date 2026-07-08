# Thermal And Network Event Collection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote thermal throttling and network reconnect history from UI extension slots into real read-only collector events and rule-based investigation findings.

**Architecture:** Keep the existing observation batch contract. Add collector log parsing and best-effort journalctl reads that emit compact `events`, extend server rule classification for event-specific findings, and extend the React Telemetry Matrix with direct throttling/reconnect tiles.

**Tech Stack:** Python stdlib collector, FastAPI/Pydantic server contracts, SQLite repository, React/TypeScript/Vite, Vitest, pytest.

---

### Task 1: Collector Event Tests

**Files:**
- Modify: `apps/collector/tests/test_collect.py`

- [x] **Step 1: Write failing collector test**

Create fake log excerpts under the test root:

```text
var/log/quipu/kernel.log
var/log/quipu/networkmanager.log
```

Expected events:

- `thermal` warning from a thermal throttling line.
- `network` warning from a NetworkManager reconnect/disconnect line.

- [x] **Step 2: Run collector test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest apps/collector/tests/test_collect.py
```

Expected: fail because collector currently always emits `events: []`.

### Task 2: Collector Event Implementation

**Files:**
- Modify: `apps/collector/src/quipu_collector/collect.py`

- [x] **Step 1: Add event parser helpers**

Add helpers that classify compact log lines into Quipu event dictionaries.

- [x] **Step 2: Add file and journal sources**

Read root-scoped log excerpts for tests and best-effort `journalctl` output for
real local runs.

- [x] **Step 3: Include parsed events in `collect_observation`**

Return `events` alongside existing metrics.

- [x] **Step 4: Run collector test**

Run:

```bash
.venv/bin/python -m pytest apps/collector/tests/test_collect.py
```

Expected: pass.

### Task 3: Server Finding Tests And Rules

**Files:**
- Modify: `apps/server/tests/test_analysis.py`
- Modify: `apps/server/src/quipu_server/analysis.py`

- [x] **Step 1: Write failing server tests**

Add tests for:

- thermal throttling event -> `Thermal throttling reported`
- network reconnect event -> `Network reconnect reported`

- [x] **Step 2: Implement event-specific findings**

Add lightweight event classification before falling back to generic warning
events.

- [x] **Step 3: Run server tests**

Run:

```bash
.venv/bin/python -m pytest apps/server/tests
```

Expected: pass.

### Task 4: Web Telemetry Matrix Tests And UI

**Files:**
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/App.tsx`

- [x] **Step 1: Write failing web assertions**

Assert `Thermal Throttling`, `Reconnect History`, and their warning counts are
visible.

- [x] **Step 2: Extend telemetry tile builders**

Add direct tiles for throttling and reconnect history based on the selected
investigation timeline.

- [x] **Step 3: Run web tests**

Run:

```bash
cd apps/web && npm test -- --run
```

Expected: pass.

### Task 5: Fixtures, Docs, Version, Release

**Files:**
- Modify: `fixtures/ingest/team-sample.json`
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `README.zh-CN.md`
- Modify: `CHANGELOG.md`
- Modify: package/version files

- [x] **Step 1: Expand fixture events**

Use realistic thermal throttling and NetworkManager reconnect summaries.

- [x] **Step 2: Bump to v0.4.0**

Update server, collector, and web versions.

- [x] **Step 3: Verify**

Run full local verification:

```bash
git diff --check
.venv/bin/python -m pytest apps/server/tests
.venv/bin/python -m pytest apps/collector/tests
cd apps/web && npm test -- --run
cd apps/web && npm run build
```

- [ ] **Step 4: Publish**

Commit, push, tag `v0.4.0`, watch CI, and create the GitHub release.
