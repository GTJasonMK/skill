from __future__ import annotations

import pandas as pd
import pytest

from data_quant.labels import build_forward_returns


def test_forward_returns_preserve_timestamps_and_currency() -> None:
    prices = pd.DataFrame(
        {
            "asset": ["A", "A", "A"],
            "ts": ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z", "2024-01-03T00:00:00Z"],
            "price": [100.0, 110.0, 121.0],
        }
    )
    labels = build_forward_returns(
        prices,
        asset_col="asset",
        timestamp_col="ts",
        price_col="price",
        horizon=1,
        label="return_1d",
        currency="CNY",
        expected_step=pd.Timedelta(days=1),
    )
    assert labels["return_value"].round(8).tolist() == [0.1, 0.1]
    assert labels["currency"].tolist() == ["CNY", "CNY"]
    assert labels["return_basis"].tolist() == ["gross", "gross"]
    assert labels["corporate_action_policy"].tolist() == ["price_return", "price_return"]


def test_gap_is_not_bridged_without_explicit_policy() -> None:
    prices = pd.DataFrame(
        {
            "asset": ["A", "A", "A"],
            "ts": ["2024-01-01T00:00:00Z", "2024-01-03T00:00:00Z", "2024-01-04T00:00:00Z"],
            "price": [100.0, 121.0, 133.1],
        }
    )
    labels = build_forward_returns(
        prices,
        asset_col="asset",
        timestamp_col="ts",
        price_col="price",
        horizon=1,
        label="return_1d",
        expected_step=pd.Timedelta(days=1),
    )
    assert labels["decision_at"].dt.day.tolist() == [3]
    assert labels["return_value"].round(8).tolist() == [0.1]


def test_excess_return_labels_require_benchmark() -> None:
    prices = pd.DataFrame(
        {
            "asset": ["A", "A"],
            "ts": ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"],
            "price": [100.0, 101.0],
        }
    )
    with pytest.raises(ValueError, match="require a benchmark"):
        build_forward_returns(
            prices,
            asset_col="asset",
            timestamp_col="ts",
            price_col="price",
            horizon=1,
            label="excess_1d",
            return_basis="excess",
        )
