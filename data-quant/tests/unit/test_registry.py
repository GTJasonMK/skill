from __future__ import annotations

from data_quant import diagnostics as _diagnostics  # noqa: F401
from data_quant.registry import registry


def test_data_contract_diagnostic_is_registered() -> None:
    definition = registry.get("data-contract")
    assert definition.artifact_type == "data_contract"
    assert definition.manifest_stage == "data"
    assert "canonical table" in definition.description


def test_manifest_diagnostics_publish_parameter_schemas() -> None:
    expected_stages = {
        "factor-attribution": "risk",
        "factor-ic": "research",
        "factor-risk": "risk",
        "purged-walk-forward": "validation",
        "portfolio-backtest": "portfolio",
        "execution-replay": "execution",
        "corporate-action-adjustment": "validation",
        "covariance-risk": "risk",
        "credit-migration-stress": "risk",
        "dependency-health": "monitoring",
        "feature-drift": "monitoring",
        "futures-roll": "research",
        "futures-roll-execution": "execution",
        "option-hedge-replay": "risk",
        "option-surface-check": "risk",
        "option-surface-smooth": "risk",
        "fixed-income-curve-stress": "risk",
        "fixed-income-price-reconciliation": "validation",
        "fixed-income-shock": "risk",
        "fx-forward-check": "research",
        "fx-rollover": "research",
        "model-calibration": "monitoring",
        "crypto-cross-margin-stress": "risk",
        "crypto-margin-stress": "risk",
        "portfolio-eligibility": "portfolio",
        "portfolio-stress": "risk",
        "rebalance-replay": "execution",
        "service-health": "monitoring",
        "source-rule-freshness": "governance",
        "short-borrow-capacity": "portfolio",
        "signal-health": "monitoring",
    }
    for diagnostic_id, stage in expected_stages.items():
        definition = registry.get(diagnostic_id)
        assert definition.manifest_stage == stage
        assert definition.parameter_schema is not None
        assert definition.parameter_schema["additionalProperties"] is False
