from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(
    tmp_path: Path,
    *,
    volatility_limit: float,
    specific_risk_volatilities: dict[str, float] | None = None,
    total_volatility_limit: float | None = None,
) -> Path:
    weights = pd.DataFrame(
        {
            "decision_at": ["2024-01-01T00:00:00Z"] * 2,
            "asset_id": ["A", "B"],
            "weight": [0.60, 0.40],
            "weight_type": ["target", "target"],
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
    factor_rows = []
    for start, end, value_return, momentum_return in (
        ("2023-12-27T00:00:00Z", "2023-12-28T00:00:00Z", 0.01, 0.00),
        ("2023-12-28T00:00:00Z", "2023-12-29T00:00:00Z", -0.01, 0.00),
        ("2023-12-29T00:00:00Z", "2023-12-30T00:00:00Z", 0.00, 0.02),
        ("2023-12-30T00:00:00Z", "2023-12-31T00:00:00Z", 0.00, -0.02),
    ):
        for factor_id, factor_return in (("VALUE", value_return), ("MOM", momentum_return)):
            factor_rows.append(
                {
                    "factor_model_id": "M",
                    "factor_id": factor_id,
                    "return_start": start,
                    "return_end": end,
                    "available_at": end,
                    "return_value": factor_return,
                    "return_type": "simple",
                    "return_basis": "gross",
                    "currency": "USD",
                }
            )
    factor_returns = pd.DataFrame(factor_rows)
    sources = []
    for source_id, frame, table_type in (
        ("weights", weights, "portfolio_weights"),
        ("exposures", exposures, "factor_exposures"),
        ("factor_returns", factor_returns, "factor_returns"),
    ):
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    manifest = {
        "project": {"name": "factor-risk", "asset_class": "equity"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "risk", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "factor-risk",
                    "stage": "risk",
                    "input_sources": ["weights", "exposures", "factor_returns"],
                    "parameters": {
                        "factor_model_id": "M",
                        "decision_at": "2024-01-01T00:00:00Z",
                        "weight_type": "target",
                        "lookback_periods": 4,
                        "minimum_observations": 4,
                        "annualization": 252.0,
                        "maximum_annualized_factor_volatility": volatility_limit,
                        "maximum_covariance_condition_number": 10.0,
                        "factor_exposure_limits": {"VALUE": 0.50, "MOM": 0.80},
                        "specific_risk_volatilities": specific_risk_volatilities or {},
                        "maximum_annualized_total_volatility": total_volatility_limit,
                    },
                }
            ],
            "required_diagnostics": ["factor-risk"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/risk/factor-risk.json").read_text(encoding="utf-8")
    )


def test_factor_risk_manifest_decomposes_covariance_volatility(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, volatility_limit=0.20),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    expected_variance = 252.0 * (0.4**2 * 0.0002 / 3 + 0.7**2 * 0.0008 / 3)
    assert artifact.summary["annualized_factor_variance"] == pytest.approx(expected_variance)
    assert artifact.summary["annualized_factor_volatility"] == pytest.approx(
        math.sqrt(expected_variance)
    )
    assert artifact.summary["component_volatility_sum"] == pytest.approx(
        artifact.summary["annualized_factor_volatility"]
    )
    assert artifact.summary["covariance_condition_number"] == pytest.approx(4.0)
    assert artifact.summary["blocker_count"] == 0


def test_factor_risk_manifest_blocks_factor_volatility_limit(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, volatility_limit=0.15),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    assert "factor_volatility_limit" in {
        blocker.code for blocker in load_artifact(result).blockers
    }


def test_factor_risk_manifest_reports_specific_and_total_volatility(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(
            tmp_path,
            volatility_limit=0.20,
            specific_risk_volatilities={"A": 0.10, "B": 0.20},
        ),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    expected_specific_variance = 0.6**2 * 0.10**2 + 0.4**2 * 0.20**2
    assert artifact.summary["annualized_specific_variance"] == pytest.approx(
        expected_specific_variance
    )
    assert artifact.summary["annualized_total_variance"] == pytest.approx(
        artifact.summary["annualized_factor_variance"] + expected_specific_variance
    )
    assert artifact.summary["annualized_total_volatility"] == pytest.approx(
        math.sqrt(
            artifact.summary["annualized_factor_variance"] + expected_specific_variance
        )
    )
    assert artifact.provenance["specific_risk_model"] == "diagonal_per_asset_variance"
    assert artifact.summary["blocker_count"] == 0


def test_factor_risk_manifest_blocks_total_volatility_limit(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(
            tmp_path,
            volatility_limit=0.20,
            specific_risk_volatilities={"A": 0.10, "B": 0.20},
            total_volatility_limit=0.05,
        ),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    assert "factor_total_volatility_limit" in {
        blocker.code for blocker in load_artifact(result).blockers
    }

