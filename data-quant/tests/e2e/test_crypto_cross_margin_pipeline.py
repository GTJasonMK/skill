from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(
    tmp_path: Path,
    *,
    shock: float,
    intraday_path: list[float] | None = None,
    order_book_impact_bps: float = 0.0,
) -> Path:
    instruments = pd.DataFrame(
        {
            "venue": ["X", "X"],
            "instrument_id": ["BTC-PERP", "ETH-PERP"],
            "instrument_type": ["perpetual", "perpetual"],
            "base_asset": ["BTC", "ETH"],
            "quote_asset": ["USDT", "USDT"],
            "settlement_asset": ["USDT", "USDT"],
            "collateral_asset": ["USDT", "USDT"],
            "multiplier": [1.0, 1.0],
            "listed_at": ["2023-01-01T00:00:00Z"] * 2,
            "margin_mode": ["cross", "cross"],
        }
    )
    positions = pd.DataFrame(
        {
            "observed_at": ["2024-01-01T00:00:00Z"] * 2,
            "available_at": ["2024-01-01T00:00:01Z"] * 2,
            "venue": ["X", "X"],
            "account_id": ["A", "A"],
            "instrument_id": ["BTC-PERP", "ETH-PERP"],
            "signed_quantity": [0.1, 1.0],
            "entry_price": [30_000.0, 2_000.0],
        }
    )
    quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-01T00:01:00Z"] * 2,
            "asset_id": ["BTC-PERP", "ETH-PERP"],
            "bid": [29_990.0, 1_999.0],
            "ask": [30_010.0, 2_001.0],
            "volume": [1_000.0, 10_000.0],
            "currency": ["USDT", "USDT"],
            "venue": ["X", "X"],
        }
    )
    tier_rows = []
    for instrument_id in ("BTC-PERP", "ETH-PERP"):
        tier_rows.extend(
            [
                {
                    "venue": "X",
                    "instrument_id": instrument_id,
                    "effective_from": "2023-01-01T00:00:00Z",
                    "available_at": "2023-01-01T00:00:00Z",
                    "notional_floor": 0.0,
                    "notional_cap": 5_000.0,
                    "initial_margin_rate": 0.10,
                    "maintenance_margin_rate": 0.05,
                    "liquidation_fee_rate": 0.01,
                },
                {
                    "venue": "X",
                    "instrument_id": instrument_id,
                    "effective_from": "2023-01-01T00:00:00Z",
                    "available_at": "2023-01-01T00:00:00Z",
                    "notional_floor": 5_000.0,
                    "notional_cap": None,
                    "initial_margin_rate": 0.20,
                    "maintenance_margin_rate": 0.10,
                    "liquidation_fee_rate": 0.02,
                },
            ]
        )
    tiers = pd.DataFrame(tier_rows)
    sources = []
    for source_id, frame, table_type in (
        ("instruments", instruments, "crypto_instruments"),
        ("positions", positions, "crypto_positions"),
        ("quotes", quotes, "market_quotes"),
        ("tiers", tiers, "crypto_margin_tiers"),
    ):
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append({"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type})
    parameters = {
        "venue": "X",
        "account_id": "A",
        "evaluated_at": "2024-01-01T00:02:00Z",
        "initial_collateral": 2_000.0,
        "insurance_fund": 100.0,
        "venue_default_recovery_rate": 0.95,
        "venue_default_loss_limit_fraction": 0.10,
        "funding_rates": {"BTC-PERP": 0.0001, "ETH-PERP": 0.0001},
        "stress_shocks": [shock],
    }
    if order_book_impact_bps:
        parameters["order_book_impact_bps"] = order_book_impact_bps
    if intraday_path is not None:
        parameters["intraday_path"] = intraday_path
    manifest = {
        "project": {"name": "crypto-cross-margin", "asset_class": "crypto"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "risk", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "crypto-cross-margin-stress",
                    "stage": "risk",
                    "input_sources": ["instruments", "positions", "quotes", "tiers"],
                    "parameters": parameters,
                }
            ],
            "required_diagnostics": ["crypto-cross-margin-stress"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/risk/crypto-cross-margin-stress.json").read_text(encoding="utf-8")
    )


def test_crypto_cross_margin_manifest_passes_supported_stress(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, shock=-0.10, order_book_impact_bps=50.0),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    assert result.run_record.action == "hold"
    assert result.run_record.stage == "research_candidate"
    artifact = load_artifact(result)
    assert artifact.summary["position_count"] == 2
    assert artifact.summary["liquidation_scenario_count"] == 0
    assert artifact.summary["venue_default_loss_fraction"] < 0.10
    assert artifact.parameters["order_book_impact_bps"] == 50.0
    assert artifact.provenance["order_book_impact"] == "linear_volume_participation"
    assert artifact.provenance["live_order_submission"] is False


def test_crypto_cross_margin_manifest_blocks_liquidation_and_adl(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, shock=-0.50, order_book_impact_bps=100.0),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    assert artifact.summary["liquidation_scenario_count"] == 1
    assert artifact.summary["maximum_liquidation_impact_cost"] < 0
    assert artifact.summary["maximum_socialized_loss"] > 0
    assert {blocker.code for blocker in artifact.blockers} == {
        "crypto_adl_required",
        "crypto_cross_margin_liquidation",
    }


def test_crypto_cross_margin_manifest_records_sequential_intraday_quantities(
    tmp_path: Path,
) -> None:
    result = run_manifest(
        write_manifest(tmp_path, shock=-0.10, intraday_path=[-0.50, -0.60]),
        output_dir=tmp_path / "run",
    )

    artifact = load_artifact(result)
    intraday = [detail for detail in artifact.details if detail["detail_type"] == "intraday_print"]
    assert len(intraday) == 2
    assert artifact.summary["intraday_liquidation_print_count"] == 1
    assert artifact.provenance["intraday_quantity_evidence"] == ("remaining_quantities_after_each_print")
    assert intraday[0]["remaining_quantities"]["BTC-PERP"] == 0.0
    assert intraday[1]["remaining_quantities"]["ETH-PERP"] == 0.0
