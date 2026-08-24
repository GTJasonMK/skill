# Theory Foundations

## Contents

- [Unifying Asset-Pricing View](#unifying-asset-pricing-view)
- [Core Terms](#core-terms)
- [Common Movement and Covariance Structure](#common-movement-and-covariance-structure)
- [Academic Origins](#academic-origins)
- [Industry View](#industry-view)
- [P-Hacking and Factor Zoo](#p-hacking-and-factor-zoo)
- [Risk Compensation, Mispricing, or Data Snooping](#risk-compensation-mispricing-or-data-snooping)
- [Behavioral Finance Explanations](#behavioral-finance-explanations)
- [Investor Sentiment](#investor-sentiment)
- [Out-of-Sample Decay](#out-of-sample-decay)
- [Fundamental Analysis and Quantamental Limits](#fundamental-analysis-and-quantamental-limits)

## Unifying Asset-Pricing View

Use this section when explaining what factor investing is.

CAPM is the one-factor starting point:

```text
E[R_i] - R_f = beta_i * (E[R_M] - R_f)
beta_i = cov(R_i, R_M) / var(R_M)
```

APT and linear multi-factor models extend CAPM:

```text
E[R_i^e] = beta_i' lambda
```

The book's unifying equation adds pricing error:

```text
E[R_i^e] = alpha_i + beta_i' lambda
```

Interpretation:

- `beta_i' lambda`: expected return explained by factor exposures and factor premia.
- `alpha_i`: pricing error relative to the chosen model; it may be omitted risk, mispricing, skill, data error, or sample noise.
- Cross-sectional work asks why assets have different expected returns.
- Time-series work asks how an asset or portfolio return moves over time and how much alpha remains after known factor returns.

The variance-model view is:

```text
Sigma = beta Sigma_lambda beta' + Sigma_epsilon
```

This explains why factor models are useful for risk management: a large asset covariance matrix can be approximated through a lower-dimensional factor covariance matrix plus specific risk.

## Common Movement and Covariance Structure

Use this section when judging whether a candidate is a real pricing factor, a useful risk factor, or only an anomaly variable.

A factor model has two jobs:

- Explain expected-return differences across assets.
- Explain return common movement (收益率共同运动) through covariance structure (协方差结构).

Rules:

- A good multi-factor model should reduce test-asset alphas and explain why asset returns co-move.
- Do not judge models only by how many anomalies they explain; a factor unrelated to covariance structure may be a searched characteristic rather than a core driver.
- A factor can be useful in a risk model even if it has weak average premium, because risk management depends on covariance and exposure.
- A factor can be a profitable signal without being a good pricing factor if it predicts returns but does not explain common movement.
- Behavioral factors can still explain common movement when many stocks share mispricing sources such as style sentiment, categorical thinking, limited attention, or common investor constraints.
- PCA/IPCA and latent-factor methods start from this covariance or factor-space question, but extracted factors still need economic interpretation and investable replication.

When comparing models, ask:

1. Does the factor have a distinct economic, behavioral, or risk-management meaning?
2. Does it reduce pricing errors under fair test assets?
3. Does it explain co-movement, not only a collection of anomaly spreads?
4. Is the improvement stable out of sample and after parsimony penalties?

## Core Terms

Keep these objects separate:

| Object | Meaning | Common confusion |
| --- | --- | --- |
| Characteristic or prediction variable | Observable value such as BM, ROE, turnover, IVOL | Often called an "alpha factor" in industry |
| Factor exposure | Asset sensitivity or loading to a factor | Not always equal to the raw characteristic |
| Factor return/premium | Return earned by a factor-mimicking portfolio or estimated factor | Not the same as the characteristic |
| Pricing factor | Factor that explains expected-return differences | Requires pricing evidence, not only sorting |
| Anomaly | Significant alpha not explained by a chosen model | Could be omitted risk or data snooping |
| Portfolio alpha | Return unexplained after weights, costs, constraints, and model controls | Regression alpha is not automatically investable |

Academic language distinguishes pricing factors from anomaly factors and from variables used to build them. Industry language often calls all predictive variables "alpha factors"; when answering, name the object being estimated.

## Academic Origins

Use these anchors for historical explanation:

- CAPM: first clean linear relation between market risk and expected excess return.
- APT: extends one market factor to multiple systematic drivers.
- Fama: efficient market hypothesis, joint hypothesis, Fama-MacBeth regression, and Fama-French factors.
- Hansen: generalized method of moments, especially important for consumption-based asset-pricing models such as CCAPM.
- Shiller: behavioral finance (行为金融) and excess volatility; prices can deviate from fundamentals because investors are not fully rational.

Joint hypothesis problem (联合假说):

- A test of market efficiency is also a test of the asset-pricing model used as benchmark.
- If a portfolio has significant alpha, either the market is inefficient, or the model is missing relevant risks, or the sample produced noise.

Event study:

- A method to measure abnormal returns around information events.
- Useful for testing mispricing mechanisms, underreaction, overreaction, and announcement-window effects.

## Industry View

Managers use factors in two ways:

- Expected-return tools: variables and models used to forecast future relative returns.
- Risk-management tools: risk factors used to estimate covariance, control exposures, and explain performance.
- Portfolio-construction tools: expected-return forecasts and risk exposures are combined with costs, constraints, and benchmark-relative objectives.

Manager alpha versus beta:

- Active alpha (主动 alpha): excess return that remains after controlling for intended and unintended factor exposures, costs, constraints, and benchmark effects.
- Active beta (主动 beta): skill in allocating to rewarded factor exposures such as value, quality, low volatility, momentum, or defensive factors.
- A manager's excess return can come mostly from factor beta exposure rather than stock-specific alpha. Treat factor attribution as a first diagnostic before praising or rejecting manager skill.
- Active beta can still be skill if exposures are intentional, stable, economically justified, and survive out-of-sample and cost checks.

Ordinary investors access factors mainly through style indexes and Smart Beta products. They still need to evaluate factor logic, product construction, cost, liquidity, crowding, and fit with portfolio objectives.

As capital flows into a factor, expected returns can decay because the market becomes more efficient along that dimension. Similar signals, similar rebalance schedules, and similar constraints create crowding. Crowding also raises crash risk when investors with similar positions unwind together.

Innovation sources:

- New data can expose faster or more granular information, but must pass licensing, timestamp, entity-mapping, bias, and incremental-value checks.
- New algorithms can uncover nonlinear interactions, but financial data has low signal-to-noise, few independent histories, and high overfit risk.

## P-Hacking and Factor Zoo

Use this section when reviewing statistical evidence.

A p-value is:

- The probability of observing data at least as extreme as the sample under the null model.
- Not the probability that the null is true given the data.

Traditional `t ~= 2` evidence is too weak for discovered factors when many variables, definitions, periods, horizons, neutralizations, and test assets have been searched.

Multiple-testing concepts:

| Concept | Meaning |
| --- | --- |
| FWER | Probability of at least one false discovery in a tested family |
| FDR | Expected proportion of false discoveries among rejected hypotheses |
| FDP | Realized false-discovery proportion |
| Bonferroni/Holm | Conservative family-wise error controls |
| Benjamini-Hochberg | Common FDR control |
| White reality check / SPA | Strategy-search diagnostics with dependence and data snooping |

Prior matters. A statistically significant factor without a credible risk, behavioral, institutional, accounting, or microstructure prior is more likely to be a lucky factor.

Factor zoo to factor war:

- Many published factors are variations of similar ideas.
- Similar labels can hide different constructions and different economic meanings.
- A larger model is not automatically better; parsimony, economic meaning, common-movement explanation, and out-of-sample behavior matter.
- Do not judge factor models only by how many anomalies they explain in sample. A model should also clarify the drivers behind return covariance and expected-return differences.
- Do not add a factor only to win a GRS or alpha table if the factor has no theory, behavioral mechanism, or robust sample-out support.

## Risk Compensation, Mispricing, or Data Snooping

Use three diagnostic paths.

Risk compensation:

- The high-return side should load on bad states or systematic risks.
- Factor exposure should explain returns better than an arbitrary characteristic.
- The premium should be stronger when the price of risk is high.
- Similar risk logic should work in related markets.

Mispricing:

- Look for underreaction, overreaction, limited attention, extrapolation, or sentiment.
- Test announcement-window returns, SUE, PEAD, analyst revisions, and correction horizons.
- Stronger anomaly returns under high limits to arbitrage support a mispricing story.

Data snooping:

- Check post-publication decay, later samples, other markets, and truly new data.
- Require an experiment registry with failed variants.
- Separate exploratory searches from confirmatory tests.

Many factors have mixed explanations. Report uncertainty instead of forcing one story.

## Behavioral Finance Explanations

Use this section for anomaly mechanisms.

Limits to arbitrage:

- Short-sale constraints, borrowing costs, benchmark mandates, transaction costs, funding risk, and synchronization risk prevent mispricing from being immediately corrected.
- Anomaly returns should often be stronger where arbitrage is harder.

Expectation bias:

- Investors extrapolate recent performance, underreact to gradual information, or overreact to salient news.
- This can generate momentum, reversal, post-earnings announcement drift, and fundamental anchoring effects.

Risk-preference bias:

- Prospect theory: investors evaluate gains/losses around reference points, dislike losses more than equal gains, and may overweight small-probability lottery payoffs.
- Lottery demand can help explain high-IVOL, high-skewness, high-turnover stocks having low future returns.
- Ambiguity aversion: investors dislike hard-to-estimate distributions and may demand or misprice uncertainty.

Cognitive limits:

- Investors have limited attention, process complex accounting information slowly, and may anchor on simple signals.
- Complex or slow-moving fundamental information can produce delayed price correction.

Behaviorally efficient market:

- Markets are not perfectly efficient, but anomalies are constrained by competition, arbitrage, and adaptation.
- A behavioral explanation does not guarantee an investable strategy after costs and crowding.

## Investor Sentiment

Investor sentiment (投资者情绪) measures:

- Market turnover, IPO volume/first-day returns, closed-end fund discount, equity issuance, consumer confidence, media tone, survey indexes, VIX-like measures, or composite indexes.

Sentiment can condition anomaly strength:

- Optimistic sentiment can overprice speculative, small, growth, high-volatility, or lottery-like stocks.
- Pessimistic sentiment can favor defensive stocks and later reduce their expected returns if they become expensive.
- Sentiment regimes must be defined with information available at the time, not with hindsight labels.

Use sentiment as a conditioning variable, not as proof of causality by itself.

## Out-of-Sample Decay

Reasons factor returns decay:

- Publication and adoption arbitrage away mispricing.
- Crowding compresses valuation spreads and raises crash risk.
- Transaction costs, market impact, and shorting costs rise with use.
- Market structure or accounting rules change.
- The original result was p-hacked.

Crowding indicators:

- Extreme factor valuation spread.
- Rising correlation among factor portfolios or among residual returns inside long/short legs.
- Rising factor volatility.
- Large overlap with popular funds or indexes.
- Short interest, borrow cost, failed trades, or flow pressure where available.

Empirical Bayes idea for published factors:

- Published sample means are upward biased because successful factors are selected for publication.
- Shrink noisy factor means toward the cross-sectional average.
- Small standard-error factors receive less shrinkage; noisy factors receive more.

## Fundamental Analysis and Quantamental Limits

Quantamental investing uses accounting variables and systematic rules to imitate parts of fundamental analysis.

Benefits:

- Scales fundamental ideas across many stocks.
- Reduces discretion and style drift.
- Fits Smart Beta and multi-factor products.

Limits:

- Simple financial ratios are crude proxies for intrinsic value.
- Accounting data can be distorted by accruals, one-off items, industry differences, and reporting choices.
- Important information such as management quality, employee training, brand, R&D productivity, and competitive position is hard to reduce to a few factors.

Use factorized fundamentals as a starting point, not a full replacement for business analysis when the task requires company-level judgment.
