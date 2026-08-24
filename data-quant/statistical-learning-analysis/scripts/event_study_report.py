#!/usr/bin/env python3
"""Compute simple event-study abnormal return diagnostics from a long CSV.

Requires the shared bundle core dependencies. Input should contain one row per asset-date return and
an event flag column. Abnormal returns are benchmark-adjusted when a benchmark
return column is supplied; otherwise they are mean-adjusted from a pre-event
estimation window.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import (
    is_missing,
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


FALSE_VALUES = {"0", "false", "f", "no", "n"}


def is_event(value: str | None) -> bool:
    if is_missing(value):
        return False
    return str(value).strip().lower() not in FALSE_VALUES


def estimate_expected_return(
    asset_rows: list[dict[str, Any]],
    event_index: int,
    estimation_window: int,
    estimation_gap: int,
    benchmark_return_col: str | None,
) -> float | None:
    end = max(0, event_index - estimation_gap)
    start = max(0, end - estimation_window)
    estimation_rows = asset_rows[start:end]
    if not estimation_rows:
        return None
    if benchmark_return_col:
        return 0.0
    return mean([row["return"] for row in estimation_rows])


def build_report(
    rows: list[dict[str, str]],
    date_col: str,
    asset_col: str,
    return_col: str,
    event_col: str,
    benchmark_return_col: str | None,
    pre_window: int,
    post_window: int,
    estimation_window: int,
    estimation_gap: int,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    dropped = 0
    for row in rows:
        date = row.get(date_col, "")
        asset = row.get(asset_col, "")
        ret = parse_float(row.get(return_col))
        bench = parse_float(row.get(benchmark_return_col)) if benchmark_return_col else None
        if not date or not asset or ret is None or (benchmark_return_col and bench is None):
            dropped += 1
            continue
        grouped.setdefault(asset, []).append(
            {
                "date": date,
                "return": ret,
                "benchmark_return": bench,
                "event": is_event(row.get(event_col)),
            }
        )
    for asset in grouped:
        grouped[asset].sort(key=lambda item: item["date"])

    events = []
    abnormal_by_offset: dict[int, list[float]] = {
        offset: [] for offset in range(-pre_window, post_window + 1)
    }
    skipped_events = 0
    for asset in sorted_group_keys(list(grouped)):
        asset_rows = grouped[asset]
        for event_index, item in enumerate(asset_rows):
            if not item["event"]:
                continue
            expected = estimate_expected_return(
                asset_rows, event_index, estimation_window, estimation_gap, benchmark_return_col
            )
            if expected is None:
                skipped_events += 1
                continue
            ar_path = []
            car = 0.0
            complete = True
            for offset in range(-pre_window, post_window + 1):
                idx = event_index + offset
                if idx < 0 or idx >= len(asset_rows):
                    complete = False
                    continue
                obs = asset_rows[idx]
                abnormal = (
                    obs["return"] - obs["benchmark_return"]
                    if benchmark_return_col
                    else obs["return"] - expected
                )
                car += abnormal
                abnormal_by_offset[offset].append(abnormal)
                ar_path.append(
                    {"offset": offset, "date": obs["date"], "abnormal_return": abnormal, "car_to_offset": car}
                )
            events.append(
                {
                    "asset": asset,
                    "event_date": item["date"],
                    "complete_window": complete,
                    "expected_return": expected,
                    "car": car,
                    "path": ar_path,
                }
            )
    aggregate_path = []
    for offset in range(-pre_window, post_window + 1):
        values = abnormal_by_offset[offset]
        summary = summarize_values(values)
        aggregate_path.append({"offset": offset, **summary})
    car_values = [event["car"] for event in events]
    complete_car_values = [event["car"] for event in events if event["complete_window"]]
    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "return_col": return_col,
        "event_col": event_col,
        "benchmark_return_col": benchmark_return_col,
        "pre_window": pre_window,
        "post_window": post_window,
        "estimation_window": estimation_window,
        "estimation_gap": estimation_gap,
        "rows_dropped": dropped,
        "events_used": len(events),
        "events_skipped": skipped_events,
        "complete_events": sum(event["complete_window"] for event in events),
        "car_summary": summarize_values(car_values),
        "complete_window_car_summary": summarize_values(complete_car_values),
        "aggregate_abnormal_returns": aggregate_path,
        "events": events,
        "notes": [
            "With --benchmark-return-col, abnormal return is asset return minus benchmark return.",
            "Without a benchmark, expected return is the asset's mean return from the "
            "pre-event estimation window.",
            "Check overlapping events, event-time leakage, confounding news, clustering, "
            "and multiple testing before making claims.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    car = report["car_summary"]
    complete = report["complete_window_car_summary"]
    lines = [
        "# Event Study Report",
        "",
        f"- Return column: {report['return_col']}",
        f"- Event column: {report['event_col']}",
        f"- Window: {report['pre_window']} before to {report['post_window']} after",
        f"- Events used: {report['events_used']}",
        f"- Complete-window events: {report['complete_events']}",
        f"- Rows dropped: {report['rows_dropped']}",
        "",
        "| CAR set | N | Mean CAR | Stdev | t-stat | Positive rate | Min | Max |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| All events | {car['n']} | {car['mean']} | {car['stdev']} | "
        f"{car['t_stat']} | {car['positive_rate']} | {car['min']} | {car['max']} |",
        f"| Complete windows | {complete['n']} | {complete['mean']} | "
        f"{complete['stdev']} | {complete['t_stat']} | "
        f"{complete['positive_rate']} | {complete['min']} | {complete['max']} |",
        "",
        "## Average Abnormal Return by Offset",
        "",
        "| Offset | N | Mean AR | t-stat | Positive rate |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["aggregate_abnormal_returns"]:
        lines.append(
            f"| {item['offset']} | {item['n']} | {item['mean']} | "
            f"{item['t_stat']} | {item['positive_rate']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute simple event-study abnormal return diagnostics from a long CSV."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--return-col", required=True)
    parser.add_argument("--event-col", required=True)
    parser.add_argument("--benchmark-return-col")
    parser.add_argument("--pre-window", type=int, default=5)
    parser.add_argument("--post-window", type=int, default=5)
    parser.add_argument("--estimation-window", type=int, default=60)
    parser.add_argument("--estimation-gap", type=int, default=1)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.pre_window < 0 or args.post_window < 0:
        raise SystemExit("--pre-window and --post-window must be non-negative.")
    if args.estimation_window < 1:
        raise SystemExit("--estimation-window must be at least 1.")
    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    require_columns(
        header,
        [args.date_col, args.asset_col, args.return_col, args.event_col]
        + ([args.benchmark_return_col] if args.benchmark_return_col else []),
    )
    report = build_report(
        rows,
        args.date_col,
        args.asset_col,
        args.return_col,
        args.event_col,
        args.benchmark_return_col,
        args.pre_window,
        args.post_window,
        args.estimation_window,
        args.estimation_gap,
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
