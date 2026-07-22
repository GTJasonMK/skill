# Quantitative Finance Statistical Methods

Use this reference when the user asks about quantitative finance, alpha research, factor analysis, risk models, portfolio construction, asset pricing, financial time series, or backtesting. This is research and education guidance, not investment advice.

## Contents

- [Quant Workflow](#quant-workflow)
- [Data Foundations](#data-foundations)
- [Factor Analysis Families](#factor-analysis-families)
- [Factor Research Playbooks](#factor-research-playbooks)
- [Risk and Portfolio Methods](#risk-and-portfolio-methods)
- [Financial Time Series](#financial-time-series)
- [Backtesting and Validation](#backtesting-and-validation)
- [Common Quant Anti-Patterns](#common-quant-anti-patterns)
- [Bundled Quant Scripts](#bundled-quant-scripts)
- [Implementation Notes](#implementation-notes)

For concise method intuition, interpretation, and failure modes, read [quant-method-principles.md](quant-method-principles.md).
For paper trading, live monitoring, and go-live checks, read [quant-production-monitoring.md](quant-production-monitoring.md).

## Quant Workflow

1. Define the unit: asset, portfolio, cross-section, time series, trade, or order.
2. Define the prediction/effect horizon: intraday, daily, monthly, quarterly, or event-window.
3. Define the tradable universe and eligibility at each timestamp before computing signals.
4. Convert prices to adjusted returns only after handling splits, dividends, delistings, holidays, stale prices, and currency.
5. Separate signal research, risk modeling, portfolio construction, execution assumptions, and performance attribution.
6. Use walk-forward, time-split, purged, or embargoed validation; do not use random IID splits for financial time series.
7. Include transaction costs, turnover, capacity, liquidity, shorting/borrow constraints, and rebalance timing before claiming economic value.
8. Before live trading, freeze the research specification and define live-vs-paper, signal-health, execution, risk, and kill-switch monitoring.

## Data Foundations

| Topic | What to check | Why it matters |
| --- | --- | --- |
| Adjusted prices | Splits, dividends, corporate actions, symbol changes. | Raw prices create false returns. |
| Survivorship | Delisted assets and historical index membership. | Survivorship bias inflates performance. |
| Point-in-time data | Accounting data availability date, restatements, index membership date. | Look-ahead bias is common in factors. |
| Calendar alignment | Trading days, holidays, time zones, asset-specific missing dates. | Misalignment creates fake lead-lag effects. |
| Return definition | Simple vs log returns; gross vs excess returns; close-to-close vs open-to-close. | Factor regressions and risk metrics must match definitions. |
| Universe construction | Liquidity, price, market cap, borrowability, listing age. | Universe filters must be known at rebalance time. |
| Outliers | Bad ticks, stale prices, limit moves, corporate action errors. | Winsorization should not hide data errors. |
| Risk-free rate | Frequency-matched and currency-matched. | Needed for excess returns, alpha, Sharpe, CAPM/FF regressions. |

## Factor Analysis Families

| Method/family | Core idea | Use when | Avoid or watch |
| --- | --- | --- | --- |
| CAPM beta | Regress asset excess return on market excess return. | Need market exposure and alpha baseline. | Alpha is not causal skill; beta instability matters. |
| Fama-French / Carhart regressions | Regress excess returns on published style factors such as market, size, value, profitability, investment, momentum. | Evaluate whether returns are explained by common risk premia. | Match factor frequency, region, currency, and risk-free definition. |
| Time-series factor exposure regression | Estimate alpha and betas for an asset/strategy against factor returns. | Performance attribution and risk exposure measurement. | OLS t-stats can be wrong under autocorrelation/heteroskedasticity; consider HAC/Newey-West. |
| Fama-MacBeth regression | Run cross-sectional regressions over time, then average premia. | Estimate factor risk premia or characteristic returns across assets. | Requires time-series dependence corrections and point-in-time characteristics. |
| Cross-sectional return regression | Regress future asset returns on current characteristics/exposures within one rebalance date or pooled sample. | Need quick characteristic-return diagnostics before full panel work. | Pooled IID t-stats are weak evidence; repeated dates need Fama-MacBeth or panel errors. |
| Statistical PCA factors | Extract orthogonal components from asset return covariance/correlation. | Build statistical risk factors or reduce dimension. | Components can rotate and lack economic meaning; use rolling stability checks. |
| Fundamental/risk-model factors | Use predefined exposures such as industry, size, value, momentum, quality, beta, volatility. | Risk attribution, portfolio neutrality, optimizer constraints. | Exposure definitions and neutralization choices drive results. |
| Factor analysis model | Explain covariance with latent factors plus idiosyncratic noise. | Need latent common drivers beyond PCA variance directions. | Factor count/rotation are modeling choices; validation is essential. |
| Dynamic factor model | Latent factors evolve over time and explain many time series. | Macro/asset panels with common time-varying drivers. | Factor interpretation and stationarity must be checked. |
| Factor mimicking portfolio | Construct tradable long-short portfolios representing factor exposures. | Need investable factor returns from characteristics. | Sorting, weighting, neutralization, transaction costs, and universe rules matter. |
| Characteristic-sorted portfolios | Sort assets into quantiles by signal and compare future returns. | First-pass alpha signal validation. | Sorting must use lagged point-in-time data; quantile spread ignores costs unless added. |
| Information coefficient (IC) | Correlate signal ranks with future returns. | Evaluate cross-sectional predictive signal quality. | Serial dependence and multiple testing inflate significance. |
| Rank IC | Spearman correlation between factor rank and future return rank. | Robust cross-sectional signal validation. | High IC does not guarantee tradable profit after turnover/cost. |
| Signal overlap / redundancy | Compare signal correlations, rank correlations, and selected-name overlap across many alpha signals. | Need to decide whether multiple signals add independent breadth. | High overlap can make a multi-alpha book behave like one crowded trade. |
| Incremental alpha diagnostics | Compare a candidate signal's residual IC and model contribution after controlling for existing signals or exposures. | Need to decide whether a new alpha adds independent value to an existing library. | Positive raw IC can vanish after base signals, sectors, style, or liquidity are controlled. |
| Neutralization | Remove market/sector/size/beta exposure from signal or portfolio. | Need isolate alpha from known risk exposures. | Over-neutralization can remove intended economic signal. |
| Orthogonalization | Regress one factor on others and use residuals. | Need incremental signal independent of existing factors. | Order-dependent unless design is explicit. |

## Factor Research Playbooks

### Time-Series Exposure Attribution

1. Convert strategy/asset returns and factors to the same frequency and currency.
2. Use excess returns when factors are excess-return factors.
3. Fit alpha/beta regression with intercept.
4. Report alpha, betas, R-squared, residual volatility, and t-stats.
5. Check rolling betas, residual autocorrelation, and drawdowns.
6. Use HAC/Newey-West in a full implementation when residuals are autocorrelated.

### Cross-Sectional Alpha Signal Research

1. Define point-in-time universe and rebalance calendar.
2. Lag all accounting/fundamental data by realistic publication delay.
3. Run `scripts/point_in_time_audit.py` before IC, regression, sorted portfolios, or backtests when availability, release, universe, revision, or execution timestamps are available.
4. Run `scripts/execution_timing_audit.py` before IC, regression, sorted portfolios, or backtests when signal, rebalance, execution, or forward-return window timestamps are available.
5. Run `scripts/tradability_audit.py` before IC, regression, sorted portfolios, or backtests when market-state, volume, limit-lock, shortability, or borrow evidence is available.
6. Winsorize or robustly transform extreme values using only current cross-section.
7. Standardize and optionally sector/size neutralize.
8. Evaluate Pearson IC and rank IC with `scripts/factor_ic_report.py`.
9. Evaluate IC decay across horizons with `scripts/factor_decay_report.py`.
10. Evaluate factor-sorted quantile returns and high-minus-low spread with `scripts/factor_quantile_report.py`.
11. Evaluate selected-name turnover and rank stability with `scripts/factor_turnover_report.py`.
12. Use `scripts/signal_overlap_report.py` when combining many candidate signals to detect redundant or crowded alpha variants.
13. Use `scripts/incremental_alpha_report.py` when a new signal must prove value after existing signals, sectors, styles, or liquidity exposures.
14. Use `scripts/long_short_backtest.py` to form a simple signal-ranked long/short portfolio only after signal timing and tradability are correct.
15. Use `scripts/cross_sectional_return_regression.py` or `scripts/fama_macbeth_regression.py` when the question is characteristic risk premium rather than pure predictive ranking.
16. Use `scripts/factor_neutralization.py` when the intended claim is alpha beyond sector, size, beta, style, or other known exposures.
17. Add transaction costs, liquidity constraints, and capacity estimates before claiming alpha.
18. Use `scripts/quant_experiment_audit.py` to verify the tested family, failed trials, selected variants, final-test evidence, and data/code versions were logged.
19. Correct for multiple testing and data snooping across the audited candidate family.
20. Use `scripts/alpha_research_gate_report.py` to combine completed JSON diagnostics into a research-stage pass/review/fail gate before promotion to portfolio construction or paper trading.

### Statistical Risk Model

1. Choose returns window and frequency.
2. Estimate covariance using sample, shrinkage, EWMA, or factor covariance.
3. Extract PCA/statistical factors or define fundamental exposures.
4. Estimate factor covariance and specific risk.
5. Validate realized vs forecast volatility, factor stability, and residual correlations.
6. Use risk model in optimization only with constraints and out-of-sample monitoring.

### Pair Trading / Cointegration

1. Define eligible pairs without future information.
2. Test spread stationarity/cointegration on formation window.
3. Estimate hedge ratio on training window only.
4. Backtest entry/exit on walk-forward windows.
5. Include borrow, transaction costs, slippage, and short-sale constraints.
6. Monitor regime breaks; cointegration can disappear.

## Risk and Portfolio Methods

| Method | Core idea | Use when | Avoid or watch |
| --- | --- | --- | --- |
| Historical volatility | Standard deviation of returns annualized by frequency. | Simple risk baseline. | Volatility clustering makes fixed-window estimates stale. |
| EWMA volatility/covariance | Exponentially weight recent returns more heavily. | Need adaptive risk estimate. | Decay parameter controls responsiveness/noise. |
| Shrinkage covariance | Pull noisy sample covariance toward structured target. | Many assets relative to observations. | Target choice matters; validate realized risk. |
| Factor covariance | Decompose asset covariance into factor covariance plus specific risk. | Large universes and portfolio risk attribution. | Missed factors leave correlated residuals. |
| Historical VaR / Expected Shortfall | Estimate tail loss from empirical return distribution. | Risk reporting and stress review. | Tail estimates are noisy and backward-looking. |
| Risk forecast calibration | Compare realized returns, standardized returns, and VaR breaches against forecast risk. | Need to validate a volatility or VaR forecast before risk budgeting. | Calibration can look acceptable while tail shape or correlation forecasts are wrong. |
| Drawdown metrics | Track peak-to-trough wealth loss. | Strategy risk communication. | Drawdown depends on path and sample period. |
| Mean-variance optimization | Maximize expected return per unit variance using expected returns and covariance. | Portfolio construction with stable inputs. | Expected returns are noisy; unconstrained weights are unstable. |
| Risk parity | Allocate so assets/risk factors contribute similar risk. | Want diversified risk contributions. | Correlation shifts and leverage constraints matter. |
| Hierarchical Risk Parity | Cluster assets and allocate recursively using covariance structure. | Need robust allocation without return forecasts. | Clustering instability can affect weights. |
| Black-Litterman | Blend market-implied equilibrium returns with investor views. | Need disciplined way to encode views. | View confidence and priors dominate output. |
| Tracking error / information ratio | Measure active risk and active return relative to benchmark. | Benchmark-aware portfolio evaluation. | Benchmark choice must match mandate. |
| Beta and factor exposure constraints | Control portfolio sensitivity to market/style/sector factors. | Risk-controlled factor or alpha portfolio. | Constraints can hide unintended exposures if factor model is poor. |

## Financial Time Series

| Method | Use when | Key warning |
| --- | --- | --- |
| AR/ARIMA/SARIMA | Forecast autocorrelated univariate returns, spreads, or macro/price series. | Asset returns often have weak mean predictability. |
| VAR/VECM | Model interacting time series or cointegrated systems. | Needs stationarity/cointegration checks and enough history. |
| GARCH / EGARCH / GJR-GARCH | Model volatility clustering and asymmetric volatility. | Mean forecast and volatility forecast are different goals. |
| HAR volatility | Model realized volatility across daily/weekly/monthly horizons. | Needs realized volatility data and careful frequency alignment. |
| Regime switching | Allow market states with different mean/volatility. | Regimes are inferred, not directly observed; avoid narrative overfit. |
| Kalman filter / state-space | Time-varying beta, latent trend, dynamic hedge ratio. | Model specification controls inference. |
| Event study | Measure abnormal returns around events. | Event windows, clustering, leakage, and benchmark model matter. |

## Backtesting and Validation

| Validation object | Recommended checks |
| --- | --- |
| Factor signal | Point-in-time audit, execution timing audit, tradability audit, rank IC, quantile spread, IC decay, turnover, signal overlap, incremental value, capacity, sector/size exposures, multiple testing control, research gate status. |
| Strategy return | Walk-forward backtest, execution timing audit, tradability audit, transaction costs, slippage, rebalance timing, drawdown, volatility, beta, factor exposures. |
| Risk model | Realized/forecast volatility ratio, residual correlation, factor stability, stress periods, exposure sanity checks, VaR breach calibration. |
| Portfolio optimizer | Weight stability, turnover, constraint binding, realized risk, sensitivity to expected returns/covariance, construction gate status. |
| Forecasting model | Rolling-origin validation, horizon-specific error, naive/seasonal baseline, regime robustness. |
| Execution process | Fill slippage, implementation shortfall, participation, spread capture, rejected/partial fills, delay, venue and broker effects. |
| Production strategy | Go-live checklist, live-vs-paper drift, signal health, risk breaches, execution exceptions, data freshness, rollback plan. |

## Common Quant Anti-Patterns

| Anti-pattern | Correction |
| --- | --- |
| Using today's index constituents for historical backtests. | Use point-in-time universe membership and delisted names. |
| Computing factors with future accounting data. | Lag data by realistic report/availability dates. |
| Ranking signals using full-sample standardization. | Standardize within each timestamp using only available data. |
| Selecting factors after looking at all backtests. | Use train/validation/test periods and multiple-testing controls. |
| Ignoring transaction costs and turnover. | Report gross and net performance with realistic cost assumptions. |
| Reporting Sharpe without drawdown, skew, tail risk, and factor exposure. | Include path and exposure diagnostics. |
| Optimizing on noisy expected returns without constraints. | Use shrinkage, robust constraints, or risk-based allocation. |
| Treating PCA factors as economic factors by default. | Validate stability and interpret with exposures/loadings. |
| Treating alpha regression intercept as investable alpha. | Check costs, capacity, timing, benchmark, and residual risk. |

For deeper review coverage, read [quant-anti-patterns.md](quant-anti-patterns.md).

## Bundled Quant Scripts

| Script | Use when | Expected input shape | Main output |
| --- | --- | --- | --- |
| `scripts/returns_risk_report.py` | Need first-pass return/risk diagnostics for assets, strategies, or portfolios. | Wide return or price CSV. | Annualized return/volatility, Sharpe/Sortino, drawdown, VaR/ES, skew/kurtosis, correlations. |
| `scripts/factor_exposure_regression.py` | Need alpha/beta attribution against market/style/factor returns. | Time-series CSV with return column and factor return columns. | Alpha, betas, IID t-stats, R-squared, residual risk. |
| `scripts/point_in_time_audit.py` | Need to check whether factor, universe, revision, and execution timestamps were observable before signal tests or backtests. | Long date-entity CSV with as-of date, entity, and optional availability, data, period-end, signal, universe, revision, vendor, rebalance, and execution timestamps. | Pass/review/fail audit, blockers, warnings, issue counts, duplicate as-of keys, and row-level timing findings. |
| `scripts/execution_timing_audit.py` | Need to check whether signal, rebalance, execution, and forward-return windows are executable before IC, regressions, or backtests. | Long date-entity or portfolio-level CSV with signal/decision date and optional rebalance, execution, return-start, return-end, calendar, and venue columns. | Pass/review/fail audit, non-executable return windows, same-day timing evidence gaps, stale signals, weekend dates, duplicate signal keys, blockers, and warnings. |
| `scripts/tradability_audit.py` | Need to check whether assets used in factor tests, backtests, or portfolio construction were tradable at simulated trade time. | Long date-entity CSV with trade side/size, execution price, volume/ADV, tradable/halted/suspended flags, limit status, shortable and borrow fields when available. | Pass/review/fail audit, halted/suspended rows, zero volume, high participation, limit-lock conflicts, stale prices, short/borrow blockers, and evidence gaps. |
| `scripts/factor_ic_report.py` | Need cross-sectional predictive signal diagnostics. | Long CSV with date, asset, factor value, and forward return. | Per-date IC/rank IC plus mean, t-stat, positive rate. |
| `scripts/factor_decay_report.py` | Need horizon decay of a signal. | Long CSV with date, factor value, and multiple forward-return columns. | IC/rank-IC summary by horizon. |
| `scripts/factor_quantile_report.py` | Need factor-sorted portfolio diagnostics. | Long CSV with date, factor value, forward return, optional weights. | Quantile mean returns and top-minus-bottom spread. |
| `scripts/factor_turnover_report.py` | Need signal stability and selected-name turnover. | Long CSV with date, asset, and factor value. | Weight turnover, membership overlap, rank autocorrelation. |
| `scripts/signal_overlap_report.py` | Need redundancy or crowding diagnostics across many alpha signals. | Long CSV with date, asset, and multiple signal columns. | Pairwise Pearson/rank correlation, top-name overlap, Jaccard overlap, redundant signal pairs. |
| `scripts/incremental_alpha_report.py` | Need to test whether a candidate alpha adds value beyond existing signals or exposures. | Long CSV with date, asset, candidate signal, forward return, and base signal/exposure columns. | Raw/residual IC, raw/residual rank IC, candidate coefficient, delta R-squared, candidate spanned-by-base R-squared. |
| `scripts/portfolio_backtest.py` | Need simple portfolio return diagnostics from weights. | Long CSV with date, asset, weight, and realized return. | Gross/net return metrics, drawdown, turnover, gross exposure. |
| `scripts/transaction_cost_report.py` | Need implementation-cost drag estimates. | Long CSV with date, asset, weight, optional returns/spread/ADV. | Turnover, trade cost, borrow cost, net-vs-gross performance, ADV participation. |
| `scripts/covariance_report.py` | Need covariance/correlation inputs for risk review or optimizer sanity checks. | Wide return CSV. | Volatility, covariance, annualized covariance, correlation, pairwise sample counts. |
| `scripts/ewma_volatility.py` | Need adaptive volatility estimates for assets, strategies, or risk monitoring. | Wide return CSV. | Latest and average EWMA volatility, optional full volatility path. |
| `scripts/rolling_beta.py` | Need time-varying market or benchmark exposure diagnostics. | Time-series CSV with return and benchmark return columns. | Rolling alpha, beta, R-squared, residual volatility. |
| `scripts/pairs_spread_report.py` | Need first-pass pair trading spread diagnostics. | Time-series CSV with two price columns. | Static hedge ratio, spread z-score, threshold crossings, autocorrelation, half-life. |
| `scripts/event_study_report.py` | Need abnormal returns around discrete events. | Long CSV with date, asset, return, event flag, optional benchmark return. | Event-window AR/CAR, average AR by offset, CAR t-stat/positive rate. |
| `scripts/cross_sectional_return_regression.py` | Need a quick single-date or pooled characteristic-return regression. | Long asset-level CSV with return and feature/exposure columns. | Coefficients, IID t-stats, R-squared, residual risk. |
| `scripts/fama_macbeth_regression.py` | Need average cross-sectional premia across many dates. | Long CSV with date, return, and characteristic/exposure columns. | Date-level coefficients, mean premia, time-series t-stats. |
| `scripts/long_short_backtest.py` | Need a simple investable-style signal portfolio after IC/quantile checks. | Long CSV with date, asset, signal, and forward return. | Gross/net performance, turnover, drawdown, selected-name counts. |
| `scripts/portfolio_exposure_report.py` | Need holdings-level risk exposure aggregation. | Long CSV with date, asset, weight, numeric exposures, optional categories. | Net/gross exposure, style beta, sector/country/category weights, concentration. |
| `scripts/pca_risk_model.py` | Need statistical factor diagnostics from a return panel. | Wide return CSV. | Eigenvalues, explained variance, component loadings, matrix diagnostics. |
| `scripts/factor_neutralization.py` | Need factor values purged of sector/style/beta/size exposures before IC or sorting. | Long CSV with date, asset, signal, numeric exposures, optional categorical exposures. | Neutralized signal residuals, z-scores, by-date R-squared, output CSV. |
| `scripts/newey_west_regression.py` | Need time-series regression t-stats robust to residual autocorrelation. | Time-series CSV with dependent return and factor/benchmark columns. | Coefficients, IID SE/t-stats, Newey-West SE/t-stats, R-squared. |
| `scripts/multiple_testing_report.py` | Need false-positive control after testing many factors/models. | CSV with test id and p-value columns. | Raw, Bonferroni, Holm, and Benjamini-Hochberg adjusted discoveries. |
| `scripts/quant_experiment_audit.py` | Need to audit whether the full alpha/strategy experiment trail is recorded before promotion. | CSV registry with experiment id, family, status, selected/predeclared/final-test flags, validation/test metrics, p-values, and data/code versions. | Blockers, warnings, family summaries, missing failed trials, unregistered experiments, final-test gaps, metric degradation, and FDR trail. |
| `scripts/capacity_impact_report.py` | Need capacity, ADV participation, and market-impact sensitivity. | Long CSV with date, asset, target weight, ADV, optional spread. | Turnover, participation, cost bps, binding NAV capacity. |
| `scripts/portfolio_constraint_check.py` | Need pretrade or backtest portfolio rule checks. | Long CSV with date, asset, weight, optional categories. | Gross/net/single-name/category/turnover violations by date. |
| `scripts/bootstrap_reality_check.py` | Need data-snooping review after trying many strategy variants. | Wide CSV with strategy return columns. | Best observed strategy, centered block-bootstrap p-values, bootstrap null summaries. |
| `scripts/alpha_research_gate_report.py` | Need a research-stage pass/review/fail decision from completed alpha diagnostics. | JSON outputs from bundled experiment-audit, IC, incremental-alpha, overlap, turnover, cost/capacity, multiple-testing, or backtest scripts. | Gate decision, blockers, warnings, missing required diagnostics, key metrics, per-report findings. |
| `scripts/walk_forward_stability.py` | Need parameter-selection stability across rolling windows. | Long CSV with date, parameter id, and validation metric. | Fold selections, out-of-sample metric, oracle regret, selection concentration. |
| `scripts/optimizer_sensitivity_report.py` | Need mean-variance optimizer fragility diagnostics. | Expected-return CSV plus covariance long-table CSV. | Base weights, simulated weight dispersion, sign flips, concentration sensitivity. |
| `scripts/portfolio_construction_gate_report.py` | Need to decide whether a candidate portfolio can move from research to paper trading or trading review. | JSON outputs from bundled portfolio backtest, constraint, exposure, risk-contribution, optimizer-sensitivity, cost, or capacity scripts. | Gate decision, blockers, warnings, missing required diagnostics, key metrics, per-report findings. |
| `scripts/performance_attribution_report.py` | Need return contribution by asset or group. | Long CSV with date, asset, weight, return, optional groups. | Portfolio return summary, asset contribution, sector/country/group contribution. |
| `scripts/risk_contribution_report.py` | Need portfolio risk contribution or risk-budget review. | Weights CSV plus covariance long-table CSV. | Portfolio volatility, marginal/component risk contribution, percent risk by asset. |
| `scripts/regime_robustness_report.py` | Need to know whether strategy returns depend on market regimes. | Time-series CSV with date, strategy return, regime label, optional benchmark return. | Per-regime return/risk metrics, regime shares, transition counts, worst regimes. |
| `scripts/risk_forecast_calibration.py` | Need to validate volatility or VaR-style risk forecasts. | Time-series CSV with date, realized return, and forecast volatility. | Realized/forecast RMS ratio, standardized-return diagnostics, VaR breach and Kupiec checks. |
| `scripts/model_risk_register_report.py` | Need to audit model-risk governance evidence before promotion, go-live, scaling, or periodic review. | Model/strategy register CSV with model id, status, risk tier, owner, validator, validation/approval status, review dates, monitoring, rollback, kill switch, versions, evidence, issues, and waivers. | Register decision, model counts, blockers, warnings, stale review dates, missing owners/validators/approvals/controls/version evidence, and top findings. |
| `scripts/execution_slippage_report.py` | Need realized fill-quality and implementation-shortfall diagnostics. | Order/fill CSV with date, asset, side, quantity, decision price, fill price, optional ADV/spread. | Side-aware slippage bps, cost dollars, participation summaries, asset/date breakdowns. |
| `scripts/live_vs_paper_report.py` | Need to compare live strategy performance with paper or backtest expectations. | Time-series CSV with date, live return, paper return, optional benchmark return. | Return summaries, live-paper gap, tracking error, correlation, underperformance streaks. |
| `scripts/signal_health_monitor.py` | Need live factor or alpha-signal health monitoring. | Long CSV with date, asset, signal value, and forward return. | IC/rank IC, top-bottom spread, coverage, turnover, rank stability, alerts. |
| `scripts/go_live_gate_report.py` | Need go-live readiness or production gate status. | Checklist CSV with category, check, status, severity, optional owner/evidence. | Gate decision, blockers, warnings, evidence gaps, category status counts. |
| `scripts/order_exception_report.py` | Need production order exception and fill-rate monitoring. | Order/fill CSV with date, asset, status, order quantity, filled quantity, optional reason/venue/strategy. | Exception rates, aggregate fill rate, rejected/partial/open orders, asset/date/status breakdowns. |
| `scripts/data_freshness_report.py` | Need dataset freshness and upstream health checks before signal generation. | Dataset monitoring CSV with dataset, latest timestamp, optional max age, row count, missing count, status. | Fresh/problem counts, stale datasets, missing-rate issues, upstream status issues. |
| `scripts/limit_breach_report.py` | Need risk, portfolio, or operations limit breach monitoring. | Metric CSV with date, metric, value, limit, optional direction/severity/owner/strategy. | Gate decision, breach/blocker counts, metric summaries, consecutive breaches, severity breakdowns. |
| `scripts/strategy_action_decision.py` | Need to turn monitoring metrics into capital/trading action recommendations. | CSV with metric, value, threshold, action, optional direction/category/reason/owner. | Recommended action, triggered rules, action/category counts, strongest triggered rule. |
| `scripts/quant_checklist_template.py` | Need a starter checklist for go-live, monitoring, or retirement review. | CLI template selection; no input file required. | CSV, JSON, or Markdown checklist with category, check, severity, status, owner, evidence, notes. |
| `scripts/quant_report_aggregator.py` | Need to combine multiple bundled JSON diagnostics into one review report. | One or more JSON files produced by bundled quant scripts. | Overall decision, decision counts, key metrics, top findings, per-report summary. |
| `scripts/quant_review_pack.py` | Need a committee-style review pack from multiple quant diagnostics and gates. | JSON outputs from bundled research, portfolio, risk, trading, data, operations, and gate scripts. | Decision stack, role review, top findings, evidence gaps, and next actions. |

Use these scripts as diagnostics and scaffolding. They do not replace a production backtester with corporate-action handling, order simulation, fills, borrow availability, risk constraints, or event-driven execution.

## Implementation Notes

| Task | Python tools | Notes |
| --- | --- | --- |
| Factor exposure regression | `statsmodels.OLS`, bundled `scripts/factor_exposure_regression.py` | Use HAC/Newey-West in full research workflows when autocorrelation exists. |
| Point-in-time data audit | bundled `scripts/point_in_time_audit.py`, vendor vintage tables, filing/release calendars | Run before IC, sorted portfolios, regressions, or backtests; availability, universe, revision, and execution timestamps must be no later than the decision timestamp. |
| Execution timing audit | bundled `scripts/execution_timing_audit.py`, trading calendars, signal and return-window timestamp tables | Run before IC, sorted portfolios, regressions, portfolio backtests, or construction gates; forward-return windows should start after executable trade time. |
| Tradability audit | bundled `scripts/tradability_audit.py`, exchange market-state feeds, borrow/shortability tables, price-limit and halt data | Run before IC, sorted portfolios, regressions, portfolio backtests, or construction gates; simulated trades should exclude or flag halted, suspended, limit-locked, zero-volume, non-borrowable, or stale-price rows. |
| Factor IC / rank IC | bundled `scripts/factor_ic_report.py`, pandas groupby/corr | Verify point-in-time alignment and use robust inference for serially dependent IC. |
| Factor quantile portfolios | bundled `scripts/factor_quantile_report.py`, pandas groupby/qcut | Add costs, neutralization, benchmark exposure, and capacity before claiming alpha. |
| Factor decay | bundled `scripts/factor_decay_report.py` | Each horizon must be computed without overlapping-window leakage or timing mistakes. |
| Factor turnover | bundled `scripts/factor_turnover_report.py` | Pair with cost estimates and liquidity/capacity checks. |
| Signal overlap / redundancy | bundled `scripts/signal_overlap_report.py`, factor library correlation/overlap dashboards | Use before allocating capital across many alpha variants; high overlap reduces independent breadth. |
| Incremental alpha diagnostics | bundled `scripts/incremental_alpha_report.py`, cross-sectional OLS, partial-correlation/residual IC dashboards | Use before adding a candidate signal to a live alpha library; define the base signal/exposure set before looking at results. |
| Factor neutralization | bundled `scripts/factor_neutralization.py`, cross-sectional OLS, pandas/statsmodels | Neutralization must be within-date and point-in-time; compare before/after diagnostics. |
| Cross-sectional return regression | bundled `scripts/cross_sectional_return_regression.py`, `statsmodels.OLS` | Use for quick single-date diagnostics; repeated cross-sections need Fama-MacBeth or panel inference. |
| Fama-MacBeth regression | bundled `scripts/fama_macbeth_regression.py`, `linearmodels`, `statsmodels`, R `fixest` | Correct inference often needs HAC or clustered errors, especially with overlapping returns. |
| Signal long/short portfolio | bundled `scripts/long_short_backtest.py`, vectorbt/backtrader/Zipline | Use after signal timing is validated; add costs, exposure constraints, borrow, and capacity. |
| Newey-West/HAC inference | bundled `scripts/newey_west_regression.py`, `statsmodels` HAC covariance, R `sandwich` | Select lags based on frequency and overlapping horizon; HAC does not fix misspecification or leakage. |
| Multiple testing / FDR | bundled `scripts/multiple_testing_report.py`, `statsmodels.stats.multitest`, R `p.adjust` | Define the tested family before looking at results; track unpublished failed trials. |
| Experiment registry audit | bundled `scripts/quant_experiment_audit.py`, research registry or experiment-tracking tables | Run before FDR/reality checks and alpha gates; missing failed trials or selected variants without final tests make the evidence base incomplete. |
| Bootstrap reality check | bundled `scripts/bootstrap_reality_check.py`, block bootstrap, White/SPA style tests | Use after broad strategy search; include all tried variants, not only surviving backtests. |
| Alpha research gate | bundled `scripts/alpha_research_gate_report.py`, internal research checklist/gate systems | Use after source diagnostics have been generated; this is a research promotion gate, not production approval. |
| Walk-forward stability | bundled `scripts/walk_forward_stability.py`, rolling validation workflow | Unstable parameter selection or high regret means the tuning rule is fragile. |
| Optimizer sensitivity | bundled `scripts/optimizer_sensitivity_report.py`, PyPortfolioOpt sensitivity runs | Optimized weights should be stress-tested against expected-return/covariance perturbations. |
| Portfolio construction gate | bundled `scripts/portfolio_construction_gate_report.py`, portfolio review/checklist systems | Use after signal research passes; this checks construction admissibility before paper trading, not production go-live readiness. |
| Rolling betas | `statsmodels.regression.rolling.RollingOLS` | Window length controls stability vs responsiveness. |
| Rolling beta diagnostics | bundled `scripts/rolling_beta.py` | Use for first-pass exposure stability before a fuller HAC/rolling-OLS implementation. |
| Covariance/correlation diagnostics | bundled `scripts/covariance_report.py`, `pandas.DataFrame.cov`, `numpy.cov` | Pairwise missingness and sample length affect the matrix. Use shrinkage before optimization when `n` is small relative to assets. |
| EWMA volatility | bundled `scripts/ewma_volatility.py`, RiskMetrics-style EWMA, `arch` | Decay controls responsiveness and noise; validate against realized risk. |
| PCA/statistical factors | bundled `scripts/pca_risk_model.py`, `sklearn.decomposition.PCA`, `statsmodels.multivariate.PCA` | Standardize returns/exposures as appropriate; components are not automatically economic factors. |
| Factor analysis | `statsmodels.multivariate.factor.Factor` | Factor count/rotation require validation. |
| Volatility models | `arch.arch_model` | GARCH/EGARCH/GJR-GARCH with distribution choices. |
| Portfolio optimization | PyPortfolioOpt `EfficientFrontier`, `BlackLittermanModel`, risk models | Expected returns and covariance estimation dominate results. |
| Panel asset pricing | `linearmodels`, `statsmodels`, R `fixest`/`plm` | Clustered/HAC errors are usually required. |
| Backtest metrics | bundled `scripts/returns_risk_report.py` | Use as a first-pass diagnostic, not a full trading simulator. |
| Portfolio weight backtest | bundled `scripts/portfolio_backtest.py` | Weights are beginning-of-period weights; document execution assumptions. |
| Portfolio exposure aggregation | bundled `scripts/portfolio_exposure_report.py`, risk model exposure reports | Check numeric style exposures and categorical sector/country/currency concentrations. |
| Performance attribution | bundled `scripts/performance_attribution_report.py`, Brinson-style/custom attribution | Attribute return by asset/group and reconcile with total portfolio return before claims. |
| Risk contribution | bundled `scripts/risk_contribution_report.py`, risk parity/risk budget tools | Monitor component risk contribution and negative hedge contributions under the chosen covariance. |
| Transaction costs | bundled `scripts/transaction_cost_report.py`, Zipline/vectorbt/backtrader for fuller simulation | Include spread, slippage, commissions, borrow, financing, market impact, and ADV participation where possible. |
| Capacity and market impact | bundled `scripts/capacity_impact_report.py`, custom execution model, broker TCA | Calibrate impact assumptions to asset class, urgency, spread, ADV, and venue microstructure. |
| Execution slippage | bundled `scripts/execution_slippage_report.py`, broker TCA, order/fill analytics | Use decision-time prices and side-aware bps; separate realized fills from simulated impact assumptions. |
| Risk forecast calibration | bundled `scripts/risk_forecast_calibration.py`, VaR backtesting, volatility forecast evaluation | Compare realized returns with forecast scale and breach rates before trusting risk budgets. |
| Model risk register audit | bundled `scripts/model_risk_register_report.py`, model inventory and governance register | Use before go-live, scaling, and periodic model review; this audits governance evidence and does not replace alpha, portfolio, execution, or go-live diagnostics. |
| Regime robustness | bundled `scripts/regime_robustness_report.py`, custom state labels, Markov/regime models | Regime labels must be point-in-time; avoid hindsight stories based on realized outcomes. |
| Live-vs-paper monitoring | bundled `scripts/live_vs_paper_report.py`, custom reconciliation reports | Same timestamps, return definitions, timing conventions, and cost assumptions are required. |
| Signal health monitoring | bundled `scripts/signal_health_monitor.py`, IC dashboards, factor monitoring jobs | Monitor the signal separately from portfolio PnL so execution or sizing problems do not hide signal decay. |
| Go-live gate review | bundled `scripts/go_live_gate_report.py`, checklist/status workflows | Treat missing evidence and high-severity unresolved checks as blockers before capital deployment. |
| Order exception monitoring | bundled `scripts/order_exception_report.py`, OMS/EMS order logs | Separate order availability and fill completeness from fill price slippage. |
| Data freshness monitoring | bundled `scripts/data_freshness_report.py`, ETL/data quality jobs | Run before signal generation; stale or incomplete data should freeze trading decisions. |
| Limit breach monitoring | bundled `scripts/limit_breach_report.py`, risk/ops limit dashboards | Critical/high unresolved breaches should block go-live, scaling, or new orders. |
| Strategy action decision | bundled `scripts/strategy_action_decision.py`, policy/rules engines | Map predeclared thresholds to maintain, review, reduce, pause, or retire actions. |
| Checklist template generation | bundled `scripts/quant_checklist_template.py`, internal checklist systems | Generate templates, then fill evidence and pass completed gate files into `go_live_gate_report.py`. |
| Diagnostics aggregation | bundled `scripts/quant_report_aggregator.py`, custom report assembly | Aggregate JSON reports for review triage; source diagnostics remain authoritative for final decisions. |
| Committee review pack | bundled `scripts/quant_review_pack.py`, report assembly workflow | Use after diagnostics and gates exist; the pack is a decision aid and evidence map, while source diagnostics remain authoritative. |
| Portfolio constraints | bundled `scripts/portfolio_constraint_check.py`, optimizer pretrade checks | Check gross/net exposure, single-name, sector/category, and turnover limits before accepting a backtest. |
| Pair spread diagnostics | bundled `scripts/pairs_spread_report.py`, `statsmodels.tsa.stattools.coint`, `VECM` | Static spread diagnostics are not proof of cointegration; estimate hedge ratio out of sample. |
| Event studies | bundled `scripts/event_study_report.py`, statsmodels/custom workflow | Check event leakage, overlapping events, confounding news, clustering, and multiple testing. |
