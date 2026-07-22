#!/usr/bin/env python3
"""Compute factor IC decay across multiple forward-return horizons.

Provide multiple forward-return columns such as ``fwd_1d,fwd_5d,fwd_20d``
that are already aligned to the same point-in-time factor value.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from quant_utils import read_dataframe, require_columns, summarize_series


def horizon_report(
    df: pd.DataFrame,
    date_col: str,
    factor_col: str,
    forward_return_col: str,
    min_assets: int,
) -> dict[str, Any]:
    sub = df[[date_col, factor_col, forward_return_col]].copy()
    sub[factor_col] = pd.to_numeric(sub[factor_col], errors="coerce")
    sub[forward_return_col] = pd.to_numeric(sub[forward_return_col], errors="coerce")
    rows_in = len(sub)
    sub = sub.dropna()
    dropped = rows_in - len(sub)
    by_date: list[dict[str, Any]] = []
    for date, g in sub.groupby(date_col, sort=True):
        if len(g) < min_assets:
            continue
        ic = g[factor_col].corr(g[forward_return_col])
        rank_ic = g[factor_col].corr(g[forward_return_col], method="spearman")
        by_date.append({
            "date": date if not isinstance(date, pd.Timestamp) else date.isoformat(),
            "n_assets": int(len(g)),
            "ic": None if pd.isna(ic) else float(ic),
            "rank_ic": None if pd.isna(rank_ic) else float(rank_ic),
        })
    ic_values = [item["ic"] for item in by_date if item["ic"] is not None]
    rank_ic_values = [item["rank_ic"] for item in by_date if item["rank_ic"] is not None]
    return {
        "forward_return_col": forward_return_col,
        "rows_dropped": dropped,
        "periods_used": len(by_date),
        "ic_summary": summarize_series(ic_values),
        "rank_ic_summary": summarize_series(rank_ic_values),
        "by_date": by_date,
    }


def build_report(
    df: pd.DataFrame,
    date_col: str,
    factor_col: str,
    forward_return_cols: list[str],
    min_assets: int,
) -> dict[str, Any]:
    horizons = [horizon_report(df, date_col, factor_col, col, min_assets) for col in forward_return_cols]
    return {
        "date_col": date_col,
        "factor_col": factor_col,
        "forward_return_cols": forward_return_cols,
        "min_assets_per_date": min_assets,
        "horizons": horizons,
        "notes": [
            "Decay is summarized as IC/rank-IC strength across forward-return horizons.",
            "Each forward-return column must be computed without look-ahead and must match the intended execution horizon.",
            "A monotone-looking decay curve is not proof of tradability; also check quantile returns, turnover, costs, and exposures.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Factor Decay Report",
        "",
        f"- Factor: {report['factor_col']}",
        f"- Horizons: {', '.join(report['forward_return_cols'])}",
        "",
        "| Forward return | Periods | Mean IC | IC t-stat | Mean rank IC | Rank IC t-stat | Rows dropped |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["horizons"]:
        ic = item["ic_summary"]
        rank_ic = item["rank_ic_summary"]
        lines.append(
            f"| {item['forward_return_col']} | {item['periods_used']} | {ic['mean']} | {ic['t_stat']} | {rank_ic['mean']} | {rank_ic['t_stat']} | {item['rows_dropped']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute factor IC decay across multiple forward-return horizons.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--factor-col", required=True)
    parser.add_argument("--forward-return-cols", required=True, help="Comma-separated forward return columns ordered by horizon.")
    parser.add_argument("--min-assets-per-date", type=int, default=5)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    forward_cols = [col.strip() for col in args.forward_return_cols.split(",") if col.strip()]
    if not forward_cols:
        raise SystemExit("--forward-return-cols must include at least one column.")
    df = read_dataframe(args.csv_path)
    require_columns(df, [args.date_col, args.factor_col] + forward_cols)
    report = build_report(df, args.date_col, args.factor_col, forward_cols, args.min_assets_per_date)
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
