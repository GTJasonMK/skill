# Validation and Risk Review

## Contents

- [Evidence Hierarchy](#evidence-hierarchy)
- [P-Values and Multiple Testing](#p-values-and-multiple-testing)
- [Prior and Economic Plausibility](#prior-and-economic-plausibility)
- [Risk Compensation, Mispricing, or Data Snooping](#risk-compensation-mispricing-or-data-snooping)
- [Out-of-Sample Decay](#out-of-sample-decay)
- [Crowding and Capacity](#crowding-and-capacity)
- [Transaction Costs and Tradability](#transaction-costs-and-tradability)
- [Machine Learning Risks](#machine-learning-risks)
- [Review Checklist](#review-checklist)

## Evidence Hierarchy

Do not give all evidence equal weight.

Stronger evidence:

- Clear prior economic, behavioral, accounting, or microstructure mechanism.
- Point-in-time data with executable timing.
- Predeclared factor definition and test family.
- Robust IC, sorting, and regression evidence across periods and markets.
- Incremental value after known factors and existing signals.
- Net portfolio performance after costs, constraints, liquidity, and capacity.
- Publication or live/paper performance that does not collapse after exposure.

Weaker evidence:

- One attractive backtest after many unreported variants.
- A t-stat around 2 with no multiple-testing adjustment.
- Gross long-short returns in a market where shorting is constrained.
- Alpha against an incomplete or mismatched factor model.
- Machine-learning performance from random splits or repeated final-test tuning.

## P-Values and Multiple Testing

State what a p-value is and is not:

- It is the probability of observing data at least this extreme under the null model.
- It is not `P(null is true | data)`.
- It is sensitive to the tested model, sample, and search process.

For factor research, traditional `t ~= 2` thresholds are often too permissive because many signals, definitions, horizons, neutralizations, and periods are tried.

Use these controls:

- Define the tested family before looking at results.
- Keep failed, rejected, and abandoned variants in the experiment registry.
- Apply FDR, FDP, FWER, Bonferroni, Holm, Benjamini-Hochberg, White reality check, SPA, or block-bootstrap diagnostics when many strategies are searched.
- Separate exploratory research from confirmatory tests.
- Preserve an untouched final test period, or use nested walk-forward validation.

If the research log contains only promoted factors, multiple-testing corrections are not credible because the denominator is missing.

## Prior and Economic Plausibility

Require a prior before trusting a factor:

- Risk-based prior: the factor performs poorly in bad times or loads on systematic risks investors dislike.
- Behavioral prior: investors underreact, overreact, extrapolate, face limited attention, or prefer lottery-like payoffs.
- Institutional prior: constraints, mandates, benchmarking, leverage limits, short-sale restrictions, or accounting frictions prevent arbitrage.
- Fundamental prior: accounting decomposition or business economics explains why the signal captures quality, growth, investment discipline, or misvaluation.

Without a prior, a significant result is more likely to be a fragile empirical pattern.

## Risk Compensation, Mispricing, or Data Snooping

Use three diagnostic paths.

Risk compensation:

- Does the high-return side have higher covariance with bad states?
- Does beta or factor exposure predict returns better than the raw characteristic?
- Is the premium stronger when risk price should be high?
- Does the factor survive in other markets with similar risk logic?

Concrete tests:

- Compare risk characteristics of the long and short sides. A risk-compensation story is weak if the high-return side is clearly safer.
- Replace the raw characteristic with exposure to a factor-mimicking portfolio. If the characteristic predicts returns but the exposure does not, the evidence leans away from pure risk compensation.
- Split returns around macro announcement days, recessions, liquidity stress, or high-risk-price regimes. Risk compensation should often be stronger when risk is more expensive.
- Check whether similar state-risk logic works in related markets rather than only in the original sample.

Mispricing:

- Is there underreaction or overreaction around information events?
- Do announcement-window returns, SUE, PEAD, or revision patterns support the mechanism?
- Are limits to arbitrage, shorting constraints, sentiment, or investor attention related to anomaly strength?
- Does correction occur over a plausible horizon?

Concrete tests:

- Test whether anomaly returns concentrate around earnings announcements, forecast revisions, guidance changes, or other information events.
- Use SUE or future fundamental changes to check whether the signal predicts subsequent cash-flow news rather than only returns.
- Interact the signal with limited-attention proxies such as small size, low analyst coverage (分析师覆盖少), low media coverage (媒体报道少), low institutional ownership (机构投资者占比低), Friday announcements (星期五公告), or crowded announcement dates.
- Interact the signal with arbitrage-cost proxies such as idiosyncratic volatility, illiquidity, borrow constraints, negative news (负面新闻), or low institutional ownership.
- Track cumulative post-formation returns. Slow correction over months supports mispricing more than a one-day jump with no economic event.

Data snooping:

- Does the result survive a later sample, another market, or a truly new dataset?
- Does performance weaken after publication or industry adoption?
- Was the hypothesis known before the backtest?
- Were all tried variants logged?

Concrete tests:

- Use pre-sample, post-sample, and post-publication windows when the discovery date is known.
- Prefer truly new data sources or historical backfills that were not part of the original discovery process.
- Check whether the anomaly's correlation with other published anomalies also changes out of sample; data snooping can distort higher moments and correlations, not only average returns.
- Treat higher in-sample t-stat thresholds as helpful but not sufficient; a clean out-of-sample design is stronger.

Accounting-anomaly families:

| Family | Representative variables |
| --- | --- |
| Profitability | Gross profitability, operating profitability, ROA, ROE, asset turnover |
| Earnings quality | Accruals, earnings consistency, net operating assets, working-capital changes |
| Value | BM, cash-flow yield, EP, enterprise multiple, sales-to-price |
| Investment and growth | Asset growth, inventory growth, sales growth, capex growth, investment-to-assets |
| Financing | Debt issuance, net share issuance, composite equity issuance, leverage, external financing |
| Distress | O-Score, Z-Score, bankruptcy or financial-distress measures |
| Composite quality | F-Score, BM plus accruals, broad quality composites |

Use this taxonomy when auditing a factor library. If many variants from the same family were searched on the same accounting database, the effective multiple-testing burden is larger than the number of final promoted signals.

Many factors have mixed explanations. Report uncertainty instead of forcing one narrative.

## Out-of-Sample Decay

Reasons factor performance decays:

- Publication reveals the signal and capital arbitrages it away.
- Crowding increases entry price and reduces future returns.
- Transaction costs rise with turnover or market impact.
- Market structure changes.
- Original result was p-hacked or sample-specific.
- Data availability or accounting rules change.

Tests:

- Split pre-discovery, post-discovery, and post-publication periods.
- Use rolling or expanding walk-forward tests.
- Compare early versus late IC, spread, alpha, turnover, and cost drag.
- Check whether the short leg becomes hard to borrow or untradeable.
- Check whether factor valuation spread compresses.

Publication and adoption:

- A factor can decay because the publication reveals the signal and capital arbitrages the mispricing away.
- Separate sample-out decay from publication-informed trading when possible. If performance falls more after publication than in an ordinary later sample, adoption pressure is a plausible cause.
- Do not treat a factor as "false" only because it decays; risk-compensation factors can still have long drawdowns and mispricing factors can be arbitraged away.

Information timeliness:

- Financial statement factors can lose power when data are used too late.
- Test faster updates such as earnings announcements, preliminary earnings (业绩快报), earnings forecasts (业绩预告), or vendor snapshot timestamps when available.
- Compare performance in the first 30 days after an accounting update against later windows such as 30-120 days and after 120 days.
- If most alpha appears only soon after the update, the factor may be an information-timeliness (信息时效性) signal rather than a slow annual-rebalance factor.
- Faster data use must still respect point-in-time availability.

## Crowding and Capacity

Crowding can turn a good factor into a bad trade.

Crowding indicators:

- Factor valuation spread (估值价差) is extreme or compressed relative to history.
- Pairwise correlation (配对相关性) among factor portfolios rises.
- Factor volatility increases.
- Factor returns reverse sharply after strong inflows; this can be measured as factor reversal (因子反转), such as a long-horizon past factor return.
- Long leg and short leg overlap heavily with popular funds or indexes.
- Borrow cost, short interest (做空持仓量), or failed trades increase where data exists.

MSCI-style crowding proxies:

| Proxy | Construction idea | Interpretation |
| --- | --- | --- |
| Valuation spread / 估值价差 | `log(median valuation long leg / median valuation short leg)` such as BM spread | Expensive long leg or compressed spread can mean crowded entry price |
| Pairwise correlation / 配对相关性 | Correlation of residual returns inside long and short legs | Higher common movement suggests crowded similar positions |
| Factor volatility / 因子波动率 | Recent factor-return volatility, optionally relative to market volatility | Crowded factors can become more volatile |
| Factor reversal / 因子反转 | Long-horizon factor return such as past three-year factor return | Strong prior run-up can indicate crowding and reversal risk |
| Short interest or borrow pressure / 做空持仓量 | Short-interest difference, borrow cost, failed trades | Useful where short data exist; often limited in A shares |

Pairwise-correlation diagnostic:

- First remove systematic components from stock returns.
- Within each factor leg, correlate each stock's residual return with the average residual return of other stocks in the same leg.
- Average across names and legs, then standardize against history.
- Rising residual co-movement can warn that many investors hold similar idiosyncratic bets.

Capacity checks:

- Estimate turnover by rebalance date.
- Compare required trade dollars to ADV.
- Apply participation caps.
- Model market impact, not only commission.
- Stress costs by liquidity buckets and market regimes.

An IC-positive signal can be capacity-negative if it concentrates in illiquid names.

## Transaction Costs and Tradability

Gross returns are not implementation evidence.

Cost components:

- Commission and fees.
- Stamp tax or transaction tax.
- Bid-ask spread or effective spread (有效价差).
- Slippage and market impact or impact cost (冲击成本).
- Borrow cost and short rebate.
- Financing and leverage cost.
- Price-limit, suspension, and stale-price effects.

Tradability checks:

- Can the simulated buy occur if the stock is limit-up?
- Can the simulated sell occur if the stock is limit-down?
- Was the stock suspended or stale-priced?
- Is volume sufficient for the target participation rate (参与率) relative to ADV?
- Is the short leg borrowable?
- Does execution happen after signal computation?

Report net returns, turnover, cost sensitivity, and capacity before calling a strategy investable.

Cost-reduction experiments:

- Restrict the strategy to lower-cost and more liquid names.
- Compare bid-ask spread and effective spread when trade data supports it.
- Stress linear costs for commission, tax, and spread-like effects.
- Stress nonlinear impact costs when trade size is large relative to ADV.
- Lower rebalance frequency or add rank buffers to reduce unnecessary turnover.
- Add explicit bid-ask spread, price-impact, and participation-rate constraints.
- Compare signal decay against cost savings; slower trading is only useful if the signal survives.

Effective spread:

- Prefer effective or realized spread estimates when available, not only quoted bid-ask spread.
- For A shares, include stamp duty, commission, price-limit failed execution, suspension, and market-impact assumptions.

Empirical-Bayes shrinkage for many published factors:

```text
observed_mean_i = true_mean_i + noise_i
true_mean_i ~ cross_sectional_distribution
```

Use shrinkage when many factor means are selected from a publication or research library:

- Noisy high-return factors should be pulled strongly toward the cross-sectional average.
- Lower-standard-error factors receive less shrinkage.
- Treat the result as an expected-return haircut, not as proof that the factor is false.

## Machine Learning Risks

Machine learning does not remove the asset-pricing evidence problem.

Common failures:

- Random split leaks future regimes into training.
- Cross-validation folds share overlapping forward-return windows.
- Feature preprocessing uses full-sample information.
- Hyperparameters are tuned repeatedly on the final test.
- High-dimensional features produce impressive but unstable in-sample fit.
- Black-box predictions cannot be mapped to exposure, risk, or implementation constraints.

Rules:

- Use rolling or expanding windows.
- Fit preprocessing inside each training window.
- Use purging or embargo when labels overlap, including overlapping forward-return horizons.
- Compare against simple baselines: historical mean, linear model, simple factor composite, and existing production signal.
- Keep an untouched final test or nested walk-forward design; do not retune hyperparameters on the final test.
- Use out-of-sample `R^2`, IC, rank IC, turnover, cost, net return, and drawdown together.
- Inspect feature importance, partial dependence, exposure overlap, and regime stability.
- Check whether predictions can be converted into feasible weights after risk, cost, liquidity, and benchmark constraints.

## Review Checklist

Before accepting a factor, answer:

- What exact object is being claimed: factor premium, anomaly alpha, prediction signal, or implementable portfolio?
- Was every input observable before the decision timestamp?
- Is the universe reconstructed historically?
- Are financial statements point-in-time?
- Does the forward-return window start after execution?
- Does the signal survive IC, quantile, regression, and robustness tests appropriate to the claim?
- Is evidence adjusted for the number of tested factors and variants?
- Does the result survive reasonable neutralization and control variables?
- Is there a plausible risk, behavioral, institutional, or fundamental mechanism?
- Are gross and net results both reported?
- Are turnover, cost, capacity, price-limit, suspension, borrow, and liquidity constraints modeled?
- Does the portfolio have unintended sector, size, beta, volatility, or liquidity exposure?
- Is the optimizer stable to expected-return and covariance perturbations?
- Are failure cases and rejected variants recorded?
- Is there an experiment registry that includes failed factors, parameter sweeps, and abandoned variants?
- Is any final test period locked from repeated feature, parameter, or model-selection decisions?
- For machine-learning models, are preprocessing, feature selection, and neutralization fit only inside training windows?
- Do feature-importance or exposure diagnostics show the signal is not merely an industry, size, liquidity, beta, or volatility proxy?
- Is there a monitoring plan for live-vs-paper drift, signal health, data freshness, risk breaches, and execution slippage?

Final interpretation rules:

- Signal evidence is not portfolio evidence.
- Gross alpha is not net alpha.
- Regression alpha is not automatically investable alpha.
- Statistical significance is not economic value.
- A larger model is not automatically a better model.
- A strong backtest is still a workflow audit, not proof of future return.
