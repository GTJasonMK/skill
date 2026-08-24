---
name: quant-trading-black-box-analysis
description: "Quantitative trading analysis workflow distilled from Rishi K. Narang's Open the Black Box. Use when Codex needs to design, explain, review, audit, or compare quantitative trading strategies, black-box investment processes, alpha models, risk models, transaction-cost models, portfolio construction, execution algorithms, data pipelines, research/backtesting, model risk, strategy crowding, quant-manager due diligence, high-speed trading, HFT strategies, order-book mechanics, flash-crash debates, market microstructure, or Chinese requests involving 量化交易、宽客、黑箱、阿尔法模型、风险模型、交易成本、组合构建、执行模型、数据清洗、回测研究、高速交易、高频交易、做市、套利、流动性、订单簿、闪电崩盘、量化策略评估。"
---

# Quant Trading Black Box Analysis

## Overview

Use this skill to reason like a disciplined quant analyst, not merely to summarize quant jargon. Treat every strategy or manager as a black box with explicit components: alpha, risk, transaction costs, portfolio construction, execution, data, research, monitoring, and market structure.

The skill is based on the local Markdown chapter summaries for *打开量化投资的黑箱（第二版）*. For exact chapter-level wording, inspect `/home/fufu/Code/Skills/source/量化交易skill/md`.

When the task involves local data, code, logs, backtests, trades, weights, exact API behavior, market rules, or venue mechanics, switch from explanation mode to evidence mode: inspect the artifact, verify timing and implementation assumptions, use authoritative documentation for exact external rules, and validate the conclusion against the local strategy constraints.

## Reference Routing

Load only the references needed for the task:

- For broad or ambiguous quant-trading tasks, routing uncertainty, failure-mode routing, or output-shape selection read [references/task-router.md](references/task-router.md) first.
- For general quant strategy structure, black-box components, lessons from quants, or "what is a quant?" read [references/black-box-framework.md](references/black-box-framework.md).
- For alpha/risk/cost/portfolio/execution/data/research component design or diagnosis read [references/model-components.md](references/model-components.md).
- For backtest review, overfitting, data leakage, model risk, endogenous risk, quant critiques, or manager due diligence read [references/validation-risk-audit.md](references/validation-risk-audit.md).
- For high-speed trading, HFT, order books, market making, latency, arbitrage, flash-crash debates, regulation, or market microstructure read [references/hft-market-structure.md](references/hft-market-structure.md).
- For final deliverables, checklists, question sets, strategy memos, or audit templates read [references/checklists.md](references/checklists.md).
- For formulas, metrics, thresholds, and quantitative definitions read [references/metrics-formulas.md](references/metrics-formulas.md).
- For task-specific reasoning playbooks, decision trees, and diagnostic loops read [references/reasoning-playbooks.md](references/reasoning-playbooks.md).
- For complete analysis records, auditable strategy reviews, data/backtest artifacts, repair logs, manager diligence records, or production-readiness reviews read [references/analysis-run-record.md](references/analysis-run-record.md).
- For stage gates, repeated tuning, evidence conflicts, paper/live decisions, promotion, monitoring, pause, or retirement decisions read [references/research-governance.md](references/research-governance.md).
- For Chinese-English term mapping, Chinese prompts, or exact Chinese concept routing read [references/bilingual-glossary.md](references/bilingual-glossary.md).
- For chapter-to-skill traceability or exact topic coverage read [references/source-coverage.md](references/source-coverage.md).

## Core Reasoning Spine

For any quant-trading task, answer these in order:

1. **Object**: Name what is being analyzed: alpha signal, risk exposure, cost model, optimizer, execution algorithm, data pipeline, HFT strategy, manager, or portfolio allocation.
2. **Claim**: State the claim side: prediction edge, risk control, cost reduction, liquidity provision, arbitrage, portfolio improvement, or operational robustness.
3. **Horizon**: Define holding period, rebalance frequency, execution timing, and whether positions can be held overnight.
4. **Universe**: Define tradable assets, geography, liquidity, shorting/borrow constraints, market venues, and data coverage.
5. **Bet Structure**: Separate absolute bets, relative bets, factor bets, market-neutral bets, inventory bets, and order-book queue bets.
6. **Black-Box Map**: Identify alpha, risk, cost, portfolio construction, execution, data, and research components. If any component is missing, state whether it is intentionally folded into another component.
7. **Baseline**: Freeze or request the simplest comparable baseline before proposing repairs, variants, or optimizer changes.
8. **Evidence**: Separate observed performance from causal explanation. Require sample design, out-of-sample evidence, transaction costs, risk attribution, and capacity checks before accepting an investable claim.
9. **Failure Modes**: Check model misspecification, regime change, exogenous shock, crowding, liquidity collapse, execution error, data pollution, stale orders, and overfitting.
10. **Decision**: Provide a concrete recommendation: build, reject, monitor, stress test, ask diligence questions, alter component design, run a targeted experiment, or apply a stage gate.

If evidence is missing, do not invent certainty. State the smallest data, test, or interview question that would change the decision.

## Black-Box Workflow

### 1. Classify the Strategy

Classify by all relevant axes:

- Alpha type: trend, mean reversion, technical sentiment, value/yield, growth, quality, data-driven, hybrid, fast alpha.
- Bet structure: absolute, relative, paired, grouped, factor-neutral, index/venue/structural arbitrage.
- Horizon: HFT intraday, short-term days/weeks, medium-term weeks/months, long-term months/years.
- Implementation: rule-based, optimized, discretionary override, semi-systematic, automated execution, HFT infrastructure.
- Market role: liquidity demander, liquidity supplier, market maker, arbitrageur, execution algorithm, portfolio allocator.

Do not mix up a prediction variable, alpha model, risk exposure, portfolio alpha, and executable PnL. Name the object precisely.

### 2. Map Components Before Judging Results

Use the black-box component map:

```text
data + research -> alpha model
data + research -> risk model
data + research -> transaction-cost model
alpha + risk + costs + constraints -> portfolio construction
target portfolio + venue/liquidity/urgency -> execution model
execution outcomes -> research, cost model, monitoring
```

When a user asks "is this strategy good?", avoid jumping to returns. First identify which component is responsible for the observed behavior and which component could fail.

### 3. Evaluate Evidence Like a Researcher

Require:

- clean point-in-time data and clear timestamp assumptions;
- sample-in vs sample-out separation;
- sensitivity to parameters, universe, horizon, costs, shorting, and liquidity;
- predictive tests such as monotonic buckets, $R^2$, hit rate, delay tests, and risk-adjusted returns;
- portfolio tests net of turnover, slippage, market impact, constraints, and execution feasibility;
- evidence that the strategy still works when reasonable implementation frictions are included.

Treat very high predictive power in noisy financial data as suspicious until data leakage, lookahead, survivorship bias, and hidden information are ruled out.

### 4. Diagnose Risk Endogeneity

Quant strategies create risks through their own design. Always check:

- model risk: wrong question, wrong model, wrong implementation;
- relationship change: correlations, factor relationships, and relative-value spreads shift over time;
- exogenous shock: regulation, war, credit crisis, short bans, funding stress, market closures;
- crowding and contagion: similar funds liquidate similar longs and shorts at the same time;
- monitoring failure: PnL attribution cannot explain losses by alpha, beta, factors, costs, liquidity, or errors.

Do not treat a green backtest as evidence that these risks are absent. Ask what would break the model.

### 5. Handle HFT And Market Microstructure Separately

For HFT/high-speed tasks, reason in order-book terms:

- passive orders earn spread/rebates but face adverse selection and queue risk;
- aggressive orders pay spread but gain certainty and speed;
- cancellation speed protects against stale quotes;
- latency matters at the venue, cross-venue, feed-handler, order-book, signal, and risk-check layers;
- market making, arbitrage, and fast alpha have different sources of edge and different failure modes.

For HFT controversies, separate evidence from rhetoric: unfairness, front-running, cancellation rates, volatility, flash-crash responsibility, social value, and regulation require different tests.

## Output Contract

For strategy design or explanation, return:

- strategy classification, universe, horizon, and bet structure;
- black-box component design;
- expected edge and why it should exist;
- data and research requirements;
- risk, cost, portfolio construction, and execution implications;
- validation plan and failure modes.

For strategy audit or backtest review, return:

- claim being tested and what evidence would prove it;
- data timing and cleaning audit;
- sample-in/sample-out and parameter sensitivity review;
- performance decomposition before and after costs;
- hidden risk, crowding, liquidity, and capacity review;
- verdict and next experiment.

For complete analysis, repair loops, production-readiness reviews, or auditable backtest/manager reviews, also include a compact run record:

- references used;
- object, claim side, timing, universe, bet structure, and baseline ID;
- black-box component map;
- observed phenomenon and defect class;
- model consistency across alpha, risk, costs, portfolio construction, execution, and data;
- targeted experiments, evidence conflicts, stage verdict, and missing evidence.

For manager due diligence, return:

- questions grouped by research, data, alpha, portfolio construction, execution, risk monitoring, team, integrity, and portfolio fit;
- expected good answers and red flags;
- what must be independently verified.

For HFT or market-structure analysis, return:

- order-book mechanics;
- speed/latency dependency;
- liquidity effect;
- adverse-selection and stale-order risk;
- evidence needed for claims about volatility, manipulation, or fairness.

## Hard Rules

- Do not call a strategy "alpha" merely because historical returns are positive.
- Do not equate statistical significance with executable PnL.
- Do not ignore transaction costs, slippage, market impact, borrow/short constraints, and execution timing.
- Do not use future information: align every input by when it was observable and tradable.
- Do not trust a risk number just because it is precise.
- Do not accept an optimizer output without checking sensitivity to expected returns, volatilities, correlations, constraints, and costs.
- Do not treat liquidity as order-book size alone; define it as the ability to transact immediately, at size, at a fair price.
- Do not blame or defend HFT as a category; identify the actual mechanism and evidence.
- Do not let a component-level metric prove a portfolio-level claim. Signal IC, model $R^2$, spread capture, or low VaR is only one input to executable net performance.
- Do not optimize a strategy before freezing the baseline and naming the defect being repaired.
- Do not promote a strategy, manager, or HFT system without a stage-gate verdict when the user asks whether it can continue, paper trade, go live, scale, pause, or retire.
