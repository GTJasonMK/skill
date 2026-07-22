# Statistical Learning Decision Tree

Use this file before `method-map.md` when the request is vague or the data/task type is not yet clear.

## 1. Start with the claim type

| User wants | Route first | Do not confuse with |
| --- | --- | --- |
| "Predict", "classify", "score", "forecast next" | Predictive modeling | Causal effect estimation |
| "Explain which variables matter" | Interpretable modeling plus diagnostics | Causal attribution unless design supports it |
| "Estimate effect of X", "impact", "policy", "intervention" | Causal inference | Ordinary prediction or correlation |
| "Group", "segment", "discover structure" | Unsupervised learning | Supervised classification |
| "Detect abnormal cases" | Anomaly/density methods | Rare-class classification if labels exist |
| "Time until event", "churn time", "survival" | Survival analysis | Ordinary binary classification |
| "Future values over time" | Forecasting/time series | Randomly split tabular regression |
| "Recommend", "rank", "next item" | Recommendation/ranking | Standard multiclass classification |

## 2. Identify the target or absence of target

| Target/data shape | First candidate families |
| --- | --- |
| No target label | Clustering, dimensionality reduction, factor/topic models, anomaly detection |
| Continuous numeric target | OLS/GLM baseline, regularized regression, GAM/splines, tree ensembles, SVR/GPR, neural nets |
| Binary target | Logistic baseline, penalized logistic, tree ensembles, SVM, calibrated boosting, cost-sensitive methods |
| Multiclass target | Multinomial logistic, trees/ensembles, SVM, neural nets; macro metrics if imbalance exists |
| Ordered categories | Ordinal logit/probit, cumulative link models, ordinal-aware metrics |
| Count outcome | Poisson, negative binomial, zero-inflated/hurdle, count boosting when prediction dominates |
| Proportion/rate | Binomial GLM with denominator, beta regression for continuous proportions, offsets/exposure |
| Time-to-event with censoring | Kaplan-Meier, Cox PH, AFT, time-varying survival models, survival forests |
| Multivariate outcomes | MANOVA/MANCOVA, multivariate regression, CCA, multioutput models |

## 3. Check design constraints

| Constraint | Routing implication |
| --- | --- |
| Time order matters | Use rolling/blocked validation; prefer forecasting/time-aware features |
| Repeated entities/groups | Use grouped CV, mixed models, GEE, fixed/random effects, cluster-robust SE |
| Treatment/intervention question | Draw causal graph; check identification before model fitting |
| High-dimensional `p >> n` | Regularization, dimension reduction inside CV, sparse models, nested CV |
| Severe imbalance | PR-AUC, class weights/resampling inside folds, threshold/cost analysis |
| Missingness is nontrivial | Diagnose missingness; use fold-safe imputation or multiple imputation |
| Spatial/network dependence | Use spatial/graph-aware validation; avoid random IID assumptions |
| Need coefficients/intervals | Prefer statsmodels/R/inferential models; avoid black-box-only answer |
| Need deployment scoring | Prefer pipelines, calibration, drift monitoring, latency/robustness checks |

## 4. Choose the analysis lane

### Predictive lane

1. Establish a naive/domain baseline.
2. Fit an interpretable baseline.
3. Add a stronger flexible model if justified.
4. Tune only inside validation folds.
5. Calibrate/threshold if decisions use probabilities.
6. Report performance, uncertainty, failure modes, and deployment caveats.

### Inferential lane

1. Define estimand and population.
2. Choose model family matching outcome distribution and dependence.
3. Check assumptions and residuals.
4. Use robust/clustered uncertainty when needed.
5. Avoid causal language unless identification is explicit.

### Causal lane

1. Define treatment, outcome, unit, timing, estimand.
2. State assumptions with a DAG or design argument.
3. Check overlap, balance, trends, instrument strength, cutoff manipulation, or randomization integrity depending on design.
4. Estimate with transparent and robust alternatives.
5. Run sensitivity/refutation/placebo checks.

### Unsupervised lane

1. Decide whether the goal is compression, visualization, segmentation, anomaly discovery, or latent constructs.
2. Scale/encode features based on distance or likelihood assumptions.
3. Use stability checks and domain review.
4. Do not treat discovered structure as ground truth without external validation.

## 5. Stop conditions before recommending a method

Ask for more context or state assumptions when:

- The target variable is unknown.
- Causal timing is ambiguous.
- Forecast horizon and data frequency are missing.
- Group/time/spatial leakage risk is likely but structure is unclear.
- Cost of errors determines the metric but no cost preference is given.
- The user asks for implementation but the data format or language ecosystem is unknown.
