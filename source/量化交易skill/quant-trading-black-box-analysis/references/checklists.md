# Checklists And Deliverables

## Strategy Design Memo

Use this structure:

1. Objective and claim.
2. Universe and tradability.
3. Horizon and rebalance timing.
4. Alpha hypothesis and economic intuition.
5. Signal construction and direction.
6. Data sources, timestamps, and cleaning.
7. Risk exposures and limits.
8. Transaction-cost assumptions.
9. Portfolio construction method.
10. Execution method.
11. Validation tests.
12. Stress tests and failure modes.
13. Capacity and monitoring.
14. Decision: build, reject, or experiment.

Add a one-line "claim side" near the top: prediction claim, risk-model claim, cost-model claim, optimizer claim, execution claim, liquidity-provision claim, or manager-quality claim. This prevents evidence for one claim from being used to prove another.

## Backtest Audit Checklist

- Is every input available at the simulated decision time?
- Are delisted, suspended, unborrowable, or illiquid assets handled correctly?
- Is the universe reconstructed historically?
- Are corporate actions and identifiers clean?
- Are transaction costs, slippage, impact, and turnover included?
- Are shorting and borrow constraints realistic?
- Are parameters chosen before the sample-out period?
- Are results robust to small parameter changes?
- Is performance decomposed by factor, alpha, beta, cost, and residual?
- Does the strategy work after delay assumptions?
- Does the strategy survive stress periods?
- Is capacity estimated from volume, spread, participation, and liquidation time?
- Is the reported performance gross or net, and does it include financing, borrow, rebates, and failed fills?
- Can the strategy still trade after adding realistic signal delay and execution latency?
- Does the test prove a standalone strategy, or only a component that still needs portfolio and execution validation?

## Quant Manager Interview Questions

Research:

- How do ideas enter the research pipeline?
- What rejects an idea?
- What is the production approval process?
- How do you avoid overfitting?

Data:

- What are the data sources?
- How are timestamps, revisions, missing values, and corporate actions handled?
- How do you test data quality?

Alpha:

- What type of alpha is this?
- Why should it exist?
- What is the horizon?
- What destroys it?

Portfolio construction:

- How are positions sized?
- What objective function or rules are used?
- What constraints matter most?
- Why can an alpha-positive asset become short?

Execution:

- Which orders and venues are used?
- How is urgency chosen?
- How are slippage and market impact measured?
- What happens when liquidity disappears?

Risk:

- What are intended and unintended exposures?
- What are the limits?
- What triggers intervention?
- How are drawdowns attributed?
- How do limits behave during stress: do they reduce risk or force liquidation into bad liquidity?

Integrity:

- What can be independently verified?
- Are answers consistent across meetings?
- Does the manager behave like a fiduciary?

## HFT Analysis Checklist

- Identify passive vs aggressive behavior.
- Define the exact order-book state and queue priority.
- Identify latency-critical steps.
- Estimate spread, rebate, adverse selection, and inventory effects.
- Check whether edge survives tail latency and data bursts.
- Separate market making, arbitrage, and fast alpha.
- For controversy claims, specify the mechanism and evidence.
- For front-running claims, state whether the alleged information is non-public client flow or faster public market data.
- For cancellation claims, distinguish stale-quote avoidance, queue management, venue fragmentation, and manipulative intent.
- For volatility claims, compare intraday, overnight, close-to-close, and high-low measures.

## Final Verdict Format

Use one of:

- **Build**: evidence supports a controlled experiment or implementation.
- **Investigate**: hypothesis is plausible but key evidence is missing.
- **Modify**: idea is useful but component design is flawed.
- **Reject**: claim is unsupported, non-tradable, too costly, or too fragile.
- **Monitor**: live strategy is acceptable but needs specific risk triggers.

Always include:

- what would change the verdict;
- strongest remaining risk;
- smallest next test that reduces uncertainty.

## Minimal Next Tests

Choose one:

- timestamp audit for leakage suspicion;
- cost replay for high-turnover strategies;
- delay test for fast-decaying signals;
- parameter grid for overfitting suspicion;
- factor/PnL attribution for unexplained drawdown;
- liquidity liquidation test for capacity claims;
- order-book replay for HFT claims;
- manager follow-up questions for diligence gaps.
