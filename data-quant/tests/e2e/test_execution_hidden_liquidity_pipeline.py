from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(tmp_path: Path) -> Path:
    orders = pd.DataFrame(
        {
            "order_id": ["o1"],
            "asset_id": ["A"],
            "decision_at": ["2024-01-02T09:00:00Z"],
            "submitted_at": ["2024-01-02T09:00:00Z"],
            "side": ["buy"],
            "quantity": [8.0],
            "order_type": ["market"],
            "venue": ["SIM"],
            "status": ["planned"],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-02T09:00:01Z"],
            "asset_id": ["A"],
            "bid": [9.9],
            "ask": [10.1],
            "volume": [50.0],
            "currency": ["USD"],
            "venue": ["SIM"],
        }
    )
    sources = []
    for source_id, frame, table_type in (
        ("orders", orders, "orders"),
        ("quotes", quotes, "market_quotes"),
    ):
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append({"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type})
    manifest = {
        "project": {"name": "hidden-liquidity", "asset_class": "equity"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "execution", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "execution-replay",
                    "stage": "execution",
                    "input_sources": ["orders", "quotes"],
                    "parameters": {
                        "initial_cash": 1_000.0,
                        "max_participation": 0.10,
                        "hidden_liquidity_fraction": 0.10,
                        "hidden_spread_bps": 10.0,
                    },
                }
            ],
            "required_diagnostics": ["execution-replay"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def test_execution_replay_manifest_fills_hidden_liquidity(tmp_path: Path) -> None:
    result = run_manifest(write_manifest(tmp_path), output_dir=tmp_path / "run")

    assert result.run_record.decision == "conditional_pass"
    assert result.run_record.action == "hold"
    assert result.run_record.stage == "research_candidate"
    artifact = ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/execution/execution-replay.json").read_text(encoding="utf-8")
    )
    fills = artifact.summary.get("fill_count")
    assert fills == 2
    assert artifact.parameters["hidden_liquidity_fraction"] == pytest.approx(0.10)
    assert artifact.parameters["hidden_spread_bps"] == pytest.approx(10.0)
