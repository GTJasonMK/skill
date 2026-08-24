"""Futures contract selection, rolling, and variation-margin helpers."""

from __future__ import annotations

import pandas as pd

from data_quant.io.validation import parse_utc_timestamp


def build_unadjusted_continuous_futures(
    prices: pd.DataFrame,
    *,
    timestamp_col: str,
    contract_col: str,
    price_col: str,
    expiry_col: str,
    roll_days_before_expiry: int = 5,
) -> pd.DataFrame:
    """Select the nearest eligible contract using only timestamp-known expiry metadata.

    The result is intentionally unadjusted. Back-adjusting with future roll gaps is
    a separate transformation that must be declared explicitly.
    """

    if roll_days_before_expiry < 0:
        raise ValueError("roll_days_before_expiry must be non-negative.")
    required = [timestamp_col, contract_col, price_col, expiry_col]
    missing = [column for column in required if column not in prices.columns]
    if missing:
        raise ValueError(f"Futures prices missing columns: {missing}")
    frame = prices[required].copy()
    frame[timestamp_col] = parse_utc_timestamp(frame[timestamp_col], timestamp_col)
    frame[expiry_col] = parse_utc_timestamp(frame[expiry_col], expiry_col)
    frame[price_col] = pd.to_numeric(frame[price_col], errors="coerce")
    if frame[price_col].isna().any() or (frame[price_col] <= 0).any():
        raise ValueError("Futures prices must be finite and positive.")
    if frame.duplicated([timestamp_col, contract_col]).any():
        raise ValueError("Duplicate futures timestamp/contract rows.")
    if (frame[expiry_col] < frame[timestamp_col]).any():
        frame = frame.loc[frame[expiry_col] >= frame[timestamp_col]].copy()

    cutoff = frame[timestamp_col] + pd.to_timedelta(roll_days_before_expiry, unit="D")
    eligible = frame.loc[frame[expiry_col] >= cutoff].copy()
    if eligible.empty:
        raise ValueError("No contract remains eligible under the requested roll rule.")
    eligible = eligible.sort_values([timestamp_col, expiry_col, contract_col])
    selected = eligible.groupby(timestamp_col, sort=True, as_index=False).first()
    selected["previous_contract"] = selected[contract_col].shift(1)
    selected["roll"] = selected["previous_contract"].notna() & (
        selected[contract_col] != selected["previous_contract"]
    )
    return selected.rename(
        columns={
            timestamp_col: "timestamp",
            contract_col: "contract_id",
            price_col: "price",
            expiry_col: "expiry_at",
        }
    )[["timestamp", "contract_id", "price", "expiry_at", "previous_contract", "roll"]]


def futures_variation_margin(
    previous_settlement: float,
    current_settlement: float,
    *,
    contract_multiplier: float,
    signed_contracts: float,
) -> float:
    if previous_settlement <= 0 or current_settlement <= 0:
        raise ValueError("Settlement prices must be positive.")
    if contract_multiplier <= 0:
        raise ValueError("contract_multiplier must be positive.")
    return (current_settlement - previous_settlement) * contract_multiplier * signed_contracts
