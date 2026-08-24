# Factor and Model Catalog

## Contents

- [A-Share Empirical Defaults](#a-share-empirical-defaults)
- [Main Factor Families](#main-factor-families)
- [Mainstream Multi-Factor Models](#mainstream-multi-factor-models)
- [A-Share Model Evidence](#a-share-model-evidence)
- [Anomaly Templates](#anomaly-templates)
- [Catalog Card Format](#catalog-card-format)

## A-Share Empirical Defaults

Use these defaults when summarizing book-style A-share evidence:

- Use point-in-time financial data and report availability.
- Adjust prices for corporate actions.
- Treat long suspensions, stale prices, and reopening outliers explicitly.
- Apply minimum trading-day/listing-age filters for price-derived signals.
- Decide whether financial firms are excluded for accounting comparability.
- Remove ST, delisting-warning, negative-net-asset, or mandate-ineligible names when the research design requires it.
- For academic factor evidence, report both equal-weight and value-weight sorted portfolios where feasible.
- For implementation, add tradability, cost, capacity, price-limit, and suspension checks.

## Main Factor Families

### Market

- Variable/exposure: market beta or market excess return.
- Theory: CAPM says expected excess return is proportional to market beta.
- Empirical lesson: market factor often explains time-series return variation better than cross-sectional expected returns.
- Common misuse: treating CAPM failure as proof that any anomaly is investable.

### Size

- Variable: market capitalization or log market capitalization.
- Direction: smaller stocks often earn higher average returns.
- Mechanisms: liquidity, distress, retail attention, limits to arbitrage, or omitted risks.
- A-share caution: equal-weight results can be dominated by small-cap effects; value-weight evidence is more scalable.

### Value

- Variables: BM, EP, CF/P, dividend yield.
- Direction: cheaper stocks may earn higher future returns.
- Mechanisms: distress/risk compensation, investor overreaction, expectation errors, or fundamental misvaluation.
- A-share notes: BM and EP are not identical; BM with size double sorting helps separate value from size.
- Common misuse: treating every cheap stock as a value opportunity; value traps require quality/fundamental screens.

### Momentum

- Variable: cumulative return from `t-12` to `t-1`, often skipping the most recent month.
- Direction: past winners continue relative outperformance.
- Mechanisms: underreaction, delayed information diffusion, or risk.
- A-share notes: short-term reversal and speculative trading can weaken traditional momentum evidence.
- Common misuse: including the most recent month without checking reversal contamination.

### Profitability and Quality

- Variables: ROE, ROA, gross profitability (`GP`), operating profitability, ROTC, ROIC, RNOA, cash-flow quality, accrual quality, stability, leverage, growth, SUE, earnings trend, and earnings acceleration.
- Direction: more profitable or higher-quality firms may earn higher returns.
- Mechanisms: valuation identities, expected profitability, quality mispricing, and conservative accounting distortions.
- A-share notes: accounting definitions, quarterly timing, and TTM construction matter heavily. Book-style `ROE(TTM)` uses latest 12-month operating profit over average shareholder equity across the latest four report periods.
- Diagnostic warning: separate profitability level, quality, stability, and growth before deciding a quality factor has worked or failed. Control size because low-profitability A-share stocks can have positive small-cap exposure.

### Investment

- Variables: asset growth, investment-to-assets, capital expenditure, accruals, net operating asset growth.
- Direction: conservative investment often predicts higher returns than aggressive investment.
- Theory: q-theory and valuation identities.
- A-share notes: investment factor can be weak or insignificant depending on construction and sample; do not assume U.S. evidence transfers mechanically.

### Turnover, Liquidity, and Speculation

- Variables: turnover, volume, Amihud illiquidity, abnormal turnover.
- Direction: effects differ by market and definition; high turnover can represent speculation and low future returns.
- A-share notes: retail trading and price limits make turnover/liquidity variables especially important.
- Implementation issue: illiquidity premia can be hard to capture after market impact.

### Volatility and Beta

- Variables: total volatility, idiosyncratic volatility, residual volatility, beta.
- Direction: low-volatility or low-IVOL stocks often earn higher risk-adjusted returns.
- Mechanisms: leverage constraints, lottery demand, short-sale limits, and omitted risk.
- A-share notes: speculative demand and shorting constraints can strengthen low-IVOL effects.

## Mainstream Multi-Factor Models

### Fama-French 3-Factor

- Factors: market, SMB, HML.
- Construction: `2 x 3` size and BM sorting; SMB captures small-minus-big, HML high-BM-minus-low-BM.
- Use: baseline model for size and value effects.
- Limitation: does not explain momentum, profitability, investment, and many anomalies.

### Carhart 4-Factor

- Factors: market, SMB, HML, momentum.
- Momentum usually uses past `t-12` to `t-1` returns to reduce short-term reversal contamination.
- Use: fund performance and style analysis where momentum exposure matters.

### Novy-Marx 4-Factor

- Factors: market, value, momentum, profitability.
- Profitability often uses gross profitability because it is closer to core production ability and less affected by lower-income-statement noise.
- Use: explaining quality/profitability-related returns.

### Fama-French 5-Factor

- Factors: market, SMB, HML, RMW, CMA.
- Theory: valuation identities imply expected returns are higher for high BM, high expected profitability, and conservative investment, holding other terms fixed.
- Construction note: SMB is averaged across size spreads from value, profitability, and investment sorts.
- Limitation: HML can appear redundant in some samples, and investment/profitability definitions matter.

### Hou-Xue-Zhang q-Factor and q5

- q-factor: market, size, investment, ROE.
- q5 adds expected investment growth.
- Theory: investment-based asset pricing; firms invest more when expected profitability is high and cost of capital is low.
- Use: strong benchmark for profitability/investment explanations and value-investing strategy attribution.

### Stambaugh-Yuan

- Factors: market, size, management, performance.
- Idea: group anomalies connected to mispricing into broader management and performance factors.
- Use: behavioral/mispricing model comparison.

### Daniel-Hirshleifer-Sun

- Factors: market, FIN, PEAD.
- FIN: long-horizon financing behavior, such as net issuance and related financing anomalies.
- PEAD: post-earnings announcement drift and short-horizon underreaction.
- Use: behavioral finance and mispricing explanations.

### Liu-Shi-Lian 4-Factor

- Role in the book: A-share-oriented benchmark that extends Fama-French-style factors with profitability evidence more consistent with local empirical results.
- Use: anomaly alpha tests and model comparison in A-share settings where FF5 investment evidence is weak.

## A-Share Model Evidence

Use this summary when answering "which model works in A-shares?"

- Market beta is important for time-series variation but weak as the only cross-sectional pricing variable.
- Size, value, profitability, turnover/liquidity, and low-volatility effects can matter, but their strength depends on weighting and sample.
- Traditional momentum is weaker in A-shares because reversal and speculative trading are strong.
- Investment evidence is weaker than in U.S. studies in the book's empirical setting.
- Fama-MacBeth evidence should be interpreted with controls and robust standard errors.
- Model comparison should focus on alpha reduction, GRS/alpha tests, parsimony, and economic meaning, not only in-sample fit.

## Anomaly Templates

### F-Score

Purpose: distinguish genuine value stocks from value traps.

Nine indicators:

| Category | Indicators |
| --- | --- |
| Profitability | ROA > 0, change in ROA > 0, CFOA > 0, accruals < 0 |
| Leverage/liquidity | leverage decreases, liquidity improves, no equity issuance |
| Operating efficiency | margin improves, turnover improves |

Use:

- Combine with high BM to find undervalued firms with improving fundamentals.
- High F-Score is stronger evidence than cheap valuation alone.

### G-Score

Purpose: distinguish high-quality growth stocks from overvalued glamour stocks.

Dimensions:

- Profitability: ROA, CFOA, accrual quality.
- Conservative accounting/investment: R&D, sales expense, capital expenditure.
- Stability: ROA and revenue-growth stability.

Use:

- Especially relevant for low-BM/growth stocks.
- Helps avoid rejecting all expensive stocks mechanically.

### Expectation Gap

Core idea (预期差):

- Market expectation is proxied by valuation, such as BM.
- Fundamental expectation is proxied by F-Score or similar quality signals.
- Misalignment creates expected correction.

Portfolio logic:

- Long high-BM/high-F-Score stocks: fundamentals strong but market expectations low.
- Short low-BM/low-F-Score stocks: fundamentals weak but market expectations high.
- Non-expectation-gap combinations should earn smaller spreads if the mechanism is right.

### Fundamental Anchoring Reversal

Core idea (基本面锚定反转):

- Investors anchor on fundamental values or fail to fully process deviations between price and fundamentals.
- Overreaction relative to a fundamental anchor later reverses.

Implementation:

- Define a fundamental anchor.
- Measure price deviation from that anchor.
- Test whether extreme deviations reverse after controlling for common factors.

Watch:

- Anchor must be observable at the decision date.
- Reversal can be confused with value, momentum reversal, or liquidity effects.

### Idiosyncratic Volatility

Core idea (特质性波动率):

- Low idiosyncratic volatility stocks can outperform high-IVOL stocks.
- This contradicts naive "higher risk, higher return" intuition.

Mechanisms:

- Lottery demand pushes high-IVOL stocks too expensive.
- Short-sale constraints and arbitrage asymmetry prevent easy correction.
- Benchmark or leverage constraints can create demand for high-beta/high-volatility stocks.

Implementation:

- Estimate IVOL as residual volatility from a factor model.
- Test low-minus-high IVOL portfolios and factor-model alpha.
- Check whether results survive size, liquidity, price, turnover, and beta controls.

## Catalog Card Format

When adding a factor, model, or anomaly, use:

1. Definition and variables.
2. Direction and expected sign.
3. Construction details and timing.
4. Economic or behavioral rationale.
5. A-share evidence or transferability caution.
6. Key controls and robustness tests.
7. Implementation risks: turnover, liquidity, shorting, capacity, and crowding.
