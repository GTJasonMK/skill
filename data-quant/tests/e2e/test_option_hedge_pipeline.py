from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.asset_classes import black_scholes
from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(
    tmp_path: Path,
    *,
    wide_spread: bool,
    american: bool = False,
    omit_events: bool = False,
) -> Path:
    expiry = pd.Timestamp("2025-01-01T00:00:00Z")
    timestamps = pd.to_datetime(
        ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z", "2024-01-03T00:00:00Z"]
    )
    spots = [100.0, 102.0, 101.0]
    mids = [
        black_scholes(
            spot,
            100.0,
            (expiry - timestamp).total_seconds() / (365.25 * 86400),
            0.25,
            option_type="call",
        ).price
        for timestamp, spot in zip(timestamps, spots, strict=True)
    ]
    contracts = pd.DataFrame(
        {
            "option_id": ["C100"],
            "underlying_id": ["S"],
            "venue": ["X"],
            "option_type": ["call"],
            "strike": [100.0],
            "expiry_at": [expiry],
            "exercise_style": ["american" if american else "european"],
            "settlement_type": ["cash"],
            "multiplier": [100.0],
            "currency": ["USD"],
            "listed_at": ["2023-01-01T00:00:00Z"],
        }
    )
    spread_fraction = 0.40 if wide_spread else 0.002
    quotes = pd.DataFrame(
        {
            "timestamp": timestamps,
            "asset_id": ["C100"] * 3,
            "bid": [mid * (1 - spread_fraction / 2) for mid in mids],
            "ask": [mid * (1 + spread_fraction / 2) for mid in mids],
            "volume": [1_000.0] * 3,
            "currency": ["USD"] * 3,
            "venue": ["X"] * 3,
        }
    )
    bars = pd.DataFrame(
        {
            "timestamp": timestamps,
            "asset_id": ["S"] * 3,
            "close": spots,
            "currency": ["USD"] * 3,
            "adjustment_state": ["raw"] * 3,
        }
    )
    exercise_events = pd.DataFrame(
        {
            "option_id": ["C100"],
            "event_at": [timestamps[1]],
            "available_at": [timestamps[0]],
            "event_type": ["assignment"],
            "quantity": [2.0],
            "underlying_price": [spots[1]],
            "currency": ["USD"],
        }
    )
    source_frames = [
        ("contracts", contracts, "option_contracts"),
        ("quotes", quotes, "market_quotes"),
        ("underlying", bars, "market_bars"),
    ]
    if american and not omit_events:
        source_frames.append(("exercise-events", exercise_events, "option_exercise_events"))
    sources = []
    for source_id, frame, table_type in source_frames:
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    input_sources = ["contracts", "quotes", "underlying"]
    if american and not omit_events:
        input_sources.append("exercise-events")
    parameters = {
        "option_id": "C100",
        "option_quantity": -2.0,
        "transaction_cost_bps": 1.0,
        "max_spread_fraction": 0.10,
    }
    if american:
        parameters["allow_american_exercise"] = True
    manifest = {
        "project": {"name": "option-hedge", "asset_class": "options"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "risk", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "option-hedge-replay",
                    "stage": "risk",
                    "input_sources": input_sources,
                    "parameters": parameters,
                }
            ],
            "required_diagnostics": ["option-hedge-replay"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/risk/option-hedge-replay.json").read_text(encoding="utf-8")
    )


def test_option_hedge_manifest_attributes_dynamic_delta_pnl(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, wide_spread=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["observation_count"] == 3
    assert artifact.summary["minimum_implied_volatility"] == pytest.approx(0.25)
    assert artifact.summary["maximum_implied_volatility"] == pytest.approx(0.25)
    assert artifact.summary["total_hedge_transaction_cost"] > 0
    assert artifact.provenance["live_order_submission"] is False


def test_option_hedge_manifest_blocks_non_executable_spread(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, wide_spread=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    assert artifact.summary["blocker_count"] == 3
    assert {blocker.code for blocker in artifact.blockers} == {"option_hedge_spread_limit"}


def test_option_hedge_manifest_replays_american_assignment(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, wide_spread=False, american=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["exercise_event_count"] == 1
    assert artifact.summary["exercise_event_type"] == "assignment"
    assert artifact.summary["observation_count"] == 2
    assert artifact.summary["exercise_settlement_cashflow"] == pytest.approx(-400.0)
    assert artifact.provenance["pricing_model"] == (
        "black_scholes_until_american_event_intrinsic_settlement"
    )
    assert artifact.details[-1]["exercise_event_type"] == "assignment"


def test_option_hedge_manifest_fails_closed_without_american_event(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, wide_spread=False, american=True, omit_events=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    assert any(
        "requires a PIT option exercise-event input" in blocker
        for blocker in result.run_record.blockers
    )
