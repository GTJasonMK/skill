"""Explicit turnover and transaction-cost conventions."""

from __future__ import annotations

import numpy as np
import pandas as pd


def align_weights(current: pd.Series, target: pd.Series) -> tuple[pd.Series, pd.Series]:
    assets = current.index.union(target.index)
    return current.reindex(assets, fill_value=0.0), target.reindex(assets, fill_value=0.0)


def traded_weight(current: pd.Series, target: pd.Series) -> float:
    """Total absolute traded notional as a fraction of NAV."""
    current_aligned, target_aligned = align_weights(current, target)
    delta = target_aligned.to_numpy(dtype=float) - current_aligned.to_numpy(dtype=float)
    return float(np.abs(delta).sum())


def one_way_turnover(current: pd.Series, target: pd.Series) -> float:
    """Conventional one-way turnover: half total absolute weight change."""
    return 0.5 * traded_weight(current, target)


def linear_cost_fraction(
    current: pd.Series,
    target: pd.Series,
    *,
    cost_bps_per_traded_notional: float,
) -> float:
    if cost_bps_per_traded_notional < 0:
        raise ValueError("cost_bps_per_traded_notional must be non-negative.")
    return traded_weight(current, target) * cost_bps_per_traded_notional / 10_000.0
