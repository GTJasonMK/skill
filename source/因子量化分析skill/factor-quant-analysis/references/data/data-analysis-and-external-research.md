# Data Analysis and External Research

Use when: the user provides data artifacts, schemas, code, backtest outputs, portfolio weights, trades, logs, implementation errors, unclear library/API behavior, market-rule questions, data-vendor field definitions, or paper factor-construction uncertainty.

Purpose: push the agent from narrative explanation into evidence-gathering mode. Do not accept a factor claim, implementation recipe, or external solution until it is checked against the local data, market constraints, and project dependencies.

## Data Evidence Mode

Enter Data Evidence Mode whenever a CSV/table/schema/code artifact/backtest/weights/trades file exists or can be inspected. First describe what evidence is available, then run or manually reproduce the smallest diagnostics that can change the conclusion.

If the user's goal is strategy construction, use the diagnostics below with [decision-core.md](../core/decision-core.md), [method-idea-anchors.md](../methods/method-idea-anchors.md), and [strategy-worked-examples.md](../strategy/strategy-worked-examples.md) to choose a strategy entrypoint in [strategy-development-map.md](../strategy/strategy-development-map.md). Do not jump from "interesting column" to "strategy"; first ask which center idea and strategy family the data can actually support and what phenomenon should appear first.

Fixed data analysis order:

1. Data object identification: classify raw market data, point-in-time fundamentals, factor panel, return label panel, holdings, trades, optimizer input, or backtest output.
2. Keys and fields: identify date key, asset key, signal fields, return labels, weights, prices, volumes, timestamps, and vendor metadata.
3. Time ordering: compare signal date, availability date, rebalance date, execution date, fill date, and forward-return start/end.
4. Coverage and missingness: summarize cross-sectional count, date coverage, missingness by date/industry/size, duplicate keys, and survivorship clues.
5. Outliers, stale values, and ties: check extreme values, repeated values, stale prices/signals, zero volume, rank ties, and full-sample preprocessing.
6. Label and forward-return window: verify label horizon, overlap, benchmark adjustment, compounding convention, and execution feasibility.
7. Factor diagnostics: run IC/rank IC, quantile spread, monotonicity, horizon decay, turnover, long/short leg split, and regime/subsample checks.
8. Costs, tradability, and capacity: inspect commissions, tax, spread, slippage, impact, ADV participation, suspensions, price limits, borrow, shorting, and capacity.
9. Exposure and redundancy: inspect industry, size, beta, volatility, liquidity, value, profitability, investment, momentum, turnover, and signal overlap.
10. Decision grading: classify as usable evidence, needs rerun, research-only, implementation-risky, or reject; state what would change the grade.

If the data is used for strategy construction or promotion, the diagnostics must be specific enough to fill the decision ledger in [research-governance.md](../strategy/research-governance.md): data state, baseline evidence, observed phenomena, missing evidence, and current grade.

Strategy-construction handoff:

- If fields are sufficient and timing is valid, pass the data features to the Data-Feature Entrypoint Scan in [strategy-development-map.md](../strategy/strategy-development-map.md).
- If the field-to-hypothesis move is unclear, match the field list to [strategy-worked-examples.md](../strategy/strategy-worked-examples.md) before choosing the first baseline.
- If several methods are possible, use [method-idea-anchors.md](../methods/method-idea-anchors.md) to select the anchor with the clearest first empirical question.
- If the user already has a backtest or flawed strategy, pass the observed phenomena to the Build-Diagnose-Repair Loop in [strategy-development-map.md](../strategy/strategy-development-map.md).
- If diagnostics conflict, use the Evidence Conflict Matrix in [research-governance.md](../strategy/research-governance.md) before choosing an interpretation.
- If timing, labels, universe, or tradability are not auditable, stop strategy construction and request or reconstruct the missing evidence first.

## Statistical-Learning Script Map

If a CSV is available and `statistical-learning-analysis` is exposed, prefer its bundled scripts for mechanical checks before writing custom code. Use these script names as the first lookup map:

| Need | Scripts |
| --- | --- |
| Structure and coverage | `profile_dataset.py`, `panel_summary.py`, `missingness_report.py` |
| Point-in-time and execution timing | `point_in_time_audit.py`, `execution_timing_audit.py` |
| Tradability | `tradability_audit.py` |
| Factor evidence | `factor_ic_report.py`, `factor_quantile_report.py`, `factor_decay_report.py`, `factor_turnover_report.py` |
| Signal redundancy and incremental value | `signal_overlap_report.py`, `incremental_alpha_report.py` |
| Costs and capacity | `transaction_cost_report.py`, `capacity_impact_report.py` |
| Regression evidence | `cross_sectional_return_regression.py`, `fama_macbeth_regression.py`, `newey_west_regression.py` |
| Portfolio evidence | `portfolio_backtest.py`, `long_short_backtest.py`, `portfolio_exposure_report.py`, `portfolio_constraint_check.py` |
| Risk and covariance | `covariance_report.py`, `risk_contribution_report.py`, `optimizer_sensitivity_report.py` |
| Multiple testing and experiment hygiene | `multiple_testing_report.py`, `quant_experiment_audit.py`, `bootstrap_reality_check.py` |
| Gate and aggregate review | `alpha_research_gate_report.py`, `portfolio_construction_gate_report.py`, `quant_report_aggregator.py`, `quant_review_pack.py` |

If a script cannot run because required columns are missing, dependencies are unavailable, or the data is not local, inspect the same diagnostics manually and report the blocker.

## Minimum Diagnostic Record

Use this compact record when scripts are unavailable, the data is partial, or the user asks for a complete analysis record. The goal is to make the evidence auditable enough to fill [full-analysis-run-record.md](../core/full-analysis-run-record.md).

| Diagnostic | Minimum record | Decision impact |
| --- | --- | --- |
| Object and keys | Data object, date key, asset key, duplicate key count. | Determines whether panel evidence is auditable. |
| Timing | Signal date, availability date, rebalance date, execution date, forward-return start/end. | Detects future function, label leakage, and non-executable timing. |
| Coverage | Date range, cross-sectional count by date, universe membership, listing-age and delisting handling. | Detects survivorship, thin samples, and universe drift. |
| Missingness | Missing rate by date, field, industry/size group where available. | Separates data absence from economic signal weakness. |
| Signal quality | Distribution, outliers, stale values, ties, invalid denominators, transformation and neutralization state. | Identifies construction defects and full-sample preprocessing risk. |
| Label quality | Return horizon, overlap, benchmark adjustment, compounding, price adjustment, suspension/limit handling. | Determines whether the target is investable and comparable. |
| First-pass factor evidence | IC/rank IC, quantile spread, monotonicity, horizon decay, turnover. | Prediction evidence only; not portfolio approval. |
| Portfolio evidence | Long leg, short leg, gross/net return, turnover, drawdown, benchmark-relative behavior. | Separates signal value from implementable PnL. |
| Costs and capacity | Commission, tax, spread, slippage, impact, ADV participation, borrow/shorting, capacity. | Can downgrade or reject significant but untradable signals. |
| Exposure and redundancy | Industry, size, beta, volatility, liquidity, value, profitability, investment, momentum, known-factor overlap. | Separates exposure harvest from residual alpha. |
| Decision grade | Usable evidence, needs rerun, research-only, implementation-risky, reject, or not auditable. | Feeds the run record and stage gate verdict. |

If a field is unavailable, record it as missing rather than assuming a favorable default. If timing, labels, universe, or tradability are not auditable, stop strategy promotion and mark the conclusion `not determinable` or `research-only`.

## External Research Protocol

Use external research when the answer depends on details not safely inferable from local context:

- Exact library/API behavior, parameter semantics, optimizer errors, version-specific changes, or package limitations.
- Exchange, regulator, index-vendor, broker, or data-vendor rules and field definitions.
- Original paper construction choices, canonical anomaly definitions, model formulas, or replication conventions.
- Error messages where local code inspection does not reveal the root cause.
- Market microstructure, transaction-cost, borrow, shorting, price-limit, suspension, or index-construction rules.

Process:

1. State the precise unknown before searching.
2. Check local code, installed package version, existing docs, and project conventions first.
3. Use Context7 or official documentation for libraries/frameworks when available.
4. Prefer original papers, exchange/regulator/index-vendor/data-vendor docs, release notes, and issue trackers over blogs.
5. Extract only the decision-relevant rule or API behavior.
6. Run a local fit check before changing code, construction, or interpretation.
7. If no authoritative source is found, mark the assumption as unverified instead of converting it into a rule.

## External Evidence Card

Use this card whenever external research affects construction, implementation, interpretation, or a stage verdict. Embed the card in [full-analysis-run-record.md](../core/full-analysis-run-record.md) for complete analysis records.

| Field | Record |
| --- | --- |
| `precise_unknown` | Exact API behavior, market rule, vendor field definition, paper construction detail, package limitation, or optimizer behavior being resolved. |
| `sources_checked` | Context7, official docs, source code, release notes, original paper, exchange/regulator/vendor docs, issue tracker, or other source type. |
| `authoritative_rule` | The decision-relevant rule or behavior found. |
| `local_fit_check` | How the rule fits local market, sample, timing, project version, schema, package version, and implementation assumptions. |
| `unresolved_assumption` | What remains unverified after the lookup. |
| `confidence` | High, medium, low, or not determinable. |
| `decision_impact` | How the evidence changes signal construction, data handling, code, interpretation, repair, or stage verdict. |

Do not cite external material as a rule until the local fit check passes. If the best source is a blog or forum, treat it as a lead and validate against a higher-priority source.

## Source Priority

1. Official documentation, Context7, local package docs, source code, and release notes for software behavior.
2. Original academic papers, author replication files, and widely used factor-library documentation for factor construction.
3. Exchanges, regulators, index vendors, brokers, and data vendors for market rules, field definitions, and investability constraints.
4. Maintainer issues, pull requests, migration guides, and changelogs for known bugs or behavior changes.
5. Blogs, forums, and secondary articles only as leads; validate them against higher-priority sources before use.

## Local Fit Check

Before applying an external solution, verify:

- Market: A-share versus US/global, mainland listing rules, ST/delisting flags, price limits, suspension treatment, and shorting feasibility.
- Sample: universe, period, frequency, rebalance calendar, benchmark, weighting, and liquidity filters.
- Timing: data availability, announcement lag, vendor update timestamp, execution delay, and forward-return window.
- Portfolio assumptions: long-only/long-short, leverage, borrow, transaction costs, capacity, turnover, and ADV participation.
- Statistical design: time split, purging/embargo, overlapping labels, Newey-West/HAC needs, multiple testing, and final-test isolation.
- Implementation: local package version, project API contracts, column names, schemas, precision, timezone/calendar conventions, and dependency constraints.

## Output Expectations

For data or externally researched answers, include these fields when they materially apply:

- Data diagnostics performed.
- External sources checked.
- Minimum diagnostic record or external evidence card when the task asks for a complete analysis record.
- Local validation of external solution.
- Unverified assumptions.
- Decision ledger snapshot when strategy construction or promotion is involved.
- Stage gate verdict when the answer implies continuation, promotion, paper trading, production, reduction, pause, or retirement.
- Decision grade and next evidence that would change it.
