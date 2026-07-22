#!/usr/bin/env python3
"""Check data freshness, row-count, and missingness health by dataset.

Standard-library only. Input is a dataset monitoring CSV with dataset name,
latest timestamp, and optional expected max age, row count, and missing count.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from quant_utils import parse_float, read_dataframe, require_columns, sorted_group_keys

import pandas as pd


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")




def parse_timestamp(value: str) -> datetime | None:
    clean = value.strip()
    if not clean:
        return None
    if clean.endswith("Z"):
        clean = clean[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(clean)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def current_time(value: str | None) -> datetime:
    if value:
        parsed = parse_timestamp(value)
        if parsed is None:
            raise SystemExit("--current-time must be ISO-8601 compatible.")
        return parsed
    return datetime.now(timezone.utc)


def build_report(
    rows: list[dict[str, str]],
    dataset_col: str,
    timestamp_col: str,
    max_age_minutes_col: str | None,
    row_count_col: str | None,
    missing_count_col: str | None,
    status_col: str | None,
    default_max_age_minutes: float,
    min_row_count: float,
    max_missing_rate: float,
    now: datetime,
) -> dict[str, Any]:
    checks = []
    dropped = 0
    for row in rows:
        dataset = row.get(dataset_col, "").strip()
        timestamp = parse_timestamp(row.get(timestamp_col, ""))
        max_age_value = parse_float(row.get(max_age_minutes_col)) if max_age_minutes_col else None
        row_count = parse_float(row.get(row_count_col)) if row_count_col else None
        missing_count = parse_float(row.get(missing_count_col)) if missing_count_col else None
        upstream_status = row.get(status_col, "").strip().lower() if status_col else ""
        if not dataset:
            dropped += 1
            continue
        max_age = max_age_value if max_age_value is not None and max_age_value > 0 else default_max_age_minutes
        age_minutes = (now - timestamp).total_seconds() / 60 if timestamp is not None else None
        missing_rate = missing_count / row_count if missing_count is not None and row_count not in {None, 0} else None
        issues = []
        if timestamp is None:
            issues.append("missing_or_invalid_timestamp")
        elif age_minutes is not None and age_minutes > max_age:
            issues.append("stale")
        elif age_minutes is not None and age_minutes < -1:
            issues.append("future_timestamp")
        if row_count is not None and row_count < min_row_count:
            issues.append("low_row_count")
        if missing_rate is not None and missing_rate > max_missing_rate:
            issues.append("high_missing_rate")
        if upstream_status and upstream_status not in {"ok", "pass", "green", "healthy"}:
            issues.append("upstream_status_not_ok")
        checks.append(
            {
                "dataset": dataset,
                "timestamp": timestamp.isoformat() if timestamp is not None else None,
                "age_minutes": age_minutes,
                "max_age_minutes": max_age,
                "row_count": row_count,
                "missing_count": missing_count,
                "missing_rate": missing_rate,
                "upstream_status": upstream_status,
                "is_fresh": not issues,
                "issues": issues,
            }
        )

    issue_counts: dict[str, int] = {}
    for item in checks:
        for issue in item["issues"]:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
    stale = [item for item in checks if item["issues"]]
    return {
        "dataset_col": dataset_col,
        "timestamp_col": timestamp_col,
        "max_age_minutes_col": max_age_minutes_col,
        "row_count_col": row_count_col,
        "missing_count_col": missing_count_col,
        "status_col": status_col,
        "default_max_age_minutes": default_max_age_minutes,
        "min_row_count": min_row_count,
        "max_missing_rate": max_missing_rate,
        "current_time_utc": now.isoformat(),
        "rows_used": len(checks),
        "rows_dropped": dropped,
        "fresh_count": sum(item["is_fresh"] for item in checks),
        "problem_count": len(stale),
        "issue_counts": issue_counts,
        "checks": sorted(checks, key=lambda item: item["dataset"]),
        "problem_checks": sorted(stale, key=lambda item: item["dataset"]),
        "notes": [
            "Naive timestamps are treated as UTC; pass timezone-aware ISO timestamps when possible.",
            "Freshness checks should run before signal generation and portfolio construction.",
            "A fresh timestamp does not prove the data is correct; pair this with missingness and reconciliation checks.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Data Freshness Report",
        "",
        f"- Current time UTC: {report['current_time_utc']}",
        f"- Rows used: {report['rows_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        f"- Fresh datasets: {report['fresh_count']}",
        f"- Problem datasets: {report['problem_count']}",
        "",
        "## Issue Counts",
        "",
    ]
    if report["issue_counts"]:
        for issue, count in sorted(report["issue_counts"].items()):
            lines.append(f"- {issue}: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Dataset Checks", "", "| Dataset | Age minutes | Max age | Row count | Missing rate | Status | Issues |", "| --- | --- | --- | --- | --- | --- | --- |"])
    for item in report["checks"]:
        lines.append(f"| {item['dataset']} | {item['age_minutes']} | {item['max_age_minutes']} | {item['row_count']} | {item['missing_rate']} | {item['upstream_status']} | {', '.join(item['issues']) if item['issues'] else 'none'} |")
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check data freshness, row-count, and missingness health by dataset.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--dataset-col", required=True)
    parser.add_argument("--timestamp-col", required=True)
    parser.add_argument("--max-age-minutes-col")
    parser.add_argument("--row-count-col")
    parser.add_argument("--missing-count-col")
    parser.add_argument("--status-col")
    parser.add_argument("--default-max-age-minutes", type=float, default=1440.0)
    parser.add_argument("--min-row-count", type=float, default=1.0)
    parser.add_argument("--max-missing-rate", type=float, default=0.05)
    parser.add_argument("--current-time")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.default_max_age_minutes <= 0:
        raise SystemExit("--default-max-age-minutes must be positive.")
    if args.min_row_count < 0:
        raise SystemExit("--min-row-count must be non-negative.")
    if not 0 <= args.max_missing_rate <= 1:
        raise SystemExit("--max-missing-rate must be in [0, 1].")
    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    optional = [col for col in [args.max_age_minutes_col, args.row_count_col, args.missing_count_col, args.status_col] if col]
    require_columns(header, [args.dataset_col, args.timestamp_col] + optional)
    report = build_report(
        rows,
        args.dataset_col,
        args.timestamp_col,
        args.max_age_minutes_col,
        args.row_count_col,
        args.missing_count_col,
        args.status_col,
        args.default_max_age_minutes,
        args.min_row_count,
        args.max_missing_rate,
        current_time(args.current_time),
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
