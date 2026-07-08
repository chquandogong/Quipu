# Collector Systemd Operations Design

Date: 2026-07-08
Release target: v0.8.0
Owner: chquan

## Problem

Quipu v0.7.0 can run the collector in one-shot, dry-run, and interval modes,
but a team still needs a repeatable way to install and supervise it on Linux
workstations. Manual terminal loops are useful for smoke tests, not reliable
team operation.

## Users

- Initial operator: a technical team member installing Quipu on 3-20 Linux
  laptops or developer workstations.
- Initial device: one Linux workstation that can reach a self-hosted Quipu API.

## Alternatives

| Option | Description | Strength | Weakness | Decision |
| --- | --- | --- | --- | --- |
| Docs only | Add copy-paste systemd snippets to README | Fastest | Easy to drift, hard to test | Rejected |
| Repo-contained ops kit | Add unit/timer/env/wrapper/install scripts with tests | Practical, testable, lightweight | Not a distro package | Selected |
| Full package | Build deb/rpm/pipx packaging and post-install hooks | Most polished | Too heavy before real fleet feedback | Deferred |

## Scope

Included:

- A systemd `oneshot` service that runs one collector batch.
- A systemd timer that runs the service every 5 minutes by default.
- An `/etc/quipu/collector.env` example file for server URL, token, root, and
  optional device ID.
- A small wrapper script that validates required config and builds collector
  CLI arguments safely.
- Dry-run capable install and uninstall scripts.
- Tests that validate the ops files without mutating the host.
- README, changelog, dashboard, roadmap, and release checklist updates.

Excluded:

- Running `systemctl` on this machine.
- Creating users or changing host services during verification.
- Package publishing, deb/rpm builds, pipx release automation.
- Offline local ring buffer.
- Remote repair actions.

## Functional Requirements

| ID | Requirement | Acceptance Criteria |
| --- | --- | --- |
| OPS-1 | The collector can be scheduled by systemd | Unit file is `Type=oneshot`; timer points to the unit |
| OPS-2 | Secrets and endpoints are configured outside the unit | Unit uses `EnvironmentFile=/etc/quipu/collector.env` |
| OPS-3 | Config is validated before invoking collector | Wrapper fails if server URL or token is missing |
| OPS-4 | Install/uninstall can be previewed safely | Scripts support `--dry-run` and do not require root in dry-run |
| OPS-5 | Host mutation is not part of CI verification | Tests parse files and run script syntax/dry-run checks only |

## Non-Functional Requirements

- Security: the service remains read-only in intent and uses basic systemd
  hardening settings.
- Maintainability: ops files live under `apps/collector/ops`; root scripts are
  thin entry points.
- Portability: scripts use Bash and standard Linux install/systemctl commands.
- Scale envelope: supports one collector instance per workstation for the
  initial 3-20 device fleet. Multi-tenant per-host collectors are out of scope.

## Data And Flow

```text
systemd timer
      |
      v
quipu-collector.service
      |
      v
/usr/local/lib/quipu/quipu-collector-run
      |
      v
quipu-collector --server-url ... --token ... --once
      |
      v
Quipu ingest API
```

## Failure Handling

- Missing config: wrapper exits non-zero before collector starts.
- Collector send failure: collector emits structured JSON error and exits
  non-zero.
- Timer recurrence: systemd records the failed service run and retries on the
  next scheduled tick.
- Uninstall: timer/service removal preserves config unless `--purge-config` is
  explicitly passed.

## Test Criteria

- Python tests validate service, timer, env example, wrapper, and dry-run
  script behavior.
- `bash -n` passes for all ops scripts.
- Full server, collector, web tests and web build pass before release.
- No real `systemctl` mutation is executed during automated verification.

## Human Approval Gates

Already approved for this project flow:

- Commit, push, tag, and GitHub release to the existing Quipu repository.

Still gated and not performed automatically:

- Installing systemd files on this host.
- Publishing packages.
- Production deployment.
- Remote repair or destructive commands.
