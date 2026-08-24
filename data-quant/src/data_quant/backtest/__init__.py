"""Vectorized and offline event-driven backtesting."""

from .execution_aware import ExecutionAwareResult, run_execution_aware_backtest
from .portfolio import PortfolioBacktestResult, run_portfolio_backtest

__all__ = [
    "ExecutionAwareResult",
    "PortfolioBacktestResult",
    "run_execution_aware_backtest",
    "run_portfolio_backtest",
]
