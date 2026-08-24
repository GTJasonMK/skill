---
name: fixed-income-quant-analysis
description: "Fixed-income quantitative workflow for instrument cashflows, day-count and business-day conventions, yield and discount curves, duration/convexity, carry and roll-down, spread and credit risk, default/recovery, portfolio attribution, liquidity, and stress testing. 中文触发：固收量化、债券定价、收益率曲线、久期、凸性、票息、信用利差、骑乘、滚降、违约、利率风险。"
---

# Fixed-Income Quant Analysis

## Workflow

1. Reconstruct instrument cashflows from issue terms, calendars, day-count, coupon, amortization, call/put and default provisions.
2. Separate clean/dirty price, accrued interest, settlement date, currency and quote convention.
3. Select and version the discount, projection, government, swap or credit curve appropriate to the claim.
4. Compute price, yield, duration, convexity, spread, carry and roll-down with consistent compounding.
5. Attribute portfolio return to curve, spread, carry, roll, FX, defaults, fees and residual.
6. Model liquidity, repo/funding, haircut, margin, downgrade/default and recovery.
7. Stress parallel/nonparallel curve moves, spread widening, correlation and forced liquidation.

## Runtime And References

- Domain contract: [references/domain-contract.md](references/domain-contract.md).
- Shared implementation: `data_quant.asset_classes.fixed_income` provides cashflow price/duration/convexity baselines.
- Manifest diagnostic: `fixed-income-shock` reconstructs a declared level-coupon baseline from canonical instrument terms and emits price, duration, convexity, and symmetric parallel-yield shock returns; its Artifact explicitly retains exact schedule, curve, credit, and liquidity gaps.
- Manifest diagnostic: `fixed-income-curve-stress` builds regular dated coupon cashflows with declared day-count and business-day rules against canonical sessions, selects the latest observable PIT zero curve, forbids extrapolation, reports dirty price/DV01/duration, and gates parallel or key-rate scenario losses.
- Manifest diagnostic: `credit-migration-stress` selects PIT portfolio exposures and one-horizon transition rows, validates complete probability rows, applies spread-duration migration repricing plus explicit default recovery, stresses default probability, and gates expected credit loss.
- Data and risk use the root contracts and shared risk modules.

## Guardrails

- Never mix yield, spot, forward and spread measures without stating the curve and compounding basis.
- Never ignore accrued interest, settlement, embedded options or currency.
- Never infer liquidity from stale evaluated prices.
- Never call duration alone a complete risk model for nonlinear, credit or option-embedded instruments.
