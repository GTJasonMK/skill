---
name: futures-quant-analysis
description: "Futures quantitative research workflow for contract masters, expiry and notice dates, continuous contracts, roll rules, settlement and variation margin, basis/carry, calendar spreads, margin, limits, liquidity, execution, backtesting, and risk. Use for commodity, equity-index, rates, FX, or crypto futures when contract lifecycle changes the data or PnL. 中文触发：期货量化、主力连续、换月、展期、基差、期限结构、保证金、结算价、交割、跨期套利。"
---

# Futures Quant Analysis

## Workflow

1. Identify exchange, underlying, contract multiplier, tick, currency, expiry, last-trade and first-notice rules.
2. Build an effective-dated contract master and trading calendar before constructing a continuous series.
3. Separate raw contract returns, roll return, collateral/funding return, fees, and variation margin.
4. Declare the roll trigger ex ante: fixed days, open interest, volume, or liquidity. A volume/OI rule must use only values observable at the roll decision.
5. Validate limits, margin changes, delivery risk, session boundaries, holiday gaps, and contract-specific liquidity.
6. Backtest actual contracts and orders; use continuous prices for signal research only unless the PnL bridge is explicit.
7. Stress basis, curve shape, spread liquidity, limit moves, margin calls, and forced liquidation.
8. Return shared Artifacts and a stage verdict; never submit live orders.

## Runtime And References

- Domain contract: [references/domain-contract.md](references/domain-contract.md).
- Data/PIT/calendar rules: `../quant-data-engineering/SKILL.md`.
- Execution and risk: `../quant-trading-black-box-analysis/SKILL.md`.
- Shared implementation: `data_quant.asset_classes.futures`.
- Manifest diagnostic: `futures-roll` consumes canonical `futures_contracts` and raw `market_bars`; it supports expiry, confirmed volume, or confirmed open-interest migration, attributes same-timestamp observable roll gaps, derives gap-adjusted futures returns, and adds an explicit flat collateral return assumption.
- Manifest diagnostic: `futures-roll-execution` reuses the same PIT selection, closes/opens roll legs at exact-timestamp bid/ask, charges explicit fees, settles daily variation margin and collateral return to cash, applies collateral haircuts and effective initial/maintenance margin, and gates daily cash-loss or exchange price-limit breaches without submitting orders.

Use `build_unadjusted_continuous_futures` only as a transparent expiry-rule baseline. It does not back-adjust roll gaps and is not a tradable backtest by itself.

## Guardrails

- Never use a future-known dominant contract or back-adjustment in signal formation.
- Never treat spot, front-contract, continuous-contract, and collateral returns as interchangeable.
- Never ignore first-notice/delivery constraints, multiplier, settlement convention, or margin.
- Never infer executable spread fills from independent leg closes without leg-risk and liquidity evidence.
