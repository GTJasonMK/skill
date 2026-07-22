# Strategy Worked Examples

Use when: the user provides fields, schemas, artifacts, or vague observations and the agent needs examples for turning data shape into a first falsifiable factor-strategy entrypoint.

Purpose: teach the field-to-hypothesis move. Do not copy an example mechanically; use it to choose a method anchor, first baseline, likely loophole, and next decision.

## Contents

- [How to Use](#how-to-use)
- [Worked Examples](#worked-examples)
- [Example Selection Rules](#example-selection-rules)

## How to Use

For a new dataset or vague strategy request:

1. Match the available fields to one or two examples below.
2. Pick one primary method anchor from [method-idea-anchors.md](../methods/method-idea-anchors.md).
3. State the first hypothesis and the first result that would falsify it.
4. Build the simplest baseline before neutralization, ML, optimizer, or timing layers.
5. Record likely loopholes before interpreting a good result.

## Worked Examples

| Data shape | Method anchor | First hypothesis | First baseline and test | Likely loophole | Next decision |
| --- | --- | --- | --- | --- | --- |
| Daily price, volume, turnover, market cap, industry, and 20-day forward return. | Turnover/speculation, liquidity, reversal, or residual momentum. | Abnormally high turnover proxies speculation or attention, so future returns reverse after the crowded trade unwinds. | Rank abnormal turnover by date, test 20-day rank IC, quantile returns, short-horizon reversal, turnover decay, and long/short leg contribution. | Small-cap/liquidity contamination, short-leg-only result, high cost, price-limit/suspension effects. | If net long-only result fails, downgrade to risk-control or microstructure insight; if effect survives liquidity and cost checks, move to portfolio candidate tests. |
| Announcement date, ROE, BM, EP, analyst revision, industry, and forward return. | Expectation gap, profitability/value interaction, PEAD, or revision strategy. | High-quality cheap firms or positive revisions after announcements contain underreacted information. | Audit announcement/vendor availability, form value-quality or revision ranks after disclosure, test IC/quantiles by report age and event window. | Future financial data, restatement, value trap, analyst coverage bias, industry concentration. | If timing is valid and drift appears after disclosure, test incremental value beyond value, profitability, industry, and momentum. |
| Quarterly fundamentals without reliable announcement or vendor-availability timestamp. | Point-in-time panel as a prerequisite, not a factor anchor yet. | No investable alpha claim is valid until input observability is proven. | Compare fiscal period end, announcement date, update timestamp, rebalance date, and forward-return start; run no alpha test until timing is auditable. | Look-ahead bias from fiscal-period-end joins or restated fields. | Mark `not determinable`; request timestamps or rebuild the panel before strategy construction. |
| Existing factor panel with IC report, quantile returns, exposures, and turnover. | Single-factor validation, redundancy test, or exposure harvest. | The factor may rank returns, but investable value depends on monotonicity, exposure, cost, and incremental value. | Reproduce IC, quantiles, long/short split, turnover, cost sensitivity, known-factor attribution, and signal overlap against existing factors. | IC driven by one tail, known exposure, overfit construction, high turnover, no long-only value. | If it adds stable net value beyond exposures, keep as portfolio candidate; otherwise relabel as exposure/risk-control or reject. |
| Holdings, weights, optimizer output, expected alpha, risk model exposures, and constraints. | Portfolio optimization and risk-model compatibility. | The problem may be optimizer construction, not alpha discovery. | Check alpha scale, covariance stability, constraint satisfaction, exposure drift, turnover, active risk, and sensitivity to small alpha changes. | Forecast/risk scale mismatch, weak constraints, extreme weights, turnover/cost explosion. | Repair optimizer objective or constraints before changing signal; compare to equal-weight/top-bucket baseline. |
| Trades, fills, rejected orders, slippage, ADV, suspension, and limit-up/limit-down flags. | Execution, tradability, and implementation-shortfall repair. | Strategy decay may come from execution friction rather than alpha decay. | Compute fill rate, implementation shortfall, slippage by liquidity bucket, delay cost, ADV participation, rejected orders, and tradability flags. | Backtest assumes impossible prices or ignores price limits, suspensions, and liquidity. | Adjust execution rule, capacity cap, buffer, or rebalance frequency; downgrade if net value cannot survive feasible trading. |
| Backtest curve only, high Sharpe, current index constituents, and fundamentals. | Forensic audit before strategy design. | The result is more likely leakage or universe bias than deployable alpha. | Rebuild historical universe, point-in-time fundamentals, next-tradable execution, costs, suspension/limit handling, and subperiod/OOS checks. | Current-constituent bias, restated accounting, full-sample preprocessing, missing costs. | Give `reject` or `not determinable` until timing and universe are repaired; do not optimize the rule first. |
| XGBoost predictions, OOS `R^2`, IC, feature importance, and turnover. | ML forecast test and portfolio conversion gate. | Nonlinear features may improve ranking, but replacement needs net portfolio value beyond fair baselines. | Check purged walk-forward splits, fold-local preprocessing, simple linear/zero forecast baselines, OOS IC, turnover, costs, capacity, exposure overlap, and locked final test. | Leakage, weak baseline, hyperparameter overuse, feature importance without economic meaning, high turnover. | Hold unless net portfolio evidence improves after costs and exposures; promote only through stage gates. |
| News, sentiment, text, patent, geolocation, or web traffic timestamps with returns. | Alternative data, limited attention, sentiment, or information-timing anchor. | The alternative data may proxy information diffusion or investor attention before prices fully adjust. | Audit source timestamp and delivery lag, align to tradable execution, test incremental alpha beyond price, volume, fundamentals, industry, and known attention proxies. | Vendor backfill, short history, sample selection, multiple testing, unscalable data access. | If incremental effect is small or timing uncertain, keep research-only; if stable and tradable, test capacity, data freshness, and monitoring. |

## Example Selection Rules

- If timing is uncertain, choose the timing-audit example before any alpha example.
- If the artifact is already a portfolio, weights, or trades, diagnose portfolio/execution first before searching for new factors.
- If a result looks too strong, use forensic audit before optimization.
- If several examples apply, choose the one with the clearest first falsification and lowest data-timing risk.
- If no example fits, return to the core chain in [decision-core.md](../core/decision-core.md) and state the missing fields that block entrypoint selection.
