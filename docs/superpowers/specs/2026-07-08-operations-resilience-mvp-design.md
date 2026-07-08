# Operations Resilience MVP Design

Date: 2026-07-08
Release target: v0.9.0
Owner: chquan

## Problem

Quipu can collect and schedule workstation telemetry, but a real team workflow
still fails if the server is briefly offline, tokens are shared forever, event
markers are too shallow, or the UI cannot explain whether the problem is the
collector, network, server, device class, or human handoff.

## Decision

Build a single v0.9.0 operations-resilience vertical slice that covers the
eight requested tracks at MVP depth:

1. Offline local ring buffer and retry flush.
2. Device enrollment and token rotation API.
3. Non-mutating systemd verification workflow.
4. Reboot/update/graphics/session/memory marker expansion.
5. UI operations and stale-telemetry explanation surface.
6. Server hardening basics: schema versioning and runbook documentation.
7. Team workflow notes for investigations.
8. Pattern explorer grouped by category, model, and kernel.

## Alternatives

| Option | Description | Strength | Weakness | Decision |
| --- | --- | --- | --- | --- |
| Sequential minor releases | v0.9 buffer, v0.10 enrollment, etc. | Lower risk per release | User asked to continue through item 8 | Rejected |
| Full production platform | Complete RBAC, migrations, packages, production deploy | Product-complete | Too large and unsafe in one autonomous pass | Rejected |
| MVP vertical slice | Minimal tested version of all eight tracks | Broad coverage, still reviewable | Some areas remain intentionally shallow | Selected |

## Scope

Included:

- File-based collector spool with max batch count pruning.
- Collector CLI flags for offline buffering, spool flushing, and retry backoff.
- systemd wrapper/env integration for the spool directory and buffer flags.
- Server token enrollment, rotation, revocation, and per-device ingest checks.
- Collector log marker expansion for reboot, update, graphics/session, and
  memory pressure.
- Pattern overview API.
- Investigation note API for team handoff.
- UI sections for Operations Rail, Team Handoff, and Pattern Explorer.
- Schema version tracking and runbook/checklist updates.

Excluded:

- Actual host systemd enablement on this machine.
- Production deployment.
- Package publishing.
- Full RBAC or multi-user auth.
- Remote repair actions.

## Data Flow

```text
collector batch
  -> flush old spool files
  -> send current batch
  -> on failure, write JSON file to spool
  -> next run retries oldest files first
  -> server idempotent ingest ignores duplicate batch ids
  -> UI shows spool/freshness/pattern/handoff context
```

## Safety And Gates

- Local file writes are limited to configured collector spool directories.
- Real systemd installation is documented and dry-run verified, not executed.
- Token enrollment endpoints require the existing admin/dev token.
- Raw logs are still summarized; full raw logs are not uploaded.

## Acceptance Criteria

- Collector tests prove enqueue, prune, flush success, flush failure retention,
  CLI buffering on send failure, and flush-before-send.
- Server tests prove enrollment token ingest, rotation invalidation, note
  persistence, pattern overview, and schema version.
- Web tests prove operations, handoff, and pattern surfaces render.
- Full local and CI verification pass before release.
