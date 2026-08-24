from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from data_quant.registry.legacy_catalog import run_legacy_cli


def test_regular_legacy_cli_preserves_format_and_caller_relative_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    csv_path = tmp_path / "data.csv"
    pd.DataFrame({"x": [1, 2, 3], "y": [3, 2, 1]}).to_csv(csv_path, index=False)

    explicit = run_legacy_cli("profile-dataset", [str(csv_path), "--format", "json"])
    assert explicit.summary["legacy_payload"]["row_count"] == 3

    monkeypatch.chdir(tmp_path)
    relative = run_legacy_cli("profile-dataset", [csv_path.name])
    assert relative.summary["legacy_payload"]["row_count"] == 3
    assert Path(relative.summary["legacy_payload"]["path"]).resolve() == csv_path


def test_split_dataset_non_format_cli_is_wrapped(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    pd.DataFrame({"x": range(10), "y": [0, 1] * 5}).to_csv(csv_path, index=False)
    artifact = run_legacy_cli(
        "split-dataset",
        [str(csv_path), "--strategy", "stratified", "--target", "y", "--seed", "7"],
    )
    payload = artifact.summary["legacy_payload"]
    assert artifact.artifact_type == "split_dataset"
    assert payload["rows_total"] == 10
    assert payload["rows_train"] + payload["rows_test"] == 10


def test_sklearn_model_file_report_is_wrapped(tmp_path: Path) -> None:
    csv_path = tmp_path / "model.csv"
    pd.DataFrame(
        {
            "x": range(30),
            "category": ["a", "b", "c"] * 10,
            "target": [0, 1] * 15,
        }
    ).to_csv(csv_path, index=False)
    artifact = run_legacy_cli(
        "sklearn-tabular-model",
        [
            str(csv_path),
            "--target",
            "target",
            "--task",
            "classification",
            "--model",
            "logistic",
            "--seed",
            "7",
        ],
    )
    payload = artifact.summary["legacy_payload"]
    assert artifact.artifact_type == "sklearn_tabular_model"
    assert payload["task"] == "classification"
    assert payload["metrics"]
