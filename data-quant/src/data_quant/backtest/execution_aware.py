"""Execution-aware multi-period portfolio backtest.

Unlike ``run_portfolio_backtest`` (which charges an abstract turnover cost),
this state machine replays each rebalance against quote liquidity and feeds the
realized fills, fees, and impact back into a single cash/position NAV that
carries across periods. It reuses ``replay_market_orders`` and
``reconcile_fills`` so the execution model is identical to the offline replay
diagnostics; only the NAV bookkeeping is new.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from data_quant.execution import reconcile_fills, replay_market_orders
from data_quant.io.validation import parse_utc_timestamp


@dataclass(frozen=True)
class ExecutionAwareResult:
    periods: pd.DataFrame
    final_nav: float
    total_fees: float
    total_traded_notional: float


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def run_execution_aware_backtest(
    weights: pd.DataFrame,
    quotes: pd.DataFrame,
    *,
    weight_type: str,
    initial_cash: float,
    lot_size: float = 1.0,
    min_trade_notional: float = 0.0,
    max_participation: float = 0.10,
    commission_bps: float = 0.0,
    slippage_bps: float = 0.0,
    impact_model: str = "linear",
    impact_coefficient_bps: float = 0.0,
    permanent_impact_coefficient_bps: float = 0.0,
) -> ExecutionAwareResult:
    """Replay target-weight rebalances across periods against quotes.

    ``weights`` carries ``decision_at``, ``asset_id``, ``weight``,
    ``weight_type``, and ``currency``. ``quotes`` carries ``timestamp``,
    ``asset_id``, ``bid``, ``ask``, ``volume``, and ``currency``. Each period
    marks the portfolio at the first post-decision quote midpoint, sizes target
    share quantities from the current NAV, replays the delta orders, and
    reconciles cash/positions into a single rolling NAV.
    """
    if weight_type not in {"current", "target"}:
        raise ValueError("weight_type must be 'current' or 'target'.")
    if initial_cash <= 0:
        raise ValueError("initial_cash must be positive.")
    if lot_size <= 0 or min_trade_notional < 0:
        raise ValueError("lot_size must be positive and min_trade_notional non-negative.")
    if not 0 < max_participation <= 1:
        raise ValueError("max_participation must be in (0, 1].")

    _require_columns(
        weights,
        ("decision_at", "asset_id", "weight", "weight_type", "currency"),
        "Execution-aware weights",
    )
    _require_columns(quotes, ("timestamp", "asset_id", "bid", "ask", "volume", "currency"), "Quotes")

    weights = weights.copy()
    quotes = quotes.copy()
    weights["decision_at"] = parse_utc_timestamp(weights["decision_at"], "decision_at")
    weights["weight"] = pd.to_numeric(weights["weight"], errors="coerce")
    quotes["timestamp"] = parse_utc_timestamp(quotes["timestamp"], "timestamp")
    for column in ("bid", "ask", "volume"):
        quotes[column] = pd.to_numeric(quotes[column], errors="coerce")

    selected = weights[weights["weight_type"].astype(str) == weight_type].copy()
    if selected.empty:
        raise ValueError(f"No weights match weight_type {weight_type!r}.")
    if selected["decision_at"].isna().any() or selected["asset_id"].isna().any():
        raise ValueError("Weight decision_at and asset_id cannot be missing.")
    selected["asset_id"] = selected["asset_id"].astype(str)
    if not selected["weight"].notna().all() or not (
        selected["weight"].map(math.isfinite).all()
    ):
        raise ValueError("Portfolio weights must be finite.")
    if selected["currency"].nunique() != 1:
        raise ValueError("Execution-aware weights must use exactly one currency.")
    currency = str(selected["currency"].iloc[0])
    if (quotes["currency"].astype(str) != currency).any():
        raise ValueError("Quotes must use the portfolio currency.")
    if (
        quotes[["bid", "ask", "volume"]].isna().any().any()
        or (quotes["bid"] <= 0).any()
        or (quotes["ask"] < quotes["bid"]).any()
        or (quotes["volume"] < 0).any()
    ):
        raise ValueError("Quotes require positive bid, ask >= bid, and non-negative volume.")
    quotes["asset_id"] = quotes["asset_id"].astype(str)
    quotes = quotes.sort_values("timestamp").reset_index(drop=True)

    decisions = sorted(selected["decision_at"].unique())
    if not decisions:
        raise ValueError("Execution-aware backtest requires at least one decision period.")

    cash = float(initial_cash)
    positions = pd.Series(dtype=float)
    rows: list[dict[str, object]] = []
    total_fees = 0.0
    total_traded_notional = 0.0

    for decision in decisions:
        slice_weights = selected[selected["decision_at"] == decision].set_index("asset_id")["weight"]
        if slice_weights.index.duplicated().any():
            raise ValueError(f"Duplicate asset_id at decision {decision}.")

        after_decision = quotes[quotes["timestamp"] >= decision]
        if after_decision.empty:
            raise ValueError(f"No quotes exist at or after decision {decision}.")
        first_time = after_decision["timestamp"].min()
        arrivals = after_decision[after_decision["timestamp"] == first_time]
        mark = (
            arrivals.assign(mid=(arrivals["bid"] + arrivals["ask"]) / 2.0)
            .groupby("asset_id", sort=False)["mid"]
            .first()
        )

        # Revalue the current book at this period's marks before trading.
        nav_before = cash
        for asset_id, quantity in positions.items():
            if quantity == 0:
                continue
            if asset_id not in mark.index:
                raise ValueError(f"No mark available for held asset {asset_id!r}.")
            nav_before += float(quantity) * float(mark.loc[asset_id])

        # Target share quantities from the current NAV, then the delta to trade.
        target_shares: dict[str, float] = {}
        for asset_id, weight in slice_weights.items():
            asset_id = str(asset_id)
            if asset_id not in mark.index:
                raise ValueError(f"No mark available for target asset {asset_id!r}.")
            target_shares[asset_id] = float(weight) * nav_before / float(mark.loc[asset_id])

        current_shares = {str(asset_id): float(quantity) for asset_id, quantity in positions.items()}
        deltas = {
            asset_id: target_shares.get(asset_id, 0.0) - current_shares.get(asset_id, 0.0)
            for asset_id in set(target_shares) | set(current_shares)
        }

        orders: list[dict[str, object]] = []
        for asset_id, delta in sorted(
            ((asset_id, delta) for asset_id, delta in deltas.items() if delta != 0),
            key=lambda item: (0 if item[1] < 0 else 1, item[0]),
        ):
            side = "sell" if delta < 0 else "buy"
            raw_quantity = abs(delta)
            quantity = math.floor(raw_quantity / lot_size + 1e-12) * lot_size
            if quantity <= 0:
                continue
            notional = quantity * float(mark.loc[asset_id])
            if notional < min_trade_notional:
                continue
            orders.append(
                {
                    "order_id": f"ea-{decision.isoformat()}-{asset_id}-{side}",
                    "asset_id": asset_id,
                    "submitted_at": decision,
                    "side": side,
                    "quantity": quantity,
                    "order_type": "market",
                    "queue_priority": 0 if side == "sell" else 1,
                }
            )

        if orders:
            order_frame = pd.DataFrame(orders)
            replay = replay_market_orders(
                order_frame,
                quotes,
                max_participation=max_participation,
                commission_bps=commission_bps,
                slippage_bps=slippage_bps,
                impact_model=impact_model,
                impact_coefficient_bps=impact_coefficient_bps,
                permanent_impact_coefficient_bps=permanent_impact_coefficient_bps,
            )
            reconciliation = reconcile_fills(
                replay.fills,
                initial_cash=cash,
                initial_positions=positions,
                marks=mark,
            )
            cash = reconciliation.cash
            positions = reconciliation.positions
            period_fees = reconciliation.total_fees
            period_notional = reconciliation.traded_notional
        else:
            period_fees = 0.0
            period_notional = 0.0

        nav_after = cash
        for asset_id, quantity in positions.items():
            if quantity != 0:
                nav_after += float(quantity) * float(mark.loc[asset_id])

        turnover = float(
            0.5 * sum(abs(delta) for delta in deltas.values())
        ) if deltas else 0.0
        total_fees += period_fees
        total_traded_notional += period_notional
        rows.append(
            {
                "decision_at": decision,
                "nav_before": nav_before,
                "nav_after": nav_after,
                "gross_turnover_fraction": turnover,
                "traded_notional": period_notional,
                "fees": period_fees,
                "position_count": int((positions != 0).sum()),
            }
        )

    periods = pd.DataFrame(rows)
    final_nav = cash
    for asset_id, quantity in positions.items():
        if quantity != 0:
            if asset_id not in mark.index:
                raise ValueError(f"No final mark for held asset {asset_id!r}.")
            final_nav += float(quantity) * float(mark.loc[asset_id])

    return ExecutionAwareResult(
        periods=periods,
        final_nav=final_nav,
        total_fees=total_fees,
        total_traded_notional=total_traded_notional,
    )
