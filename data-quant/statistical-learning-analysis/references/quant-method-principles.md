# Quant Method Principles

Use this reference when the user asks for the idea behind a quant method, why a diagnostic is needed, or how to interpret a research result. Keep the explanation tied to investable timing, point-in-time data, costs, liquidity, and risk.

## Return and Risk Diagnostics

| Method | Core idea | What the result means | Main failure mode |
| --- | --- | --- | --- |
| Return compounding | Convert period returns into path wealth and annualized return. | Shows whether gains survive compounding and losses. | Arithmetic averages can overstate path performance. |
| Volatility | Measure dispersion of returns around their mean. | Higher volatility means wider outcome range, not automatically higher loss. | Volatility is backward-looking and regime-dependent. |
| Sharpe ratio | Compare excess return with volatility. | A higher Sharpe is better only if returns are executable and risk is measured correctly. | Serial correlation, smoothing, leverage, and selection bias inflate it. |
| Drawdown | Measure peak-to-trough wealth loss. | Communicates path pain and capital impairment. | Sample-period dependent; one calm backtest can hide future drawdowns. |
| VaR / Expected Shortfall | Estimate tail loss quantiles and average tail loss. | VaR marks a loss threshold; ES estimates loss severity beyond it. | Tail estimates are noisy and do not cover unseen stress regimes. |

## Factor Research

| Method | Core idea | What the result means | Main failure mode |
| --- | --- | --- | --- |
| IC / Rank IC | Correlate current signal values with future cross-sectional returns. | Measures directional predictive ordering before portfolio construction. | Timing errors, overlapping horizons, and many tried factors inflate significance. |
| Quantile portfolios | Sort assets by signal and compare future returns across buckets. | Shows monotonicity and high-minus-low spread. | Ignores constraints, liquidity, borrow, sector exposure, and costs unless added. |
| Factor decay | Recompute IC across horizons. | Shows whether the signal is short-lived or persistent. | Overlapping forward returns can create misleading significance. |
| Turnover / rank stability | Compare selected names or ranks across rebalances. | High turnover means higher cost and lower capacity. | Stable ranks can still be non-predictive. |
| Signal overlap / redundancy | Compare many signals by cross-sectional correlation, rank correlation, and selected-name overlap. | Shows whether a multi-alpha set adds independent breadth or repeats the same trade. | Low pairwise correlation does not rule out shared sector, style, liquidity, or crowding exposure. |
| Incremental alpha diagnostics | Residualize a candidate and future returns against existing signals/exposures, then test residual IC and model contribution. | Shows whether a new signal adds information beyond the base alpha library. | The base set, residualization order, timing, and repeated testing can determine the result. |
| Neutralization | Regress signal on known exposures within each date and use residuals. | Tests whether the signal remains after removing sector, size, beta, or style exposure. | Over-neutralization can remove the intended economic effect. |

## Asset Pricing and Exposure

| Method | Core idea | What the result means | Main failure mode |
| --- | --- | --- | --- |
| Factor exposure regression | Regress asset or strategy excess returns on factor returns. | Alpha is unexplained average return; betas are systematic exposures. | Alpha is not automatically tradable skill; omitted factors and costs matter. |
| Newey-West / HAC inference | Adjust standard errors for autocorrelation and heteroskedasticity. | More defensible t-stats for time-series return regressions. | HAC does not fix leakage, bad benchmarks, or misspecified factors. |
| Fama-MacBeth | Run cross-sectional regressions by date, then average premia over time. | Estimates average characteristic or exposure premia. | Inference is weak with short samples, correlated errors, or overlapping returns. |
| Cross-sectional regression | Explain one-date or pooled returns using characteristics/exposures. | Useful first-pass signal and risk-premium diagnostic. | Pooled IID t-stats usually overstate evidence in panels. |

## Portfolio Construction

| Method | Core idea | What the result means | Main failure mode |
| --- | --- | --- | --- |
| Long/short signal portfolio | Translate a ranking signal into investable-style weights. | Tests whether predictive ordering survives sizing and rebalance rules. | Gross returns without costs, borrow, and liquidity are not implementation evidence. |
| Portfolio backtest | Apply beginning-period weights to realized asset returns. | Measures path performance under explicit weighting assumptions. | Wrong timing convention creates look-ahead or execution bias. |
| Constraint check | Test weights against leverage, concentration, category, and turnover limits. | Shows whether a backtest would have been admissible. | Checking constraints after selecting winners hides invalid trials. |
| Mean-variance optimization | Use expected returns and covariance to maximize return per risk. | Converts forecasts into weights. | Small input errors can cause extreme, unstable allocations. |
| Optimizer sensitivity | Perturb expected returns/covariance and observe weight changes. | Large flips or concentration changes indicate fragile optimization. | A stable optimizer can still be wrong if inputs are biased. |
| Risk contribution | Decompose portfolio volatility into component contributions. | Identifies which positions or hedges dominate risk. | Contributions depend heavily on covariance estimates and leverage convention. |
| Portfolio construction gate | Convert backtest, constraint, exposure, risk, optimizer, cost, and capacity diagnostics into a pass/review/fail portfolio decision. | Shows whether a candidate portfolio is admissible enough for paper trading or trading review. | Passing construction checks is not production readiness; execution controls, owners, and monitoring still need go-live review. |

## Costs, Capacity, and Execution

| Method | Core idea | What the result means | Main failure mode |
| --- | --- | --- | --- |
| Transaction cost analysis | Convert turnover into commission, spread, slippage, borrow, and impact drag. | Net returns show whether alpha survives implementation assumptions. | Generic cost bps can hide asset-specific liquidity and spread regimes. |
| Capacity analysis | Compare required trades with ADV and participation caps. | Estimates the NAV scale where liquidity constraints bind. | ADV-based capacity is only a proxy and must be calibrated with execution data. |
| Execution slippage | Compare fill price with decision or benchmark price using side-aware bps. | Positive slippage is realized implementation shortfall. | Decision price, partial fills, and order timing must be defined precisely. |
| Execution timing audit | Compare signal, rebalance, execution, and forward-return window timestamps. | Shows whether IC, sorted portfolios, regressions, or backtests use returns that start after an executable trade. | Same-day date-only timestamps, same-close prices, or return windows starting before execution can create hidden look-ahead even when data is point-in-time. |
| Tradability audit | Compare each simulated trade row with market-state, volume, price-limit, shortability, and borrow evidence. | Shows whether a strategy could plausibly enter or exit the assets used by IC, sorted portfolios, backtests, or portfolio construction. | Halted/suspended assets, zero volume, limit locks, missing borrow, and stale prices can make otherwise time-safe backtests untradable. |
| Performance attribution | Decompose portfolio return by asset, sector, country, or factor. | Explains where performance came from. | Attribution is not causality and must reconcile to total return. |

## Validation and Robustness

| Method | Core idea | What the result means | Main failure mode |
| --- | --- | --- | --- |
| Point-in-time audit | Compare data availability, source date, period end, universe, revision, signal, rebalance, and execution timestamps against the decision timestamp. | Shows whether a signal panel is time-safe enough to interpret IC, regressions, sorted portfolios, or backtests. | Passing timestamp checks does not prove the vendor vintage is correct; missing availability evidence is still an evidence gap. |
| Walk-forward validation | Select parameters on a training window and evaluate on the next window. | Tests whether the research process works out of sample. | Reusing test results for new tuning turns it into another validation set. |
| Experiment registry audit | Check whether tested variants, failed trials, selected candidates, final-test evidence, and data/code versions are recorded. | Shows whether the evidence base for multiple testing, reality checks, and alpha gates is complete enough to review. | If failed or abandoned trials are absent, every later significance or gate report has an incomplete denominator. |
| Bootstrap reality check | Compare the best observed strategy against a bootstrap null over all tried variants. | Helps judge whether the selected winner is likely data snooping. | The tested strategy family must include failed and unpublished variants. |
| Multiple-testing correction | Adjust discoveries for the number of tested hypotheses. | Reduces false positives across many signals or models. | It cannot correct for untracked experiments or changed hypotheses. |
| Alpha research gate | Convert completed alpha diagnostics into a pass/review/fail promotion decision with blockers and evidence gaps. | Shows whether a candidate signal has enough research evidence to move to portfolio construction or paper trading. | If thresholds and required diagnostics are chosen after seeing results, the gate becomes another overfit report. |
| Regime robustness | Compare performance across market states. | Reveals dependence on bull/bear, volatility, liquidity, or macro regimes. | Regime labels can be hindsight narratives if not known at the time. |
| Risk forecast calibration | Compare realized returns, standardized residuals, and VaR breaches with forecasts. | Tests whether forecast risk scale is too high, too low, or unstable. | A calibrated volatility forecast can still miss tail shape and correlation breaks. |
| Model risk register audit | Check whether live or high-risk models have owners, risk tiers, validation, approval, review dates, monitoring, rollback controls, and version evidence. | Shows whether governance evidence is complete enough for go-live, scaling, or periodic model review. | A clean register does not validate alpha quality, and a missing register makes sign-off, escalation, and accountability weak. |
| Live-vs-paper monitoring | Compare live returns with frozen paper or backtest expectations. | Identifies implementation drift after deployment. | Different timestamps, costs, universes, or return definitions make the comparison invalid. |
| Signal health monitoring | Track coverage, IC, rank IC, spread, and turnover over recent live windows. | Separates signal decay from portfolio sizing and execution effects. | A healthy signal can still lose money after costs, and noisy live windows can overstate decay. |
| Go-live gate | Convert readiness evidence into pass, fail, warning, waiver, and blocker status. | Forces unresolved risks to be visible before capital deployment. | A checklist without evidence, owners, and stop conditions becomes procedural theater. |
| Order exception monitoring | Count rejected, cancelled, open, expired, and partially filled orders. | Shows whether the strategy can actually access intended trades. | Looking only at completed fills hides unavailable liquidity or broker/risk rejects. |
| Data freshness monitoring | Compare feed timestamps and quality stats with predeclared tolerances. | Stops stale or incomplete data from driving signals and orders. | Fresh data can still be wrong, restated, or not point-in-time. |
| Limit breach monitoring | Compare daily risk/ops metrics with directional thresholds and severities. | Turns risk appetite into observable stop/go decisions. | Limits without owner, escalation, and enforcement are only descriptive reports. |
| Strategy action decision | Map triggered monitoring rules to maintain, review, reduce, pause, or retire. | Converts diagnostics into explicit capital and trading actions. | If thresholds are chosen after seeing outcomes, the action policy becomes hindsight fitting. |
| Checklist template generation | Start from a structured set of go-live, monitoring, or retirement checks. | Makes required evidence and ownership visible before sign-off. | Templates do not replace strategy-specific thresholds, evidence, and mandate approval. |
| Diagnostics aggregation | Combine multiple JSON diagnostic reports into one review index. | Helps reviewers see overall decision, key metrics, blockers, and top findings in one place. | Aggregation can hide nuance; source diagnostics remain authoritative. |
| Committee review pack | Convert diagnostics and gate outputs into a role-aware review package. | Helps PM, research, risk, trading, data, and operations reviewers see decisions, evidence, gaps, and actions. | A polished pack can hide weak source evidence if reviewers do not inspect the underlying diagnostics. |

## Interpretation Rules

- Separate signal evidence from portfolio evidence: IC and quantile spreads are not the same as executable PnL.
- Separate gross performance from net performance: costs, spread, borrow, financing, and impact must be explicit.
- Separate statistical significance from economic value: tiny effects can be statistically real but untradable.
- Separate exposure from alpha: factor regressions explain common risks but do not prove skill.
- Treat every optimizer result as a hypothesis about inputs, constraints, and stability, not as a final answer.
- Treat every backtest as a workflow audit: universe, point-in-time data, timing, costs, constraints, and selection process matter as much as the metric.
