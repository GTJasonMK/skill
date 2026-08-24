#!/usr/bin/env python3
"""Run Fama-MacBeth cross-sectional regressions by date.

Each date gets a cross-sectional OLS regression of future returns on
characteristics/exposures; risk premia are the time-series average of
date-level coefficients.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from quant_utils import ols, read_dataframe, require_columns, summarize_series


def date_regression(
    g: pd.DataFrame, return_col: str, feature_cols: list[str], intercept: bool
) -> tuple[dict[str, Any] | None, int]:
    cols = [return_col] + feature_cols
    sub = g[cols].apply(lambda s: pd.to_numeric(s, errors="coerce"))
    rows_in = len(sub)
    sub = sub.dropna()
    dropped = rows_in - len(sub)
    if sub.empty:
        return None, dropped
    y = sub[return_col].to_numpy(dtype=float)
    feats = sub[feature_cols].to_numpy(dtype=float)
    X = np.column_stack([np.ones(len(sub)), feats]) if intercept else feats
    try:
        return ols(y, X), dropped
    except ValueError:
        return None, dropped


def build_report(
    df: pd.DataFrame,
    date_col: str,
    return_col: str,
    feature_cols: list[str],
    min_assets: int,
    intercept: bool,
    annualization: int,
) -> dict[str, Any]:
    df = df[df[date_col].astype(str).str.len() > 0]
    names = (["intercept"] if intercept else []) + feature_cols
    by_date = []
    skipped_dates = 0
    total_dropped = 0
    for date, g in df.groupby(date_col, sort=True):
        if len(g) < min_assets:
            skipped_dates += 1
            continue
        fit, dropped = date_regression(g, return_col, feature_cols, intercept)
        total_dropped += dropped
        if fit is None or fit["n"] < min_assets:
            skipped_dates += 1
            continue
        coeffs = {name: coef for name, coef in zip(names, fit["coefficients"], strict=False)}
        by_date.append(
            {
                "date": date if not isinstance(date, pd.Timestamp) else date.isoformat(),
                "n": fit["n"],
                "r2": fit["r2"],
                "coefficients": coeffs,
            }
        )

    coefficient_summary = []
    for name in names:
        values = [item["coefficients"][name] for item in by_date if name in item["coefficients"]]
        summary = summarize_series(values)
        row = {"name": name, **summary}
        if name == "intercept":
            row["annualized_mean_arithmetic"] = (
                summary["mean"] * annualization if summary["mean"] is not None else None
            )
        coefficient_summary.append(row)
    r2_values = [item["r2"] for item in by_date if item["r2"] is not None]
    return {
        "date_col": date_col,
        "return_col": return_col,
        "feature_cols": feature_cols,
        "intercept": intercept,
        "annualization": annualization,
        "min_assets_per_date": min_assets,
        "dates_used": len(by_date),
        "dates_skipped": skipped_dates,
        "rows_dropped_missing": total_dropped,
        "coefficient_summary": coefficient_summary,
        "r2_summary": summarize_series(r2_values),
        "by_date": by_date,
        "notes": [
            "Fama-MacBeth t-stats here are simple time-series t-stats of date-level coefficients.",
            "Use point-in-time characteristics and forward returns aligned to each rebalance date.",
            "For overlapping returns, autocorrelated premia, or clustered assets, use "
            "HAC/clustered inference in a full implementation.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Fama-MacBeth Regression",
        "",
        f"- Return column: {report['return_col']}",
        f"- Features: {', '.join(report['feature_cols'])}",
        f"- Dates used: {report['dates_used']}",
        f"- Dates skipped: {report['dates_skipped']}",
        f"- Rows dropped missing: {report['rows_dropped_missing']}",
        "",
        "| Term | Dates | Mean premium | Stdev | t-stat | Positive rate | Annualized mean |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["coefficient_summary"]:
        lines.append(
            f"| {row['name']} | {row['n']} | {row['mean']} | {row['stdev']} | "
            f"{row['t_stat']} | {row['positive_rate']} | "
            f"{row.get('annualized_mean_arithmetic', '')} |"
        )
    r2 = report["r2_summary"]
    lines.extend(["", f"- Mean cross-sectional R-squared: {r2['mean']}", "", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Fama-MacBeth cross-sectional regressions by date.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--return-col", required=True)
    parser.add_argument(
        "--feature-cols", required=True, help="Comma-separated characteristic/exposure columns."
    )
    parser.add_argument("--min-assets-per-date", type=int, default=10)
    parser.add_argument("--no-intercept", action="store_true")
    parser.add_argument("--annualization", type=int, default=12)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    feature_cols = [col.strip() for col in args.feature_cols.split(",") if col.strip()]
    if not feature_cols:
        raise SystemExit("--feature-cols must include at least one column.")
    df = read_dataframe(args.csv_path)
    require_columns(df, [args.date_col, args.return_col] + feature_cols)
    report = build_report(
        df,
        args.date_col,
        args.return_col,
        feature_cols,
        args.min_assets_per_date,
        not args.no_intercept,
        args.annualization,
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
