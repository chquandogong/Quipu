# Contributing To Quipu

Quipu is early-stage. The main rule is to preserve its product direction:
investigation first, metrics second.

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

Web:

```bash
cd apps/web
npm test
npm run build
```

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

Important decisions belong in:

- `docs/superpowers/DECISION_LOG.md`
- `docs/superpowers/specs/`
- `docs/superpowers/plans/`
