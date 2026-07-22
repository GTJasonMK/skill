# Development Workflow

Use this workflow for application changes that involve more than a trivial edit.

## 1. Clarify the Target State

Extract these items from the user request and current code:

- User-visible behavior or system behavior that must change.
- Explicit constraints such as stack, style, compatibility, performance, security, or deployment.
- Files, modules, commands, tests, issues, specs, or artifacts that define success.
- Unknowns that materially affect implementation.

Ask the user only when the ambiguity changes the expected product or architecture. Otherwise choose the conservative option that matches the codebase.

## 2. Build a Current-State Map

Inspect enough code to answer:

- Where does the relevant flow start and end?
- Which modules own presentation, orchestration, domain rules, and infrastructure?
- What contracts already exist?
- What tests cover the flow now?
- What conventions are used for naming, errors, validation, logging, state, and data access?

Prefer repository evidence over memory. Use fast search first, then read the smallest useful set of files.

## 3. Choose a Slice

Implement one vertical slice that can be verified:

- Input or trigger.
- Domain/application behavior.
- Persistence or external interaction, if required.
- Output, UI state, API response, event, or side effect.
- Test or executable check.

For larger work, repeat the slice instead of building disconnected layers.

## 4. Edit with Locality

- Modify the module that owns the behavior.
- Keep adapter code at the edge and domain logic in the core.
- Make shared changes only after confirming at least two real consumers or a stable boundary need them.
- Keep naming specific until a real general concept emerges.
- Update adjacent tests and fixtures with the code that changes them.

## 5. Handle Existing Debt

- Fix debt when it directly blocks the requested change or makes verification unreliable.
- Record residual debt when fixing it would expand scope.
- Avoid mixing broad cleanup with feature behavior unless cleanup is required for correctness.

## 6. Verify the Slice

Use this order:

- Static checks for syntax, types, lint, schema generation, or formatting when available.
- Focused unit or component tests for changed logic.
- Integration tests for contracts between modules.
- End-to-end or manual runtime checks for user-visible workflows.

If a check cannot run, state the command and reason. Do not imply unrun checks passed.

## 7. Final Audit

Before finishing, inspect:

- The request is satisfied end to end.
- No duplicated rules, schemas, constants, query logic, or formatting were introduced.
- New dependencies point inward toward stable contracts.
- Shared modules remain generic and product-agnostic.
- Extension points are named, narrow, and supported by current requirements.
- Tests or checks cover the actual changed behavior.
