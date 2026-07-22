#!/usr/bin/env python3
"""Build a simple signal-ranked long-short backtest from long-form data.

Ranks assets by signal within each date, forms equal-weight long/short
portfolios, and reports gross/net performance, turnover, and selected-name
counts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_utils import read_dataframe, require_columns, summarize_returns, summarize_series


def _build_weights(g: pd.DataFrame, asset_col: str, signal_col: str,
                   top_frac: float, mode: str) -> pd.Series:
    ordered = g.sort_values(signal_col).reset_index(drop=True)
    n = len(ordered)
    k = max(1, int(round(n * top_frac)))
    weights = pd.Series(0.0, index=ordered[asset_col])
    if mode == "long_only":
        for asset in ordered[asset_col].tail(k):
            weights.loc[asset] = 1.0 / k
        return weights
    long_weight = 0.5 if mode == "long_short" else 1.0
    short_weight = -0.5 if mode == "long_short" else -1.0
    if mode in {"long_short", "short_only"}:
        for asset in ordered[asset_col].head(k):
            weights.loc[asset] = weights.loc[asset] + short_weight / k
    if mode == "long_short":
        for asset in ordered[asset_col].tail(k):
            weights.loc[asset] = weights.loc[asset] + long_weight / k
    return weights


def _one_way_turnover(prev: pd.Series | None, cur: pd.Series) -> float:
    if prev is None:
        return float(0.5 * cur.abs().sum())
    combined = pd.concat([prev, cur], axis=1).fillna(0.0)
    return float(0.5 * (combined.iloc[:, 1] - combined.iloc[:, 0]).abs().sum())


def build_report(
    df: pd.DataFrame,
    date_col: str,
    asset_col: str,
    signal_col: str,
    return_col: str,
    top_frac: float,
    mode: str,
    min_assets: int,
    annualization: int,
    cost_bps: float,
) -> dict[str, Any]:
    df = df.copy()
    df[signal_col] = pd.to_numeric(df[signal_col], errors="coerce")
    df[return_col] = pd.to_numeric(df[return_col], errors="coerce")
    rows_in = len(df)
    df = df.dropna(subset=[date_col, asset_col, signal_col, return_col])
    df = df[df[asset_col].astype(str).str.len() > 0]
    dropped = rows_in - len(df)

    periods: list[dict[str, Any]] = []
    prev_weights: pd.Series | None = None
    skipped_dates = 0
    for date, g in df.groupby(date_col, sort=True):
        if len(g) < min_assets:
            skipped_dates += 1
            continue
        weights = _build_weights(g, asset_col, signal_col, top_frac, mode)
        returns = g.set_index(asset_col)[return_col]
        common = weights.index.intersection(returns.index)
        gross_return = float((weights.loc[common] * returns.loc[common]).sum())
        turnover = _one_way_turnover(prev_weights, weights)
        cost = turnover * cost_bps / 10000.0
        periods.append({
            "date": date if not isinstance(date, pd.Timestamp) else date.isoformat(),
            "n_assets": int(len(g)),
            "n_selected": int((weights != 0).sum()),
            "gross_return": gross_return,
            "turnover": turnover,
            "cost": cost,
            "net_return": gross_return - cost,
            "gross_exposure": float(weights.abs().sum()),
            "net_exposure": float(weights.sum()),
        })
        prev_weights = weights

    gross_returns = [item["gross_return"] for item in periods]
    net_returns = [item["net_return"] for item in periods]
    turnovers = [item["turnover"] for item in periods]
    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "signal_col": signal_col,
        "return_col": return_col,
        "top_frac": top_frac,
        "mode": mode,
        "annualization": annualization,
        "cost_bps_per_one_way_turnover": cost_bps,
        "min_assets_per_date": min_assets,
        "rows_dropped": dropped,
        "dates_skipped": skipped_dates,
        "periods_used": len(periods),
        "gross_return_summary": summarize_returns(gross_returns, annualization),
        "net_return_summary": summarize_returns(net_returns, annualization),
        "turnover_summary": summarize_series(turnovers),
        "periods": periods,
        "notes": [
            "Signals must be point-in-time and lagged to the rebalance/execution date.",
            "Long-short mode uses 50% long and 50% short exposure for gross exposure near 1.",
            "This is a simple rank portfolio diagnostic; it does not model fills, borrow availability, market impact, or constraints.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    gross = report["gross_return_summary"]
    net = report["net_return_summary"]
    turn = report["turnover_summary"]
    lines = [
        "# Long-Short Backtest",
        "",
        f"- Signal column: {report['signal_col']}",
        f"- Return column: {report['return_col']}",
        f"- Mode: {report['mode']}",
        f"- Top fraction: {report['top_frac']}",
        f"- Periods used: {report['periods_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        "",
        "| Series | Ann. return | Ann. vol | Sharpe | Max drawdown | VaR 95 | ES 95 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        f"| Gross | {gross['annualized_return_geometric']} | {gross['annualized_volatility']} | {gross['sharpe']} | {gross['max_drawdown']} | {gross['historical_var_95']} | {gross['historical_expected_shortfall_95']} |",
        f"| Net | {net['annualized_return_geometric']} | {net['annualized_volatility']} | {net['sharpe']} | {net['max_drawdown']} | {net['historical_var_95']} | {net['historical_expected_shortfall_95']} |",
        "",
        f"- Mean turnover: {turn['mean']}",
        f"- Annualized turnover: {turn['mean'] * report['annualization'] if turn['mean'] is not None else None}",
        "",
        "Notes:",
    ]
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a simple signal-ranked long-short backtest from long-form data.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--signal-col", required=True)
    parser.add_argument("--return-col", required=True)
    parser.add_argument("--top-frac", type=float, default=0.2)
    parser.add_argument("--mode", choices=["long_short", "long_only", "short_only"], default="long_short")
    parser.add_argument("--min-assets-per-date", type=int, default=5)
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--cost-bps", type=float, default=0.0)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.top_frac <= 0 or args.top_frac > 0.5:
        raise SystemExit("--top-frac must be in (0, 0.5].")
    df = read_dataframe(args.csv_path)
    require_columns(df, [args.date_col, args.asset_col, args.signal_col, args.return_col])
    report = build_report(df, args.date_col, args.asset_col, args.signal_col, args.return_col,
                         args.top_frac, args.mode, args.min_assets_per_date, args.annualization, args.cost_bps)
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
