from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(tmp_path: Path, *, degraded: bool, crash: bool) -> Path:
    factor_rows = []
    label_rows = []
    for period in range(8):
        decision = pd.Timestamp("2024-01-01T09:00:00Z") + pd.Timedelta(days=period)
        for asset_number in range(5):
            asset_id = f"asset-{asset_number}"
            value = float(asset_number)
            return_value = (asset_number - 2) * 0.001
            if degraded and period >= 5:
                return_value *= -1
            factor_rows.append(
                {
                    "as_of": decision,
                    "asset_id": asset_id,
                    "signal": "model-score",
                    "value": value,
                    "available_at": decision - pd.Timedelta(minutes=1),
                }
            )
            label_rows.append(
                {
                    "decision_at": decision,
                    "execution_at": decision + pd.Timedelta(minutes=1),
                    "return_start": decision + pd.Timedelta(minutes=1),
                    "return_end": decision + pd.Timedelta(hours=1),
                    "asset_id": asset_id,
                    "label": "intraday",
                    "return_value": return_value,
                    "return_type": "simple",
                    "return_basis": "gross",
                    "corporate_action_policy": "total_return",
                    "currency": "USD",
                }
            )
    factors = tmp_path / "factors.csv"
    labels = tmp_path / "labels.csv"
    weights = tmp_path / "weights.csv"
    pd.DataFrame(factor_rows).to_csv(factors, index=False)
    pd.DataFrame(label_rows).to_csv(labels, index=False)
    pd.DataFrame(
        {
            "decision_at": ["2024-01-09T09:00:00Z"] * 5,
            "asset_id": [f"asset-{number}" for number in range(5)],
            "weight": [0.2] * 5,
            "weight_type": ["target"] * 5,
            "currency": ["USD"] * 5,
        }
    ).to_csv(weights, index=False)
    shock = -0.30 if crash else -0.02
    scenarios = [
        {
            "name": "cross-asset-shock",
            "asset_shocks": {f"asset-{number}": shock for number in range(5)},
        }
    ]
    manifest = {
        "project": {"name": "risk-monitoring", "asset_class": "mixed"},
        "data_sources": [
            {"id": "factors", "uri": str(factors), "format": "csv", "table_type": "factor_panel"},
            {"id": "labels", "uri": str(labels), "format": "csv", "table_type": "return_labels"},
            {"id": "weights", "uri": str(weights), "format": "csv", "table_type": "portfolio_weights"},
        ],
        "pipeline": {
            "stages": ["data", "risk", "monitoring", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "portfolio-stress",
                    "stage": "risk",
                    "input_sources": ["labels", "weights"],
                    "parameters": {
                        "label": "intraday",
                        "return_basis": "gross",
                        "weight_type": "target",
                        "confidence": 0.95,
                        "loss_limit": 0.10,
                        "scenarios": scenarios,
                    },
                },
                {
                    "diagnostic_id": "signal-health",
                    "stage": "monitoring",
                    "input_sources": ["factors", "labels"],
                    "parameters": {
                        "signal": "model-score",
                        "label": "intraday",
                        "evaluated_at": "2024-01-08T10:00:00Z",
                        "max_signal_age": "2h",
                        "min_assets": 5,
                        "recent_periods": 3,
                        "min_baseline_periods": 5,
                        "min_recent_rank_ic": 0.0,
                        "max_rank_ic_degradation": 0.10,
                    },
                },
            ],
            "required_diagnostics": ["portfolio-stress", "signal-health"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def artifact(result, stage: str, diagnostic_id: str) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / f"artifacts/{stage}/{diagnostic_id}.json").read_text(encoding="utf-8")
    )


def test_risk_and_signal_health_manifest_passes_stable_inputs(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, degraded=False, crash=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    stress = artifact(result, "risk", "portfolio-stress")
    health = artifact(result, "monitoring", "signal-health")
    assert stress.summary["blocker_count"] == 0
    assert health.summary["recent_mean_rank_ic"] == pytest.approx(1.0)
    assert health.summary["blocker_count"] == 0


def test_portfolio_stress_scenario_blocks_manifest(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, degraded=False, crash=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    stress = artifact(result, "risk", "portfolio-stress")
    assert stress.blockers[0].code == "scenario_loss_limit"


def test_signal_ic_degradation_blocks_manifest(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, degraded=True, crash=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    health = artifact(result, "monitoring", "signal-health")
    assert {blocker.code for blocker in health.blockers} == {
        "rank_ic_degradation",
        "recent_rank_ic_floor",
    }
