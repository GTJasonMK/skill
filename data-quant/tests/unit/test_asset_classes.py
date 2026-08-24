from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from data_quant.asset_classes import (
    annualized_basis,
    black_scholes,
    build_unadjusted_continuous_futures,
    futures_variation_margin,
    fx_forward_outright,
    implied_volatility,
    perpetual_funding_cashflow,
    price_cashflows,
    triangular_mispricing,
)
from data_quant.diagnostics.asset_classes import (
    _crypto_tiered_charge,
    crypto_cross_margin_stress_artifact,
    fixed_income_curve_stress_artifact,
    futures_roll_artifact,
    futures_roll_execution_artifact,
    fx_forward_check_artifact,
    option_hedge_replay_artifact,
    option_surface_artifact,
    option_surface_smooth_artifact,
)


def test_futures_roll_uses_expiry_rule_and_variation_margin() -> None:
    prices = pd.DataFrame(
        {
            "timestamp": [
                "2024-01-01T00:00:00Z",
                "2024-01-01T00:00:00Z",
                "2024-01-08T00:00:00Z",
                "2024-01-08T00:00:00Z",
            ],
            "contract": ["F1", "F2", "F1", "F2"],
            "price": [100.0, 101.0, 102.0, 103.0],
            "expiry": [
                "2024-01-10T00:00:00Z",
                "2024-02-10T00:00:00Z",
                "2024-01-10T00:00:00Z",
                "2024-02-10T00:00:00Z",
            ],
        }
    )
    continuous = build_unadjusted_continuous_futures(
        prices,
        timestamp_col="timestamp",
        contract_col="contract",
        price_col="price",
        expiry_col="expiry",
        roll_days_before_expiry=5,
    )
    assert continuous["contract_id"].tolist() == ["F1", "F2"]
    assert continuous["roll"].tolist() == [False, True]
    assert futures_variation_margin(100, 102, contract_multiplier=10, signed_contracts=3) == 60


@pytest.mark.parametrize("roll_method", ["volume", "open_interest"])
def test_futures_roll_confirms_liquidity_migration_and_attributes_collateral(
    roll_method: str,
) -> None:
    contracts = pd.DataFrame(
        {
            "contract_id": ["F1", "F2"],
            "root": ["F", "F"],
            "currency": ["USD", "USD"],
            "listed_at": ["2023-01-01T00:00:00Z"] * 2,
            "last_trade_at": ["2024-01-30T00:00:00Z", "2024-02-28T00:00:00Z"],
            "expiry_at": ["2024-01-30T00:00:00Z", "2024-02-28T00:00:00Z"],
        }
    )
    rows = []
    for day, first_metric, second_metric, first_price, second_price in (
        (1, 100.0, 50.0, 100.0, 103.0),
        (2, 80.0, 90.0, 101.0, 104.0),
        (3, 60.0, 120.0, 102.0, 105.0),
    ):
        for contract, metric, price in (
            ("F1", first_metric, first_price),
            ("F2", second_metric, second_price),
        ):
            rows.append(
                {
                    "timestamp": f"2024-01-0{day}T00:00:00Z",
                    "asset_id": contract,
                    "close": price,
                    "volume": metric,
                    "open_interest": metric,
                    "currency": "USD",
                    "adjustment_state": "raw",
                }
            )
    bars = pd.DataFrame(rows)
    artifact = futures_roll_artifact(
        contracts,
        bars,
        root="F",
        roll_days_before_expiry=0,
        roll_method=roll_method,
        confirmation_periods=2,
        collateral_rate_annual=0.252,
        annualization=252,
    )

    assert [row["contract_id"] for row in artifact.details] == ["F1", "F1", "F2"]
    assert artifact.details[-1]["roll_gap"] == 3.0
    assert artifact.details[-1]["futures_return"] == pytest.approx(102 / 101 - 1)
    assert artifact.summary["cumulative_futures_return"] == pytest.approx(0.02)
    assert artifact.summary["total_collateral_return"] == pytest.approx(0.002)

    after_last_trade = bars.copy()
    after_last_trade.loc[0, "timestamp"] = "2025-01-01T00:00:00Z"
    with pytest.raises(ValueError, match="outside the listed/last-trade lifecycle"):
        futures_roll_artifact(
            contracts,
            after_last_trade,
            root="F",
            roll_method=roll_method,
        )


def test_futures_roll_execution_uses_bid_ask_vm_fees_and_margin_haircut() -> None:
    contracts = pd.DataFrame(
        {
            "contract_id": ["F1", "F2"],
            "root": ["F", "F"],
            "venue": ["X", "X"],
            "currency": ["USD", "USD"],
            "multiplier": [10.0, 10.0],
            "listed_at": ["2023-01-01T00:00:00Z"] * 2,
            "last_trade_at": ["2024-01-10T00:00:00Z", "2024-02-10T00:00:00Z"],
            "expiry_at": ["2024-01-10T00:00:00Z", "2024-02-10T00:00:00Z"],
        }
    )
    bars = pd.DataFrame(
        [
            {
                "timestamp": f"2024-01-{day:02d}T00:00:00Z",
                "asset_id": contract_id,
                "close": price,
                "currency": "USD",
                "adjustment_state": "raw",
            }
            for day, prices in ((1, (100.0, 101.0)), (8, (102.0, 103.0)), (9, (104.0, 105.0)))
            for contract_id, price in zip(("F1", "F2"), prices, strict=True)
        ]
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-08T00:00:00Z"] * 2,
            "asset_id": ["F1", "F2"],
            "venue": ["X", "X"],
            "bid": [101.9, 102.9],
            "ask": [102.1, 103.1],
        }
    )
    terms = pd.DataFrame(
        {
            "venue": ["X", "X"],
            "contract_id": ["F1", "F2"],
            "effective_from": ["2023-01-01T00:00:00Z"] * 2,
            "available_at": ["2023-01-01T00:00:00Z"] * 2,
            "initial_margin_per_contract": [200.0, 200.0],
            "maintenance_margin_per_contract": [150.0, 150.0],
            "daily_price_limit_fraction": [0.20, 0.20],
            "currency": ["USD", "USD"],
        }
    )
    common = {
        "root": "F",
        "position_quantity": 2.0,
        "roll_days_before_expiry": 5,
        "per_contract_fee": 1.0,
        "collateral_haircut": 0.10,
    }

    artifact = futures_roll_execution_artifact(
        contracts,
        bars,
        quotes,
        terms,
        initial_cash=1_000.0,
        **common,
    )
    breached = futures_roll_execution_artifact(
        contracts,
        bars,
        quotes,
        terms,
        initial_cash=310.0,
        **common,
    )

    assert artifact.summary["roll_count"] == 1
    assert artifact.summary["total_variation_margin"] == pytest.approx(76.0)
    assert artifact.summary["total_fees"] == pytest.approx(4.0)
    assert artifact.summary["ending_cash"] == pytest.approx(1_072.0)
    assert artifact.summary["blocker_count"] == 0
    assert breached.blockers[0].code == "futures_maintenance_margin_breach"

    fx_cut = futures_roll_execution_artifact(
        contracts,
        bars,
        quotes,
        terms,
        initial_cash=1_000.0,
        collateral_fx_rate=0.10,
        maximum_gross_notional=1_000.0,
        **common,
    )
    assert "futures_maintenance_margin_breach" in {b.code for b in fx_cut.blockers}
    assert "futures_collateral_concentration" in {b.code for b in fx_cut.blockers}

    deep = quotes.copy()
    deep["volume"] = [1.0, 1.0]
    depth = futures_roll_execution_artifact(
        contracts,
        bars,
        deep,
        terms,
        initial_cash=1_000.0,
        max_roll_participation=0.50,
        roll_impact_coefficient_bps=10.0,
        **common,
    )
    assert "futures_roll_depth" in {blocker.code for blocker in depth.blockers}

    marked = bars.copy()
    marked["high"] = marked["close"]
    marked["low"] = marked["close"]
    marked.loc[
        (marked["asset_id"] == "F2") & (marked["timestamp"] == "2024-01-09T00:00:00Z"),
        "low",
    ] = 50.0
    intra = futures_roll_execution_artifact(
        contracts,
        marked,
        quotes,
        terms,
        initial_cash=1_000.0,
        **common,
    )
    assert "futures_intraday_margin_call" in {blocker.code for blocker in intra.blockers}


def test_futures_roll_execution_blocks_unplanned_delivery_and_can_cash_settle() -> None:
    contracts = pd.DataFrame(
        {
            "contract_id": ["F1"],
            "root": ["F"],
            "venue": ["X"],
            "currency": ["USD"],
            "multiplier": [10.0],
            "listed_at": ["2023-01-01T00:00:00Z"],
            "last_trade_at": ["2024-01-10T00:00:00Z"],
            "expiry_at": ["2024-01-10T00:00:00Z"],
        }
    )
    bars = pd.DataFrame(
        {
            "timestamp": ["2024-01-01T00:00:00Z", "2024-01-10T00:00:00Z"],
            "asset_id": ["F1", "F1"],
            "close": [100.0, 104.0],
            "currency": ["USD", "USD"],
            "adjustment_state": ["raw", "raw"],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-10T00:00:00Z"],
            "asset_id": ["F1"],
            "venue": ["X"],
            "bid": [103.9],
            "ask": [104.1],
        }
    )
    terms = pd.DataFrame(
        {
            "venue": ["X"],
            "contract_id": ["F1"],
            "effective_from": ["2023-01-01T00:00:00Z"],
            "available_at": ["2023-01-01T00:00:00Z"],
            "initial_margin_per_contract": [200.0],
            "maintenance_margin_per_contract": [150.0],
            "daily_price_limit_fraction": [0.20],
            "currency": ["USD"],
        }
    )
    blocked = futures_roll_execution_artifact(
        contracts,
        bars,
        quotes,
        terms,
        position_quantity=2.0,
        initial_cash=1_000.0,
        root="F",
        roll_days_before_expiry=0,
        allow_physical_delivery=False,
    )
    delivered = futures_roll_execution_artifact(
        contracts,
        bars,
        quotes,
        terms,
        position_quantity=2.0,
        initial_cash=1_000.0,
        root="F",
        roll_days_before_expiry=0,
        allow_physical_delivery=True,
    )
    assert "futures_unplanned_delivery" in {blocker.code for blocker in blocked.blockers}
    assert delivered.summary["delivery_count"] == 1
    assert delivered.summary["blocker_count"] == 0
    assert delivered.details[-1]["delivery"] is True
    assert delivered.details[-1]["live_quantity"] == 0.0


def test_black_scholes_put_call_parity_and_implied_volatility() -> None:
    call = black_scholes(100, 100, 1.0, 0.2, risk_free_rate=0.03, option_type="call")
    put = black_scholes(100, 100, 1.0, 0.2, risk_free_rate=0.03, option_type="put")
    parity = 100 - 100 * math.exp(-0.03)
    assert call.price - put.price == pytest.approx(parity)
    recovered = implied_volatility(
        call.price,
        100,
        100,
        1.0,
        risk_free_rate=0.03,
        option_type="call",
    )
    assert recovered == pytest.approx(0.2, abs=1e-8)
    assert call.rho > 0
    assert put.rho < 0


def test_option_hedge_replay_recovers_dynamic_iv_and_attributes_pnl() -> None:
    expiry = pd.Timestamp("2025-01-01T00:00:00Z")
    timestamps = pd.to_datetime(
        ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z", "2024-01-03T00:00:00Z"]
    )
    spots = [100.0, 102.0, 101.0]
    mids = [
        black_scholes(
            spot,
            100.0,
            (expiry - timestamp).total_seconds() / (365.25 * 86400),
            0.25,
            option_type="call",
        ).price
        for timestamp, spot in zip(timestamps, spots, strict=True)
    ]
    contracts = pd.DataFrame(
        {
            "option_id": ["C100"],
            "underlying_id": ["S"],
            "venue": ["X"],
            "option_type": ["call"],
            "strike": [100.0],
            "expiry_at": [expiry],
            "exercise_style": ["european"],
            "multiplier": [100.0],
            "currency": ["USD"],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": timestamps,
            "asset_id": ["C100"] * 3,
            "venue": ["X"] * 3,
            "bid": [mid - 0.01 for mid in mids],
            "ask": [mid + 0.01 for mid in mids],
            "currency": ["USD"] * 3,
        }
    )
    bars = pd.DataFrame(
        {
            "timestamp": timestamps,
            "asset_id": ["S"] * 3,
            "close": spots,
            "currency": ["USD"] * 3,
            "adjustment_state": ["raw"] * 3,
        }
    )

    artifact = option_hedge_replay_artifact(
        contracts,
        quotes,
        bars,
        option_id="C100",
        option_quantity=-2.0,
        transaction_cost_bps=1.0,
    )

    assert artifact.summary["observation_count"] == 3
    assert artifact.summary["minimum_implied_volatility"] == pytest.approx(0.25)
    assert artifact.summary["maximum_implied_volatility"] == pytest.approx(0.25)
    assert artifact.summary["blocker_count"] == 0
    assert artifact.summary["total_net_hedged_pnl"] == pytest.approx(
        sum(row["net_hedged_pnl"] for row in artifact.details)
    )

    wide = quotes.copy()
    wide["bid"] = [mid * 0.8 for mid in mids]
    wide["ask"] = [mid * 1.2 for mid in mids]
    blocked = option_hedge_replay_artifact(
        contracts,
        wide,
        bars,
        option_id="C100",
        option_quantity=-2.0,
        max_spread_fraction=0.10,
    )
    assert blocked.summary["blocker_count"] == 3
    assert {blocker.code for blocker in blocked.blockers} == {"option_hedge_spread_limit"}


def test_option_hedge_replay_fills_underlying_at_bid_ask() -> None:
    expiry = pd.Timestamp("2025-01-01T00:00:00Z")
    timestamps = pd.to_datetime(
        ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z", "2024-01-03T00:00:00Z"]
    )
    spots = [100.0, 102.0, 101.0]
    mids = [
        black_scholes(
            spot,
            100.0,
            (expiry - timestamp).total_seconds() / (365.25 * 86400),
            0.25,
            option_type="call",
        ).price
        for timestamp, spot in zip(timestamps, spots, strict=True)
    ]
    contracts = pd.DataFrame(
        {
            "option_id": ["C100"],
            "underlying_id": ["S"],
            "venue": ["X"],
            "option_type": ["call"],
            "strike": [100.0],
            "expiry_at": [expiry],
            "exercise_style": ["european"],
            "multiplier": [100.0],
            "currency": ["USD"],
        }
    )
    option_quotes = pd.DataFrame(
        {
            "timestamp": timestamps,
            "asset_id": ["C100"] * 3,
            "venue": ["X"] * 3,
            "bid": [mid - 0.01 for mid in mids],
            "ask": [mid + 0.01 for mid in mids],
            "currency": ["USD"] * 3,
        }
    )
    underlying_quotes = pd.DataFrame(
        {
            "timestamp": timestamps,
            "asset_id": ["S"] * 3,
            "venue": ["X"] * 3,
            "bid": [spot - 0.10 for spot in spots],
            "ask": [spot + 0.10 for spot in spots],
            "currency": ["USD"] * 3,
        }
    )
    quotes = pd.concat([option_quotes, underlying_quotes], ignore_index=True)
    bars = pd.DataFrame(
        {
            "timestamp": timestamps,
            "asset_id": ["S"] * 3,
            "close": spots,
            "currency": ["USD"] * 3,
            "adjustment_state": ["raw"] * 3,
        }
    )
    mid_fill = option_hedge_replay_artifact(
        contracts,
        quotes,
        bars,
        option_id="C100",
        option_quantity=-2.0,
        transaction_cost_bps=0.0,
        hedge_fill_mode="mid",
    )
    bid_ask = option_hedge_replay_artifact(
        contracts,
        quotes,
        bars,
        option_id="C100",
        option_quantity=-2.0,
        transaction_cost_bps=0.0,
        hedge_fill_mode="bid_ask",
    )
    assert bid_ask.provenance["hedge_fill"] == "underlying_bid_ask"
    assert bid_ask.summary["total_hedge_transaction_cost"] > mid_fill.summary[
        "total_hedge_transaction_cost"
    ]
    assert bid_ask.summary["total_net_hedged_pnl"] < mid_fill.summary["total_net_hedged_pnl"]


def test_fixed_income_curve_schedule_dv01_and_scenario_blocker() -> None:
    instruments = pd.DataFrame(
        {
            "instrument_id": ["BOND"],
            "currency": ["USD"],
            "issue_at": ["2023-12-31T00:00:00Z"],
            "maturity_at": ["2025-12-31T00:00:00Z"],
            "coupon_rate": [0.05],
            "coupon_frequency": [2],
            "day_count": ["ACT/365"],
            "business_day_convention": ["following"],
            "face_value": [100.0],
        }
    )
    nodes = pd.DataFrame(
        {
            "curve_id": ["USD-OIS"] * 5,
            "observed_at": ["2024-01-02T08:00:00Z"] * 5,
            "available_at": ["2024-01-02T08:30:00Z"] * 5,
            "tenor_years": [0.25, 0.5, 1.0, 2.0, 3.0],
            "zero_rate": [0.04] * 5,
            "currency": ["USD"] * 5,
            "compounding": ["continuous"] * 5,
        }
    )
    sessions = pd.DataFrame(
        {
            "calendar_id": "US",
            "session": pd.bdate_range("2023-01-01", "2026-12-31"),
        }
    )
    scenarios = [{"name": "rates-up", "parallel_bps": 100.0, "node_shocks_bps": {}}]

    artifact = fixed_income_curve_stress_artifact(
        instruments,
        nodes,
        sessions,
        instrument_id="BOND",
        curve_id="USD-OIS",
        calendar_id="US",
        valuation_at="2024-01-02T09:00:00Z",
        scenarios=scenarios,
        loss_limit_fraction=0.10,
    )
    blocked = fixed_income_curve_stress_artifact(
        instruments,
        nodes,
        sessions,
        instrument_id="BOND",
        curve_id="USD-OIS",
        calendar_id="US",
        valuation_at="2024-01-02T09:00:00Z",
        scenarios=scenarios,
        loss_limit_fraction=0.005,
    )

    cashflows = [detail for detail in artifact.details if detail["detail_type"] == "cashflow"]
    assert cashflows[0]["payment_date"] == "2024-07-01"
    assert artifact.summary["dirty_price"] > 100
    assert artifact.summary["parallel_dv01"] > 0
    assert artifact.summary["blocker_count"] == 0
    matched = fixed_income_curve_stress_artifact(
        instruments,
        nodes,
        sessions,
        instrument_id="BOND",
        curve_id="USD-OIS",
        calendar_id="US",
        valuation_at="2024-01-02T09:00:00Z",
        scenarios=scenarios,
        market_dirty_price=artifact.summary["dirty_price"],
    )
    assert matched.summary["oas_bps"] == pytest.approx(0.0, abs=1e-6)
    cheap = fixed_income_curve_stress_artifact(
        instruments,
        nodes,
        sessions,
        instrument_id="BOND",
        curve_id="USD-OIS",
        calendar_id="US",
        valuation_at="2024-01-02T09:00:00Z",
        scenarios=scenarios,
        market_dirty_price=artifact.summary["dirty_price"] - 1.0,
    )
    assert cheap.summary["oas_bps"] > 0
    assert cheap.summary["dirty_price"] == pytest.approx(
        artifact.summary["dirty_price"] - 1.0, abs=1e-6
    )
    assert blocked.blockers[0].code == "fixed_income_curve_loss_limit"

    callable_bond = fixed_income_curve_stress_artifact(
        instruments,
        nodes,
        sessions,
        instrument_id="BOND",
        curve_id="USD-OIS",
        calendar_id="US",
        valuation_at="2024-01-02T09:00:00Z",
        scenarios=scenarios,
        call_price_per_100=99.0,
    )
    assert callable_bond.summary["embedded_option_exercised"] is True
    assert callable_bond.summary["dirty_price"] == pytest.approx(99.0)
    bermudan = fixed_income_curve_stress_artifact(
        instruments,
        nodes,
        sessions,
        instrument_id="BOND",
        curve_id="USD-OIS",
        calendar_id="US",
        valuation_at="2024-01-02T09:00:00Z",
        scenarios=scenarios,
        call_price_per_100=101.0,
        call_style="bermudan",
    )
    assert bermudan.provenance["embedded_option"] == "bermudan_coupon_date_call"
    assert bermudan.summary["dirty_price"] <= artifact.summary["dirty_price"] + 1e-9
    stochastic = fixed_income_curve_stress_artifact(
        instruments,
        nodes,
        sessions,
        instrument_id="BOND",
        curve_id="USD-OIS",
        calendar_id="US",
        valuation_at="2024-01-02T09:00:00Z",
        scenarios=scenarios,
        call_price_per_100=101.0,
        call_style="bermudan",
        rate_volatility=0.10,
    )
    assert stochastic.provenance["embedded_option"] == "bermudan_two_state_rate_tree"
    assert stochastic.summary["dirty_price"] <= bermudan.summary["dirty_price"] + 1e-9

    floater = instruments.copy()
    floater["coupon_type"] = ["floating"]
    floater["coupon_spread_bps"] = [0.0]
    projected = fixed_income_curve_stress_artifact(
        floater,
        nodes,
        sessions,
        instrument_id="BOND",
        curve_id="USD-OIS",
        calendar_id="US",
        valuation_at="2024-01-02T09:00:00Z",
        scenarios=scenarios,
        projection_curve_id="USD-OIS",
    )
    assert projected.summary["coupon_type"] == "floating"
    assert projected.provenance["floating_projection"] == "simple_forward_from_projection_zeros"
    assert projected.summary["dirty_price"] == pytest.approx(100.0, abs=0.05)


def test_fixed_income_duration_and_convexity_are_positive() -> None:
    analytics = price_cashflows(
        np.array([0.5, 1.0, 1.5, 2.0]),
        np.array([2.5, 2.5, 2.5, 102.5]),
        yield_rate=0.04,
        compounding_frequency=2,
    )
    assert analytics.price > 100
    assert analytics.modified_duration > 0
    assert analytics.convexity > 0


def test_fx_forward_and_triangle() -> None:
    forward = fx_forward_outright(1.10, base_rate=0.02, quote_rate=0.05, time_years=1.0)
    assert forward > 1.10
    assert triangular_mispricing(2.0, 3.0, 6.0) == pytest.approx(0.0)


def test_fx_forward_check_uses_joint_holidays_basis_and_bid_ask() -> None:
    spot_bid, spot_ask = 1.099, 1.101
    years = 7 / 365
    factor = math.exp((0.05 - 0.02 + 0.0025) * years)
    spots = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T12:00:00Z"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [spot_bid],
            "ask": [spot_ask],
            "venue": ["SPOT"],
            "spot_date": ["2024-01-04T00:00:00Z"],
        }
    )
    forwards = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T12:00:00Z"],
            "value_date": ["2024-01-11"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [spot_bid * factor],
            "ask": [spot_ask * factor],
            "quote_type": ["outright"],
            "venue": ["FWD"],
        }
    )
    session_dates = pd.to_datetime(
        ["2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08", "2024-01-11"]
    )
    calendars = pd.DataFrame(
        {
            "calendar_id": ["TARGET"] * len(session_dates) + ["US"] * len(session_dates),
            "session": list(session_dates) * 2,
        }
    )

    artifact = fx_forward_check_artifact(
        spots,
        forwards,
        calendars,
        base_currency="EUR",
        quote_currency="USD",
        base_calendar_id="TARGET",
        quote_calendar_id="US",
        base_rate=0.02,
        quote_rate=0.05,
        cross_currency_basis_bps=25.0,
        tenor_days=7,
        deviation_tolerance_bps=1.0,
    )
    assert artifact.summary["spot_value_date"] == "2024-01-04"
    assert artifact.summary["forward_value_date"] == "2024-01-11"
    assert artifact.summary["deviation_bps"] == pytest.approx(0.0)
    assert artifact.summary["implied_cross_currency_basis_bps"] == pytest.approx(25.0)

    shifted = forwards.copy()
    shifted[["bid", "ask"]] *= 1.002
    blocked = fx_forward_check_artifact(
        spots,
        shifted,
        calendars,
        base_currency="EUR",
        quote_currency="USD",
        base_calendar_id="TARGET",
        quote_calendar_id="US",
        base_rate=0.02,
        quote_rate=0.05,
        cross_currency_basis_bps=25.0,
        tenor_days=7,
        deviation_tolerance_bps=5.0,
    )
    assert blocked.blockers[0].code == "fx_forward_deviation_limit"


def test_fx_forward_check_blocks_cls_cutoff_and_funding_limit() -> None:
    spot_bid, spot_ask = 1.099, 1.101
    years = 7 / 365
    factor = math.exp((0.05 - 0.02 + 0.0025) * years)
    spots = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T18:00:00Z"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [spot_bid],
            "ask": [spot_ask],
            "venue": ["SPOT"],
            "spot_date": ["2024-01-04T00:00:00Z"],
        }
    )
    forwards = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T18:00:00Z"],
            "value_date": ["2024-01-11"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [spot_bid * factor],
            "ask": [spot_ask * factor],
            "quote_type": ["outright"],
            "venue": ["FWD"],
        }
    )
    session_dates = pd.to_datetime(
        ["2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08", "2024-01-11"]
    )
    calendars = pd.DataFrame(
        {
            "calendar_id": ["TARGET"] * len(session_dates) + ["US"] * len(session_dates),
            "session": list(session_dates) * 2,
        }
    )
    artifact = fx_forward_check_artifact(
        spots,
        forwards,
        calendars,
        base_currency="EUR",
        quote_currency="USD",
        base_calendar_id="TARGET",
        quote_calendar_id="US",
        base_rate=0.02,
        quote_rate=0.05,
        cross_currency_basis_bps=25.0,
        tenor_days=7,
        cls_cutoff_utc="17:00",
        enforce_cls_cutoff=True,
        maximum_funding_notional=0.5,
        notional_base=1.0,
        cls_member_venues=["CLS"],
        nostro_capacity_base=0.5,
        settlement_fail_probability=0.10,
        settlement_fail_lgd=1.0,
        settlement_fail_loss_limit=0.05,
    )
    assert artifact.summary["missed_cls_cutoff"] is True
    assert artifact.summary["funding_utilization"] == pytest.approx(2.0)
    assert artifact.provenance["cls_cutoff"] == "utc_clock_time"
    assert artifact.provenance["cls_membership"] == "configured_venue_allowlist"
    assert {blocker.code for blocker in artifact.blockers} == {
        "fx_cls_cutoff",
        "fx_funding_limit",
        "fx_cls_membership",
        "fx_nostro_limit",
        "fx_settlement_fail_credit",
    }


def test_fx_forward_check_prices_pit_replacement_cost() -> None:
    spot_bid, spot_ask = 1.099, 1.101
    years = 7 / 365
    factor = math.exp((0.05 - 0.02) * years)
    spots = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T12:00:00Z"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [spot_bid],
            "ask": [spot_ask],
            "venue": ["SPOT"],
            "spot_date": ["2024-01-04T00:00:00Z"],
        }
    )
    forwards = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T12:00:00Z"],
            "value_date": ["2024-01-11"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [spot_bid * factor],
            "ask": [spot_ask * factor],
            "quote_type": ["outright"],
            "venue": ["FWD"],
        }
    )
    replacement = pd.DataFrame(
        {
            "observed_at": ["2024-01-11T10:00:00Z"],
            "available_at": ["2024-01-11T10:05:00Z"],
            "value_date": ["2024-01-11"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [1.110],
            "ask": [1.112],
            "venue": ["FWD"],
        }
    )
    session_dates = pd.to_datetime(
        ["2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08", "2024-01-11"]
    )
    calendars = pd.DataFrame(
        {
            "calendar_id": ["TARGET"] * len(session_dates) + ["US"] * len(session_dates),
            "session": list(session_dates) * 2,
        }
    )
    artifact = fx_forward_check_artifact(
        spots,
        forwards,
        calendars,
        replacement_quotes=replacement,
        base_currency="EUR",
        quote_currency="USD",
        base_calendar_id="TARGET",
        quote_calendar_id="US",
        base_rate=0.02,
        quote_rate=0.05,
        tenor_days=7,
        notional_base=1.0,
        settlement_fail_probability=0.50,
        require_replacement_cost=True,
        replacement_evaluated_at="2024-01-11T12:00:00Z",
    )
    assert artifact.summary["replacement_cost_quote"] > 0
    assert artifact.summary["replacement_cost_base"] > 0
    assert artifact.summary["replacement_expected_loss"] > 0
    assert artifact.provenance["replacement_cost"] == "adverse_pit_bid_ask_replacement_quote"

    missing = fx_forward_check_artifact(
        spots,
        forwards,
        calendars,
        base_currency="EUR",
        quote_currency="USD",
        base_calendar_id="TARGET",
        quote_calendar_id="US",
        base_rate=0.02,
        quote_rate=0.05,
        tenor_days=7,
        require_replacement_cost=True,
    )
    assert missing.blockers[0].code == "fx_replacement_cost_data"


def test_fx_forward_check_uses_rate_bid_ask_bounds() -> None:
    spot_bid, spot_ask = 1.099, 1.101
    spots = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T12:00:00Z"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [spot_bid],
            "ask": [spot_ask],
            "venue": ["SPOT"],
            "spot_date": ["2024-01-04T00:00:00Z"],
        }
    )
    years = 7 / 365
    base_bid, base_ask = 0.0198, 0.0202
    quote_bid, quote_ask = 0.0498, 0.0502
    mid_factor = math.exp((0.05 - 0.02) * years)
    forwards = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T12:00:00Z"],
            "value_date": ["2024-01-11"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [spot_bid * mid_factor],
            "ask": [spot_ask * mid_factor],
            "quote_type": ["outright"],
            "venue": ["FWD"],
        }
    )
    session_dates = pd.to_datetime(
        ["2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08", "2024-01-11"]
    )
    calendars = pd.DataFrame(
        {
            "calendar_id": ["TARGET"] * len(session_dates) + ["US"] * len(session_dates),
            "session": list(session_dates) * 2,
        }
    )
    artifact = fx_forward_check_artifact(
        spots,
        forwards,
        calendars,
        base_currency="EUR",
        quote_currency="USD",
        base_calendar_id="TARGET",
        quote_calendar_id="US",
        base_rate=0.02,
        quote_rate=0.05,
        base_rate_bid=base_bid,
        base_rate_ask=base_ask,
        quote_rate_bid=quote_bid,
        quote_rate_ask=quote_ask,
        tenor_days=7,
        deviation_tolerance_bps=20.0,
    )
    assert artifact.summary["rate_quote_mode"] == "bid_ask"
    detail = artifact.details[0]
    assert detail["theoretical_forward_bid"] < detail["forward_bid"]
    assert detail["theoretical_forward_ask"] > detail["forward_ask"]


def test_fx_forward_check_interpolates_broken_date_points() -> None:
    spot_bid, spot_ask = 1.099, 1.101
    spots = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T12:00:00Z"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [spot_bid],
            "ask": [spot_ask],
            "venue": ["SPOT"],
            "spot_date": ["2024-01-04T00:00:00Z"],
        }
    )
    # Bracketing forwards at 7 and 14 days; target is the 10-day broken date.
    forwards = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T12:00:00Z"] * 2,
            "value_date": ["2024-01-11", "2024-01-18"],
            "base_currency": ["EUR", "EUR"],
            "quote_currency": ["USD", "USD"],
            "bid": [spot_bid * 1.0010, spot_bid * 1.0020],
            "ask": [spot_ask * 1.0010, spot_ask * 1.0020],
            "quote_type": ["outright", "outright"],
            "venue": ["FWD", "FWD"],
        }
    )
    session_dates = pd.to_datetime(
        ["2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08", "2024-01-11", "2024-01-14"]
    )
    calendars = pd.DataFrame(
        {
            "calendar_id": ["TARGET"] * len(session_dates) + ["US"] * len(session_dates),
            "session": list(session_dates) * 2,
        }
    )
    artifact = fx_forward_check_artifact(
        spots,
        forwards,
        calendars,
        base_currency="EUR",
        quote_currency="USD",
        base_calendar_id="TARGET",
        quote_calendar_id="US",
        base_rate=0.02,
        quote_rate=0.05,
        tenor_days=10,
        allow_broken_date_interpolation=True,
        deviation_tolerance_bps=200.0,
    )
    assert artifact.summary["broken_date_interpolation"] is not None
    assert artifact.summary["broken_date_interpolation"]["before_value_date"] == "2024-01-11"
    assert artifact.summary["broken_date_interpolation"]["after_value_date"] == "2024-01-18"

    with pytest.raises(ValueError, match="bracketing"):
        fx_forward_check_artifact(
            spots,
            forwards.iloc[:1],
            calendars,
            base_currency="EUR",
            quote_currency="USD",
            base_calendar_id="TARGET",
            quote_calendar_id="US",
            base_rate=0.02,
            quote_rate=0.05,
            tenor_days=10,
            allow_broken_date_interpolation=True,
        )


def test_crypto_cross_margin_applies_tiers_and_liquidation_waterfall() -> None:
    instruments = pd.DataFrame(
        {
            "venue": ["X", "X"],
            "instrument_id": ["BTC-PERP", "ETH-PERP"],
            "multiplier": [1.0, 1.0],
            "quote_asset": ["USDT", "USDT"],
            "collateral_asset": ["USDT", "USDT"],
            "margin_mode": ["cross", "cross"],
        }
    )
    positions = pd.DataFrame(
        {
            "observed_at": ["2024-01-01T00:00:00Z"] * 2,
            "available_at": ["2024-01-01T00:00:01Z"] * 2,
            "venue": ["X", "X"],
            "account_id": ["A", "A"],
            "instrument_id": ["BTC-PERP", "ETH-PERP"],
            "signed_quantity": [0.1, 1.0],
            "entry_price": [30_000.0, 2_000.0],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-01T00:01:00Z"] * 2,
            "venue": ["X", "X"],
            "asset_id": ["BTC-PERP", "ETH-PERP"],
            "bid": [29_990.0, 1_999.0],
            "ask": [30_010.0, 2_001.0],
            "currency": ["USDT", "USDT"],
        }
    )
    tier_rows = []
    for instrument_id in ("BTC-PERP", "ETH-PERP"):
        tier_rows.extend(
            [
                {
                    "venue": "X",
                    "instrument_id": instrument_id,
                    "effective_from": "2023-01-01T00:00:00Z",
                    "available_at": "2023-01-01T00:00:00Z",
                    "notional_floor": 0.0,
                    "notional_cap": 5_000.0,
                    "initial_margin_rate": 0.10,
                    "maintenance_margin_rate": 0.05,
                    "liquidation_fee_rate": 0.01,
                },
                {
                    "venue": "X",
                    "instrument_id": instrument_id,
                    "effective_from": "2023-01-01T00:00:00Z",
                    "available_at": "2023-01-01T00:00:00Z",
                    "notional_floor": 5_000.0,
                    "notional_cap": None,
                    "initial_margin_rate": 0.20,
                    "maintenance_margin_rate": 0.10,
                    "liquidation_fee_rate": 0.02,
                },
            ]
        )
    tiers = pd.DataFrame(tier_rows)
    common = {
        "venue": "X",
        "account_id": "A",
        "evaluated_at": "2024-01-01T00:02:00Z",
        "initial_collateral": 2_000.0,
        "insurance_fund": 100.0,
        "venue_default_recovery_rate": 0.95,
        "venue_default_loss_limit_fraction": 0.10,
    }

    stable = crypto_cross_margin_stress_artifact(
        instruments,
        positions,
        quotes,
        tiers,
        stress_shocks=[-0.10],
        **common,
    )
    liquidated = crypto_cross_margin_stress_artifact(
        instruments,
        positions,
        quotes,
        tiers,
        stress_shocks=[-0.50],
        **common,
    )

    assert stable.summary["liquidation_scenario_count"] == 0
    assert stable.summary["blocker_count"] == 0
    assert liquidated.summary["liquidation_scenario_count"] == 1
    assert liquidated.summary["maximum_socialized_loss"] > 0
    assert {blocker.code for blocker in liquidated.blockers} == {
        "crypto_adl_required",
        "crypto_cross_margin_liquidation",
    }


def test_crypto_cross_margin_ranks_profitable_legs_for_adl() -> None:
    instruments = pd.DataFrame(
        {
            "venue": ["X", "X"],
            "instrument_id": ["BTC-PERP", "ETH-PERP"],
            "multiplier": [1.0, 1.0],
            "quote_asset": ["USDT", "USDT"],
            "collateral_asset": ["USDT", "USDT"],
            "margin_mode": ["cross", "cross"],
        }
    )
    positions = pd.DataFrame(
        {
            "observed_at": ["2024-01-01T00:00:00Z"] * 2,
            "available_at": ["2024-01-01T00:00:01Z"] * 2,
            "venue": ["X", "X"],
            "account_id": ["A", "A"],
            "instrument_id": ["BTC-PERP", "ETH-PERP"],
            "signed_quantity": [0.1, -2.0],
            "entry_price": [30_000.0, 2_000.0],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-01T00:01:00Z"] * 2,
            "venue": ["X", "X"],
            "asset_id": ["BTC-PERP", "ETH-PERP"],
            "bid": [29_990.0, 1_999.0],
            "ask": [30_010.0, 2_001.0],
            "currency": ["USDT", "USDT"],
        }
    )
    tiers = pd.DataFrame(
        [
            {
                "venue": "X",
                "instrument_id": instrument_id,
                "effective_from": "2023-01-01T00:00:00Z",
                "available_at": "2023-01-01T00:00:00Z",
                "notional_floor": 0.0,
                "notional_cap": None,
                "initial_margin_rate": 0.10,
                "maintenance_margin_rate": 0.05,
                "liquidation_fee_rate": 0.01,
            }
            for instrument_id in ("BTC-PERP", "ETH-PERP")
        ]
    )
    artifact = crypto_cross_margin_stress_artifact(
        instruments,
        positions,
        quotes,
        tiers,
        venue="X",
        account_id="A",
        evaluated_at="2024-01-01T00:02:00Z",
        initial_collateral=5_000.0,
        stress_shocks=[-0.10],
        adl_ranking="pnl_leverage",
    )
    stress = next(row for row in artifact.details if row["detail_type"] == "price_stress")
    assert artifact.provenance["adl_ranking"] == "pnl_leverage"
    assert [row["instrument_id"] for row in stress["adl_queue"]] == ["ETH-PERP"]
    assert stress["adl_queue"][0]["adl_rank"] == 1
    assert stress["adl_queue"][0]["unrealized_pnl"] > 0


def test_crypto_cross_margin_applies_collateral_haircut_and_fx() -> None:
    instruments = pd.DataFrame(
        {
            "venue": ["X"],
            "instrument_id": ["BTC-PERP"],
            "multiplier": [1.0],
            "quote_asset": ["USDT"],
            "collateral_asset": ["USDC"],
            "margin_mode": ["cross"],
        }
    )
    positions = pd.DataFrame(
        {
            "observed_at": ["2024-01-01T00:00:00Z"],
            "available_at": ["2024-01-01T00:00:01Z"],
            "venue": ["X"],
            "account_id": ["A"],
            "instrument_id": ["BTC-PERP"],
            "signed_quantity": [0.1],
            "entry_price": [30_000.0],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-01T00:01:00Z"],
            "venue": ["X"],
            "asset_id": ["BTC-PERP"],
            "bid": [29_990.0],
            "ask": [30_010.0],
            "currency": ["USDT"],
        }
    )
    tiers = pd.DataFrame(
        [
            {
                "venue": "X",
                "instrument_id": "BTC-PERP",
                "effective_from": "2023-01-01T00:00:00Z",
                "available_at": "2023-01-01T00:00:00Z",
                "notional_floor": 0.0,
                "notional_cap": None,
                "initial_margin_rate": 0.10,
                "maintenance_margin_rate": 0.05,
                "liquidation_fee_rate": 0.01,
            }
        ]
    )
    common = {
        "venue": "X",
        "account_id": "A",
        "evaluated_at": "2024-01-01T00:02:00Z",
        "initial_collateral": 2_000.0,
        "collateral_fx_rates": {"USDT": 1.0},
        "stress_shocks": [-0.10],
    }
    par = crypto_cross_margin_stress_artifact(
        instruments, positions, quotes, tiers, collateral_haircut=0.0, **common
    )
    cut = crypto_cross_margin_stress_artifact(
        instruments, positions, quotes, tiers, collateral_haircut=0.90, **common
    )
    assert par.summary["available_collateral"] == pytest.approx(2_000.0)
    assert cut.summary["available_collateral"] == pytest.approx(200.0)
    assert par.summary["liquidation_scenario_count"] == 0
    assert cut.summary["liquidation_scenario_count"] == 1
    halved = crypto_cross_margin_stress_artifact(
        instruments,
        positions,
        quotes,
        tiers,
        collateral_haircut=0.0,
        **{**common, "collateral_fx_rates": {"USDT": 0.5}},
    )
    par_stress = next(row for row in par.details if row["detail_type"] == "price_stress")
    half_stress = next(row for row in halved.details if row["detail_type"] == "price_stress")
    assert half_stress["gross_notional"] == pytest.approx(par_stress["gross_notional"] * 0.5)
    assert half_stress["unrealized_pnl"] == pytest.approx(par_stress["unrealized_pnl"] * 0.5)


def test_crypto_cross_margin_sequential_liquidation_closes_worst_leg_first() -> None:
    instruments = pd.DataFrame(
        {
            "venue": ["X", "X"],
            "instrument_id": ["BTC-PERP", "ETH-PERP"],
            "multiplier": [1.0, 1.0],
            "quote_asset": ["USDT", "USDT"],
            "collateral_asset": ["USDT", "USDT"],
            "margin_mode": ["cross", "cross"],
        }
    )
    positions = pd.DataFrame(
        {
            "observed_at": ["2024-01-01T00:00:00Z"] * 2,
            "available_at": ["2024-01-01T00:00:01Z"] * 2,
            "venue": ["X", "X"],
            "account_id": ["A", "A"],
            "instrument_id": ["BTC-PERP", "ETH-PERP"],
            "signed_quantity": [0.1, 1.0],
            "entry_price": [30_000.0, 2_000.0],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-01T00:01:00Z"] * 2,
            "venue": ["X", "X"],
            "asset_id": ["BTC-PERP", "ETH-PERP"],
            "bid": [29_990.0, 1_999.0],
            "ask": [30_010.0, 2_001.0],
            "currency": ["USDT", "USDT"],
        }
    )
    tiers = pd.DataFrame(
        [
            {
                "venue": "X",
                "instrument_id": instrument_id,
                "effective_from": "2023-01-01T00:00:00Z",
                "available_at": "2023-01-01T00:00:00Z",
                "notional_floor": 0.0,
                "notional_cap": None,
                "initial_margin_rate": 0.10,
                "maintenance_margin_rate": 0.05,
                "liquidation_fee_rate": 0.01,
            }
            for instrument_id in ("BTC-PERP", "ETH-PERP")
        ]
    )
    common = {
        "venue": "X",
        "account_id": "A",
        "evaluated_at": "2024-01-01T00:02:00Z",
        "initial_collateral": 700.0,
        "stress_shocks": [-0.10],
    }
    sequential = crypto_cross_margin_stress_artifact(
        instruments, positions, quotes, tiers, liquidation_mode="sequential", **common
    )
    full = crypto_cross_margin_stress_artifact(
        instruments, positions, quotes, tiers, liquidation_mode="all_or_nothing", **common
    )
    seq = next(row for row in sequential.details if row["detail_type"] == "price_stress")
    all_legs = next(row for row in full.details if row["detail_type"] == "price_stress")
    assert seq["liquidation_sequence"] == ["BTC-PERP"]
    assert set(all_legs["liquidation_sequence"]) == {"BTC-PERP", "ETH-PERP"}
    assert seq["remaining_maintenance"] > 0
    assert sequential.provenance["liquidation_mode"] == "sequential"

    path = crypto_cross_margin_stress_artifact(
        instruments,
        positions,
        quotes,
        tiers,
        liquidation_mode="sequential",
        stress_shocks=[-0.10],
        intraday_path=[-0.05, -0.10],
        venue="X",
        account_id="A",
        evaluated_at="2024-01-01T00:02:00Z",
        initial_collateral=700.0,
    )
    prints = [row for row in path.details if row["detail_type"] == "intraday_print"]
    assert [row["print_index"] for row in prints] == [0, 1]
    assert path.summary["intraday_print_count"] == 2
    assert path.provenance["intraday_liquidation"] == "sequential_between_prints"
    assert prints[0]["liquidation_sequence"] == []
    assert prints[1]["liquidation_sequence"] == ["BTC-PERP"]


def test_crypto_cumulative_tier_deduction_bands_notional() -> None:
    tiers = pd.DataFrame(
        {
            "notional_floor": [0.0, 5_000.0],
            "notional_cap": [5_000.0, None],
            "maintenance_margin_rate": [0.05, 0.10],
            "liquidation_fee_rate": [0.01, 0.02],
        }
    )
    assert _crypto_tiered_charge(tiers, 4_000.0, "maintenance_margin_rate") == pytest.approx(200.0)
    assert _crypto_tiered_charge(tiers, 8_000.0, "maintenance_margin_rate") == pytest.approx(550.0)
    assert _crypto_tiered_charge(tiers, 8_000.0, "liquidation_fee_rate") == pytest.approx(110.0)


def test_crypto_funding_sign_and_basis() -> None:
    assert perpetual_funding_cashflow(2.0, 100.0, 0.001) == pytest.approx(-0.2)
    assert perpetual_funding_cashflow(-2.0, 100.0, 0.001) == pytest.approx(0.2)
    assert annualized_basis(105.0, 100.0, days_to_expiry=30) > 0


def test_option_surface_blocks_strike_monotonicity_violation() -> None:
    contracts = pd.DataFrame(
        {
            "option_id": ["C90", "C100"],
            "underlying_id": ["S", "S"],
            "venue": ["X", "X"],
            "option_type": ["call", "call"],
            "strike": [90.0, 100.0],
            "expiry_at": ["2025-01-01T00:00:00Z"] * 2,
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-01T00:00:00Z"] * 2,
            "asset_id": ["C90", "C100"],
            "venue": ["X", "X"],
            "bid": [14.99, 19.99],
            "ask": [15.01, 20.01],
        }
    )

    artifact = option_surface_artifact(contracts, quotes, spot=100.0, parity_tolerance=0.001)

    assert any(blocker.code == "option_strike_monotonicity" for blocker in artifact.blockers)


def test_option_surface_smooth_recovers_two_pit_expiries_without_extrapolation() -> None:
    quote_at = pd.Timestamp("2024-01-01T00:00:00Z")
    expiry_values = [pd.Timestamp("2024-07-01T00:00:00Z"), pd.Timestamp("2025-01-01T00:00:00Z")]
    strikes = [80.0, 100.0, 120.0]
    rows = []
    quote_rows = []
    for expiry_index, expiry in enumerate(expiry_values):
        years = (expiry - quote_at).total_seconds() / (365.25 * 24 * 3600)
        for strike in strikes:
            for option_type in ("call", "put"):
                option_id = f"{option_type[0].upper()}{expiry_index}{int(strike)}"
                price = black_scholes(
                    100.0,
                    strike,
                    years,
                    0.20,
                    option_type=option_type,
                ).price
                rows.append(
                    {
                        "option_id": option_id,
                        "underlying_id": "S",
                        "venue": "X",
                        "option_type": option_type,
                        "strike": strike,
                        "expiry_at": expiry.isoformat(),
                        "listed_at": "2023-01-01T00:00:00Z",
                        "exercise_style": "european",
                    }
                )
                quote_rows.append(
                    {
                        "timestamp": quote_at.isoformat(),
                        "asset_id": option_id,
                        "venue": "X",
                        "bid": price - 0.001,
                        "ask": price + 0.001,
                    }
                )
    artifact = option_surface_smooth_artifact(
        pd.DataFrame(rows),
        pd.DataFrame(quote_rows),
        underlying_id="S",
        venue="X",
        evaluated_at="2024-01-02T00:00:00Z",
        spot=100.0,
        moneyness_grid=[-0.15, 0.0, 0.15],
        min_expiries=2,
        min_strikes_per_expiry=3,
    )

    assert artifact.summary["observed_expiry_count"] == 2
    assert artifact.summary["smoothed_node_count"] == 6
    assert artifact.summary["blocker_count"] == 0
    assert artifact.summary["calendar_arbitrage_violations"] == 0
    assert artifact.summary["butterfly_arbitrage_violations"] == 0
    assert artifact.provenance["arbitrage_constraints"] == "calendar_total_variance_and_call_butterfly"
    assert artifact.provenance["live_order_submission"] is False

    fitted = option_surface_smooth_artifact(
        pd.DataFrame(rows),
        pd.DataFrame(quote_rows),
        underlying_id="S",
        venue="X",
        evaluated_at="2024-01-02T00:00:00Z",
        spot=100.0,
        moneyness_grid=[-0.15, 0.0, 0.15],
        min_expiries=2,
        min_strikes_per_expiry=3,
        smoothing_method="quadratic_total_variance",
    )
    assert fitted.provenance["smoothing"] == (
        "quadratic_total_variance_then_bounded_linear_interpolation"
    )
    assert fitted.summary["blocker_count"] == 0
    svi = option_surface_smooth_artifact(
        pd.DataFrame(rows),
        pd.DataFrame(quote_rows),
        underlying_id="S",
        venue="X",
        evaluated_at="2024-01-02T00:00:00Z",
        spot=100.0,
        moneyness_grid=[-0.15, 0.0, 0.15],
        min_expiries=2,
        min_strikes_per_expiry=3,
        smoothing_method="svi_total_variance",
    )
    assert svi.provenance["smoothing"] == (
        "restricted_svi_total_variance_then_bounded_linear_interpolation"
    )
    assert svi.summary["blocker_count"] == 0
    ssvi = option_surface_smooth_artifact(
        pd.DataFrame(rows),
        pd.DataFrame(quote_rows),
        underlying_id="S",
        venue="X",
        evaluated_at="2024-01-02T00:00:00Z",
        spot=100.0,
        moneyness_grid=[-0.15, 0.0, 0.15],
        min_expiries=2,
        min_strikes_per_expiry=3,
        smoothing_method="ssvi_total_variance",
    )
    assert ssvi.provenance["smoothing"] == "ssvi_power_law_then_bounded_linear_interpolation"
    assert ssvi.summary["blocker_count"] == 0

    cubic_rows = []
    cubic_quotes = []
    for expiry_index, expiry in enumerate(expiry_values):
        years = (expiry - quote_at).total_seconds() / (365.25 * 24 * 3600)
        for strike in (80.0, 90.0, 100.0, 120.0):
            for option_type in ("call", "put"):
                option_id = f"{option_type[0].upper()}{expiry_index}{int(strike)}"
                price = black_scholes(
                    100.0,
                    strike,
                    years,
                    0.20,
                    option_type=option_type,
                ).price
                cubic_rows.append(
                    {
                        "option_id": option_id,
                        "underlying_id": "S",
                        "venue": "X",
                        "option_type": option_type,
                        "strike": strike,
                        "expiry_at": expiry.isoformat(),
                        "listed_at": "2023-01-01T00:00:00Z",
                        "exercise_style": "european",
                    }
                )
                cubic_quotes.append(
                    {
                        "timestamp": quote_at.isoformat(),
                        "asset_id": option_id,
                        "venue": "X",
                        "bid": price - 0.001,
                        "ask": price + 0.001,
                    }
                )
    cubic = option_surface_smooth_artifact(
        pd.DataFrame(cubic_rows),
        pd.DataFrame(cubic_quotes),
        underlying_id="S",
        venue="X",
        evaluated_at="2024-01-02T00:00:00Z",
        spot=100.0,
        moneyness_grid=[-0.15, 0.0, 0.15],
        min_expiries=2,
        min_strikes_per_expiry=4,
        smoothing_method="cubic_total_variance",
    )
    assert cubic.provenance["smoothing"] == (
        "cubic_total_variance_then_bounded_linear_interpolation"
    )
    assert cubic.summary["blocker_count"] == 0

    raw_svi_rows = []
    raw_svi_quotes = []
    smile = {80.0: 0.22, 90.0: 0.205, 100.0: 0.19, 110.0: 0.205, 120.0: 0.22}
    for expiry_index, expiry in enumerate(expiry_values):
        years = (expiry - quote_at).total_seconds() / (365.25 * 24 * 3600)
        for strike, volatility in smile.items():
            for option_type in ("call", "put"):
                option_id = f"{option_type[0].upper()}{expiry_index}{int(strike)}"
                price = black_scholes(
                    100.0,
                    strike,
                    years,
                    volatility,
                    option_type=option_type,
                ).price
                raw_svi_rows.append(
                    {
                        "option_id": option_id,
                        "underlying_id": "S",
                        "venue": "X",
                        "option_type": option_type,
                        "strike": strike,
                        "expiry_at": expiry.isoformat(),
                        "listed_at": "2023-01-01T00:00:00Z",
                        "exercise_style": "european",
                    }
                )
                raw_svi_quotes.append(
                    {
                        "timestamp": quote_at.isoformat(),
                        "asset_id": option_id,
                        "venue": "X",
                        "bid": price - 0.001,
                        "ask": price + 0.001,
                    }
                )
    raw_svi = option_surface_smooth_artifact(
        pd.DataFrame(raw_svi_rows),
        pd.DataFrame(raw_svi_quotes),
        underlying_id="S",
        venue="X",
        evaluated_at="2024-01-02T00:00:00Z",
        spot=100.0,
        moneyness_grid=[-0.15, 0.0, 0.15],
        min_expiries=2,
        min_strikes_per_expiry=5,
        smoothing_method="raw_svi_total_variance",
    )
    assert raw_svi.provenance["smoothing"] == (
        "raw_svi_total_variance_then_bounded_linear_interpolation"
    )
    assert raw_svi.summary["blocker_count"] == 0


def test_option_surface_smooth_blocks_calendar_variance_decrease() -> None:
    quote_at = pd.Timestamp("2024-01-01T00:00:00Z")
    expiry_values = [pd.Timestamp("2024-07-01T00:00:00Z"), pd.Timestamp("2025-01-01T00:00:00Z")]
    volatilities = [0.80, 0.10]
    strikes = [80.0, 100.0, 120.0]
    rows = []
    quote_rows = []
    for expiry_index, (expiry, volatility) in enumerate(zip(expiry_values, volatilities, strict=True)):
        years = (expiry - quote_at).total_seconds() / (365.25 * 24 * 3600)
        for strike in strikes:
            for option_type in ("call", "put"):
                option_id = f"{option_type[0].upper()}{expiry_index}{int(strike)}"
                price = black_scholes(
                    100.0,
                    strike,
                    years,
                    volatility,
                    option_type=option_type,
                ).price
                rows.append(
                    {
                        "option_id": option_id,
                        "underlying_id": "S",
                        "venue": "X",
                        "option_type": option_type,
                        "strike": strike,
                        "expiry_at": expiry.isoformat(),
                        "listed_at": "2023-01-01T00:00:00Z",
                        "exercise_style": "european",
                    }
                )
                quote_rows.append(
                    {
                        "timestamp": quote_at.isoformat(),
                        "asset_id": option_id,
                        "venue": "X",
                        "bid": price - 0.001,
                        "ask": price + 0.001,
                    }
                )
    artifact = option_surface_smooth_artifact(
        pd.DataFrame(rows),
        pd.DataFrame(quote_rows),
        underlying_id="S",
        venue="X",
        evaluated_at="2024-01-02T00:00:00Z",
        spot=100.0,
        moneyness_grid=[-0.15, 0.0, 0.15],
        min_expiries=2,
        min_strikes_per_expiry=3,
    )
    assert artifact.summary["calendar_arbitrage_violations"] > 0
    assert "option_surface_calendar_arbitrage" in {
        blocker.code for blocker in artifact.blockers
    }
