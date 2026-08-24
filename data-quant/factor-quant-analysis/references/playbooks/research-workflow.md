# Factor Research Workflow

## Contents

- [Source Map](#source-map)
- [Unifying View](#unifying-view)
- [Research Question Types](#research-question-types)
- [Point-in-Time Data and Universe](#point-in-time-data-and-universe)
- [Signal and Factor Construction](#signal-and-factor-construction)
- [Empirical Testing Loop](#empirical-testing-loop)
- [Multi-Factor Model Work](#multi-factor-model-work)
- [Explanation and Economic Mechanism](#explanation-and-economic-mechanism)
- [From Research to Portfolio](#from-research-to-portfolio)
- [Report Structure](#report-structure)

## Source Map

Use the local project summaries as the domain base:

- Chapter 1: unified view of factor investing, `beta'lambda` versus `alpha`, cross-sectional versus time-series perspectives, academic and industry roles.
- Chapter 2: portfolio sorting, multi-sorting, time-series regression, cross-sectional regression, Fama-MacBeth, anomaly testing, GRS, spanning, alpha tests, orthogonalization, and GMM.
- Chapter 3: A-share data cleaning, financial statement timing, stock-pool construction, factor construction, and mainstream factor empirical settings.
- Chapter 4: mainstream multi-factor models, A-share Fama-MacBeth evidence, GRS/alpha model comparison, and parsimony.
- Chapter 5: anomaly research examples such as F-Score, G-Score, expectation gaps, fundamental anchoring reversal, and idiosyncratic volatility.
- Chapter 6: p-hacking, factor zoo, behavioral explanations, investor sentiment, risk compensation versus mispricing versus data snooping, sample-out decay, costs, fundamental analysis, and machine learning.
- Chapter 7: return models, Barra-style risk models, portfolio optimization, Smart Beta, factor timing, style analysis, risk attribution, alternative data, and asset-class factor allocation.

## Unifying View

Start from the asset-pricing decomposition:

```text
E[R_i] - R_f = beta_i' lambda + alpha_i
```

Interpret it before choosing methods:

- `beta_i' lambda` is the component explained by systematic factor exposures and factor risk premia.
- `alpha_i` is the part not explained by the chosen pricing model; it may be true skill, omitted risk, mispricing, data error, or overfit.
- Cross-sectional work explains why different assets have different expected returns.
- Time-series work explains why one asset or portfolio return moves over time and how much alpha remains after known factor returns.

Keep four objects separate:

- Characteristic or prediction variable `z_it`: observed company or market feature at time `t`.
- Factor exposure `beta_it`: sensitivity to a factor or characteristic loading.
- Factor return/premium `lambda_t` or `f_t`: return earned by the factor in a period.
- Portfolio return/alpha: realized result after weights, costs, constraints, and execution timing.

## Research Question Types

Use the question type to route the workflow:

| Question | Main object | Primary methods | Main failure mode |
| --- | --- | --- | --- |
| Is a factor priced? | Factor exposure and premium | Fama-MacBeth, cross-sectional regression, model comparison | Treating a characteristic sort as a risk premium proof |
| Is this an anomaly? | Unexplained return/alpha | Sorted portfolios, time-series alpha, Fama-MacBeth with controls | Omitted factors or p-hacking |
| Does this signal predict returns? | Prediction variable | IC/rank IC, quantile returns, horizon decay, incremental alpha | Ignoring turnover and costs |
| Does a model explain returns? | Multi-factor model | GRS, alpha tests, spanning, average absolute alpha | Adding factors without economic meaning |
| Can this become a portfolio? | Expected returns and weights | Risk model, optimizer, constraints, costs, backtest | Confusing gross signal evidence with investable alpha |
| Can this be a Smart Beta product? | Transparent factor index | Exposure design, rebalancing, capacity, tracking error | Factor label not matching holdings |
| Can factors be timed? | Factor allocation weights | Valuation, momentum, volatility, sentiment, macro signals | Timing model overfit and unstable regimes |
| What explains a portfolio? | Return or holding exposures | Style analysis, factor regression, risk attribution | Attribution interpreted as causality |

## Point-in-Time Data and Universe

Define the data contract before any test:

1. Use a rebalance calendar and state whether decisions occur at close, next open, next close, or another executable price.
2. Define forward returns so the return window starts after execution, not at the signal timestamp.
3. Build historical universe membership at each rebalance date. Avoid current constituents for historical tests.
4. Apply eligibility filters using only information observable by the rebalance date: listing age, ST or delisting flags, net asset status, suspension, price limits, liquidity, and borrowability if shorting.
5. Treat accounting data as point-in-time. Use announcement, correction, vendor availability, and report period fields; never join only by fiscal period end.
6. Preserve delisting, suspension, limit-up/limit-down, and stale-price evidence. Do not silently turn non-trading into zero return.

For A-share work, also check the detailed rules in [data-and-implementation.md](../data/data-and-implementation.md).

## Signal and Factor Construction

For each candidate factor:

1. State economic direction: high value, high profitability, low investment, low turnover, high momentum, low idiosyncratic volatility, or another explicit direction.
2. Compute the raw signal from point-in-time data.
3. Handle invalid values before ranking: negative denominators, missing financials, extreme accounting ratios, newly listed stocks, suspensions, and financial-sector comparability.
4. Winsorize or robustly cap within date, not across the full sample.
5. Standardize within date if the next method assumes comparable scales.
6. Neutralize only when the claim requires it. Common neutralizers are industry, size, market beta, liquidity, volatility, and known style exposures.
7. Keep a record of raw, cleaned, standardized, and neutralized signals so later analysis can identify where performance was created or lost.

For factor-mimicking portfolios:

- Use sorting rules that are fixed before seeing results.
- State independent versus conditional sorting.
- State equal-weight versus value-weight and why it matches the research claim.
- For long-short factors, verify whether the short leg is feasible in the target market.

## Empirical Testing Loop

Run tests in escalating order:

1. Coverage and distribution: missing rate, cross-sectional dispersion, extreme values, rank stability, and overlap with known factors.
2. IC and rank IC: measure whether the signal orders future cross-sectional returns.
3. Quantile portfolios: inspect monotonicity and high-minus-low spread.
4. Multi-sorting: control for size, industry, value, or the suspected confounder.
5. Fama-MacBeth: estimate average cross-sectional premium while controlling multiple characteristics.
6. Time-series regression: test whether a strategy or sorted portfolio alpha survives known factor returns.
7. Robustness: subperiods, market regimes, neutralization choices, weighting schemes, horizons, and costs.

Do not promote a signal from step 2 or 3 directly to production. IC and sorting are research diagnostics; portfolio evidence requires weights, risk, costs, constraints, and timing.

## Multi-Factor Model Work

When building or comparing models:

1. Start from a parsimonious benchmark: CAPM, Fama-French style factors, q-factor model, or the local production risk model.
2. Add factors only when they have a distinct economic or behavioral interpretation and incremental empirical value.
3. Compare models by their ability to reduce test-asset alphas, not only by in-sample fit.
4. Use GRS or alpha tests when testing whether many test-asset alphas are jointly zero.
5. Use mean-variance spanning when asking whether new factors expand the attainable mean-variance frontier.
6. Preserve parsimony: a larger model can overfit, become unstable, and lose interpretability even if some statistics improve.

## Explanation and Economic Mechanism

Classify evidence into three possible explanations:

- Risk compensation: the factor loads on bad states or systematic risks, and higher returns compensate investors for bearing them.
- Mispricing: behavioral bias, investor sentiment, limited attention, limited arbitrage, or institutional frictions cause temporary price errors.
- Data snooping: the factor survives in-sample because many variables, definitions, periods, or model variants were searched.

Do not force one explanation. Report what the evidence supports and what remains unresolved.

## From Research to Portfolio

Before using a signal in a portfolio:

1. Turn the signal into an expected-return model, not just a rank.
2. Estimate or import a risk model: country, industry, style exposures, factor covariance, and specific risk.
3. Define constraints: long-only or long-short, leverage, turnover, single-name, industry, style, benchmark, liquidity, and tracking error.
4. Model costs: commission, tax, bid-ask spread, market impact, borrow, financing, and price-limit/suspension effects.
5. Run optimizer sensitivity checks because expected returns are noisy.
6. Reconcile attribution: realized return should decompose into intended factor exposure, unintended exposure, idiosyncratic contribution, costs, and residual.

## Report Structure

Use this report order for factor research memos:

1. Research question and hypothesis.
2. Universe, timing, and point-in-time data rules.
3. Signal definition and construction choices.
4. Primary evidence: IC, quantile returns, regressions, model tests, or backtest.
5. Robustness: subperiods, alternative definitions, controls, neutralization, costs, and capacity.
6. Interpretation: risk compensation, mispricing, or data-snooping evidence.
7. Implementation: portfolio role, constraints, risk exposures, expected turnover, cost drag, and monitoring.
8. Limitations and rejected variants.
