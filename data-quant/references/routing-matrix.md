# Data-Quant Routing Matrix

Use one primary Skill and the smallest supporting set that can answer the next decision.

| Request signal | Primary route | Supporting route | Typical output |
| --- | --- | --- | --- |
| Method choice, regression/classification, clustering, causal, survival, forecasting | `statistical-learning-analysis/SKILL.md` | Shared contracts and data diagnostics | Method plan, validation design, baseline report |
| Equity factor, IC, Fama-MacBeth, A-share timing, Smart Beta | `factor-quant-analysis/SKILL.md` | Statistical diagnostics; data engineering | Factor research record and stage verdict |
| Alpha/risk/cost/portfolio/execution architecture | `quant-trading-black-box-analysis/SKILL.md` | Statistical diagnostics; factor Skill when equity factor-specific | Component map, audit, repair plan |
| CSV/schema/vendor fields/PIT/corporate actions/calendar/labels | `quant-data-engineering/SKILL.md` | Asset-class rules | Canonical table contract and evidence grade |
| Backtest is too good, unstable, or loses after costs | Domain Skill matching the strategy | Black-box audit plus shared diagnostics | Findings-first audit and targeted reruns |
| Full data-to-go-live workflow | Root `SKILL.md` | Domain Skill per stage | Manifest run, artifacts, Run Record, gate |
| HFT/order book/latency/market making | `quant-trading-black-box-analysis/SKILL.md` | Data engineering and execution replay | Mechanism analysis and fidelity-bounded replay |
| Futures/options/fixed income/FX/crypto | Corresponding asset-class Skill | Black-box and shared core | Domain contract, backtest, risk report |
| Quant manager or black-box vendor diligence | `quant-trading-black-box-analysis/SKILL.md` | Domain Skill for strategy details | Question set, verification, allocation verdict |

## Route Selection Rules

1. Route by desired outcome and claim, not by a single keyword.
2. Data and implementation artifacts force evidence mode regardless of the primary domain.
3. Equity factor requests use the factor Skill even when they mention ordinary regression.
4. Execution and HFT mechanism claims use the black-box Skill even when a factor generated the order.
5. Non-equity requests must load the matching asset-class rules before applying costs, calendars, cashflows, or leverage.
6. Complete workflows use the root router; short domain questions may invoke a child directly.
7. Do not load all children. Order supporting work as data -> research -> portfolio -> execution -> risk -> governance.

## Conflict Rules

- Shared machine contracts and fail-closed behavior outrank child formatting preferences.
- The root `references/decision-ontology.md` is the single source of truth for evidence priority and the stage/decision/action/claim-strength vocabulary; a child Skill (including a governed book-derived mirror) may restate them, but any divergence resolves in favor of the root definition.
- A child may add stricter market rules but may not weaken point-in-time, tradability, cost, or evidence requirements.
- Official effective-dated market rules outrank book summaries and generic defaults.
- Local project schemas and dependency versions outrank example field names and package APIs.
