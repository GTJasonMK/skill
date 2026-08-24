"""Deterministic offline market/limit-order replay against timestamped quotes."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from data_quant.io.validation import parse_utc_timestamp


@dataclass(frozen=True)
class ReplayResult:
    fills: pd.DataFrame
    order_outcomes: pd.DataFrame


def replay_market_orders(
    orders: pd.DataFrame,
    quotes: pd.DataFrame,
    *,
    max_participation: float = 0.10,
    commission_bps: float = 0.0,
    slippage_bps: float = 0.0,
    impact_model: str = "linear",
    impact_coefficient_bps: float = 0.0,
    permanent_impact_coefficient_bps: float = 0.0,
    hidden_liquidity_fraction: float = 0.0,
    hidden_spread_bps: float = 0.0,
) -> ReplayResult:
    """Replay offline orders with quote-volume capacity, limits, expiry, and IOC semantics."""

    if not 0 < max_participation <= 1:
        raise ValueError("max_participation must be in (0, 1].")
    if (
        commission_bps < 0
        or slippage_bps < 0
        or impact_coefficient_bps < 0
        or permanent_impact_coefficient_bps < 0
        or not 0 <= hidden_liquidity_fraction <= 1
        or hidden_spread_bps < 0
    ):
        raise ValueError("commission, slippage, impact, or hidden-liquidity parameters are invalid.")
    if impact_model not in {"linear", "square_root"}:
        raise ValueError("impact_model must be 'linear' or 'square_root'.")
    required_orders = ["order_id", "asset_id", "submitted_at", "side", "quantity", "order_type"]
    required_quotes = ["timestamp", "asset_id", "bid", "ask", "volume"]
    missing_orders = [column for column in required_orders if column not in orders.columns]
    missing_quotes = [column for column in required_quotes if column not in quotes.columns]
    if missing_orders or missing_quotes:
        raise ValueError(f"Missing order columns={missing_orders}; quote columns={missing_quotes}")

    order_frame = orders.copy()
    quote_frame = quotes.copy()
    order_frame["submitted_at"] = parse_utc_timestamp(order_frame["submitted_at"], "submitted_at")
    if "expires_at" in order_frame:
        order_frame["expires_at"] = parse_utc_timestamp(order_frame["expires_at"], "expires_at")
    else:
        order_frame["expires_at"] = pd.Series(
            pd.NaT,
            index=order_frame.index,
            dtype=order_frame["submitted_at"].dtype,
        )
    order_frame["time_in_force"] = (
        order_frame["time_in_force"].fillna("gtc").astype(str).str.lower()
        if "time_in_force" in order_frame
        else "gtc"
    )
    quote_frame["timestamp"] = parse_utc_timestamp(quote_frame["timestamp"], "timestamp")
    order_frame["quantity"] = pd.to_numeric(order_frame["quantity"], errors="coerce")
    if "limit_price" in order_frame:
        order_frame["limit_price"] = pd.to_numeric(order_frame["limit_price"], errors="coerce")
    else:
        order_frame["limit_price"] = np.nan
    if "amended_at" in order_frame:
        order_frame["amended_at"] = parse_utc_timestamp(order_frame["amended_at"], "amended_at")
    else:
        order_frame["amended_at"] = pd.Series(
            pd.NaT, index=order_frame.index, dtype=order_frame["submitted_at"].dtype
        )
    if "amend_limit_price" in order_frame:
        order_frame["amend_limit_price"] = pd.to_numeric(
            order_frame["amend_limit_price"], errors="coerce"
        )
    else:
        order_frame["amend_limit_price"] = np.nan
    for column in ("bid", "ask", "volume"):
        quote_frame[column] = pd.to_numeric(quote_frame[column], errors="coerce")
    if order_frame["order_id"].duplicated().any():
        raise ValueError("order_id values must be unique.")
    if order_frame["quantity"].isna().any() or (order_frame["quantity"] <= 0).any():
        raise ValueError("Order quantities must be finite and positive.")
    if quote_frame[["bid", "ask", "volume"]].isna().any().any():
        raise ValueError("Quote bid, ask, and volume must be finite.")
    if (quote_frame["bid"] <= 0).any() or (quote_frame["ask"] < quote_frame["bid"]).any():
        raise ValueError("Quotes require positive bid and ask >= bid.")
    if (quote_frame["volume"] < 0).any():
        raise ValueError("Quote volume cannot be negative.")
    if (~order_frame["time_in_force"].isin(["gtc", "day", "ioc"])).any():
        raise ValueError("time_in_force must be gtc, day, or ioc.")
    if (order_frame["time_in_force"].eq("day") & order_frame["expires_at"].isna()).any():
        raise ValueError("DAY orders require an explicit expires_at timestamp.")
    if (
        order_frame["expires_at"].notna()
        & (order_frame["expires_at"] < order_frame["submitted_at"])
    ).any():
        raise ValueError("expires_at cannot precede submitted_at.")
    if (
        order_frame["amended_at"].notna()
        & (order_frame["amended_at"] < order_frame["submitted_at"])
    ).any():
        raise ValueError("amended_at cannot precede submitted_at.")

    quote_frame = quote_frame.sort_values(["asset_id", "timestamp"]).reset_index(drop=True)
    remaining_volume = quote_frame["volume"].astype(float) * max_participation
    remaining_hidden = quote_frame["volume"].astype(float) * hidden_liquidity_fraction
    fills: list[dict] = []
    outcomes: list[dict] = []
    fill_sequence = 0
    permanent_shift: dict[str, float] = {}

    if "queue_priority" in order_frame:
        order_frame["queue_priority"] = pd.to_numeric(
            order_frame["queue_priority"], errors="coerce"
        )
        if order_frame["queue_priority"].notna().any() and (
            order_frame["queue_priority"].dropna() < 0
        ).any():
            raise ValueError("queue_priority must be non-negative.")
        order_frame["queue_priority"] = order_frame["queue_priority"].fillna(10**9)
    else:
        order_frame["queue_priority"] = 10**9
    for order in order_frame.sort_values(
        ["submitted_at", "queue_priority", "order_id"]
    ).to_dict("records"):
        side = str(order["side"]).lower()
        order_type = str(order["order_type"]).lower()
        time_in_force = str(order["time_in_force"])
        requested = float(order["quantity"])
        remaining = requested
        reason = ""
        expiration = order["expires_at"]
        has_expiration = not pd.isna(expiration)
        mask = (quote_frame["asset_id"].astype(str) == str(order["asset_id"])) & (
            quote_frame["timestamp"] >= order["submitted_at"]
        )
        if has_expiration:
            mask &= quote_frame["timestamp"] <= expiration
        eligible = quote_frame.index[mask]
        if time_in_force == "ioc":
            eligible = eligible[:1]
        arrival_quote = quote_frame.loc[eligible[0]] if len(eligible) else None
        arrival_mid = (
            (float(arrival_quote["bid"]) + float(arrival_quote["ask"])) / 2.0
            if arrival_quote is not None
            else None
        )
        order_fill_prices: list[float] = []
        order_fill_quantities: list[float] = []
        order_fill_times: list[pd.Timestamp] = []

        if side not in {"buy", "sell"}:
            reason = "unsupported_side"
        elif order_type not in {"market", "limit"}:
            reason = "unsupported_order_type"
        elif order_type == "limit" and (
            pd.isna(order["limit_price"]) or float(order["limit_price"]) <= 0
        ):
            reason = "invalid_limit_price"
        else:
            marketable_seen = order_type == "market"
            for quote_index in eligible:
                quote = quote_frame.loc[quote_index]
                asset_key = str(quote["asset_id"])
                reference_price = float(quote["ask"] if side == "buy" else quote["bid"])
                reference_price *= 1.0 + permanent_shift.get(asset_key, 0.0)
                if order_type == "limit":
                    limit_price = float(order["limit_price"])
                    amended_at = order.get("amended_at")
                    amend_limit = order.get("amend_limit_price")
                    if (
                        not pd.isna(amended_at)
                        and not pd.isna(amend_limit)
                        and pd.Timestamp(quote["timestamp"]) >= pd.Timestamp(amended_at)
                    ):
                        if float(amend_limit) <= 0:
                            raise ValueError("amend_limit_price must be positive.")
                        limit_price = float(amend_limit)
                    marketable = reference_price <= limit_price if side == "buy" else (
                        reference_price >= limit_price
                    )
                    if not marketable:
                        continue
                    marketable_seen = True
                direction = 1.0 if side == "buy" else -1.0
                layers = [
                    (float(remaining_volume.loc[quote_index]), 0.0, remaining_volume),
                    (
                        float(remaining_hidden.loc[quote_index]),
                        hidden_spread_bps,
                        remaining_hidden,
                    ),
                ]
                for available, extra_spread, book in layers:
                    if remaining <= 1e-12 or available <= 0:
                        continue
                    fill_quantity = min(remaining, available)
                    participation_fraction = (
                        fill_quantity / float(quote["volume"])
                        if float(quote["volume"]) > 0
                        else 0.0
                    )
                    impact = (
                        impact_coefficient_bps * participation_fraction
                        if impact_model == "linear"
                        else impact_coefficient_bps * math.sqrt(participation_fraction)
                    )
                    price = reference_price * (
                        1.0
                        + direction * (slippage_bps + impact + extra_spread) / 10_000.0
                    )
                    permanent_shift[asset_key] = permanent_shift.get(asset_key, 0.0) + (
                        direction
                        * permanent_impact_coefficient_bps
                        * participation_fraction
                        / 10_000.0
                    )
                    notional = fill_quantity * price
                    fees = notional * commission_bps / 10_000.0
                    fill_sequence += 1
                    fills.append(
                        {
                            "fill_id": f"fill-{fill_sequence:08d}",
                            "order_id": str(order["order_id"]),
                            "asset_id": str(order["asset_id"]),
                            "filled_at": quote["timestamp"],
                            "side": side,
                            "quantity": fill_quantity,
                            "price": price,
                            "reference_price": reference_price,
                            "fees": fees,
                            "venue": str(order.get("venue", "offline-replay")),
                            "liquidity": "hidden" if extra_spread else "visible",
                        }
                    )
                    order_fill_prices.append(price)
                    order_fill_quantities.append(fill_quantity)
                    order_fill_times.append(pd.Timestamp(quote["timestamp"]))
                    book.loc[quote_index] = available - fill_quantity
                    remaining -= fill_quantity
                if remaining <= 1e-12:
                    remaining = 0.0
                    break
            if remaining == requested:
                reason = "limit_not_reached" if len(eligible) and not marketable_seen else (
                    "no_eligible_liquidity"
                )
            elif remaining > 0:
                reason = "partial_liquidity"

        filled = requested - remaining
        terminal_rejection = reason in {
            "unsupported_side",
            "unsupported_order_type",
            "invalid_limit_price",
        }
        if terminal_rejection:
            status = "rejected"
        elif remaining == 0:
            status = "filled"
        elif time_in_force == "ioc":
            status = "partial_cancelled" if filled > 0 else "cancelled"
        elif has_expiration:
            status = "partial_expired" if filled > 0 else "expired"
        else:
            status = "partial" if filled > 0 else "rejected"
        vwap = (
            float(np.average(order_fill_prices, weights=order_fill_quantities))
            if order_fill_prices
            else None
        )
        direction = 1.0 if side == "buy" else -1.0
        shortfall_bps = (
            direction * (vwap - arrival_mid) / arrival_mid * 10_000.0
            if vwap is not None and arrival_mid is not None
            else None
        )
        outcomes.append(
            {
                "order_id": str(order["order_id"]),
                "asset_id": str(order["asset_id"]),
                "side": side,
                "requested_quantity": requested,
                "filled_quantity": filled,
                "remaining_quantity": remaining,
                "fill_rate": filled / requested,
                "status": status,
                "reason": reason,
                "time_in_force": time_in_force,
                "expires_at": pd.Timestamp(expiration).isoformat() if has_expiration else None,
                "arrival_mid": arrival_mid,
                "vwap": vwap,
                "implementation_shortfall_bps": shortfall_bps,
                "first_fill_at": order_fill_times[0].isoformat() if order_fill_times else None,
                "last_fill_at": order_fill_times[-1].isoformat() if order_fill_times else None,
                "arrival_to_first_fill_seconds": (
                    float((order_fill_times[0] - order["submitted_at"]).total_seconds())
                    if order_fill_times
                    else None
                ),
            }
        )

    return ReplayResult(fills=pd.DataFrame(fills), order_outcomes=pd.DataFrame(outcomes))
