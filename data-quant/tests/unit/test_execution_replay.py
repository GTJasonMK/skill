from __future__ import annotations

import math

import pandas as pd
import pytest

from data_quant.diagnostics.execution import rebalance_replay_artifact
from data_quant.execution import reconcile_fills, replay_artifact, replay_market_orders


def inputs():
    orders = pd.DataFrame(
        {
            "order_id": ["o1", "o2"],
            "asset_id": ["A", "A"],
            "submitted_at": ["2024-01-02T09:00:00Z", "2024-01-02T09:00:00Z"],
            "side": ["buy", "sell"],
            "quantity": [8.0, 2.0],
            "order_type": ["market", "market"],
            "venue": ["SIM", "SIM"],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T09:00:01Z", "2024-01-02T09:00:02Z"],
            "asset_id": ["A", "A"],
            "bid": [9.9, 10.0],
            "ask": [10.1, 10.2],
            "volume": [50.0, 50.0],
        }
    )
    return orders, quotes


def test_replay_respects_participation_and_quote_side() -> None:
    orders, quotes = inputs()
    result = replay_market_orders(orders.iloc[[0]], quotes, max_participation=0.1)
    assert result.order_outcomes.loc[0, "status"] == "filled"
    assert result.fills["quantity"].tolist() == [5.0, 3.0]
    assert result.fills["price"].tolist() == [10.1, 10.2]


def test_replay_applies_linear_participation_impact_to_buys() -> None:
    orders, quotes = inputs()
    result = replay_market_orders(
        orders.iloc[[0]],
        quotes,
        max_participation=0.1,
        impact_coefficient_bps=10.0,
    )
    # First fill consumes 5 of 50 volume => participation 0.1 => 1.0 bps impact.
    first_price = result.fills.iloc[0]["price"]
    assert first_price == pytest.approx(10.1 * (1.0 + 1.0 / 10_000.0))


def test_replay_applies_square_root_impact_to_buys() -> None:
    orders, quotes = inputs()
    result = replay_market_orders(
        orders.iloc[[0]],
        quotes,
        max_participation=0.1,
        impact_model="square_root",
        impact_coefficient_bps=10.0,
    )
    # First fill participation 0.1 => sqrt(0.1) ~ 0.3162 => ~3.162 bps impact.
    first_price = result.fills.iloc[0]["price"]
    assert first_price == pytest.approx(10.1 * (1.0 + 10.0 * math.sqrt(0.1) / 10_000.0))


def test_replay_applies_permanent_impact_to_later_fills() -> None:
    orders, quotes = inputs()
    result = replay_market_orders(
        orders.iloc[[0]],
        quotes,
        max_participation=0.1,
        permanent_impact_coefficient_bps=10.0,
    )
    first, second = result.fills.iloc[0]["price"], result.fills.iloc[1]["price"]
    # First fill participation 0.1 → permanent +1bp, second buy is 10.2 * 1.0001.
    assert first == pytest.approx(10.1)
    assert second == pytest.approx(10.2 * (1.0 + 1.0 / 10_000.0))


def test_replay_uses_hidden_liquidity_after_visible_book() -> None:
    orders, quotes = inputs()
    result = replay_market_orders(
        orders.iloc[[0]],
        quotes,
        max_participation=0.1,
        hidden_liquidity_fraction=0.1,
        hidden_spread_bps=10.0,
    )
    assert result.fills["liquidity"].tolist() == ["visible", "hidden"]
    assert result.fills["quantity"].tolist() == [5.0, 3.0]
    assert result.fills.iloc[1]["price"] == pytest.approx(10.1 * (1.0 + 10.0 / 10_000.0))


def test_replay_applies_limit_amendment_after_amended_at() -> None:
    orders, quotes = inputs()
    order = orders.iloc[[0]].copy()
    order["order_type"] = "limit"
    order["limit_price"] = 9.5
    order["amended_at"] = "2024-01-02T09:00:02Z"
    order["amend_limit_price"] = 10.2
    result = replay_market_orders(order, quotes, max_participation=0.1)
    assert result.fills["quantity"].tolist() == [5.0]
    assert result.fills.iloc[0]["price"] == pytest.approx(10.2)


def test_shared_quote_liquidity_can_leave_later_order_partial() -> None:
    orders, quotes = inputs()
    orders.loc[1, "quantity"] = 4.0
    result = replay_market_orders(orders, quotes, max_participation=0.1)
    first = result.order_outcomes.set_index("order_id").loc["o1"]
    second = result.order_outcomes.set_index("order_id").loc["o2"]
    assert first["filled_quantity"] == 8.0
    assert second["filled_quantity"] == 2.0
    assert second["status"] == "partial"


def test_replay_honors_queue_priority_before_order_id() -> None:
    orders, quotes = inputs()
    orders.loc[1, "quantity"] = 4.0
    orders["queue_priority"] = [1, 0]
    result = replay_market_orders(orders, quotes, max_participation=0.1)
    first = result.order_outcomes.set_index("order_id").loc["o1"]
    second = result.order_outcomes.set_index("order_id").loc["o2"]
    assert second["filled_quantity"] == 4.0
    assert first["filled_quantity"] == 6.0
    assert first["status"] == "partial"


def test_reconciliation_preserves_cash_position_identity() -> None:
    orders, quotes = inputs()
    replay = replay_market_orders(
        orders.iloc[[0]],
        quotes,
        max_participation=0.1,
        commission_bps=10,
    )
    reconciliation = reconcile_fills(
        replay.fills,
        initial_cash=1_000.0,
        marks=pd.Series({"A": 10.3}),
    )
    expected_cash = 1_000.0 - (5 * 10.1 + 3 * 10.2) - replay.fills["fees"].sum()
    assert reconciliation.cash == pytest.approx(expected_cash)
    assert reconciliation.positions.loc["A"] == 8.0
    assert reconciliation.nav == pytest.approx(reconciliation.cash + 8 * 10.3)
    artifact = replay_artifact(replay, reconciliation, parameters={"max_participation": 0.1})
    assert artifact.provenance["live_order_submission"] is False
    assert artifact.summary["quantity_weighted_implementation_shortfall_bps"] > 0


def test_limit_order_without_limit_price_is_rejected() -> None:
    orders, quotes = inputs()
    orders.loc[0, "order_type"] = "limit"
    result = replay_market_orders(orders.iloc[[0]], quotes)
    assert result.fills.empty
    assert result.order_outcomes.loc[0, "status"] == "rejected"
    assert result.order_outcomes.loc[0, "reason"] == "invalid_limit_price"


def test_limit_order_waits_for_marketable_quote() -> None:
    orders, quotes = inputs()
    orders.loc[0, "order_type"] = "limit"
    orders.loc[0, "limit_price"] = 10.05
    quotes["ask"] = [10.2, 10.0]

    result = replay_market_orders(orders.iloc[[0]], quotes, max_participation=0.1)

    assert result.fills["price"].tolist() == [10.0]
    assert result.order_outcomes.loc[0, "status"] == "partial"
    assert result.order_outcomes.loc[0, "arrival_to_first_fill_seconds"] == 2.0


def test_day_expiry_and_ioc_leave_explicit_lifecycle_status() -> None:
    orders, quotes = inputs()
    day = orders.iloc[[0]].copy()
    day["time_in_force"] = "day"
    day["expires_at"] = "2024-01-02T09:00:01Z"
    expired = replay_market_orders(day, quotes, max_participation=0.1)
    assert expired.order_outcomes.loc[0, "status"] == "partial_expired"
    assert expired.order_outcomes.loc[0, "remaining_quantity"] == 3.0

    ioc = orders.iloc[[0]].copy()
    ioc["time_in_force"] = "ioc"
    cancelled = replay_market_orders(ioc, quotes, max_participation=0.1)
    assert cancelled.order_outcomes.loc[0, "status"] == "partial_cancelled"
    assert cancelled.order_outcomes.loc[0, "remaining_quantity"] == 3.0


def test_rebalance_replay_generates_lot_rounded_capacity_constrained_orders() -> None:
    decision = "2024-01-02T09:00:00Z"
    weights = pd.DataFrame(
        {
            "decision_at": [decision] * 4,
            "asset_id": ["A", "B", "A", "B"],
            "weight": [0.5, 0.5, 0.7, 0.3],
            "weight_type": ["current", "current", "target", "target"],
            "currency": ["USD"] * 4,
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T09:00:01Z"] * 2,
            "asset_id": ["A", "B"],
            "bid": [9.9, 19.9],
            "ask": [10.1, 20.1],
            "volume": [100.0, 100.0],
            "currency": ["USD", "USD"],
            "venue": ["SIM", "SIM"],
        }
    )

    artifact = rebalance_replay_artifact(
        weights,
        quotes,
        portfolio_value=1_000.0,
        lot_size=1.0,
        max_participation=0.10,
    )

    assert artifact.summary["generated_order_count"] == 2
    assert artifact.summary["generated_order_notional_at_arrival"] == pytest.approx(400.0)
    assert artifact.summary["status_counts"] == {"partial": 1, "filled": 1}
    assert artifact.provenance["cash_sequencing"] == "sells_before_buys"
    sides = [row["side"] for row in artifact.details]
    assert sides[0] == "sell"
    assert artifact.provenance["live_order_submission"] is False


def test_rebalance_replay_sizes_orders_from_decision_nav() -> None:
    decision = "2024-01-02T09:00:00Z"
    weights = pd.DataFrame(
        {
            "decision_at": [decision] * 2,
            "asset_id": ["A", "A"],
            "weight": [0.5, 0.7],
            "weight_type": ["current", "target"],
            "currency": ["USD", "USD"],
            "nav": [2_000.0, 2_000.0],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T09:00:01Z"],
            "asset_id": ["A"],
            "bid": [9.9],
            "ask": [10.1],
            "volume": [10_000.0],
            "currency": ["USD"],
            "venue": ["SIM"],
        }
    )
    artifact = rebalance_replay_artifact(
        weights,
        quotes,
        portfolio_value=1_000.0,
        lot_size=1.0,
        max_participation=1.0,
    )
    assert artifact.summary["generated_order_notional_at_arrival"] == pytest.approx(400.0)
    assert artifact.provenance["notional_basis"] == "decision_nav_or_static_portfolio_value"


def test_rebalance_replay_realizes_fifo_tax_lots_on_sells() -> None:
    decision = "2024-01-02T09:00:00Z"
    weights = pd.DataFrame(
        {
            "decision_at": [decision] * 2,
            "asset_id": ["A", "A"],
            "weight": [1.0, 0.0],
            "weight_type": ["current", "target"],
            "currency": ["USD", "USD"],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T09:00:01Z"],
            "asset_id": ["A"],
            "bid": [9.9],
            "ask": [10.1],
            "volume": [10_000.0],
            "currency": ["USD"],
            "venue": ["SIM"],
        }
    )
    lots = pd.DataFrame(
        {
            "lot_id": ["L1", "L2"],
            "asset_id": ["A", "A"],
            "acquired_at": ["2023-01-01T00:00:00Z", "2023-06-01T00:00:00Z"],
            "quantity": [50.0, 50.0],
            "cost_price": [8.0, 12.0],
            "currency": ["USD", "USD"],
        }
    )
    artifact = rebalance_replay_artifact(
        weights,
        quotes,
        lots,
        portfolio_value=1_000.0,
        lot_size=1.0,
        max_participation=1.0,
    )
    # Sell 100 at mid 10: 50*(10-8)+50*(10-12)=100-100=0.
    assert artifact.summary["realized_tax_lot_pnl"] == pytest.approx(0.0)
    assert artifact.provenance["tax_lots"] == "fifo_cost_basis"
    assert artifact.summary["blocker_count"] == 0

    short = lots.copy()
    short["quantity"] = [10.0, 10.0]
    blocked = rebalance_replay_artifact(
        weights,
        quotes,
        short,
        portfolio_value=1_000.0,
        lot_size=1.0,
        max_participation=1.0,
    )
    assert "tax_lot_insufficient" in {blocker.code for blocker in blocked.blockers}


def test_rebalance_replay_nets_opposite_orders_across_decisions() -> None:
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T09:00:01Z", "2024-01-03T09:00:01Z"],
            "asset_id": ["A", "A"],
            "bid": [9.9, 9.9],
            "ask": [10.1, 10.1],
            "volume": [10_000.0, 10_000.0],
            "currency": ["USD", "USD"],
            "venue": ["SIM", "SIM"],
        }
    )
    cancelled = pd.DataFrame(
        {
            "decision_at": [
                "2024-01-02T09:00:00Z",
                "2024-01-02T09:00:00Z",
                "2024-01-03T09:00:00Z",
                "2024-01-03T09:00:00Z",
            ],
            "asset_id": ["A"] * 4,
            "weight": [0.5, 0.7, 0.7, 0.5],
            "weight_type": ["current", "target", "current", "target"],
            "currency": ["USD"] * 4,
        }
    )
    with pytest.raises(ValueError, match="netting cancelled"):
        rebalance_replay_artifact(
            cancelled,
            quotes,
            portfolio_value=1_000.0,
            lot_size=1.0,
            max_participation=1.0,
            net_across_decisions=True,
        )
    residual = cancelled.copy()
    residual["weight"] = [0.5, 0.8, 0.8, 0.6]
    artifact = rebalance_replay_artifact(
        residual,
        quotes,
        portfolio_value=1_000.0,
        lot_size=1.0,
        max_participation=1.0,
        net_across_decisions=True,
    )
    assert artifact.summary["generated_order_count"] == 1
    assert artifact.details[0]["side"] == "buy"
    assert artifact.provenance["cross_batch_netting"] == "signed_quantity_by_asset"


def test_rebalance_replay_fails_when_trade_floor_skips_every_order() -> None:
    decision = "2024-01-02T09:00:00Z"
    weights = pd.DataFrame(
        {
            "decision_at": [decision, decision],
            "asset_id": ["A", "A"],
            "weight": [0.5, 0.51],
            "weight_type": ["current", "target"],
            "currency": ["USD", "USD"],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T09:00:01Z"],
            "asset_id": ["A"],
            "bid": [9.9],
            "ask": [10.1],
            "volume": [100.0],
            "currency": ["USD"],
            "venue": ["SIM"],
        }
    )

    with pytest.raises(ValueError, match="no executable orders"):
        rebalance_replay_artifact(
            weights,
            quotes,
            portfolio_value=1_000.0,
            min_trade_notional=20.0,
        )


def test_replay_reports_arrival_shortfall_and_latency() -> None:
    orders, quotes = inputs()
    replay = replay_market_orders(orders.iloc[[0]], quotes, max_participation=0.1)
    outcome = replay.order_outcomes.iloc[0]
    assert outcome["arrival_mid"] == 10.0
    assert outcome["vwap"] == pytest.approx(10.1375)
    assert outcome["implementation_shortfall_bps"] == pytest.approx(137.5)
    assert outcome["arrival_to_first_fill_seconds"] == 1.0
