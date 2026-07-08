# Disk And Battery Telemetry Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use verification-before-completion
> before claiming completion. This plan is intentionally small and can be
> executed in one session.

Date: 2026-07-08
Release target: v0.5.0

## Checklist

- [x] Add failing tests for collector battery metrics, storage events, and
      power events.
- [x] Add failing tests for server storage/power findings and queue next steps.
- [x] Add failing web test assertions for `Disk Health` and `Battery Power`.
- [x] Implement read-only disk and power metrics in collector.
- [x] Implement storage and power kernel event classification.
- [x] Implement storage and battery/power findings in server analysis.
- [x] Add Telemetry Matrix tiles for disk and battery power.
- [x] Update fixture data, versions, README translations, changelog, dashboard,
      roadmap, and ship checklist.
- [x] Run Python tests, web tests, build, diff check, secret scan, live UI
      screenshot.
- [ ] Commit, push, tag `v0.5.0`, and publish release notes.

## Verification Commands

```bash
.venv/bin/python -m pytest apps/collector/tests
.venv/bin/python -m pytest apps/server/tests
cd apps/web && npm test -- --run && npm run build
git diff --check
```
