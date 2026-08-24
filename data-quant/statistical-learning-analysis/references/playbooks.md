# Statistical Learning Playbooks

Use these playbooks to turn common user requests into complete analysis plans. Pair them with `decision-tree.md`, `method-map.md`, `principles.md`, and `evaluation-checklist.md`.

## Contents

- [Continuous Prediction](#continuous-prediction)
- [Binary or Multiclass Classification](#binary-or-multiclass-classification)
- [Imbalanced Classification](#imbalanced-classification)
- [Causal Effect or Policy Impact](#causal-effect-or-policy-impact)
- [Time Series Forecasting](#time-series-forecasting)
- [Survival or Duration Analysis](#survival-or-duration-analysis)
- [Unsupervised Segmentation](#unsupervised-segmentation)
- [High-Dimensional Small-Sample Analysis](#high-dimensional-small-sample-analysis)
- [Panel or Longitudinal Data](#panel-or-longitudinal-data)
- [Recommendation or Ranking](#recommendation-or-ranking)

## Continuous Prediction

Use when the target is numeric and the user wants prediction.

| Step | Action |
| --- | --- |
| Questions | What is the prediction horizon? Are observations IID, grouped, spatial, or temporal? Which error is costly? |
| Baselines | Mean/median baseline; OLS/regularized linear model. |
| Candidates | Ridge/Lasso/Elastic Net, GAM/splines, random forest, gradient boosting, SVR/GPR for moderate nonlinear data. |
| Validation | IID CV, grouped CV, or rolling-origin depending on data dependence. |
| Metrics | MAE, RMSE, R-squared, pinball loss for quantiles. |
| Diagnostics | Residual plots, outlier influence, heteroskedasticity, learning curves, calibration of prediction intervals if used. |
| Report | Error by segment, important predictors, model limits, production leakage checks. |

## Binary or Multiclass Classification

| Step | Action |
| --- | --- |
| Questions | Are probabilities or hard labels needed? Are classes imbalanced? What are false-positive/false-negative costs? |
| Baselines | Majority class; logistic/penalized logistic; naive Bayes for sparse text. |
| Candidates | Random forest, gradient boosting, linear/kernel SVM, neural nets for large/unstructured data. |
| Validation | Stratified CV; grouped/time-aware splits when needed. |
| Metrics | ROC-AUC, PR-AUC, log loss, Brier score, F1, recall/precision, confusion matrix. |
| Diagnostics | Calibration curve, threshold curve, class-wise errors, subgroup performance. |
| Report | Operating threshold and reason; cost tradeoff; probability reliability. |

## Imbalanced Classification

| Step | Action |
| --- | --- |
| Questions | What is the rare class? What recall/precision is acceptable? Are labels reliable? |
| Baselines | Prevalence baseline; class-weighted logistic regression. |
| Candidates | Class weights, resampling inside CV, balanced random forest, gradient boosting with class weights, anomaly detection only if positive labels are absent or weak. |
| Validation | Stratified folds; resample only inside training folds; keep a final untouched test set. |
| Metrics | PR-AUC, recall at fixed precision, precision at fixed recall, expected cost, calibration. |
| Diagnostics | Threshold sensitivity, false positive review, label noise audit. |
| Report | Chosen operating point; expected workload; rare-class confidence limits. |

## Causal Effect or Policy Impact

| Step | Action |
| --- | --- |
| Questions | What are treatment, outcome, unit, timing, estimand, and confounders? Is there randomization or quasi-experiment? |
| Baselines | Descriptive pre/post and treated/control comparisons without causal overclaim. |
| Candidates | RCT analysis, regression adjustment, matching/IPW, doubly robust, DiD, IV, RD, interrupted time series, causal forests for heterogeneity. |
| Validation | Balance/overlap, pre-trends, placebo outcomes, weak instrument checks, cutoff manipulation, sensitivity analysis. |
| Metrics | Effect estimate, CI/credible interval, standardized mean differences, robustness results. |
| Diagnostics | DAG/identification, missing confounders, interference, attrition, spillovers. |
| Report | State assumptions before estimates; separate identification from estimation. |

## Time Series Forecasting

| Step | Action |
| --- | --- |
| Questions | Frequency, horizon, seasonality, external regressors, known future covariates, forecast granularity. |
| Baselines | Naive and seasonal naive. |
| Candidates | ETS, ARIMA/SARIMA/SARIMAX, state-space, VAR/VECM, dynamic regression, ML with lag/rolling features. |
| Validation | Rolling-origin or expanding-window; evaluate by forecast horizon. |
| Metrics | MAE, RMSE, MASE, sMAPE with caution near zero, interval coverage. |
| Diagnostics | Residual autocorrelation, stationarity, seasonality, drift, backtest stability. |
| Report | Horizon-wise accuracy, prediction intervals, covariate availability, retraining cadence. |

## Survival or Duration Analysis

| Step | Action |
| --- | --- |
| Questions | What is event, origin time, censoring rule, follow-up end, competing risks, time-varying covariates? |
| Baselines | Kaplan-Meier by key groups; log-rank where appropriate. |
| Candidates | Cox PH, stratified Cox, AFT, parametric survival, time-varying Cox, survival forests/boosting for prediction. |
| Validation | Subject-level splits; survival-specific metrics; censoring-aware diagnostics. |
| Metrics | C-index, integrated Brier score, time-dependent AUC, calibration over time. |
| Diagnostics | Proportional hazards, censoring mechanism, influential observations, event count per parameter. |
| Report | Survival curves, hazard/time ratios, censoring caveats, time horizon of validity. |

## Unsupervised Segmentation

| Step | Action |
| --- | --- |
| Questions | Is the goal compression, visualization, segmentation, anomaly discovery, or latent constructs? Which distance is meaningful? |
| Baselines | PCA visualization; simple K-means after scaling if numeric. |
| Candidates | Hierarchical clustering, GMM, DBSCAN/HDBSCAN, spectral clustering, factor analysis, NMF/topic models for nonnegative/text. |
| Validation | Stability under resampling, silhouette/DB indices, domain review, external labels if available. |
| Diagnostics | Scaling sensitivity, cluster size balance, feature dominance, seed sensitivity. |
| Report | Cluster profiles and actionability; do not claim clusters are natural ground truth. |

## High-Dimensional Small-Sample Analysis

| Step | Action |
| --- | --- |
| Questions | Are features generated before outcomes? Are there batches/sites? What is the final inferential or predictive target? |
| Baselines | Penalized linear/logistic model; simple feature screening inside CV. |
| Candidates | Ridge/Lasso/Elastic Net, PLS, PCA inside CV, linear SVM, Bayesian shrinkage. |
| Validation | Nested CV or bootstrap; all screening and preprocessing inside folds. |
| Metrics | Match target type; report uncertainty due to small `n`. |
| Diagnostics | Selection stability, batch effects, leakage from normalization, multiplicity. |
| Report | Emphasize uncertainty and avoid overclaiming selected markers/features. |

## Panel or Longitudinal Data

| Step | Action |
| --- | --- |
| Questions | What are entity, time, treatment/exposure timing, within/between variation, and dependence structure? |
| Baselines | Pooled model with clustered SE; fixed effects if within variation matters. |
| Candidates | Fixed effects, random effects, first differences, mixed models, GEE, DiD, panel IV/GMM. |
| Validation | Group/time-aware split for prediction; clustered/robust inference for explanation. |
| Metrics | Prediction metrics by entity/time; inferential SE and robustness checks. |
| Diagnostics | Serial correlation, entity/time effects, weak instruments, parallel trends if causal. |
| Report | Separate within-entity from between-entity interpretation. |

## Recommendation or Ranking

| Step | Action |
| --- | --- |
| Questions | Is the target rating, click, purchase, next item, or ordered relevance? Are data implicit or explicit? |
| Baselines | Popularity, recency, simple content filters. |
| Candidates | Matrix factorization, collaborative filtering, learning-to-rank, gradient boosting rankers, two-stage retrieval/ranking, GNNs for graph-rich data. |
| Validation | Time/user/session-aware splits; avoid exposing future interactions. |
| Metrics | NDCG@k, MAP, MRR, recall@k, coverage, diversity, online A/B guardrails. |
| Diagnostics | Cold start, popularity bias, position bias, exposure bias, calibration. |
| Report | Offline/online mismatch and business constraints. |
