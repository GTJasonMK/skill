"""Cash, position, and NAV reconciliation for offline fills."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ReconciliationResult:
    cash: float
    positions: pd.Series
    market_value: float
    nav: float
    traded_notional: float
    total_fees: float


def reconcile_fills(
    fills: pd.DataFrame,
    *,
    initial_cash: float,
    initial_positions: pd.Series | None = None,
    marks: pd.Series | None = None,
) -> ReconciliationResult:
    required = ["asset_id", "side", "quantity", "price", "fees"]
    missing = [column for column in required if column not in fills.columns]
    if missing and not fills.empty:
        raise ValueError(f"Fills missing columns: {missing}")
    cash = float(initial_cash)
    positions = (
        initial_positions.astype(float).copy()
        if initial_positions is not None
        else pd.Series(dtype=float)
    )
    traded_notional = 0.0
    total_fees = 0.0
    for fill in fills.to_dict("records"):
        side = str(fill["side"]).lower()
        if side not in {"buy", "sell"}:
            raise ValueError(f"Unsupported fill side: {side}")
        quantity = float(fill["quantity"])
        price = float(fill["price"])
        fees = float(fill["fees"])
        if quantity <= 0 or price <= 0 or fees < 0:
            raise ValueError("Fill quantity/price must be positive and fees non-negative.")
        signed_quantity = quantity if side == "buy" else -quantity
        notional = quantity * price
        asset = str(fill["asset_id"])
        positions.loc[asset] = float(positions.get(asset, 0.0)) + signed_quantity
        cash -= signed_quantity * price
        cash -= fees
        traded_notional += notional
        total_fees += fees

    market_value = 0.0
    if marks is not None:
        missing_marks = [
            asset
            for asset, quantity in positions.items()
            if quantity != 0 and asset not in marks.index
        ]
        if missing_marks:
            raise ValueError(f"Missing marks for open positions: {missing_marks}")
        market_value = float(
            sum(float(quantity) * float(marks.loc[asset]) for asset, quantity in positions.items())
        )
    elif any(quantity != 0 for quantity in positions):
        raise ValueError("marks are required when open positions remain.")
    return ReconciliationResult(
        cash=cash,
        positions=positions.sort_index(),
        market_value=market_value,
        nav=cash + market_value,
        traded_notional=traded_notional,
        total_fees=total_fees,
    )
