# Reuse and Coupling Checklist

Use this checklist before creating abstractions, copying code, touching shared modules, or finishing work.

## Reuse

- Existing component/helper/service/type checked before adding a new one.
- Shared logic has one owner and one authoritative implementation.
- Reuse preserves readability at call sites.
- Reuse does not force unrelated features to accept irrelevant parameters.
- Reuse is backed by a stable concept, not superficial code similarity.

## Redundancy

Look for duplicated:

- Validation rules.
- Permission checks.
- Data mapping.
- API schemas or DTOs.
- UI formatting.
- Constants and feature flags.
- Query filters.
- Error handling.
- Loading and empty states.
- Test factories and fixtures.

If duplication exists, decide whether to centralize now, leave local intentionally, or remove obsolete code.

## Coupling

Check for:

- Import cycles or bidirectional knowledge.
- Domain code importing framework, transport, persistence, or vendor SDK details.
- Components calling unrelated feature services directly.
- Shared packages importing application-specific modules.
- Hidden dependencies through globals, environment variables, module singletons, or ambient context.
- Tests requiring broad setup for narrow behavior.

Reduce coupling by introducing explicit contracts, adapters, parameters, events, or narrower module boundaries.

## Extensibility

An extension point is healthy when:

- The axis of variation is already known.
- The contract is small and documented by types or tests.
- Adding one new variant does not require editing unrelated variants.
- Default behavior is explicit.
- Errors are local and diagnosable.
- The extension mechanism does not leak infrastructure details into domain code.

## Stop Conditions

Stop abstracting when:

- The next abstraction would not remove a current duplication or dependency problem.
- The name becomes vague, such as manager, helper, util, common, base, or generic.
- Call sites become harder to read than the duplicated code.
- The abstraction requires configuration that mirrors implementation details.

## Final Questions

- Can a future maintainer find the owner of this behavior quickly?
- Can one feature change without surprising another feature?
- Can the next similar feature reuse a clear contract?
- Can tests prove the boundary without booting the whole application?
- Can obsolete paths be deleted safely?
