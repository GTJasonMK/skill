# Architecture Principles

Use these rules when defining application structure, module boundaries, and extension points.

## Dependency Direction

- Keep high-level policy independent from low-level mechanisms.
- Let UI, transport, persistence, and external services depend on application/domain contracts, not the reverse.
- Pass dependencies in through constructors, function parameters, context objects, or framework-native injection points.
- Hide unstable external APIs behind adapters owned by the application.
- Keep shared packages free of product-specific behavior unless that behavior is truly universal.

## Boundary Types

- **Presentation boundary**: Own rendering, interaction state, accessibility, loading states, and view-specific formatting.
- **Application boundary**: Own use cases, orchestration, permissions, transactions, and cross-domain workflows.
- **Domain boundary**: Own business rules, invariants, domain events, calculations, and state transitions.
- **Infrastructure boundary**: Own databases, queues, HTTP clients, file systems, vendor SDKs, caches, and environment access.
- **Integration boundary**: Own mapping between internal contracts and external protocols or schemas.

## Module Contract Rules

- Make input and output shapes explicit.
- Keep validation at system boundaries and invariant checks inside domain code.
- Return typed results, structured errors, or framework-standard error objects; avoid stringly typed control flow.
- Avoid exporting mutable internals, singleton state, and broad utility bags.
- Keep module names aligned with business capability or technical responsibility, not implementation accidents.

## Abstraction Rules

Add an abstraction only when at least one condition is true:

- Two or more call sites share behavior and are likely to evolve together.
- A volatile dependency needs isolation behind a stable contract.
- Tests need a clear seam for a slow, nondeterministic, or external dependency.
- A domain concept has a stable name and rules that should not be scattered.
- Extension is a stated requirement and the variation points are known.

Do not add an abstraction when:

- The only benefit is making current code look more generic.
- The variation point is hypothetical.
- The abstraction hides a simple framework API without reducing risk or repetition.
- Callers must understand every implementation detail to use it correctly.

## Extensibility Patterns

- Use strategy objects or function maps for known interchangeable behavior.
- Use registries only when contributions come from multiple modules or plugins.
- Use event publication for cross-cutting reactions when direct calls would create a dependency cycle.
- Use adapters for external systems and anti-corruption layers for incompatible domain models.
- Use configuration for deployment or environment differences, not for encoding complex business rules.

## Anti-Patterns

- Domain logic inside controllers, components, migrations, serializers, or vendor callbacks.
- Shared utility modules that become dumping grounds.
- Bidirectional imports between feature modules.
- State duplicated between client, server, cache, and database without ownership rules.
- A generic service layer that only forwards calls.
- One change requiring edits across many unrelated modules.
