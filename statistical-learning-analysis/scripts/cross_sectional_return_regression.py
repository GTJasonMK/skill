#!/usr/bin/env python3
"""Run a cross-sectional return regression from asset-level rows.

Use this for a single rebalance date or as a quick pooled diagnostic.
For formal asset-pricing inference across many dates, use
``fama_macbeth_regression.py``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_utils import ols, read_dataframe, require_columns


def build_design(
    df: pd.DataFrame,
    return_col: str,
    feature_cols: list[str],
    date_col: str | None,
    date_value: str | None,
    intercept: bool,
) -> tuple[np.ndarray, np.ndarray, int, int]:
    rows_in = len(df)
    if date_col and date_value:
        skipped_by_date = int((df[date_col].astype(str) != date_value).sum())
        df = df[df[date_col].astype(str) == date_value]
    else:
        skipped_by_date = 0
    cols = [return_col] + feature_cols
    sub = df[cols].apply(lambda s: pd.to_numeric(s, errors="coerce"))
    rows_before_drop = len(sub)
    sub = sub.dropna()
    dropped_missing = rows_before_drop - len(sub)
    y = sub[return_col].to_numpy(dtype=float)
    feats = sub[feature_cols].to_numpy(dtype=float)
    if intercept:
        X = np.column_stack([np.ones(len(sub)), feats])
    else:
        X = feats
    return y, X, skipped_by_date, dropped_missing


def build_report(
    df: pd.DataFrame,
    return_col: str,
    feature_cols: list[str],
    date_col: str | None,
    date_value: str | None,
    intercept: bool,
    annualization: int,
) -> dict[str, Any]:
    y, X, skipped_by_date, dropped_missing = build_design(df, return_col, feature_cols, date_col, date_value, intercept)
    try:
        fit = ols(y, X)
    except ValueError as exc:
        raise SystemExit(f"Could not fit OLS: {exc}") from exc
    names = (["intercept"] if intercept else []) + feature_cols
    coefficient_table = []
    for name, coef, se, t_stat in zip(names, fit["coefficients"], fit["standard_errors_iid"], fit["t_stats_iid"]):
        row = {
            "name": name,
            "coefficient": coef,
            "standard_error_iid": se,
            "t_stat_iid": t_stat,
        }
        if name == "intercept":
            row["annualized_intercept_arithmetic"] = coef * annualization
        coefficient_table.append(row)
    return {
        "return_col": return_col,
        "feature_cols": feature_cols,
        "date_col": date_col,
        "date_filter": date_value,
        "intercept": intercept,
        "annualization": annualization,
        "n": fit["n"],
        "df_resid": fit["df_resid"],
        "rows_skipped_by_date": skipped_by_date,
        "rows_dropped_missing": dropped_missing,
        "r2": fit["r2"],
        "adj_r2": fit["adj_r2"],
        "residual_std": fit["residual_std"],
        "coefficient_table": coefficient_table,
        "notes": [
            "This is an OLS cross-sectional diagnostic; t-stats are IID approximations.",
            "Use point-in-time features and returns aligned to the intended future horizon.",
            "For repeated cross-sections, prefer Fama-MacBeth or panel methods with clustered/HAC errors.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Cross-Sectional Return Regression",
        "",
        f"- Return column: {report['return_col']}",
        f"- Features: {', '.join(report['feature_cols'])}",
        f"- Date filter: {report['date_filter'] or 'None'}",
        f"- Observations: {report['n']}",
        f"- Rows dropped missing: {report['rows_dropped_missing']}",
        f"- R-squared: {report['r2']}",
        f"- Adjusted R-squared: {report['adj_r2']}",
        "",
        "| Term | Coefficient | Std. error (IID) | t-stat (IID) | Annualized intercept |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["coefficient_table"]:
        lines.append(
            f"| {row['name']} | {row['coefficient']} | {row['standard_error_iid']} | {row['t_stat_iid']} | {row.get('annualized_intercept_arithmetic', '')} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a cross-sectional return regression from asset-level rows.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--return-col", required=True)
    parser.add_argument("--feature-cols", required=True, help="Comma-separated feature/exposure columns.")
    parser.add_argument("--date-col")
    parser.add_argument("--date", help="Optional date value to filter before fitting.")
    parser.add_argument("--no-intercept", action="store_true")
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    feature_cols = [col.strip() for col in args.feature_cols.split(",") if col.strip()]
    if not feature_cols:
        raise SystemExit("--feature-cols must include at least one column.")
    df = read_dataframe(args.csv_path)
    require_columns(df, [args.return_col] + feature_cols + ([args.date_col] if args.date_col else []))
    report = build_report(df, args.return_col, feature_cols, args.date_col, args.date, not args.no_intercept, args.annualization)
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
