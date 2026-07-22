#!/usr/bin/env python3
"""Summarize order exceptions, fill quality, and rejection/partial-fill rates.

Standard-library only. Input is an order or fill CSV with date, asset, order
status, order quantity, and filled quantity. The report treats unfilled,
rejected, cancelled, and partial orders as production exceptions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from quant_utils import parse_float, read_dataframe, require_columns, sorted_group_keys, summarize_values

import pandas as pd


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")




STATUS_ALIASES = {
    "filled": "filled",
    "fill": "filled",
    "done": "filled",
    "complete": "filled",
    "completed": "filled",
    "partial": "partial",
    "partially_filled": "partial",
    "partially filled": "partial",
    "rejected": "rejected",
    "reject": "rejected",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "cancel": "cancelled",
    "expired": "expired",
    "open": "open",
    "new": "open",
    "pending": "open",
}


EXCEPTION_STATUSES = {"partial", "rejected", "cancelled", "expired", "open", "unknown"}


def normalize_status(value: str) -> str:
    clean = value.strip().lower()
    return STATUS_ALIASES.get(clean, "unknown")


def ratio(num: float, den: float) -> float | None:
    return num / den if den else None


def summarize_orders(items: list[dict[str, Any]]) -> dict[str, Any]:
    order_qty = [item["order_qty"] for item in items]
    filled_qty = [item["filled_qty"] for item in items]
    fill_rates = [item["fill_rate"] for item in items if item["fill_rate"] is not None]
    notional = [item["notional"] for item in items if item["notional"] is not None]
    status_counts: dict[str, int] = {}
    for item in items:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1
    total_qty = sum(order_qty)
    total_filled = sum(filled_qty)
    total_orders = len(items)
    exception_count = sum(item["is_exception"] for item in items)
    return {
        "orders": total_orders,
        "status_counts": status_counts,
        "exception_count": exception_count,
        "exception_rate": ratio(exception_count, total_orders),
        "total_order_qty": total_qty,
        "total_filled_qty": total_filled,
        "aggregate_fill_rate": ratio(total_filled, total_qty),
        "mean_order_fill_rate": summarize_values(fill_rates)["mean"],
        "fill_rate_summary": summarize_values(fill_rates),
        "notional_summary": summarize_values(notional),
    }


def build_report(
    rows: list[dict[str, str]],
    date_col: str,
    asset_col: str,
    status_col: str,
    quantity_col: str,
    filled_quantity_col: str,
    reason_col: str | None,
    venue_col: str | None,
    strategy_col: str | None,
    notional_col: str | None,
    max_exception_rate: float,
    min_aggregate_fill_rate: float,
) -> dict[str, Any]:
    orders = []
    dropped = 0
    for i, row in enumerate(rows, start=1):
        date = row.get(date_col, "")
        asset = row.get(asset_col, "")
        status = normalize_status(row.get(status_col, ""))
        order_qty = parse_float(row.get(quantity_col))
        filled_qty = parse_float(row.get(filled_quantity_col))
        notional = parse_float(row.get(notional_col)) if notional_col else None
        reason = row.get(reason_col, "").strip() if reason_col else ""
        venue = row.get(venue_col, "").strip() if venue_col else ""
        strategy = row.get(strategy_col, "").strip() if strategy_col else ""
        if not date or not asset or order_qty is None or filled_qty is None or order_qty <= 0 or filled_qty < 0:
            dropped += 1
            continue
        filled_qty = min(filled_qty, order_qty)
        fill_rate = filled_qty / order_qty
        if status == "filled" and fill_rate < 0.999999:
            status = "partial"
        is_exception = status in EXCEPTION_STATUSES or fill_rate < 0.999999
        orders.append(
            {
                "row_number": i,
                "date": date,
                "asset": asset,
                "status": status,
                "order_qty": order_qty,
                "filled_qty": filled_qty,
                "unfilled_qty": order_qty - filled_qty,
                "fill_rate": fill_rate,
                "reason": reason,
                "venue": venue,
                "strategy": strategy,
                "notional": notional,
                "is_exception": is_exception,
            }
        )

    by_date: dict[str, list[dict[str, Any]]] = {}
    by_asset: dict[str, list[dict[str, Any]]] = {}
    by_status: dict[str, list[dict[str, Any]]] = {}
    by_reason: dict[str, list[dict[str, Any]]] = {}
    by_venue: dict[str, list[dict[str, Any]]] = {}
    by_strategy: dict[str, list[dict[str, Any]]] = {}
    for order in orders:
        by_date.setdefault(order["date"], []).append(order)
        by_asset.setdefault(order["asset"], []).append(order)
        by_status.setdefault(order["status"], []).append(order)
        if order["reason"]:
            by_reason.setdefault(order["reason"], []).append(order)
        if order["venue"]:
            by_venue.setdefault(order["venue"], []).append(order)
        if order["strategy"]:
            by_strategy.setdefault(order["strategy"], []).append(order)

    overall = summarize_orders(orders)
    alerts = []
    if overall["exception_rate"] is not None and overall["exception_rate"] > max_exception_rate:
        alerts.append({"severity": "warning", "name": "high_exception_rate", "detail": f"Exception rate above {max_exception_rate}."})
    if overall["aggregate_fill_rate"] is not None and overall["aggregate_fill_rate"] < min_aggregate_fill_rate:
        alerts.append({"severity": "warning", "name": "low_aggregate_fill_rate", "detail": f"Aggregate fill rate below {min_aggregate_fill_rate}."})
    rejected = overall["status_counts"].get("rejected", 0)
    if rejected:
        alerts.append({"severity": "warning", "name": "rejected_orders", "detail": f"{rejected} rejected orders found."})

    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "status_col": status_col,
        "quantity_col": quantity_col,
        "filled_quantity_col": filled_quantity_col,
        "reason_col": reason_col,
        "venue_col": venue_col,
        "strategy_col": strategy_col,
        "notional_col": notional_col,
        "max_exception_rate": max_exception_rate,
        "min_aggregate_fill_rate": min_aggregate_fill_rate,
        "rows_used": len(orders),
        "rows_dropped": dropped,
        "overall": overall,
        "by_date": {date: summarize_orders(by_date[date]) for date in sorted_group_keys(list(by_date))},
        "by_asset": {asset: summarize_orders(by_asset[asset]) for asset in sorted_group_keys(list(by_asset))},
        "by_status": {status: summarize_orders(items) for status, items in sorted(by_status.items())},
        "by_reason": {reason: summarize_orders(items) for reason, items in sorted(by_reason.items())},
        "by_venue": {venue: summarize_orders(items) for venue, items in sorted(by_venue.items())},
        "by_strategy": {strategy: summarize_orders(items) for strategy, items in sorted(by_strategy.items())},
        "alerts": alerts,
        "exceptions": [item for item in orders if item["is_exception"]],
        "orders": orders,
        "notes": [
            "Rejected, cancelled, expired, open, unknown, and partially filled orders are treated as exceptions.",
            "Fill rate is filled quantity divided by order quantity after capping filled quantity at order quantity.",
            "Use this with execution_slippage_report.py to separate fill availability from fill price quality.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    overall = report["overall"]
    lines = [
        "# Order Exception Report",
        "",
        f"- Rows used: {report['rows_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        f"- Orders: {overall['orders']}",
        f"- Exception rate: {overall['exception_rate']}",
        f"- Aggregate fill rate: {overall['aggregate_fill_rate']}",
        f"- Exception count: {overall['exception_count']}",
        "",
        "## Alerts",
        "",
    ]
    if report["alerts"]:
        lines.extend(f"- {item['severity']}: {item['name']} - {item['detail']}" for item in report["alerts"])
    else:
        lines.append("- none")
    lines.extend(["", "## Status Counts", ""])
    for status, count in sorted(overall["status_counts"].items()):
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## By Date", "", "| Date | Orders | Exception rate | Aggregate fill rate |", "| --- | --- | --- | --- |"])
    for date, item in report["by_date"].items():
        lines.append(f"| {date} | {item['orders']} | {item['exception_rate']} | {item['aggregate_fill_rate']} |")
    lines.extend(["", "## By Asset", "", "| Asset | Orders | Exception rate | Aggregate fill rate |", "| --- | --- | --- | --- |"])
    for asset, item in report["by_asset"].items():
        lines.append(f"| {asset} | {item['orders']} | {item['exception_rate']} | {item['aggregate_fill_rate']} |")
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize order exceptions, fill quality, and rejection/partial-fill rates.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--status-col", required=True)
    parser.add_argument("--quantity-col", required=True)
    parser.add_argument("--filled-quantity-col", required=True)
    parser.add_argument("--reason-col")
    parser.add_argument("--venue-col")
    parser.add_argument("--strategy-col")
    parser.add_argument("--notional-col")
    parser.add_argument("--max-exception-rate", type=float, default=0.05)
    parser.add_argument("--min-aggregate-fill-rate", type=float, default=0.98)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if not 0 <= args.max_exception_rate <= 1:
        raise SystemExit("--max-exception-rate must be in [0, 1].")
    if not 0 <= args.min_aggregate_fill_rate <= 1:
        raise SystemExit("--min-aggregate-fill-rate must be in [0, 1].")
    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    optional = [col for col in [args.reason_col, args.venue_col, args.strategy_col, args.notional_col] if col]
    require_columns(header, [args.date_col, args.asset_col, args.status_col, args.quantity_col, args.filled_quantity_col] + optional)
    report = build_report(
        rows,
        args.date_col,
        args.asset_col,
        args.status_col,
        args.quantity_col,
        args.filled_quantity_col,
        args.reason_col,
        args.venue_col,
        args.strategy_col,
        args.notional_col,
        args.max_exception_rate,
        args.min_aggregate_fill_rate,
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
