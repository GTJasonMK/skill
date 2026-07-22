# Validation, Risk, And Manager Audit

## Research Validation

Do not accept a strategy because a backtest looks smooth. Validate the claim being made.

Minimum validation:

- point-in-time data audit;
- universe and tradability audit;
- sample-in and sample-out split;
- parameter sensitivity;
- transaction-cost and turnover analysis;
- shorting/borrow/liquidity constraints;
- performance decomposition;
- delay and stale-signal tests;
- capacity and crowding checks;
- stress tests for volatility, correlation, spread, liquidity, and funding.

Overfitting signs:

- too many variables or conditions;
- strategy works only on a narrow sample;
- small parameter changes destroy performance;
- out-of-sample $R^2$ collapses;
- low-frequency strategy makes too few independent bets;
- results depend on data revisions, survivorship, or lookahead.

## Risk Endogeneity

Quant strategies can create the risks that later damage them.

Main endogenous risk channels:

- **Model risk**: wrong model, wrong objective, wrong assumptions, or implementation bug.
- **Structural relationship change**: correlations, spreads, factor payoffs, and relative relationships shift.
- **Exogenous shocks**: regulation, bans, war, credit events, macro crises, exchange outages.
- **Crowding and contagion**: similar managers liquidate similar positions simultaneously.
- **Liquidity spiral**: losses raise volatility and risk estimates, causing deleveraging, causing more losses.

When diagnosing a drawdown:

1. Attribute PnL to alpha, beta, factors, costs, liquidity, and errors.
2. Check whether signal performance changed or execution/cost assumptions changed.
3. Check crowding: are common longs being sold and common shorts being covered?
4. Check whether the model is reacting to its own footprint.
5. Check whether risk limits amplify liquidation pressure.

## Critiques Of Quant Trading

Common critiques and appropriate responses:

- "Trading is art, not science": reject the false binary. Good quant trading still uses judgment in design and supervision.
- "Quants underestimate risk": sometimes true, especially when risk is reduced to one precise number. But underestimating risk is not unique to quants.
- "Quants cause volatility": require evidence distinguishing quant activity from macro, leverage, credit, and structural market causes.
- "Quants cannot handle unusual events": partially true; models need monitoring and override procedures for out-of-domain states.
- "All quants are the same": usually false. Strategies differ by assets, data, alpha, horizon, bet structure, cost model, execution, and risk controls.
- "Only big firms can win": scale helps infrastructure but reduces flexibility and capacity; small firms may exploit narrower opportunities.
- "Data mining invalidates quant": data mining is a tool; overfitting and weak validation are the real problems.

## Manager Due Diligence

Evaluate a quant manager with two goals:

- understand the strategy, risk exposures, and return sources;
- judge whether the team is good enough and honest enough to manage capital.

Question areas:

- **Research**: idea source, testing process, sample split, overfitting controls, production criteria.
- **Data**: sources, cleaning, storage, identifier handling, revisions, point-in-time controls.
- **Alpha**: type, horizon, bet structure, universe, signal combination, decay.
- **Portfolio construction**: sizing, constraints, optimizer objective, cost/risk tradeoffs.
- **Execution**: order types, algorithms, broker/venue choices, slippage and impact measurement.
- **Risk**: model factors, limits, monitoring, stress tests, intervention rules.
- **Team**: relevant experience, judgment, humility, ability to convert research into production.
- **Integrity**: background checks, consistency of details, fiduciary mindset, willingness to answer non-proprietary process questions.
- **Portfolio fit**: alpha type, bet structure, and horizon diversification versus existing allocations.

Red flags:

- refuses all process questions as proprietary;
- cannot explain why a design choice was made;
- reports precise risk numbers without assumptions;
- has strong returns but no credible data or cost controls;
- changes story across meetings;
- performance pattern does not match described strategy;
- cannot explain drawdowns or disaster response.

## Disaster Handling

Good managers prepare for failure:

- monitor whether alpha still works;
- monitor data and execution errors;
- decompose losses quickly;
- reduce risk deliberately rather than panic;
- know when to stop trading;
- preserve research discipline after losses;
- avoid doubling down because a model says the signal is more extreme.
