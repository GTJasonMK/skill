# Data and Backtest Playbook

Use when: auditing datasets, timestamps, future-function risk, backtests, claimed strategy performance, or execution assumptions.
Read after: [agent-playbooks.md](agent-playbooks.md) identifies a data or backtest mode.
Key decisions: data class, point-in-time availability, universe reconstruction, tradability, execution, cost credibility.
Do not use for: detailed factor formulas, optimizer design, or exact source-table lookup.

## Contents

- [Evidence Mode and Script-First Diagnostics](#evidence-mode-and-script-first-diagnostics)
- [Dataset Audit](#dataset-audit)
- [Future-Function Audit](#future-function-audit)
- [Backtest Review](#backtest-review)
- [Required Reruns](#required-reruns)

## Evidence Mode and Script-First Diagnostics

Use evidence mode when the user provides a CSV, table, schema, field list, code artifact, backtest output, holdings, weights, trades, or logs. Read [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md) first, then inspect the artifact before accepting or rejecting any factor claim.

If `statistical-learning-analysis` is available and the data is local CSV, use its scripts before writing custom analysis code:

| Diagnostic need | Preferred scripts |
| --- | --- |
| Structure and panel shape | `profile_dataset.py`, `panel_summary.py`, `missingness_report.py` |
| Point-in-time and execution timing | `point_in_time_audit.py`, `execution_timing_audit.py` |
| Tradability | `tradability_audit.py` |
| Factor evidence | `factor_ic_report.py`, `factor_quantile_report.py`, `factor_decay_report.py`, `factor_turnover_report.py` |
| Costs and capacity | `transaction_cost_report.py`, `capacity_impact_report.py` |
| Cross-sectional regression | `cross_sectional_return_regression.py`, `fama_macbeth_regression.py` |
| Portfolio and exposure | `portfolio_backtest.py`, `portfolio_exposure_report.py`, `portfolio_constraint_check.py` |
| Gate or aggregate review | `alpha_research_gate_report.py`, `portfolio_construction_gate_report.py`, `quant_report_aggregator.py`, `quant_review_pack.py` |

If a script cannot run, still inspect the same diagnostics manually and report why the deterministic check was unavailable.

## Dataset Audit

Use when the user provides a CSV, database table, schema, field list, factor panel, or return panel.

Classify:

- Raw market data, point-in-time fundamentals, vendor factors, factor panel, return panel, holdings, trades, or backtest output.
- Validation, implementation, or forensic audit.

Read:

- [a-share-data-details.md](../data/a-share-data-details.md)
- [data-and-implementation.md](../data/data-and-implementation.md)
- [validation-and-risks.md](../practice/validation-and-risks.md)

Inspect first:

- `date` or rebalance date.
- `asset_id` or security identifier.
- Signal or factor value.
- Forward return label with clear start and end dates.
- Tradability fields or enough data to reconstruct them.
- Industry and market-cap fields for exposure diagnostics.
- Announcement, correction, or vendor-availability timestamps for fundamentals.

Check:

- Which evidence-mode diagnostics were run or manually replicated.
- Duplicate keys by date and asset.
- Missing values by date, industry, and size group.
- Cross-sectional stock count by date.
- Extreme values, stale values, and repeated ranks.
- Survivorship or current-constituent bias.
- Label overlap when cross-validation or ML is planned.

Stop or downgrade if:

- Financial data only has fiscal period end.
- Return labels start before execution.
- Dataset contains only stocks that survive to the end date.
- Full-sample winsorization, standardization, neutralization, PCA, or imputation was already applied.

## Future-Function Audit

Use when accounting, alternative data, or vendor features could be known only after the simulated trade.

Inspect first:

- Original event date, report period end, announcement date, correction date, vendor update timestamp, and strategy rebalance date.
- Whether restated values replace historical values before restatement publication.
- Whether industry mappings, index constituents, ST flags, or delisting status use future classifications.
- Whether the execution price is after signal computation.

Try next:

- Rebuild the panel using availability timestamps.
- Delay accounting variables until observable.
- Run sensitivity with conservative lags.
- Compare performance before and after point-in-time rebuild.

Stop or downgrade if:

- No timestamp can establish observability.
- Performance exists only when fiscal-period-end data is used immediately.
- The strategy buys limit-up names or sells limit-down names in the simulation.

## Backtest Review

Use when the user provides performance metrics, a net value curve, code, or a claimed strategy result.

Classify:

- Signal backtest, long-short anomaly test, long-only portfolio, index enhancement, Smart Beta product, or ML strategy.
- Research evidence versus executable PnL.

Read:

- [validation-and-risks.md](../practice/validation-and-risks.md)
- [a-share-data-details.md](../data/a-share-data-details.md)
- [practice-deep-dive.md](../practice/practice-deep-dive.md)
- [report-templates.md](../core/report-templates.md) for findings-first review format.

Inspect first:

- Signal timestamp, trade timestamp, and return window.
- Universe reconstruction and survivorship handling.
- Trading price and delay: same close, next open, next close, VWAP, or another executable convention.
- Costs: commission, stamp duty, spread, effective spread, slippage, impact, borrow, financing.
- Tradability: suspension, price limits, ST, listing age, low liquidity, blacklists.
- Parameter selection process and locked final test.

Try next:

- Recompute gross versus net returns.
- Split by year, regime, size, industry, liquidity, turnover, and long/short leg.
- Attribute returns to market, industry, style, and residual alpha.
- Run cost sensitivity, participation sensitivity, and capacity sensitivity.
- Compare with simple baselines.

Stop or downgrade if:

- Timing and tradability cannot be audited.
- Performance disappears under reasonable costs.
- Model superiority lacks out-of-sample or walk-forward evidence.
- Gross long-short returns are presented as feasible long-only alpha.

## Required Reruns

When a result is questionable, request or perform only reruns that can change the verdict:

- Strict point-in-time rebuild.
- Next-tradable-day execution.
- Realistic costs and market-impact sensitivity.
- Current-constituent removal.
- Equal-weight versus value-weight comparison.
- Size, industry, liquidity, and regime splits.
- Locked final test or post-publication split.
