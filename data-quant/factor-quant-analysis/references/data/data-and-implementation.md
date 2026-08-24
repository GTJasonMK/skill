# Data and Implementation Guide

## Contents

- [A-Share Data Rules](#a-share-data-rules)
- [Financial Statement Timing](#financial-statement-timing)
- [Data Schemas](#data-schemas)
- [Universe and Tradability](#universe-and-tradability)
- [Factor Construction Defaults](#factor-construction-defaults)
- [Main Factor Families](#main-factor-families)
- [Anomaly Examples](#anomaly-examples)
- [Return Prediction Model](#return-prediction-model)
- [Barra-Style Risk Model](#barra-style-risk-model)
- [Portfolio Optimization](#portfolio-optimization)
- [Smart Beta](#smart-beta)
- [Factor Timing](#factor-timing)
- [Style Analysis and Risk Attribution](#style-analysis-and-risk-attribution)
- [Alternative Data and Asset Allocation](#alternative-data-and-asset-allocation)

## A-Share Data Rules

Use these defaults unless the project specifies stricter rules:

- Use adjusted returns that correctly account for splits, dividends, and corporate actions. In the book summaries, post-adjusted price data is the practical default for historical return computation.
- Treat long suspensions and reopenings explicitly. Do not let one mechanical return outlier dominate factor tests without marking or stress-testing the treatment.
- Decide whether suspension-day factor values are carried forward or set missing by factor type. Price/volume factors and fundamental factors can require different treatment.
- Require a minimum number of trading days before using price-derived factors such as beta, momentum, reversal, volatility, or turnover.
- For monthly factor research, rebalance at month-end and use next-period returns after an executable trade assumption.
- For sorted portfolios, inspect both equal-weight and value-weight returns. Equal-weight highlights small-stock effects; value-weight is closer to scalable capital.
- Treat one-word limit-up stocks as not buyable and one-word limit-down stocks as not sellable at the simulated execution price.
- Mark suspension periods and reopening returns explicitly. Stress-test whether excluding, delaying, or carrying suspended positions changes conclusions.
- Apply a minimum listing-age rule for newly listed stocks, especially for price/volume factors distorted by early trading limits and abnormal turnover.
- State the exchange board and price-limit regime when a universe spans main board, ChiNext, STAR Market, or Beijing Stock Exchange names.
- Distinguish total market cap, free-float market cap, and float market cap; academic tests, index construction, and trade sizing can require different choices.

## Financial Statement Timing

Do not use accounting data unless its availability is clear.

Key fields:

- Report period: the fiscal quarter or year the statement describes.
- Announcement or disclosure date: when investors could first observe the statement.
- Correction or restatement date: when revised information became observable.
- Vendor availability date: when the data source made the record available.
- Base report period: the latest report that should be visible at a given rebalance date.

Use point-in-time records:

- For a rebalance date, use only statements announced and available by that date.
- If corrections exist, use the version available at the rebalance date, not the latest revised value.
- For quarterly flow variables, compute single-quarter data from cumulative reports.
- For trailing-twelve-month values:

```text
TTM = current cumulative value
      + previous fiscal-year annual value
      - previous-year same-period cumulative value
```

For annual reports, TTM equals the annual value. For balance-sheet stock variables, use the latest available point-in-time balance rather than a TTM construction.

## Data Schemas

Use these minimum fields when designing CSVs, tables, or data contracts. Rename only when the project already has established conventions.

| Table | Required fields |
| --- | --- |
| Price panel | `date`, `asset_id`, `open`, `high`, `low`, `close`, `volume`, `amount`, `adj_factor`, `is_suspended`, `limit_up`, `limit_down` |
| Universe | `date`, `asset_id`, `in_universe`, `listed_date`, `is_st`, `is_delisting_warning`, `industry`, `market_cap`, `float_market_cap` |
| Fundamentals | `asset_id`, `report_period`, `announcement_date`, `available_date`, `statement_type` plus factor-specific accounting fields |
| Factor panel | `date`, `asset_id`, `factor_name`, `raw_value`, `clean_value`, `zscore`, `neutralized_value` |
| Forward returns | `signal_date`, `execution_date`, `asset_id`, `horizon`, `forward_return` |
| Portfolio weights | `date`, `asset_id`, `weight`, `benchmark_weight`, `active_weight` |
| Trades | `date`, `asset_id`, `prev_weight`, `target_weight`, `trade_weight`, `price`, `cost`, `participation` |

Recommended metadata fields:

- `data_timestamp` or `available_at` for any record whose availability can lag the economic date.
- `source` and `version` for vendor data, restatements, or derived datasets.
- `eligible_reason` or `exclusion_reason` for universe filters, so coverage changes are auditable.
- `raw_return`, `adjusted_return`, and `tradable_return` when suspension or price-limit handling can change results.

## Universe and Tradability

Define the eligible stock pool before factor ranking:

- Remove stocks that were not listed long enough for the factor horizon.
- Remove ST, delisting-warning, negative-net-asset, or otherwise ineligible stocks when the mandate requires it.
- Decide whether to exclude financial stocks for accounting-ratio comparability; document the choice.
- At rebalance or execution, flag or exclude suspended stocks, one-word limit-up stocks that cannot be bought, and one-word limit-down stocks that cannot be sold.
- If long-short portfolios are simulated, check borrowability and short-sale constraints. In A-shares, many academic long-short factors are diagnostic rather than directly executable.
- Use only contemporaneous liquidity, volume, price, and market-cap data for eligibility.

## Factor Construction Defaults

A conservative research setup:

1. Construct raw factor values from point-in-time data.
2. Remove invalid observations caused by impossible denominators, stale prices, or missing essential fields.
3. Winsorize within rebalance date, such as by percentile or MAD; do not use future cross-sections.
4. Standardize within date:

```text
z_{it} = (x_{it} - mean_t(x)) / std_t(x)
```

5. Neutralize industry and major style exposures only when the claim is incremental alpha rather than exposure harvesting.
6. Form 10 groups for single-variable sorting, `5 x 5` for dense double sorting, or `2 x 3` for Fama-French style factor construction.
7. Record the signal direction. If high values are bad, reverse the sign before combining with other signals.
8. Measure factor turnover and rank autocorrelation before portfolio use.

## Main Factor Families

Use these families as a research checklist:

| Family | Typical variable | Direction often tested | Notes |
| --- | --- | --- | --- |
| Market | Market excess return, beta | Higher beta should earn premium under CAPM | Often explains time-series variation better than cross-sectional returns. |
| Size | Market cap or log market cap | Smaller stocks may earn higher returns | Can proxy liquidity, distress, and retail participation. |
| Value | BM, EP, CF/P, dividend yield | Cheaper stocks may earn higher returns | BM and EP can behave differently; control profitability and size. |
| Momentum | Return from `t-12` to `t-1` | Past winners continue | Skip most recent month to reduce short-term reversal contamination. |
| Profitability/quality | ROE, ROA, gross profitability, operating profitability | More profitable firms may earn higher returns | Accounting definitions matter heavily. |
| Investment | Asset growth, capital expenditure, accruals | Conservative investment often earns more | Connect to q-theory or valuation identities. |
| Turnover/liquidity | Turnover, volume, Amihud illiquidity | Lower liquidity or turnover effects vary by market | In A-shares, trading-friction variables can be especially important. |
| Volatility/beta | Idiosyncratic volatility, residual volatility, beta | Low-volatility effects often appear | Check leverage constraints, lottery demand, and omitted risk. |
| Sentiment | Composite sentiment, IPO, turnover, closed-end discount | Sentiment can condition anomaly strength | Must avoid hindsight regime labels. |

## Anomaly Examples

Use anomaly examples as templates, not as guaranteed factors:

- F-Score: combine profitability, leverage/liquidity, and operating-efficiency signals to improve value investing screens.
- G-Score: identify growth firms with stronger fundamentals rather than treating all growth stocks as expensive.
- Expectation gap: compare market expectations with subsequent fundamentals or analyst revisions; ensure expectation data is time-stamped.
- Fundamental anchoring reversal: test whether prices overreact relative to a fundamental anchor and later reverse.
- Idiosyncratic volatility: estimate residual volatility after a factor model; low-IVOL anomalies often require limits-to-arbitrage and lottery-demand interpretation.

Each anomaly must pass controls for known factors, implementation costs, and data-snooping risk.

## Return Prediction Model

A prediction variable should satisfy six practical standards:

- Logic: it has an economic, accounting, behavioral, or microstructure reason.
- Persistence: it is not a one-period accident.
- Incrementality: it adds information beyond existing factors.
- Robustness: it survives alternative definitions, periods, and controls.
- Investability: it survives turnover, cost, liquidity, and capacity.
- Breadth: it works across enough stocks, time, or related markets to be useful.

IC definition:

```text
IC_t = corr_i(z_{it}, R_{i,t+1})
```

Use rank IC when monotonic order matters more than linear scale. Report mean IC, t-stat, positive-rate, decay by horizon, and subperiod stability.

Common return-model forms:

- Z-score composite: standardize signals and combine by fixed, IC-based, or optimized weights.
- Layered scoring: apply hard filters first, then rank inside the qualified set.
- Cross-sectional regression: estimate expected returns from characteristics and exposures.
- Machine learning: model nonlinear interactions, with walk-forward validation and a locked final test.

Treat expected return as only one component of alpha. The portfolio result also depends on breadth, transfer coefficient from signal to weights, and implementation cost.

## Barra-Style Risk Model

Use a risk model to explain covariance and control unintended exposures. A simplified form is:

```text
r_t = X_t f_t + u_t
Var(r_t) = X_t Cov(f_t) X_t' + Delta_t
```

where:

- `X_t` is the exposure matrix, including country, industry, and style exposures.
- `f_t` is factor return.
- `u_t` is idiosyncratic return.
- `Delta_t` is the specific-risk covariance, usually diagonal or structured.

Implementation points:

- Estimate factor returns with weighted least squares when large-cap stability matters.
- Use pure factor portfolios to interpret factor returns and isolate exposures.
- Adjust covariance estimates with shrinkage, volatility scaling, and specific-risk corrections.
- Validate realized versus forecast risk, residual correlations, and exposure reasonableness.

Barra-style risk factors are for risk and attribution. They are not automatically expected-return alpha signals.

## Portfolio Optimization

A standard mean-variance objective:

```text
max_w  w' mu - (lambda / 2) w' Sigma w - Cost(w - w_prev)
```

Use constraints before trusting weights:

- Full-investment, long-only or long-short, leverage, and cash rules.
- Single-name and industry concentration.
- Benchmark active weight and tracking error.
- Factor exposure neutrality or target exposure.
- Turnover, liquidity, ADV participation, and price-limit tradability.
- Minimum holding size and lot-size rules when relevant.

Compare objectives:

- Equal weight: robust baseline, ignores signal strength.
- Minimum variance: useful when expected returns are unreliable.
- Mean-variance: powerful but fragile to expected-return noise.
- Maximum diversification: emphasizes diversification ratio.
- Risk parity: equalizes risk contribution but can hide leverage and correlation assumptions.

Always run optimizer sensitivity checks. If small changes in `mu` or `Sigma` flip weights, reduce degrees of freedom or strengthen constraints.

## Smart Beta

Smart Beta converts factor ideas into transparent, rules-based index products.

Review five layers:

1. Factor definition: what exposure is intended.
2. Security selection: universe, eligibility, and ranking.
3. Weighting: equal, cap-weighted, factor-tilted, risk-weighted, or optimized.
4. Rebalancing: frequency, buffer, turnover control, and tradability.
5. Evaluation: factor exposure, tracking error, cost, capacity, drawdown, and benchmark fit.

When evaluating a Smart Beta fund, inspect holdings and realized exposures rather than relying on the product label.

## Factor Timing

Factor timing is difficult and should be held to a higher evidence bar than static factor allocation.

Common timing signals:

- Factor valuation: compare factor long and short legs by valuation spread.
- Factor momentum: allocate to factors with stronger recent returns or IC.
- Factor volatility: reduce exposure to unstable or high-volatility factors.
- Market sentiment: condition factor weights on sentiment states.
- Macro variables: connect factor premia to growth, inflation, rates, liquidity, or credit.

Guardrails:

- Define timing signals before testing.
- Use walk-forward allocation.
- Include turnover and tax/cost effects.
- Compare against static equal-weight or risk-weighted factor allocation.
- Avoid hindsight state labels.

## Style Analysis and Risk Attribution

Style analysis can be return-based or holding-based.

Return-based regression:

```text
R_{pt}^e = alpha_p + beta_p' f_t + epsilon_t
```

Holding-based exposure:

```text
Exposure_{p,k,t} = sum_i w_{i,t} X_{i,k,t}
```

Use both when possible:

- Return-based analysis captures realized co-movement but can be unstable.
- Holding-based analysis shows intended and unintended exposures but depends on exposure definitions.

Risk attribution decomposes portfolio volatility by exposure, covariance, and active weights. Do not treat independent risk contribution alone as sufficient when factors are correlated; use covariance-aware contribution.

## Alternative Data and Asset Allocation

Alternative data is useful only when it improves the full pipeline:

- Legal and compliance availability.
- Stable entity mapping.
- Point-in-time timestamping.
- Coverage and survivorship checks.
- Economic linkage to returns.
- Capacity and decay after adoption.

For asset-class factor allocation, use factor-mimicking portfolios to translate asset returns into common exposures such as growth, inflation, carry, momentum, value, and defensive factors. Tail correlation matters: diversification can disappear in stress regimes.
