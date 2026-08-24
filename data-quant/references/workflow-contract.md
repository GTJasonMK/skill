# Data-Quant Workflow And Handoff Contract

## Shared Intake

Record before routing:

- task and requested decision;
- object and claim side;
- asset class, venue, universe, benchmark, currency, horizon;
- observable, rebalance, execution, return-start, and return-end times;
- available data/code/weights/orders/fills/logs;
- current implementation state: idea, research, paper, live, retired;
- evidence that is missing or cannot be audited.

## Stage Handoff

Every stage returns this owned object:

```yaml
stage: intake | data | research | validation | portfolio | execution | risk | governance | report
status: ready | needs_input | blocked | complete
primary_decision: one sentence
artifact_ids: []
constraints: []
checks_completed: []
open_questions: []
next_stage: null
```

A handoff contains references to versioned artifacts, not DataFrames, model instances, database connections, or entire child Skill bodies.

## Standard Stage Responsibilities

### Intake

Classify object, claim, asset class, timing, user outcome, and evidence availability. Choose one primary route.

### Data

Validate table contracts, identifiers, units, timestamps, calendar, point-in-time availability, revisions, universe, corporate actions, missingness, and tradability. Produce canonical-table and audit artifacts.

### Research

Freeze a baseline; construct signals only from observable inputs; run the smallest diagnostics appropriate to the claim. Preserve raw and transformed signals.

### Validation

Create reproducible folds, purge overlapping labels, apply embargo, record all variants, keep the final test locked, and quantify uncertainty and selection bias.

### Portfolio

Translate forecasts into weights with explicit expected-return meaning, covariance horizon, benchmark, constraints, costs, liquidity, borrow, leverage, and cash.

### Execution

Use offline timing/cost/fill replay consistent with the signal horizon and venue. State simulation fidelity and unmodeled mechanics.

### Risk

Attribute exposures, covariance and specific risk; run tail, liquidity, funding, margin, correlation, and historical/scenario stress tests.

### Governance

Apply the decision ontology, preserve evidence conflicts, enforce stage requirements, and produce blockers, warnings, evidence gaps, action, and decision changers.

### Report

Render JSON, Markdown, and optional HTML from the same Run Record. Reporting does not recompute metrics.

## Executable Manifest Stages

`pipeline.stages` starts with `data`, follows the canonical order above, and places `report` last. A non-automatic stage declares one or more executable diagnostics:

```yaml
pipeline:
  stages: [data, research, governance, report]
  diagnostics:
    - diagnostic_id: factor-ic
      stage: research
      input_sources: [factors, labels]
      parameters: {signal: value_signal, label: next_close}
  required_diagnostics: [factor-ic]
```

The native Manifest path now covers every declared stage: automatic `data-contract`; research `factor-ic`, `fama-macbeth`, `futures-roll`, `fx-rollover`, and `fx-forward-check`; validation `purged-walk-forward`, `corporate-action-adjustment`, and `fixed-income-price-reconciliation`; portfolio `portfolio-eligibility`, `short-borrow-capacity`, and `portfolio-backtest`; deterministic offline execution `execution-replay`, `rebalance-replay`, and `futures-roll-execution`; risk `covariance-risk`, `portfolio-stress`, `factor-risk`, `factor-attribution`, `option-surface-check`, `option-surface-smooth`, `option-hedge-replay`, `fixed-income-shock`, `fixed-income-curve-stress`, `credit-migration-stress`, and `crypto-margin-stress`/`crypto-cross-margin-stress`; monitoring `feature-drift`, `signal-health`, `model-calibration`, and `service-health`; governance gates; and Run Record reporting. `execution-replay` models quote-volume participation, market/limit prices, GTC/DAY/IOC lifecycle, explicit expiry, partial fills, VWAP, arrival latency, and implementation shortfall; it does not claim queue or impact fidelity. `rebalance-replay` deterministically sizes market orders from same-timestamp current/target weights using static portfolio value, arrival midpoint, lot size, minimum notional, venue, and quote-volume participation; it never submits them. `factor-attribution` uses a complete decision-time PIT exposure snapshot and aligned realized factor/asset returns to exactly reconcile factor plus specific contribution while gating gross, factor, and specific limits. `futures-roll` supports expiry, confirmed volume, and confirmed open-interest migration, with same-timestamp roll-gap return adjustment and an explicit collateral-rate assumption. `futures-roll-execution` closes/opens roll legs at exact-timestamp bid/ask, charges explicit fees, settles end-of-day variation margin and collateral return, applies PIT margin/price-limit terms plus collateral haircuts, and never submits an order. `option-surface-smooth` selects a latest-common PIT quote snapshot across multiple expiries, smooths IV in log-moneyness, and permits only bounded moneyness/term interpolation without extrapolation. `option-hedge-replay` recovers a time series of European IV/Greeks and attributes signed option mark-to-market, discrete underlying hedge PnL, and hedge transaction costs, while blocking excessive option spreads. `fixed-income-curve-stress` builds a session-adjusted dated coupon schedule, selects the latest available PIT zero curve without extrapolation, reports dirty price/DV01/duration, and gates parallel or key-rate scenario losses. `credit-migration-stress` validates PIT exposure and transition-matrix snapshots, reprices migrations with explicit spread-duration semantics, applies instrument recovery on default, and gates stressed expected credit loss. `fx-forward-check` derives joint-currency spot and holiday-adjusted forward value dates, normalizes outright or decimal-points bid/ask, applies an explicit cross-currency-basis sign, and gates observed deviations from executable CIP bounds. `crypto-cross-margin-stress` aggregates multiple PIT positions under effective margin tiers, applies funding and price shocks, and gates maintenance liquidation, insurance-fund exhaustion/ADL, and venue-default recovery loss. `portfolio-eligibility` audits effective-dated PIT membership, total-return labels, in-window corporate actions, and borrow flags; `portfolio-backtest` applies explicit flat cash, financing, and short-borrow rates without claiming locate quantity or recall fidelity. Each diagnostic reads named canonical sources, validates its semantic timing and parameters, writes an Artifact under `artifacts/<stage>/`, and contributes to the stage handoff and gate. `data-contract` runs automatically for every source. Every native diagnostic publishes `manifest_stage` and a strict `parameter_schema` through `quantctl list-capabilities --json`; unknown keys, missing required fields, invalid ranges, and stage mismatches fail before a run directory is created. `RunManifest.execution` accepts only `offline_replay` or `paper_simulation`; live-order submission, fund transfer, credential storage, and undeclared broker fields are schema-invalid. Requesting any other non-automatic stage without an executable diagnostic is a blocker rather than a silent pass. The report stage renders `reports/review.md` from `run.json` without recomputing metrics.

## Stop And Fail-Closed Rules

- `needs_input`: a user/data choice is required but safe partial work remains possible.
- `blocked`: a required contract, dependency, credential reference, or authoritative market rule is absent and dependent work cannot be trusted.
- `review`: evidence is incomplete or conflicting; never treat it as a pass.
- `fail`: observed evidence violates a mandatory check.
- Missing required diagnostics, unavailable point-in-time fields, invalid execution windows, or untradable simulated fills cannot be promoted.
