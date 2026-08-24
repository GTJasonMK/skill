# Statistical Learning Anti-Patterns

Use this file when reviewing a plan, code, notebook, or model report. If any anti-pattern appears, name it and give the correction.

## Leakage

| Anti-pattern | Why it is wrong | Correction |
| --- | --- | --- |
| Scale, impute, select features, or reduce dimensions on the full dataset before splitting. | Test data informs training transformations. | Put preprocessing inside CV/pipeline folds. |
| Target encoding before cross-validation. | Category encodings contain validation/test target information. | Use fold-aware target encoding. |
| Time series random split. | Future information leaks into training. | Use blocked or rolling-origin validation. |
| Grouped observations split by rows. | Same subject/user/site can appear in train and test. | Use group-aware splits. |
| Graph embeddings computed on full graph before edge/node split. | Test relationships can influence training representations. | Use inductive split or explicitly state transductive setting. |

## Misframed Claims

| Anti-pattern | Why it is wrong | Correction |
| --- | --- | --- |
| Calling predictive feature importance causal. | Prediction uses associations, not interventions. | Use causal design, DAG, and identification checks. |
| Treating SHAP/PDP as causal explanation. | Model explanations inherit observational confounding. | Phrase as model behavior unless causal assumptions are met. |
| Inferring causality from VAR/lag predictability. | Temporal precedence is not sufficient. | Use causal time-series design or domain identification. |
| Reporting adjusted regression as policy effect without assumptions. | Model adjustment alone does not prove no confounding. | State causal assumptions or downgrade to association. |

## Metrics and Validation

| Anti-pattern | Why it is wrong | Correction |
| --- | --- | --- |
| Accuracy-only imbalanced classification. | Majority-class performance hides rare-class failure. | Use PR-AUC, recall/precision, cost curves, calibration. |
| Choosing threshold on the test set. | Test set becomes part of model selection. | Tune threshold on validation data. |
| Reporting best fold or best validation run. | Inflates performance by selection. | Report mean/interval and final untouched test if available. |
| No naive baseline for forecasting. | Complex models may not beat simple persistence/seasonality. | Always include naive and seasonal naive baselines. |
| No nested CV after heavy tuning. | Model-selection bias contaminates performance estimate. | Use nested CV or final holdout. |

## Model Assumption Failures

| Anti-pattern | Why it is wrong | Correction |
| --- | --- | --- |
| OLS with strong nonlinear residual structure. | Linear mean model is misspecified. | Add transformations, splines/GAM, interactions, or flexible models. |
| Poisson count model with overdispersion. | Standard errors and mean-variance fit are wrong. | Use negative binomial, quasi-Poisson, robust SE, or zero-inflated models. |
| Cox model without proportional hazards check. | Hazard ratio may vary over time. | Check PH diagnostics; use stratified/time-varying models. |
| K-means on unscaled mixed-unit features. | Large-scale variables dominate distances. | Scale/encode appropriately or choose a suitable distance/model. |
| t-SNE/UMAP plot used as proof. | Visualization can fabricate apparent clusters. | Use stability, external validation, and domain review. |

## Reporting and Reproducibility

| Anti-pattern | Why it is wrong | Correction |
| --- | --- | --- |
| Method chosen after seeing all results, with no selection rule. | Researcher degrees of freedom are hidden. | Report selection procedure and alternatives considered. |
| P-values after many tests without adjustment. | False discoveries accumulate. | Use FDR/FWER or mark as exploratory. |
| No data dictionary or target timing. | Target leakage and misinterpretation are likely. | Define unit, target, time, eligibility, and features. |
| No seed/version/preprocessing record. | Results are not reproducible. | Record seed, package versions, transformations, and split logic. |
| Only global performance reported. | Model may fail on important subgroups. | Report segment/time/group performance where relevant. |
