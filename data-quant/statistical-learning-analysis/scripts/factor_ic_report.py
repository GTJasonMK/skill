#!/usr/bin/env python3
"""Compute cross-sectional factor IC and rank IC by date.

Input is a long CSV with one row per date-asset observation and a
point-in-time factor value matched to a future return over the chosen
horizon.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import read_dataframe, require_columns

from data_quant.diagnostics.factor import factor_ic_artifact, factor_ic_legacy_payload


def period_ics(
    df: pd.DataFrame,
    date_col: str,
    factor_col: str,
    forward_return_col: str,
    min_assets: int,
) -> tuple[list[dict[str, Any]], int]:
    needed = [date_col, factor_col, forward_return_col]
    rows_in = len(df)
    df = df.copy()
    df[factor_col] = pd.to_numeric(df[factor_col], errors="coerce")
    df[forward_return_col] = pd.to_numeric(df[forward_return_col], errors="coerce")
    df = df.dropna(subset=needed)
    dropped = rows_in - len(df)
    out: list[dict[str, Any]] = []
    for date, g in df.groupby(date_col, sort=True):
        if len(g) < min_assets:
            continue
        ic = g[factor_col].corr(g[forward_return_col])
        rank_ic = g[factor_col].corr(g[forward_return_col], method="spearman")
        out.append(
            {
                "date": date if not isinstance(date, pd.Timestamp) else date.isoformat(),
                "n_assets": int(len(g)),
                "ic": None if pd.isna(ic) else float(ic),
                "rank_ic": None if pd.isna(rank_ic) else float(rank_ic),
            }
        )
    return out, dropped


def build_report(
    df: pd.DataFrame,
    date_col: str,
    factor_col: str,
    forward_return_col: str,
    min_assets: int,
) -> dict[str, Any]:
    artifact = factor_ic_artifact(
        df,
        date_col=date_col,
        factor_col=factor_col,
        forward_return_col=forward_return_col,
        min_assets=min_assets,
    )
    return factor_ic_legacy_payload(artifact)


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Factor IC Report",
        "",
        f"- Factor: {report['factor_col']}",
        f"- Forward return: {report['forward_return_col']}",
        f"- Periods used: {report['periods_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        "",
        "| Metric | N | Mean | Stdev | t-stat | Positive rate | Min | Max |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, summary in [("IC", report["ic_summary"]), ("Rank IC", report["rank_ic_summary"])]:
        lines.append(
            f"| {name} | {summary['n']} | {summary['mean']} | {summary['stdev']} | {summary['t_stat']} | {summary['positive_rate']} | {summary['min']} | {summary['max']} |"
        )
    lines.extend(["", "## By Date", "", "| Date | N assets | IC | Rank IC |", "| --- | --- | --- | --- |"])
    for item in report["by_date"]:
        lines.append(f"| {item['date']} | {item['n_assets']} | {item['ic']} | {item['rank_ic']} |")
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute cross-sectional factor IC and rank IC by date.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--factor-col", required=True)
    parser.add_argument("--forward-return-col", required=True)
    parser.add_argument("--min-assets-per-date", type=int, default=5)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    df = read_dataframe(args.csv_path)
    require_columns(df, [args.date_col, args.factor_col, args.forward_return_col])
    report = build_report(
        df, args.date_col, args.factor_col, args.forward_return_col, args.min_assets_per_date
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
