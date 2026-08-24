from __future__ import annotations

import pandas as pd
import pytest

from data_quant.backtest import run_execution_aware_backtest


def _weights_and_quotes() -> tuple[pd.DataFrame, pd.DataFrame]:
    weights = pd.DataFrame(
        {
            "decision_at": ["2024-01-01T00:00:00Z"] * 2 + ["2024-01-02T00:00:00Z"] * 2,
            "asset_id": ["A", "B", "A", "B"],
            "weight": [0.5, 0.5, 0.0, 1.0],
            "weight_type": ["target"] * 4,
            "currency": ["USD"] * 4,
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-01T00:00:01Z"] * 2 + ["2024-01-02T00:00:01Z"] * 2,
            "asset_id": ["A", "B", "A", "B"],
            "bid": [99.0, 49.0, 99.0, 49.0],
            "ask": [101.0, 51.0, 101.0, 51.0],
            "volume": [10000.0] * 4,
            "currency": ["USD"] * 4,
        }
    )
    return weights, quotes


def test_execution_aware_carries_nav_across_periods() -> None:
    weights, quotes = _weights_and_quotes()
    result = run_execution_aware_backtest(
        weights, quotes, weight_type="target", initial_cash=10000.0, lot_size=1.0
    )
    assert len(result.periods) == 2
    # Buy/sell spread erodes NAV even with zero commission; the second period's
    # opening NAV must equal the first period's closing NAV.
    assert result.periods.loc[1, "nav_before"] == pytest.approx(result.periods.loc[0, "nav_after"])
    assert result.final_nav < 10000.0
    assert result.total_traded_notional > 0


def test_execution_aware_applies_commission() -> None:
    weights, quotes = _weights_and_quotes()
    free = run_execution_aware_backtest(
        weights, quotes, weight_type="target", initial_cash=10000.0, commission_bps=0.0
    )
    paid = run_execution_aware_backtest(
        weights, quotes, weight_type="target", initial_cash=10000.0, commission_bps=10.0
    )
    assert paid.total_fees > free.total_fees
    assert paid.final_nav < free.final_nav


def test_execution_aware_enforces_lot_size() -> None:
    weights, quotes = _weights_and_quotes()
    # Large lot size means no trade reaches a full lot, so no fills occur and
    # NAV stays at initial cash.
    result = run_execution_aware_backtest(
        weights, quotes, weight_type="target", initial_cash=10000.0, lot_size=100000.0
    )
    assert result.total_traded_notional == 0.0
    assert result.final_nav == pytest.approx(10000.0)


def test_execution_aware_requires_marks_for_held_assets() -> None:
    weights = pd.DataFrame(
        {
            "decision_at": ["2024-01-01T00:00:00Z"],
            "asset_id": ["A"],
            "weight": [1.0],
            "weight_type": ["target"],
            "currency": ["USD"],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-01T00:00:01Z"],
            "asset_id": ["B"],  # no mark for A
            "bid": [9.0],
            "ask": [11.0],
            "volume": [100.0],
            "currency": ["USD"],
        }
    )
    with pytest.raises(ValueError, match="No mark available"):
        run_execution_aware_backtest(
            weights, quotes, weight_type="target", initial_cash=1000.0
        )
