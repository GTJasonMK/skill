#!/usr/bin/env python3
"""Monitor live factor or alpha-signal health over time.

Requires the shared bundle core dependencies. Input is a long CSV with date, asset, signal value, and
forward return. The report tracks coverage, IC/rank IC, top-minus-bottom spread,
selection turnover, and recent-window alerts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import (
    correlation,
    mean,
    parse_float,
    read_dataframe,
    require_columns,
    sorted_group_keys,
    spearman,
    stdev,
    summarize_values,
)


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")


def selected_assets(items: list[dict[str, Any]], selection_frac: float) -> set[str]:
    ordered = sorted(items, key=lambda item: item["signal"], reverse=True)
    k = max(1, round(len(ordered) * selection_frac))
    return {item["asset"] for item in ordered[:k]}


def top_bottom_spread(items: list[dict[str, Any]], selection_frac: float) -> float | None:
    if len(items) < 2:
        return None
    ordered = sorted(items, key=lambda item: item["signal"])
    k = max(1, round(len(ordered) * selection_frac))
    bottom = [item["forward_return"] for item in ordered[:k]]
    top = [item["forward_return"] for item in ordered[-k:]]
    top_mean = mean(top)
    bottom_mean = mean(bottom)
    return top_mean - bottom_mean if top_mean is not None and bottom_mean is not None else None


def rank_autocorr(prev_signals: dict[str, float], cur_signals: dict[str, float]) -> float | None:
    common = sorted(set(prev_signals) & set(cur_signals))
    if len(common) < 2:
        return None
    return spearman([prev_signals[asset] for asset in common], [cur_signals[asset] for asset in common])


def build_report(
    rows: list[dict[str, str]],
    date_col: str,
    asset_col: str,
    signal_col: str,
    forward_return_col: str,
    selection_frac: float,
    recent_dates: int,
    min_assets: int,
    min_recent_rank_ic: float,
    min_positive_rate: float,
    max_mean_turnover: float,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    dropped = 0
    for row in rows:
        date = row.get(date_col, "")
        asset = row.get(asset_col, "")
        signal = parse_float(row.get(signal_col))
        forward_return = parse_float(row.get(forward_return_col))
        if not date or not asset or signal is None or forward_return is None:
            dropped += 1
            continue
        grouped.setdefault(date, []).append(
            {"asset": asset, "signal": signal, "forward_return": forward_return}
        )

    dates = sorted_group_keys(list(grouped))
    per_date = []
    prev_selected: set[str] | None = None
    prev_signals: dict[str, float] = {}
    for date in dates:
        items = grouped[date]
        signals = [item["signal"] for item in items]
        returns = [item["forward_return"] for item in items]
        cur_selected = selected_assets(items, selection_frac)
        cur_signals = {item["asset"]: item["signal"] for item in items}
        turnover = None
        overlap_rate = None
        if prev_selected is not None:
            union = cur_selected | prev_selected
            overlap = cur_selected & prev_selected
            overlap_rate = len(overlap) / len(union) if union else None
            turnover = 1 - overlap_rate if overlap_rate is not None else None
        per_date.append(
            {
                "date": date,
                "n_assets": len(items),
                "signal_mean": mean(signals),
                "signal_stdev": stdev(signals),
                "forward_return_mean": mean(returns),
                "ic": correlation(signals, returns),
                "rank_ic": spearman(signals, returns),
                "top_minus_bottom_return": top_bottom_spread(items, selection_frac),
                "selected_count": len(cur_selected),
                "selection_overlap_rate": overlap_rate,
                "selection_turnover": turnover,
                "rank_autocorrelation": rank_autocorr(prev_signals, cur_signals),
            }
        )
        prev_selected = cur_selected
        prev_signals = cur_signals

    recent = per_date[-recent_dates:] if recent_dates else per_date
    all_rank_ic = [item["rank_ic"] for item in per_date if item["rank_ic"] is not None]
    recent_rank_ic = [item["rank_ic"] for item in recent if item["rank_ic"] is not None]
    recent_turnover = [
        item["selection_turnover"] for item in recent if item["selection_turnover"] is not None
    ]
    recent_n_assets = [item["n_assets"] for item in recent]
    recent_spreads = [
        item["top_minus_bottom_return"] for item in recent if item["top_minus_bottom_return"] is not None
    ]
    recent_rank_ic_summary = summarize_values(recent_rank_ic)
    recent_turnover_summary = summarize_values(recent_turnover)
    alerts = []
    if recent_n_assets and min(recent_n_assets) < min_assets:
        alerts.append(
            {
                "severity": "warning",
                "name": "low_coverage",
                "detail": f"Recent minimum asset count below {min_assets}.",
            }
        )
    if recent_rank_ic_summary["mean"] is not None and recent_rank_ic_summary["mean"] < min_recent_rank_ic:
        alerts.append(
            {
                "severity": "warning",
                "name": "weak_recent_rank_ic",
                "detail": f"Recent mean rank IC below {min_recent_rank_ic}.",
            }
        )
    if (
        recent_rank_ic_summary["positive_rate"] is not None
        and recent_rank_ic_summary["positive_rate"] < min_positive_rate
    ):
        alerts.append(
            {
                "severity": "warning",
                "name": "low_rank_ic_positive_rate",
                "detail": f"Recent rank IC positive rate below {min_positive_rate}.",
            }
        )
    if recent_turnover_summary["mean"] is not None and recent_turnover_summary["mean"] > max_mean_turnover:
        alerts.append(
            {
                "severity": "warning",
                "name": "high_selection_turnover",
                "detail": f"Recent mean selection turnover above {max_mean_turnover}.",
            }
        )

    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "signal_col": signal_col,
        "forward_return_col": forward_return_col,
        "selection_frac": selection_frac,
        "recent_dates": recent_dates,
        "min_assets": min_assets,
        "min_recent_rank_ic": min_recent_rank_ic,
        "min_positive_rate": min_positive_rate,
        "max_mean_turnover": max_mean_turnover,
        "rows_used": sum(len(grouped[date]) for date in dates),
        "rows_dropped": dropped,
        "dates_used": len(dates),
        "all_rank_ic_summary": summarize_values(all_rank_ic),
        "recent_rank_ic_summary": recent_rank_ic_summary,
        "recent_turnover_summary": recent_turnover_summary,
        "recent_asset_count_summary": summarize_values([float(value) for value in recent_n_assets]),
        "recent_spread_summary": summarize_values(recent_spreads),
        "alerts": alerts,
        "per_date": per_date,
        "notes": [
            "Signal and forward return must be aligned so the signal is known before the return horizon.",
            "Rank IC health is signal evidence, not proof of live portfolio profitability.",
            "Turnover and coverage alerts should be reviewed with costs, liquidity, and universe changes.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    recent_ic = report["recent_rank_ic_summary"]
    turnover = report["recent_turnover_summary"]
    assets = report["recent_asset_count_summary"]
    spread = report["recent_spread_summary"]
    lines = [
        "# Signal Health Monitor",
        "",
        f"- Rows used: {report['rows_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        f"- Dates used: {report['dates_used']}",
        f"- Recent window dates: {report['recent_dates']}",
        f"- Recent mean rank IC: {recent_ic['mean']}",
        f"- Recent rank IC t-stat: {recent_ic['t_stat']}",
        f"- Recent rank IC positive rate: {recent_ic['positive_rate']}",
        f"- Recent mean selection turnover: {turnover['mean']}",
        f"- Recent minimum asset count: {assets['min']}",
        f"- Recent mean top-bottom spread: {spread['mean']}",
        "",
        "## Alerts",
        "",
    ]
    if report["alerts"]:
        lines.extend(f"- {item['severity']}: {item['name']} - {item['detail']}" for item in report["alerts"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Per-Date Diagnostics",
            "",
            "| Date | Assets | IC | Rank IC | Top-bottom return | Turnover | Rank autocorr |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in report["per_date"]:
        lines.append(
            f"| {item['date']} | {item['n_assets']} | {item['ic']} | {item['rank_ic']} | {item['top_minus_bottom_return']} | {item['selection_turnover']} | {item['rank_autocorrelation']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor live factor or alpha-signal health over time.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--signal-col", required=True)
    parser.add_argument("--forward-return-col", required=True)
    parser.add_argument("--selection-frac", type=float, default=0.2)
    parser.add_argument("--recent-dates", type=int, default=20)
    parser.add_argument("--min-assets", type=int, default=20)
    parser.add_argument("--min-recent-rank-ic", type=float, default=0.0)
    parser.add_argument("--min-positive-rate", type=float, default=0.5)
    parser.add_argument("--max-mean-turnover", type=float, default=0.8)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if not 0 < args.selection_frac <= 0.5:
        raise SystemExit("--selection-frac must be in (0, 0.5].")
    if args.recent_dates <= 0:
        raise SystemExit("--recent-dates must be positive.")
    if args.min_assets <= 0:
        raise SystemExit("--min-assets must be positive.")
    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    require_columns(header, [args.date_col, args.asset_col, args.signal_col, args.forward_return_col])
    report = build_report(
        rows,
        args.date_col,
        args.asset_col,
        args.signal_col,
        args.forward_return_col,
        args.selection_frac,
        args.recent_dates,
        args.min_assets,
        args.min_recent_rank_ic,
        args.min_positive_rate,
        args.max_mean_turnover,
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
