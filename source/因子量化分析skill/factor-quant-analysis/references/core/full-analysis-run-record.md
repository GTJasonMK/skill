# Full Analysis Run Record

Use when: the user asks for a complete factor analysis, strategy development run, strategy repair loop, backtest audit, production/paper-trading decision, or any task where the final answer should be auditable from the skill's reasoning workflow.

Purpose: force a complete analysis to leave a compact process record. This record is not a long final report. It is the evidence trail that shows how the agent used the skill: which references were loaded, what object and timing were locked, what baseline was frozen, what phenomenon was observed, what defect was diagnosed, what experiments were allowed, and why the stage verdict follows.

Read after: [decision-core.md](decision-core.md) and [task-router.md](task-router.md).
Use with: [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md) for data artifacts, [strategy-development-map.md](../strategy/strategy-development-map.md) for entrypoint/repair loops, [research-governance.md](../strategy/research-governance.md) for ledgers and stage gates, and [report-templates.md](report-templates.md) for user-facing deliverables.

Do not use for: short conceptual answers, exact chapter lookup, or ordinary method explanations unless the user explicitly asks for a full analysis record.

## Contents

- [Record Modes](#record-modes)
- [Minimal Run Record](#minimal-run-record)
- [Expanded Run Record](#expanded-run-record)
- [Output Compression Rules](#output-compression-rules)

## Record Modes

Choose the smallest mode that keeps the decision auditable:

| Mode | Use when | Required output |
| --- | --- | --- |
| `snapshot` | The final answer needs a visible reasoning audit but not a full appendix. | Task intake, decision spine, claim side, evidence state, applicable reasoning gates, stage verdict, missing evidence. |
| `diagnostic` | Data, backtest, factor result, or strategy flaw is being reviewed. | Snapshot plus data evidence, observed phenomena, defect class, targeted experiments. |
| `full` | The user asks for a complete analysis, reusable research record, paper/live decision, or production readiness review. | All sections below, compressed where evidence is unavailable. |

If the user asks only for the final conclusion, include a `snapshot`. If the user asks for a complete analysis workflow, include the `full` record or a clearly labeled compact version of it.

## Minimal Run Record

Use this as the default visible record in user-facing answers when the task is strategy design, repair, audit, or promotion.

| Field | Record |
| --- | --- |
| `task_type` | Research design, strategy entrypoint, data artifact analysis, backtest audit, repair loop, external lookup, portfolio conversion, stage gate, or monitoring decision. |
| `references_used` | Skill references actually loaded, not the whole directory. |
| `current_question` | The one decision being answered now. |
| `object` | Characteristic, exposure, factor return, pricing factor, prediction variable, portfolio alpha, or risk-control rule. |
| `claim_side` | `alpha_claim`, `beta_lambda_claim`, `risk_model_claim`, `prediction_claim`, or `portfolio_implementation_claim`; state the exact claim being tested before choosing evidence. |
| `timing` | Observable date, rebalance date, execution date, forward-return window, universe, and tradability rule. |
| `anchor` | Method or factor-family center idea from [method-idea-anchors.md](../methods/method-idea-anchors.md). |
| `baseline_id` | Frozen signal, portfolio rule, benchmark, cost assumption, and diagnostics used for comparison. |
| `observed_phenomenon` | IC, quantile shape, long/short legs, turnover, costs, exposures, capacity, OOS, live/paper, or missing evidence. |
| `defect_class` | Data/timing, label, signal construction, universe/tradability, hidden exposure, portfolio construction, cost/capacity, overfit/multiple testing, regime, or implementation mismatch. |
| `six_criteria_grade` | Logic, persistence, incremental information, robustness, investability, and universality: pass, weak, failed, not tested, or not applicable. |
| `search_space_prior` | Tested family, variants seen, search-space size or unknown, prior plausibility, multiple-testing control, and locked final-test policy. |
| `model_consistency` | For portfolio work: return horizon, risk horizon, cost horizon, universe, benchmark, constraints, and optimizer objective are aligned or not applicable. |
| `domain_logic_check` | Accounting, business, economic, microstructure, industry, or data-generating mechanism; record failure mode if the proxy is wrong. |
| `next_experiments` | No more than three targeted experiments tied to the defect hypothesis. |
| `stage_verdict` | Reject, not determinable, research-only, risk-control only, portfolio candidate, paper trade, production candidate, monitor, reduce, pause, or retire. |
| `decision_changer` | Evidence that would change the conclusion. |

Do not leave `object`, `claim_side`, `timing`, `baseline_id`, `defect_class`, or `stage_verdict` blank when the answer recommends a repair, promotion, rejection, or next experiment. If a reasoning gate does not apply, write `not applicable`; if evidence is missing, write `not auditable` or `not determinable` and state the blocker.

## Expanded Run Record

Use the following sections for a full analysis. Keep each section compact; record only decision-relevant evidence.

### 1. Task Intake

| Field | Record |
| --- | --- |
| `user_request` | Original request or compact paraphrase. |
| `task_type` | Primary task from [task-router.md](task-router.md). |
| `primary_decision` | The one decision the analysis must answer. |
| `references_used` | Files loaded because they were needed. |
| `references_not_loaded` | Important files intentionally skipped and why. |

### 2. Decision Spine

| Step | Record |
| --- | --- |
| `object` | Name the exact research object. |
| `claim_side` | Decide whether the evidence is meant to support alpha, beta/lambda, risk-model quality, prediction quality, or portfolio implementation. |
| `timing` | Lock observable, rebalance, execution, return window, universe, and tradability assumptions. |
| `anchor` | Select one method/factor anchor and first falsification question. |
| `baseline` | Freeze `baseline_id` before repairs. |
| `phenomenon` | Record actual evidence before interpreting it. |
| `defect` | Map the main bad or surprising phenomenon to one defect class. |
| `experiment` | List at most three targeted experiments. |
| `gate` | Apply the relevant stage gate. |

### 3. Claim Side and Reasoning Gates

Use these gates to keep source-derived method discipline visible in complete analyses. Record `not applicable` only when the task truly does not touch that gate.

#### Claim Side Classification

| Claim side | Use when | Evidence must not be confused with |
| --- | --- | --- |
| `alpha_claim` | The claim is residual or implementable alpha after named risks and costs. | Raw IC, sorted spread, or in-sample alpha alone. |
| `beta_lambda_claim` | The claim is that an exposure earns a cross-sectional premium or priced risk compensation. | A stock-selection signal or portfolio backtest. |
| `risk_model_claim` | The claim is that exposures, covariance, or specific risk explain or control portfolio risk. | Expected-return forecasting. |
| `prediction_claim` | The claim is that a variable predicts returns or fundamentals. | Tradable net PnL or priced factor status. |
| `portfolio_implementation_claim` | The claim is that a signal can survive constraints, costs, liquidity, capacity, and monitoring. | Statistical significance before implementation frictions. |

#### Six Criteria Gate

| Criterion | Required record |
| --- | --- |
| `logic` | Economic, behavioral, institutional, accounting, microstructure, or business mechanism exists before relying on significance. |
| `persistence` | Effect survives time splits, regimes, publication/sample-out checks, or live/paper evidence appropriate to the stage. |
| `incremental_information` | Signal adds information beyond known factors, simple baselines, exposures, and correlated proxies. |
| `robustness` | Result is not driven by one construction, weighting rule, neutralization choice, outlier policy, or subgroup unless explicitly scoped. |
| `investability` | Turnover, costs, liquidity, borrow/shorting, price limits, suspensions, capacity, and implementation path are addressed. |
| `universality` | Cross-market, cross-universe, cross-period, or domain-specific boundary is stated; lack of universality raises prior skepticism but does not automatically reject a local strategy. |

#### Search Space and Prior Record

| Field | Record |
| --- | --- |
| `tested_family` | Factor family, feature group, model class, or parameter family searched. |
| `variants_seen` | Count or description of directions, windows, transforms, neutralizations, universes, filters, horizons, and model settings tried. |
| `search_space_size_or_unknown` | Known count, bounded estimate, or `unknown`; unknown search space lowers claim strength. |
| `prior_plausibility` | Strong, medium, weak, or absent prior, with mechanism named. |
| `multiple_testing_control` | FDR/FWER, Bayesian prior adjustment, holdout/final-test isolation, walk-forward, or none. |
| `final_test_policy` | Locked final test, unused holdout, paper/live plan, or blocker if final evidence was reused for tuning. |

#### Model Consistency Check

Required for portfolio optimization, Smart Beta, risk attribution, and production-readiness decisions.

| Component | Required consistency check |
| --- | --- |
| `objective_benchmark` | Objective, benchmark, active risk, and allowed instruments describe the same mandate. |
| `return_model` | Forecast horizon, score scaling, decay, and rebalance frequency match the intended holding period. |
| `risk_model` | Exposure horizon, covariance horizon, specific risk, and constraints match the portfolio decision. |
| `cost_model` | Cost horizon, turnover assumption, market impact, borrow, tax, and liquidity match the rebalance/execution plan. |
| `constraints_optimizer` | Constraints and optimizer objective do not silently override the alpha, risk, or cost assumptions. |

#### Domain Logic Check

Use for fundamental, industry, event, text, alternative-data, and microstructure signals.

| Field | Record |
| --- | --- |
| `domain_mechanism` | Accounting, business, economic, behavioral, institutional, industry, or data-generating mechanism. |
| `proxy_validity` | Why the field measures the intended concept rather than a vendor artifact, reporting lag, coverage bias, or tradability proxy. |
| `failure_mode_if_wrong` | What result would appear if the mechanism is false or the proxy is contaminated. |
| `local_fit` | Whether the mechanism fits the local market, accounting convention, data vendor, universe, and execution constraints. |

### 4. Data Evidence Record

| Field | Record |
| --- | --- |
| `data_object` | Raw market data, point-in-time fundamentals, factor panel, return label panel, holdings, trades, optimizer input, or backtest output. |
| `keys_and_fields` | Date key, asset key, signal fields, labels, weights, prices, volumes, timestamps, vendor metadata. |
| `time_ordering` | Signal date, availability date, rebalance date, execution date, fill date, forward-return start/end. |
| `coverage_missingness` | Date range, cross-sectional count, missingness, duplicates, survivorship clues. |
| `signal_quality` | Outliers, stale values, ties, transformations, neutralization, full-sample preprocessing risk. |
| `label_quality` | Return horizon, overlap, benchmark adjustment, compounding, execution feasibility. |
| `tradability_cost_capacity` | Suspensions, price limits, borrow/shorting, turnover, costs, ADV participation, impact, capacity. |
| `exposure_redundancy` | Industry, size, beta, volatility, liquidity, value, profitability, investment, momentum, signal overlap. |
| `data_grade` | Usable evidence, needs rerun, research-only, implementation-risky, reject, or not auditable. |

If no local artifact exists, state which diagnostics cannot be run and what artifact would make them auditable.

### 5. Method Anchor Selection

| Anchor | Feasible because | First falsification | Decision |
| --- | --- | --- | --- |
| Candidate anchor | Data/timing/mechanism support. | First empirical result that would disprove it. | Selected or rejected. |

Select one primary anchor and at most two backups. Do not add ML, optimizer, neutralization, or timing layers before the simplest valid baseline can fail.

### 6. Baseline Protocol

| Field | Record |
| --- | --- |
| `baseline_id` | Stable identifier for the frozen baseline. |
| `raw_signal` | Raw variable/formula and expected sign. |
| `transform` | Winsorization, ranking, standardization, neutralization, missing policy. |
| `universe_benchmark` | Universe, benchmark, eligibility, weighting. |
| `timing_rule` | Rebalance, execution, holding horizon, forward return. |
| `portfolio_rule` | Long-only, long-short, quantile spread, optimizer, or risk-control rule. |
| `cost_assumption` | Commission, tax, spread, slippage, impact, borrow, financing. |
| `frozen_diagnostics` | Diagnostics that all variants must compare against. |

### 7. Observed Phenomena

| Evidence | Observation | Interpretation limit |
| --- | --- | --- |
| IC/rank IC | Value, stability, sign, horizon decay. | Prediction evidence, not executable PnL. |
| Quantile returns | Spread, monotonicity, tail behavior. | Inspect long and short legs separately. |
| Portfolio result | Gross/net return, drawdown, turnover, benchmark-relative behavior. | Net value outranks statistical fit. |
| Costs/capacity | Cost drag, ADV participation, slippage, capacity. | Can invalidate otherwise significant factors. |
| Exposures | Industry, style, size, beta, liquidity, known factors. | Decide exposure harvest versus residual alpha. |
| Robustness | Subperiod, regime, OOS, walk-forward, live/paper. | Avoid tuning on final tests. |

### 8. Defect Diagnosis

Record one primary defect class before repairs:

- Data/timing.
- Label construction.
- Signal construction.
- Universe/tradability.
- Hidden exposure.
- Portfolio construction.
- Cost/capacity.
- Overfit/multiple testing.
- Regime dependence.
- Implementation mismatch.

| Competing explanation | Evidence for | Evidence against | Decision |
| --- | --- | --- | --- |
| Candidate defect |  |  | Primary, secondary, or rejected. |

### 9. Experiment Registry

Use experiments to change decisions, not to search until something works.

| `baseline_id` | `variant_id` | `changed_one_element` | `defect_hypothesis` | `expected_change` | `result` | `new_problem_created` | `decision` |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

Rules:

- Run no more than three targeted experiments per loop.
- Change one major design element per experiment.
- Compare every variant against the frozen baseline.
- Keep failed or invalid variants visible.
- Do not reuse final-test results for tuning.

### 10. External Evidence Card

Use when exact API behavior, market rule, data-vendor field semantics, paper construction, optimizer behavior, or package-version behavior affects the decision.

| Field | Record |
| --- | --- |
| `precise_unknown` | The exact unknown before searching. |
| `sources_checked` | Official docs, Context7, source code, original paper, exchange/regulator/vendor docs, issue tracker. |
| `authoritative_rule` | Decision-relevant rule or API behavior retrieved. |
| `local_fit_check` | How the rule fits local market, data, package version, schema, timing, or project code. |
| `unresolved_assumption` | Assumption that remains unverified. |
| `confidence` | High, medium, low, or not determinable. |
| `decision_impact` | How this evidence changes construction, diagnosis, or verdict. |

### 11. Evidence Conflict Resolution

Use the priority from [research-governance.md](../strategy/research-governance.md):

```text
observable timing
> tradability
> net portfolio value
> out-of-sample stability
> mechanism evidence
> statistical significance
> in-sample fit
```

| Conflict | Priority applied | Verdict |
| --- | --- | --- |
|  |  |  |

If conflicts remain unresolved, mark the conclusion `not determinable`, `research-only`, or `downgrade`; do not choose the most optimistic metric.

### 12. Stage Gate Verdict

| Stage | Verdict | Blocker or evidence |
| --- | --- | --- |
| `idea` |  |  |
| `research_candidate` |  |  |
| `validated_signal` |  |  |
| `portfolio_candidate` |  |  |
| `paper_trading` |  |  |
| `production_candidate` |  |  |
| `live_monitoring` |  |  |
| `reduce_pause_retire` |  |  |

### 13. Final Claim and Self-Review

| Field | Record |
| --- | --- |
| `current_conclusion` | The strongest defensible conclusion. |
| `claim_strength` | Reject, not determinable, research-only, risk-control only, portfolio candidate, paper trade, production candidate, monitor, reduce, pause, or retire. |
| `what_is_proven` | Evidence-supported claim only. |
| `what_is_not_proven` | Missing evidence or claim boundary. |
| `main_risk` | The failure mode most likely to change the conclusion. |
| `next_evidence` | Evidence that would change the conclusion. |

Before finalizing, apply the checklist in [decision-core.md](decision-core.md). If any material answer is missing, downgrade the claim or mark it `not determinable`.

## Output Compression Rules

- For ordinary user answers, output the `Minimal Run Record` plus the final recommendation.
- For formal research memos or audits, use the expanded sections as a process appendix and the relevant template in [report-templates.md](report-templates.md) as the user-facing structure.
- If the record would be mostly empty because data is missing, do not pad it. State the missing evidence and the stage verdict.
- If a task has no data artifact and no strategy decision, do not use this record unless the user asks for one.
- Never let the run record become a substitute for analysis. The record should expose the reasoning chain; it does not by itself prove the factor works.
