# Model Components

## Alpha Model

An alpha model is a systematic way to choose what to buy, sell, short, avoid, or hold. It can forecast direction, magnitude, relative performance, or probability.

Classify alpha models:

- **Trend**: prices or fundamentals continue moving in the same direction.
- **Mean reversion**: deviations from a fair or relative value reverse.
- **Technical sentiment**: price, volume, flow, positioning, or market behavior reveals demand.
- **Value/yield**: cheap assets outperform expensive assets; use P/E, E/P, yields, spreads, carry.
- **Growth**: improving fundamentals, earnings, sales, or macro prospects predict returns.
- **Quality**: low leverage, stable income, good management, low fraud risk, high earnings quality.
- **Data-driven**: statistical or machine learning search for patterns without strong prior theory.
- **Hybrid**: combine signals linearly, conditionally, or through machine learning.

Always specify:

- prediction target: return direction, return magnitude, rank, spread, risk-adjusted return;
- horizon: microseconds, intraday, days, weeks, months, years;
- bet structure: absolute, relative, paired, grouped, factor-neutral;
- investment universe: geography, asset class, liquidity, borrowability, venue;
- run frequency and whether the model updates intraday or at scheduled intervals.

Do not treat signal mixing as portfolio construction. A mixed alpha combines forecasts before sizing; portfolio construction decides holdings after risk, cost, and constraints. For mixed alpha, state whether the combination is linear, conditional, Bayesian, machine-learned, or a separate sleeve/portfolio blend.

Common valuation and alpha details:

- value/yield can use P/E, E/P, dividend yield, bond yield, credit spread, carry, or roll yield;
- growth can use earnings growth, sales growth, macro growth, or PEG-style growth-adjusted valuation;
- quality can include leverage, income stability, earnings quality, management proxies, fraud risk, and market-implied deterioration such as CDS or implied volatility;
- data-driven models need stronger controls for false discovery, market regime change, and signal decay.

## Risk Model

A risk model identifies exposures that are not intended alpha. It should not eliminate all risk; it should remove or control risks that are not expected to be rewarded.

Common risk controls:

- hard limits on position, sector, factor, asset class, leverage, gross/net exposure;
- penalty functions that make more risk require disproportionately more expected return;
- volatility, cross-sectional dispersion, covariance, correlation, VaR, drawdown, liquidity, and factor exposure measures;
- theoretical factors: market, sector, size, style, interest rates, commodities, credit, currencies;
- empirical factors: PCA/statistical factors, residual risk clusters, latent common drivers.

Do not trust risk models blindly. Theoretical models can be incomplete; empirical models can find temporary or spurious factors; both can fail when market relationships change.

When risk determines sizing, distinguish volatility targeting, equal-risk sizing, VaR limits, Kelly-like sizing, drawdown caps, and liquidity-based liquidation limits. A precise risk metric is not proof of risk understanding.

## Transaction-Cost Model

A transaction-cost model estimates the cost of moving from current holdings to target holdings. It is not the same as an execution algorithm.

Decompose costs:

- commissions and exchange/regulatory fees;
- slippage between decision price and executed price;
- market impact caused by the order's own liquidity demand.

Model forms:

- constant cost: only reasonable for stable, small, similar trades;
- linear cost: simple but can overstate small trades and understate large trades;
- piecewise linear cost: common compromise between speed and realism;
- quadratic cost: captures rising market impact but is harder to estimate and compute.

Check whether the model varies by asset, time, volatility, spread, volume, participation rate, venue, and market stress.

Ask whether costs are used twice or not at all: the portfolio construction model may decide whether a trade is worthwhile, while the execution model minimizes realized cost after the target trade is chosen.

## Portfolio Construction

Portfolio construction converts forecasts into target positions.

Rule-based methods:

- equal position weighting: robust and simple, but ignores risk and signal strength;
- equal risk weighting: sizes positions inversely to volatility or risk, but can be misled by backward-looking low-volatility periods;
- alpha-weighted sizing: lets stronger signals get larger positions, but can overbet extreme or stale signals;
- decision-tree rules: combine alpha, cost, liquidity, and risk thresholds.

Optimization methods:

- mean-variance optimization: maximize expected return for risk, or risk-adjusted objective;
- constrained optimization: add position, sector, factor, leverage, turnover, shorting, liquidity, and cost constraints;
- Black-Litterman: combine investor views and confidence with historical or equilibrium estimates;
- Grinold-Kahn factor-portfolio optimization: optimize combinations of signal portfolios;
- resampled efficiency: use simulation to reduce sensitivity to estimation error;
- machine-learning optimization: search portfolio space, but treat as data mining unless validated carefully.

Optimizer outputs can be unintuitive. A long alpha signal can become a short final position because of constraints, risk neutrality, costs, or substitution by correlated assets.

For volatility forecasts, identify whether the model uses historical volatility, implied volatility, stochastic volatility, or GARCH-like volatility clustering. For correlations, check whether time-zone mismatches, rolling-window instability, and crisis correlation shifts are handled.

## Execution Model

Execution transforms target trades into actual orders. It must balance completion, cost, information leakage, urgency, and market conditions.

Execution concepts:

- mid-market price;
- VWAP and other benchmarks;
- implementation shortfall;
- aggressive vs passive orders;
- hidden orders, iceberg orders, market-on-close, stop-limit, FOK, AON, GTC, intermarket sweep orders;
- smart routing across exchanges and dark pools;
- direct market access, broker algorithms, FIX, co-location, and latency.

For large orders, evaluate slicing, footprint, adverse selection, fill probability, and market impact. For small orders, evaluate spread capture, queue priority, and whether speed matters enough to justify infrastructure cost.

Execution analysis should compare the benchmark to the strategy's objective. VWAP is useful for participation-style execution, implementation shortfall for decision-price slippage, and midpoint for spread-aware order placement. Avoid optimizing an execution benchmark that conflicts with the alpha horizon or urgency.

## Data

Data are the fuel of the black box. Evaluate:

- price data, trades, volume, quotes, order-book levels;
- fundamentals, accounting data, filings, macro data, corporate actions;
- identifiers, security masters, delistings, symbol changes;
- alternative data such as news sentiment, geolocation, satellite, web, or social data;
- frequency fit: macro quarterly data cannot support minute-level claims.

Data cleaning must address:

- missing values and imputation policy;
- bad ticks and outliers;
- corporate actions and split/dividend adjustments;
- timestamp errors and market close mismatches;
- survivorship bias, lookahead bias, restatements, announcement dates, and vendor availability;
- storage model: flat files, relational databases, or data cubes.

For accounting or fundamentals, use announcement, correction, and vendor-availability timestamps, not fiscal period end alone. For global markets, handle asynchronous closes explicitly.

## Research

Research should follow the scientific method: observe, theorize, test, try to falsify, and update.

Evaluate model quality with:

- cumulative PnL;
- average return and volatility;
- maximum drawdown;
- $R^2$ or other predictive power measures;
- monotonic buckets/quantiles;
- hit rate and profit time share;
- Sharpe, information ratio, Calmar, Omega, and other risk-adjusted ratios;
- correlation with existing strategies;
- delay tests;
- parameter sensitivity;
- out-of-sample tests;
- assumptions about costs, liquidity, and shorting.

Low $R^2$ can still matter in finance. Extremely high $R^2$ is suspicious unless leakage and hidden information are ruled out.

A good research report separates signal evidence from portfolio evidence. A signal can sort returns without surviving turnover, costs, borrow, liquidity, optimizer constraints, or execution delay.
