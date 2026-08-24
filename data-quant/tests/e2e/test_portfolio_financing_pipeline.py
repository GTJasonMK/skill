from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(tmp_path: Path, *, bounded: bool) -> Path:
    decisions = ["2024-01-02T09:00:00Z", "2024-01-03T09:00:00Z"]
    weights = pd.DataFrame(
        [
            {
                "decision_at": decision,
                "asset_id": asset_id,
                "weight": 0.25,
                "weight_type": "target",
                "currency": "USD",
            }
            for decision in decisions
            for asset_id in ("A", "B")
        ]
    )
    labels = pd.DataFrame(
        [
            {
                "decision_at": decision,
                "execution_at": decision,
                "return_start": decision,
                "return_end": return_end,
                "asset_id": asset_id,
                "label": "daily",
                "return_value": 0.0,
                "return_type": "simple",
                "return_basis": "gross",
                "corporate_action_policy": "total_return",
                "currency": "USD",
            }
            for decision, return_end in zip(
                decisions,
                ["2024-01-03T09:00:00Z", "2024-01-04T09:00:00Z"],
                strict=True,
            )
            for asset_id in ("A", "B")
        ]
    )
    curve_rows = []
    for effective_from, effective_to, rate in (
        ("2024-01-01T00:00:00Z", "2024-01-03T00:00:00Z", 0.12),
        ("2024-01-03T00:00:00Z", None, 0.24),
    ):
        for rate_type in ("cash", "financing"):
            for tenor_days in ((0, 30) if bounded else (0,)):
                curve_rows.append(
                    {
                        "curve_id": "USD-FUNDING",
                        "currency": "USD",
                        "rate_type": rate_type,
                        "effective_from": effective_from,
                        "effective_to": effective_to,
                        "available_at": effective_from,
                        "tenor_days": tenor_days,
                        "annual_rate": rate,
                        "day_count_basis": "ACT/365",
                        "compounding": "simple",
                    }
                )
    curves = pd.DataFrame(curve_rows)
    sources = []
    for source_id, frame, table_type in (
        ("weights", weights, "portfolio_weights"),
        ("labels", labels, "return_labels"),
        ("curves", curves, "financing_curves"),
    ):
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    manifest = {
        "project": {"name": "pit-financing", "asset_class": "equity"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "portfolio", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "portfolio-backtest",
                    "stage": "portfolio",
                    "input_sources": ["weights", "labels", "curves"],
                    "parameters": {
                        "weight_type": "target",
                        "label": "daily",
                        "financing_curve_id": "USD-FUNDING",
                    },
                }
            ],
            "required_diagnostics": ["portfolio-backtest"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def test_portfolio_manifest_uses_pit_financing_curve(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, bounded=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/portfolio/portfolio-backtest.json").read_text(
            encoding="utf-8"
        )
    )
    assert [row["cash_financing_annual_rate"] for row in artifact.details] == pytest.approx(
        [0.12, 0.24]
    )
    assert artifact.summary["total_cash_financing_return"] == pytest.approx(
        0.5 * (0.12 + 0.24) / 365
    )
    assert artifact.parameters["financing_curve_id"] == "USD-FUNDING"


def test_portfolio_manifest_refuses_financing_curve_extrapolation(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, bounded=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    assert any("extrapolation is prohibited" in blocker for blocker in result.run_record.blockers)
