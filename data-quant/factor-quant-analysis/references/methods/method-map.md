# Factor Method Map

## Contents

- [Choosing a Method](#choosing-a-method)
- [Portfolio Sorting](#portfolio-sorting)
- [Multi-Sorting](#multi-sorting)
- [Time-Series Regression](#time-series-regression)
- [Cross-Sectional and Fama-MacBeth Regression](#cross-sectional-and-fama-macbeth-regression)
- [Anomaly Testing](#anomaly-testing)
- [Multi-Factor Model Comparison](#multi-factor-model-comparison)
- [Orthogonalization and Neutralization](#orthogonalization-and-neutralization)
- [GMM](#gmm)
- [Mainstream Multi-Factor Models](#mainstream-multi-factor-models)
- [Machine Learning and PCA](#machine-learning-and-pca)

## Choosing a Method

| Claim | Preferred method | Evidence to report | Watch |
| --- | --- | --- | --- |
| Signal predicts next-period returns | IC/rank IC, quantile portfolios, horizon decay | Mean IC, t-stat, positive rate, spread, monotonicity | Timing, turnover, costs |
| Factor earns a characteristic premium | Fama-MacBeth or cross-sectional regression | Mean coefficient/premium, HAC t-stat, controls | Errors-in-variables, correlated errors |
| Portfolio has alpha beyond known factors | Time-series factor regression | Alpha, beta, Newey-West t-stat, R-squared | Omitted factors, cost-free returns |
| Candidate anomaly survives controls | Multi-sorting, Fama-MacBeth, time-series alpha | Controlled spread, alpha, coefficient stability | Confounds and p-hacking |
| New model explains test assets | GRS, alpha tests, spanning | Joint alpha test, average alpha, alpha t-stats | Sample size and factor count |
| New factor adds independent information | Orthogonalization, incremental regression, spanning | Residual IC/alpha, delta R-squared, alpha reduction | Order dependence |
| Many factors were searched | Multiple testing, FDR, reality checks | Adjusted p-values, experiment registry | Missing failed trials |

## Portfolio Sorting

Use sorting as the first intuitive test of a factor or anomaly.

Basic procedure:

1. At each rebalance date, rank eligible stocks by the lagged factor value.
2. Split into quantiles, commonly 5 or 10 groups.
3. Compute next-period returns for each group using equal-weight and, when appropriate, value-weight.
4. Report high-minus-low or good-minus-bad spread:

```text
R_{t+1}^{H-L} = R_{t+1}^{H} - R_{t+1}^{L}
```

5. Test the time-series mean of the spread with robust standard errors when returns overlap or autocorrelate.

Sorting is good for monotonicity and intuition. It is weak for controlling many variables at once.

## Multi-Sorting

Use multi-sorting when a target factor may be contaminated by another characteristic.

Independent sorting:

- Sort all stocks independently on factor A and factor B.
- Cross the groups, such as `5 x 5` or Fama-French `2 x 3`.
- Use when both dimensions should be symmetrically represented.

Conditional sorting:

- Sort first by the control variable, then sort by the target factor inside each control bucket.
- Average target-factor spreads across control buckets.
- Use when the goal is to test whether the target factor works after controlling a known confounder such as size.

Check cell counts. Sparse cross-cells make spreads unstable and can create artificial extremes.

## Time-Series Regression

Use time-series regression when factor returns are known and the question is whether an asset, portfolio, fund, or strategy has alpha beyond those factors.

Canonical form:

```text
R_{it}^e = alpha_i + beta_i' f_t + epsilon_{it}
```

Report:

- `alpha_i`: average return not explained by factor returns.
- `beta_i`: exposure to each factor return.
- `R^2`: how much time-series variation is explained.
- Newey-West/HAC t-stats when residuals are autocorrelated or heteroskedastic.

Do not call `alpha_i` investable alpha until costs, capacity, timing, constraints, and omitted factor exposure are checked.

## Cross-Sectional and Fama-MacBeth Regression

Use cross-sectional regression when the question is whether characteristics or exposures explain differences in future returns across assets.

One-period cross-sectional form:

```text
R_{i,t+1} = a_t + b_t' z_{it} + epsilon_{i,t+1}
```

Fama-MacBeth procedure:

1. Run the cross-sectional regression at each date `t`.
2. Store the coefficient vector `b_t`.
3. Estimate the average premium:

```text
bar_b = (1 / T) * sum_t b_t
```

4. Compute standard errors from the time series of coefficients; use Newey-West/HAC when coefficients are autocorrelated, especially with overlapping returns.

Use company characteristics directly when the research design treats them as conditional factor exposures. For market beta, estimate beta from a rolling time-series window, such as 252 trading days, before using it in cross-sectional regressions.

Common pitfalls:

- Pooled panel OLS with IID t-stats usually overstates evidence.
- Estimated betas introduce measurement error.
- Controls can change the sign and meaning of a factor premium.

## Anomaly Testing

For an anomaly, ask whether abnormal returns survive after known factor models and controls.

Time-series anomaly test:

```text
R_{pt}^e = alpha_p + beta_p' f_t + epsilon_{pt}
```

where `p` is a sorted long-short portfolio or test portfolio. A significant alpha means the chosen model does not explain the anomaly, not that the anomaly is guaranteed investable.

Cross-sectional anomaly test:

- Include the anomaly characteristic with known controls in Fama-MacBeth.
- Check whether its coefficient remains stable and significant.
- Compare raw and neutralized versions.

Econometric issues:

- Use White or HAC/Newey-West standard errors for heteroskedasticity and autocorrelation.
- Use block bootstrap or clustered inference when date or industry dependence is strong.
- Avoid interpreting p-values without considering the full tested family.

## Multi-Factor Model Comparison

Use multiple tests because no single statistic decides model quality.

GRS test:

```text
GRS = ((T - N - K) / N)
      * (alpha_hat' Sigma_hat^{-1} alpha_hat)
      / (1 + mu_f_hat' Omega_f_hat^{-1} mu_f_hat)
```

Under the standard assumptions, `GRS ~ F(N, T - N - K)`. Use it to test whether all `N` test-asset alphas are jointly zero under a `K`-factor model. Require `T > N + K`; otherwise the test is not well-conditioned.

Alpha tests:

- Inspect individual alphas and alpha t-stats.
- Summarize average absolute alpha and average absolute alpha t-stat.
- A better model should leave smaller, less systematic alphas across economically meaningful test assets.

Mean-variance spanning:

- Ask whether adding a candidate factor or test asset expands the mean-variance frontier.
- Use when the research question is about investment opportunity sets rather than only pricing errors.

Bayesian comparison:

- Use when prior beliefs about plausible alpha or factor usefulness should be explicit.
- Interpret posterior evidence, not only classical rejection.

Parsimony rule:

- Do not add factors only to improve in-sample fit.
- Require distinct economic meaning, robust incremental evidence, and stable implementation.

## Orthogonalization and Neutralization

Use residualization to isolate incremental information:

```text
x = a + B controls + residual
```

The residual is the part of `x` not linearly explained by the controls.

Rules:

- State whether residualization is done within date, over time, or across a pooled sample.
- State the base factor set and the order.
- Compare raw and residualized results because neutralization can remove intended economic content.
- Do not residualize using future information or full-sample coefficients when building a live signal.

## GMM

Use generalized method of moments when the model is naturally expressed through moment conditions:

```text
E[g_t(theta)] = 0
g_T(theta) = (1 / T) * sum_t g_t(theta)
theta_hat = argmin_theta g_T(theta)' W_T g_T(theta)
J = T * g_T(theta_hat)' W_T g_T(theta_hat)
```

Use GMM to unify estimation and testing, especially in asset pricing models with Euler equations or multiple moments.

Do not use GMM as a black box. Specify:

- Moment conditions and economic meaning.
- Parameter vector.
- Weighting matrix.
- Identification logic.
- Over-identification test interpretation.

## Mainstream Multi-Factor Models

Use these models as benchmarks or design references:

| Model | Factors | Main idea |
| --- | --- | --- |
| CAPM | Market | Expected excess return is explained by market beta. |
| Fama-French 3-factor | Market, SMB, HML | Add size and value to explain CAPM anomalies. |
| Carhart 4-factor | Market, SMB, HML, momentum | Add momentum to FF3. |
| Novy-Marx 4-factor | Market, value, momentum, profitability | Use gross profitability as an economically cleaner profitability measure. |
| Fama-French 5-factor | Market, SMB, HML, RMW, CMA | Add profitability and investment, motivated by valuation identities. |
| Hou-Xue-Zhang q-factor/q5 | Market, size, investment, ROE, expected growth | Ground expected returns in investment-based asset pricing. |
| Stambaugh-Yuan | Market, size, management, performance | Group anomalies related to mispricing and behavioral frictions. |
| Daniel-Hirshleifer-Sun | Market, FIN, PEAD | Use long-horizon financing behavior and short-horizon post-earnings drift. |

When applying to A-shares, verify factor construction, rebalancing frequency, financial data timing, price limits, suspension, and shorting feasibility instead of copying U.S. conventions mechanically.

## Machine Learning and PCA

Use machine learning for prediction, feature selection, nonlinear interactions, or high-dimensional factor libraries. Do not use it to bypass research discipline.

Linear and regularized models:

- OLS is a baseline but can fail badly with many correlated features.
- Ridge, lasso, and elastic net reduce overfit and can select useful predictors.
- Huber or robust loss helps when returns have outliers.

Tree and nonlinear models:

- Regression trees capture interactions but overfit easily.
- Random forest and boosting improve predictive performance through ensembling.
- XGBoost often works well in sparse or nonlinear tabular factor panels.
- Neural networks can work with enough data and regularization, but require strict validation and interpretability checks.

Evaluation:

```text
R^2_OOS = 1 - sum((R_{i,t+1} - R_hat_{i,t+1})^2)
              / sum((R_{i,t+1} - R_bar_{it})^2)
```

Use an economically fair benchmark. Historical mean can be too easy and may exaggerate model value. Use Diebold-Mariano style comparisons when comparing forecast errors.

Financial machine-learning validation:

- Define labels from executable forward-return windows. If labels overlap, use purging or embargoing so adjacent folds do not share future return information.
- Fit winsorization, imputation, scaling, neutralization, feature selection, and dimensionality reduction inside each training window, not on the full sample.
- Use rolling or expanding walk-forward validation for time variation; avoid random splits for panels with market regimes.
- Report out-of-sample `R^2`, IC, rank IC, turnover, net return, drawdown, and exposure overlap together.
- Compare against simple baselines: historical mean, linear factor composite, equal-weight signal score, and any existing production signal.
- Inspect whether feature importance is only rediscovering industry, size, liquidity, beta, or volatility exposures.

PCA and related methods:

- PCA extracts latent factors from return covariance but can lack economic interpretation.
- IPCA parameterizes factor exposures using company characteristics and can handle dynamic conditional models.
- Risk-premium PCA adds first-moment information to avoid using covariance alone.

PCA-derived factors still need stability, interpretability, investability, turnover, and constraint checks.
