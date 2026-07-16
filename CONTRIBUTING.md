# Contributing To Quipu

Quipu is early-stage. The main rule is to preserve its product direction:
investigation first, metrics second.

## Development Setup

Each app manages its own environment.

```bash
# Server
cd apps/server
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"

# Collector
cd apps/collector
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"

# Web
cd apps/web
npm install
```

Python 3.11+ and Node.js 20+ are required. CI runs on Python 3.12 and
Node 24 (`.github/workflows/ci.yml`).

To run the app locally, see the Quick Start in [README.md](README.md):
`scripts/dev-server.sh` starts the API server and `npm run dev` starts the
web UI.

## Development Workflow

1. Create a branch for the change.
2. Keep changes scoped to one product or engineering concern.
3. Write or update tests before changing behavior.
4. Run the relevant verification commands.
5. Update docs when a decision, workflow, or user-facing behavior changes.

## Verification

Server:

```bash
cd apps/server
. .venv/bin/activate
pytest -v
```

Collector:

```bash
cd apps/collector
. .venv/bin/activate
pytest -v
```

Web:

```bash
cd apps/web
npm test
npm run build
```

CI runs all three suites on every push to `main` and every pull request.

## Commit Style

Use Conventional Commits:

```text
feat(scope): add capability
fix(scope): correct behavior
docs(scope): update documentation
test(scope): add or update tests
chore(scope): maintain repository hygiene
```

## Product Guardrails

- Do not turn Quipu into a generic metrics dashboard.
- Do not add remote command execution without an explicit design and safety
  review.
- Do not store full raw logs by default.
- Do not make AI output authoritative without evidence links.
- Prefer local-first, read-only, reversible behavior.

## Documentation

- Release notes go in [CHANGELOG.md](CHANGELOG.md).
- Important product decisions belong in
  `docs/superpowers/DECISION_LOG.md`; project status and plans live in
  `docs/superpowers/DASHBOARD.md` and `docs/superpowers/ROADMAP.md`.
- User-facing positioning belongs in the Korean default `README.md`. Keep
  `README.en.md` and `README.zh-CN.md` aligned when the product message, setup
  flow, safety boundary, or roadmap changes.
- Operator-facing procedures belong in `USER_MANUAL.md`.
