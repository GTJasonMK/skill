---
name: data-quant-hybrid
description: "Unified router and execution contract for statistical learning, quantitative data engineering, factor research, portfolio construction, backtesting, execution analysis, risk, monitoring, market microstructure, and asset-class-specific quant work. Use as the single entrypoint for broad, ambiguous, end-to-end, or cross-skill data/quant requests; route to the smallest local specialist set and require machine-readable evidence before stage promotion. 中文触发：数据分析、统计学习、量化研究、因子投资、A股因子、回测审计、组合优化、交易成本、执行、风险、监控、高频、期货、期权、固收、外汇、加密资产。"
version: 1.0.0
---

# Data-Quant Hybrid Router

## Purpose

This is the canonical entrypoint for the complete `data-quant` bundle. It coordinates domain reasoning, local artifacts, shared diagnostics, and stage-gate decisions without loading every child Skill. The shared evidence contract outranks optimistic component metrics.

This bundle supports research, offline replay, and monitoring analysis. It does not submit live orders, move funds, store credentials, or operate a broker/exchange account.

## Operating Contract

1. Classify the object, claim side, asset class, horizon, decision timestamp, execution assumption, universe, and requested outcome before selecting a method.
2. Route to one primary Skill and only the supporting references needed for the next decision.
3. When data, code, weights, trades, logs, or schemas exist, enter evidence mode: inspect the artifact and run the smallest diagnostic that can change the conclusion.
4. Treat data availability, universe reconstruction, tradability, execution timing, net value, out-of-sample evidence, risk, capacity, and mechanism as separate checks.
5. Exchange only versioned Artifact and Run Record objects between stages; never hand off a dump of live objects or whole reference directories.
6. Missing point-in-time, tradability, cost, or execution evidence is an evidence gap and prevents paper/production promotion.
7. Preserve failed variants and the frozen baseline. Permit at most three targeted experiments per diagnosed defect before updating the decision ledger.
8. Use the shared stage, decision, action, and claim-strength vocabulary in `references/decision-ontology.md`.
9. Finish complete tasks with a Run Record and stage-gate verdict. Short conceptual answers may stop after the relevant domain explanation.

## Primary Routes

- General statistical learning, model selection, evaluation, causal/survival/time-series method guidance: `statistical-learning-analysis/SKILL.md`.
- Equity factor research, empirical asset pricing, A-share data rules, Smart Beta, factor mechanism and portfolio conversion: `factor-quant-analysis/SKILL.md`.
- Quant strategy components, execution, HFT, market microstructure, drawdown diagnosis, and manager due diligence: `quant-trading-black-box-analysis/SKILL.md`.
- Point-in-time tables, identifiers, calendars, corporate actions, labels, vendor fields, and data pipelines: `quant-data-engineering/SKILL.md`.
- Futures: `futures-quant-analysis/SKILL.md`.
- Options and volatility: `options-volatility-analysis/SKILL.md`.
- Fixed income: `fixed-income-quant-analysis/SKILL.md`.
- Foreign exchange: `fx-quant-analysis/SKILL.md`.
- Crypto spot, perpetuals, and venue risk: `crypto-quant-analysis/SKILL.md`.

Never apply equity defaults silently to another asset class.

For exact task-to-route mapping, read `references/routing-matrix.md`. For handoffs, read `references/workflow-contract.md`. For official-rule and vendor-source evidence, read `references/source-governance.md` and `source-registry.yaml`.

## Evidence Priority

The authoritative evidence-priority ordering and the shared stage/decision/action/claim-strength vocabulary live in `references/decision-ontology.md`. Child Skills may restate the ordering for self-containment, but `decision-ontology.md` is the single source of truth; do not introduce a divergent ordering.

If a lower-priority result is strong but a higher-priority check fails, downgrade the claim. Do not average conflicts away.

## Standard Workflow

```text
intake
-> data contract and canonicalization
-> point-in-time / timing / tradability audit
-> labels and validation splits
-> research diagnostics
-> portfolio / backtest / execution / risk
-> governance gate
-> Run Record and review report
```

Stop early when the user requested only explanation or when a required artifact is missing. Mark the handoff `needs_input` or `blocked`; do not invent the evidence.

## Machine Contracts

- Run manifest: `schemas/run-manifest.schema.json`
- Artifact envelope: `schemas/artifact-envelope.schema.json`
- Run record: `schemas/run-record.schema.json`
- Stage gate: `schemas/stage-gate.schema.json`

Use `quantctl doctor`, `quantctl validate-manifest`, and `quantctl verify-artifact` for local validation.

## Shared Guardrails

- Never sort unparsed date strings or assume naive timestamps are UTC.
- Never construct adjusted returns, universes, or labels using future corporate actions, revisions, constituents, or vendor vintages.
- Never call gross IC, regression alpha, or optimizer output investable alpha without costs, constraints, risk, and execution evidence.
- Never silently repair a non-PSD covariance matrix, infeasible optimizer, invalid schema, or missing required diagnostic.
- Never hide rejected variants or reuse a locked final test for tuning.
- Never claim HFT fidelity without the market-depth, venue-priority, and latency evidence required by the mechanism.
- Never write generated runs, credentials, environments, or caches into the Skill bundle.
- Never send live orders. Execution capabilities are offline research, simulation, replay, and audit only.

## Completion Contract

A complete implementation, audit, repair, or promotion task returns:

1. primary route and references used;
2. data and timing evidence state;
3. baseline and observed phenomena;
4. diagnostics and Artifact IDs;
5. blockers, warnings, and evidence gaps;
6. stage, decision, action, and claim strength;
7. no more than three targeted next experiments;
8. the evidence that would change the conclusion.
