# Before/After Intervention Verification Design

> Status: approved by autonomous v0.3.0 execution · Date: 2026-07-07 · Owner: chquan

## Meaning

Quipu's core promise is not "show more machine metrics." It is "help a team solve a workstation problem and verify whether the human action helped." The next smallest wedge is to turn a recorded intervention into an evidence-backed before/after comparison.

The concrete motivating case is a bottom-fan laptop that may cool better after one edge is lifted. Quipu should be able to answer whether CPU package temperature and warning recurrence improved after that physical intervention.

## Scope

In scope for v0.3.0:

- Compute verification for each recorded intervention from persisted observations.
- Compare a fixed window before and after the intervention timestamp.
- Cover thermal metrics, load context, and warning/critical event recurrence.
- Return verification details in investigation detail API responses.
- Show the comparison in the React investigation UI.
- Keep collection read-only and local-first.

Out of scope:

- Collector daemonization.
- Automatic repair or remote commands.
- Long-term statistical baselines.
- AI-authored conclusions.
- New database schema for materialized verification results.

## Alternatives

| Option | Description | Pros | Cons | Decision |
| --- | --- | --- | --- | --- |
| Snapshot-only | Use `latest_metrics` and intervention records already passed into analysis. | Minimal code. | Cannot compute real before/after windows. | Rejected. |
| Repository window query | Query metric/event samples around each intervention and compute a deterministic projection. | Real evidence, no schema change, testable. | More repository/API plumbing. | Selected. |
| Materialized verification table | Persist computed verification rows. | Fast reads and historical audit trail. | Requires schema lifecycle before the model is stable. | Deferred. |

## Data Model

The API will keep `interventions` as the action history and add a derived field:

```json
{
  "verification_result": {
    "status": "helped",
    "summary": "CPU package temperature fell by 17.4C after Raised rear edge.",
    "window_minutes": 30,
    "checks": [
      {
        "name": "CPU package temperature",
        "before": "86.4C",
        "after": "69.0C",
        "delta": "-17.4C",
        "verdict": "improved"
      }
    ]
  }
}
```

Statuses:

- `helped`: at least one core health signal improved and none worsened.
- `worse`: at least one core health signal worsened materially.
- `unclear`: data exists but signals conflict or movement is too small.
- `insufficient_data`: missing before or after window data.

## Comparison Rules

Window:

- Default: 30 minutes before and 30 minutes after `recorded_at`.
- The before side excludes the exact intervention timestamp.
- The after side includes observations at or after the intervention timestamp.

Thermal:

- Compare `cpu.package_temp_c` average before vs after.
- `<= -5.0C` is improved.
- `>= +5.0C` is worsened.
- Otherwise unchanged.

Load context:

- Compare `cpu.load_1m` average before vs after.
- Load does not decide the overall result by itself.
- If temperature improves while load is similar or higher, the summary says the intervention is stronger evidence.
- If temperature improves while load drops sharply, the summary says the result may be workload-driven.

Events:

- Count warning/critical events in the same category before and after.
- A lower after count improves recurrence; a higher after count worsens recurrence.

## UX

The `Recorded interventions` panel should show the action and its verification result together. The `Verification` panel should show the most recent intervention result as the current answer.

UI copy should be concrete:

- "Helped" when evidence improves.
- "Needs after data" when the team has not collected an after window.
- "Unclear" when load or event evidence prevents a clean conclusion.

## Safety

This feature is read-only. It only reads already-ingested observations and recorded intervention metadata. It does not trigger repair commands, collect new raw logs, or contact external systems.

## Test Plan

- Repository test: metric/event window query returns before and after samples around an intervention.
- Analysis test: a thermal intervention with lower after temperature produces `helped`.
- Analysis test: missing after samples produces `insufficient_data`.
- API test: investigation detail includes verification result on intervention records.
- Web test: verification comparison is rendered in the intervention and verification panels.
