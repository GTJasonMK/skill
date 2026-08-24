---
name: crypto-quant-analysis
description: "Crypto quantitative workflow for venue/instrument masters, spot, perpetuals and dated futures, funding, basis, margin, liquidation, 24/7 calendars, exchange outages, fragmented liquidity, on-chain availability, custody and counterparty risk. 中文触发：加密量化、数字货币、永续合约、资金费率、基差、爆仓、清算、交易所风险、链上数据、24小时交易。"
---

# Crypto Quant Analysis

## Workflow

1. Identify venue, instrument, collateral, margin mode, contract type, multiplier, quote orientation and custody path.
2. Treat each venue as a separate market; align server/event/receipt timestamps and outage intervals.
3. Separate spot, dated-future basis, perpetual funding, fees/rebates, borrow, collateral yield and liquidation effects.
4. Version funding formulas, mark/index composition, margin tiers, liquidation and insurance/ADL rules.
5. Validate 24/7 data gaps, venue fragmentation, stale marks, transfer latency and counterparty limits.
6. For on-chain signals, distinguish block/event time, indexing time and first strategy-available time.
7. Backtest actual venue instruments with funding and liquidation; stress outage, depeg, gap and forced deleveraging.

## Runtime And References

- Domain contract: [references/domain-contract.md](references/domain-contract.md).
- Shared implementation: `data_quant.asset_classes.crypto`.
- Manifest diagnostic: `crypto-margin-stress` binds one venue/instrument/quote, applies funding and explicit price shocks, reports maintenance buffers, and blocks scenarios that breach maintenance margin; it remains a linear isolated-position diagnostic rather than an exchange liquidation engine.
- Manifest diagnostic: `crypto-cross-margin-stress` selects one venue/account's PIT positions, canonical cross-margin instruments, latest marks, and effective contiguous margin tiers; it aggregates funding and scenario PnL, then gates maintenance liquidation, liquidation fees, insurance-fund exhaustion/socialized ADL, and venue-default recovery loss.
- Execution fidelity and market-structure claims use the black-box Skill.

## Guardrails

- Never merge venue prices/funding as if they were one executable market.
- Never omit funding, collateral, margin tier, liquidation or exchange outage from leveraged PnL.
- Never treat block timestamp as immediate strategy availability.
- Never treat a backtest on the surviving exchange/instruments as proof free of survivorship or counterparty risk.
