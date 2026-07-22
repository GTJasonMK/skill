#!/usr/bin/env python3
"""Backtest portfolio returns from date-asset weights and asset returns.

Weights are interpreted as beginning-of-period weights for the return in
the same row. This is a diagnostic backtest utility, not a full execution
simulator.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_utils import read_dataframe, require_columns, summarize_returns, summarize_series


def _exposure_stats(weights: pd.Series) -> dict[str, float | None]:
    gross = float(weights.abs().sum())
    net = float(weights.sum())
    long_exposure = float(weights[weights > 0].sum())
    short_exposure = float(-weights[weights < 0].sum())
    hhi = float(((weights.abs() / gross) ** 2).sum()) if gross > 0 else None
    return {
        "gross_exposure": gross,
        "net_exposure": net,
        "long_exposure": long_exposure,
        "short_exposure": short_exposure,
        "concentration_hhi": hhi,
    }


def _turnover(prev: pd.Series | None, cur: pd.Series) -> float:
    if prev is None:
        return float(0.5 * cur.abs().sum())
    combined = pd.concat([prev, cur], axis=1).fillna(0.0)
    return float(0.5 * (combined.iloc[:, 1] - combined.iloc[:, 0]).abs().sum())


def build_report(
    df: pd.DataFrame,
    date_col: str,
    asset_col: str,
    weight_col: str,
    return_col: str,
    annualization: int,
    risk_free_annual: float,
    cost_bps: float,
) -> dict[str, Any]:
    df = df.copy()
    df[weight_col] = pd.to_numeric(df[weight_col], errors="coerce")
    df[return_col] = pd.to_numeric(df[return_col], errors="coerce")
    rows_in = len(df)
    df = df.dropna(subset=[date_col, asset_col, weight_col, return_col])
    df = df[(df[asset_col].astype(str).str.len() > 0)]
    dropped = rows_in - len(df)

    periods: list[dict[str, Any]] = []
    prev_weights: pd.Series | None = None
    for date, g in df.groupby(date_col, sort=True):
        weights = g.groupby(asset_col)[weight_col].sum()
        returns = g.groupby(asset_col)[return_col].last()
        common = weights.index.intersection(returns.index)
        gross_return = float((weights.loc[common] * returns.loc[common]).sum())
        period_turnover = _turnover(prev_weights, weights)
        cost = period_turnover * cost_bps / 10000.0
        stats = _exposure_stats(weights)
        periods.append({
            "date": date if not isinstance(date, pd.Timestamp) else date.isoformat(),
            "n_assets": int(len(weights)),
            "gross_return": gross_return,
            "turnover": period_turnover,
            "cost": cost,
            "net_return": gross_return - cost,
            **stats,
        })
        prev_weights = weights

    gross_returns = [item["gross_return"] for item in periods]
    net_returns = [item["net_return"] for item in periods]
    turnovers = [item["turnover"] for item in periods]
    gross_exposures = [item["gross_exposure"] for item in periods]
    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "weight_col": weight_col,
        "return_col": return_col,
        "annualization": annualization,
        "risk_free_annual": risk_free_annual,
        "cost_bps_per_one_way_turnover": cost_bps,
        "rows_dropped": dropped,
        "periods_used": len(periods),
        "gross_return_summary": summarize_returns(gross_returns, annualization, risk_free_annual),
        "net_return_summary": summarize_returns(net_returns, annualization, risk_free_annual),
        "turnover_summary": summarize_series(turnovers),
        "gross_exposure_summary": summarize_series(gross_exposures),
        "periods": periods,
        "notes": [
            "Weights are treated as beginning-of-period weights for same-row returns.",
            "Transaction cost is cost_bps * one-way turnover; use transaction_cost_report.py for richer cost diagnostics.",
            "This utility does not model intraperiod drift, execution price, borrow constraints, or market impact.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    gross = report["gross_return_summary"]
    net = report["net_return_summary"]
    turn = report["turnover_summary"]
    exposure = report["gross_exposure_summary"]
    lines = [
        "# Portfolio Backtest Report",
        "",
        f"- Return column: {report['return_col']}",
        f"- Weight column: {report['weight_col']}",
        f"- Periods used: {report['periods_used']}",
        f"- Cost bps per one-way turnover: {report['cost_bps_per_one_way_turnover']}",
        f"- Rows dropped: {report['rows_dropped']}",
        "",
        "| Series | N | Ann. return | Ann. vol | Sharpe | Max drawdown | VaR 95 | ES 95 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| Gross | {gross['n']} | {gross['annualized_return_geometric']} | {gross['annualized_volatility']} | {gross['sharpe']} | {gross['max_drawdown']} | {gross['historical_var_95']} | {gross['historical_expected_shortfall_95']} |",
        f"| Net | {net['n']} | {net['annualized_return_geometric']} | {net['annualized_volatility']} | {net['sharpe']} | {net['max_drawdown']} | {net['historical_var_95']} | {net['historical_expected_shortfall_95']} |",
        "",
        "## Trading and Exposure",
        "",
        f"- Mean turnover: {turn['mean']}",
        f"- Annualized turnover: {turn['mean'] * report['annualization'] if turn['mean'] is not None else None}",
        f"- Mean gross exposure: {exposure['mean']}",
        "",
        "Notes:",
    ]
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Backtest portfolio returns from date-asset weights and returns.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--weight-col", required=True)
    parser.add_argument("--return-col", required=True)
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--risk-free-annual", type=float, default=0.0)
    parser.add_argument("--cost-bps", type=float, default=0.0, help="Cost in bps per one-way turnover.")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    df = read_dataframe(args.csv_path)
    require_columns(df, [args.date_col, args.asset_col, args.weight_col, args.return_col])
    report = build_report(df, args.date_col, args.asset_col, args.weight_col, args.return_col,
                         args.annualization, args.risk_free_annual, args.cost_bps)
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
