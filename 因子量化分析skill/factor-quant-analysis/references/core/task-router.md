# Task Router

## Contents

- [Use This First](#use-this-first)
- [Strategy Development Shortcut](#strategy-development-shortcut)
- [Task Bundles](#task-bundles)
- [Failure Mode Routing](#failure-mode-routing)
- [Output Shape Routing](#output-shape-routing)
- [Escalation Rules](#escalation-rules)

## Use This First

Use this file as the first reference for ordinary factor-analysis tasks. It routes the request to a small reference bundle so the agent does not load the full skill.

Do not use this file for chapter-by-chapter coverage checks. Use [source-coverage-map.md](source-coverage-map.md) for source coverage and exact original summary lookup.

Default process:

1. Classify the request into one primary task.
2. Load only the bundle listed for that task.
3. If data artifacts, code, logs, exact API behavior, market rules, or field definitions are involved, load [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md) before answering.
4. Add optional references only when the request or evidence requires them.
5. If directory layout or load order is unclear, read [reference-architecture.md](reference-architecture.md) before loading more references.
6. Return the output shape listed below instead of a generic explanation.

## Strategy Development Shortcut

If the user asks how to develop, explore, debug, or productionize a factor strategy, read [decision-core.md](decision-core.md) first, then [strategy-development-map.md](../strategy/strategy-development-map.md) if the task needs a full decision flow. This keeps the first decision context-light before selecting detailed method references.

## Task Bundles

| Task | Use when | Minimum references | Add only if needed |
| --- | --- | --- | --- |
| Method anchor selection | User asks for central ideas, method anchors, which factor method to start from, or a high-level method map | [method-idea-anchors.md](../methods/method-idea-anchors.md), [method-map.md](../methods/method-map.md), [factor-and-model-catalog.md](../models-factors/factor-and-model-catalog.md) | [strategy-development-map.md](../strategy/strategy-development-map.md) if the user wants to turn anchors into a strategy |
| Factor idea triage | User has a signal idea but no full test yet | [decision-core.md](decision-core.md), [method-idea-anchors.md](../methods/method-idea-anchors.md), [strategy-development-map.md](../strategy/strategy-development-map.md), [validation-and-risks.md](../practice/validation-and-risks.md) | [playbook-factor-research.md](../playbooks/playbook-factor-research.md) for a full protocol; [a-share-data-details.md](../data/a-share-data-details.md) for A-share timing; [fundamental-quantamental.md](../theory/fundamental-quantamental.md) for accounting-quality questions |
| Strategy entrypoint discovery | User wants to build a strategy from available data, features, schema, or rough observations | [decision-core.md](decision-core.md), [method-idea-anchors.md](../methods/method-idea-anchors.md), [strategy-worked-examples.md](../strategy/strategy-worked-examples.md), [strategy-development-map.md](../strategy/strategy-development-map.md), [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md) | Use `statistical-learning-analysis` scripts when CSV data is local; add [research-governance.md](../strategy/research-governance.md) for a decision ledger; add [full-analysis-run-record.md](full-analysis-run-record.md) if the user asks for a complete workflow record; add [playbook-factor-research.md](../playbooks/playbook-factor-research.md), [playbook-data-backtest.md](../playbooks/playbook-data-backtest.md), or [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md) only after the entrypoint is selected |
| Dataset or future-function audit | User provides data fields, timestamps, or asks about leakage | [playbook-data-backtest.md](../playbooks/playbook-data-backtest.md), [a-share-data-details.md](../data/a-share-data-details.md), [data-and-implementation.md](../data/data-and-implementation.md), [validation-and-risks.md](../practice/validation-and-risks.md) | [full-analysis-run-record.md](full-analysis-run-record.md) for end-to-end audit records; [agent-playbooks.md](../playbooks/agent-playbooks.md) for generic output patterns |
| Data artifact analysis | User provides CSV/table/schema/code/backtest output/weights/trades or asks what the data proves | [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md), [playbook-data-backtest.md](../playbooks/playbook-data-backtest.md), [data-and-implementation.md](../data/data-and-implementation.md) | Use `statistical-learning-analysis` scripts when CSV data is local; add [full-analysis-run-record.md](full-analysis-run-record.md) for complete analysis records; add [research-governance.md](../strategy/research-governance.md) if the artifact supports strategy promotion or repair decisions |
| Single-factor validation | User asks whether one factor is effective | [method-idea-anchors.md](../methods/method-idea-anchors.md), [research-workflow.md](../playbooks/research-workflow.md), [method-map.md](../methods/method-map.md), [validation-and-risks.md](../practice/validation-and-risks.md) | [anomaly-construction-recipes.md](../methods/anomaly-construction-recipes.md) for F-Score/G-Score/FAR/IVOL/expectation gap; [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) for mechanism diagnosis |
| Factor failure or too-good diagnosis | Factor is weak, too strong, unstable, or disappears after costs | [decision-core.md](decision-core.md), [strategy-development-map.md](../strategy/strategy-development-map.md), [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md), [validation-and-risks.md](../practice/validation-and-risks.md) | [playbook-factor-research.md](../playbooks/playbook-factor-research.md) for a full protocol; [playbook-data-backtest.md](../playbooks/playbook-data-backtest.md) and [a-share-data-details.md](../data/a-share-data-details.md) for A-share tradability and timing checks |
| Strategy loophole iteration | User has a flawed strategy, surprising result, broken backtest, poor live/paper behavior, or asks how to optimize defects | [decision-core.md](decision-core.md), [full-analysis-run-record.md](full-analysis-run-record.md), [strategy-development-map.md](../strategy/strategy-development-map.md), [research-governance.md](../strategy/research-governance.md), [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md), [validation-and-risks.md](../practice/validation-and-risks.md) | [playbook-data-backtest.md](../playbooks/playbook-data-backtest.md) for backtest artifacts; [playbook-factor-research.md](../playbooks/playbook-factor-research.md) for mechanism diagnosis; [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md) for optimizer/ML defects; [practice-deep-dive.md](../practice/practice-deep-dive.md) for production portfolio conversion |
| Research governance and stage gate | User asks whether evidence is enough, whether a strategy can continue/promote/go live, how to resolve conflicting evidence, or how to manage repeated iterations | [decision-core.md](decision-core.md), [full-analysis-run-record.md](full-analysis-run-record.md), [research-governance.md](../strategy/research-governance.md), [strategy-development-map.md](../strategy/strategy-development-map.md), [validation-and-risks.md](../practice/validation-and-risks.md) | [report-templates.md](report-templates.md) for a formal verdict; task-specific playbooks for missing evidence |
| Complete analysis run record | User asks for complete analysis, full workflow record, strategy run record, end-to-end audit, or an auditable trail of how the skill was used | [decision-core.md](decision-core.md), [full-analysis-run-record.md](full-analysis-run-record.md), [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md), [strategy-development-map.md](../strategy/strategy-development-map.md), [research-governance.md](../strategy/research-governance.md) | [report-templates.md](report-templates.md) for user-facing deliverables; add method/model/practice references only for the current uncertainty |
| Multi-factor model reproduction or comparison | User asks to reproduce FF/Carhart/HXZ/SY/DHS/CHN/LSL or compare models | [model-construction-recipes.md](../methods/model-construction-recipes.md), [econometrics-deep-dive.md](../methods/econometrics-deep-dive.md), [econometrics-advanced-notes.md](../methods/econometrics-advanced-notes.md), [a-share-model-evidence.md](../models-factors/a-share-model-evidence.md) | [factor-and-model-catalog.md](../models-factors/factor-and-model-catalog.md) for model summaries |
| A-share model or main factor explanation | User asks about A-share size/value/momentum/profitability/investment/turnover evidence | [a-share-model-evidence.md](../models-factors/a-share-model-evidence.md), [factor-and-model-catalog.md](../models-factors/factor-and-model-catalog.md), [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) | [a-share-data-details.md](../data/a-share-data-details.md) for construction assumptions |
| Portfolio optimization or index enhancement | User asks how to turn signals into a portfolio | [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md), [practice-deep-dive.md](../practice/practice-deep-dive.md), [data-and-implementation.md](../data/data-and-implementation.md), [validation-and-risks.md](../practice/validation-and-risks.md) | [strategy-development-map.md](../strategy/strategy-development-map.md) if the research-to-portfolio path is unclear; [research-governance.md](../strategy/research-governance.md) if promotion or production readiness is requested |
| Smart Beta, style, or risk attribution | User asks about factor products, BetaPlus, style analysis, Buffett, or risk attribution | [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md), [data-and-implementation.md](../data/data-and-implementation.md), [report-templates.md](report-templates.md) | [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) for factor rationale |
| Machine learning or alternative data | User asks about ML factor selection, PCA/IPCA, nonlinear models, text/geolocation/alternative data | [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md), [ml-and-frontiers.md](../practice/ml-and-frontiers.md), [validation-and-risks.md](../practice/validation-and-risks.md) | [method-map.md](../methods/method-map.md) for OOS metrics and method selection |
| External solution lookup | User asks for an implementation fix, library/API behavior, optimizer error, paper construction, market rule, or data-vendor field definition | [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md), task-specific factor reference | Use Context7 or official documentation for libraries; use original papers or exchange/regulator/index/data-vendor docs for finance rules |
| Theory, behavior, or factor zoo explanation | User asks conceptual questions about CAPM/APT, p-hacking, priors, sentiment, or behavior | [theory-foundations.md](../theory/theory-foundations.md), [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md), [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md) | [econometrics-advanced-notes.md](../methods/econometrics-advanced-notes.md) for Bayesian/model-comparison details |
| Chapter coverage or exact source lookup | User asks whether the skill covers a chapter or needs exact table values | [source-coverage-map.md](source-coverage-map.md) | Original `md/` summaries for exact source values |

## Failure Mode Routing

| Observed symptom | First suspicion | First checks |
| --- | --- | --- |
| Very high t-statistic or Sharpe | Leakage, bad universe reconstruction, missing costs | Timestamp audit, signal/return alignment, survivorship, suspension and price-limit handling |
| Significant factor result but no claim side | Prediction, pricing, risk-model, and portfolio claims are mixed | Classify `alpha_claim`, `beta_lambda_claim`, `risk_model_claim`, `prediction_claim`, or `portfolio_implementation_claim` before selecting evidence |
| Good backtest but no six-criteria review | Statistical result is being treated as factor validity | Grade logic, persistence, incremental information, robustness, investability, and universality before promotion |
| One good factor found after many variables or variants | Hidden p-hacking and weak prior | Record tested family, variants, search-space size or unknown, prior plausibility, multiple-testing control, and locked final-test policy |
| IC is good but portfolio does not make money | Turnover, cost, capacity, unintended exposure, weak monotonicity | Quantile returns, turnover, cost sensitivity, exposure attribution, long-only result |
| Long-short spread is good but long leg is weak | Short-leg-driven paper anomaly | Long and short leg attribution, borrow/short feasibility, long-only proxy |
| Factor disappears out of sample | Overfit, publication decay, crowding, regime dependence | Walk-forward, post-publication split, crowding metrics, subperiod and regime tests |
| Factor disappears after size control | Small-cap, microcap, shell-value, or liquidity proxy | Size-neutral sort, value-weight returns, microcap exclusion, liquidity controls |
| Factor disappears after cost | High turnover, market impact, capacity limit | Turnover decomposition, ADV and impact model, rebalance frequency, buffer rules |
| A-share momentum is negative or weak | Short-term reversal, small-cap speculation, crash exposure | Skip-month construction, size split, residual momentum, target-volatility check |
| Low-vol or IVOL spread is only in short leg | Lottery demand or shorting-constrained overpricing | Long-only low-vol test, MAX/skewness controls, high-IVOL short-leg tradability |
| Accounting signal works only before disclosure date | Future function | Announcement/vendor-availability timestamp, restatement handling, lagged report availability |
| Fundamental, industry, event, text, alternative-data, or microstructure signal has no domain logic | Proxy may be a data artifact, coverage bias, or post-hoc story | Check accounting/business/economic/data-generating mechanism, proxy validity, local fit, and failure mode if the proxy is wrong |
| Multi-factor optimizer produces extreme weights | Forecast/risk model mismatch, weak constraints | Exposure caps, turnover/cost penalty, covariance shrinkage, constraint priority |
| Portfolio or optimizer answer has mismatched horizons or assumptions | Return model, risk model, cost model, constraints, and objective target different decisions | Check forecast horizon, risk horizon, cost horizon, benchmark, universe, constraints, and optimizer objective consistency |
| Dataset has many possible columns but no strategy idea | Unranked entrypoints and unclear first hypothesis | Inventory data features, rank feasible strategy families, pick simplest falsifiable baseline |
| Strategy is being "optimized" without a diagnosed flaw | In-sample tuning and moving target | Record observed phenomenon, map to one defect class, run at most three targeted experiments |
| Conflicting evidence across IC, quantiles, regression, portfolio, and costs | Metric cherry-picking or unresolved research object | Use evidence priority: timing, tradability, net portfolio value, OOS stability, mechanism, statistical significance, in-sample fit |
| Stage promotion without required evidence | Premature productionization | Apply stage gates; downgrade, hold, reject, or mark not determinable if required evidence is missing |
| Repeated optimization without frozen baseline | Moving target and hidden p-hacking | Freeze baseline, update decision ledger, record rejected variants, and limit the next loop to three targeted experiments |
| Complete analysis answer has no run record | Unreviewable reasoning and hidden cherry-picking | Use [full-analysis-run-record.md](full-analysis-run-record.md) to record references used, decision spine, claim side, reasoning gates, baseline, observed phenomenon, defect, experiments, conflicts, stage verdict, and missing evidence |
| Broad strategy task loads many references before the first uncertainty is clear | Context bloat and unfocused reasoning | Use [decision-core.md](decision-core.md) first, identify the current uncertainty, then load only the next useful reference |
| Final strategy answer skips object, claim side, timing, baseline, defect, reasoning gates, or gate checks | Incomplete reasoning audit | Apply the self-review checklist in [decision-core.md](decision-core.md) and downgrade or mark not determinable if material evidence is missing |
| Implementation answer depends on library/API/version or market rule | Unverified external assumption | Check Context7, official documentation, source docs, release notes, original paper, or exchange/vendor rule, then run local fit check |
| Data-vendor field semantics are unknown | Hidden availability or survivorship rule | Find vendor definition, availability timestamp, revision policy, and universe membership rule; otherwise mark uncertain |
| External paper, blog, or package example is copied into local A-share work | Imported method may not fit local data, rules, or tradability | Check original/official source, local market fit, point-in-time data, trading rules, costs, and dependency version |

## Output Shape Routing

| Task | Output shape |
| --- | --- |
| Method anchor selection | Method/factor anchors, center idea, first empirical question, common misuse, next reference to load |
| Research design | Objective, data timing, signal construction, primary tests, robustness, implementation caveats |
| Strategy entrypoint discovery | Data features, matched worked example if useful, feasible strategy families, claim side, ranked entrypoints, first baseline, expected first phenomenon, falsification tests |
| Dataset audit | Available timestamps, leakage risks, universe/tradability rules, required fixes, not-determinable items |
| Data artifact analysis | Data object, keys/fields, timing order, coverage/missingness, diagnostics run, decision grade, missing evidence |
| Factor diagnosis | Mechanism hypothesis, competing explanations, tests to run next, implementation risks, what would change the conclusion |
| Strategy loophole iteration | Observed phenomenon, primary defect class, targeted experiments, allowed repair, comparison baseline, stop/promote decision |
| Research governance and stage gate | Decision ledger snapshot, evidence conflict resolution, stage gate verdict, missing evidence, next decision |
| Complete analysis run record | Run record snapshot or full record, evidence state, claim side, baseline ID, observed phenomenon, defect class, six criteria, search-space/prior state when relevant, model consistency when relevant, domain logic when relevant, experiment registry, evidence conflict resolution, stage gate verdict, final claim |
| Backtest review | Findings first, severity, file/data evidence if available, missing tests, residual risk |
| Model comparison | Models, construction parity, test assets, alpha/GRS/parsimony, economic interpretation |
| Portfolio implementation | Expected return model, risk model, constraints, costs, optimizer objective, model consistency, monitoring |
| Smart Beta review | Target exposure, holdings audit, non-target exposures, fees/capacity, attribution, recommendation caveats |
| ML factor selection | Label definition, split design, leakage controls, benchmark, OOS metrics, final-test isolation |
| External lookup | Unknown resolved, source priority, retrieved rule/API behavior, local fit check, validation result, unverified assumptions |
| Core self-review | Object, claim side, timing, anchor, baseline, phenomenon, defect, experiment, gate, six criteria when material, search-space/prior when material, model consistency when material, domain logic when material, missing evidence that would change the conclusion |

## Escalation Rules

- If the user asks for exact table values, source wording, or chapter summary reproduction, route to [source-coverage-map.md](source-coverage-map.md) and the original `md/` files.
- If there is code or CSV data, pair this skill with the available project scripts or `statistical-learning-analysis` mechanical diagnostics.
- If the task is blocked by reference layout uncertainty, read [reference-architecture.md](reference-architecture.md) and load only the next task-specific file.
- If the task is broad and could trigger many references, start with [decision-core.md](decision-core.md), identify the first decision, then load only the reference needed for that uncertainty.
- If evidence conflicts or the user asks whether a strategy can continue, promote, paper trade, productionize, reduce, pause, or retire, route to [research-governance.md](../strategy/research-governance.md).
- If the user asks for complete analysis, full workflow record, strategy run record, or end-to-end audit, route to [full-analysis-run-record.md](full-analysis-run-record.md) after [decision-core.md](decision-core.md).
- If exact API/library behavior, optimizer behavior, dependency-version behavior, or market-rule interpretation matters, use Context7 or official documentation first, then check the local project version and assumptions.
- If a result depends on exact data vendor fields, do not invent availability rules; mark unknown timestamps or ask for the field definition.
- If the task spans several bundles, start with the smallest bundle that can answer the first decision, then load more references only after identifying the next uncertainty.
