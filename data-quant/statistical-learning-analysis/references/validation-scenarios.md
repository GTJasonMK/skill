# Validation Scenarios

Use these scenarios to forward-test this skill after major edits. A good answer should select the right family, state assumptions, avoid leakage, recommend validation, and refuse overclaiming.

## Contents

- General statistical learning: scenarios 1-10 cover high-dimensional prediction, causal policy impact, rare classification, survival, forecasting, segmentation, panel data, recommendation, spatial modeling, and graph link prediction.
- Quant research and portfolio validation: scenarios 11-32 cover equity factors, backtests, exposure attribution, optimizers, event studies, pair trading, risk monitoring, asset pricing, constraints, multiple testing, capacity, reality checks, walk-forward stability, attribution, risk budgets, regimes, and risk calibration.
- Quant production monitoring: scenarios 33-52 cover execution slippage, live-vs-paper drift, signal health, go-live gates, order exceptions, data freshness, limits, strategy actions, checklist generation, review packs, experiment/model-risk audits, point-in-time checks, execution timing, and tradability.

## 1. High-dimensional disease prediction

Prompt: "I have 120 patients, 20,000 gene-expression variables, and a binary disease label. Which methods should I use?"

Expected checks:

- Flag `p >> n`, feature selection leakage, batch effects, and selection instability.
- Recommend penalized logistic, linear SVM, PLS/PCA inside CV, nested CV.
- Avoid deep learning as default.
- Use ROC-AUC plus PR-AUC if imbalance exists.

## 2. Policy impact

Prompt: "A city introduced a new subsidy in 2023. I have monthly sales for treated and untreated cities from 2020-2025. Did it work?"

Expected checks:

- Treat as causal, not ordinary forecasting.
- Ask about treatment timing, control comparability, spillovers.
- Recommend DiD/event study or interrupted time series variants.
- Check pre-trends, placebo, autocorrelation, clustered SE.

## 3. Rare fraud classification

Prompt: "Fraud is 0.7% of my transactions. I want a classifier."

Expected checks:

- Reject accuracy-only evaluation.
- Recommend class-weighted logistic/boosting, resampling inside folds, PR-AUC, recall at precision, threshold/workload analysis.
- Warn about temporal/user leakage.

## 4. Churn time with censoring

Prompt: "Some customers have not churned yet, but I want to model time to churn."

Expected checks:

- Route to survival analysis.
- Recommend Kaplan-Meier baseline, Cox/AFT/time-varying models.
- Discuss censoring, origin time, time-varying covariates, C-index/Brier.

## 5. Sales forecast

Prompt: "I have five years of monthly sales and need the next six months."

Expected checks:

- Use forecasting lane and rolling-origin validation.
- Include naive/seasonal naive baseline.
- Consider ETS, SARIMA/SARIMAX, state-space, lag-feature ML.
- Evaluate by horizon and check future availability of regressors.

## 6. Customer segmentation

Prompt: "I want to segment customers based on behavior, but I have no labels."

Expected checks:

- Route to unsupervised learning.
- Ask about actionability and feature scaling.
- Recommend PCA visualization, K-means/GMM/hierarchical/HDBSCAN as appropriate.
- Emphasize stability and domain review.

## 7. Panel data with firms

Prompt: "I have firm-year data and want to estimate whether ESG score affects profit."

Expected checks:

- Discuss panel structure, fixed effects, random effects, clustered SE.
- Treat causal language carefully; ask about confounders and timing.
- Consider DiD/IV if intervention/exogeneity exists.

## 8. Recommender system

Prompt: "I need to recommend products to users using purchase history."

Expected checks:

- Route to recommendation, not multiclass classification.
- Include popularity baseline, collaborative filtering/matrix factorization/two-stage ranking.
- Use user/time-aware validation and NDCG/recall@k.
- Warn about cold start, exposure bias, offline-online gap.

## 9. Spatial air quality

Prompt: "I have sensor readings across a city and want to predict pollution at unsampled locations."

Expected checks:

- Route to spatial modeling.
- Discuss spatial autocorrelation, kriging/GP/spatial regression, spatial blocked CV.
- Warn against random splits by nearby points.

## 10. Graph link prediction

Prompt: "I have a social graph and want to predict future connections."

Expected checks:

- Route to graph/link prediction.
- Split by future edges/time.
- Warn against computing embeddings using the full graph if deployment is inductive.
- Consider graph features, embeddings, GNNs if data scale supports them.

## 11. Equity factor signal

Prompt: "I have daily stock factor values and next-20-day returns. How do I know whether this factor has alpha?"

Expected checks:

- Route to quant finance / cross-sectional factor research.
- Require point-in-time universe, survivorship control, realistic signal lag, and executable forward-return timing.
- Recommend IC/rank IC, IC decay, quantile returns, high-minus-low spread, turnover, capacity, costs, and exposure checks.
- Mention `factor_ic_report.py`, `factor_decay_report.py`, `factor_quantile_report.py`, and `factor_turnover_report.py` if CSV columns are available.
- Mention `long_short_backtest.py` only after confirming signal timing, universe, costs, and execution assumptions.
- Avoid claiming alpha from high IC alone.

## 12. Strategy backtest review

Prompt: "My long-short equity strategy has Sharpe 2.1 in a backtest. Is it good enough to trade?"

Expected checks:

- Ask for universe construction, point-in-time data, delistings, rebalance timing, execution price, leverage, and shorting constraints.
- Require net-of-cost results, turnover, drawdown, tail risk, capacity, borrow, benchmark, and factor exposures.
- Recommend `portfolio_backtest.py`, `transaction_cost_report.py`, `returns_risk_report.py`, and `factor_exposure_regression.py` when returns/weights are provided.
- Warn about data snooping, parameter tuning on the final test period, and annualizing short samples.

## 13. Factor exposure attribution

Prompt: "My crypto strategy beat Bitcoin last year. Can I call the excess return alpha?"

Expected checks:

- Reframe as benchmark/factor exposure attribution before alpha claims.
- Check return frequency, risk-free/cash treatment, leverage, trading costs, beta, momentum/market factors, and sample length.
- Recommend factor exposure regression, `rolling_beta.py`, residual risk, drawdowns, and robustness by subperiod.
- Warn that regression intercept is not automatically investable alpha.

## 14. Portfolio optimizer

Prompt: "I have expected returns and a covariance matrix for 200 stocks. Should I run mean-variance optimization?"

Expected checks:

- Discuss noisy expected returns, covariance estimation error, constraints, turnover, liquidity, and sensitivity.
- Recommend `covariance_report.py` and `pca_risk_model.py` for first-pass covariance/statistical-factor diagnostics, then shrinkage covariance, robust constraints, risk budgets, turnover limits, and out-of-sample realized-risk validation.
- Avoid unconstrained optimizer output as a direct trading portfolio.

## 15. Event study

Prompt: "I want to measure whether earnings announcements create abnormal returns."

Expected checks:

- Route to event study, not generic classification.
- Define event timestamp, estimation window, event window, benchmark/factor expected-return model, overlapping events, and leakage.
- Report abnormal returns/CAR with uncertainty, clustering, multiple-testing status, and confounding news checks.
- Mention `event_study_report.py` when long-form event/return data are available.
- Use quant report templates when a formal deliverable is requested.

## 16. Pair trading spread

Prompt: "I found two cointegrated-looking stocks and want to trade the spread."

Expected checks:

- Route to pair trading / cointegration, not generic correlation.
- Require formation and trading windows, hedge-ratio estimation without future data, stationarity/cointegration checks, regime-break monitoring, costs, borrow, and short-sale constraints.
- Mention `pairs_spread_report.py` for first-pass spread, z-score, crossing, autocorrelation, and half-life diagnostics.
- Warn that static spread diagnostics are not proof of tradable cointegration.

## 17. Volatility and risk monitoring

Prompt: "My strategy volatility changes a lot. How should I monitor risk?"

Expected checks:

- Separate mean-return forecasting from volatility/risk forecasting.
- Recommend realized volatility, EWMA volatility, rolling drawdown, VaR/ES, exposure, and stress-period checks.
- Mention `ewma_volatility.py`, `returns_risk_report.py`, and `covariance_report.py` when return columns are available.
- Warn that short recent windows can be noisy and regime-dependent.

## 18. Fama-MacBeth asset pricing

Prompt: "I have monthly stock returns and firm characteristics. How do I estimate which characteristics earn a premium?"

Expected checks:

- Route to asset pricing / repeated cross-sectional regression.
- Require point-in-time characteristics, return horizon alignment, universe rules, delistings, and treatment of overlapping returns.
- Recommend `fama_macbeth_regression.py` for first-pass date-by-date premia and `cross_sectional_return_regression.py` for a single-date diagnostic.
- Warn that simple time-series t-stats may be insufficient; mention HAC/clustered inference for serious research.

## 19. Portfolio exposure review

Prompt: "I have portfolio weights and asset betas/sectors. How do I check whether my strategy is unintentionally loaded on risks?"

Expected checks:

- Route to portfolio risk/exposure attribution.
- Require holdings timing, benchmark, leverage, long/short treatment, numeric style exposures, and categorical exposures such as sector/country/currency.
- Recommend `portfolio_exposure_report.py`, `rolling_beta.py`, and `factor_exposure_regression.py` when holdings/returns are available.
- Warn that exposure definitions and point-in-time holdings matter.

## 20. Statistical PCA risk factors

Prompt: "Can I use PCA on stock returns to build a risk model?"

Expected checks:

- Explain PCA factors as statistical variance directions, not automatically economic factors.
- Discuss covariance vs correlation PCA, window length, standardization, eigenvalue stability, loadings, residual correlations, and rolling validation.
- Recommend `pca_risk_model.py` and `covariance_report.py` for first-pass diagnostics.
- Warn against using unstable components directly in an optimizer without constraints and realized-risk monitoring.

## 21. Neutralized factor claim

Prompt: "My factor works, but I need to prove it is not just sector, size, or beta exposure."

Expected checks:

- Route to quant factor research and exposure-neutral signal diagnostics.
- Require point-in-time sector/style/beta/size exposures, within-date neutralization, and before/after comparison.
- Recommend `factor_neutralization.py`, then rerun IC/quantile/long-short diagnostics on the neutralized signal.
- Warn that over-neutralization can remove intended economic signal.

## 22. Autocorrelated alpha t-stat

Prompt: "My strategy alpha regression has t-stat 3.0, but returns are autocorrelated."

Expected checks:

- Route to time-series factor exposure and robust inference.
- Recommend Newey-West/HAC or block bootstrap; discuss lag choice, overlapping returns, frequency, and residual diagnostics.
- Mention `newey_west_regression.py` when time-series return/factor columns are available.
- Warn that HAC standard errors do not fix leakage, benchmark mismatch, or omitted factors.

## 23. Many tested factors

Prompt: "I tested 400 alpha signals and 12 have p-values below 0.05. Which are real?"

Expected checks:

- Route to multiple testing and data-snooping control.
- Ask whether the tested family was predeclared and whether failed trials were tracked.
- Recommend train/validation/test split, false discovery control, Bonferroni/Holm/BH checks, and out-of-sample replication.
- Mention `multiple_testing_report.py` if p-values are available.

## 24. Capacity and market impact

Prompt: "The backtest looks good at $5M. Can this strategy run $200M?"

Expected checks:

- Route to capacity, liquidity, market impact, and execution review.
- Require ADV, spread, turnover, rebalance frequency, order timing, borrow, shorting, and participation assumptions.
- Recommend `capacity_impact_report.py`, `transaction_cost_report.py`, and turnover diagnostics.
- Warn that simple ADV participation is only a first-pass proxy and must be calibrated with execution data.

## 25. Portfolio constraint acceptance

Prompt: "Before I accept this backtest, how do I check whether weights violate risk constraints?"

Expected checks:

- Route to portfolio construction and pretrade/backtest constraint checking.
- Check gross/net exposure, single-name concentration, sector/country/category exposure, leverage, turnover, and shorting constraints.
- Recommend `portfolio_constraint_check.py` and `portfolio_exposure_report.py` for date-level diagnostics.
- Warn that constraints must be applied before performance evaluation, not only after selecting good backtests.

## 26. Data-snooping reality check

Prompt: "I tested many strategy variants and picked the best Sharpe. How do I know it is not luck?"

Expected checks:

- Route to data-snooping and multiple-strategy selection bias.
- Require the full set of tried strategy variants, not only the winners.
- Recommend train/validation/test discipline, block bootstrap, reality-check style tests, and out-of-sample replication.
- Mention `bootstrap_reality_check.py` and `multiple_testing_report.py` when returns or p-values are available.

## 27. Walk-forward parameter stability

Prompt: "My strategy only works for one lookback window. Is the parameter choice stable?"

Expected checks:

- Route to walk-forward validation and parameter stability review.
- Require date/parameter/metric results computed without future leakage.
- Recommend `walk_forward_stability.py` to inspect selected parameters, test regret, and selection concentration.
- Warn that unstable parameter selection is evidence of tuning fragility even when one backtest looks good.

## 28. Optimizer sensitivity

Prompt: "The optimizer gives extreme weights. How sensitive is it to small input changes?"

Expected checks:

- Route to portfolio optimization robustness, not just return maximization.
- Discuss expected-return noise, covariance noise, constraints, shrinkage, turnover, and concentration.
- Recommend `optimizer_sensitivity_report.py`, `portfolio_constraint_check.py`, and `risk_contribution_report.py` when inputs are available.
- Warn that unconstrained mean-variance weights are usually fragile.

## 29. Performance attribution

Prompt: "The strategy made money last quarter. Which assets or sectors contributed?"

Expected checks:

- Route to performance attribution and contribution reconciliation.
- Require beginning-period weights, asset returns, groups, benchmark, fees/costs, and timing convention.
- Recommend `performance_attribution_report.py`, `portfolio_exposure_report.py`, and factor exposure regression as needed.
- Warn not to confuse contribution attribution with causal alpha.

## 30. Risk budget review

Prompt: "I want each position to contribute similar risk, not just similar capital."

Expected checks:

- Route to risk contribution / risk-budget analysis.
- Require weights, covariance estimate, leverage convention, and out-of-sample risk monitoring.
- Recommend `risk_contribution_report.py`, `covariance_report.py`, and `pca_risk_model.py` when return/covariance inputs are available.
- Warn that risk budgets are only as reliable as the covariance estimate and can shift by regime.

## 31. Regime robustness

Prompt: "The strategy looks good overall, but does it only work in bull markets?"

Expected checks:

- Route to regime robustness and conditional performance review.
- Require point-in-time regime labels or a clear rule for constructing regimes without future information.
- Recommend `regime_robustness_report.py`, `returns_risk_report.py`, and factor exposure diagnostics when returns are available.
- Warn that hindsight regime labels can turn robustness analysis into narrative overfit.

## 32. Risk forecast calibration

Prompt: "Our daily VaR model says risk is controlled, but losses still surprise us. How should we check it?"

Expected checks:

- Route to risk model forecast calibration rather than only portfolio performance.
- Require realized returns, forecast volatility or VaR inputs, forecast timestamp, annualization convention, and confidence level.
- Recommend `risk_forecast_calibration.py`, realized/forecast volatility ratios, standardized returns, breach rates, and breach clustering checks.
- Warn that normal-VaR calibration is not enough to validate tail shape, correlation, liquidity, or stress scenarios.

## 33. Execution slippage review

Prompt: "The live strategy underperforms the paper backtest. Are fills and slippage the problem?"

Expected checks:

- Route to execution quality, implementation shortfall, and TCA review.
- Require side, quantity, decision price, fill price, order timestamp, fill timestamp, spread, ADV, venue/broker, partial fills, and rejected orders if available.
- Recommend `execution_slippage_report.py`, `transaction_cost_report.py`, and `capacity_impact_report.py` for realized and modeled cost comparison.
- Warn that paper slippage assumptions should be recalibrated from realized fills, not averaged across unrelated assets or regimes.

## 34. Live vs paper drift

Prompt: "The live strategy is behind the paper portfolio. How do we diagnose the drift?"

Expected checks:

- Route to production monitoring and live-vs-paper reconciliation.
- Require identical timestamps, return definitions, cost convention, rebalance timing, universe, data feed, and benchmark alignment.
- Recommend `live_vs_paper_report.py`, `execution_slippage_report.py`, attribution, and cost/capacity diagnostics.
- Warn that live drift should be decomposed before changing the signal or retuning the model.

## 35. Signal health decay

Prompt: "Our live PnL is noisy. How can we tell if the alpha signal itself is decaying?"

Expected checks:

- Route to signal health monitoring rather than only portfolio PnL review.
- Require live signal values, forward returns, universe coverage, timestamp alignment, and recent-vs-research baseline expectations.
- Recommend `signal_health_monitor.py`, IC/rank IC, top-bottom spread, coverage, turnover, and rank stability checks.
- Warn that execution, risk sizing, and costs can mask signal health, so monitor signal evidence separately.

## 36. Go-live gate

Prompt: "What should block this strategy from going live?"

Expected checks:

- Route to go-live readiness and production risk review.
- Require a checklist covering data, signal, portfolio, costs, capacity, execution, risk, operations, monitoring, rollback, owner, and evidence.
- Recommend `go_live_gate_report.py` when a checklist CSV exists.
- Warn that missing evidence for critical/high checks should block or conditionally block capital deployment.

## 37. Order exception monitoring

Prompt: "The slippage report looks fine, but some orders did not fill. How do we monitor that?"

Expected checks:

- Route to order availability, rejection, cancellation, open-order, and partial-fill monitoring.
- Require order status, ordered quantity, filled quantity, reason, venue/broker, asset, strategy, and timestamp where available.
- Recommend `order_exception_report.py` plus `execution_slippage_report.py` to separate fill completeness from fill price quality.
- Warn that analyzing only completed fills creates survivorship bias in execution quality.

## 38. Data freshness gate

Prompt: "How do we stop stale vendor data from generating today's trades?"

Expected checks:

- Route to data freshness and upstream data-quality monitoring before signal generation.
- Require dataset name, latest timestamp, max allowed age, row count, missing count/rate, upstream job status, and current time convention.
- Recommend `data_freshness_report.py` and missingness/reconciliation checks.
- Warn that fresh timestamps do not prove point-in-time correctness or corporate-action accuracy.

## 39. Risk and operations limit breaches

Prompt: "We have daily metrics and limits. Which breaches should block trading or scaling?"

Expected checks:

- Route to risk/operations limit monitoring and escalation.
- Require metric name, observed value, limit value, direction, severity, owner, strategy, date, and consecutive breach policy.
- Recommend `limit_breach_report.py`, `portfolio_constraint_check.py`, and go-live gate review.
- Warn that unresolved critical/high breaches should block go-live, scaling, or new order release until signed off.

## 40. Strategy action decision

Prompt: "Given these monitoring metrics, should we maintain, reduce, pause, or retire the strategy?"

Expected checks:

- Route to production action policy rather than ad hoc interpretation.
- Require predeclared thresholds, metric direction, mapped action, owner, and reason for each rule.
- Recommend `strategy_action_decision.py` when a metric-threshold-action CSV exists.
- Warn that action rules should be set before looking at live outcomes and final capital changes still need mandate/owner approval.

## 41. Checklist template generation

Prompt: "Can you give me a default checklist for launching and monitoring a quant strategy?"

Expected checks:

- Route to go-live, monitoring, or retirement checklist generation.
- Ask which template is needed if unclear: `go-live`, `monitoring`, or `retirement`.
- Recommend `quant_checklist_template.py` to generate CSV, JSON, or Markdown templates.
- Warn that generated templates are starting points; evidence, owners, thresholds, and stop conditions must be filled for the strategy mandate.

## 42. Aggregated strategy review

Prompt: "I ran several of these quant diagnostics. Can you combine them into one health report?"

Expected checks:

- Route to diagnostics aggregation and review triage.
- Require JSON outputs from the relevant bundled scripts; ask for missing diagnostics if a decision depends on them.
- Recommend `quant_report_aggregator.py` to combine decisions, key metrics, alerts, blockers, breaches, and top findings.
- Warn that the aggregated report is an index and summary; source diagnostics remain authoritative for final capital or trading decisions.

## 43. Multi-signal overlap and crowding

Prompt: "I have 20 alpha signals. How do I know whether they are actually different?"

Expected checks:

- Route to multi-signal redundancy, crowding, and independent breadth review.
- Require a date-asset panel with all candidate signal columns computed point-in-time on the same universe.
- Recommend `signal_overlap_report.py` to inspect pairwise Pearson/rank correlation, selected-name overlap, Jaccard overlap, and redundant signal pairs.
- Warn that low signal correlation alone is not enough; sector/style/liquidity exposure, cost, capacity, and common top holdings also matter.

## 44. Incremental alpha value

Prompt: "This new factor has positive IC. Does it add anything beyond our existing alpha stack?"

Expected checks:

- Route to incremental alpha, partial/residual IC, and predeclared base-signal review.
- Require date, asset, candidate signal, forward return, existing signal columns, and relevant sector/style/liquidity exposures computed point-in-time.
- Recommend `incremental_alpha_report.py` to compare raw IC with residual IC, candidate coefficient, delta R-squared, and candidate-explained-by-base R-squared.
- Warn that changing the base set after seeing results is another multiple-testing path; out-of-sample portfolio value, cost, capacity, and risk exposure still need review.

## 45. Alpha research gate

Prompt: "We have IC, overlap, incremental alpha, cost, and capacity reports. Can this factor move to paper trading?"

Expected checks:

- Route to research-stage alpha promotion gate, not production go-live approval.
- Require completed JSON diagnostics for point-in-time data audit, execution timing audit, tradability audit, experiment registry audit, IC/rank IC, incremental alpha, signal overlap, turnover, implementation costs or capacity, and multiple-testing or data-snooping review.
- Recommend `alpha_research_gate_report.py` to produce pass/review/fail, blockers, warnings, missing required diagnostics, and key metrics.
- Warn that gate thresholds and required diagnostics must be set before reviewing the candidate; a pass still requires separate portfolio construction, risk review, and production go-live checks.

## 46. Portfolio construction gate

Prompt: "The signal passed research review. Are these portfolio weights acceptable for paper trading?"

Expected checks:

- Route to portfolio construction gate, not signal research validation or production go-live approval.
- Require completed JSON diagnostics for execution timing audit, tradability audit, portfolio backtest, constraints, exposure, risk contribution, optimizer sensitivity when optimized weights are used, and implementation cost or capacity.
- Recommend `portfolio_construction_gate_report.py` to produce pass/review/fail, blockers, warnings, missing required diagnostics, and key metrics.
- Warn that passing construction checks does not prove live execution readiness; order handling, data freshness, limits, monitoring, owners, and rollback still need go-live review.

## 47. Committee review pack

Prompt: "Can you turn all these quant diagnostics into a review pack for PM, risk, trading, and operations?"

Expected checks:

- Route to role-aware review pack generation rather than recomputing source diagnostics.
- Require JSON outputs from relevant research, portfolio, risk, trading, data, operations, and gate scripts.
- Recommend `quant_review_pack.py` to produce a decision stack, role review, top findings, evidence gaps, and next actions.
- Warn that the review pack is a decision aid; source diagnostics and owner sign-off remain authoritative.

## 48. Quant experiment registry audit

Prompt: "We tested many alpha variants. Can you check whether the research log is complete enough before we run the gate?"

Expected checks:

- Route to experiment registry audit before multiple-testing, reality-check, or alpha-gate interpretation.
- Require a registry with experiment id, family, status, selected/promoted flag, predeclared flag, final-test flag or metric, validation/test metrics, p-values where available, and data/code versions.
- Recommend `quant_experiment_audit.py` to surface missing failed trials, unregistered experiments, selected variants without final tests, validation-to-test degradation, selected raw-significant but not FDR-significant variants, and version evidence gaps.
- Warn that FDR, reality checks, and alpha gates are not trustworthy when the tested family or failed trials are missing from the registry.

## 49. Model risk register audit

Prompt: "Before we scale this strategy, can you check whether the model-risk register is complete?"

Expected checks:

- Route to model-risk register governance audit, not alpha validation or ordinary go-live checklist status.
- Require model id, active/live status, risk tier, owner, independent validator, validation status, approval status, last review date, next review due date, monitoring plan, rollback plan, kill switch or manual override, data/code versions, evidence links, open issues, limitations, and waivers when applicable.
- Recommend `model_risk_register_report.py` to surface missing owners, invalid risk tiers, missing or failed validation, missing approvals, stale or overdue reviews, missing monitoring/rollback/kill-switch controls, version gaps, open issues, and unwaived limitations.
- Warn that a model-risk register pass does not prove alpha quality, portfolio admissibility, execution readiness, or go-live approval; it verifies governance evidence and accountability.

## 50. Point-in-time data audit

Prompt: "Can you check whether this factor dataset has look-ahead bias before IC/backtest?"

Expected checks:

- Route to point-in-time data and look-ahead leakage audit before factor IC, sorted portfolios, regressions, or backtests.
- Require date/entity rows with decision or as-of timestamp, and ask for availability/release/filing timestamp, source data date, period end, universe timestamp, revision/vendor timestamp, signal timestamp, rebalance timestamp, and execution timestamp when available.
- Recommend `point_in_time_audit.py` to surface availability after decision, source data after decision, signal before availability, future universe membership, later revisions or vendor vintages, invalid timestamps, duplicate entity/as-of rows, and missing availability evidence.
- Warn that fresh current data is not proof of point-in-time correctness; vendor vintage evidence, survivorship controls, corporate-action handling, and downstream cost/risk diagnostics still matter.

## 51. Execution timing and forward-return window audit

Prompt: "Can you check whether my factor/backtest uses same-close execution or a forward-return window that starts too early?"

Expected checks:

- Route to execution timing audit before IC, sorted-portfolio, regression, or backtest interpretation.
- Require signal or decision date, asset/entity, rebalance date, execution date, return-start date, return-end date, and signal/execution/return-start prices when available.
- Recommend `execution_timing_audit.py` to surface same-day signal/execution evidence gaps, same-close price use, rebalance after execution, return windows starting before signal or execution, nonpositive horizons, stale signals, weekend dates, and duplicate entity-signal keys.
- Warn that point-in-time source data is necessary but not sufficient; a backtest can still be invalid if the simulated execution time or forward-return window is not tradable.

## 52. Tradability and market-state audit

Prompt: "Can you check whether my backtest trades assets that were halted, zero-volume, limit-locked, or impossible to short?"

Expected checks:

- Route to tradability audit before IC, sorted-portfolio, regression, portfolio backtest, or construction-gate interpretation.
- Require date, asset/entity, side or trade size, execution price, volume or dollar volume, tradable/halted/suspended flags, limit-up/limit-down or limit status, shortable flag, borrow availability, and borrow rate when available.
- Recommend `tradability_audit.py` to surface non-tradable flags, halted or suspended rows, missing or nonpositive execution prices, zero/tiny volume, high participation, buy-at-limit-up, sell-at-limit-down, stale prices, non-shortable rows, unavailable borrow, high borrow rate, and missing market-state evidence gaps.
- Warn that point-in-time data and executable timing are necessary but not sufficient; a strategy can still be invalid if the simulated trade could not be filled or borrowed in the market state being tested.
