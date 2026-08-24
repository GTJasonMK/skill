# Strategy Development Map

Use when: the user wants to develop, explore, debug, or productionize a factor strategy, including 因子策略开发.
Read after: [decision-core.md](../core/decision-core.md) and [task-router.md](../core/task-router.md) when the task is broader than one method or asks "how should the agent think".
Key decisions: research object, timing, first evidence, mechanism, portfolio conversion, stop rule.
Do not use for: exact source-table lookup, long derivations, or product-only Smart Beta reviews.

## Contents

- [Purpose](#purpose)
- [Data-Feature Entrypoint Scan](#data-feature-entrypoint-scan)
- [Seven-Step Decision Flow](#seven-step-decision-flow)
- [Build-Diagnose-Repair Loop](#build-diagnose-repair-loop)
- [Phenomenon-to-Defect Matrix](#phenomenon-to-defect-matrix)
- [Situation Playbook](#situation-playbook)
- [Stop and Continue Rules](#stop-and-continue-rules)

## Purpose

Use this map to keep factor strategy work from jumping straight from an idea to a backtest. It turns the task into ordered decisions an agent can follow.

For a shorter context-light pass, use [decision-core.md](../core/decision-core.md) first. Use this map when the task needs the full entrypoint scan, build-diagnose-repair loop, or phenomenon-to-defect routing.

The default goal is not to prove the factor works. The default goal is to learn whether the idea is:

- Not testable.
- Testable but weak.
- A risk exposure.
- A research candidate.
- A portfolio candidate.
- A deployable strategy after costs, constraints, and monitoring.

## Data-Feature Entrypoint Scan

When data arrives before a clear idea, do not start with a model. Start by turning the data shape into a small set of testable strategy entrypoints.

Entrypoint process:

1. Inventory available evidence: fields, timestamps, asset keys, frequency, coverage, tradability fields, return labels, weights, trades, and known data-vendor constraints.
2. Use [method-idea-anchors.md](../methods/method-idea-anchors.md) to identify feasible strategy families from the data, not from preference: cross-sectional selection, event/revision strategy, momentum/reversal, liquidity/volatility/lottery effect, quality/value/profitability/investment, industry or style rotation, risk-control overlay, optimizer improvement, or execution/cost repair.
3. If the field-to-hypothesis move is unclear, match the data shape to [strategy-worked-examples.md](strategy-worked-examples.md) before proposing a strategy.
4. Rank entrypoints by observability, point-in-time safety, economic mechanism, sample size, tradability, cost sensitivity, and the cheapest falsification test.
5. Open a decision ledger from [research-governance.md](research-governance.md) for the selected entrypoint.
6. Pick one primary entrypoint and at most two backups. Build the simplest baseline that can disprove the idea before adding neutralization, ML, optimizer, or timing layers.
7. State the first expected phenomenon before running tests, such as positive rank IC, monotonic quantiles, lower drawdown, reduced turnover, lower unintended exposure, or improved net active return.

Data feature to entrypoint map:

| Data feature | First strategy entrypoint | First falsification |
| --- | --- | --- |
| Point-in-time fundamentals with announcement/vendor timestamps | Value, quality, profitability, investment, F-Score/G-Score, expectation-gap, or revision strategy | Availability lag audit plus raw IC/quantile test by report age |
| Daily price and volume panel | Momentum, reversal, turnover/liquidity, volatility, skewness, MAX, residual momentum, or price-volume interaction | Skip-month or short-horizon variant, turnover/cost check, long/short leg split |
| Analyst, news, text, sentiment, web, patent, geolocation, or alternative data | Information-timing, attention, sentiment, revision, or incremental signal test | Timestamp delivery audit and incremental alpha beyond price, volume, fundamentals, and industry |
| Existing factor panel or factor library | Single-factor validation, redundancy test, neutralized residual alpha, or multi-factor score | Coverage, IC decay, signal overlap, incremental alpha, and known-exposure attribution |
| Holdings, weights, or optimizer output | Portfolio construction, exposure control, constraint repair, turnover reduction, or cost/capacity repair | Exposure report, constraint check, optimizer sensitivity, cost and capacity diagnostics |
| Trades, fills, or execution logs | Execution slippage, tradability, participation, delay, and implementation-shortfall repair | Fill-rate, slippage, rejected/open order, limit/suspension, and ADV participation checks |
| Backtest metrics or net value curve only | Forensic audit before new strategy design | Rebuild timing, universe, costs, tradability, subperiod, and benchmark exposure evidence |

Prefer entrypoints that can fail quickly. A weak but falsifiable entrypoint is better than a rich story that cannot be timed, traded, or separated from known exposures.

Use [strategy-worked-examples.md](strategy-worked-examples.md) for concrete examples such as price-volume panels, announcement-date fundamentals, factor panels, optimizer outputs, trades/fills, suspicious backtests, ML predictions, and alternative data.

## Seven-Step Decision Flow

1. Define the object.
   - Name whether the object is a prediction variable, factor exposure, factor return, pricing factor, anomaly alpha, or portfolio alpha.
   - State expected sign, horizon, universe, and economic mechanism before testing.

2. Lock investable timing.
   - Define signal date, observable or vendor-availability date, rebalance date, execution date, execution price, and forward-return window.
   - For accounting data, require announcement, correction, or vendor timestamp rather than fiscal period end alone.

3. Inspect the raw signal.
   - Check coverage, missingness, dispersion, outliers, ties, stale values, rank stability, and overlap with known factors.
   - Keep raw, cleaned, standardized, and neutralized versions separate.

4. Validate prediction evidence.
   - Start with IC/rank IC, quantile portfolios, monotonicity, high-minus-low spread, horizon decay, and turnover.
   - Compare equal-weight and value-weight results when feasible.
   - Do not treat IC or gross spread as executable PnL.

5. Diagnose mechanism.
   - Compare risk compensation, mispricing, behavioral bias, market microstructure, and data-snooping explanations.
   - Test the mechanism with controls, conditional sorts, event windows, attention or arbitrage-cost proxies, and known-factor attribution.

6. Convert to portfolio evidence.
   - Define expected return model, risk model, objective, constraints, cost model, liquidity, capacity, and benchmark-relative exposure.
   - Attribute long leg, short leg, market, industry, style, residual, turnover, and cost drag.

7. Decide continuation.
   - Continue only if timing is valid, evidence is robust enough for the claim, mechanism is plausible, and net performance survives realistic costs and capacity.
   - Otherwise classify as reject, exploratory, risk-control only, research-only, or non-investable.

## Build-Diagnose-Repair Loop

Use this loop after the first entrypoint is selected. Each loop should produce either a narrower claim, a repaired design, or a stop decision.

Read [research-governance.md](research-governance.md) when evidence conflicts, repeated experiments begin, or the user asks whether the strategy can continue, promote, paper trade, or go live.

1. Build the minimum viable strategy.
   - Start with the raw signal, simple date-wise ranks, quantile portfolios, long-only top bucket, and a plain benchmark-relative comparison.
   - Keep the first baseline unchanged as the anchor for later comparisons.
   - Record `baseline_id`, `current_question`, and `selected_anchor` in the decision ledger.

2. Record observed phenomena before interpreting them.
   - Report IC/rank IC, quantile shape, long leg, short leg, turnover, cost drag, drawdown, exposure, capacity, and subperiod behavior.
   - Separate signal evidence from portfolio evidence and gross evidence from net evidence.
   - If the evidence conflicts, resolve it with the Evidence Conflict Matrix in [research-governance.md](research-governance.md).

3. Map each bad or surprising phenomenon to one primary defect class.
   - Possible classes: data/timing, label construction, signal construction, universe/tradability, hidden exposure, portfolio construction, cost/capacity, overfit/multiple testing, or regime dependence.
   - Update `primary_uncertainty` and `defect_class` before changing design.

4. Run no more than three targeted experiments per loop.
   - Change one design element at a time.
   - Prefer experiments that can falsify the current explanation: timing delay, value-weighting, long/short split, neutralization, cost sensitivity, turnover decomposition, subperiod split, or known-factor attribution.

5. Repair only the diagnosed defect.
   - Timing defect: rebuild point-in-time data, delay execution, or change the forward-return window.
   - Signal defect: fix direction, denominator, outlier policy, stale values, missing policy, rank transform, or horizon.
   - Exposure defect: report it as exposure harvest, or test neutralized/residual alpha with stated base factors.
   - Portfolio defect: adjust weighting, constraints, risk model, turnover penalty, liquidity filter, or benchmark-relative exposure.
   - Cost/capacity defect: reduce turnover, add buffers, lengthen holding period, cap ADV participation, or downgrade to research-only.

6. Compare repaired design against the frozen baseline.
   - Promote only if the repair improves the diagnosed weakness without creating a larger timing, exposure, cost, or overfit problem.
   - Log failed variants; do not hide them by presenting only the surviving specification.
   - Apply the Stage Gates in [research-governance.md](research-governance.md) before recommending paper trading, production, reduction, pause, or retirement.
   - Apply the final self-review checklist in [decision-core.md](../core/decision-core.md) before presenting the verdict.

## Phenomenon-to-Defect Matrix

| Observed phenomenon | Likely defect | Next experiment |
| --- | --- | --- |
| Result is implausibly strong | Leakage, survivorship, missing costs, current-constituent bias, or full-sample preprocessing | Strict point-in-time rebuild, next-tradable execution, realistic costs, and current-constituent removal |
| IC is positive but quantiles are not monotonic | Outliers, threshold effect, wrong transform, subgroup dependence, or weak economic link | Winsorized/raw comparison, quantile table by subgroup, and rank versus level transform |
| IC is good but portfolio PnL is weak | Turnover, costs, exposure mismatch, poor long leg, or optimizer dilution | Long/short leg attribution, turnover and cost sensitivity, exposure report, and simple top-bucket baseline |
| Spread is driven by short leg | Shorting constraint, lottery overpricing, illiquidity, or untradeable losers | Long-only proxy, borrow/short feasibility, high-risk exclusion, and short-leg tradability audit |
| Effect disappears after size/liquidity control | Small-cap, shell-value, distress, or liquidity proxy | Value-weight returns, size-neutral sort, microcap exclusion, and capacity check |
| Effect disappears after industry/style neutralization | The signal is a known exposure rather than residual alpha | Decide exposure-harvest versus residual-alpha claim; compare raw, neutralized, and exposure-attributed results |
| Gross result vanishes after costs | Excess turnover, short horizon, spread/slippage, impact, or crowding | Turnover decomposition, longer rebalance period, buffer rule, cost sensitivity, and ADV capacity test |
| Sample-out result collapses | Overfit, regime dependence, publication decay, or unstable mechanism | Walk-forward test, post-event split, regime split, simpler baseline, and variant registry audit |
| ML model beats in-sample but not out-of-sample | Leakage, full-sample preprocessing, weak baseline, or hyperparameter overuse | Purged walk-forward split, fold-local preprocessing, zero/historical mean baseline, and locked final test |
| Optimizer creates extreme weights | Forecast scale mismatch, covariance instability, weak constraints, or alpha concentration | Constraint check, optimizer sensitivity, covariance shrinkage, exposure caps, and simple rank baseline |
| Good backtest but poor live/paper behavior | Data freshness, execution slippage, regime shift, implementation mismatch, or monitoring gap | Live-vs-paper comparison, slippage report, signal health monitor, and production rule audit |

## Situation Playbook

| Situation | First question | First action |
| --- | --- | --- |
| New factor idea | What object and mechanism is being claimed? | Use [playbook-factor-research.md](../playbooks/playbook-factor-research.md) and write a research protocol. |
| Dataset arrives first | Which entrypoint is feasible from the data shape? | Use [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md), then [strategy-worked-examples.md](strategy-worked-examples.md) and the Data-Feature Entrypoint Scan before any alpha test. |
| Need a first strategy from messy data | What is the cheapest falsifiable strategy family? | Use [strategy-worked-examples.md](strategy-worked-examples.md), rank two or three entrypoints, pick the simplest baseline, and define the first expected phenomenon. |
| Strategy has a visible flaw | Which defect class explains the observed phenomenon? | Use the Build-Diagnose-Repair Loop and run at most three targeted experiments. |
| IC works but portfolio fails | Is turnover, cost, exposure, or optimizer mismatch killing the signal? | Split long/short legs, turnover buckets, costs, and exposures. |
| Factor works only in small caps | Is it size, liquidity, shell value, or capacity? | Compare value-weight results, size-neutral sorts, and liquidity filters. |
| Factor disappears after neutralization | Was alpha actually an exposure? | Decide whether to keep it as exposure strategy or redesign the claim. |
| Backtest looks too good | Is there leakage, survivorship, missing cost, or overfit? | Run strict timing, cost, tradability, and sample-out audit. |
| ML model wins | Does it beat fair baselines out of sample and after costs? | Use [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md), zero forecast baseline, walk-forward validation, and feature diagnostics. |
| Portfolio is required | Are research evidence and investable constraints compatible? | Use [playbook-portfolio-ml.md](../playbooks/playbook-portfolio-ml.md) to define return, risk, costs, constraints, and monitoring. |

## Stop and Continue Rules

Stop or mark not determinable when:

- Input observability cannot be proven.
- Execution timing is not executable.
- Results depend on current constituents, restated data, full-sample preprocessing, or arbitrary parameter search.
- Net returns vanish under realistic costs or capacity.
- The mechanism has no testable implication and many variants must be searched.

Continue only with a narrower claim when:

- The signal predicts returns but is not tradable after costs.
- The signal is useful as risk control but not alpha.
- The effect is limited to a tradable subuniverse with a plausible mechanism.
- A complex ML model adds stable sample-out value beyond simple baselines and known exposures.
