#!/usr/bin/env python3
"""Estimate factor exposures with an OLS return regression.

Regresses an asset/strategy return column on factor return columns and
reports alpha, betas, t-stats, R-squared, and residual risk. For
production research, consider HAC/Newey-West errors when residuals are
autocorrelated.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_utils import ols, read_dataframe, require_columns


def build_design(df: pd.DataFrame, return_col: str, factor_cols: list[str],
                 risk_free_col: str | None) -> tuple[np.ndarray, np.ndarray, int]:
    cols = [return_col, *factor_cols] + ([risk_free_col] if risk_free_col else [])
    sub = df[cols].apply(lambda s: pd.to_numeric(s, errors="coerce"))
    rows_in = len(sub)
    sub = sub.dropna()
    dropped = rows_in - len(sub)
    if risk_free_col:
        y = (sub[return_col] - sub[risk_free_col]).to_numpy(dtype=float)
    else:
        y = sub[return_col].to_numpy(dtype=float)
    factors = sub[factor_cols].to_numpy(dtype=float)
    X = np.column_stack([np.ones(len(sub)), factors])
    return y, X, dropped


def run_regression(df: pd.DataFrame, return_col: str, factor_cols: list[str],
                   risk_free_col: str | None, annualization: int) -> dict[str, Any]:
    y, X, dropped = build_design(df, return_col, factor_cols, risk_free_col)
    result = ols(y, X)
    names = ["alpha"] + factor_cols
    coef_rows = []
    for name, coef, se, t_stat in zip(names, result["coefficients"],
                                       result["standard_errors_iid"], result["t_stats_iid"]):
        row = {
            "name": name,
            "coefficient": coef,
            "standard_error_iid": se,
            "t_stat_iid": t_stat,
        }
        if name == "alpha":
            row["annualized_alpha_arithmetic"] = coef * annualization
        coef_rows.append(row)
    result.update({
        "return_col": return_col,
        "factor_cols": factor_cols,
        "risk_free_col": risk_free_col,
        "annualization": annualization,
        "rows_dropped": dropped,
        "coefficient_table": coef_rows,
        "notes": [
            "Dependent variable is return minus risk-free rate when --risk-free-col is provided.",
            "Standard errors and t-stats are IID OLS approximations; use HAC/Newey-West for autocorrelated financial returns.",
        ],
    })
    return result


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Factor Exposure Regression",
        "",
        f"- Return column: {report['return_col']}",
        f"- Factors: {', '.join(report['factor_cols'])}",
        f"- Risk-free column: {report['risk_free_col'] or 'None'}",
        f"- Observations: {report['n']}",
        f"- Rows dropped: {report['rows_dropped']}",
        f"- R-squared: {report['r2']}",
        f"- Adjusted R-squared: {report['adj_r2']}",
        f"- Residual standard deviation: {report['residual_std']}",
        "",
        "| Term | Coefficient | Std. error (IID) | t-stat (IID) | Annualized alpha |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["coefficient_table"]:
        annual_alpha = row.get("annualized_alpha_arithmetic", "")
        lines.append(f"| {row['name']} | {row['coefficient']} | {row['standard_error_iid']} | {row['t_stat_iid']} | {annual_alpha} |")
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate alpha and factor betas from return and factor columns.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--return-col", required=True, help="Asset/strategy return column.")
    parser.add_argument("--factor-cols", required=True, help="Comma-separated factor return columns.")
    parser.add_argument("--risk-free-col", help="Optional risk-free return column subtracted from dependent returns.")
    parser.add_argument("--annualization", type=int, default=252, help="Periods per year for annualized alpha.")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    df = read_dataframe(args.csv_path)
    factor_cols = [name.strip() for name in args.factor_cols.split(",") if name.strip()]
    required = [args.return_col] + factor_cols + ([args.risk_free_col] if args.risk_free_col else [])
    require_columns(df, required)
    report = run_regression(df, args.return_col, factor_cols, args.risk_free_col, args.annualization)
    # remove arrays from result for cleaner JSON output (residuals/fitted)
    report.pop("residuals", None)
    report.pop("fitted", None)
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
