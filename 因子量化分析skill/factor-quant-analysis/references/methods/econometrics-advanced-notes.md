# Econometrics Advanced Notes

Use when: Shanken correction, EIV, instrumental variables, GRS/spanning geometry, Bayesian model comparison, orthogonalization geometry, or GMM math matters.
Read after: `method-map.md` or `task-router.md` indicates a standard method explanation is not enough.
Key decisions: estimated object, generated-beta uncertainty, alpha geometry, spanning interpretation, prior choice, and moment conditions.
Do not use for: first-pass factor screening or implementation-only portfolio work.

## Contents

- [Cross-Sectional Regression Details](#cross-sectional-regression-details)
- [Shanken Correction](#shanken-correction)
- [Time-Series Versus Cross-Sectional Regression](#time-series-versus-cross-sectional-regression)
- [Errors-in-Variables and Instrumental Variables](#errors-in-variables-and-instrumental-variables)
- [Characteristics as Exposures](#characteristics-as-exposures)
- [GRS Geometry](#grs-geometry)
- [Mean-Variance Spanning](#mean-variance-spanning)
- [GRS Versus Spanning](#grs-versus-spanning)
- [Bayesian Model Comparison](#bayesian-model-comparison)
- [Orthogonalization Geometry](#orthogonalization-geometry)
- [GMM Framework](#gmm-framework)
- [GMM Effectiveness and Warnings](#gmm-effectiveness-and-warnings)

## Cross-Sectional Regression Details

Use cross-sectional regression when factor returns are unavailable or when the question is whether estimated exposures explain average returns.

Two-step cross-sectional setup:

```text
Step 1: R_it^e = a_i + beta_i' f_t + epsilon_it
Step 2: E_T[R_i^e] = gamma + beta_hat_i' lambda + alpha_i
```

Important distinction:

- `a_i` in step 1 is a time-series intercept; if `f_t` is not a traded factor return, it is not a pricing alpha.
- `alpha_i` in step 2 is the pricing error relative to the cross-sectional model.

OLS estimate:

```text
lambda_hat = (B'B)^(-1) B' E_T[R^e]
alpha_hat = E_T[R^e] - B lambda_hat
```

GLS estimate:

```text
lambda_GLS = (B' Sigma^(-1) B)^(-1) B' Sigma^(-1) E_T[R^e]
```

Use GLS when cross-sectional pricing errors are materially correlated and residual covariance can be estimated with enough stability. Do not use GLS mechanically when `N` is large and the covariance estimate is weak.

## Shanken Correction

Shanken correction is needed because beta estimates are generated regressors.

Problem:

- The second-stage regression uses `beta_hat`, not the true `beta`.
- Treating `beta_hat` as known understates uncertainty.
- The correction inflates the covariance of estimated factor premia and alphas using a term related to factor Sharpe ratio.

Book-style expression:

```text
cov(lambda_hat)
= (1/T) [
  (B'B)^(-1) B' Sigma B (B'B)^(-1)
  * (1 + lambda' Sigma_f^(-1) lambda)
  + Sigma_f
]
```

Interpretation:

- Higher factor Sharpe ratios make beta-estimation error more consequential.
- Longer time-series windows reduce the problem but do not remove it.
- Portfolio test assets reduce idiosyncratic beta error, but they can hide stock-level characteristics.

When answering:

- Mention Shanken correction in two-pass beta-premium tests.
- Mention it is less central when firm characteristics are used directly as exposures.
- Do not present uncorrected two-pass t-statistics as final pricing evidence.

## Time-Series Versus Cross-Sectional Regression

Time-series regression:

- Requires factor return time series.
- Estimates each asset's beta and alpha relative to traded factor returns.
- The factor premium is the mean of the factor return series.
- Good for testing whether a portfolio has alpha after known traded factors.

Cross-sectional regression:

- Can use non-traded factors or characteristics.
- Estimates factor premia by minimizing pricing errors across assets.
- Produces implicit pure-factor portfolios.
- Good for asking whether exposures or characteristics are priced.

Pure factor portfolio:

```text
Omega = (B'B)^(-1) B'
Omega B = I
```

The `k`-th row of `Omega` defines a portfolio with exposure 1 to factor `k` and 0 to other factors. This is why cross-sectional regression can be interpreted as constructing pure factor portfolios (纯因子组合).

Conflict diagnostic:

- If sorted factor returns are positive but cross-sectional slope is negative, the factor construction may contain confounding exposures.
- Investigate exposure correlations, universe filters, weighting, and omitted characteristics.

## Errors-in-Variables and Instrumental Variables

Errors-in-variables (EIV) appears when estimated betas proxy true exposures.

Traditional mitigation:

- Use portfolios as test assets so individual beta noise diversifies away.
- Downside: portfolio formation is dimensionality reduction; it can hide stock-level information.

Instrumental variable approach:

```text
R_t^e = beta zeta_t + alpha_t
zeta_hat_IV = (beta_tilde' beta_hat)^(-1) beta_tilde' R_t^e
```

Jegadeesh et al.-style idea:

- Estimate `beta_hat` and instrumental beta `beta_tilde` from non-overlapping historical samples.
- Example: split past daily returns by odd and even months.
- Use one split for beta, the other split as instrument.
- Non-overlap reduces correlation between beta-estimation errors.

Use IV when:

- The research claim is about beta exposures rather than raw characteristics.
- Betas are estimated from noisy stock-level time series.
- The user asks why portfolio test assets may lose information.

Do not use IV as a ritual. It solves one EIV problem but does not fix omitted variables, stale data, or weak economic mechanisms.

## Characteristics as Exposures

Some modern empirical asset-pricing work uses firm characteristics directly as factor exposures.

Examples:

- Size exposure: standardized log market cap.
- Value exposure: standardized BM or EP.
- Profitability exposure: ROE, ROA, gross profitability.
- Investment exposure: asset growth or investment-to-assets.

Why:

- Sorting variables are often better proxies for the economic characteristic than noisy time-series betas.
- For size and value, including both time-series betas and company characteristics can make beta premia disappear while characteristics remain significant.

Common mistake:

- Calling a characteristic "factor return" before estimating a premium or building a factor-mimicking portfolio.

Answering rule:

- If the object is a prediction variable, call it a characteristic.
- If it enters a risk model, call it exposure.
- If a portfolio return is built from it, call that factor return.
- If it explains expected return differences after controls, discuss priced factor evidence.

## GRS Geometry

GRS tests whether all test-asset alphas are jointly zero under a traded-factor model.

Statistic:

```text
GRS = ((T - N - K) / N)
      * (1 + mean(f)' Sigma_f^(-1) mean(f))^(-1)
      * alpha' Sigma_e^(-1) alpha
```

Under standard assumptions:

```text
GRS ~ F(N, T - N - K)
```

Geometric interpretation (几何意义):

- Assume a risk-free asset exists and investors can borrow/lend at the risk-free rate.
- The relevant object is the tangency portfolio or maximum Sharpe ratio.
- GRS asks whether adding `N` test assets to `K` factors significantly increases the maximum attainable Sharpe ratio.

Sharpe-ratio form:

```text
GRS proportional to
[(sqrt(1 + theta_(N+K)^2) / sqrt(1 + theta_K^2))^2 - 1]
```

Use GRS when:

- Factors are traded or represented by return series.
- Test assets are portfolios or anomaly returns.
- `T > N + K` and residual covariance is estimable.

Do not use GRS when:

- Test assets are too many relative to time periods.
- Factor returns are not traded or not observed.
- The goal is to identify which single asset causes rejection; GRS is a joint test.

## Mean-Variance Spanning

Mean-variance spanning (均值-方差张成检验) asks whether adding test assets improves the minimum-variance frontier spanned by existing factors. Its geometry (几何意义) is broader than GRS because it compares the minimum-variance frontier rather than only the tangency portfolio.

Setup:

```text
R_t = [R_1t', R_2t']'
R_1t: K benchmark factors/assets
R_2t: N test assets
```

Regression:

```text
R_2t = alpha + beta R_1t + epsilon_t
delta = 1_N - beta 1_K
```

Null hypothesis:

```text
H0: alpha = 0 and delta = 0
```

Interpretation:

- `alpha = 0`: test assets do not add mean-return improvement.
- `delta = 0`: test assets do not alter the global minimum-variance portfolio in a relevant way.
- If both hold, the benchmark assets span the efficient frontier; test assets are redundant.

Large-sample tests:

```text
LR = T [ln(1+s1) + ln(1+s2)]
W  = T (s1+s2)
LM = T [s1/(1+s1) + s2/(1+s2)]
```

Use spanning tests when the question is frontier improvement rather than only alpha under a risk-free tangency framework.

## GRS Versus Spanning

GRS:

- Assumes a risk-free asset and unrestricted borrowing/lending.
- Focuses on whether the tangency portfolio's Sharpe ratio improves.
- Tests joint alpha in excess-return space.
- More common in factor-model comparison.

Mean-variance spanning:

- Does not require a risk-free asset.
- Compares broader minimum-variance frontiers.
- Requires both `alpha=0` and `delta=0`.
- More general but harder to explain and implement.

Practical answer:

- Use GRS for "does this factor model explain these test assets?"
- Use spanning for "do these assets expand the attainable mean-variance opportunity set?"
- If sample size is small relative to assets, prefer fewer test portfolios or report finite-sample caution.

## Bayesian Model Comparison

Bayesian model comparison asks which factor model is more probable given data and prior assumptions.

Barillas-Shanken-style setup:

```text
R_t^e = alpha + beta f_t + epsilon_t
H0: alpha = 0
H1: alpha ~ N(0, tau Sigma)
```

Model posterior odds:

```text
P(M_i | D) / P(M_j | D)
= [P(M_i) / P(M_j)] * [P(D | M_i) / P(D | M_j)]
```

The second term is the Bayes factor or marginal likelihood ratio.

Usefulness:

- Forces explicit priors.
- Can penalize model complexity.
- Avoids judging models only by in-sample alpha reduction.

Caution:

- Results can be sensitive to prior choices.
- Chib et al.-style critique: marginal likelihood comparison is only coherent when priors and parameter spaces are comparable across models.
- Do not present Bayesian ranking as mechanically superior to GRS or alpha tests.

Answering rule:

- Use Bayesian methods as one lens for model comparison.
- Report prior assumptions, marginal likelihood logic, and sensitivity.
- Preserve economic interpretation and parsimony as separate criteria.

## Orthogonalization Geometry

Orthogonalization is regression residualization in geometry.

Simple regression:

```text
b_hat = <x, y> / <x, x>
```

OLS residuals are orthogonal to regressors:

```text
X' epsilon_hat = 0
```

Gram-Schmidt form:

```text
z_k = x_k - sum_j<k [<z_j, x_k> / <z_j, z_j>] z_j
```

The coefficient of the last residualized variable is:

```text
b_k = <z_k, y> / <z_k, z_k>
```

Implications:

- Orthogonalization is order-dependent.
- A factor highly explained by earlier factors has a small residual vector and unstable coefficient.
- Orthogonalization changes economic meaning; residual value is not the same as raw value.

For factor work:

- State the base factor set.
- State the residualization order.
- Explain whether the goal is interpretation, risk control, or signal de-correlation.
- Prefer neutralization against known risk exposures when the goal is implementation risk control.

## GMM Framework

Generalized method of moments (GMM) starts from moment conditions:

```text
E[f(x_t, b0)] = 0
```

Asset-pricing examples:

```text
E[m(b0) R_f^g - 1] = 0
E[m(b0) R^e] = 0
```

Sample moment:

```text
g_T(b) = (1/T) sum_t f(x_t, b)
```

Estimator:

```text
b_hat = argmin_b g_T(b)' W g_T(b)
```

Over-identification:

- Number of moments `n` exceeds number of parameters `p`.
- Not all sample moments can be forced to zero.
- The model is judged by whether remaining pricing errors are large relative to their covariance.

Core variance idea:

```text
var(g_T(b0)) = S / T
S = sum_j E[f(x_t,b0) f(x_(t-j),b0)']
```

The matrix `S` is a long-run covariance or spectral-density matrix. HAC/Newey-West estimators are practical ways to estimate it when moments are autocorrelated.

J-test:

```text
T g_T(b_hat)' S^(-1) g_T(b_hat) ~ chi-square(n-p)
```

Use GMM when:

- The model naturally gives moment conditions.
- The user asks about CCAPM, stochastic discount factors, Euler equations, or unified asset-pricing tests.
- You can state moments, parameters, weighting matrix, and test assets.

## GMM Effectiveness and Warnings

Efficient GMM:

```text
W = S^(-1)
```

Two-stage workflow:

1. Use `W = I` to estimate initial parameters.
2. Estimate `S` from first-stage residual moments.
3. Use `W = S^(-1)` to estimate efficient parameters.
4. Optionally iterate until stable.

Interpretation:

- `S^(-1)` gives less weight to noisy moments and more weight to precise moments.
- Statistical efficiency is conditional on the chosen moments.
- Adding many assets changes the moments and can change the estimate.

Book warning:

- GMM should not become a black box.
- Choosing moments is an economic decision, not only a statistical one.
- In asset pricing, use assets or portfolios that matter for the model's claim.
- A formally efficient estimate based on irrelevant moments can be economically meaningless.

Review checklist:

- Are the moment conditions explicit?
- Are the test assets economically motivated?
- Is the weighting matrix reported?
- Is the number of moments reasonable relative to sample length?
- Is the over-identification test interpreted as model diagnostic, not proof?
- Are HAC choices, lags, and small-sample limitations disclosed?
