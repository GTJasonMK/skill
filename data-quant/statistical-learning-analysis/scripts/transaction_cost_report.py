#!/usr/bin/env python3
"""Estimate turnover-driven transaction costs from portfolio weights.

Supports simple commission/slippage bps, optional per-asset spread bps,
optional borrow bps for short exposure, and optional net-return diagnostics
when an asset return column is provided.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from quant_utils import read_dataframe, require_columns, summarize_returns, summarize_series


def build_report(
    df: pd.DataFrame,
    date_col: str,
    asset_col: str,
    weight_col: str,
    return_col: str | None,
    spread_bps_col: str | None,
    adv_col: str | None,
    annualization: int,
    commission_bps: float,
    slippage_bps: float,
    borrow_bps_annual: float,
    nav: float | None,
) -> dict[str, Any]:
    df = df.copy()
    df[weight_col] = pd.to_numeric(df[weight_col], errors="coerce")
    if return_col:
        df[return_col] = pd.to_numeric(df[return_col], errors="coerce")
    if spread_bps_col:
        df[spread_bps_col] = pd.to_numeric(df[spread_bps_col], errors="coerce")
    if adv_col:
        df[adv_col] = pd.to_numeric(df[adv_col], errors="coerce")
    needed = [date_col, asset_col, weight_col]
    for col in [return_col, spread_bps_col, adv_col]:
        if col:
            needed.append(col)
    rows_in = len(df)
    df = df.dropna(subset=needed)
    df = df[df[asset_col].astype(str).str.len() > 0]
    dropped = rows_in - len(df)

    periods: list[dict[str, Any]] = []
    prev_weights: dict[str, float] = {}
    for date, g in df.groupby(date_col, sort=True):
        cur_weights = g.groupby(asset_col)[weight_col].sum().to_dict()
        per_asset_meta = {row[asset_col]: row for _, row in g.iterrows()}
        universe = set(prev_weights) | set(cur_weights)
        turnover = 0.5 * sum(abs(cur_weights.get(a, 0.0) - prev_weights.get(a, 0.0)) for a in universe)
        trade_cost = 0.0
        max_adv_participation: float | None = None
        for asset in universe:
            delta = abs(cur_weights.get(asset, 0.0) - prev_weights.get(asset, 0.0))
            if delta == 0:
                continue
            meta = per_asset_meta.get(asset)
            half_spread_bps = float(meta[spread_bps_col]) / 2 if spread_bps_col and meta is not None else 0.0
            trade_cost += delta * (commission_bps + slippage_bps + half_spread_bps) / 10000
            if adv_col and nav is not None and meta is not None:
                adv = float(meta[adv_col])
                if adv > 0:
                    participation = delta * nav / adv
                    max_adv_participation = (
                        participation
                        if max_adv_participation is None
                        else max(max_adv_participation, participation)
                    )
        short_exposure = -sum(w for w in cur_weights.values() if w < 0)
        borrow_cost = short_exposure * borrow_bps_annual / 10000 / annualization
        total_cost = trade_cost + borrow_cost
        gross_return: float | None = None
        net_return: float | None = None
        if return_col:
            returns_by_asset = g.set_index(asset_col)[return_col].to_dict()
            gross_return = sum(
                w * float(returns_by_asset[a]) for a, w in cur_weights.items() if a in returns_by_asset
            )
            net_return = gross_return - total_cost
        periods.append(
            {
                "date": date if not isinstance(date, pd.Timestamp) else date.isoformat(),
                "n_assets": int(len(cur_weights)),
                "one_way_turnover": turnover,
                "trade_cost": trade_cost,
                "borrow_cost": borrow_cost,
                "total_cost": total_cost,
                "short_exposure": short_exposure,
                "gross_return": gross_return,
                "net_return": net_return,
                "max_adv_participation": max_adv_participation,
            }
        )
        prev_weights = cur_weights

    turnovers = [item["one_way_turnover"] for item in periods]
    trade_costs = [item["trade_cost"] for item in periods]
    borrow_costs = [item["borrow_cost"] for item in periods]
    total_costs = [item["total_cost"] for item in periods]
    gross_returns = [item["gross_return"] for item in periods if item["gross_return"] is not None]
    net_returns = [item["net_return"] for item in periods if item["net_return"] is not None]
    participation = [
        item["max_adv_participation"] for item in periods if item["max_adv_participation"] is not None
    ]
    mean_cost = float(np.mean(total_costs)) if total_costs else None
    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "weight_col": weight_col,
        "return_col": return_col,
        "spread_bps_col": spread_bps_col,
        "adv_col": adv_col,
        "annualization": annualization,
        "commission_bps": commission_bps,
        "slippage_bps": slippage_bps,
        "borrow_bps_annual": borrow_bps_annual,
        "nav": nav,
        "rows_dropped": dropped,
        "periods_used": len(periods),
        "turnover_summary": summarize_series(turnovers),
        "trade_cost_summary": summarize_series(trade_costs),
        "borrow_cost_summary": summarize_series(borrow_costs),
        "total_cost_summary": summarize_series(total_costs),
        "gross_return_summary": summarize_returns(gross_returns, annualization) if gross_returns else None,
        "net_return_summary": summarize_returns(net_returns, annualization) if net_returns else None,
        "max_adv_participation_summary": summarize_series(participation) if participation else None,
        "total_cost_sum": float(sum(total_costs)),
        "mean_cost_bps_per_period": mean_cost * 10000 if mean_cost is not None else None,
        "periods": periods,
        "notes": [
            "Trade cost is applied to absolute weight changes using commission, slippage, and optional half-spread bps.",
            "Borrow cost is applied to short exposure per period from annual borrow bps.",
            "ADV participation is approximate and requires --nav plus an ADV column in currency units.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    turn = report["turnover_summary"]
    total = report["total_cost_summary"]
    lines = [
        "# Transaction Cost Report",
        "",
        f"- Weight column: {report['weight_col']}",
        f"- Periods used: {report['periods_used']}",
        f"- Commission bps: {report['commission_bps']}",
        f"- Slippage bps: {report['slippage_bps']}",
        f"- Borrow bps annual: {report['borrow_bps_annual']}",
        f"- Rows dropped: {report['rows_dropped']}",
        "",
        "| Metric | N | Mean | Stdev | Min | Max |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| One-way turnover | {turn['n']} | {turn['mean']} | {turn['stdev']} | {turn['min']} | {turn['max']} |",
        f"| Total cost | {total['n']} | {total['mean']} | {total['stdev']} | {total['min']} | {total['max']} |",
        "",
        f"- Total cost sum: {report['total_cost_sum']}",
        f"- Mean cost bps per period: {report['mean_cost_bps_per_period']}",
    ]
    if report["gross_return_summary"] and report["net_return_summary"]:
        gross = report["gross_return_summary"]
        net = report["net_return_summary"]
        lines.extend(
            [
                "",
                "## Net Performance",
                "",
                "| Series | Ann. return | Ann. vol | Sharpe | Max drawdown |",
                "| --- | --- | --- | --- | --- |",
                f"| Gross | {gross['annualized_return_geometric']} | {gross['annualized_volatility']} | {gross['sharpe']} | {gross['max_drawdown']} |",
                f"| Net | {net['annualized_return_geometric']} | {net['annualized_volatility']} | {net['sharpe']} | {net['max_drawdown']} |",
            ]
        )
    if report["max_adv_participation_summary"]:
        part = report["max_adv_participation_summary"]
        lines.extend(
            ["", f"- Mean max ADV participation: {part['mean']}", f"- Max ADV participation: {part['max']}"]
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Estimate turnover-driven transaction costs from portfolio weights."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--weight-col", required=True)
    parser.add_argument("--return-col")
    parser.add_argument("--spread-bps-col")
    parser.add_argument("--adv-col", help="Average daily dollar volume column for participation diagnostics.")
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--commission-bps", type=float, default=0.0)
    parser.add_argument("--slippage-bps", type=float, default=0.0)
    parser.add_argument("--borrow-bps-annual", type=float, default=0.0)
    parser.add_argument("--nav", type=float, help="Portfolio NAV in the same currency as ADV.")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    df = read_dataframe(args.csv_path)
    require_columns(
        df,
        [args.date_col, args.asset_col, args.weight_col]
        + ([args.return_col] if args.return_col else [])
        + ([args.spread_bps_col] if args.spread_bps_col else [])
        + ([args.adv_col] if args.adv_col else []),
    )
    report = build_report(
        df,
        args.date_col,
        args.asset_col,
        args.weight_col,
        args.return_col,
        args.spread_bps_col,
        args.adv_col,
        args.annualization,
        args.commission_bps,
        args.slippage_bps,
        args.borrow_bps_annual,
        args.nav,
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
