"""Fold-local linear baselines for quantitative tabular prediction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    log_loss,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.validation import TimeFold

Task = Literal["regression", "classification"]


@dataclass(frozen=True)
class TabularEvaluation:
    predictions: pd.DataFrame
    artifact: ArtifactEnvelope


def _pipeline(task: Task, numeric_columns: list[str], categorical_columns: list[str]) -> Pipeline:
    numeric = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessing = ColumnTransformer(
        [
            ("numeric", numeric, numeric_columns),
            ("categorical", categorical, categorical_columns),
        ],
        remainder="drop",
    )
    model = (
        Ridge(alpha=1.0)
        if task == "regression"
        else LogisticRegression(max_iter=2_000, class_weight="balanced")
    )
    return Pipeline([("preprocess", preprocessing), ("model", model)])


def _regression_metrics(
    truth: pd.Series, prediction: np.ndarray
) -> dict[str, float | None]:
    return {
        "mae": float(mean_absolute_error(truth, prediction)),
        "rmse": float(np.sqrt(mean_squared_error(truth, prediction))),
        "r2": float(r2_score(truth, prediction)),
    }


def _classification_metrics(truth: pd.Series, probability: np.ndarray) -> dict[str, float | None]:
    predicted = (probability >= 0.5).astype(int)
    values: dict[str, float | None] = {
        "accuracy": float(accuracy_score(truth, predicted)),
        "log_loss": float(log_loss(truth, probability, labels=[0, 1])),
    }
    if truth.nunique() == 2:
        values["roc_auc"] = float(roc_auc_score(truth, probability))
        values["average_precision"] = float(average_precision_score(truth, probability))
    else:
        values["roc_auc"] = None
        values["average_precision"] = None
    return values


def evaluate_tabular_baseline(
    frame: pd.DataFrame,
    *,
    target_col: str,
    numeric_columns: list[str],
    categorical_columns: list[str],
    folds: list[TimeFold],
    task: Task,
    run_id: str | None = None,
) -> TabularEvaluation:
    feature_columns = numeric_columns + categorical_columns
    required = [target_col] + feature_columns
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Tabular evaluation missing columns: {missing}")
    if len(feature_columns) != len(set(feature_columns)) or target_col in feature_columns:
        raise ValueError("Feature columns must be unique and cannot include the target.")
    if not folds:
        raise ValueError("At least one time-aware fold is required.")

    rows: list[dict] = []
    fold_metrics: list[dict] = []
    for fold in folds:
        train = frame.iloc[list(fold.train_positions)]
        test = frame.iloc[list(fold.test_positions)]
        if train[target_col].isna().any() or test[target_col].isna().any():
            raise ValueError("Targets cannot be missing within train or test folds.")
        model = _pipeline(task, numeric_columns, categorical_columns)
        model.fit(train[feature_columns], train[target_col])
        if task == "regression":
            prediction = np.asarray(model.predict(test[feature_columns]), dtype=float)
            metrics = _regression_metrics(test[target_col], prediction)
        else:
            classes = list(model.named_steps["model"].classes_)
            if classes != [0, 1]:
                raise ValueError("Classification baseline requires binary targets encoded as 0 and 1.")
            prediction = np.asarray(model.predict_proba(test[feature_columns])[:, 1], dtype=float)
            metrics = _classification_metrics(test[target_col], prediction)
        fold_metrics.append({"fold": fold.fold, "n_test": len(test), **metrics})
        for position, truth, value in zip(fold.test_positions, test[target_col], prediction, strict=True):
            rows.append(
                {
                    "position": int(position),
                    "fold": fold.fold,
                    "truth": float(truth),
                    "prediction": float(value),
                }
            )

    predictions = pd.DataFrame(rows).sort_values(["position", "fold"]).reset_index(drop=True)
    truth = predictions["truth"]
    values = predictions["prediction"].to_numpy(dtype=float)
    overall = (
        _regression_metrics(truth, values)
        if task == "regression"
        else _classification_metrics(truth, values)
    )
    warnings = [
        DiagnosticMessage(
            code="linear_baseline_only",
            message="This is a fold-local linear baseline, not a tuned production model.",
            severity="warning",
        )
    ]
    artifact = ArtifactEnvelope(
        artifact_type="tabular_oof_evaluation",
        run_id=run_id,
        producer=ProducerReference(name="quant-tabular-baseline", version=__version__),
        parameters={
            "task": task,
            "target_col": target_col,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "fold_count": len(folds),
        },
        summary={"n_oof": len(predictions), "overall_metrics": overall},
        warnings=warnings,
        details=fold_metrics,
    ).finalize()
    return TabularEvaluation(predictions=predictions, artifact=artifact)
