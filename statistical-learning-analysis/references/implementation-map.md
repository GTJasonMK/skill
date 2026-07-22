# Implementation Map

Use this file only when the user asks for implementation choices, code, or package recommendations. Prefer official APIs and keep preprocessing inside pipelines/folds.

## Contents

- [General Python Workflow](#general-python-workflow)
- [Bundled Scripts](#bundled-scripts)
- [Supervised Learning](#supervised-learning)
- [Unsupervised, Anomaly, and Representation](#unsupervised-anomaly-and-representation)
- [Statistical Inference and Specialized Models](#statistical-inference-and-specialized-models)
- [Time, Survival, Causal, Spatial, Graph, and Recommendation](#time-survival-causal-spatial-graph-and-recommendation)
- [Quantitative Finance](#quantitative-finance)
- [Implementation Rules](#implementation-rules)

## General Python Workflow

| Task | Preferred tools | Notes |
| --- | --- | --- |
| Tabular ML pipeline | `sklearn.pipeline.Pipeline`, `sklearn.compose.ColumnTransformer` | Keep preprocessing inside CV to avoid leakage. |
| Scaling/encoding | `StandardScaler`, `OneHotEncoder`, `OrdinalEncoder`, `SimpleImputer` | Fit only on training folds. |
| Model selection | `GridSearchCV`, `RandomizedSearchCV`, `cross_validate`, nested CV | Use `StratifiedKFold`, `GroupKFold`, or time-aware split as needed. |
| Metrics | `sklearn.metrics` | Choose metrics before tuning. |
| Probability calibration | `CalibratedClassifierCV`, calibration curves | Calibrate on held-out/cross-fitted data. |

## Bundled Scripts

| Script | Use | Dependencies |
| --- | --- | --- |
| `scripts/profile_dataset.py` | First-pass CSV profiling for target type, missingness, leakage hints, time/group hints, and imbalance. | Python standard library |
| `scripts/split_dataset.py` | Create reproducible random, stratified, time-ordered, or grouped train/test splits. | Python standard library |
| `scripts/causal_balance_check.py` | Check treated/control covariate balance with standardized mean differences before causal estimation. | Python standard library |
| `scripts/time_series_backtest.py` | Establish naive and seasonal-naive forecasting baselines before complex time-series models. | Python standard library |
| `scripts/sklearn_tabular_model.py` | Train a starter tabular classification/regression pipeline and write reports. | `pandas`, `scikit-learn`, `joblib` |
| `scripts/classification_report.py` | Evaluate classification labels/scores with confusion matrix, per-class metrics, ROC-AUC, average precision, Brier score, and log loss. | Python standard library |
| `scripts/threshold_tuning.py` | Select binary classification operating thresholds for F1, precision, recall, specificity, or cost constraints. | Python standard library |
| `scripts/missingness_report.py` | Report missingness by column, row, and pattern before imputation or complete-case decisions. | Python standard library |
| `scripts/panel_summary.py` | Summarize repeated entity/time structure for panel, grouped validation, fixed effects, or mixed-model planning. | Python standard library |
| `scripts/compare_model_reports.py` | Compare JSON metric reports and produce a simple leaderboard. | Python standard library |
| `scripts/returns_risk_report.py` | Compute quant return/risk diagnostics including annualized return/volatility, Sharpe, Sortino, drawdown, VaR, expected shortfall, and correlations. | numpy, pandas |
| `scripts/factor_exposure_regression.py` | Estimate alpha/beta factor exposures with OLS for asset or strategy returns. | numpy, pandas |
| `scripts/point_in_time_audit.py` | Audit date-entity factor panels for point-in-time availability, look-ahead leakage, universe timing, revisions, execution ordering, and duplicate as-of keys. | numpy, pandas |
| `scripts/execution_timing_audit.py` | Audit signal, rebalance, execution, and forward-return window timing for same-day execution gaps, non-executable windows, stale signals, weekend dates, and duplicate signal keys. | numpy, pandas |
| `scripts/tradability_audit.py` | Audit market-state tradability evidence for halted/suspended rows, zero volume, price-limit locks, high participation, stale prices, and short/borrow availability. | numpy, pandas |
| `scripts/factor_ic_report.py` | Compute per-date cross-sectional factor IC and rank IC against forward returns. | numpy, pandas |
| `scripts/factor_quantile_report.py` | Evaluate factor-sorted quantile forward returns and high-minus-low spreads. | numpy, pandas |
| `scripts/factor_decay_report.py` | Compare factor IC and rank IC across multiple forward-return horizons. | numpy, pandas |
| `scripts/factor_turnover_report.py` | Estimate selected-name turnover, membership overlap, and factor rank autocorrelation. | numpy, pandas |
| `scripts/signal_overlap_report.py` | Diagnose signal correlation, rank correlation, selected-name overlap, and redundant signal pairs. | numpy, pandas |
| `scripts/incremental_alpha_report.py` | Test residual IC, candidate coefficient, and delta R-squared after controlling for existing signals or exposures. | numpy, pandas |
| `scripts/portfolio_backtest.py` | Backtest date-asset portfolio weights against asset returns with turnover and gross/net return metrics. | numpy, pandas |
| `scripts/transaction_cost_report.py` | Estimate turnover-driven commissions, slippage, spread, borrow, cost drag, and optional ADV participation. | numpy, pandas |
| `scripts/covariance_report.py` | Compute covariance, annualized covariance, correlation, and volatility diagnostics for return columns. | numpy, pandas |
| `scripts/ewma_volatility.py` | Compute EWMA volatility paths and latest annualized volatility for return columns. | numpy, pandas |
| `scripts/rolling_beta.py` | Estimate rolling alpha, beta, R-squared, and residual volatility against a benchmark. | numpy, pandas |
| `scripts/pairs_spread_report.py` | Estimate pair spread hedge ratio, z-scores, crossings, autocorrelation, and approximate half-life. | numpy, pandas |
| `scripts/event_study_report.py` | Compute simple benchmark-adjusted or mean-adjusted abnormal returns and CAR around events. | numpy, pandas |
| `scripts/cross_sectional_return_regression.py` | Run single-date or pooled cross-sectional return regressions on characteristics/exposures. | numpy, pandas |
| `scripts/fama_macbeth_regression.py` | Run date-by-date Fama-MacBeth regressions and summarize average premia. | numpy, pandas |
| `scripts/long_short_backtest.py` | Form signal-ranked long/short or long-only portfolios and report gross/net performance and turnover. | numpy, pandas |
| `scripts/portfolio_exposure_report.py` | Aggregate numeric and categorical portfolio exposures from date-asset weights. | numpy, pandas |
| `scripts/pca_risk_model.py` | Compute PCA statistical risk-factor diagnostics from return covariance/correlation matrices. | numpy, pandas |
| `scripts/factor_neutralization.py` | Residualize a factor signal against numeric and categorical exposures within each date. | numpy, pandas |
| `scripts/newey_west_regression.py` | Run OLS with IID and Newey-West/HAC standard errors for time-series regressions. | numpy, pandas, scipy |
| `scripts/multiple_testing_report.py` | Apply Bonferroni, Holm, and Benjamini-Hochberg corrections to factor/model p-values. | numpy, pandas |
| `scripts/quant_experiment_audit.py` | Audit a quant research experiment registry for missing failed trials, selected-final-test gaps, FDR issues, and version evidence. | numpy, pandas |
| `scripts/capacity_impact_report.py` | Estimate ADV participation, simple market impact, cost bps, and binding NAV capacity from weight changes. | numpy, pandas |
| `scripts/portfolio_constraint_check.py` | Check portfolio weights against gross, net, single-name, category, and turnover constraints. | numpy, pandas |
| `scripts/bootstrap_reality_check.py` | Run a centered block-bootstrap reality-check diagnostic across many strategy return columns. | numpy, pandas |
| `scripts/alpha_research_gate_report.py` | Convert bundled alpha diagnostics into a research-stage pass/review/fail gate with blockers and evidence gaps. | numpy, pandas |
| `scripts/walk_forward_stability.py` | Evaluate walk-forward parameter-selection stability from date/parameter/metric results. | numpy, pandas |
| `scripts/optimizer_sensitivity_report.py` | Assess mean-variance weight sensitivity to expected-return and covariance perturbations. | numpy, pandas, scipy |
| `scripts/portfolio_construction_gate_report.py` | Convert portfolio backtest, constraint, exposure, risk, optimizer, cost, and capacity diagnostics into a construction-stage gate. | numpy, pandas |
| `scripts/performance_attribution_report.py` | Attribute portfolio return to assets and optional groups from weights and asset returns. | numpy, pandas |
| `scripts/risk_contribution_report.py` | Compute portfolio volatility and component risk contributions from weights and covariance. | numpy, pandas, scipy |
| `scripts/regime_robustness_report.py` | Evaluate strategy return robustness across market regimes. | numpy, pandas |
| `scripts/risk_forecast_calibration.py` | Check volatility and normal-VaR forecast calibration against realized returns. | numpy, pandas, scipy |
| `scripts/model_risk_register_report.py` | Audit model-risk register governance evidence for owners, validation, approvals, reviews, monitoring, rollback controls, and version evidence. | numpy, pandas |
| `scripts/execution_slippage_report.py` | Summarize side-aware execution slippage and implementation shortfall from fills. | numpy, pandas |
| `scripts/live_vs_paper_report.py` | Compare live strategy returns with paper or backtest returns. | numpy, pandas |
| `scripts/signal_health_monitor.py` | Monitor factor or alpha-signal coverage, IC, spread, and turnover health. | numpy, pandas |
| `scripts/go_live_gate_report.py` | Summarize quant strategy go-live checklist status and blockers. | numpy, pandas |
| `scripts/order_exception_report.py` | Summarize rejected, cancelled, open, and partially filled order exceptions. | numpy, pandas |
| `scripts/data_freshness_report.py` | Check dataset timestamp, row-count, missingness, and upstream status freshness. | numpy, pandas |
| `scripts/limit_breach_report.py` | Summarize risk, portfolio, and operations limit breaches. | numpy, pandas |
| `scripts/strategy_action_decision.py` | Convert monitoring thresholds into maintain/review/reduce/pause/retire action recommendations. | numpy, pandas |
| `scripts/quant_checklist_template.py` | Generate default go-live, monitoring, or retirement checklist templates. | numpy, pandas |
| `scripts/quant_report_aggregator.py` | Aggregate bundled quant JSON diagnostics into one strategy review or production health report. | numpy, pandas |
| `scripts/quant_review_pack.py` | Generate role-aware committee review packs from bundled quant JSON diagnostics and gates. | numpy, pandas |
| `scripts/survival_km_report.py` | Kaplan-Meier survival curves, median survival, and Mantel-Haenszel log-rank test across groups. | numpy, pandas, scipy |
| `scripts/anomaly_score_report.py` | Univariate (z-score, IQR) and multivariate (Mahalanobis) anomaly scores with chi-square reference. | numpy, pandas, scipy |
| `scripts/cluster_quality_report.py` | Silhouette / Calinski-Harabasz / Davies-Bouldin + bootstrap ARI stability for k-means or precomputed labels. | numpy, pandas, scikit-learn |
| `scripts/calibration_report.py` | Reliability table, expected/maximum calibration error, Brier score, log loss. | numpy, pandas |

## Supervised Learning

| Method family | Python implementation | R implementation | Notes |
| --- | --- | --- | --- |
| Linear regression | `statsmodels.OLS`, `sklearn.linear_model.LinearRegression` | `lm` | Use statsmodels/R for inference; sklearn for pipelines/prediction. |
| Ridge/Lasso/Elastic Net | `Ridge`, `Lasso`, `ElasticNet`, `LogisticRegression(penalty=...)` | `glmnet` | Standardize features. |
| Logistic regression | `sklearn.linear_model.LogisticRegression`, `statsmodels.Logit` | `glm(family=binomial)` | Use statsmodels/R for coefficient inference. |
| GLM | `statsmodels.GLM` | `glm` | Match family/link to outcome. |
| GAM/splines | `statsmodels.gam.GLMGam`, `pygam` | `mgcv::gam` | Check smoothness and concurvity. |
| Robust/quantile regression | `statsmodels.RLM`, `statsmodels.QuantReg` | `MASS::rlm`, `quantreg::rq` | Useful for outliers/tails. |
| SVM/SVR | `sklearn.svm.SVC`, `SVR`, `LinearSVC` | `e1071`, `kernlab` | Scale features; calibrate probabilities. |
| kNN | `KNeighborsClassifier`, `KNeighborsRegressor` | `class`, `caret` | Scale and check distance metric. |
| Trees | `DecisionTreeClassifier/Regressor` | `rpart` | Constrain depth/prune. |
| Random forest/Extra Trees | `RandomForest*`, `ExtraTrees*` | `randomForest`, `ranger` | Check calibration and feature importance bias. |
| Gradient boosting | `HistGradientBoosting*`, `GradientBoosting*`, `xgboost`, `lightgbm`, `catboost` | `xgboost`, `lightgbm`, `catboost` | Use validation/early stopping; handle categorical features carefully. |
| Neural networks | `sklearn.neural_network.MLP*`, PyTorch, Keras | `keras`, `torch` | Prefer deep learning for large/unstructured data. |

## Unsupervised, Anomaly, and Representation

| Method family | Python implementation | Notes |
| --- | --- | --- |
| PCA/ICA/NMF/factor analysis | `sklearn.decomposition`, `statsmodels.multivariate.factor.Factor` | Fit inside folds when used for supervised prediction. |
| Clustering | `KMeans`, `AgglomerativeClustering`, `GaussianMixture`, `DBSCAN`, `SpectralClustering`, `Birch` | Scale/encode and validate stability. |
| Manifold visualization | `TSNE`, external `umap-learn` | Visualization is not proof. |
| Anomaly detection | `IsolationForest`, `OneClassSVM`, `LocalOutlierFactor`, `EllipticEnvelope` | Threshold depends on contamination/cost. |
| Topic modeling | `sklearn.decomposition.LatentDirichletAllocation`, gensim | Validate topics with humans/domain labels. |
| Autoencoders/representation | PyTorch, Keras, PyTorch Lightning | Use when representation learning is central. |

## Statistical Inference and Specialized Models

| Problem | Python implementation | R implementation | Notes |
| --- | --- | --- | --- |
| Mixed effects | `statsmodels.MixedLM` | `lme4::lmer/glmer` | Convergence and random-effect structure matter. |
| GEE | `statsmodels.GEE` | `geepack::geeglm` | Population-average effects. |
| Count/zero-inflated | `statsmodels.Poisson`, `NegativeBinomial`, `ZeroInflatedPoisson`, `HurdleCountModel` | `MASS`, `pscl`, `glmmTMB` | Check overdispersion/zero inflation. |
| Ordinal/multinomial | `statsmodels.OrderedModel`, `MNLogit`; sklearn classifiers for prediction | `MASS::polr`, `nnet::multinom` | Distinguish prediction from inference. |
| MANOVA/CCA/factor | `statsmodels.MANOVA`, `CanCorr`, `Factor`; `sklearn.cross_decomposition.CCA` | `manova`, `CCA` | Validate multivariate assumptions/stability. |
| Panel models | `linearmodels.PanelOLS`, `RandomEffects`, `FirstDifferenceOLS` | `plm` | Clustered SE and entity/time effects. |
| IV/GMM | `linearmodels.IV2SLS`, `IVGMM`; `statsmodels.sandbox.regression.gmm` | `AER::ivreg`, `fixest`, `gmm` | Weak/invalid instruments are central risk. |
| Multiple testing | `statsmodels.stats.multitest.multipletests` | `p.adjust`, `qvalue` | Predefine family of tests. |
| Multiple imputation | `statsmodels.imputation.mice` | `mice` | Pool estimates correctly. |

## Time, Survival, Causal, Spatial, Graph, and Recommendation

| Problem | Python implementation | R implementation | Notes |
| --- | --- | --- | --- |
| ARIMA/SARIMA/state-space | `statsmodels.tsa.arima.model.ARIMA`, `SARIMAX`, `ETSModel`, `UnobservedComponents` | `forecast`, `fable` | Use rolling-origin validation. |
| VAR/VECM | `statsmodels.tsa.vector_ar.var_model.VAR`, `vecm.VECM` | `vars`, `urca` | Check stationarity/cointegration. |
| Survival | `lifelines.KaplanMeierFitter`, `CoxPHFitter`, `CoxTimeVaryingFitter`, `WeibullAFTFitter`; `statsmodels.PHReg` | `survival::coxph`, `survreg` | Check censoring and PH assumptions. |
| Bayesian modeling | PyMC, Stan, NumPyro | `brms`, `rstanarm`, `rstan` | Prior/posterior predictive checks and sampling diagnostics. |
| Causal inference | DoWhy, EconML, statsmodels, linearmodels | `MatchIt`, `did`, `AER`, `fixest`, `grf` | State identification before estimation. |
| Spatial statistics | PySAL/spreg, geopandas | `spdep`, `sf`, `spatialreg` | Use spatial weights and spatial CV. |
| Graph learning | NetworkX, PyTorch Geometric, DGL | `igraph`, `tidygraph` | Avoid graph split leakage. |
| Recommendation | implicit, LightFM, Surprise, LensKit, PyTorch | `recommenderlab` | Time/user-aware validation. |

## Quantitative Finance

| Problem | Python implementation | R implementation | Notes |
| --- | --- | --- | --- |
| Return/risk diagnostics | bundled `returns_risk_report.py`, empyrical/quantstats | `PerformanceAnalytics` | Check drawdown, tail risk, factor exposure, and costs. |
| Factor exposure regression | bundled `factor_exposure_regression.py`, `statsmodels.OLS`, `RollingOLS` | `lm`, `sandwich`, `PerformanceAnalytics` | Use HAC/Newey-West for autocorrelated residuals in serious research. |
| Point-in-time data audit | bundled `point_in_time_audit.py`, vendor vintage tables, filing/release calendars | custom R/Python, SQL timestamp checks | Check availability, data, period-end, universe, revision, vendor, signal, rebalance, and execution timestamps before IC or backtests. |
| Execution timing audit | bundled `execution_timing_audit.py`, exchange calendars, signal/return-window timestamp tables | custom R/Python, SQL timestamp checks | Check signal, rebalance, execution, and forward-return window order before IC, regressions, sorted portfolios, or backtests. |
| Tradability audit | bundled `tradability_audit.py`, exchange market-state feeds, halt/suspension tables, borrow locates, price-limit data | custom R/Python, SQL market-state checks | Check that simulated trades were not in halted, suspended, zero-volume, limit-locked, non-borrowable, or stale-price rows before accepting IC or backtests. |
| Factor IC / rank IC | bundled `factor_ic_report.py`, pandas groupby/corr | `data.table`, `dplyr`, `PerformanceAnalytics` | Confirm point-in-time signal and forward-return alignment before interpreting IC. |
| Factor quantile tests | bundled `factor_quantile_report.py`, pandas groupby/qcut | `data.table`, `dplyr` | Add neutralization, transaction costs, and capacity checks before claiming tradability. |
| Factor decay | bundled `factor_decay_report.py`, pandas groupby/corr | `data.table`, `dplyr` | Each horizon must be computed from executable future returns without overlap mistakes. |
| Factor turnover | bundled `factor_turnover_report.py`, pandas groupby/rank | `data.table`, `dplyr` | High turnover usually requires cost and liquidity sensitivity analysis. |
| Signal overlap / redundancy | bundled `signal_overlap_report.py`, factor library correlation dashboards | `data.table`, `dplyr`, custom R | High pairwise rank correlation or top-name overlap means signals may not add independent breadth. |
| Incremental alpha diagnostics | bundled `incremental_alpha_report.py`, cross-sectional OLS, partial correlation | `lm`, `fixest`, `data.table`, custom R | Test a candidate signal only against a predeclared base set; raw IC is not incremental evidence. |
| Factor neutralization | bundled `factor_neutralization.py`, pandas/statsmodels cross-sectional regression | `fixest`, `data.table`, `dplyr` | Neutralize within each timestamp; avoid full-sample transforms. |
| Portfolio weight backtest | bundled `portfolio_backtest.py`, vectorbt/backtrader/Zipline | `PerformanceAnalytics`, `PortfolioAnalytics` | Document whether weights are beginning-of-period, close-to-close, or next-open executable. |
| Transaction cost diagnostics | bundled `transaction_cost_report.py`, vectorbt/backtrader/custom simulator | `PerformanceAnalytics`, custom R | Include commissions, spread, slippage, borrow, financing, market impact, and ADV participation where possible. |
| Covariance/correlation diagnostics | bundled `covariance_report.py`, pandas/numpy covariance, PyPortfolioOpt risk models | `cov`, `PerformanceAnalytics` | Use shrinkage or factor covariance before large-universe optimization. |
| EWMA volatility | bundled `ewma_volatility.py`, `arch`, pandas `ewm` | `TTR`, `rugarch` | Decay and frequency choices control responsiveness. |
| Rolling beta | bundled `rolling_beta.py`, `statsmodels.regression.rolling.RollingOLS` | `roll`, `zoo`, `PerformanceAnalytics` | Use for exposure stability and benchmark attribution, not alpha proof. |
| Cross-sectional return regression | bundled `cross_sectional_return_regression.py`, `statsmodels.OLS` | `lm`, `fixest` | Use point-in-time characteristics and forward returns; pooled t-stats are only first-pass diagnostics. |
| Fama-MacBeth regression | bundled `fama_macbeth_regression.py`, `linearmodels`, custom statsmodels workflow | `plm`, `fixest`, custom `lm` by date | Use HAC/clustered errors for serious inference, especially with overlapping returns. |
| Newey-West/HAC regression | bundled `newey_west_regression.py`, `statsmodels` HAC covariance | `sandwich`, `lmtest`, `NeweyWest` | Select lag length from frequency and horizon overlap. |
| Multiple testing / FDR | bundled `multiple_testing_report.py`, `statsmodels.stats.multitest.multipletests` | `p.adjust`, `qvalue` | Controls false positives only for the declared family of tests. |
| Experiment registry audit | bundled `quant_experiment_audit.py`, experiment tracking tables | custom R/Python | Audits whether the tested family, failed trials, selected variants, final tests, and data/code versions are recorded before gates. |
| Bootstrap reality check | bundled `bootstrap_reality_check.py`, block bootstrap/custom White Reality Check | `boot`, `tseries`, custom R | Include the whole searched strategy family to reduce data-snooping bias. |
| Alpha research gate | bundled `alpha_research_gate_report.py`, JSON diagnostics, checklist/gate workflow | custom R/Python | Predeclare required diagnostics and thresholds before reviewing a candidate alpha package. |
| Walk-forward stability | bundled `walk_forward_stability.py`, custom rolling validation workflow | `rsample`, custom R | Separates parameter-selection rule stability from single best backtest performance. |
| Optimizer sensitivity | bundled `optimizer_sensitivity_report.py`, PyPortfolioOpt/custom simulations | `PortfolioAnalytics`, `quadprog` | Stress expected returns and covariance before accepting optimized weights. |
| Portfolio construction gate | bundled `portfolio_construction_gate_report.py`, JSON diagnostics, portfolio review workflow | custom R/Python | Predeclare construction thresholds before reviewing weights; this gate is separate from production go-live approval. |
| Long/short signal portfolio | bundled `long_short_backtest.py`, vectorbt/backtrader/Zipline | `PerformanceAnalytics`, custom R | Add exposure neutrality, costs, borrow, liquidity, and capacity before claiming tradability. |
| Portfolio exposure aggregation | bundled `portfolio_exposure_report.py`, risk model exposure tools | `data.table`, `dplyr`, `PortfolioAnalytics` | Check style, beta, sector, country, currency, and concentration exposure over time. |
| Performance attribution | bundled `performance_attribution_report.py`, Brinson/custom attribution | `PerformanceAnalytics`, `pa`, custom R | Reconcile asset/group contributions to portfolio return before explaining performance. |
| Risk contribution | bundled `risk_contribution_report.py`, risk parity/risk budget tooling | `PortfolioAnalytics`, custom R | Component risk contribution depends on the covariance estimate and leverage convention. |
| Capacity and market impact | bundled `capacity_impact_report.py`, custom execution/TCA model | custom R/Python, broker TCA | Use ADV participation and calibrated impact assumptions before scale claims. |
| Execution slippage | bundled `execution_slippage_report.py`, broker TCA/order analytics | custom R/Python, broker TCA | Positive side-aware slippage is implementation shortfall; decision price must be defined before order release. |
| Risk forecast calibration | bundled `risk_forecast_calibration.py`, VaR backtesting, volatility forecast evaluation | `rugarch`, custom R | Standardized returns and VaR breaches test forecast scale, not full tail-model correctness. |
| Model risk register audit | bundled `model_risk_register_report.py`, model inventory/governance tables | custom R/Python | Checks owners, risk tiers, independent validation, approvals, review cadence, monitoring, rollback, kill-switch, versions, and waivers. |
| Regime robustness | bundled `regime_robustness_report.py`, custom state labels, HMM/regime-switching tools | `MSwM`, custom R | Regime labels must be point-in-time and should not be fitted on the evaluation outcome. |
| Live-vs-paper monitoring | bundled `live_vs_paper_report.py`, custom reconciliation reports | custom R/Python | Compare identical timestamps and timing conventions before attributing live drift. |
| Signal health monitoring | bundled `signal_health_monitor.py`, IC monitoring dashboards | custom R/Python | Track signal coverage, rank IC, turnover, and recent decay independently from portfolio PnL. |
| Go-live gate review | bundled `go_live_gate_report.py`, checklist/status workflows | custom R/Python | Use a documented checklist with severity, owner, and evidence before production approval. |
| Order exception monitoring | bundled `order_exception_report.py`, OMS/EMS order logs | custom R/Python, broker exports | Rejections and partial fills are production failures even when slippage on completed fills looks normal. |
| Data freshness monitoring | bundled `data_freshness_report.py`, ETL/data quality jobs | custom R/Python, orchestration checks | Stale or incomplete data should block signal generation and order release. |
| Limit breach monitoring | bundled `limit_breach_report.py`, risk/ops dashboards | custom R/Python | Severity, direction, owner, and consecutive breaches control escalation. |
| Strategy action decision | bundled `strategy_action_decision.py`, policy/rules engines | custom R/Python | Predeclare thresholds and actions before reviewing live outcomes. |
| Checklist template generation | bundled `quant_checklist_template.py`, checklist/status workflows | custom R/Python | Generate CSV/Markdown/JSON templates for go-live, monitoring, and retirement reviews. |
| Diagnostics aggregation | bundled `quant_report_aggregator.py`, report assembly jobs | custom R/Python | Combine JSON diagnostics into a review index without replacing source reports. |
| Committee review pack | bundled `quant_review_pack.py`, Markdown/JSON report assembly | custom R/Python | Produces role-aware decision materials; source diagnostics remain authoritative. |
| Portfolio constraint checks | bundled `portfolio_constraint_check.py`, optimizer/pretrade risk checks | `PortfolioAnalytics`, custom R | Surface leverage, concentration, category, and turnover breaches by date. |
| PCA/statistical risk factors | `sklearn.decomposition.PCA`, `statsmodels.multivariate.PCA` | `prcomp`, `FactoMineR` | Components may not be economically interpretable. |
| Factor analysis | `statsmodels.multivariate.factor.Factor` | `psych::fa`, `factanal` | Validate factor count, rotation, and stability. |
| Asset-pricing panels | `linearmodels`, `statsmodels`, custom Fama-MacBeth | `plm`, `fixest` | Cluster/HAC standard errors are usually needed. |
| Volatility modeling | `arch.arch_model` | `rugarch`, `fGarch` | Match mean, volatility, and error distribution choices. |
| Portfolio optimization | PyPortfolioOpt `EfficientFrontier`, `BlackLittermanModel`, risk models | `PortfolioAnalytics`, `quadprog` | Optimizers are highly sensitive to expected returns/covariance. |
| Cointegration/pairs | bundled `pairs_spread_report.py`, `statsmodels.tsa.stattools`, `VAR`, `VECM` | `urca`, `vars` | Hedge ratios and tests must be fit out-of-sample. |
| Event studies | bundled `event_study_report.py`, statsmodels/custom workflow | `eventstudies`, `fixest` | Event timing, overlapping windows, and benchmark model matter. |

## Implementation Rules

- Use `statsmodels`, R, or Bayesian libraries when inference, coefficients, uncertainty, or tests are central.
- Use `scikit-learn` pipelines when predictive workflow and preprocessing reliability are central.
- Use specialized libraries only after the data structure demands them: survival, panel, causal, spatial, graph, recommendation, or deep learning.
- Record package versions when reporting results.
- Do not include code unless the user asks for code or provides data/code to modify.
