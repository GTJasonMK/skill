# Practice Deep Dive

Use when: converting factor research into return forecasts, Barra-style risk models, pure factor portfolios, constraints, costs, or optimizers.
Read after: `task-router.md` selects portfolio implementation, index enhancement, or production signal work.
Key decisions: expected-return vector, risk model, investable universe, objective function, constraints, and cost model.
Do not use for: basic factor validity tests or exact chapter table values.

## Contents

- [Return Model Workflow](#return-model-workflow)
- [Prediction Variables Versus Academic Factors](#prediction-variables-versus-academic-factors)
- [Six Criteria for Prediction Variables](#six-criteria-for-prediction-variables)
- [IC Interpretation](#ic-interpretation)
- [Investable Universe Optimization](#investable-universe-optimization)
- [Outlier Handling in Production Signals](#outlier-handling-in-production-signals)
- [Screening Versus Ranking](#screening-versus-ranking)
- [Parametric Alpha Forecast](#parametric-alpha-forecast)
- [Barra Risk Model Details](#barra-risk-model-details)
- [Country Factor and Industry Constraints](#country-factor-and-industry-constraints)
- [WLS Factor Return Estimation](#wls-factor-return-estimation)
- [Pure Factor Portfolios](#pure-factor-portfolios)
- [Covariance Adjustments](#covariance-adjustments)
- [Portfolio Optimization Consistency](#portfolio-optimization-consistency)
- [Objective Functions](#objective-functions)
- [Constraint Priority](#constraint-priority)
- [Transaction Cost Model](#transaction-cost-model)

## Return Model Workflow

A return model is not a bag of good indicators. It turns observable variables into a stock-level expected-return vector.

Workflow:

1. Define objective and benchmark: full-market enhancement, CSI 300 enhancement, CSI 500 enhancement, sector fund, market-neutral, or long-only active.
2. Define investable universe and remove low-liquidity, high-risk, and structurally negative-alpha names.
3. Construct candidate prediction variables from price-volume, accounting, revised signals, events, and alternative data.
4. Clean variables: point-in-time alignment, outlier treatment, standardization, neutralization, direction alignment.
5. Select variables using IC, rank IC, sorting, regression, sample splits, and sample-out tests.
6. Convert variables into expected returns, then pass them to risk, cost, and portfolio optimization.

Core warning:

- A variable can be statistically significant but unusable if it works only in tiny, illiquid, high-turnover, or short-constrained stocks.
- Research alpha is not production alpha until it survives costs, capacity, and tradability.

## Prediction Variables Versus Academic Factors

The same quantity can mean different things.

| Context | Object |
| --- | --- |
| Academic factor research | Variable used to construct factor or anomaly portfolio |
| Return model | Prediction variable for future stock return |
| Risk model | Style exposure or risk descriptor |
| Smart Beta index | Constituent-selection or weighting rule |
| Portfolio attribution | Explanation of realized return or risk |

Example:

- `BM` in an academic paper can build HML.
- `BM` in a return model can be a value score.
- `BM` in a risk model can be value exposure.
- `BM` in a Smart Beta index can determine inclusion or weight.

Hard rule:

- Always name whether the user is asking about a characteristic, exposure, factor return, expected return, or portfolio alpha.

## Six Criteria for Prediction Variables

The six criteria are a staged filter, not a checklist with equal weights.

Logic:

- First gate.
- Require risk compensation, mispricing, behavioral mechanism, market microstructure, or accounting rationale.
- Without logic, strong backtests are likely data mining.

Persistence:

- IC time series should not be dominated by one subperiod.
- Sorting spreads should not vanish outside the discovery period.
- Test publication, regime, market, and sub-universe stability.

Incremental information:

- A variable must add information beyond existing value, quality, size, liquidity, momentum, industry, and risk signals.
- Use correlations, conditional sorts, and multivariate Fama-MacBeth or panel regressions.

Robustness:

- Vary windows, lags, winsorization, grouping, neutralization, weighting, and rebalance frequency.
- A signal that dies under tiny parameter changes is not robust.

Investability:

- Check turnover, half-life, liquidity, market impact, borrow availability, price limits, suspensions, and capacity.
- Investability is part of signal validity, not a later portfolio detail.

Universality:

- Stronger evidence if the variable works across markets, asset classes, regimes, or reasonable implementations.
- Lack of universality does not kill an A-share-specific signal, but it raises prior skepticism.

## IC Interpretation

IC measures cross-sectional association between signal and next-period returns.

Use IC for:

- Ranking stock attractiveness at a date.
- Comparing prediction variables.
- Monitoring signal decay.
- Estimating expected return when combined with cross-sectional return dispersion.

Limits:

- High IC does not guarantee high PnL; PnL also depends on return dispersion and portfolio constraints.
- Stable IC can still be untradable if it comes from illiquid names.
- IC can be redundant if the signal overlaps existing variables.
- Pearson IC is sensitive to extreme returns; rank IC is often more robust.
- IC must use executable timing: signal known before return window begins.

Report IC with:

- Mean IC and t-statistic.
- Rank IC.
- ICIR.
- Horizon decay.
- Positive-rate.
- Subperiod and universe breakdown.
- Turnover and cost-adjusted spread.

## Investable Universe Optimization

Stock-pool optimization (股票池优化) is itself a return model.

Common exclusions:

| Exclusion | Reason |
| --- | --- |
| Low liquidity | High impact, low capacity, hard entry/exit |
| Long suspension risk | Trading right and liquidity risk |
| ST or delisting-risk stocks | Tail risk and mandate constraints |
| Negative net assets | Accounting distress and risk-warning risk |
| Newly listed stocks | High uncertainty, limited history, speculative trading |
| Structurally weak candidates | High turnover, high volatility, expensive-low-quality, persistent negative events |

Why it matters:

- Removing high-turnover/high-volatility stocks embeds low-speculation and low-volatility information.
- Removing expensive-low-quality stocks embeds value and quality information.
- Universe changes can alter factor return sources.

Implementation rule:

- Universe filters must be versioned, point-in-time, and applied before ranking.
- Report how much alpha comes from universe construction versus signal ranking when possible.

## Outlier Handling in Production Signals

Outlier treatment has two goals:

- Remove data errors and nonsensical ratios.
- Prevent extreme observations from dominating ranks or regressions.

Methods:

| Method | Good for | Risk |
| --- | --- | --- |
| Winsorization | Stable variables with rare extremes | Can suppress true extreme information |
| Mean-standard-deviation filter | Near-normal variables | Fragile for fat-tailed finance data |
| Median/MAD | Heavy-tailed variables | Can fail if abnormal observations are common |
| Log transform | Positive skewed liquidity/size variables | Not usable for zero/negative values without rules |

Variable-specific guidance:

- Ratio accounting variables often need winsorization or MAD due to small denominators.
- Momentum extremes can contain real information; do not blindly delete them.
- Liquidity variables often need log transform and robust scaling.
- Event variables may be extreme by design; treat by event logic, not generic clipping.

## Screening Versus Ranking

Screening:

- Uses hard conditions such as "low valuation and high profitability."
- Easy to explain.
- Sensitive to thresholds.
- Number of eligible stocks changes with market regimes.
- Multiple conditions can create overly concentrated portfolios.

Ranking:

- Converts variables to continuous scores.
- Stabilizes stock counts.
- Easier to combine many variables.
- Needs direction alignment, scaling, and weighting.

Recommended ranking workflow:

1. Align signal direction.
2. Winsorize or robustly transform.
3. Neutralize industry, size, beta, or other undesired exposures if needed.
4. Standardize or rank within date.
5. Combine variables within the same dimension first.
6. Combine dimensions after controlling variable-count imbalance.

## Parametric Alpha Forecast

Parametric forecasting converts score into expected alpha.

Useful approximation:

```text
alpha_hat_it ~= IC_t * sigma_alpha,t * z_i,t-1
```

Where:

- `IC_t`: signal predictive strength.
- `sigma_alpha,t`: cross-sectional dispersion of stock excess returns.
- `z_i,t-1`: standardized score.

Implications:

- The same signal is worth more when cross-sectional opportunity is large.
- Strong IC but low return dispersion can generate limited alpha.
- Extreme z-scores matter, but position constraints and outlier treatment cap their impact.

Use in portfolio construction:

- Estimate expected return vector.
- Shrink forecasts aggressively because expected returns are noisy.
- Align forecast horizon with rebalance and cost model.

## Barra Risk Model Details

Barra-style risk models (风险模型) estimate covariance ex ante:

```text
Sigma = beta Sigma_f beta' + Sigma_epsilon
```

Differences from academic pricing models:

| Dimension | Academic pricing model | Barra-style risk model |
| --- | --- | --- |
| Goal | Explain expected-return differences | Forecast volatility and covariance |
| Factor choice | Economic meaning and risk premia | Return covariance explanation |
| Factor returns | Sorting or regression | Cross-sectional regression each period |
| Exposures | Betas or characteristics | Standardized descriptors and industry dummies |
| Good model | Low alpha, priced factors | Accurate risk forecasts |

Important point:

- A Barra factor need not have positive long-term premium.
- Industry factors are important even when they are not "priced" because they explain common return variation.
- Do not judge a production risk model by academic pricing-model rules. Its job is covariance prediction, exposure control, and attribution.

## Country Factor and Industry Constraints

Country factor (国家因子):

- All stocks have exposure 1.
- It captures broad A-share market movement.
- Its factor return is close to value-weighted market excess return.

Industry dummies create collinearity:

```text
sum industry dummies = country exposure
```

Barra resolves this through constraints such as weighted industry factor returns summing to zero.

Interpretation:

- Country factor: market-wide risk.
- Industry factors: industry returns relative to market.
- Style factors: value, size, momentum, volatility, liquidity, quality, and other style risks after market/industry controls.
- In Chinese practice, map these directly to 国家因子, 行业因子, and 风格因子.

In attribution:

- Market risk maps to country factor.
- Industry risk maps to industry deviations.
- Style risk maps to descriptor exposures.

## WLS Factor Return Estimation

Barra estimates factor returns with weighted least squares (WLS).

Reason:

- Different stocks have different specific risk.
- Larger stocks often have lower noise and higher portfolio relevance.
- WLS can make factor returns closer to investable market risk.

Typical intuition:

```text
higher weight for larger, more liquid, lower-specific-risk names
```

Implications:

- Barra factor returns are not equal-weight average spreads.
- They are influenced more by large-cap risk structure.
- A WLS factor return can differ materially from a sorted academic factor return.
- The residual is specific return (特质性收益率), and its forecast volatility is specific or idiosyncratic risk (特质性风险).

Audit questions:

- What weights are used?
- Are weights lagged and point-in-time?
- Are industry constraints applied?
- Are style exposures standardized and winsorized before regression?

## Pure Factor Portfolios

Pure factor portfolios (纯因子组合) isolate one factor exposure.

For a style factor:

1. Exposure to target style factor equals 1.
2. Exposure to other style factors equals 0.
3. Exposure to country and industry factors equals 0.

Use cases:

- Estimate factor returns.
- Build risk covariance.
- Attribute portfolio risk.
- Diagnose unintended style exposures.

Not ideal for:

- Direct long-only investment products.
- Simple investor communication.
- Capacity estimates without further tradability constraints.

Contrast:

| Portfolio | Strength | Weakness |
| --- | --- | --- |
| Sorting factor | Transparent and investable proxy | Mixed exposures |
| Pure factor | Clean exposure | Model-dependent and less directly investable |

## Covariance Adjustments

Raw historical covariance is unstable.

Problems:

- Limited sample length.
- Time-varying volatility.
- Optimization amplifies small estimation errors.

Barra-style adjustments:

Feature-factor adjustment (特征因子调整):

- Focuses on factor covariance matrix.
- Identifies eigenvector-like factor combinations whose historical variance is likely underestimated.
- Corrects the "low-risk direction" that optimizers would overuse.

Bayesian shrinkage for specific risk (贝叶斯收缩):

- Uses individual stock historical specific volatility as sample information.
- Uses similar-stock group average as prior information.
- Shrinks more when a stock's estimate is noisy or far from peer prior.

Bias statistic (偏差统计量):

- Use it to check whether ex ante risk forecasts are systematically too high or too low.
- A common diagnostic standardizes realized residual return by predicted risk; if the standard deviation is far from 1, the risk forecast is biased.
- Calibrate shrinkage to reduce forecast bias, not to make the optimizer's backtest look smoother.

Practical rule:

- Risk estimates should be stable and conservative.
- Do not let an optimizer exploit covariance noise.

## Portfolio Optimization Consistency

Optimization must align return model, risk model, cost model, and constraints.

Model mismatch (错位):

- Return model may predict alpha from an improved momentum signal.
- Risk model may only include traditional momentum exposure.
- Optimizer then treats the improved-momentum residual as low-risk free alpha.

Consequences:

- Hidden style concentration.
- Ex ante risk understated.
- Drawdown larger than predicted.
- Portfolio appears risk-controlled but actually takes model-specific risk.

Fixes:

- Add missing risk descriptor if it is a persistent source of return and risk.
- Penalize unexplained alpha concentration.
- Cap exposure to forecast components not represented in the risk model.
- Stress test with alternate risk models.

## Objective Functions

Common objective functions:

| Objective | Use when | Hidden assumption |
| --- | --- | --- |
| Mean-variance | Expected returns and risk model are credible | Alpha forecasts have useful scale |
| Minimum variance | Goal is risk reduction | Expected returns roughly equal |
| Maximum diversification | Need diversification benefit | Sharpe ratios are similar |
| Risk parity | Need balanced risk contribution | Assets have comparable reward per risk |
| Equal weight | Need robust simplicity | Assets are broadly similar |

Book-style formulas:

Mean-variance optimization:

```text
maximize_w  w' mu - (zeta / 2) * w' Sigma w
unconstrained solution: w_mvo = (zeta Sigma)^(-1) mu
budget-normalized intuition: w_mvo proportional to Sigma^(-1) mu
```

Minimum variance:

```text
w_mv proportional to Sigma^(-1) 1
```

Maximum diversification:

```text
maximize_w  (sum_i w_i sigma_i) / sqrt(w' Sigma w)
```

Risk parity:

```text
RC_i = w_i * (Sigma w)_i / sqrt(w' Sigma w)
choose w so RC_i are equal or close to equal
```

Inverse volatility:

```text
w_i proportional to 1 / sigma_i
```

Equivalence conditions:

| Method | Equivalent to mean-variance when |
| --- | --- |
| Minimum variance | Expected returns are equal across assets |
| Maximum diversification | Asset Sharpe ratios are equal |
| Risk parity | Asset Sharpe ratios and pairwise correlations are equal |
| Equal weight | Sharpe ratios, pairwise correlations, and volatilities are equal |

Stock selection:

- Mean-variance is common for index enhancement and active quant.
- Minimum variance or low-volatility objectives are used for defensive products.

Asset allocation:

- Risk parity, max diversification, and inverse-volatility are more common because asset-level return forecasts are very noisy.
- Risk parity (风险平价) is not assumption-free: it works best when assets have comparable reward per unit risk and correlations are not dominated by one crisis regime.

Rule:

- Choosing an objective function means choosing assumptions. State them.
- If expected returns, volatilities, or correlations are informative, use them; if they are mostly noise, a simpler objective can be more robust out of sample.

## Constraint Priority

Too many constraints can make optimization infeasible.

Prioritize constraints:

| Priority | Examples | Treatment |
| --- | --- | --- |
| Legal/contract hard constraints | Banned stocks, no shorting, position bounds | Must satisfy |
| Risk hard constraints | Single-name cap, industry cap, tracking error cap | Usually must satisfy |
| Investment preference | Style exposure range, turnover target | Soft constraint or penalty |
| Cost control | Transaction cost, impact, turnover | Penalty or soft cap |

Common constraint forms:

```text
long-only:              w_i >= 0
budget:                 1' w = 1
single-name bounds:      L_i <= w_i <= U_i
industry neutrality:     H w = h
style exposure cap:      lower_k <= sum_i w_i beta_i,k <= upper_k
active exposure cap:     lower_k <= sum_i (w_i - w_i^B) beta_i,k <= upper_k
turnover cap:            sum_i |w_i - w_i^0| <= turnover_limit
tracking error cap:      sqrt((w - w_B)' Sigma (w - w_B)) <= TE_limit
```

When infeasible:

- Do not relax all constraints blindly.
- Relax lower-priority soft constraints first.
- Preserve benchmark, legal, mandate, and core risk constraints.
- Report which constraints bind.

Index enhancement default:

- Tracking error, industry deviation, banned list, and liquidity constraints usually outrank a desired style tilt.

## Transaction Cost Model

Transaction cost model (交易成本模型) converts turnover into expected loss.

Linear costs:

- Commission.
- Stamp duty.
- Transfer fees.
- Bid-ask spread approximations.

Nonlinear costs:

- Market impact.
- Crowding impact.
- Cost rising with trade size relative to volume.

Turnover constraint (换手率约束) versus cost penalty:

| Method | Strength | Weakness |
| --- | --- | --- |
| Turnover cap | Simple and stable | Ignores stock-level liquidity and buy/sell asymmetry |
| Cost penalty | Stock-specific and direction-aware | Needs estimated parameters |

Penalty form:

```text
maximize_w  f(mu, Sigma, theta, w) - gamma_TC * TC(w)
```

Linear and quadratic examples:

```text
TC_linear(w)    = sum_i c_i * |w_i - w_i^0|
TC_quadratic(w) = sum_i c_i * |w_i - w_i^0| + sum_i q_i * (w_i - w_i^0)^2
```

Use:

- Linear cost captures fees, taxes, and spread-like costs.
- Quadratic cost captures market impact that rises with trade size.
- Set `gamma_TC` high enough that optimizer does not harvest tiny forecast differences through excessive turnover.

Production practice:

- Use both a turnover guardrail and stock-level cost penalty.
- Align cost model with execution horizon.
- Penalize trades in suspended-risk, price-limit-risk, and low-liquidity names.
- Report gross alpha, estimated cost, and net alpha separately.
- In real portfolios, a turnover cap controls total churn while the cost penalty redirects trades away from expensive names; they solve related but different problems.
