# Reasoning Playbooks

Use this file when the user asks for analysis, diagnosis, strategy design, improvement, or critique. For broad or ambiguous routing, read `task-router.md` first. Start with the smallest relevant playbook, then load other references as needed.

## Task Router

| User Task | First Questions | Load |
| --- | --- | --- |
| Explain a quant strategy | What is predicted, over what horizon, in what universe? | `black-box-framework.md`, `model-components.md` |
| Design a strategy | What edge should exist and what data can observe it before trading? | `model-components.md`, `metrics-formulas.md`, `checklists.md` |
| Review a backtest | What claim does the test prove, and what implementation assumptions are included? | `validation-risk-audit.md`, `metrics-formulas.md` |
| Diagnose a drawdown | Did alpha fail, risk move, cost rise, liquidity vanish, or execution break? | `validation-risk-audit.md`, `analysis-run-record.md` |
| Evaluate a quant manager | What is the edge, how is it researched, and can the team be trusted? | `validation-risk-audit.md`, `checklists.md`, `analysis-run-record.md` |
| Repair or promote a strategy | What baseline is frozen, what defect is diagnosed, and what stage gate applies? | `research-governance.md`, `analysis-run-record.md` |
| Analyze HFT or market microstructure | Which order-book mechanism creates the claimed effect? | `hft-market-structure.md`, `metrics-formulas.md` |
| Discuss criticism/regulation | What precise harm is claimed and what evidence would distinguish causes? | `validation-risk-audit.md`, `hft-market-structure.md` |

## Strategy Design Loop

1. State the exploitable behavior: trend continuation, mean reversion, structural arbitrage, liquidity provision, valuation spread, data advantage, or execution edge.
2. Convert the behavior into a measurable signal with timestamped inputs.
3. Define the tradable universe and filters before testing.
4. Decide the bet structure: absolute, relative, grouped, paired, factor-neutral, inventory, or queue-position.
5. Choose a horizon that matches the data frequency and expected signal decay.
6. Build a baseline simple enough to falsify.
7. Add risk, cost, portfolio, and execution rules only after the baseline defect is observed.
8. Validate sample-out, costs, capacity, and stress behavior before claiming edge.
9. Define live monitoring: signal decay, drawdown, crowding, data errors, cost drift, and execution slippage.

## Backtest Audit Loop

1. Reconstruct the decision timestamp: what did the model know, and when could it trade?
2. Reconstruct the universe: what assets were eligible at that historical time?
3. Recompute the signal with only point-in-time data.
4. Compare gross signal evidence to net executable evidence.
5. Decompose performance by alpha, beta, factor exposure, cost, liquidity, and residual.
6. Stress parameters, universe, rebalance timing, delay, transaction costs, and liquidity.
7. Check whether the strategy survives when the most favorable assumptions are removed.
8. State whether the backtest proves prediction, portfolio improvement, or only historical curve fit.

## Drawdown Diagnosis Loop

Ask in this order:

1. Did data or implementation break?
2. Did execution costs, spreads, market impact, borrow, or venue behavior change?
3. Did intended alpha stop working?
4. Did an unintended risk exposure dominate?
5. Did correlations, spreads, or structural relationships change?
6. Did exogenous events alter market rules or behavior?
7. Did crowding, liquidation, or financing pressure amplify losses?
8. Did risk controls force selling into stress?

Return the smallest targeted test: PnL attribution, factor exposure report, execution-cost replay, liquidity stress, signal-decay chart, or crowding proxy.

## Component Consistency Checks

Alpha and portfolio construction:

- If alpha outputs only direction, avoid pretending it contains reliable magnitude.
- If portfolio construction uses expected returns, verify the alpha model really estimates magnitudes.
- If a signal is relative, check that the grouping or hedge relation is stable.

Risk and alpha:

- If a risk exposure is intended and paid, call it alpha or beta exposure, not a risk to eliminate.
- If a risk exposure is unintended, require a limit, hedge, or monitoring rule.

Costs and horizon:

- High-turnover strategies require cost modeling before alpha claims.
- Long-horizon strategies still need costs, but capacity, borrow, and liquidation matter more.

Execution and research:

- If a backtest assumes close-to-close returns, verify the execution model can trade at that price.
- If a signal appears before market open, verify whether the model could know it before the opening price moved.

HFT and regulation:

- If a claim concerns front-running, distinguish non-public client-order information from faster public market data.
- If a claim concerns cancellation, distinguish stale-quote risk control from spoofing or manipulation.

## Evidence Strength Scale

- **Weak**: plausible story, in-sample return, no costs, no timestamp audit.
- **Developing**: clean signal evidence, some robustness, partial costs, no live proof.
- **Tradable candidate**: sample-out evidence, realistic costs, turnover, constraints, and risk attribution.
- **Portfolio candidate**: net performance improves existing portfolio after capacity, correlation, and drawdown checks.
- **Production candidate**: monitoring, kill switches, data QA, execution controls, and post-trade attribution exist.

Use this scale to keep conclusions calibrated.

## Common Agent Failure Modes

Avoid these mistakes:

- accepting a backtest as strategy validation;
- skipping data availability and timestamp checks;
- describing HFT moral arguments without order-book mechanics;
- treating a low-risk optimizer output as safe without input-sensitivity tests;
- using Sharpe or CAGR without drawdown, turnover, liquidity, and capacity;
- treating all quant strategies as market-neutral equity statistical arbitrage;
- ignoring human oversight, disaster response, and integrity in manager evaluation.
