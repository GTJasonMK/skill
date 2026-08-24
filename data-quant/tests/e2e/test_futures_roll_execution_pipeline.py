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
    initial_cash: float,
    enforce_position_limits: bool = False,
    limit_contracts: float = 1.0,
) -> Path:
    contracts = pd.DataFrame(
        {
            "contract_id": ["F1", "F2"],
            "root": ["F", "F"],
            "venue": ["X", "X"],
            "currency": ["USD", "USD"],
            "multiplier": [10.0, 10.0],
            "tick_size": [0.1, 0.1],
            "listed_at": ["2023-01-01T00:00:00Z"] * 2,
            "last_trade_at": ["2024-01-10T00:00:00Z", "2024-02-10T00:00:00Z"],
            "expiry_at": ["2024-01-10T00:00:00Z", "2024-02-10T00:00:00Z"],
            "settlement_type": ["cash", "cash"],
        }
    )
    bars = pd.DataFrame(
        [
            {
                "timestamp": f"2024-01-{day:02d}T00:00:00Z",
                "asset_id": contract_id,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": 10_000.0,
                "open_interest": 20_000.0,
                "currency": "USD",
                "adjustment_state": "raw",
            }
            for day, prices in ((1, (100.0, 101.0)), (8, (102.0, 103.0)), (9, (104.0, 105.0)))
            for contract_id, price in zip(("F1", "F2"), prices, strict=True)
        ]
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-08T00:00:00Z"] * 2,
            "asset_id": ["F1", "F2"],
            "bid": [101.9, 102.9],
            "ask": [102.1, 103.1],
            "volume": [1_000.0, 1_000.0],
            "currency": ["USD", "USD"],
            "venue": ["X", "X"],
        }
    )
    terms = pd.DataFrame(
        {
            "venue": ["X", "X"],
            "contract_id": ["F1", "F2"],
            "effective_from": ["2023-01-01T00:00:00Z"] * 2,
            "available_at": ["2023-01-01T00:00:00Z"] * 2,
            "initial_margin_per_contract": [200.0, 200.0],
            "maintenance_margin_per_contract": [150.0, 150.0],
            "daily_price_limit_fraction": [0.20, 0.20],
            "currency": ["USD", "USD"],
        }
    )
    limits = pd.DataFrame(
        {
            "venue": ["X", "X"],
            "contract_id": ["F1", "F2"],
            "effective_from": ["2023-01-01T00:00:00Z"] * 2,
            "available_at": ["2023-01-01T00:00:00Z"] * 2,
            "max_contracts": [limit_contracts, limit_contracts],
            "limit_source": ["EXCHANGE", "EXCHANGE"],
        }
    )
    source_frames = [
        ("contracts", contracts, "futures_contracts"),
        ("bars", bars, "market_bars"),
        ("quotes", quotes, "market_quotes"),
        ("terms", terms, "futures_margin_terms"),
    ]
    if enforce_position_limits:
        source_frames.append(("limits", limits, "futures_position_limits"))
    sources = []
    for source_id, frame, table_type in source_frames:
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    input_sources = ["contracts", "bars", "quotes", "terms"]
    if enforce_position_limits:
        input_sources.append("limits")
    parameters = {
        "root": "F",
        "position_quantity": 2.0,
        "initial_cash": initial_cash,
        "roll_days_before_expiry": 5,
        "per_contract_fee": 1.0,
        "collateral_haircut": 0.10,
    }
    if enforce_position_limits:
        parameters["enforce_position_limits"] = True
    manifest = {
        "project": {"name": "futures-roll-execution", "asset_class": "futures"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "execution", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "futures-roll-execution",
                    "stage": "execution",
                    "input_sources": input_sources,
                    "parameters": parameters,
                }
            ],
            "required_diagnostics": ["futures-roll-execution"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/execution/futures-roll-execution.json").read_text(
            encoding="utf-8"
        )
    )


def test_futures_roll_execution_manifest_replays_roll_and_daily_margin(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, initial_cash=1_000.0),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["roll_count"] == 1
    assert artifact.summary["total_variation_margin"] == pytest.approx(76.0)
    assert artifact.summary["total_fees"] == pytest.approx(4.0)
    assert artifact.summary["ending_cash"] == pytest.approx(1_072.0)
    assert artifact.provenance["live_order_submission"] is False


def test_futures_roll_execution_manifest_blocks_margin_breach(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, initial_cash=310.0),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    assert artifact.blockers[0].code == "futures_maintenance_margin_breach"


def test_futures_roll_execution_manifest_blocks_position_limit_breach(
    tmp_path: Path,
) -> None:
    result = run_manifest(
        write_manifest(
            tmp_path,
            initial_cash=1_000.0,
            enforce_position_limits=True,
            limit_contracts=1.0,
        ),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    assert "futures_position_limit_breach" in {
        blocker.code for blocker in artifact.blockers
    }
    assert artifact.summary["position_limits_enforced"] is True


def test_futures_roll_execution_manifest_passes_within_position_limit(
    tmp_path: Path,
) -> None:
    result = run_manifest(
        write_manifest(
            tmp_path,
            initial_cash=1_000.0,
            enforce_position_limits=True,
            limit_contracts=5.0,
        ),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["position_limits_enforced"] is True
    assert artifact.summary["blocker_count"] == 0
