# Hybrid UI Workflow Contract

This document defines how multiple child Skills hand work to one another. It is not a replacement for the child Skill bodies.

## Shared input

Before routing, record:

- user and repeated task;
- product or content domain;
- primary action and next likely action;
- framework, component primitives, theme/token system, and asset constraints;
- target viewports and supported input modes;
- required states and known defects;
- whether the task is build, redesign, audit, or review-only.

## Stage contract

Each stage returns a small owned handoff, not a dump of the source Skill:

stage: intent | structure | implementation | audit
status: ready | needs-input | blocked | complete
primary_decision: one sentence
artifacts: paths or named UI surfaces
constraints: rules the next stage must preserve
open_questions: unresolved user or product decisions
checks: verification already performed

## Standard staged flow

### Intent

Use ckw design-thinking or the visual-direction route. Produce audience, task, domain signature, visual character, hierarchy, and reasons for the major choices. Ask the user when the intent cannot be made specific without guessing.

### Structure

Use interface-design for product surfaces or ckw design-system/spatial for a broader visual composition. Produce navigation, information hierarchy, surface relationships, component states, and responsive constraints.

### Implementation

Use frontend-excellence and the relevant references. Map decisions to the existing framework, tokens, component primitives, rendering strategy, asset loading, accessibility semantics, and performance budgets.

### Audit

Use the focused specialist routes. Render the real workflow, exercise the primary task, capture wide and narrow states, run the overflow check, and have a separate reviewer critique the artifact when visual or usability quality is in scope.

## When to stop the pipeline

- Stop at intent when the user asked only for a visual direction.
- Stop at structure when the user asked for wireframes, information architecture, or component states.
- Continue through implementation when code changes are requested.
- Continue through audit before calling a UI change done, fixed, or production-ready.
- Mark the handoff blocked when a required user decision, authorization, asset, API, or test environment is missing. Do not silently invent it.

## Review output

For review tasks, findings come first and are ordered by severity: broken workflow or inaccessible control, responsive or state failure, visual hierarchy, then polish. Include exact evidence and a concrete fix. Summaries come after findings.
