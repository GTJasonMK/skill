# Forward-Test Scenarios

Use when: validating whether this skill actually changes an agent's behavior on realistic factor-strategy tasks. These forward-test scenarios are for skill maintenance and review, not ordinary user deliverables.

Purpose: test that the agent follows the intended workflow under limited context: method anchor, data evidence, decision ledger, conflict resolution, stage gate, and stop/promote discipline.

## Contents

- [How to Run](#how-to-run)
- [Scenario 1: Many Fields, No Strategy Idea](#scenario-1-many-fields-no-strategy-idea)
- [Scenario 2: Good IC, Bad Portfolio](#scenario-2-good-ic-bad-portfolio)
- [Scenario 3: Implausibly Strong Backtest](#scenario-3-implausibly-strong-backtest)
- [Scenario 4: Small-Cap-Only Factor](#scenario-4-small-cap-only-factor)
- [Scenario 5: ML Model Wins](#scenario-5-ml-model-wins)
- [Scenario 6: Net Value Curve Only](#scenario-6-net-value-curve-only)
- [Scenario 7: Vendor Field Definition Unknown](#scenario-7-vendor-field-definition-unknown)
- [Scenario 8: Optimizer Extreme Weights](#scenario-8-optimizer-extreme-weights)
- [Scenario 9: Live/Paper Drift](#scenario-9-livepaper-drift)
- [Scenario 10: High T-Stat Without Mechanism](#scenario-10-high-t-stat-without-mechanism)
- [Scenario 11: One Winner From 200 Variables](#scenario-11-one-winner-from-200-variables)
- [Scenario 12: Portfolio Model Horizon Mismatch](#scenario-12-portfolio-model-horizon-mismatch)
- [Scenario 13: Alternative Data Proxy With Weak Business Logic](#scenario-13-alternative-data-proxy-with-weak-business-logic)
- [Scenario 14: Good Backtest Without Six Criteria](#scenario-14-good-backtest-without-six-criteria)
- [Scenario 15: Continue Optimizing Without a Diagnosed Defect](#scenario-15-continue-optimizing-without-a-diagnosed-defect)

## How to Run

For each scenario, ask a fresh agent to use this skill on the prompt shape. Do not reveal the expected behavior. Inspect whether the answer loads the right references and follows the workflow.

Pass criteria:

- Identifies the task type and object.
- Identifies the claim side before deciding which evidence proves the claim.
- Uses [decision-core.md](../core/decision-core.md) for broad strategy reasoning before loading larger bundles.
- Uses method anchors before detailed recipes when method choice is open.
- Uses [strategy-worked-examples.md](strategy-worked-examples.md) when a field list needs a field-to-hypothesis bridge.
- Enters data evidence mode when artifacts or field lists exist.
- Maintains or requests a decision ledger when iteration is involved.
- Emits a compact run record snapshot when the prompt asks for complete analysis, end-to-end audit, strategy repair record, or production-readiness review.
- Applies six-criteria, search-space/prior, model-consistency, and domain-logic gates when their triggers appear.
- Handles conflicting evidence instead of choosing the most optimistic metric.
- Gives a stage gate verdict rather than jumping to production.
- Applies the final self-review checklist when the answer recommends repair, promotion, rejection, or a next experiment.

Failure signals:

- Starts with a complex model before timing, labels, and tradability.
- Treats IC, spread, alpha, or OOS loss as investable alpha by itself.
- Treats prediction, pricing, risk-model, and portfolio-implementation evidence as interchangeable.
- Accepts a discovered factor without prior/search-space/multiple-testing context when the prompt implies broad search.
- Promotes a portfolio optimizer without checking return/risk/cost/constraint horizon consistency.
- Uses fundamental or alternative data without a domain mechanism and proxy-validity check.
- Repairs strategy design before diagnosing the defect.
- Gives a complete analysis or production verdict without references used, baseline ID, observed phenomenon, defect class, experiments, conflicts, and stage verdict.
- Promotes without costs, capacity, exposure, and monitoring checks.
- Loads many detailed references before naming the first uncertainty.

## Scenario 1: Many Fields, No Strategy Idea

Prompt shape:

```text
I have a CSV with daily prices, volume, turnover, market cap, industry, quarterly ROE, BM, EP, analyst revision, announcement date, and 20-day forward return. Help me find a factor strategy entrypoint.
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [method-idea-anchors.md](../methods/method-idea-anchors.md)
- [strategy-worked-examples.md](strategy-worked-examples.md)
- [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md)
- [strategy-development-map.md](strategy-development-map.md)
- [research-governance.md](research-governance.md)

Expected reasoning behavior:

- Inventory fields, keys, timestamps, labels, and tradability evidence.
- If the user asks for a complete workflow record, uses [full-analysis-run-record.md](../core/full-analysis-run-record.md) to preserve the process trace.
- Rank feasible strategy families: value/quality, revision, turnover/liquidity, momentum/reversal, and multi-factor score.
- Match the fields to a worked example before selecting the primary entrypoint.
- Choose one primary entrypoint by observability, mechanism, cost sensitivity, and fastest falsification.
- Define a frozen baseline and first expected phenomenon.

Failure signal:

- Immediately recommends XGBoost or a multi-factor score without timing audit, method anchor, or first falsification test.

## Scenario 2: Good IC, Bad Portfolio

Prompt shape:

```text
My factor has monthly rank IC around 4%, but the long-only backtest underperforms after costs. What should I fix?
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [strategy-development-map.md](strategy-development-map.md)
- [research-governance.md](research-governance.md)
- [playbook-factor-research.md](../playbooks/playbook-factor-research.md)
- [playbook-data-backtest.md](../playbooks/playbook-data-backtest.md)

Expected reasoning behavior:

- Separates signal evidence from portfolio evidence.
- Uses the evidence conflict matrix for IC-good/PnL-bad.
- Diagnoses likely defects: turnover, costs, weak long leg, exposure mismatch, constraints, or capacity.
- Proposes at most three targeted experiments and keeps the original baseline frozen.
- Gives a stage gate verdict no higher than `hold` until portfolio evidence improves.
- Applies the self-review checklist before recommending any repair.

Failure signal:

- Suggests changing weights, adding filters, or trying ML without diagnosing whether cost, exposure, or long-leg weakness explains the failure.

## Scenario 3: Implausibly Strong Backtest

Prompt shape:

```text
The strategy has a Sharpe above 4 and a very high t-stat. It uses fundamentals and current CSI 500 constituents. Can we deploy it?
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md)
- [playbook-data-backtest.md](../playbooks/playbook-data-backtest.md)
- [research-governance.md](research-governance.md)
- [validation-and-risks.md](../practice/validation-and-risks.md)

Expected reasoning behavior:

- Treats the result as forensic review, not deployment evidence.
- Flags current-constituent bias, financial-report timing, restatement risk, costs, and tradability.
- Requires point-in-time rebuild and next-tradable execution.
- Gives `reject` or `not determinable` stage gate until timing and universe are repaired.
- Self-review catches that object, timing, baseline, and tradability are not production-ready.

Failure signal:

- Accepts high Sharpe/t-stat as production readiness or only asks for minor robustness tests.

## Scenario 4: Small-Cap-Only Factor

Prompt shape:

```text
This factor only works in the smallest stocks and disappears in the CSI 300. Is it still useful?
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [method-idea-anchors.md](../methods/method-idea-anchors.md)
- [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md)
- [strategy-development-map.md](strategy-development-map.md)
- [research-governance.md](research-governance.md)

Expected reasoning behavior:

- Treats the result as possible size, liquidity, shell-value, distress, or capacity exposure.
- Requires equal-weight versus value-weight, microcap exclusion, liquidity filters, and capacity checks.
- Separates alpha claim from exposure-harvest or risk-control claim.
- Gives a narrower stage verdict if tradability or capacity fails.
- Uses self-review to avoid promoting a subgroup-only paper result.

Failure signal:

- Calls it a valid alpha solely because the small-cap subgroup works.

## Scenario 5: ML Model Wins

Prompt shape:

```text
An XGBoost model beats the linear baseline in OOS R2 and IC. Should I replace my factor model with it?
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [method-idea-anchors.md](../methods/method-idea-anchors.md)
- [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md)
- [ml-and-frontiers.md](../practice/ml-and-frontiers.md)
- [research-governance.md](research-governance.md)

Expected reasoning behavior:

- Checks walk-forward design, fold-local preprocessing, purging/embargo, final-test isolation, and fair baselines.
- Requires portfolio-level net return, turnover, drawdown, cost, capacity, and exposure overlap.
- Treats OOS R2/IC as prediction evidence, not replacement approval.
- Gives `hold` or `portfolio_candidate` only if investable evidence exists.
- Applies the self-review checklist before recommending replacement.

Failure signal:

- Recommends replacement based only on OOS R2 and IC.

## Scenario 6: Net Value Curve Only

Prompt shape:

```text
I only have a net value curve and summary stats. The strategy Sharpe is 3.2 with low drawdown. Please do a complete audit and tell me whether it can go live.
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [full-analysis-run-record.md](../core/full-analysis-run-record.md)
- [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md)
- [research-governance.md](research-governance.md)
- [playbook-data-backtest.md](../playbooks/playbook-data-backtest.md)
- [validation-and-risks.md](../practice/validation-and-risks.md)

Expected reasoning behavior:

- Treats the request as an audit, not production proof.
- Emits a run record snapshot with missing data state, missing baseline ID if unavailable, observed headline phenomenon, defect suspicion, and stage blockers.
- Requests or reconstructs timing, universe, signal, trades, costs, capacity, exposure, and reproducibility evidence before promotion.
- Gives `not determinable` or `hold`; does not promote from the net value curve alone.

Failure signal:

- Accepts Sharpe and drawdown as sufficient live evidence or skips the run record because raw files are absent.

## Scenario 7: Vendor Field Definition Unknown

Prompt shape:

```text
My vendor has a field called adjusted_profit_revision. I do not know its update time or whether it is restated. Use it to build a factor strategy and document the full workflow.
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [full-analysis-run-record.md](../core/full-analysis-run-record.md)
- [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md)
- [strategy-development-map.md](strategy-development-map.md)
- [research-governance.md](research-governance.md)

Expected reasoning behavior:

- Enters data evidence mode and marks vendor availability/restatement policy as the first blocker.
- Uses an external evidence card before treating the field as point-in-time.
- Performs local fit checks for A-share timing, announcement lag, revision policy, and forward-return alignment.
- Holds strategy construction or downgrades to research-only until availability is auditable.

Failure signal:

- Treats the vendor field name as self-explanatory and builds a strategy without external evidence or local fit checks.

## Scenario 8: Optimizer Extreme Weights

Prompt shape:

```text
My multi-factor optimizer gets great backtest return but puts 35% in one stock and flips sectors every month. Please diagnose and create a repair record.
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [full-analysis-run-record.md](../core/full-analysis-run-record.md)
- [strategy-development-map.md](strategy-development-map.md)
- [research-governance.md](research-governance.md)
- [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md)
- [practice-deep-dive.md](../practice/practice-deep-dive.md)

Expected reasoning behavior:

- Separates forecast evidence from optimizer and portfolio construction evidence.
- Diagnoses likely portfolio construction, risk-model, constraint, turnover, or cost/capacity defects before repair.
- Freezes a baseline and records variants with one changed element per experiment.
- Proposes at most three targeted experiments: exposure caps/position caps, covariance shrinkage or risk-model check, turnover/cost penalty or sector constraints.
- Gives a stage verdict no higher than `hold` or `portfolio_candidate` until concentration, turnover, costs, and exposure stability pass.

Failure signal:

- Adds many constraints at once without baseline, defect diagnosis, or variant registry.

## Scenario 9: Live/Paper Drift

Prompt shape:

```text
The backtest and paper trade looked good, but live trading has underperformed for four months with higher slippage and delayed signals. Should I pause the strategy?
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [full-analysis-run-record.md](../core/full-analysis-run-record.md)
- [strategy-development-map.md](strategy-development-map.md)
- [research-governance.md](research-governance.md)
- [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md)

Expected reasoning behavior:

- Treats the request as a live monitoring and reduce/pause stage-gate decision.
- Records live/paper drift, slippage, signal delay, data freshness, exposure drift, and rule/version differences in the run record.
- Diagnoses implementation mismatch, cost/slippage, data freshness, regime, or capacity before recommending repairs.
- Gives a monitor/reduce/pause verdict tied to missing or failed monitoring evidence.

Failure signal:

- Calls it normal noise or recommends retuning the factor without comparing live, paper, and backtest evidence.

## Scenario 10: High T-Stat Without Mechanism

Prompt shape:

```text
I found a new factor with a t-stat of 2.4 in A-shares. I do not have a clear economic story yet, but the backtest looks statistically significant. Is this enough to add it?
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [full-analysis-run-record.md](../core/full-analysis-run-record.md) if the user wants a recorded verdict
- [validation-and-risks.md](../practice/validation-and-risks.md)
- [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md)
- [research-governance.md](research-governance.md)

Expected reasoning behavior:

- Classifies the claim side before saying what the t-stat can prove.
- Treats `t ~= 2` as weak discovery evidence without a prior.
- Requires a mechanism, search-space record, multiple-testing control, OOS or walk-forward evidence, and economic magnitude.
- Gives `research-only`, `hold`, or `not determinable`; does not accept the factor for production.

Failure signal:

- Says the factor is valid because the t-stat is above 2.

## Scenario 11: One Winner From 200 Variables

Prompt shape:

```text
I tested about 200 accounting and price-volume variables and found one with strong IC and a good long-short spread. Help me write the conclusion.
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [full-analysis-run-record.md](../core/full-analysis-run-record.md)
- [research-governance.md](research-governance.md)
- [validation-and-risks.md](../practice/validation-and-risks.md)

Expected reasoning behavior:

- Records tested family, variants seen, search-space size, prior plausibility, multiple-testing control, and final-test policy.
- Lowers claim strength if the 200-variable search was not pre-registered, adjusted, or followed by a locked final test.
- Separates discovery evidence from validation evidence.
- Recommends a holdout, walk-forward, or paper/live plan rather than writing a confident conclusion.

Failure signal:

- Presents the surviving variable as a clean factor without discussing the 199 failed or unseen variants.

## Scenario 12: Portfolio Model Horizon Mismatch

Prompt shape:

```text
My alpha model forecasts monthly returns, the risk model uses daily covariance, the cost model assumes one-way 10 bps, and the optimizer rebalances weekly. The backtest is good. Can I productionize it?
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [full-analysis-run-record.md](../core/full-analysis-run-record.md)
- [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md)
- [practice-deep-dive.md](../practice/practice-deep-dive.md)
- [research-governance.md](research-governance.md)

Expected reasoning behavior:

- Treats the prompt as a portfolio-implementation claim, not just a backtest claim.
- Runs the model-consistency check across return horizon, risk horizon, cost horizon, rebalance frequency, benchmark, universe, constraints, and optimizer objective.
- Gives no production verdict until horizon and cost assumptions are reconciled and sensitivity tested.

Failure signal:

- Accepts the backtest without pointing out that alpha, risk, cost, and rebalance assumptions target different decisions.

## Scenario 13: Alternative Data Proxy With Weak Business Logic

Prompt shape:

```text
I have app location pings near retail stores and want to use them as a sales-growth factor. The field updates daily, but I am not sure about sample coverage or user bias.
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md)
- [ml-and-frontiers.md](../practice/ml-and-frontiers.md)
- [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md)

Expected reasoning behavior:

- Requires a domain-logic record: business mechanism, proxy validity, update timestamp, coverage bias, user-sample bias, and failure mode if pings do not represent sales.
- Treats the data as a candidate incremental signal, not a direct sales truth.
- Requires local fit checks, timestamp audit, incremental-information test against price-volume and fundamentals, and short-history caution.

Failure signal:

- Builds the factor directly from pings without checking whether the proxy measures store traffic or biased data collection.

## Scenario 14: Good Backtest Without Six Criteria

Prompt shape:

```text
This factor has high IC, good quantile monotonicity, and a positive net backtest. Can we mark it as a validated signal?
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [full-analysis-run-record.md](../core/full-analysis-run-record.md)
- [research-governance.md](research-governance.md)
- [practice-deep-dive.md](../practice/practice-deep-dive.md)

Expected reasoning behavior:

- Applies the six-criteria gate: logic, persistence, incremental information, robustness, investability, and universality.
- Identifies which criteria are proven, weak, failed, not tested, or not applicable.
- Gives `validated_signal` only if the missing criteria do not affect the current claim; otherwise gives `hold` or `research-only`.

Failure signal:

- Marks the signal validated from IC, monotonicity, and net curve alone.

## Scenario 15: Continue Optimizing Without a Diagnosed Defect

Prompt shape:

```text
The strategy is profitable but I want to improve it further. Try adding filters, changing the holding period, and neutralizing more exposures.
```

Expected references:

- [task-router.md](../core/task-router.md)
- [decision-core.md](../core/decision-core.md)
- [full-analysis-run-record.md](../core/full-analysis-run-record.md)
- [strategy-development-map.md](strategy-development-map.md)
- [research-governance.md](research-governance.md)

Expected reasoning behavior:

- Refuses to start broad optimization before recording the observed phenomenon and primary defect class.
- Freezes the current baseline and asks which weakness should be repaired: turnover, cost, drawdown, exposure, capacity, OOS decay, live drift, or another measured defect.
- Allows at most three targeted experiments, each changing one major element and updating the variant registry.
- Updates search-space/prior records as new degrees of freedom are added.

Failure signal:

- Tries many filters and horizons at once because the strategy is already profitable.
