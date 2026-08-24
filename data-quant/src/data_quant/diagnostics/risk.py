"""Native covariance and portfolio-risk diagnostics."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.contracts.parameters import (
    CovarianceRiskParameters,
    CreditMigrationParameters,
    FactorAttributionParameters,
    FactorRiskParameters,
    PortfolioStressParameters,
)
from data_quant.io.validation import parse_utc_timestamp
from data_quant.registry import register_diagnostic
from data_quant.risk import (
    ewma_covariance,
    portfolio_volatility,
    regime_covariance,
    sample_covariance,
    shrinkage_covariance,
)


@register_diagnostic(
    "covariance-risk",
    "portfolio_risk",
    required_table_types=("return_labels", "portfolio_weights"),
    manifest_stage="risk",
    parameter_model=CovarianceRiskParameters,
    description="Estimate covariance and decompose portfolio volatility without claiming stress coverage.",
)
def covariance_risk_artifact(
    returns: pd.DataFrame,
    weights: pd.Series,
    *,
    estimator: str = "sample",
    annualization: float = 252.0,
    decay: float = 0.94,
    shrinkage_target: str = "constant_correlation",
    stress_regime: str = "high",
    run_id: str | None = None,
) -> ArtifactEnvelope:
    numeric_weights = pd.to_numeric(weights, errors="coerce")
    if numeric_weights.isna().any() or not all(math.isfinite(float(value)) for value in numeric_weights):
        raise ValueError("Risk weights must be finite and non-null.")
    if numeric_weights.index.astype(str).duplicated().any():
        raise ValueError("Risk weight asset IDs must be unique.")
    numeric_weights.index = numeric_weights.index.astype(str)
    if estimator == "sample":
        covariance = sample_covariance(returns, annualization=annualization)
    elif estimator == "ewma":
        covariance = ewma_covariance(returns, decay=decay, annualization=annualization)
    elif estimator == "ledoit_wolf":
        covariance = shrinkage_covariance(
            returns,
            annualization=annualization,
            target=shrinkage_target,
        )
    elif estimator == "regime":
        covariance = regime_covariance(
            returns,
            annualization=annualization,
            stress_regime=stress_regime,
        )
    else:
        raise ValueError("estimator must be 'sample', 'ewma', 'ledoit_wolf', or 'regime'.")
    volatility = portfolio_volatility(numeric_weights, covariance)
    assets = list(numeric_weights.index)
    matrix = covariance.loc[assets, assets].to_numpy(dtype=float)
    vector = numeric_weights.to_numpy(dtype=float)
    covariance_times_weight = matrix @ vector
    marginal = covariance_times_weight / volatility if volatility > 0 else np.zeros_like(vector)
    component = vector * marginal
    details = [
        {
            "asset_id": asset,
            "weight": float(vector[index]),
            "marginal_volatility": float(marginal[index]),
            "component_volatility": float(component[index]),
        }
        for index, asset in enumerate(assets)
    ]
    return ArtifactEnvelope(
        artifact_type="portfolio_risk",
        run_id=run_id,
        producer=ProducerReference(name="covariance-risk", version=__version__),
        parameters={
            "estimator": estimator,
            "annualization": annualization,
            "decay": decay if estimator == "ewma" else None,
            "shrinkage_target": shrinkage_target if estimator == "ledoit_wolf" else None,
            "stress_regime": stress_regime if estimator == "regime" else None,
        },
        summary={
            "asset_count": len(assets),
            "observation_count": int(len(returns)),
            "annualized_volatility": volatility,
            "gross_exposure": float(numeric_weights.abs().sum()),
            "net_exposure": float(numeric_weights.sum()),
            "covariance_condition_number": float(np.linalg.cond(matrix)),
        },
        details=details,
        evidence_gaps=[
            DiagnosticMessage(
                code="risk_scope_baseline_only",
                message=(
                    "Covariance volatility does not cover factor attribution, tails, liquidity, funding, "
                    "margin, concentration limits, or scenario stress."
                ),
                severity="warning",
            )
        ],
        provenance={"live_order_submission": False},
    ).finalize()


@register_diagnostic(
    "portfolio-stress",
    "portfolio_stress",
    required_table_types=("return_labels", "portfolio_weights"),
    manifest_stage="risk",
    parameter_model=PortfolioStressParameters,
    description="Measure historical tail loss and explicit linear asset-shock scenarios.",
)
def portfolio_stress_artifact(
    returns: pd.DataFrame,
    weights: pd.Series,
    *,
    scenarios: list[dict[str, Any]],
    confidence: float = 0.95,
    loss_limit: float = 0.10,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    if not 0.5 < confidence < 1 or loss_limit <= 0:
        raise ValueError("Stress confidence/loss_limit parameters are invalid.")
    numeric_weights = pd.to_numeric(weights, errors="coerce")
    if numeric_weights.isna().any() or not all(
        math.isfinite(float(value)) for value in numeric_weights
    ):
        raise ValueError("Stress weights must be finite and non-null.")
    numeric_weights.index = numeric_weights.index.astype(str)
    active_weights = numeric_weights[numeric_weights != 0]
    missing_assets = sorted(set(active_weights.index) - set(returns.columns.astype(str)))
    if missing_assets:
        raise ValueError(f"Stress return history is missing weighted assets: {missing_assets}")
    numeric_returns = returns.copy()
    numeric_returns.columns = numeric_returns.columns.astype(str)
    numeric_returns = numeric_returns[list(active_weights.index)].apply(pd.to_numeric, errors="coerce")
    if len(numeric_returns) < 5 or numeric_returns.isna().any().any():
        raise ValueError("Portfolio stress requires five complete return periods.")
    portfolio_returns = numeric_returns.dot(active_weights)
    quantile_return = float(portfolio_returns.quantile(1.0 - confidence))
    tail = portfolio_returns[portfolio_returns <= quantile_return]
    value_at_risk = max(0.0, -quantile_return)
    expected_shortfall = max(0.0, -float(tail.mean()))
    blockers: list[DiagnosticMessage] = []
    if expected_shortfall > loss_limit:
        blockers.append(
            DiagnosticMessage(
                code="historical_expected_shortfall_limit",
                message="Historical expected shortfall exceeds the configured loss limit.",
                severity="blocker",
                context={"expected_shortfall": expected_shortfall, "loss_limit": loss_limit},
            )
        )
    details = []
    scenario_losses: list[float] = []
    required_assets = set(active_weights.index)
    cash_weight = 1.0 - float(active_weights.sum())
    for scenario in scenarios:
        name = str(scenario["name"])
        asset_shocks = {str(key): float(value) for key, value in scenario["asset_shocks"].items()}
        missing_shocks = sorted(required_assets - set(asset_shocks))
        if missing_shocks:
            raise ValueError(f"Stress scenario {name!r} is missing assets: {missing_shocks}")
        scenario_return = float(
            sum(active_weights[asset] * asset_shocks[asset] for asset in active_weights.index)
            + cash_weight * float(scenario.get("cash_shock", 0.0))
        )
        loss = max(0.0, -scenario_return)
        row = {
            "scenario": name,
            "portfolio_return": scenario_return,
            "loss": loss,
            "limit": loss_limit,
            "breach": loss > loss_limit,
        }
        details.append(row)
        scenario_losses.append(loss)
        if row["breach"]:
            blockers.append(
                DiagnosticMessage(
                    code="scenario_loss_limit",
                    message=f"Stress scenario {name!r} exceeds the configured loss limit.",
                    severity="blocker",
                    context=row,
                )
            )
    return ArtifactEnvelope(
        artifact_type="portfolio_stress",
        run_id=run_id,
        producer=ProducerReference(name="portfolio-stress", version=__version__),
        parameters={
            "confidence": confidence,
            "loss_limit": loss_limit,
            "scenarios": scenarios,
        },
        summary={
            "observation_count": len(portfolio_returns),
            "asset_count": len(active_weights),
            "cash_weight": cash_weight,
            "historical_value_at_risk": value_at_risk,
            "historical_expected_shortfall": expected_shortfall,
            "worst_scenario_loss": max(scenario_losses, default=None),
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            DiagnosticMessage(
                code="linear_stress_scope",
                message=(
                    "Historical and linear shocks omit nonlinear repricing, liquidity/impact, funding, "
                    "margin calls, regime probabilities, and second-order contagion."
                ),
                severity="warning",
            )
        ],
        details=details,
        provenance={"live_order_submission": False},
    ).finalize()


@register_diagnostic(
    "credit-migration-stress",
    "credit_migration_stress",
    required_table_types=("credit_exposures", "credit_transition_matrix"),
    manifest_stage="risk",
    parameter_model=CreditMigrationParameters,
    description="Estimate PIT rating-migration/default loss with spread-duration and recovery semantics.",
)
def credit_migration_stress_artifact(
    exposures: pd.DataFrame,
    transition_matrix: pd.DataFrame,
    *,
    portfolio_id: str,
    matrix_id: str,
    evaluated_at: str,
    rating_spreads_bps: dict[str, float],
    rating_liquidity_bps: dict[str, float] | None = None,
    default_rating: str = "D",
    default_probability_multiplier: float = 1.0,
    loss_limit_fraction: float = 0.05,
    row_sum_tolerance: float = 1e-8,
    recovery_volatility: float = 0.0,
    recovery_confidence: float = 0.95,
    migration_correlation: float = 0.0,
    tail_confidence: float = 0.99,
    tail_loss_limit_fraction: float | None = None,
    realized_default_settlement_fraction: float | None = None,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    rating_liquidity_bps = rating_liquidity_bps or {}
    if (
        default_probability_multiplier < 1
        or loss_limit_fraction <= 0
        or row_sum_tolerance <= 0
        or recovery_volatility < 0
        or not 0.5 < recovery_confidence < 1
        or not 0 <= migration_correlation < 1
        or not 0.5 < tail_confidence < 1
        or (tail_loss_limit_fraction is not None and tail_loss_limit_fraction <= 0)
        or (
            realized_default_settlement_fraction is not None
            and not 0 <= realized_default_settlement_fraction <= 1
        )
        or any(spread < 0 for spread in rating_spreads_bps.values())
        or any(liq < 0 for liq in rating_liquidity_bps.values())
        or not set(rating_liquidity_bps) <= set(rating_spreads_bps)
    ):
        raise ValueError("Credit migration stress parameters are invalid.")
    evaluated = parse_utc_timestamp(pd.Series([evaluated_at]), "evaluated_at").iloc[0]
    selected_exposures = exposures[exposures["portfolio_id"].astype(str) == portfolio_id].copy()
    for column in ("observed_at", "available_at"):
        selected_exposures[column] = parse_utc_timestamp(selected_exposures[column], column)
    selected_exposures = selected_exposures[
        (selected_exposures["observed_at"] <= evaluated)
        & (selected_exposures["available_at"] <= evaluated)
    ]
    if selected_exposures.empty:
        raise ValueError("No point-in-time credit exposures are available for the portfolio.")
    selected_exposures = selected_exposures[
        selected_exposures["observed_at"] == selected_exposures["observed_at"].max()
    ].copy()
    for column in ("market_value", "modified_duration", "recovery_rate"):
        selected_exposures[column] = pd.to_numeric(selected_exposures[column], errors="coerce")
    if "convexity" not in selected_exposures:
        selected_exposures["convexity"] = pd.Series(0.0, index=selected_exposures.index)
    selected_exposures["convexity"] = pd.to_numeric(
        selected_exposures["convexity"], errors="coerce"
    ).fillna(0.0)
    if (
        selected_exposures[["market_value", "modified_duration", "recovery_rate", "convexity"]]
        .isna()
        .any()
        .any()
        or (selected_exposures["market_value"] <= 0).any()
        or (selected_exposures["modified_duration"] < 0).any()
        or (selected_exposures["convexity"] < 0).any()
        or selected_exposures["recovery_rate"].lt(0).any()
        or selected_exposures["recovery_rate"].gt(1).any()
    ):
        raise ValueError("Credit exposure value, duration, recovery, or convexity is invalid.")
    if selected_exposures["currency"].astype(str).nunique() != 1:
        raise ValueError("Credit migration stress requires one reporting currency.")
    if selected_exposures["rating"].astype(str).eq(default_rating).any():
        if realized_default_settlement_fraction is None:
            raise ValueError(
                "Current default-state exposures require realized default accounting, not migration."
            )
    else:
        realized_default_settlement_fraction = None
    matrix = transition_matrix[transition_matrix["matrix_id"].astype(str) == matrix_id].copy()
    for column in ("observed_at", "available_at"):
        matrix[column] = parse_utc_timestamp(matrix[column], column)
    matrix = matrix[
        (matrix["observed_at"] <= evaluated) & (matrix["available_at"] <= evaluated)
    ]
    if matrix.empty:
        raise ValueError("No point-in-time credit transition matrix is available.")
    matrix = matrix[matrix["observed_at"] == matrix["observed_at"].max()].copy()
    matrix["probability"] = pd.to_numeric(matrix["probability"], errors="coerce")
    matrix["horizon_years"] = pd.to_numeric(matrix["horizon_years"], errors="coerce")
    if (
        matrix[["probability", "horizon_years"]].isna().any().any()
        or matrix["probability"].lt(0).any()
        or matrix["probability"].gt(1).any()
        or matrix["horizon_years"].le(0).any()
        or matrix["horizon_years"].nunique() != 1
    ):
        raise ValueError("Credit transition probabilities or horizons are invalid.")
    required_ratings = set(selected_exposures["rating"].astype(str))
    if realized_default_settlement_fraction is not None:
        required_ratings = {rating for rating in required_ratings if rating != default_rating}
    available_rows = set(matrix["from_rating"].astype(str))
    missing_rows = sorted(required_ratings - available_rows)
    if missing_rows:
        raise ValueError(f"Transition matrix is missing exposure ratings: {missing_rows}")
    row_sums = matrix.groupby(matrix["from_rating"].astype(str))["probability"].sum()
    invalid_rows = row_sums[~np.isclose(row_sums, 1.0, rtol=0, atol=row_sum_tolerance)]
    if not invalid_rows.empty:
        raise ValueError(f"Transition matrix rows must sum to one: {invalid_rows.to_dict()}")
    reachable_non_default = set(
        matrix.loc[
            (matrix["probability"] > 0)
            & matrix["to_rating"].astype(str).ne(default_rating),
            "to_rating",
        ].astype(str)
    )
    missing_spreads = sorted((required_ratings | reachable_non_default) - set(rating_spreads_bps))
    if missing_spreads:
        raise ValueError(f"rating_spreads_bps is missing states: {missing_spreads}")

    def probabilities(from_rating: str, multiplier: float) -> dict[str, float]:
        rows = matrix[matrix["from_rating"].astype(str) == from_rating]
        base = {
            str(row["to_rating"]): float(row["probability"])
            for row in rows.to_dict("records")
        }
        default_probability = base.get(default_rating, 0.0)
        stressed_default = min(1.0, default_probability * multiplier)
        non_default_total = 1.0 - default_probability
        scale = (1.0 - stressed_default) / non_default_total if non_default_total > 0 else 0.0
        return {
            state: stressed_default if state == default_rating else probability * scale
            for state, probability in base.items()
        }

    def exposure_expected_pnl(
        from_rating: str,
        value: float,
        duration: float,
        convexity: float,
        recovery: float,
        multiplier: float,
    ) -> tuple[float, float]:
        pnl = 0.0
        state_probabilities = probabilities(from_rating, multiplier)
        for to_rating, probability in state_probabilities.items():
            if to_rating == default_rating:
                state_pnl = -value * (1.0 - recovery)
            else:
                spread_change = (
                    rating_spreads_bps[to_rating]
                    + rating_liquidity_bps.get(to_rating, 0.0)
                    - rating_spreads_bps[from_rating]
                    - rating_liquidity_bps.get(from_rating, 0.0)
                ) / 10_000.0
                first_order = -duration * spread_change
                second_order = 0.5 * convexity * spread_change**2
                state_pnl = value * (first_order + second_order)
            pnl += probability * state_pnl
        return pnl, state_probabilities.get(default_rating, 0.0)

    details = []
    total_value = float(selected_exposures["market_value"].sum())
    base_expected_pnl = 0.0
    stressed_expected_pnl = 0.0
    all_default_loss = 0.0
    recovery_quantile = norm.ppf(recovery_confidence)
    for row in selected_exposures.to_dict("records"):
        from_rating = str(row["rating"])
        value = float(row["market_value"])
        duration = float(row["modified_duration"])
        convexity = float(row["convexity"])
        recovery = float(row["recovery_rate"])
        stressed_recovery = max(
            0.0, min(1.0, recovery - recovery_quantile * recovery_volatility)
        )

        base_pnl, base_default_probability = exposure_expected_pnl(
            from_rating,
            value,
            duration,
            convexity,
            recovery,
            1.0,
        )
        stressed_pnl, stressed_default_probability = exposure_expected_pnl(
            from_rating,
            value,
            duration,
            convexity,
            stressed_recovery,
            default_probability_multiplier,
        )
        base_expected_pnl += base_pnl
        stressed_expected_pnl += stressed_pnl
        instrument_default_loss = value * (1.0 - stressed_recovery)
        all_default_loss += instrument_default_loss
        details.append(
            {
                "instrument_id": str(row["instrument_id"]),
                "from_rating": from_rating,
                "market_value": value,
                "modified_duration": duration,
                "convexity": convexity,
                "recovery_rate": recovery,
                "stressed_recovery_rate": stressed_recovery,
                "base_default_probability": base_default_probability,
                "stressed_default_probability": stressed_default_probability,
                "base_expected_pnl": base_pnl,
                "base_expected_loss": max(0.0, -base_pnl),
                "stressed_expected_pnl": stressed_pnl,
                "stressed_expected_loss": max(0.0, -stressed_pnl),
                "all_default_loss": instrument_default_loss,
            }
        )
    base_expected_loss = max(0.0, -base_expected_pnl)
    stressed_expected_loss = max(0.0, -stressed_expected_pnl)
    stressed_loss_fraction = stressed_expected_loss / total_value
    blockers = []
    realized_settlement_loss = 0.0
    if realized_default_settlement_fraction is not None:
        for row in selected_exposures.to_dict("records"):
            value = float(row["market_value"])
            recovery = float(row["recovery_rate"])
            realized_settlement_loss += (
                value * (1.0 - recovery) * realized_default_settlement_fraction
            )
        realized_loss_fraction = realized_settlement_loss / total_value
        if realized_loss_fraction > loss_limit_fraction:
            blockers.append(
                DiagnosticMessage(
                    code="credit_realized_default_settlement_limit",
                    message="Realized default settlement loss exceeds the configured limit.",
                    severity="blocker",
                    context={
                        "realized_settlement_loss": realized_settlement_loss,
                        "realized_loss_fraction": realized_loss_fraction,
                        "limit": loss_limit_fraction,
                    },
                )
            )
    else:
        realized_loss_fraction = None
    if stressed_loss_fraction > loss_limit_fraction:
        blockers.append(
            DiagnosticMessage(
                code="credit_migration_loss_limit",
                message="Stressed expected credit loss exceeds the configured portfolio limit.",
                severity="blocker",
                context={
                    "stressed_expected_loss": stressed_expected_loss,
                    "stressed_loss_fraction": stressed_loss_fraction,
                    "limit": loss_limit_fraction,
                },
            )
        )
    correlated_tail_loss: float | None = None
    correlated_tail_fraction: float | None = None
    if migration_correlation > 0:
        factor_threshold = norm.ppf(1.0 - tail_confidence)
        systematic = factor_threshold
        idiosyncratic = math.sqrt(1.0 - migration_correlation)
        correlated_tail_loss = 0.0
        for detail, row in zip(details, selected_exposures.to_dict("records"), strict=True):
            from_rating = str(row["rating"])
            value = float(row["market_value"])
            recovery = float(row["recovery_rate"])
            default_probability = probabilities(from_rating, 1.0).get(default_rating, 0.0)
            threshold = norm.ppf(max(default_probability, 1e-12))
            conditioned_default = norm.cdf(
                (threshold - math.sqrt(migration_correlation) * systematic) / idiosyncratic
            )
            detail["correlated_default_probability"] = conditioned_default
            correlated_tail_loss += value * (1.0 - recovery) * conditioned_default
        correlated_tail_fraction = correlated_tail_loss / total_value
        if (
            tail_loss_limit_fraction is not None
            and correlated_tail_fraction > tail_loss_limit_fraction
        ):
            blockers.append(
                DiagnosticMessage(
                    code="credit_migration_correlation_tail_limit",
                    message="Correlated one-factor tail loss exceeds the configured tail limit.",
                    severity="blocker",
                    context={
                        "correlated_tail_loss": correlated_tail_loss,
                        "correlated_tail_fraction": correlated_tail_fraction,
                        "limit": tail_loss_limit_fraction,
                    },
                )
            )
    return ArtifactEnvelope(
        artifact_type="credit_migration_stress",
        run_id=run_id,
        producer=ProducerReference(name="credit-migration-stress", version=__version__),
        parameters={
            "portfolio_id": portfolio_id,
            "matrix_id": matrix_id,
            "evaluated_at": evaluated.isoformat(),
            "default_rating": default_rating,
            "rating_spreads_bps": rating_spreads_bps,
            "rating_liquidity_bps": rating_liquidity_bps,
            "default_probability_multiplier": default_probability_multiplier,
            "loss_limit_fraction": loss_limit_fraction,
            "row_sum_tolerance": row_sum_tolerance,
            "recovery_volatility": recovery_volatility,
            "recovery_confidence": recovery_confidence,
            "migration_correlation": migration_correlation,
            "tail_confidence": tail_confidence,
            "tail_loss_limit_fraction": tail_loss_limit_fraction,
            "realized_default_settlement_fraction": realized_default_settlement_fraction,
        },
        summary={
            "currency": str(selected_exposures["currency"].iloc[0]),
            "matrix_observed_at": pd.Timestamp(matrix["observed_at"].iloc[0]).isoformat(),
            "horizon_years": float(matrix["horizon_years"].iloc[0]),
            "exposure_count": len(details),
            "total_market_value": total_value,
            "base_expected_credit_loss": base_expected_loss,
            "stressed_expected_credit_loss": stressed_expected_loss,
            "stressed_loss_fraction": stressed_loss_fraction,
            "all_default_loss": all_default_loss,
            "recovery_stress": "lognormal_quantile" if recovery_volatility > 0 else "deterministic",
            "correlated_tail_loss": correlated_tail_loss,
            "correlated_tail_fraction": correlated_tail_fraction,
            "realized_settlement_loss": realized_settlement_loss,
            "realized_loss_fraction": realized_loss_fraction,
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            DiagnosticMessage(
                code="credit_migration_scope",
                message=(
                    "Independent one-horizon transition rows and second-order spread/convexity "
                    "repricing with rating-liquidity premia omit rating-watch dynamics and "
                    "settlement timing. Realized-default accounting is a single settlement-fraction "
                    "snapshot without recovery-timing cashflow sequencing. Correlation stress uses "
                    "a one-factor Gaussian default model (systematic + idiosyncratic), not a full "
                    "migration copula. Stochastic recovery uses a normal quantile shock on the "
                    "recovery rate, not a full loss-distribution."
                ),
                severity="warning",
            )
        ],
        details=details,
        provenance={
            "migration_repricing": "second_order_spread_convexity",
            "default_loss": "market_value_times_one_minus_stressed_recovery",
            "recovery_stress": "normal_quantile_shock",
            "correlation_model": "one_factor_gaussian_default",
            "spread_liquidity": "rating_liquidity_premium",
            "realized_default_accounting": "settlement_fraction_snapshot",
            "live_order_submission": False,
        },
    ).finalize()


@register_diagnostic(
    "factor-risk",
    "factor_risk",
    required_table_types=("portfolio_weights", "factor_exposures", "factor_returns"),
    manifest_stage="risk",
    parameter_model=FactorRiskParameters,
    description="Estimate PIT portfolio factor covariance risk and component volatility.",
)
def factor_risk_artifact(
    weights: pd.DataFrame,
    exposures: pd.DataFrame,
    factor_returns: pd.DataFrame,
    *,
    factor_model_id: str,
    decision_at: str,
    weight_type: str,
    return_basis: str = "gross",
    lookback_periods: int = 60,
    minimum_observations: int = 20,
    annualization: float = 252.0,
    maximum_annualized_factor_volatility: float = 1.0,
    maximum_covariance_condition_number: float = 1e8,
    factor_exposure_limits: dict[str, float] | None = None,
    factor_component_volatility_limits: dict[str, float] | None = None,
    specific_risk_volatilities: dict[str, float] | None = None,
    maximum_annualized_total_volatility: float | None = None,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    factor_exposure_limits = factor_exposure_limits or {}
    factor_component_volatility_limits = factor_component_volatility_limits or {}
    specific_risk_volatilities = specific_risk_volatilities or {}
    if (
        return_basis not in {"gross", "excess"}
        or lookback_periods < 3
        or minimum_observations < 3
        or minimum_observations > lookback_periods
        or annualization <= 0
        or maximum_annualized_factor_volatility < 0
        or maximum_covariance_condition_number <= 1
        or any(limit <= 0 for limit in factor_exposure_limits.values())
        or any(limit <= 0 for limit in factor_component_volatility_limits.values())
        or any(vol < 0 for vol in specific_risk_volatilities.values())
        or (maximum_annualized_total_volatility is not None and maximum_annualized_total_volatility <= 0)
    ):
        raise ValueError("Factor risk sample, basis, annualization, or limits are invalid.")
    decision = parse_utc_timestamp(pd.Series([decision_at]), "decision_at").iloc[0]
    selected_weights = weights[weights["weight_type"].astype(str) == weight_type].copy()
    selected_weights["decision_at"] = parse_utc_timestamp(
        selected_weights["decision_at"], "decision_at"
    )
    selected_weights = selected_weights[selected_weights["decision_at"] == decision].copy()
    selected_weights["weight"] = pd.to_numeric(selected_weights["weight"], errors="coerce")
    if (
        selected_weights.empty
        or not np.isfinite(selected_weights["weight"]).all()
        or selected_weights["asset_id"].astype(str).duplicated().any()
    ):
        raise ValueError("Factor risk requires unique finite weights at the decision timestamp.")
    selected_weights = selected_weights[selected_weights["weight"] != 0].copy()
    if selected_weights.empty:
        raise ValueError("Factor risk requires at least one nonzero portfolio weight.")
    currencies = selected_weights["currency"].astype(str).unique()
    if len(currencies) != 1:
        raise ValueError("Factor risk weights must use one reporting currency.")
    currency = str(currencies[0])
    active_assets = sorted(selected_weights["asset_id"].astype(str))
    selected_exposures = exposures[
        (exposures["factor_model_id"].astype(str) == factor_model_id)
        & exposures["asset_id"].astype(str).isin(active_assets)
    ].copy()
    for column in ("as_of", "available_at"):
        selected_exposures[column] = parse_utc_timestamp(selected_exposures[column], column)
    selected_exposures = selected_exposures[
        (selected_exposures["as_of"] <= decision)
        & (selected_exposures["available_at"] <= decision)
    ].copy()
    if selected_exposures.empty:
        raise ValueError("No PIT factor exposure snapshot is available for factor risk.")
    exposure_as_of = pd.Timestamp(selected_exposures["as_of"].max())
    selected_exposures = selected_exposures[
        selected_exposures["as_of"] == exposure_as_of
    ].copy()
    selected_exposures["exposure"] = pd.to_numeric(
        selected_exposures["exposure"], errors="coerce"
    )
    if not np.isfinite(selected_exposures["exposure"]).all():
        raise ValueError("Factor risk exposures must be finite.")
    factor_ids = sorted(selected_exposures["factor_id"].astype(str).unique())
    exposure_matrix = selected_exposures.pivot(
        index="asset_id", columns="factor_id", values="exposure"
    ).reindex(index=active_assets, columns=factor_ids)
    if exposure_matrix.empty or exposure_matrix.isna().any().any():
        raise ValueError("PIT factor risk exposures must cover every active asset-factor pair.")
    unknown_limits = sorted(
        (set(factor_exposure_limits) | set(factor_component_volatility_limits))
        - set(factor_ids)
    )
    if unknown_limits:
        raise ValueError(f"Factor risk limits reference unknown factors: {unknown_limits}")
    selected_returns = factor_returns[
        factor_returns["factor_model_id"].astype(str) == factor_model_id
    ].copy()
    for column in ("return_start", "return_end", "available_at"):
        selected_returns[column] = parse_utc_timestamp(selected_returns[column], column)
    selected_returns = selected_returns[
        (selected_returns["return_end"] <= decision)
        & (selected_returns["available_at"] <= decision)
        & selected_returns["factor_id"].astype(str).isin(factor_ids)
    ].copy()
    if selected_returns.empty:
        raise ValueError("No PIT factor return history is available by decision_at.")
    if (
        selected_returns["return_type"].astype(str).ne("simple").any()
        or selected_returns["return_basis"].astype(str).ne(return_basis).any()
        or selected_returns["currency"].astype(str).ne(currency).any()
        or (selected_returns["return_end"] <= selected_returns["return_start"]).any()
    ):
        raise ValueError("Factor risk returns must be simple, aligned by basis/currency, and ordered.")
    selected_returns["return_value"] = pd.to_numeric(
        selected_returns["return_value"], errors="coerce"
    )
    if not np.isfinite(selected_returns["return_value"]).all():
        raise ValueError("Factor risk returns must be finite.")
    if selected_returns.duplicated(
        ["return_start", "return_end", "factor_id"], keep=False
    ).any():
        raise ValueError("Factor return history contains duplicate window-factor rows.")
    history = selected_returns.pivot(
        index=["return_start", "return_end"],
        columns="factor_id",
        values="return_value",
    ).reindex(columns=factor_ids)
    complete_history = history.dropna().sort_index(level="return_end").tail(lookback_periods)
    if len(complete_history) < minimum_observations:
        raise ValueError(
            "Complete PIT factor return observations are below minimum_observations."
        )
    windows = complete_history.index.to_frame(index=False).sort_values("return_start")
    if (windows["return_start"].iloc[1:].to_numpy() < windows["return_end"].iloc[:-1].to_numpy()).any():
        raise ValueError("Factor covariance return windows must not overlap.")
    covariance = complete_history.cov() * annualization
    matrix = covariance.to_numpy(dtype=float)
    if not np.isfinite(matrix).all():
        raise ValueError("Factor covariance matrix must be finite.")
    raw_condition_number = float(np.linalg.cond(matrix))
    condition_number = raw_condition_number if math.isfinite(raw_condition_number) else None
    weight_series = selected_weights.set_index("asset_id")["weight"].reindex(active_assets)
    portfolio_factor_exposures = exposure_matrix.mul(weight_series, axis=0).sum(axis=0)
    factor_vector = portfolio_factor_exposures.to_numpy(dtype=float)
    covariance_times_exposure = matrix @ factor_vector
    factor_variance = max(0.0, float(factor_vector @ covariance_times_exposure))
    factor_volatility = math.sqrt(factor_variance)
    marginal_volatility = (
        covariance_times_exposure / factor_volatility
        if factor_volatility > 0
        else np.zeros_like(factor_vector)
    )
    component_volatility = factor_vector * marginal_volatility
    unknown_specific = sorted(set(specific_risk_volatilities) - set(active_assets))
    if unknown_specific:
        raise ValueError(f"Specific-risk volatilities reference unknown assets: {unknown_specific}")
    specific_variance = sum(
        float(weight_series[asset]) ** 2 * float(specific_risk_volatilities.get(asset, 0.0)) ** 2
        for asset in active_assets
    )
    total_variance = factor_variance + specific_variance
    total_volatility = math.sqrt(total_variance)
    blockers: list[DiagnosticMessage] = []
    if factor_volatility > maximum_annualized_factor_volatility:
        blockers.append(
            DiagnosticMessage(
                code="factor_volatility_limit",
                message="Annualized portfolio factor volatility exceeds the configured limit.",
                severity="blocker",
                context={
                    "annualized_factor_volatility": factor_volatility,
                    "limit": maximum_annualized_factor_volatility,
                },
            )
        )
    if condition_number is None or condition_number > maximum_covariance_condition_number:
        blockers.append(
            DiagnosticMessage(
                code="factor_covariance_condition",
                message="Factor covariance condition number exceeds the configured limit.",
                severity="blocker",
                context={
                    "condition_number": condition_number,
                    "limit": maximum_covariance_condition_number,
                },
            )
        )
    if (
        maximum_annualized_total_volatility is not None
        and total_volatility > maximum_annualized_total_volatility
    ):
        blockers.append(
            DiagnosticMessage(
                code="factor_total_volatility_limit",
                message="Annualized total portfolio volatility exceeds the configured limit.",
                severity="blocker",
                context={
                    "annualized_total_volatility": total_volatility,
                    "limit": maximum_annualized_total_volatility,
                },
            )
        )
    details = []
    for index, factor_id in enumerate(factor_ids):
        exposure = float(factor_vector[index])
        component = float(component_volatility[index])
        detail = {
            "factor_id": factor_id,
            "portfolio_exposure": exposure,
            "marginal_volatility": float(marginal_volatility[index]),
            "component_volatility": component,
            "component_variance": float(factor_vector[index] * covariance_times_exposure[index]),
        }
        details.append(detail)
        exposure_limit = factor_exposure_limits.get(factor_id)
        if exposure_limit is not None and abs(exposure) > exposure_limit:
            blockers.append(
                DiagnosticMessage(
                    code="factor_risk_exposure_limit",
                    message=f"Factor {factor_id!r} exceeds its absolute exposure limit.",
                    severity="blocker",
                    context={**detail, "limit": exposure_limit},
                )
            )
        component_limit = factor_component_volatility_limits.get(factor_id)
        if component_limit is not None and abs(component) > component_limit:
            blockers.append(
                DiagnosticMessage(
                    code="factor_component_volatility_limit",
                    message=f"Factor {factor_id!r} exceeds its component-volatility limit.",
                    severity="blocker",
                    context={**detail, "limit": component_limit},
                )
            )
    return ArtifactEnvelope(
        artifact_type="factor_risk",
        run_id=run_id,
        producer=ProducerReference(name="factor-risk", version=__version__),
        parameters={
            "factor_model_id": factor_model_id,
            "decision_at": decision.isoformat(),
            "weight_type": weight_type,
            "return_basis": return_basis,
            "lookback_periods": lookback_periods,
            "minimum_observations": minimum_observations,
            "annualization": annualization,
            "maximum_annualized_factor_volatility": maximum_annualized_factor_volatility,
            "maximum_covariance_condition_number": maximum_covariance_condition_number,
            "factor_exposure_limits": factor_exposure_limits,
            "factor_component_volatility_limits": factor_component_volatility_limits,
            "specific_risk_volatilities": specific_risk_volatilities,
            "maximum_annualized_total_volatility": maximum_annualized_total_volatility,
        },
        summary={
            "asset_count": len(active_assets),
            "factor_count": len(factor_ids),
            "observation_count": len(complete_history),
            "incomplete_observation_count": len(history) - len(history.dropna()),
            "exposure_as_of": exposure_as_of.isoformat(),
            "annualized_factor_variance": factor_variance,
            "annualized_factor_volatility": factor_volatility,
            "annualized_specific_variance": specific_variance,
            "annualized_specific_volatility": math.sqrt(specific_variance),
            "annualized_total_variance": total_variance,
            "annualized_total_volatility": total_volatility,
            "covariance_condition_number": condition_number,
            "component_volatility_sum": float(component_volatility.sum()),
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            DiagnosticMessage(
                code="factor_risk_scope",
                message=(
                    "Historical factor covariance omits covariance shrinkage, regime "
                    "shifts, nonlinear exposures, liquidity, funding, estimation uncertainty, and "
                    "stress covariance. Specific risk is a diagonal per-asset variance model with "
                    "cross-sectional idiosyncratic correlation assumed zero."
                ),
                severity="warning",
            )
        ],
        details=details,
        provenance={
            "exposure_selection": "latest_complete_pit_snapshot_at_decision",
            "covariance_estimator": "sample_complete_nonoverlapping_factor_returns",
            "specific_risk_model": "diagonal_per_asset_variance",
            "live_order_submission": False,
        },
    ).finalize()


@register_diagnostic(
    "factor-attribution",
    "factor_attribution",
    required_table_types=(
        "portfolio_weights",
        "return_labels",
        "factor_exposures",
        "factor_returns",
    ),
    manifest_stage="risk",
    parameter_model=FactorAttributionParameters,
    description="Attribute realized portfolio return to PIT factor exposures and specific return.",
)
def factor_attribution_artifact(
    weights: pd.DataFrame,
    labels: pd.DataFrame,
    exposures: pd.DataFrame,
    factor_returns: pd.DataFrame,
    *,
    factor_model_id: str,
    decision_at: str,
    evaluated_at: str,
    label: str,
    weight_type: str,
    return_basis: str = "gross",
    factor_exposure_limits: dict[str, float] | None = None,
    gross_exposure_limit: float = 2.0,
    specific_contribution_limit: float = 0.05,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    factor_exposure_limits = factor_exposure_limits or {}
    if (
        return_basis not in {"gross", "excess"}
        or gross_exposure_limit <= 0
        or specific_contribution_limit < 0
        or any(limit <= 0 for limit in factor_exposure_limits.values())
    ):
        raise ValueError("Factor attribution basis or risk limits are invalid.")
    decision = parse_utc_timestamp(pd.Series([decision_at]), "decision_at").iloc[0]
    evaluated = parse_utc_timestamp(pd.Series([evaluated_at]), "evaluated_at").iloc[0]
    if evaluated < decision:
        raise ValueError("Factor attribution evaluated_at must not precede decision_at.")
    selected_weights = weights[
        (weights["weight_type"].astype(str) == weight_type)
    ].copy()
    selected_weights["decision_at"] = parse_utc_timestamp(
        selected_weights["decision_at"], "decision_at"
    )
    selected_weights = selected_weights[selected_weights["decision_at"] == decision]
    if selected_weights.empty:
        raise ValueError("No portfolio weights match the attribution decision and weight type.")
    selected_weights["weight"] = pd.to_numeric(selected_weights["weight"], errors="coerce")
    if not np.isfinite(selected_weights["weight"]).all():
        raise ValueError("Portfolio attribution weights must be finite.")
    if selected_weights["asset_id"].astype(str).duplicated().any():
        raise ValueError("Portfolio attribution weights must be unique by asset.")
    selected_weights = selected_weights[selected_weights["weight"] != 0].copy()
    if selected_weights.empty:
        raise ValueError("Factor attribution requires at least one nonzero portfolio weight.")
    currencies = selected_weights["currency"].astype(str).unique()
    if len(currencies) != 1:
        raise ValueError("Factor attribution requires one portfolio reporting currency.")
    currency = str(currencies[0])
    selected_labels = labels[labels["label"].astype(str) == label].copy()
    for column in ("decision_at", "execution_at", "return_start", "return_end"):
        selected_labels[column] = parse_utc_timestamp(selected_labels[column], column)
    selected_labels = selected_labels[
        (selected_labels["decision_at"] == decision)
        & selected_labels["asset_id"].astype(str).isin(
            selected_weights["asset_id"].astype(str)
        )
    ].copy()
    active_assets = set(selected_weights["asset_id"].astype(str))
    if set(selected_labels["asset_id"].astype(str)) != active_assets:
        raise ValueError("Every active portfolio asset requires one realized return label.")
    if (
        selected_labels["asset_id"].astype(str).duplicated().any()
        or selected_labels["return_start"].nunique() != 1
        or selected_labels["return_end"].nunique() != 1
        or selected_labels["return_type"].astype(str).nunique() != 1
        or selected_labels["return_type"].astype(str).iloc[0] != "simple"
        or selected_labels["return_basis"].astype(str).nunique() != 1
        or selected_labels["return_basis"].astype(str).iloc[0] != return_basis
        or selected_labels["currency"].astype(str).nunique() != 1
        or selected_labels["currency"].astype(str).iloc[0] != currency
    ):
        raise ValueError("Attribution labels must share one simple-return window, basis, and currency.")
    return_start = pd.Timestamp(selected_labels["return_start"].iloc[0])
    return_end = pd.Timestamp(selected_labels["return_end"].iloc[0])
    if return_end > evaluated:
        raise ValueError("Realized attribution labels are unavailable at evaluated_at.")
    selected_labels["return_value"] = pd.to_numeric(
        selected_labels["return_value"], errors="coerce"
    )
    if not np.isfinite(selected_labels["return_value"]).all():
        raise ValueError("Attribution label returns must be finite.")
    selected_factor_returns = factor_returns[
        factor_returns["factor_model_id"].astype(str) == factor_model_id
    ].copy()
    for column in ("return_start", "return_end", "available_at"):
        selected_factor_returns[column] = parse_utc_timestamp(
            selected_factor_returns[column], column
        )
    selected_factor_returns = selected_factor_returns[
        (selected_factor_returns["return_start"] == return_start)
        & (selected_factor_returns["return_end"] == return_end)
        & (selected_factor_returns["available_at"] <= evaluated)
    ].copy()
    if selected_factor_returns.empty:
        raise ValueError("No factor returns match the attribution model and realized window.")
    if (
        selected_factor_returns["factor_id"].astype(str).duplicated().any()
        or selected_factor_returns["return_type"].astype(str).nunique() != 1
        or selected_factor_returns["return_type"].astype(str).iloc[0] != "simple"
        or selected_factor_returns["return_basis"].astype(str).nunique() != 1
        or selected_factor_returns["return_basis"].astype(str).iloc[0] != return_basis
        or selected_factor_returns["currency"].astype(str).nunique() != 1
        or selected_factor_returns["currency"].astype(str).iloc[0] != currency
    ):
        raise ValueError("Factor returns must be unique and match label type, basis, and currency.")
    selected_factor_returns["return_value"] = pd.to_numeric(
        selected_factor_returns["return_value"], errors="coerce"
    )
    if not np.isfinite(selected_factor_returns["return_value"]).all():
        raise ValueError("Factor returns must be finite.")
    factor_ids = sorted(selected_factor_returns["factor_id"].astype(str))
    unknown_limits = sorted(set(factor_exposure_limits) - set(factor_ids))
    if unknown_limits:
        raise ValueError(f"Factor exposure limits reference unknown factors: {unknown_limits}")
    selected_exposures = exposures[
        (exposures["factor_model_id"].astype(str) == factor_model_id)
        & exposures["asset_id"].astype(str).isin(active_assets)
    ].copy()
    for column in ("as_of", "available_at"):
        selected_exposures[column] = parse_utc_timestamp(selected_exposures[column], column)
    selected_exposures = selected_exposures[
        (selected_exposures["as_of"] <= decision)
        & (selected_exposures["available_at"] <= decision)
    ]
    if selected_exposures.empty:
        raise ValueError("No PIT factor exposure snapshot is available at the decision timestamp.")
    exposure_as_of = selected_exposures["as_of"].max()
    selected_exposures = selected_exposures[
        selected_exposures["as_of"] == exposure_as_of
    ].copy()
    selected_exposures["exposure"] = pd.to_numeric(
        selected_exposures["exposure"], errors="coerce"
    )
    if not np.isfinite(selected_exposures["exposure"]).all():
        raise ValueError("Factor exposures must be finite.")
    exposure_matrix = selected_exposures.pivot(
        index="asset_id", columns="factor_id", values="exposure"
    ).reindex(index=sorted(active_assets), columns=factor_ids)
    if exposure_matrix.isna().any().any():
        raise ValueError("The PIT factor exposure snapshot must cover every asset-factor pair.")
    weight_series = selected_weights.set_index("asset_id")["weight"].reindex(
        exposure_matrix.index
    )
    realized_returns = selected_labels.set_index("asset_id")["return_value"].reindex(
        exposure_matrix.index
    )
    factor_return_series = selected_factor_returns.set_index("factor_id")[
        "return_value"
    ].reindex(factor_ids)
    portfolio_factor_exposures = exposure_matrix.mul(weight_series, axis=0).sum(axis=0)
    factor_contributions = portfolio_factor_exposures * factor_return_series
    predicted_asset_returns = exposure_matrix.dot(factor_return_series)
    specific_asset_returns = realized_returns - predicted_asset_returns
    realized_asset_contributions = weight_series * realized_returns
    specific_asset_contributions = weight_series * specific_asset_returns
    portfolio_return = float(realized_asset_contributions.sum())
    factor_return_contribution = float(factor_contributions.sum())
    specific_return_contribution = float(specific_asset_contributions.sum())
    if not math.isclose(
        portfolio_return,
        factor_return_contribution + specific_return_contribution,
        rel_tol=0,
        abs_tol=1e-12,
    ):
        raise ValueError("Factor attribution failed exact portfolio-return reconciliation.")
    gross_exposure = float(weight_series.abs().sum())
    blockers: list[DiagnosticMessage] = []
    if gross_exposure > gross_exposure_limit:
        blockers.append(
            DiagnosticMessage(
                code="gross_exposure_limit",
                message="Portfolio gross exposure exceeds the configured formal limit.",
                severity="blocker",
                context={"gross_exposure": gross_exposure, "limit": gross_exposure_limit},
            )
        )
    if abs(specific_return_contribution) > specific_contribution_limit:
        blockers.append(
            DiagnosticMessage(
                code="specific_contribution_limit",
                message="Absolute specific return contribution exceeds the configured limit.",
                severity="blocker",
                context={
                    "specific_return_contribution": specific_return_contribution,
                    "limit": specific_contribution_limit,
                },
            )
        )
    for factor_id, limit in factor_exposure_limits.items():
        exposure = float(portfolio_factor_exposures[factor_id])
        if abs(exposure) > limit:
            blockers.append(
                DiagnosticMessage(
                    code="factor_exposure_limit",
                    message=f"Factor {factor_id!r} exceeds its absolute exposure limit.",
                    severity="blocker",
                    context={"factor_id": factor_id, "exposure": exposure, "limit": limit},
                )
            )
    details = [
        {
            "detail_type": "factor",
            "factor_id": factor_id,
            "portfolio_exposure": float(portfolio_factor_exposures[factor_id]),
            "factor_return": float(factor_return_series[factor_id]),
            "return_contribution": float(factor_contributions[factor_id]),
        }
        for factor_id in factor_ids
    ] + [
        {
            "detail_type": "asset_specific",
            "asset_id": asset_id,
            "weight": float(weight_series[asset_id]),
            "realized_return": float(realized_returns[asset_id]),
            "predicted_factor_return": float(predicted_asset_returns[asset_id]),
            "specific_return": float(specific_asset_returns[asset_id]),
            "realized_contribution": float(realized_asset_contributions[asset_id]),
            "specific_contribution": float(specific_asset_contributions[asset_id]),
        }
        for asset_id in exposure_matrix.index
    ]
    return ArtifactEnvelope(
        artifact_type="factor_attribution",
        run_id=run_id,
        producer=ProducerReference(name="factor-attribution", version=__version__),
        parameters={
            "factor_model_id": factor_model_id,
            "decision_at": decision.isoformat(),
            "evaluated_at": evaluated.isoformat(),
            "label": label,
            "weight_type": weight_type,
            "return_basis": return_basis,
            "factor_exposure_limits": factor_exposure_limits,
            "gross_exposure_limit": gross_exposure_limit,
            "specific_contribution_limit": specific_contribution_limit,
        },
        summary={
            "currency": currency,
            "return_start": return_start.isoformat(),
            "return_end": return_end.isoformat(),
            "exposure_as_of": pd.Timestamp(exposure_as_of).isoformat(),
            "asset_count": len(active_assets),
            "factor_count": len(factor_ids),
            "gross_exposure": gross_exposure,
            "portfolio_return": portfolio_return,
            "factor_return_contribution": factor_return_contribution,
            "specific_return_contribution": specific_return_contribution,
            "reconciliation_error": portfolio_return
            - factor_return_contribution
            - specific_return_contribution,
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            DiagnosticMessage(
                code="factor_attribution_scope",
                message=(
                    "Linear realized-return attribution omits time-varying intraperiod exposures, "
                    "factor covariance/risk decomposition, nonlinear payoffs, transaction effects, "
                    "estimation uncertainty, and causal interpretation."
                ),
                severity="warning",
            )
        ],
        details=details,
        provenance={
            "exposure_timing": "latest_complete_snapshot_available_at_decision",
            "return_attribution": "linear_factor_plus_specific_exact_reconciliation",
            "live_order_submission": False,
        },
    ).finalize()
