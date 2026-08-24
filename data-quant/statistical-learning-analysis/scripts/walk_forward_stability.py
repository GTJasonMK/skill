#!/usr/bin/env python3
"""Evaluate walk-forward parameter-selection stability from long-form results.

Requires the shared bundle core dependencies. Input should contain date, parameter identifier, and a
metric such as validation Sharpe, IC, or return. For each fold, the script
selects the best parameter on a trailing training window and evaluates it on
the following test window.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import (
    mean,
    parse_float,
    read_dataframe,
    require_columns,
    sorted_group_keys,
    summarize_values,
)


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")


def aggregate_by_date_param(
    rows: list[dict[str, str]], date_col: str, param_col: str, metric_col: str
) -> tuple[dict[str, dict[str, list[float]]], int]:
    grouped: dict[str, dict[str, list[float]]] = {}
    dropped = 0
    for row in rows:
        date = row.get(date_col, "")
        param = row.get(param_col, "")
        metric = parse_float(row.get(metric_col))
        if not date or not param or metric is None:
            dropped += 1
            continue
        grouped.setdefault(date, {}).setdefault(param, []).append(metric)
    return grouped, dropped


def window_param_mean(
    grouped: dict[str, dict[str, list[float]]], dates: list[str], params: list[str]
) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for param in params:
        values = []
        for date in dates:
            values.extend(grouped.get(date, {}).get(param, []))
        out[param] = mean(values)
    return out


def build_report(
    rows: list[dict[str, str]],
    date_col: str,
    param_col: str,
    metric_col: str,
    train_periods: int,
    test_periods: int,
    higher_is_better: bool,
) -> dict[str, Any]:
    grouped, dropped = aggregate_by_date_param(rows, date_col, param_col, metric_col)
    dates = sorted_group_keys(list(grouped))
    params = sorted({param for by_param in grouped.values() for param in by_param})
    folds = []
    start = 0
    while start + train_periods + test_periods <= len(dates):
        train_dates = dates[start : start + train_periods]
        test_dates = dates[start + train_periods : start + train_periods + test_periods]
        train_scores = window_param_mean(grouped, train_dates, params)
        valid_train = {param: value for param, value in train_scores.items() if value is not None}
        if not valid_train:
            start += test_periods
            continue
        selected = (
            max(valid_train, key=valid_train.get)
            if higher_is_better
            else min(valid_train, key=valid_train.get)
        )
        test_scores = window_param_mean(grouped, test_dates, params)
        valid_test = {param: value for param, value in test_scores.items() if value is not None}
        selected_test = test_scores.get(selected)
        oracle = None
        regret = None
        if valid_test:
            oracle = max(valid_test.values()) if higher_is_better else min(valid_test.values())
            regret = (
                oracle - selected_test
                if higher_is_better and selected_test is not None
                else selected_test - oracle
                if selected_test is not None
                else None
            )
        folds.append(
            {
                "fold": len(folds) + 1,
                "train_start": train_dates[0],
                "train_end": train_dates[-1],
                "test_start": test_dates[0],
                "test_end": test_dates[-1],
                "selected_param": selected,
                "selected_train_metric": train_scores[selected],
                "selected_test_metric": selected_test,
                "oracle_test_metric": oracle,
                "test_regret": regret,
            }
        )
        start += test_periods
    selected_counts: dict[str, int] = {}
    for fold in folds:
        selected_counts[fold["selected_param"]] = selected_counts.get(fold["selected_param"], 0) + 1
    test_values = [fold["selected_test_metric"] for fold in folds if fold["selected_test_metric"] is not None]
    regret_values = [fold["test_regret"] for fold in folds if fold["test_regret"] is not None]
    return {
        "date_col": date_col,
        "param_col": param_col,
        "metric_col": metric_col,
        "higher_is_better": higher_is_better,
        "train_periods": train_periods,
        "test_periods": test_periods,
        "dates_used": len(dates),
        "params_seen": params,
        "rows_dropped": dropped,
        "folds": folds,
        "folds_used": len(folds),
        "selected_param_counts": selected_counts,
        "selection_concentration": max(selected_counts.values()) / len(folds) if folds else None,
        "selected_test_metric_summary": summarize_values(test_values),
        "test_regret_summary": summarize_values(regret_values),
        "notes": [
            "This evaluates parameter-selection stability from precomputed date/parameter metrics.",
            "The metric must be computed without future leakage relative to each date.",
            "Unstable selected parameters or high test regret indicate tuning fragility.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    test = report["selected_test_metric_summary"]
    regret = report["test_regret_summary"]
    lines = [
        "# Walk-Forward Stability Report",
        "",
        f"- Metric: {report['metric_col']}",
        f"- Train periods: {report['train_periods']}",
        f"- Test periods: {report['test_periods']}",
        f"- Folds used: {report['folds_used']}",
        f"- Selection concentration: {report['selection_concentration']}",
        f"- Mean selected test metric: {test['mean']}",
        f"- Mean test regret: {regret['mean']}",
        "",
        "| Fold | Train | Test | Selected param | Train metric | Test metric | Oracle | Regret |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for fold in report["folds"]:
        lines.append(
            f"| {fold['fold']} | {fold['train_start']} to {fold['train_end']} | {fold['test_start']} to {fold['test_end']} | {fold['selected_param']} | {fold['selected_train_metric']} | {fold['selected_test_metric']} | {fold['oracle_test_metric']} | {fold['test_regret']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate walk-forward parameter-selection stability from long-form results."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--param-col", required=True)
    parser.add_argument("--metric-col", required=True)
    parser.add_argument("--train-periods", type=int, default=6)
    parser.add_argument("--test-periods", type=int, default=1)
    parser.add_argument("--lower-is-better", action="store_true")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.train_periods < 1 or args.test_periods < 1:
        raise SystemExit("--train-periods and --test-periods must be positive.")
    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    require_columns(header, [args.date_col, args.param_col, args.metric_col])
    report = build_report(
        rows,
        args.date_col,
        args.param_col,
        args.metric_col,
        args.train_periods,
        args.test_periods,
        not args.lower_is_better,
    )
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown(report), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
