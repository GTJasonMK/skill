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
    deviation_bps: float,
    with_replacement: bool = False,
) -> Path:
    spot_bid, spot_ask = 1.099, 1.101
    years = 7 / 365
    carry_factor = math.exp((0.05 - 0.02 + 0.0025) * years)
    deviation_factor = 1 + deviation_bps / 10_000
    spots = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T12:00:00Z"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [spot_bid],
            "ask": [spot_ask],
            "venue": ["SPOT"],
            "spot_date": ["2024-01-04T00:00:00Z"],
        }
    )
    forwards = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T12:00:00Z"],
            "value_date": ["2024-01-11"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [spot_bid * carry_factor * deviation_factor],
            "ask": [spot_ask * carry_factor * deviation_factor],
            "quote_type": ["outright"],
            "venue": ["FWD"],
        }
    )
    replacement = pd.DataFrame(
        {
            "observed_at": ["2024-01-11T10:00:00Z"],
            "available_at": ["2024-01-11T10:05:00Z"],
            "value_date": ["2024-01-11"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [1.110],
            "ask": [1.112],
            "venue": ["FWD"],
        }
    )
    dates = pd.to_datetime(
        ["2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08", "2024-01-11"]
    )
    calendars = pd.concat(
        [
            pd.DataFrame(
                {
                    "calendar_id": calendar_id,
                    "session": dates.strftime("%Y-%m-%d"),
                    "timezone": timezone,
                    "open_at": dates.strftime("%Y-%m-%dT08:00:00Z"),
                    "close_at": dates.strftime("%Y-%m-%dT17:00:00Z"),
                    "is_half_day": False,
                }
            )
            for calendar_id, timezone in (("TARGET", "Europe/Paris"), ("US", "America/New_York"))
        ],
        ignore_index=True,
    )
    source_frames = [
        ("spot", spots, "fx_quotes"),
        ("forward", forwards, "fx_forward_quotes"),
        ("calendar", calendars, "calendar_sessions"),
    ]
    if with_replacement:
        source_frames.append(("replacement", replacement, "fx_replacement_quotes"))
    sources = []
    for source_id, frame, table_type in source_frames:
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    input_sources = ["spot", "forward", "calendar"]
    parameters = {
        "base_currency": "EUR",
        "quote_currency": "USD",
        "base_calendar_id": "TARGET",
        "quote_calendar_id": "US",
        "base_rate": 0.02,
        "quote_rate": 0.05,
        "cross_currency_basis_bps": 25.0,
        "tenor_days": 7,
        "settlement_lag_business_days": 2,
        "deviation_tolerance_bps": 5.0,
        "spot_venue": "SPOT",
        "forward_venue": "FWD",
    }
    if with_replacement:
        input_sources.append("replacement")
        parameters.update(
            {
                "require_replacement_cost": True,
                "replacement_evaluated_at": "2024-01-11T12:00:00Z",
                "settlement_fail_probability": 0.50,
            }
        )
    manifest = {
        "project": {"name": "fx-forward", "asset_class": "fx"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "research", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "fx-forward-check",
                    "stage": "research",
                    "input_sources": input_sources,
                    "parameters": parameters,
                }
            ],
            "required_diagnostics": ["fx-forward-check"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/research/fx-forward-check.json").read_text(encoding="utf-8")
    )


def test_fx_forward_manifest_uses_joint_value_dates_and_basis(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, deviation_bps=0.0),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["spot_value_date"] == "2024-01-04"
    assert artifact.summary["forward_value_date"] == "2024-01-11"
    assert artifact.summary["implied_cross_currency_basis_bps"] == pytest.approx(25.0)
    assert artifact.summary["blocker_count"] == 0


def test_fx_forward_manifest_blocks_cip_basis_deviation(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, deviation_bps=20.0),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    assert artifact.blockers[0].code == "fx_forward_deviation_limit"


def test_fx_forward_manifest_prices_pit_replacement_cost(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, deviation_bps=0.0, with_replacement=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["replacement_cost_quote"] > 0
    assert artifact.summary["replacement_cost_base"] > 0
    assert artifact.summary["replacement_expected_loss"] > 0
    assert artifact.provenance["replacement_cost"] == (
        "adverse_pit_bid_ask_replacement_quote"
    )
