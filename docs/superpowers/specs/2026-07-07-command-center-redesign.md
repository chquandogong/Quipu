# Command Center Redesign

> Date: 2026-07-07
> Status: implementation track
> Release target: v0.3.2

## Problem

The current UI exposes the right investigation parts, but it still reads as a
set of cards. A user cannot immediately answer:

- what to inspect now,
- why it matters,
- what to do next,
- what proof is needed before calling the issue fixed.

The `Creator and visual references` drawer also repeats information already
visible in the header and competes with the actual investigation workflow.

## Research Compared

1. Carbon dashboard guidance: use strong hierarchy, fewer metrics, consistent
   colors, and whitespace for clarity.
2. Material tooltip guidance: use concise contextual help, not large permanent
   explanations.
3. Fluent layout guidance: use space, proximity, and responsive re-architecture
   to keep the important content visible on each screen size.
4. Primer progressive disclosure guidance: disclose sparingly and preserve the
   user's context.
5. 2026 SaaS workflow pattern: command-style interfaces and focused action
   surfaces reduce menu and panel overload.

## Chosen Design

Use a `Command Center` first viewport.

- Replace the separate flow rail, summary cards, and focus-board stack with one
  command surface.
- Put four answers at the top: `Inspect now`, `Why it matters`, `Do next`, and
  `Proof needed`.
- Keep short English command labels for speed, with compact Korean helper labels
  where they clarify intent.
- Keep metric explanations bilingual only where useful: Korean explanation with
  the English technical term in parentheses.
- Remove the creator/reference image drawer. Keep `Made by`, `About`, and
  `Version` as compact header metadata.

## Interaction Model

- `Review evidence`, `Record action`, and `Verify result` remain the primary
  actions.
- The DTIHAVR stage list becomes compact stage chips inside the command center.
- Fleet counts become a compact health strip inside the same command center.
- Queue and detailed panels remain below the command center for drill-down.
- Metric help buttons remain hover/focus accessible.

## Boundaries

- No new heavy UI library.
- No bundled image assets.
- No command-palette implementation yet; the current change focuses the first
  viewport and removes nonessential reference content.
- No server data contract change.

## Verification

- Web test must assert the command center exists.
- Web test must assert creator/reference drawer content is absent.
- Web test must assert bilingual metric explanation text is present.
- Browser screenshot must show the first viewport gives a clear next action.
