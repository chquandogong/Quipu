# Summary-First Investigation UI Design

> Date: 2026-07-07
> Release: v0.3.0
> Status: implemented

## Problem

The investigation UI had the right workflow pieces, but the page read as a
list of panels. A user could see many facts yet still miss the practical
sequence:

- what to inspect first,
- what action to take or record,
- how to verify that action.

## Product Principle

Quipu should behave like an investigation cockpit, not a raw monitoring wall.
The first viewport must reduce the problem to the next useful decision, then
let the operator expand evidence as needed.

## Chosen Approach

Use a summary-first surface with three always-visible focus cards:

1. **Look first**: the strongest current signal and evidence.
2. **Next action**: the recommended human action to record.
3. **Verification**: the latest before/after result or pending state.

Detailed panels remain compact by default and expand on hover, keyboard focus,
or CTA routing. This keeps scanning calm while preserving the full DTIHAVR
flow:

```text
Detect -> Triage -> Investigate -> Hypothesize -> Act -> Verify -> Report
```

## Interaction Model

- `Review evidence` routes to the evidence timeline.
- `Record action` routes to the intervention form.
- `Verify result` routes to the before/after verification panel.
- Evidence, hypotheses, interventions, verification, and report panels expose a
  short summary first, then expand to full detail.
- Mobile view disables the collapsed height so touch users do not lose access
  to content.

## Visual References

The UI includes a separate maker/reference band with public Dogu Robotics,
Dogu X, and Physical AI portfolio materials. The band provides provenance and
domain context without turning the app into a marketing landing page.

To keep the repository light, v0.3.0 uses public GitHub raw URLs for those
visuals instead of committing large binary image assets.

## Boundaries

- No remote repair controls.
- No AI-generated conclusions.
- No bundled heavy image assets.
- No hidden-only interaction on mobile.
- No change to the server data contract beyond the existing v0.3.0
  verification result fields.

## Verification

- Web unit test covers the maker band, CTA buttons, and before/after delta.
- Web production build verifies TypeScript and Vite bundling.
- Manual visual smoke uses seeded API data with the Vite app.
