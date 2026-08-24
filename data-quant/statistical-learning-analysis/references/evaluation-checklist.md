# Evaluation and Diagnostics Checklist

Use this checklist after selecting candidate methods from `method-map.md`.

## 1. Define the estimand or prediction target

- State the unit of analysis, target variable, prediction horizon, and population.
- Mark whether the goal is prediction, association, causal effect, forecasting, segmentation, anomaly detection, or uncertainty quantification.
- Define the baseline model before complex models.
- Define what error is costly: false positives, false negatives, overprediction, underprediction, late detection, or biased estimates.

## 2. Choose the split strategy

| Data structure | Split strategy |
| --- | --- |
| IID tabular classification/regression | Train/validation/test or cross-validation; stratify classification labels when needed. |
| Imbalanced classification | Stratified CV; preserve rare class in every fold; resample only inside training folds. |
| Grouped data | GroupKFold or held-out groups; keep all rows from a subject/site/store/user in the same fold. |
| Time series | Rolling-origin, expanding-window, sliding-window, or blocked validation; no random shuffle. |
| Survival data | Split by subject; preserve censoring structure; use survival-specific metrics. |
| Causal inference | Prefer design-based holdouts where useful, but prioritize identification, balance, overlap, and robustness checks over predictive split alone. |
| Small data | Repeated CV, bootstrap intervals, nested CV for model selection; report uncertainty. |

## 3. Select metrics by target type

| Target/problem | Metrics |
| --- | --- |
| Continuous regression | RMSE for large errors, MAE for robust typical error, R-squared for explained variation, pinball loss for quantiles. |
| Binary classification | ROC-AUC, PR-AUC for rare positives, log loss, Brier score, precision, recall, F1, sensitivity/specificity, calibration. |
| Multiclass classification | Macro/micro F1, balanced accuracy, multiclass log loss, confusion matrix, top-k accuracy when relevant. |
| Imbalanced classification | PR-AUC, recall at fixed precision, precision at fixed recall, balanced accuracy, expected cost, threshold-specific metrics. |
| Probabilistic prediction | Log loss, Brier score, calibration curve, expected calibration error, reliability diagrams. |
| Clustering | Silhouette, Davies-Bouldin, Calinski-Harabasz, stability, domain review; adjusted Rand/NMI if labels exist. |
| Forecasting | MAE/RMSE by horizon, MAPE/sMAPE with caution near zero, MASE, pinball loss for prediction intervals, coverage. |
| Survival | C-index, time-dependent AUC, integrated Brier score, calibration over time, survival curve checks. |
| Causal effect | Point estimate, confidence/credible interval, balance diagnostics, overlap, sensitivity/refutation, placebo/pre-trend tests when applicable. |
| Ranking/search | NDCG, MAP, MRR, precision@k, recall@k, click/conversion guardrails, query/user-level holdouts. |
| Recommendation | Hit rate@k, recall@k, NDCG@k, coverage, novelty/diversity, calibration, time-aware offline validation, online A/B tests. |
| Panel/longitudinal | Cluster-robust uncertainty, within/between fit, serial correlation checks, entity/time fixed-effect sensitivity. |
| Spatial/graph | Spatial blocked CV, Moran's I/residual spatial autocorrelation, link-prediction AUC/AP, community stability, leakage-aware graph splits. |

## 4. Diagnose assumptions and failure modes

- Linear/GLM: residual patterns, heteroskedasticity, influential points, link function, overdispersion, collinearity, separation.
- Penalized models: coefficient stability, selected features across folds, penalty path, standardization.
- Trees/ensembles: learning curves, feature leakage, calibration, monotonicity/domain constraints, extrapolation failure.
- SVM/kernels/GPR: scaling, kernel choice, hyperparameter sensitivity, computational cost.
- Neural networks: data volume, leakage, regularization, early stopping, calibration, seed sensitivity.
- Clustering: distance metric, feature scaling, stability under resampling, domain coherence, cluster count sensitivity.
- Dimensionality reduction: variance explained, reconstruction error, loading interpretation, out-of-sample transform behavior.
- Time series: stationarity, seasonality, autocorrelation, residual whiteness, forecast horizon degradation, exogenous regressor availability.
- Survival: censoring assumptions, proportional hazards, time-varying effects, competing risks if relevant.
- Causal: DAG/identification, overlap/common support, balance, instrument validity, parallel trends, manipulation at cutoff, interference.
- Bayesian: prior sensitivity, posterior predictive checks, convergence diagnostics, effective sample size, divergent transitions.
- Panel/econometric: entity/time effects, endogeneity, weak instruments, serial correlation, clustered errors, instrument proliferation.
- Ranking/recommendation: user/query leakage, popularity bias, cold start, position bias, exposure bias, offline-online metric mismatch.
- Spatial/graph: dependence between neighboring nodes/regions, graph construction, transductive leakage, spatial autocorrelation in residuals.
- Deep learning: representation leakage, data augmentation leakage, distribution shift, calibration, seed sensitivity, compute constraints.

## 5. Prevent leakage

- Fit scalers, encoders, imputers, feature selectors, target encoders, resamplers, calibrators, and dimensionality reducers only on training folds.
- Build target-dependent features using only information available at prediction time.
- For time series, compute lags and rolling statistics from the past only.
- For grouped data, prevent duplicates, repeated subjects, or near-identical records from crossing fold boundaries.
- For text or categorical target encoding, learn vocabulary/encoding inside each training fold.
- For recommendation/ranking, split by user/query/session/time according to the deployment question.
- For graph learning, ensure test edges/nodes are not encoded through training-time graph construction unless the deployment setting is transductive and explicitly stated.
- For spatial data, avoid random splits when nearby observations make the test set too similar to training locations.

## 6. Compare models

- Compare every candidate against a simple baseline.
- Use the same split, preprocessing boundaries, and metric definitions across candidates.
- Prefer nested CV when the reported performance is used for model choice and hyperparameter tuning.
- Report mean and uncertainty across folds, not only the best fold.
- Inspect practical significance, not only statistical significance.

## 7. Report results

Include:

- Problem type and data assumptions.
- Ranked method recommendations with applicability scenarios and caveats.
- Validation design and metrics.
- Diagnostic results and known weaknesses.
- Interpretation at the right level: coefficients/effects for inferential models, feature importance or partial effects for predictive models, survival curves/hazard ratios for survival, causal estimands and assumptions for causal models.
- Reproducibility details: split seed, package versions, preprocessing, hyperparameters, and final model selection rule.

## 8. Escalate when needed

- Ask for domain input when the causal graph, cost matrix, event definition, censoring mechanism, or acceptable error tradeoff is unclear.
- Recommend collecting more data when the model family needs support the data cannot provide.
- Recommend an experiment when the user needs causal evidence and observational assumptions are weak.
- Recommend a simpler model when interpretability, compliance, or operational stability matters more than marginal accuracy.
