## Summary

- 

## Product Impact

- Which part of the DTIHAVR flow does this improve?
- Does this preserve investigation-first, metrics-second behavior?

## Test Plan

- [ ] Server tests: `cd apps/server && . .venv/bin/activate && pytest -v`
- [ ] Web tests: `cd apps/web && npm test`
- [ ] Web build: `cd apps/web && npm run build`

## Safety / Privacy

- [ ] No remote command execution added
- [ ] No full raw-log persistence added by default
- [ ] Findings remain evidence-linked
- [ ] Sensitive data handling reviewed if logs or host data changed

## Docs

- [ ] README updated if user-facing behavior changed
- [ ] Decision log/spec/plan updated if product direction changed
