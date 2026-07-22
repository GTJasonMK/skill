#!/usr/bin/env python3
"""Attribute portfolio return to assets and optional groups from weights.

Input is a long CSV with date, asset, beginning-period weight, and asset
return. Optional group columns such as sector/country can be aggregated.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_utils import read_dataframe, require_columns, summarize_returns, summarize_series


def split_cols(value: str | None) -> list[str]:
    return [col.strip() for col in value.split(",") if col.strip()] if value else []


def build_report(
    df: pd.DataFrame,
    date_col: str,
    asset_col: str,
    weight_col: str,
    return_col: str,
    group_cols: list[str],
    annualization: int,
) -> dict[str, Any]:
    df = df.copy()
    df[weight_col] = pd.to_numeric(df[weight_col], errors="coerce")
    df[return_col] = pd.to_numeric(df[return_col], errors="coerce")
    rows_in = len(df)
    df = df.dropna(subset=[date_col, asset_col, weight_col, return_col])
    df = df[df[asset_col].astype(str).str.len() > 0]
    dropped = rows_in - len(df)
    df["_contrib"] = df[weight_col] * df[return_col]

    periods: list[dict[str, Any]] = []
    portfolio_returns: list[float] = []
    for date, g in df.groupby(date_col, sort=True):
        p_ret = float(g["_contrib"].sum())
        gross = float(g[weight_col].abs().sum())
        by_asset = g.groupby(asset_col)["_contrib"].sum().to_dict()
        by_group: dict[str, dict[str, float]] = {}
        for col in group_cols:
            sub = g[g[col].astype(str).str.len() > 0]
            by_group[col] = sub.groupby(col)["_contrib"].sum().to_dict()
        portfolio_returns.append(p_ret)
        periods.append({
            "date": date if not isinstance(date, pd.Timestamp) else date.isoformat(),
            "portfolio_return": p_ret,
            "gross_exposure": gross,
            "asset_contribution": {k: float(v) for k, v in by_asset.items()},
            "group_contribution": {col: {k: float(v) for k, v in by_group[col].items()} for col in group_cols},
        })

    asset_groups = df.groupby(asset_col)["_contrib"]
    asset_summary = []
    for asset, vals in asset_groups:
        values = vals.tolist()
        summary = summarize_series(values)
        asset_summary.append({"asset": asset, "total_contribution": float(sum(values)), **summary})
    asset_summary.sort(key=lambda item: item["total_contribution"], reverse=True)

    group_summary: dict[str, list[dict[str, Any]]] = {}
    for col in group_cols:
        sub = df[df[col].astype(str).str.len() > 0]
        group_summary[col] = []
        for label, vals in sub.groupby(col)["_contrib"]:
            values = vals.tolist()
            summary = summarize_series(values)
            group_summary[col].append({"group": label, "total_contribution": float(sum(values)), **summary})
        group_summary[col].sort(key=lambda item: item["total_contribution"], reverse=True)

    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "weight_col": weight_col,
        "return_col": return_col,
        "group_cols": group_cols,
        "annualization": annualization,
        "rows_dropped": dropped,
        "periods_used": len(periods),
        "portfolio_return_summary": summarize_returns(portfolio_returns, annualization),
        "asset_contribution_summary": asset_summary,
        "group_contribution_summary": group_summary,
        "periods": periods,
        "notes": [
            "Contribution is beginning-period weight times same-period asset return.",
            "Group attribution sums asset contributions by supplied category columns.",
            "This is arithmetic attribution and does not decompose execution slippage, fees, or intraperiod drift.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    perf = report["portfolio_return_summary"]
    lines = [
        "# Performance Attribution Report",
        "",
        f"- Periods used: {report['periods_used']}",
        f"- Annualized return: {perf['annualized_return_geometric']}",
        f"- Annualized volatility: {perf['annualized_volatility']}",
        f"- Sharpe: {perf['sharpe']}",
        "",
        "## Asset Contribution",
        "",
        "| Asset | Total contribution | Mean | t-stat | Positive rate |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["asset_contribution_summary"]:
        lines.append(f"| {item['asset']} | {item['total_contribution']} | {item['mean']} | {item['t_stat']} | {item['positive_rate']} |")
    for col, items in report["group_contribution_summary"].items():
        lines.extend(["", f"## {col} Contribution", "", "| Group | Total contribution | Mean | t-stat |", "| --- | --- | --- | --- |"])
        for item in items:
            lines.append(f"| {item['group']} | {item['total_contribution']} | {item['mean']} | {item['t_stat']} |")
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Attribute portfolio return to assets and optional groups from weights.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--weight-col", required=True)
    parser.add_argument("--return-col", required=True)
    parser.add_argument("--group-cols")
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    group_cols = split_cols(args.group_cols)
    df = read_dataframe(args.csv_path)
    require_columns(df, [args.date_col, args.asset_col, args.weight_col, args.return_col] + group_cols)
    report = build_report(df, args.date_col, args.asset_col, args.weight_col, args.return_col,
                         group_cols, args.annualization)
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
