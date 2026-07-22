# Task Router

Use this file first for ordinary quant-trading tasks when the request is broad, ambiguous, or could load many references. Route to the smallest useful reference bundle, then stop loading once the next decision can be made.

## Default Process

1. Classify the request into one primary task.
2. Identify the current decision: explain, design, audit, repair, diligence, HFT analysis, implementation review, or stage verdict.
3. Load only the minimum references listed below.
4. If the user provides data, code, logs, backtest output, trades, weights, venue details, or exact API/rule questions, inspect the artifact or authoritative source before concluding.
5. Return the output shape for the task; avoid generic quant commentary.

## Task Bundles

| Task | Use when | Minimum references | Add only if needed |
| --- | --- | --- | --- |
| Strategy explanation | User asks what a quant strategy is doing or how a black box works | `black-box-framework.md`, `model-components.md` | `bilingual-glossary.md` for Chinese aliases; `metrics-formulas.md` for formulas |
| Strategy design | User wants to build a strategy, alpha model, portfolio process, or execution process | `model-components.md`, `reasoning-playbooks.md`, `metrics-formulas.md`, `checklists.md` | `research-governance.md` for stage gates; `analysis-run-record.md` for auditable records |
| Backtest audit | User asks whether a backtest proves a claim or contains leakage | `validation-risk-audit.md`, `reasoning-playbooks.md`, `metrics-formulas.md`, `analysis-run-record.md` | `research-governance.md` for promotion decisions; original `md/` files for chapter-level detail |
| Strategy repair | User has a weak, too-good, unstable, costly, or live-decaying strategy | `reasoning-playbooks.md`, `validation-risk-audit.md`, `research-governance.md`, `analysis-run-record.md` | `model-components.md` for component redesign |
| Drawdown diagnosis | User asks why a quant strategy lost money or diverged from expectations | `validation-risk-audit.md`, `reasoning-playbooks.md`, `analysis-run-record.md` | `metrics-formulas.md` for attribution and risk measures |
| Manager due diligence | User evaluates a quant manager, fund, or black-box provider | `validation-risk-audit.md`, `checklists.md`, `analysis-run-record.md` | `source-coverage.md` for exact book-derived topics |
| HFT and market structure | User asks about high-speed trading, HFT, order books, liquidity, or flash crashes | `hft-market-structure.md`, `metrics-formulas.md`, `checklists.md` | `research-governance.md` for regulation or production-readiness claims |
| Data or implementation artifact | User provides CSV/table/schema/code/backtest/trades/weights or asks what evidence proves | `model-components.md`, `validation-risk-audit.md`, `analysis-run-record.md` | Use project scripts and official/Context7 docs for exact library behavior |
| Complete analysis record | User asks for complete workflow, auditable analysis, production-readiness review, or strategy run record | `analysis-run-record.md`, `research-governance.md`, `reasoning-playbooks.md` | Task-specific component references |
| Chapter coverage or exact source lookup | User asks whether a chapter/topic is covered or wants source traceability | `source-coverage.md` | Local `/home/fufu/Code/Skills/量化交易skill/md` chapter summaries |

## Failure Mode Routing

| Symptom | First suspicion | First checks |
| --- | --- | --- |
| Sharpe, CAGR, hit rate, or $R^2$ looks too good | Leakage, survivorship, hidden future data, missing costs | Timestamp audit, universe reconstruction, signal/return alignment, cost replay |
| Signal evidence is good but portfolio PnL is weak | Turnover, costs, constraints, capacity, or unwanted exposure | Gross-to-net bridge, turnover, exposure attribution, long/short leg split |
| Optimizer produces extreme or unstable weights | Forecast/covariance sensitivity, weak constraints, cost mismatch | Input perturbation, constraint audit, risk/cost horizon consistency |
| Drawdown is unexplained | Alpha decay, risk exposure, liquidity shock, execution break, model bug | PnL attribution, factor exposure report, slippage replay, data QA |
| Strategy fails after delay | Signal decay, stale data, unrealistic execution timestamp | Delay tests, execution schedule audit, event-time reconstruction |
| Good result disappears after costs | Turnover, spread, impact, borrow, financing, rebates omitted | Cost decomposition, participation-rate stress, capacity estimate |
| HFT claim is moral or rhetorical only | Mechanism not specified | Identify passive/aggressive orders, queue, adverse selection, latency layer, venue rule |
| HFT cancellation rate is used as proof of harm | Stale-quote management and manipulation are mixed | Separate stale-order protection, queue management, spoofing, quote stuffing, venue fragmentation |
| Flash-crash claim blames one actor | Multi-causal market-structure event is oversimplified | Separate order flow, liquidity withdrawal, market rules, feedback loops, data delays |
| Manager gives strong returns but vague process | Due diligence gap or integrity risk | Ask process questions, compare story to performance, verify data/cost/risk controls |
| Live strategy drifts from backtest | Implementation, execution, regime, crowding, or data freshness mismatch | Live-vs-paper attribution, data freshness, slippage, model version, crowding proxy |
| Strategy is repeatedly tuned | Hidden p-hacking and moving target | Freeze baseline, record variants, limit next tests to diagnosed defects |

## Evidence Priority

Resolve conflicts in this order:

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

If a lower-priority metric is strong but a higher-priority check fails, downgrade the claim. Do not choose the most optimistic metric.

## Output Shape Routing

| Task | Output shape |
| --- | --- |
| Strategy explanation | Classification, universe, horizon, bet structure, black-box components, edge source, key risks |
| Strategy design | Claim, data, alpha, risk, cost, portfolio, execution, validation plan, monitoring, next experiment |
| Backtest audit | Findings first, timing/data audit, gross-to-net bridge, robustness, hidden risks, verdict |
| Strategy repair | Baseline, observed phenomenon, defect class, at most three targeted experiments, stage verdict |
| Drawdown diagnosis | PnL attribution hypotheses, evidence needed, smallest diagnostic, action trigger |
| Manager diligence | Question set, expected good answers, red flags, independent verification, allocation verdict |
| HFT analysis | Order-book mechanism, latency dependency, liquidity effect, adverse selection, evidence needed |
| Data artifact analysis | Data object, keys/timestamps, coverage, diagnostics run, decision grade, missing evidence |
| Complete analysis | Compact run record from `analysis-run-record.md` plus recommendation |

