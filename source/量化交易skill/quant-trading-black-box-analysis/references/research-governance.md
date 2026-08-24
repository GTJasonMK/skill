# Research Governance And Stage Gates

Use when a quant strategy, black-box process, backtest, manager, or HFT system has conflicting evidence, repeated tuning, paper/live drift, or a question about whether to build, modify, promote, monitor, pause, or retire.

Purpose: keep the agent from changing the target midstream. A strategy may improve only through recorded evidence, a frozen baseline, targeted experiments, and explicit stage gates.

## Decision Ledger

Maintain a compact ledger for strategy development, diagnosis, and review. Embed it in `analysis-run-record.md` for complete audits.

| Field | Meaning |
| --- | --- |
| `current_question` | The one decision being answered now. |
| `object_type` | Alpha signal, risk model, cost model, optimizer, execution algorithm, HFT mechanism, manager, or portfolio. |
| `claim_side` | Prediction, alpha, risk-control, cost-model, optimizer, execution, liquidity-provision, arbitrage, market-structure, or manager-quality claim. |
| `data_state` | Available, missing, invalid, or not auditable evidence for timing, universe, tradability, costs, exposures, and execution. |
| `baseline_id` | Frozen simple signal, portfolio rule, benchmark, cost assumption, execution assumption, and diagnostics. |
| `observed_phenomena` | Signal metrics, portfolio PnL, drawdown, turnover, costs, exposures, capacity, slippage, fills, cancellations, or live/paper behavior. |
| `primary_uncertainty` | The next uncertainty that can change the decision. |
| `defect_class` | Data/timing, alpha decay, hidden exposure, cost/capacity, portfolio construction, execution, risk model, overfit, regime, crowding, or operational failure. |
| `experiments_allowed` | At most three targeted experiments tied to the defect hypothesis. |
| `rejected_variants` | Failed or invalid variants and why they were rejected. |
| `current_grade` | Reject, not determinable, investigate, modify, build, portfolio candidate, paper trade, production candidate, monitor, reduce, pause, or retire. |
| `next_decision` | Continue, rerun, repair, downgrade, promote, stop, monitor, or request missing evidence. |

Rules:

- Do not change the research question without recording why.
- Do not repair before naming the defect class.
- Do not promote a strategy using missing ledger evidence.
- Do not hide failed variants by presenting only the surviving specification.
- Do not treat a component metric as a portfolio-level proof.

## Stage Gates

| Stage | Minimum evidence | Cannot promote if |
| --- | --- | --- |
| `idea` | Object, claim, horizon, universe, bet structure, and plausible edge are stated. | No observable data path, no tradable instrument, or no falsification question. |
| `research_candidate` | Point-in-time data, historical universe, return labels, and minimum viable test can be reconstructed. | Data timing, labels, universe, or tradability cannot be audited. |
| `validated_component` | Alpha/risk/cost/execution component shows sample-out or stress evidence appropriate to its claim. | Evidence proves only in-sample fit, omits costs, or mixes claim sides. |
| `portfolio_candidate` | Net performance, turnover, constraints, risk attribution, capacity, and model consistency are tested. | Net value, unintended exposure, capacity, or alpha-risk-cost consistency fails. |
| `paper_trading` | Code/data path is reproducible, final test is locked, execution assumptions are defined, and monitoring fields exist. | Final test was reused for tuning, production data path is undefined, or rejected variants are hidden. |
| `production_candidate` | Paper/live drift, slippage, data freshness, risk limits, kill switch, rollback plan, and owner responsibilities are defined. | Monitoring, capacity cap, operational control, or disaster response is missing. |
| `live_monitoring` | Signal health, exposure drift, capacity, slippage, data freshness, and risk breaches are monitored with action thresholds. | Breaches are ignored or thresholds do not trigger decisions. |
| `reduce_pause_retire` | Persistent decay, drift, capacity stress, crowding, execution break, or rule failure is documented. | Action is based only on short-term noise without diagnostic evidence. |

Stage verdicts:

- `promote`: all minimum evidence exists and no blocker remains.
- `hold`: evidence is promising but one material check is missing.
- `downgrade`: evidence supports a narrower claim only.
- `reject`: timing, tradability, mechanism, net value, or operational control fails.
- `not determinable`: required evidence is unavailable.

## Experiment Discipline

Use experiments to change decisions, not to search until something works.

1. Freeze the baseline before the first repair.
2. Change one major design element per experiment.
3. Run no more than three targeted experiments per loop.
4. Tie each experiment to one defect hypothesis.
5. Compare every repair to the frozen baseline and simple alternatives.
6. Keep failed variants in the ledger.
7. Record added degrees of freedom: directions, windows, filters, venues, horizons, cost assumptions, risk constraints, order types, optimizer settings, and model classes.
8. Promote only if the repair solves the diagnosed defect without creating a larger timing, exposure, cost, capacity, execution, model-consistency, or overfit problem.

## Evidence Conflict Matrix

| Conflict | Interpretation | Required action |
| --- | --- | --- |
| Signal metric is strong but portfolio PnL is weak | Prediction evidence is not portfolio evidence. | Split gross/net, long/short legs, turnover, costs, constraints, and exposure attribution. |
| Portfolio works gross but fails net | Costs, turnover, impact, borrow, financing, or capacity dominate. | Downgrade unless a pre-specified lower-cost implementation restores net value. |
| Optimizer improves return but increases fragility | Forecast, covariance, or constraints may be unstable. | Perturb inputs, test constraints, compare simple sizing rules. |
| OOS prediction improves but net return worsens | Better forecasts can create expensive or constrained trades. | Check turnover, costs, capacity, and optimizer/execution interaction. |
| Risk model reports low risk but drawdown is high | Missing factor, correlation break, liquidity shock, or nonlinear exposure. | Run factor/PnL attribution, stress tests, and liquidity liquidation checks. |
| Backtest and live/paper diverge | Data freshness, execution, regime, code version, or slippage mismatch. | Compare live-vs-paper, data timestamps, fills, slippage, model versions, and venue behavior. |
| HFT spread capture is positive but tail losses dominate | Adverse selection, stale quotes, queue risk, or latency bursts dominate. | Replay order book, tail latency, cancellation, adverse selection, and inventory risk. |
| Market-structure claim is statistically weak but rhetorically strong | Mechanism and evidence are being mixed. | Specify the harm/value mechanism and evidence required for that mechanism. |

When conflicts remain unresolved, mark the claim `not determinable`, `investigate`, or `research-only`; do not select the most favorable metric.

## Final Self-Review Checklist

Before finalizing a strategy design, audit, repair, promotion, diligence, or HFT verdict, check:

- Did I name the exact object and claim side?
- Did I lock timing, horizon, universe, and tradability?
- Did I separate signal, component, portfolio, and execution evidence?
- Did I freeze or request a baseline before suggesting repairs?
- Did I diagnose the defect before proposing changes?
- Did I limit repairs to the diagnosed weakness?
- Did I include costs, liquidity, capacity, constraints, and execution timing when portfolio use is implied?
- Did I check alpha, risk, cost, optimizer, execution, and data consistency?
- Did I handle evidence conflicts by priority rather than selecting the best-looking metric?
- Did I keep failed variants visible when repeated tuning occurred?
- Did I give a stage verdict when build, promote, paper trade, productionize, monitor, reduce, pause, or retire is being considered?
- Did I state what evidence would change the conclusion?

If any material answer is missing, downgrade the claim or mark it `not determinable`.

