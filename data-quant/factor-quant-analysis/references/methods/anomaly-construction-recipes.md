# Anomaly Construction Recipes

Use when: constructing or auditing F-Score, G-Score, expectation gap, fundamental-anchored reversal, IVOL, or similar chapter-5 anomaly tests.
Read after: `task-router.md` selects named anomaly construction or single-factor validation needs a recipe.
Key decisions: point-in-time inputs, score definition, sorting grid, long/short leg, pricing alpha test, and tradability check.
Do not use for: broad factor mechanism diagnosis without `factor-mechanism-diagnostics.md`.

## Contents

- [Purpose](#purpose)
- [Common Setup](#common-setup)
- [F-Score](#f-score)
- [G-Score](#g-score)
- [Expectation Gap](#expectation-gap)
- [Fundamental-Anchored Reversal](#fundamental-anchored-reversal)
- [Idiosyncratic Volatility](#idiosyncratic-volatility)
- [Validation Pattern](#validation-pattern)
- [Implementation Red Flags](#implementation-red-flags)

## Purpose

Use this file when the user asks how to construct or test the chapter-5 anomalies: F-Score, G-Score, expectation gap, fundamental-anchored reversal, or idiosyncratic volatility.

This file gives implementable recipes. It does not reproduce exact return tables, t-statistics, or chart values. Use the original chapter summaries for exact source numbers.

## Common Setup

Use book-style A-share anomaly testing defaults unless the user's project specifies otherwise:

- Use point-in-time accounting data with announcement or vendor-availability timestamps.
- Use adjusted return series consistently with the project return convention.
- Remove or separately flag ST, delisting-risk, negative-net-asset, newly listed, suspended, and price-limit-constrained stocks according to the research design.
- Rebalance monthly unless the user asks to reproduce a different paper exactly.
- Report equal-weight and value-weight results when feasible.
- Test gross results first for signal diagnosis, then add tradability, turnover, cost, borrow, capacity, and price-limit constraints before claiming investability.
- Use CAPM, Fama-French-style factors, and a local A-share model such as Liu-Shi-Lian as baseline pricing models for anomaly alpha tests.

Do not treat a long-short anomaly as implementable in A shares without checking whether the short leg can actually be traded or whether the long leg alone retains value.

## F-Score

F-Score is a fundamental-quality score for distinguishing genuine value stocks from value traps.

### Inputs

Use point-in-time financial statements. Typical fields:

- Net income excluding minority interests.
- Total assets, preferably average total assets where the source definition requires it.
- Operating cash flow.
- Operating profit or earnings before accrual adjustment.
- Long-term debt or leverage-related fields.
- Current assets and current liabilities for current ratio.
- Equity issuance or seasoned offering indicator.
- Gross profit or gross margin.
- Revenue or asset turnover fields.

### Nine Signals

Score each item as `1` when the condition is true, otherwise `0`.

| Category | Signal | Book-style rule |
| --- | --- | --- |
| Profitability | `ROA` | `ROA > 0` |
| Profitability | `Delta ROA` | Latest `ROA` greater than same period last year |
| Profitability | `CFOA` | Operating cash flow / average total assets > 0 |
| Profitability | Accruals | Accruals < 0, meaning earnings quality is better |
| Leverage/liquidity | `Delta LEVER` | Long-term leverage decreases |
| Leverage/liquidity | `Delta LIQUID` | Current ratio improves |
| Leverage/liquidity | `EQ_OFFER` | No equity issuance in the past year |
| Operating efficiency | `Delta MARGIN` | Gross margin or asset gross-profitability improves |
| Operating efficiency | `Delta TURN` | Asset turnover improves |

Accruals can be implemented as:

```text
accruals = (operating_profit_TTM - operating_cash_flow_TTM) / average_total_assets
```

If the project uses net income rather than operating profit, state the variant.

### Score and Groups

```text
F_Score = sum(nine binary signals)
```

Use these groups when reproducing the chapter:

| Group | Score range | Interpretation |
| --- | --- | --- |
| Low | 0 to 3 | Weak fundamentals |
| Middle | 4 to 6 | Neutral fundamentals |
| High | 7 to 9 | Strong fundamentals |

### Use

- Combine with high `BM` to identify cheap stocks with improving fundamentals.
- Use as a fundamental expectation proxy in expectation-gap tests.
- Use as a fundamental anchor in reversal tests.

### Checks

- Verify all year-over-year and TTM inputs are available at rebalance time.
- Check whether score distribution is concentrated around 4-5; if groups are sparse, report counts.
- Inspect whether the score merely proxies size, industry, profitability, or financial distress.
- Test long side and short side separately.

## G-Score

G-Score is a growth-stock fundamental score. It is designed to separate high-quality growth firms from overvalued glamour stocks.

### Inputs

Use point-in-time accounting data and industry classifications:

- `ROA`
- Operating cash flow over assets (`CFOA`)
- Accrual quality
- R&D expense over assets
- Selling expense over assets
- Capital expenditure over assets
- Single-quarter `ROA` history
- Single-quarter revenue growth history

### Eight Signals

Score each item as `1` when true, otherwise `0`.

| Category | Signal | Book-style rule |
| --- | --- | --- |
| Profitability | `ROA` | Above industry median |
| Profitability | `CFOA` | Above industry median |
| Profitability | Accruals | `ROA - CFOA < 0` |
| Conservative accounting | R&D / assets | Above industry median |
| Conservative accounting | Selling expense / assets | Above industry median |
| Conservative accounting | Capex / assets | Above industry median |
| Stability | `ROA` variance | Below industry median using past three years of quarterly data |
| Stability | Revenue-growth variance | Below industry median using past three years of quarterly data |

Book-specific A-share adaptations:

- Use selling expense as a proxy for advertising expense when advertising expense is not consistently available.
- Quarterly cash-flow statement availability can be sparse before 2003; early-sample G-Score can be lower quality.
- Most G-Score items are compared against same-industry medians, unlike F-Score's mostly absolute thresholds.

### Score and Groups

```text
G_Score = sum(eight binary signals)
```

Original grouping:

| Group | Score range |
| --- | --- |
| Low | 0 to 1 |
| Middle | 2 to 5 |
| High | 6 to 8 |

A-share early-sample adjustment in the chapter:

- Before the stability variables have enough history, treat `2 to 4` as middle and `5 to 8` as high.
- After adequate quarterly history exists, use the original grouping.

### Use

- Apply especially inside low-`BM` or growth-stock universes.
- Avoid rejecting all expensive stocks mechanically; high G-Score can identify growth stocks with fundamentals that may justify valuation.
- Use equal-weight and value-weight tests separately because small-stock sensitivity can change the conclusion.

## Expectation Gap

Expectation-gap anomalies test whether market expectations and fundamental expectations are misaligned.

### Proxies

| Concept | Proxy |
| --- | --- |
| Market expectation | Valuation such as `BM` |
| Fundamental expectation | F-Score or another quality/fundamental score |
| Expectation gap | Valuation and fundamentals point in opposite directions |

In the chapter setup, high `BM` means low market expectation or cheap valuation. High F-Score means high fundamental expectation.

### Portfolio Grid

Construct a `3 x 3` independent double sort:

- Sort `BM` into low, middle, high.
- Sort F-Score into low, middle, high.

Expectation-gap portfolio:

```text
Expectation_Gap = High_BM & High_FScore - Low_BM & Low_FScore
```

Non-expectation-gap comparison:

```text
No_Expectation_Gap = High_BM & Low_FScore - Low_BM & High_FScore
```

Interpretation:

- `High_BM & High_FScore`: fundamentals are strong but market valuation is low; likely undervalued.
- `Low_BM & Low_FScore`: fundamentals are weak but market valuation is high; likely overvalued.
- If the expectation-gap mechanism is correct, the expectation-gap portfolio should outperform the simple high-minus-low `BM` value spread, and the no-gap portfolio should earn little or negative alpha.

### Tests

- Report raw spread and alpha under baseline pricing models.
- Compare against simple `High BM - Low BM`.
- Test whether future announcement-window returns or analyst revisions support the correction mechanism.
- Check whether results survive value-weighting and costs.

## Fundamental-Anchored Reversal

Fundamental-anchored reversal (FAR) refines short-term reversal by separating price moves with and without fundamental support.

### Intuition

Short-term losers can be good buys only when the price drop is not fully justified by deteriorating fundamentals. F-Score acts as the fundamental anchor.

### Construction

Use two sorting variables:

- Past one-month cumulative return, sorted into five groups:
  - `Loser`, `P2`, `P3`, `P4`, `Winner`
- F-Score, sorted into:
  - `Low` (`0-3`)
  - `Middle` (`4-6`)
  - `High` (`7-9`)

Run independent double sorting to obtain `5 x 3 = 15` portfolios.

Core portfolios:

```text
FAR = Loser/High - Winner/Low
FUR = Loser/Low - Winner/High
Reversal = Loser - Winner
```

Interpretation:

- `Loser/High`: price fell but fundamentals are strong; more likely underreaction, overreaction, or liquidity shock.
- `Winner/Low`: price rose but fundamentals are weak; more likely overpricing.
- `FUR` is the unfavorable reversal comparison because it buys weak-fundamental losers and shorts strong-fundamental winners.

### Tests

- Compare FAR with traditional one-month reversal.
- Report long side, short side, and long-short separately.
- Use CAPM, Fama-French-style, and local A-share model alphas.
- Check size exposure because reversal effects can be strongest in small stocks.
- Add turnover and cost sensitivity because short-horizon reversal can be expensive.

## Idiosyncratic Volatility

Idiosyncratic volatility (IVOL) tests whether stocks with high residual volatility earn lower future returns.

### IVOL Estimation

Book-style A-share construction:

1. Use past 21 trading days.
2. Regress daily stock excess returns on daily Fama-French-style factor returns:

```text
R_i,d^e = alpha_i
        + beta_i,MKT * R_MKT,d
        + beta_i,SMB * R_SMB,d
        + beta_i,HML * R_HML,d
        + epsilon_i,d
```

3. Define IVOL as the standard deviation of residuals:

```text
IVOL_i,t = std(epsilon_hat_i,d over past 21 trading days)
```

4. Apply minimum valid-trading-day rules before estimating.

### Mispricing Sort

To test the arbitrage-asymmetry mechanism, build a composite mispricing score from available anomaly variables.

The chapter's A-share implementation uses eight variables because some U.S. variables are not consistently available:

- Accruals.
- Net operating assets.
- Total asset growth.
- Investment to assets.
- O-Score.
- Momentum.
- Gross profitability.
- Return on assets.

If the project has net issuance, composite equity issuance, or distress data, record whether they are included.

### Conditional Double Sort

1. Sort composite mispricing into five groups:
   - Most undervalued, 2, 3, 4, most overvalued.
2. Within each mispricing group, sort IVOL into five groups.
3. Construct:

```text
Low_IVOL_Minus_High_IVOL = lowest_IVOL - highest_IVOL
```

4. Compare across mispricing groups.

Expected mechanism:

- The low-minus-high IVOL spread should be strongest among overvalued stocks if high IVOL and short-sale constraints prevent correction.
- Underpriced stocks need not show a symmetric positive IVOL premium.

### Tests

- Report raw return and alphas under multiple pricing models.
- Compare equal-weight and value-weight results.
- Control for size, beta, liquidity, turnover, price, and maximum daily return.
- Inspect whether the result is driven by high-IVOL short leg.
- Treat long-only implementation separately from long-short paper evidence.

## Validation Pattern

For each anomaly, return these items:

1. Definition and signal direction.
2. Required fields and point-in-time timestamps.
3. Universe and tradability filters.
4. Sorting or scoring recipe.
5. Portfolio construction and weighting.
6. Primary evidence: IC/rank IC, sorted returns, monotonicity, and alpha tests.
7. Mechanism tests: risk compensation, mispricing, or data snooping.
8. Robustness: subperiod, size bucket, industry, liquidity, value-weighting, and alternative definitions.
9. Implementation checks: turnover, costs, borrow, suspension, price limits, and capacity.
10. Verdict: reject, exploratory, research candidate, or implementation candidate.

## Implementation Red Flags

- Score components use fiscal period end instead of announcement or availability date.
- G-Score industry medians are computed using future constituents or full-sample industry mappings.
- F-Score or G-Score variables use later restatements before they were announced.
- FAR buys stocks that were limit-up or suspended at the execution date.
- IVOL uses zero-filled suspension returns.
- IVOL is estimated with too few valid daily returns.
- The anomaly looks strong only in equal-weight microcaps.
- The long-short spread is driven entirely by a non-tradable short leg.
- The user wants to search many score thresholds until one works.
