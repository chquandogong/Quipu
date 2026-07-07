# Dark Telemetry Expansion Implementation Plan

**Goal:** Make Quipu visibly more useful for team workstation investigation by
showing Wi-Fi, memory, network, kernel, and telemetry freshness signals in a
high-contrast dark UI.

**Architecture:** Keep the current React/Vite app and existing API contract.
Build derived UI tiles from `latest_metrics`, `timeline`, and `fleet_context`.

---

### Task 1: Test First

**Files:**
- `apps/web/src/App.test.tsx`

- [x] Add fixture coverage for Load, NVMe, Memory, Wi-Fi, network events, and
  kernel warnings.
- [x] Assert `.page-command-dark`.
- [x] Assert Wi-Fi metric help.
- [x] Assert `Telemetry coverage matrix`.
- [x] Assert Memory, Network Events, and Kernel Warnings are visible.
- [x] Run web test and confirm it fails before implementation.

### Task 2: Extend Telemetry UI

**Files:**
- `apps/web/src/App.tsx`

- [x] Add Wi-Fi signal as a core metric.
- [x] Add metric formatting for `dbm`.
- [x] Add status classification for core signals.
- [x] Add first-glance signal console.
- [x] Add Telemetry Matrix tiles for Memory Used, Network Events, Kernel
  Warnings, and Agent Freshness.

### Task 3: Redesign Theme

**Files:**
- `apps/web/src/styles.css`

- [x] Switch to dark color scheme.
- [x] Increase Command Center contrast.
- [x] Add signal status styles for nominal, watch, critical, and missing.
- [x] Add responsive layouts for signal console and telemetry matrix.

### Task 4: Data And Docs

**Files:**
- `fixtures/ingest/team-sample.json`
- `README.md`
- `README.en.md`
- `README.zh-CN.md`
- `CHANGELOG.md`
- `docs/superpowers/*`
- version files

- [x] Expand fixture metrics for local demo clarity.
- [x] Explain why three metrics are not enough for the team product.
- [x] Bump release target to `v0.3.3`.

### Task 5: Verify And Release

- [x] Run whitespace check.
- [x] Run server tests.
- [x] Run collector tests.
- [x] Run web tests.
- [x] Run web build.
- [x] Inspect browser screenshot.
- [ ] Commit, push, tag, and create GitHub release.
