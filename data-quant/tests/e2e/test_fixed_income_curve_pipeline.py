from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(
    tmp_path: Path,
    *,
    loss_limit_fraction: float,
    with_spread: bool = False,
    incomplete_spread: bool = False,
    call_style: str | None = None,
    rate_volatility: float = 0.0,
) -> Path:
    instruments = pd.DataFrame(
        {
            "instrument_id": ["BOND"],
            "issuer_id": ["UST"],
            "currency": ["USD"],
            "issue_at": ["2023-12-31T00:00:00Z"],
            "maturity_at": ["2025-12-31T00:00:00Z"],
            "coupon_rate": [0.05],
            "coupon_frequency": [2],
            "day_count": ["ACT/365"],
            "business_day_convention": ["following"],
            "face_value": [100.0],
        }
    )
    nodes = pd.DataFrame(
        {
            "curve_id": ["USD-OIS"] * 5,
            "observed_at": ["2024-01-02T08:00:00Z"] * 5,
            "available_at": ["2024-01-02T08:30:00Z"] * 5,
            "tenor_years": [0.25, 0.5, 1.0, 2.0, 3.0],
            "zero_rate": [0.04] * 5,
            "currency": ["USD"] * 5,
            "compounding": ["continuous"] * 5,
        }
    )
    spread_tenors = [0.25, 0.5, 1.0] if incomplete_spread else [0.25, 0.5, 1.0, 2.0, 3.0]
    spread_nodes = pd.DataFrame(
        {
            "spread_curve_id": ["BOND-SPREAD"] * len(spread_tenors),
            "instrument_id": ["BOND"] * len(spread_tenors),
            "observed_at": ["2024-01-02T08:00:00Z"] * len(spread_tenors),
            "available_at": ["2024-01-02T08:30:00Z"] * len(spread_tenors),
            "tenor_years": spread_tenors,
            "spread_bps": [100.0] * len(spread_tenors),
            "currency": ["USD"] * len(spread_tenors),
        }
    )
    session_dates = pd.bdate_range("2023-01-01", "2026-12-31")
    calendar = pd.DataFrame(
        {
            "calendar_id": ["US"] * len(session_dates),
            "session": session_dates.strftime("%Y-%m-%d"),
            "timezone": ["America/New_York"] * len(session_dates),
            "open_at": session_dates.strftime("%Y-%m-%dT14:30:00Z"),
            "close_at": session_dates.strftime("%Y-%m-%dT21:00:00Z"),
            "is_half_day": [False] * len(session_dates),
        }
    )
    source_frames = [
        ("instruments", instruments, "fixed_income_instruments"),
        ("curve", nodes, "yield_curve_nodes"),
        ("calendar", calendar, "calendar_sessions"),
    ]
    if with_spread:
        source_frames.append(("spread", spread_nodes, "fixed_income_spread_nodes"))
    sources = []
    for source_id, frame, table_type in source_frames:
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    input_sources = ["instruments", "curve", "calendar"]
    parameters = {
        "instrument_id": "BOND",
        "curve_id": "USD-OIS",
        "calendar_id": "US",
        "valuation_at": "2024-01-02T09:00:00Z",
        "loss_limit_fraction": loss_limit_fraction,
        "scenarios": [
            {
                "name": "rates-up",
                "parallel_bps": 100.0,
                "node_shocks_bps": {"2.0": 25.0},
            }
        ],
    }
    if with_spread:
        input_sources.append("spread")
        parameters.update({"spread_curve_id": "BOND-SPREAD", "require_spread_curve": True})
    if call_style is not None:
        parameters.update(
            {
                "call_price_per_100": 101.0,
                "call_style": call_style,
                "rate_volatility": rate_volatility,
            }
        )
    manifest = {
        "project": {"name": "fixed-income-curve", "asset_class": "fixed_income"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "risk", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "fixed-income-curve-stress",
                    "stage": "risk",
                    "input_sources": input_sources,
                    "parameters": parameters,
                }
            ],
            "required_diagnostics": ["fixed-income-curve-stress"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/risk/fixed-income-curve-stress.json").read_text(
            encoding="utf-8"
        )
    )


def test_fixed_income_curve_manifest_prices_dated_schedule(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, loss_limit_fraction=0.10),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    cashflows = [detail for detail in artifact.details if detail["detail_type"] == "cashflow"]
    assert cashflows[0]["payment_date"] == "2024-07-01"
    assert artifact.summary["dirty_price"] > 100
    assert artifact.summary["parallel_dv01"] > 0
    assert artifact.provenance["curve_extrapolation"] is False


def test_fixed_income_curve_manifest_blocks_scenario_loss(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, loss_limit_fraction=0.005),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    assert artifact.blockers[0].code == "fixed_income_curve_loss_limit"


def test_fixed_income_curve_manifest_applies_pit_spread_nodes(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, loss_limit_fraction=0.10, with_spread=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    cashflows = [detail for detail in artifact.details if detail["detail_type"] == "cashflow"]
    assert artifact.summary["spread_node_count"] == 5
    assert artifact.summary["spread_curve_observed_at"] == "2024-01-02T08:00:00+00:00"
    assert all(detail["spread_bps"] == pytest.approx(100.0) for detail in cashflows)
    assert all(detail["discount_rate"] > detail["zero_rate"] for detail in cashflows)
    assert artifact.summary["dirty_price"] < 100


def test_fixed_income_curve_manifest_blocks_spread_extrapolation(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(
            tmp_path,
            loss_limit_fraction=0.10,
            with_spread=True,
            incomplete_spread=True,
        ),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    assert any(
        "spread extrapolation is prohibited" in blocker
        for blocker in result.run_record.blockers
    )


def test_fixed_income_curve_manifest_prices_stochastic_bermudan(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(
            tmp_path,
            loss_limit_fraction=0.50,
            call_style="bermudan",
            rate_volatility=0.10,
        ),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.provenance["embedded_option"] == "bermudan_two_state_rate_tree"
    assert artifact.parameters["rate_volatility"] == pytest.approx(0.10)
