# Quipu Ship Checklist

> Status: release candidate approved for private GitHub release
> Date: 2026-07-07
> Owner: chquan
> Release: v0.1.0

## Scope

Included:

- FastAPI ingest API.
- SQLite persistence.
- Deterministic sample fleet data.
- Rule-based fleet and investigation projections.
- Investigation queue and detail API.
- React investigation-first UI.
- Project docs, GitHub templates, contribution notes, and security policy.

Excluded:

- Native Linux collector.
- Persistent intervention/action records.
- Before/after verification windows.
- Remote repair or remote command execution.
- AI-generated conclusions.
- Public release.

## Tests

- Server tests: `pytest -v` -> 14 passed, 1 Starlette deprecation warning.
- Web tests: `npm test` -> 1 passed.
- Web build: `npm run build` -> succeeded.
- Whitespace check: `git diff --check` -> passed.

Evidence source:

- Latest verified local commit before release prep: `47727e2`.

## Risks

Known risks:

- Prototype uses seeded/sample data unless a client ingests observations.
- Fan RPM collection remains out of scope and may be unreliable on some laptops.
- Current analysis is deterministic and intentionally conservative.
- GitHub repository is being created as private by default.

Approved risks:

- User explicitly requested commit, tag, push, and release on 2026-07-07.
- Private GitHub release is approved for this release cycle.

Unapproved risks:

- Public repository or public release.
- Package publishing.
- Production deployment.
- Remote execution on team machines.

## Rollback

Rollback method:

- Delete or supersede the GitHub release if the release note is wrong.
- Move forward with a patch tag such as `v0.1.1` for code or documentation fixes.
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
- `v0.1.0` tag exists locally and remotely.
- GitHub release exists for `v0.1.0`.

## Documents

- README: current.
- Dashboard: current release state recorded.
- Roadmap: Phase 2 first slice implemented.
- Changelog: `v0.1.0` prepared.
- Security policy: present.

## Final Judgment

Private GitHub release is allowed for `v0.1.0`.

Public release, package publishing, production deployment, and destructive git
operations remain outside this approval.
