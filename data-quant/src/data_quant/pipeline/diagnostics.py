"""Explicit native diagnostic adapters for Manifest pipeline stages."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.contracts.manifest import DiagnosticSpec
from data_quant.diagnostics.asset_classes import (
    crypto_cross_margin_stress_artifact,
    crypto_margin_stress_artifact,
    fixed_income_curve_stress_artifact,
    fixed_income_price_reconciliation_artifact,
    fixed_income_risk_artifact,
    futures_roll_artifact,
    futures_roll_execution_artifact,
    fx_forward_check_artifact,
    fx_rollover_artifact,
    option_hedge_replay_artifact,
    option_surface_artifact,
    option_surface_smooth_artifact,
)
from data_quant.diagnostics.execution import execution_replay_artifact, rebalance_replay_artifact
from data_quant.diagnostics.factor import factor_ic_artifact, fama_macbeth_artifact
from data_quant.diagnostics.governance import source_rule_freshness_artifact
from data_quant.diagnostics.portfolio import (
    portfolio_backtest_artifact,
    portfolio_eligibility_artifact,
    short_borrow_capacity_artifact,
)
from data_quant.diagnostics.risk import (
    covariance_risk_artifact,
    credit_migration_stress_artifact,
    factor_attribution_artifact,
    factor_risk_artifact,
    portfolio_stress_artifact,
)
from data_quant.diagnostics.validation import (
    corporate_action_adjustment_artifact,
    purged_walk_forward_artifact,
)
from data_quant.io import CanonicalTable
from data_quant.monitoring import (
    dependency_health_artifact,
    drift_artifact,
    model_calibration_artifact,
    service_health_artifact,
    signal_health_artifact,
)
from data_quant.registry import registry

ManifestExecutor = Callable[[DiagnosticSpec, dict[str, CanonicalTable], str], ArtifactEnvelope]


def _table(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    table_type: str,
) -> CanonicalTable:
    matches = [
        tables[source_id]
        for source_id in spec.input_sources
        if source_id in tables and tables[source_id].contract.table_type == table_type
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Diagnostic {spec.diagnostic_id!r} requires exactly one {table_type!r} input; "
            f"found {len(matches)}."
        )
    return matches[0]


def _parameters(spec: DiagnosticSpec) -> dict[str, Any]:
    return dict(spec.parameters)


def _one_value(frame: pd.DataFrame, column: str, requested: object, diagnostic_id: str) -> str:
    values = sorted(str(value) for value in frame[column].dropna().unique())
    if requested is None:
        if len(values) != 1:
            raise ValueError(
                f"Diagnostic {diagnostic_id!r} must select one {column}; available values: {values}"
            )
        return values[0]
    selected = str(requested)
    if selected not in values:
        raise ValueError(
            f"Diagnostic {diagnostic_id!r} requested unknown {column} {selected!r}; "
            f"available values: {values}"
        )
    return selected


def _attach_manifest_provenance(
    artifact: ArtifactEnvelope,
    spec: DiagnosticSpec,
) -> ArtifactEnvelope:
    artifact.provenance = {
        **artifact.provenance,
        "manifest_diagnostic_id": spec.diagnostic_id,
        "manifest_stage": spec.stage,
        "input_sources": list(spec.input_sources),
    }
    artifact.artifact_id = None
    artifact.content_digest = None
    return artifact.finalize()


def _aligned_factor_returns(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
) -> tuple[pd.DataFrame, str, str]:
    parameters = _parameters(spec)
    factors = _table(spec, tables, "factor_panel").frame.copy()
    labels = _table(spec, tables, "return_labels").frame.copy()
    signal = _one_value(factors, "signal", parameters.get("signal"), spec.diagnostic_id)
    label = _one_value(labels, "label", parameters.get("label"), spec.diagnostic_id)
    factors = factors[factors["signal"].astype(str) == signal]
    labels = labels[labels["label"].astype(str) == label]
    if (factors["available_at"] > factors["as_of"]).any():
        raise ValueError(
            f"{spec.diagnostic_id} input contains factor values unavailable at the decision timestamp."
        )
    if (labels["execution_at"] < labels["decision_at"]).any():
        raise ValueError(f"{spec.diagnostic_id} return labels execute before the decision time.")
    if (labels["return_start"] < labels["execution_at"]).any():
        raise ValueError(f"{spec.diagnostic_id} return labels begin before execution.")
    if (labels["return_end"] <= labels["return_start"]).any():
        raise ValueError(f"{spec.diagnostic_id} return labels must end after they start.")
    merged = factors.merge(
        labels[["decision_at", "asset_id", "return_value"]],
        left_on=["as_of", "asset_id"],
        right_on=["decision_at", "asset_id"],
        how="left",
        validate="one_to_one",
    )
    if merged["return_value"].isna().any():
        raise ValueError(f"{spec.diagnostic_id} has signals without aligned return labels.")
    return merged, signal, label


def _factor_ic(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    if spec.stage != "research":
        raise ValueError("factor-ic must run in the research stage.")
    parameters = _parameters(spec)
    merged, signal, label = _aligned_factor_returns(spec, tables)
    min_assets = int(parameters.get("min_assets", 5))
    artifact = factor_ic_artifact(
        merged,
        date_col="as_of",
        factor_col="value",
        forward_return_col="return_value",
        min_assets=min_assets,
        run_id=run_id,
    )
    artifact.parameters = {
        **artifact.parameters,
        "signal": signal,
        "label": label,
    }
    return _attach_manifest_provenance(artifact, spec)


def _fama_macbeth(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    if spec.stage != "research":
        raise ValueError("fama-macbeth must run in the research stage.")
    parameters = _parameters(spec)
    factors = _table(spec, tables, "factor_panel").frame.copy()
    labels = _table(spec, tables, "return_labels").frame.copy()
    label = _one_value(labels, "label", parameters.get("label"), spec.diagnostic_id)
    labels = labels[labels["label"].astype(str) == label]
    features = parameters.get("features")
    if not features:
        features = sorted(factors["signal"].astype(str).unique())
    if len(features) != len(set(features)):
        raise ValueError("fama-macbeth features must be unique.")
    for column in ("available_at", "as_of"):
        factors[column] = pd.to_datetime(factors[column], utc=True)
    for column in ("decision_at", "execution_at", "return_start", "return_end"):
        labels[column] = pd.to_datetime(labels[column], utc=True)
    if (factors["available_at"] > factors["as_of"]).any():
        raise ValueError("fama-macbeth input contains factor values unavailable at the decision timestamp.")
    if (labels["execution_at"] < labels["decision_at"]).any():
        raise ValueError("fama-macbeth return labels execute before the decision time.")

    pivoted = factors.pivot_table(
        index=["as_of", "asset_id"], columns="signal", values="value"
    ).reset_index()
    missing = [f for f in features if f not in pivoted.columns]
    if missing:
        raise ValueError(f"fama-macbeth features missing from factor_panel: {missing}")
    merged = labels[["decision_at", "asset_id", "return_value"]].merge(
        pivoted, left_on=["decision_at", "asset_id"], right_on=["as_of", "asset_id"], how="left"
    )
    if merged["return_value"].isna().any():
        raise ValueError("fama-macbeth has signals without aligned return labels.")
    artifact = fama_macbeth_artifact(
        merged,
        date_col="decision_at",
        return_col="return_value",
        feature_cols=features,
        min_assets=int(parameters.get("min_assets", 5)),
        intercept=bool(parameters.get("intercept", True)),
        annualization=int(parameters.get("annualization", 12)),
        run_id=run_id,
    )
    artifact.parameters = {**artifact.parameters, "label": label}
    return _attach_manifest_provenance(artifact, spec)


def _corporate_action_adjustment(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = corporate_action_adjustment_artifact(
        _table(spec, tables, "market_bars").frame,
        _table(spec, tables, "corporate_actions").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _purged_walk_forward(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    if spec.stage != "validation":
        raise ValueError("purged-walk-forward must run in the validation stage.")
    parameters = _parameters(spec)
    labels = _table(spec, tables, "return_labels").frame.copy()
    label = _one_value(labels, "label", parameters.get("label"), spec.diagnostic_id)
    labels = labels[labels["label"].astype(str) == label]
    artifact = purged_walk_forward_artifact(
        labels,
        train_periods=int(parameters["train_periods"]),
        test_periods=int(parameters["test_periods"]),
        step_periods=(
            int(parameters["step_periods"]) if parameters.get("step_periods") is not None else None
        ),
        embargo=str(parameters.get("embargo", "0s")),
        expanding=bool(parameters.get("expanding", False)),
        run_id=run_id,
    )
    artifact.parameters = {**artifact.parameters, "label": label}
    return _attach_manifest_provenance(artifact, spec)


def _portfolio_backtest(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    if spec.stage != "portfolio":
        raise ValueError("portfolio-backtest must run in the portfolio stage.")
    parameters = _parameters(spec)
    weights = _table(spec, tables, "portfolio_weights").frame.copy()
    labels = _table(spec, tables, "return_labels").frame.copy()
    weight_type = _one_value(
        weights,
        "weight_type",
        parameters.get("weight_type"),
        spec.diagnostic_id,
    )
    label = _one_value(labels, "label", parameters.get("label"), spec.diagnostic_id)
    weights = weights[weights["weight_type"].astype(str) == weight_type]
    labels = labels[labels["label"].astype(str) == label]
    curve_matches = [
        tables[source_id]
        for source_id in spec.input_sources
        if source_id in tables and tables[source_id].contract.table_type == "financing_curves"
    ]
    if len(curve_matches) > 1:
        raise ValueError("portfolio-backtest accepts at most one financing_curves input.")
    financing_curves = curve_matches[0].frame.copy() if curve_matches else None
    artifact = portfolio_backtest_artifact(
        weights,
        labels,
        cost_bps_per_one_way_turnover=float(
            parameters.get("cost_bps_per_one_way_turnover", 0.0)
        ),
        annualization=int(parameters.get("annualization", 252)),
        risk_free_annual=float(parameters.get("risk_free_annual", 0.0)),
        cash_rate_annual=float(parameters.get("cash_rate_annual", 0.0)),
        financing_rate_annual=float(parameters.get("financing_rate_annual", 0.0)),
        short_borrow_rate_annual=float(parameters.get("short_borrow_rate_annual", 0.0)),
        secured_financing_spread_bps=float(parameters.get("secured_financing_spread_bps", 0.0)),
        collateralization_ratio=float(parameters.get("collateralization_ratio", 0.0)),
        financing_convexity_bps=float(parameters.get("financing_convexity_bps", 0.0)),
        financing_curves=financing_curves,
        financing_curve_id=(
            str(parameters["financing_curve_id"])
            if parameters.get("financing_curve_id") is not None
            else None
        ),
        initial_nav=float(parameters.get("initial_nav", 1.0)),
        run_id=run_id,
    )
    artifact.parameters = {
        **artifact.parameters,
        "weight_type": weight_type,
        "label": label,
    }
    return _attach_manifest_provenance(artifact, spec)


def _portfolio_eligibility(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    parameters = _parameters(spec)
    weights = _table(spec, tables, "portfolio_weights").frame.copy()
    labels = _table(spec, tables, "return_labels").frame.copy()
    weight_type = _one_value(
        weights,
        "weight_type",
        parameters.get("weight_type"),
        spec.diagnostic_id,
    )
    label = _one_value(labels, "label", parameters.get("label"), spec.diagnostic_id)
    weights = weights[weights["weight_type"].astype(str) == weight_type]
    labels = labels[labels["label"].astype(str) == label]
    artifact = portfolio_eligibility_artifact(
        weights,
        labels,
        _table(spec, tables, "universe_membership").frame,
        _table(spec, tables, "corporate_actions").frame,
        _table(spec, tables, "borrow_availability").frame,
        universe_id=str(parameters["universe_id"]),
        run_id=run_id,
    )
    artifact.parameters = {
        **artifact.parameters,
        "weight_type": weight_type,
        "label": label,
    }
    return _attach_manifest_provenance(artifact, spec)


def _short_borrow_capacity(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    parameters = _parameters(spec)
    weights = _table(spec, tables, "portfolio_weights").frame.copy()
    weight_type = _one_value(
        weights,
        "weight_type",
        parameters.get("weight_type"),
        spec.diagnostic_id,
    )
    weights = weights[weights["weight_type"].astype(str) == weight_type]
    artifact = short_borrow_capacity_artifact(
        weights,
        _table(spec, tables, "market_quotes").frame,
        _table(spec, tables, "borrow_locates").frame,
        portfolio_value=float(parameters["portfolio_value"]),
        holding_period=str(parameters.get("holding_period", "1D")),
        max_quote_age=str(parameters.get("max_quote_age", "1D")),
        minimum_borrow_buffer=float(parameters.get("minimum_borrow_buffer", 1.0)),
        maximum_blended_fee_annual=float(
            parameters.get("maximum_blended_fee_annual", 1.0)
        ),
        venue=str(parameters["venue"]) if parameters.get("venue") is not None else None,
        run_id=run_id,
    )
    artifact.parameters = {**artifact.parameters, "weight_type": weight_type}
    return _attach_manifest_provenance(artifact, spec)


def _selected_risk_inputs(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
) -> tuple[pd.DataFrame, pd.Series, dict[str, str]]:
    parameters = _parameters(spec)
    labels = _table(spec, tables, "return_labels").frame.copy()
    weights = _table(spec, tables, "portfolio_weights").frame.copy()
    label = _one_value(labels, "label", parameters.get("label"), spec.diagnostic_id)
    return_basis = _one_value(
        labels,
        "return_basis",
        parameters.get("return_basis"),
        spec.diagnostic_id,
    )
    weight_type = _one_value(
        weights,
        "weight_type",
        parameters.get("weight_type"),
        spec.diagnostic_id,
    )
    labels = labels[
        (labels["label"].astype(str) == label)
        & (labels["return_basis"].astype(str) == return_basis)
    ]
    weights = weights[weights["weight_type"].astype(str) == weight_type]
    label_currency = _one_value(labels, "currency", None, spec.diagnostic_id)
    weight_currency = _one_value(weights, "currency", None, spec.diagnostic_id)
    if label_currency != weight_currency:
        raise ValueError(f"{spec.diagnostic_id} weights and returns must use the same currency.")
    latest_decision = weights["decision_at"].max()
    latest_weights = weights[weights["decision_at"] == latest_decision].set_index("asset_id")["weight"]
    returns = labels.pivot(index="decision_at", columns="asset_id", values="return_value")
    metadata = {
        "label": label,
        "return_basis": return_basis,
        "weight_type": weight_type,
        "currency": weight_currency,
        "weight_decision_at": pd.Timestamp(latest_decision).isoformat(),
    }
    return returns, latest_weights, metadata


def _covariance_risk(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    if spec.stage != "risk":
        raise ValueError("covariance-risk must run in the risk stage.")
    parameters = _parameters(spec)
    returns, latest_weights, metadata = _selected_risk_inputs(spec, tables)
    artifact = covariance_risk_artifact(
        returns,
        latest_weights,
        estimator=str(parameters.get("estimator", "sample")),
        annualization=float(parameters.get("annualization", 252.0)),
        decay=float(parameters.get("decay", 0.94)),
        run_id=run_id,
    )
    artifact.parameters = {**artifact.parameters, **metadata}
    return _attach_manifest_provenance(artifact, spec)


def _credit_migration_stress(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = credit_migration_stress_artifact(
        _table(spec, tables, "credit_exposures").frame,
        _table(spec, tables, "credit_transition_matrix").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _factor_risk(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = factor_risk_artifact(
        _table(spec, tables, "portfolio_weights").frame,
        _table(spec, tables, "factor_exposures").frame,
        _table(spec, tables, "factor_returns").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _factor_attribution(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = factor_attribution_artifact(
        _table(spec, tables, "portfolio_weights").frame,
        _table(spec, tables, "return_labels").frame,
        _table(spec, tables, "factor_exposures").frame,
        _table(spec, tables, "factor_returns").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _portfolio_stress(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    parameters = _parameters(spec)
    returns, latest_weights, metadata = _selected_risk_inputs(spec, tables)
    artifact = portfolio_stress_artifact(
        returns,
        latest_weights,
        scenarios=parameters["scenarios"],
        confidence=float(parameters.get("confidence", 0.95)),
        loss_limit=float(parameters.get("loss_limit", 0.10)),
        run_id=run_id,
    )
    artifact.parameters = {**artifact.parameters, **metadata}
    return _attach_manifest_provenance(artifact, spec)


def _execution_replay(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    if spec.stage != "execution":
        raise ValueError("execution-replay must run in the execution stage.")
    parameters = _parameters(spec)
    artifact = execution_replay_artifact(
        _table(spec, tables, "orders").frame.copy(),
        _table(spec, tables, "market_quotes").frame.copy(),
        max_participation=float(parameters.get("max_participation", 0.10)),
        commission_bps=float(parameters.get("commission_bps", 0.0)),
        slippage_bps=float(parameters.get("slippage_bps", 0.0)),
        impact_model=str(parameters.get("impact_model", "linear")),
        impact_coefficient_bps=float(parameters.get("impact_coefficient_bps", 0.0)),
        permanent_impact_coefficient_bps=float(
            parameters.get("permanent_impact_coefficient_bps", 0.0)
        ),
        hidden_liquidity_fraction=float(parameters.get("hidden_liquidity_fraction", 0.0)),
        hidden_spread_bps=float(parameters.get("hidden_spread_bps", 0.0)),
        initial_cash=float(parameters.get("initial_cash", 1_000_000.0)),
        run_id=run_id,
    )
    return _attach_manifest_provenance(artifact, spec)


def _futures_roll_execution(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    limit_matches = [
        tables[source_id]
        for source_id in spec.input_sources
        if source_id in tables
        and tables[source_id].contract.table_type == "futures_position_limits"
    ]
    if len(limit_matches) > 1:
        raise ValueError("futures-roll-execution accepts at most one position-limit input.")
    artifact = futures_roll_execution_artifact(
        _table(spec, tables, "futures_contracts").frame,
        _table(spec, tables, "market_bars").frame,
        _table(spec, tables, "market_quotes").frame,
        _table(spec, tables, "futures_margin_terms").frame,
        position_limits=limit_matches[0].frame if limit_matches else None,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _futures_roll(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = futures_roll_artifact(
        _table(spec, tables, "futures_contracts").frame,
        _table(spec, tables, "market_bars").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _option_surface(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = option_surface_artifact(
        _table(spec, tables, "option_contracts").frame,
        _table(spec, tables, "market_quotes").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _option_surface_smooth(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = option_surface_smooth_artifact(
        _table(spec, tables, "option_contracts").frame,
        _table(spec, tables, "market_quotes").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _option_hedge_replay(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    event_matches = [
        tables[source_id]
        for source_id in spec.input_sources
        if source_id in tables
        and tables[source_id].contract.table_type == "option_exercise_events"
    ]
    if len(event_matches) > 1:
        raise ValueError("option-hedge-replay accepts at most one exercise-event input.")
    artifact = option_hedge_replay_artifact(
        _table(spec, tables, "option_contracts").frame,
        _table(spec, tables, "market_quotes").frame,
        _table(spec, tables, "market_bars").frame,
        exercise_events=event_matches[0].frame if event_matches else None,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _fixed_income_price_reconciliation(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    rate_fixing_matches = [
        tables[source_id]
        for source_id in spec.input_sources
        if source_id in tables
        and tables[source_id].contract.table_type == "fixed_income_rate_fixings"
    ]
    if len(rate_fixing_matches) > 1:
        raise ValueError("fixed-income-price-reconciliation accepts at most one rate-fixing input.")
    artifact = fixed_income_price_reconciliation_artifact(
        _table(spec, tables, "fixed_income_instruments").frame,
        _table(spec, tables, "fixed_income_cashflows").frame,
        _table(spec, tables, "fixed_income_price_quotes").frame,
        rate_fixings=rate_fixing_matches[0].frame if rate_fixing_matches else None,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _fixed_income_curve_stress(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    curve_nodes = _table(spec, tables, "yield_curve_nodes").frame
    spread_matches = [
        tables[source_id]
        for source_id in spec.input_sources
        if source_id in tables
        and tables[source_id].contract.table_type == "fixed_income_spread_nodes"
    ]
    if len(spread_matches) > 1:
        raise ValueError("fixed-income-curve-stress accepts at most one spread-node input.")
    artifact = fixed_income_curve_stress_artifact(
        _table(spec, tables, "fixed_income_instruments").frame,
        curve_nodes,
        _table(spec, tables, "calendar_sessions").frame,
        spread_nodes=spread_matches[0].frame if spread_matches else None,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _fixed_income_risk(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = fixed_income_risk_artifact(
        _table(spec, tables, "fixed_income_instruments").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _fx_forward_check(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    replacement = tables.get(
        next(
            (
                source_id
                for source_id in spec.input_sources
                if source_id in tables
                and tables[source_id].contract.table_type == "fx_replacement_quotes"
            ),
            "",
        )
    )
    artifact = fx_forward_check_artifact(
        _table(spec, tables, "fx_quotes").frame,
        _table(spec, tables, "fx_forward_quotes").frame,
        _table(spec, tables, "calendar_sessions").frame,
        replacement_quotes=replacement.frame if replacement is not None else None,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _fx_rollover(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = fx_rollover_artifact(
        _table(spec, tables, "fx_quotes").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _crypto_cross_margin_stress(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = crypto_cross_margin_stress_artifact(
        _table(spec, tables, "crypto_instruments").frame,
        _table(spec, tables, "crypto_positions").frame,
        _table(spec, tables, "market_quotes").frame,
        _table(spec, tables, "crypto_margin_tiers").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _crypto_margin_stress(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = crypto_margin_stress_artifact(
        _table(spec, tables, "crypto_instruments").frame,
        _table(spec, tables, "market_quotes").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _model_calibration(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = model_calibration_artifact(
        _table(spec, tables, "model_predictions").frame,
        _table(spec, tables, "return_labels").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _source_rule_freshness(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    approval_matches = [
        tables[source_id]
        for source_id in spec.input_sources
        if source_id in tables
        and tables[source_id].contract.table_type == "source_change_approvals"
    ]
    if len(approval_matches) > 1:
        raise ValueError("source-rule-freshness accepts at most one approval input.")
    artifact = source_rule_freshness_artifact(
        _table(spec, tables, "source_cards").frame,
        approvals=approval_matches[0].frame if approval_matches else None,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _service_health(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = service_health_artifact(
        _table(spec, tables, "service_health_windows").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _dependency_health(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    artifact = dependency_health_artifact(
        _table(spec, tables, "synthetic_probes").frame,
        _table(spec, tables, "service_dependencies").frame,
        run_id=run_id,
        **_parameters(spec),
    )
    return _attach_manifest_provenance(artifact, spec)


def _signal_health(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    parameters = _parameters(spec)
    merged, signal, label = _aligned_factor_returns(spec, tables)
    artifact = signal_health_artifact(
        merged,
        evaluated_at=str(parameters["evaluated_at"]),
        max_signal_age=str(parameters.get("max_signal_age", "2D")),
        min_assets=int(parameters.get("min_assets", 5)),
        recent_periods=int(parameters.get("recent_periods", 3)),
        min_baseline_periods=int(parameters.get("min_baseline_periods", 5)),
        min_recent_rank_ic=float(parameters.get("min_recent_rank_ic", 0.0)),
        max_rank_ic_degradation=float(parameters.get("max_rank_ic_degradation", 0.10)),
        min_latest_std=float(parameters.get("min_latest_std", 1e-12)),
        run_id=run_id,
    )
    artifact.parameters = {**artifact.parameters, "signal": signal, "label": label}
    return _attach_manifest_provenance(artifact, spec)


def _rebalance_replay(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    parameters = _parameters(spec)
    lot_matches = [
        tables[source_id]
        for source_id in spec.input_sources
        if source_id in tables and tables[source_id].contract.table_type == "tax_lots"
    ]
    if len(lot_matches) > 1:
        raise ValueError("rebalance-replay accepts at most one tax-lot input.")
    artifact = rebalance_replay_artifact(
        _table(spec, tables, "portfolio_weights").frame.copy(),
        _table(spec, tables, "market_quotes").frame.copy(),
        tax_lots=lot_matches[0].frame if lot_matches else None,
        current_weight_type=str(parameters.get("current_weight_type", "current")),
        target_weight_type=str(parameters.get("target_weight_type", "target")),
        portfolio_value=float(parameters["portfolio_value"]),
        min_trade_notional=float(parameters.get("min_trade_notional", 0.0)),
        lot_size=float(parameters.get("lot_size", 1.0)),
        time_in_force=str(parameters.get("time_in_force", "gtc")),
        net_across_decisions=bool(parameters.get("net_across_decisions", False)),
        max_participation=float(parameters.get("max_participation", 0.10)),
        commission_bps=float(parameters.get("commission_bps", 0.0)),
        slippage_bps=float(parameters.get("slippage_bps", 0.0)),
        run_id=run_id,
    )
    return _attach_manifest_provenance(artifact, spec)


def _feature_drift(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    if spec.stage != "monitoring":
        raise ValueError("feature-drift must run in the monitoring stage.")
    parameters = _parameters(spec)
    reference_id = str(parameters["reference_source"])
    current_id = str(parameters["current_source"])
    if reference_id == current_id or {reference_id, current_id} != set(spec.input_sources):
        raise ValueError("feature-drift reference/current sources must match two distinct input_sources.")
    reference = tables[reference_id]
    current = tables[current_id]
    if reference.contract.table_type != current.contract.table_type:
        raise ValueError("feature-drift inputs must use the same canonical table type.")
    columns = parameters["columns"]
    artifact = drift_artifact(
        reference.frame,
        current.frame,
        columns=columns,
        bins=int(parameters.get("bins", 10)),
        warning_threshold=float(parameters.get("warning_threshold", 0.10)),
        blocker_threshold=float(parameters.get("blocker_threshold", 0.25)),
        run_id=run_id,
    )
    return _attach_manifest_provenance(artifact, spec)


EXECUTORS: dict[str, ManifestExecutor] = {
    "corporate-action-adjustment": _corporate_action_adjustment,
    "covariance-risk": _covariance_risk,
    "credit-migration-stress": _credit_migration_stress,
    "crypto-cross-margin-stress": _crypto_cross_margin_stress,
    "crypto-margin-stress": _crypto_margin_stress,
    "dependency-health": _dependency_health,
    "execution-replay": _execution_replay,
    "factor-ic": _factor_ic,
    "fama-macbeth": _fama_macbeth,
    "factor-attribution": _factor_attribution,
    "factor-risk": _factor_risk,
    "feature-drift": _feature_drift,
    "fixed-income-curve-stress": _fixed_income_curve_stress,
    "fixed-income-price-reconciliation": _fixed_income_price_reconciliation,
    "fixed-income-shock": _fixed_income_risk,
    "futures-roll": _futures_roll,
    "futures-roll-execution": _futures_roll_execution,
    "fx-forward-check": _fx_forward_check,
    "fx-rollover": _fx_rollover,
    "model-calibration": _model_calibration,
    "option-hedge-replay": _option_hedge_replay,
    "option-surface-check": _option_surface,
    "option-surface-smooth": _option_surface_smooth,
    "portfolio-backtest": _portfolio_backtest,
    "portfolio-eligibility": _portfolio_eligibility,
    "portfolio-stress": _portfolio_stress,
    "purged-walk-forward": _purged_walk_forward,
    "rebalance-replay": _rebalance_replay,
    "service-health": _service_health,
    "short-borrow-capacity": _short_borrow_capacity,
    "signal-health": _signal_health,
    "source-rule-freshness": _source_rule_freshness,
}


def validate_diagnostic_spec(spec: DiagnosticSpec) -> DiagnosticSpec:
    if spec.diagnostic_id not in EXECUTORS:
        known = ", ".join(sorted(EXECUTORS))
        raise ValueError(
            f"No Manifest executor for diagnostic {spec.diagnostic_id!r}; known: {known}"
        )
    definition = registry.get(spec.diagnostic_id)
    if definition.manifest_stage != spec.stage:
        raise ValueError(
            f"Diagnostic {spec.diagnostic_id!r} belongs to stage "
            f"{definition.manifest_stage!r}, not {spec.stage!r}."
        )
    if definition.parameter_model is None:
        raise ValueError(f"Diagnostic {spec.diagnostic_id!r} has no Manifest parameter contract.")
    parameters = definition.parameter_model.model_validate(spec.parameters).model_dump(exclude_none=True)
    return spec.model_copy(update={"parameters": parameters})


def validate_diagnostic_specs(specs: list[DiagnosticSpec]) -> list[DiagnosticSpec]:
    return [validate_diagnostic_spec(spec) for spec in specs]


def execute_diagnostic(
    spec: DiagnosticSpec,
    tables: dict[str, CanonicalTable],
    run_id: str,
) -> ArtifactEnvelope:
    validated = validate_diagnostic_spec(spec)
    return EXECUTORS[validated.diagnostic_id](validated, tables, run_id)
