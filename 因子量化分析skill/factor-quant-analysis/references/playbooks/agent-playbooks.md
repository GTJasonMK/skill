# Agent Playbooks

Use when: deciding how to approach a factor-strategy task, what to inspect first, what to try next, and when to stop.
Read after: [task-router.md](../core/task-router.md) selects a playbook-driven task or failure mode.
Key decisions: task mode, first inspection, next experiment, red flags, output shape.
Do not use for: detailed formulas, exact factor construction recipes, or source-table lookup.

## Contents

- [Purpose](#purpose)
- [Fast Triage](#fast-triage)
- [Playbook Index](#playbook-index)
- [Common Rules](#common-rules)
- [Missing Information Handling](#missing-information-handling)
- [Diagnostic Matrix](#diagnostic-matrix)
- [Output Patterns](#output-patterns)

## Purpose

Use this file as the procedural index. It should stay small so an agent can choose the next move without loading every playbook.

Load a specialized playbook only after the primary task is clear:

- [playbook-factor-research.md](playbook-factor-research.md) for factor ideas, single-factor validation, weak or too-good factors, and multi-factor combinations.
- [playbook-data-backtest.md](playbook-data-backtest.md) for datasets, leakage, future-function checks, and backtest reviews.
- [playbook-portfolio-ml.md](playbook-portfolio-ml.md) for research-to-portfolio conversion, portfolio implementation, ML factor selection, and alternative data.

## Fast Triage

| If the user has... | First move | Specialized playbook |
| --- | --- | --- |
| A factor idea | Check mechanism, timing, data availability, and investability | [playbook-factor-research.md](playbook-factor-research.md) |
| A single factor result | Check IC, sorting, monotonicity, controls, and costs | [playbook-factor-research.md](playbook-factor-research.md) |
| A weak factor | Diagnose construction, horizon, neutralization, sample, and mechanism mismatch | [playbook-factor-research.md](playbook-factor-research.md) |
| A too-good factor | Assume leakage or hidden cost until disproved | [playbook-factor-research.md](playbook-factor-research.md), [playbook-data-backtest.md](playbook-data-backtest.md) |
| Multiple factors | Check redundancy, exposure overlap, combination rule, and turnover | [playbook-factor-research.md](playbook-factor-research.md) |
| A dataset | Audit timestamps, universe reconstruction, and tradability fields | [playbook-data-backtest.md](playbook-data-backtest.md) |
| A backtest | Look for leakage, survivorship, execution assumptions, and missing costs | [playbook-data-backtest.md](playbook-data-backtest.md) |
| A portfolio goal | Translate signal evidence into expected return, risk, cost, and constraints | [playbook-portfolio-ml.md](playbook-portfolio-ml.md) |
| ML factor selection | Lock labels, time split, purging or embargo, baseline, and final test | [playbook-portfolio-ml.md](playbook-portfolio-ml.md) |

## Playbook Index

Use the smallest file that can answer the next decision.

| Mode | Read |
| --- | --- |
| Factor idea triage | [playbook-factor-research.md](playbook-factor-research.md) |
| Single-factor validation | [playbook-factor-research.md](playbook-factor-research.md) |
| Weak or insignificant factor | [playbook-factor-research.md](playbook-factor-research.md) |
| Too-good factor or backtest | [playbook-factor-research.md](playbook-factor-research.md), then [playbook-data-backtest.md](playbook-data-backtest.md) if data or execution details matter |
| Multi-factor combination | [playbook-factor-research.md](playbook-factor-research.md) |
| Dataset or future-function audit | [playbook-data-backtest.md](playbook-data-backtest.md) |
| Backtest review | [playbook-data-backtest.md](playbook-data-backtest.md) |
| Research-to-portfolio conversion | [playbook-portfolio-ml.md](playbook-portfolio-ml.md) |
| Machine-learning factor selection | [playbook-portfolio-ml.md](playbook-portfolio-ml.md) |

## Common Rules

Always name the estimated object:

- Prediction variable or characteristic.
- Factor exposure.
- Factor return or factor premium.
- Pricing factor.
- Anomaly alpha.
- Portfolio alpha after costs and constraints.

Use this playbook format:

1. Classify the task type and object being estimated.
2. Read only the references needed for that task.
3. Inspect the minimum facts that can invalidate the analysis.
4. Try the first concrete tests or implementation steps.
5. State red flags and stop conditions.
6. Return the smallest useful deliverable.

Do not let the word "factor" hide whether the task is prediction, pricing, exposure control, or portfolio construction.

## Missing Information Handling

Use defaults when missing information does not change the core research logic.

| Missing item | Default assumption |
| --- | --- |
| Market | A shares if the user writes in this skill context |
| Rebalance frequency | Monthly for first-pass equity factor research |
| Execution | Next tradable day after signal date |
| Return horizon | One month, plus horizon-decay checks |
| Weighting | Report equal-weight and value-weight when feasible |
| Costs | Show gross first, then require cost sensitivity |
| Neutralization | Start raw, then test industry, size, beta, and style neutralization |
| Validation split | Time split or walk-forward, never random IID split |

Ask or mark not determinable when the missing information changes the conclusion:

- No timestamp or availability date but the user asks about future-function risk.
- No trading rule but the user asks about executable performance.
- No universe but the user asks about capacity, liquidity, or benchmark-relative alpha.
- No costs but the user asks about live deployment.
- No sample period but the user asks about statistical significance.
- No final-test policy but the user asks whether ML results are reliable.

## Diagnostic Matrix

| Symptom | First suspicion | Inspect first | Acceptable conclusion |
| --- | --- | --- | --- |
| Very high Sharpe and tiny drawdown | Leakage or omitted costs | Timing, execution, costs, tradability | Credible only after strict point-in-time and cost audit |
| IC positive but portfolio return weak | Turnover, cost, or exposure mismatch | Turnover, cost, long/short legs, optimizer | Predictive but not investable, or needs different construction |
| Quantile spread significant but not monotone | Outliers or unstable relation | All buckets, Spearman rank, subperiods | Weak evidence unless mechanism predicts threshold behavior |
| Effect only in small caps | Size, liquidity, or capacity exposure | Size buckets, value-weight portfolios, liquidity filters | Implementation limited or risk-premium interpretation |
| Cost-adjusted return disappears | Turnover or market impact | Cost sensitivity, rank stability, liquidity | Not deployable without slower horizon or lower turnover |
| Sample-out failure | Overfit, crowding, publication decay, regime change | Time splits, recent period, valuation spread, crowding | Research-only unless mechanism and redesign are strong |
| Neutralization removes alpha | Alpha was exposure-driven | Pre/post exposures, economic meaning | Treat as exposure strategy or use explicit portfolio constraints |
| ML beats linear model only in sample | Overfit or leakage | Walk-forward, preprocessing scope, final test | Reject model improvement claim |
| Long-short works but long-only fails | Short leg drives anomaly | Long leg, short leg, borrow and shorting feasibility | Not suitable for long-only strategy |
| Optimizer creates extreme weights | Noisy alpha or covariance | Weight concentration, constraints, risk model | Add constraints, shrink alpha, or simplify portfolio |
| Capacity collapses | Illiquidity and crowding | ADV, participation, impact, overlap | Reduce AUM target, broaden universe, or reject |

## Output Patterns

Research design:

- Task classification.
- Hypothesis and expected sign.
- Data and timing assumptions.
- Signal construction.
- Primary tests.
- Robustness checks.
- Cost and capacity checks.
- Decision thresholds.

Audit:

- Credibility verdict.
- Critical failures first.
- Evidence gaps.
- Required reruns.
- What can still be concluded.

Diagnosis:

- Most likely cause.
- Checks to confirm or reject it.
- Next experiments, no more than three unless asked.
- Stop rule.

Implementation:

- Investable assumptions.
- Return model.
- Risk model.
- Objective and constraints.
- Cost model.
- Validation and monitoring.
- Deployment verdict.
