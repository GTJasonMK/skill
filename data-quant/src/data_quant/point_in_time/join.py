"""Leakage-resistant point-in-time joins."""

from __future__ import annotations

import pandas as pd

from data_quant.io.validation import parse_utc_timestamp


def point_in_time_join(
    decisions: pd.DataFrame,
    records: pd.DataFrame,
    *,
    entity_col: str,
    decision_time_col: str,
    available_time_col: str,
    revision_time_col: str | None = None,
    suffix: str = "_record",
) -> pd.DataFrame:
    """Attach the latest record observable at each decision time.

    A record is observable at max(available_time, revision_time) when a revision
    timestamp is supplied. The join never selects a record observable after the
    decision timestamp.
    """

    left = decisions.copy()
    right = records.copy()
    for frame, columns in (
        (left, [entity_col, decision_time_col]),
        (right, [entity_col, available_time_col] + ([revision_time_col] if revision_time_col else [])),
    ):
        missing = [column for column in columns if column not in frame.columns]
        if missing:
            raise ValueError(f"Point-in-time join missing columns: {missing}")

    left[decision_time_col] = parse_utc_timestamp(left[decision_time_col], decision_time_col)
    right[available_time_col] = parse_utc_timestamp(right[available_time_col], available_time_col)
    right["_observable_at"] = right[available_time_col]
    if revision_time_col:
        right[revision_time_col] = parse_utc_timestamp(right[revision_time_col], revision_time_col)
        right["_observable_at"] = right[[available_time_col, revision_time_col]].max(axis=1)

    if left[[entity_col, decision_time_col]].isna().any().any():
        raise ValueError("Decision entity and time cannot be missing.")
    if right[[entity_col, "_observable_at"]].isna().any().any():
        raise ValueError("Record entity and observable time cannot be missing.")

    left["_pit_order"] = range(len(left))
    left = left.sort_values([decision_time_col, entity_col])
    right = right.sort_values(["_observable_at", entity_col])
    overlapping = [
        column
        for column in right.columns
        if column in left.columns and column not in {entity_col, available_time_col, revision_time_col}
    ]
    right = right.rename(columns={column: f"{column}{suffix}" for column in overlapping})

    joined = pd.merge_asof(
        left,
        right,
        left_on=decision_time_col,
        right_on="_observable_at",
        by=entity_col,
        direction="backward",
        allow_exact_matches=True,
        suffixes=("", suffix),
    )
    leaked = joined["_observable_at"].notna() & (joined["_observable_at"] > joined[decision_time_col])
    if leaked.any():  # defensive invariant
        raise AssertionError("Point-in-time join selected a future record.")
    return joined.sort_values("_pit_order").drop(columns=["_pit_order"]).reset_index(drop=True)
