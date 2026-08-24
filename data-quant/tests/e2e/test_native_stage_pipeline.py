from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_stage_manifest(tmp_path: Path, *, drifted: bool) -> Path:
    decisions = pd.date_range("2024-01-01T09:00:00Z", periods=6, freq="D")
    label_rows = []
    returns = {
        "A": [0.01, 0.02, -0.01, 0.03, 0.0, 0.015],
        "B": [0.0, -0.01, 0.02, 0.01, -0.005, 0.025],
    }
    for index, decision in enumerate(decisions):
        for asset in ("A", "B"):
            label_rows.append(
                {
                    "decision_at": decision,
                    "execution_at": decision + pd.Timedelta(minutes=1),
                    "return_start": decision + pd.Timedelta(minutes=1),
                    "return_end": decision + pd.Timedelta(hours=1),
                    "asset_id": asset,
                    "label": "intraday",
                    "return_value": returns[asset][index],
                    "return_type": "simple",
                    "return_basis": "gross",
                    "corporate_action_policy": "total_return",
                    "currency": "USD",
                }
            )
    labels_path = tmp_path / "labels.csv"
    pd.DataFrame(label_rows).to_csv(labels_path, index=False)

    weights_path = tmp_path / "weights.csv"
    pd.DataFrame(
        {
            "decision_at": ["2024-01-07T09:00:00Z"] * 2,
            "asset_id": ["A", "B"],
            "weight": [0.6, 0.4],
            "weight_type": ["target", "target"],
            "currency": ["USD", "USD"],
        }
    ).to_csv(weights_path, index=False)

    factor_rows = pd.DataFrame(
        {
            "as_of": ["2024-01-01T09:00:00Z"] * 20,
            "asset_id": [f"asset-{index:02d}" for index in range(20)],
            "signal": ["feature"] * 20,
            "value": [float(index) for index in range(20)],
            "available_at": ["2024-01-01T08:59:00Z"] * 20,
        }
    )
    reference_path = tmp_path / "reference.csv"
    current_path = tmp_path / "current.csv"
    factor_rows.to_csv(reference_path, index=False)
    if drifted:
        factor_rows["value"] = factor_rows["value"] + 100.0
    factor_rows.to_csv(current_path, index=False)

    manifest = {
        "project": {"name": "native-stages", "asset_class": "equity"},
        "data_sources": [
            {
                "id": "labels",
                "uri": str(labels_path),
                "format": "csv",
                "table_type": "return_labels",
            },
            {
                "id": "weights",
                "uri": str(weights_path),
                "format": "csv",
                "table_type": "portfolio_weights",
            },
            {
                "id": "reference",
                "uri": str(reference_path),
                "format": "csv",
                "table_type": "factor_panel",
            },
            {
                "id": "current",
                "uri": str(current_path),
                "format": "csv",
                "table_type": "factor_panel",
            },
        ],
        "pipeline": {
            "stages": ["data", "validation", "risk", "monitoring", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "purged-walk-forward",
                    "stage": "validation",
                    "input_sources": ["labels"],
                    "parameters": {
                        "label": "intraday",
                        "train_periods": 2,
                        "test_periods": 1,
                    },
                },
                {
                    "diagnostic_id": "covariance-risk",
                    "stage": "risk",
                    "input_sources": ["labels", "weights"],
                    "parameters": {
                        "label": "intraday",
                        "return_basis": "gross",
                        "weight_type": "target",
                        "annualization": 252,
                    },
                },
                {
                    "diagnostic_id": "feature-drift",
                    "stage": "monitoring",
                    "input_sources": ["reference", "current"],
                    "parameters": {
                        "reference_source": "reference",
                        "current_source": "current",
                        "columns": ["value"],
                        "bins": 5,
                        "warning_threshold": 0.01,
                        "blocker_threshold": 0.10,
                    },
                },
            ],
            "required_diagnostics": [
                "purged-walk-forward",
                "covariance-risk",
                "feature-drift",
            ],
            "fail_closed": True,
        },
    }
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return manifest_path


def test_validation_risk_and_monitoring_stages_emit_artifacts(tmp_path: Path) -> None:
    result = run_manifest(
        write_stage_manifest(tmp_path, drifted=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    assert result.run_record.action == "hold"
    assert result.run_record.stage == "research_candidate"
    assert result.run_record.provenance["completed_diagnostics"] == [
        "covariance-risk",
        "data-contract",
        "feature-drift",
        "purged-walk-forward",
    ]
    split = ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/validation/purged-walk-forward.json").read_text(
            encoding="utf-8"
        )
    )
    risk = ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/risk/covariance-risk.json").read_text(encoding="utf-8")
    )
    drift = ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/monitoring/feature-drift.json").read_text(
            encoding="utf-8"
        )
    )
    assert split.summary["fold_count"] == 4
    assert risk.summary["annualized_volatility"] > 0
    assert drift.summary["max_psi"] == 0.0


def test_monitoring_blocker_fails_closed_but_preserves_artifact(tmp_path: Path) -> None:
    result = run_manifest(
        write_stage_manifest(tmp_path, drifted=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    monitoring = next(
        handoff for handoff in result.run_record.handoffs if handoff.stage == "monitoring"
    )
    assert monitoring.status == "blocked"
    artifact = ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/monitoring/feature-drift.json").read_text(
            encoding="utf-8"
        )
    )
    assert artifact.summary["blocker_count"] == 1
    assert artifact.blockers[0].code == "feature_drift_blocker"
