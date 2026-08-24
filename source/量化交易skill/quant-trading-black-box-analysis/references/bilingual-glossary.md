# Bilingual Glossary And Chinese Concept Routing

Use this file when the user asks in Chinese, when source chapter terms need exact mapping, or when an agent must avoid losing meaning across Chinese and English quant terminology.

## Core Black-Box Terms

| 中文 | English | Route | Use In Reasoning |
| --- | --- | --- | --- |
| 量化交易 | quantitative trading | `black-box-framework.md` | Treat as systematic investment process, not automatically market-neutral or HFT. |
| 宽客 | quant | `black-box-framework.md` | Analyze as researcher/operator using explicit rules, data, and automation. |
| 黑箱 | black box | `black-box-framework.md` | Open into alpha, risk, cost, portfolio construction, execution, data, research, monitoring. |
| 伪宽客 | quasi-quant | `black-box-framework.md` | Identify human/manual stages and where systematic rules stop. |
| 市场效率 | market efficiency | `black-box-framework.md` | Ask whether the strategy improves price discovery/liquidity while earning risk-bearing profit. |
| 统计套利 | statistical arbitrage | `model-components.md` | Usually relative-value or spread convergence; check grouping, hedge ratio, costs, and crowding. |
| 配对交易 | pairs trade | `model-components.md` | Check pair similarity, spread stationarity, hedge ratio, and divergence risk. |
| 纪律 | discipline | `black-box-framework.md` | Automation reduces behavioral bias but amplifies bad specifications. |

## Alpha And Signal Terms

| 中文 | English | Route | Use In Reasoning |
| --- | --- | --- | --- |
| 阿尔法模型 | alpha model | `model-components.md` | Forecast or rank opportunities; do not equate with realized portfolio alpha. |
| 贝塔 | beta | `metrics-formulas.md` | Systematic market exposure; separate from alpha. |
| 趋势 | trend | `model-components.md` | Continuation hypothesis; test horizon and delay sensitivity. |
| 均值回复 | mean reversion | `model-components.md` | Convergence hypothesis; check adverse selection and structural breaks. |
| 技术情绪 | technical sentiment | `model-components.md` | Price/volume/flow signal; validate against costs and decay. |
| 价值/收益 | value/yield | `model-components.md` | P/E, E/P, yield, carry; check slow decay and crowded value risk. |
| 成长 | growth | `model-components.md` | Growth forecast; distinguish quality growth from overvaluation. |
| 品质 | quality | `model-components.md` | Leverage, income stability, earnings quality, management/fraud proxies. |
| 数据驱动 | data-driven | `model-components.md` | Strong false-discovery and sample-out controls required. |
| 投注结构 | bet structure | `SKILL.md` | Absolute, relative, paired, grouped, factor-neutral, inventory, or queue-position bet. |
| 投资期限 | horizon | `SKILL.md` | Must match data frequency, signal decay, turnover, and execution feasibility. |
| 贝叶斯更新 | Bayesian update | `metrics-formulas.md` | New evidence updates prior belief; do not replace priors blindly. |
| PEG | PEG ratio | `metrics-formulas.md` | Growth-adjusted valuation; validate growth estimate quality. |

## Risk Terms

| 中文 | English | Route | Use In Reasoning |
| --- | --- | --- | --- |
| 风险模型 | risk model | `model-components.md` | Identify unwanted exposures and size controls. |
| 风险度量 | risk measurement | `metrics-formulas.md` | Precision does not imply correctness. |
| 净敞口 | net exposure | `metrics-formulas.md` | Long minus short; directional bias. |
| 总敞口 | gross exposure | `metrics-formulas.md` | Long plus absolute short; leverage and balance-sheet usage. |
| 硬性约束 | hard constraint | `model-components.md` | Rule that cannot be violated by optimizer or sizing logic. |
| 惩罚函数 | penalty function | `model-components.md` | Soft constraint; riskier choices require more expected return. |
| 波动率 | volatility | `metrics-formulas.md` | Time-series uncertainty; may cluster and shift regimes. |
| 离散度 | cross-sectional dispersion | `metrics-formulas.md` | Cross-asset spread of returns; opportunity and risk context. |
| 凯利准则 | Kelly criterion | `metrics-formulas.md` | Sizing reference, not production sizing without haircuts. |
| 主成分分析 | PCA | `metrics-formulas.md` | Empirical risk factor extraction; check economic stability. |
| 风险内生性 | endogenous risk | `validation-risk-audit.md` | Strategy design/crowding can create the risk that later hurts it. |
| 模型风险 | model risk | `validation-risk-audit.md` | Wrong question, wrong model, wrong assumptions, or implementation bug. |
| 结构关系变化 | structural relationship change | `validation-risk-audit.md` | Correlations, spreads, factor payoffs, or relative relationships shift over time. |
| 外生冲击 | exogenous shock | `validation-risk-audit.md` | Regulation, war, credit events, macro crises, exchange outages, or rule changes. |
| 拥挤 | crowding | `validation-risk-audit.md` | Similar funds hold/liquidate similar positions. |
| 蔓延风险 | contagion risk | `validation-risk-audit.md` | Losses and liquidation transmit across related strategies/assets. |
| 压力测试 | stress test | `validation-risk-audit.md` | Simulate volatility, correlation, spread, liquidity, funding, and rule shocks. |
| 监控 | monitoring | `validation-risk-audit.md` | Track live alpha decay, risk exposure, cost drift, liquidity, data errors, and execution errors. |

## Cost, Portfolio, And Execution Terms

| 中文 | English | Route | Use In Reasoning |
| --- | --- | --- | --- |
| 交易成本模型 | transaction-cost model | `model-components.md` | Estimate pre-trade cost; distinct from execution algorithm. |
| 佣金和费用 | commissions and fees | `metrics-formulas.md` | Usually observable but not always dominant. |
| 滑点 | slippage | `metrics-formulas.md` | Decision price vs execution price; sign convention matters. |
| 市场冲击 | market impact | `metrics-formulas.md` | Own order moves price; capacity and liquidity sensitive. |
| 暗池 | dark pool | `model-components.md` | Hidden liquidity; assess information leakage and execution quality. |
| 常值/线性/分段/二次成本 | constant/linear/piecewise/quadratic costs | `metrics-formulas.md` | Choose model complexity based on size, liquidity, and speed. |
| 组合构建 | portfolio construction | `model-components.md` | Convert alpha/risk/cost/constraints into target holdings. |
| 等权 | equal weighting | `model-components.md` | Robust but ignores risk and signal magnitude. |
| 等风险 | equal risk weighting | `model-components.md` | Backward-looking risk can fail in regime shifts. |
| 阿尔法加权 | alpha-weighted sizing | `model-components.md` | Requires reliable magnitude forecasts. |
| 均值方差 | mean-variance optimization | `model-components.md` | Sensitive to expected returns, volatilities, correlations. |
| 有效边界 | efficient frontier | `metrics-formulas.md` | Frontier is only as reliable as inputs and constraints. |
| 替代效应 | substitution effect | `model-components.md` | Optimizer may choose correlated cheaper asset instead of highest-alpha asset. |
| 执行模型 | execution model | `model-components.md` | Converts target trades into actual orders. |
| 执行短缺 | implementation shortfall | `metrics-formulas.md` | Measures cost from decision price to final execution. |
| 进取订单 | aggressive order | `hft-market-structure.md` | Takes liquidity; pays spread for certainty/speed. |
| 被动订单 | passive order | `hft-market-structure.md` | Provides liquidity; earns spread/rebate but faces adverse selection. |
| 逆向选择 | adverse selection | `hft-market-structure.md` | Counterparty trades because they know/observe something adverse. |
| 暗订单 | hidden order | `model-components.md` | Hidden liquidity; affects queue and information exposure. |
| 扫架订单 | intermarket sweep order / ISO | `model-components.md` | Venue-routing mechanism; relevant in fragmented markets. |

## Data And Research Terms

| 中文 | English | Route | Use In Reasoning |
| --- | --- | --- | --- |
| 价格数据 | price data | `model-components.md` | Trades, quotes, bars, order book, corporate-action-adjusted prices. |
| 基本面数据 | fundamental data | `model-components.md` | Use announcement/vendor timestamps, not fiscal period end alone. |
| 另类数据 | alternative data | `model-components.md` | News, web, location, satellite, social; noisy and compliance-sensitive. |
| 标识符 | identifiers | `model-components.md` | Security master, ticker changes, delistings, mapping. |
| 缺失值 | missing values | `model-components.md` | Explicit policy; do not silently fill alpha-critical data. |
| 前视偏差 | lookahead bias | `validation-risk-audit.md` | Data available in file may not be available at decision time. |
| 幸存者偏差 | survivorship bias | `validation-risk-audit.md` | Historical universe must include dead/delisted assets. |
| 数据立方体 | data cube | `model-components.md` | Date x asset x field storage pattern. |
| 科学方法 | scientific method | `model-components.md` | Observe, theorize, test, attempt falsification. |
| 样本内 | in-sample | `validation-risk-audit.md` | Training/fitting data. |
| 样本外 | out-of-sample | `validation-risk-audit.md` | Validation data not used to fit parameters. |
| 过度拟合 | overfitting | `validation-risk-audit.md` | Too many conditions, fragile parameters, sample-specific success. |
| 最大回撤 | maximum drawdown | `metrics-formulas.md` | Path-dependent downside risk. |
| 胜率 | hit rate | `metrics-formulas.md` | Active profitable periods divided by active periods. |
| 参数敏感性 | parameter sensitivity | `validation-risk-audit.md` | Small parameter changes should not destroy a robust idea. |

## Critique And Due Diligence Terms

| 中文 | English | Route | Use In Reasoning |
| --- | --- | --- | --- |
| 批评 | critique | `validation-risk-audit.md` | Separate precise mechanism and evidence from broad anti-quant rhetoric. |
| 交易是艺术不是科学 | trading is art, not science | `validation-risk-audit.md` | Reject the false binary; judgment is used in model design and supervision. |
| 数据挖掘 | data mining | `validation-risk-audit.md` | Tool, not sin; overfitting and weak validation are the problem. |
| 规模 | scale / size | `validation-risk-audit.md` | Large scale helps infrastructure but can reduce flexibility and capacity. |
| 宽客完全相同 | quants are all the same | `validation-risk-audit.md` | Usually false; compare assets, data, alpha, horizon, costs, execution, and risk controls. |
| 尽调 | due diligence | `checklists.md` | Structured evaluation of strategy, team, integrity, and portfolio fit. |
| 信任 | trust | `validation-risk-audit.md` | Built through confidentiality, competence, consistent answers, and verifiable details. |
| 优势 | edge | `validation-risk-audit.md` | Sustainable source of excess return, cost advantage, data advantage, structural advantage, or process quality. |
| 诚信 | integrity | `checklists.md` | Check fiduciary mindset, background, consistency, and willingness to answer process questions. |
| 受托人 | fiduciary | `checklists.md` | Manager should act in the investor's best interest and disclose conflicts. |
| 背景核查 | background check | `checklists.md` | Verify education, employment, legal, regulatory, investor, and reputation details. |
| 组合适配 | portfolio fit | `checklists.md` | Assess whether alpha type, bet structure, horizon, and risk exposures diversify existing allocations. |

## HFT And Market Structure Terms

| 中文 | English | Route | Use In Reasoning |
| --- | --- | --- | --- |
| 高频交易 | high-frequency trading / HFT | `hft-market-structure.md` | Intraday, no overnight, high-speed infrastructure. |
| 超高频交易 | ultra-high-frequency trading / UHFT | `hft-market-structure.md` | More speed-sensitive subset of HFT. |
| 高频交易经济性 | HFT economics | `hft-market-structure.md` | Thin unit profits require large volume, strong infrastructure, and strict cost/risk control. |
| 高速交易/低延迟 | high-speed / low-latency trading | `hft-market-structure.md` | Infrastructure and process, not a strategy by itself. |
| 订单簿 | limit order book | `hft-market-structure.md` | Resting passive liquidity organized by price/time or price/size. |
| 连接 | joining | `hft-market-structure.md` | Add size at current best price. |
| 改进 | improving | `hft-market-structure.md` | Improve best quote and gain price priority. |
| 队列位置 | queue position | `metrics-formulas.md` | Determines passive fill priority and expected edge. |
| 微爆发 | microburst | `hft-market-structure.md` | Burst of messages; tail latency matters more than average latency. |
| NBBO | national best bid and offer | `hft-market-structure.md` | Reference quote in fragmented US markets, not full liquidity. |
| 订单流支付 | payment for order flow | `hft-market-structure.md` | Contractual market-making economics and agency issue. |
| 零售流动性程序 | Retail Liquidity Program / RLP | `hft-market-structure.md` | Retail order interaction mechanism; assess selection and routing. |
| 契约型做市 | contractual market making | `hft-market-structure.md` | Receives/fills routed flow, manages inventory and agency risks. |
| 非契约型做市 | noncontractual market making | `hft-market-structure.md` | Posts passive liquidity competitively without formal obligation. |
| 快速阿尔法 | fast alpha | `hft-market-structure.md` | Short-horizon statistical alpha; not structural arbitrage. |
| 老鼠仓/抢跑 | front-running | `hft-market-structure.md` | Requires non-public client-order misuse; faster public data is different. |
| 取消率 | cancellation rate | `metrics-formulas.md` | May reflect stale-quote control or manipulation; inspect mechanism. |
| 幻觉流动性 | phantom liquidity | `hft-market-structure.md` | Displayed depth disappears under stress; test executable liquidity. |
| 最小停留时间 | minimum resting time | `hft-market-structure.md` | Can create stale-order arbitrage against liquidity providers. |
| 金融交易税 | financial transaction tax / FTT | `hft-market-structure.md` | May reduce liquidity and shift costs to end investors. |
| 闪电崩盘 | Flash Crash | `hft-market-structure.md` | Diagnose market fragility, large orders, fragmentation, data delays, HFT withdrawal. |
| 骑士资本 | Knight Capital | `hft-market-structure.md` | Operational/software failure and low-latency risk-control lesson. |
| Waddell & Reed | Waddell & Reed | `hft-market-structure.md` | Large futures sell program in flash-crash analysis. |

## Future And Industry Terms

| 中文 | English | Route | Use In Reasoning |
| --- | --- | --- | --- |
| 透明 | transparency | `black-box-framework.md` | Future markets and investors may demand clearer process explanations. |
| 机器学习 | machine learning | `model-components.md` | More feasible with data/compute, but leakage and overfit risks remain. |
| 大数据 | big data | `model-components.md` | Alternative, large, noisy data; requires engineering and compliance. |
| 中频策略 | medium-frequency strategy | `hft-market-structure.md` | Between HFT and traditional quant; needs both microstructure and alpha research. |
| 监管 | regulation | `hft-market-structure.md` | Evaluate specific mechanism, not broad anti-quant claims. |
| 行业结构 | industry structure | `black-box-framework.md` | Infrastructure sharing, consolidation, specialization, investor acceptance. |
