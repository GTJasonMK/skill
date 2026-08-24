from __future__ import annotations

import pandas as pd
from hypothesis import given
from hypothesis import strategies as st

from data_quant.point_in_time import point_in_time_join


def test_join_selects_latest_observable_record() -> None:
    decisions = pd.DataFrame(
        {
            "asset": ["A", "A"],
            "decision": ["2024-01-05T00:00:00Z", "2024-01-10T00:00:00Z"],
        }
    )
    records = pd.DataFrame(
        {
            "asset": ["A", "A", "A"],
            "available": ["2024-01-01T00:00:00Z", "2024-01-07T00:00:00Z", "2024-01-12T00:00:00Z"],
            "value": [1.0, 2.0, 3.0],
        }
    )
    joined = point_in_time_join(
        decisions,
        records,
        entity_col="asset",
        decision_time_col="decision",
        available_time_col="available",
    )
    assert joined["value"].tolist() == [1.0, 2.0]
    assert (joined["_observable_at"] <= joined["decision"]).all()


@given(
    decision_day=st.integers(min_value=2, max_value=28),
    record_days=st.lists(st.integers(min_value=1, max_value=31), min_size=1, max_size=12, unique=True),
)
def test_join_never_selects_future_record(decision_day: int, record_days: list[int]) -> None:
    decisions = pd.DataFrame({"asset": ["A"], "decision": [f"2024-01-{decision_day:02d}T00:00:00Z"]})
    records = pd.DataFrame(
        {
            "asset": ["A"] * len(record_days),
            "available": [f"2024-01-{day:02d}T00:00:00Z" for day in record_days],
            "value": record_days,
        }
    )
    joined = point_in_time_join(
        decisions,
        records,
        entity_col="asset",
        decision_time_col="decision",
        available_time_col="available",
    )
    observable = joined.loc[0, "_observable_at"]
    if pd.notna(observable):
        assert observable <= joined.loc[0, "decision"]
