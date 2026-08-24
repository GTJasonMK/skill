from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(tmp_path: Path, *, value_limit: float) -> Path:
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
    sources = []
    for source_id, frame, table_type in (
        ("weights", weights, "portfolio_weights"),
        ("labels", labels, "return_labels"),
        ("exposures", exposures, "factor_exposures"),
        ("factor_returns", factor_returns, "factor_returns"),
    ):
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    manifest = {
        "project": {"name": "factor-attribution", "asset_class": "equity"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "risk", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "factor-attribution",
                    "stage": "risk",
                    "input_sources": ["weights", "labels", "exposures", "factor_returns"],
                    "parameters": {
                        "factor_model_id": "M",
                        "decision_at": "2024-01-01T00:00:00Z",
                        "evaluated_at": "2024-02-02T00:00:00Z",
                        "label": "month",
                        "weight_type": "target",
                        "factor_exposure_limits": {"VALUE": value_limit, "MOM": 0.80},
                        "gross_exposure_limit": 1.10,
                        "specific_contribution_limit": 0.02,
                    },
                }
            ],
            "required_diagnostics": ["factor-attribution"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/risk/factor-attribution.json").read_text(encoding="utf-8")
    )


def test_factor_attribution_manifest_reconciles_factor_and_specific_return(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, value_limit=0.50),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["portfolio_return"] == pytest.approx(0.011)
    assert artifact.summary["factor_return_contribution"] == pytest.approx(0.001)
    assert artifact.summary["specific_return_contribution"] == pytest.approx(0.010)
    assert artifact.summary["reconciliation_error"] == pytest.approx(0.0)


def test_factor_attribution_manifest_blocks_formal_exposure_limit(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, value_limit=0.30),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    assert artifact.blockers[0].code == "factor_exposure_limit"
