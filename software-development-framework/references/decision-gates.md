# Decision Gates

Use these gates before making structural choices. If a gate fails, revise the design before editing.

## Abstraction Gate

Pass only when at least one is true:

- Two or more real call sites share the same business concept and likely evolution path.
- A dependency is volatile, external, slow, nondeterministic, or hard to test.
- A boundary needs a stable contract for multiple consumers.
- A known extension axis needs interchangeable behavior.

Fail when:

- The abstraction has one caller and no proven volatility.
- The name is vague, such as helper, util, common, manager, base, or generic.
- Callers need flags that mirror implementation branches.
- Call sites become harder to read than explicit local code.

## Reuse Gate

Pass only when:

- Existing code matches the same concept, not just similar syntax.
- Reuse keeps caller intent clear.
- Ownership remains obvious.
- The reused contract can evolve without forcing unrelated features together.

Fail when:

- Reuse requires irrelevant parameters.
- Error behavior differs between callers.
- A shared module would need product-specific knowledge.
- Local duplication is clearer and unlikely to diverge dangerously.

## Coupling Gate

Pass only when:

- Dependencies point toward stable application/domain contracts.
- External services, databases, environment reads, files, and framework details stay behind adapters.
- Cross-feature communication uses an explicit contract, event, or application service.
- Tests can exercise changed logic without booting unrelated systems.

Fail when:

- Domain code imports UI, transport, persistence, or vendor SDKs.
- Shared packages import feature modules.
- A new import cycle appears.
- Behavior depends on hidden globals, module initialization order, or ambient mutable state.

## Extension Gate

Pass only when:

- The variation point is already known.
- The contract is small, typed or tested, and named after the domain capability.
- Default behavior and failure behavior are explicit.
- Adding one variant does not require editing unrelated variants.

Fail when:

- The extension point is speculative.
- Configuration becomes a second programming language.
- Every implementation must know about every other implementation.
- The extension mechanism leaks vendor or infrastructure details into domain code.

## Completion Gate

Pass only when:

- Every explicit requirement has direct or contract evidence.
- Changed public contracts have affected consumers checked.
- New failure paths are handled or explicitly accepted.
- The final response identifies verification and meaningful residual risk.

Fail when:

- Only code inspection supports a behavioral claim.
- Tests pass but do not cover the changed behavior.
- Obsolete parallel paths remain without an intentional compatibility reason.
- The final answer implies unrun checks passed.
