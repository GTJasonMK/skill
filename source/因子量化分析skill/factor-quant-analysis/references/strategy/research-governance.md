# Research Governance

Use when: a factor strategy has conflicting evidence, repeated iterations, stage-promotion questions, live/paper drift, or uncertainty about whether to continue, stop, downgrade, paper trade, or productionize.

Purpose: keep the agent from changing the research target midstream. A strategy may improve only through recorded evidence, a frozen baseline, targeted experiments, and explicit stage gates.

## Contents

- [Decision Ledger](#decision-ledger)
- [Variant Registry](#variant-registry)
- [Evidence Conflict Matrix](#evidence-conflict-matrix)
- [Stage Gates](#stage-gates)
- [Experiment Discipline](#experiment-discipline)

## Decision Ledger

Maintain a compact ledger for strategy development, diagnosis, and review. Update it whenever the task moves from one evidence state to another.

For complete analysis, repair, audit, or production-readiness tasks, embed this ledger inside the process record in [full-analysis-run-record.md](../core/full-analysis-run-record.md). The ledger answers the current decision; the run record preserves the full reasoning trail.

Ledger fields:

| Field | Meaning |
| --- | --- |
| `current_question` | The one decision being answered now. |
| `object_type` | Characteristic, exposure, factor return, pricing factor, prediction variable, portfolio alpha, or risk-control rule. |
| `claim_side` | `alpha_claim`, `beta_lambda_claim`, `risk_model_claim`, `prediction_claim`, or `portfolio_implementation_claim`; prevents using one evidence type to prove another claim. |
| `selected_anchor` | The method or factor anchor from [method-idea-anchors.md](../methods/method-idea-anchors.md). |
| `data_state` | Available, missing, invalid, or not auditable evidence for timing, labels, universe, tradability, costs, and exposures. |
| `baseline_id` | Frozen raw signal, portfolio rule, benchmark, cost assumption, and diagnostic set used for comparison. |
| `observed_phenomena` | IC, quantile shape, long/short legs, turnover, costs, exposures, drawdown, capacity, OOS, and live/paper behavior. |
| `primary_uncertainty` | The next uncertainty that can change the decision. |
| `defect_class` | Data/timing, label, signal construction, universe/tradability, hidden exposure, portfolio construction, cost/capacity, overfit, or regime. |
| `six_criteria_grade` | Logic, persistence, incremental information, robustness, investability, and universality: pass, weak, failed, not tested, or not applicable. |
| `search_space_prior` | Tested family, variants seen, search-space size or unknown, prior plausibility, multiple-testing control, and final-test policy. |
| `experiments_allowed` | At most three targeted experiments tied to the current defect hypothesis. |
| `rejected_variants` | Failed or invalid variants, including why they were rejected. |
| `current_grade` | Reject, not determinable, research-only, risk-control only, portfolio candidate, paper trade, production candidate, or monitor/reduce/pause. |
| `next_decision` | Continue, rerun, repair, downgrade, promote, stop, or request missing evidence. |

Rules:

- Do not change the research question without recording why.
- Do not change the claim side without recording why the old claim was too broad, too narrow, or unsupported.
- Do not repair before naming the defect class.
- Do not promote a strategy using evidence that is missing from the ledger.
- Do not hide failed variants by presenting only the surviving specification.
- Do not promote a discovered factor if the search-space and prior record is missing and the result came from repeated trial.

## Variant Registry

Use a variant registry whenever the strategy has more than one tested specification, repair, filter, weighting rule, cost assumption, or model setting. The goal is to prevent hidden p-hacking and moving-target comparisons.

| Field | Meaning |
| --- | --- |
| `baseline_id` | Frozen baseline that remains the comparison anchor. |
| `variant_id` | Stable identifier for the tested variant. |
| `tested_family` | Factor family, feature group, model class, or parameter family the variant belongs to. |
| `changed_one_element` | The one major design element changed in this experiment. |
| `defect_hypothesis` | The diagnosed defect the variant is meant to repair. |
| `expected_change` | What should improve if the diagnosis is right. |
| `result` | Decision-relevant result, including failure. |
| `new_problem_created` | New timing, exposure, cost, capacity, overfit, or implementation problem introduced. |
| `decision` | Keep, reject, rerun, downgrade, or hold for more evidence. |

Rules:

- Do not compare a variant against an unfrozen moving baseline.
- Do not keep a variant only because it improves the headline metric if it worsens timing, tradability, net value, OOS stability, or capacity.
- Do not remove bad periods, expensive trades, or failed variants unless the exclusion rule existed before the result.
- Do not let the registry hide degrees of freedom: record directions, windows, transforms, neutralization choices, universes, filters, horizons, model classes, and optimizer settings that were tried or considered.
- If the number of possible variants is unknown, say `search_space_size_or_unknown = unknown` and lower the claim strength until a locked final test or walk-forward evidence exists.
- Summarize the variant registry in the run record when the user asks for a complete workflow record or when promotion is being considered.

## Evidence Conflict Matrix

Resolve conflicts by evidence priority:

```text
observable timing
> tradability
> net portfolio value
> out-of-sample stability
> mechanism evidence
> statistical significance
> in-sample fit
```

| Conflict | Interpretation | Required action |
| --- | --- | --- |
| IC is positive but quantiles are not monotonic | Ranking relation may be weak, thresholded, outlier-driven, or subgroup-specific. | Inspect quantile table, subgroup splits, raw versus winsorized signal, and rank versus level transform before promoting. |
| IC is good but portfolio PnL is weak | Signal evidence is not portfolio evidence. Turnover, costs, dispersion, constraints, or exposures may dominate. | Split long/short legs, compute turnover/cost drag, compare simple top bucket, and run exposure attribution. |
| Long-short works but long-only is weak | The paper anomaly may be short-leg-driven and hard to implement. | Audit shorting/borrow/tradability and test a long-only or risk-control interpretation. |
| Regression is significant but sorting is weak | Average linear coefficient may hide nonlinear, tail, or unstable effects. | Compare Fama-MacBeth, conditional sorts, quantile shape, and robust/outlier treatment. |
| Sorting works but regression loses significance | Effect may be nonlinear, collinear with controls, or concentrated in a group. | Report raw effect and controlled effect separately; decide exposure harvest versus residual-alpha claim. |
| Neutralization removes the effect | The strategy may be harvesting a known exposure, not residual alpha. | Either relabel as exposure strategy or require residual alpha after named controls. |
| OOS prediction improves but net return worsens | Forecast loss improvement does not imply investable alpha. | Check turnover, costs, capacity, constraints, long/short legs, and known exposures. |
| Gross performance disappears after costs | Implementation friction is part of signal validity. | Downgrade unless turnover reduction, rebalance change, buffer rule, or capacity cap restores net value without overfit. |
| Paper/live behavior diverges from backtest | Data freshness, execution, regime, or implementation mismatch may dominate. | Compare live-vs-paper returns, slippage, data freshness, signal health, and rule/version differences. |
| Model comparison improves in-sample fit but adds many factors | Complexity may overfit. | Require alpha reduction, parsimony, economic meaning, OOS behavior, and stable construction. |

When conflicts remain unresolved, mark the strategy `not determinable` or `research-only`; do not choose the most optimistic metric.

## Stage Gates

Use stage gates to prevent premature promotion.

| Stage | Minimum evidence | Cannot promote if |
| --- | --- | --- |
| `idea` | Object, claim side, sign, horizon, universe, and mechanism are stated. | No testable mechanism, no observable data path, no expected phenomenon, or no domain logic for a domain-dependent signal. |
| `research_candidate` | Timing can be audited and a minimum viable test can be run. | Inputs, labels, universe, or tradability cannot be reconstructed. |
| `validated_signal` | Raw and cleaned evidence, IC/rank IC, quantile behavior, horizon decay, robustness, mechanism checks, six-criteria grade, and search-space/prior record when discovery was broad. | Effect is only in-sample, only microcap/illiquid, lacks prior or multiple-testing discipline, or disappears under basic timing/cost checks. |
| `portfolio_candidate` | Expected return mapping, risk model or exposure controls, constraints, costs, capacity, benchmark-relative behavior, and model consistency are tested. | Net return, capacity, unintended exposure, or return/risk/cost/constraint consistency fails. |
| `paper_trading` | Reproducible code/data, locked final test or walk-forward evidence, monitoring fields, and execution assumptions are ready. | Final test was reused for tuning, production data path is not defined, or variant registry hides material rejected variants. |
| `production_candidate` | Paper/live drift, slippage, data freshness, risk limits, rollback plan, and owner responsibilities are defined. | Monitoring, rollback, capacity cap, or implementation controls are missing. |
| `live_monitoring` | Signal health, exposure drift, capacity, slippage, data freshness, and risk breaches are monitored. | Breaches are ignored or thresholds are not tied to actions. |
| `reduce_pause_retire` | Persistent decay, drift, capacity stress, crowding, or rule failure is documented. | The action is based only on short-term noise without diagnostic evidence. |

Stage verdicts:

- `promote`: all minimum evidence exists and no blocker remains.
- `hold`: evidence is promising but one material check is missing.
- `downgrade`: evidence supports a narrower claim only.
- `reject`: timing, tradability, mechanism, or net value fails.
- `not determinable`: required evidence is unavailable.

## Experiment Discipline

Use experiments to change decisions, not to search until something works.

Rules:

1. Freeze the baseline before the first repair.
2. Change one major design element per experiment.
3. Run no more than three targeted experiments per loop.
4. Tie each experiment to one defect hypothesis.
5. Compare every repair to the frozen baseline and to simple alternatives.
6. Keep failed variants in the ledger.
7. Update the search-space/prior record whenever the loop adds directions, windows, filters, neutralization choices, model classes, or optimizer settings.
8. Promote only if the repair solves the diagnosed defect without creating a larger timing, exposure, cost, capacity, model-consistency, or overfit problem.

Good experiment examples:

| Defect hypothesis | Targeted experiment |
| --- | --- |
| Leakage | Add execution delay, rebuild point-in-time panel, and remove current-constituent bias. |
| Small-cap contamination | Compare value-weight, size-neutral, and microcap-excluded results. |
| Cost drag | Add turnover decomposition, longer rebalance period, and buffer rule. |
| Hidden exposure | Run known-factor and industry/style attribution; compare raw and neutralized signals. |
| Overfit | Use walk-forward, post-discovery split, variant registry, and simpler baseline. |

Bad experiment examples:

- Change signal direction, horizon, universe, neutralization, and cost model together.
- Keep retuning after every weak result without a defect hypothesis.
- Use final test results to select hyperparameters.
- Drop bad periods or expensive trades without an ex ante rule.
