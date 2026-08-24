from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(tmp_path: Path, *, mismatch: bool) -> Path:
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
                ("split", "2024-01-01T21:00:00Z", 100.0, "raw"),
                ("split", "2024-01-02T21:00:00Z", 50.0, "raw"),
                ("split", "2024-01-01T21:00:00Z", 50.0, "total_return_adjusted"),
                (
                    "split",
                    "2024-01-02T21:00:00Z",
                    55.0 if mismatch else 50.0,
                    "total_return_adjusted",
                ),
                ("dividend", "2024-01-01T21:00:00Z", 100.0, "raw"),
                ("dividend", "2024-01-02T21:00:00Z", 99.0, "raw"),
                ("dividend", "2024-01-01T21:00:00Z", 99.0, "total_return_adjusted"),
                ("dividend", "2024-01-02T21:00:00Z", 99.0, "total_return_adjusted"),
            )
        ]
    )
    actions = pd.DataFrame(
        [
            {
                "action_id": "split-2-for-1",
                "asset_id": "split",
                "action_type": "split",
                "announced_at": "2023-12-01T12:00:00Z",
                "available_at": "2023-12-01T12:01:00Z",
                "effective_at": "2024-01-02T00:00:00Z",
                "value": 2.0,
                "currency": "USD",
            },
            {
                "action_id": "cash-1",
                "asset_id": "dividend",
                "action_type": "cash_dividend",
                "announced_at": "2023-12-01T12:00:00Z",
                "available_at": "2023-12-01T12:01:00Z",
                "effective_at": "2024-01-02T00:00:00Z",
                "value": 1.0,
                "currency": "USD",
            },
        ]
    )
    sources = []
    for source_id, frame, table_type in (
        ("bars", bars, "market_bars"),
        ("actions", actions, "corporate_actions"),
    ):
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    manifest = {
        "project": {"name": "corporate-action-adjustment", "asset_class": "equity"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "validation", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "corporate-action-adjustment",
                    "stage": "validation",
                    "input_sources": ["bars", "actions"],
                    "parameters": {
                        "evaluated_at": "2024-01-03T00:00:00Z",
                        "max_bar_gap": "2D",
                        "maximum_return_error": 1e-10,
                        "minimum_actions": 2,
                    },
                }
            ],
            "required_diagnostics": ["corporate-action-adjustment"],
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
            / "artifacts/validation/corporate-action-adjustment.json"
        ).read_text(encoding="utf-8")
    )


def test_corporate_action_adjustment_reconciles_split_and_dividend(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, mismatch=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["observable_action_count"] == 2
    assert artifact.summary["reconciled_event_count"] == 2
    assert artifact.summary["maximum_absolute_return_error"] == pytest.approx(0.0)
    assert artifact.summary["blocker_count"] == 0


def test_corporate_action_adjustment_blocks_mismatched_adjusted_return(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, mismatch=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    assert artifact.summary["maximum_absolute_return_error"] == pytest.approx(0.1)
    assert "corporate_action_adjustment_mismatch" in {
        blocker.code for blocker in artifact.blockers
    }


def write_revision_manifest(tmp_path: Path, *, allow_late: bool) -> Path:
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
    sources = []
    for source_id, frame, table_type in (
        ("bars", bars, "market_bars"),
        ("actions", actions, "corporate_actions"),
    ):
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    manifest = {
        "project": {"name": "corporate-action-revision", "asset_class": "equity"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "validation", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "corporate-action-adjustment",
                    "stage": "validation",
                    "input_sources": ["bars", "actions"],
                    "parameters": {
                        "evaluated_at": "2024-01-04T00:00:00Z",
                        "max_bar_gap": "2D",
                        "allow_late_revisions": allow_late,
                    },
                }
            ],
            "required_diagnostics": ["corporate-action-adjustment"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def test_corporate_action_adjustment_manifest_uses_latest_vendor_revision(
    tmp_path: Path,
) -> None:
    result = run_manifest(
        write_revision_manifest(tmp_path, allow_late=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.details[0]["cash_equivalent"] == pytest.approx(2.0)
    assert artifact.summary["blocker_count"] == 0


def test_corporate_action_adjustment_manifest_blocks_late_vendor_revision(
    tmp_path: Path,
) -> None:
    result = run_manifest(
        write_revision_manifest(tmp_path, allow_late=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    assert "corporate_action_late_revision" in {
        blocker.code for blocker in artifact.blockers
    }
