#!/usr/bin/env python3
"""Summarize missingness patterns in a CSV file.

Standard-library only. Useful before imputation and to identify columns or rows
that may need special treatment.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

MISSING = {"", "na", "n/a", "nan", "null", "none", "."}


def is_missing(value: str | None) -> bool:
    return value is None or value.strip().lower() in MISSING


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]], csv.Dialect]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(handle, dialect=dialect)
        header = list(reader.fieldnames or [])
        rows = [{name: row.get(name, "") for name in header} for row in reader]
    return header, rows, dialect


def summarize(
    rows: list[dict[str, str]], header: list[str], row_threshold: float, col_threshold: float
) -> dict[str, object]:
    n = len(rows)
    column_stats = []
    row_missing_counts = []
    for row in rows:
        missing_count = sum(is_missing(row.get(col, "")) for col in header)
        row_missing_counts.append(missing_count)
    for col in header:
        missing_count = sum(is_missing(row.get(col, "")) for row in rows)
        rate = missing_count / n if n else None
        column_stats.append(
            {
                "column": col,
                "missing_count": missing_count,
                "missing_rate": rate,
                "flag_row_threshold": bool(rate is not None and rate >= col_threshold),
            }
        )
    patterns = Counter(tuple("1" if is_missing(row.get(col, "")) else "0" for col in header) for row in rows)
    top_patterns = [
        {"pattern": "".join(pattern), "count": count, "rate": count / n if n else None}
        for pattern, count in patterns.most_common(10)
    ]
    return {
        "rows": n,
        "columns": len(header),
        "column_stats": column_stats,
        "row_missing_counts": row_missing_counts,
        "rows_with_any_missing": sum(count > 0 for count in row_missing_counts),
        "rows_with_high_missing": sum(count / len(header) >= row_threshold for count in row_missing_counts)
        if header
        else 0,
        "top_missing_patterns": top_patterns,
        "high_missing_columns": [item["column"] for item in column_stats if item["flag_row_threshold"]],
    }


def markdown(report: dict[str, object]) -> str:
    lines = [
        "# Missingness Report",
        "",
        f"- Rows: {report['rows']}",
        f"- Columns: {report['columns']}",
        f"- Rows with any missing values: {report['rows_with_any_missing']}",
        f"- Rows with high missingness: {report['rows_with_high_missing']}",
        "",
        "## Columns",
        "",
        "| Column | Missing count | Missing rate | Flag |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["column_stats"]:
        lines.append(
            f"| {item['column']} | {item['missing_count']} | {item['missing_rate']} | {item['flag_row_threshold']} |"
        )
    lines.extend(["", "## Top Missingness Patterns", "", "| Pattern | Count | Rate |", "| --- | --- | --- |"])
    for item in report["top_missing_patterns"]:
        lines.append(f"| {item['pattern']} | {item['count']} | {item['rate']} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize missingness in a CSV.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--row-threshold", type=float, default=0.5, help="Flag rows with missing rate above this threshold."
    )
    parser.add_argument(
        "--col-threshold",
        type=float,
        default=0.4,
        help="Flag columns with missing rate above this threshold.",
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    header, rows, _ = read_csv(args.csv_path)
    report = summarize(rows, header, args.row_threshold, args.col_threshold)
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
