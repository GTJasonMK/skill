# Behavioral and Factor Zoo Details

Use when: explaining p-hacking, factor zoo, priors, behavioral finance, investor sentiment, prospect theory, or behaviorally efficient markets.
Read after: `task-router.md` selects theory/behavior work or a mechanism diagnosis needs behavioral detail.
Key decisions: prior plausibility, multiple-testing burden, behavioral mechanism, sentiment state, and whether evidence distinguishes mispricing from omitted risk.
Do not use for: mechanical factor construction or portfolio optimization.

## Contents

- [P-Hacking Culture](#p-hacking-culture)
- [P-Value Interpretation](#p-value-interpretation)
- [Hard Science and Soft Science](#hard-science-and-soft-science)
- [Multiple Testing](#multiple-testing)
- [Bayesian P-Value and Priors](#bayesian-p-value-and-priors)
- [From Factor Zoo to Factor War](#from-factor-zoo-to-factor-war)
- [Limits to Arbitrage](#limits-to-arbitrage)
- [Expectation Biases](#expectation-biases)
- [Prospect Theory](#prospect-theory)
- [Ambiguity Aversion](#ambiguity-aversion)
- [Cognitive Limits](#cognitive-limits)
- [Investor Sentiment Diagnostics](#investor-sentiment-diagnostics)
- [Behavioral Explanations for Anomalies](#behavioral-explanations-for-anomalies)
- [Behaviorally Efficient Market](#behaviorally-efficient-market)

## P-Hacking Culture

P-hacking is the process of changing variables, samples, filters, horizons, or tests until a result becomes statistically significant.

In factor research, p-hacking often appears through:

- Trying many characteristics and reporting only the best.
- Changing sample windows after seeing results.
- Switching equal-weight and value-weight returns opportunistically.
- Trying many rebalance frequencies, holding periods, and neutralization schemes.
- Dropping inconvenient stocks, industries, or subperiods.
- Using post-publication data as if it were an untouched out-of-sample test.

Factor zoo (因子动物园):

- The term criticizes the large number of published anomalies and factors.
- It does not mean all factors are false.
- It means the number of claimed factors is too large relative to plausible independent economic drivers.

Review rule:

- A factor needs prior logic, transparent trials, multiple-testing adjustment, and sample-out survival.
- A low p-value alone is not a discovery.

## P-Value Interpretation

Correct meaning:

```text
p-value = P(D or more extreme data | H0)
```

Incorrect meaning:

```text
p-value != P(H0 | D)
```

For factor returns:

- `H0`: factor premium equals zero.
- Low p-value means the observed premium is unlikely under that null model.
- It does not prove the factor is real.
- It does not measure economic magnitude.
- It does not control for all tried but unreported variants.

American Statistical Association-style cautions:

1. P-values measure incompatibility between data and a model.
2. They do not give the probability that the null is true.
3. Decisions should not rely only on crossing a threshold.
4. Full transparency is necessary to detect p-hacking.
5. Statistical significance is not economic significance.
6. P-values alone are not enough evidence for a model or hypothesis.

Answering rule:

- When a user cites `t ~= 2`, ask how many hypotheses were searched.
- Demand effect size, turnover, costs, prior logic, and sample-out behavior.

## Hard Science and Soft Science

Hard science versus soft science (硬科学与软科学) is used to explain why factor research is vulnerable to researcher degrees of freedom.

Hard-science-like settings:

- Results are less dependent on researcher preferences.
- Experiments or proofs can often be reproduced with limited interpretation choices.

Soft-science-like settings:

- Research design choices strongly affect results.
- Sample selection, variable definitions, filters, estimation methods, and interpretation all matter.

Finance is closer to soft science:

- Markets are non-stationary.
- There is only one realized history.
- Researchers cannot rerun history under controlled conditions.
- Published findings change investor behavior.

Implication:

- A factor study must disclose design choices and failed variants.
- Replication and robustness are part of evidence, not optional appendices.

## Multiple Testing

Multiple testing occurs when many hypotheses are tested on the same historical data.

False-discovery table:

| Truth / Decision | Reject H0 | Do not reject H0 |
| --- | --- | --- |
| H0 true | False discovery | Correct non-discovery |
| H0 false | True discovery | Missed discovery |

Main controls:

| Control | Meaning | Use in factor work |
| --- | --- | --- |
| FWER | Probability of at least one false discovery | Very strict; useful for narrow confirmatory tests |
| FDR | Expected false-discovery share among discoveries | Practical for many searched factors |
| FDP | Probability false-discovery share exceeds a threshold | Useful when controlling discovery quality |

Common methods:

- Bonferroni and Holm for FWER.
- White reality check and SPA for searched strategies.
- Benjamini-Hochberg and Benjamini-Yekutieli for FDR.
- Romano-Wolf-style procedures for FDP or stepwise inference.

Finance-specific rule:

- Traditional `t = 2` is too weak when hundreds of factors were tried.
- Harvey et al.-style evidence suggests `t > 3` or higher may be needed.
- Chordia et al.-style results can imply even higher thresholds depending on method.

## Bayesian P-Value and Priors

Bayesian p-value (贝叶斯 p 值, 贝叶斯p值) reframes the question:

```text
P(H0 | D)
```

instead of:

```text
P(D | H0)
```

Minimum Bayes factor lower bound:

```text
phi = -e * p * ln(p)
phi = exp(-t^2 / 2)
```

Bayesian p-value form used in the chapter:

```text
Bayesian p-value = (phi * prior probability) / (1 + phi * prior probability)
```

Prior categories:

| Factor prior | Example meaning |
| --- | --- |
| Very unlikely | No credible economic or behavioral mechanism |
| Possible | Some logic but weak or indirect |
| Very likely | Strong theory and established market mechanism |

Interpretation:

- A clever but implausible factor can have a very low raw p-value and still fail under a skeptical prior.
- A factor with strong prior logic needs less extraordinary sample evidence than a random-looking factor.
- Priors are subjective, but ignoring priors is also a hidden assumption.

Use this when:

- A user asks whether a strange anomaly is credible.
- A result has a low p-value but no mechanism.
- Many factors have been searched.

## From Factor Zoo to Factor War

Factor war (因子大战) refers to competing multi-factor models claiming to explain more anomalies.

Problem:

- A new model can often explain more anomalies by adding or refining factors.
- Explaining anomalies is useful, but it is not the only purpose of asset pricing.
- A good factor model should explain both common return movement and the economic source of expected returns.

Example:

- Fama-French investment factor and Hou-Xue-Zhang investment factor use similar investment variables.
- Their theoretical motivations differ: dividend-discount logic versus q-theory and investment economics.
- Similar construction does not imply identical meaning.

q5 model:

- Extends q-factor logic by adding expected investment growth.
- Its expected-growth factor is more complex and depends on prediction models.
- Complexity raises model-risk and estimation-error concerns.

Review rule:

- Do not rank models only by in-sample anomaly count.
- Compare parsimony, factor meaning, common movement, alpha reduction, sample-out behavior, and implementation.
- Ask whether the model explains why returns move together, not only whether it absorbs anomaly alphas.
- Do not force an extra factor into a model only because it improves a GRS table. If the factor is outside the model's theory, the extra alpha reduction may be data snooping rather than understanding.
- A model that refuses to add an empirically helpful but theoretically unsupported factor can be more coherent than a larger model built mainly to win an anomaly horse race.

## Limits to Arbitrage

Limits to arbitrage (套利限制) explain why mispricing can persist.

Main sources:

- Noise-trader risk: irrational demand can push mispricing further before it corrects.
- Short-sale constraints: overpricing is harder to exploit than underpricing.
- Funding and margin constraints: arbitrageurs may be forced to exit before convergence.
- Horizon mismatch: investors may not tolerate drawdowns before the thesis pays off.
- Transaction costs and illiquidity: small theoretical alpha can be uneconomic.

Use in anomaly explanation:

- Stronger for high-volatility, hard-to-short, small, illiquid, or retail-attention stocks.
- Helps explain why overpriced lottery-like stocks can remain overpriced.

Do not use it as a universal excuse. If limits to arbitrage are cited, identify the specific constraint and test a cross-sectional implication.

## Expectation Biases

Expectation biases (预期偏差) affect how investors process information.

Overconfidence:

- Investors overestimate their private information and analytical skill.
- Can create excessive trading volume and short-run under/overreaction.

Optimism:

- Investors overestimate favorable outcomes, especially when they feel control.
- Can amplify growth-stock overpricing or speculative demand.
- Illusion of control (控制幻觉) can strengthen optimism after a few lucky outcomes, especially in trading environments with frequent feedback.
- Self-serving bias (自利偏差) can make analysts, managers, or investors interpret ambiguous evidence in the direction that benefits their position.

Representativeness heuristic:

- Investors judge by similarity and ignore base rates.
- Leads to extrapolation and the law-of-small-numbers bias.
- Law of small numbers (小数定律偏误) means investors infer too much from a short record of returns, earnings, or fund performance.

Conservatism:

- Investors update beliefs too slowly after new information.
- Helps explain post-earnings announcement drift and momentum.

Confirmation bias:

- Investors seek evidence supporting existing beliefs and ignore contradicting data.
- Can prolong mispricing.

Anchoring:

- Investors over-rely on initial or salient reference values.
- Examples include 52-week highs, historical highs, and fundamental anchors.

Availability heuristic:

- Investors overweight vivid, recent, or attention-grabbing examples.
- News coverage, extreme returns, and abnormal volume can attract buying pressure.

## Prospect Theory

Prospect theory (前景理论) describes decisions over gains and losses relative to a reference point.

Key value-function properties:

- Outcomes are measured relative to a reference point, not final wealth.
- Loss aversion: losses hurt more than same-sized gains are valued.
- Sensitivity is diminishing in both gains and losses.

Canonical value function:

```text
v(x) = x^c,                x >= 0
v(x) = -kappa * (-x)^c,    x < 0
```

Typical parameters from cumulative prospect theory:

- `c` around 0.5 to 0.95.
- `kappa` around 1.5 to 2.5.

Probability weighting:

- Small-probability tail events are overweighted.
- Investors can overpay for lottery-like right-tail stocks.
- The same mechanism can explain insurance demand and lottery demand.

Anomaly links:

- Lottery and skewness anomaly: high right-skew stocks become overpriced and earn lower future returns.
- Low-volatility anomaly: high-IVOL stocks can be overpriced because they resemble lottery tickets.
- Disposition effect: investors sell winners too early and hold losers too long.
- CGO-based anomalies: unrealized gains/losses condition how investors react to news and volatility.
- Mental accounting (心理账户): investors evaluate positions in separate accounts rather than only total wealth.
- Narrow framing (狭隘框架): investors evaluate a single position, recent holding-period outcome, or account bucket too narrowly. This can connect prospect theory to momentum, IVOL, skewness, PEAD, and disposition-effect tests.

## Ambiguity Aversion

Ambiguity aversion (模糊厌恶) means investors dislike unknown probability distributions.

Classic intuition:

- A known 50/50 urn can be preferred to an unknown-composition urn even when expected probabilities appear symmetric.

Investment implications:

- Investors prefer familiar companies, industries, and countries.
- Home bias and familiarity bias can persist.
- Unknown or opaque assets may require a premium, but investor "familiarity" can be overestimated.

Practical caution:

- A manager saying "we only invest in what we understand" is sensible only if understanding is real.
- Confirmation bias and overconfidence can make investors mistake familiarity for expertise.

## Cognitive Limits

Cognitive limits (认知限制) or bounded rationality constrain information processing.

Limited attention:

- Investors cannot process all public information immediately.
- Slow-moving or low-salience information can be underreacted to.
- Friday earnings announcements and crowded announcement days can strengthen PEAD.

Categorical thinking:

- Investors group stocks into categories such as value, growth, quality, small cap, or index membership.
- Category membership can increase return comovement even without fundamental comovement.
- Index inclusion can change correlation patterns because investors trade the category.

Use in factor work:

- Limited attention supports underreaction, momentum, and PEAD mechanisms.
- Categorical thinking supports style comovement and factor crowding.
- Behavioral forces can also create common return movement. Sentiment, category trading, benchmarked style demand, and shared extrapolation can make stocks with similar labels move together even without a traditional risk shock.

## Investor Sentiment Diagnostics

Investor sentiment (投资者情绪) measures aggregate expectation bias, speculative demand, or risk appetite that is not fully captured by fundamentals.

Use sentiment as a state variable, not as proof of causality by itself.

Baker-Wurgler-style components:

| Component | Meaning | Expected sentiment link |
| --- | --- | --- |
| Closed-end fund discount `CEFD` | Fund NAV versus market price discount | Larger discount usually means lower sentiment |
| Turnover `TURN` | Detrended market turnover | Higher speculative turnover means higher sentiment |
| IPO count `NIPO` | Number of IPOs | More IPOs during high sentiment |
| IPO first-day return `RIPO` | Average first-day IPO return | Higher first-day return means higher sentiment |
| Equity issuance share `S` | Equity issuance relative to equity plus long-term debt issuance | High equity issuance can indicate firms exploiting high sentiment |
| Dividend premium `P^{D-ND}` | Valuation difference between dividend payers and non-payers | Can be negative when investors prefer growth and speculation |

Composite construction:

1. Build current and lagged versions of the sentiment proxies.
2. Extract the first principal component as a temporary index.
3. For each proxy, keep current or lagged version based on higher correlation with the temporary index.
4. Extract the first principal component from the selected proxies.
5. Optionally regress each proxy on macro/business-cycle variables and repeat PCA on residuals to obtain macro-orthogonal sentiment.

Book-style coefficient pattern:

```text
SENTIMENT_t ~= -CEFD + lagged TURN + NIPO + lagged RIPO
              + equity_issuance_share - lagged dividend_premium
```

Macro-orthogonal version:

```text
proxy_perp = residual from proxy ~ macro/business-cycle controls
SENTIMENT_perp = first principal component of selected proxy_perp series
```

Use these formulas as construction logic, not fixed production coefficients. PCA weights are sample-dependent, and the index should be re-estimated with point-in-time macro and proxy data.

PLS alternative:

- PCA can mix true sentiment with common measurement errors in the proxy variables.
- Partial least squares can be used when the target is predictive content for future market or anomaly returns rather than explaining proxy variance.
- Treat PLS sentiment as another searched timing signal and validate it out of sample.

Interpretation:

- High sentiment often overprices young, small, volatile, distressed, growth, hard-to-value, or lottery-like stocks.
- Low sentiment can leave speculative stocks cheaper, making their future returns higher.
- Sentiment can affect anomaly returns mainly through the short leg because overpriced stocks are harder to arbitrage than underpriced stocks.

Testing anomaly state dependence:

- Split months into high- and low-sentiment states using only information available at the time.
- Test long leg, short leg, and long-short returns separately.
- Control for market, size, value, profitability, investment, and momentum factors.
- Check whether the effect remains after volatility, liquidity, and macro controls.

Other sentiment proxies:

- VIX-like risk appetite indicators.
- News, social-media, announcement, and earnings-call text tone.
- Fund flows, margin activity, retail participation, or search intensity.
- Manager sentiment extracted from company filings or conference-call transcripts.
- Global and country sentiment when studying cross-market assets.

Practical warnings:

- PCA weights are sample-dependent and can change when proxies are revised.
- Macro orthogonalization must be fit without future information.
- Sentiment timing is vulnerable to data snooping because there are few independent market cycles.
- A sentiment-conditioned factor still needs cost, turnover, capacity, and robustness checks.

## Behavioral Explanations for Anomalies

PEAD:

- Investors underreact to earnings surprises because of limited attention and conservatism.
- Announcement timing, number of simultaneous announcements, and attention measures should condition the effect.

Momentum:

- Early underreaction to information can create return continuation.
- Later overreaction and extrapolation can create reversals.

Value:

- Over-extrapolated growth expectations can overprice glamour stocks.
- Fundamental disappointment later reverses the mispricing.

Low volatility and IVOL:

- Lottery demand and short-sale constraints can overprice high-volatility stocks.
- Benchmark or leverage constraints can also affect demand for high-beta names.

Skewness:

- Overweighting right-tail payoffs lowers expected returns for lottery-like stocks.

Disposition and CGO:

- Unrealized gain/loss state affects selling pressure and response to news.
- CGO can modify PEAD, volatility, and lottery anomalies.

Use this section to connect an anomaly to a mechanism, but still require empirical tests that distinguish behavior from omitted risk.

Behavioral factor caution:

- A behavioral story can justify a prior, but it does not by itself prove mispricing.
- If a behavioral mechanism affects many stocks at once, test both cross-sectional return prediction and common movement.
- If exploiting the behavior requires shorting, leverage, or frequent trading, limits to arbitrage can preserve the anomaly while also making it hard to monetize.

## Behaviorally Efficient Market

Behaviorally efficient market (行为有效市场) separates two claims:

| Claim | Behavioral view |
| --- | --- |
| Price equals value | Often false because bias and limits to arbitrage create mispricing. |
| Market is hard to beat | Often true because exploiting mispricing is costly, risky, and competitive. |

Implication:

- "Market is hard to beat" does not imply "price always equals value."
- "Price differs from value" does not imply "there is easy alpha."

Useful summary:

- Noise makes markets less than perfectly efficient.
- The same noise, costs, and constraints prevent easy exploitation.
- Mispricing can exist without offering a clean trade. Always separate informational inaccuracy from arbitrageability and implementable alpha.

When answering:

- Avoid binary "efficient or inefficient" framing.
- Ask whether the user means informational accuracy, arbitrageability, or implementable excess return.
