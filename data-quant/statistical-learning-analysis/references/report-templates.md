# Statistical Learning Report Templates

Use these outlines when the user asks for a written analysis plan, report, or final deliverable. Keep sections concise and evidence-based.

## Method Recommendation Report

1. **Problem framing**: unit, target, population, prediction/causal/inferential goal.
2. **Data structure**: target type, sample size, features, time/group/spatial dependence, missingness, imbalance.
3. **Candidate methods**: ranked table with method, core idea, fit to scenario, assumptions, avoid conditions.
4. **Validation design**: split strategy, metrics, leakage controls.
5. **Diagnostics**: assumption checks, residuals/calibration/stability, subgroup analysis.
6. **Recommendation**: baseline plus primary method and backup.
7. **Risks and next data needed**: confounding, measurement, missingness, insufficient sample size, deployment drift.

## Model Comparison Report

1. **Experimental design**: training/validation/test or CV structure.
2. **Preprocessing boundary**: what is fit inside folds.
3. **Models compared**: baseline, interpretable model, flexible model.
4. **Metrics**: primary and secondary metrics with rationale.
5. **Results table**: mean, uncertainty, segment/horizon results.
6. **Diagnostics**: calibration, errors, residuals, stability.
7. **Decision**: chosen model, threshold if any, operational implications.

## Causal Inference Report

1. **Estimand**: treatment, outcome, unit, timing, population, effect scale.
2. **Identification**: DAG or design argument; assumptions.
3. **Data checks**: overlap, balance, missingness, treatment timing, attrition.
4. **Estimator**: method and why it matches the design.
5. **Robustness**: sensitivity, placebo, pre-trend, instrument/cutoff checks as relevant.
6. **Results**: point estimate, uncertainty, practical significance.
7. **Limits**: unmeasured confounding, interference, generalizability.

## Forecasting Report

1. **Series definition**: frequency, horizon, hierarchy, target, external regressors.
2. **Backtest design**: rolling/expanding windows and horizon-specific evaluation.
3. **Baselines**: naive and seasonal naive.
4. **Candidate models**: ETS/ARIMA/state-space/ML with lag features.
5. **Accuracy**: horizon-wise metrics and interval coverage.
6. **Diagnostics**: residual autocorrelation, seasonality, drift, changepoints.
7. **Operational plan**: retraining cadence, feature availability, monitoring.

## Survival Analysis Report

1. **Event definition**: origin, event, censoring, follow-up window.
2. **Descriptive survival**: Kaplan-Meier curves and censoring summary.
3. **Regression model**: Cox/AFT/parametric/time-varying method choice.
4. **Diagnostics**: proportional hazards, influential cases, event-per-parameter, calibration.
5. **Results**: survival curves, hazard/time ratios, uncertainty.
6. **Limitations**: censoring mechanism, competing risks, measurement timing.

## Unsupervised Analysis Report

1. **Goal**: visualization, compression, segmentation, anomaly discovery, or latent constructs.
2. **Feature preparation**: scaling, encoding, missingness, distance metric.
3. **Methods**: simple baseline plus alternatives.
4. **Validation**: stability, internal metrics, external/domain review.
5. **Interpretation**: cluster/component profiles and actionability.
6. **Limits**: no ground truth, seed/parameter sensitivity, risk of overinterpretation.
