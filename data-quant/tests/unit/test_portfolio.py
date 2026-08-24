from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data_quant.diagnostics.risk import (
    credit_migration_stress_artifact,
    factor_attribution_artifact,
    portfolio_stress_artifact,
)
from data_quant.portfolio import (
    OptimizationError,
    PortfolioConstraints,
    linear_cost_fraction,
    one_way_turnover,
    optimize_portfolio,
    traded_weight,
)
from data_quant.risk import (
    ewma_covariance,
    portfolio_volatility,
    regime_covariance,
    sample_covariance,
    shrinkage_covariance,
)


def inputs():
    mu = pd.Series([0.08, 0.05, 0.03], index=["A", "B", "C"])
    cov = pd.DataFrame(
        [[0.04, 0.01, 0.0], [0.01, 0.03, 0.005], [0.0, 0.005, 0.02]],
        index=mu.index,
        columns=mu.index,
    )
    return mu, cov


def test_turnover_and_cost_use_explicit_notional_convention() -> None:
    current = pd.Series({"A": 1.0, "B": 0.0})
    target = pd.Series({"A": 0.0, "B": 1.0})
    assert traded_weight(current, target) == 2.0
    assert one_way_turnover(current, target) == 1.0
    assert linear_cost_fraction(current, target, cost_bps_per_traded_notional=10) == pytest.approx(0.002)


def test_minimum_variance_respects_constraints() -> None:
    mu, cov = inputs()
    result = optimize_portfolio(
        mu,
        cov,
        constraints=PortfolioConstraints(target_sum=1.0, min_weight=0.0, max_weight=0.6),
    )
    assert result.weights.sum() == pytest.approx(1.0)
    assert result.weights.max() <= 0.6 + 1e-8
    assert result.volatility > 0


def test_turnover_limit_is_enforced() -> None:
    mu, cov = inputs()
    current = pd.Series([1 / 3, 1 / 3, 1 / 3], index=mu.index)
    result = optimize_portfolio(
        mu,
        cov,
        objective="mean_variance",
        current_weights=current,
        constraints=PortfolioConstraints(turnover_limit=0.05),
    )
    assert result.one_way_turnover is not None
    assert result.one_way_turnover <= 0.05 + 1e-8


def test_non_psd_covariance_fails_unless_repair_is_explicit() -> None:
    mu, cov = inputs()
    cov.loc["A", "B"] = cov.loc["B", "A"] = 0.2
    with pytest.raises(OptimizationError, match="positive semidefinite"):
        optimize_portfolio(mu, cov)
    repaired = optimize_portfolio(mu, cov, repair_covariance=True)
    assert repaired.covariance_repaired is True


def test_infeasible_bounds_fail() -> None:
    mu, cov = inputs()
    with pytest.raises(OptimizationError, match="failed"):
        optimize_portfolio(mu, cov, constraints=PortfolioConstraints(min_weight=0.5, max_weight=0.8))


def test_covariance_estimators_and_portfolio_volatility() -> None:
    returns = pd.DataFrame(
        {
            "A": [0.01, -0.02, 0.015, 0.005],
            "B": [0.005, -0.01, 0.01, 0.002],
        }
    )
    sample = sample_covariance(returns, annualization=252)
    ewma = ewma_covariance(returns, annualization=252)
    shrunk = shrinkage_covariance(returns, annualization=252)
    diagonal = shrinkage_covariance(returns, annualization=252, target="diagonal_variance")
    weights = pd.Series([0.5, 0.5], index=["A", "B"])
    assert np.allclose(sample, sample.T)
    assert np.allclose(ewma, ewma.T)
    assert np.allclose(shrunk, shrunk.T)
    assert np.allclose(diagonal, diagonal.T)
    assert portfolio_volatility(weights, sample) > 0
    assert np.trace(shrunk.to_numpy()) == pytest.approx(np.trace(diagonal.to_numpy()))

    regime = regime_covariance(returns, annualization=252, stress_regime="high")
    low_regime = regime_covariance(returns, annualization=252, stress_regime="low")
    assert np.allclose(regime, regime.T)
    assert np.allclose(low_regime, low_regime.T)


def test_portfolio_stress_blocks_historical_or_scenario_limit_breach() -> None:
    returns = pd.DataFrame(
        {
            "A": [0.01, -0.02, 0.015, 0.005, -0.01, 0.02, 0.0, -0.015, 0.01, 0.005],
            "B": [0.005, -0.01, 0.01, 0.002, -0.005, 0.01, 0.0, -0.01, 0.004, 0.003],
        }
    )
    weights = pd.Series({"A": 0.6, "B": 0.4})
    artifact = portfolio_stress_artifact(
        returns,
        weights,
        scenarios=[
            {"name": "mild", "asset_shocks": {"A": -0.02, "B": -0.01}},
            {"name": "crash", "asset_shocks": {"A": -0.30, "B": -0.20}},
        ],
        loss_limit=0.10,
    )

    assert artifact.summary["historical_expected_shortfall"] > 0
    assert artifact.summary["blocker_count"] == 1
    assert artifact.blockers[0].code == "scenario_loss_limit"


def test_credit_migration_prices_spread_moves_default_and_recovery() -> None:
    exposures = pd.DataFrame(
        {
            "observed_at": ["2024-01-01T00:00:00Z"] * 2,
            "available_at": ["2024-01-01T00:00:01Z"] * 2,
            "portfolio_id": ["P", "P"],
            "instrument_id": ["BOND-A", "BOND-B"],
            "rating": ["A", "B"],
            "market_value": [1_000.0, 1_000.0],
            "modified_duration": [4.0, 4.0],
            "recovery_rate": [0.40, 0.40],
            "currency": ["USD", "USD"],
        }
    )
    matrix = pd.DataFrame(
        [
            {
                "matrix_id": "M",
                "observed_at": "2023-12-31T00:00:00Z",
                "available_at": "2023-12-31T00:00:01Z",
                "horizon_years": 1.0,
                "from_rating": source,
                "to_rating": target,
                "probability": probability,
            }
            for source, transitions in (
                ("A", {"A": 0.90, "B": 0.09, "D": 0.01}),
                ("B", {"A": 0.05, "B": 0.90, "D": 0.05}),
            )
            for target, probability in transitions.items()
        ]
    )
    common = {
        "portfolio_id": "P",
        "matrix_id": "M",
        "evaluated_at": "2024-01-02T00:00:00Z",
        "rating_spreads_bps": {"A": 100.0, "B": 300.0},
        "loss_limit_fraction": 0.03,
    }

    base = credit_migration_stress_artifact(
        exposures,
        matrix,
        default_probability_multiplier=1.0,
        **common,
    )
    stressed = credit_migration_stress_artifact(
        exposures,
        matrix,
        default_probability_multiplier=3.0,
        **common,
    )

    assert base.summary["base_expected_credit_loss"] == pytest.approx(39.2)
    assert base.summary["blocker_count"] == 0
    assert stressed.summary["stressed_expected_credit_loss"] > 100
    assert stressed.blockers[0].code == "credit_migration_loss_limit"

    stochastic = credit_migration_stress_artifact(
        exposures,
        matrix,
        default_probability_multiplier=1.0,
        recovery_volatility=0.20,
        recovery_confidence=0.95,
        loss_limit_fraction=0.50,
        **{key: value for key, value in common.items() if key != "loss_limit_fraction"},
    )
    assert stochastic.summary["recovery_stress"] == "lognormal_quantile"

    convex = exposures.copy()
    convex["convexity"] = [60.0, 60.0]
    with_convexity = credit_migration_stress_artifact(
        convex,
        matrix,
        default_probability_multiplier=1.0,
        **common,
    )
    assert with_convexity.provenance["migration_repricing"] == "second_order_spread_convexity"
    assert with_convexity.summary["base_expected_credit_loss"] < base.summary[
        "base_expected_credit_loss"
    ]
    assert all(detail["stressed_recovery_rate"] < 0.40 for detail in stochastic.details)
    assert stochastic.summary["all_default_loss"] > 1_200.0

    correlated = credit_migration_stress_artifact(
        exposures,
        matrix,
        default_probability_multiplier=1.0,
        migration_correlation=0.50,
        tail_confidence=0.99,
        tail_loss_limit_fraction=0.02,
        **{key: value for key, value in common.items() if key != "loss_limit_fraction"},
    )
    assert correlated.provenance["correlation_model"] == "one_factor_gaussian_default"
    assert correlated.summary["correlated_tail_loss"] is not None
    assert correlated.summary["correlated_tail_loss"] > correlated.summary[
        "base_expected_credit_loss"
    ]
    assert any(
        blocker.code == "credit_migration_correlation_tail_limit"
        for blocker in correlated.blockers
    )

    with_liquidity = credit_migration_stress_artifact(
        exposures,
        matrix,
        default_probability_multiplier=1.0,
        rating_liquidity_bps={"A": 10.0, "B": 80.0},
        **common,
    )
    assert with_liquidity.provenance["spread_liquidity"] == "rating_liquidity_premium"
    assert with_liquidity.summary["base_expected_credit_loss"] > base.summary[
        "base_expected_credit_loss"
    ]

    defaulted = exposures.copy()
    defaulted["rating"] = ["D", "D"]
    realized = credit_migration_stress_artifact(
        defaulted,
        matrix,
        default_probability_multiplier=1.0,
        realized_default_settlement_fraction=0.50,
        loss_limit_fraction=0.20,
        **{key: value for key, value in common.items() if key != "loss_limit_fraction"},
    )
    assert realized.provenance["realized_default_accounting"] == "settlement_fraction_snapshot"
    assert realized.summary["realized_settlement_loss"] == pytest.approx(600.0)
    assert realized.summary["realized_loss_fraction"] == pytest.approx(0.30)
    assert any(
        blocker.code == "credit_realized_default_settlement_limit"
        for blocker in realized.blockers
    )


def test_factor_attribution_reconciles_factor_specific_and_formal_limits() -> None:
    weights = pd.DataFrame(
        {
            "decision_at": ["2024-01-01T00:00:00Z"] * 2,
            "asset_id": ["A", "B"],
            "weight": [0.60, 0.40],
            "weight_type": ["target", "target"],
            "currency": ["USD", "USD"],
        }
    )
    labels = pd.DataFrame(
        {
            "decision_at": ["2024-01-01T00:00:00Z"] * 2,
            "execution_at": ["2024-01-02T00:00:00Z"] * 2,
            "return_start": ["2024-01-02T00:00:00Z"] * 2,
            "return_end": ["2024-02-01T00:00:00Z"] * 2,
            "asset_id": ["A", "B"],
            "label": ["month", "month"],
            "return_value": [0.025, -0.010],
            "return_type": ["simple", "simple"],
            "return_basis": ["gross", "gross"],
            "corporate_action_policy": ["total_return", "total_return"],
            "currency": ["USD", "USD"],
        }
    )
    exposures = pd.DataFrame(
        {
            "as_of": ["2024-01-01T00:00:00Z"] * 4,
            "available_at": ["2024-01-01T00:00:00Z"] * 4,
            "factor_model_id": ["M"] * 4,
            "asset_id": ["A", "A", "B", "B"],
            "factor_id": ["VALUE", "MOM", "VALUE", "MOM"],
            "exposure": [1.0, 0.5, -0.5, 1.0],
        }
    )
    factor_returns = pd.DataFrame(
        {
            "factor_model_id": ["M", "M"],
            "factor_id": ["VALUE", "MOM"],
            "return_start": ["2024-01-02T00:00:00Z"] * 2,
            "return_end": ["2024-02-01T00:00:00Z"] * 2,
            "available_at": ["2024-02-01T00:00:01Z"] * 2,
            "return_value": [0.02, -0.01],
            "return_type": ["simple", "simple"],
            "return_basis": ["gross", "gross"],
            "currency": ["USD", "USD"],
        }
    )
    common = {
        "factor_model_id": "M",
        "decision_at": "2024-01-01T00:00:00Z",
        "evaluated_at": "2024-02-02T00:00:00Z",
        "label": "month",
        "weight_type": "target",
    }

    artifact = factor_attribution_artifact(
        weights,
        labels,
        exposures,
        factor_returns,
        factor_exposure_limits={"VALUE": 0.50, "MOM": 0.80},
        specific_contribution_limit=0.02,
        **common,
    )
    blocked = factor_attribution_artifact(
        weights,
        labels,
        exposures,
        factor_returns,
        factor_exposure_limits={"VALUE": 0.30},
        specific_contribution_limit=0.005,
        **common,
    )

    assert artifact.summary["portfolio_return"] == pytest.approx(0.011)
    assert artifact.summary["factor_return_contribution"] == pytest.approx(0.001)
    assert artifact.summary["specific_return_contribution"] == pytest.approx(0.010)
    assert artifact.summary["reconciliation_error"] == pytest.approx(0.0)
    assert artifact.summary["blocker_count"] == 0
    assert {message.code for message in blocked.blockers} == {
        "factor_exposure_limit",
        "specific_contribution_limit",
    }
