# Analysis Run Record

Use when the user asks for a complete analysis, backtest audit, strategy repair loop, manager due diligence record, production/paper-trading decision, or any quant-trading task where the final answer should be auditable.

Purpose: leave a compact evidence trail showing which black-box component was evaluated, what claim was tested, what evidence was available, what failed, and why the verdict follows. This is not a long report; it is a disciplined record that prevents hidden cherry-picking.

Read after `task-router.md` or `reasoning-playbooks.md`. Use with `research-governance.md` when a stage decision, promotion, pause, or retirement is involved.

## Record Modes

| Mode | Use when | Required output |
| --- | --- | --- |
| `snapshot` | The answer needs a visible reasoning audit but not a full appendix | Task intake, decision spine, evidence state, verdict, missing evidence |
| `diagnostic` | Data, backtest, drawdown, strategy flaw, or manager claim is being reviewed | Snapshot plus observed phenomenon, defect class, diagnostics, targeted experiments |
| `full` | The user asks for a full workflow, audit trail, production-readiness review, or reusable research record | All sections below, compressed where evidence is unavailable |

If data is missing, do not pad the record. State which fields are not auditable and what artifact would make them testable.

## Minimal Run Record

Use this as the default visible record for strategy design, repair, audit, diligence, or promotion tasks.

| Field | Record |
| --- | --- |
| `task_type` | Explanation, strategy design, backtest audit, repair loop, drawdown diagnosis, manager diligence, HFT analysis, data artifact review, or stage decision. |
| `references_used` | Skill references actually loaded. |
| `current_question` | The one decision being answered now. |
| `object` | Alpha signal, risk exposure, cost model, optimizer, execution algorithm, data pipeline, HFT mechanism, manager, or portfolio allocation. |
| `claim_side` | Prediction edge, alpha claim, risk-control claim, cost-model claim, optimizer claim, execution claim, liquidity-provision claim, arbitrage claim, market-structure claim, or manager-quality claim. |
| `timing` | Observable timestamp, rebalance time, execution time, holding window, overnight rule, venue/session, universe, and tradability rule. |
| `baseline_id` | Frozen simple signal, portfolio rule, benchmark, cost assumption, execution assumption, and diagnostics used for comparison. |
| `black_box_map` | Alpha, risk, cost, portfolio construction, execution, data, research, monitoring, and governance components. |
| `observed_phenomenon` | Return, drawdown, Sharpe, hit rate, $R^2$, turnover, cost drag, exposure, capacity, slippage, latency, queue outcome, or missing evidence. |
| `defect_class` | Data/timing, alpha decay, hidden exposure, cost/capacity, portfolio construction, execution, risk model, overfit, regime change, crowding, HFT stale-order/adverse-selection, or operational failure. |
| `model_consistency` | Whether alpha horizon, risk horizon, cost horizon, optimizer objective, constraints, execution schedule, and universe describe the same decision. |
| `implementation_state` | Research-only, simulated, paper, live, production, retired, or not auditable. |
| `next_experiments` | No more than three targeted diagnostics tied to the defect hypothesis. |
| `stage_verdict` | Reject, not determinable, investigate, modify, build, portfolio candidate, paper trade, production candidate, monitor, reduce, pause, or retire. |
| `decision_changer` | Evidence that would change the conclusion. |

Do not leave `object`, `claim_side`, `timing`, `baseline_id`, `defect_class`, or `stage_verdict` blank when recommending a repair, promotion, rejection, or next experiment. If a field does not apply, write `not applicable`; if evidence is missing, write `not auditable`.

## Expanded Record

### 1. Task Intake

| Field | Record |
| --- | --- |
| `user_request` | Original request or compact paraphrase. |
| `task_type` | Primary task from `task-router.md`. |
| `primary_decision` | The one decision the analysis must answer. |
| `references_used` | Files loaded because they were needed. |
| `references_not_loaded` | Important files intentionally skipped and why. |

### 2. Decision Spine

| Step | Record |
| --- | --- |
| `object` | Exact research or investment object. |
| `claim_side` | Prediction, alpha, risk, cost, optimizer, execution, liquidity, arbitrage, manager, or market-structure claim. |
| `horizon` | Holding period, rebalance frequency, execution timing, and whether positions can be held overnight. |
| `universe` | Assets, geography, venues, liquidity, shorting/borrow, data coverage, and eligibility. |
| `bet_structure` | Absolute, relative, grouped, paired, market-neutral, factor, inventory, queue-position, or venue-arbitrage bet. |
| `baseline` | Frozen baseline before repairs or variants. |
| `phenomenon` | Evidence observed before interpretation. |
| `defect` | Main defect class that explains the evidence. |
| `experiment` | At most three targeted tests. |
| `decision` | Build, reject, investigate, modify, monitor, promote, pause, or retire. |

### 3. Black-Box Component Record

| Component | Required record |
| --- | --- |
| `data` | Sources, timestamps, revisions, identifiers, missing values, outliers, corporate actions, and storage. |
| `research` | Hypothesis source, in-sample/out-of-sample split, parameter selection, sensitivity, delay tests, and overfit controls. |
| `alpha_model` | Signal, direction, horizon, decay, theory/data source, combination method, and falsification test. |
| `risk_model` | Intended and unintended exposures, volatility/correlation assumptions, limits, factor model, stress tests, and model risk. |
| `transaction_cost_model` | Commissions, fees, spread, slippage, impact, borrow, rebates, financing, participation, and capacity. |
| `portfolio_construction` | Objective, sizing, constraints, optimizer/rules, alpha-risk-cost tradeoff, and sensitivity. |
| `execution_model` | Order types, venue/broker routing, urgency, passive/aggressive choice, latency, slippage measurement, and failed-fill handling. |
| `monitoring_governance` | Signal health, data QA, PnL attribution, risk breaches, kill switch, manual override, owner, and disaster response. |

### 4. Evidence Record

| Evidence | Observation | Interpretation limit |
| --- | --- | --- |
| Signal evidence | IC, $R^2$, hit rate, bucket spread, delay behavior, or decay. | Prediction evidence is not executable PnL. |
| Portfolio evidence | Gross/net return, drawdown, turnover, exposure, benchmark-relative behavior. | Net portfolio value outranks component metrics. |
| Cost/capacity | Cost drag, impact, ADV participation, liquidation time, borrow, rebates. | Can invalidate otherwise strong alpha. |
| Risk attribution | Beta, factors, sector, style, volatility, correlation, liquidity, residual. | Precise risk numbers do not prove safety. |
| Robustness | Parameter sensitivity, sample-out, regimes, stress periods, live/paper behavior. | Do not reuse final tests for tuning. |
| HFT evidence | Spread capture, queue position, adverse selection, stale quote losses, latency, fill/cancel behavior. | Cancellation or speed alone does not prove harm or value. |

### 5. Variant And Experiment Registry

Use when there is more than one tested specification, parameter choice, cost assumption, execution rule, venue choice, optimizer setting, or repair.

| `baseline_id` | `variant_id` | `changed_one_element` | `defect_hypothesis` | `expected_change` | `result` | `new_problem_created` | `decision` |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

Rules:

- Freeze the baseline before repairs.
- Change one major design element per experiment.
- Run no more than three targeted experiments per loop.
- Keep failed or invalid variants visible.
- Do not use final-test results to tune the next variant.

### 6. Evidence Conflict Resolution

Apply the priority from `task-router.md`:

```text
observable timing
> tradability and execution feasibility
> net portfolio value
> out-of-sample or live stability
> risk attribution and capacity
> causal or structural mechanism
> statistical significance
> in-sample fit
```

| Conflict | Priority applied | Verdict |
| --- | --- | --- |
|  |  |  |

If conflicts remain unresolved, mark the conclusion `not determinable`, `investigate`, or `research-only`. Do not choose the best-looking metric.

### 7. Final Claim

| Field | Record |
| --- | --- |
| `current_conclusion` | Strongest defensible conclusion. |
| `what_is_proven` | Evidence-supported claim only. |
| `what_is_not_proven` | Missing evidence or claim boundary. |
| `main_risk` | Failure mode most likely to change the conclusion. |
| `next_evidence` | Smallest data, test, or interview answer that would change the decision. |

Before finalizing, apply the final self-review checklist in `research-governance.md`. Downgrade any claim whose material evidence is missing.

