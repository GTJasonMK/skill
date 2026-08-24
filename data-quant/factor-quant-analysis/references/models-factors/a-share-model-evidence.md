# A-Share Model Evidence

Use when: interpreting A-share priced factors, Liu-Shi-Lian/CHN models, EP versus BM, ROE relations, anomaly test assets, alpha/GRS comparison, or parsimony.
Read after: `task-router.md` selects A-share model evidence or multi-factor model comparison.
Key decisions: A-share construction convention, priced factor interpretation, model comparison metric, and whether a more complex model is justified.
Do not use for: exact empirical table values or general econometric derivations.

## Contents

- [Purpose](#purpose)
- [A-Share Fama-MacBeth Setup](#a-share-fama-macbeth-setup)
- [Priced Factors in A Shares](#priced-factors-in-a-shares)
- [Liu-Shi-Lian China Models](#liu-shi-lian-china-models)
- [CHN Factors](#chn-factors)
- [LSL Factors](#lsl-factors)
- [EP, BM, and ROE](#ep-bm-and-roe)
- [Factor Correlation Lessons](#factor-correlation-lessons)
- [Anomaly Test Assets](#anomaly-test-assets)
- [Alpha and GRS Comparison](#alpha-and-grs-comparison)
- [Parsimony](#parsimony)
- [Black CAPM, Low Beta, and Abnormal Turnover](#black-capm-low-beta-and-abnormal-turnover)
- [How to Answer A-Share Model Questions](#how-to-answer-a-share-model-questions)

## Purpose

Use this file when the user asks about A-share multi-factor model evidence, Liu et al. China factors, CHN/LSL notation, EP versus BM, or why a model that looks stronger in one test may not be economically better.

This file compresses chapter-4 evidence. It is not a replacement for rerunning the tests; it provides the empirical interpretation and construction conventions needed to reason about the chapter.

## A-Share Fama-MacBeth Setup

Book-style Fama-MacBeth setup:

- Use firm characteristics as factor exposures for size, value, momentum, profitability, investment, and turnover.
- Use rolling 252 trading-day time-series regression to estimate market beta.
- At month `t`, use current observable characteristics to explain stock returns in month `t+1`.
- Run one cross-sectional regression per month.
- Average monthly factor premia and compute Newey-West adjusted t-statistics.
- Include an intercept to reduce model-misspecification contamination.
- Winsorize factor exposures but do not standardize them in the chapter's main table.

Because exposures are not standardized, raw factor premia are not directly comparable across factors. Use the impact coefficient:

```text
impact = factor premium * cross-sectional standard deviation of exposure
```

Interpretation:

- It estimates the return change associated with a one-standard-deviation increase in exposure.
- It lets users compare economic magnitude across variables measured in different units.

## Priced Factors in A Shares

Chapter-4 Fama-MacBeth evidence identifies these as priced under the book's setup:

| Factor | Exposure | Sign | Evidence |
| --- | --- | --- | --- |
| Size | log market cap | Negative | Small-cap effect; large caps earn lower future returns. |
| Value | BM | Positive | High book-to-market earns higher future returns. |
| Profitability | ROE(TTM) | Positive | Higher profitability earns higher future returns. |
| Abnormal turnover | Abnormal turnover | Negative | High speculative turnover predicts lower future returns. |

Weak or insignificant in the same setup:

- Market beta: not significantly priced and can be negative, consistent with Black-CAPM-style concerns.
- Momentum: positive but weak, consistent with A-share short-term reversal and speculative trading.
- Investment: weak and can have the opposite sign from U.S. q-theory evidence depending on construction.

Practical conclusion:

- For A-share equity factors, size, value, profitability, and abnormal turnover deserve default inclusion in research baselines.
- Do not assume U.S. momentum or investment evidence transfers mechanically.

## Liu-Shi-Lian China Models

Liu et al. (2019) address China-specific issues:

- A-share shell-value contamination (壳价值污染): very small listed firms can carry shell value unrelated to fundamentals.
- The shell-value channel is tied to historical IPO constraints and reverse-merger demand (借壳上市): some firms acquired small listed shells to obtain listing status.
- To reduce this effect, the original design often excludes the smallest 30% by market cap (剔除市值最低的 30% 股票).
- The China three-factor model uses market, size, and EP-based value.
- A four-factor extension adds profitability through ROE while using BM for value.

Key warning:

- Excluding the smallest 30% is not a neutral technical filter. It changes the strength of size, value, and profitability evidence.
- In A shares, this filter can weaken BM evidence in the smallest stocks while making ROE and EP look stronger in the remaining universe.
- Results should report both full-universe and ex-smallest-30% variants when comparing A-share models.

## CHN Factors

CHN denotes factors in the Liu et al. China three-factor style.

Construction:

- Sort stocks into small `S` and big `B` by market cap median.
- Sort stocks into value `V`, middle `M`, and growth `G` by EP 30% and 70% breakpoints.
- Form six value-weighted portfolios.

Size:

```text
CHN-SMB = (S/V + S/M + S/G)/3 - (B/V + B/M + B/G)/3
```

Value:

```text
CHN-VMG = (S/V + B/V)/2 - (S/G + B/G)/2
```

Interpretation:

- `CHN-SMB` captures the small-minus-big return in the EP-sorted China setup.
- `CHN-VMG` captures value-minus-growth using EP rather than BM.
- `VMG` is not a pure BM value factor because EP embeds profitability through `EP = BM * ROE`.

## LSL Factors

LSL denotes the Liu-Shi-Lian four-factor style using BM and ROE separately.

Value sort:

- Sort on BM into high `H`, middle `M`, low `L`.

```text
LSL-HML = (S/H + B/H)/2 - (S/L + B/L)/2
```

Profitability sort:

- Sort on ROE(TTM) into robust `R`, neutral `N`, weak `W`.

```text
LSL-RMW = (S/R + B/R)/2 - (S/W + B/W)/2
```

Size:

```text
LSL-SMB = (SMB_BM + SMB_ROE)/2
SMB_BM  = (S/H + S/M + S/L)/3 - (B/H + B/M + B/L)/3
SMB_ROE = (S/R + S/N + S/W)/3 - (B/R + B/N + B/W)/3
```

Interpretation:

- `LSL-HML` is closer to a pure BM value factor than `CHN-VMG`.
- `LSL-RMW` isolates profitability better than EP-based value.
- `LSL-SMB` can differ from `CHN-SMB` because it averages size spreads across BM and ROE sorts rather than EP sorts.

## EP, BM, and ROE

Core identity:

```text
EP = BM * ROE
```

This explains much of the chapter's A-share model comparison.

Economic logic:

- Higher BM can imply higher expected return when other valuation components are held fixed.
- Higher expected ROE can imply higher expected return when price-to-book and investment expectations are held fixed.
- Historical ROE can proxy expected ROE, though this is an empirical approximation.
- EP mixes valuation and profitability.

Why EP can look strong:

- In small stocks, BM effects can be distorted by shell value.
- After excluding the smallest 30%, profitability and EP can become stronger.
- EP-based value loads on both BM and ROE, so it can perform like a combined value-profitability factor.

Why EP is not automatically better:

- It is less interpretable as a pure value factor.
- It can double-count profitability if ROE is also added.
- It can make model comparison look better by blending dimensions rather than clarifying economic drivers.

Answering rule:

- If the user asks "BM or EP?", say it depends on objective.
- Use BM for cleaner value interpretation.
- Use EP cautiously when the goal is empirical prediction and its profitability exposure is acceptable.
- Use BM plus ROE when separating value and profitability is important.

## Factor Correlation Lessons

Empirical lessons from the chapter:

- `CHN-SMB` and `LSL-SMB` are highly correlated, but their average returns can differ.
- `CHN-VMG` and `LSL-RMW` are highly correlated because EP embeds ROE.
- `LSL-HML` and `LSL-RMW` can be nearly uncorrelated, making them cleaner separate dimensions.
- Excluding the smallest 30% weakens size factors and can strengthen profitability.
- A factor's performance can vary sharply across decades.

Regime lesson:

- In the first decade, BM-based value was strong and profitability was weak.
- In the second decade, profitability became stronger and BM-based value weakened.
- EP-based `CHN-VMG` stayed more stable because it loaded on both value and profitability.

Practical warning:

- GRS outcomes can be driven by these changing factor correlations and regime-specific factor returns.
- Do not summarize a model as "wins" only because it explains another model's factors in one window.

## Anomaly Test Assets

Chapter-4 model comparison uses anomaly long-short portfolios as test assets.

Examples:

| Anomaly | Definition |
| --- | --- |
| Price-to-cash-flow | Price divided by per-share cash flow |
| Net operating assets | `(shareholder equity + financial liabilities - financial assets) / total assets` |
| Total asset growth / 总资产增长率 | Year-over-year total asset growth from annual reports |
| Accruals | Operating profit minus operating cash flow, scaled by average total assets |
| MAX | Average of top 5 daily returns in the past 21 trading days |
| One-month volatility | Standard deviation of daily returns in the past 21 trading days |
| One-month abnormal turnover / 1 个月异常换手率 | 21-day average turnover divided by 252-day average turnover |
| Twelve-month turnover | Average daily turnover over the past 252 trading days |
| Illiquidity | Amihud-style illiquidity over the past 21 trading days |
| Reversal / 短期反转 | Past 21-day cumulative return |

Testing approach:

- Build anomaly long-short portfolios with single sorting.
- Regress anomaly returns on candidate model factors.
- Use full-sample regression and rolling 60-month regression as complementary views.
- Report alpha, Newey-West t-statistics, average absolute alpha, and average absolute t-statistics.

## Alpha and GRS Comparison

Alpha-test lesson:

- Both CHN three-factor and LSL four-factor variants explain many anomalies.
- Differences are often small.
- Abnormal turnover and illiquidity can remain difficult to explain.
- Rolling-window results can differ from full-sample results.

GRS-test lesson:

- Use non-market style factors from one model as test assets against the other model.
- Test multiple windows: first decade, second decade, full sample, and original-paper period if relevant.
- Full-sample conclusions can change when the smallest 30% stocks are excluded.

Interpretation:

- A rejected GRS test means the model fails to jointly explain the test assets.
- It does not automatically prove the alternative model is economically better.
- Time-window sensitivity is itself evidence that model comparison is fragile.

Report model comparison with:

1. Construction differences.
2. Factor return means and t-statistics.
3. Factor correlations.
4. Alpha-test results on anomalies.
5. GRS tests across windows.
6. Economic interpretation and parsimony.

## Parsimony

Parsimony means a model should explain returns with as few economically meaningful factors as possible.

Why it matters:

- Adding more factors mechanically reduces in-sample alpha.
- More construction variables increase model complexity and overfit risk.
- A complex model is harder to interpret, implement, and validate out of sample.

Parsimony-index idea:

- Penalize number of factors and number of variables used to construct factors.
- Count repeated variable usage when the same variable enters multiple factor constructions.

Parsimony Index I:

```text
Parsimony_I = 0 - sum(number of variables used by each factor)
```

Rules:

- The index is non-positive; closer to zero means simpler.
- Count the same variable repeatedly if it is used to construct multiple factors.
- The market factor usually contributes zero construction variables.

Parsimony Index II:

```text
Parsimony_II = 0 - number_of_factors - number_of_unique_construction_variables
```

Rules:

- The index is also non-positive.
- Count each construction variable only once.
- It penalizes both the number of factors and the breadth of the variable library.

Book-style parsimony table:

| Model | Short name | Parsimony I | Parsimony II |
| --- | --- | ---: | ---: |
| Fama-French 3-factor | FF3 | -4 | -5 |
| Carhart 4-factor | C4 | -6 | -7 |
| Novy-Marx 4-factor | NM4 | -9 | -9 |
| Fama-French 5-factor | FF5 | -10 | -9 |
| Hou-Xue-Zhang 4-factor | HXZ4 | -9 | -7 |
| Stambaugh-Yuan 4-factor | SY4 | -25 | -16 |
| Daniel-Hirshleifer-Sun 3-factor | BF3/DHS3 | -4 | -6 |

Interpretation:

- SY4 can explain many anomalies partly because it embeds a large anomaly library.
- A lower index can be acceptable only when the added factors have strong economic meaning and sample-out evidence.
- Do not call a model better only because it leaves fewer significant in-sample anomalies.

Use parsimony to challenge:

- Factor models built mainly by anomaly-mining.
- Models that explain many test assets but have weak economic logic.
- Models whose extra factors are highly correlated with existing factors.

## Black CAPM, Low Beta, and Abnormal Turnover

Black CAPM is useful when explaining why market beta can be weak in A-share cross-sectional tests.

Core lesson:

- Traditional Sharpe-Lintner CAPM assumes borrowing and lending at the risk-free rate.
- Black CAPM relaxes that assumption and introduces a zero-beta portfolio.
- The extra zero-beta term can make the expected-return-versus-beta relation flatter than the traditional CAPM line.
- Empirically, high-beta portfolios often fail to earn enough return; this is the background for low-beta and BAB-style anomalies.

Use this carefully:

- CAPM failure does not prove every low-beta strategy is investable.
- Test whether low-beta returns survive size, volatility, liquidity, leverage, and industry controls.
- For A shares, check price limits, speculative demand, and short-sale constraints before interpreting beta evidence.

Abnormal turnover (异常换手率):

```text
abnormal_turnover_t =
    average_daily_turnover_past_21_trading_days
    / average_daily_turnover_past_252_trading_days
```

Interpretation:

- High abnormal turnover can indicate speculative demand, disagreement, attention, or optimistic trading pressure.
- In the chapter's A-share evidence, high abnormal turnover predicts lower future returns.
- Long-short paper returns can be driven heavily by the high-turnover short leg.
- When reproducing the book-style A-share variable, state whether turnover is based on free-float shares or total shares; the chapter's construction uses a free-float-share denominator.
- A/B-share evidence is useful background: speculative demand can raise A-share turnover and relative prices without improving fundamentals.

Implementation rule:

- For long-only A-share use, test the low-abnormal-turnover long leg separately.
- For long-short claims, check borrow, shorting feasibility, price-limit execution, turnover, and market impact.

## How to Answer A-Share Model Questions

For "which factors are priced in A shares?":

- Start with size, value, profitability, and abnormal turnover as book-supported evidence.
- Mention weak market beta, weak momentum, and weak investment under the chapter's setup.
- State that evidence depends on universe, period, weighting, and controls.

For "why does A-share momentum look weak?":

- Mention short-term reversal, retail trading, price limits, speculative turnover, and weak continuation after excluding recent reversal effects.
- Use factor-and-model catalog for the broader momentum card.

For "why use EP in China models?":

- Explain shell-value concern and the empirical strength of EP after small-stock exclusion.
- Then explain `EP = BM * ROE` and the loss of pure interpretation.

For "CHN versus LSL which is better?":

- Do not give a one-word answer.
- Compare construction, sample window, small-stock exclusion, alpha tests, GRS tests, correlations, and economic meaning.
- State that the chapter's evidence shows close competition and substantial window sensitivity.
