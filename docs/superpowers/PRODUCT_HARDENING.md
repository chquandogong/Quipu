# Product Hardening Roadmap

Date: 2026-07-08

This document tracks the product-grade work that remains after the local-first
prototype. It separates work that can be prepared in-repo from work that is
gated because it mutates hosts, publishes packages, or changes production
infrastructure.

## Guiding Principle

Quipu should stay useful without AI, without remote repair commands, and
without privileged collectors. Production hardening should make evidence
handling safer and team workflow clearer before adding heavier analytics.

## Execution Order

1. Team collector rollout runbook.
2. Redaction, retention, backup, and restore policies.
3. Role-aware team workflow states.
4. Package publishing preparation.
5. Production deployment guide.
6. Postgres adapter.
7. Long-term baseline and recurrence analytics.
8. Optional AI analysis layer.

## 1. Team Collector Rollout

Status: prepared, host installation gated.

In-repo preparation:

- Keep the systemd timer path documented in the README.
- Require per-device enrollment tokens for team machines.
- Record device id, hostname, owner/team, and collector install date in the
  team inventory outside the Quipu database until RBAC lands.

Acceptance criteria:

- A new Linux laptop can run one dry-run batch.
- A new Linux laptop can send one authenticated batch with a device-bound token.
- The UI shows the device in the queue or fleet summary within five minutes.

Safety gate:

- Do not install timers on actual team machines without owner approval.

## 2. Redaction And Retention

Status: design needed before team rollout.

Default policy:

- Store metric values as-is.
- Store event summaries only, not full raw logs.
- Truncate event summaries to bounded length.
- Treat raw refs as local references, not uploaded log bodies.
- Retain local SQLite data for 30 days by default in a team setting unless the
  team explicitly chooses a longer diagnostic window.

Implementation tasks:

- Add configurable retention days.
- Add a cleanup command or admin endpoint.
- Add redaction filters for usernames, home paths, SSIDs, IP addresses, and MAC
  addresses before event summaries are persisted.
- Add tests for common sensitive-token patterns.

## 3. Backup And Restore

Status: documentable now, automation later.

SQLite backup command:

```bash
sqlite3 /home/chquan/Quipu/data/quipu.sqlite3 ".backup '/home/chquan/Quipu/backups/quipu-$(date +%Y%m%d-%H%M%S).sqlite3'"
```

Restore flow:

```bash
systemctl --user stop quipu-server.service 2>/dev/null || true
cp /home/chquan/Quipu/backups/quipu-YYYYMMDD-HHMMSS.sqlite3 /home/chquan/Quipu/data/quipu.sqlite3
systemctl --user start quipu-server.service 2>/dev/null || true
```

Acceptance criteria:

- Backup can be created while the API is idle.
- Restore is tested against a copy before replacing the active database.
- WAL files are handled consistently by stopping the server or using the SQLite
  backup API.

## 4. Role-Based Team Workflow

Status: not implemented.

Initial roles:

- Viewer: read fleet, investigations, patterns, and reports.
- Operator: record interventions and handoff notes.
- Maintainer: enroll devices, rotate/revoke collector tokens.
- Admin: retention, backup/restore, deployment settings.

Workflow states:

- Triage.
- Assigned.
- Investigating.
- Waiting for after-window.
- Verified.
- Reported.

Acceptance criteria:

- UI shows owner, role, and next responsibility without increasing first-screen
  clutter.
- API rejects write actions from roles that should be read-only.

## 5. Package Publishing Preparation

Status: gated for actual publishing.

Preparation tasks:

- Split server, collector, and web release artifacts.
- Add versioned changelog entries per artifact.
- Add install checks for Python version, Linux environment, writable spool path,
  and API reachability.
- Add signed release artifact plan before public package distribution.

Safety gate:

- Do not run `npm publish`, PyPI publish, container registry push, or release
  automation without explicit approval.

## 6. Production Deployment

Status: documentation needed, deployment gated.

Recommended first deployment:

- Single private Linux host.
- SQLite WAL.
- Reverse proxy with TLS on a private hostname.
- Device-bound collector tokens.
- Daily SQLite backup.
- 30-day default retention.

Future deployment:

- Postgres for multi-user or higher fleet concurrency.
- Object storage only if sanitized report exports or attachments are added.

Safety gate:

- No production deployment, migration, or infrastructure mutation without
  explicit approval.

## 7. Postgres Adapter

Status: future implementation.

Approach:

- Keep repository functions as the boundary.
- Add a second adapter behind the same repository contract.
- Add cross-adapter tests for ingest, queue, interventions, notes, enrollment,
  and pattern overview.
- Migrate only after SQLite behavior is locked by tests.

## 8. Deeper Analytics

Status: first component-signature slice implemented.

Implemented:

- Cooling-response finding for hot CPU plus low fan RPM.
- Component pattern grouping for GPU, Wi-Fi, and NVMe signatures.

Next tasks:

- Collect richer fan labels when hwmon exposes names.
- Extract Wi-Fi driver/hardware identity without root where Linux exposes it.
- Add baseline windows for CPU temp, load, fan RPM, Wi-Fi signal, and warning
  recurrence.
- Add recurrence score by device, category, component, kernel, and model.

## 9. Optional AI Analysis Layer

Status: future, evidence-gated.

Rules:

- AI never replaces deterministic findings.
- AI can draft summaries only from already persisted evidence.
- AI output must cite metric/event/report fields.
- AI suggestions must be labeled as suggestions, not actions.
- Redaction must run before any external model call.

First useful AI feature:

- Draft a team-readable incident summary from selected investigation detail,
  timeline, interventions, verification result, and pattern context.
