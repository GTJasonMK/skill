# Metrics And Formulas

Use this file when a task requires concrete definitions, equations, or quantitative checks. Keep formulas tied to the claim being tested.

## Returns And Exposures

Single-period return:

```text
R_t = (V_t - V_{t-1}) / V_{t-1}
```

Compound annual growth rate:

```text
CAGR = (V_T / V_0)^(1/T) - 1
```

Net and gross exposure:

```text
Net = LongExposure - ShortExposure
Gross = LongExposure + |ShortExposure|
```

Portfolio beta exposure:

```text
Beta_p = sum_i w_i * Beta_i
```

Use net exposure for directional market bias, gross exposure for leverage and balance-sheet usage, and beta exposure for systematic market sensitivity.

## Alpha And Valuation Metrics

Market-model alpha:

```text
r_p - r_f = alpha + beta * (r_m - r_f) + epsilon
```

Price-to-earnings and earnings yield:

```text
P/E = Price / EarningsPerShare
E/P = EarningsPerShare / Price
```

PEG:

```text
PEG = (P/E) / ExpectedEarningsGrowth
```

Pair/stat-arb spread:

```text
Spread_t = Price_A,t - beta * Price_B,t
z_t = (Spread_t - mean(Spread)) / std(Spread)
```

Linear alpha combination:

```text
Alpha_i = sum_k theta_k * Signal_{i,k}
```

Conditional alpha combination:

```text
Alpha_i =
  Alpha_A if RegimeCondition is true
  Alpha_B otherwise
```

Bayesian update:

```text
Posterior odds = Prior odds * Likelihood ratio
```

Use Bayesian framing when a new signal should update, not replace, prior belief.

## Risk Metrics

Volatility:

```text
sigma = sqrt(sum_t (r_t - mean(r))^2 / (T - 1))
Annualized sigma = Daily sigma * sqrt(252)
```

Cross-sectional dispersion:

```text
Dispersion_t = sqrt(sum_i (r_{i,t} - mean_cross_section_t)^2 / (N - 1))
```

Covariance and correlation:

```text
Cov(i,j) = E[(r_i - mu_i)(r_j - mu_j)]
rho(i,j) = Cov(i,j) / (sigma_i * sigma_j)
```

Portfolio variance:

```text
Var(p) = w' * Sigma * w
```

Normal VaR approximation:

```text
VaR_c = z_c * sigma_p * PortfolioValue
```

Target-volatility leverage:

```text
Leverage = TargetVolatility / ForecastVolatility
```

Kelly fraction:

```text
f* = edge / variance
```

Use Kelly only as a sizing reference. Real strategies require drawdown, tail risk, financing, and model-error haircuts.

PCA/statistical risk factor model:

```text
R = B * F + epsilon
```

Check whether the statistical factor is economically interpretable, stable, and not a short-lived artifact.

## Transaction Costs

Total cost:

```text
TC = CommissionsAndFees + Slippage + MarketImpact
```

Slippage:

```text
Slippage = ExecutedPrice - DecisionPrice
```

Use sign conventions consistently: for buys, higher executed price is worse; for sells, lower executed price is worse.

Cost functions:

```text
Constant: TC(q) = c
Linear: TC(q) = a + b * |q|
Piecewise: TC(q) = a_j + b_j * |q| for q in interval j
Quadratic: TC(q) = a + b * |q| + gamma * q^2
```

Participation rate:

```text
Participation = OrderSize / MarketVolumeOverExecutionWindow
```

Trade worthiness:

```text
ExpectedAlphaBenefit + ExpectedRiskReduction > ExpectedTransactionCost
```

## Portfolio Construction

Target trade:

```text
Trade_i = TargetWeight_i - CurrentWeight_i
```

Equal risk weight approximation:

```text
w_i proportional to 1 / sigma_i
```

Mean-variance objective:

```text
maximize: w' * mu - lambda * w' * Sigma * w - TC(w - w0)
subject to constraints
```

Sharpe ratio:

```text
Sharpe = (mean(r_p) - r_f) / sigma_p
```

GARCH(1,1):

```text
sigma_t^2 = omega + alpha * epsilon_{t-1}^2 + beta * sigma_{t-1}^2
```

Use GARCH when volatility clustering matters; do not use it as evidence that volatility shocks are fully understood.

## Research Metrics

Cumulative return:

```text
CumReturn_T = product_t (1 + r_t) - 1
```

Maximum drawdown:

```text
MDD = min_t (Wealth_t / running_max(Wealth)_t - 1)
```

Predictive $R^2$:

```text
R^2 = 1 - sum_t (y_t - yhat_t)^2 / sum_t (y_t - mean(y))^2
```

Robustness ratio:

```text
Robustness = R^2_out_of_sample / R^2_in_sample
```

Hit rate:

```text
HitRate = ProfitablePeriods / ActivePeriods
```

Information ratio:

```text
IR = mean(active_return) / std(active_return)
```

Calmar and Omega:

```text
Calmar = AnnualizedReturn / |MaximumDrawdown|
Omega(threshold) = sum gains above threshold / |sum losses below threshold|
```

Bucket monotonicity:

```text
AverageReturn(Q1) <= AverageReturn(Q2) <= ... <= AverageReturn(QN)
```

For financial prediction, small $R^2$ can be valuable. Extremely high $R^2$ is a leakage alarm.

## HFT And Market Microstructure Metrics

Spread and midpoint:

```text
Spread = BestAsk - BestBid
Mid = (BestAsk + BestBid) / 2
```

Queue edge:

```text
QueueEdge = PnL_front_of_queue - PnL_back_of_queue
```

Cancellation rate:

```text
CancelRate = CancelledOrders / SubmittedOrders
```

HFT unit economics:

```text
NetProfit = GrossSpreadCapture + Rebates + Alpha - Fees - AdverseSelection - InventoryLoss - InfrastructureCost
```

Index arbitrage fair value:

```text
FuturesFairValue ~= SpotIndex * exp((r - dividend_yield) * time_to_expiry)
```

Use HFT formulas only with venue, latency, fill probability, and queue assumptions stated.
