from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest

DAY_COUNT_FIRST_STUB = 198 / 365
DAY_COUNT_SECOND_PERIOD = 184 / 365
FIRST_COUPON = 100.0 * 0.05 * DAY_COUNT_FIRST_STUB
SECOND_COUPON = 100.0 * 0.05 * DAY_COUNT_SECOND_PERIOD
ACCRUED_AT_SETTLEMENT = FIRST_COUPON * 91 / 198


def write_manifest(
    tmp_path: Path,
    *,
    mismatch: bool,
    floating: bool = False,
    scheduled: bool = False,
    omit_fixings: bool = False,
    ex_coupon: bool = False,
) -> Path:
    instruments = pd.DataFrame(
        {
            "instrument_id": ["BOND"],
            "issuer_id": ["ISSUER"],
            "currency": ["USD"],
            "issue_at": ["2024-01-15T00:00:00Z"],
            "maturity_at": ["2025-01-31T00:00:00Z"],
            "coupon_rate": [0.05],
            "coupon_frequency": [2],
            "day_count": ["ACT/365"],
            "business_day_convention": ["unadjusted"],
            "face_value": [100.0],
        }
    )
    if floating:
        instruments["coupon_type"] = "floating"
        instruments["coupon_spread_bps"] = 100.0
    if scheduled:
        instruments["amortization_type"] = "scheduled"
    coupon_amounts = [FIRST_COUPON, SECOND_COUPON]
    principal_amounts = [0.0, 100.0]
    accrued_interest = ACCRUED_AT_SETTLEMENT
    if floating:
        coupon_amounts = [100.0 * 0.04 * DAY_COUNT_FIRST_STUB, 100.0 * 0.045 * DAY_COUNT_SECOND_PERIOD]
        accrued_interest = coupon_amounts[0] * 91 / 198
    if scheduled:
        coupon_amounts = [100.0 * (0.04 if floating else 0.05) * DAY_COUNT_FIRST_STUB]
        coupon_amounts.append(60.0 * (0.045 if floating else 0.05) * DAY_COUNT_SECOND_PERIOD)
        principal_amounts = [40.0, 60.0]
    settlement_at = "2024-04-15T12:00:00Z"
    valuation_at = "2024-04-15T13:00:00Z"
    if ex_coupon:
        instruments["ex_coupon_days"] = 30
        settlement_at = "2024-07-15T12:00:00Z"
        valuation_at = "2024-07-15T13:00:00Z"
        accrued_interest = FIRST_COUPON * 182 / 198 - FIRST_COUPON
    observed_at = settlement_at.replace("12:00:00", "10:00:00")
    quote_available_at = settlement_at.replace("12:00:00", "10:05:00")
    cashflows = pd.DataFrame(
        {
            "instrument_id": ["BOND", "BOND"],
            "cashflow_id": ["stub", "final"],
            "available_at": [
                "2024-01-15T00:00:00Z",
                "2024-01-15T00:00:00Z",
            ],
            "accrual_start": [
                "2024-01-15T00:00:00Z",
                "2024-07-31T00:00:00Z",
            ],
            "accrual_end": [
                "2024-07-31T00:00:00Z",
                "2025-01-31T00:00:00Z",
            ],
            "payment_at": [
                "2024-07-31T00:00:00Z",
                "2025-01-31T00:00:00Z",
            ],
            "coupon_amount": coupon_amounts,
            "principal_amount": principal_amounts,
            "currency": ["USD", "USD"],
        }
    )
    if floating:
        cashflows["coupon_rate"] = [0.04, 0.045]
    if scheduled:
        cashflows["principal_balance_start"] = [100.0, 60.0]
        cashflows["principal_balance_end"] = [60.0, 0.0]
    quotes = pd.DataFrame(
        {
            "observed_at": [observed_at],
            "available_at": [quote_available_at],
            "settlement_at": [settlement_at],
            "instrument_id": ["BOND"],
            "venue": ["OTC-1"],
            "clean_price": [99.0],
            "dirty_price": [99.0 + (0.30 if mismatch else accrued_interest)],
            "accrued_interest": [accrued_interest],
            "currency": ["USD"],
        }
    )
    fixings = pd.DataFrame(
        {
            "instrument_id": ["BOND", "BOND"],
            "reset_at": ["2024-01-15T00:00:00Z", "2024-07-31T00:00:00Z"],
            "available_at": ["2024-01-15T00:00:00Z", "2024-01-15T00:00:00Z"],
            "reference_rate": [0.03, 0.035],
            "currency": ["USD", "USD"],
        }
    )
    source_frames = [
        ("instruments", instruments, "fixed_income_instruments"),
        ("cashflows", cashflows, "fixed_income_cashflows"),
        ("quotes", quotes, "fixed_income_price_quotes"),
    ]
    if floating and not omit_fixings:
        source_frames.append(("fixings", fixings, "fixed_income_rate_fixings"))
    sources = []
    for source_id, frame, table_type in source_frames:
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    input_sources = ["instruments", "cashflows", "quotes"]
    if floating and not omit_fixings:
        input_sources.append("fixings")
    manifest = {
        "project": {"name": "fixed-income-price", "asset_class": "fixed_income"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "validation", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "fixed-income-price-reconciliation",
                    "stage": "validation",
                    "input_sources": input_sources,
                    "parameters": {
                        "instrument_id": "BOND",
                        "valuation_at": valuation_at,
                        "venue": "OTC-1",
                        "max_quote_age": "1D",
                        "maximum_price_error": 1e-10,
                        "maximum_coupon_error": 1e-10,
                        "require_irregular_stub": True,
                    },
                }
            ],
            "required_diagnostics": ["fixed-income-price-reconciliation"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (
            result.run_dir
            / "artifacts/validation/fixed-income-price-reconciliation.json"
        ).read_text(encoding="utf-8")
    )


def test_fixed_income_price_manifest_reconciles_irregular_stub_and_accrued_price(
    tmp_path: Path,
) -> None:
    result = run_manifest(
        write_manifest(tmp_path, mismatch=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["cashflow_count"] == 2
    assert artifact.summary["irregular_stub_count"] == 1
    assert artifact.summary["principal_error"] == pytest.approx(0.0)
    assert artifact.summary["computed_accrued_interest"] == pytest.approx(
        ACCRUED_AT_SETTLEMENT
    )
    assert artifact.summary["dirty_identity_error"] == pytest.approx(0.0)
    assert artifact.summary["blocker_count"] == 0


def test_fixed_income_price_manifest_blocks_clean_dirty_mismatch(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, mismatch=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    assert "fixed_income_clean_dirty_mismatch" in {
        blocker.code for blocker in load_artifact(result).blockers
    }


def test_fixed_income_price_manifest_supports_floating_scheduled_amortization(
    tmp_path: Path,
) -> None:
    result = run_manifest(
        write_manifest(tmp_path, mismatch=False, floating=True, scheduled=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["floating_coupon_count"] == 2
    assert artifact.summary["amortization_type"] == "scheduled"
    assert artifact.summary["ending_principal_balance"] == pytest.approx(0.0)
    assert artifact.summary["computed_accrued_interest"] == pytest.approx(
        100.0 * 0.04 * DAY_COUNT_FIRST_STUB * 91 / 198
    )
    assert all(
        detail["coupon_type"] == "floating"
        for detail in artifact.details
        if detail["detail_type"] == "cashflow"
    )


def test_fixed_income_price_manifest_fails_closed_without_floating_fixings(
    tmp_path: Path,
) -> None:
    result = run_manifest(
        write_manifest(tmp_path, mismatch=False, floating=True, omit_fixings=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    assert any("Floating coupons require" in blocker for blocker in result.run_record.blockers)


def test_fixed_income_price_manifest_reconciles_ex_coupon_accrual(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, mismatch=False, ex_coupon=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["ex_coupon_active"] is True
    assert artifact.summary["ex_coupon_days"] == 30
    assert artifact.summary["computed_accrued_interest"] < 0
    assert artifact.details[-1]["ex_coupon_active"] is True
    assert artifact.details[-1]["dirty_identity_error"] == pytest.approx(0.0)
