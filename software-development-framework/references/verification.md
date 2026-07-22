# Verification

Use this guide to choose checks and decide whether the task is complete.

## Evidence Levels

- **Direct evidence**: A test, build, runtime check, screenshot, API call, log, migration dry run, or command output that exercises the changed behavior.
- **Contract evidence**: Type checks, schema checks, generated clients, lint rules, or tests that prove an interface still matches consumers.
- **Inspection evidence**: Manual code review, search results, or file inspection. Useful, but not enough for broad behavioral claims.
- **Missing evidence**: A required check did not run, failed, or covers only unrelated behavior.

Prefer direct evidence for user-visible behavior and contract evidence for shared interfaces.

## Test Selection

- Use unit tests for deterministic domain rules, pure transforms, validation, and error mapping.
- Use component tests for UI state, rendering, accessibility, and interaction behavior.
- Use integration tests for module boundaries, API contracts, persistence, queues, auth, and external adapters.
- Use end-to-end tests for critical user workflows and cross-system behavior.
- Use smoke/manual checks when automation is unavailable, then report exactly what was checked.

## Coverage Targets

Cover:

- Happy path.
- Boundary values.
- Invalid input.
- Permission or authorization behavior.
- Empty, loading, and failure states.
- Migration or backward compatibility behavior when data shape changes.
- At least one regression test for a fixed bug.

Do not add low-value tests that only restate framework behavior.

## Completion Audit

For each explicit requirement:

- Identify the authoritative artifact proving completion.
- Inspect the artifact or run the command.
- Decide whether the evidence proves, contradicts, partially supports, or does not address the requirement.
- Continue working if evidence is missing or indirect.

For shared changes, also verify:

- Existing consumers still compile or pass tests.
- Public contracts are documented by types, tests, or schemas.
- No obsolete parallel path remains unless intentionally retained.

## Reporting

Final responses should include:

- What changed.
- Which commands or checks ran.
- Any checks that could not run and why.
- Residual risk or follow-up only when it matters.

Never describe unrun checks as passing.
