"""Native offline execution diagnostics."""

from __future__ import annotations

import hashlib
import math
from typing import Any

import pandas as pd

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.contracts.parameters import ExecutionReplayParameters, RebalanceReplayParameters
from data_quant.execution import reconcile_fills, replay_artifact, replay_market_orders
from data_quant.io.validation import parse_utc_timestamp
from data_quant.registry import register_diagnostic


@register_diagnostic(
    "execution-replay",
    "execution_replay",
    required_table_types=("orders", "market_quotes"),
    manifest_stage="execution",
    parameter_model=ExecutionReplayParameters,
    description="Replay planned or historical orders against quotes without submitting live orders.",
)
def execution_replay_artifact(
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
    initial_cash: float = 1_000_000.0,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    if initial_cash <= 0:
        raise ValueError("initial_cash must be positive.")
    if "decision_at" in orders:
        decision_at = parse_utc_timestamp(orders["decision_at"], "decision_at")
        submitted_at = parse_utc_timestamp(orders["submitted_at"], "submitted_at")
        if (submitted_at < decision_at).any():
            raise ValueError("Orders cannot be submitted before their decision timestamp.")
    replay = replay_market_orders(
        orders,
        quotes,
        max_participation=max_participation,
        commission_bps=commission_bps,
        slippage_bps=slippage_bps,
        impact_model=impact_model,
        impact_coefficient_bps=impact_coefficient_bps,
        permanent_impact_coefficient_bps=permanent_impact_coefficient_bps,
        hidden_liquidity_fraction=hidden_liquidity_fraction,
        hidden_spread_bps=hidden_spread_bps,
    )
    latest_quotes = quotes.copy()
    latest_quotes["timestamp"] = parse_utc_timestamp(latest_quotes["timestamp"], "timestamp")
    latest_quotes["bid"] = pd.to_numeric(latest_quotes["bid"], errors="raise")
    latest_quotes["ask"] = pd.to_numeric(latest_quotes["ask"], errors="raise")
    latest_quotes = latest_quotes.sort_values("timestamp").groupby("asset_id", sort=False).tail(1)
    marks = latest_quotes.assign(mark=(latest_quotes["bid"] + latest_quotes["ask"]) / 2).set_index(
        "asset_id"
    )["mark"]
    reconciliation = reconcile_fills(
        replay.fills,
        initial_cash=initial_cash,
        marks=marks,
    )
    return replay_artifact(
        replay,
        reconciliation,
        parameters={
            "mode": "offline_replay",
            "max_participation": max_participation,
            "commission_bps": commission_bps,
            "slippage_bps": slippage_bps,
            "impact_model": impact_model,
            "impact_coefficient_bps": impact_coefficient_bps,
            "permanent_impact_coefficient_bps": permanent_impact_coefficient_bps,
            "hidden_liquidity_fraction": hidden_liquidity_fraction,
            "hidden_spread_bps": hidden_spread_bps,
            "initial_cash": initial_cash,
        },
        run_id=run_id,
    )


@register_diagnostic(
    "rebalance-replay",
    "rebalance_execution",
    required_table_types=("portfolio_weights", "market_quotes"),
    manifest_stage="execution",
    parameter_model=RebalanceReplayParameters,
    description="Generate deterministic rebalance orders from current/target weights and replay capacity.",
)
def rebalance_replay_artifact(
    weights: pd.DataFrame,
    quotes: pd.DataFrame,
    tax_lots: pd.DataFrame | None = None,
    *,
    current_weight_type: str = "current",
    target_weight_type: str = "target",
    portfolio_value: float,
    min_trade_notional: float = 0.0,
    lot_size: float = 1.0,
    time_in_force: str = "gtc",
    net_across_decisions: bool = False,
    max_participation: float = 0.10,
    commission_bps: float = 0.0,
    slippage_bps: float = 0.0,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    if current_weight_type == target_weight_type:
        raise ValueError("Current and target weight types must differ.")
    if portfolio_value <= 0 or min_trade_notional < 0 or lot_size <= 0:
        raise ValueError("Rebalance notional and lot parameters are invalid.")
    if time_in_force not in {"gtc", "ioc"}:
        raise ValueError("Rebalance time_in_force must be gtc or ioc.")
    weights = weights.copy()
    quotes = quotes.copy()
    weights["decision_at"] = parse_utc_timestamp(weights["decision_at"], "decision_at")
    quotes["timestamp"] = parse_utc_timestamp(quotes["timestamp"], "timestamp")
    weights["weight"] = pd.to_numeric(weights["weight"], errors="raise")

    def nav_for_decision(decision_stamp: pd.Timestamp) -> float:
        if "nav" not in weights.columns:
            return portfolio_value
        values = pd.to_numeric(
            weights.loc[weights["decision_at"] == decision_stamp, "nav"],
            errors="coerce",
        ).dropna()
        unique = pd.unique(values)
        if len(unique) == 0:
            return portfolio_value
        if len(unique) != 1 or float(unique[0]) <= 0:
            raise ValueError("Rebalance nav must be one positive value per decision.")
        return float(unique[0])
    for column in ("bid", "ask", "volume"):
        quotes[column] = pd.to_numeric(quotes[column], errors="raise")
    selected = weights[
        weights["weight_type"].astype(str).isin([current_weight_type, target_weight_type])
    ]
    available_types = set(selected["weight_type"].astype(str))
    if available_types != {current_weight_type, target_weight_type}:
        raise ValueError("Rebalance replay requires both current and target weight types.")
    current = selected[selected["weight_type"].astype(str) == current_weight_type]
    target = selected[selected["weight_type"].astype(str) == target_weight_type]
    if set(current["decision_at"]) != set(target["decision_at"]):
        raise ValueError("Current and target weights must share the same decision timestamps.")
    currencies = selected["currency"].astype(str).unique()
    if len(currencies) != 1:
        raise ValueError("Rebalance weights must use exactly one currency.")
    currency = str(currencies[0])
    lot_inventory: dict[str, list[dict[str, Any]]] = {}
    if tax_lots is not None:
        lots = tax_lots.copy()
        lots["acquired_at"] = parse_utc_timestamp(lots["acquired_at"], "acquired_at")
        lots["quantity"] = pd.to_numeric(lots["quantity"], errors="coerce")
        lots["cost_price"] = pd.to_numeric(lots["cost_price"], errors="coerce")
        if (
            lots[["quantity", "cost_price"]].isna().any().any()
            or (lots["quantity"] <= 0).any()
            or (lots["cost_price"] <= 0).any()
        ):
            raise ValueError("Tax lots require positive remaining quantity and cost price.")
        if lots["lot_id"].astype(str).duplicated().any():
            raise ValueError("tax lot_id values must be unique.")
        if (lots["currency"].astype(str) != currency).any():
            raise ValueError("Tax lots must use the rebalance reporting currency.")
        for lot in lots.sort_values(["asset_id", "acquired_at", "lot_id"]).to_dict("records"):
            lot_inventory.setdefault(str(lot["asset_id"]), []).append(
                {
                    "lot_id": str(lot["lot_id"]),
                    "remaining": float(lot["quantity"]),
                    "cost_price": float(lot["cost_price"]),
                }
            )
    orders = []
    generated_notional = 0.0
    skipped_notional = 0.0
    realized_pnl = 0.0
    lot_blockers: list[DiagnosticMessage] = []
    for decision in sorted(target["decision_at"].unique()):
        current_slice = current[current["decision_at"] == decision].set_index("asset_id")["weight"]
        target_slice = target[target["decision_at"] == decision].set_index("asset_id")["weight"]
        assets = current_slice.index.union(target_slice.index).astype(str)
        current_slice.index = current_slice.index.astype(str)
        target_slice.index = target_slice.index.astype(str)
        deltas = target_slice.reindex(assets, fill_value=0.0) - current_slice.reindex(
            assets,
            fill_value=0.0,
        )
        ordered_deltas = sorted(
            ((str(asset_id), float(delta)) for asset_id, delta in deltas.items() if delta != 0),
            key=lambda item: (0 if item[1] < 0 else 1, item[0]),
        )
        for asset_id, delta in ordered_deltas:
            candidates = quotes[
                (quotes["asset_id"].astype(str) == asset_id)
                & (quotes["currency"].astype(str) == currency)
                & (quotes["timestamp"] >= decision)
            ]
            if candidates.empty:
                raise ValueError(f"No executable quote exists for {asset_id!r} after {decision}.")
            arrival_at = candidates["timestamp"].min()
            arrivals = candidates[candidates["timestamp"] == arrival_at]
            side = "buy" if delta > 0 else "sell"
            quote_index = arrivals["ask"].idxmin() if side == "buy" else arrivals["bid"].idxmax()
            arrival = arrivals.loc[quote_index]
            mid = float((arrival["bid"] + arrival["ask"]) / 2.0)
            requested_notional = abs(float(delta)) * nav_for_decision(pd.Timestamp(decision))
            raw_quantity = requested_notional / mid
            quantity = math.floor(raw_quantity / lot_size + 1e-12) * lot_size
            rounded_notional = quantity * mid
            if quantity <= 0 or rounded_notional < min_trade_notional:
                skipped_notional += requested_notional
                continue
            if tax_lots is not None and side == "sell":
                remaining_sell = quantity
                for lot in lot_inventory.get(asset_id, []):
                    take = min(lot["remaining"], remaining_sell)
                    if take <= 0:
                        continue
                    realized_pnl += take * (mid - lot["cost_price"])
                    lot["remaining"] -= take
                    remaining_sell -= take
                    if remaining_sell <= 1e-12:
                        break
                if remaining_sell > 1e-12:
                    lot_blockers.append(
                        DiagnosticMessage(
                            code="tax_lot_insufficient",
                            message="FIFO tax lots do not cover the generated sell quantity.",
                            severity="blocker",
                            context={
                                "asset_id": asset_id,
                                "sell_quantity": quantity,
                                "uncovered_quantity": remaining_sell,
                            },
                        )
                    )
            identity = f"{pd.Timestamp(decision).isoformat()}|{asset_id}|{side}"
            order_id = f"rebalance-{hashlib.sha256(identity.encode()).hexdigest()[:16]}"
            generated_notional += rounded_notional
            orders.append(
                {
                    "order_id": order_id,
                    "asset_id": asset_id,
                    "decision_at": decision,
                    "submitted_at": decision,
                    "side": side,
                    "queue_priority": 0 if side == "sell" else 1,
                    "quantity": quantity,
                    "order_type": "market",
                    "time_in_force": time_in_force,
                    "venue": str(arrival["venue"]),
                    "status": "planned",
                }
            )
    if not orders:
        raise ValueError("Rebalance constraints produced no executable orders.")
    if net_across_decisions:
        signed_qty: dict[str, float] = {}
        last_order: dict[str, dict[str, Any]] = {}
        for order in orders:
            asset_id = str(order["asset_id"])
            signed = float(order["quantity"]) if order["side"] == "buy" else -float(order["quantity"])
            signed_qty[asset_id] = signed_qty.get(asset_id, 0.0) + signed
            last_order[asset_id] = order
        netted = []
        for asset_id, quantity in signed_qty.items():
            if abs(quantity) <= 1e-12:
                continue
            template = last_order[asset_id]
            side = "buy" if quantity > 0 else "sell"
            identity = f"net|{asset_id}|{side}|{template['submitted_at']}"
            netted.append(
                {
                    **template,
                    "order_id": f"rebalance-{hashlib.sha256(identity.encode()).hexdigest()[:16]}",
                    "side": side,
                    "quantity": abs(quantity),
                    "queue_priority": 0 if side == "sell" else 1,
                }
            )
        netted.sort(key=lambda item: (item["queue_priority"], str(item["asset_id"])))
        if not netted:
            raise ValueError("Cross-decision netting cancelled every generated order.")
        orders = netted
    order_frame = pd.DataFrame(orders)
    replay = execution_replay_artifact(
        order_frame,
        quotes,
        max_participation=max_participation,
        commission_bps=commission_bps,
        slippage_bps=slippage_bps,
        initial_cash=portfolio_value,
        run_id=run_id,
    )
    return ArtifactEnvelope(
        artifact_type="rebalance_execution",
        run_id=run_id,
        producer=ProducerReference(name="rebalance-replay", version=__version__),
        parameters={
            "mode": "offline_replay",
            "current_weight_type": current_weight_type,
            "target_weight_type": target_weight_type,
            "portfolio_value": portfolio_value,
            "min_trade_notional": min_trade_notional,
            "lot_size": lot_size,
            "time_in_force": time_in_force,
            "net_across_decisions": net_across_decisions,
            "max_participation": max_participation,
            "commission_bps": commission_bps,
            "slippage_bps": slippage_bps,
        },
        summary={
            "generated_order_count": len(order_frame),
            "generated_order_notional_at_arrival": generated_notional,
            "skipped_target_notional": skipped_notional,
            "fill_count": replay.summary["fill_count"],
            "status_counts": replay.summary["status_counts"],
            "aggregate_fill_rate": replay.summary["aggregate_fill_rate"],
            "traded_notional": replay.summary["traded_notional"],
            "total_fees": replay.summary["total_fees"],
            "quantity_weighted_implementation_shortfall_bps": replay.summary[
                "quantity_weighted_implementation_shortfall_bps"
            ],
            "realized_tax_lot_pnl": realized_pnl if tax_lots is not None else None,
            "blocker_count": len(replay.blockers) + len(lot_blockers),
        },
        warnings=replay.warnings,
        blockers=[*replay.blockers, *lot_blockers],
        evidence_gaps=[
            *replay.evidence_gaps,
            DiagnosticMessage(
                code="rebalance_generation_scope",
                message=(
                    "Weight-to-order sizing uses per-decision nav when provided, else a static "
                    "portfolio value, and arrival midpoint; sells are queued before buys at the "
                    "same decision. FIFO tax lots cover sells when provided. It does not model "
                    "borrow locates. Cross-decision netting is optional signed-quantity collapse."
                ),
                severity="warning",
            ),
        ],
        details=replay.details,
        provenance={
            "live_order_submission": False,
            "order_generation": "deterministic_weight_delta",
            "notional_basis": "decision_nav_or_static_portfolio_value",
            "cash_sequencing": "sells_before_buys",
            "tax_lots": "fifo_cost_basis" if tax_lots is not None else "not_provided",
            "cross_batch_netting": "signed_quantity_by_asset" if net_across_decisions else "off",
        },
    ).finalize()
