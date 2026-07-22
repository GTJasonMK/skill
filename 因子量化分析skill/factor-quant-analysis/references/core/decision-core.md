# Decision Core

Use when: a factor task needs a fast reasoning spine before loading larger references, or the agent is about to deliver a strategy recommendation, repair, promotion, or rejection.

Purpose: keep the agent from overloading context before the first decision is clear. Use this file as the smallest operating loop, then load detailed references only for the current uncertainty.

## Contents

- [Core Decision Chain](#core-decision-chain)
- [Load-Minimum Rule](#load-minimum-rule)
- [Mandatory Output Switches](#mandatory-output-switches)
- [Final Self-Review Checklist](#final-self-review-checklist)

## Core Decision Chain

Run this chain before proposing a model, factor, repair, or portfolio rule:

```text
object -> claim_side -> timing -> anchor -> baseline -> phenomenon -> defect -> experiment -> gate
```

| Step | Decision | Fail-fast question |
| --- | --- | --- |
| `object` | Name what is being estimated: characteristic, exposure, factor return, pricing factor, prediction variable, portfolio alpha, or risk-control rule. | Am I mixing signal evidence, factor exposure, and investable alpha? |
| `claim_side` | Name the side of the claim: `alpha_claim`, `beta_lambda_claim`, `risk_model_claim`, `prediction_claim`, or `portfolio_implementation_claim`. | Am I using evidence for one claim side to prove another? |
| `timing` | Lock observable date, rebalance date, execution date, forward-return window, universe, and tradability rule. | Could this input or universe be known only after the trade? |
| `anchor` | Pick one method or factor-family center idea from [method-idea-anchors.md](../methods/method-idea-anchors.md). | What first empirical result would falsify this idea? |
| `baseline` | Freeze the simplest valid baseline: raw signal, rank rule, universe, benchmark, cost assumption, and diagnostics. | Can later variants be compared to one unchanged baseline? |
| `phenomenon` | Record actual IC, quantile shape, long/short legs, turnover, costs, exposures, capacity, OOS, and live/paper behavior. | Am I interpreting before observing the result? |
| `defect` | Map the main bad or surprising phenomenon to one defect class. | Which single defect explains the evidence best? |
| `experiment` | Run at most three targeted experiments tied to the defect hypothesis. | Am I changing one major design element at a time? |
| `gate` | Apply stage gates before continue, downgrade, promote, paper trade, productionize, pause, or retire. | Is the verdict supported by timing, tradability, net value, OOS, mechanism, and monitoring evidence? |

## Load-Minimum Rule

Start with this file when the request is broad, then load only the next useful reference:

| Current uncertainty | Next reference |
| --- | --- |
| Which method or factor family should anchor the work? | [method-idea-anchors.md](../methods/method-idea-anchors.md) |
| The user asks for a complete analysis, full workflow record, strategy run record, end-to-end audit, or auditable process trace. | [full-analysis-run-record.md](full-analysis-run-record.md) |
| The user provided data, fields, code, logs, backtest output, weights, or trades. | [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md) |
| Need to turn data features into a first strategy entrypoint. | [strategy-worked-examples.md](../strategy/strategy-worked-examples.md), then [strategy-development-map.md](../strategy/strategy-development-map.md) |
| A factor or strategy result is weak, too good, unstable, or contradictory. | [strategy-development-map.md](../strategy/strategy-development-map.md), then [research-governance.md](../strategy/research-governance.md) |
| The answer depends on promotion, paper trading, production, reduction, pause, or retirement. | [research-governance.md](../strategy/research-governance.md) |
| Exact construction, formula, econometric test, or A-share rule is needed. | The task-specific reference selected by [task-router.md](task-router.md) |

If the next decision can be made from the current reference, stop loading more files.

## Mandatory Output Switches

Include the listed output elements whenever the trigger appears:

| Trigger | Required output element |
| --- | --- |
| Strategy entrypoint discovery | Object, claim side, feasible anchors, chosen baseline, first expected phenomenon, first falsification test. |
| Complete analysis, full workflow record, end-to-end audit, or strategy run record | Compact run record from [full-analysis-run-record.md](full-analysis-run-record.md): references used, decision spine, evidence state, claim side, baseline ID, observed phenomenon, defect class, six criteria, search-space/prior state when relevant, model consistency when relevant, domain logic when relevant, experiment registry or next experiments, conflicts, gate verdict, and missing evidence. |
| Strategy repair or repeated optimization | Decision ledger snapshot, frozen `baseline_id`, observed phenomenon, defect class, no more than three experiments. |
| Conflicting IC, quantile, regression, portfolio, cost, or OOS evidence | Evidence conflict resolution using the priority in [research-governance.md](../strategy/research-governance.md). |
| Paper trade, production, promotion, reduction, pause, or retirement question | Stage gate verdict and missing blockers. |
| Data or external rule uncertainty | Data diagnostics, source checked, local fit check, unverified assumptions. |
| New factor discovery, many tested variables, ML search, or repeated variants | Tested family, search-space size or unknown, prior plausibility, multiple-testing control, and locked final-test policy. |
| Factor effectiveness, promotion, or rejection claim | Six criteria grade: logic, persistence, incremental information, robustness, investability, and universality. |
| Portfolio optimization, Smart Beta, risk attribution, or production portfolio use | Model consistency: return model, risk model, cost model, constraints, optimizer objective, benchmark, universe, and horizon alignment. |
| Fundamental, industry, event, text, alternative-data, or microstructure signal | Domain logic: accounting/business/economic/data-generating mechanism, proxy validity, local fit, and failure mode if the proxy is wrong. |

## Final Self-Review Checklist

Before the final answer on any strategy-design, data-artifact, backtest-review, or promotion task, check:

- Did I name the object being estimated?
- Did I name the claim side and avoid using prediction evidence as alpha, pricing, risk-model, or portfolio evidence?
- Did I lock investable timing and state any unknown availability dates?
- Did I separate signal evidence from portfolio evidence?
- Did I avoid treating IC, spread, alpha, or OOS loss as executable PnL by itself?
- Did I state the method anchor and the first falsification question?
- Did I grade logic, persistence, incremental information, robustness, investability, and universality when factor effectiveness or promotion is being claimed?
- Did I record tested family, variants, search-space size or unknown, prior plausibility, multiple-testing control, and final-test isolation when discovery or repeated search is involved?
- Did I freeze or request a baseline before suggesting repairs?
- Did I diagnose the defect before proposing changes?
- Did I limit repairs to the diagnosed weakness?
- Did I handle evidence conflicts by priority instead of choosing the best-looking metric?
- Did I include costs, liquidity, capacity, exposure, and monitoring when portfolio use is implied?
- Did I check return-model, risk-model, cost-model, constraint, benchmark, universe, and horizon consistency when optimizer or portfolio use is implied?
- Did I check accounting, business, economic, microstructure, industry, or data-generating logic when the signal depends on domain interpretation?
- Did I give a stage gate verdict when continuation, promotion, or stop decisions are involved?
- Did I state what evidence would change the conclusion?
- If this was a complete analysis, repair record, audit, or production-readiness decision, did I include the compact run-record fields from [full-analysis-run-record.md](full-analysis-run-record.md)?
- Did I record `baseline_id`, rejected or invalid variants, and external evidence cards when they materially affect the decision?

If any answer is "no" and the missing item is material, mark the conclusion `not determinable`, downgrade the claim, or request the missing evidence.
