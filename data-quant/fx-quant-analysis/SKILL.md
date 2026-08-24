---
name: fx-quant-analysis
description: "Foreign-exchange quantitative workflow for pair/numeraire conventions, spot and forwards, forward points, carry, settlement calendars, rollover, cross rates, funding, execution, attribution, and currency risk. 中文触发：外汇量化、汇率、远期点、套息、掉期、交叉汇率、基准货币、结算日、展期、汇率风险。"
---

# FX Quant Analysis

## Workflow

1. State every quote as quote-currency units per base-currency unit and define the portfolio numeraire.
2. Align venue/session, spot date, settlement holidays, cut-off, fixing source and rollover convention.
3. Separate spot return, forward points/carry, funding, cross-currency basis, fees and translation effects.
4. Build cross rates from simultaneous point-in-time quotes and test triangular consistency.
5. Match forward tenor, rate compounding, collateral currency and settlement convention.
6. Backtest executable bid/ask and rollover rather than midpoint spot alone.
7. Attribute portfolio PnL by currency, spot, carry, hedge, cost and residual; stress gaps and funding.

## Runtime And References

- Domain contract: [references/domain-contract.md](references/domain-contract.md).
- Shared implementation: `data_quant.asset_classes.fx`.
- Manifest diagnostic: `fx-rollover` selects one explicitly oriented canonical pair, retains venue spreads, and emits covered-interest-parity forward points and rollover cashflows with rates and tenor in provenance.
- Manifest diagnostic: `fx-forward-check` intersects both currencies' canonical sessions, validates T+N spot and holiday-adjusted forward value dates, normalizes outright or decimal-points bid/ask, applies an explicitly signed cross-currency basis, and gates deviations from executable CIP bounds.
- Calendars/PIT and execution use the data-engineering and black-box Skills.

## Guardrails

- Never invert a pair without also inverting bid/ask correctly.
- Never mix base/quote orientation, local/base reporting currency or spot/forward returns.
- Never use one market's holiday/session for both legs of a cross-currency trade.
- Never label spot excess return as carry without forward/funding decomposition.
