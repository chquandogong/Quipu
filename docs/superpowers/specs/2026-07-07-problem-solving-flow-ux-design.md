# Quipu Problem-Solving Flow UX Design

> Status: draft for review
> Date: 2026-07-07
> Owner: chquan

## Product Redefinition

Quipu is a team workstation health investigator. Its core interface should not
be a generic status dashboard. Its core interface should be a guided problem
solving flow that helps a team detect instability, triage impact, investigate
evidence, form hypotheses, record actions, verify outcomes, and report findings.

The current fleet overview remains useful, but it should become a supporting
surface beneath an investigation-centered experience.

## Differentiation Principles

1. Investigation first, metrics second.
   Users should enter through incidents, risks, and questions. Metrics appear as
   evidence, not as the product's main destination.

2. Evidence-linked conclusions.
   Every claim must link to sensor values, journal events, update records, or
   user notes. Each finding needs confidence, supporting evidence, contradicting
   evidence, and raw source references.

3. Team-level pattern memory.
   The product should remember and group repeated signatures across machines:
   model, kernel, GPU driver, SSD, Wi-Fi device, workload, physical setup, and
   intervention history.

4. Intervention verification.
   The product should track human actions and compare before/after windows so
   teams can see whether a fix actually helped.

5. Read-only, local-first trust.
   The default product must be safe: read-only collection, local/self-hosted
   storage, limited log excerpts, explicit redaction, and no remote repair.

## Primary Flow: DTIHAVR

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

### Detect

Goal: identify machines, incidents, and repeated patterns that need attention.

Inputs:

- Fresh metrics and events.
- New warning or critical findings.
- Stale agents.
- Repeated signatures across devices.

Output:

- Investigation queue items.

### Triage

Goal: decide what should be looked at first.

Each queue item should show:

- Priority.
- Affected device or pattern.
- Why now.
- Confidence.
- Blast radius.
- Suggested next step.

### Investigate

Goal: build the evidence timeline.

Incident detail should show:

- Sensor timeline.
- Journal and kernel events.
- Updates and package changes.
- Reboot and unclean shutdown markers.
- Session/graphics/storage/network evidence.
- Missing or unreliable data.

### Hypothesize

Goal: help the operator reason without hiding uncertainty.

Each hypothesis should include:

- Cause category.
- Confidence.
- Supporting evidence.
- Contradicting evidence.
- Missing checks.
- Suggested command or source to inspect.

### Act

Goal: record what a human did or plans to do.

Action examples:

- Lift laptop or change cooling setup.
- Change power profile.
- Stop or change workload.
- Update kernel, driver, BIOS, or firmware.
- Clean fan or change physical placement.

The MVP should record actions, not execute them remotely.

### Verify

Goal: compare before/after windows.

Verification should show:

- Temperature delta.
- Load-adjusted temperature change.
- Throttling warning count change.
- Reboot or session error recurrence.
- Storage/network event recurrence.
- Whether the evidence supports "helped", "no clear change", or "worse".

### Report

Goal: produce a short team-readable incident summary.

Report should include:

- What happened.
- Most likely cause.
- Evidence.
- Action taken.
- Result.
- Follow-up.

## Primary Surface: Investigation Queue

The first screen should become an investigation queue.

Example:

| Priority | Item | Why now | Next step |
| --- | --- | --- | --- |
| High | `build-xps` thermal risk | CPU package at 86.4C with thermal warning during compile workload | Compare cooling and workload windows |
| Medium | `dev-p1` unclean shutdown | Previous boot ended without clean shutdown marker | Inspect pre-reboot graphics, thermal, and storage evidence |
| Medium | `ops-framework` graphics warning | Kernel graphics warning before visible stutter | Check i915/session timeline and repeated signatures |

Queue item states:

- New.
- Investigating.
- Action planned.
- Verification pending.
- Resolved.
- Needs follow-up.

## Navigation Model

Primary navigation:

- Queue.
- Incidents.
- Patterns.
- Devices.
- Interventions.
- Reports.
- Settings.

The existing fleet overview should move under Devices or remain as a secondary
panel on Queue, not as the dominant first screen.

## Success Criteria

The UX is successful when a user can answer these questions quickly:

- Which issue should I inspect first?
- Why did Quipu rank it that way?
- What are the top hypotheses?
- What evidence supports each hypothesis?
- What evidence weakens each hypothesis?
- What should I check or do next?
- Did the action help?
- Is this isolated or recurring across the team?

## MVP Scope For Next UI Iteration

The next UI iteration should add:

- Investigation queue generated from current device findings.
- Incident detail view for one selected queue item.
- Hypothesis board with evidence and counter-evidence.
- Action recording form.
- Verification placeholder using before/after windows from available samples.

Out of scope for the next UI iteration:

- Remote command execution.
- AI-generated final reports.
- Full intervention analytics across months.
- Native Linux agent changes.
