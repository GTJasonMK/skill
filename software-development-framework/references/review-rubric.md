# Review Rubric

Use this rubric for architecture review, code review, or final self-audit. A strong change scores at least 16/20 and has no critical failure.

## Scorecard

Score each category from 0 to 2:

- **Goal fit**: 0 misses the request, 1 partially satisfies it, 2 satisfies it end to end with evidence.
- **Locality**: 0 scatters behavior, 1 touches more modules than needed, 2 changes the owning modules only.
- **Reuse**: 0 duplicates existing capability, 1 reuses awkwardly or partially, 2 reuses clear existing contracts or leaves local code intentionally.
- **Redundancy**: 0 duplicates rules/schemas/state, 1 leaves minor justified duplication, 2 has one owner for each rule.
- **Coupling**: 0 adds dependency cycles or infrastructure leakage, 1 adds manageable coupling, 2 preserves inward dependency direction.
- **Extensibility**: 0 blocks likely variants, 1 supports extension with friction, 2 has narrow contracts for known variation.
- **Cohesion**: 0 mixes unrelated responsibilities, 1 has small responsibility leaks, 2 keeps modules single-purpose.
- **Failure handling**: 0 ignores failures, 1 handles common failures only, 2 handles expected errors at the right boundary.
- **Tests**: 0 lacks meaningful checks, 1 checks only the happy path, 2 covers changed contracts and edge behavior.
- **Maintainability**: 0 relies on cleverness or hidden state, 1 is understandable with effort, 2 is boring, explicit, and easy to change.

## Critical Failures

Do not approve or finish a change with any of these unresolved:

- Domain code imports UI, transport, persistence, or vendor SDK details.
- A shared module imports a product-specific feature.
- The same business rule is implemented in multiple places without a stated owner.
- A new abstraction has only one real use and no proven boundary or volatility reason.
- A public contract changes without checking existing consumers.
- Work is called complete without direct or contract evidence for the changed behavior.
- A bug fix has no regression check unless the codebase has no practical test path.

## Review Procedure

1. State the behavior or architecture claim being reviewed.
2. Identify the owning module and affected consumers.
3. Check dependency direction and data ownership.
4. Search for duplicated rules, schemas, constants, mapping, and formatting.
5. Apply the scorecard.
6. Resolve critical failures before polishing.
7. Report only meaningful residual risk.

## Common Findings

- **Over-generalization**: Replace flags/config branches with specific functions, strategies, or local code.
- **Utility dumping**: Move functions to the domain or feature owner; keep shared utilities tiny and stable.
- **Boundary leakage**: Map external types at adapters; expose internal contracts to domain/application code.
- **State duplication**: Declare one source of truth and derive secondary state when possible.
- **Validation drift**: Centralize validation at the schema or boundary owner and reuse through that contract.
- **Unreadable reuse**: Prefer local explicit code when shared code makes call sites harder to understand.

## Full-Score Standard

A full-score change:

- Solves the requested behavior with the smallest coherent design.
- Uses existing conventions and contracts.
- Has one owner for every rule and state source.
- Keeps dependencies pointed toward stable application/domain contracts.
- Adds only justified abstraction or extension points.
- Includes evidence that covers the changed behavior.
- Leaves future similar work easier without making current code vague.
