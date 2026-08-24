from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(tmp_path: Path, *, include_target: bool) -> Path:
    decision = "2024-01-02T09:00:00Z"
    rows = [
        {
            "decision_at": decision,
            "asset_id": asset_id,
            "weight": 0.5,
            "weight_type": "current",
            "currency": "USD",
        }
        for asset_id in ("A", "B")
    ]
    if include_target:
        rows.extend(
            {
                "decision_at": decision,
                "asset_id": asset_id,
                "weight": weight,
                "weight_type": "target",
                "currency": "USD",
            }
            for asset_id, weight in (("A", 0.7), ("B", 0.3))
        )
    weights = tmp_path / "weights.csv"
    quotes = tmp_path / "quotes.csv"
    pd.DataFrame(rows).to_csv(weights, index=False)
    pd.DataFrame(
        {
            "timestamp": ["2024-01-02T09:00:01Z"] * 2,
            "asset_id": ["A", "B"],
            "bid": [9.9, 19.9],
            "ask": [10.1, 20.1],
            "volume": [100.0, 100.0],
            "currency": ["USD", "USD"],
            "venue": ["SIM", "SIM"],
        }
    ).to_csv(quotes, index=False)
    manifest = {
        "project": {"name": "rebalance-replay", "asset_class": "equity"},
        "data_sources": [
            {"id": "weights", "uri": str(weights), "format": "csv", "table_type": "portfolio_weights"},
            {"id": "quotes", "uri": str(quotes), "format": "csv", "table_type": "market_quotes"},
        ],
        "pipeline": {
            "stages": ["data", "execution", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "rebalance-replay",
                    "stage": "execution",
                    "input_sources": ["weights", "quotes"],
                    "parameters": {
                        "current_weight_type": "current",
                        "target_weight_type": "target",
                        "portfolio_value": 1_000.0,
                        "lot_size": 1.0,
                        "min_trade_notional": 10.0,
                        "max_participation": 0.10,
                    },
                }
            ],
            "required_diagnostics": ["rebalance-replay"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def test_rebalance_manifest_generates_and_replays_capacity_limited_orders(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, include_target=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/execution/rebalance-replay.json").read_text(encoding="utf-8")
    )
    assert artifact.summary["generated_order_count"] == 2
    assert artifact.summary["status_counts"] == {"filled": 1, "partial": 1}
    assert artifact.provenance["live_order_submission"] is False


def test_rebalance_manifest_fails_closed_without_target_weights(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, include_target=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    assert "requires both current and target weight types" in result.run_record.blockers[0]
