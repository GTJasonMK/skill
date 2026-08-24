#!/usr/bin/env python3
"""Estimate simple capacity and market-impact diagnostics from weight changes.

Input is a long portfolio CSV with date, asset, target weight, and ADV.
Optional spread bps can be included.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import read_dataframe, require_columns, summarize_series


def build_report(
    df: pd.DataFrame,
    date_col: str,
    asset_col: str,
    weight_col: str,
    adv_col: str,
    spread_bps_col: str | None,
    nav: float,
    max_participation: float,
    impact_bps: float,
    impact_power: float,
) -> dict[str, Any]:
    df = df.copy()
    df[weight_col] = pd.to_numeric(df[weight_col], errors="coerce")
    df[adv_col] = pd.to_numeric(df[adv_col], errors="coerce")
    if spread_bps_col:
        df[spread_bps_col] = pd.to_numeric(df[spread_bps_col], errors="coerce")
    else:
        df["__spread_bps"] = 0.0
    spread_eff = spread_bps_col or "__spread_bps"

    rows_in = len(df)
    df = df.dropna(subset=[date_col, asset_col, weight_col, adv_col, spread_eff])
    df = df[df[adv_col] > 0]
    df = df[df[asset_col].astype(str).str.len() > 0]
    dropped = rows_in - len(df)

    prev_weights: dict[str, float] = {}
    prev_liquidity: dict[str, dict[str, float]] = {}
    periods: list[dict[str, Any]] = []
    for date, g in df.groupby(date_col, sort=True):
        liquidity = {
            row[asset_col]: {"adv": float(row[adv_col]), "spread_bps": float(row[spread_eff])}
            for _, row in g.iterrows()
        }
        current = g.groupby(asset_col)[weight_col].sum().to_dict()
        assets = set(prev_weights) | set(current)
        asset_rows: list[dict[str, Any]] = []
        period_turnover = 0.0
        period_cost = 0.0
        max_part = 0.0
        capacity_limits: list[float] = []
        for asset in sorted(assets):
            delta = abs(current.get(asset, 0.0) - prev_weights.get(asset, 0.0))
            if delta == 0:
                continue
            values = liquidity.get(asset) or prev_liquidity.get(asset)
            if values is None:
                continue
            dollars = delta * nav
            participation = dollars / values["adv"]
            half_spread_cost = delta * values["spread_bps"] / 2 / 10000
            impact_cost = delta * impact_bps * (participation**impact_power) / 10000
            total_cost = half_spread_cost + impact_cost
            period_turnover += 0.5 * delta
            period_cost += total_cost
            max_part = max(max_part, participation)
            if delta > 0:
                capacity_limits.append(max_participation * values["adv"] / delta)
            asset_rows.append(
                {
                    "asset": asset,
                    "weight_change": delta,
                    "dollar_trade": dollars,
                    "adv": values["adv"],
                    "participation": participation,
                    "half_spread_cost": half_spread_cost,
                    "impact_cost": impact_cost,
                    "total_cost": total_cost,
                    "nav_capacity_at_limit": max_participation * values["adv"] / delta if delta > 0 else None,
                }
            )
        periods.append(
            {
                "date": date if not isinstance(date, pd.Timestamp) else date.isoformat(),
                "one_way_turnover": period_turnover,
                "max_adv_participation": max_part,
                "estimated_cost": period_cost,
                "estimated_cost_bps": period_cost * 10000,
                "binding_nav_capacity": min(capacity_limits) if capacity_limits else None,
                "assets": asset_rows,
            }
        )
        prev_weights = current
        prev_liquidity.update(liquidity)

    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "weight_col": weight_col,
        "adv_col": adv_col,
        "spread_bps_col": spread_bps_col,
        "nav": nav,
        "max_participation": max_participation,
        "impact_bps_at_100pct_adv": impact_bps,
        "impact_power": impact_power,
        "rows_dropped": dropped,
        "periods_used": len(periods),
        "turnover_summary": summarize_series([item["one_way_turnover"] for item in periods]),
        "participation_summary": summarize_series([item["max_adv_participation"] for item in periods]),
        "cost_bps_summary": summarize_series([item["estimated_cost_bps"] for item in periods]),
        "binding_capacity_summary": summarize_series(
            [item["binding_nav_capacity"] for item in periods if item["binding_nav_capacity"] is not None]
        ),
        "periods": periods,
        "notes": [
            "Capacity is approximated from target weight changes, NAV, ADV, and a participation cap.",
            "Impact model is a simple power law and should be calibrated to asset class and execution style.",
            "This does not model intraday volume curves, queue priority, borrow, halts, "
            "or nonlinear liquidity regimes.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    turn = report["turnover_summary"]
    part = report["participation_summary"]
    cost = report["cost_bps_summary"]
    cap = report["binding_capacity_summary"]
    lines = [
        "# Capacity and Market Impact Report",
        "",
        f"- NAV: {report['nav']}",
        f"- Max ADV participation: {report['max_participation']}",
        f"- Periods used: {report['periods_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        "",
        f"- Mean one-way turnover: {turn['mean']}",
        f"- Mean max ADV participation: {part['mean']}",
        f"- Mean estimated cost bps: {cost['mean']}",
        f"- Minimum binding NAV capacity: {cap['min']}",
        "",
        "| Date | Turnover | Max participation | Cost bps | Binding NAV capacity |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["periods"]:
        lines.append(
            f"| {item['date']} | {item['one_way_turnover']} | "
            f"{item['max_adv_participation']} | {item['estimated_cost_bps']} | "
            f"{item['binding_nav_capacity']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Estimate simple capacity and market-impact diagnostics from weight changes."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--weight-col", required=True)
    parser.add_argument("--adv-col", required=True)
    parser.add_argument("--spread-bps-col")
    parser.add_argument("--nav", type=float, required=True)
    parser.add_argument("--max-participation", type=float, default=0.1)
    parser.add_argument(
        "--impact-bps",
        type=float,
        default=50.0,
        help="Impact bps at full ADV participation before power scaling.",
    )
    parser.add_argument("--impact-power", type=float, default=0.5)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.nav <= 0:
        raise SystemExit("--nav must be positive.")
    if args.max_participation <= 0:
        raise SystemExit("--max-participation must be positive.")
    df = read_dataframe(args.csv_path)
    require_columns(
        df,
        [args.date_col, args.asset_col, args.weight_col, args.adv_col]
        + ([args.spread_bps_col] if args.spread_bps_col else []),
    )
    report = build_report(
        df,
        args.date_col,
        args.asset_col,
        args.weight_col,
        args.adv_col,
        args.spread_bps_col,
        args.nav,
        args.max_participation,
        args.impact_bps,
        args.impact_power,
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
