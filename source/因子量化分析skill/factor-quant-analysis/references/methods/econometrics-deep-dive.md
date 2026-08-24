# Econometrics Deep Dive

## Contents

- [Factor-Mimicking Portfolios](#factor-mimicking-portfolios)
- [Single Sorting](#single-sorting)
- [Multi-Sorting](#multi-sorting)
- [Regression Tests](#regression-tests)
- [Factor Exposures and Factor Returns](#factor-exposures-and-factor-returns)
- [Anomaly Tests](#anomaly-tests)
- [Robust Standard Errors](#robust-standard-errors)
- [Model Comparison](#model-comparison)
- [Orthogonalization](#orthogonalization)
- [GMM](#gmm)
- [Method Selection Rules](#method-selection-rules)

## Factor-Mimicking Portfolios

A factor-mimicking portfolio is a tradable or diagnostic portfolio whose return proxies a factor return.

Ideal conditions:

1. Positive exposure to the target factor.
2. Zero exposure to other factors.
3. Minimum idiosyncratic risk among portfolios satisfying the exposure constraints.

Strict construction requires knowing factor exposures, which often require factor returns. Sorting avoids this circularity by using observable characteristics as noisy exposure proxies.

## Single Sorting

Use single sorting for first-pass evidence.

Procedure:

1. Define the eligible universe at each rebalance date.
2. Rank stocks by a lagged characteristic.
3. Split into quantiles, commonly 5 or 10 groups.
4. Compute next-period returns after an executable trade assumption.
5. Construct a high-minus-low or good-minus-bad spread.
6. Test the time-series mean of the spread.
7. Inspect monotonicity across all groups, not only the extreme spread.

Mean spread test:

```text
lambda_hat = mean(lambda_t)
t = lambda_hat / se(lambda_hat)
```

Monotonicity:

- Use group returns across quantiles.
- Spearman rank correlation is useful when the theory predicts monotone ordering.
- A significant high-minus-low spread with no monotonicity is weaker evidence.

Equal-weight versus value-weight:

- Equal-weight highlights small-stock effects and breadth.
- Value-weight is closer to scalable capital.
- Report both when the claim is broad A-share validity.

## Multi-Sorting

Use multi-sorting to control confounds.

Independent double sorting:

- Sort all stocks independently on variables A and B.
- Cross groups such as `5 x 5` or `2 x 3`.
- Use when both variables should be symmetrically represented, as in Fama-French-style factor construction.

Conditional double sorting:

- Sort first by a control variable.
- Within each control bucket, sort by the target variable.
- Average target-variable spreads across control buckets.
- Use when asking whether the target works after controlling for a known confounder such as size.

Check cell counts. Sparse cells create unstable spreads and artificial extremes.

Triple sorting:

- Use when two controls must be held while testing a third signal.
- Common in investment/profitability/size settings.
- Keep group counts coarse enough to avoid empty cells.

## Regression Tests

Time-series regression:

```text
R_it^e = alpha_i + beta_i' f_t + epsilon_it
```

Use when factor returns are observed or constructed. Output:

- `alpha_i`: model-unexplained average return.
- `beta_i`: factor exposure.
- `R^2`: time-series explanatory power.

Cross-sectional regression:

```text
R_{i,t+1} = a_t + b_t' z_it + epsilon_{i,t+1}
```

Use when characteristics or exposures explain return differences across assets at a point in time.

Fama-MacBeth:

1. Run cross-sectional regressions at each date.
2. Store `b_t`.
3. Average coefficients through time.
4. Compute standard errors from the coefficient time series, with HAC/Newey-West when autocorrelated.

Comparison:

| Method | Main use | Strength | Main risk |
| --- | --- | --- | --- |
| Sorting | Intuition and monotonicity | Transparent | Weak controls |
| Time-series regression | Alpha and exposure | Direct factor attribution | Omitted factors |
| Cross-sectional regression | Characteristic premium | Multiple controls | Cross-sectional dependence |
| Fama-MacBeth | Average premium through time | Handles changing cross-sections | Noisy betas and coefficient autocorrelation |

## Factor Exposures and Factor Returns

Two exposure approaches:

- Estimate beta from time-series returns when the factor return is known.
- Use company characteristics as conditional exposures when the characteristic is the object of pricing or prediction.

Instrumental-variable view:

- Characteristics can proxy hard-to-observe factor exposures.
- Measurement error in estimated beta can bias cross-sectional regression.
- Characteristics may predict returns even when estimated betas are noisy.

Two model types:

- Traded-factor models: factor returns are portfolio returns; time-series regression is natural.
- Non-traded-factor models: macro or latent factors require cross-sectional methods, GMM, or proxies.

## Anomaly Tests

An anomaly is model-relative. A significant alpha says the chosen model fails to explain the portfolio, not that the strategy is executable.

Time-series anomaly test:

```text
R_pt^e = alpha_p + beta_p' f_t + epsilon_pt
```

Cross-sectional anomaly test:

- Include the anomaly characteristic in Fama-MacBeth regressions with controls.
- Compare raw, neutralized, and controlled-sort results.
- Inspect whether the sign, magnitude, and t-stat remain stable.

Controls:

- Size, value, profitability, investment, momentum, beta, volatility, liquidity, industry, and known production signals.

## Robust Standard Errors

White standard errors:

- Correct for heteroskedasticity.
- Do not correct serial correlation by themselves.

Newey-West/HAC:

- Correct for heteroskedasticity and autocorrelation up to a chosen lag.
- Important for overlapping returns, monthly factor returns, rolling estimates, and Fama-MacBeth coefficient series.

Clustered or bootstrap inference:

- Use when dependence is by date, industry, firm, or block.
- Use block bootstrap when time dependence and non-normal returns are material.

Always report the inference method and lag/cluster choice.

## Model Comparison

GRS test:

- Tests whether all test-asset alphas are jointly zero under a factor model.
- Requires enough time observations relative to number of test assets and factors.
- Sensitive to test-asset choice and residual covariance estimation.

Mean-variance spanning:

- Tests whether adding a factor expands the mean-variance frontier.
- Useful when the question is about investment opportunity sets, not only pricing errors.

Alpha tests:

- Inspect individual alphas, average absolute alpha, and average alpha t-stat.
- A good model should leave small and economically unsystematic alphas.

Bayesian comparison:

- Makes priors about plausible alpha explicit.
- Useful when classical rejection is too mechanical or when model uncertainty matters.

Model-selection rule:

- Prefer the smallest model that has distinct economic meaning, reduces meaningful alphas, behaves out of sample, and avoids redundant factors.

## Orthogonalization

Residualization:

```text
x = a + B controls + residual
```

Use the residual as the part of `x` not linearly explained by controls.

Rules:

- State whether residualization is within date, time-series, or pooled.
- State the base set and order.
- Compare raw and residualized results.
- Do not use full-sample coefficients for live signals.

Geometry:

- OLS projects a vector onto the span of controls.
- The residual is orthogonal to that span.
- Sequential orthogonalization is order-dependent; different order can change factor meaning.

## GMM

Use GMM when the model is naturally written as moment conditions:

```text
E[g_t(theta)] = 0
g_T(theta) = (1/T) sum_t g_t(theta)
theta_hat = argmin g_T(theta)' W_T g_T(theta)
J = T * g_T(theta_hat)' W_T g_T(theta_hat)
```

Report:

- Moment conditions and economic meaning.
- Parameter vector.
- Weighting matrix.
- Identification logic.
- Over-identification/J-test interpretation.

Do not use GMM as a black box. It is powerful because it unifies estimation and testing, but weak moment design gives weak conclusions.

## Method Selection Rules

- Use sorting first for intuition.
- Use multi-sorting when a known confounder is central.
- Use Fama-MacBeth when estimating characteristic premia with many controls.
- Use time-series regression when testing alpha against known factor returns.
- Use GRS or alpha tests for model comparison across many test assets.
- Use GMM only when moment conditions are explicit.
- Use robust inference whenever returns overlap, residuals autocorrelate, or heteroskedasticity is likely.
