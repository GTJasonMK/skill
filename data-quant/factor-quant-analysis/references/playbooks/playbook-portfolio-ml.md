# Portfolio and ML Playbook

Use when: converting research signals into portfolios, reviewing portfolio implementation, using ML for factor selection, or evaluating alternative data.
Read after: [agent-playbooks.md](agent-playbooks.md) identifies a portfolio or ML mode.
Key decisions: expected-return object, risk model, constraints, costs, validation split, baseline, final-test policy.
Do not use for: detailed econometric derivations or exact source-table lookup.

## Contents

- [External Lookup and Local Fit Checks](#external-lookup-and-local-fit-checks)
- [Research-to-Portfolio Conversion](#research-to-portfolio-conversion)
- [Portfolio Implementation Review](#portfolio-implementation-review)
- [Machine-Learning Factor Selection](#machine-learning-factor-selection)
- [Alternative Data](#alternative-data)

## External Lookup and Local Fit Checks

Read [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md) when the task depends on:

- Library/API uncertainty, optimizer errors, solver options, package-version behavior, or ML validation utilities.
- Data-vendor field semantics, index-vendor methodology, exchange rules, borrow/shorting rules, suspension/price-limit handling, or cost/capacity model assumptions.
- Paper or vendor definitions for portfolio construction, factor timing, risk models, covariance adjustment, Smart Beta rules, or alternative-data timestamps.

Use Context7 or official documentation for software behavior. Use original papers, exchange/regulator/index-vendor/data-vendor docs, or replication files for finance rules. Before applying the result, run a local fit check against the project package version, available columns, market, sample, frequency, weights, costs, shorting assumptions, and execution convention.

For ML work, an external solution can fix implementation details but cannot bypass time splits, walk-forward validation, purging/embargo where needed, final-test isolation, leakage checks, and cost-aware portfolio validation.

## Research-to-Portfolio Conversion

Use when the user wants an investable strategy, index enhancement, Smart Beta product, or production rollout.

Classify:

- Move from signal evidence to portfolio evidence.
- Identify benchmark, active-risk budget, turnover budget, cost model, risk model, and constraints.
- State whether alpha is a rank score, expected return, or optimizer objective coefficient.

Read:

- [practice-deep-dive.md](../practice/practice-deep-dive.md)
- [data-and-implementation.md](../data/data-and-implementation.md)
- [smart-beta-style-attribution.md](../practice/smart-beta-style-attribution.md) for factor products.
- [validation-and-risks.md](../practice/validation-and-risks.md)

Inspect first:

- Whether return model and risk model use compatible universes and horizons.
- Intended exposures: market, industry, size, value, profitability, investment, momentum, volatility, liquidity, beta.
- Cost model, ADV participation, liquidity capacity, borrowability, price limits, and suspensions.
- Hard constraints versus soft preferences.

Try next:

- Define expected return model.
- Define risk model or exposure controls.
- Define objective function.
- Add constraints in priority order.
- Add transaction-cost penalty or turnover limit.
- Run attribution: market, industry, style, residual, and cost drag.
- Build monitoring for IC decay, exposure drift, crowding, capacity, turnover, and drawdown.

Stop or downgrade if:

- Research universe differs from investable universe.
- Optimizer takes extreme positions.
- Alpha comes from names that cannot be bought or sold.
- Active risk is dominated by unintended exposures.
- Capacity or tradability is insufficient.

## Portfolio Implementation Review

Use when the user asks whether a proposed optimizer, index enhancement process, or production portfolio is reasonable.

Inspect first:

- Objective function: mean-variance, minimum variance, risk parity, maximum diversification, tracking-error objective, or custom utility.
- Return forecast scale and risk forecast scale.
- Factor covariance, specific risk, and covariance shrinkage or adjustment.
- Constraint priority: mandate constraints, benchmark exposure, risk limits, turnover, liquidity, and preferences.
- Cost function: linear fees/spread/tax and nonlinear market impact.

Try next:

- Stress expected returns, covariance, costs, and constraints.
- If optimizer behavior is surprising, verify solver/library semantics against official documentation before changing constraints.
- Inspect weight concentration, exposure flips, and turnover.
- Compare optimized portfolio to simple rank, equal-weight top bucket, and benchmark-relative baseline.
- Attribute ex ante and realized risk.

Stop or downgrade if:

- The optimizer is harvesting tiny alpha differences through excessive turnover.
- Small covariance or alpha perturbations produce large weight changes.
- Constraint relaxation is arbitrary or violates mandate priorities.

## Machine-Learning Factor Selection

Use when the user wants Ridge, Lasso, random forest, XGBoost, neural nets, PCA, IPCA, or high-dimensional features.

Classify:

- Decide whether ML is used for prediction, feature selection, nonlinear interaction discovery, latent-factor extraction, or timing.
- Keep asset-pricing interpretation separate from predictive performance.

Read:

- [ml-and-frontiers.md](../practice/ml-and-frontiers.md)
- [validation-and-risks.md](../practice/validation-and-risks.md)
- [a-share-data-details.md](../data/a-share-data-details.md)
- [method-map.md](../methods/method-map.md) for OOS metrics if needed.

Inspect first:

- Label definition and whether labels overlap.
- Time split, rolling window, expanding window, purging, and embargo.
- Whether preprocessing is fit only inside the training window.
- Feature availability timestamps.
- Baseline models and final-test policy.

Try next:

- Start with historical-mean and zero-forecast baselines, then linear and regularized baselines.
- Add nonlinear models only after simple baselines are fixed.
- Evaluate OOS `R^2`, IC, rank IC, quantile spreads, turnover, net return, drawdown, and factor exposures.
- Inspect feature importance, partial dependence, regime stability, and overlap with size, liquidity, beta, volatility, industry, and turnover.
- Record failed variants.

Stop or downgrade if:

- Train/test split is random IID.
- Scaling, imputation, neutralization, PCA, or feature selection uses full-sample data.
- Hyperparameters touch the final test.
- An external ML recipe replaces walk-forward evidence or final-test isolation.
- Only prediction loss is reported.
- No comparison to simple factor scores.

## Alternative Data

Use when the user wants text, geolocation, web scrape, satellite, payment, patent, or other nontraditional data.

Inspect first:

- Timestamp of raw observation, vendor delivery, revision, and strategy availability.
- Whether the signal is economically linked to a forecastable business variable.
- Coverage bias, survivorship bias, selection bias, and short history.
- Whether the data adds incremental information beyond price, volume, fundamentals, industry, and known sentiment.

Try next:

- Start with a narrow mechanism test before large ML modeling.
- Test timeliness advantage against public disclosures.
- Compare incremental IC, incremental alpha, and exposure overlap.
- Stress transaction costs because alternative data signals often decay quickly.

Stop or downgrade if:

- The data cannot be reproduced historically with availability timestamps.
- The signal is only a proxy for known liquidity, size, attention, or sentiment effects.
- The data provider's backfill or coverage start creates a hidden sample-selection problem.
