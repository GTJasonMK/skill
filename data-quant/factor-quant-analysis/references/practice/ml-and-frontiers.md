# Machine Learning and Frontiers

## Contents

- [Role of Machine Learning](#role-of-machine-learning)
- [Chinese Method Alias Matrix](#chinese-method-alias-matrix)
- [Linear and Regularized Models](#linear-and-regularized-models)
- [Mixed Forecasts and Ensembles](#mixed-forecasts-and-ensembles)
- [Nonlinear Models](#nonlinear-models)
- [Model Evaluation](#model-evaluation)
- [Unsupervised and Latent-Factor Methods](#unsupervised-and-latent-factor-methods)
- [Machine-Learning Failure Modes](#machine-learning-failure-modes)
- [Alternative Data](#alternative-data)
- [Asset-Class Factor Allocation](#asset-class-factor-allocation)

## Role of Machine Learning

In factor investing, machine learning mainly serves:

- Prediction: estimate future stock or market returns from many features.
- Feature selection: identify which firm characteristics or interactions matter.

It does not replace asset-pricing discipline. A machine-learning signal still needs point-in-time data, economic interpretation, robust validation, cost checks, capacity analysis, and risk attribution.

## Chinese Method Alias Matrix

Use this table when a user asks with Chinese method names.

| Chinese term | Method | First use check |
| --- | --- | --- |
| 稳健回归 / Huber | Robust regression, Huber loss | Heavy tails and outliers |
| 岭回归 / 套索回归 / 弹性网络 | Ridge, lasso, elastic net | Many correlated features |
| 主成分回归 / 偏最小二乘 | PCR, PLS | Dimensionality reduction with many predictors |
| 样条函数 | Spline terms in generalized linear models | Smooth nonlinear relation |
| 逻辑回归 / 多分类逻辑 | Logistic or multinomial model | Direction or return-group prediction |
| 决策树 / 回归树 | Decision tree or regression tree | Nonlinear interactions |
| 随机森林 | Random forest | Bagging tree ensemble |
| GBDT / XGBoost | Gradient boosting and XGBoost | Sequential residual fitting |
| 核函数 / SVM | Kernel support vector machine | Nonlinear boundary, smaller panels |
| 批标准化 / 提前停止 / 学习率收缩 | Batch normalization, early stopping, learning-rate shrinkage | Neural-network regularization |
| 历史均值 / 零预测基准 | Historical mean or zero forecast benchmark | OOS `R^2` denominator choice |
| 特征重要性 | Feature importance | Check hidden size, liquidity, beta, volatility, and industry exposure |
| 隐性因子 / 潜在因子 | Latent factors | PCA/IPCA interpretation and replication |
| 旋转不变性 | Rotation ambiguity or invariance | Latent factor space identification |
| 稀疏 PCA / 宏观四因子 | Sparse PCA macro factors | Interpretability through fewer macro variables |
| 动态条件 | Dynamic conditional model | IPCA with characteristics as exposure instruments |

## Linear and Regularized Models

OLS:

- Useful baseline.
- Fragile with many correlated predictors and outliers.

Weighted regression:

- Gives different weights to observations, such as more weight to cross-sections with more stocks.
- Related in spirit to Fama-MacBeth weighting choices.

Robust regression:

- Huber or similar losses reduce the influence of extreme returns.
- Useful because stock returns are heavy-tailed.

Huber-style loss:

```text
h(x; xi) = x^2,              if |x| <= xi
h(x; xi) = 2 * |xi| * |x| - xi^2,  if |x| > xi
```

Use it when large residuals are common but deleting observations would remove economically meaningful stress periods.

Ridge:

- Shrinks coefficients toward zero.
- Helps with correlated predictors.

Lasso:

- Performs variable selection by driving some coefficients to zero.
- Can be unstable when predictors are highly correlated.

Elastic net (弹性网络):

- Combines ridge and lasso.
- Often more stable for factor libraries with correlated signals.

Empirical Bayes or shrinkage (经验贝叶斯):

- Useful for stabilizing noisy factor premia, IC means, or many related signal estimates.
- Treat it as an estimation shrinkage device, not as evidence that a searched signal is real.

PLS and PCR:

- PCR uses principal components of predictors; this is principal component analysis (主成分分析) applied before regression.
- PLS extracts components that are more directly related to the target.
- Useful when many characteristics are collinear.

Generalized linear models:

- Add nonlinear transformations such as polynomial or spline terms.
- Logistic or multinomial models can predict positive excess return or return group membership instead of return magnitude.

## Mixed Forecasts and Ensembles

Mixed forecasts (混合预测) average or combine predictions from multiple models.

Use:

- Reduce dependence on a single model specification.
- Smooth errors when different models work in different regimes.
- Combine linear, penalized, tree, and neural-network forecasts after each model passes leakage checks.

Rules:

- Build each component forecast inside the same walk-forward window.
- Combine only out-of-sample predictions; do not average in-sample fitted values and call it an ensemble.
- Compare the mixed forecast with simple baselines and the best single model after costs.
- Inspect exposure overlap. An ensemble can still be only a disguised liquidity, size, or momentum signal.

Warning:

- Averaging many searched models does not remove p-hacking. Keep the searched model family and failed variants in the experiment log.

## Nonlinear Models

Trees:

- Capture interactions and nonlinear thresholds.
- Overfit easily without pruning or ensembling.

Random forest (随机森林):

- Reduces tree overfit by averaging many trees.
- Useful for nonlinear interactions but can be hard to map to economic exposures.

Bagging:

- Trains many models on bootstrap samples in parallel.
- Averages predictions to reduce variance.
- Random forest is the standard tree-based example.

GBDT/XGBoost:

- Strong tabular predictor.
- Requires strict walk-forward tuning and feature leakage checks.

Boosting:

- Trains weak learners sequentially, each step focusing on errors left by earlier steps.
- AdaBoost changes observation weights after mistakes.
- GBDT fits new regression trees to previous residuals.
- LPBoost and LogitBoost are related boosting variants.
- XGBoost improves regularization, sparsity handling, and computation around gradient boosting.

SVM:

- Uses kernels to create nonlinear decision boundaries.
- Historically important before boosting/deep learning dominated many tabular tasks.
- Can be expensive and less interpretable in large panels.

Neural networks (神经网络):

- Can model complex nonlinearities.
- Need large data, regularization, stable validation, and interpretability diagnostics.

Training and variants:

- SGD trades exact optimization for scalable updates.
- Learning-rate shrinkage, early stopping, batch normalization, and ensembling are common regularizers.
- DFN can model nonlinear cross-sectional relations.
- RNN and LSTM are relevant only when sequence structure is economically meaningful and validation is strict.

## Model Evaluation

Out-of-sample `R^2`:

```text
R^2_OOS = 1 - sum((R - R_hat)^2) / sum((R - benchmark_forecast)^2)
```

Use a meaningful benchmark:

- Historical mean can be too easy.
- For individual stock-return prediction, a zero forecast (零预测基准) is often a fairer benchmark than each stock's historical mean (历史均值).
- Compare against linear models, simple factor composites, equal-weight signal scores, and production signals.

Book-style warning:

- Using historical mean instead of zero can mechanically raise reported individual-stock `R^2_OOS` by several percentage points.
- For cross-sectional stock-return prediction, an `R^2_OOS` above roughly `0.5%` can already be economically meaningful if turnover and costs are controlled.
- A positive `R^2_OOS` is not enough; also test ranking quality and net portfolio results.
- If a model only beats the historical-mean benchmark but not the zero-forecast benchmark, treat the prediction claim as weak for individual stocks.

Report together:

- OOS `R^2`.
- IC and rank IC.
- Quantile return spread.
- Turnover and rank stability.
- Net returns after cost.
- Drawdown and tail behavior.
- Exposure overlap with known factors.

Validation rules:

- Use rolling or expanding walk-forward.
- Fit preprocessing inside each training window.
- Use purging/embargo when labels overlap.
- Keep an untouched final test.
- Record failed variants.

Deflated Sharpe ratio (平减夏普比率):

- Use when many strategies or model variants were tried.
- It adjusts the interpretation of high Sharpe ratios for selection and non-normality.
- It is a diagnostic, not a substitute for economic logic.

Gu et al.-style lesson:

- High-dimensional firm characteristics and interactions can improve prediction.
- Strong performance usually comes with strict validation, many features, and careful regularization.
- Model comparison must include simple baselines and economic interpretability.
- Full-feature OLS can perform poorly when predictors are many and correlated.
- Penalized linear models often beat unconstrained OLS.
- Tree models and neural networks can improve prediction, but their advantage must be tested against transaction costs and exposure overlap.
- In A-share applications, liquidity and trading-friction variables can be more important than in U.S. samples.
- For A shares, always compare the model's feature importance with turnover, Amihud illiquidity, price-limit risk, suspension risk, bid-ask or spread proxies, and market-impact proxies before treating a complex prediction as a new economic factor.

Diebold-Mariano-style comparison:

```text
d_12,t = average_i((e_i,t+1^(1))^2 - (e_i,t+1^(2))^2)
DM_12  = mean(d_12,t) / se(mean(d_12,t))
```

Interpretation:

- Positive `DM_12` means model 1 has larger squared prediction error than model 2 under this sign convention.
- Use HAC or block-aware standard errors when forecast errors are serially dependent.
- Pairwise forecast-error tests complement, but do not replace, portfolio-level net-return tests.

## Unsupervised and Latent-Factor Methods

PCA (主成分分析):

- Extracts latent factors (隐性因子 / 潜在因子) from return covariance.
- Useful when true factors are unobserved.
- Can lack direct economic interpretation.
- It relies on second moments; pure covariance PCA can miss first-moment expected-return information.

Sparse PCA:

- Produces more interpretable components by using fewer variables.
- Useful for macro factor extraction.
- Macro sparse-PCA examples can map components to nominal bond yield level, inflation, output, housing, and optimism-like sentiment; a sparse macro four-factor model (稀疏宏观四因子) adds market exposure to selected sparse macro components.

IPCA:

- Instrumented PCA parameterizes conditional factor exposures using firm characteristics.
- Handles dynamic conditional models better than static PCA.
- Useful when characteristics drive both exposures and expected returns.

Risk-premium PCA (风险溢价 PCA):

- Adds first-moment information to avoid relying only on covariance.
- Aims to extract factors that explain both co-movement and expected-return differences.

Key theoretical points:

- Linear factor models have rotation ambiguity or rotation invariance (旋转不变性): latent factor space can be identified up to rotation.
- Strong factors are easier to recover.
- Rotation ambiguity is not fatal for risk-premium estimation if the recovered factor space spans the true latent factors.
- Latent factors still need interpretation and investable implementation.

Practical caution:

- PCA/IPCA factors can have high in-sample Sharpe but weak investability.
- Mapping latent factors to portfolios may require shorting, leverage, and unstable weights.
- A high IPCA tangent-portfolio Sharpe can show strong explanatory information, but it does not prove a deployable long-only strategy.
- Dynamic conditional (动态条件) exposure modeling can improve fit, but it also raises the bar for point-in-time characteristic handling and out-of-sample validation.
- Always report whether latent-factor returns can be replicated with realistic weights, turnover, and constraints.

## Machine-Learning Failure Modes

Black-box risk:

- A model can predict without explaining.
- Inspect feature importance, partial dependence, regime stability, and overlap with industry/size/liquidity/beta/volatility.

Overfit risk:

- Financial history is one realized path.
- Monthly panels have few independent time periods.
- Repeated searches over features, labels, horizons, models, and hyperparameters create p-hacking.

Validation leakage:

- Random splits leak future regimes.
- Overlapping labels leak adjacent future returns.
- Full-sample scaling, imputation, neutralization, PCA, or feature selection leaks information.

Interpretation rule:

- A machine-learning result becomes a factor-investing result only after it is tied to a plausible mechanism, survives robust validation, and can be implemented after costs.

## Alternative Data

Alternative data (另类数据) is relative. Financial statements were once alternative to price/volume data; analyst forecasts, web data, text, geolocation, satellite images, and transaction data later became alternative.

Five checks:

1. Technology match: text, images, geolocation, and transaction data require suitable NLP, computer vision, entity mapping, and timestamping.
2. Domain knowledge: know how the data is generated and how it maps to business activity.
3. Data bias: user-generated or vendor-processed data can have selection, coverage, survivorship, and incentive biases.
4. Short history: many alternative datasets have only 2-5 years of history, increasing overfit and multiple-testing risk.
5. Incremental contribution: verify the data is not merely a proxy for existing value, momentum, quality, size, or liquidity signals.

Case lessons:

- The Tesla/Thasos-style geolocation or phone-location case (手机定位) is about timeliness: factory-area phone-location signals suggested night-shift and production changes before traditional financial disclosures.
- Geolocation around a factory can be useful only when the analyst understands the production process, shift schedule, entity mapping, and timing relative to earnings announcements.
- Satellite data (卫星数据) can support activity inference only when images of ports, oil fields, crops, parking lots, or ships map to real business quantities.
- Patent or technology-link data (专利数据) can work when it captures business relationships or knowledge spillovers, not merely patent counts.
- User-generated data (用户生成数据), such as employee reviews, can be noisy because of weak identity verification, negative-review selection, extreme ratings, company incentives to influence reviews, ambiguous star meanings, and uneven industry coverage.

Technology match:

| Data type | Typical techniques | Main failure mode |
| --- | --- | --- |
| Price and volume | Technical/statistical signals, microstructure filters | Crowded standard factors |
| Structured fundamentals | Multi-factor models, cross-sectional regressions | Point-in-time leakage and accounting mismatch |
| Text | NLP, entity recognition, tone and topic models | Wrong entity mapping or sentiment proxy |
| Images/audio/multimedia | Computer vision, deep learning | Short history and opaque features |
| Geolocation/satellite | Spatial mapping, activity inference, timestamp alignment | Incorrect business mapping or privacy/licensing risk |
| Consumer transactions | Merchant mapping, panel normalization | Coverage and selection bias |

Common sources:

- Web scraping: job postings, product rankings, promotions, company reviews.
- Sentiment: social media, news, announcements, earnings-call transcripts.
- Satellite/geolocation (卫星数据/手机定位): traffic, ports, oil fields, crops, factory activity.
- Patent data (专利): citations, technology classifications, firm links, and supply-chain or knowledge-spillover networks.
- User-generated data (用户生成数据): reviews, ratings, posts, and community content with selection and manipulation risk.
- Consumer transactions: credit/debit card or receipt-like spending data.

Compliance, privacy, licensing, and entity mapping are part of the research design, not afterthoughts.

Incremental-value tests:

- Correlate the alternative-data signal with existing value, quality, momentum, size, liquidity, volatility, and industry signals.
- Run Fama-MacBeth or portfolio tests with common factor controls and existing production signals.
- Check whether performance appears only in a short vendor backfill period.
- Test whether the signal has a plausible reporting lag, vendor update timestamp, and tradable execution delay.
- Reject the "new data" claim if the signal is only a disguised version of a cheaper standard factor.

## Asset-Class Factor Allocation

Asset allocation can be reframed as factor allocation. Assets such as equities, bonds, commodities, FX, credit, real estate, and inflation-linked instruments are bundles of underlying risk drivers.

Common drivers:

- Growth/equity risk.
- Real rates.
- Inflation.
- Credit.
- Commodity risk.
- Real estate.
- Liquidity.
- Carry, value, momentum, and defensive styles across asset classes.

Factor-mimicking portfolios:

- Construct tradable proxies for non-traded drivers such as real rates, credit, inflation, or liquidity.
- The quality of the proxy determines the quality of the allocation.

Tail correlation:

- Normal-period diversification can disappear in crises.
- Downside correlations across factors can rise sharply.

Defensive factor timing:

- Focuses on risk reduction, not return forecasting.
- Monitors risk appetite, factor correlations, and extreme factor valuation.

RTI (风险容忍指标):

```text
RTI = corr(rank(factor returns), rank(factor volatility))
```

Higher RTI means higher-risk factors are being rewarded; lower RTI signals risk appetite deterioration.

Diversification ratio / DR (多样化比例):

```text
DR = sum_i w_i sigma_i / sigma_portfolio
```

Higher DR means better diversification; falling DR means correlations are rising and diversification is weakening.
