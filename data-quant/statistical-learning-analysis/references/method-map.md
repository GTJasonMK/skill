# Statistical Learning Method Map

Use this reference when choosing or explaining statistical learning methods. Match the method to the question, target type, data constraints, assumptions, and validation design.

Scope note: this is a broad practical method-selection map, not an exhaustive encyclopedia of every statistical procedure. If the user is working in a specialized domain such as spatial statistics, graph learning, signal processing, econometrics, bioinformatics, NLP, computer vision, or recommender systems, use this map to identify the right family and then consult domain-specific references.

## Contents

- [Problem Triage](#problem-triage)
- [Supervised Regression](#supervised-regression)
- [Classification](#classification)
- [Ensembles and Meta-Learning](#ensembles-and-meta-learning)
- [Structured Outcomes](#structured-outcomes)
- [Unsupervised Learning](#unsupervised-learning)
- [Anomaly and Density Methods](#anomaly-and-density-methods)
- [Time Series and Forecasting](#time-series-and-forecasting)
- [Survival and Duration Analysis](#survival-and-duration-analysis)
- [Causal Inference](#causal-inference)
- [Bayesian and Probabilistic Modeling](#bayesian-and-probabilistic-modeling)
- [Multivariate, Panel, and Econometric Models](#multivariate-panel-and-econometric-models)
- [Ranking, Recommendation, Association, Spatial, and Graph Methods](#ranking-recommendation-association-spatial-and-graph-methods)
- [Deep Learning and Representation Learning](#deep-learning-and-representation-learning)
- [Special Data Regimes](#special-data-regimes)
- [Common Preprocessing and Selection Methods](#common-preprocessing-and-selection-methods)

## Problem Triage

| Question | Prefer these families | 适用场景 / Applicability scenario |
| --- | --- | --- |
| Predict a continuous numeric outcome | OLS, regularized regression, GAM/splines, tree ensembles, SVR, GPR, neural nets | Use when `y` is continuous and the goal is prediction or effect association. |
| Predict a category | Logistic regression, LDA/QDA, naive Bayes, SVM, kNN, trees, ensembles, neural nets | Use when `y` is binary, multiclass, multilabel, or ordinal. |
| Explain relationships with uncertainty | Linear models, GLM, mixed models, GAM, Bayesian models | Use when coefficients, intervals, hypothesis tests, or transparent assumptions matter. |
| Discover groups without labels | K-means, hierarchical, GMM, DBSCAN/HDBSCAN, spectral clustering | Use when no target labels exist and the goal is segmentation or structure discovery. |
| Reduce dimensions or latent structure | PCA, factor analysis, ICA, NMF, LDA topic models, manifold learning | Use for visualization, denoising, compression, latent factors, or feature extraction. |
| Find rare or abnormal cases | Isolation Forest, One-Class SVM, LOF, robust covariance, density models | Use when anomalies are sparse and labels are missing or weak. |
| Forecast over time | ARIMA/SARIMA, ETS, state-space, VAR/VECM, dynamic regression, ML with lag features | Use when order, seasonality, autocorrelation, and rolling validation matter. |
| Analyze time-to-event with censoring | Kaplan-Meier, Cox PH, AFT, parametric survival, random survival forests | Use when not all events are observed by study end or follow-up differs. |
| Estimate the effect of an intervention | RCT/AB test, regression adjustment, matching/weighting, DiD, IV, RD, doubly robust, causal forests | Use when the estimand is causal and assumptions can be defended. |
| Model panel/longitudinal units | Fixed effects, random effects, first differences, mixed models, GEE, panel IV/GMM | Use when repeated observations are nested in entities such as people, firms, stores, regions, or devices. |
| Analyze multiple outcomes or variable blocks | MANOVA, CCA, PLS, factor analysis, multioutput models | Use when response variables or feature blocks should be modeled jointly. |
| Rank, recommend, or discover co-occurrence | Learning-to-rank, collaborative filtering, matrix factorization, association rules | Use when the outcome is order, relevance, next item, or item-set co-occurrence rather than a simple label. |
| Learn from images, text, audio, graphs, or high-volume embeddings | CNNs, transformers, RNNs, autoencoders, graph neural networks, transfer learning | Use when representation learning is central and data volume/compute justify it. |

## Supervised Regression

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| Ordinary Least Squares (OLS) | Baseline continuous-outcome model; interpretable coefficients; roughly linear relationships; moderate `p` and enough samples. | Sensitive to outliers, collinearity, heteroskedasticity, omitted variables, nonlinear effects, and `p >= n`. |
| Ridge regression | Many correlated predictors; stable prediction; shrinkage without feature deletion. | Coefficients stay nonzero, so it is weaker for sparse feature discovery. Scale features first. |
| Lasso | Feature selection in high-dimensional or sparse settings; interpretable sparse model. | Unstable under strong collinearity; may select one of many correlated predictors arbitrarily. |
| Elastic Net | High-dimensional data with groups of correlated predictors; balance between Ridge stability and Lasso sparsity. | Requires tuning two penalties; standardization is mandatory. |
| Polynomial regression and basis expansion | Smooth curvature with low-dimensional predictors; simple nonlinear baseline. | High-degree terms overfit quickly and extrapolate badly. Use cross-validation and regularization. |
| Splines and GAM | Interpretable nonlinear effects; additive smooth relationships; partial effect plots are useful. | Weak when interactions dominate unless explicitly included; smoothing choice matters. |
| Robust regression | Continuous outcome with outliers or heavy-tailed errors; coefficients should resist extreme points. | Does not fix leverage, omitted variables, or bad measurements automatically. |
| Quantile regression | Model median or tail behavior; heterogeneous effects across response distribution; asymmetric loss. | More complex inference and less intuitive for users expecting mean effects. |
| kNN regression | Local smooth prediction; small to medium data; nonparametric baseline after scaling. | Poor with high dimensions, irrelevant features, or large datasets; sensitive to distance metric. |
| Support Vector Regression (SVR) | Medium-sized nonlinear regression with kernel structure and margin-based robustness. | Scaling and hyperparameter tuning are critical; kernel SVR can be expensive on large `n`. |
| Kernel ridge regression | Smooth nonlinear regression with kernel methods and squared-loss regularization. | Computationally expensive for large `n`; less sparse than SVR. |
| Gaussian Process Regression | Small to medium data; calibrated uncertainty; smooth functions; active learning or Bayesian optimization. | Scales poorly with sample size; kernel choice controls behavior strongly. |
| Decision tree regression | Interpretable nonlinear splits and interactions; quick baseline. | High variance and stepwise predictions; usually inferior to ensembles unless interpretability is primary. |
| Random forest regression | Strong tabular baseline; nonlinearities and interactions; robust to monotone transforms and outliers. | Less extrapolation beyond training range; less transparent; can be weak with sparse high-dimensional text. |
| Gradient boosting regression | High-performing tabular prediction; complex nonlinear patterns; mixed feature types with proper preprocessing. | Easy to overfit without validation; tuning, leakage control, and calibration of uncertainty matter. |
| Neural network regression | Large datasets, unstructured inputs, complex interactions, representation learning. | Usually unnecessary for small tabular data; needs scaling, regularization, validation, and compute. |
| Partial Least Squares (PLS) | Many correlated predictors and continuous outcomes; chemometrics, spectra, high-collinearity measurement data. | Components can be harder to interpret; validate component count carefully. |

## Classification

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| Logistic regression | Binary or multiclass baseline; interpretable odds/logit effects; calibrated probabilities after checks; small to medium data. | Linear decision boundary unless engineered features are added; watch separation and collinearity. |
| Penalized logistic regression | Sparse/high-dimensional predictors; text features; many correlated variables; stable classification baseline. | Tune penalty inside cross-validation; scale dense numeric features. |
| LDA | Low-dimensional Gaussian-like classes with shared covariance; interpretable linear boundary. | Assumptions break with skewed, heavy-tailed, or high-dimensional data without shrinkage. |
| QDA | Classes have different covariance structures; nonlinear quadratic boundaries with enough samples per class. | High parameter count; unstable when sample size per class is small. |
| Naive Bayes | Fast baseline for text, counts, sparse categorical data; small data; online or high-dimensional settings. | Feature independence assumption is strong; probabilities can be poorly calibrated. |
| kNN classification | Simple local decision rule; small to medium data; meaningful distance metric. | Poor in high dimensions, unscaled features, imbalanced classes, or large datasets. |
| Linear SVM | High-dimensional sparse features; robust margin classifier; text classification. | Probabilities need calibration; choose `C` via cross-validation. |
| Kernel SVM | Medium-sized nonlinear classification; clear margin separation with kernels. | Expensive on large datasets; scaling and kernel tuning are critical. |
| Decision tree classification | Transparent rules, interactions, nonlinear splits, mixed features. | High variance; prune or constrain depth; unstable to small data changes. |
| Random forest classification | Strong default for tabular classification; nonlinearities; many interactions; modest preprocessing. | Probabilities may need calibration; class imbalance needs weighting/resampling/thresholding. |
| Gradient boosting classification | Often best tabular accuracy; handles nonlinear interactions; supports ranking/cost objectives in some libraries. | Sensitive to leakage, hyperparameters, and class imbalance. Use validation curves and early stopping. |
| Neural network classifier | Large datasets, images/text/embeddings, complex representation learning. | Requires substantial validation, regularization, and compute; not first choice for small tabular data. |
| Semi-supervised learning | Many unlabeled samples plus few labeled samples; labels expensive and feature space has label-consistent geometry. | Can amplify wrong pseudo-labels; validate against a labeled holdout. |
| Probability calibration | Decisions require reliable probabilities, risk scores, or threshold optimization. | Calibrate on held-out folds; do not calibrate on the test set. |
| Threshold tuning | Costs of false positives and false negatives differ; precision/recall tradeoff matters. | Tune threshold after model fitting on validation data; report chosen operating point. |
| Imbalanced classification methods | Rare events, fraud, churn, medical diagnosis, defect detection. Use class weights, resampling, PR-AUC, recall, precision, sensitivity/specificity, and cost curves. | Do resampling inside CV folds only; accuracy and ROC-AUC can hide poor rare-class performance. |
| Ordinal classification | Ordered categories such as ratings, severity, stages, or Likert responses. | Treating ordinal labels as nominal loses order; treating as continuous can distort spacing. |
| Multilabel and multioutput classification | Multiple labels can be true at once, or multiple target columns exist. | Need label-wise and example-wise metrics; label dependence may matter. |

## Ensembles and Meta-Learning

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| Bagging | Reduce variance of unstable base learners such as trees; improve robustness by fitting models on bootstrap samples. | Less useful for high-bias base models; final model is less interpretable than a single tree. |
| Random forest | General-purpose bagged tree ensemble for tabular regression/classification with nonlinearities and interactions. | Can underperform tuned boosting; probabilities and extrapolation need checks. |
| Extra Trees | Fast randomized tree ensemble; useful when variance reduction and speed matter. | Extra randomization can increase bias; tune tree count and depth. |
| AdaBoost | Boost weak learners sequentially; effective for clean tabular classification and simple base estimators. | Sensitive to label noise and outliers because misclassified points receive high weight. |
| Gradient boosting / histogram gradient boosting | High-performing tabular prediction; handles complex interactions and nonlinearities with staged additive trees. | Needs careful validation, early stopping, and leakage control; can overfit small/noisy data. |
| Voting ensemble | Combine several strong, diverse classifiers when no single model is consistently best. | Diversity matters; soft voting needs calibrated probabilities. |
| Stacking / Super Learner | Combine heterogeneous models through a meta-learner using out-of-fold predictions. | Must use cross-fitted base predictions; otherwise the meta-learner leaks training labels. |
| Blending | Simple holdout-based stacking for quick competitions or prototypes. | Wastes validation data and can be unstable with small samples. |
| Bayesian model averaging | Average over model uncertainty when several plausible statistical models exist. | Priors/model space drive results; explain posterior model probabilities carefully. |

## Structured Outcomes

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| Poisson regression | Counts over fixed exposure with mean approximately equal to variance; rate modeling with offsets. | Overdispersion and excess zeros require alternatives. |
| Negative binomial regression | Overdispersed count outcomes such as incidents, claims, visits, or defects. | Still assumes a count data-generating process; inspect zero inflation and exposure. |
| Zero-inflated/hurdle models | Count data with more zeros than Poisson/NB can explain; two-stage "any event" and "how many" process. | Needs a plausible zero-generation mechanism; can be hard to identify. |
| Binomial GLM | Success/failure counts out of trials; proportions with known denominators. | Not for arbitrary continuous proportions without trial counts. |
| Beta regression | Continuous proportions in `(0, 1)` such as rates, shares, utilization. | Exact zeros/ones require transformation or inflated beta variants. |
| Multinomial logit | Nominal outcome with more than two categories and no natural order. | Independence of irrelevant alternatives may be inappropriate. |
| Ordinal logit/probit | Ordered categories where thresholds on latent severity are plausible. | Check proportional odds/parallel slopes assumptions. |
| Mixed effects models | Repeated measures, clustered observations, sites, subjects, stores, classrooms, panels. | Random-effect structure and convergence require care; do not ignore grouping. |
| GEE | Population-average effects with correlated observations when random-effects assumptions are not central. | Less suited for subject-specific predictions; working correlation must be considered. |

## Unsupervised Learning

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| PCA | Linear dimensionality reduction, denoising, compression, visualization, collinearity handling. | Components are linear and variance-driven, not necessarily predictive or causal. Scale features when units differ. |
| Sparse PCA | Need more interpretable components with many zero loadings. | Optimization and component stability require validation. |
| Kernel PCA | Nonlinear low-dimensional structure with moderate data. | Kernel choice and scalability are limiting. |
| Factor analysis | Latent constructs with measurement noise; psychometrics, surveys, latent traits. | Requires factor interpretability and rotation decisions; assumptions matter. |
| ICA | Separate independent sources from mixed signals; signal processing, artifact removal. | Independence assumption is strong; scale and preprocessing matter. |
| NMF | Nonnegative data and additive parts-based representation; topics, images, counts, parts decomposition. | Requires nonnegative inputs; component count and initialization matter. |
| Topic models (LDA) | Document collections, bag-of-words counts, latent topics. | Topics can be unstable and need human interpretation; not a substitute for supervised text classification. |
| t-SNE | Local-neighborhood visualization of high-dimensional data. | Visualization only; distances, cluster sizes, and global structure can mislead. |
| UMAP | Fast nonlinear visualization or feature embedding; local/global structure tradeoff. | Results depend on hyperparameters and random seed; validate downstream use separately. |
| K-means | Compact, roughly spherical clusters; large numeric datasets; segmentation with expected cluster count. | Poor for nonconvex clusters, varying densities, categorical features, and arbitrary `k`. |
| Hierarchical clustering | Nested cluster structure; dendrogram inspection; small to medium datasets. | Linkage/distance choices strongly affect results; can be expensive for large `n`. |
| Gaussian mixture models | Soft clustering; elliptical clusters; density estimates; uncertainty in cluster assignment. | Sensitive to initialization and covariance assumptions; select components with BIC/AIC/CV. |
| DBSCAN | Arbitrary-shaped dense clusters with noise; no need to predefine cluster count. | Struggles with varying density and high dimensions; `eps` choice is critical. |
| HDBSCAN | Varying-density clusters; noise detection; fewer manual density thresholds than DBSCAN. | Still distance-sensitive; cluster stability needs interpretation. |
| Spectral clustering | Nonconvex clusters defined by graph similarity; medium data. | Graph construction and memory scale poorly; not ideal for very large data. |
| BIRCH | Large datasets needing incremental hierarchical clustering. | Best for numeric features and roughly compact clusters. |

## Anomaly and Density Methods

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| Isolation Forest | Unlabeled anomaly detection in tabular data; anomalies isolate quickly in random trees. | Contamination rate affects threshold; weak for subtle contextual anomalies. |
| One-Class SVM | Novelty detection with mostly normal training data; nonlinear boundary with kernels. | Scaling and kernel tuning are critical; expensive on large data. |
| Local Outlier Factor | Local density anomalies; points unusual relative to neighbors. | Mainly for outlier scoring; sensitive to `k`, scale, and local density variation. |
| Robust covariance / Elliptic Envelope | Gaussian-like data with covariance outliers; low to moderate dimensions. | Not suitable for complex non-elliptical distributions. |
| Kernel density estimation | Estimate continuous density; anomaly thresholding; distribution comparison. | Bandwidth selection dominates; poor in high dimensions. |
| Gaussian mixtures for density | Multimodal density and soft anomaly scores. | Component selection and covariance regularization matter. |

## Time Series and Forecasting

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| Naive/seasonal naive baseline | Mandatory benchmark for forecasting; strong baseline when changes are slow or seasonal. | Not enough for explanatory modeling or changing regimes. |
| AR/ARIMA | Univariate autocorrelated series; stationary or differenced processes. | Needs stationarity checks, residual diagnostics, and rolling validation. |
| SARIMA/SARIMAX | Seasonal time series; exogenous regressors with lagged dynamics. | Exogenous variables must be available at forecast time. |
| Exponential smoothing / ETS | Level, trend, seasonality with interpretable components; short to medium horizon. | Less suited for many external predictors or complex nonlinear effects. |
| State-space / Kalman filter | Missing observations, latent components, structural time series, dynamic regression. | Model specification can be complex; diagnostics are required. |
| VAR/VECM | Multiple interacting time series; lagged cross-effects; cointegrated systems. | Needs enough time points; stationarity/cointegration assumptions matter. |
| Dynamic factor models | Many related time series driven by a few latent factors. | Factor count and interpretation require validation. |
| ML with lag/rolling features | Nonlinear forecasting with many predictors; tabular supervised setup over time. | Use rolling-origin/blocked validation; prevent future leakage in feature construction. |
| Change-point/regime-switching models | Structural breaks, policy changes, market regimes, process shifts. | Need enough data per regime; avoid overinterpreting noise as breaks. |

## Survival and Duration Analysis

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| Kaplan-Meier | Nonparametric survival curves; compare groups visually; right-censored data. | Does not adjust for many covariates except stratified comparisons. |
| Log-rank test | Compare survival curves between groups. | Less informative with crossing hazards or covariate imbalance. |
| Cox proportional hazards | Time-to-event regression with censoring; covariate effects as hazard ratios. | Check proportional hazards; handle time-varying covariates if needed. |
| Stratified Cox | Non-proportional baseline hazards across strata while estimating shared covariate effects. | Cannot estimate effects for stratification variables directly. |
| Accelerated Failure Time (AFT) | Parametric time-ratio interpretation; event time is accelerated/decelerated by covariates. | Distributional assumptions matter. |
| Parametric survival models | Exponential, Weibull, log-normal, piecewise models for extrapolation or smooth hazards. | Misspecification can bias long-horizon estimates. |
| Time-varying survival regression | Covariates change during follow-up; longitudinal exposure histories. | Requires careful data expansion and no future leakage. |
| Survival forests/boosting | Nonlinear survival prediction and interactions. | Harder inference; need survival-specific metrics like C-index and integrated Brier score. |

## Causal Inference

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| Randomized experiment / A/B test | Gold-standard intervention effect when randomization is feasible. | Check sample ratio mismatch, interference, noncompliance, multiple testing, and guardrail metrics. |
| Regression adjustment / ANCOVA | Observational or experimental data with measured confounders; estimate adjusted association/effect. | Not causal without no-unmeasured-confounding and correct model assumptions. |
| Propensity score matching | Balance treated/control groups on observed covariates; intuitive matched comparisons. | Discards data; overlap/common support and balance diagnostics are mandatory. |
| Propensity weighting/IPW | Estimate marginal effects under measured confounding; reweight to target population. | Extreme weights cause variance; diagnose overlap and stabilize/truncate weights. |
| Doubly robust methods (AIPW/TMLE) | Combine outcome and treatment models; consistent if one model is correct under assumptions. | Still requires identification assumptions and careful nuisance-model validation. |
| Difference-in-differences | Policy/intervention with treated and control groups observed before and after. | Parallel trends is central; check pre-trends and spillovers. |
| Instrumental variables | Unmeasured confounding with a credible instrument affecting treatment but not outcome except through treatment. | Weak or invalid instruments can be worse than ordinary regression. |
| Regression discontinuity | Treatment assignment changes at a cutoff; local causal effect near threshold. | Requires no manipulation around cutoff and careful bandwidth sensitivity. |
| Interrupted time series | Aggregate intervention at known time with pre/post trends. | Confounded by simultaneous shocks and autocorrelation. |
| Causal forests / heterogeneous treatment effects | Estimate treatment effect heterogeneity with many covariates. | Needs large data, valid identification, honest splitting, and policy-relevant interpretation. |
| Mediation analysis | Decompose total effect into direct and indirect pathways. | Sequential ignorability and mediator timing assumptions are strong. |
| Causal discovery | Hypothesize graph structure from data when experiments are limited. | Outputs are assumption-sensitive hypotheses, not proof. Use domain knowledge and refutation. |

## Bayesian and Probabilistic Modeling

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| Bayesian GLM | Small data, prior knowledge, uncertainty intervals, complete posterior predictions. | Priors must be defensible; check posterior predictive fit and sampling diagnostics. |
| Hierarchical Bayesian models | Partial pooling across groups, sites, users, stores, studies, or repeated measures. | Requires convergence checks; model complexity should match data support. |
| Bayesian logistic/count/survival models | Probabilistic classification, counts, rates, time-to-event with prior information. | Sampling can be slow; communicate posterior uncertainty clearly. |
| Bayesian Gaussian processes | Nonparametric functions with uncertainty; small to medium datasets. | Kernel and computational scaling limitations are significant. |
| Bayesian model comparison | Compare models with WAIC/LOO, Bayes factors, or posterior predictive checks. | Do not use a single score without checking predictive adequacy and prior sensitivity. |

## Multivariate, Panel, and Econometric Models

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| MANOVA / MANCOVA | Multiple continuous outcomes tested jointly across groups or predictors; useful when outcomes are correlated. | Assumptions are stronger than separate regressions; inspect covariance structure and follow-up contrasts. |
| Canonical Correlation Analysis (CCA) | Study associations between two multivariate blocks, such as behavior and biomarkers. | Highly sensitive to sample size and regularization; cross-validate canonical relationships. |
| Correspondence analysis / multiple correspondence analysis | Explore associations in contingency tables or categorical survey data. | Mostly exploratory; distances and dimensions need careful explanation. |
| Seemingly Unrelated Regression (SUR) | Multiple regression equations with correlated errors; improves efficiency when equations are related. | Gains are small if error correlations are weak; equation specification matters. |
| Fixed effects panel regression | Control for time-invariant unobserved heterogeneity within entities. | Cannot estimate effects of entity-invariant covariates; needs within-entity variation. |
| Random effects panel regression | Panel data where entity-specific effects are uncorrelated with covariates; estimate time-invariant covariates too. | Hausman-style reasoning is needed; bias if random effects correlate with predictors. |
| First-difference models | Remove entity fixed effects by differencing adjacent periods; useful for two-period or strongly persistent panels. | Amplifies measurement error and changes the interpretation to within-entity changes. |
| Instrumental variables / 2SLS | Estimate causal effects with endogenous treatment/exposure and credible instruments. | Weak or invalid instruments can badly mislead; report first-stage strength and exclusion restriction reasoning. |
| GMM | Moment-condition estimation for endogeneity, panels, systems, or heteroskedasticity-robust settings. | Moment validity and instrument proliferation are major risks. |
| Fama-MacBeth regression | Asset pricing or finance panels with cross-sectional regressions over time. | Standard errors and time dependence need domain-specific treatment. |
| Multiple testing / FDR control | Many hypotheses, features, genes, metrics, or subgroup tests. | Adjust for multiplicity; distinguish confirmatory tests from exploration. |
| Bootstrap / permutation inference | Small samples, complex estimators, or weak parametric assumptions. | Respect dependence structure when resampling; not a cure for biased design. |

## Ranking, Recommendation, Association, Spatial, and Graph Methods

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| Learning-to-rank | Search, ads, feeds, candidate prioritization, or relevance ordering. | Use ranking metrics such as NDCG/MAP; random row splits can leak user/query context. |
| Collaborative filtering | Recommend items from user-item interactions; explicit ratings or implicit feedback. | Cold start and popularity bias are common; use time-aware and user-aware validation. |
| Matrix factorization for recommendation | Low-rank latent factors for sparse user-item matrices. | Interpretability is limited; negative sampling and implicit feedback assumptions matter. |
| Association rules | Market baskets, co-purchase, co-occurrence, and rule discovery. | High support/confidence can be trivial; use lift/leverage and domain review. |
| Spatial regression | Outcomes with spatial autocorrelation or region-level dependence. | Ignoring spatial dependence biases uncertainty; define spatial weights carefully. |
| Geographically weighted regression | Spatially varying relationships across locations. | Exploratory and bandwidth-sensitive; avoid overinterpreting local coefficients. |
| Kriging / Gaussian process spatial interpolation | Predict continuous spatial fields from sampled locations. | Stationarity and covariance assumptions control interpolation; extrapolation is risky. |
| Graph community detection | Discover communities in networks, social graphs, transaction graphs, or interaction data. | Results depend on graph construction and resolution; modularity has known limits. |
| Node/edge/link prediction | Predict graph labels, missing edges, or future connections. | Train/test split must preserve temporal and graph leakage constraints. |
| Graph neural networks | Representation learning on relational graph data with node/edge features. | Needs enough graph signal; oversmoothing, leakage, and scalability are common issues. |

## Deep Learning and Representation Learning

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| Multilayer perceptron (MLP) | Large tabular or embedding-based supervised learning with nonlinear interactions. | Often loses to tree boosting on small/medium tabular data; needs scaling and regularization. |
| Convolutional neural networks (CNNs) | Images, grids, spectrograms, local spatial patterns. | Data augmentation and transfer learning are often essential; monitor dataset shift. |
| Recurrent neural networks / sequence models | Ordered sequences, sensor streams, language/time sequences where hidden state matters. | Transformers often outperform them at scale; long dependencies and leakage need care. |
| Transformers | Text, images, multimodal data, long-context sequence modeling, transfer learning with pretrained models. | Expensive and data-hungry when trained from scratch; fine-tuning requires strict validation. |
| Autoencoders | Unsupervised representation learning, denoising, compression, reconstruction anomaly scores. | Reconstruction error may miss semantic anomalies; validate against downstream goals. |
| Variational autoencoders | Probabilistic latent representations and generative modeling. | Latent dimensions and likelihood choices affect interpretability and sample quality. |
| Contrastive/self-supervised learning | Learn embeddings from unlabeled data when labels are scarce. | Positive/negative sampling choices define what the model learns. |
| Transfer learning / fine-tuning | Specialized task with limited labels but relevant pretrained representations. | Pretraining domain mismatch and data leakage through benchmark contamination are risks. |
| Conformal prediction | Distribution-free prediction intervals or prediction sets under exchangeability. | Coverage depends on calibration data matching deployment distribution; handle time/group splits carefully. |

## Special Data Regimes

| Regime | Prefer | 适用场景 / Applicability scenario |
| --- | --- | --- |
| `p >> n` high-dimensional data | Regularization, feature screening, PCA/PLS, sparse models, nested CV | Use when predictors exceed samples, such as genomics or text. |
| Sparse text/count features | Multinomial/Bernoulli naive Bayes, linear SVM, penalized logistic regression, topic models | Use sparse matrices and proper tokenization; avoid dense distance methods as default. |
| Strong class imbalance | Class weights, resampling inside CV, calibrated thresholds, PR-AUC, recall/precision, cost-sensitive learning | Use when rare class value/cost is central. |
| Missing data | Missingness diagnosis, imputation inside pipelines, multiple imputation for inference, models that handle NaN | Avoid complete-case analysis unless missingness is small and plausibly random. |
| Grouped/repeated observations | Grouped CV, mixed models, cluster-robust SE, GEE, hierarchical Bayes | Never let the same group leak across train/test if predicting new groups. |
| Temporal data | Rolling-origin validation, lag features, blocked splits, time-aware imputation | Never use future observations in preprocessing or feature engineering. |
| Outliers/heavy tails | Robust regression, quantile regression, transformations, winsorization with justification, tree ensembles | Investigate whether outliers are errors or meaningful extremes. |
| Interpretability required | Linear/GLM/GAM, shallow trees, monotonic constraints, partial dependence/ICE, permutation importance, SHAP with caveats | Match explanation method to model and question. |
| Deployment constraints | Simpler models, calibration, latency checks, drift monitoring, reproducible pipeline | Optimize operational reliability, not just offline score. |
| Panel/longitudinal data | Fixed effects, random effects, mixed models, GEE, clustered SE, group/time-aware validation | Use when each entity has repeated observations and within-entity dependence matters. |
| Spatial data | Spatial regression, kriging, geographically weighted regression, spatial CV | Use when nearby observations are correlated or predictions are location-based. |
| Graph/network data | Community detection, graph embeddings, link prediction, GNNs | Use when relationships between observations carry signal. |
| Streaming or nonstationary data | Online learning, drift detection, rolling retraining, prequential evaluation | Use when data distribution changes over time or the model updates continuously. |
| Many simultaneous tests | FDR, family-wise error control, hierarchical testing, shrinkage | Use when multiple comparisons can create false discoveries. |

## Common Preprocessing and Selection Methods

| Method | 适用场合 / Best use | 注意事项 / Avoid or watch |
| --- | --- | --- |
| Standardization | Distance, margin, penalized linear, PCA, neural network, and kernel methods. | Fit scaler on training folds only. |
| Categorical encoding | One-hot for low-cardinality nominal variables; target/impact encoding for high cardinality with leakage-safe CV; ordinal encoding only for true order. | Target encoding leaks easily if not fold-aware. |
| Imputation | Missing numeric/categorical values before models that cannot handle them. | Learn imputation parameters inside folds; add missingness indicators when informative. |
| Feature selection | Reduce noise, improve interpretability, handle high dimensions. | Select inside CV; univariate screening can miss interactions. |
| Dimensionality reduction | Reduce collinearity, denoise, compress, visualize. | Fit inside CV; unsupervised components may not preserve target signal. |
| Cross-validation | Estimate generalization and tune hyperparameters. | Use stratified, grouped, nested, blocked, or rolling CV as the data structure requires. |
| Nested cross-validation | Honest performance estimation when hyperparameters/features are selected. | More expensive; use when model-selection bias matters. |
| Calibration | Reliable probabilities and risk decisions. | Needs separate validation or cross-fitting; report calibration curve/Brier score. |
| Model interpretation | Coefficients, PDP/ICE, permutation importance, SHAP, counterfactual explanations. | Interpretation can be invalid under correlated features, extrapolation, or causal misframing. |
| Drift monitoring | Production models with changing data, labels, or user behavior. | Separate covariate drift, label drift, concept drift, and data quality failures. |
