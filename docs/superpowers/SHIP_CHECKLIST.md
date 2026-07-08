# Quipu Ship Checklist

> Status: release candidate approved for GitHub release and public visibility after audit
> Date: 2026-07-08
> Owner: chquan
> Release: v0.7.0

## Scope

Included:

- FastAPI ingest API.
- SQLite persistence.
- Deterministic sample fleet data.
- Rule-based fleet and investigation projections.
- Investigation queue and detail API.
- React investigation-first UI.
- Korean default README, English README, and Simplified Chinese README.
- GitHub Actions CI.
- GitHub Actions runtime version patch.
- Read-only Linux collector.
- Persistent intervention records.
- Intervention recording UI.
- Before/after intervention verification.
- Verification result UI.
- Command Center first viewport and hover/focus expansion panels.
- High-contrast dark command theme.
- Core signal console for CPU package temperature, 1-minute load average, NVMe
  temperature, and Wi-Fi signal.
- Telemetry Matrix for Memory Used, Network Events, Reconnect History, Thermal
  Throttling, Fan RPM, NVMe Health, Disk Health, Battery Power, Kernel Warnings,
  and Agent Freshness.
- Hover/focus metric explanations for CPU package temperature, 1-minute load
  average, NVMe temperature, and Wi-Fi signal.
- Best-effort collector summaries for kernel thermal throttling and
  NetworkManager reconnect/disconnect events.
- Event-specific findings for thermal throttling and network reconnects.
- Root filesystem usage, battery capacity, and AC online collector metrics.
- Best-effort kernel storage and power warning summaries.
- Event-specific findings for storage health and battery/power issues.
- Fan RPM and NVMe SMART-lite health collector metrics.
- Storage findings for NVMe critical-warning, spare, lifetime usage, and media
  error signals.
- Collector dry-run mode.
- Collector interval and iterations mode for lightweight supervised operation.
- Structured collector JSON error output.
- Removed duplicate creator/reference image drawer from the working UI.
- Visible Made by, About, and Version metadata chips.
- Project docs, GitHub templates, contribution notes, and security policy.

Excluded:

- Packaged collector daemon files.
- systemd service/timer installation.
- Offline local ring buffer.
- Remote repair or remote command execution.
- AI-generated conclusions.
- Package publishing.
- Production deployment.

## Tests

- Server tests: `pytest -v` -> 27 passed, 1 Starlette deprecation warning.
- Collector tests: `pytest -v` -> 7 passed.
- Web tests: `npm test` -> 1 passed.
- Web build: `npm run build` -> succeeded.
- Whitespace check: `git diff --check` -> passed.

Evidence source:

- Latest verified local commit before release prep: feature branch final
  verification.

## Risks

Known risks:

- Collector coverage is best-effort because Linux sensor exposure varies by
  machine.
- Fan RPM and NVMe SMART-lite coverage are best-effort because Linux hardware
  exposure varies by machine.
- The collector operation loop is CLI-level only; production supervisor
  packaging is not included yet.
- Current analysis is deterministic and intentionally conservative.
- Verification uses a fixed 30-minute window.
- `npm ci` reports existing transitive web dependency vulnerabilities; no public
  production deployment is included in this release.
- Public creator/reference images are not shown in the working UI; provenance
  remains in compact metadata.

Approved risks:

- User explicitly requested autonomous continuation; this release follows the
  approved commit, tag, push, and release flow.
- GitHub release is approved for this release cycle.
- Public repository visibility is approved after sensitive-content audit.

Unapproved risks:

- Package publishing.
- Production deployment.
- Remote execution on team machines.

## Rollback

Rollback method:

- Delete or supersede the private GitHub release if the release note is wrong.
- Move forward with a patch tag such as `v0.7.1` for code or documentation fixes.
- Avoid force-push and history rewrite.

Rollback owner:

- chquan.

Rollback conditions:

- Release points to the wrong commit.
- Security-sensitive content is accidentally included.
- Verification fails after push.

## Monitoring

Check after release:

- GitHub repository URL resolves.
- `main` branch is pushed.
- `v0.7.0` tag exists locally and remotely.
- GitHub release exists for `v0.7.0`.
- Repository visibility is public after audit.

## Documents

- README: current.
- Dashboard: current release state recorded.
- Roadmap: collector operation loop recorded.
- Changelog: `v0.7.0` prepared.
- Security policy: present.

## Final Judgment

GitHub release is allowed for `v0.7.0`.

Public repository visibility is allowed after sensitive-content audit.
Package publishing, production deployment, destructive git operations, and
remote repair remain outside this approval.
