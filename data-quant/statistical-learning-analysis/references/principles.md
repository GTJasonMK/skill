# Statistical Learning Method Principles

Use this reference when the user asks how a method works, why it is appropriate, or why one method is preferable to another. Keep explanations concise: state the mechanism, the assumptions it trades on, and the misuse to avoid.

## Contents

- [How to Explain a Method](#how-to-explain-a-method)
- [Regression and GLM Principles](#regression-and-glm-principles)
- [Classification Principles](#classification-principles)
- [Tree and Ensemble Principles](#tree-and-ensemble-principles)
- [Unsupervised Learning Principles](#unsupervised-learning-principles)
- [Anomaly and Density Principles](#anomaly-and-density-principles)
- [Time Series Principles](#time-series-principles)
- [Survival Principles](#survival-principles)
- [Causal Inference Principles](#causal-inference-principles)
- [Bayesian Principles](#bayesian-principles)
- [Panel, Multivariate, and Econometric Principles](#panel-multivariate-and-econometric-principles)
- [Ranking, Recommendation, Spatial, and Graph Principles](#ranking-recommendation-spatial-and-graph-principles)
- [Deep and Representation Learning Principles](#deep-and-representation-learning-principles)
- [Preprocessing, Selection, and Interpretation Principles](#preprocessing-selection-and-interpretation-principles)

## How to Explain a Method

For any method, answer in this order:

1. **Core idea**: What objective or structure does it exploit?
2. **What it buys**: Interpretability, flexibility, variance reduction, bias reduction, uncertainty, causal identification, or scalability.
3. **Main assumption or cost**: Linearity, independence, exchangeability, stationarity, proportional hazards, no unmeasured confounding, distance meaning, enough data, or compute.
4. **Misuse warning**: The most likely way an analyst would overclaim or leak information.

Do not present a method's mathematical machinery as evidence that its assumptions are true. Validation and design still carry the claim.

## Regression and GLM Principles

| Method/family | 核心思想 / Principle | 关键假设或代价 | 常见误用 |
| --- | --- | --- | --- |
| OLS / linear regression | Fit an additive linear function by minimizing squared residuals. | Linear mean structure, independent errors for simple inference, enough samples, controlled leverage. | Treating coefficients as causal without design; ignoring nonlinear residual patterns. |
| WLS / GLS | Reweight or model error covariance so estimation matches heteroskedastic or correlated error structure. | Weights/covariance model must be meaningful. | Using arbitrary weights without checking what estimand changes. |
| Ridge | Minimize squared error plus an L2 penalty that shrinks coefficients toward zero. | Features should be scaled; shrinkage adds bias to reduce variance. | Calling it feature selection; interpreting coefficient magnitude without scaling. |
| Lasso | Use an L1 penalty to shrink some coefficients exactly to zero. | Sparsity assumption; unstable with highly correlated predictors. | Treating selected features as stable scientific discoveries without resampling stability checks. |
| Elastic Net | Combine L1 and L2 penalties to encourage sparse but more stable solutions. | Penalty mix must be tuned; scaling matters. | Tuning on the test set or using selected variables for post-selection inference naively. |
| Polynomial/features/basis expansion | Convert nonlinear relationships into linear regression over engineered basis functions. | Basis choice controls shape; complexity grows quickly. | High-degree extrapolation and fitting noise as curvature. |
| Splines / GAM | Model smooth nonlinear effects through additive smooth functions. | Additivity unless interactions are included; smoothing controls bias-variance. | Reading smooth partial effects as causal without confounding control. |
| Robust regression | Downweight observations with large residual influence to resist heavy tails/outliers. | Robust to some response outliers, not all bad data mechanisms. | Using it to hide data quality problems instead of diagnosing them. |
| Quantile regression | Estimate conditional quantiles by minimizing asymmetric absolute loss. | Explains distributional positions, not the conditional mean. | Comparing quantile coefficients as if they were mean effects. |
| kNN regression | Predict by averaging nearby training cases under a distance metric. | Distance must be meaningful; local smoothness. | Using unscaled mixed features or high-dimensional noisy features. |
| SVR | Fit a function that ignores small errors inside an epsilon tube while controlling margin/complexity. | Scaling and kernel tuning are central. | Applying kernel SVR to large data without computational checks. |
| Kernel ridge | Fit smooth nonlinear functions through kernels with L2 regularization. | Kernel defines similarity; scales poorly with large `n`. | Treating kernel choice as a minor detail. |
| Gaussian process regression | Place a distribution over functions; infer predictions and uncertainty from a kernel covariance. | Kernel and noise model drive smoothness and uncertainty; cubic scaling in classic GP. | Trusting posterior uncertainty when kernel/misspecification or distribution shift is untested. |
| PLS | Build latent components that explain predictor variation relevant to the response. | Useful under collinearity; component count must be validated. | Interpreting components without checking loadings and stability. |

## Classification Principles

| Method/family | 核心思想 / Principle | 关键假设或代价 | 常见误用 |
| --- | --- | --- | --- |
| Logistic regression | Model log-odds as a linear function and estimate class probabilities. | Linear logit unless features transform it; separation can destabilize estimates. | Reporting accuracy only or interpreting odds ratios causally. |
| Penalized logistic regression | Add regularization to logistic loss to stabilize high-dimensional or sparse classification. | Penalty and scaling affect interpretation. | Selecting penalty after seeing test results. |
| LDA | Use class means and shared covariance to form a linear discriminant rule. | Gaussian-like classes and equal covariance are helpful. | Using it in high dimensions without shrinkage. |
| QDA | Allow each class to have its own covariance, producing quadratic boundaries. | Needs many samples per class. | Applying it when class-specific covariance estimates are noisy. |
| Naive Bayes | Combine feature likelihoods under conditional independence given the class. | Independence assumption is strong but often useful for sparse text/counts. | Treating its raw probabilities as calibrated. |
| kNN classifier | Classify by majority vote among nearest labeled examples. | Distance metric and local label smoothness. | Ignoring class imbalance and feature scaling. |
| Linear SVM | Find a large-margin linear separator. | Good for high-dimensional sparse features; probabilities require calibration. | Using margin scores as probabilities. |
| Kernel SVM | Use kernels to build nonlinear large-margin boundaries. | Kernel and hyperparameters define the geometry; expensive at large scale. | Tuning many kernels without nested validation. |
| Ordinal models | Model ordered categories through thresholds on a latent score. | Order matters; proportional odds may be assumed. | Treating ordered labels as nominal and losing information, or as interval data without justification. |
| Multilabel models | Predict multiple non-exclusive labels, usually through label-wise or structured models. | Label dependence may matter. | Reporting only subset accuracy when label-level performance is important. |
| Calibration | Transform scores into reliable probabilities. | Needs held-out/cross-fitted calibration data. | Calibrating and evaluating on the same test set. |
| Threshold tuning | Choose operating point based on costs or precision/recall constraints. | Threshold is part of model selection. | Reporting tuned threshold performance on the data used to choose it. |

## Tree and Ensemble Principles

| Method/family | 核心思想 / Principle | 关键假设或代价 | 常见误用 |
| --- | --- | --- | --- |
| Decision tree | Recursively split features to create locally homogeneous regions. | Captures interactions; high variance unless constrained. | Reading one unstable tree as a robust scientific rule set. |
| Bagging | Fit many unstable learners on bootstrap samples and average/vote. | Reduces variance most when base learners are unstable. | Expecting it to fix high bias. |
| Random forest | Bagging plus random feature subsets decorrelates trees before averaging. | Strong tabular baseline; less transparent and weak at extrapolation. | Interpreting impurity importance under correlated or high-cardinality features. |
| Extra Trees | Randomize split thresholds/features more aggressively to reduce variance and improve speed. | More randomization can increase bias. | Assuming it is always better than random forest. |
| AdaBoost | Sequentially reweight difficult cases so later weak learners focus on errors. | Can work well with clean labels. | Using it on noisy labels/outliers without robustness checks. |
| Gradient boosting | Sequentially fit learners to residuals/gradients of a loss function. | Powerful bias reduction; requires shrinkage, depth, early stopping. | Letting leakage or overfitting create inflated tabular results. |
| Voting ensemble | Combine predictions from diverse models by hard/soft votes. | Works when errors differ across models. | Soft voting with uncalibrated probability outputs. |
| Stacking / Super Learner | Train a meta-model on out-of-fold predictions from base models. | Cross-fitting prevents leakage. | Training meta-learner on in-sample base predictions. |
| Bayesian model averaging | Average predictions/parameters over plausible models weighted by posterior support. | Requires a defensible model space and priors. | Treating model probabilities as objective when model space is arbitrary. |

## Unsupervised Learning Principles

| Method/family | 核心思想 / Principle | 关键假设或代价 | 常见误用 |
| --- | --- | --- | --- |
| PCA | Find orthogonal linear directions of maximum variance. | Variance is not necessarily signal; scaling matters. | Calling PCA components causal factors or using them outside CV in supervised pipelines. |
| Sparse PCA | Add sparsity to PCA loadings for interpretability. | Optimization and stability are harder. | Overinterpreting unstable sparse components. |
| Kernel PCA | Perform PCA in an implicit nonlinear feature space. | Kernel defines nonlinear structure. | Using it without out-of-sample validation. |
| Factor analysis | Explain covariance through latent factors plus measurement noise. | A latent variable model; rotation and factor count matter. | Treating factors as real constructs without domain validation. |
| ICA | Separate observed mixtures into statistically independent sources. | Source independence and preprocessing are central. | Applying it when independence is not plausible. |
| NMF | Decompose nonnegative data into additive nonnegative parts. | Inputs must be nonnegative; parts-based representation. | Comparing components across runs without stability checks. |
| Topic models | Represent documents as mixtures of latent topics and topics as word distributions. | Bag-of-words assumptions; topics need human interpretation. | Treating topic labels as objective ground truth. |
| t-SNE | Preserve local neighborhoods for visualization. | Visualization depends on perplexity, seed, and preprocessing. | Interpreting cluster sizes or global distances as quantitative evidence. |
| UMAP | Learn a low-dimensional embedding preserving neighborhood graph structure. | Hyperparameters control local/global tradeoff. | Using a 2D plot as proof of class separability. |
| K-means | Minimize within-cluster squared distances around centroids. | Prefers spherical equal-variance clusters and numeric Euclidean features. | Choosing `k` because the plot looks nice without stability/domain checks. |
| Hierarchical clustering | Build nested clusters by repeatedly merging/splitting using a distance and linkage rule. | Distance/linkage define the result. | Treating a dendrogram as unique structure independent of design choices. |
| GMM | Model data as a mixture of Gaussian distributions with soft memberships. | Elliptical cluster assumptions; component count matters. | Calling mixture components real populations without validation. |
| DBSCAN/HDBSCAN | Identify dense regions separated by sparse regions; label sparse points as noise. | Density and distance metric define clusters. | Using default parameters in high dimensions. |
| Spectral clustering | Cluster using eigenvectors of a similarity graph. | Graph construction is the model. | Ignoring memory/scaling and graph sensitivity. |

## Anomaly and Density Principles

| Method/family | 核心思想 / Principle | 关键假设或代价 | 常见误用 |
| --- | --- | --- | --- |
| Isolation Forest | Anomalies require fewer random splits to isolate. | Assumes anomalies are rare and structurally isolated. | Treating score threshold as objective without contamination/cost choice. |
| One-Class SVM | Learn a boundary around normal data in feature/kernel space. | Training data should mostly represent normal behavior. | Mixing many anomalies into the "normal" training set. |
| LOF | Score points by local density relative to neighbors. | Local neighborhoods must be meaningful. | Comparing scores across regions with very different density structure. |
| Robust covariance | Estimate an outlier-resistant covariance ellipsoid. | Works best for roughly elliptical distributions. | Applying it to multimodal or strongly nonlinear data. |
| KDE | Estimate density by smoothing kernels over observations. | Bandwidth dominates results; high-dimensional density is hard. | Using density estimates in high dimensions without validation. |

## Time Series Principles

| Method/family | 核心思想 / Principle | 关键假设或代价 | 常见误用 |
| --- | --- | --- | --- |
| Naive / seasonal naive | Forecast future values as last observed or last seasonal value. | Baseline, not a full explanatory model. | Skipping it and overvaluing complex models. |
| AR / ARIMA | Model current value as lagged values plus shocks, with differencing for stationarity. | Stationarity after transformation; residuals should be approximately white noise. | Random train/test splits or using future information in features. |
| SARIMA/SARIMAX | Extend ARIMA with seasonal structure and exogenous regressors. | Exogenous variables must be known or forecastable at prediction time. | Including future-known only variables that will not exist in deployment. |
| ETS | Decompose level, trend, and seasonality with exponential smoothing. | Works well for repeated seasonal/trend patterns. | Using it where external drivers dominate. |
| State-space / Kalman | Represent observed series through latent states updated over time. | Model structure defines latent dynamics. | Treating latent components as real without diagnostics. |
| VAR/VECM | Model multiple time series as lagged functions of each other; VECM handles cointegration. | Needs enough time points and stationarity/cointegration checks. | Inferring causality from lag predictability alone. |
| Dynamic factor | Explain many time series through a few latent common factors. | Factor count and interpretation are design choices. | Overinterpreting latent factors without external validation. |
| ML lag features | Turn forecasting into supervised learning using lagged/rolling predictors. | Feature construction must be time-safe. | Computing rolling features with future data leakage. |

## Survival Principles

| Method/family | 核心思想 / Principle | 关键假设或代价 | 常见误用 |
| --- | --- | --- | --- |
| Kaplan-Meier | Estimate survival probability over time while accounting for censoring. | Non-informative censoring assumption. | Comparing curves without considering covariate imbalance. |
| Log-rank test | Compare survival curves using event counts over time. | Most sensitive under proportional hazards. | Using it when hazards cross without further analysis. |
| Cox PH | Model covariate effects multiplicatively on hazard with unspecified baseline hazard. | Proportional hazards is central. | Reporting hazard ratios as risk ratios or ignoring time-varying effects. |
| Stratified Cox | Allow baseline hazards to differ by strata while sharing other covariate effects. | Strata effects are not directly estimated. | Stratifying away a variable whose effect is the scientific target. |
| AFT | Model covariates as accelerating or decelerating event time. | Parametric time distribution often required. | Choosing distribution without checking fit. |
| Time-varying survival models | Let covariates or effects change over follow-up. | Data must be organized by time intervals without future leakage. | Updating covariates using information after the risk time. |

## Causal Inference Principles

| Method/family | 核心思想 / Principle | 关键假设或代价 | 常见误用 |
| --- | --- | --- | --- |
| Randomized experiment | Random assignment breaks confounding in expectation. | Interference, noncompliance, attrition, and sample ratio issues can break interpretation. | Ignoring guardrail metrics or multiple testing. |
| Regression adjustment | Compare outcomes after conditioning on observed covariates. | No unmeasured confounding plus model adequacy for causal interpretation. | Calling adjusted association causal without a causal graph/design. |
| Propensity matching | Match treated/control units with similar treatment probability. | Requires overlap and measured confounders. | Checking match counts but not covariate balance. |
| IPW | Reweight observations to create a pseudo-population with balanced treatment assignment. | Extreme weights increase variance; overlap required. | Leaving unstable weights untreated. |
| Doubly robust methods | Combine treatment and outcome models so one correct nuisance model can suffice under assumptions. | Identification assumptions still required. | Treating "doubly robust" as robust to unmeasured confounding. |
| Difference-in-differences | Compare pre/post changes between treated and control groups. | Parallel trends and no spillovers. | Skipping pre-trend and placebo checks. |
| Instrumental variables | Use exogenous variation in treatment induced by an instrument. | Relevance, exclusion restriction, monotonicity/interpretation. | Using weak instruments or instruments with direct outcome effects. |
| Regression discontinuity | Use near-cutoff assignment as local quasi-random variation. | No manipulation around cutoff; local effect only. | Generalizing local cutoff effects to all units. |
| Interrupted time series | Estimate level/slope changes after an intervention in ordered aggregate data. | No simultaneous shocks; autocorrelation modeled. | Attributing coincident external changes to the intervention. |
| Causal forests | Estimate heterogeneous treatment effects with machine learning under valid identification. | Needs enough data and honest splitting/cross-fitting. | Using heterogeneous effects as causal without overlap and identification checks. |
| Mediation | Decompose effects into pathways through mediators. | Sequential ignorability and timing assumptions are strong. | Conditioning on post-treatment variables without a mediation design. |

## Bayesian Principles

| Method/family | 核心思想 / Principle | 关键假设或代价 | 常见误用 |
| --- | --- | --- | --- |
| Bayesian GLM | Combine likelihood and prior to produce posterior distributions over parameters and predictions. | Priors and likelihood are part of the model. | Hiding strong priors or reporting posterior intervals as assumption-free. |
| Hierarchical Bayes | Share information across groups through partial pooling. | Group exchangeability and hierarchy structure matter. | Overfitting group-level variation with too many random effects. |
| Bayesian survival/count/classification | Put probabilistic priors on domain-specific outcome models. | Sampling diagnostics and posterior predictive checks are required. | Trusting estimates with divergences or poor effective sample size. |
| Bayesian GP | Place priors over functions with uncertainty from kernel structure. | Kernel choice drives smoothness and extrapolation. | Interpreting uncertainty without prior/kernel sensitivity checks. |
| Bayesian model comparison | Compare predictive adequacy or posterior support across models. | Scores depend on priors, likelihoods, and candidate set. | Selecting by WAIC/LOO without posterior predictive checking. |

## Panel, Multivariate, and Econometric Principles

| Method/family | 核心思想 / Principle | 关键假设或代价 | 常见误用 |
| --- | --- | --- | --- |
| MANOVA/MANCOVA | Test group/predictor effects on multiple correlated outcomes jointly. | Multivariate distribution/covariance assumptions affect inference. | Running many unadjusted univariate tests instead. |
| CCA | Find linear combinations of two variable blocks with maximal correlation. | Sample size and regularization are critical. | Interpreting canonical variates without validation. |
| Correspondence analysis | Represent categorical association tables in low-dimensional geometry. | Exploratory visualization of associations. | Treating map distances as causal or confirmatory evidence. |
| SUR | Estimate multiple equations jointly when errors are correlated. | Cross-equation error correlation creates efficiency gains. | Using it when equations are unrelated. |
| Fixed effects | Use within-entity variation to remove time-invariant unobserved heterogeneity. | Needs within-entity changes. | Estimating time-invariant covariate effects in a standard entity fixed-effect model. |
| Random effects | Model entity heterogeneity as random and uncorrelated with predictors. | Stronger exogeneity assumption than fixed effects. | Using it because it is more efficient without checking plausibility. |
| First differences | Difference over time to remove fixed entity effects. | Increases noise from measurement error. | Applying it when meaningful change variation is too small. |
| IV / 2SLS | Use an instrument to isolate exogenous treatment variation. | Instrument must be relevant and excluded from the outcome equation. | Treating any correlated proxy as an instrument. |
| GMM | Estimate parameters from moment conditions. | Moment validity is the design. | Adding many instruments until tests look favorable. |
| Multiple testing / FDR | Control false discoveries when many hypotheses are screened. | Error-rate target must match the analysis goal. | Reporting only unadjusted significant findings after many tests. |
| Bootstrap / permutation | Approximate sampling variation by resampling or random relabeling. | Resampling must match dependence/exchangeability structure. | Bootstrapping clustered/time data as if IID. |

## Ranking, Recommendation, Spatial, and Graph Principles

| Method/family | 核心思想 / Principle | 关键假设或代价 | 常见误用 |
| --- | --- | --- | --- |
| Learning-to-rank | Optimize ordering quality for queries/users/items rather than class labels. | Evaluation unit is often query or session. | Random row splits that leak query/user context. |
| Collaborative filtering | Predict preferences from patterns of similar users/items. | Interaction matrix structure carries signal. | Ignoring cold start and popularity/exposure bias. |
| Matrix factorization | Approximate user-item interactions with low-rank latent factors. | Latent dimensions are predictive abstractions. | Treating factors as directly interpretable traits. |
| Association rules | Find item co-occurrence rules with support, confidence, and lift. | Co-occurrence is not causation. | Ranking rules by confidence alone and rediscovering base rates. |
| Spatial regression | Model spatial dependence through lag/error structures or spatial random effects. | Spatial weights/neighborhood definition matters. | Ignoring residual spatial autocorrelation. |
| GWR | Fit local regressions so coefficients vary over space. | Bandwidth controls locality. | Overinterpreting noisy local coefficient maps. |
| Kriging | Predict spatial fields using covariance over distance. | Stationarity/covariance model drives interpolation. | Extrapolating outside sampled spatial support. |
| Community detection | Partition graph nodes by edge-density or connectivity patterns. | Graph construction and resolution parameter define communities. | Treating algorithmic communities as natural groups without validation. |
| Link prediction | Predict missing/future edges from graph structure and features. | Evaluation split must mimic future edge discovery. | Letting test edges influence graph embeddings. |
| Graph neural networks | Learn node/edge/graph representations by message passing over neighborhoods. | Graph topology and features both matter; transductive settings can leak. | Evaluating with splits that share hidden neighborhood information. |

## Deep and Representation Learning Principles

| Method/family | 核心思想 / Principle | 关键假设或代价 | 常见误用 |
| --- | --- | --- | --- |
| MLP | Learn nonlinear feature interactions through stacked dense layers. | Needs regularization and sufficient data. | Using it as default for small tabular data where boosting is stronger. |
| CNN | Use local filters and weight sharing for spatial/grid-like structure. | Works when local patterns and translation structure matter. | Applying CNNs to arbitrary tabular features by reshaping them. |
| RNN/sequence models | Maintain hidden state over ordered observations. | Order and sequential dependence carry signal. | Randomly shuffling sequence elements or leaking future context. |
| Transformers | Use attention to learn context-dependent representations over sequences or tokens. | Data/compute and pretraining quality matter. | Fine-tuning on small data without leakage and overfitting checks. |
| Autoencoder | Learn compressed representations by reconstructing inputs. | Reconstruction objective defines learned signal. | Using low reconstruction error as proof of semantic usefulness. |
| VAE | Learn probabilistic latent variables with reconstruction plus distributional regularization. | Latent prior/likelihood choices matter. | Expecting crisp interpretable factors without constraints. |
| Contrastive/self-supervised learning | Learn representations by pulling related views together and pushing unrelated views apart. | View construction and negative sampling define semantics. | Creating augmented views that leak labels or destroy task-relevant information. |
| Transfer learning | Adapt pretrained representations to a target task. | Source and target domains must be compatible. | Assuming pretrained performance transfers under distribution shift. |
| Conformal prediction | Wrap a model with calibrated prediction sets/intervals under exchangeability. | Calibration data must match deployment distribution. | Claiming coverage after distribution shift or invalid split design. |

## Preprocessing, Selection, and Interpretation Principles

| Method/family | 核心思想 / Principle | 关键假设或代价 | 常见误用 |
| --- | --- | --- | --- |
| Standardization | Put numeric features on comparable scale. | Essential for distance, margin, penalty, and gradient methods. | Fitting scaler before train/test split. |
| Encoding | Convert categorical variables into model-usable numeric representations. | Encoding must match nominal/ordinal/cardinality structure. | Target encoding without fold-aware leakage control. |
| Imputation | Replace missing values using learned rules or model-based draws. | Missingness mechanism affects bias. | Imputing once on the full dataset before validation. |
| Feature selection | Reduce irrelevant/noisy variables to improve stability or interpretability. | Selection is part of model training. | Selecting features on all data before cross-validation. |
| Dimensionality reduction | Replace original variables with lower-dimensional summaries. | May preserve variance rather than target signal. | Fitting unsupervised transforms outside CV in predictive workflows. |
| Cross-validation | Approximate out-of-sample performance by repeated train/validation splits. | Split must match deployment dependence structure. | Using IID CV for time, grouped, spatial, or graph data. |
| Nested CV | Separate model tuning from final performance estimation. | More computation. | Reporting inner-CV tuned performance as unbiased generalization. |
| Calibration | Align predicted probabilities with observed frequencies. | Needs independent calibration data or cross-fitting. | Calibrating after looking at test outcomes. |
| Interpretation tools | Summarize learned relationships with coefficients, permutation importance, PDP/ICE, SHAP, or counterfactuals. | Explanations inherit model/data assumptions. | Treating model explanation as causal explanation. |
| Drift monitoring | Track distribution, label, concept, and data-quality changes after deployment. | Monitoring target depends on deployment feedback availability. | Treating stable feature distributions as proof the model remains accurate. |
