# Quant Finance Anti-Patterns

Use this file when reviewing alpha research, risk models, portfolio construction, financial time-series notebooks, or backtests. Name the failure mode, explain the consequence, then give the correction.

## Data and Universe Construction

| Anti-pattern | Why it is wrong | Correction |
| --- | --- | --- |
| Using current constituents for historical tests. | Delisted and removed assets disappear, inflating returns and reducing drawdowns. | Use point-in-time universe membership, delisting returns, and historical eligibility rules. |
| Joining fundamentals by fiscal period end instead of availability date. | The model sees data before investors could have known it. | Use announcement/filing/availability timestamps and apply realistic reporting lags. |
| Assuming historical `data_date` columns make a dataset point-in-time. | Observation dates do not prove the values were available before each decision timestamp. | Audit availability, release, revision, vendor, universe, signal, rebalance, and execution timestamps before IC or backtests. |
| Backfilling revised macro or fundamental data. | Revisions leak future information into past decisions. | Use vintage or point-in-time datasets; otherwise mark the analysis as non-tradable research. |
| Filtering the universe with future liquidity, price, or market-cap information. | Asset eligibility is conditioned on later outcomes. | Compute universe filters at each rebalance timestamp using only prior or same-time observable fields. |
| Treating missing prices as zero returns without cause checks. | Suspensions, holidays, bad data, and delistings have different meanings. | Distinguish non-trading days, stale prices, bad ticks, and true delisting outcomes. |
| Mixing currencies or return definitions. | Apparent alpha can be FX exposure or inconsistent compounding. | Convert to common currency and document simple/log, gross/excess, and close/open timing. |

## Factor Research

| Anti-pattern | Why it is wrong | Correction |
| --- | --- | --- |
| Computing z-scores, winsorization cutoffs, or ranks on the full sample. | Future cross-sections affect historical signals. | Transform within each timestamp using only that timestamp's eligible universe. |
| Sorting on a signal that was not lagged to the trade date. | Forward returns are matched with unavailable signal values. | Explicitly define signal timestamp, rebalance timestamp, execution price, and forward-return horizon. |
| Reporting one strong backtest after testing many factors. | Data snooping turns noise into apparent skill. | Track the tested factor family, failed variants, selected candidates, final-test evidence, and data/code versions; then use validation/test periods and adjust for multiple testing or false discovery. |
| Keeping only promoted alpha experiments in the research log. | Multiple-testing and reality-check reports use an incomplete denominator. | Maintain an experiment registry with rejected, failed, abandoned, and promoted variants before running FDR, reality checks, or alpha gates. |
| Interpreting high IC as tradable alpha by itself. | IC ignores turnover, costs, capacity, borrow, and constraints. | Pair IC with quantile returns, turnover, cost estimates, drawdowns, and exposure checks. |
| Ignoring sector, beta, size, or liquidity exposure. | The signal may be a disguised known risk factor. | Report neutralized and unneutralized results plus factor/sector exposure diagnostics. |
| Calling a new signal incremental because raw IC is positive. | The candidate can be spanned by existing signals or known exposures. | Predeclare the base signal/exposure set and report residual IC, delta R-squared, and out-of-sample value. |
| Orthogonalizing factors without stating order. | Residualized factors depend on the chosen ordering. | State the base factor set and residualization order; test incremental value out of sample. |
| Treating PCA factors as economic factors by default. | Components can rotate and may not map to stable economic drivers. | Validate rolling stability, loadings, explained variance, and relationship to known exposures. |

## Backtesting and Execution

| Anti-pattern | Why it is wrong | Correction |
| --- | --- | --- |
| Random train/test splits for financial time series. | Future regimes leak into model selection. | Use walk-forward, rolling, expanding, purged, or embargoed validation. |
| Executing at the same close used to compute the signal. | The trade price is not available after signal calculation. | Use next-open/next-close execution assumptions and document order timing. |
| Starting the forward-return window before the simulated fill. | Backtest or IC results include returns the strategy could not have earned. | Audit signal, rebalance, execution, return-start, and return-end timestamps before interpreting results. |
| Reporting gross returns only. | High-turnover strategies often disappear after costs. | Report gross and net performance with commissions, spread/slippage, borrow, financing, and market-impact assumptions. |
| Ignoring turnover and capacity. | Scalable economic value depends on how much must trade. | Report one-way/two-way turnover, dollar volume participation, and sensitivity to cost levels. |
| Rebalancing into assets that could not be traded or shorted. | Practical constraints change realized performance and can turn fake fills into fake alpha. | Run a tradability audit for liquidity, borrowability, halt/suspension status, price-limit locks, stale prices, and short-sale constraints before portfolio formation. |
| Tuning strategy rules on the final backtest. | The backtest becomes training data. | Reserve an untouched test period or use nested walk-forward selection. |
| Annualizing short samples mechanically. | A few lucky periods create misleading Sharpe and CAGR. | Show sample length, confidence/uncertainty, path drawdowns, and regime coverage. |

## Risk, Attribution, and Reporting

| Anti-pattern | Why it is wrong | Correction |
| --- | --- | --- |
| Calling regression alpha investable alpha. | Alpha can vanish after timing, costs, constraints, or omitted factors. | Report net returns, benchmark fit, residual risk, factor exposures, and implementation assumptions. |
| Using IID standard errors for autocorrelated returns. | T-stats are overstated when residuals cluster over time. | Use HAC/Newey-West, block bootstrap, clustered errors, or conservative inference. |
| Reporting Sharpe without drawdown and tail metrics. | Mean/volatility misses path risk, skew, and crashes. | Include max drawdown, VaR/ES, skew, kurtosis, hit rate, and stress periods. |
| Optimizing portfolios from noisy expected returns without constraints. | Small input errors create unstable extreme weights. | Use shrinkage, robust constraints, turnover limits, and sensitivity analysis. |
| Comparing strategies with different leverage or cash assumptions. | Risk and return are not on the same basis. | Normalize leverage, cash yield, benchmark, and financing treatment before comparison. |
| Omitting benchmark and factor exposure attribution. | Performance may come from beta, style, sector, or duration exposure. | Report benchmark-relative metrics and factor/sector contributions. |
