from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(tmp_path: Path, *, unstable: bool) -> Path:
    weights = pd.DataFrame(
        [
            {
                "decision_at": "2024-01-01T10:00:00Z",
                "asset_id": "A",
                "weight": -0.10,
                "weight_type": "target",
                "currency": "USD",
            },
            {
                "decision_at": "2024-01-01T10:00:00Z",
                "asset_id": "B",
                "weight": 1.10,
                "weight_type": "target",
                "currency": "USD",
            },
        ]
    )
    quotes = pd.DataFrame(
        [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "asset_id": "A",
                "bid": 99.0,
                "ask": 101.0,
                "volume": 10_000.0,
                "currency": "USD",
                "venue": "X",
            }
        ]
    )
    locates = pd.DataFrame(
        [
            {
                "locate_id": "L1",
                "asset_id": "A",
                "available_at": "2024-01-01T09:00:00Z",
                "effective_from": "2024-01-01T09:00:00Z",
                "expires_at": "2024-01-10T00:00:00Z",
                "recalled_at": "2024-01-02T00:00:00Z" if unstable else None,
                "located_quantity": 60.0,
                "remaining_quantity": 60.0,
                "fee_rate_annual": 0.02,
                "currency": "USD",
                "status": "active",
            },
            {
                "locate_id": "L2",
                "asset_id": "A",
                "available_at": "2024-01-01T09:00:00Z",
                "effective_from": "2024-01-01T09:00:00Z",
                "expires_at": "2024-01-02T12:00:00Z" if unstable else "2024-01-10T00:00:00Z",
                "recalled_at": None,
                "located_quantity": 60.0,
                "remaining_quantity": 60.0,
                "fee_rate_annual": 0.04,
                "currency": "USD",
                "status": "active",
            },
        ]
    )
    sources = []
    for source_id, frame, table_type in (
        ("weights", weights, "portfolio_weights"),
        ("quotes", quotes, "market_quotes"),
        ("locates", locates, "borrow_locates"),
    ):
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    manifest = {
        "project": {"name": "short-borrow-capacity", "asset_class": "equity"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "portfolio", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "short-borrow-capacity",
                    "stage": "portfolio",
                    "input_sources": ["weights", "quotes", "locates"],
                    "parameters": {
                        "weight_type": "target",
                        "venue": "X",
                        "portfolio_value": 100_000.0,
                        "holding_period": "2D",
                        "max_quote_age": "1h",
                        "minimum_borrow_buffer": 1.10,
                        "maximum_blended_fee_annual": 0.05,
                    },
                }
            ],
            "required_diagnostics": ["short-borrow-capacity"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/portfolio/short-borrow-capacity.json").read_text(
            encoding="utf-8"
        )
    )


def test_short_borrow_manifest_passes_buffered_horizon_stable_locates(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, unstable=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["required_quantity"] == pytest.approx(100.0)
    assert artifact.summary["buffered_required_quantity"] == pytest.approx(110.0)
    assert artifact.details[0]["blended_fee_rate_annual"] == pytest.approx(0.02909090909)
    assert artifact.summary["blocker_count"] == 0


def test_short_borrow_manifest_blocks_recall_and_expiry_capacity_loss(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, unstable=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    assert {
        "borrow_expiry_within_horizon",
        "borrow_locate_capacity",
        "borrow_recall_within_horizon",
    } <= {blocker.code for blocker in load_artifact(result).blockers}


def test_short_borrow_tracks_reuse_unscheduled_recall_and_lender_concentration() -> None:
    from data_quant.diagnostics.portfolio import short_borrow_capacity_artifact

    weights = pd.DataFrame(
        {
            "decision_at": ["2024-01-01T10:00:00Z", "2024-01-02T10:00:00Z"],
            "asset_id": ["A", "A"],
            "weight": [-0.10, -0.10],
            "weight_type": ["target", "target"],
            "currency": ["USD", "USD"],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-01T10:00:00Z", "2024-01-02T10:00:00Z"],
            "asset_id": ["A", "A"],
            "bid": [99.0, 99.0],
            "ask": [101.0, 101.0],
            "volume": [10_000.0, 10_000.0],
            "currency": ["USD", "USD"],
            "venue": ["X", "X"],
        }
    )
    locates = pd.DataFrame(
        [
            {
                "locate_id": "L1",
                "asset_id": "A",
                "available_at": "2024-01-01T09:00:00Z",
                "effective_from": "2024-01-01T09:00:00Z",
                "expires_at": "2024-01-10T00:00:00Z",
                "recalled_at": None,
                "located_quantity": 200.0,
                "remaining_quantity": 110.0,
                "fee_rate_annual": 0.02,
                "currency": "USD",
                "status": "active",
                "lender_id": "LN-A",
            }
        ]
    )
    reused = short_borrow_capacity_artifact(
        weights,
        quotes,
        locates,
        portfolio_value=100_000.0,
        holding_period="1D",
        max_quote_age="1h",
        minimum_borrow_buffer=1.0,
        venue="X",
    )
    assert reused.details[0]["status"] == "pass"
    assert reused.details[1]["status"] == "blocked"
    assert reused.provenance["locate_reuse"] == "sequential_remaining_quantity"

    stressed = short_borrow_capacity_artifact(
        weights.iloc[[0]],
        quotes.iloc[[0]],
        locates,
        portfolio_value=100_000.0,
        holding_period="1D",
        max_quote_age="1h",
        minimum_borrow_buffer=1.0,
        unscheduled_recall_fraction=0.50,
        maximum_lender_concentration=0.40,
        venue="X",
    )
    codes = {blocker.code for blocker in stressed.blockers}
    assert "borrow_locate_capacity" in codes
    assert "borrow_lender_concentration" in codes
    assert stressed.details[0]["lender_concentration"] == pytest.approx(1.0)
