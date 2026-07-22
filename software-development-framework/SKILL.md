---
name: software-development-framework
description: Concise application-development workflow and design discipline for Codex agents. Use when planning, implementing, reviewing, or refactoring software applications, features, services, APIs, frontends, backends, or shared modules, especially when the work must optimize for high reuse, low redundancy, low coupling, extensibility, maintainability, clear boundaries, decision gates, reviewable architecture, and verifiable delivery.
---

# Software Development Framework

## Operating Rule

Treat every application task as a design-and-verification loop, not only a code edit. Preserve user goals, inspect the current system first, make the smallest coherent change that improves the actual target state, and verify the result with evidence.

## Required Gates

Before editing shared or architectural code, pass the relevant gate:

- **Abstraction gate**: Add an abstraction only when real duplication, a stable boundary, a volatile dependency, or a known extension axis proves it useful.
- **Reuse gate**: Reuse existing code only when it preserves call-site clarity and does not force unrelated features into one shape.
- **Coupling gate**: Reject designs where domain code depends on UI, transport, persistence, vendor SDKs, or hidden globals.
- **Extension gate**: Add extension points only for known variation; define the contract, default behavior, and failure mode.
- **Review gate**: For shared, architectural, or risky changes, score the design with `references/review-rubric.md`; resolve critical failures before finishing.
- **Completion gate**: Do not call work complete until direct or contract evidence covers the changed behavior.

## Workflow

1. **Frame the task**
   - Restate the outcome only when the request is ambiguous or broad.
   - Identify product behavior, technical constraints, explicit non-goals, affected users, and success evidence.
   - Prefer the existing stack, conventions, and ownership boundaries unless they block the goal.

2. **Inspect before designing**
   - Read entry points, nearby modules, tests, build scripts, configuration, and current data flow.
   - Map the change surface: UI, API, domain logic, persistence, background jobs, infrastructure, and tests.
   - Find existing abstractions before adding new ones.

3. **Shape the design**
   - Keep domain decisions close to domain code and infrastructure details behind adapters.
   - Reuse existing types, helpers, services, UI components, and validation paths when they fit.
   - Add a new abstraction only when it removes real duplication, clarifies a boundary, or creates a stable extension point.
   - Define module contracts before editing shared code.

4. **Implement in thin vertical slices**
   - Build through one working user path or system path at a time.
   - Keep changes cohesive: one reason to change per module, explicit inputs and outputs, minimal ambient state.
   - Avoid speculative frameworks, generic factories, and broad rewrites unless the current task proves they are needed.

5. **Verify continuously**
   - Run the narrowest meaningful tests first, then broader checks when shared behavior or integration changed.
   - Add or update tests for changed contracts, boundary behavior, and regressions.
   - Treat a passing command as evidence only for the behavior it actually covers.

6. **Audit before finishing**
   - Compare the final state against the original request, not against the implementation path.
   - Check reuse, redundancy, coupling, extensibility, failure handling, and maintainability.
   - Report changed files, verification performed, and any residual risk.

## Delivery Contract

For non-trivial application work, finish with:

- Behavior implemented or reviewed.
- Existing structures reused or intentionally not reused.
- Duplications removed, avoided, or intentionally left local.
- Boundary or dependency changes.
- Extension points added or deliberately deferred.
- Review rubric result when shared, architectural, or risky code changed.
- Verification commands and what each proves.
- Residual risk, only when meaningful.

## Design Defaults

- Prefer composition over inheritance and dependency injection over hidden globals.
- Prefer pure functions for domain transformations and narrow adapters for I/O.
- Prefer explicit data contracts over loosely shaped objects crossing boundaries.
- Prefer one source of truth for state, schema, validation, formatting, and business rules.
- Prefer boring, local code until repetition or boundary pressure justifies abstraction.
- Prefer deleting obsolete paths when safe, instead of leaving parallel implementations.

## Reference Files

Load only the reference needed for the current decision:

- `references/architecture-principles.md`: Use when defining boundaries, module responsibilities, dependency direction, extension points, or shared abstractions.
- `references/decision-gates.md`: Use when a design choice could introduce abstraction, shared code, new dependencies, extension points, or completion claims.
- `references/development-workflow.md`: Use when planning multi-step application work, slicing implementation, or deciding what to inspect and verify.
- `references/examples.md`: Use when a concrete implementation pattern is needed for APIs, frontends, integrations, refactors, or shared modules.
- `references/review-rubric.md`: Use when reviewing architecture quality or deciding whether a change meets the framework's standard.
- `references/reuse-and-coupling-checklist.md`: Use before adding abstractions, duplicating logic, changing shared modules, or finishing a feature.
- `references/verification.md`: Use when choosing tests, designing quality gates, or auditing whether the task is complete.
