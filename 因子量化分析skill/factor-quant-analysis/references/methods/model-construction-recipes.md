# Model Construction Recipes

Use when: reproducing or adapting FF3, Carhart, Novy-Marx, FF5, HXZ/q, Stambaugh-Yuan, Daniel-Hirshleifer-Sun, or related model factors.
Read after: `task-router.md` selects multi-factor model reproduction or comparison.
Key decisions: universe, breakpoints, sorting variables, weighting, rebalance timing, and factor-return formula.
Do not use for: A-share empirical model ranking without `a-share-model-evidence.md`.

## Contents

- [Purpose](#purpose)
- [Common Construction Rules](#common-construction-rules)
- [Fama-French 3-Factor](#fama-french-3-factor)
- [Carhart 4-Factor](#carhart-4-factor)
- [Novy-Marx 4-Factor](#novy-marx-4-factor)
- [Fama-French 5-Factor](#fama-french-5-factor)
- [Hou-Xue-Zhang q-Factor and q5](#hou-xue-zhang-q-factor-and-q5)
- [Stambaugh-Yuan 4-Factor](#stambaugh-yuan-4-factor)
- [Daniel-Hirshleifer-Sun 3-Factor](#daniel-hirshleifer-sun-3-factor)
- [A-Share Adaptation Rules](#a-share-adaptation-rules)
- [Model Comparison Checklist](#model-comparison-checklist)

## Purpose

Use this file when the user asks how to construct, reproduce, adapt, or compare mainstream multi-factor model factors.

This file focuses on construction recipes and implementation warnings. Use [a-share-model-evidence.md](../models-factors/a-share-model-evidence.md) for CHN/LSL China factor evidence and EP/BM/ROE interpretation.

## Common Construction Rules

Most academic factor models follow a repeated pattern:

1. Define a universe and data availability rule.
2. Pick sorting variables such as market equity, `BM`, profitability, investment, momentum, or mispricing scores.
3. Choose breakpoints from a reference exchange or universe.
4. Form portfolios by independent sorting.
5. Compute portfolio returns, usually value-weighted for mainstream academic model factors.
6. Construct factor returns as simple averages of long-leg portfolios minus simple averages of short-leg portfolios.
7. Rebalance at the frequency implied by the signal's data update cycle.

Implementation rules:

- State whether breakpoints come from the full universe, NYSE-like large exchange subset, CSI constituents, or the project's investment universe.
- State whether portfolio returns are equal-weight or value-weight.
- State whether accounting variables use annual, quarterly, TTM, or point-in-time restated data.
- Do not mix model factors and prediction variables without naming the object being estimated.
- Do not compare models only by in-sample alpha reduction; include parsimony and economic meaning.

## Fama-French 3-Factor

Factors:

- Market excess return.
- `SMB`: small minus big.
- `HML`: high book-to-market minus low book-to-market.

Classic construction:

1. At each annual formation date, sort stocks into size groups:
   - `S`: small.
   - `B`: big.
2. Sort stocks into `BM` groups:
   - `L`: low `BM`.
   - `M`: middle `BM`.
   - `H`: high `BM`.
3. Use a `2 x 3` independent double sort to form six value-weighted portfolios:

```text
S/H, S/M, S/L, B/H, B/M, B/L
```

Factor formulas:

```text
SMB = (S/H + S/M + S/L)/3 - (B/H + B/M + B/L)/3
HML = (S/H + B/H)/2       - (S/L + B/L)/2
```

Notes:

- In U.S. implementations, June formation and prior fiscal-year accounting data avoid look-ahead bias.
- `HML` captures value using `BM`, not `EP`.
- `SMB` in FF3 is constructed only from size spreads within the `BM` sort.

Use:

- Baseline model for market, size, and value exposure.
- Common benchmark for anomaly alpha tests.

Warning:

- CAPM or FF3 alpha is not proof of investable alpha; missing profitability, investment, momentum, liquidity, and local factors can matter.

## Carhart 4-Factor

Factors:

- Market.
- `SMB`.
- `HML`.
- Momentum, often called `MOM`, `UMD`, or winners-minus-losers.

Momentum construction:

1. At month `t`, compute cumulative return from `t-12` to `t-1`.
2. Skip the most recent month to reduce short-term reversal contamination.
3. Sort stocks into winners and losers, commonly top and bottom 30%.
4. Construct momentum as winners minus losers.

Book-specific caution:

- Carhart momentum is an exception among many model factors because the long and short legs can be equal-weighted in the original style, while other mainstream factors are often value-weighted sorted portfolios.

Use:

- Fund performance attribution.
- Style analysis when return continuation exposure matters.
- Baseline when testing momentum-like anomalies.

Warning:

- In A shares, short-term reversal, price limits, and retail speculation can weaken traditional momentum.
- Including the most recent month can turn a momentum test into a reversal-contaminated signal.

## Novy-Marx 4-Factor

Factors:

- Market.
- Value.
- Momentum.
- Profitability, often `PMU`: profitable minus unprofitable.

Profitability variable:

- Gross profitability is preferred because it is closer to production ability and less affected by lower-income-statement accounting noise.
- R&D and advertising can depress net income while supporting future profitability; gross profitability avoids some of this distortion.

Profitability construction:

1. Sort by size into `S` and `B`.
2. Sort by profitability into:
   - `P`: profitable.
   - `N`: neutral.
   - `U`: unprofitable.
3. Form six portfolios:

```text
S/P, S/N, S/U, B/P, B/N, B/U
```

Formula:

```text
PMU = (S/P + B/P)/2 - (S/U + B/U)/2
```

Chapter warning:

- Novy-Marx's profitability factor can include industry-neutral construction, such as doing long a stock and shorting its industry index to reduce industry exposure.

Use:

- Explain profitability and quality-related returns.
- Test whether value-like alpha is really profitability exposure.

## Fama-French 5-Factor

Factors:

- Market.
- `SMB`.
- `HML`.
- `RMW`: robust minus weak profitability.
- `CMA`: conservative minus aggressive investment.

Theory:

- Valuation identities imply higher expected returns for high `BM`, high expected profitability, and conservative investment, holding other terms fixed.

Profitability factor:

```text
RMW = (S/R + B/R)/2 - (S/W + B/W)/2
```

where:

- `R`: robust profitability.
- `N`: neutral profitability.
- `W`: weak profitability.

Investment factor:

```text
CMA = (S/C + B/C)/2 - (S/A + B/A)/2
```

where:

- `C`: conservative investment.
- `N`: neutral investment.
- `A`: aggressive investment.

FF5 size factor:

```text
SMB = (SMB_BM + SMB_PROF + SMB_INV)/3
```

with:

```text
SMB_BM   = (S/H + S/M + S/L)/3 - (B/H + B/M + B/L)/3
SMB_PROF = (S/R + S/N + S/W)/3 - (B/R + B/N + B/W)/3
SMB_INV  = (S/C + S/N + S/A)/3 - (B/C + B/N + B/A)/3
```

Use:

- Baseline model when profitability and investment are central to the claim.

Warning:

- `HML` can appear redundant after adding profitability and investment in some samples.
- Investment factor transferability to A shares can be weak and construction-sensitive.

## Hou-Xue-Zhang q-Factor and q5

Factors:

- Market.
- Size, often `ME`.
- Investment, often `I/A`.
- Profitability, often `ROE`.
- q5 adds expected investment growth.

Theory:

- Investment-based asset pricing starts from the firm's investment first-order condition.
- Intuition:

```text
expected stock return rises with expected profitability
expected stock return falls with investment, holding profitability fixed
```

Basic q-factor construction:

1. Sort by size into `S` and `B`.
2. Sort by profitability into high, middle, low.
3. Sort by investment into high, middle, low.
4. Use a `2 x 3 x 3` independent sort to form 18 value-weighted portfolios.

Let each portfolio be named by:

```text
size/profitability/investment
```

Size factor:

```text
ME = average(9 small portfolios) - average(9 big portfolios)
```

Profitability factor:

```text
ROE = average(6 high-profitability portfolios)
    - average(6 low-profitability portfolios)
```

Investment factor:

```text
I/A = average(6 low-investment portfolios)
    - average(6 high-investment portfolios)
```

q5:

- Adds an expected growth or expected investment growth factor.
- The added prediction model increases estimation risk and should be audited more strictly.

Use:

- Strong benchmark for profitability and investment explanations.
- Useful when comparing value-investing strategies against investment-based asset pricing.

Warning:

- q theory and FF5 both use investment-like variables, but the theoretical motivation differs.
- Expected growth factors can become black boxes if the forecasting model is not transparent.

## Stambaugh-Yuan 4-Factor

Factors:

- Market.
- Size.
- `MGMT`: management-related mispricing.
- `PERF`: performance-related mispricing.

Idea:

- Group multiple anomaly variables into broader mispricing factors.
- Use averaged ranks to reduce single-anomaly noise.

Mispricing variables:

| Group | Variables |
| --- | --- |
| Management | Net stock issues, composite equity issuance, accruals, net operating assets, asset growth, investment to assets |
| Performance | Distress, O-Score, momentum, gross profitability, return on assets |

Ranking rule:

- If a variable is negatively related to expected returns, high raw values indicate overpricing.
- If a variable is positively related to expected returns, low raw values indicate overpricing.
- Convert every variable so that a higher mispricing rank means more overvalued and lower expected return.

Group scores:

```text
MGMT_score = average rank of 6 management anomalies
PERF_score = average rank of 5 performance anomalies
```

Factor construction:

1. Sort stocks by size into `S` and `B`.
2. Sort `MGMT_score` or `PERF_score` into low, middle, high mispricing groups.
3. Low score means more undervalued; high score means more overvalued.

Book-style breakpoints:

- Size uses a large-exchange-style median in the original U.S. setup.
- MGMT and PERF use 20% and 80% breakpoints across NYSE, AMEX, and NASDAQ, not the usual NYSE 30% and 70%.
- When adapting to A shares, explicitly state whether these become full-universe 20/80, investable-universe 20/80, or a China-specific large-cap reference universe.

Management factor:

```text
MGMT = (S/L + B/L)/2 - (S/H + B/H)/2
```

Performance factor:

```text
PERF = (S/L + B/L)/2 - (S/H + B/H)/2
```

Special size construction:

- Construct size twice: once from the size x MGMT grid and once from the size x PERF grid.
- Use only the middle mispricing groups:

```text
SMB_MGMT = S/M_MGMT - B/M_MGMT
SMB_PERF = S/M_PERF - B/M_PERF
SMB_SY   = (SMB_MGMT + SMB_PERF) / 2
```

- This avoids using highly overvalued or undervalued stocks in the size factor and reduces mispricing contamination.

Warning:

- Averaging many anomalies helps explain more test assets but raises overfit risk.
- Results can be sensitive to the 20/80 versus 30/70 breakpoint choice and the universe used for breakpoints.
- The special size factor is not interchangeable with FF-style SMB; it is a model-specific construction.

## Daniel-Hirshleifer-Sun 3-Factor

Factors:

- Market.
- `FIN`: long-horizon financing behavior factor.
- `PEAD`: short-horizon post-earnings-announcement drift factor.

Behavioral idea:

- Long-horizon anomalies often reflect overconfidence and slow correction around financing decisions.
- Short-horizon anomalies often reflect limited attention and underreaction to earnings news.

### FIN

Inputs:

- Composite share issuance (`CSI`) over a multi-year horizon.
- Net share issuance (`NSI`) over a shorter horizon.

Logic:

- Managers issue equity when they believe shares are overpriced.
- Managers repurchase when they believe shares are underpriced.
- Investors underreact to financing decisions.

Grouping:

- Low `FIN` represents undervalued or repurchase-like firms.
- High `FIN` represents overvalued or issuance-like firms.

Book-style component grouping:

- `CSI`: sort by 20% and 80% breakpoints into low, middle, high issuance.
- `NSI`: split firms into net-repurchase and net-issuance groups before ranking.
- For net-repurchase firms, use the median repurchase amount to distinguish stronger versus weaker repurchase behavior.
- For net-issuance firms, use 30% and 70% breakpoints to distinguish low, middle, and high issuance.
- Map strong repurchase-like firms to low `NSI` and high-issuance firms to high `NSI`.

Book-style FIN group rule:

| Condition | FIN group | Interpretation |
| --- | --- | --- |
| `CSI` high and `NSI` high | High | Overpriced or issuance-like |
| One of `CSI` or `NSI` high and the other missing | High | Treat available issuance evidence as sufficient |
| `CSI` low and `NSI` low | Low | Underpriced or repurchase-like |
| One of `CSI` or `NSI` low and the other missing | Low | Treat available repurchase evidence as sufficient |
| Other combinations | Middle | Mixed or weak financing signal |

Formula:

```text
FIN = (S/L + B/L)/2 - (S/H + B/H)/2
```

Implementation warnings:

- Financing variables move slowly; FIN is a long-horizon factor and should not be evaluated only over one-month reversals.
- The NSI grouping is intentionally asymmetric and can look overfit; preserve it only when reproducing the original DHS recipe.
- For new strategy design, test simpler issuance/repurchase variants against this recipe rather than assuming the complex grouping is superior.

### PEAD

Input:

- Announcement-window cumulative abnormal return around the latest earnings announcement.

Book-style window:

```text
CAR_i = sum_{d=-2}^{1} (R_i,d - R_M,d)
```

Construction:

1. Sort stocks by size into `S` and `B`.
2. Sort announcement-window `CAR` into low, middle, high.
3. High `CAR` indicates positive earnings news and underreaction.

Formula:

```text
PEAD = (S/H + B/H)/2 - (S/L + B/L)/2
```

Use:

- Behavioral model comparison.
- Explanations of financing and earnings-announcement anomalies.

Warning:

- Earnings announcement dates and returns must be point-in-time and tradeable after the announcement window.
- Announcement clustering, Friday announcements, and attention variables can change PEAD strength.

## A-Share Adaptation Rules

When adapting U.S. model recipes to A shares:

- Recheck reporting dates, quarter availability, and restatement rules.
- Decide whether to use annual data, quarterly data, or TTM variables.
- Recheck breakpoints because NYSE-style breakpoints may not have a direct A-share analogue.
- State whether financial firms are included.
- Handle ST stocks, price limits, suspensions, shell-value concerns, and short-sale limits.
- Report whether the smallest stocks are excluded; this can materially change size, value, and profitability evidence.
- Compare equal-weight and value-weight versions when translating academic evidence into implementable signals.

## Model Comparison Checklist

When answering which model is better, report:

1. Construction differences and data timing.
2. Factor return means and t-statistics.
3. Factor correlations.
4. Test assets or anomaly portfolios used.
5. Time-series alpha tests.
6. GRS or spanning tests when appropriate.
7. Sample-window sensitivity.
8. Parsimony and economic meaning.
9. Implementation relevance if the user is building a strategy.

Do not declare a model superior only because it has higher in-sample explanatory power or more factors.
