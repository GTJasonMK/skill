from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(tmp_path: Path, *, default_multiplier: float) -> Path:
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
    sources = []
    for source_id, frame, table_type in (
        ("exposures", exposures, "credit_exposures"),
        ("matrix", matrix, "credit_transition_matrix"),
    ):
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    manifest = {
        "project": {"name": "credit-migration", "asset_class": "fixed_income"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "risk", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "credit-migration-stress",
                    "stage": "risk",
                    "input_sources": ["exposures", "matrix"],
                    "parameters": {
                        "portfolio_id": "P",
                        "matrix_id": "M",
                        "evaluated_at": "2024-01-02T00:00:00Z",
                        "rating_spreads_bps": {"A": 100.0, "B": 300.0},
                        "default_probability_multiplier": default_multiplier,
                        "loss_limit_fraction": 0.03,
                    },
                }
            ],
            "required_diagnostics": ["credit-migration-stress"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/risk/credit-migration-stress.json").read_text(
            encoding="utf-8"
        )
    )


def test_credit_migration_manifest_prices_migration_default_and_recovery(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, default_multiplier=1.0),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["base_expected_credit_loss"] == pytest.approx(39.2)
    assert artifact.summary["all_default_loss"] == pytest.approx(1_200.0)
    assert artifact.summary["blocker_count"] == 0
    assert artifact.provenance["live_order_submission"] is False


def test_credit_migration_manifest_blocks_stressed_default_loss(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, default_multiplier=3.0),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    assert artifact.summary["stressed_loss_fraction"] > 0.03
    assert artifact.blockers[0].code == "credit_migration_loss_limit"
