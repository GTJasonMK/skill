# HFT And Market Structure

## Definitions

High-speed trading is low-latency infrastructure and process. High-frequency trading is one category of strategy that uses such infrastructure.

A practical HFT definition:

- requires high-speed trading facilities;
- operates on holding periods below one day;
- normally avoids overnight positions.

Users of high-speed facilities include ultra-high-frequency traders, HFT firms, medium-frequency traders, and algorithmic execution engines.

HFT economics are usually thin per share. Small spread capture, rebates, or fast-alpha gains require large volume, strong infrastructure, and strict risk controls. High revenue stories should be checked against fees, infrastructure, adverse selection, inventory losses, and competition.

## Order-Book Mechanics

Passive orders rest in the limit order book and do not immediately execute. Aggressive orders execute immediately against resting liquidity.

Priority rules often include:

- best price first;
- for the same price, time priority;
- in some markets, size priority.

Key terms:

- **joining**: add size at the current best price;
- **improving**: post a better price than the current best quote;
- **inside market**: best bid and best ask;
- **spread**: best ask minus best bid;
- **midpoint**: average of best bid and best ask;
- **queue position**: order priority within a price level.
- **NBBO**: national best bid and offer; useful in fragmented US equity markets but not identical to a complete executable liquidity picture.

Liquidity is not merely displayed depth. Define liquidity as the ability to trade immediately, in size, at a fair price.

## Why Speed Matters

Speed matters in three situations:

- placing passive orders: get better queue position and spread/rebate opportunity;
- placing aggressive orders: reach available liquidity before it disappears;
- cancelling passive orders: avoid stale quotes and adverse selection.

Latency sources:

- trader-to-venue transmission;
- venue internal matching;
- venue-to-market-data transmission;
- cross-venue propagation;
- feed handling and order-book reconstruction;
- signal calculation;
- risk checks;
- broker and routing infrastructure;
- data bursts or microbursts.

Average latency is not enough. Tail latency and burst handling determine whether the system survives stressful periods.

## HFT Strategy Types

### Contractual Market Making

A contractual market maker receives retail or broker order flow and agrees to fill orders. It earns from spread, order-flow economics, and favorable selection, but must manage inventory and adverse price moves.

Risks:

- payment for order flow and broker routing economics can create agency questions;
- large customer orders create agency conflicts;
- inventory can accumulate in one direction;
- retail flow can become less benign during stress;
- speed is needed to reprice and hedge quickly.

Retail Liquidity Programs and related structures matter because retail flow is often less informed than institutional flow. Still, order flow can become one-sided, and market makers must exit or hedge inventory quickly.

### Noncontractual Market Making

The trader posts passive orders without a formal obligation. It earns spread/rebates but faces adverse selection and stale-order risk.

Necessary controls:

- queue priority;
- rapid cancellation;
- inventory limits;
- cross-asset hedging;
- venue-specific order management;
- kill switches.

### Arbitrage

Arbitrage exploits structural price relationships:

- index futures vs ETF vs basket;
- same asset across venues;
- related instruments with stale quotes;
- contractually received flow vs public market hedges.

It is rarely riskless in practice. One leg can execute while the other fails, moves, or loses liquidity.

### Fast Alpha

Fast alpha uses short-horizon predictive signals from price, volume, order book, flow, or short-term sentiment. It differs from arbitrage because the relationship is statistical rather than structural.

Validate like an alpha strategy, but include latency, queue, spread, cancellation, and market-impact effects.

## HFT Controversies

Analyze each controversy separately:

- **Unfairness**: speed is an advantage, but not all advantages are unfair. Ask whether the advantage uses public market data or privileged client information.
- **Front-running**: true front-running requires seeing or misusing non-public client orders before they reach the market. Seeing public order-book changes faster is different.
- **Cancellation rates**: high cancellation can reflect risk control, queue competition, stale quote avoidance, fragmented venues, and decimalization. It can also be manipulative in some cases; inspect intent and effect.
- **Phantom liquidity**: displayed liquidity may disappear under stress. Test whether liquidity is available immediately, at size, at fair prices.
- **Volatility**: compare intraday vs overnight volatility and control for macro events. Do not infer causality from HFT presence alone.
- **Flash crash**: consider market fragility, large directional orders, cross-instrument propagation, fragmented market structure, data delays, and HFT withdrawal.
- **Social value**: evaluate liquidity, spreads, price discovery, cost reduction, and market resilience. Avoid broad moral claims without evidence.

## Regulation

Reasonable controls include:

- pre-trade risk checks;
- limits on naked access;
- kill switches;
- better market data and surveillance technology;
- circuit breakers;
- clearer rules for intermarket routing and locked/crossed markets;
- flatter, less distorting rebate structures.

Be cautious with financial transaction taxes and minimum resting times. They can reduce liquidity, increase stale-order risk, create arbitrage opportunities against liquidity providers, and shift costs to end investors.

## Cases To Remember

- **Sergey Aleynikov**: brought HFT into public attention through code-theft allegations, not through proof that HFT itself is manipulation.
- **Knight Capital**: showed that low-latency automated trading can fail catastrophically through deployment or software controls, even when the strategy idea is not the issue.
- **Waddell & Reed flash-crash order**: a large futures sell program during fragile market conditions helped trigger cross-market stress; HFT withdrawal and market fragmentation amplified conditions but were not the sole root cause.
- **SPY volatility debate**: compare intraday and overnight volatility before blaming HFT. If volatility increased more outside HFT-active hours, the causal claim weakens.
