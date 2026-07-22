#!/usr/bin/env python3
"""Compute covariance, correlation, and volatility diagnostics for return columns.

Input is a wide CSV where selected columns are return series for assets,
factors, or strategies.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_utils import read_dataframe, require_columns


def _matrix_to_dict(mat: pd.DataFrame, columns: list[str]) -> dict[str, dict[str, float | None]]:
    out: dict[str, dict[str, float | None]] = {}
    for a in columns:
        out[a] = {}
        for b in columns:
            value = mat.at[a, b]
            out[a][b] = None if pd.isna(value) else float(value)
    return out


def build_report(df: pd.DataFrame, columns: list[str], annualization: int) -> dict[str, Any]:
    numeric = df[columns].apply(lambda s: pd.to_numeric(s, errors="coerce"))
    dropped_by_column = numeric.isna().sum().to_dict()

    assets = []
    for col in columns:
        series = numeric[col].dropna()
        sd = float(series.std(ddof=1)) if len(series) >= 2 else None
        avg = float(series.mean()) if len(series) > 0 else None
        assets.append({
            "asset": col,
            "n": int(len(series)),
            "rows_dropped": int(dropped_by_column[col]),
            "mean_return": avg,
            "annualized_return_arithmetic": avg * annualization if avg is not None else None,
            "volatility": sd,
            "annualized_volatility": sd * np.sqrt(annualization) if sd is not None else None,
        })

    # pairwise n
    pairwise_n: dict[str, dict[str, int]] = {}
    for a in columns:
        pairwise_n[a] = {}
        for b in columns:
            mask = numeric[a].notna() & numeric[b].notna()
            pairwise_n[a][b] = int(mask.sum())

    cov_df = numeric.cov(ddof=1)
    corr_df = numeric.corr()
    ann_cov_df = cov_df * annualization
    return {
        "columns": columns,
        "annualization": annualization,
        "assets": assets,
        "covariance": _matrix_to_dict(cov_df, columns),
        "annualized_covariance": _matrix_to_dict(ann_cov_df, columns),
        "correlation": _matrix_to_dict(corr_df, columns),
        "pairwise_n": pairwise_n,
        "notes": [
            "Covariance and correlation are computed pairwise after dropping missing values for each pair.",
            "Annualized covariance multiplies periodic covariance by the annualization factor.",
            "These are historical estimates; shrinkage, regime checks, and out-of-sample realized-risk validation are needed before optimization.",
        ],
    }


def matrix_markdown(title: str, matrix: dict[str, dict[str, Any]], columns: list[str]) -> list[str]:
    lines = [f"## {title}", "", "| Asset | " + " | ".join(columns) + " |", "| --- | " + " | ".join("---" for _ in columns) + " |"]
    for row in columns:
        lines.append("| " + row + " | " + " | ".join(str(matrix[row][col]) for col in columns) + " |")
    return lines


def markdown(report: dict[str, Any]) -> str:
    columns = report["columns"]
    lines = [
        "# Covariance Report",
        "",
        f"- Columns: {', '.join(columns)}",
        f"- Annualization: {report['annualization']}",
        "",
        "| Asset | N | Mean return | Ann. return | Volatility | Ann. volatility | Rows dropped |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["assets"]:
        lines.append(
            f"| {item['asset']} | {item['n']} | {item['mean_return']} | {item['annualized_return_arithmetic']} | {item['volatility']} | {item['annualized_volatility']} | {item['rows_dropped']} |"
        )
    lines.extend([""])
    lines.extend(matrix_markdown("Correlation", report["correlation"], columns))
    lines.extend([""])
    lines.extend(matrix_markdown("Annualized Covariance", report["annualized_covariance"], columns))
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute covariance, correlation, and volatility diagnostics for return columns.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--columns", required=True, help="Comma-separated return columns.")
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    columns = [col.strip() for col in args.columns.split(",") if col.strip()]
    if not columns:
        raise SystemExit("--columns must include at least one return column.")
    df = read_dataframe(args.csv_path)
    require_columns(df, columns)
    report = build_report(df, columns, args.annualization)
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
