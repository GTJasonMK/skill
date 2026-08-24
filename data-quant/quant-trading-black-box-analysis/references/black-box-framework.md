# Black-Box Framework

## Core Idea

Quantitative trading is not mysterious because it is unknowable; it is "black box" mainly because the internal decision process is complex, systematic, and often proprietary. Analyze it by opening the box into components.

## Why Quant Trading Matters

- Quant firms can generate large trading volumes and can materially affect liquidity, price discovery, and market efficiency.
- Success stories show that systematic research, disciplined execution, and risk control can compound small advantages.
- Failure stories show that model precision can create false confidence, especially when assumptions about liquidity, correlation, leverage, or market regimes fail.
- The main transferable lessons from quants are precise thinking, explicit risk measurement, and disciplined execution.

## What A Quant Is

A quant systematically develops, tests, and implements trading strategies. The key distinction is not that the trade idea is always unique; many ideas resemble discretionary trading ideas. The distinction is that definitions, rules, data, sizing, risk, costs, and execution are made explicit enough to be tested and automated.

Avoid false binaries:

- Fully discretionary and fully systematic trading are endpoints on a spectrum.
- "Quasi-quant" processes may use screens, optimizers, or risk systems while retaining human selection or sizing.
- Human judgment remains important for strategy design, data interpretation, model selection, and deciding when a model is outside its valid domain.

## The Black-Box Components

Use this map:

- **Data**: raw input, timestamps, identifiers, fundamentals, prices, order books, alternative data.
- **Research**: idea generation, simulation, model validation, stress tests, false-positive control.
- **Alpha model**: predicts return direction, magnitude, relative performance, or trade opportunity.
- **Risk model**: identifies unwanted exposures and controls risk size.
- **Transaction-cost model**: estimates commissions, fees, slippage, and market impact before trading.
- **Portfolio construction model**: converts forecasts, risks, costs, and constraints into target holdings.
- **Execution model**: converts target trades into actual market orders.
- **Monitoring**: observes live behavior, attribution, errors, drift, and regime change.

The components may be separate modules or folded together. If a strategy lacks an explicit transaction-cost or portfolio-construction module, identify where that logic is implicitly handled.

## Lessons For Agent Reasoning

When analyzing any strategy:

1. Force vague terms into executable definitions. "Cheap", "trend", "quality", "liquid", "risk", "fast", and "fair price" must become measurable.
2. Separate idea quality from implementation quality. A good alpha can fail from costs, sizing, data, or execution.
3. Separate normal-state behavior from stress-state behavior. Many quant failures appear only during liquidation, funding stress, or correlation breaks.
4. Treat discipline as both strength and weakness. Automation prevents emotional mistakes but can amplify specification or data errors.
5. Ask how humans supervise the model without turning it into uncontrolled discretionary trading.

## Black-Box Questions

Use these questions first:

- What is the strategy trying to predict or exploit?
- What is the holding period and rebalance frequency?
- What assets are eligible and actually tradable?
- Which component produces the target portfolio?
- Which component decides whether a trade is worth its cost?
- Which component prevents unintended exposure?
- Which data are point-in-time and when are they available?
- What must happen for the strategy to lose money despite a historically good backtest?
- What live monitoring tells the manager the model is wrong, stale, crowded, or broken?
