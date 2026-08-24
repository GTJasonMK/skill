#!/usr/bin/env python3
"""Estimate selected-name and factor-rank turnover across rebalance dates.

Input is a long CSV with one row per date-asset factor observation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import read_dataframe, require_columns, summarize_series


def _selected_positions(
    items: pd.DataFrame, asset_col: str, factor_col: str, top_frac: float, side: str
) -> dict[str, float]:
    ordered = items.sort_values(factor_col).reset_index(drop=True)
    n = len(ordered)
    k = max(1, int(round(n * top_frac)))
    positions: dict[str, float] = {}
    if side in {"short", "long_short"}:
        for asset in ordered[asset_col].head(k):
            positions[asset] = positions.get(asset, 0.0) - 1.0 / k
    if side in {"long", "long_short"}:
        for asset in ordered[asset_col].tail(k):
            positions[asset] = positions.get(asset, 0.0) + 1.0 / k
    return positions


def _weighted_turnover(prev: dict[str, float], cur: dict[str, float]) -> float:
    assets = set(prev) | set(cur)
    return 0.5 * sum(abs(cur.get(a, 0.0) - prev.get(a, 0.0)) for a in assets)


def _membership_overlap(prev: dict[str, float], cur: dict[str, float]) -> float | None:
    prev_set = {a for a, w in prev.items() if w != 0}
    cur_set = {a for a, w in cur.items() if w != 0}
    union = prev_set | cur_set
    if not union:
        return None
    return len(prev_set & cur_set) / len(union)


def _rank_autocorrelation(
    prev_items: pd.DataFrame, cur_items: pd.DataFrame, asset_col: str, factor_col: str
) -> float | None:
    prev_ranks = prev_items.set_index(asset_col)[factor_col].rank(method="average")
    cur_ranks = cur_items.set_index(asset_col)[factor_col].rank(method="average")
    common = prev_ranks.index.intersection(cur_ranks.index)
    if len(common) < 2:
        return None
    corr = prev_ranks.loc[common].corr(cur_ranks.loc[common], method="spearman")
    return None if pd.isna(corr) else float(corr)


def build_report(
    df: pd.DataFrame,
    date_col: str,
    asset_col: str,
    factor_col: str,
    top_frac: float,
    side: str,
    min_assets: int,
) -> dict[str, Any]:
    df = df.copy()
    df[factor_col] = pd.to_numeric(df[factor_col], errors="coerce")
    rows_in = len(df)
    df = df.dropna(subset=[date_col, asset_col, factor_col])
    df = df[df[asset_col].astype(str).str.len() > 0]
    dropped = rows_in - len(df)

    snapshots: list[dict[str, Any]] = []
    skipped_dates = 0
    for date, g in df.groupby(date_col, sort=True):
        if len(g) < min_assets:
            skipped_dates += 1
            continue
        positions = _selected_positions(g, asset_col, factor_col, top_frac, side)
        snapshots.append(
            {
                "date": date if not isinstance(date, pd.Timestamp) else date.isoformat(),
                "n_assets": int(len(g)),
                "items": g[[asset_col, factor_col]].reset_index(drop=True),
                "positions": positions,
            }
        )

    transitions = []
    for prev, cur in zip(snapshots, snapshots[1:], strict=False):
        transitions.append(
            {
                "from_date": prev["date"],
                "to_date": cur["date"],
                "prev_n_assets": prev["n_assets"],
                "cur_n_assets": cur["n_assets"],
                "weight_turnover": _weighted_turnover(prev["positions"], cur["positions"]),
                "membership_overlap": _membership_overlap(prev["positions"], cur["positions"]),
                "rank_autocorrelation": _rank_autocorrelation(
                    prev["items"], cur["items"], asset_col, factor_col
                ),
            }
        )

    turnovers = [item["weight_turnover"] for item in transitions]
    overlaps = [item["membership_overlap"] for item in transitions if item["membership_overlap"] is not None]
    rank_autos = [
        item["rank_autocorrelation"] for item in transitions if item["rank_autocorrelation"] is not None
    ]
    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "factor_col": factor_col,
        "top_frac": top_frac,
        "side": side,
        "min_assets_per_date": min_assets,
        "rows_dropped": dropped,
        "skipped_dates": skipped_dates,
        "periods_used": len(snapshots),
        "turnover_summary": summarize_series(turnovers),
        "membership_overlap_summary": summarize_series(overlaps),
        "rank_autocorrelation_summary": summarize_series(rank_autos),
        "transitions": transitions,
        "notes": [
            "Selected-name turnover uses equal-weight selected portfolios formed from factor ranks.",
            "Weight turnover is 0.5 * sum(abs(current_weight - previous_weight)) across selected assets.",
            "Rank autocorrelation is measured only on assets present in both adjacent cross-sections.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    turn = report["turnover_summary"]
    overlap = report["membership_overlap_summary"]
    rank_auto = report["rank_autocorrelation_summary"]
    lines = [
        "# Factor Turnover Report",
        "",
        f"- Factor: {report['factor_col']}",
        f"- Side: {report['side']}",
        f"- Top fraction: {report['top_frac']}",
        f"- Periods used: {report['periods_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        "",
        "| Metric | N | Mean | Stdev | Min | Max |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| Weight turnover | {turn['n']} | {turn['mean']} | {turn['stdev']} | {turn['min']} | {turn['max']} |",
        f"| Membership overlap | {overlap['n']} | {overlap['mean']} | {overlap['stdev']} | {overlap['min']} | {overlap['max']} |",
        f"| Rank autocorrelation | {rank_auto['n']} | {rank_auto['mean']} | {rank_auto['stdev']} | {rank_auto['min']} | {rank_auto['max']} |",
        "",
        "## Transitions",
        "",
        "| From | To | Turnover | Overlap | Rank autocorr |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["transitions"]:
        lines.append(
            f"| {item['from_date']} | {item['to_date']} | {item['weight_turnover']} | {item['membership_overlap']} | {item['rank_autocorrelation']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Estimate selected-name and factor-rank turnover across rebalance dates."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--factor-col", required=True)
    parser.add_argument("--top-frac", type=float, default=0.2)
    parser.add_argument("--side", choices=["long", "short", "long_short"], default="long_short")
    parser.add_argument("--min-assets-per-date", type=int, default=5)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.top_frac <= 0 or args.top_frac > 0.5:
        raise SystemExit("--top-frac must be in (0, 0.5].")
    df = read_dataframe(args.csv_path)
    require_columns(df, [args.date_col, args.asset_col, args.factor_col])
    report = build_report(
        df, args.date_col, args.asset_col, args.factor_col, args.top_frac, args.side, args.min_assets_per_date
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
