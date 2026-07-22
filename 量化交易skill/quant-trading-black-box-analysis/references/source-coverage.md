# Source Coverage

This map links the 17 local chapter summaries to this skill's reusable reasoning modules. Use it when a task asks whether a topic is covered or when exact chapter context should be re-opened from `/home/fufu/Code/Skills/量化交易skill/md`. For Chinese-English term lookup, use `bilingual-glossary.md`.

| Chapter | Main Knowledge Points | Skill Location |
| --- | --- | --- |
| 1. 关注量化交易的原因 | quant success/failure, market scale, efficiency, statistical arbitrage, precise thinking, risk measurement, discipline | `black-box-framework.md`, `validation-risk-audit.md` |
| 2. 量化交易简介 | black-box definition, quant vs discretionary vs quasi-quant, alpha/risk/cost/portfolio/execution modules, data and research | `black-box-framework.md`, `model-components.md` |
| 3. 阿尔法模型 | alpha definition, theory vs data-driven models, trend, mean reversion, technical sentiment, value/yield, growth, quality, horizon, bet structure, signal mixing, PEG, Bayesian update | `model-components.md`, `metrics-formulas.md`, `reasoning-playbooks.md` |
| 4. 风险模型 | intended vs unintended exposure, hard limits, penalty functions, volatility, dispersion, VaR, Kelly, PCA, theoretical and empirical risk factors, external risk models | `model-components.md`, `validation-risk-audit.md`, `metrics-formulas.md` |
| 5. 交易成本模型 | commissions/fees, slippage, market impact, ECN rebates, dark pools, constant/linear/piecewise/quadratic cost models, participation rate | `model-components.md`, `metrics-formulas.md` |
| 6. 投资组合构建模型 | equal position, equal risk, alpha weighting, optimization, MPT, constraints, Black-Litterman, Grinold-Kahn, resampling, GARCH, substitution effect | `model-components.md`, `metrics-formulas.md` |
| 7. 执行模型 | electronic/manual execution, basket bidding, VWAP, mid-market, aggressive/passive orders, order types, smart routing, DMA, co-location, FIX | `model-components.md`, `hft-market-structure.md` |
| 8. 数据 | price/fundamental/alternative data, sources, security master, missing values, outliers, corporate actions, timestamps, lookahead, storage | `model-components.md`, `validation-risk-audit.md` |
| 9. 研究 | scientific method, idea sources, in-sample/out-of-sample testing, PnL, drawdown, predictive power, hit rate, ratios, delay, parameter sensitivity, assumptions | `model-components.md`, `validation-risk-audit.md`, `checklists.md`, `analysis-run-record.md`, `research-governance.md` |
| 10. 风险内生性 | model risk, relationship changes, exogenous shocks, contagion, crowding, 2007 quant crisis, PHM case, monitoring | `validation-risk-audit.md`, `research-governance.md` |
| 11. 对量化交易的批评 | art vs science, risk underestimation, volatility claims, 2008 crisis distinction, unusual events, strategy similarity, scale, data mining | `validation-risk-audit.md` |
| 12. 评估宽客和策略 | due diligence, interrogation method, six strategy modules, historical returns, manager quality, edge, integrity, portfolio fit | `validation-risk-audit.md`, `checklists.md`, `analysis-run-record.md`, `research-governance.md` |
| 13. 高速及高频交易概要 | HFT public attention, Aleynikov, flash crash, HFT definition, high-speed users, economics, low margins, competition | `hft-market-structure.md` |
| 14. 高速交易 | high-speed vs HFT, passive/aggressive orders, joining/improving, liquidity definition, adverse selection, queue position, latency, data bursts, risk checks, NBBO | `hft-market-structure.md`, `metrics-formulas.md` |
| 15. 高频交易 | contractual/noncontractual market making, retail flow, payment for order flow, Retail Liquidity Program, Knight Capital, arbitrage, fast alpha, HFT risk management, transaction costs | `hft-market-structure.md`, `metrics-formulas.md` |
| 16. 高频交易争论 | fairness, front-running, cancellation rates, phantom liquidity, volatility evidence, Waddell & Reed, flash crash causes, social value, regulation, FTT critique | `hft-market-structure.md`, `validation-risk-audit.md`, `reasoning-playbooks.md` |
| 17. 量化交易展望 | transparency, low-latency limits, research improvement, hybrid quant, ML, big data, medium-frequency strategies, investor acceptance, industry structure, regulation | `black-box-framework.md`, `model-components.md`, `hft-market-structure.md`, `research-governance.md` |

## Exact Local Source Files

The source summaries are in:

```text
/home/fufu/Code/Skills/量化交易skill/md/第1章_关注量化交易的原因.md
/home/fufu/Code/Skills/量化交易skill/md/第2章_量化交易简介.md
/home/fufu/Code/Skills/量化交易skill/md/第3章_阿尔法模型_宽客如何盈利.md
/home/fufu/Code/Skills/量化交易skill/md/第4章_风险模型.md
/home/fufu/Code/Skills/量化交易skill/md/第5章_交易成本模型.md
/home/fufu/Code/Skills/量化交易skill/md/第6章_投资组合构建模型.md
/home/fufu/Code/Skills/量化交易skill/md/第7章_执行模型.md
/home/fufu/Code/Skills/量化交易skill/md/第8章_数据.md
/home/fufu/Code/Skills/量化交易skill/md/第9章_研究.md
/home/fufu/Code/Skills/量化交易skill/md/第10章_量化策略的风险内生性.md
/home/fufu/Code/Skills/量化交易skill/md/第11章_对量化交易的批评.md
/home/fufu/Code/Skills/量化交易skill/md/第12章_评估宽客和量化交易策略.md
/home/fufu/Code/Skills/量化交易skill/md/第13章_高速及高频交易概要.md
/home/fufu/Code/Skills/量化交易skill/md/第14章_高速交易.md
/home/fufu/Code/Skills/量化交易skill/md/第15章_高频交易.md
/home/fufu/Code/Skills/量化交易skill/md/第16章_关于高频交易的争论.md
/home/fufu/Code/Skills/量化交易skill/md/第17章_量化交易的展望.md
```
