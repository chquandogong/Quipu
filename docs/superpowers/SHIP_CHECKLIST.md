# Quipu Ship Checklist

> Status: v0.13.0 release checklist for device-first fleet UI and Windows telemetry collection
> Date: 2026-07-09
> Owner: chquan
> Release: v0.13.0

## Scope

Included:

- FastAPI ingest API.
- SQLite persistence.
- Deterministic sample fleet data.
- Rule-based fleet and investigation projections.
- Investigation queue and detail API.
- React investigation-first UI.
- Korean default README, English README, and Simplified Chinese README.
- Korean user manual for operators and first-time users.
- GitHub Actions CI.
- GitHub Actions runtime version patch.
- Read-only Linux collector.
- Persistent intervention records.
- Intervention recording UI.
- Before/after intervention verification.
- Verification result UI.
- Command Center first viewport and hover/focus expansion panels.
- High-contrast dark command theme.
- Core signal console for CPU package temperature, 1-minute/5-minute/15-minute
  load average, NVMe temperature, and Wi-Fi signal.
- Telemetry Matrix for CPU Profile, Memory Used, Network Events, Reconnect
  History, Thermal Throttling, Fan RPM, NVMe Health, NVMe Capacity, NVMe I/O,
  Disk Health, Battery Power, Wi-Fi Link, Kernel Warnings, and Agent Freshness.
- Hover/focus metric explanations for CPU package temperature, load average,
  NVMe temperature, and Wi-Fi signal.
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
- Collector systemd service and five-minute timer files.
- Collector environment example and wrapper script.
- Dry-run install and uninstall scripts for collector systemd files.
- Collector offline local ring buffer, flush-before-current-send, flush limit,
  and retry backoff.
- Expanded collector markers for graphics, memory, update, and reboot events.
- Device enrollment API.
- Device display aliases stored as `display_name` and shown beside hostnames.
- CPU model stored as `cpu_model` and shown through CPU Profile telemetry.
- Device-bound ingest tokens.
- Token rotation and revocation APIs.
- Schema version endpoint.
- Team handoff notes API and UI.
- Pattern overview API and Pattern Explorer UI grouped by category, model, and
  kernel.
- Operations Rail for agent freshness, offline buffering, enrollment guard,
  and pattern radar.
- Metric Ledger breakdown chips for load average, CPU package/core sensors,
  NVMe devices/capacity/I/O, and Wi-Fi interfaces/link bitrate.
- Intel Core Ultra 5 125H CPU core grouping for P, E, and LP-E core
  temperature sensors when the observed sensor IDs match that topology.
- Collector CPU topology, Wi-Fi Rx/Tx link bitrate, NVMe namespace capacity,
  and NVMe read/write bytes/sec telemetry.
- Collector state directory for sample-to-sample NVMe throughput calculation.
- Local-notebook-only collector workflow documented after deleting sample data.
- Multi-notebook collector workflow documented for LAN server collection.
- Unified `Project info` metadata chip.
- Consistent hover/focus explanation popovers across status, metric, coverage,
  operations, telemetry, workflow, and fleet surfaces.
- Device-first `Devices` list with alias/hostname, hardware label, metric/event
  counts, last-seen time, issue summary, and risk.
- `Device Issues` list scoped to the selected device.
- Healthy device detail view with no active investigation item required.
- Fleet Brief `Open issues` wording instead of `Queue cases`.
- Compatible Windows collector documentation and manual verification command.
- Best-effort Windows collector metrics for CPU core/thread counts, memory
  usage, battery charge/AC state, Wi-Fi signal/link speed, NVMe capacity, and
  ACPI thermal zones when exposed by Windows.
- Private LAN CORS allowance for Vite UI origins on ports `5173` and `5174`.
- Preservation of existing `display_name` and `cpu_model` when later batches
  omit optional metadata.
- Removed duplicate creator/reference image drawer from the working UI.
- Visible Made by, About, and Version metadata in one compact chip.
- Project docs, GitHub templates, contribution notes, and security policy.

Excluded:

- Actual host systemd service/timer installation during verification.
- Remote repair or remote command execution.
- AI-generated conclusions.
- Package publishing.
- Production deployment.

## Tests

- Server tests: `.venv/bin/python -m pytest` -> 37 passed, 1 Starlette deprecation warning.
- Collector tests: `pytest -v` -> 21 passed.
- Web tests: `npm test -- --run` -> 3 passed.
- Web build: `npm run build` -> succeeded.
- Whitespace check: `git diff --check` -> passed.
- Browser DOM smoke check: `Version v0.13.0`, `Devices`, `Device Issues`,
  `우분투 · chquan-17ZD90SP-GX56K`, `윈도우 · DOGU_CHQUAN`, and `Telemetry Matrix`
  rendered from the LAN UI without `Failed to fetch`.

Evidence source:

- Latest verified local commit before release prep: v0.13.0 release candidate.

## Risks

Known risks:

- Collector coverage is best-effort because Linux sensor exposure varies by
  machine.
- Wi-Fi link bitrate depends on `iw` availability and an active wireless link;
  it is not an internet speed test.
- NVMe read/write throughput requires at least two collector samples for the
  same device.
- Fan RPM and NVMe SMART-lite coverage are best-effort because Linux hardware
  exposure varies by machine.
- systemd operations files are included, but CI does not mutate host systemd.
- Offline buffering is local-file based and bounded; production retention
  policy still needs team configuration.
- Enrollment tokens are stored as hashes, but role-aware admin auth is still a
  future hardening item.
- Current analysis is deterministic and intentionally conservative.
- Windows telemetry coverage depends on the Windows task running the v0.13.0
  collector package. The current observed Windows device is visible, but an
  older task may keep sending only smoke-level telemetry until the release is
  installed and the task is restarted on that machine.
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
- Move forward with a patch tag such as `v0.13.1` for code or documentation fixes.
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
- New release tag exists locally and remotely.
- GitHub release exists for the new tag.
- Repository visibility is public after audit.

## Documents

- README: updated for device-first UI, Windows best-effort telemetry, LAN UI
  access, and rollout guidance.
- User manual: includes Windows collector verification and updated screen guide.
- Dashboard: current v0.13.0 release state recorded.
- Roadmap: device-first, Windows telemetry, and connected-laptop rollout tracks
  recorded.
- Changelog: `v0.13.0` prepared.
- Security policy: present.

## Final Judgment

GitHub release is ready for `v0.13.0` after the local test/build/browser checks
pass. Windows full telemetry display on the currently connected laptop requires
deploying this release to that laptop and restarting its scheduled task.

Public repository visibility is allowed after sensitive-content audit.
Package publishing, production deployment, destructive git operations, and
remote repair remain outside this approval.
