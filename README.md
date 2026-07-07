# Quipu

Team-first workstation health investigator for Linux laptops and developer
workstations.

Quipu is intended to turn sensor readings, system logs, and user interventions
from multiple machines into clear incident timelines: current state, likely
causes, supporting evidence, and practical next actions.

Initial wedge:

- Compare health patterns across a small team's machines.
- Reconstruct freeze or hard-power-off incidents from local evidence.
- Detect recurring thermal, graphics, storage, network, and update-related
  issues before they become team-wide productivity loss.
- Keep collection lightweight, read-only, and self-hosted by default.

## First Vertical Slice

The first implementation slice provides:

- FastAPI ingest API.
- SQLite persistence.
- Rule-based fleet overview.
- Deterministic three-device sample data.
- Vite React team dashboard.

Run the server:

```bash
scripts/dev-server.sh
```

In another terminal, run the web UI:

```bash
cd apps/web
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.
