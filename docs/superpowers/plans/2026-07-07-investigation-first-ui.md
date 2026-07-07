# Investigation-First UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Quipu's generic fleet-first experience with an investigation-first flow centered on Queue, Incident Detail, hypotheses, actions, verification, and report.

**Architecture:** Keep the existing FastAPI + SQLite + React stack. Add deterministic server-side investigation projections derived from the current fleet snapshots, then make the React UI consume those projections and use the existing fleet overview as supporting context.

**Tech Stack:** Python 3.11+, FastAPI, pytest, Vite, React, TypeScript, Vitest.

---

## Scope

This plan implements the next vertical slice:

- `GET /api/investigations/queue`
- `GET /api/investigations/{item_id}`
- A new React first screen based on DTIHAVR:
  `Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report`
- A selectable investigation queue.
- An incident detail panel with timeline, hypotheses, action suggestions,
  verification status, and report summary.

Deferred:

- Persistent action records.
- User-authored notes.
- Real before/after windows from native agents.
- AI-generated reports.
- Remote commands or repairs.

## Files

- Modify: `apps/server/src/quipu_server/analysis.py`
- Modify: `apps/server/src/quipu_server/app.py`
- Create: `apps/server/tests/test_investigations.py`
- Modify: `apps/web/src/types.ts`
- Modify: `apps/web/src/api.ts`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/styles.css`
- Modify: `README.md`
- Modify: `docs/superpowers/DASHBOARD.md`

---

### Task 1: Server Investigation Projection

- [ ] **Step 1: Write failing server tests**

Create `apps/server/tests/test_investigations.py` with tests that:

- Seed the repository with `sample_batch`.
- Call `build_investigation_queue(list_device_snapshots(conn), now=...)`.
- Assert queue item fields:
  - `id`
  - `priority`
  - `stage`
  - `device_hostname`
  - `why_now`
  - `next_step`
- Call `build_investigation_detail(...)`.
- Assert the detail contains:
  - `item`
  - `timeline`
  - `hypotheses`
  - `actions`
  - `verification`
  - `report`

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest tests/test_investigations.py -v
```

Expected: FAIL because `build_investigation_queue` is not defined.

- [ ] **Step 2: Implement server projection functions**

Modify `apps/server/src/quipu_server/analysis.py`:

- Add `build_investigation_queue(snapshots, now=None)`.
- Add `build_investigation_detail(snapshots, item_id, now=None)`.
- Derive queue items from existing `classify_snapshot` output.
- Generate deterministic IDs as `"{device_id}:{primary_category}"`.
- Map risk to priority:
  - critical -> High
  - warning -> Medium
  - stale -> Medium
  - healthy -> Low
- Generate action text and deterministic verification summaries from the category.

- [ ] **Step 3: Run server projection tests**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest tests/test_investigations.py -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/server/src/quipu_server/analysis.py apps/server/tests/test_investigations.py
git commit -m "feat(server): project investigation workflow"
```

---

### Task 2: Investigation API Endpoints

- [ ] **Step 1: Write failing API tests**

Modify `apps/server/tests/test_api.py` or add new tests to
`apps/server/tests/test_investigations.py`:

- Ingest a valid batch.
- `GET /api/investigations/queue` returns at least one item.
- `GET /api/investigations/{item_id}` returns incident detail.
- Unknown item returns `404`.

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest tests/test_investigations.py -v
```

Expected: FAIL because the API routes do not exist.

- [ ] **Step 2: Implement routes**

Modify `apps/server/src/quipu_server/app.py`:

- Add `GET /api/investigations/queue`.
- Add `GET /api/investigations/{item_id}`.
- Reuse `list_device_snapshots(db)`.
- Return `404` when detail is unavailable.

- [ ] **Step 3: Run server tests**

Run:

```bash
cd apps/server
. .venv/bin/activate
pytest -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/server/src/quipu_server/app.py apps/server/tests/test_investigations.py
git commit -m "feat(server): expose investigation api"
```

---

### Task 3: Investigation-First React UI

- [ ] **Step 1: Write failing UI test**

Modify `apps/web/src/App.test.tsx` so the mocked API provides:

- Fleet overview.
- Investigation queue.
- Investigation detail.

Assert the UI renders:

- `Investigation Queue`
- `Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report`
- The selected queue item hostname.
- `Top hypotheses`
- `Action plan`
- `Verification`
- `Report`

Run:

```bash
cd apps/web
npm test
```

Expected: FAIL because the current UI has no investigation flow sections.

- [ ] **Step 2: Update web contracts and API client**

Modify `apps/web/src/types.ts`:

- Add `InvestigationItem`.
- Add `TimelineEvent`.
- Add `Hypothesis`.
- Add `ActionSuggestion`.
- Add `VerificationSummary`.
- Add `InvestigationDetail`.

Modify `apps/web/src/api.ts`:

- Add `fetchInvestigationQueue()`.
- Add `fetchInvestigationDetail(itemId)`.

- [ ] **Step 3: Implement the new UI**

Modify `apps/web/src/App.tsx`:

- Fetch fleet overview, queue, and selected detail.
- Default to the first queue item.
- Render:
  - DTIHAVR stage rail.
  - Investigation Queue.
  - Incident Detail.
  - Evidence timeline.
  - Top hypotheses.
  - Action plan.
  - Verification.
  - Report summary.
  - Fleet context panel.

Modify `apps/web/src/styles.css`:

- Use dense operational layout.
- Keep cards shallow and not nested.
- Make text fit on desktop and mobile.

- [ ] **Step 4: Run web tests and build**

Run:

```bash
cd apps/web
npm test
npm run build
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/types.ts apps/web/src/api.ts apps/web/src/App.test.tsx apps/web/src/App.tsx apps/web/src/styles.css
git commit -m "feat(web): make investigation queue the primary surface"
```

---

### Task 4: Docs And Final Verification

- [ ] **Step 1: Update docs**

Modify:

- `README.md`
- `docs/superpowers/DASHBOARD.md`

Record that the UI now has an implemented investigation-first slice.

- [ ] **Step 2: Run final verification**

Run:

```bash
git diff --check
cd apps/server
. .venv/bin/activate
pytest -v
cd ../web
npm test
npm run build
cd ../..
git status --short --branch
```

Expected:

- Server tests pass.
- Web tests pass.
- Web build succeeds.
- Working tree is clean after commit.

- [ ] **Step 3: Commit**

```bash
git add README.md docs/superpowers/DASHBOARD.md
git commit -m "docs: mark investigation-first ui implemented"
```

## Self-Review

Spec coverage:

- DTIHAVR flow: Task 3.
- Investigation Queue: Tasks 1, 2, and 3.
- Incident detail: Tasks 1, 2, and 3.
- Hypotheses/actions/verification/report: Tasks 1 and 3.
- Existing fleet overview as supporting context: Task 3.

Intentional gaps:

- Persistent intervention records are deferred.
- AI reports are deferred.
- Native agent collection is deferred.

Placeholder scan:

- No unknown file paths.
- No unspecified commands.
- Deferred items are explicit scope boundaries.

Type consistency:

- Server item/detail shapes are mirrored by TypeScript types.
- Queue IDs use `device_id:category`.
