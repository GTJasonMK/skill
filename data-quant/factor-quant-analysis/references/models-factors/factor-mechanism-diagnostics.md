# Factor Mechanism Diagnostics

## Contents

- [Purpose](#purpose)
- [Diagnostic Loop](#diagnostic-loop)
- [Main Factor Mechanisms](#main-factor-mechanisms)
- [Idiosyncratic Volatility Extensions](#idiosyncratic-volatility-extensions)
- [Behavioral Mechanism Map](#behavioral-mechanism-map)
- [How to Use in Agent Work](#how-to-use-in-agent-work)

## Purpose

Use this reference when a factor works, fails, looks too good, reverses after controls, or needs an economic explanation. It focuses on mechanism diagnosis: what story could make the signal work, what else could explain the same evidence, and what the next empirical test should be.

Do not use this file as a substitute for exact source tables. Use the original chapter summaries for exact returns, t-statistics, sample windows, and product numbers.

## Diagnostic Loop

For any factor or anomaly:

1. Name the object: prediction variable, factor exposure, factor return, pricing factor, or portfolio alpha.
2. State the proposed mechanism before tuning construction.
3. Identify competing explanations: omitted risk, mispricing, data snooping, liquidity, trading frictions, or proxy exposure to another factor.
4. Choose tests that can distinguish the explanations, not only tests that increase t-statistics.
5. Inspect long leg and short leg separately. Many A-share paper anomalies are driven by short legs that are hard to implement.
6. Compare equal-weight and value-weight evidence. Large differences often indicate microcap, illiquidity, or capacity problems.
7. Stress the horizon: one-week, one-month, quarterly, and annual effects can have opposite signs.
8. Report the unresolved mechanism uncertainty instead of forcing one story.

## Main Factor Mechanisms

### Size

Core mechanisms:

- Banz-style small-firm effect: the premium can be concentrated in the smallest stocks rather than linear across market capitalization.
- Distress or fallen angels (坠落天使): small firms can be former distressed large firms with higher financial risk.
- Liquidity and investor base: small stocks can be neglected, illiquid, or outside institutional mandates.
- Delisting bias, extreme-return concentration, and seasonality can exaggerate historical evidence.
- Berk-style omitted-risk proxy: if the pricing model is misspecified, market cap can mechanically proxy unobserved cash-flow risk instead of being a causal characteristic.

Try next:

- Separate microcap, shell-value, ST, and delisting-risk names from normal small stocks.
- Compare equal-weight and value-weight spreads, and report capacity.
- Control for liquidity, beta, volatility, profitability, distress, turnover, and industry.
- Test whether size remains after excluding the smallest 20-30% when the market has shell-value distortions.
- In A shares, treat 壳价值, 借壳上市, and the 市值最低的 30% filter as research-design choices, not as harmless data cleaning.

Red flags:

- Evidence exists only in equal-weight microcaps.
- Long-short spread is mostly a short leg in large, liquid names or an untradeable long leg in tiny names.
- Size disappears after liquidity, distress, or profitability controls.

### Value

Core mechanisms:

- Risk compensation: high BM or high EP firms can have distress risk, operating leverage (经营杠杆), or greater exposure to bad states.
- Mispricing: investors over-extrapolate glamour-stock growth and become too pessimistic about value stocks.
- Intangible information (无形信息): book value can miss intangible assets; BM can proxy investor underreaction to intangible news.
- R&D and advertising can depress current accounting earnings or book metrics while supporting future profitability.

Try next:

- Compare BM, EP, CF/P, sales-to-price, enterprise multiple, and dividend yield.
- Use quality screens to separate cheap value from value traps.
- Test whether value is stronger among high arbitrage-cost, low attention, or low institutional-ownership stocks.
- Adjust or tag R&D, advertising, and other intangible investment when the accounting definition makes BM misleading.
- In A shares, compare BM and EP because EP can be a more direct value component in some model comparisons.

Red flags:

- Cheap stocks are concentrated in weak-quality firms with deteriorating fundamentals.
- Value alpha vanishes after profitability, investment, leverage, or industry controls.
- A value index is actually a dividend, low-volatility, or sector bet.

### Momentum

Core mechanisms:

- Risk compensation: winners and losers can have time-varying systematic risk. Momentum crash (动量崩溃) occurs when the long-short strategy has large losses around sharp market reversals.
- Underreaction: limited attention and slow information diffusion can produce continuation.
- Overconfidence and self-attribution can amplify continuation after private information.
- Disposition effect and capital gains overhang (CGO, 未实现盈利) can create selling pressure that affects continuation.
- Industry momentum and earnings momentum (盈余动量) can drive price momentum.

Improvement variants:

- Skip the most recent month to reduce short-term reversal contamination.
- Residual momentum (残差动量): compute momentum from residual returns after removing chosen factor exposures; this can reduce crash exposure but depends on the base model.
- Target-volatility or dynamic momentum: scale exposure by predicted momentum volatility or crash risk.
- News or information-driven momentum: separate information-driven returns from non-information-driven price moves.

Try next:

- Test `t-12` to `t-1` momentum and versions that skip the latest month.
- Test residual momentum under several base models; state the base model and do not hide order dependence.
- Separate small-cap and large-cap results. A-share traditional momentum can be weak or become reversal in small stocks.
- Inspect whether profits come from earnings announcements, analyst revisions, industry moves, or price-only continuation.
- Report crash months, skewness, turnover, and cost sensitivity.

Red flags:

- Momentum works only by including the most recent reversal-prone month.
- The result is mostly short-leg alpha but shorting is infeasible.
- A high-turnover implementation loses the paper spread after costs.

### Profitability and Quality

Core mechanisms:

- Higher ROE, ROA, gross profitability, or operating profitability can proxy persistent cash-flow strength.
- Gross profitability can be cleaner than net income because R&D, advertising, financing, taxes, and accounting discretion affect lower income-statement lines.
- Quality signals can also be mispricing signals when investors underreact to fundamental persistence.
- Profitability has several dimensions: level, cash-flow quality, stability, and growth. Do not treat one ratio as the whole quality factor.

Common variable variants:

| Variable | Typical meaning | Diagnostic use |
| --- | --- | --- |
| `ROE` | Profit over book equity | Strong for shareholder return but can be distorted by leverage and buybacks. |
| `ROA` | Profit over total assets | Better cross-firm operating comparison, but still mixes financing and non-operating assets. |
| `GP` | Gross profit over total assets | Cleaner near-production profitability; less affected by lower income-statement discretion. |
| Operating profitability | Operating profit scaled by assets, equity, or book value | Useful when net income is noisy because of taxes, interest, or one-off gains. |
| `ROTC` | EBIT over tangible capital | Greenblatt-style operating return; useful when tangible capital is the binding resource. |
| `ROIC` | After-tax operating profit over invested capital | Useful for capital-efficiency and business-quality analysis. |
| `RNOA` | Operating profit over net operating assets | Removes some financing and investment-asset noise; can be sensitive to accounting classification. |

A-share `ROE(TTM)` book-style proxy:

```text
ROE(TTM) = latest 12-month operating profit
           / average shareholder equity over the latest four report periods
```

Use the exact vendor fields only after checking minority-interest treatment, restatement policy, and report availability dates.

Profitability-quality extensions:

- Earnings quality: compare cash-flow profitability with accrual-based profitability. High accruals can signal low earnings quality.
- Profitability volatility: use rolling quarterly or annual profit volatility as a persistence proxy; require enough valid observations.
- Profitability growth: use SUE, earnings trend, growth persistence, and earnings acceleration when the question is about improvement rather than current level.
- Margin versus turnover: decompose ROA or ROE before concluding that high profitability is economically persistent.

Try next:

- Compare ROE, ROA, gross profitability, operating profitability, ROTC, ROIC, RNOA, margins, accrual quality, leverage, stability, and growth.
- Use point-in-time financial-report availability and restatement rules.
- Test whether profitability survives value and investment controls.
- Control size explicitly. In A shares, low-profitability groups can have positive small-cap exposure, and profitability effects can become clearer after size control.
- Watch financial firms because balance-sheet structure changes interpretation.

Red flags:

- The signal uses fiscal period end rather than announcement or vendor-availability date.
- Profitability is dominated by one-off gains, accounting changes, or sector structure.

### Investment

Core mechanisms:

- q-theory: for a given profitability level, higher investment implies lower expected return because the marginal cost of investment is higher.
- Real option (实物期权): investment can convert risky growth options into lower-risk assets, lowering expected returns.
- Decreasing returns to scale: aggressive investment can reduce marginal productivity.
- Manager timing: managers issue equity or invest more when the firm is overvalued.
- Overinvestment or empire building (企业帝国): managers invest in negative-NPV projects, investors underreact, and future returns fall.
- Earnings management and acquisitions: asset growth can be tied to managed earnings or M&A; in A shares, acquisition-driven asset growth can offset the theory-implied negative relation.

Try next:

- Control profitability before judging investment. In A shares, low investment can have negative profitability exposure.
- Use conditional sorting: first profitability, then investment.
- Separate organic asset growth from acquisition-driven growth when data allow.
- Compare asset growth, investment-to-assets, capex growth, inventory growth, and net operating asset growth.
- Test whether investment predicts future fundamentals, issuance, or analyst revisions.
- Map Chinese aliases explicitly: 总资产增长, 资产增长率, and 投资与总资产 are investment-factor proxies, but they can mix profitability, financing, and acquisition effects.
- When the A-share investment factor has the wrong sign, first check ROA or other profitability exposure; then test ROA-first conditional double sorting (条件双重排序) before changing the theory.

Red flags:

- The investment factor has the wrong sign before controlling profitability.
- The result is mostly an M&A, sector, or accounting-timing effect.

### Turnover, Liquidity, and Volume

Core mechanisms:

- Turnover is not the same as liquidity. Amihud illiquidity measures price impact per trading amount; turnover can measure speculative demand, attention, disagreement, or overconfidence.
- PMO (Pessimistic-Minus-Optimistic) uses low-minus-high abnormal turnover logic in A-share models: high abnormal turnover can indicate optimistic speculative trading and lower future returns.
- A/B-share evidence links speculative demand to high A-share turnover and higher relative prices.
- Turnover can relate to crash risk when past winners experience sharp increases in turnover.
- Abnormal high volume can predict stronger short-horizon returns because visibility attracts buyers, but longer-horizon expected or persistent turnover can predict lower returns.

Try next:

- Define abnormal turnover as short-window turnover divided by a long-window baseline; state free-float or total-share denominator.
- Split expected turnover and unexpected turnover when possible.
- Run horizon tests: next week, next month, next quarter, next year.
- Compare turnover with Amihud illiquidity, bid-ask spread, price impact, volatility, and attention proxies.
- Inspect whether low-turnover long leg is investable and whether high-turnover short leg drives the spread.
- For book-style A-share abnormal turnover (异常换手率), use past 21 trading-day average turnover divided by past 252 trading-day average turnover, and state whether the denominator is free-float shares.
- Treat abnormal volume (异常成交量) separately from persistent high turnover: short-horizon attention effects can have the opposite sign from long-horizon speculative-turnover effects.
- If the long-short spread is strong, attribute the low-abnormal-turnover long leg and high-abnormal-turnover short leg separately before calling it implementable.

Red flags:

- A turnover factor is treated as pure liquidity without testing speculation or attention.
- Short-horizon positive abnormal-volume effects are mixed with long-horizon low-turnover effects.
- A high-turnover factor ignores turnover cost and market impact.
- The reported alpha depends on shorting high-turnover names that are hard to borrow or hard to sell near price limits.

## Idiosyncratic Volatility Extensions

Base IVOL tests ask whether high residual volatility stocks earn lower future returns. Use the construction recipes for estimation and sorting, then use the extensions below to diagnose mechanism.

Mechanism candidates:

- Arbitrage asymmetry: high IVOL raises arbitrage risk; overpriced stocks are harder to short than underpriced stocks are to buy.
- Lottery demand: investors overpay for right-tail payoff profiles, lowering future returns of high-IVOL or high-skewness stocks.
- Uncertainty versus residual volatility: IVOL can mix hard-to-price uncertainty with residual return noise. The negative return relation can be stronger for the uncertainty component.
- Common IVOL factor: idiosyncratic volatilities can move together, creating a latent factor structure rather than purely stock-specific risk.
- Residual coskewness (剩余协偏度): investors can prefer positive skewness. If pricing models omit coskewness, low-volatility anomalies can appear as alpha.
- Implied skewness (隐含偏度): option-implied skewness can proxy future residual coskewness and help test whether low-volatility alpha is an omitted-skewness effect.

Try next:

- Decompose IVOL into uncertainty-related and residual-volatility-related parts when proxies allow.
- Add MAX, skewness, implied skewness, lottery demand, price, and turnover controls.
- Test low-IVOL spreads inside mispricing groups, then inspect whether the spread is strongest among overvalued stocks.
- Compare equal-weight and value-weight results and inspect high-IVOL short-leg contribution.
- Test whether adding a skewness or coskewness proxy reduces low-IVOL alpha.
- In A shares, do not expect underpriced high-IVOL stocks to behave symmetrically; high noise and high turnover can keep the highest-IVOL group weak even among seemingly undervalued stocks.

Red flags:

- IVOL is estimated with too few daily observations or with zero-filled suspension returns.
- The effect vanishes after controlling for price, MAX, turnover, liquidity, or beta.
- The long-only low-IVOL leg is weak while the paper spread relies on shorting very speculative stocks.

## Behavioral Mechanism Map

Use behavioral mechanisms as testable priors, not as post-hoc labels.

| Chinese term | English term | Useful anomaly links | Tests to try |
| --- | --- | --- | --- |
| 过度自信 | overconfidence | Momentum, turnover, issuance, FIN | Disagreement, turnover, private-information proxies, issuance or repurchase response |
| 乐观主义 | optimism | Growth overpricing, speculative demand, high turnover | Sentiment states, hard-to-value stocks, short-leg behavior |
| 代表性启发法 | representativeness heuristic | Extrapolation, value, reversal, momentum | Long-run reversal, valuation spread, forecast-error patterns |
| 小数定律 | law of small numbers | Over-extrapolation from short histories | Subperiod sensitivity, recent-performance dependence |
| 保守主义 | conservatism | PEAD, earnings momentum, underreaction | Earnings-surprise drift, analyst revision drift |
| 确认偏误 | confirmation bias | Momentum, delayed correction | News sentiment conflict, slow reversal after contrary information |
| 锚定效应 | anchoring | 52-week high, historical high, fundamental anchoring reversal | Distance-to-anchor sorts, interaction with news |
| 可得性启发法 | availability heuristic | Attention-driven buying, abnormal volume, extreme-return effects | News coverage, search, media, extreme-return and volume proxies |
| 有限注意力 | limited attention | PEAD, slow-moving information, delayed reaction | Friday announcements, crowded announcement days, analyst/media/ownership attention proxies |
| 分类思维 | categorical thinking | Style comovement, index inclusion, factor crowding | Index inclusion, style-bucket comovement, residual correlation |
| 前景理论 | prospect theory | Lottery, low volatility, skewness, disposition effect | Skewness/MAX controls, gain/loss state, probability-weighting proxies |
| 处置效应 | disposition effect | Momentum, PEAD, volatility, lottery anomalies | Capital gains overhang (CGO) conditioning |
| 未实现盈利 | capital gains overhang, CGO | PEAD and low-volatility conditioning | Split by gain/loss state and news sign |
| 控制幻觉 | illusion of control | Overconfidence, speculative trading | Retail trading intensity, turnover after random wins |
| 自利偏差 | self-serving bias | Optimistic interpretation of firm or manager information | Forecast revisions by stakeholder incentives |
| 心理账户 | mental accounting | Disposition effect, lottery demand, narrow framing | Split by gain/loss accounts and holding-period reference points |
| 狭隘框架 | narrow framing | Prospect-theory value, volatility and skewness anomalies | Test investor state and payoff distribution jointly |

Mechanism-to-test patterns:

- If the story is limited attention, interact the signal with attention proxies such as small size, low analyst coverage, low media coverage, low institutional ownership, Friday announcements, or many same-day announcements.
- If the story is disposition effect, build CGO or another unrealized gain/loss state proxy and test whether it conditions PEAD, momentum, volatility, or lottery effects.
- If the story uses mental accounting or narrow framing, define the investor reference account first: purchase price, recent high, benchmark, fund reporting period, or tax lot. Then test whether the anomaly changes across gain/loss states.
- If the story is overconfidence or disagreement, examine turnover, abnormal volume, analyst dispersion, retail participation, and issuance response.
- If the story is extrapolation, test whether high expectations reverse when future fundamentals disappoint.
- If the story is lottery preference, control for MAX, skewness, price, IVOL, and retail attention.

## How to Use in Agent Work

When diagnosing a factor:

- Start from the closest mechanism family above.
- Name at least two competing explanations before proposing refinements.
- Propose one construction check, one control or neutralization check, one horizon check, and one implementation check.
- If the factor is intended for a portfolio, separate research evidence from tradable evidence.
- If evidence is mixed, say which mechanism remains plausible and what data would distinguish it.

Response pattern:

```text
Mechanism hypothesis:
Competing explanations:
Tests to run next:
Implementation risks:
What would change my mind:
```
