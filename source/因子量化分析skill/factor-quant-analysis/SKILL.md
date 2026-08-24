---
name: factor-quant-analysis
description: "Factor quant workflow for factor investing, empirical asset pricing, anomaly research, alpha signal testing, factor construction, data diagnostics, analysis run records, research governance/stage gates, external research/local fit checks, multi-factor models, A-share data, risk models, portfolio optimization, Smart Beta, factor timing, style analysis, risk attribution, ML factor selection, factor mechanism diagnosis, and validation of backtests, p-hacking, costs, crowding, and capacity. Use when Codex needs to design, explain, implement, review, or audit factor quant methods. 中文触发：因子投资、因子量化分析、A股因子研究、CAPM、APT、联合假说、行为金融、投资者情绪、因子动物园、因子大战、异象检验、多因子模型、排序法、Fama-MacBeth、Newey-West、GRS、GMM、工具变量、Shanken、贝叶斯 p 值、IC、rank IC、A股数据、复权、停牌、财报更正、Barra、WLS、纯因子组合、完整分析记录、策略运行记录、组合优化、交易成本、Smart Beta、BetaPlus、因子择时、风格分析、风险归因、机器学习选因子、PCA、IPCA、另类数据、回测审计、未来函数、拥挤度、容量分析、PMO、残差动量、动量崩溃、处置效应、CGO、剩余协偏度、隐含偏度、定投胜率。"
---

# Factor Quant Analysis

## Overview

Use this skill to turn factor-investing questions into a defensible research or implementation workflow. Treat factor work as a chain from economic hypothesis, point-in-time data, signal construction, empirical testing, model comparison, portfolio construction, and post-trade risk review.

This skill is based on the local chapter summaries for *因子投资：方法与实践* and should be used together with project-specific data/code conventions when those are available.

This skill is the domain workflow layer. When available, use `statistical-learning-analysis` bundled scripts for mechanical diagnostics, but keep research design, interpretation, and final judgment in this skill's workflow.

When local data artifacts or implementation uncertainty appear, switch from explanation mode to evidence mode: inspect the artifact, run the smallest relevant diagnostics, use authoritative external sources for exact API/rule/paper details, then validate the solution against the local market, data, and dependency constraints.

For strategy development, start from the data's feasible entrypoints, build the smallest falsifiable baseline, diagnose observed defects from actual results, and repair only the diagnosed weakness before adding complexity.

For broad strategy tasks, use the compact decision spine before loading larger references: object, timing, anchor, baseline, phenomenon, defect, experiment, and gate.

## Core Workflow

1. Classify the task: pricing factor, anomaly, return prediction variable, factor library, risk model, portfolio optimizer, Smart Beta product, factor timing, style analysis, risk attribution, or method review.
2. Define the object and horizon: asset universe, benchmark, rebalance date, execution date, holding period, return definition, weighting scheme, and tradability rule.
3. Build the point-in-time panel: use observable data only, align accounting availability dates, reconstruct historical universes, and remove ineligible stocks before computing ranks.
4. Construct signals: state direction, transform extreme values, standardize within date, optionally neutralize industry/size/beta/style, and preserve the raw and transformed versions.
5. Run first-pass validation: coverage, IC/rank IC, quantile portfolios, high-minus-low spread, monotonicity, turnover, and horizon decay.
6. Choose econometric tests by claim: sorting for intuition, Fama-MacBeth for cross-sectional premia, time-series regression for alpha/exposure, GRS or alpha tests for model comparison, and GMM only when moment conditions are explicit.
7. Diagnose explanation: distinguish risk compensation, mispricing, and data snooping; require economic or behavioral priors before treating a significant factor as credible.
8. Convert to implementation: estimate expected returns, risk exposures, covariance, constraints, costs, liquidity, capacity, and benchmark-relative exposures before claiming investable alpha.
9. Stress robustness: sample splits, walk-forward tests, alternative construction, neutralization sensitivity, multiple-testing controls, publication decay, crowding, and transaction-cost sensitivity.
10. Report assumptions and failures: separate signal evidence from portfolio evidence, gross from net, statistical significance from economic value, and regression alpha from implementable alpha.

## Reference Routing

- For ordinary work, read [references/core/task-router.md](references/core/task-router.md) first. It maps common tasks and failure modes to the smallest useful reference bundle.
- For a fast strategy reasoning spine, context-efficient routing, or final self-review, read [references/core/decision-core.md](references/core/decision-core.md).
- For complete analysis, strategy repair, backtest audit, or production-readiness tasks that need an auditable reasoning trace, read [references/core/full-analysis-run-record.md](references/core/full-analysis-run-record.md).
- For the directory layout or load-order uncertainty, read [references/core/reference-architecture.md](references/core/reference-architecture.md).
- For method selection, factor-family selection, central idea anchors, or "which method should I start from?" questions, read [references/methods/method-idea-anchors.md](references/methods/method-idea-anchors.md).
- For factor-strategy development, exploration, debugging, or productionization, read [references/strategy/strategy-development-map.md](references/strategy/strategy-development-map.md) after `core/task-router.md`.
- For concrete examples that turn data fields into a first hypothesis, baseline, loophole check, and next decision, read [references/strategy/strategy-worked-examples.md](references/strategy/strategy-worked-examples.md).
- For strategy stage gates, evidence conflicts, decision ledgers, repeated iterations, or promotion/stop decisions, read [references/strategy/research-governance.md](references/strategy/research-governance.md).
- For data files, schemas, code artifacts, backtest outputs, implementation uncertainty, external lookup, or exact API/market-rule questions, read [references/data/data-analysis-and-external-research.md](references/data/data-analysis-and-external-research.md).
- For chapter coverage, exact source lookup, or "is this covered?" questions, read [references/core/source-coverage-map.md](references/core/source-coverage-map.md).
- For Chinese term routing or ambiguous Chinese aliases, read [references/core/chinese-term-router.md](references/core/chinese-term-router.md).
- For user-facing deliverables, read [references/core/report-templates.md](references/core/report-templates.md) after the task-specific references.

- Core control: [references/core/decision-core.md](references/core/decision-core.md), [references/core/task-router.md](references/core/task-router.md), [references/core/full-analysis-run-record.md](references/core/full-analysis-run-record.md), [references/core/reference-architecture.md](references/core/reference-architecture.md), [references/core/report-templates.md](references/core/report-templates.md), [references/core/source-coverage-map.md](references/core/source-coverage-map.md), [references/core/chinese-term-router.md](references/core/chinese-term-router.md).
- Strategy workflow: [references/strategy/strategy-development-map.md](references/strategy/strategy-development-map.md), [references/strategy/strategy-worked-examples.md](references/strategy/strategy-worked-examples.md), [references/strategy/research-governance.md](references/strategy/research-governance.md), [references/strategy/forward-test-scenarios.md](references/strategy/forward-test-scenarios.md).
- Data and implementation: [references/data/data-analysis-and-external-research.md](references/data/data-analysis-and-external-research.md), [references/data/data-and-implementation.md](references/data/data-and-implementation.md), [references/data/a-share-data-details.md](references/data/a-share-data-details.md).
- Methods: [references/methods/method-idea-anchors.md](references/methods/method-idea-anchors.md), [references/methods/method-map.md](references/methods/method-map.md), [references/methods/econometrics-deep-dive.md](references/methods/econometrics-deep-dive.md), [references/methods/econometrics-advanced-notes.md](references/methods/econometrics-advanced-notes.md), [references/methods/model-construction-recipes.md](references/methods/model-construction-recipes.md), [references/methods/anomaly-construction-recipes.md](references/methods/anomaly-construction-recipes.md).
- Models and factors: [references/models-factors/factor-and-model-catalog.md](references/models-factors/factor-and-model-catalog.md), [references/models-factors/a-share-model-evidence.md](references/models-factors/a-share-model-evidence.md), [references/models-factors/factor-mechanism-diagnostics.md](references/models-factors/factor-mechanism-diagnostics.md).
- Playbooks: [references/playbooks/research-workflow.md](references/playbooks/research-workflow.md), [references/playbooks/agent-playbooks.md](references/playbooks/agent-playbooks.md), [references/playbooks/playbook-factor-research.md](references/playbooks/playbook-factor-research.md), [references/playbooks/playbook-data-backtest.md](references/playbooks/playbook-data-backtest.md), [references/playbooks/playbook-portfolio-ml.md](references/playbooks/playbook-portfolio-ml.md).
- Practice: [references/practice/practice-deep-dive.md](references/practice/practice-deep-dive.md), [references/practice/smart-beta-style-attribution.md](references/practice/smart-beta-style-attribution.md), [references/practice/validation-and-risks.md](references/practice/validation-and-risks.md), [references/practice/ml-and-frontiers.md](references/practice/ml-and-frontiers.md).
- Theory: [references/theory/theory-foundations.md](references/theory/theory-foundations.md), [references/theory/behavioral-and-factor-zoo-details.md](references/theory/behavioral-and-factor-zoo-details.md), [references/theory/fundamental-quantamental.md](references/theory/fundamental-quantamental.md).

For data artifacts or external research needs, use [references/data/data-analysis-and-external-research.md](references/data/data-analysis-and-external-research.md). If a CSV dataset is available and the environment also exposes the `statistical-learning-analysis` skill, prefer its bundled quant scripts for mechanical diagnostics such as point-in-time audits, IC reports, Fama-MacBeth regressions, transaction-cost reports, exposure reports, and multiple-testing checks.

## Typical Requests

- For factor research, diagnosis, implementation, Smart Beta, ML, or attribution requests, read `core/task-router.md` first and load only its minimum bundle.
- For broad factor-strategy tasks, use `core/decision-core.md` to keep the first decision context-light before loading detailed references.
- For method-center summaries, factor-family anchors, or "give the agent an entrypoint" requests, read `methods/method-idea-anchors.md` before detailed recipes.
- For "我想开发因子策略", "从数据特征找入手点", "发现策略漏洞并逐步优化", "遇到不同结果该怎么探索", or "让 agent 知道怎么思考" requests, read `core/decision-core.md`, `strategy/strategy-development-map.md`, and then the specialized playbook selected by `core/task-router.md`.
- For "完整分析", "完整工作流记录", "策略运行记录", complete analysis, end-to-end audit, strategy repair record, or production-readiness review requests, read `core/full-analysis-run-record.md` after `core/decision-core.md` and `core/task-router.md`.
- For field-to-hypothesis examples, data-feature entrypoint examples, or "给 agent 一些策略构建样例" requests, read `strategy/strategy-worked-examples.md`.
- For strategy promotion, stage gate, evidence conflict, repeated optimization, decision ledger, or "can this go live?" requests, read `strategy/research-governance.md`.
- For CSV/table/schema/code/backtest/weights/trades artifacts, exact library/API behavior, data-vendor field semantics, or market-rule lookup, read `data/data-analysis-and-external-research.md` before making a recommendation.
- For "这个 skill 是否覆盖第 X 章/某个主题" or exact source-table questions, read `core/source-coverage-map.md`.
- For a research memo, anomaly test report, backtest audit, Smart Beta review, portfolio optimization review, or attribution report, read `core/report-templates.md` after the task bundle.

## Output Contract

For a research design or review, return:

- Problem classification and investable timing assumptions.
- Data/universe construction rules and leakage controls.
- Signal/factor construction steps, including direction, transformations, neutralization, and missing-value rules.
- Primary tests and why they match the claim.
- Robustness, cost, capacity, and multiple-testing checks.
- Interpretation: risk compensation, mispricing, or data-snooping evidence.
- Implementation path: expected return model, risk model, optimizer, constraints, and monitoring if portfolio use is intended.

For strategy entrypoint, repair, or promotion tasks, also return the material parts of the decision spine: object, claim side, timing, anchor, frozen or requested baseline, observed phenomenon, defect class, targeted experiment, stage gate verdict, and the evidence that would change the conclusion.

For a complete analysis, end-to-end audit, strategy repair record, or production-readiness review, include a compact analysis run record: references used, decision spine, claim side, evidence state, baseline ID, observed phenomenon, defect class, six-criteria grade, search-space/prior state when relevant, model consistency when relevant, domain logic when relevant, experiment registry or next experiments, evidence conflicts, stage verdict, and missing evidence.

For an implementation task, translate the same items into concrete files, functions, data schemas, or scripts, and validate with the smallest diagnostic that can catch timing, leakage, and cost errors.

## Hard Rules

- Do not mix up prediction variables, factor exposures, factor returns, pricing factors, and portfolio alpha. Name which object is being estimated.
- Do not use evidence for one claim side to prove another. Separate alpha, beta/lambda, risk-model, prediction, and portfolio-implementation claims.
- Do not use random IID splits for financial panels or time series. Use time splits, rolling/expanding windows, walk-forward validation, purging, or embargoing as appropriate.
- Do not use financial statement values by fiscal period end alone. Use announcement, correction, vendor-availability, or other point-in-time timestamps.
- Do not treat `t ~= 2` as enough evidence for a discovered factor. Check prior plausibility, multiple testing, sample-out performance, and economic magnitude.
- Do not treat IC, rank IC, or sorted-portfolio spread as executable PnL. Add turnover, costs, liquidity, borrow/shorting, price-limit, suspension, and capacity checks.
- Do not call a model better only because in-sample explanatory power is higher. Require parsimony, economic meaning, out-of-sample behavior, and alpha reduction.
- Do not orthogonalize factors without stating the base set and order. Orthogonalization is order-dependent unless the design explicitly avoids it.
- Do not let machine learning hide leakage or overfit. Use walk-forward validation, conservative baselines, interpretable diagnostics, and a locked final test.
- Do not finalize a strategy-design, repair, audit, or promotion answer before applying the self-review checklist in `core/decision-core.md` when the missing checks could change the recommendation.
- Do not present a complete analysis, strategy repair record, backtest audit, or production-readiness verdict without the compact run-record fields in `core/full-analysis-run-record.md`.
