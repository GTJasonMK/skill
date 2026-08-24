from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.asset_classes import black_scholes
from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_multi_asset_manifest(tmp_path: Path, *, crypto_equity: float) -> Path:
    futures_contracts = pd.DataFrame(
        {
            "contract_id": ["F1", "F2"],
            "root": ["F", "F"],
            "venue": ["X", "X"],
            "currency": ["USD", "USD"],
            "multiplier": [10.0, 10.0],
            "tick_size": [0.01, 0.01],
            "listed_at": ["2023-01-01T00:00:00Z"] * 2,
            "last_trade_at": ["2024-01-10T00:00:00Z", "2024-02-10T00:00:00Z"],
            "expiry_at": ["2024-01-10T00:00:00Z", "2024-02-10T00:00:00Z"],
            "settlement_type": ["cash", "cash"],
        }
    )
    futures_bars = pd.DataFrame(
        {
            "timestamp": [
                "2024-01-01T00:00:00Z",
                "2024-01-01T00:00:00Z",
                "2024-01-08T00:00:00Z",
                "2024-01-08T00:00:00Z",
            ],
            "asset_id": ["F1", "F2", "F1", "F2"],
            "close": [100.0, 102.0, 101.0, 104.0],
            "volume": [100.0, 50.0, 60.0, 120.0],
            "open_interest": [110.0, 55.0, 70.0, 130.0],
            "currency": ["USD"] * 4,
            "adjustment_state": ["raw"] * 4,
        }
    )

    quote_at = pd.Timestamp("2024-01-01T00:00:00Z")
    expiry = pd.Timestamp("2025-01-01T00:00:00Z")
    years = (expiry - quote_at).total_seconds() / (365.25 * 86400)
    option_contract_rows = []
    option_quote_rows = []
    for option_type in ("call", "put"):
        for strike in (90.0, 100.0, 110.0):
            option_id = f"OPT-{option_type}-{int(strike)}"
            mid = black_scholes(
                100.0,
                strike,
                years,
                0.20,
                risk_free_rate=0.02,
                option_type=option_type,
            ).price
            option_contract_rows.append(
                {
                    "option_id": option_id,
                    "underlying_id": "SPOT",
                    "venue": "X",
                    "option_type": option_type,
                    "strike": strike,
                    "expiry_at": expiry.isoformat(),
                    "exercise_style": "european",
                    "settlement_type": "cash",
                    "multiplier": 100.0,
                    "currency": "USD",
                    "listed_at": "2023-01-01T00:00:00Z",
                }
            )
            option_quote_rows.append(
                {
                    "timestamp": quote_at.isoformat(),
                    "asset_id": option_id,
                    "bid": mid - 0.01,
                    "ask": mid + 0.01,
                    "volume": 100.0,
                    "currency": "USD",
                    "venue": "X",
                }
            )

    fixed_income = pd.DataFrame(
        {
            "instrument_id": ["BOND-1"],
            "issuer_id": ["ISSUER"],
            "currency": ["USD"],
            "issue_at": ["2020-01-01T00:00:00Z"],
            "maturity_at": ["2027-01-01T00:00:00Z"],
            "coupon_rate": [0.05],
            "coupon_frequency": [2],
            "day_count": ["ACT/365"],
            "business_day_convention": ["following"],
            "face_value": [100.0],
        }
    )
    fx_quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-01T00:00:00Z"],
            "base_currency": ["EUR"],
            "quote_currency": ["USD"],
            "bid": [1.099],
            "ask": [1.101],
            "venue": ["FX"],
            "spot_date": ["2024-01-03T00:00:00Z"],
        }
    )
    crypto_instruments = pd.DataFrame(
        {
            "venue": ["CRX"],
            "instrument_id": ["BTC-PERP"],
            "instrument_type": ["perpetual"],
            "base_asset": ["BTC"],
            "quote_asset": ["USDT"],
            "settlement_asset": ["USDT"],
            "collateral_asset": ["USDT"],
            "multiplier": [1.0],
            "listed_at": ["2020-01-01T00:00:00Z"],
            "margin_mode": ["isolated"],
        }
    )
    crypto_quotes = pd.DataFrame(
        {
            "timestamp": ["2024-01-01T00:00:00Z"],
            "asset_id": ["BTC-PERP"],
            "bid": [9990.0],
            "ask": [10010.0],
            "volume": [100.0],
            "currency": ["USDT"],
            "venue": ["CRX"],
        }
    )

    sources = {
        "futures-contracts": (futures_contracts, "futures_contracts"),
        "futures-bars": (futures_bars, "market_bars"),
        "option-contracts": (pd.DataFrame(option_contract_rows), "option_contracts"),
        "option-quotes": (pd.DataFrame(option_quote_rows), "market_quotes"),
        "fixed-income": (fixed_income, "fixed_income_instruments"),
        "fx-quotes": (fx_quotes, "fx_quotes"),
        "crypto-instruments": (crypto_instruments, "crypto_instruments"),
        "crypto-quotes": (crypto_quotes, "market_quotes"),
    }
    data_sources = []
    for source_id, (frame, table_type) in sources.items():
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        data_sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )

    diagnostics = [
        {
            "diagnostic_id": "futures-roll",
            "stage": "research",
            "input_sources": ["futures-contracts", "futures-bars"],
            "parameters": {
                "root": "F",
                "roll_days_before_expiry": 0,
                "roll_method": "volume",
                "confirmation_periods": 1,
                "collateral_rate_annual": 0.0252,
                "annualization": 252,
            },
        },
        {
            "diagnostic_id": "fx-rollover",
            "stage": "research",
            "input_sources": ["fx-quotes"],
            "parameters": {
                "base_currency": "EUR",
                "quote_currency": "USD",
                "base_rate": 0.02,
                "quote_rate": 0.05,
                "tenor_days": 30,
            },
        },
        {
            "diagnostic_id": "option-surface-check",
            "stage": "risk",
            "input_sources": ["option-contracts", "option-quotes"],
            "parameters": {
                "underlying_id": "SPOT",
                "spot": 100.0,
                "risk_free_rate": 0.02,
                "parity_tolerance": 0.001,
            },
        },
        {
            "diagnostic_id": "fixed-income-shock",
            "stage": "risk",
            "input_sources": ["fixed-income"],
            "parameters": {
                "instrument_id": "BOND-1",
                "valuation_at": "2024-01-01T00:00:00Z",
                "yield_rate": 0.04,
                "parallel_shock_bps": 100,
            },
        },
        {
            "diagnostic_id": "crypto-margin-stress",
            "stage": "risk",
            "input_sources": ["crypto-instruments", "crypto-quotes"],
            "parameters": {
                "venue": "CRX",
                "instrument_id": "BTC-PERP",
                "signed_quantity": 1.0,
                "initial_equity": crypto_equity,
                "maintenance_margin_rate": 0.05,
                "funding_rate": 0.001,
                "stress_shocks": [-0.20, -0.10, 0.10],
            },
        },
    ]
    manifest = {
        "project": {"name": "multi-asset-native", "asset_class": "mixed"},
        "data_sources": data_sources,
        "pipeline": {
            "stages": ["data", "research", "risk", "governance", "report"],
            "diagnostics": diagnostics,
            "required_diagnostics": [item["diagnostic_id"] for item in diagnostics],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(run_dir: Path, stage: str, diagnostic_id: str) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (run_dir / f"artifacts/{stage}/{diagnostic_id}.json").read_text(encoding="utf-8")
    )


def test_multi_asset_manifest_emits_versioned_artifacts(tmp_path: Path) -> None:
    result = run_manifest(
        write_multi_asset_manifest(tmp_path, crypto_equity=5_000.0),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    futures = load_artifact(result.run_dir, "research", "futures-roll")
    options = load_artifact(result.run_dir, "risk", "option-surface-check")
    fixed_income = load_artifact(result.run_dir, "risk", "fixed-income-shock")
    fx = load_artifact(result.run_dir, "research", "fx-rollover")
    crypto = load_artifact(result.run_dir, "risk", "crypto-margin-stress")
    assert futures.summary["roll_count"] == 1
    assert futures.summary["total_observable_roll_gap"] == 3.0
    assert futures.parameters["roll_method"] == "volume"
    assert futures.summary["cumulative_futures_return"] == pytest.approx(0.01)
    assert futures.summary["total_collateral_return"] == pytest.approx(0.0001)
    assert options.summary["iv_count"] == 6
    assert options.summary["blocker_count"] == 0
    assert fixed_income.details[0]["up_shock_return"] < 0
    assert fx.summary["mean_forward_points"] > 0
    assert crypto.summary["blocker_count"] == 0


def test_crypto_margin_breach_blocks_multi_asset_run(tmp_path: Path) -> None:
    result = run_manifest(
        write_multi_asset_manifest(tmp_path, crypto_equity=1_000.0),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result.run_dir, "risk", "crypto-margin-stress")
    assert artifact.summary["blocker_count"] >= 1
    assert artifact.blockers[0].code == "crypto_maintenance_margin_breach"
