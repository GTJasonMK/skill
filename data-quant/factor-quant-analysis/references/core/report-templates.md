# Report Templates

## Contents

- [Common Evidence Fields](#common-evidence-fields)
- [Strategy Development and Iteration Report](#strategy-development-and-iteration-report)
- [Factor Research Memo](#factor-research-memo)
- [Anomaly Test Report](#anomaly-test-report)
- [Backtest Audit Report](#backtest-audit-report)
- [Smart Beta Evaluation](#smart-beta-evaluation)
- [Portfolio Optimization Review](#portfolio-optimization-review)
- [Style and Risk Attribution](#style-and-risk-attribution)

## Common Evidence Fields

Add these fields when data artifacts or external research materially affect the answer:

- Analysis run record summary from [full-analysis-run-record.md](full-analysis-run-record.md) when the task asks for complete analysis, strategy repair, audit, promotion, paper trading, production, reduction, pause, or retirement.
- Claim side: alpha, beta/lambda, risk-model, prediction, or portfolio-implementation claim.
- Six-criteria grade when factor effectiveness or stage promotion is claimed: logic, persistence, incremental information, robustness, investability, and universality.
- Search-space/prior record when discovery, many variants, ML search, or repeated optimization is involved.
- Model-consistency record when portfolio optimization, Smart Beta, risk attribution, or production portfolio use is involved.
- Domain-logic record when fundamental, industry, event, text, alternative-data, or microstructure signals drive the claim.
- Data diagnostics performed.
- External sources checked.
- Local validation of external solution.
- Unverified assumptions.
- Final self-review from [decision-core.md](decision-core.md) when a recommendation, repair, promotion, rejection, or next experiment depends on strategy evidence.

## Strategy Development and Iteration Report

Use this template when the user asks to build a strategy from data features, find an entrypoint, diagnose a flawed strategy, or iteratively improve a backtest.

1. Available evidence: data artifacts, fields, timestamps, frequency, coverage, labels, tradability, weights, trades, and code/backtest outputs.
2. Data-feature entrypoint scan: feasible strategy families, rejected entrypoints, and why the primary entrypoint was selected.
3. First falsifiable hypothesis: object, mechanism, sign, horizon, universe, benchmark, execution timing, and expected first phenomenon.
4. Analysis run record summary: references used, decision spine, claim side, evidence state, baseline ID, observed phenomenon, defect class, six-criteria grade, search-space/prior state when relevant, model consistency when relevant, domain logic when relevant, experiment registry or next experiments, and stage gate verdict.
5. Decision ledger snapshot: current question, object type, selected anchor, data state, baseline ID, primary uncertainty, current grade, and next decision.
6. Frozen baseline: raw signal, simple portfolio rule, benchmark, cost assumption, and diagnostics that must remain comparable across repairs.
7. Observed phenomena: IC/rank IC, quantile shape, long/short legs, turnover, cost drag, exposure, drawdown, capacity, and subperiod behavior.
8. Evidence conflict resolution: conflicting metrics, priority used, and why the interpretation is not cherry-picked.
9. Primary defect class: data/timing, label, signal, universe/tradability, hidden exposure, portfolio construction, cost/capacity, overfit, or regime.
10. Targeted experiments: at most three changes, each tied to one defect hypothesis and compared against the frozen baseline.
11. Repair decision: what changed, what did not change, whether the repair solved the diagnosed flaw, and what new risk it introduced.
12. Stage gate verdict: reject, not determinable, research-only, risk-control only, portfolio candidate, paper trade, production candidate, monitor, reduce, pause, or retire.
13. Final self-review: object, claim side, timing, anchor, baseline, phenomenon, defect, experiment, gate, applicable reasoning gates, and missing evidence that would change the conclusion.
14. Failed variants, Unverified assumptions, and next evidence that would change the conclusion.

## Factor Research Memo

Use this template when the user asks for a formal factor research report.

1. Research question and economic hypothesis.
2. Claim side and proof boundary: alpha, beta/lambda, risk-model, prediction, or portfolio-implementation claim; what the current evidence can and cannot prove.
3. Universe, benchmark, rebalance calendar, execution timing, holding horizon, and tradability assumptions.
4. Point-in-time data sources, financial-statement availability rules, corporate-action handling, and eligibility filters.
5. Signal definition: raw formula, direction, missing values, invalid denominators, winsorization, standardization, and neutralization.
6. Domain logic and prior: economic, behavioral, accounting, microstructure, industry, or business mechanism; proxy validity and failure mode if wrong.
7. Search-space/prior record: tested family, variants seen, search-space size or unknown, prior plausibility, multiple-testing control, and final-test policy.
8. Data diagnostics performed: coverage, distribution, missingness, outliers, stale values, duplicates, timing, and tradability checks.
9. Analysis run record summary when the memo is part of a complete analysis or stage decision.
10. External sources checked: original paper, factor-library definition, vendor rule, market rule, or official documentation if construction depends on them.
11. First-pass evidence: coverage, distribution, IC/rank IC, positive-rate, ICIR, horizon decay, and rank autocorrelation.
12. Portfolio evidence: quantile returns, high-minus-low spread, monotonicity, turnover, equal-weight and value-weight results.
13. Regression evidence: Fama-MacBeth coefficients, controls, time-series alpha against benchmark factors, and robust standard errors.
14. Robustness: subperiods, regimes, alternative definitions, weighting schemes, neutralization choices, and out-of-sample behavior.
15. Six-criteria grade: logic, persistence, incremental information, robustness, investability, and universality.
16. Implementation evidence: expected return mapping, risk model, constraints, turnover, costs, liquidity, capacity, and borrow/shorting feasibility.
17. Local validation of external solution: how any imported construction/API/rule was tested against local data and dependencies.
18. Interpretation: risk compensation, mispricing, or data-snooping evidence; unresolved competing explanations.
19. Recommendation: research-only, monitor, paper trade, production candidate, or reject.
20. Limitations, failed variants, Unverified assumptions, and monitoring plan.

## Anomaly Test Report

Use this template when the claim is abnormal return not explained by known models.

1. Anomaly definition, sorting variable, expected sign, and prior mechanism.
2. Claim side: unexplained alpha, omitted risk/beta-lambda, prediction-only, or implementation candidate.
3. Test assets or sorted portfolios, weighting, rebalance frequency, and return horizon.
4. Baseline pricing models: CAPM, Fama-French style factors, q-factor/q5, local A-share model, or production risk model.
5. Raw evidence: quantile returns, spread, monotonicity, and sample stability.
6. Controlled evidence: multi-sorting, Fama-MacBeth controls, and neutralized signal results.
7. Alpha evidence: time-series alpha, factor exposures, Newey-West/HAC t-stats, and average absolute alpha.
8. Search-space, multiple-testing, prior, final-test, and publication-decay checks.
9. Risk-compensation diagnostics: bad-state loadings, covariance with known risks, and regime behavior.
10. Mispricing diagnostics: behavioral channel, limits to arbitrage, correction horizon, and event evidence.
11. Data diagnostics performed and external construction sources checked.
12. Six-criteria grade and investability: logic, persistence, incremental information, robustness, universality, short leg feasibility, turnover, costs, liquidity, and capacity.
13. Conclusion: unexplained anomaly, omitted-risk candidate, prediction-only pattern, implementation candidate, fragile pattern, or rejected result.

## Backtest Audit Report

Use this template when reviewing an existing factor backtest or strategy result.

1. Claimed result and minimum reproduction target.
2. Analysis run record summary: references used, audit object, claim side, timing state, baseline ID if available, observed phenomenon, defect class, six-criteria gaps, search-space/prior gaps, domain-logic gaps, evidence conflicts, and stage blockers.
3. Decision timestamp audit: signal date, data availability, rebalance date, execution date, and forward-return window.
4. Universe audit: historical membership, delistings, listing-age filters, ST/delisting-warning flags, sector exclusions, and survivorship.
5. Data audit: point-in-time financials, revisions, adjusted prices, suspensions, price limits, stale prices, and corporate actions.
6. Data diagnostics performed: scripts or manual checks used for structure, timing, coverage, missingness, outliers, labels, tradability, costs, and exposures.
7. Signal audit: raw formula, transformations, neutralization, missing values, outliers, and full-sample preprocessing risk.
8. Portfolio audit: weighting, constraints, turnover, benchmark-relative exposure, and optimizer sensitivity.
9. Cost and tradability audit: commission, tax, spread, slippage, market impact, borrow, participation, limit-up buys, and limit-down sells.
10. External sources checked for data/vendor/market-rule/API assumptions.
11. Local validation of external solution, if any.
12. Statistical audit: tested variants, search-space size or unknown, prior plausibility, multiple-testing controls, final-test isolation, and walk-forward design.
13. Conflicting evidence and interpretation: timing versus statistics, signal versus portfolio, gross versus net, long-short versus long-only, or backtest versus paper/live.
14. Stage promotion blockers: missing timing, cost, capacity, exposure, final-test, monitoring, rollback, or reproducibility evidence.
15. Reproducibility gaps: missing code, missing metadata, ambiguous assumptions, unlogged rejected variants, or Unverified assumptions.
16. Required fixes before trusting the result.

## Smart Beta Evaluation

Use this template when evaluating a factor index, ETF, or rules-based product.

1. Product objective, benchmark, target factor exposure, and investor use case.
2. Index construction: universe, eligibility, factor variables, scoring, selection, weighting, rebalancing, buffers, and turnover controls.
3. Exposure review: target factor exposure, unintended industry/size/value/momentum/quality/volatility/liquidity exposures, and exposure stability.
4. Performance review: absolute return, active return, drawdown, tracking error, hit rate, and benchmark-relative risk.
5. Cost review: management fee, turnover, estimated trading cost, capacity, and liquidity.
6. Crowding review: valuation spread, ownership overlap, factor volatility, correlation, and flow/capacity stress where data exists.
7. External sources checked: index methodology, vendor definitions, official documentation, and fee/holding disclosures.
8. Local validation of external solution or methodology against holdings, exposures, costs, and tradability.
9. Product fit: role in portfolio, overlap with existing holdings, regime behavior, and rebalancing implications.
10. Recommendation, Unverified assumptions, and monitoring triggers.

## Portfolio Optimization Review

Use this template when reviewing an expected-return model plus optimizer.

1. Investment objective, benchmark, risk budget, and allowable instruments.
2. Expected-return model: signal inputs, scaling, decay, forecast horizon, and mapping from score to expected return.
3. Risk model: factor exposures, covariance, specific risk, forecast-risk validation, and residual diagnostics.
4. Model consistency check: whether expected-return horizon, risk horizon, cost horizon, benchmark, universe, constraints, and optimizer objective target the same portfolio decision.
5. Misalignment check: whether return-model variables match, overlap with, or are missing from the risk model.
6. Objective function: mean-variance, minimum variance, risk parity, maximum diversification, or custom utility.
7. Constraints: long-only/shorting, leverage, single-name, industry, style, benchmark active weight, tracking error, turnover, liquidity, and lot-size rules.
8. Cost model: linear costs, market impact, borrow, tax, financing, and participation limits.
9. Sensitivity: perturb expected returns, covariance, costs, and constraints; inspect weight turnover and exposure flips.
10. External sources checked: optimizer/library behavior, solver options, risk-model convention, market rule, or vendor field definition.
11. Local validation of external solution against package version, project API, constraints, weights, costs, and execution convention.
12. Production readiness gate: required evidence for portfolio candidate, paper trading, production candidate, or live monitoring.
13. Analysis run record summary when the optimizer review supports strategy repair, promotion, or production-readiness decisions.
14. Monitoring and rollback assumptions: signal health, exposure drift, capacity, slippage, data freshness, risk breaches, action thresholds, and rollback owner.
15. Attribution and monitoring: intended factor exposure, unintended exposure, idiosyncratic contribution, costs, residual, live-vs-paper drift, and Unverified assumptions.

## Style and Risk Attribution

Use this template when explaining a fund, strategy, or portfolio.

1. Object analyzed, benchmark, frequency, sample window, and data source.
2. Style model: chosen factors, return-based or holding-based approach, constraints, and rolling-window setup.
3. Return attribution: alpha, factor exposures, factor return contributions, residual, and stability.
4. Style drift: rolling exposure changes, manager mandate consistency, and benchmark-relative style shifts.
5. Risk model: market, industry, style, specific risk, covariance assumptions, and active weights.
6. Risk attribution: exposure x volatility x correlation contribution, factor risk, industry risk, specific risk, and concentration risk.
7. Interpretation: intended style, unintended bets, omitted factors, and whether alpha survives reasonable model changes.
8. Monitoring: exposure limits, drawdown triggers, factor crowding, and data freshness.
