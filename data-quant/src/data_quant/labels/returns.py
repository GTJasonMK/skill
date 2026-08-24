"""Execution-aligned return-label construction."""

from __future__ import annotations

import numpy as np
import pandas as pd

from data_quant.io.validation import parse_utc_timestamp


def build_forward_returns(
    prices: pd.DataFrame,
    *,
    asset_col: str,
    timestamp_col: str,
    price_col: str,
    horizon: int,
    label: str,
    return_type: str = "simple",
    return_basis: str = "gross",
    corporate_action_policy: str = "price_return",
    benchmark: str | None = None,
    currency: str = "USD",
    expected_step: pd.Timedelta | None = None,
    allow_gaps: bool = False,
) -> pd.DataFrame:
    if horizon <= 0:
        raise ValueError("horizon must be positive.")
    if return_type not in {"simple", "log"}:
        raise ValueError("return_type must be 'simple' or 'log'.")
    if return_basis not in {"gross", "excess"}:
        raise ValueError("return_basis must be 'gross' or 'excess'.")
    if return_basis == "excess" and not benchmark:
        raise ValueError("Excess return labels require a benchmark.")
    if corporate_action_policy not in {"price_return", "total_return"}:
        raise ValueError("corporate_action_policy must be 'price_return' or 'total_return'.")
    required = [asset_col, timestamp_col, price_col]
    missing = [column for column in required if column not in prices.columns]
    if missing:
        raise ValueError(f"Price table missing columns: {missing}")

    frame = prices[required].copy()
    frame[timestamp_col] = parse_utc_timestamp(frame[timestamp_col], timestamp_col)
    frame[price_col] = pd.to_numeric(frame[price_col], errors="coerce")
    if frame[price_col].isna().any() or (frame[price_col] <= 0).any():
        raise ValueError("Prices must be finite and strictly positive.")
    if frame.duplicated([asset_col, timestamp_col]).any():
        raise ValueError("Price table contains duplicate asset/timestamp keys.")
    frame = frame.sort_values([asset_col, timestamp_col]).reset_index(drop=True)

    grouped = frame.groupby(asset_col, sort=False)
    frame["return_end"] = grouped[timestamp_col].shift(-horizon)
    future_price = grouped[price_col].shift(-horizon)
    if return_type == "simple":
        frame["return_value"] = future_price / frame[price_col] - 1.0
    else:
        frame["return_value"] = np.log(future_price / frame[price_col])

    if expected_step is not None and not allow_gaps:
        expected_end = frame[timestamp_col] + expected_step * horizon
        bad_gap = frame["return_end"].notna() & (frame["return_end"] != expected_end)
        frame.loc[bad_gap, ["return_end", "return_value"]] = [pd.NaT, np.nan]

    out = pd.DataFrame(
        {
            "decision_at": frame[timestamp_col],
            "execution_at": frame[timestamp_col],
            "return_start": frame[timestamp_col],
            "return_end": frame["return_end"],
            "asset_id": frame[asset_col].astype("string"),
            "label": label,
            "return_value": frame["return_value"],
            "return_type": return_type,
            "return_basis": return_basis,
            "corporate_action_policy": corporate_action_policy,
            "benchmark": benchmark,
            "currency": currency,
        }
    )
    return out.dropna(subset=["return_end", "return_value"]).reset_index(drop=True)
