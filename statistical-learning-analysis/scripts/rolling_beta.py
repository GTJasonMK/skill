#!/usr/bin/env python3
"""Estimate rolling beta and alpha of a return series versus a benchmark.

Input is a time-ordered CSV with strategy/asset returns and benchmark
returns. Optional risk-free returns are subtracted from both.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_utils import read_dataframe, require_columns, summarize_series


def _regression_stats(y: np.ndarray, x: np.ndarray, annualization: int) -> dict[str, Any]:
    n = int(min(y.size, x.size))
    blank = {"n": n, "beta": None, "alpha": None, "annualized_alpha_arithmetic": None,
             "r2": None, "residual_volatility": None, "annualized_residual_volatility": None}
    if n < 2:
        return blank
    yy = y[:n]
    xx = x[:n]
    mx = float(xx.mean())
    my = float(yy.mean())
    var_x = float(((xx - mx) ** 2).sum())
    if var_x == 0:
        return blank
    beta = float(((xx - mx) * (yy - my)).sum() / var_x)
    alpha = my - beta * mx
    fitted = alpha + beta * xx
    residuals = yy - fitted
    tss = float(((yy - my) ** 2).sum())
    sse = float((residuals ** 2).sum())
    resid_vol = float(residuals.std(ddof=1)) if residuals.size >= 2 else None
    return {
        "n": n,
        "beta": beta,
        "alpha": alpha,
        "annualized_alpha_arithmetic": alpha * annualization,
        "r2": 1.0 - sse / tss if tss > 0 else None,
        "residual_volatility": resid_vol,
        "annualized_residual_volatility": resid_vol * np.sqrt(annualization) if resid_vol is not None else None,
    }


def build_report(
    df: pd.DataFrame,
    date_col: str | None,
    return_col: str,
    benchmark_col: str,
    risk_free_col: str | None,
    window: int,
    annualization: int,
) -> dict[str, Any]:
    rows_in = len(df)
    df = df.copy()
    df[return_col] = pd.to_numeric(df[return_col], errors="coerce")
    df[benchmark_col] = pd.to_numeric(df[benchmark_col], errors="coerce")
    if risk_free_col:
        df[risk_free_col] = pd.to_numeric(df[risk_free_col], errors="coerce")
    needed = [return_col, benchmark_col] + ([risk_free_col] if risk_free_col else [])
    df = df.dropna(subset=needed).reset_index(drop=True)
    dropped = rows_in - len(df)

    rf = df[risk_free_col].to_numpy(dtype=float) if risk_free_col else np.zeros(len(df))
    excess_ret = df[return_col].to_numpy(dtype=float) - rf
    excess_bench = df[benchmark_col].to_numpy(dtype=float) - rf
    dates = (df[date_col].astype(str).tolist() if date_col else [None] * len(df))

    rolling = []
    for end in range(window, len(df) + 1):
        y = excess_ret[end - window: end]
        x = excess_bench[end - window: end]
        stats = _regression_stats(y, x, annualization)
        rolling.append({
            "end_index": end,
            "end_date": dates[end - 1],
            **stats,
        })
    betas = [item["beta"] for item in rolling if item["beta"] is not None]
    alphas = [item["alpha"] for item in rolling if item["alpha"] is not None]
    r2_values = [item["r2"] for item in rolling if item["r2"] is not None]
    return {
        "date_col": date_col,
        "return_col": return_col,
        "benchmark_col": benchmark_col,
        "risk_free_col": risk_free_col,
        "window": window,
        "annualization": annualization,
        "rows_dropped": dropped,
        "observations_used": int(len(df)),
        "rolling_windows": len(rolling),
        "beta_summary": summarize_series(betas),
        "alpha_summary": summarize_series(alphas),
        "r2_summary": summarize_series(r2_values),
        "latest": rolling[-1] if rolling else None,
        "rolling": rolling,
        "notes": [
            "Returns and benchmark are converted to excess returns when --risk-free-col is provided.",
            "Rolling beta stability is a diagnostic; it does not prove alpha or causal exposure.",
            "Use HAC/Newey-West or block bootstrap in serious inference workflows with autocorrelated returns.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    beta = report["beta_summary"]
    alpha = report["alpha_summary"]
    r2 = report["r2_summary"]
    latest = report["latest"] or {}
    lines = [
        "# Rolling Beta Report",
        "",
        f"- Return column: {report['return_col']}",
        f"- Benchmark column: {report['benchmark_col']}",
        f"- Window: {report['window']}",
        f"- Rolling windows: {report['rolling_windows']}",
        f"- Rows dropped: {report['rows_dropped']}",
        "",
        "| Metric | N | Mean | Stdev | Min | Max |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| Beta | {beta['n']} | {beta['mean']} | {beta['stdev']} | {beta['min']} | {beta['max']} |",
        f"| Alpha | {alpha['n']} | {alpha['mean']} | {alpha['stdev']} | {alpha['min']} | {alpha['max']} |",
        f"| R-squared | {r2['n']} | {r2['mean']} | {r2['stdev']} | {r2['min']} | {r2['max']} |",
        "",
        "## Latest Window",
        "",
        f"- End date: {latest.get('end_date')}",
        f"- Beta: {latest.get('beta')}",
        f"- Annualized alpha: {latest.get('annualized_alpha_arithmetic')}",
        f"- R-squared: {latest.get('r2')}",
        "",
        "Notes:",
    ]
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate rolling beta and alpha of a return series versus a benchmark.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col")
    parser.add_argument("--return-col", required=True)
    parser.add_argument("--benchmark-col", required=True)
    parser.add_argument("--risk-free-col")
    parser.add_argument("--window", type=int, default=60)
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.window < 2:
        raise SystemExit("--window must be at least 2.")
    df = read_dataframe(args.csv_path)
    require_columns(df, [args.return_col, args.benchmark_col]
                    + ([args.date_col] if args.date_col else [])
                    + ([args.risk_free_col] if args.risk_free_col else []))
    report = build_report(df, args.date_col, args.return_col, args.benchmark_col,
                         args.risk_free_col, args.window, args.annualization)
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
