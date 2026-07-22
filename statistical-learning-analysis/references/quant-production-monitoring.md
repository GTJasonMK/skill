# Quant Production Monitoring

Use this reference when a quant strategy is moving from research to paper trading, live trading, or ongoing monitoring. The focus is whether the research process still matches live evidence.

## Contents

- [Promotion Stages](#promotion-stages)
- [Go-Live Gate](#go-live-gate)
- [Default Monitoring Checklist](#default-monitoring-checklist)
- [Point-in-Time Data Audit](#point-in-time-data-audit)
- [Execution Timing Audit](#execution-timing-audit)
- [Tradability Audit](#tradability-audit)
- [Model Risk Register](#model-risk-register)
- [Live vs Paper Drift](#live-vs-paper-drift)
- [Signal Health Monitoring](#signal-health-monitoring)
- [Order Exceptions](#order-exceptions)
- [Data Freshness](#data-freshness)
- [Limit Breaches](#limit-breaches)
- [Strategy Actions](#strategy-actions)
- [Aggregated Review](#aggregated-review)
- [Retirement Criteria](#retirement-criteria)
- [Monitoring Cadence](#monitoring-cadence)
- [Escalation Rules](#escalation-rules)

## Promotion Stages

| Stage | Required evidence | Stop condition |
| --- | --- | --- |
| Research candidate | Point-in-time data, execution timing, tradability evidence, clean universe rules, IC/portfolio evidence, costs, capacity, risk, and multiple-testing review. | Any unresolved leakage, invalid universe, invalid execution timing, untradable assets, or untracked strategy search. |
| Paper trading | Frozen code, frozen signal definition, live data feed, order-generation logs, paper fills, monitoring dashboard. | Paper results cannot be reconciled to research assumptions. |
| Limited live | Small capital, explicit risk/cost limits, execution monitoring, kill switch, daily reconciliation. | Live-vs-paper gap, risk breach, or execution shortfall exceeds predeclared tolerance. |
| Scaled live | Capacity evidence, stable operations, documented overrides, post-trade TCA, periodic model review. | Signal decay, cost drift, concentration, liquidity, or risk forecast failure. |

## Go-Live Gate

| Gate area | Checks |
| --- | --- |
| Data | Point-in-time fields, survivorship handling, corporate actions, stale prices, missing data, market-state flags, vendor changes, data delay. |
| Signal | Frozen formula, signal distribution, coverage, IC/rank IC, decay, turnover, neutralization, multiple testing, economic rationale. |
| Portfolio | Weight timing, constraints, exposure limits, concentration, optimizer sensitivity, risk contribution, benchmark alignment. |
| Costs and capacity | Commission, spread, slippage, borrow, financing, ADV participation, market impact, capacity assumptions. |
| Execution | Decision price, signal-to-order timing, execution timestamp, return-window convention, order generation, fills, partial fills, rejected orders, venue/broker routing, slippage monitoring. |
| Risk | Volatility forecast calibration, VaR/ES breach review, drawdown limits, stress scenarios, leverage, factor exposure. |
| Operations | Code freeze, reproducibility, logging, alerts, owner, rollback plan, kill switch, manual override process. |
| Model governance | Model inventory entry, risk tier, independent validation, approval, review cadence, limitations, waivers, monitoring owner, version evidence. |
| Reporting | Live-vs-paper report, attribution, exception log, evidence links, sign-off status. |

Use `scripts/go_live_gate_report.py` when the gate checklist is available as CSV.

## Default Monitoring Checklist

| Area | Minimum production check | Bundled utility |
| --- | --- | --- |
| Point-in-time data audit | Availability, source, period-end, universe, revision, vendor, signal, rebalance, and execution timestamps are observable at decision time. | `scripts/point_in_time_audit.py` |
| Execution timing audit | Signal, rebalance, execution, and forward-return windows follow an executable order; same-day date-only rows have price/timestamp evidence. | `scripts/execution_timing_audit.py` |
| Tradability audit | Halt/suspension status, zero/tiny volume, price-limit locks, participation, stale prices, shortability, and borrow evidence support simulated trades. | `scripts/tradability_audit.py` |
| Data freshness | Latest timestamp within tolerance, row count above floor, missing rate below threshold, upstream status healthy. | `scripts/data_freshness_report.py` |
| Signal health | Coverage, rank IC, top-bottom spread, turnover, rank stability, recent degradation. | `scripts/signal_health_monitor.py` |
| Portfolio risk | Gross/net exposure, concentration, factor exposure, risk contribution, drawdown, volatility forecast calibration. | `scripts/portfolio_constraint_check.py`, `scripts/risk_contribution_report.py`, `scripts/risk_forecast_calibration.py` |
| Limits | Breaches by date/metric/severity, consecutive breaches, unresolved high-severity blockers. | `scripts/limit_breach_report.py` |
| Execution availability | Rejected, cancelled, expired, open, and partially filled orders; aggregate fill rate. | `scripts/order_exception_report.py` |
| Execution price | Slippage, implementation shortfall, participation, spread-relative cost. | `scripts/execution_slippage_report.py` |
| Capacity and liquidity | ADV participation, binding NAV capacity, impact sensitivity, cost drift. | `scripts/capacity_impact_report.py`, `scripts/transaction_cost_report.py` |
| Live drift | Live-vs-paper gap, tracking error, correlation, underperformance streaks. | `scripts/live_vs_paper_report.py` |
| Model risk register | Owner, risk tier, validation, approval, review cadence, monitoring, rollback, kill switch, versions, evidence, open issues, and waivers. | `scripts/model_risk_register_report.py` |
| Go-live or scaling gate | Checklist status, critical/high blockers, warnings, missing evidence, owner sign-off. | `scripts/go_live_gate_report.py` |
| Action decision | Predeclared thresholds mapped to maintain, review, reduce, pause, or retire. | `scripts/strategy_action_decision.py` |
| Report aggregation | Combine JSON diagnostics into one strategy review or production health report. | `scripts/quant_report_aggregator.py` |

Use `scripts/quant_checklist_template.py` to generate starter go-live, monitoring, or retirement checklist CSV/Markdown/JSON templates.

## Point-in-Time Data Audit

Run a point-in-time audit before interpreting factor IC, sorted portfolios, backtests, paper/live comparisons, or scaling requests:

- Availability, release, filing, vendor, revision, and universe timestamps should be no later than the decision timestamp.
- Signal, rebalance, and execution timestamps should follow the intended order.
- Duplicate entity/as-of rows should be explained or removed before downstream diagnostics.
- Missing availability evidence is an evidence gap even when the data feed is fresh.

Use `scripts/point_in_time_audit.py` for date-entity factor, universe, or signal panels.

## Execution Timing Audit

Run an execution timing audit before interpreting factor IC, sorted portfolios, regressions, portfolio backtests, paper/live comparisons, or construction gates:

- Signal, rebalance, execution, return-start, and return-end timestamps should follow the intended executable order.
- Forward-return windows should start after the simulated fill; otherwise returns include periods the strategy could not earn.
- Date-only same-day signal/execution rows need intraday timestamp or price-convention evidence.
- Same-close signal and execution prices should be treated as a timing blocker unless the strategy can prove the order was executable.
- Weekend or non-calendar timestamps should be reconciled to the asset's actual trading calendar.

Use `scripts/execution_timing_audit.py` for date-entity factor panels, portfolio backtest rows, or paper/live timing checks.

## Tradability Audit

Run a tradability audit before interpreting factor IC, sorted portfolios, regressions, portfolio backtests, paper/live comparisons, or construction gates:

- Rows used for trades should not be halted, suspended, closed, or marked non-tradable.
- Buy rows should not assume fills through limit-up locks; sell/short rows should not assume fills through limit-down locks.
- Zero or tiny volume, stale repeated prices, and missing execution prices are evidence gaps or blockers depending on trade size.
- Short rows need shortability or borrow evidence; missing or unavailable borrow should block short-side promotion.
- Participation above the predeclared threshold should block or escalate the candidate before scaling.

Use `scripts/tradability_audit.py` for date-asset factor panels, long/short selections, portfolio backtest rows, or construction-gate inputs.

## Model Risk Register

Use a model-risk register when a signal, optimizer, risk forecast, execution model, or live strategy needs governance evidence beyond ordinary diagnostics:

- Owner, validator, approval status, risk tier, and active/live status.
- Last review date, next review due date, open issue count, limitations, waivers, and evidence links.
- Monitoring plan, rollback plan, kill switch or manual override, data version, and code version.
- Separate register governance from go-live checklist status: the register records accountable model ownership and review cadence; the go-live gate records launch-readiness checklist evidence.

Use `scripts/model_risk_register_report.py` for model inventory or governance-register CSVs.

## Live vs Paper Drift

Compare live and paper returns over identical timestamps and timing conventions:

- Same universe, same signal timestamp, same rebalance schedule, same weight convention.
- Same corporate-action handling and return definition.
- Same gross/net convention and cost assumptions.
- Live fills reconciled to decision price and paper execution price.
- Drift decomposed into signal, portfolio, cost, execution, data, borrow, and operational components.

Use `scripts/live_vs_paper_report.py` for a first-pass live-vs-paper return gap report.

## Signal Health Monitoring

Track the signal separately from the portfolio:

- Coverage: number of tradable assets with valid signal and forward return.
- Distribution: mean, dispersion, missingness, outlier rate, cross-sectional stability.
- Predictive evidence: IC, rank IC, top-minus-bottom spread, positive rate.
- Stability: selected-name turnover, rank autocorrelation, exposure drift.
- Recent degradation: compare recent windows against research expectations.

Use `scripts/signal_health_monitor.py` when live signal and forward-return panels are available.

## Order Exceptions

Monitor order availability separately from fill price:

- Rejected, cancelled, expired, unknown, and still-open orders.
- Partial fills and low aggregate fill rate.
- Exception clustering by asset, venue, broker, strategy, and date.
- Rejection reasons such as borrow unavailable, price band, market closed, risk limit, or stale data.

Use `scripts/order_exception_report.py` with order/fill status logs.

## Data Freshness

Run data checks before signal generation:

- Latest timestamp compared with max allowed age.
- Minimum row count by dataset or feed.
- Missing-count or missing-rate tolerance.
- Upstream status from vendor, ETL job, or reconciliation process.
- Future timestamps, stale timestamps, and invalid timestamps.

Use `scripts/data_freshness_report.py` when dataset monitoring rows are available.

## Limit Breaches

Treat risk and operations limits as production gates:

- Upper limits: gross exposure, single-name weight, turnover, VaR, drawdown, ADV participation, order rejects.
- Lower limits: cash minimum, fill rate minimum, universe coverage minimum.
- Absolute limits: beta neutrality, sector active weight, tracking-error target drift.
- Severity and owner fields should drive escalation and sign-off.

Use `scripts/limit_breach_report.py` for date/metric/value/limit monitoring tables.

## Strategy Actions

Monitoring should produce explicit capital and trading actions:

- `maintain`: no triggered threshold; continue monitoring at the normal cadence.
- `review`: evidence is weaker or noisy; require research or risk owner review before increasing capital.
- `reduce`: keep the strategy active but cut risk, gross exposure, notional, or trading frequency.
- `pause`: stop new orders until the triggering data, execution, risk, or signal issue is resolved.
- `retire`: close the strategy or remove it from the active allocation set after predeclared retirement criteria trigger.

Use `scripts/strategy_action_decision.py` when monitoring metrics have predeclared thresholds and mapped actions.

## Aggregated Review

Use a single review report when multiple diagnostics are available:

- Research review: factor IC, quantile spread, long/short backtest, multiple testing, bootstrap reality check.
- Portfolio review: backtest, constraints, exposure, risk contribution, optimizer sensitivity, attribution.
- Production review: data freshness, signal health, live-vs-paper, order exceptions, slippage, limits, action decision.
- Governance review: model-risk register, go-live gate, owner sign-off, waivers, and review cadence.

Use `scripts/quant_report_aggregator.py` to combine JSON outputs from bundled scripts into one Markdown or JSON review index. The aggregated report is a triage layer; source diagnostics still need to be read for final decisions.

## Retirement Criteria

Predeclare retirement or deallocation rules before live results are known:

- Signal evidence: recent rank IC, top-bottom spread, coverage, or positive rate below threshold for repeated windows.
- Implementation evidence: live-vs-paper gap, slippage, order exceptions, or borrow failures above tolerance.
- Risk evidence: drawdown, VaR/ES breach clustering, exposure drift, or risk contribution concentration above tolerance.
- Capacity evidence: ADV participation, binding capacity, or cost drift invalidates expected net alpha.
- Operations evidence: stale data, manual overrides, incident count, or unresolved high-severity breaches.

Retirement decisions should separate `signal no longer works` from `implementation no longer matches research`.

## Monitoring Cadence

| Cadence | Review |
| --- | --- |
| Daily | PnL reconciliation, live-vs-paper gap, order/fill exceptions, risk limits, data freshness. |
| Weekly | Signal health, turnover, cost drift, exposure drift, regime behavior, drawdown. |
| Monthly | Attribution, capacity, optimizer sensitivity, risk forecast calibration, benchmark-relative behavior. |
| Quarterly | Research assumptions, factor crowding, model decay, vendor changes, code dependency changes, strategy retirement criteria. |

## Escalation Rules

- Pause trading when live-vs-paper drift exceeds the predefined loss or tracking-error tolerance.
- Reduce capital when realized slippage or participation exceeds capacity assumptions.
- Freeze new orders when data freshness, corporate-action, or universe membership checks fail.
- Re-review the model when rank IC, top-minus-bottom spread, or signal coverage deteriorates for several consecutive monitoring windows.
- Recalibrate or de-risk when volatility forecasts understate realized risk or VaR breaches cluster.
- Convert repeated unresolved alerts into a predeclared action: review, reduce, pause, or retire.
- Document every override with owner, timestamp, reason, and rollback condition.
