# Command Center Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current card-heavy first viewport with a command-center layout that makes the next investigation decision obvious.

**Architecture:** Keep the existing React single-file app structure, but replace the top layout sections and remove the image reference drawer. Update styles in place and keep API contracts unchanged.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, CSS, Lucide icons.

---

### Task 1: Test The New First Viewport

**Files:**
- Modify: `apps/web/src/App.test.tsx`

- [ ] **Step 1: Write the failing test**

Add assertions that the command center exists, the old reference drawer does not, and bilingual metric help text appears.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npm test -- --run`

Expected: FAIL because `Investigation command center` and Korean metric help text are not rendered yet.

### Task 2: Implement Command Center Markup

**Files:**
- Modify: `apps/web/src/App.tsx`

- [ ] **Step 1: Remove duplicate visual reference content**

Delete `makerImages`, the reference drawer markup, and unused image/link imports.

- [ ] **Step 2: Add command-center sections**

Add a top command surface with:

- `Inspect now`
- `Why it matters`
- `Do next`
- `Proof needed`
- compact fleet health strip
- compact Workflow Rail for the current DTIHAVR stage and next action

- [ ] **Step 3: Add compact bilingual helper text**

Metric tooltips should use Korean explanation with English technical terms in
parentheses.

### Task 3: Implement Command Center Styling

**Files:**
- Modify: `apps/web/src/styles.css`

- [ ] **Step 1: Replace visual hierarchy**

Remove carousel/reference drawer styles and add command-center, answer-grid,
fleet-brief, and workflow-rail styles.

- [ ] **Step 2: Preserve responsive behavior**

Desktop should show the command surface and queue/detail below. Mobile should
stack without hidden-only hover content.

### Task 4: Docs And Version

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `README.zh-CN.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/superpowers/DASHBOARD.md`
- Modify: package/version files

- [ ] **Step 1: Document the command-center decision**

Explain that creator/reference visuals were removed from the working UI because
they did not support the investigation task.

- [ ] **Step 2: Bump release target to v0.3.2**

Update visible app and package versions.

### Task 5: Verify And Publish

**Files:**
- No source edits unless verification finds a defect.

- [ ] **Step 1: Run full local verification**

Run:

```bash
git diff --check
.venv/bin/python -m pytest apps/server/tests
.venv/bin/python -m pytest apps/collector/tests
cd apps/web && npm test -- --run
cd apps/web && npm run build
```

- [ ] **Step 2: Capture a browser screenshot**

Use the running Vite app to verify the first viewport is readable.

- [ ] **Step 3: Commit and push**

Commit with a focused message and push `main`.
