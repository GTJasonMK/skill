# Source Coverage Map

## Contents

- [Purpose](#purpose)
- [Task Router Boundary](#task-router-boundary)
- [Coverage Rules](#coverage-rules)
- [Chapter 1: Factor Investing Foundations](#chapter-1-factor-investing-foundations)
- [Chapter 2: Factor Methodology](#chapter-2-factor-methodology)
- [Chapter 3: Main Factor Interpretation](#chapter-3-main-factor-interpretation)
- [Chapter 4: Multi-Factor Models](#chapter-4-multi-factor-models)
- [Chapter 5: Anomaly Research](#chapter-5-anomaly-research)
- [Chapter 6: Current Factor Research](#chapter-6-current-factor-research)
- [Chapter 7: Factor Investing Practice](#chapter-7-factor-investing-practice)
- [Exact-Source Lookup Rules](#exact-source-lookup-rules)

## Purpose

Use this map when the user asks whether this skill covers a chapter, where a topic lives, or whether the skill is complete relative to the local `md/` summaries.

This file maps the seven local chapter summaries to the skill's references. It is an internal routing index, not a replacement for the source summaries.

## Task Router Boundary

Do not start ordinary factor research, backtest review, portfolio implementation, Smart Beta evaluation, or machine-learning factor work from this file.

Use [task-router.md](task-router.md) first for task-level routing. Use [reference-architecture.md](reference-architecture.md) only when the directory layout or load order is unclear. Use this file only when:

- The user asks whether a chapter or source topic is covered.
- The user asks where a chapter topic lives inside the skill.
- The user needs exact source table values, t-statistics, sample numbers, or chapter wording from the original `md/` summaries.
- The user asks to audit skill completeness against the local chapter summaries.

## Coverage Rules

- Treat the skill as a method, theory, and workflow knowledge base.
- Treat the one-level reference directories as reasoning-stage categories, not source chapters.
- Use `core/task-router.md` for ordinary task routing and this file for source coverage.
- Use `core/reference-architecture.md` for directory roles and default load order.
- Use references for definitions, formulas, research design, implementation guidance, and audit checklists.
- Use `methods/method-idea-anchors.md` for compressed center-idea anchors across factor methods, factor families, anomalies, models, portfolio practice, and ML methods.
- Use `core/chinese-term-router.md` for Chinese aliases that are covered under English or compressed reference wording.
- Use `core/decision-core.md` for the compact decision spine, context-efficient reference loading, mandatory output switches, and final self-review checklist. This is workflow support, not source-summary coverage.
- Use `core/full-analysis-run-record.md` for complete analysis records, strategy run records, audit traces, repair-loop records, claim-side classification, six-criteria gates, search-space/prior records, model-consistency checks, domain-logic checks, external evidence cards, variant registries, and stage-gate evidence trails. This is workflow support, not source-summary coverage.
- Use `strategy/strategy-development-map.md` and the split playbooks for "how should the agent think or explore" workflows.
- Use `strategy/strategy-worked-examples.md` for compact examples that map data fields to method anchors, first hypotheses, baselines, loopholes, and next decisions. This is workflow support, not source-summary coverage.
- Use `data/data-analysis-and-external-research.md` for data-artifact analysis, script-first diagnostics, external lookup, and local fit checks. This is workflow support, not a source-summary replacement.
- Use `strategy/strategy-development-map.md` for data-feature entrypoint selection, build-diagnose-repair loops, and phenomenon-driven strategy iteration. This is agent operating guidance, not chapter-summary replacement.
- Use `strategy/research-governance.md` for decision ledgers, evidence conflict resolution, stage gates, and experiment discipline. This is workflow support, not a source-summary replacement.
- Use `strategy/forward-test-scenarios.md` to validate skill behavior on realistic prompts. This is maintenance support, not source-summary coverage.
- Use the original `md/` summaries for exact table values, long derivations, page-level wording, or chapter-summary reproduction.
- Do not duplicate full source chapters inside the skill. Keep source-derived content compressed into reusable cards.

Source summary files:

| Chapter | Source summary |
| --- | --- |
| 1 | `/home/fufu/Code/因子量化分析skill/md/第一章_因子投资基础_总结.md` |
| 2 | `/home/fufu/Code/因子量化分析skill/md/第二章_因子投资方法论_总结.md` |
| 3 | `/home/fufu/Code/因子量化分析skill/md/第三章_主流因子解读_总结.md` |
| 4 | `/home/fufu/Code/因子量化分析skill/md/第四章_多因子模型_总结.md` |
| 5 | `/home/fufu/Code/因子量化分析skill/md/第五章_异象研究_总结.md` |
| 6 | `/home/fufu/Code/因子量化分析skill/md/第六章_因子研究现状_总结.md` |
| 7 | `/home/fufu/Code/因子量化分析skill/md/第七章_因子投资实践_总结.md` |

## Chapter 1: Factor Investing Foundations

| Source topic | Reference coverage | Notes |
| --- | --- | --- |
| Formula completion and unified factor-investing equation | `theory-foundations.md`, `research-workflow.md` | Covers expected excess return, alpha, beta, factor premia, and variance-model view. |
| Factor, multi-factor model, and anomaly | `theory-foundations.md`, `research-workflow.md` | Separates characteristics, exposures, factor returns, pricing factors, anomalies, and portfolio alpha. |
| Alpha-side versus beta-lambda-side research | `theory-foundations.md`, `research-workflow.md`, `decision-core.md`, `full-analysis-run-record.md` | Use when explaining why factor investing includes both pricing and anomaly work; workflow files force `claim_side` so prediction, pricing, risk-model, and portfolio claims are not mixed. |
| Cross-sectional versus time-series perspective | `theory-foundations.md`, `method-map.md`, `econometrics-deep-dive.md` | Covers object estimated, regression choice, and interpretation. |
| Empirical asset pricing and academic origins | `theory-foundations.md` | Covers CAPM, APT, Fama, Hansen, Shiller, joint hypothesis. |
| Industry development, manager use, and investor use | `theory-foundations.md`, `data-and-implementation.md`, `smart-beta-style-attribution.md`, `chinese-term-router.md` | Covers return prediction, risk management, portfolio construction, active alpha versus active beta, crowding from flows, innovation sources, and factor products. |
| ETF examples and source tables | Original Chapter 1 `md` | Exact table values should be read from source. |

## Chapter 2: Factor Methodology

| Source topic | Reference coverage | Notes |
| --- | --- | --- |
| Factor-mimicking portfolios | `econometrics-deep-dive.md`, `smart-beta-style-attribution.md` | Covers target exposure, zero non-target exposures, and idiosyncratic-risk minimization idea. |
| Single sorting and tests | `method-map.md`, `econometrics-deep-dive.md` | Covers quantiles, spreads, monotonicity, weighting, t-tests. |
| Multi-sorting | `method-map.md`, `econometrics-deep-dive.md`, `factor-and-model-catalog.md` | Covers independent and conditional sorting, `2 x 3`, `5 x 5`, sparse-cell risks. |
| Factor naming conventions | `factor-and-model-catalog.md`, `a-share-model-evidence.md` | Covers factor families and CHN/LSL naming where relevant. |
| Time-series regression | `method-map.md`, `econometrics-deep-dive.md` | Covers alpha, beta, residuals, HAC/Newey-West use. |
| Cross-sectional regression | `method-map.md`, `econometrics-deep-dive.md`, `econometrics-advanced-notes.md` | Covers premia, exposures, Shanken correction, and pure factor interpretation. |
| Fama-MacBeth regression | `method-map.md`, `econometrics-deep-dive.md`, `econometrics-advanced-notes.md` | Covers two-step structure, time-series standard errors, overlapping-return caution. |
| Regression-method comparison | `econometrics-advanced-notes.md` | Covers time-series versus cross-sectional regression and different estimated objects. |
| Factor exposures and factor returns | `econometrics-deep-dive.md`, `econometrics-advanced-notes.md`, `practice-deep-dive.md` | Covers traded-factor and non-traded-factor cases, characteristics-as-exposures, and risk-model factor returns. |
| Method center-idea anchors | `method-idea-anchors.md`, `method-map.md`, `factor-and-model-catalog.md` | Compresses sorting, regression, anomaly tests, model comparison, orthogonalization, GMM, Bayesian priors, and p-hacking controls into first-principle method anchors. |
| EIV and instrumental variables | `econometrics-advanced-notes.md` | Covers generated beta errors and non-overlapping historical instruments. |
| Anomaly tests | `method-map.md`, `econometrics-deep-dive.md`, `validation-and-risks.md` | Covers time-series alpha, cross-sectional controls, and evidence hierarchy. |
| White and Newey-West estimators | `method-map.md`, `econometrics-deep-dive.md` | Covers heteroskedasticity and autocorrelation robust errors. |
| GRS test | `method-map.md`, `econometrics-deep-dive.md`, `econometrics-advanced-notes.md` | Covers joint alpha test and geometry. |
| Mean-variance spanning | `method-map.md`, `econometrics-deep-dive.md`, `econometrics-advanced-notes.md` | Covers spanning logic and difference from GRS. |
| Alpha tests | `method-map.md`, `econometrics-deep-dive.md` | Covers average and absolute alpha comparison. |
| Bayesian model comparison | `econometrics-advanced-notes.md`, `behavioral-and-factor-zoo-details.md` | Covers marginal likelihood, Bayesian factor, and prior caution. |
| Orthogonalization and regression geometry | `method-map.md`, `econometrics-deep-dive.md`, `econometrics-advanced-notes.md` | Covers order dependence and projection view. |
| GMM framework, math, effectiveness, warnings | `method-map.md`, `econometrics-deep-dive.md`, `econometrics-advanced-notes.md` | Covers moments, weighting, J-test, and non-black-box use. |
| Full derivations and equation-by-equation walkthroughs | Original Chapter 2 `md` | Use source when exact derivation steps are requested. |

## Chapter 3: Main Factor Interpretation

| Source topic | Reference coverage | Notes |
| --- | --- | --- |
| Data sources and empirical setup | `a-share-data-details.md`, `data-and-implementation.md` | Covers A-share defaults and timing rules. |
| Price adjustment, suspension, reopening, stale prices | `a-share-data-details.md` | Covers forward/backward adjustment, long suspension, price limits, and minimum trading-day rules. |
| Financial report timing and record types | `a-share-data-details.md`, `data-and-implementation.md` | Covers report period, announcement date, correction/restatement, single-quarter, and TTM construction. |
| Factor construction workflow | `a-share-data-details.md`, `data-and-implementation.md`, `research-workflow.md` | Covers universe, financial-stock exclusion, blacklist, outliers, sorting, rebalancing, tradability. |
| Market factor | `factor-and-model-catalog.md`, `theory-foundations.md`, `method-map.md`, `a-share-model-evidence.md` | Covers CAPM, Black CAPM/zero-beta intuition, market beta, low-beta caveats, and time-series versus cross-section lesson. |
| Size factor | `factor-and-model-catalog.md`, `a-share-model-evidence.md`, `factor-mechanism-diagnostics.md` | Covers small-cap premium, A-share caveats, equal versus value weighting, microcap/shell-value checks, 壳价值/借壳上市/市值最低的 30% filters, distress/liquidity explanations, and Berk-style omitted-risk proxy. |
| Value factor | `factor-and-model-catalog.md`, `a-share-model-evidence.md`, `factor-mechanism-diagnostics.md` | Covers BM, EP, EP versus BM, A-share model comparison, operating leverage, intangible information, R&D/accounting distortions, and value-trap diagnostics. |
| Momentum factor | `factor-and-model-catalog.md`, `behavioral-and-factor-zoo-details.md`, `factor-mechanism-diagnostics.md` | Covers underreaction, reversal contamination, A-share weakness, momentum crash, residual momentum, earnings/industry/news momentum, CGO, and cost/crash diagnostics. |
| Profitability factor | `factor-and-model-catalog.md`, `a-share-model-evidence.md`, `factor-mechanism-diagnostics.md` | Covers ROE/ROA, ROE(TTM), GP, ROTC, ROIC, RNOA, profitability level/quality/stability/growth, size-control caveats, and relation with value. |
| Investment factor | `factor-and-model-catalog.md`, `a-share-model-evidence.md`, `factor-mechanism-diagnostics.md` | Covers asset growth, 总资产增长/资产增长率/投资与总资产 aliases, q-theory, HXZ/q models, profitability controls, conditional sorting, M&A effects, and A-share transferability. |
| Turnover factor | `factor-and-model-catalog.md`, `data-and-implementation.md`, `a-share-model-evidence.md`, `validation-and-risks.md`, `factor-mechanism-diagnostics.md` | Covers speculation, PMO, 异常换手/异常成交量 definitions, A/B-share speculative demand, abnormal-volume horizon split, liquidity, short-leg contribution, costs, and implementation limits. |
| Main factor center-idea anchors | `method-idea-anchors.md`, `factor-and-model-catalog.md`, `factor-mechanism-diagnostics.md` | Gives compact anchors for market, size, value, profitability, investment, momentum, reversal, turnover/liquidity, low-volatility, IVOL, skewness/MAX, accrual quality, and dividend. |
| Exact descriptive-stat tables and empirical numbers | Original Chapter 3 `md` | Use source for table-specific values. |

## Chapter 4: Multi-Factor Models

| Source topic | Reference coverage | Notes |
| --- | --- | --- |
| Fama-French 3-factor model | `factor-and-model-catalog.md`, `method-map.md`, `model-construction-recipes.md` | Covers market, SMB, HML, `2 x 3` sorting, and factor formulas. |
| Carhart 4-factor model | `factor-and-model-catalog.md`, `method-map.md`, `model-construction-recipes.md` | Covers added momentum factor, skipped recent month, and construction caveats. |
| Novy-Marx 4-factor model | `factor-and-model-catalog.md`, `method-map.md`, `model-construction-recipes.md` | Covers gross profitability, PMU construction, and industry-neutral caution. |
| Fama-French 5-factor model | `factor-and-model-catalog.md`, `method-map.md`, `model-construction-recipes.md` | Covers profitability, investment, RMW/CMA, and adjusted SMB construction. |
| Hou-Xue-Zhang q-factor and q5 | `factor-and-model-catalog.md`, `method-map.md`, `behavioral-and-factor-zoo-details.md`, `model-construction-recipes.md` | Covers investment-based asset pricing, `2 x 3 x 3` construction, and q5 expected-growth addition. |
| Stambaugh-Yuan model | `factor-and-model-catalog.md`, `method-map.md`, `model-construction-recipes.md` | Covers mispricing-management/performance factors, anomaly ranks, 20/80 breakpoint caution, and middle-group special size construction. |
| Daniel-Hirshleifer-Sun model | `factor-and-model-catalog.md`, `method-map.md`, `model-construction-recipes.md` | Covers FIN, PEAD, CSI/NSI grouping, financing behavior, and announcement-window CAR. |
| Liu-Shi-Lian China models | `factor-and-model-catalog.md`, `a-share-model-evidence.md` | Covers China-specific size/value/profitability construction, shell-value contamination, and smallest-30% exclusion warnings. |
| A-share Fama-MacBeth evidence | `a-share-model-evidence.md`, `method-map.md` | Covers setup, priced factors, and interpretation. |
| CHN and LSL factor construction | `a-share-model-evidence.md` | Covers CHN-SMB/VMG and LSL-SMB/HML/RMW. |
| EP, BM, and ROE relation | `a-share-model-evidence.md` | Covers `EP = BM x ROE` and factor-correlation implications. |
| Model comparison, alpha, GRS, parsimony | `a-share-model-evidence.md`, `method-map.md`, `econometrics-advanced-notes.md` | Covers alpha reduction, GRS, average absolute alpha, parsimony index I/II, and simple-model preference. |
| Multi-factor model center-idea anchors | `method-idea-anchors.md`, `factor-and-model-catalog.md`, `model-construction-recipes.md` | Gives compact anchors for CAPM, FF3, Carhart, Novy-Marx, FF5, HXZ/q/q5, SY, DHS, and CHN/LSL model use. |
| Exact model-comparison tables | Original Chapter 4 `md` | Use source for table-specific returns, t-stats, and correlations. |

## Chapter 5: Anomaly Research

| Source topic | Reference coverage | Notes |
| --- | --- | --- |
| Value factor and value investing | `factor-and-model-catalog.md`, `theory-foundations.md`, `validation-and-risks.md` | Covers cheapness, risk/mispricing interpretations, and value traps. |
| F-Score | `factor-and-model-catalog.md`, `data-and-implementation.md`, `a-share-model-evidence.md`, `anomaly-construction-recipes.md` | Covers profitability, leverage/liquidity, operating-efficiency dimensions, 9 signals, and grouping. |
| G-Score | `factor-and-model-catalog.md`, `data-and-implementation.md`, `anomaly-construction-recipes.md` | Covers growth-firm fundamentals, conservative accounting signals, 8 signals, and A-share grouping caveats. |
| Expectation gap | `factor-and-model-catalog.md`, `behavioral-and-factor-zoo-details.md`, `anomaly-construction-recipes.md` | Covers valuation expectation versus fundamental expectation mismatch and double-sort recipes. |
| Fundamental anchoring reversal | `factor-and-model-catalog.md`, `behavioral-and-factor-zoo-details.md`, `anomaly-construction-recipes.md` | Covers fundamental anchor, price deviation, FAR/FUR construction, and reversal tests. |
| Idiosyncratic volatility | `factor-and-model-catalog.md`, `behavioral-and-factor-zoo-details.md`, `validation-and-risks.md`, `anomaly-construction-recipes.md`, `factor-mechanism-diagnostics.md` | Covers lottery demand, limits to arbitrage, IVOL estimation, 综合错误定价 and 条件双重排序, uncertainty versus residual-volatility decomposition, common IVOL factor, residual coskewness, implied skewness, and controls. |
| Anomaly and behavioral center-idea anchors | `method-idea-anchors.md`, `factor-and-model-catalog.md`, `factor-mechanism-diagnostics.md`, `behavioral-and-factor-zoo-details.md` | Gives compact anchors for F-Score, G-Score, expectation gap, fundamental anchoring reversal, PEAD, sentiment, limited attention, disposition effect/CGO, overconfidence, and disagreement. |
| A-share anomaly-specific empirical tables | Original Chapter 5 `md` | Use source for exact portfolio returns and table values. |

## Chapter 6: Current Factor Research

| Source topic | Reference coverage | Notes |
| --- | --- | --- |
| P-hacking and factor zoo | `theory-foundations.md`, `validation-and-risks.md`, `behavioral-and-factor-zoo-details.md`, `chinese-term-router.md`, `full-analysis-run-record.md`, `research-governance.md` | Covers p-value misuse, 多重假设检验, 先验概率, 后验概率, FDR/FWER, 发表偏差, publication decay, and workflow records for tested family, variants, search-space size, prior plausibility, multiple-testing control, and final-test policy. |
| Hard science and soft science | `behavioral-and-factor-zoo-details.md` | Covers why empirical finance has weaker replication conditions. |
| Bayesian p-values and priors | `behavioral-and-factor-zoo-details.md`, `chinese-term-router.md` | Covers prior probability, minimum Bayes factor, posterior interpretation, and Chinese aliases such as 先验概率 and 后验概率. |
| Factor zoo to factor war | `theory-foundations.md`, `behavioral-and-factor-zoo-details.md`, `factor-and-model-catalog.md`, `a-share-model-evidence.md` | Covers factor redundancy, model competition, q5, common-movement/covariance-structure purpose versus anomaly-count purpose, and model-purpose caution. |
| Behavioral finance explanations | `theory-foundations.md`, `behavioral-and-factor-zoo-details.md`, `factor-mechanism-diagnostics.md` | Covers limits to arbitrage, expectation bias, risk-preference bias, cognitive limits, control illusion, self-serving bias, mental accounting, narrow framing, bilingual behavior terms, and mechanism-to-test mappings. |
| Prospect theory and ambiguity aversion | `behavioral-and-factor-zoo-details.md` | Covers value function, probability weighting, and ambiguity aversion. |
| Behavioral explanations for anomalies | `behavioral-and-factor-zoo-details.md`, `factor-and-model-catalog.md`, `factor-mechanism-diagnostics.md` | Covers momentum, PEAD, value, IVOL, anchoring, disposition effect, CGO, limited attention tests, and lottery/skewness links. |
| Behaviorally efficient market | `behavioral-and-factor-zoo-details.md` | Covers market ecology and limits of simple efficiency/inefficiency labels. |
| Investor sentiment | `theory-foundations.md`, `behavioral-and-factor-zoo-details.md`, `smart-beta-style-attribution.md` | Covers measures, Baker-Wurgler components, PCA/PLS construction warnings, anomaly conditioning, and sentiment timing. |
| Risk compensation, mispricing, data snooping | `theory-foundations.md`, `validation-and-risks.md` | Covers evidence split, concrete mechanism tests, announcement/SUE checks, limited-attention checks, accounting-anomaly families, and data-snooping diagnostics. |
| Sample-out decay, crowding, costs | `validation-and-risks.md`, `chinese-term-router.md` | Covers publication decay, information timeliness, crowding metrics, turnover, trading cost, capacity, shrinkage, and Chinese aliases such as 估值价差、配对相关性、有效价差、冲击成本. |
| Fundamental analysis and quantamental limits | `theory-foundations.md`, `fundamental-quantamental.md` | Covers why factorization does not replace business judgment, quality-index signals, accounting decomposition, and BIG5-style failure modes. |
| Machine learning and factor investing | `ml-and-frontiers.md`, `validation-and-risks.md`, `playbook-portfolio-ml.md`, `chinese-term-router.md` | Covers linear/nonlinear models, Huber/elastic-net/boosting/bagging/random-forest/neural-network variants, mixed forecasts, OOS `R^2`, historical-mean versus zero benchmarks, Diebold-Mariano comparison, PCA/IPCA/risk-premium PCA, latent-factor cautions, A-share trading-friction feature importance, failure modes, leakage, final tests, and Chinese method aliases. |
| ML center-idea anchors | `method-idea-anchors.md`, `ml-and-frontiers.md` | Compresses regularized linear models, robust regression, trees/boosting, neural networks, mixed forecasts, PCA/IPCA, and OOS forecast tests into method anchors. |
| Exact examples and historical narrative | Original Chapter 6 `md` | Use source for extended examples or exact wording. |

## Chapter 7: Factor Investing Practice

| Source topic | Reference coverage | Notes |
| --- | --- | --- |
| Return model and alpha acquisition | `strategy-development-map.md`, `practice-deep-dive.md`, `data-and-implementation.md`, `playbook-factor-research.md`, `decision-core.md`, `full-analysis-run-record.md` | Covers prediction-variable workflow, six criteria, IC limits, screening versus ranking, parametric alpha forecast, and agent decision flow for factor-strategy exploration; core workflow now forces six-criteria grading before factor validity or promotion claims. |
| Practice-method center-idea anchors | `method-idea-anchors.md`, `practice-deep-dive.md`, `smart-beta-style-attribution.md` | Gives compact anchors for return models, investable universe optimization, screening/ranking, alpha forecasts, Barra risk models, pure factor portfolios, covariance shrinkage, optimization, costs, capacity, Smart Beta, mixing/integration, factor timing, style analysis, and risk attribution. |
| Data-feature strategy entrypoint and iterative repair | `core/decision-core.md`, `core/full-analysis-run-record.md`, `strategy/strategy-development-map.md`, `strategy/strategy-worked-examples.md`, `data/data-analysis-and-external-research.md`, `playbooks/playbook-factor-research.md`, `playbooks/playbook-data-backtest.md`, `core/report-templates.md` | Workflow support for selecting entrypoints from available fields, mapping fields to first hypotheses, freezing a baseline, diagnosing observed defects, recording claim side and reasoning gates, running targeted experiments, and deciding stop/promote. |
| Research governance, stage gates, and evidence conflicts | `core/full-analysis-run-record.md`, `strategy/research-governance.md`, `strategy/strategy-development-map.md`, `practice/validation-and-risks.md`, `core/report-templates.md` | Workflow support for run record snapshots, decision ledger snapshots, variant registries, search-space/prior discipline, conflicting evidence, experiment discipline, stage promotion, production readiness, monitoring, and stop/downgrade decisions. |
| Context-efficient decision spine and self-review | `core/decision-core.md`, `core/task-router.md`, `core/reference-architecture.md`, `strategy/strategy-development-map.md`, `strategy/research-governance.md` | Workflow support for object-timing-anchor-baseline-phenomenon-defect-experiment-gate reasoning, one-level directory routing, load-minimum routing, mandatory output switches, and final self-review before strategy recommendations. |
| Field-to-hypothesis worked examples | `strategy/strategy-worked-examples.md`, `methods/method-idea-anchors.md`, `strategy/strategy-development-map.md`, `data/data-analysis-and-external-research.md` | Workflow support for converting price-volume, announcement fundamentals, factor panels, optimizer outputs, trades, suspicious backtests, ML predictions, and alternative data into first falsifiable entrypoints. |
| Forward-test scenarios for agent behavior | `strategy/forward-test-scenarios.md`, `core/task-router.md`, `strategy/research-governance.md` | Maintenance support for checking whether the skill leads agents through method anchors, data evidence, decision ledgers, evidence conflicts, stage gates, and stop/promote discipline. |
| Investable universe optimization | `practice-deep-dive.md`, `a-share-data-details.md` | Covers low-liquidity, high-risk, and long-negative-alpha exclusions. |
| Barra risk model | `data-and-implementation.md`, `practice-deep-dive.md`, `chinese-term-router.md` | Covers 风险模型, 国家因子, 行业因子, 风格因子, WLS, 特质性风险, and pure factor portfolios. |
| Covariance matrix and adjustments | `practice-deep-dive.md`, `data-and-implementation.md`, `chinese-term-router.md` | Covers factor covariance, specific risk, 特征因子调整, 贝叶斯收缩, and 偏差统计量. |
| Portfolio optimization | `practice-deep-dive.md`, `data-and-implementation.md`, `playbook-portfolio-ml.md`, `full-analysis-run-record.md`, `report-templates.md` | Covers return/risk-model mismatch, objective-function formulas, equivalence conditions, constraints, tracking error, 换手率约束, cost models, risk parity, research-to-portfolio conversion, and workflow model-consistency checks across return, risk, cost, constraints, benchmark, universe, and horizon. |
| Data-analysis and external-research operating mode | `data-analysis-and-external-research.md`, `playbook-data-backtest.md`, `playbook-factor-research.md`, `playbook-portfolio-ml.md` | Workflow support for artifact-first diagnostics, statistical-learning script routing, official documentation/Context7 lookup, source priority, and local fit checks. It does not replace Chapter 7 source-summary coverage. |
| Smart Beta | `smart-beta-style-attribution.md`, `data-and-implementation.md`, `chinese-term-router.md` | Covers factor index conversion, five-level pyramid, MSCI quality lesson, fund/ETF review, fee and holdings audit, and Chinese aliases. |
| BetaPlus evidence | `smart-beta-style-attribution.md` | Covers BetaPlus 1000, factor-index evidence, dollar-cost averaging logic, and caveats. |
| Mixing versus integration | `smart-beta-style-attribution.md` | Covers multi-index allocation versus integrated multi-factor stock selection. |
| Factor allocation weights | `smart-beta-style-attribution.md` | Covers equal weight, inverse volatility, risk parity, maximum diversification, factor momentum. |
| Factor timing | `smart-beta-style-attribution.md`, `data-and-implementation.md` | Covers factor valuation decomposition, factor momentum, volatility/inverse-volatility weighting, sentiment, macro timing, cycle heuristics, and IC weighting. |
| Style analysis | `smart-beta-style-attribution.md`, `data-and-implementation.md`, `chinese-term-router.md` | Covers 风格分析, return-based style analysis, holdings-based style analysis, MECE/nonnegative/sum-to-one constraints, and long-short factor style analysis. |
| Buffett case | `smart-beta-style-attribution.md` | Covers style-attribution interpretation and limits. |
| Risk attribution | `smart-beta-style-attribution.md`, `data-and-implementation.md` | Covers standalone, marginal, component contribution, correlation-channel formula, and factor-model decomposition. |
| Alternative data | `ml-and-frontiers.md`, `data-and-implementation.md`, `smart-beta-style-attribution.md`, `playbook-portfolio-ml.md`, `chinese-term-router.md`, `full-analysis-run-record.md` | Covers technology match, domain knowledge, bias, short history, incremental contribution, 手机定位, 卫星数据, 专利数据, user-generated-data bias, timestamp/incremental-signal checks, and domain-logic/proxy-validity records. |
| Cross-asset factor allocation | `ml-and-frontiers.md`, `smart-beta-style-attribution.md`, `chinese-term-router.md` | Covers asset-class factor allocation, 尾部相关, 防御性择时, RTI/风险容忍指标, and DR/多样化比例. |
| Exact BetaPlus tables and case-specific numbers | Original Chapter 7 `md` | Use source for exact table values, index performance numbers, and long case details. |

## Exact-Source Lookup Rules

Use the original `md/` summaries when the user asks for:

1. Exact table values, t-statistics, correlations, or sample-period numbers.
2. The wording or structure of a chapter summary.
3. A long mathematical derivation beyond the compressed formulas in the references.
4. A book-specific case detail that is not needed for general method guidance.
5. A request to compare the skill content against the chapter summaries line by line.

For ordinary factor research, implementation, review, or explanation tasks, prefer the skill references first and load the original `md/` only when the requested detail is source-specific.
