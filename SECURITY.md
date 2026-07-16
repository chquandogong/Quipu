# Security Policy

Quipu is an early local-first prototype. It is not ready for exposure to the
public internet.

## Supported Use

- Run on a trusted local machine or private team network.
- Treat collected logs and device names as sensitive.
- Use the development ingest token (`dev-token`, overridable with
  `QUIPU_DEV_AGENT_TOKEN`) only for local testing; issue per-device
  enrollment tokens for repeated operation. Per-device tokens are stored as
  SHA-256 hashes only.

## Current Auth Model

- Ingest (`POST /api/ingest/batches`) requires the `X-Quipu-Agent-Token`
  header with the dev token or an active per-device enrollment token.
- Token administration endpoints (`/api/enrollment/tokens`,
  `/api/admin/schema`) require the dev token.
- Read endpoints (fleet overview, investigations, patterns, notes) are
  currently unauthenticated. This is another reason to keep the server on a
  trusted private network only.

## Safety Boundaries

Current and planned defaults:

- Read-only data collection.
- Self-hosted storage.
- Minimal log excerpts.
- No remote command execution.
- No automatic repair.

## Reporting Issues

Until a public issue tracker or security contact is selected, keep sensitive
reports local and avoid pasting raw logs, hostnames, tokens, private URLs, or
user-identifying paths into public channels.
