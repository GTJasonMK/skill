# Sources

Reviewed on 2026-05-23. Use these sources when updating the skill or when the user asks for citations.

## Core statistical learning texts

- An Introduction to Statistical Learning: https://www.statlearning.com/
  - Broad applied treatment of statistical learning, including regression, classification, resampling, regularization, tree methods, SVM, deep learning, survival analysis, unsupervised learning, and multiple testing.
- The Elements of Statistical Learning: https://hastie.su.domains/ElemStatLearn/
  - More technical reference for statistical learning, model selection, supervised/unsupervised methods, kernels, boosting, additive models, and related theory.

## Python statistical learning and modeling documentation

- scikit-learn User Guide: https://scikit-learn.org/stable/user_guide.html
  - Main reference for supervised learning, unsupervised learning, model selection/evaluation, inspection, preprocessing, pipelines, dimensionality reduction, clustering, anomaly detection, and estimator selection.
- scikit-learn Pipeline and ColumnTransformer examples: https://scikit-learn.org/stable/auto_examples/compose/plot_column_transformer_mixed_types.html
  - Reference for leakage-resistant preprocessing and model pipelines.
- scikit-learn model evaluation and metrics API: https://scikit-learn.org/stable/api/sklearn.metrics.html
  - Reference for classification and regression metrics used in starter modeling scripts.
- pandas documentation: https://pandas.pydata.org/docs/
  - Reference for CSV I/O, DataFrame operations, missing values, type handling, and data manipulation.
- scikit-learn Ensemble API and guide: https://scikit-learn.org/stable/api/sklearn.ensemble.html
  - Reference for bagging, random forests, Extra Trees, AdaBoost, gradient boosting, voting, and stacking estimators.
- scikit-learn Cross Decomposition API: https://sklearn.org/stable/modules/generated/sklearn.cross_decomposition.CCA.html
  - Reference for CCA and related cross-decomposition/PLS-style methods.
- statsmodels User Guide: https://www.statsmodels.org/stable/user-guide.html
  - Main reference for statistical modeling with inference: linear regression, GLM, GEE, GAM, robust models, mixed effects, discrete/count models, ANOVA, time series, survival/duration, nonparametric methods, treatment effects, and multiple imputation.
- linearmodels documentation: https://bashtage.github.io/linearmodels/
  - Reference for panel data models, instrumental variables, system regression, GMM, and asset-pricing factor models.
- ARCH documentation: https://bashtage.github.io/arch/
  - Reference for financial econometrics, especially ARCH/GARCH-family volatility models, unit root and cointegration tools.
- PyPortfolioOpt documentation: https://pyportfolioopt.readthedocs.io/
  - Reference for portfolio optimization, expected return models, risk models, efficient frontier, Black-Litterman, and HRP.
- Kenneth R. French Data Library: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
  - Reference source for commonly used academic asset-pricing factor returns and portfolios.
- imbalanced-learn User Guide: https://imbalanced-learn.org/stable/user_guide.html
  - Reference for over-sampling, under-sampling, combined sampling, sampler ensembles, metrics, cross-validation, and leakage pitfalls in imbalanced classification.
- PyMC learning documentation: https://www.pymc.io/projects/docs/en/stable/learn.html
  - Reference for Bayesian modeling, GLMs, Gaussian processes, posterior predictive checks, and model comparison.
- lifelines documentation: https://lifelines.readthedocs.io/en/latest/
  - Reference for survival analysis, including Kaplan-Meier, parametric models, Cox regression, time-varying survival regression, and censoring support.
- DoWhy documentation: https://www.pywhy.org/dowhy/main/index.html
  - Reference for causal inference workflows, explicit identifying assumptions, separation of identification and estimation, robustness/refutation checks, interventions, counterfactuals, and root-cause analysis.
- EconML documentation: https://www.pywhy.org/EconML/
  - Reference for machine-learning based heterogeneous treatment effect estimation, DML, doubly robust learning, causal forests, IV CATE estimators, and validation.
- XGBoost documentation: https://xgboost.readthedocs.io/en/stable/
  - Reference for scalable gradient boosted trees, ranking, categorical data, survival AFT, Python/R APIs, and parameter tuning.
- LightGBM documentation: https://lightgbm.readthedocs.io/en/stable/
  - Reference for gradient boosting implementation and Python/R APIs.
- CatBoost documentation: https://catboost.ai/docs/en/
  - Reference for gradient boosting with categorical/text/embedding features and model analysis tools.
- sktime documentation: https://www.sktime.net/en/stable/
  - Reference for machine learning with time series, including forecasting, classification, regression, clustering, pipelines, ensembles, and tuning.
- PySAL documentation: https://pysal.org/
  - Reference entry point for spatial data science and spatial statistical modeling in Python.
- PyTorch Geometric documentation: https://pytorch-geometric.readthedocs.io/en/latest/
  - Reference for graph neural network implementation.
- implicit PyPI project: https://pypi.org/project/implicit/
  - Reference for implicit-feedback recommender algorithms such as matrix factorization for collaborative filtering.

## Update guidance

- Prefer stable official documentation and freely available textbooks.
- Check package version changes before changing API-specific advice.
- Preserve the method map's distinction between prediction, inference, causal effect estimation, forecasting, survival analysis, and unsupervised discovery.
- When adding a method, include its appropriate use case, when to avoid it, and the validation/diagnostic implication.
