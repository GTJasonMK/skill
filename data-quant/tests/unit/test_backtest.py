from __future__ import annotations

import pandas as pd
import pytest

from data_quant.backtest import run_portfolio_backtest


def weights() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "decision_at": [
                "2024-01-02T09:00:00Z",
                "2024-01-02T09:00:00Z",
                "2024-01-03T09:00:00Z",
                "2024-01-03T09:00:00Z",
            ],
            "asset_id": ["A", "B", "A", "B"],
            "weight": [0.6, 0.4, 0.5, 0.5],
            "weight_type": ["target"] * 4,
            "currency": ["USD"] * 4,
        }
    )


def labels() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "decision_at": [
                "2024-01-02T09:00:00Z",
                "2024-01-02T09:00:00Z",
                "2024-01-03T09:00:00Z",
                "2024-01-03T09:00:00Z",
            ],
            "execution_at": [
                "2024-01-02T09:01:00Z",
                "2024-01-02T09:01:00Z",
                "2024-01-03T09:01:00Z",
                "2024-01-03T09:01:00Z",
            ],
            "return_start": [
                "2024-01-02T09:01:00Z",
                "2024-01-02T09:01:00Z",
                "2024-01-03T09:01:00Z",
                "2024-01-03T09:01:00Z",
            ],
            "return_end": [
                "2024-01-03T09:00:00Z",
                "2024-01-03T09:00:00Z",
                "2024-01-04T09:00:00Z",
                "2024-01-04T09:00:00Z",
            ],
            "asset_id": ["A", "B", "A", "B"],
            "return_value": [0.01, 0.02, -0.01, 0.03],
            "label": ["next_period"] * 4,
            "return_type": ["simple"] * 4,
            "return_basis": ["gross"] * 4,
            "corporate_action_policy": ["total_return"] * 4,
            "currency": ["USD"] * 4,
        }
    )


def test_portfolio_backtest_applies_costs_and_emits_artifact() -> None:
    result = run_portfolio_backtest(
        weights(),
        labels(),
        cost_bps_per_one_way_turnover=10,
        annualization=252,
        run_id="run-1",
    )

    assert result.periods["gross_return"].tolist() == pytest.approx([0.014, 0.01])
    assert result.periods["one_way_turnover"].tolist() == pytest.approx([0.5, 0.1])
    assert result.periods["net_return"].tolist() == pytest.approx([0.0135, 0.0099])
    assert result.artifact.artifact_type == "portfolio_backtest"
    assert result.artifact.run_id == "run-1"
    assert result.artifact.provenance["live_order_submission"] is False
    assert result.artifact.content_digest == result.artifact.compute_content_digest()
    assert result.artifact.summary["ending_nav"] == pytest.approx(1.0135 * 1.0099)


def test_portfolio_backtest_fails_when_nonzero_weight_has_no_return() -> None:
    incomplete = labels().query("not (asset_id == 'B' and decision_at == '2024-01-03T09:00:00Z')")
    with pytest.raises(ValueError, match="lack aligned return labels"):
        run_portfolio_backtest(weights(), incomplete)


def test_portfolio_backtest_requires_one_prefiltered_label() -> None:
    mixed = labels()
    mixed.loc[mixed.index[-1], "label"] = "other"
    with pytest.raises(ValueError, match="exactly one return label"):
        run_portfolio_backtest(weights(), mixed)


def test_portfolio_backtest_rejects_non_executable_return_window() -> None:
    invalid = labels()
    invalid.loc[0, "return_start"] = "2024-01-02T08:59:00Z"
    with pytest.raises(ValueError, match="return_start cannot precede"):
        run_portfolio_backtest(weights(), invalid)


@pytest.mark.parametrize("field", ["weight_type", "currency"])
def test_portfolio_backtest_requires_full_weight_semantics(field: str) -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        run_portfolio_backtest(weights().drop(columns=field), labels())


@pytest.mark.parametrize(
    "field",
    [
        "execution_at",
        "return_start",
        "return_end",
        "label",
        "return_type",
        "return_basis",
        "corporate_action_policy",
        "currency",
    ],
)
def test_portfolio_backtest_requires_full_return_label_semantics(field: str) -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        run_portfolio_backtest(weights(), labels().drop(columns=field))


def test_portfolio_backtest_rejects_overlapping_label_windows() -> None:
    overlapping = labels()
    overlapping.loc[overlapping["decision_at"] == "2024-01-02T09:00:00Z", "return_end"] = (
        "2024-01-03T10:00:00Z"
    )
    with pytest.raises(ValueError, match="cannot overlap"):
        run_portfolio_backtest(weights(), overlapping)


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("return_type", "log", "requires simple"),
        ("return_basis", "excess", "requires gross"),
        ("corporate_action_policy", "price_return", "requires total_return"),
    ],
)
def test_portfolio_backtest_rejects_non_nav_return_semantics(
    column: str,
    value: str,
    message: str,
) -> None:
    invalid = labels()
    invalid[column] = value
    with pytest.raises(ValueError, match=message):
        run_portfolio_backtest(weights(), invalid)


def test_portfolio_backtest_rejects_currency_mismatch() -> None:
    mismatched = labels()
    mismatched["currency"] = "EUR"
    with pytest.raises(ValueError, match="does not match"):
        run_portfolio_backtest(weights(), mismatched)


def financing_curves() -> pd.DataFrame:
    rows = []
    for effective_from, effective_to, rate in (
        ("2024-01-01T00:00:00Z", "2024-01-03T00:00:00Z", 0.12),
        ("2024-01-03T00:00:00Z", None, 0.24),
    ):
        for rate_type in ("cash", "financing"):
            for tenor_days in (0, 30):
                rows.append(
                    {
                        "curve_id": "USD-FUNDING",
                        "currency": "USD",
                        "rate_type": rate_type,
                        "effective_from": effective_from,
                        "effective_to": effective_to,
                        "available_at": effective_from,
                        "tenor_days": tenor_days,
                        "annual_rate": rate,
                        "day_count_basis": "ACT/365",
                        "compounding": "simple",
                    }
                )
    return pd.DataFrame(rows)


def test_portfolio_backtest_uses_pit_financing_curve_by_holding_period() -> None:
    zero_returns = labels()
    zero_returns["return_value"] = 0.0
    zero_returns["execution_at"] = zero_returns["decision_at"]
    zero_returns["return_start"] = zero_returns["decision_at"]
    zero_returns["return_end"] = [
        "2024-01-03T09:00:00Z",
        "2024-01-03T09:00:00Z",
        "2024-01-04T09:00:00Z",
        "2024-01-04T09:00:00Z",
    ]
    cash_weights = weights()
    cash_weights["weight"] *= 0.5

    result = run_portfolio_backtest(
        cash_weights,
        zero_returns,
        financing_curves=financing_curves(),
        financing_curve_id="USD-FUNDING",
    )

    assert result.periods["cash_financing_annual_rate"].tolist() == pytest.approx([0.12, 0.24])
    assert result.periods["cash_financing_return"].tolist() == pytest.approx(
        [0.5 * 0.12 / 365, 0.5 * 0.24 / 365]
    )
    assert result.artifact.parameters["financing_rate_source"] == "pit_financing_curve"


def test_portfolio_backtest_accounts_for_cash_and_short_borrow_rates() -> None:
    zero_returns = labels()
    zero_returns["return_value"] = 0.0
    cash_weights = weights()
    cash_weights["weight"] *= 0.5
    cash = run_portfolio_backtest(
        cash_weights,
        zero_returns,
        annualization=12,
        cash_rate_annual=0.12,
    )
    assert cash.periods["cash_financing_return"].tolist() == pytest.approx([0.005, 0.005])

    short_weights = weights()
    short_weights["weight"] = [1.2, -0.2, 1.2, -0.2]
    short = run_portfolio_backtest(
        short_weights,
        zero_returns,
        annualization=12,
        short_borrow_rate_annual=0.12,
    )
    assert short.periods["short_borrow_cost"].tolist() == pytest.approx([0.002, 0.002])
    assert short.periods["net_return"].tolist() == pytest.approx([-0.002, -0.002])


def test_portfolio_backtest_blends_secured_financing_spread() -> None:
    leveraged = weights()
    leveraged["weight"] = [0.8, 0.4, 0.8, 0.4]
    unsecured = run_portfolio_backtest(
        leveraged,
        labels().assign(return_value=0.0),
        annualization=12,
        financing_rate_annual=0.12,
    )
    secured = run_portfolio_backtest(
        leveraged,
        labels().assign(return_value=0.0),
        annualization=12,
        financing_rate_annual=0.12,
        secured_financing_spread_bps=100.0,
        collateralization_ratio=1.0,
    )
    assert unsecured.periods["cash_financing_return"].tolist() == pytest.approx([-0.002, -0.002])
    assert secured.periods["cash_financing_rate_type"].tolist() == [
        "blended_secured_financing",
        "blended_secured_financing",
    ]
    assert secured.periods["cash_financing_return"].tolist() == pytest.approx(
        [-0.2 * 0.11 / 12, -0.2 * 0.11 / 12]
    )
    assert secured.periods["cash_financing_return"].iloc[0] > unsecured.periods[
        "cash_financing_return"
    ].iloc[0]
    convex = run_portfolio_backtest(
        leveraged,
        labels().assign(return_value=0.0),
        annualization=12,
        financing_rate_annual=0.12,
        financing_convexity_bps=100.0,
    )
    extra = 0.01 * ((-0.2) ** 2)
    assert convex.periods["cash_financing_rate_type"].iloc[0] == "convex_leverage_financing"
    assert convex.periods["cash_financing_return"].tolist() == pytest.approx(
        [-0.2 * (0.12 + extra) / 12] * 2
    )
