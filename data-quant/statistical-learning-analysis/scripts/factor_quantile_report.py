#!/usr/bin/env python3
"""Evaluate factor-sorted quantile forward returns by date.

Input is a long CSV with one row per date-asset observation, a factor
value, and a matched forward return.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from quant_utils import read_dataframe, require_columns, summarize_series


def _weighted_mean(values: np.ndarray, weights: np.ndarray | None) -> float | None:
    if values.size == 0:
        return None
    if weights is None:
        return float(values.mean())
    mask = weights > 0
    if not mask.any():
        return None
    v = values[mask]
    w = weights[mask]
    total = w.sum()
    if total <= 0:
        return None
    return float((v * w).sum() / total)


def _quantile_returns(
    g: pd.DataFrame, factor_col: str, return_col: str, weight_col: str | None, quantiles: int
) -> dict[int, float | None]:
    ordered = g.sort_values(factor_col).reset_index(drop=True)
    n = len(ordered)
    bucket_index = np.minimum(quantiles, (np.arange(n) * quantiles // n) + 1)
    out: dict[int, float | None] = {}
    for q in range(1, quantiles + 1):
        sel = ordered[bucket_index == q]
        if sel.empty:
            out[q] = None
            continue
        returns = sel[return_col].to_numpy(dtype=float)
        weights = sel[weight_col].to_numpy(dtype=float) if weight_col else None
        out[q] = _weighted_mean(returns, weights)
    return out


def build_report(
    df: pd.DataFrame,
    date_col: str,
    factor_col: str,
    forward_return_col: str,
    quantiles: int,
    min_assets: int,
    annualization: int,
    weight_col: str | None,
) -> dict[str, Any]:
    needed = [date_col, factor_col, forward_return_col] + ([weight_col] if weight_col else [])
    rows_in = len(df)
    df = df.copy()
    df[factor_col] = pd.to_numeric(df[factor_col], errors="coerce")
    df[forward_return_col] = pd.to_numeric(df[forward_return_col], errors="coerce")
    if weight_col:
        df[weight_col] = pd.to_numeric(df[weight_col], errors="coerce")
    df = df.dropna(subset=needed)
    dropped = rows_in - len(df)

    by_date: list[dict[str, Any]] = []
    skipped_dates = 0
    for date, g in df.groupby(date_col, sort=True):
        if len(g) < max(min_assets, quantiles):
            skipped_dates += 1
            continue
        returns_by_q = _quantile_returns(g, factor_col, forward_return_col, weight_col, quantiles)
        high = returns_by_q.get(quantiles)
        low = returns_by_q.get(1)
        by_date.append(
            {
                "date": date if not isinstance(date, pd.Timestamp) else date.isoformat(),
                "n_assets": int(len(g)),
                "quantile_returns": returns_by_q,
                "high_minus_low": (high - low) if high is not None and low is not None else None,
            }
        )

    quantile_summary = []
    for q in range(1, quantiles + 1):
        values = [item["quantile_returns"][q] for item in by_date if item["quantile_returns"][q] is not None]
        summary = summarize_series(values)
        summary["quantile"] = q
        summary["annualized_return_arithmetic"] = (
            summary["mean"] * annualization if summary["mean"] is not None else None
        )
        quantile_summary.append(summary)
    spreads = [item["high_minus_low"] for item in by_date if item["high_minus_low"] is not None]
    spread_summary = summarize_series(spreads)
    spread_summary["annualized_return_arithmetic"] = (
        spread_summary["mean"] * annualization if spread_summary["mean"] is not None else None
    )
    return {
        "date_col": date_col,
        "factor_col": factor_col,
        "forward_return_col": forward_return_col,
        "weight_col": weight_col,
        "quantiles": quantiles,
        "annualization": annualization,
        "rows_dropped": dropped,
        "skipped_dates": skipped_dates,
        "periods_used": len(by_date),
        "quantile_summary": quantile_summary,
        "high_minus_low_summary": spread_summary,
        "by_date": by_date,
        "notes": [
            "Quantile 1 contains the lowest factor values; the top quantile contains the highest factor values.",
            "High-minus-low spread is top quantile forward return minus bottom quantile forward return.",
            "Rows must already use point-in-time factors and an executable forward-return horizon.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Factor Quantile Report",
        "",
        f"- Factor: {report['factor_col']}",
        f"- Forward return: {report['forward_return_col']}",
        f"- Quantiles: {report['quantiles']}",
        f"- Periods used: {report['periods_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        "",
        "| Quantile | N periods | Mean return | Ann. return | t-stat | Positive rate |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["quantile_summary"]:
        lines.append(
            f"| Q{item['quantile']} | {item['n']} | {item['mean']} | {item['annualized_return_arithmetic']} | {item['t_stat']} | {item['positive_rate']} |"
        )
    spread = report["high_minus_low_summary"]
    lines.extend(
        [
            "",
            "## High Minus Low",
            "",
            f"- Mean spread: {spread['mean']}",
            f"- Annualized arithmetic spread: {spread['annualized_return_arithmetic']}",
            f"- t-stat: {spread['t_stat']}",
            f"- Positive rate: {spread['positive_rate']}",
            "",
            "Notes:",
        ]
    )
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate factor-sorted quantile forward returns by date.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--factor-col", required=True)
    parser.add_argument("--forward-return-col", required=True)
    parser.add_argument("--weight-col")
    parser.add_argument("--quantiles", type=int, default=5)
    parser.add_argument("--min-assets-per-date", type=int, default=5)
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.quantiles < 2:
        raise SystemExit("--quantiles must be at least 2.")
    df = read_dataframe(args.csv_path)
    require_columns(
        df,
        [args.date_col, args.factor_col, args.forward_return_col]
        + ([args.weight_col] if args.weight_col else []),
    )
    report = build_report(
        df,
        args.date_col,
        args.factor_col,
        args.forward_return_col,
        args.quantiles,
        args.min_assets_per_date,
        args.annualization,
        args.weight_col,
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
