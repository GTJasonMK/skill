#!/usr/bin/env python3
"""Lightweight CSV profiler for statistical-learning task triage.

This script intentionally uses only the Python standard library so it can run in
minimal environments. It does not replace EDA; it produces first-pass signals
for method selection, validation design, and leakage risk.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import math
import re
import statistics
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

MISSING = {"", "na", "n/a", "nan", "null", "none", "."}
BOOL_TRUE = {"true", "t", "yes", "y", "1"}
BOOL_FALSE = {"false", "f", "no", "n", "0"}
DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m",
    "%Y",
)


def is_missing(value: str | None) -> bool:
    return value is None or value.strip().lower() in MISSING


def clean(value: str | None) -> str:
    return "" if value is None else value.strip()


def parse_float(value: str) -> float | None:
    value = clean(value).replace(",", "")
    if is_missing(value):
        return None
    try:
        out = float(value)
    except ValueError:
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def parse_int(value: str) -> int | None:
    value = clean(value).replace(",", "")
    if not re.fullmatch(r"[-+]?\d+", value):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_bool(value: str) -> bool | None:
    value = clean(value).lower()
    if value in BOOL_TRUE:
        return True
    if value in BOOL_FALSE:
        return False
    return None


def parse_date(value: str) -> str | None:
    value = clean(value)
    if is_missing(value):
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        pass
    for fmt in DATE_FORMATS:
        try:
            return dt.datetime.strptime(value, fmt).isoformat()
        except ValueError:
            continue
    return None


def read_csv(path: Path, max_rows: int) -> tuple[list[str], list[dict[str, str]], int, bool]:
    rows: list[dict[str, str]] = []
    total_rows = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        if handle.seekable():
            sample = handle.read(4096)
            handle.seek(0)
            source: Iterable[str] = handle
        else:
            text = handle.read()
            sample = text[:4096]
            source = io.StringIO(text)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(source, dialect=dialect)
        header = list(reader.fieldnames or [])
        for row in reader:
            total_rows += 1
            if len(rows) < max_rows:
                rows.append({name: clean(row.get(name)) for name in header})
    return header, rows, total_rows, total_rows > len(rows)


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[int(pos)]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def infer_type(non_missing: list[str], unique_count: int, n: int) -> str:
    if not non_missing:
        return "empty"
    bool_count = sum(parse_bool(v) is not None for v in non_missing)
    int_count = sum(parse_int(v) is not None for v in non_missing)
    float_count = sum(parse_float(v) is not None for v in non_missing)
    date_count = sum(parse_date(v) is not None for v in non_missing)
    avg_len = statistics.mean(len(v) for v in non_missing)

    if bool_count / len(non_missing) >= 0.95 and unique_count <= 2:
        return "boolean"
    if int_count / len(non_missing) >= 0.95:
        if unique_count <= min(20, max(2, int(0.05 * n))):
            return "categorical_integer"
        return "integer"
    if float_count / len(non_missing) >= 0.95:
        return "numeric"
    if date_count / len(non_missing) >= 0.85:
        return "datetime"
    if unique_count <= min(50, max(2, int(0.2 * n))):
        return "categorical"
    if avg_len > 80:
        return "text"
    return "high_cardinality_text"


def profile_column(name: str, values: list[str]) -> dict[str, Any]:
    n = len(values)
    missing_count = sum(is_missing(v) for v in values)
    non_missing = [v for v in values if not is_missing(v)]
    counts = Counter(non_missing)
    unique_count = len(counts)
    inferred = infer_type(non_missing, unique_count, max(n, 1))
    result: dict[str, Any] = {
        "name": name,
        "inferred_type": inferred,
        "missing_count": missing_count,
        "missing_rate": round(missing_count / n, 4) if n else None,
        "unique_count": unique_count,
        "unique_rate": round(unique_count / len(non_missing), 4) if non_missing else None,
        "examples": [v for v, _ in counts.most_common(3)],
    }

    numeric_values = [parse_float(v) for v in non_missing]
    numeric_values = [v for v in numeric_values if v is not None]
    if inferred in {"integer", "numeric", "categorical_integer"} and numeric_values:
        result["numeric_summary"] = {
            "min": min(numeric_values),
            "p25": quantile(numeric_values, 0.25),
            "median": quantile(numeric_values, 0.5),
            "mean": statistics.mean(numeric_values),
            "p75": quantile(numeric_values, 0.75),
            "max": max(numeric_values),
            "stdev": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0.0,
        }
    if inferred in {"boolean", "categorical", "categorical_integer", "high_cardinality_text"}:
        result["top_values"] = [{"value": v, "count": c} for v, c in counts.most_common(5)]
    if inferred == "datetime":
        parsed_dates = [parse_date(v) for v in non_missing]
        parsed_dates = [v for v in parsed_dates if v is not None]
        if parsed_dates:
            result["datetime_summary"] = {"min": min(parsed_dates), "max": max(parsed_dates)}
    return result


def likely_id_column(column: dict[str, Any], row_count: int) -> bool:
    name = column["name"].lower()
    unique_rate = column.get("unique_rate") or 0
    if name in {"id", "uuid", "guid"} or name.endswith("_id") or name.endswith("id"):
        return True
    return (
        row_count >= 20
        and unique_rate >= 0.98
        and column["inferred_type"] not in {"numeric", "integer", "categorical_integer", "datetime"}
    )


def build_profile(
    path: Path, target: str | None, group: str | None, time: str | None, max_rows: int
) -> dict[str, Any]:
    header, rows, total_rows, truncated = read_csv(path, max_rows)
    sample_rows = len(rows)
    values_by_col = {name: [row.get(name, "") for row in rows] for name in header}
    columns = [profile_column(name, values_by_col[name]) for name in header]
    duplicate_count = 0
    if rows:
        row_tuples = [tuple(row.get(name, "") for name in header) for row in rows]
        duplicate_count = len(row_tuples) - len(set(row_tuples))

    warnings: list[str] = []
    if not header:
        warnings.append("No header detected.")
    if not rows:
        warnings.append("No data rows sampled.")
    if truncated:
        warnings.append(
            f"Profile uses first {sample_rows} rows out of {total_rows}; rerun with higher --max-rows if needed."
        )
    if sample_rows and len(header) > sample_rows and (len(header) > 100 or len(header) / sample_rows > 2):
        warnings.append(
            "p > n in sampled data; prefer regularization, dimension reduction inside CV, and nested validation."
        )
    if sample_rows and duplicate_count / sample_rows > 0.01:
        warnings.append("Duplicate rows exceed 1% of sampled data; check data extraction and split leakage.")

    constant_cols = [c["name"] for c in columns if c.get("unique_count") == 1]
    high_missing_cols = [c["name"] for c in columns if (c.get("missing_rate") or 0) >= 0.4]
    id_like_cols = [c["name"] for c in columns if likely_id_column(c, sample_rows)]
    possible_time_cols = [
        c["name"]
        for c in columns
        if c["inferred_type"] == "datetime" or "date" in c["name"].lower() or "time" in c["name"].lower()
    ]
    possible_group_cols = [
        c["name"]
        for c in columns
        if c["inferred_type"] in {"categorical", "categorical_integer", "high_cardinality_text"}
        and 2 <= (c.get("unique_count") or 0) <= max(2, min(1000, sample_rows // 2 if sample_rows else 0))
        and c["name"] not in id_like_cols
    ]
    if constant_cols:
        warnings.append(f"Constant columns: {', '.join(constant_cols[:10])}.")
    if high_missing_cols:
        warnings.append(f"High-missing columns (>=40%): {', '.join(high_missing_cols[:10])}.")
    if id_like_cols:
        warnings.append(
            f"ID-like columns: {', '.join(id_like_cols[:10])}; do not use as ordinary predictive features."
        )
    if possible_time_cols and not time:
        warnings.append(
            f"Possible time columns detected: {', '.join(possible_time_cols[:10])}; use time-aware splits if prediction time matters."
        )
    if possible_group_cols and not group:
        warnings.append(
            f"Possible group columns detected: {', '.join(possible_group_cols[:10])}; consider group-aware validation if rows repeat entities."
        )

    target_profile = None
    if target:
        if target not in values_by_col:
            warnings.append(f"Target column '{target}' was not found.")
        else:
            target_profile = profile_column(target, values_by_col[target])
            if (target_profile.get("missing_rate") or 0) > 0:
                warnings.append(
                    f"Target column '{target}' has missing values; define eligibility before modeling."
                )
            target_type = target_profile["inferred_type"]
            if target_type in {"boolean", "categorical", "categorical_integer"}:
                counts = target_profile.get("top_values", [])
                total = sum(item["count"] for item in counts)
                if total:
                    min_rate = min(item["count"] for item in counts) / sample_rows if sample_rows else 0
                    if min_rate < 0.05:
                        warnings.append(
                            "Target appears imbalanced; avoid accuracy-only evaluation and tune thresholds on validation data."
                        )
            if likely_id_column(target_profile, sample_rows):
                warnings.append(f"Target column '{target}' looks ID-like; verify it is a real outcome.")

    return {
        "path": str(path),
        "row_count": total_rows,
        "sampled_rows": sample_rows,
        "truncated": truncated,
        "column_count": len(header),
        "duplicate_rows_in_sample": duplicate_count,
        "target": target,
        "group": group,
        "time": time,
        "columns": columns,
        "target_profile": target_profile,
        "risk_flags": {
            "constant_columns": constant_cols,
            "high_missing_columns": high_missing_cols,
            "id_like_columns": id_like_cols,
            "possible_time_columns": possible_time_cols,
            "possible_group_columns": possible_group_cols,
        },
        "warnings": warnings,
        "next_steps": suggest_next_steps(target_profile, possible_time_cols, possible_group_cols, warnings),
    }


def suggest_next_steps(
    target_profile: dict[str, Any] | None, time_cols: list[str], group_cols: list[str], warnings: list[str]
) -> list[str]:
    steps = []
    if target_profile is None:
        steps.append(
            "No target was profiled; route to unsupervised learning, anomaly detection, or ask for the target variable."
        )
    else:
        target_type = target_profile["inferred_type"]
        if target_type in {"numeric", "integer"}:
            steps.append(
                "For a continuous target, compare naive/linear baselines with regularized regression and tree ensembles."
            )
        elif target_type in {"boolean", "categorical", "categorical_integer"}:
            steps.append(
                "For a categorical target, start with logistic/penalized logistic baselines and choose metrics before tuning."
            )
        elif target_type == "datetime":
            steps.append(
                "Target appears time-like; verify whether this is survival/time-to-event or forecasting."
            )
        else:
            steps.append("Target type is unusual; define the outcome carefully before selecting a method.")
    if time_cols:
        steps.append("If observations are time ordered, use blocked or rolling-origin validation.")
    if group_cols:
        steps.append("If rows repeat entities, use group-aware validation or clustered/mixed/panel methods.")
    if any("p > n" in warning for warning in warnings):
        steps.append("Use regularization and perform all feature screening inside cross-validation.")
    return steps


def to_markdown(profile: dict[str, Any]) -> str:
    lines = [
        "# Dataset Profile",
        "",
        f"- Rows: {profile['row_count']} (sampled {profile['sampled_rows']})",
        f"- Columns: {profile['column_count']}",
        f"- Duplicate rows in sample: {profile['duplicate_rows_in_sample']}",
    ]
    if profile["target"]:
        lines.append(f"- Target: {profile['target']}")
    lines.extend(["", "## Warnings"])
    if profile["warnings"]:
        lines.extend(f"- {warning}" for warning in profile["warnings"])
    else:
        lines.append("- None detected in the sampled data.")
    lines.extend(["", "## Next Steps"])
    lines.extend(f"- {step}" for step in profile["next_steps"])
    lines.extend(
        [
            "",
            "## Columns",
            "",
            "| Column | Type | Missing | Unique | Examples |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for col in profile["columns"]:
        missing = col["missing_rate"]
        unique = col["unique_count"]
        examples = ", ".join(map(str, col.get("examples", [])))
        lines.append(f"| {col['name']} | {col['inferred_type']} | {missing} | {unique} | {examples} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile a CSV for statistical-learning method selection.")
    parser.add_argument("csv_path", type=Path, help="Path to a CSV file.")
    parser.add_argument("--target", help="Optional target/outcome column.")
    parser.add_argument("--group", help="Optional group/entity column.")
    parser.add_argument("--time", help="Optional time/order column.")
    parser.add_argument(
        "--max-rows", type=int, default=50000, help="Maximum rows to store/profile in detail."
    )
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown", help="Output format.")
    args = parser.parse_args()

    profile = build_profile(args.csv_path, args.target, args.group, args.time, args.max_rows)
    if args.format == "json":
        print(json.dumps(profile, ensure_ascii=False, indent=2))
    else:
        print(to_markdown(profile), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
