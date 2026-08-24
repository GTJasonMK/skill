from __future__ import annotations

import pandas as pd
import pytest

from data_quant.contracts.tables import get_table_contract
from data_quant.io.validation import canonicalize_table


def bars_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": ["2024-01-02T08:00:00+00:00", "2024-01-03T08:00:00+00:00"],
            "asset_id": ["A", "A"],
            "close": [10.0, 10.5],
            "currency": ["CNY", "CNY"],
            "adjustment_state": ["raw", "raw"],
        }
    )


def test_canonicalize_parses_utc_timestamps() -> None:
    table = canonicalize_table(bars_frame(), get_table_contract("market_bars"))
    assert str(table.frame["timestamp"].dtype) == "datetime64[us, UTC]"


def test_duplicate_primary_keys_fail() -> None:
    frame = pd.concat([bars_frame().iloc[[0]], bars_frame().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="Duplicate primary keys"):
        canonicalize_table(frame, get_table_contract("market_bars"))


def test_ambiguous_or_invalid_timestamp_fails() -> None:
    frame = bars_frame()
    frame.loc[0, "timestamp"] = "not-a-date"
    with pytest.raises(ValueError, match="unparseable"):
        canonicalize_table(frame, get_table_contract("market_bars"))


def test_naive_timestamp_is_not_silently_assumed_to_be_utc() -> None:
    frame = bars_frame()
    frame.loc[0, "timestamp"] = "2024-01-02 08:00:00"
    with pytest.raises(ValueError, match="explicit timezone"):
        canonicalize_table(frame, get_table_contract("market_bars"))
