#!/usr/bin/env python3
"""Backtest naive and seasonal-naive forecasts for a univariate CSV series.

Standard-library only. This gives forecasting baselines that more complex
models should beat before they are trusted.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


def parse_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    try:
        out = float(value.replace(",", ""))
    except ValueError:
        return None
    return None if math.isnan(out) or math.isinf(out) else out


def read_series(path: Path, date_col: str, target_col: str) -> list[tuple[str, float]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(handle, dialect=dialect)
        if date_col not in (reader.fieldnames or []) or target_col not in (reader.fieldnames or []):
            raise SystemExit("Date or target column not found.")
        rows = []
        for row in reader:
            value = parse_float(row.get(target_col))
            if value is not None:
                rows.append((row.get(date_col, ""), value))
    return sorted(rows, key=lambda item: item[0])


def metric_summary(errors: list[float]) -> dict[str, float | int | None]:
    if not errors:
        return {"count": 0, "mae": None, "rmse": None, "bias": None}
    mae = sum(abs(err) for err in errors) / len(errors)
    rmse = math.sqrt(sum(err * err for err in errors) / len(errors))
    bias = sum(errors) / len(errors)
    return {"count": len(errors), "mae": mae, "rmse": rmse, "bias": bias}


def backtest(
    series: list[tuple[str, float]], horizon: int, seasonal_period: int, initial_window: int
) -> dict[str, object]:
    y = [value for _, value in series]
    dates = [date for date, _ in series]
    errors: dict[str, dict[int, list[float]]] = {
        "naive": defaultdict(list),
        "seasonal_naive": defaultdict(list),
    }
    predictions = []
    max_origin = len(y) - horizon
    for origin in range(initial_window, max_origin + 1):
        last_value = y[origin - 1]
        for h in range(1, horizon + 1):
            actual_index = origin + h - 1
            actual = y[actual_index]
            naive_pred = last_value
            errors["naive"][h].append(naive_pred - actual)
            row = {
                "origin_index": origin,
                "target_date": dates[actual_index],
                "horizon": h,
                "actual": actual,
                "naive": naive_pred,
            }
            seasonal_index = actual_index - seasonal_period
            if seasonal_period > 0 and 0 <= seasonal_index < origin:
                seasonal_pred = y[seasonal_index]
                errors["seasonal_naive"][h].append(seasonal_pred - actual)
                row["seasonal_naive"] = seasonal_pred
            predictions.append(row)
    metrics = {}
    for model, by_horizon in errors.items():
        metrics[model] = {str(h): metric_summary(vals) for h, vals in sorted(by_horizon.items())}
        all_errors = [err for vals in by_horizon.values() for err in vals]
        metrics[model]["overall"] = metric_summary(all_errors)
    return {
        "n_observations": len(series),
        "horizon": horizon,
        "seasonal_period": seasonal_period,
        "initial_window": initial_window,
        "origins_evaluated": max(0, max_origin - initial_window + 1),
        "metrics": metrics,
        "predictions": predictions,
    }


def markdown(result: dict[str, object]) -> str:
    lines = [
        "# Time Series Baseline Backtest",
        "",
        f"- Observations: {result['n_observations']}",
        f"- Horizon: {result['horizon']}",
        f"- Seasonal period: {result['seasonal_period']}",
        f"- Initial window: {result['initial_window']}",
        f"- Origins evaluated: {result['origins_evaluated']}",
        "",
        "| Model | Horizon | Count | MAE | RMSE | Bias |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    metrics = result["metrics"]
    assert isinstance(metrics, dict)
    for model, by_horizon in metrics.items():
        assert isinstance(by_horizon, dict)
        for horizon, values in by_horizon.items():
            assert isinstance(values, dict)
            lines.append(
                f"| {model} | {horizon} | {values['count']} | {values['mae']} | {values['rmse']} | {values['bias']} |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backtest naive and seasonal-naive forecasts for a CSV time series."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date", required=True, help="Date/time/order column.")
    parser.add_argument("--target", required=True, help="Numeric target column.")
    parser.add_argument("--horizon", type=int, default=6)
    parser.add_argument("--seasonal-period", type=int, default=12)
    parser.add_argument(
        "--initial-window", type=int, help="Minimum observations before first forecast origin."
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    series = read_series(args.csv_path, args.date, args.target)
    if len(series) < args.horizon + 2:
        raise SystemExit("Not enough observations for the requested horizon.")
    initial_window = args.initial_window
    if initial_window is None:
        initial_window = max(1, min(len(series) - args.horizon, max(args.seasonal_period, len(series) // 2)))
    if initial_window < 1 or initial_window >= len(series):
        raise SystemExit("--initial-window must be at least 1 and less than the number of observations.")
    result = backtest(series, args.horizon, args.seasonal_period, initial_window)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown(result), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(markdown(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
