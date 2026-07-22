# Examples

Use these patterns when a task needs concrete structure. Adapt names and framework details to the repository.

## Contents

- API Feature
- Frontend Feature
- External Integration
- Refactor Duplicate Logic
- Shared Module Change

## API Feature

Request shape: "Add an endpoint to let users update notification settings."

Expected flow:

1. Inspect existing routes, request validation, auth, service/use-case layer, persistence model, and tests.
2. Put transport parsing in the route/controller.
3. Put permission checks and orchestration in the application/use-case layer.
4. Put settings invariants in domain code or the model owner.
5. Put database details in the repository/adapter already used by the feature area.
6. Reuse existing user identity, validation, error, logging, and response helpers when they match.
7. Add focused tests for valid update, invalid payload, unauthorized user, and persistence failure.

Good boundary:

- Controller maps HTTP to an application command.
- Use case owns "who may update what."
- Repository owns SQL/ORM calls.
- Domain owns valid settings transitions.

Reject:

- Controller directly mutates database rows and repeats permission logic.
- New DTO duplicates an existing schema without a compatibility reason.
- Shared helper accepts unrelated settings options only to force reuse.

## Frontend Feature

Request shape: "Add a settings panel with save, loading, validation, and error states."

Expected flow:

1. Inspect existing form components, state conventions, query/mutation helpers, validation schema, and design system.
2. Keep presentational components focused on rendering and interaction.
3. Keep server state in the existing data-fetching layer.
4. Keep domain validation in the shared schema or form resolver already used by the feature.
5. Keep view-only formatting in UI helpers, not in API clients or domain code.
6. Reuse existing empty, loading, error, toast, modal, and button patterns.
7. Test rendering, invalid input, successful save, failed save, and disabled/loading behavior.

Good boundary:

- Component owns layout and local interaction state.
- Hook or feature module owns query/mutation orchestration.
- Schema owns field validation.
- API client owns transport mapping.

Reject:

- Component embeds API URLs, auth headers, or persistence assumptions.
- Same validation rule appears in component, API client, and server.
- New generic form abstraction is added for one screen.

## External Integration

Request shape: "Integrate a payment/email/search provider."

Expected flow:

1. Inspect existing adapter, environment, retry, logging, secret, and test patterns.
2. Define an internal port that describes the application need, not the vendor API.
3. Implement vendor mapping in an infrastructure adapter.
4. Convert vendor errors to internal structured errors at the boundary.
5. Keep credentials and environment reads outside domain code.
6. Add contract tests or adapter tests using fixtures/mocks appropriate to the repo.
7. Document operational assumptions only where the codebase already keeps such notes.

Good boundary:

- Application calls `sendReceipt(...)` or equivalent internal operation.
- Adapter calls the vendor SDK/API.
- Domain never imports vendor types.

Reject:

- Vendor SDK objects cross into domain or UI code.
- Provider-specific statuses become business enums without mapping.
- Retry, timeout, and idempotency behavior is unspecified for side effects.

## Refactor Duplicate Logic

Request shape: "These modules repeat validation/mapping; refactor them."

Expected flow:

1. Identify every real duplicate and its caller.
2. Decide whether duplicates share the same business concept or only look similar.
3. Centralize only shared rules with the same owner and evolution path.
4. Keep local duplication when callers differ in meaning, lifecycle, or error behavior.
5. Name the abstraction after the domain concept, not "common", "helper", or "util".
6. Delete obsolete paths after consumers move.
7. Add regression tests that prove old behaviors still hold.

Good abstraction:

- Has a small contract.
- Makes call sites clearer.
- Can support the next known variant without changing existing variants.

Reject:

- A generic function with many flags.
- An abstraction that callers must understand internally to use correctly.
- Moving code to a shared folder without clarifying ownership.

## Shared Module Change

Request shape: "Update a shared package used by multiple features."

Expected flow:

1. List current consumers before editing.
2. Define the public contract and compatibility requirement.
3. Prefer additive changes when consumers cannot all move together.
4. Update all affected tests, fixtures, generated types, and docs that the repo treats as contracts.
5. Run checks for each affected consumer or explain what could not run.

Reject:

- Product-specific behavior in a general shared package.
- Breaking public shape without migration.
- Tests only for the new consumer while existing consumers are unverified.
