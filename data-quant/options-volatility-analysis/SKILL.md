---
name: options-volatility-analysis
description: "Options and volatility quantitative workflow for option chains, contract terms, rates/dividends, implied volatility, Greeks, surfaces, static arbitrage, early exercise, assignment, margin, hedging PnL, liquidity, and volatility-strategy backtests. 中文触发：期权量化、隐含波动率、波动率曲面、希腊字母、Delta对冲、Gamma、Vega、波动率套利、行权、保证金。"
---

# Options And Volatility Analysis

## Workflow

1. Lock underlying, venue, exercise style, settlement, multiplier, expiry, strike, currency, rate and dividend assumptions.
2. Validate quote timestamps, bid/ask, stale quotes, contract adjustments, corporate actions, open interest and executable liquidity.
3. Compute model prices and Greeks with declared model and units; invert implied volatility only inside no-arbitrage bounds.
4. Build surfaces by expiry/moneyness with static-arbitrage checks and point-in-time smoothing.
5. Separate option PnL into delta, gamma, vega, theta, rates/dividends, residual, fees and hedge slippage.
6. Model exercise/assignment, margin, borrow, pin and gap risk when applicable.
7. Backtest actual contracts and hedge trades, not a future-cleaned IV surface.
8. Stress spot, volatility level/skew, rates, dividends, liquidity and jump scenarios.

## Runtime And References

- Domain contract: [references/domain-contract.md](references/domain-contract.md).
- Shared implementation: `data_quant.asset_classes.options` provides European Black-Scholes diagnostics and implied volatility.
- Manifest diagnostic: `option-surface-check` binds canonical contracts/quotes to one underlying and expiry, recovers IV, and blocks strike-monotonicity, butterfly-convexity, or model-bound failures while reporting parity deviations.
- Manifest diagnostic: `option-surface-smooth` builds a latest-common-time PIT European surface across expiries, collapses call/put IVs onto log-moneyness nodes, applies rolling-median smoothing, and performs bounded linear moneyness/term interpolation without extrapolation.
- Manifest diagnostic: `option-hedge-replay` aligns one European option quote series with raw underlying bars, recovers point-in-time IV/Greeks, and attributes signed option mark-to-market, discrete delta-hedge PnL, hedge costs, and excessive-spread blockers without submitting hedge orders.
- Data and execution use `quant-data-engineering` and `quant-trading-black-box-analysis`.

## Guardrails

- Never use mid prices as guaranteed fills or stale zero-bid options as liquid marks.
- Never apply European formulas to American exercise without labeling the model limitation.
- Never compare Greeks with inconsistent units, multipliers, volatility scales or time bases.
- Never call delta-hedged backtest PnL volatility alpha without hedge timing, costs and residual attribution.
