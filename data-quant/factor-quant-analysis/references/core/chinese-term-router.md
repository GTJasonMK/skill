# Chinese Term Router

Use this file when a Chinese user phrase does not directly match an English heading in the skill. Route to the smallest reference that answers the term; do not use this as a substitute for [task-router.md](task-router.md).

## Contents

- [Purpose](#purpose)
- [Theory and Model Comparison](#theory-and-model-comparison)
- [Data and Accounting](#data-and-accounting)
- [Fundamental Factors and Anomalies](#fundamental-factors-and-anomalies)
- [Behavior and Sentiment](#behavior-and-sentiment)
- [Crowding, Costs, and Capacity](#crowding-costs-and-capacity)
- [Machine Learning and PCA](#machine-learning-and-pca)
- [Practice, Portfolio, and Products](#practice-portfolio-and-products)
- [Alias Rules](#alias-rules)

## Purpose

This file improves Chinese-language lookup. It maps Chinese factor-investing terms to the references where the actual workflow, method, or diagnostic rule lives.

For ordinary factor research, still start with [task-router.md](task-router.md). Use this file only when the user's Chinese wording is ambiguous, sparse in English headings, or likely to be missed by direct search.

## Theory and Model Comparison

| Chinese term | Equivalent or intent | First reference |
| --- | --- | --- |
| 收益率共同运动 / 共同运动 | Common movement in returns; factor model covariance purpose | [theory-foundations.md](../theory/theory-foundations.md), [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md) |
| 协方差结构 / 协方差矩阵 | Covariance structure or covariance matrix | [theory-foundations.md](../theory/theory-foundations.md), [practice-deep-dive.md](../practice/practice-deep-dive.md) |
| 有效前沿 / 最小方差前沿 | Efficient frontier or minimum-variance frontier | [econometrics-advanced-notes.md](../methods/econometrics-advanced-notes.md), [method-map.md](../methods/method-map.md) |
| 切点组合 / 切线组合 | Tangency portfolio | [econometrics-advanced-notes.md](../methods/econometrics-advanced-notes.md) |
| 最大夏普比率 / 切线组合夏普 | Maximum Sharpe ratio in GRS or spanning geometry | [econometrics-advanced-notes.md](../methods/econometrics-advanced-notes.md) |
| 张成检验 / 均值-方差张成 | Mean-variance spanning | [econometrics-advanced-notes.md](../methods/econometrics-advanced-notes.md), [method-map.md](../methods/method-map.md) |
| GRS / 联合 alpha 检验 | GRS joint alpha test | [econometrics-advanced-notes.md](../methods/econometrics-advanced-notes.md), [econometrics-deep-dive.md](../methods/econometrics-deep-dive.md) |
| 主动 alpha | Manager skill after factor exposures | [theory-foundations.md](../theory/theory-foundations.md), [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) |
| 主动 beta | Skill in allocating factor betas | [theory-foundations.md](../theory/theory-foundations.md), [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) |
| 形同意不同 | Similar variable, different model meaning | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md), [model-construction-recipes.md](../methods/model-construction-recipes.md) |
| 因子大战 | Factor war and model competition | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md), [a-share-model-evidence.md](../models-factors/a-share-model-evidence.md) |

## Data and Accounting

| Chinese term | Equivalent or intent | First reference |
| --- | --- | --- |
| 复权 | Price adjustment | [a-share-data-details.md](../data/a-share-data-details.md) |
| 停牌 / 复牌 | Suspension and reopening | [a-share-data-details.md](../data/a-share-data-details.md) |
| 财报更正 / 财报调整 | Restatement and point-in-time records | [a-share-data-details.md](../data/a-share-data-details.md), [data-and-implementation.md](../data/data-and-implementation.md) |
| 公告日 / 公告窗口 | Announcement date or event window | [a-share-data-details.md](../data/a-share-data-details.md), [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md) |
| 业绩预告 / 业绩快报 | Preliminary earnings or faster accounting signal | [validation-and-risks.md](../practice/validation-and-risks.md), [a-share-data-details.md](../data/a-share-data-details.md) |
| 信息时效性 | Information timeliness | [validation-and-risks.md](../practice/validation-and-risks.md), [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 30 天 / 120 天 | Post-update accounting signal decay windows | [validation-and-risks.md](../practice/validation-and-risks.md) |
| 单季度 / TTM | Single-quarter and trailing-twelve-month data | [a-share-data-details.md](../data/a-share-data-details.md) |
| 股东权益均值 / 少数股东权益 | Equity denominator and minority-interest treatment | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [a-share-data-details.md](../data/a-share-data-details.md) |
| 黑名单 / 不可交易股票 | Universe and tradability exclusion | [a-share-data-details.md](../data/a-share-data-details.md), [practice-deep-dive.md](../practice/practice-deep-dive.md) |
| 壳价值 / 借壳上市 / 市值最低的 30% | A-share shell-value contamination and smallest-30% exclusion | [a-share-model-evidence.md](../models-factors/a-share-model-evidence.md), [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) |
| 退市偏差 / 净资产为负 | Delisting bias, negative net assets, and investable-universe exclusion | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [a-share-data-details.md](../data/a-share-data-details.md) |

## Fundamental Factors and Anomalies

| Chinese term | Equivalent or intent | First reference |
| --- | --- | --- |
| 盈利因子 / 质量因子 | Profitability or quality factor | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [factor-and-model-catalog.md](../models-factors/factor-and-model-catalog.md) |
| 毛利润 / 营业利润 | Gross or operating profitability | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [model-construction-recipes.md](../methods/model-construction-recipes.md) |
| ROE(TTM) | A-share profitability exposure | [a-share-model-evidence.md](../models-factors/a-share-model-evidence.md), [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) |
| ROTC / ROIC / RNOA | Profitability and operating-return variants | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) |
| 投入资本 / 有形资本 | Invested capital or tangible capital | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [fundamental-quantamental.md](../theory/fundamental-quantamental.md) |
| 净利润 / 自由现金流 | Net income or free cash flow | [fundamental-quantamental.md](../theory/fundamental-quantamental.md), [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) |
| 资产周转率 | Asset turnover | [fundamental-quantamental.md](../theory/fundamental-quantamental.md), [validation-and-risks.md](../practice/validation-and-risks.md) |
| 企业价值倍数 | Enterprise multiple | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [validation-and-risks.md](../practice/validation-and-risks.md) |
| 市盈率 / 市净率 / 市销率 / 市现率 | PE, PB, PS, PCF valuation multiples | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [factor-and-model-catalog.md](../models-factors/factor-and-model-catalog.md) |
| 应计 / 应计异象 | Accruals and earnings quality | [anomaly-construction-recipes.md](../methods/anomaly-construction-recipes.md), [validation-and-risks.md](../practice/validation-and-risks.md) |
| 应计项目 / 现金流含量 | Accrual items and cash-flow content of earnings | [anomaly-construction-recipes.md](../methods/anomaly-construction-recipes.md), [fundamental-quantamental.md](../theory/fundamental-quantamental.md) |
| 销售费用 / 广告费用 / 研发费用 / 资本性支出 | G-Score conservative accounting inputs | [anomaly-construction-recipes.md](../methods/anomaly-construction-recipes.md), [fundamental-quantamental.md](../theory/fundamental-quantamental.md) |
| 低 BM / 高 BM | Growth versus value valuation state | [anomaly-construction-recipes.md](../methods/anomaly-construction-recipes.md), [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) |
| 预期差组合 / 非预期差组合 | Expectation gap portfolios | [anomaly-construction-recipes.md](../methods/anomaly-construction-recipes.md), [factor-and-model-catalog.md](../models-factors/factor-and-model-catalog.md) |
| 基本面锚定 / 基本面锚定反转 | Fundamental anchoring reversal | [anomaly-construction-recipes.md](../methods/anomaly-construction-recipes.md), [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md) |
| 短期反转 / 长期反转 | Short-term or long-term return reversal | [anomaly-construction-recipes.md](../methods/anomaly-construction-recipes.md), [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) |
| 过度反应 / 反应不足 | Overreaction or underreaction mechanism | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md), [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) |
| 标准化预期外盈利 / 超预期盈利 / SUE | Standardized unexpected earnings and earnings-surprise drift | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [validation-and-risks.md](../practice/validation-and-risks.md) |
| 盈利波动 / 盈利稳定性 / 盈利增长 | Profitability volatility, stability, and growth dimensions | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [factor-and-model-catalog.md](../models-factors/factor-and-model-catalog.md) |
| 总资产增长 / 资产增长率 / 投资与总资产 | Asset growth and investment-to-assets investment proxies | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [a-share-model-evidence.md](../models-factors/a-share-model-evidence.md) |
| 低投资 / 高投资 | Conservative versus aggressive investment groups | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [model-construction-recipes.md](../methods/model-construction-recipes.md) |
| 异常换手 / 异常换手率 / 异常成交量 | Abnormal turnover or abnormal volume | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [a-share-model-evidence.md](../models-factors/a-share-model-evidence.md) |
| B 股 / A/B 股 | A/B-share speculative-demand evidence | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [a-share-model-evidence.md](../models-factors/a-share-model-evidence.md) |
| 财务困境 / O-分数 | Distress or O-Score | [validation-and-risks.md](../practice/validation-and-risks.md), [model-construction-recipes.md](../methods/model-construction-recipes.md) |
| 股票净发行量 / 复合股权发行量 | Net stock issuance or composite equity issuance | [model-construction-recipes.md](../methods/model-construction-recipes.md), [validation-and-risks.md](../practice/validation-and-risks.md) |
| 净发行 / 回购 / 外部融资 / 新增发债 | Financing and issuance anomalies | [model-construction-recipes.md](../methods/model-construction-recipes.md), [validation-and-risks.md](../practice/validation-and-risks.md) |
| 综合错误定价 | Composite mispricing score | [anomaly-construction-recipes.md](../methods/anomaly-construction-recipes.md), [model-construction-recipes.md](../methods/model-construction-recipes.md) |
| 条件双重排序 | Conditional double sorting | [method-map.md](../methods/method-map.md), [econometrics-deep-dive.md](../methods/econometrics-deep-dive.md) |
| 不确定性 / 共同 IVOL | IVOL uncertainty and common IVOL factor | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [anomaly-construction-recipes.md](../methods/anomaly-construction-recipes.md) |

## Behavior and Sentiment

| Chinese term | Equivalent or intent | First reference |
| --- | --- | --- |
| 控制幻觉 / 自利偏差 | Illusion of control or self-serving bias | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md) |
| 心理账户 | Mental accounting | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md), [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) |
| 狭隘框架 | Narrow framing | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md) |
| 有限注意力 | Limited attention | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md), [validation-and-risks.md](../practice/validation-and-risks.md) |
| 星期五 / 同步公告 / 多家公司公告 | Limited-attention PEAD tests | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md), [validation-and-risks.md](../practice/validation-and-risks.md) |
| 处置效应 / CGO | Disposition effect and capital gains overhang | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md), [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) |
| 52 周高点 / 历史高点 | Anchoring reference prices | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md), [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) |
| Ellsberg / 模糊厌恶 | Ambiguity aversion | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md) |
| 损失厌恶 / 小概率权重 | Prospect-theory value and probability weighting | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md) |
| 彩票股 / 右偏 / 左尾 | Lottery demand and skewness | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md), [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) |
| 分析师覆盖 / 媒体报道 / 机构投资者占比 | Attention or arbitrage-cost proxies | [validation-and-risks.md](../practice/validation-and-risks.md), [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md) |
| 负面新闻 | Arbitrage cost, attention, or sentiment proxy | [validation-and-risks.md](../practice/validation-and-risks.md), [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md) |
| 封闭式基金折价 / IPO 数量 / 股利溢价 | Baker-Wurgler sentiment components | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md), [theory-foundations.md](../theory/theory-foundations.md) |
| 电话会议 / 管理者情绪 | Call-transcript or managerial sentiment | [ml-and-frontiers.md](../practice/ml-and-frontiers.md), [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md) |

## Crowding, Costs, and Capacity

| Chinese term | Equivalent or intent | First reference |
| --- | --- | --- |
| 样本外 | Out-of-sample test or decay | [validation-and-risks.md](../practice/validation-and-risks.md), [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 数据窥探 | Data snooping | [validation-and-risks.md](../practice/validation-and-risks.md), [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md) |
| 多重假设 / 多重假设检验 | Multiple testing burden in factor discovery | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md), [validation-and-risks.md](../practice/validation-and-risks.md) |
| 先验概率 / 后验概率 / 贝叶斯 p 值 | Bayesian prior and posterior interpretation of p-values | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md) |
| 发表偏差 / 伪回归 | Publication bias or spurious regression/data-mined evidence | [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md), [validation-and-risks.md](../practice/validation-and-risks.md) |
| 估值价差 | Factor valuation spread crowding proxy | [validation-and-risks.md](../practice/validation-and-risks.md), [data-and-implementation.md](../data/data-and-implementation.md) |
| 配对相关性 | Pairwise residual correlation crowding proxy | [validation-and-risks.md](../practice/validation-and-risks.md) |
| 因子反转 | Factor reversal as crowding proxy | [validation-and-risks.md](../practice/validation-and-risks.md), [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) |
| 做空持仓量 / 融券压力 | Short interest or borrow pressure | [validation-and-risks.md](../practice/validation-and-risks.md) |
| 有效价差 | Effective spread | [validation-and-risks.md](../practice/validation-and-risks.md), [playbook-data-backtest.md](../playbooks/playbook-data-backtest.md) |
| 冲击成本 / 市场冲击 | Market impact or impact cost | [validation-and-risks.md](../practice/validation-and-risks.md), [practice-deep-dive.md](../practice/practice-deep-dive.md) |
| 参与率 / ADV | Participation rate versus average daily volume | [validation-and-risks.md](../practice/validation-and-risks.md), [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md) |
| 线性成本 / 二次成本 | Linear and quadratic transaction-cost models | [practice-deep-dive.md](../practice/practice-deep-dive.md), [validation-and-risks.md](../practice/validation-and-risks.md) |
| 拥挤度 / 容量分析 | Crowding and capacity | [validation-and-risks.md](../practice/validation-and-risks.md), [strategy-development-map.md](../strategy/strategy-development-map.md) |

## Machine Learning and PCA

| Chinese term | Equivalent or intent | First reference |
| --- | --- | --- |
| 混合预测 | Ensemble forecast averaging | [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 稳健回归 / Huber | Robust regression and Huber loss | [ml-and-frontiers.md](../practice/ml-and-frontiers.md), [method-map.md](../methods/method-map.md) |
| 岭回归 / 套索回归 / 弹性网络 | Ridge, lasso, elastic net | [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 主成分回归 / 偏最小二乘 | PCR and PLS | [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 样条函数 | Spline terms in generalized linear models | [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 逻辑回归 / 多分类逻辑 | Logistic or multinomial models | [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 决策树 / 回归树 | Decision tree or regression tree | [ml-and-frontiers.md](../practice/ml-and-frontiers.md), [method-map.md](../methods/method-map.md) |
| 随机森林 / GBDT / XGBoost | Random forest, gradient boosting, XGBoost | [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 核函数 / SVM | Kernel methods and support vector machines | [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 神经网络 / DFN / RNN / LSTM | Neural-network variants | [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 批标准化 / 提前停止 / 学习率收缩 | Batch normalization, early stopping, learning-rate shrinkage | [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 历史均值 / 零预测基准 | Historical-mean versus zero-forecast benchmark | [ml-and-frontiers.md](../practice/ml-and-frontiers.md), [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md) |
| 特征重要性 | Feature importance and exposure overlap | [ml-and-frontiers.md](../practice/ml-and-frontiers.md), [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md) |
| 主成分分析 / PCA | Principal component analysis | [ml-and-frontiers.md](../practice/ml-and-frontiers.md), [method-map.md](../methods/method-map.md) |
| 隐性因子 / 潜在因子 | Latent factor | [ml-and-frontiers.md](../practice/ml-and-frontiers.md), [econometrics-deep-dive.md](../methods/econometrics-deep-dive.md) |
| 旋转不变性 | Rotation ambiguity or rotation invariance | [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 稀疏 PCA / 宏观四因子 | Sparse PCA and sparse macro factor model | [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 动态条件 / IPCA | Dynamic conditional model and instrumented PCA | [ml-and-frontiers.md](../practice/ml-and-frontiers.md), [method-map.md](../methods/method-map.md) |
| 风险溢价 PCA | Risk-premium PCA | [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 手机定位 / 卫星数据 | Geolocation or satellite alternative data | [ml-and-frontiers.md](../practice/ml-and-frontiers.md), [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md) |
| 专利 / 专利数据 | Patent or technology-link alternative data | [ml-and-frontiers.md](../practice/ml-and-frontiers.md), [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md) |
| 用户生成数据 | User-generated alternative data and selection bias | [ml-and-frontiers.md](../practice/ml-and-frontiers.md), [validation-and-risks.md](../practice/validation-and-risks.md) |

## Practice, Portfolio, and Products

| Chinese term | Equivalent or intent | First reference |
| --- | --- | --- |
| 管理人视角 | Manager use of factors | [theory-foundations.md](../theory/theory-foundations.md), [method-map.md](../methods/method-map.md) |
| 投资者视角 | Factor products and ETF selection | [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) |
| 市值加权 | Value-weighted portfolio | [factor-and-model-catalog.md](../models-factors/factor-and-model-catalog.md), [model-construction-recipes.md](../methods/model-construction-recipes.md) |
| 等权 | Equal-weight portfolio or allocation | [factor-and-model-catalog.md](../models-factors/factor-and-model-catalog.md), [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) |
| 风险模型 / Barra 风险模型 | Barra-style risk model for covariance and exposure control | [practice-deep-dive.md](../practice/practice-deep-dive.md), [data-and-implementation.md](../data/data-and-implementation.md) |
| 国家因子 / 行业因子 / 风格因子 | Country, industry, and style factors in a risk model | [practice-deep-dive.md](../practice/practice-deep-dive.md), [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) |
| 特征因子调整 / 特征因子组合 | Eigenfactor-like covariance adjustment | [practice-deep-dive.md](../practice/practice-deep-dive.md) |
| 贝叶斯收缩 / 偏差统计量 | Bayesian shrinkage and bias statistic for risk forecasts | [practice-deep-dive.md](../practice/practice-deep-dive.md) |
| 特质性风险 / 特质性收益率 | Specific or idiosyncratic risk and residual return | [practice-deep-dive.md](../practice/practice-deep-dive.md), [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) |
| 目标函数 | Optimization objective function | [practice-deep-dive.md](../practice/practice-deep-dive.md) |
| 换手率约束 | Turnover constraint or turnover cap | [practice-deep-dive.md](../practice/practice-deep-dive.md), [validation-and-risks.md](../practice/validation-and-risks.md) |
| 风险平价 | Risk parity portfolio objective or allocation rule | [practice-deep-dive.md](../practice/practice-deep-dive.md), [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) |
| 跟踪误差 | Tracking error | [practice-deep-dive.md](../practice/practice-deep-dive.md), [data-and-implementation.md](../data/data-and-implementation.md) |
| 风格分析 / 收益率基础风格分析 / 持仓基础风格分析 | Return-based or holdings-based style analysis | [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md), [data-and-implementation.md](../data/data-and-implementation.md) |
| 边际风险贡献 | Marginal risk contribution | [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) |
| 收益相关性 | Risk-source correlation channel | [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) |
| 五层金字塔 | Five-level factor index pyramid | [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) |
| MSCI 质量 | MSCI-style quality index lesson | [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) |
| 大类资产 | Cross-asset factor allocation | [ml-and-frontiers.md](../practice/ml-and-frontiers.md), [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) |
| 尾部相关 / 尾部相关性 | Tail correlation | [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md), [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| 防御性因子 / 防御性择时 | Defensive factor timing | [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md), [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| RTI / 风险容忍指标 | Risk tolerance indicator for factor allocation | [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md), [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |
| DR / 多样化比例 | Diversification ratio for correlation-breakdown monitoring | [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md), [ml-and-frontiers.md](../practice/ml-and-frontiers.md) |

## Alias Rules

- If the Chinese term is a broad task, route by [task-router.md](task-router.md) after identifying the closest task.
- If the term asks for exact table values, t-statistics, sample windows, or chapter wording, route to [source-coverage-map.md](source-coverage-map.md) and the original `md/` summaries.
- If several references are listed, load the first reference for concept and workflow; load the second only when the answer needs that implementation or product context.
- Do not add a new reference file for every Chinese synonym. Add aliases here only when direct search or headings are likely to miss the term.
