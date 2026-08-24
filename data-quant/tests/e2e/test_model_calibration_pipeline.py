from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(tmp_path: Path, *, inverted: bool) -> Path:
    prediction_rows = []
    label_rows = []
    asset_index = 0
    for probability, positive_count in ((0.1, 1), (0.5, 5), (0.9, 9)):
        for within_group in range(10):
            asset_id = f"asset-{asset_index}"
            asset_index += 1
            prediction_rows.append(
                {
                    "decision_at": "2024-01-01T00:00:00Z",
                    "available_at": "2024-01-01T00:00:00Z",
                    "model_id": "M",
                    "model_version": "v1",
                    "asset_id": asset_id,
                    "target_label": "up",
                    "prediction": 1.0 - probability if inverted else probability,
                    "prediction_type": "probability",
                }
            )
            label_rows.append(
                {
                    "decision_at": "2024-01-01T00:00:00Z",
                    "execution_at": "2024-01-01T01:00:00Z",
                    "return_start": "2024-01-01T01:00:00Z",
                    "return_end": "2024-01-02T00:00:00Z",
                    "asset_id": asset_id,
                    "label": "up",
                    "return_value": 0.01 if within_group < positive_count else -0.01,
                    "return_type": "simple",
                    "return_basis": "gross",
                    "corporate_action_policy": "total_return",
                    "currency": "USD",
                }
            )
    predictions = pd.DataFrame(prediction_rows)
    labels = pd.DataFrame(label_rows)
    sources = []
    for source_id, frame, table_type in (
        ("predictions", predictions, "model_predictions"),
        ("labels", labels, "return_labels"),
    ):
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    manifest = {
        "project": {"name": "model-calibration", "asset_class": "equity"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "monitoring", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "model-calibration",
                    "stage": "monitoring",
                    "input_sources": ["predictions", "labels"],
                    "parameters": {
                        "model_id": "M",
                        "model_version": "v1",
                        "label": "up",
                        "evaluated_at": "2024-01-03T00:00:00Z",
                        "bins": 10,
                        "min_observations": 30,
                        "max_brier_score": 0.20,
                        "max_log_loss": 1.0,
                        "max_expected_calibration_error": 0.05,
                    },
                }
            ],
            "required_diagnostics": ["model-calibration"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/monitoring/model-calibration.json").read_text(
            encoding="utf-8"
        )
    )


def test_model_calibration_manifest_passes_reliable_probabilities(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, inverted=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["brier_score"] == pytest.approx(0.1433333333)
    assert artifact.summary["expected_calibration_error"] == pytest.approx(0.0)
    assert artifact.summary["calibration_slope"] == pytest.approx(1.0)
    assert artifact.summary["blocker_count"] == 0


def test_model_calibration_manifest_blocks_inverted_probabilities(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, inverted=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    blocker_codes = {blocker.code for blocker in artifact.blockers}
    assert "model_calibration_slope" in blocker_codes
    assert "model_expected_calibration_error" in blocker_codes
