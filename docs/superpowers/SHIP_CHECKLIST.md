# Quipu Ship Checklist

> Status: release candidate approved for GitHub release and public visibility after audit
> Date: 2026-07-07
> Owner: chquan
> Release: v0.3.1

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
- Read-only one-shot Linux collector.
- Persistent intervention records.
- Intervention recording UI.
- Before/after intervention verification.
- Verification result UI.
- Investigation Lens focus board and hover/focus expansion panels.
- Hover/focus metric explanations for CPU package temperature, 1-minute load
  average, and NVMe temperature.
- Collapsed creator/reference drawer with public Dogu Robotics, Dogu X, and
  Physical AI materials.
- Visible Made by, About, and Version metadata chips.
- Project docs, GitHub templates, contribution notes, and security policy.

Excluded:

- Long-running collector daemon.
- Remote repair or remote command execution.
- AI-generated conclusions.
- Package publishing.
- Production deployment.

## Tests

- Server tests: `pytest -v` -> 21 passed, 1 Starlette deprecation warning.
- Collector tests: `pytest -v` -> 1 passed.
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
- Fan RPM collection remains out of scope and may be unreliable on some laptops.
- Current analysis is deterministic and intentionally conservative.
- Verification uses a fixed 30-minute window.
- `npm ci` reports existing transitive web dependency vulnerabilities; no public
  production deployment is included in this release.
- UI reference images are loaded from public GitHub raw URLs to avoid bundling
  heavy binary assets in the repository.

Approved risks:

- User explicitly requested commit, tag, push, and release on 2026-07-07.
- GitHub release is approved for this release cycle.
- Public repository visibility is approved after sensitive-content audit.

Unapproved risks:

- Package publishing.
- Production deployment.
- Remote execution on team machines.

## Rollback

Rollback method:

- Delete or supersede the private GitHub release if the release note is wrong.
- Move forward with a patch tag such as `v0.3.1` for code or documentation fixes.
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
- `v0.3.1` tag exists locally and remotely.
- GitHub release exists for `v0.3.1`.
- Repository visibility is public after audit.

## Documents

- README: current.
- Dashboard: current release state recorded.
- Roadmap: intervention verification slice recorded.
- Changelog: `v0.3.1` prepared.
- Security policy: present.

## Final Judgment

GitHub release is allowed for `v0.3.1`.

Public repository visibility is allowed after sensitive-content audit.
Package publishing, production deployment, destructive git operations, and
remote repair remain outside this approval.
