# A-Share Data Details

## Contents

- [Price and Volume Data](#price-and-volume-data)
- [Forward and Backward Adjustment](#forward-and-backward-adjustment)
- [Suspensions and Reopenings](#suspensions-and-reopenings)
- [Minimum Trading-Day Rule](#minimum-trading-day-rule)
- [Financial Reporting Timeline](#financial-reporting-timeline)
- [Restatements and Point-in-Time Records](#restatements-and-point-in-time-records)
- [Single-Quarter and TTM Data](#single-quarter-and-ttm-data)
- [Universe and Exclusion Rules](#universe-and-exclusion-rules)
- [Sorting, Rebalancing, and Tradability](#sorting-rebalancing-and-tradability)
- [A-Share Empirical Defaults](#a-share-empirical-defaults)

## Price and Volume Data

Use this file when a user asks about A-share data cleaning, future-function audits, factor construction inputs, or why a backtest differs from book-style evidence.

Daily price-volume fields usually include:

- Open, high, low, close, adjusted close.
- Volume, amount, turnover.
- Trading status, suspension status, price-limit status.
- Corporate-action adjustment factors.

Core rule: price-volume data look simpler than accounting data, but A-share trading rules make naive returns dangerous. Treat suspension, price limits, reopenings, and tradability as part of the research design, not as post-processing.

## Forward and Backward Adjustment

Forward adjustment (前复权):

- Keeps the latest price unchanged.
- Adjusts historical prices so the chart is continuous.
- Useful for visual inspection and technical overlays.
- Problem: historical forward-adjusted prices are time-varying after each ex-rights or dividend event.
- Problem: long dividend histories can create negative historical adjusted prices.

Backward adjustment (后复权):

- Keeps historical prices unchanged.
- Adjusts later prices after corporate actions.
- Better represents a long-horizon investor's wealth path.
- Less suitable for charting because adjusted prices may diverge from traded prices.
- Book-style return calculations use backward-adjusted prices when reconstructing historical performance.

Practical guidance:

- For return series, prefer vendor total-return or backward-adjusted prices with a documented adjustment factor.
- For point-in-time simulations, do not use an adjustment series that is revised with future corporate-action knowledge unless the adjustment is applied only after the event date.
- Store raw prices, adjustment factors, and adjusted prices separately so return disputes can be audited.

## Suspensions and Reopenings

Long suspensions and reopenings (长期停牌、复牌) can create extreme returns. A-share stocks that resume after restructuring or suspended listing may have no normal price-limit constraint on the reopening day.

Book-style treatment:

```text
After 1996-12-15:
if R_it > 10%, set R_it = 10%
if R_it < -10%, set R_it = -10%
```

Interpretation:

- This approximates the normal A-share daily limit after the price-limit regime began.
- It is a research normalization rule, not a universal trading-cost model.
- ST stocks usually have a 5% limit, and IPO/relisting/reopening days may have special rules.

Suspension-day fill rules (停牌日填充值):

- Momentum: filling the suspended day price with the last traded price can be acceptable when the goal is to measure price change over a calendar trading window.
- Volatility: do not fill suspension-day returns with zero. Zero return means no trade, not no economic risk.
- Beta or exposure regressions: treat suspended-day stock returns as missing, otherwise beta is biased downward or distorted.
- Liquidity and tradability: suspension is a direct negative tradability signal and should not be hidden by imputation.

## Minimum Trading-Day Rule

Minimum trading-day filters (最少交易日) prevent small-sample artifacts.

Default book rule:

```text
valid observations >= 2/3 of window length
```

Examples:

- For a 21-trading-day volatility window, require at least 14 valid returns.
- For 252-trading-day beta or turnover windows, require enough non-suspended observations before estimating.

Failure mode:

- A stock trading only a few days in a month can show artificially low volatility or unstable returns.
- Sparse observations can create misleading rank extremes in volatility, beta, illiquidity, and momentum factors.

## Financial Reporting Timeline

Accounting data need point-in-time timestamps.

Reporting period (报告期):

- A-share fiscal year normally ends on December 31.
- Standard periods are first quarter, half-year, third quarter, and annual report.
- Period labels such as `20180930` identify the accounting period, not the date the data became observable.

Disclosure date:

- The date a report is released.
- Factor construction must use this date, vendor availability date, or another defensible observable timestamp.
- Do not make data available at the reporting-period end.

Financial statements:

- Balance sheet: point-in-time stock values.
- Income statement and cash-flow statement: period-flow values.
- Owner's equity statement and notes may affect accounting interpretation but are less often used directly in factor formulas.

Benchmark reporting period (基准报告期):

- Balance sheet benchmark usually references the prior annual report.
- Income and cash-flow benchmark usually references the same period in the prior year.
- A later report can restate a prior benchmark period; this is why record type matters.

## Restatements and Point-in-Time Records

Restatements and corrections (调整和更正) are a major future-function source.

Simple but flawed approaches:

- Use only first disclosure: avoids future data but ignores later corrections that were known at later dates.
- Use latest corrected value everywhere: easy to compute but leaks future corrections into the past.

Point-in-time rule:

```text
At each historical date, use the latest accounting record that was already disclosed and vendor-available by that date.
```

Common record types:

| Type | Meaning |
| --- | --- |
| Type 1 | Initial statement, latest value |
| Type 2 | Benchmark statement, latest value |
| Type 3 | Initial statement, original value |
| Type 4 | Benchmark statement, original value |

Usage patterns:

- No restatement: use Type 1 after initial disclosure.
- Benchmark report later appears: use Type 1 until the benchmark disclosure, then Type 2.
- Correction before benchmark report: use Type 3 before correction, Type 1 after correction, Type 2 after benchmark disclosure.
- Correction after benchmark report: use Type 3 before benchmark disclosure, Type 4 before correction, Type 2 after correction.

Audit questions:

- Does each accounting value have `report_period`, `announce_date`, and `effective_available_date`?
- Are corrections applied only after the correction announcement?
- Are benchmark-period values overwritten by later records before they were available?
- Are vendor data snapshots reproducible?

## Single-Quarter and TTM Data

Single-quarter data (单季度):

- Balance-sheet variables are point-in-time values, so the single-quarter value is the reported period value.
- Income and cash-flow values are cumulative within the fiscal year.
- Q1 equals the first-quarter cumulative value.
- Q2, Q3, and Q4 single-quarter values equal current cumulative value minus previous cumulative period value.

```text
single_quarter_Q1 = current_Q1
single_quarter_Qk = current_cumulative_Qk - previous_cumulative_Q(k-1)
```

If the previous cumulative period is missing, set the single-quarter flow to missing rather than fabricating it.

TTM:

```text
TTM = current_cumulative + prior_annual - prior_same_period_cumulative
```

Use this for income-statement and cash-flow-statement flows when the latest report is not annual.

Fallback annualization:

```text
annualized_Q1 = current_cumulative * 4
annualized_H1 = current_cumulative * 2
annualized_Q3 = current_cumulative * 4/3
```

Use annualization only when prior annual or prior same-period data are unavailable, and mark it as lower quality.

Balance-sheet variables:

- Use latest point-in-time value, four-quarter average, or current/prior-year average depending on the factor definition.
- Do not call balance-sheet averages TTM; TTM is for flow variables.

## Universe and Exclusion Rules

Financial stocks (金融股):

- Academic studies often exclude banks, brokers, and insurers because their accounting structure differs from industrial firms.
- The book keeps financial stocks unless a factor's accounting logic requires exclusion.
- Practical answer: decide factor by factor and report the rule.

Blacklist stocks (黑名单):

- Delisting-risk stocks.
- ST or risk-warning stocks.
- Negative net-asset stocks.
- Newly listed stocks, often less than one year of listing history.
- Mandate-ineligible or compliance-restricted names.

Why exclusions matter:

- Exclusions change the return model because they remove a set of stocks with systematic characteristics.
- Excluding high-turnover, high-volatility, expensive-low-quality names already embeds low-speculation, value, and quality information.
- Never change the universe rule silently between research and production.

Research universe default:

- Shanghai main board, Shenzhen main board, SME board, and ChiNext.
- Exclude STAR Market when following the book's 2000-2019 empirical setup.
- Start in 2000 for more stable accounting rules and sufficient cross-sectional breadth.

## Sorting, Rebalancing, and Tradability

Sorting and grouping:

- Single sorting commonly uses 10 groups for firm characteristics.
- Independent double sorting commonly uses size and target variable in `5 x 5` portfolios.
- Fama-French-style factor construction often uses `2 x 3` independent double sorting.
- Always state equal-weight or value-weight returns.

Rebalancing frequency (调仓频率):

- Price-volume factors often use monthly rebalancing.
- Accounting factors often use annual or quarterly rebalancing.
- The book's factor tests use monthly rebalancing for all factors to reduce information staleness.

Tradability filters (不可交易):

- Exclude stocks suspended on the rebalance date.
- Exclude one-word limit-up stocks when the strategy needs to buy.
- Exclude one-word limit-down stocks when the strategy needs to sell or when long-only legs proxy a short-leg restriction.
- Price limits, borrow constraints, and suspensions make paper long-short spreads overstate implementable profit.

Transaction cost:

- The book's chapter-3 empirical tests set rebalancing cost to zero.
- Real implementation should model commissions, stamp duty, bid-ask spread, impact, turnover, and failed execution.
- A rough single-side estimate can be used for sensitivity analysis, but production needs stock-level cost estimates.

## A-Share Empirical Defaults

Use these defaults when reconstructing or reviewing book-style A-share factor evidence:

1. Use point-in-time accounting values based on disclosure or vendor availability date.
2. Use backward-adjusted or total-return prices for return calculation.
3. Treat long suspension reopenings and abnormal returns explicitly.
4. Do not fill suspended-day returns as zero for volatility or beta.
5. Require at least two-thirds valid observations in rolling windows.
6. Apply stock eligibility rules before ranking, not after portfolio returns are computed.
7. Keep raw factor values, winsorized values, standardized values, and neutralized values separately.
8. Report equal-weight and value-weight results when the claim is about broad factor validity.
9. Add tradability, cost, capacity, and price-limit checks before claiming implementable alpha.
