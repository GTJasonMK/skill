#!/usr/bin/env python3
"""Run OLS with IID and Newey-West/HAC standard errors.

Use for time-series return regressions where residual autocorrelation
can make ordinary OLS t-stats too optimistic.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_utils import newey_west_se, ols, read_dataframe, require_columns


def build_design(df: pd.DataFrame, y_col: str, x_cols: list[str],
                 intercept: bool) -> tuple[np.ndarray, np.ndarray, int]:
    sub = df[[y_col] + x_cols].apply(lambda s: pd.to_numeric(s, errors="coerce"))
    rows_in = len(sub)
    sub = sub.dropna()
    dropped = rows_in - len(sub)
    y = sub[y_col].to_numpy(dtype=float)
    xs = sub[x_cols].to_numpy(dtype=float)
    X = np.column_stack([np.ones(len(sub)), xs]) if intercept else xs
    return y, X, dropped


def build_report(df: pd.DataFrame, y_col: str, x_cols: list[str], lags: int,
                 intercept: bool, annualization: int) -> dict[str, Any]:
    y, X, dropped = build_design(df, y_col, x_cols, intercept)
    try:
        fit = ols(y, X)
        resid = np.asarray(fit["residuals"], dtype=float)
        se_hac = newey_west_se(X, resid, lags)
        # HC1-style small-sample correction
        n = fit["n"]
        p = fit["p"]
        scale = np.sqrt(n / max(n - p, 1))
        se_hac = se_hac * scale
    except ValueError as exc:
        raise SystemExit(f"Could not fit regression: {exc}") from exc
    names = (["intercept"] if intercept else []) + x_cols
    coefficient_table = []
    for i, name in enumerate(names):
        coef = fit["coefficients"][i]
        se = float(se_hac[i])
        row = {
            "name": name,
            "coefficient": coef,
            "standard_error_iid": fit["standard_errors_iid"][i],
            "t_stat_iid": fit["t_stats_iid"][i],
            "standard_error_newey_west": se,
            "t_stat_newey_west": coef / se if se > 0 else None,
        }
        if name == "intercept":
            row["annualized_intercept_arithmetic"] = coef * annualization
        coefficient_table.append(row)
    return {
        "y_col": y_col,
        "x_cols": x_cols,
        "intercept": intercept,
        "newey_west_lags": lags,
        "annualization": annualization,
        "n": fit["n"],
        "df_resid": fit["df_resid"],
        "rows_dropped": dropped,
        "r2": fit["r2"],
        "adj_r2": fit["adj_r2"],
        "residual_std": fit["residual_std"],
        "coefficient_table": coefficient_table,
        "notes": [
            "Newey-West standard errors adjust for autocorrelation up to the selected lag length.",
            "Lag choice should reflect data frequency, horizon overlap, and research design.",
            "For panel or clustered assets, use clustered/HAC panel inference in a full implementation.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Newey-West Regression",
        "",
        f"- Dependent variable: {report['y_col']}",
        f"- Regressors: {', '.join(report['x_cols'])}",
        f"- Observations: {report['n']}",
        f"- Newey-West lags: {report['newey_west_lags']}",
        f"- R-squared: {report['r2']}",
        "",
        "| Term | Coefficient | t-stat IID | t-stat NW | SE IID | SE NW | Annualized intercept |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["coefficient_table"]:
        lines.append(
            f"| {row['name']} | {row['coefficient']} | {row['t_stat_iid']} | {row['t_stat_newey_west']} | {row['standard_error_iid']} | {row['standard_error_newey_west']} | {row.get('annualized_intercept_arithmetic', '')} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OLS with IID and Newey-West/HAC standard errors.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--y-col", required=True)
    parser.add_argument("--x-cols", required=True, help="Comma-separated regressor columns.")
    parser.add_argument("--lags", type=int, default=5)
    parser.add_argument("--no-intercept", action="store_true")
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.lags < 0:
        raise SystemExit("--lags must be non-negative.")
    x_cols = [col.strip() for col in args.x_cols.split(",") if col.strip()]
    if not x_cols:
        raise SystemExit("--x-cols must include at least one regressor.")
    df = read_dataframe(args.csv_path)
    require_columns(df, [args.y_col] + x_cols)
    report = build_report(df, args.y_col, x_cols, args.lags, not args.no_intercept, args.annualization)
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
