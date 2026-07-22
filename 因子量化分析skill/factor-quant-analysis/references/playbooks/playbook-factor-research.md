# Factor Research Playbook

Use when: handling factor ideas, single-factor validation, weak factors, implausibly strong factors, or multi-factor combinations.
Read after: [agent-playbooks.md](agent-playbooks.md) identifies a factor-research mode.
Key decisions: object type, mechanism, timing, first tests, red flags, stop rule.
Do not use for: point-in-time data audit details, optimizer design, or exact source-table lookup.

## Contents

- [Evidence and External-Research Hooks](#evidence-and-external-research-hooks)
- [Factor Idea Triage](#factor-idea-triage)
- [Single-Factor Validation](#single-factor-validation)
- [Weak or Insignificant Factor](#weak-or-insignificant-factor)
- [Too-Good Factor](#too-good-factor)
- [Multi-Factor Combination](#multi-factor-combination)

## Evidence and External-Research Hooks

If the user provides data, code, backtest output, weights, or trades, run the data evidence sequence in [data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md) before accepting the factor hypothesis. Treat the artifact as stronger evidence than a verbal claim, but weaker than a point-in-time, cost-aware, reproducible test.

Use external lookup only to resolve a specific uncertainty: original paper construction, canonical factor-library definition, market rule, data-vendor field semantics, library/API behavior, or a plausible next diagnostic. Do not use external examples to bypass local timing, tradability, cost, multiple-testing, and walk-forward checks.

For paper-based methods, check the original paper or replication source before changing direction, breakpoint, lag, weighting, neutralization, or test asset construction. Then run a local fit check for A-share rules, sample, frequency, costs, and available columns.

When a factor strategy has a visible flaw, use the Build-Diagnose-Repair Loop in [strategy-development-map.md](../strategy/strategy-development-map.md). Optimize only against a diagnosed defect from the observed results; do not add neutralization, nonlinear transforms, filters, ML, or optimizer layers merely because the first result is weak.

## Factor Idea Triage

Use when the user only has an idea such as low volatility, quality, sentiment, analyst revision, or alternative data.

Classify:

- Decide whether the idea is a prediction variable, anomaly, pricing factor, risk-control exposure, or portfolio construction rule.
- Identify the hypothesized mechanism: risk compensation, mispricing, behavioral bias, market microstructure, or pure data-mining candidate.
- State expected sign and horizon before looking at results.

Read:

- [research-workflow.md](research-workflow.md)
- [factor-and-model-catalog.md](../models-factors/factor-and-model-catalog.md)
- [factor-mechanism-diagnostics.md](../models-factors/factor-mechanism-diagnostics.md)
- [validation-and-risks.md](../practice/validation-and-risks.md)
- [behavioral-and-factor-zoo-details.md](../theory/behavioral-and-factor-zoo-details.md) if the story is behavioral.

Inspect first:

- Market, benchmark, universe, rebalance date, signal date, execution date, holding period, and return label.
- Observable timestamp for every input variable.
- Tradability filter: ST, suspension, price limits, listing age, liquidity, blacklists, financial firms when accounting comparability matters.
- Overlap with size, value, profitability, investment, momentum, volatility, turnover, liquidity, beta, or industry.

Try next:

- Write a research protocol before code.
- If data is already available, run evidence-mode checks before revising the hypothesis.
- Define raw signal, transformed signal, neutralized signal, and missing-value policy.
- Run coverage, distribution, IC/rank IC, quantile portfolios, monotonicity, turnover, and horizon decay.
- Add controls only after raw behavior is understood.

Stop or downgrade if:

- The idea has no sign or horizon.
- The signal requires data not observable at rebalance.
- The expected return source is a hidden small-cap, illiquidity, or industry bet.
- No point-in-time construction is possible.

## Single-Factor Validation

Use when the user asks whether one factor works.

Classify:

- Identify whether the factor predicts returns, explains risk, or controls exposure.
- Define raw signal direction and whether higher values should imply higher or lower future returns.

Read:

- [method-map.md](../methods/method-map.md)
- [econometrics-deep-dive.md](../methods/econometrics-deep-dive.md)
- [validation-and-risks.md](../practice/validation-and-risks.md)
- [a-share-data-details.md](../data/a-share-data-details.md) for A-share data handling.

Inspect first:

- Signal availability at rebalance time.
- Coverage, missing rate, outliers, stale values, and ties.
- Exposure to industry, size, beta, volatility, liquidity, price, and known styles.
- Turnover and rank stability.

Try next:

- Run raw IC and rank IC by date.
- Run quantile portfolios, equal-weight and value-weight where feasible.
- Check monotonicity across all groups, not only top-minus-bottom.
- Test holding periods and horizon decay.
- Compare gross and cost-adjusted spreads.

Stop or downgrade if:

- Middle groups are unordered and mechanism does not predict thresholds.
- Effect exists only in microcaps or illiquid names.
- Long side is weak and short side drives the reported spread.
- Cost-adjusted returns vanish under realistic turnover.

## Weak or Insignificant Factor

Use when a factor has weak IC, insignificant spreads, unstable results, or poor sample-out behavior.

Classify:

- Decide whether this is construction failure, data issue, horizon mismatch, market-regime issue, cost issue, or truly invalid factor.
- Decide whether the factor was expected to produce alpha or only control risk.

Inspect first:

- Factor direction, timing alignment, holding period, rebalance frequency, outlier policy, and neutralization policy.
- Sample split by size, industry, liquidity, and regime.
- Long side and short side separately.

Try next:

- Use external lookup only to find canonical construction differences or the next diagnostic, then validate locally.
- Map the weak result to one defect class before changing the construction.
- Reverse sign only if the economic mechanism supports it.
- Test alternative but pre-specified horizons.
- Compare raw, winsorized, standardized, and neutralized versions.
- Compare equal-weight and value-weight portfolios.
- Run no more than three targeted next experiments before changing the research claim.

Stop or downgrade if:

- The only working version uses an arbitrary lag, bucket, filter, or neutralization.
- The factor works only in a tiny high-turnover or low-liquidity subuniverse.
- The effect lacks sign stability, horizon logic, and economic rationale.

## Too-Good Factor

Use when the result looks implausibly strong.

Classify:

- Treat this as forensic review before accepting the result.
- Identify whether the result is a data artifact, execution artifact, hidden exposure, overfit, or genuine anomaly candidate.

Read:

- [validation-and-risks.md](../practice/validation-and-risks.md)
- [a-share-data-details.md](../data/a-share-data-details.md)
- [playbook-data-backtest.md](playbook-data-backtest.md) when backtest mechanics matter.

Inspect first:

- Timing of every input and label.
- Survivorship, current-constituent use, and financial announcement timestamps.
- Costs and tradability.
- Concentration by year, industry, size bucket, crisis, or short leg.
- Number of attempted variants.

Try next:

- Check original construction rules and known failure modes before accepting a new variant.
- Treat each repair as a hypothesis test against the frozen baseline.
- Rebuild strict point-in-time data.
- Add realistic execution delay, costs, impact, and liquidity filters.
- Run time splits and locked final period.
- Attribute to known factors and industries.
- Run multiple-testing diagnostics if many candidates were searched.

Stop or downgrade if:

- Performance collapses after execution delay or costs.
- Performance is mostly exposure to known factors.
- Strategy depends on shorting hard-to-borrow or limit-down names.

## Multi-Factor Combination

Use when the user has multiple factors or wants a score.

Classify:

- Separate substitute factors from complementary factors.
- Decide whether the target is return prediction, risk control, Smart Beta index construction, or portfolio optimization.

Read:

- [practice-deep-dive.md](../practice/practice-deep-dive.md)
- [factor-and-model-catalog.md](../models-factors/factor-and-model-catalog.md)
- [a-share-model-evidence.md](../models-factors/a-share-model-evidence.md)
- [validation-and-risks.md](../practice/validation-and-risks.md)

Inspect first:

- Pairwise correlations, rank correlations, and overlap with known factor families.
- Economic relationship such as `EP = BM x ROE`.
- Stability of each factor's IC and turnover.
- Exposure overlap after industry, size, beta, liquidity, and volatility controls.

Try next:

- Start with simple equal-weight standardized scores.
- Compare with IC weighting only after checking IC stability.
- Use neutralization or orthogonalization only with explicit base set and order.
- Compare combined score against the best single-factor baseline.
- Check whether combination improves sample-out net performance, not only in-sample fit.

Stop or downgrade if:

- Many variants of the same idea are labeled diversification.
- Optimized weights are learned from the full sample.
- Orthogonalization order is unstated.
- Improvement is only higher in-sample IC or only an arbitrary subperiod.
