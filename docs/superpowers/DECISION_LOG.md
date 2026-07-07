# Decision Log

> Status: active
> Date: 2026-07-07
> Owner: chquan

## 2026-07-07: Start With Team Scope

Decision: Quipu will start as a multi-device, team-oriented workstation health
investigator.

Context: The initial idea came from diagnosing one laptop freeze and thermal
behavior. The user then selected "multiple devices, team use" as the starting
scope.

Reasoning:

- Team use creates stronger value than a personal dashboard when the system can
  compare recurring failures across devices.
- The product should avoid competing head-on with general observability
  dashboards by focusing on incident explanation, evidence, and next actions.
- A small self-hosted team deployment keeps the first version useful without
  requiring a cloud service.

Rejected for MVP:

- Single-device only utility.
- Full fleet observability platform.
- Server administration console.

Risks:

- Team scope can become too broad quickly.
- Logs may contain sensitive data.
- Multi-device ingestion introduces auth, clock drift, retention, and offline
  state earlier than a personal app.

Mitigation:

- Limit initial scale to 3-20 machines.
- Use read-only agents.
- Store only normalized events and minimal log excerpts by default.
- Keep AI output explainable and evidence-linked.
