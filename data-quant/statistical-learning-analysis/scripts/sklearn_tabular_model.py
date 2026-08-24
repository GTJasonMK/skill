#!/usr/bin/env python3
"""Train baseline tabular classification/regression models from a CSV.

Requires pandas and scikit-learn. Imports are delayed so `--help` works in
minimal environments. Use this as a dependable starter, not as a replacement
for task-specific modeling decisions.
"""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
from typing import Any


def require_dependencies() -> dict[str, Any]:
    missing = []
    try:
        import pandas as pd
    except ImportError:
        missing.append("pandas")
        pd = None
    try:
        import joblib
    except ImportError:
        missing.append("joblib")
        joblib = None
    try:
        from sklearn.compose import ColumnTransformer
        from sklearn.dummy import DummyClassifier, DummyRegressor
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import LogisticRegression, Ridge
        from sklearn.metrics import (
            accuracy_score,
            average_precision_score,
            balanced_accuracy_score,
            f1_score,
            log_loss,
            mean_absolute_error,
            mean_squared_error,
            r2_score,
            roc_auc_score,
        )
        from sklearn.model_selection import GroupShuffleSplit, train_test_split
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler
    except ImportError:
        missing.append("scikit-learn")
    if missing:
        raise SystemExit(
            "Missing dependencies: "
            + ", ".join(sorted(set(missing)))
            + ". Install them before running this script."
        )
    return {
        "pd": pd,
        "joblib": joblib,
        "ColumnTransformer": ColumnTransformer,
        "DummyClassifier": DummyClassifier,
        "DummyRegressor": DummyRegressor,
        "RandomForestClassifier": RandomForestClassifier,
        "RandomForestRegressor": RandomForestRegressor,
        "SimpleImputer": SimpleImputer,
        "LogisticRegression": LogisticRegression,
        "Ridge": Ridge,
        "accuracy_score": accuracy_score,
        "average_precision_score": average_precision_score,
        "balanced_accuracy_score": balanced_accuracy_score,
        "f1_score": f1_score,
        "log_loss": log_loss,
        "mean_absolute_error": mean_absolute_error,
        "mean_squared_error": mean_squared_error,
        "r2_score": r2_score,
        "roc_auc_score": roc_auc_score,
        "GroupShuffleSplit": GroupShuffleSplit,
        "train_test_split": train_test_split,
        "Pipeline": Pipeline,
        "OneHotEncoder": OneHotEncoder,
        "StandardScaler": StandardScaler,
    }


def one_hot_encoder(OneHotEncoder: Any) -> Any:
    params = inspect.signature(OneHotEncoder).parameters
    if "sparse_output" in params:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    return OneHotEncoder(handle_unknown="ignore", sparse=False)


def infer_task(y: Any) -> str:
    unique = y.dropna().nunique()
    if y.dtype.kind in {"O", "b", "U", "S"}:
        return "classification"
    if unique <= 20:
        return "classification"
    return "regression"


def build_pipeline(
    task: str, model_name: str, deps: dict[str, Any], numeric_cols: list[str], categorical_cols: list[str]
) -> Any:
    Pipeline = deps["Pipeline"]
    ColumnTransformer = deps["ColumnTransformer"]
    SimpleImputer = deps["SimpleImputer"]
    StandardScaler = deps["StandardScaler"]
    OneHotEncoder = deps["OneHotEncoder"]
    LogisticRegression = deps["LogisticRegression"]
    Ridge = deps["Ridge"]
    RandomForestClassifier = deps["RandomForestClassifier"]
    RandomForestRegressor = deps["RandomForestRegressor"]

    numeric = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical = Pipeline(
        [("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", one_hot_encoder(OneHotEncoder))]
    )
    preprocessor = ColumnTransformer(
        [("numeric", numeric, numeric_cols), ("categorical", categorical, categorical_cols)],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    if task == "classification":
        if model_name == "auto":
            model_name = "logistic"
        if model_name == "logistic":
            model = LogisticRegression(max_iter=2000, class_weight="balanced")
        elif model_name == "random_forest":
            model = RandomForestClassifier(
                n_estimators=300, random_state=42, class_weight="balanced", n_jobs=-1
            )
        else:
            raise SystemExit("Classification model must be auto, logistic, or random_forest.")
    else:
        if model_name == "auto":
            model_name = "ridge"
        if model_name == "ridge":
            model = Ridge()
        elif model_name == "random_forest":
            model = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
        else:
            raise SystemExit("Regression model must be auto, ridge, or random_forest.")
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def split_data(
    df: Any, target: str, task: str, args: argparse.Namespace, deps: dict[str, Any]
) -> tuple[Any, Any, Any, Any, dict[str, Any]]:
    train_test_split = deps["train_test_split"]
    GroupShuffleSplit = deps["GroupShuffleSplit"]
    sort_info: dict[str, Any] = {}
    if args.time_col:
        df = df.sort_values(args.time_col)
        n_test = max(1, int(round(len(df) * args.test_size)))
        train = df.iloc[:-n_test]
        test = df.iloc[-n_test:]
        sort_info["split"] = "time"
    elif args.group_col:
        splitter = GroupShuffleSplit(n_splits=1, test_size=args.test_size, random_state=args.seed)
        groups = df[args.group_col]
        train_idx, test_idx = next(splitter.split(df, df[target], groups))
        train = df.iloc[train_idx]
        test = df.iloc[test_idx]
        sort_info["split"] = "group"
    else:
        stratify = None
        if task == "classification":
            counts = df[target].value_counts(dropna=False)
            if counts.min() >= 2:
                stratify = df[target]
        train, test = train_test_split(
            df, test_size=args.test_size, random_state=args.seed, stratify=stratify
        )
        sort_info["split"] = "random_stratified" if stratify is not None else "random"
    feature_cols = [
        c
        for c in df.columns
        if c != target and c not in {args.time_col, args.group_col} and c not in args.exclude
    ]
    return train[feature_cols], test[feature_cols], train[target], test[target], sort_info


def classification_metrics(
    y_true: Any, y_pred: Any, proba: Any, deps: dict[str, Any]
) -> dict[str, float | None]:
    metrics = {
        "accuracy": deps["accuracy_score"](y_true, y_pred),
        "balanced_accuracy": deps["balanced_accuracy_score"](y_true, y_pred),
        "f1_weighted": deps["f1_score"](y_true, y_pred, average="weighted"),
    }
    if proba is not None:
        try:
            metrics["log_loss"] = deps["log_loss"](y_true, proba)
        except Exception:
            metrics["log_loss"] = None
        if len(set(y_true)) == 2 and getattr(proba, "shape", [0, 0])[1] >= 2:
            scores = proba[:, 1]
            try:
                metrics["roc_auc"] = deps["roc_auc_score"](y_true, scores)
            except Exception:
                metrics["roc_auc"] = None
            try:
                metrics["average_precision"] = deps["average_precision_score"](y_true, scores)
            except Exception:
                metrics["average_precision"] = None
    return metrics


def regression_metrics(y_true: Any, y_pred: Any, deps: dict[str, Any]) -> dict[str, float]:
    mse = deps["mean_squared_error"](y_true, y_pred)
    return {
        "mae": deps["mean_absolute_error"](y_true, y_pred),
        "rmse": mse**0.5,
        "r2": deps["r2_score"](y_true, y_pred),
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Tabular Model Report",
        "",
        f"- Task: {report['task']}",
        f"- Model: {report['model']}",
        f"- Split: {report['split']['split']}",
        f"- Train rows: {report['n_train']}",
        f"- Test rows: {report['n_test']}",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key, value in report["metrics"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Columns",
            "",
            f"- Numeric: {', '.join(report['numeric_columns']) or 'None'}",
            f"- Categorical: {', '.join(report['categorical_columns']) or 'None'}",
        ]
    )
    lines.extend(
        [
            "",
            "## Caveats",
            "",
            "- This is a starter pipeline. Review leakage, target timing, split design, "
            "calibration, and task-specific diagnostics before using results.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Train a starter scikit-learn tabular classifier/regressor from CSV."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--target", required=True)
    parser.add_argument("--task", choices=["auto", "classification", "regression"], default="auto")
    parser.add_argument("--model", choices=["auto", "logistic", "ridge", "random_forest"], default="auto")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--time-col", help="Optional time column for chronological holdout.")
    parser.add_argument("--group-col", help="Optional group column for group holdout.")
    parser.add_argument("--exclude", default="", help="Comma-separated feature columns to exclude.")
    parser.add_argument("--output-dir", type=Path, default=Path("tabular_model_output"))
    parser.add_argument("--save-model", action="store_true")
    args = parser.parse_args()
    args.exclude = {name.strip() for name in args.exclude.split(",") if name.strip()}

    deps = require_dependencies()
    pd = deps["pd"]
    joblib = deps["joblib"]
    df = pd.read_csv(args.csv_path)
    if args.target not in df.columns:
        raise SystemExit(f"Target column '{args.target}' not found.")
    df = df.dropna(subset=[args.target])
    task = infer_task(df[args.target]) if args.task == "auto" else args.task
    X_train, X_test, y_train, y_test, split_info = split_data(df, args.target, task, args, deps)
    numeric_cols = list(X_train.select_dtypes(include=["number", "bool"]).columns)
    categorical_cols = [col for col in X_train.columns if col not in numeric_cols]
    pipe = build_pipeline(task, args.model, deps, numeric_cols, categorical_cols)
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    if task == "classification":
        proba = pipe.predict_proba(X_test) if hasattr(pipe, "predict_proba") else None
        metrics = classification_metrics(y_test, y_pred, proba, deps)
    else:
        metrics = regression_metrics(y_test, y_pred, deps)
    report = {
        "task": task,
        "model": args.model,
        "target": args.target,
        "split": split_info,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "metrics": metrics,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "model_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "model_report.md").write_text(markdown(report), encoding="utf-8")
    if args.save_model:
        joblib.dump(pipe, args.output_dir / "model.joblib")
    print(markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
