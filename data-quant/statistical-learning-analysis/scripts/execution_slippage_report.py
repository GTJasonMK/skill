#!/usr/bin/env python3
"""Summarize execution slippage and implementation shortfall diagnostics.

Requires the shared bundle core dependencies. Input is an order/fill CSV with side, quantity,
decision price, and fill price. Positive slippage means execution cost.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import (
    mean,
    parse_float,
    quantile,
    read_dataframe,
    require_columns,
    sorted_group_keys,
    summarize_values,
)


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")


def parse_side(value: str, buy_values: set[str], sell_values: set[str]) -> int | None:
    clean = value.strip().lower()
    if clean in buy_values:
        return 1
    if clean in sell_values:
        return -1
    return None


def weighted_slippage(items: list[dict[str, Any]], key: str = "slippage_bps") -> float | None:
    total_notional = sum(item["notional"] for item in items)
    if total_notional == 0:
        return None
    return sum(item["notional"] * item[key] for item in items if item[key] is not None) / total_notional


def summarize_orders(items: list[dict[str, Any]]) -> dict[str, Any]:
    notionals = [item["notional"] for item in items]
    slips = [item["slippage_bps"] for item in items]
    benchmark_slips = [
        item["benchmark_slippage_bps"] for item in items if item["benchmark_slippage_bps"] is not None
    ]
    participation = [item["participation"] for item in items if item["participation"] is not None]
    total_notional = sum(notionals)
    total_cost = sum(item["cost_dollars"] for item in items)
    return {
        "n_orders": len(items),
        "total_notional": total_notional,
        "total_cost_dollars": total_cost,
        "mean_slippage_bps": mean(slips),
        "median_slippage_bps": quantile(slips, 0.5),
        "p90_slippage_bps": quantile(slips, 0.9),
        "notional_weighted_slippage_bps": total_cost / total_notional * 10000 if total_notional else None,
        "mean_benchmark_slippage_bps": mean(benchmark_slips),
        "notional_weighted_benchmark_slippage_bps": weighted_slippage(
            [item for item in items if item["benchmark_slippage_bps"] is not None], "benchmark_slippage_bps"
        ),
        "participation_summary": summarize_values(participation),
    }


def build_report(
    rows: list[dict[str, str]],
    date_col: str,
    asset_col: str,
    side_col: str,
    quantity_col: str,
    decision_price_col: str,
    fill_price_col: str,
    benchmark_price_col: str | None,
    adv_col: str | None,
    adv_mode: str,
    spread_bps_col: str | None,
    buy_values: set[str],
    sell_values: set[str],
) -> dict[str, Any]:
    orders = []
    dropped = 0
    for row in rows:
        side_sign = parse_side(row.get(side_col, ""), buy_values, sell_values)
        quantity = parse_float(row.get(quantity_col))
        decision_price = parse_float(row.get(decision_price_col))
        fill_price = parse_float(row.get(fill_price_col))
        benchmark_price = parse_float(row.get(benchmark_price_col)) if benchmark_price_col else None
        adv = parse_float(row.get(adv_col)) if adv_col else None
        spread_bps = parse_float(row.get(spread_bps_col)) if spread_bps_col else None
        date = row.get(date_col, "")
        asset = row.get(asset_col, "")
        if (
            not date
            or not asset
            or side_sign is None
            or quantity is None
            or decision_price is None
            or fill_price is None
            or quantity == 0
            or decision_price <= 0
            or fill_price <= 0
        ):
            dropped += 1
            continue
        if benchmark_price_col and (benchmark_price is None or benchmark_price <= 0):
            dropped += 1
            continue
        if adv_col and (adv is None or adv <= 0):
            dropped += 1
            continue
        quantity_abs = abs(quantity)
        notional = quantity_abs * decision_price
        slippage_bps = side_sign * (fill_price - decision_price) / decision_price * 10000
        benchmark_slippage_bps = (
            side_sign * (fill_price - benchmark_price) / benchmark_price * 10000
            if benchmark_price is not None
            else None
        )
        participation = None
        if adv is not None:
            participation = quantity_abs / adv if adv_mode == "shares" else notional / adv
        orders.append(
            {
                "date": date,
                "asset": asset,
                "side": "buy" if side_sign == 1 else "sell",
                "quantity": quantity_abs,
                "decision_price": decision_price,
                "fill_price": fill_price,
                "benchmark_price": benchmark_price,
                "notional": notional,
                "slippage_bps": slippage_bps,
                "benchmark_slippage_bps": benchmark_slippage_bps,
                "cost_dollars": notional * slippage_bps / 10000,
                "adv": adv,
                "adv_mode": adv_mode if adv is not None else None,
                "participation": participation,
                "spread_bps": spread_bps,
                "slippage_to_spread": slippage_bps / spread_bps if spread_bps not in {None, 0} else None,
            }
        )

    by_asset: dict[str, list[dict[str, Any]]] = {}
    by_side: dict[str, list[dict[str, Any]]] = {}
    by_date: dict[str, list[dict[str, Any]]] = {}
    for order in orders:
        by_asset.setdefault(order["asset"], []).append(order)
        by_side.setdefault(order["side"], []).append(order)
        by_date.setdefault(order["date"], []).append(order)

    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "side_col": side_col,
        "quantity_col": quantity_col,
        "decision_price_col": decision_price_col,
        "fill_price_col": fill_price_col,
        "benchmark_price_col": benchmark_price_col,
        "adv_col": adv_col,
        "adv_mode": adv_mode,
        "spread_bps_col": spread_bps_col,
        "rows_used": len(orders),
        "rows_dropped": dropped,
        "overall": summarize_orders(orders),
        "by_side": {side: summarize_orders(items) for side, items in sorted(by_side.items())},
        "by_asset": {asset: summarize_orders(items) for asset, items in sorted(by_asset.items())},
        "by_date": {date: summarize_orders(by_date[date]) for date in sorted_group_keys(list(by_date))},
        "orders": orders,
        "notes": [
            "Positive slippage means execution cost relative to the decision price.",
            "Decision price should be the price available when the order decision was made.",
            "This report summarizes realized fills; it does not simulate queue position, "
            "partial fills, or market impact.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    overall = report["overall"]
    lines = [
        "# Execution Slippage Report",
        "",
        f"- Rows used: {report['rows_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        f"- Total notional: {overall['total_notional']}",
        f"- Total cost dollars: {overall['total_cost_dollars']}",
        f"- Notional-weighted slippage bps: {overall['notional_weighted_slippage_bps']}",
        f"- Mean slippage bps: {overall['mean_slippage_bps']}",
        f"- P90 slippage bps: {overall['p90_slippage_bps']}",
        "",
        "## By Side",
        "",
        "| Side | Orders | Notional | Cost dollars | Weighted slippage bps | "
        "Mean slippage bps | Mean participation |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for side, item in report["by_side"].items():
        lines.append(
            f"| {side} | {item['n_orders']} | {item['total_notional']} | "
            f"{item['total_cost_dollars']} | "
            f"{item['notional_weighted_slippage_bps']} | "
            f"{item['mean_slippage_bps']} | "
            f"{item['participation_summary']['mean']} |"
        )
    lines.extend(
        [
            "",
            "## By Asset",
            "",
            "| Asset | Orders | Notional | Cost dollars | Weighted slippage bps | "
            "P90 slippage bps | Mean participation |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for asset, item in report["by_asset"].items():
        lines.append(
            f"| {asset} | {item['n_orders']} | {item['total_notional']} | "
            f"{item['total_cost_dollars']} | "
            f"{item['notional_weighted_slippage_bps']} | "
            f"{item['p90_slippage_bps']} | "
            f"{item['participation_summary']['mean']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize execution slippage and implementation shortfall diagnostics."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--side-col", required=True)
    parser.add_argument("--quantity-col", required=True)
    parser.add_argument("--decision-price-col", required=True)
    parser.add_argument("--fill-price-col", required=True)
    parser.add_argument("--benchmark-price-col")
    parser.add_argument("--adv-col")
    parser.add_argument("--adv-mode", choices=["dollars", "shares"], default="dollars")
    parser.add_argument("--spread-bps-col")
    parser.add_argument("--buy-values", default="buy,b,1,long")
    parser.add_argument("--sell-values", default="sell,s,-1,short")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    df = read_dataframe(args.csv_path)

    header, rows = _df_to_rows(df)
    optional = [col for col in [args.benchmark_price_col, args.adv_col, args.spread_bps_col] if col]
    require_columns(
        header,
        [
            args.date_col,
            args.asset_col,
            args.side_col,
            args.quantity_col,
            args.decision_price_col,
            args.fill_price_col,
        ]
        + optional,
    )
    buy_values = {item.strip().lower() for item in args.buy_values.split(",") if item.strip()}
    sell_values = {item.strip().lower() for item in args.sell_values.split(",") if item.strip()}
    report = build_report(
        rows,
        args.date_col,
        args.asset_col,
        args.side_col,
        args.quantity_col,
        args.decision_price_col,
        args.fill_price_col,
        args.benchmark_price_col,
        args.adv_col,
        args.adv_mode,
        args.spread_bps_col,
        buy_values,
        sell_values,
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
