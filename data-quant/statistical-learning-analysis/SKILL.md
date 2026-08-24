---
name: statistical-learning-analysis
description: "End-to-end statistical learning and data analysis guidance for problem triage, dataset profiling, method selection, method principles, implementation mapping, validation, diagnostics, anti-pattern review, and reporting. Use when Codex needs to choose, compare, explain, implement, or review statistical learning methods for regression, classification, clustering, dimensionality reduction, anomaly detection, time series, survival analysis, causal inference, Bayesian modeling, panel/econometric analysis, quantitative finance/factor analysis, recommendation/ranking, spatial/graph data, preprocessing, evaluation, or when the user asks which method fits a scenario and why."
---

# Statistical Learning Analysis

## Overview

Use this skill to turn a statistical learning question into a defensible analysis plan. Always connect method choice to the dataset shape, target variable, inferential goal, validation design, assumptions, and failure modes.

This skill is a broad method-selection map, not an exhaustive encyclopedia. For specialized areas, identify the method family here, then consult field-specific references before giving implementation-level advice.

## Dependencies

- **Core:** install the root bundle from `../pyproject.toml` with `pip install -e ..`; it provides pandas, numpy, scipy, Pydantic, PyYAML, and the shared `quantctl` contracts.
- **Optional ML:** install the root `ml` extra for scikit-learn and joblib: `pip install -e '..[ml]'`. The legacy requirements files remain compatibility views of the root dependency groups.
- **Development validation:** install `pip install -e '..[dev]'` and run the root lint, schema, bundle, and pytest checks in addition to this Skill's smoke check.
- Some legacy utilities happen to use only the Python standard library, but the supported bundle installation is the root `data-quant` package. Do not infer dependency guarantees from an individual script's current imports; use `quantctl doctor`.

## Core Workflow

1. Clarify the analysis goal: prediction, explanation, causal effect, forecasting, segmentation, anomaly detection, dimensionality reduction, survival/time-to-event, or uncertainty quantification.
2. Identify the statistical target: continuous, binary, multiclass, ordinal, count, rate, proportion, time-to-event, time series, multivariate, text/image/sparse features, or no target label.
3. Inspect data constraints: sample size, `p >> n`, missingness, censoring, repeated measures, grouped data, class imbalance, leakage risk, temporal ordering, confounding, nonlinearity, outliers, and deployment constraints.
4. If a CSV is available and profiling is useful, run `scripts/profile_dataset.py` for a leakage-aware first pass over column types, missingness, imbalance, time/group hints, and risk flags.
5. Read [references/decision-tree.md](references/decision-tree.md) to route the task to the right method family.
6. Read [references/playbooks.md](references/playbooks.md) for scenario-specific workflows and baseline/candidate ordering.
7. Read [references/method-map.md](references/method-map.md) before recommending methods. Use its applicability column to mark where each candidate method fits.
8. Read [references/principles.md](references/principles.md) when explaining a method, comparing candidates, teaching intuition, or diagnosing misuse.
9. Read [references/anti-patterns.md](references/anti-patterns.md) when reviewing an analysis plan or detecting likely mistakes.
10. Read [references/evaluation-checklist.md](references/evaluation-checklist.md) when designing train/test splits, metrics, diagnostics, assumptions checks, or reporting.
11. Read [references/implementation-map.md](references/implementation-map.md) only when the user asks for code, libraries, or implementation choices.
12. Read [references/output-contracts.md](references/output-contracts.md) when chaining bundled JSON outputs, changing script schemas, or writing gate/aggregator scripts.
13. Read [references/quant-finance.md](references/quant-finance.md) when the task involves asset returns, alpha signals, factor analysis, factor exposures, risk models, portfolio construction, financial time series, or backtesting.
14. Read [references/quant-method-principles.md](references/quant-method-principles.md) when explaining the idea, assumptions, interpretation, or misuse of quant methods.
15. Read [references/quant-anti-patterns.md](references/quant-anti-patterns.md) when reviewing alpha research, factor tests, portfolio backtests, transaction costs, risk models, or investment performance claims.
16. Read [references/quant-production-monitoring.md](references/quant-production-monitoring.md) when the task involves paper trading, live trading, go-live gates, live-vs-paper drift, signal health monitoring, production alerts, or strategy retirement.
17. Read [references/quant-report-templates.md](references/quant-report-templates.md) when the user asks for a quant research memo, factor report, backtest review, risk report, event study, or formal quant deliverable.
18. Prefer a simple baseline plus one or more stronger candidates. Explain what would make each candidate win or fail.
19. Separate predictive claims from causal claims. Do not present observational associations as causal effects unless causal assumptions, identification, and robustness checks are explicit.
20. Return an actionable plan: data preparation, recommended methods, alternatives, validation scheme, diagnostics, interpretation/reporting, and caveats.

## Method Selection Shortcuts

- Use linear/logistic/GLM families first when interpretability, inference, small data, or a strong baseline matters.
- Use regularized linear models when features are many, collinear, sparse, or high-dimensional.
- Use tree ensembles when tabular prediction quality matters and nonlinear interactions are likely.
- Use SVM, kernel ridge, Gaussian processes, splines, or GAMs when nonlinearity matters but sample size is moderate enough for careful tuning.
- Use clustering, matrix factorization, PCA, manifold learning, topic models, or density/anomaly methods when labels are absent.
- Use time-series models only when temporal dependence, lag structure, seasonality, or rolling-origin validation matters.
- Use survival models when the outcome is time until event and censoring is present.
- Use causal methods when the question asks "what is the effect of doing X?" rather than "what predicts Y?"
- Use Bayesian models when prior knowledge, hierarchical pooling, sparse data, uncertainty propagation, or probabilistic statements are central.
- Use panel/econometric methods when repeated units, endogeneity, instruments, systems of equations, or many simultaneous tests are central.
- Use quantitative finance methods when observations are assets, returns, factors, portfolios, trades, event windows, or backtests; check point-in-time data, survivorship, costs, turnover, and benchmark/factor exposures.
- Use recommender/ranking/association methods when the output is ordering, relevance, next-item choice, or co-occurrence rather than a standard label.
- Use spatial, graph, deep learning, or representation-learning methods only when the data structure and scale justify those specialized families.

## Output Contract

When answering a user, include:

- A one-paragraph diagnosis of the data/problem type.
- A ranked method table with `method`, `core idea`, `why it fits`, `when to avoid`, `validation/diagnostics`, and `interpretation`.
- The recommended evaluation design and metrics.
- Assumptions and risks, including leakage, confounding, missingness, imbalance, temporal dependence, and overfitting.
- A report outline from [references/report-templates.md](references/report-templates.md), or [references/quant-report-templates.md](references/quant-report-templates.md) for quant finance deliverables, when the user asks for a formal analysis deliverable.
- Next implementation steps in Python/R/SQL only when the user asks to execute or code the analysis.

## Guardrails

- Never tune preprocessing, resampling, feature selection, or imputation outside cross-validation folds.
- Never use random splits for forecasting, survival with time-dependent leakage, or panel data where groups must be held out.
- Never optimize accuracy alone for imbalanced classification without checking precision, recall, PR-AUC, calibration, and cost-sensitive thresholds.
- Never rely on t-SNE/UMAP plots as proof of separability or clustering quality.
- Never recommend black-box models alone when the user asks for inference, coefficients, confidence intervals, or policy explanations.
- Always distinguish association, prediction, intervention, and counterfactual questions.

## Scripts

### Shared helpers

- `scripts/quant_utils.py`: pandas/numpy/scipy helpers used by ~50 of the bundled scripts. Provides `read_dataframe`, `require_columns`, `ols` (SVD-based), `newey_west_se`, `solve_psd`, `summarize_series`, `summarize_returns`, `max_drawdown`, `cross_sectional_corr`, `rank_within`, plus scalar helpers (`parse_float`, `is_missing`, `mean`, `stdev`, `quantile`, `correlation`, `spearman`, `sorted_group_keys`) for row-by-row audit scripts. Not invoked directly.
- `scripts/_check_skill_index.py`: verifies that every script and reference is indexed in SKILL.md and `implementation-map.md`. Run from the repo root. Standard library only.
- `scripts/smoke_check.sh`: runs quick standard-library validation (`--quick`) or full dependency + example validation (`--full`) for release checks.

### Statistical learning starter tools

- `scripts/profile_dataset.py`: Profile CSV structure, column types, missingness, imbalance, time/group hints, and leakage risk flags. Requires the declared bundle dependencies.
- `scripts/split_dataset.py`: Create train/test CSV splits using random, stratified, time-ordered, or grouped strategies. Requires the declared bundle dependencies.
- `scripts/causal_balance_check.py`: Compute standardized mean-difference covariate balance diagnostics for treated/control data. Requires the declared bundle dependencies.
- `scripts/time_series_backtest.py`: Backtest naive and seasonal-naive forecasting baselines by horizon. Requires the declared bundle dependencies.
- `scripts/sklearn_tabular_model.py`: Train a starter scikit-learn tabular classification/regression pipeline and write model reports. Requires `pandas`, `scikit-learn`, and `joblib`.
- `scripts/classification_report.py`: Evaluate classification predictions from labels and/or positive-class scores. Requires the declared bundle dependencies.
- `scripts/threshold_tuning.py`: Tune binary classification thresholds for F1, precision, recall, specificity, or simple cost. Requires the declared bundle dependencies.
- `scripts/missingness_report.py`: Summarize missingness by column, row, and missingness pattern. Requires the declared bundle dependencies.
- `scripts/panel_summary.py`: Summarize entity/time panel structure and repeated-observation risks. Requires the declared bundle dependencies.
- `scripts/compare_model_reports.py`: Compare JSON model reports into a metric leaderboard. Requires the declared bundle dependencies.
- `scripts/survival_km_report.py`: Kaplan-Meier survival curves, median survival, and Mantel-Haenszel log-rank test across groups. Requires numpy/pandas/scipy.
- `scripts/anomaly_score_report.py`: Univariate (z-score, IQR) and multivariate (Mahalanobis with covariance shrinkage) anomaly scores with a chi-square reference and top-row listing. Requires numpy/pandas/scipy.
- `scripts/cluster_quality_report.py`: Silhouette, Calinski-Harabasz, Davies-Bouldin, and bootstrap ARI stability for k-means or precomputed cluster labels. Requires scikit-learn (and numpy/pandas).
- `scripts/calibration_report.py`: Probability calibration: per-bin reliability table (equal-width or equal-frequency binning), expected/maximum calibration error, Brier score, log loss. Requires numpy/pandas.
- `scripts/returns_risk_report.py`: Compute return/risk metrics, drawdowns, VaR/ES, Sharpe/Sortino, and correlations for return or price CSVs. Requires the declared bundle dependencies.
- `scripts/factor_exposure_regression.py`: Regress asset/strategy returns on factor returns and report alpha, betas, t-stats, R-squared, and residual risk. Requires the declared bundle dependencies.
- `scripts/point_in_time_audit.py`: Audit date-entity signal panels for point-in-time availability, look-ahead leakage, universe timing, revisions, execution ordering, and duplicate as-of keys. Requires the declared bundle dependencies.
- `scripts/execution_timing_audit.py`: Audit signal, rebalance, execution, and forward-return window timing for same-day execution gaps, non-executable return windows, stale signals, weekend dates, and duplicate signal keys. Requires the declared bundle dependencies.
- `scripts/tradability_audit.py`: Audit market-state tradability evidence for halted/suspended assets, zero volume, limit locks, high participation, stale prices, shorting, and borrow availability. Requires the declared bundle dependencies.
- `scripts/factor_ic_report.py`: Compute per-date cross-sectional IC and rank IC for factor values against forward returns. Requires the declared bundle dependencies.
- `scripts/factor_quantile_report.py`: Evaluate factor-sorted quantile forward returns and high-minus-low spreads. Requires the declared bundle dependencies.
- `scripts/factor_decay_report.py`: Compare IC and rank IC across multiple forward-return horizons. Requires the declared bundle dependencies.
- `scripts/factor_turnover_report.py`: Estimate selected-name turnover, membership overlap, and rank autocorrelation across rebalance dates. Requires the declared bundle dependencies.
- `scripts/signal_overlap_report.py`: Diagnose correlation, rank correlation, selected-name overlap, and redundancy across multiple alpha signal columns. Requires the declared bundle dependencies.
- `scripts/incremental_alpha_report.py`: Test whether a candidate alpha adds residual IC, coefficient, and R-squared value after existing signals or exposures. Requires the declared bundle dependencies.
- `scripts/portfolio_backtest.py`: Backtest date-asset portfolio weights against asset returns with gross/net metrics and turnover. Requires the declared bundle dependencies.
- `scripts/transaction_cost_report.py`: Estimate turnover-driven commissions, slippage, spread, borrow, cost drag, and optional ADV participation. Requires the declared bundle dependencies.
- `scripts/covariance_report.py`: Compute covariance, annualized covariance, correlation, and volatility diagnostics for return columns. Requires the declared bundle dependencies.
- `scripts/ewma_volatility.py`: Compute EWMA volatility paths and latest annualized volatility for return columns. Requires the declared bundle dependencies.
- `scripts/rolling_beta.py`: Estimate rolling alpha, beta, R-squared, and residual volatility against a benchmark. Requires the declared bundle dependencies.
- `scripts/pairs_spread_report.py`: Estimate static hedge ratio, spread z-scores, crossings, autocorrelation, and approximate half-life for a pair. Requires the declared bundle dependencies.
- `scripts/event_study_report.py`: Compute simple benchmark-adjusted or mean-adjusted event-study abnormal returns and CAR. Requires the declared bundle dependencies.
- `scripts/cross_sectional_return_regression.py`: Run single-date or pooled cross-sectional return regressions on asset characteristics/exposures. Requires the declared bundle dependencies.
- `scripts/fama_macbeth_regression.py`: Run date-by-date Fama-MacBeth regressions and summarize average risk premia. Requires the declared bundle dependencies.
- `scripts/long_short_backtest.py`: Form signal-ranked long/short or long-only portfolios and report gross/net performance and turnover. Requires the declared bundle dependencies.
- `scripts/portfolio_exposure_report.py`: Aggregate numeric and categorical portfolio exposures from date-asset weights. Requires the declared bundle dependencies.
- `scripts/pca_risk_model.py`: Compute PCA statistical risk-factor diagnostics from return covariance/correlation matrices. Requires the declared bundle dependencies.
- `scripts/factor_neutralization.py`: Residualize a factor signal against numeric and categorical exposures within each date. Requires the declared bundle dependencies.
- `scripts/newey_west_regression.py`: Run OLS with IID and Newey-West/HAC standard errors for time-series regressions. Requires the declared bundle dependencies.
- `scripts/multiple_testing_report.py`: Apply Bonferroni, Holm, and Benjamini-Hochberg corrections to factor/model p-values. Requires the declared bundle dependencies.
- `scripts/quant_experiment_audit.py`: Audit a quant research experiment registry for unregistered trials, missing failed variants, selective promotion, final-test gaps, and version evidence. Requires the declared bundle dependencies.
- `scripts/capacity_impact_report.py`: Estimate ADV participation, simple market impact, cost bps, and binding NAV capacity from weight changes. Requires the declared bundle dependencies.
- `scripts/portfolio_constraint_check.py`: Check portfolio weights against gross, net, single-name, category, and turnover constraints. Requires the declared bundle dependencies.
- `scripts/bootstrap_reality_check.py`: Run a block-bootstrap reality-check diagnostic across many strategy return columns. Requires the declared bundle dependencies.
- `scripts/alpha_research_gate_report.py`: Gate candidate alpha research using bundled JSON diagnostics for experiment audit, IC, incremental value, overlap, turnover, costs, capacity, and multiple testing. Requires the declared bundle dependencies.
- `scripts/walk_forward_stability.py`: Evaluate walk-forward parameter-selection stability from date/parameter/metric results. Requires the declared bundle dependencies.
- `scripts/optimizer_sensitivity_report.py`: Assess mean-variance weight sensitivity to expected-return and covariance perturbations. Requires the declared bundle dependencies.
- `scripts/portfolio_construction_gate_report.py`: Gate portfolio construction using bundled JSON diagnostics for backtest, constraints, exposures, risk contribution, optimizer stability, costs, and capacity. Requires the declared bundle dependencies.
- `scripts/performance_attribution_report.py`: Attribute portfolio return to assets and optional groups from weights and asset returns. Requires the declared bundle dependencies.
- `scripts/risk_contribution_report.py`: Compute portfolio volatility and component risk contributions from weights and covariance. Requires the declared bundle dependencies.
- `scripts/regime_robustness_report.py`: Evaluate return robustness across user-provided market regimes. Requires the declared bundle dependencies.
- `scripts/risk_forecast_calibration.py`: Check volatility and normal-VaR forecast calibration against realized returns. Requires the declared bundle dependencies.
- `scripts/model_risk_register_report.py`: Audit quant model-risk registers for owners, risk tiers, validation, approvals, review dates, monitoring, rollback controls, and version evidence. Requires the declared bundle dependencies.
- `scripts/execution_slippage_report.py`: Summarize side-aware execution slippage and implementation shortfall from fills. Requires the declared bundle dependencies.
- `scripts/live_vs_paper_report.py`: Compare live strategy returns with paper or backtest returns. Requires the declared bundle dependencies.
- `scripts/signal_health_monitor.py`: Monitor factor or alpha-signal coverage, IC, spread, and turnover health. Requires the declared bundle dependencies.
- `scripts/go_live_gate_report.py`: Summarize quant strategy go-live checklist status and blockers. Requires the declared bundle dependencies.
- `scripts/order_exception_report.py`: Summarize rejected, cancelled, open, and partially filled order exceptions. Requires the declared bundle dependencies.
- `scripts/data_freshness_report.py`: Check dataset timestamp, row-count, missingness, and upstream status freshness. Requires the declared bundle dependencies.
- `scripts/limit_breach_report.py`: Summarize risk, portfolio, and operations limit breaches. Requires the declared bundle dependencies.
- `scripts/strategy_action_decision.py`: Convert monitoring thresholds into maintain/review/reduce/pause/retire action recommendations. Requires the declared bundle dependencies.
- `scripts/quant_checklist_template.py`: Generate default go-live, monitoring, or retirement checklist templates. Requires the declared bundle dependencies.
- `scripts/quant_report_aggregator.py`: Aggregate bundled quant JSON diagnostics into one strategy review or production health report. Requires the declared bundle dependencies.
- `scripts/quant_review_pack.py`: Generate committee-style quant review packs from bundled JSON diagnostics with decision stack, role review, evidence gaps, and next actions. Requires the declared bundle dependencies.

## References

- [references/method-map.md](references/method-map.md): Detailed method families and applicability scenarios.
- [references/principles.md](references/principles.md): Concise core ideas, assumptions, and common misuses for major method families.
- [references/decision-tree.md](references/decision-tree.md): Routing logic from data/question type to method families.
- [references/playbooks.md](references/playbooks.md): Scenario-specific statistical learning workflows.
- [references/evaluation-checklist.md](references/evaluation-checklist.md): Validation, diagnostics, metric selection, and reporting checklist.
- [references/implementation-map.md](references/implementation-map.md): Python/R library and class/function mapping for implementation tasks.
- [references/output-contracts.md](references/output-contracts.md): Stable JSON, Markdown, CSV, gate, and aggregator output conventions for bundled scripts.
- [references/quant-finance.md](references/quant-finance.md): Quantitative finance method map for factor analysis, risk models, portfolio construction, financial time series, and backtesting.
- [references/quant-method-principles.md](references/quant-method-principles.md): Core ideas, interpretation rules, and failure modes for quant methods.
- [references/quant-production-monitoring.md](references/quant-production-monitoring.md): Paper trading, live monitoring, go-live gates, drift checks, and escalation rules.
- [references/quant-anti-patterns.md](references/quant-anti-patterns.md): Quant-specific research, backtest, execution, risk, and reporting failure modes.
- [references/quant-report-templates.md](references/quant-report-templates.md): Quant research, factor, backtest, attribution, risk, and event-study report structures.
- [references/anti-patterns.md](references/anti-patterns.md): Common statistical learning mistakes and corrective actions.
- [references/report-templates.md](references/report-templates.md): Reusable structures for analysis deliverables.
- [references/glossary-zh-en.md](references/glossary-zh-en.md): Chinese-English terminology for statistical learning work.
- [references/validation-scenarios.md](references/validation-scenarios.md): Forward-test scenarios and expected behavior checks.
- [references/sources.md](references/sources.md): Online sources used to build this skill and where to look for deeper details.
- [scripts/profile_dataset.py](scripts/profile_dataset.py): Lightweight CSV profiler for first-pass method-selection signals.
- [scripts/split_dataset.py](scripts/split_dataset.py): Leakage-aware train/test CSV splitting utility.
- [scripts/causal_balance_check.py](scripts/causal_balance_check.py): Standardized mean-difference balance diagnostic utility.
- [scripts/time_series_backtest.py](scripts/time_series_backtest.py): Naive and seasonal-naive forecast backtesting utility.
- [scripts/sklearn_tabular_model.py](scripts/sklearn_tabular_model.py): Starter scikit-learn tabular modeling pipeline.
- [scripts/classification_report.py](scripts/classification_report.py): Classification metrics, confusion matrix, ROC-AUC, average precision, and loss utility.
- [scripts/threshold_tuning.py](scripts/threshold_tuning.py): Binary threshold selection utility.
- [scripts/missingness_report.py](scripts/missingness_report.py): Missingness diagnostic utility.
- [scripts/panel_summary.py](scripts/panel_summary.py): Panel/repeated-entity structure summary utility.
- [scripts/compare_model_reports.py](scripts/compare_model_reports.py): JSON model report comparison utility.
- [scripts/survival_km_report.py](scripts/survival_km_report.py): Kaplan-Meier and log-rank survival utility.
- [scripts/anomaly_score_report.py](scripts/anomaly_score_report.py): Univariate/multivariate anomaly score diagnostic utility.
- [scripts/cluster_quality_report.py](scripts/cluster_quality_report.py): Silhouette + bootstrap ARI cluster quality utility.
- [scripts/calibration_report.py](scripts/calibration_report.py): Probability calibration diagnostic utility.
- [scripts/returns_risk_report.py](scripts/returns_risk_report.py): Quant return and risk metric utility.
- [scripts/factor_exposure_regression.py](scripts/factor_exposure_regression.py): Factor exposure regression utility.
- [scripts/point_in_time_audit.py](scripts/point_in_time_audit.py): Point-in-time data and look-ahead leakage audit utility.
- [scripts/execution_timing_audit.py](scripts/execution_timing_audit.py): Signal execution and forward-return window timing audit utility.
- [scripts/tradability_audit.py](scripts/tradability_audit.py): Market-state tradability and short/borrow evidence audit utility.
- [scripts/factor_ic_report.py](scripts/factor_ic_report.py): Cross-sectional factor IC and rank-IC utility.
- [scripts/factor_quantile_report.py](scripts/factor_quantile_report.py): Factor quantile return and high-minus-low spread utility.
- [scripts/factor_decay_report.py](scripts/factor_decay_report.py): Factor IC decay utility across multiple horizons.
- [scripts/factor_turnover_report.py](scripts/factor_turnover_report.py): Factor selection turnover and rank-stability utility.
- [scripts/signal_overlap_report.py](scripts/signal_overlap_report.py): Multi-signal overlap and redundancy diagnostic utility.
- [scripts/incremental_alpha_report.py](scripts/incremental_alpha_report.py): Candidate signal incremental-alpha diagnostic utility.
- [scripts/portfolio_backtest.py](scripts/portfolio_backtest.py): Portfolio weight backtest utility.
- [scripts/transaction_cost_report.py](scripts/transaction_cost_report.py): Portfolio transaction-cost diagnostic utility.
- [scripts/covariance_report.py](scripts/covariance_report.py): Covariance, correlation, and volatility diagnostic utility.
- [scripts/ewma_volatility.py](scripts/ewma_volatility.py): EWMA volatility diagnostic utility.
- [scripts/rolling_beta.py](scripts/rolling_beta.py): Rolling benchmark beta utility.
- [scripts/pairs_spread_report.py](scripts/pairs_spread_report.py): Pair spread diagnostic utility.
- [scripts/event_study_report.py](scripts/event_study_report.py): Event-study abnormal return utility.
- [scripts/cross_sectional_return_regression.py](scripts/cross_sectional_return_regression.py): Cross-sectional return regression utility.
- [scripts/fama_macbeth_regression.py](scripts/fama_macbeth_regression.py): Fama-MacBeth regression utility.
- [scripts/long_short_backtest.py](scripts/long_short_backtest.py): Signal-ranked long/short portfolio utility.
- [scripts/portfolio_exposure_report.py](scripts/portfolio_exposure_report.py): Portfolio exposure aggregation utility.
- [scripts/pca_risk_model.py](scripts/pca_risk_model.py): PCA statistical risk-factor diagnostic utility.
- [scripts/factor_neutralization.py](scripts/factor_neutralization.py): Factor exposure neutralization utility.
- [scripts/newey_west_regression.py](scripts/newey_west_regression.py): Newey-West/HAC regression utility.
- [scripts/multiple_testing_report.py](scripts/multiple_testing_report.py): Multiple-testing correction utility.
- [scripts/quant_experiment_audit.py](scripts/quant_experiment_audit.py): Quant research experiment registry audit utility.
- [scripts/capacity_impact_report.py](scripts/capacity_impact_report.py): Capacity and market-impact diagnostic utility.
- [scripts/portfolio_constraint_check.py](scripts/portfolio_constraint_check.py): Portfolio constraint checking utility.
- [scripts/bootstrap_reality_check.py](scripts/bootstrap_reality_check.py): Bootstrap reality-check diagnostic utility.
- [scripts/alpha_research_gate_report.py](scripts/alpha_research_gate_report.py): Candidate alpha research gate utility.
- [scripts/walk_forward_stability.py](scripts/walk_forward_stability.py): Walk-forward parameter-stability utility.
- [scripts/optimizer_sensitivity_report.py](scripts/optimizer_sensitivity_report.py): Optimizer input-sensitivity diagnostic utility.
- [scripts/portfolio_construction_gate_report.py](scripts/portfolio_construction_gate_report.py): Portfolio construction gate utility.
- [scripts/performance_attribution_report.py](scripts/performance_attribution_report.py): Portfolio performance attribution utility.
- [scripts/risk_contribution_report.py](scripts/risk_contribution_report.py): Portfolio risk contribution utility.
- [scripts/regime_robustness_report.py](scripts/regime_robustness_report.py): Regime robustness diagnostic utility.
- [scripts/risk_forecast_calibration.py](scripts/risk_forecast_calibration.py): Risk forecast calibration utility.
- [scripts/model_risk_register_report.py](scripts/model_risk_register_report.py): Quant model-risk register audit utility.
- [scripts/execution_slippage_report.py](scripts/execution_slippage_report.py): Execution slippage and shortfall diagnostic utility.
- [scripts/live_vs_paper_report.py](scripts/live_vs_paper_report.py): Live-vs-paper drift diagnostic utility.
- [scripts/signal_health_monitor.py](scripts/signal_health_monitor.py): Signal health monitoring utility.
- [scripts/go_live_gate_report.py](scripts/go_live_gate_report.py): Go-live gate checklist utility.
- [scripts/order_exception_report.py](scripts/order_exception_report.py): Order exception and fill-rate monitoring utility.
- [scripts/data_freshness_report.py](scripts/data_freshness_report.py): Dataset freshness and missingness monitoring utility.
- [scripts/limit_breach_report.py](scripts/limit_breach_report.py): Limit breach monitoring utility.
- [scripts/strategy_action_decision.py](scripts/strategy_action_decision.py): Strategy action decision utility.
- [scripts/quant_checklist_template.py](scripts/quant_checklist_template.py): Quant checklist template generator.
- [scripts/quant_report_aggregator.py](scripts/quant_report_aggregator.py): Quant JSON diagnostics aggregation utility.
- [scripts/quant_review_pack.py](scripts/quant_review_pack.py): Committee-style quant review pack generator.
