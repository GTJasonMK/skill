from __future__ import annotations

import numpy as np
import pandas as pd

from data_quant.ml import evaluate_tabular_baseline
from data_quant.validation import purged_walk_forward_split


def frame() -> pd.DataFrame:
    times = pd.date_range("2024-01-01", periods=20, freq="D", tz="UTC")
    return pd.DataFrame(
        {
            "observation": times,
            "label_end": times + pd.Timedelta(hours=12),
            "x": np.linspace(-2, 2, 20),
            "category": ["a", "b"] * 10,
            "target_regression": np.linspace(-2, 2, 20) * 2 + 1,
            "target_classification": (np.arange(20) % 2).astype(int),
        }
    )


def folds(data: pd.DataFrame):
    return purged_walk_forward_split(
        data,
        observation_time_col="observation",
        label_end_time_col="label_end",
        train_periods=8,
        test_periods=4,
        expanding=True,
    )


def test_regression_pipeline_emits_oof_artifact() -> None:
    data = frame()
    result = evaluate_tabular_baseline(
        data,
        target_col="target_regression",
        numeric_columns=["x"],
        categorical_columns=["category"],
        folds=folds(data),
        task="regression",
    )
    assert not result.predictions.empty
    assert result.artifact.artifact_type == "tabular_oof_evaluation"
    assert result.artifact.summary["overall_metrics"]["r2"] > 0.9


def test_classification_pipeline_uses_binary_probability() -> None:
    data = frame()
    result = evaluate_tabular_baseline(
        data,
        target_col="target_classification",
        numeric_columns=["x"],
        categorical_columns=[],
        folds=folds(data),
        task="classification",
    )
    assert result.predictions["prediction"].between(0, 1).all()
    assert result.artifact.summary["overall_metrics"]["roc_auc"] is not None
