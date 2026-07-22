# Quant Finance Report Templates

Use these outlines when the user asks for a quant research plan, factor report, backtest review, risk model report, or portfolio diagnostics. Keep investment claims conditional on data quality, costs, and validation evidence.

## Alpha Factor Research Report

1. **Research question**: asset class, universe, signal definition, economic hypothesis, rebalance frequency, and forward-return horizon.
2. **Point-in-time and timing design**: signal timestamp, availability lag, tradable universe, corporate actions, survivorship controls, missing-data handling, point-in-time audit findings, execution timing, and forward-return window alignment.
3. **Research audit trail**: experiment registry coverage, failed variants, predeclared families, selected candidates, final-test evidence, data/code versions, and FDR/reality-check scope.
4. **Signal preparation**: winsorization, ranking/z-scoring, sector/size/beta neutralization, lagging, and outlier policy.
5. **Predictive diagnostics**: Pearson IC, rank IC, IC t-stat/positive rate, IC decay, quantile returns, long-short spread, and hit rate.
6. **Tradability diagnostics**: execution timing audit, tradability audit, turnover, transaction cost sensitivity, liquidity/capacity, borrow constraints, and implementation timing.
7. **Risk and exposure checks**: benchmark beta, style/sector exposures, drawdowns, tail risk, and residual volatility.
8. **Validation decision**: train/validation/test split, multiple-testing status, robustness windows, and go/no-go criteria.

## Strategy Backtest Report

1. **Strategy specification**: signals, portfolio rule, rebalance calendar, holding period, execution price, leverage, and constraints.
2. **Data integrity**: survivorship, point-in-time audit status, availability/revision/universe timestamps, execution timing audit status, tradability audit status, delistings, corporate actions, calendars, currencies, and stale prices.
3. **Backtest design**: walk-forward or out-of-sample structure, benchmark, execution timestamp, forward-return window, cash/risk-free treatment, and cost assumptions.
4. **Performance**: CAGR, annualized return/volatility, Sharpe/Sortino, drawdown, VaR/ES, win rate, exposure, and benchmark-relative metrics.
5. **Implementation costs**: one-way/two-way turnover, commissions, spread/slippage, borrow, financing, market impact, and net-vs-gross results.
6. **Robustness**: subperiods, regimes, parameter sensitivity, universe sensitivity, execution timing, and stress periods.
7. **Decision**: whether evidence supports further research, paper trading, capital allocation, or rejection.

## Factor Exposure and Attribution Report

1. **Return definition**: strategy/asset return, benchmark, risk-free rate, frequency, currency, and sample period.
2. **Factor model**: CAPM, Fama-French/Carhart, custom style factors, sector factors, or statistical factors.
3. **Regression output**: alpha, betas, standard errors/t-stats, R-squared, residual volatility, and sample size.
4. **Diagnostics**: rolling beta stability, residual autocorrelation, heteroskedasticity, influence points, and drawdown overlap.
5. **Attribution**: benchmark contribution, factor contribution, residual return, active risk, and information ratio.
6. **Limits**: omitted factors, nonstationarity, autocorrelated returns, costs, capacity, and benchmark mismatch.

## Portfolio Risk Report

1. **Portfolio definition**: holdings, weights, rebalance timing, leverage, cash, constraints, and benchmark.
2. **Risk inputs**: return window, covariance estimator, volatility model, factor model, and data frequency.
3. **Portfolio diagnostics**: volatility, drawdown, VaR/ES, beta, tracking error, concentration, and turnover.
4. **Exposure diagnostics**: asset, sector, country, currency, duration, style, and factor exposures.
5. **Stress and sensitivity**: historical stress periods, shock scenarios, covariance/volatility sensitivity, and liquidity stress.
6. **Actions**: hedge, rebalance, reduce concentration, revise constraints, or collect better risk data.

## Model Risk Register Report

1. **Inventory scope**: models, signals, optimizers, execution models, risk forecasts, or live strategies included in the register.
2. **Governance status**: owner, validator, risk tier, active/live status, approval status, limitations, waivers, and evidence links.
3. **Review cadence**: last review date, next review due date, stale or overdue reviews, open issues, and required sign-offs.
4. **Control evidence**: monitoring plan, rollback plan, kill switch or manual override, data version, code version, and production evidence.
5. **Decision**: pass, review, or fail for go-live, scaling, periodic review, or committee escalation.

## Committee Review Pack

1. **Decision stack**: research gate, portfolio construction gate, production gate, and any action policy decisions.
2. **Source diagnostics**: point-in-time audit, execution timing audit, tradability audit, IC, incremental alpha, overlap, backtest, constraints, exposures, risk, model-risk register, cost/capacity, execution, data, and monitoring evidence.
3. **Role review**: PM/research, portfolio, risk, trading, data, and operations findings with owners.
4. **Blockers and evidence gaps**: unresolved blockers, missing diagnostics, missing owner sign-off, and waiver requirements.
5. **Next actions**: approve, review, revise, pause, reject, or define additional diagnostics before promotion.

## Event Study Report

1. **Event definition**: event type, event timestamp, affected assets, clustering, and inclusion/exclusion rules.
2. **Windows**: estimation window, event window, post-event window, and gap between estimation and event windows.
3. **Expected-return model**: market-adjusted, CAPM/factor model, matched control, or fixed-effects model.
4. **Abnormal return results**: AR, CAR/BHAR, uncertainty, cross-sectional dispersion, and sign/hit rate.
5. **Validity checks**: leakage before event, overlapping events, confounding news, thin trading, and multiple testing.
6. **Conclusion**: economic magnitude, robustness, and whether the evidence is exploratory or confirmatory.
