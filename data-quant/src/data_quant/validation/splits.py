"""Purged and embargoed time-aware validation splitters."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd

from data_quant.io.validation import parse_utc_timestamp

ZERO_EMBARGO = pd.Timedelta(0)


@dataclass(frozen=True)
class TimeFold:
    fold: int
    train_positions: tuple[int, ...]
    test_positions: tuple[int, ...]
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    purged_count: int
    embargoed_count: int


def _canonical_times(
    frame: pd.DataFrame,
    observation_time_col: str,
    label_end_time_col: str,
) -> tuple[pd.Series, pd.Series]:
    missing = [
        column
        for column in (observation_time_col, label_end_time_col)
        if column not in frame.columns
    ]
    if missing:
        raise ValueError(f"Validation frame missing columns: {missing}")
    observations = parse_utc_timestamp(frame[observation_time_col], observation_time_col)
    label_ends = parse_utc_timestamp(frame[label_end_time_col], label_end_time_col)
    if observations.isna().any() or label_ends.isna().any():
        raise ValueError("Observation and label-end times cannot be missing.")
    if (label_ends < observations).any():
        raise ValueError("Every label-end time must be no earlier than its observation time.")
    return observations, label_ends


def purged_walk_forward_split(
    frame: pd.DataFrame,
    *,
    observation_time_col: str,
    label_end_time_col: str,
    train_periods: int,
    test_periods: int,
    step_periods: int | None = None,
    embargo: pd.Timedelta = ZERO_EMBARGO,
    expanding: bool = False,
) -> list[TimeFold]:
    if train_periods <= 0 or test_periods <= 0:
        raise ValueError("train_periods and test_periods must be positive.")
    if embargo < pd.Timedelta(0):
        raise ValueError("embargo must be non-negative.")
    step = test_periods if step_periods is None else step_periods
    if step <= 0:
        raise ValueError("step_periods must be positive.")

    observations, label_ends = _canonical_times(frame, observation_time_col, label_end_time_col)
    unique_times = pd.DatetimeIndex(sorted(observations.unique()))
    if len(unique_times) < train_periods + test_periods:
        raise ValueError("Not enough unique observation periods for the requested split.")

    folds: list[TimeFold] = []
    start = train_periods
    while start + test_periods <= len(unique_times):
        test_times = unique_times[start : start + test_periods]
        train_times = unique_times[:start] if expanding else unique_times[start - train_periods : start]
        test_start = test_times[0]
        test_end = test_times[-1]
        train_candidate = observations.isin(train_times)
        overlap = train_candidate & (label_ends >= test_start)
        embargoed = train_candidate & (observations > test_start - embargo)
        train_mask = train_candidate & ~overlap & ~embargoed
        test_mask = observations.isin(test_times)

        train_positions = tuple(np.flatnonzero(train_mask.to_numpy()).tolist())
        test_positions = tuple(np.flatnonzero(test_mask.to_numpy()).tolist())
        if not train_positions:
            raise ValueError(f"Fold {len(folds) + 1} has no training rows after purging/embargo.")
        if not test_positions:
            raise ValueError(f"Fold {len(folds) + 1} has no test rows.")
        train_obs = observations.iloc[list(train_positions)]
        train_end_values = label_ends.iloc[list(train_positions)]
        if train_end_values.max() >= test_start:
            raise AssertionError("Purged split retained a training label that overlaps the test window.")

        folds.append(
            TimeFold(
                fold=len(folds) + 1,
                train_positions=train_positions,
                test_positions=test_positions,
                train_start=train_obs.min(),
                train_end=train_obs.max(),
                test_start=test_start,
                test_end=test_end,
                purged_count=int(overlap.sum()),
                embargoed_count=int((embargoed & ~overlap).sum()),
            )
        )
        start += step
    return folds


def combinatorial_purged_split(
    frame: pd.DataFrame,
    *,
    observation_time_col: str,
    label_end_time_col: str,
    block_count: int,
    test_block_count: int,
    embargo: pd.Timedelta = ZERO_EMBARGO,
) -> list[TimeFold]:
    if block_count < 2:
        raise ValueError("block_count must be at least 2.")
    if not 1 <= test_block_count < block_count:
        raise ValueError("test_block_count must be between 1 and block_count - 1.")
    if embargo < pd.Timedelta(0):
        raise ValueError("embargo must be non-negative.")

    observations, label_ends = _canonical_times(frame, observation_time_col, label_end_time_col)
    unique_times = pd.DatetimeIndex(sorted(observations.unique()))
    blocks = [pd.DatetimeIndex(values) for values in np.array_split(unique_times, block_count) if len(values)]
    if len(blocks) != block_count:
        raise ValueError("Not enough unique periods to populate every block.")

    folds: list[TimeFold] = []
    for selected in combinations(range(block_count), test_block_count):
        test_times = blocks[selected[0]]
        for block_index in selected[1:]:
            test_times = test_times.append(blocks[block_index])
        test_mask = observations.isin(test_times)
        train_mask = ~test_mask
        purged = pd.Series(False, index=frame.index)
        embargoed = pd.Series(False, index=frame.index)
        for block_index in selected:
            block_start = blocks[block_index][0]
            block_end = blocks[block_index][-1]
            purged |= train_mask & (observations <= block_end) & (label_ends >= block_start)
            if embargo > pd.Timedelta(0):
                embargoed |= train_mask & (observations > block_end) & (observations <= block_end + embargo)
        final_train = train_mask & ~purged & ~embargoed
        train_positions = tuple(np.flatnonzero(final_train.to_numpy()).tolist())
        test_positions = tuple(np.flatnonzero(test_mask.to_numpy()).tolist())
        if not train_positions or not test_positions:
            continue
        train_obs = observations.iloc[list(train_positions)]
        selected_test_obs = observations.iloc[list(test_positions)]
        folds.append(
            TimeFold(
                fold=len(folds) + 1,
                train_positions=train_positions,
                test_positions=test_positions,
                train_start=train_obs.min(),
                train_end=train_obs.max(),
                test_start=selected_test_obs.min(),
                test_end=selected_test_obs.max(),
                purged_count=int(purged.sum()),
                embargoed_count=int((embargoed & ~purged).sum()),
            )
        )
    if not folds:
        raise ValueError("No valid combinatorial folds remain after purging and embargo.")
    return folds
