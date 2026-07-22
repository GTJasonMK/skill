#!/usr/bin/env python3
"""Summarize risk, portfolio, and operations limit breaches.

Standard-library only. Input is a metric CSV with date, metric, observed value,
limit value, and optional direction/severity/owner columns.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from quant_utils import parse_float, read_dataframe, require_columns, sorted_group_keys, summarize_values

import pandas as pd


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")




SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def normalize_severity(value: str) -> str:
    clean = value.strip().lower()
    return clean if clean in SEVERITY_ORDER else "medium"


def normalize_direction(value: str) -> str:
    clean = value.strip().lower().replace(" ", "_")
    aliases = {
        "upper": "upper",
        "<=": "upper",
        "max": "upper",
        "lower": "lower",
        ">=": "lower",
        "min": "lower",
        "abs_upper": "abs_upper",
        "abs": "abs_upper",
        "absolute": "abs_upper",
    }
    return aliases.get(clean, "upper")


def is_breach(value: float, limit: float, direction: str) -> bool:
    if direction == "upper":
        return value > limit
    if direction == "lower":
        return value < limit
    if direction == "abs_upper":
        return abs(value) > limit
    return value > limit


def breach_margin(value: float, limit: float, direction: str) -> float:
    if direction == "upper":
        return value - limit
    if direction == "lower":
        return limit - value
    if direction == "abs_upper":
        return abs(value) - limit
    return value - limit


def max_consecutive_breaches(items: list[dict[str, Any]]) -> int:
    best = 0
    current = 0
    for item in sorted(items, key=lambda row: row["date"]):
        if item["is_breach"]:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def build_report(
    rows: list[dict[str, str]],
    date_col: str,
    metric_col: str,
    value_col: str,
    limit_col: str,
    direction_col: str | None,
    severity_col: str | None,
    owner_col: str | None,
    strategy_col: str | None,
    block_severities: set[str],
) -> dict[str, Any]:
    records = []
    dropped = 0
    for i, row in enumerate(rows, start=1):
        date = row.get(date_col, "")
        metric = row.get(metric_col, "").strip()
        value = parse_float(row.get(value_col))
        limit = parse_float(row.get(limit_col))
        direction = normalize_direction(row.get(direction_col, "")) if direction_col else "upper"
        severity = normalize_severity(row.get(severity_col, "")) if severity_col else "medium"
        owner = row.get(owner_col, "").strip() if owner_col else ""
        strategy = row.get(strategy_col, "").strip() if strategy_col else ""
        if not date or not metric or value is None or limit is None:
            dropped += 1
            continue
        breached = is_breach(value, limit, direction)
        margin = breach_margin(value, limit, direction)
        records.append(
            {
                "row_number": i,
                "date": date,
                "metric": metric,
                "value": value,
                "limit": limit,
                "direction": direction,
                "severity": severity,
                "owner": owner,
                "strategy": strategy,
                "is_breach": breached,
                "breach_margin": margin,
                "breach_ratio": margin / abs(limit) if limit != 0 else None,
                "is_blocker": breached and severity in block_severities,
            }
        )

    by_metric: dict[str, list[dict[str, Any]]] = {}
    by_date: dict[str, list[dict[str, Any]]] = {}
    by_severity: dict[str, list[dict[str, Any]]] = {}
    by_strategy: dict[str, list[dict[str, Any]]] = {}
    for item in records:
        by_metric.setdefault(item["metric"], []).append(item)
        by_date.setdefault(item["date"], []).append(item)
        by_severity.setdefault(item["severity"], []).append(item)
        if item["strategy"]:
            by_strategy.setdefault(item["strategy"], []).append(item)

    breaches = [item for item in records if item["is_breach"]]
    blockers = [item for item in records if item["is_blocker"]]
    metric_summary = {}
    for metric, items in sorted(by_metric.items()):
        metric_breaches = [item for item in items if item["is_breach"]]
        margins = [item["breach_margin"] for item in metric_breaches]
        metric_summary[metric] = {
            "observations": len(items),
            "breach_count": len(metric_breaches),
            "breach_rate": len(metric_breaches) / len(items) if items else None,
            "max_consecutive_breaches": max_consecutive_breaches(items),
            "breach_margin_summary": summarize_values(margins),
        }

    return {
        "date_col": date_col,
        "metric_col": metric_col,
        "value_col": value_col,
        "limit_col": limit_col,
        "direction_col": direction_col,
        "severity_col": severity_col,
        "owner_col": owner_col,
        "strategy_col": strategy_col,
        "block_severities": sorted(block_severities, key=lambda item: -SEVERITY_ORDER.get(item, 0)),
        "rows_used": len(records),
        "rows_dropped": dropped,
        "breach_count": len(breaches),
        "blocker_count": len(blockers),
        "gate_decision": "fail" if blockers else ("warn" if breaches else "pass"),
        "metric_summary": metric_summary,
        "date_breach_counts": {date: sum(item["is_breach"] for item in by_date[date]) for date in sorted_group_keys(list(by_date))},
        "severity_breach_counts": {severity: sum(item["is_breach"] for item in items) for severity, items in sorted(by_severity.items())},
        "strategy_breach_counts": {strategy: sum(item["is_breach"] for item in items) for strategy, items in sorted(by_strategy.items())},
        "blockers": blockers,
        "breaches": breaches,
        "records": records,
        "notes": [
            "Direction upper means value must be <= limit; lower means value must be >= limit; abs_upper means abs(value) must be <= limit.",
            "Critical or high breaches usually require de-risking, capital reduction, or trading pause depending on the mandate.",
            "Pair this report with go_live_gate_report.py so unresolved limit breaches can block promotion or scaling.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Limit Breach Report",
        "",
        f"- Gate decision: {report['gate_decision']}",
        f"- Rows used: {report['rows_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        f"- Breaches: {report['breach_count']}",
        f"- Blockers: {report['blocker_count']}",
        "",
        "## Metric Summary",
        "",
        "| Metric | Observations | Breaches | Breach rate | Max consecutive breaches |",
        "| --- | --- | --- | --- | --- |",
    ]
    for metric, item in report["metric_summary"].items():
        lines.append(f"| {metric} | {item['observations']} | {item['breach_count']} | {item['breach_rate']} | {item['max_consecutive_breaches']} |")
    lines.extend(["", "## Blockers", "", "| Date | Metric | Value | Limit | Direction | Severity | Owner |", "| --- | --- | --- | --- | --- | --- | --- |"])
    for item in report["blockers"]:
        lines.append(f"| {item['date']} | {item['metric']} | {item['value']} | {item['limit']} | {item['direction']} | {item['severity']} | {item['owner']} |")
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize risk, portfolio, and operations limit breaches.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--metric-col", required=True)
    parser.add_argument("--value-col", required=True)
    parser.add_argument("--limit-col", required=True)
    parser.add_argument("--direction-col")
    parser.add_argument("--severity-col")
    parser.add_argument("--owner-col")
    parser.add_argument("--strategy-col")
    parser.add_argument("--block-severities", default="critical,high")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    df = read_dataframe(args.csv_path)

    header, rows = _df_to_rows(df)
    optional = [col for col in [args.direction_col, args.severity_col, args.owner_col, args.strategy_col] if col]
    require_columns(header, [args.date_col, args.metric_col, args.value_col, args.limit_col] + optional)
    block_severities = {normalize_severity(item) for item in args.block_severities.split(",") if item.strip()}
    report = build_report(
        rows,
        args.date_col,
        args.metric_col,
        args.value_col,
        args.limit_col,
        args.direction_col,
        args.severity_col,
        args.owner_col,
        args.strategy_col,
        block_severities,
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
