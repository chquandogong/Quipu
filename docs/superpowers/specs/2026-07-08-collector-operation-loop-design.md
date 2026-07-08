# Collector Operation Loop Design

Date: 2026-07-08
Release target: v0.7.0

## Decision

Quipu v0.7.0 makes the collector easier to operate on team machines without
turning it into a heavyweight daemon.

The collector remains read-only and stdlib-only. It keeps the existing one-shot
behavior by default, then adds:

- `--once`: explicit one-shot mode.
- `--interval SECONDS`: repeat collection with a sleep between runs.
- `--iterations N`: cap repeated runs for tests, smoke checks, and supervised
  jobs.
- `--dry-run`: collect and print the observation batch without posting, even if
  `--server-url` is present.
- Structured JSON error output to stderr with non-zero exit code.

## Why This Matters

Quipu now has useful telemetry coverage, but a team cannot rely on manual
one-shot execution. The next pragmatic step is not packaging a daemon. It is a
small operation loop that can be run under a terminal, cron, systemd timer, or a
future supervised service.

## Scope

Collector CLI:

- Preserve current default behavior: one collection, print JSON when no
  `--server-url` is provided.
- Preserve current posting behavior when `--server-url` and `--token` are
  provided.
- Add repeat mode with clear stdout output:
  - one-shot output remains pretty JSON for humans;
  - repeated output uses one compact JSON object per line.
- Validate positive interval and iteration values.
- Return `0` on clean completion or Ctrl-C.
- Return `1` on collection/send failures and write a compact JSON error to
  stderr.

Docs:

- README examples for one-shot, dry-run, interval smoke test, and supervised
  loop.
- Keep production service installation gated for a later release.

## Non-Goals

- No systemd unit files yet.
- No package publishing.
- No background service manager.
- No local ring buffer yet.
- No remote repair actions.

## Testing

- CLI tests use injected fake collect/send/sleep functions.
- Tests verify dry-run skips POST, interval mode sleeps between iterations, and
  failures return structured JSON errors.
- Existing collector signal tests remain unchanged.
