from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from data_quant.asset_classes import black_scholes
from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(
    tmp_path: Path,
    *,
    tenor_grid_years: list[float],
    smoothing_method: str = "rolling_median",
) -> Path:
    quote_at = pd.Timestamp("2024-01-01T00:00:00Z")
    expiries = [pd.Timestamp("2024-07-01T00:00:00Z"), pd.Timestamp("2025-01-01T00:00:00Z")]
    strikes = [80.0, 100.0, 120.0]
    contracts_rows = []
    quote_rows = []
    for expiry_index, expiry in enumerate(expiries):
        years = (expiry - quote_at).total_seconds() / (365.25 * 24 * 3600)
        for strike in strikes:
            for option_type in ("call", "put"):
                option_id = f"{option_type[0].upper()}{expiry_index}{int(strike)}"
                price = black_scholes(
                    100.0, strike, years, 0.20, option_type=option_type
                ).price
                contracts_rows.append(
                    {
                        "option_id": option_id,
                        "underlying_id": "S",
                        "venue": "X",
                        "option_type": option_type,
                        "strike": strike,
                        "expiry_at": expiry.isoformat(),
                        "exercise_style": "european",
                        "settlement_type": "cash",
                        "multiplier": 1.0,
                        "currency": "USD",
                        "listed_at": "2023-01-01T00:00:00Z",
                    }
                )
                quote_rows.append(
                    {
                        "timestamp": quote_at.isoformat(),
                        "asset_id": option_id,
                        "bid": price - 0.001,
                        "ask": price + 0.001,
                        "volume": 1_000.0,
                        "currency": "USD",
                        "venue": "X",
                    }
                )
    sources = []
    for source_id, frame, table_type in (
        ("contracts", pd.DataFrame(contracts_rows), "option_contracts"),
        ("quotes", pd.DataFrame(quote_rows), "market_quotes"),
    ):
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    parameters = {
        "underlying_id": "S",
        "venue": "X",
        "evaluated_at": "2024-01-02T00:00:00Z",
        "spot": 100.0,
        "min_expiries": 2,
        "min_strikes_per_expiry": 3,
        "moneyness_grid": [-0.15, 0.0, 0.15],
        "tenor_grid_years": tenor_grid_years,
        "smoothing_method": smoothing_method,
    }
    manifest = {
        "project": {"name": "option-surface-smooth", "asset_class": "options"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "risk", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "option-surface-smooth",
                    "stage": "risk",
                    "input_sources": ["contracts", "quotes"],
                    "parameters": parameters,
                }
            ],
            "required_diagnostics": ["option-surface-smooth"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/risk/option-surface-smooth.json").read_text(encoding="utf-8")
    )


def test_option_surface_smooth_manifest_passes_pit_term_and_moneyness_grid(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, tenor_grid_years=[]),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["observed_expiry_count"] == 2
    assert artifact.summary["smoothed_node_count"] == 6
    assert artifact.summary["blocker_count"] == 0
    assert artifact.provenance["live_order_submission"] is False


def test_option_surface_smooth_manifest_blocks_term_extrapolation(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, tenor_grid_years=[0.10]),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    assert artifact.summary["smoothed_node_count"] == 0
    assert artifact.blockers[0].code == "option_surface_term_extrapolation"


def test_option_surface_smooth_manifest_passes_restricted_svi(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, tenor_grid_years=[], smoothing_method="svi_total_variance"),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.provenance["smoothing"] == (
        "restricted_svi_total_variance_then_bounded_linear_interpolation"
    )
    assert artifact.summary["blocker_count"] == 0


def test_option_surface_smooth_manifest_passes_ssvi(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, tenor_grid_years=[], smoothing_method="ssvi_total_variance"),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.provenance["smoothing"] == "ssvi_power_law_then_bounded_linear_interpolation"
    assert artifact.summary["blocker_count"] == 0
