# Fundamental and Quantamental Analysis

## Contents

- [Purpose](#purpose)
- [Quantamental Role](#quantamental-role)
- [Why Simple Ratios Are Not Enough](#why-simple-ratios-are-not-enough)
- [Quality Index Signals](#quality-index-signals)
- [BIG5 Lesson](#big5-lesson)
- [Accounting Decomposition](#accounting-decomposition)
- [How to Use Fundamental Analysis in Factor Research](#how-to-use-fundamental-analysis-in-factor-research)
- [Output Pattern](#output-pattern)

## Purpose

Use this file when the user asks whether fundamental factor investing can replace fundamental analysis, how to improve value or quality factors with accounting logic, or how to avoid value traps and accounting-driven false signals.

This file compresses the chapter-6 discussion on quantamental investing and the limits of factorizing fundamental analysis.

## Quantamental Role

Quantamental investing (基本面量化投资) uses systematic accounting variables and portfolio rules to imitate parts of fundamental analysis at scale.

Useful roles:

- Turn broad accounting ideas into repeatable screens.
- Reduce discretionary style drift.
- Apply quality, value, profitability, growth, and balance-sheet logic to many stocks.
- Build Smart Beta or multi-factor products with transparent rules.

Limits:

- A few ratios are crude proxies for intrinsic value.
- Accounting data can be distorted by one-off events, classification choices, accruals, industry structure, and restatements.
- Important drivers such as brand, management quality, employee training, R&D productivity, product cycle, and competitive position are hard to compress into a few factors.
- A factor can identify a probability advantage across a diversified portfolio while still being wrong on many single stocks.

Practical rule:

- Use factorized fundamentals as a starting point for broad selection or risk control, not as a complete substitute for company-level business analysis when the decision depends on a specific firm.

## Why Simple Ratios Are Not Enough

A cheap stock can be:

- Mispriced because the market is too pessimistic.
- Cheap because business quality is poor.
- Cheap because reported earnings are temporarily inflated.
- Cheap because accounting values do not reflect economic asset quality.
- Cheap because of industry decline, governance issues, financial distress, or litigation risk.

A high-quality stock by simple accounting ratios can still be fragile when:

- Profitability was boosted by one-off events.
- Competitors' bankruptcy or exit temporarily improved margins.
- Political, regulatory, or inventory-cycle shocks pulled demand forward.
- Depreciation or asset accounting understates invested capital.
- Working-capital changes temporarily inflate operating cash flow.
- The business model is deteriorating faster than lagged accounting variables reveal.

Agent rule:

- When a value or quality factor looks strong, ask whether the accounting signal captures persistent business economics or a temporary measurement artifact.

## Quality Index Signals

Common quality indexes use multiple accounting dimensions rather than one ratio.

| Provider style | Common quality variables |
| --- | --- |
| MSCI-like | High ROE, low debt-to-equity, stable earnings growth |
| Russell-like | High ROA, improving asset turnover, low accruals, high operating cash flow to debt |
| Fidelity-like | High free-cash-flow margin, high return on invested capital, stable free cash flow |

Lessons:

- Quality is multi-dimensional: profitability, leverage, cash conversion, stability, and capital efficiency can point in different directions.
- Similar "quality" labels can hide different exposures.
- A quality index can still load on size, industry, low volatility, value, or growth.
- Always inspect holdings, exposures, concentration, turnover, and accounting definitions before accepting a product's label.

## BIG5 Lesson

The BIG5 Sporting Goods case shows why factorized fundamentals can fail.

Factor screen view:

- High value by `EP`, `BM`, or cash-flow yield.
- Positive momentum.
- Acceptable quality by `ROE`, debt ratio, accruals, or other simple metrics.
- Small-cap exposure that can improve factor ranks.

Fundamental analysis view:

- Competitor bankruptcies temporarily reduced competition and lifted reported performance.
- Political demand shocks temporarily boosted gun-related sales.
- Earnings improvement was not persistent.
- Property, plant, and equipment accounting understated invested capital.
- Recalculating capital and leverage changed the apparent quality conclusion.
- Working-capital and payables effects distorted cash-flow quality.

Agent rule:

- When a stock passes value, momentum, quality, and small-cap screens at the same time, check whether a temporary business event created the signal.
- Treat a single-company factor score as a hypothesis requiring business validation, not as a verdict.

## Accounting Decomposition

Use accounting decomposition to turn a crude factor into a better signal.

ROA can be decomposed as:

```text
ROA = net_income / total_assets
    = (net_income / revenue) * (revenue / total_assets)
```

Interpretation:

- `net_income / revenue`: margin or efficiency of converting sales into profit.
- `revenue / total_assets`: asset turnover or efficiency of using assets to generate sales.

Why it matters:

- High ROA from high margins can mean pricing power or strong cost control.
- High ROA from high turnover can mean efficient asset use.
- A firm with both healthy margins and high turnover is more persuasive than one with a single extreme component.
- Decomposition can expose accounting artifacts that a single ratio hides.

Other useful decompositions:

- ROE into profitability, asset turnover, and leverage.
- Earnings into cash-flow component and accrual component.
- Growth into organic revenue growth, margin change, and capital intensity.
- Free cash flow into operating cash flow, capex, and working-capital movements.

## How to Use Fundamental Analysis in Factor Research

For value factors:

- Add quality or distress screens to reduce value traps.
- Check whether low valuation comes from temporary pessimism or structural decline.
- Separate `BM`, `EP`, cash-flow yield, and dividend yield because they embed different accounting and payout assumptions.

For quality factors:

- Combine profitability, cash conversion, leverage, stability, and investment discipline.
- Use point-in-time restatements and avoid full-sample accounting corrections.
- Check industry comparability before ranking raw accounting ratios.

For growth factors:

- Distinguish sustainable growth from expensive extrapolation.
- Treat R&D, advertising, sales expense, and capex as possible investment, not only as current-period cost.
- Check whether growth comes from price, volume, acquisition, accounting change, or one-off demand.

For anomaly diagnosis:

- If a factor works only before controlling for fundamentals, it may be a low-quality or distress proxy.
- If a factor works mostly around earnings announcements, delayed fundamental information processing is plausible.
- If a factor fails after accounting decomposition, the original variable was likely too crude.

## Output Pattern

When advising on a fundamental or quantamental factor, return:

- The raw factor definition.
- The business interpretation.
- Accounting distortions to inspect.
- Suggested decompositions.
- Point-in-time data requirements.
- Controls: size, industry, leverage, profitability, investment, liquidity, and beta.
- Tests: IC, sorting, Fama-MacBeth, alpha tests, announcement-window evidence, and cost-adjusted portfolios.
- Verdict: broad portfolio signal, risk-control signal, company-analysis prompt, or reject.
