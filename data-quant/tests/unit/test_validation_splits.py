from __future__ import annotations

import pandas as pd
import pytest

from data_quant.diagnostics.validation import corporate_action_adjustment_artifact
from data_quant.validation import combinatorial_purged_split, purged_walk_forward_split, split_artifact


def overlapping_labels() -> pd.DataFrame:
    times = pd.date_range("2024-01-01", periods=12, freq="D", tz="UTC")
    rows = []
    for asset in ("A", "B"):
        for timestamp in times:
            rows.append(
                {
                    "asset": asset,
                    "observation": timestamp,
                    "label_end": timestamp + pd.Timedelta(days=2),
                }
            )
    return pd.DataFrame(rows)


def test_purged_walk_forward_removes_overlapping_labels() -> None:
    frame = overlapping_labels()
    folds = purged_walk_forward_split(
        frame,
        observation_time_col="observation",
        label_end_time_col="label_end",
        train_periods=5,
        test_periods=2,
        embargo=pd.Timedelta(days=1),
    )
    assert folds
    for fold in folds:
        train_end = frame.iloc[list(fold.train_positions)]["label_end"].max()
        test_start = frame.iloc[list(fold.test_positions)]["observation"].min()
        assert train_end < test_start
        assert fold.purged_count > 0


def test_combinatorial_split_has_disjoint_positions() -> None:
    frame = overlapping_labels()
    folds = combinatorial_purged_split(
        frame,
        observation_time_col="observation",
        label_end_time_col="label_end",
        block_count=4,
        test_block_count=1,
        embargo=pd.Timedelta(days=1),
    )
    assert len(folds) >= 2
    for fold in folds:
        assert set(fold.train_positions).isdisjoint(fold.test_positions)


def test_split_artifact_has_stable_contract() -> None:
    folds = purged_walk_forward_split(
        overlapping_labels(),
        observation_time_col="observation",
        label_end_time_col="label_end",
        train_periods=5,
        test_periods=2,
    )
    artifact = split_artifact(folds, method="purged_walk_forward", parameters={"embargo_days": 0})
    assert artifact.artifact_type == "validation_split"
    assert artifact.summary["fold_count"] == len(folds)
    assert artifact.content_digest


def test_invalid_label_end_fails() -> None:
    frame = overlapping_labels()
    frame.loc[0, "label_end"] = frame.loc[0, "observation"] - pd.Timedelta(days=1)
    with pytest.raises(ValueError, match="no earlier"):
        purged_walk_forward_split(
            frame,
            observation_time_col="observation",
            label_end_time_col="label_end",
            train_periods=5,
            test_periods=2,
        )


def test_corporate_action_adjustment_reconciles_spin_off_and_rights() -> None:
    bars = pd.DataFrame(
        [
            {
                "timestamp": timestamp,
                "asset_id": asset_id,
                "close": close,
                "currency": "USD",
                "adjustment_state": state,
            }
            for asset_id, timestamp, close, state in (
                ("spin", "2024-01-01T21:00:00Z", 100.0, "raw"),
                ("spin", "2024-01-02T21:00:00Z", 90.0, "raw"),
                ("spin", "2024-01-01T21:00:00Z", 90.0, "total_return_adjusted"),
                ("spin", "2024-01-02T21:00:00Z", 90.0, "total_return_adjusted"),
                ("rights", "2024-01-01T21:00:00Z", 100.0, "raw"),
                ("rights", "2024-01-02T21:00:00Z", 80.0, "raw"),
                ("rights", "2024-01-01T21:00:00Z", 80.0, "total_return_adjusted"),
                ("rights", "2024-01-02T21:00:00Z", 80.0, "total_return_adjusted"),
            )
        ]
    )
    actions = pd.DataFrame(
        [
            {
                "action_id": "spin-10",
                "asset_id": "spin",
                "action_type": "spin_off",
                "announced_at": "2023-12-01T12:00:00Z",
                "available_at": "2023-12-01T12:01:00Z",
                "effective_at": "2024-01-02T00:00:00Z",
                "value": 10.0,
                "currency": "USD",
            },
            {
                "action_id": "rights-1.25",
                "asset_id": "rights",
                "action_type": "rights",
                "announced_at": "2023-12-01T12:00:00Z",
                "available_at": "2023-12-01T12:01:00Z",
                "effective_at": "2024-01-02T00:00:00Z",
                "value": 1.25,
            },
        ]
    )
    artifact = corporate_action_adjustment_artifact(
        bars,
        actions,
        evaluated_at="2024-01-03T00:00:00Z",
    )
    assert artifact.summary["reconciled_event_count"] == 2
    assert artifact.summary["blocker_count"] == 0
    assert artifact.provenance["spin_off_value_semantics"] == "cash_equivalent_per_parent_share"
    assert artifact.provenance["rights_value_semantics"] == "pre_event_price_adjustment_factor"


def test_corporate_action_adjustment_composes_same_timestamp_split_and_dividend() -> None:
    bars = pd.DataFrame(
        [
            {
                "timestamp": timestamp,
                "asset_id": "A",
                "close": close,
                "currency": "USD",
                "adjustment_state": state,
            }
            for timestamp, close, state in (
                ("2024-01-01T21:00:00Z", 100.0, "raw"),
                ("2024-01-02T21:00:00Z", 49.0, "raw"),
                ("2024-01-01T21:00:00Z", 50.0, "total_return_adjusted"),
                ("2024-01-02T21:00:00Z", 50.0, "total_return_adjusted"),
            )
        ]
    )
    actions = pd.DataFrame(
        [
            {
                "action_id": "split-2",
                "asset_id": "A",
                "action_type": "split",
                "announced_at": "2023-12-01T12:00:00Z",
                "available_at": "2023-12-01T12:01:00Z",
                "effective_at": "2024-01-02T00:00:00Z",
                "value": 2.0,
            },
            {
                "action_id": "div-1",
                "asset_id": "A",
                "action_type": "cash_dividend",
                "announced_at": "2023-12-01T12:00:00Z",
                "available_at": "2023-12-01T12:01:00Z",
                "effective_at": "2024-01-02T00:00:00Z",
                "value": 1.0,
                "currency": "USD",
            },
        ]
    )
    artifact = corporate_action_adjustment_artifact(
        bars,
        actions,
        evaluated_at="2024-01-03T00:00:00Z",
    )
    assert artifact.summary["event_count"] == 1
    assert artifact.summary["reconciled_event_count"] == 1
    assert artifact.summary["blocker_count"] == 0
    assert artifact.details[0]["split_factor"] == pytest.approx(2.0)
    assert artifact.details[0]["cash_equivalent"] == pytest.approx(1.0)
    assert artifact.details[0]["action_order"] == "split_then_rights_then_cash_equivalent"


def test_corporate_action_adjustment_merger_conversion_and_withholding() -> None:
    bars = pd.DataFrame(
        [
            {
                "timestamp": timestamp,
                "asset_id": asset_id,
                "close": close,
                "currency": "USD",
                "adjustment_state": state,
            }
            for asset_id, timestamp, close, state in (
                ("merge", "2024-01-01T21:00:00Z", 100.0, "raw"),
                ("merge", "2024-01-02T21:00:00Z", 20.0, "raw"),
                ("merge", "2024-01-01T21:00:00Z", 50.0, "total_return_adjusted"),
                ("merge", "2024-01-02T21:00:00Z", 50.0, "total_return_adjusted"),
                ("conv", "2024-01-01T21:00:00Z", 100.0, "raw"),
                ("conv", "2024-01-02T21:00:00Z", 50.0, "raw"),
                ("conv", "2024-01-01T21:00:00Z", 50.0, "total_return_adjusted"),
                ("conv", "2024-01-02T21:00:00Z", 50.0, "total_return_adjusted"),
                ("tax", "2024-01-01T21:00:00Z", 100.0, "raw"),
                ("tax", "2024-01-02T21:00:00Z", 99.0, "raw"),
                ("tax", "2024-01-01T21:00:00Z", 50.0, "total_return_adjusted"),
                ("tax", "2024-01-02T21:00:00Z", 50.0, "total_return_adjusted"),
            )
        ]
    )
    actions = pd.DataFrame(
        [
            {
                "action_id": "merge-80",
                "asset_id": "merge",
                "action_type": "merger",
                "announced_at": "2023-12-01T12:00:00Z",
                "available_at": "2023-12-01T12:01:00Z",
                "effective_at": "2024-01-02T00:00:00Z",
                "value": 80.0,
                "currency": "USD",
            },
            {
                "action_id": "conv-2",
                "asset_id": "conv",
                "action_type": "conversion",
                "announced_at": "2023-12-01T12:00:00Z",
                "available_at": "2023-12-01T12:01:00Z",
                "effective_at": "2024-01-02T00:00:00Z",
                "value": 2.0,
            },
            {
                "action_id": "div-2",
                "asset_id": "tax",
                "action_type": "cash_dividend",
                "announced_at": "2023-12-01T12:00:00Z",
                "available_at": "2023-12-01T12:01:00Z",
                "effective_at": "2024-01-02T00:00:00Z",
                "value": 2.0,
                "currency": "USD",
            },
        ]
    )
    artifact = corporate_action_adjustment_artifact(
        bars,
        actions,
        evaluated_at="2024-01-03T00:00:00Z",
        dividend_withholding_rate=0.50,
    )
    assert artifact.summary["reconciled_event_count"] == 3
    assert artifact.summary["blocker_count"] == 0
    by_asset = {row["asset_id"]: row for row in artifact.details}
    assert by_asset["merge"]["cash_equivalent"] == pytest.approx(80.0)
    assert by_asset["conv"]["split_factor"] == pytest.approx(2.0)
    assert by_asset["tax"]["cash_equivalent"] == pytest.approx(1.0)
    assert artifact.provenance["merger_value_semantics"] == "cash_consideration_per_share"
    assert artifact.provenance["dividend_withholding"] == "flat_rate_on_cash_dividend"


def test_corporate_action_adjustment_stock_merger_and_fractional_cash() -> None:
    bars = pd.DataFrame(
        [
            {
                "timestamp": timestamp,
                "asset_id": "A",
                "close": close,
                "currency": "USD",
                "adjustment_state": state,
            }
            for timestamp, close, state in (
                ("2024-01-01T21:00:00Z", 100.0, "raw"),
                ("2024-01-02T21:00:00Z", 49.0, "raw"),
                ("2024-01-01T21:00:00Z", 50.0, "total_return_adjusted"),
                ("2024-01-02T21:00:00Z", 50.0, "total_return_adjusted"),
            )
        ]
    )
    actions = pd.DataFrame(
        [
            {
                "action_id": "stock-2",
                "asset_id": "A",
                "action_type": "stock_merger",
                "announced_at": "2023-12-01T12:00:00Z",
                "available_at": "2023-12-01T12:01:00Z",
                "effective_at": "2024-01-02T00:00:00Z",
                "value": 2.0,
            },
            {
                "action_id": "frac-1",
                "asset_id": "A",
                "action_type": "fractional_cash_in_lieu",
                "announced_at": "2023-12-01T12:00:00Z",
                "available_at": "2023-12-01T12:01:00Z",
                "effective_at": "2024-01-02T00:00:00Z",
                "value": 1.0,
                "currency": "USD",
            },
        ]
    )
    artifact = corporate_action_adjustment_artifact(
        bars,
        actions,
        evaluated_at="2024-01-03T00:00:00Z",
    )
    assert artifact.summary["reconciled_event_count"] == 1
    assert artifact.summary["blocker_count"] == 0
    assert artifact.details[0]["split_factor"] == pytest.approx(2.0)
    assert artifact.details[0]["cash_equivalent"] == pytest.approx(1.0)
    assert artifact.provenance["stock_merger_value_semantics"] == (
        "acquirer_shares_per_target_share"
    )


def test_corporate_action_adjustment_fail_closes_late_vendor_revision() -> None:
    bars = pd.DataFrame(
        [
            {
                "timestamp": timestamp,
                "asset_id": "A",
                "close": close,
                "currency": "USD",
                "adjustment_state": state,
            }
            for timestamp, close, state in (
                ("2024-01-01T21:00:00Z", 100.0, "raw"),
                ("2024-01-02T21:00:00Z", 98.0, "raw"),
                ("2024-01-01T21:00:00Z", 98.0, "total_return_adjusted"),
                ("2024-01-02T21:00:00Z", 98.0, "total_return_adjusted"),
            )
        ]
    )
    actions = pd.DataFrame(
        [
            {
                "action_id": "div-1",
                "asset_id": "A",
                "action_type": "cash_dividend",
                "announced_at": "2023-12-01T12:00:00Z",
                "available_at": "2023-12-01T12:01:00Z",
                "effective_at": "2024-01-02T00:00:00Z",
                "value": 1.0,
                "currency": "USD",
            },
            {
                "action_id": "div-1",
                "asset_id": "A",
                "action_type": "cash_dividend",
                "announced_at": "2023-12-01T12:00:00Z",
                "available_at": "2024-01-03T00:00:00Z",
                "effective_at": "2024-01-02T00:00:00Z",
                "value": 2.0,
                "currency": "USD",
            },
        ]
    )
    allowed = corporate_action_adjustment_artifact(
        bars,
        actions,
        evaluated_at="2024-01-04T00:00:00Z",
        allow_late_revisions=True,
    )
    blocked = corporate_action_adjustment_artifact(
        bars,
        actions,
        evaluated_at="2024-01-04T00:00:00Z",
        allow_late_revisions=False,
    )
    assert allowed.provenance["vendor_revision"] == "latest_available_at_or_before_evaluation"
    assert allowed.summary["reconciled_event_count"] == 1
    assert allowed.summary["blocker_count"] == 0
    assert allowed.details[0]["cash_equivalent"] == pytest.approx(2.0)
    assert "corporate_action_late_revision" in {blocker.code for blocker in blocked.blockers}
