# Chinese-English Statistical Learning Glossary

Use this glossary to keep Chinese explanations consistent while preserving standard English terms.

| 中文 | English | Note |
| --- | --- | --- |
| 统计学习 | statistical learning | Broad field connecting statistics and machine learning. |
| 监督学习 | supervised learning | Target labels are observed. |
| 无监督学习 | unsupervised learning | No target labels; discover structure. |
| 半监督学习 | semi-supervised learning | Few labeled samples plus many unlabeled samples. |
| 回归 | regression | Predict or model continuous outcomes unless otherwise specified. |
| 分类 | classification | Predict discrete labels. |
| 泛化误差 | generalization error | Out-of-sample error on new data. |
| 偏差-方差权衡 | bias-variance tradeoff | Simplicity versus flexibility tradeoff. |
| 正则化 | regularization | Penalize complexity to reduce overfitting. |
| 过拟合 | overfitting | Model learns noise or validation artifacts. |
| 欠拟合 | underfitting | Model too simple for signal. |
| 泄漏 | leakage | Validation/test information enters training. |
| 交叉验证 | cross-validation | Repeated train/validation splitting. |
| 嵌套交叉验证 | nested cross-validation | Separates tuning from performance estimation. |
| 校准 | calibration | Predicted probabilities match observed frequencies. |
| 阈值调优 | threshold tuning | Choose decision cutoff after probability scoring. |
| 混杂 | confounding | Common causes distort exposure-outcome association. |
| 因果识别 | causal identification | Assumptions/design enabling causal effect estimation. |
| 倾向得分 | propensity score | Probability of treatment given covariates. |
| 双重稳健 | doubly robust | Consistent if one of treatment/outcome nuisance models is correct under assumptions. |
| 工具变量 | instrumental variable | Exogenous variable shifting treatment only through treatment path. |
| 断点回归 | regression discontinuity | Local quasi-experiment around cutoff. |
| 双重差分 | difference-in-differences | Compare treated/control changes over time. |
| 删失 | censoring | Event time is only partially observed. |
| 比例风险 | proportional hazards | Cox model hazard ratio constant over time. |
| 生存函数 | survival function | Probability event has not happened by time `t`. |
| 危险率 | hazard rate | Instantaneous event rate among survivors. |
| 面板数据 | panel data | Repeated observations of entities over time. |
| 固定效应 | fixed effects | Control time-invariant entity heterogeneity. |
| 随机效应 | random effects | Model group/entity effects as random variables. |
| 聚类稳健标准误 | cluster-robust standard errors | Uncertainty robust to within-cluster dependence. |
| 多重检验 | multiple testing | Many hypotheses increase false positives. |
| 错误发现率 | false discovery rate | Expected share of false positives among discoveries. |
| 降维 | dimensionality reduction | Replace features by lower-dimensional representation. |
| 主成分分析 | principal component analysis | Linear directions of maximal variance. |
| 因子分析 | factor analysis | Latent factors explain covariance plus noise. |
| 聚类 | clustering | Group similar observations without labels. |
| 异常检测 | anomaly detection | Identify rare/unusual observations. |
| 时间序列 | time series | Ordered observations over time. |
| 滚动验证 | rolling-origin validation | Forecast backtest preserving time order. |
| 推荐系统 | recommender system | Predict/rank user-item relevance. |
| 排序学习 | learning to rank | Optimize ordered relevance. |
| 空间自相关 | spatial autocorrelation | Nearby observations are statistically dependent. |
| 图神经网络 | graph neural network | Neural model using graph message passing. |
| 表示学习 | representation learning | Learn useful features/embeddings. |
| 共形预测 | conformal prediction | Prediction sets/intervals with coverage under exchangeability. |
| 量化金融 | quantitative finance | Statistical and computational methods for financial markets. |
| 因子暴露 | factor exposure | Sensitivity of asset/portfolio returns to factor returns or characteristics. |
| 阿尔法 | alpha | Regression intercept or excess performance not explained by benchmark/factors. |
| 贝塔 | beta | Market or factor sensitivity. |
| 因子收益 | factor return | Return of a factor-mimicking portfolio or asset-pricing factor. |
| 风险模型 | risk model | Model decomposing portfolio risk into factors and idiosyncratic risk. |
| 夏普比率 | Sharpe ratio | Excess return per unit volatility. |
| 信息比率 | information ratio | Active return per unit tracking error. |
| 最大回撤 | maximum drawdown | Largest peak-to-trough wealth decline. |
| 在险价值 | value at risk | Quantile-based loss threshold. |
| 预期损失 | expected shortfall | Average tail loss beyond VaR threshold. |
| 换手率 | turnover | Portfolio trading intensity across rebalances. |
| 幸存者偏差 | survivorship bias | Bias from excluding failed/delisted assets. |
| 未来函数 / 前视偏差 | look-ahead bias | Using information unavailable at decision time. |
| 点时数据 | point-in-time data | Data as known at a historical timestamp. |
| 协整 | cointegration | Stationary long-run relationship among nonstationary series. |
| 风险平价 | risk parity | Allocation targeting balanced risk contributions. |
| Black-Litterman模型 | Black-Litterman model | Portfolio framework blending market-implied priors with investor views. |
