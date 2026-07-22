# Method Idea Anchors

Use when: the agent needs a fast conceptual anchor before selecting a factor method, proposing a strategy entrypoint, diagnosing a result, or explaining why a method fits the available data.

Purpose: keep factor work grounded in first principles. These anchors are not formulas or recipes; they are the center ideas that should shape the next empirical question.

## Contents

- [How to Use](#how-to-use)
- [Research Method Anchors](#research-method-anchors)
- [Factor Family Anchors](#factor-family-anchors)
- [Anomaly and Behavioral Anchors](#anomaly-and-behavioral-anchors)
- [Model Anchors](#model-anchors)
- [Portfolio and Product Anchors](#portfolio-and-product-anchors)
- [Machine-Learning Anchors](#machine-learning-anchors)

## How to Use

Before proposing a test or strategy, pick one primary anchor:

1. State the method's center idea in one sentence.
2. Name the object: characteristic, exposure, factor return, pricing factor, prediction variable, portfolio alpha, or risk-control rule.
3. Choose the first empirical question that can falsify the idea.
4. Check the common misuse before adding complexity.

If several anchors seem plausible, prefer the one with cleaner timing, clearer mechanism, lower cost sensitivity, and the fastest falsification test.

## Research Method Anchors

| Method | Center idea | First empirical question | Common misuse |
| --- | --- | --- | --- |
| Point-in-time panel | A factor is only valid if inputs were observable before the trade. | Can every field be tied to announcement, vendor-availability, or market timestamp? | Using fiscal-period-end, current constituents, or restated fields as if they were known. |
| Single sorting | Sorts show the raw shape of a signal's return relation. | Are quantile returns monotonic, stable, and not driven by one tail? | Treating top-minus-bottom spread as executable PnL. |
| Multi-sorting | A target signal should survive a known confounder. | Does the target spread remain inside size, value, liquidity, industry, or profitability buckets? | Creating sparse cells and mistaking noise for control. |
| IC/rank IC | A prediction variable should rank assets before it builds a portfolio. | Is IC stable across dates, horizons, and subuniverses? | Ignoring turnover, costs, dispersion, and portfolio constraints. |
| Time-series regression | A portfolio alpha is residual return after known factor exposures. | Does alpha survive benchmark factors with robust standard errors? | Treating regression alpha as tradable alpha before costs and capacity. |
| Cross-sectional regression | Characteristics or exposures should explain return differences across assets. | Is the coefficient stable across dates after controls? | Pooled IID t-stats, hidden timing errors, and uncontrolled correlated residuals. |
| Fama-MacBeth | Estimate cross-sectional premia date by date, then test average premia over time. | Do average coefficients survive HAC/Newey-West when returns overlap? | Treating estimated beta errors and control-order changes as harmless. |
| GRS and alpha tests | A pricing model should leave no systematic test-asset alpha. | Are joint and average alphas smaller under the candidate model? | Calling the highest in-sample fit the best model without parsimony. |
| Mean-variance spanning | A new asset or factor matters if it expands the investment opportunity set. | Does adding it improve the mean-variance frontier after estimation error? | Confusing spanning with anomaly significance. |
| Orthogonalization/neutralization | Residualization asks whether a signal adds information beyond controls. | Does residual alpha remain after naming the base set and order? | Removing the intended economic content or using full-sample coefficients. |
| GMM | Moment conditions unify estimation and model testing. | Are the moments economically justified and identified? | Using GMM as a black box without stating moments, weights, and J-test meaning. |
| Bayesian priors and p-hacking control | A t-stat is weaker when many factors were searched or prior plausibility is low. | What was the tested family, and do adjusted p-values or posterior odds still support it? | Treating `t ~= 2` as discovery proof. |

## Factor Family Anchors

| Factor family | Center idea | First empirical question | Common misuse |
| --- | --- | --- | --- |
| Market beta | Systematic market risk explains much time-series variation. | Is the claim about risk exposure, expected return, or unexplained alpha? | Treating CAPM failure as permission to accept any anomaly. |
| Size | Small stocks may earn premia because of risk, neglect, liquidity, or market frictions. | Does evidence survive value-weighting, microcap exclusion, liquidity, and capacity checks? | Letting equal-weight microcaps dominate the result. |
| Value | Cheap prices can reflect risk compensation or investor overreaction. | Does cheapness work after quality, profitability, leverage, industry, and value-trap checks? | Treating every low valuation as undervaluation. |
| Profitability | Persistent cash-flow strength can predict returns and improve value interpretation. | Which dimension works: level, quality, stability, growth, or cash conversion? | Collapsing ROE, ROA, GP, accrual quality, and growth into one vague quality label. |
| Investment | Aggressive investment can imply lower expected returns, holding profitability fixed. | Does investment retain the expected sign after profitability and M&A controls? | Importing U.S. investment evidence without A-share transferability checks. |
| Momentum | Prices can underreact to information and continue, but reversal and crash risk matter. | Does skip-month or residual momentum work after cost and crash diagnostics? | Including the latest reversal-prone month and calling it momentum. |
| Reversal | Short-horizon overreaction can reverse, especially where speculation is strong. | Is the horizon truly short and executable after costs? | Mixing reversal with long-horizon value or liquidity effects. |
| Turnover and speculation | High abnormal trading can reflect optimism, attention, disagreement, or lottery demand. | Does the sign differ by horizon, and is long/short leg tradable? | Treating turnover as pure liquidity. |
| Liquidity and Amihud | Illiquidity may earn compensation but is expensive to trade. | Is the premium still positive after market impact and capacity limits? | Capturing a paper premium that cannot be scaled. |
| Low beta and low volatility | Leverage constraints and lottery demand can make high-risk stocks overpriced. | Is performance from long-only defensive exposure or untradeable high-risk short leg? | Calling low-vol alpha without beta, size, price, turnover, and short-leg checks. |
| Idiosyncratic volatility | High residual volatility can be overpriced because of lottery demand and shorting frictions. | Does low-IVOL survive factor-model choice, MAX/skewness, liquidity, and beta controls? | Estimating IVOL from too few observations or suspension-tainted returns. |
| Skewness, MAX, and lottery | Investors may overpay for right-tail payoff profiles. | Does skewness/MAX explain high-IVOL or speculative-stock underperformance? | Treating lottery demand as risk compensation without shorting-friction evidence. |
| Accruals and earnings quality | Accounting profits are weaker when not backed by cash flow. | Do accrual quality and cash-flow profitability add beyond valuation and profitability level? | Using restated financials or ignoring announcement timing. |
| Dividend | Dividend yield can mix value, quality, maturity, and payout policy. | Is it distinct from value and low-volatility exposure? | Treating dividend yield as a pure income factor. |

## Anomaly and Behavioral Anchors

| Anomaly or mechanism | Center idea | First empirical question | Common misuse |
| --- | --- | --- | --- |
| F-Score | Cheap stocks are safer when fundamentals are improving. | Among high-BM stocks, does high F-Score avoid value traps? | Using F-Score as a standalone quality factor without value context. |
| G-Score | Expensive growth stocks can still be attractive when fundamentals justify expectations. | Among low-BM/growth stocks, does G-Score separate quality growth from glamour overpricing? | Rejecting all expensive stocks mechanically. |
| Expectation gap | Alpha comes from mismatch between market expectation and fundamental expectation. | Do high-BM/high-quality and low-BM/low-quality corners drive the spread? | Calling any value-plus-quality combination an expectation-gap strategy. |
| Fundamental anchoring reversal | Prices that deviate too far from a fundamental anchor may reverse. | Is the anchor observable and distinct from ordinary value or reversal? | Using future fundamentals as anchors. |
| PEAD and earnings momentum | Investors underreact to earnings news and revisions. | Does drift appear after announcement timing and attention controls? | Using accounting data before public release. |
| Investor sentiment | Sentiment can condition anomaly payoffs and mispricing severity. | Is the effect stronger in hard-to-arbitrage, speculative, or retail-dominated names? | Data-mining sentiment indicators without a prior channel. |
| Limited attention | Investors process salient or crowded information slowly. | Do announcement timing, media, analyst, or attention proxies explain drift? | Labeling any delayed return pattern as attention. |
| Disposition effect and CGO | Investors' unrealized gains/losses can create selling pressure and continuation/reversal. | Does capital gains overhang condition momentum or reversal profits? | Ignoring tax, investor base, and turnover differences. |
| Overconfidence and disagreement | High disagreement can fuel trading, issuance, and overpricing. | Do turnover, analyst dispersion, issuance, or short-sale constraints align with the return pattern? | Treating disagreement proxies as universal risk signals. |

## Model Anchors

| Model | Center idea | First empirical question | Common misuse |
| --- | --- | --- | --- |
| CAPM | One market factor prices expected excess return through beta. | Does beta explain time-series variation or cross-sectional premia in this sample? | Using CAPM alpha as final anomaly evidence. |
| Fama-French 3-factor | Size and value explain major CAPM pricing errors. | Does the result survive market, SMB, and HML exposure? | Forgetting profitability, investment, momentum, and local factors. |
| Carhart 4-factor | Momentum is a separate exposure needed for performance attribution. | Does the strategy load on skipped-month momentum? | Using momentum factor without reversal contamination checks. |
| Novy-Marx profitability | Gross profitability captures cleaner production strength than noisy net income. | Does GP explain returns beyond value and momentum? | Treating all profitability ratios as interchangeable. |
| Fama-French 5-factor | Valuation identities link expected return to BM, profitability, and investment. | Does adding profitability and investment reduce alphas parsimoniously? | Assuming HML redundancy or investment strength transfers to all markets. |
| Hou-Xue-Zhang q/q5 | Investment-based pricing links expected return to profitability and investment decisions. | Does profitability-investment sorting explain test assets better than FF-style models? | Ignoring local accounting and investment-construction sensitivity. |
| Stambaugh-Yuan | Many anomalies share broader mispricing-management and performance dimensions. | Does grouping anomalies reduce redundant factor zoo claims? | Treating anomaly aggregation as proof of investable alpha. |
| Daniel-Hirshleifer-Sun | Financing behavior and PEAD capture behavioral underreaction/mispricing channels. | Do FIN and PEAD explain anomaly returns and event drift? | Mixing long-horizon financing and short-horizon announcement effects. |
| CHN/LSL A-share models | Local markets need local size/value/profitability construction and shell-value caution. | Does the model handle smallest-stock contamination, EP/BM differences, and local profitability evidence? | Copying U.S. factor definitions mechanically into A shares. |

## Portfolio and Product Anchors

| Practice method | Center idea | First empirical question | Common misuse |
| --- | --- | --- | --- |
| Return model | Convert prediction variables into an expected-return vector. | Does each variable pass logic, persistence, incremental value, robustness, investability, and universality checks? | Treating a list of good indicators as a forecast model. |
| Investable universe optimization | The stock pool can itself embed alpha and risk control. | How much result comes from exclusions versus ranking? | Applying future or unversioned filters before ranking. |
| Screening versus ranking | Screens are interpretable; ranks are smoother and easier to combine. | Does the method need hard eligibility or continuous ordering? | Creating arbitrary thresholds that overfit regimes. |
| Parametric alpha forecast | Expected alpha scales with IC, cross-sectional opportunity, and standardized score. | Is forecast scale consistent with horizon, dispersion, and constraints? | Feeding raw scores directly into an optimizer. |
| Barra-style risk model | Risk factors forecast covariance and explain common return variation. | Are exposures, factor covariance, and specific risk calibrated for portfolio use? | Judging a risk model by factor premia instead of risk forecast quality. |
| Pure factor portfolio | Isolate one exposure while neutralizing others. | Is target exposure strong and non-target exposure controlled? | Assuming pure factor portfolios are cheap, scalable products. |
| Covariance shrinkage and adjustment | Noisy risk estimates need stabilization. | Does shrinkage improve out-of-sample risk calibration and optimizer stability? | Overfitting covariance to in-sample returns. |
| Portfolio optimization | Convert alpha, risk, costs, and constraints into holdings. | Are expected returns and risk forecasts on compatible scales? | Letting tiny alpha differences drive extreme turnover. |
| Transaction-cost model | Net alpha is gross alpha minus explicit and implicit trading costs. | Does performance survive spread, slippage, impact, tax, borrow, and participation limits? | Adding costs after choosing a high-turnover strategy. |
| Capacity analysis | A strategy is only investable up to liquidity and impact limits. | At what NAV does ADV participation or impact bind? | Reporting Sharpe without scalable capital. |
| Smart Beta | Turn factor evidence into transparent long-only product rules. | Does the product keep target exposure while staying liquid, diversified, and low-turnover? | Equating academic long-short alpha with ETF return. |
| Mixing versus integration | Multi-factor exposure can be held as sleeves or integrated stock scores. | Is transparency, turnover, factor purity, or stock-level efficiency more important? | Assuming integrated scoring is always superior. |
| Factor allocation weighting | Factor sleeves need weights, but estimates are noisy. | Does a complex weighting scheme beat equal weight out of sample after turnover? | Optimizing factor weights on short histories. |
| Factor timing | Time-varying factor returns may be predicted by valuation, momentum, volatility, sentiment, or macro state. | Does timing improve net results without data revisions, few-regime overfit, or crowding risk? | Treating factor valuation spreads as short-term timing signals. |
| Style analysis | Holdings or returns can reveal what exposures a fund actually owns. | Are realized returns explained by intended or unintended styles? | Calling residual return skill before model and benchmark sensitivity checks. |
| Risk attribution | Decompose risk into factor, industry, specific, and concentration sources. | Which exposure contributes marginal and component risk? | Confusing return contribution with risk contribution. |

## Machine-Learning Anchors

| ML method | Center idea | First empirical question | Common misuse |
| --- | --- | --- | --- |
| Regularized linear models | Shrink or select many correlated factor features. | Do ridge/lasso/elastic net beat simple factor scores out of sample? | Treating selected variables as stable economic truths. |
| Robust regression | Heavy-tailed returns need loss functions that limit extreme residual influence. | Does robust loss improve OOS ranking without deleting stress information? | Removing economically important crash periods. |
| Trees and boosting | Nonlinear interactions can matter in tabular factor panels. | Do tree/boosting models add net alpha beyond linear baselines and known exposures? | Accepting feature importance without exposure and leakage checks. |
| Neural networks | Flexible nonlinear models need scale, regularization, and strict validation. | Is there enough data and an untouched final test? | Using complex models to hide weak economic structure. |
| Mixed forecasts | Combining models can reduce specification dependence. | Does the ensemble beat the best simple model using only OOS predictions? | Averaging many searched models to hide p-hacking. |
| PCA and latent factors | Covariance can reveal hidden common return drivers. | Are latent factors stable, interpretable, and useful for risk or prediction? | Treating rotated components as named economic factors. |
| IPCA | Characteristics can instrument time-varying exposures to latent factors. | Do instruments improve pricing or prediction without overfit? | Forgetting identification and rotation ambiguity. |
| OOS `R^2` and forecast tests | Forecast quality must beat a fair baseline. | Does the model beat zero/historical-mean baselines and produce tradable net portfolios? | Reporting prediction loss without IC, turnover, cost, drawdown, and exposure checks. |
