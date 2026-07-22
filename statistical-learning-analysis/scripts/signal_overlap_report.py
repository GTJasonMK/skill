#!/usr/bin/env python3
"""Diagnose overlap and redundancy across multiple alpha signal columns.

Standard-library only. Input is a long date-asset CSV with several signal
columns. The report computes per-date pairwise Pearson correlation, Spearman
rank correlation, selected-name overlap, and pair-level redundancy flags.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from quant_utils import (
    correlation,
    parse_float,
    read_dataframe,
    require_columns,
    spearman,
    summarize_values,
)


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")


def selected_assets(items: list[tuple[str, float]], selection_frac: float, side: str) -> set[str]:
    if not items:
        return set()
    reverse = side in {"top", "both"}
    ordered = sorted(items, key=lambda item: item[1], reverse=reverse)
    k = max(1, round(len(ordered) * selection_frac))
    if side == "bottom":
        return {asset for asset, _ in sorted(items, key=lambda item: item[1])[:k]}
    if side == "both":
        bottom = {asset for asset, _ in sorted(items, key=lambda item: item[1])[:k]}
        top = {asset for asset, _ in sorted(items, key=lambda item: item[1], reverse=True)[:k]}
        return top | bottom
    return {asset for asset, _ in ordered[:k]}


def pair_key(a: str, b: str) -> str:
    return f"{a}__{b}"


def build_report(
    rows: list[dict[str, str]],
    date_col: str,
    asset_col: str,
    signal_cols: list[str],
    selection_frac: float,
    selection_side: str,
    corr_threshold: float,
    overlap_threshold: float,
    min_pair_count: int,
) -> dict[str, Any]:
    by_date: dict[str, dict[str, dict[str, float]]] = {}
    dropped = 0
    for row in rows:
        date = row.get(date_col, "")
        asset = row.get(asset_col, "")
        if not date or not asset:
            dropped += 1
            continue
        values = {col: parse_float(row.get(col)) for col in signal_cols}
        clean = {col: value for col, value in values.items() if value is not None}
        if not clean:
            dropped += 1
            continue
        by_date.setdefault(date, {})[asset] = clean

    pair_rows: dict[str, list[dict[str, Any]]] = {}
    signal_rows: dict[str, list[dict[str, Any]]] = {signal: [] for signal in signal_cols}
    per_date = []

    for date in sorted(by_date):
        assets = by_date[date]
        date_signals: dict[str, list[tuple[str, float]]] = {signal: [] for signal in signal_cols}
        for asset, values in assets.items():
            for signal, value in values.items():
                date_signals[signal].append((asset, value))

        selected = {
            signal: selected_assets(items, selection_frac, selection_side)
            for signal, items in date_signals.items()
            if items
        }
        signal_counts = {}
        for signal, items in date_signals.items():
            count = len(items)
            selected_count = len(selected.get(signal, set()))
            signal_counts[signal] = {"coverage": count, "selected_count": selected_count}
            signal_rows[signal].append({"date": date, "coverage": count, "selected_count": selected_count})

        date_pairs = []
        for i, left in enumerate(signal_cols):
            for right in signal_cols[i + 1 :]:
                common_assets = sorted({asset for asset, _ in date_signals[left]} & {asset for asset, _ in date_signals[right]})
                left_map = dict(date_signals[left])
                right_map = dict(date_signals[right])
                left_values = [left_map[asset] for asset in common_assets]
                right_values = [right_map[asset] for asset in common_assets]
                left_selected = selected.get(left, set())
                right_selected = selected.get(right, set())
                union = left_selected | right_selected
                intersection = left_selected & right_selected
                min_selected = min(len(left_selected), len(right_selected))
                pair = {
                    "date": date,
                    "left": left,
                    "right": right,
                    "pair": pair_key(left, right),
                    "common_assets": len(common_assets),
                    "pearson": correlation(left_values, right_values) if len(common_assets) >= min_pair_count else None,
                    "spearman": spearman(left_values, right_values) if len(common_assets) >= min_pair_count else None,
                    "left_selected_count": len(left_selected),
                    "right_selected_count": len(right_selected),
                    "intersection_count": len(intersection),
                    "jaccard_overlap": len(intersection) / len(union) if union else None,
                    "top_overlap_rate": len(intersection) / min_selected if min_selected else None,
                }
                pair_rows.setdefault(pair["pair"], []).append(pair)
                date_pairs.append(pair)
        per_date.append({"date": date, "asset_count": len(assets), "signals": signal_counts, "pairs": date_pairs})

    pair_summary = []
    for key, items in sorted(pair_rows.items()):
        pearson_values = [item["pearson"] for item in items if item["pearson"] is not None]
        spearman_values = [item["spearman"] for item in items if item["spearman"] is not None]
        overlap_values = [item["top_overlap_rate"] for item in items if item["top_overlap_rate"] is not None]
        jaccard_values = [item["jaccard_overlap"] for item in items if item["jaccard_overlap"] is not None]
        mean_abs_spearman = summarize_values([abs(value) for value in spearman_values])["mean"]
        mean_overlap = summarize_values(overlap_values)["mean"]
        redundant = (mean_abs_spearman is not None and mean_abs_spearman >= corr_threshold) or (mean_overlap is not None and mean_overlap >= overlap_threshold)
        pair_summary.append(
            {
                "pair": key,
                "left": items[0]["left"],
                "right": items[0]["right"],
                "dates": len(items),
                "pearson_summary": summarize_values(pearson_values),
                "spearman_summary": summarize_values(spearman_values),
                "abs_spearman_summary": summarize_values([abs(value) for value in spearman_values]),
                "top_overlap_summary": summarize_values(overlap_values),
                "jaccard_summary": summarize_values(jaccard_values),
                "high_abs_spearman_rate": sum(abs(value) >= corr_threshold for value in spearman_values) / len(spearman_values) if spearman_values else None,
                "high_overlap_rate": sum(value >= overlap_threshold for value in overlap_values) / len(overlap_values) if overlap_values else None,
                "redundant": redundant,
            }
        )

    signal_summary = []
    for signal, items in sorted(signal_rows.items()):
        coverages = [float(item["coverage"]) for item in items]
        selected_counts = [float(item["selected_count"]) for item in items]
        redundancy_partners = [item for item in pair_summary if item["redundant"] and signal in {item["left"], item["right"]}]
        overlap_partners = []
        for item in pair_summary:
            if signal not in {item["left"], item["right"]}:
                continue
            overlap_mean = item["top_overlap_summary"]["mean"]
            if overlap_mean is not None:
                overlap_partners.append(overlap_mean)
        signal_summary.append(
            {
                "signal": signal,
                "coverage_summary": summarize_values(coverages),
                "selected_count_summary": summarize_values(selected_counts),
                "redundant_partner_count": len(redundancy_partners),
                "mean_pair_overlap": summarize_values(overlap_partners)["mean"],
            }
        )

    redundant_pairs = [item for item in pair_summary if item["redundant"]]
    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "signal_cols": signal_cols,
        "selection_frac": selection_frac,
        "selection_side": selection_side,
        "corr_threshold": corr_threshold,
        "overlap_threshold": overlap_threshold,
        "min_pair_count": min_pair_count,
        "rows_used": sum(len(assets) for assets in by_date.values()),
        "rows_dropped": dropped,
        "dates_used": len(by_date),
        "pair_count": len(pair_summary),
        "redundant_pair_count": len(redundant_pairs),
        "pair_summary": pair_summary,
        "signal_summary": signal_summary,
        "redundant_pairs": redundant_pairs,
        "per_date": per_date,
        "notes": [
            "High signal correlation or selected-name overlap means signals may not add independent breadth.",
            "Top-name overlap should be reviewed with sector, style, liquidity, and borrow constraints before combining alphas.",
            "This diagnostic uses same-date cross-sectional signal values; it does not prove economic crowding without position and market-wide ownership data.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Signal Overlap Report",
        "",
        f"- Signals: {', '.join(report['signal_cols'])}",
        f"- Dates used: {report['dates_used']}",
        f"- Rows used: {report['rows_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        f"- Pair count: {report['pair_count']}",
        f"- Redundant pair count: {report['redundant_pair_count']}",
        f"- Selection fraction: {report['selection_frac']}",
        f"- Selection side: {report['selection_side']}",
        "",
        "## Redundant Pairs",
        "",
        "| Pair | Dates | Mean abs rank corr | Mean top overlap | High corr rate | High overlap rate |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["redundant_pairs"]:
        lines.append(f"| {item['pair']} | {item['dates']} | {item['abs_spearman_summary']['mean']} | {item['top_overlap_summary']['mean']} | {item['high_abs_spearman_rate']} | {item['high_overlap_rate']} |")
    lines.extend(["", "## All Pairs", "", "| Pair | Mean Pearson | Mean Rank Corr | Mean Top Overlap | Mean Jaccard | Redundant |", "| --- | --- | --- | --- | --- | --- |"])
    for item in report["pair_summary"]:
        lines.append(f"| {item['pair']} | {item['pearson_summary']['mean']} | {item['spearman_summary']['mean']} | {item['top_overlap_summary']['mean']} | {item['jaccard_summary']['mean']} | {item['redundant']} |")
    lines.extend(["", "## Signal Summary", "", "| Signal | Mean coverage | Mean selected | Redundant partners | Mean pair overlap |", "| --- | --- | --- | --- | --- |"])
    for item in report["signal_summary"]:
        lines.append(f"| {item['signal']} | {item['coverage_summary']['mean']} | {item['selected_count_summary']['mean']} | {item['redundant_partner_count']} | {item['mean_pair_overlap']} |")
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose overlap and redundancy across multiple alpha signal columns.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--signal-cols", required=True, help="Comma-separated signal columns.")
    parser.add_argument("--selection-frac", type=float, default=0.2)
    parser.add_argument("--selection-side", choices=["top", "bottom", "both"], default="top")
    parser.add_argument("--corr-threshold", type=float, default=0.8)
    parser.add_argument("--overlap-threshold", type=float, default=0.6)
    parser.add_argument("--min-pair-count", type=int, default=5)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    signal_cols = [col.strip() for col in args.signal_cols.split(",") if col.strip()]
    if len(signal_cols) < 2:
        raise SystemExit("--signal-cols must include at least two columns.")
    if not 0 < args.selection_frac <= 0.5:
        raise SystemExit("--selection-frac must be in (0, 0.5].")
    if args.corr_threshold < 0:
        raise SystemExit("--corr-threshold must be non-negative.")
    if not 0 <= args.overlap_threshold <= 1:
        raise SystemExit("--overlap-threshold must be in [0, 1].")
    if args.min_pair_count < 2:
        raise SystemExit("--min-pair-count must be at least 2.")

    df = read_dataframe(args.csv_path)
    require_columns(df, [args.date_col, args.asset_col] + signal_cols)
    header, rows = _df_to_rows(df)
    report = build_report(
        rows,
        args.date_col,
        args.asset_col,
        signal_cols,
        args.selection_frac,
        args.selection_side,
        args.corr_threshold,
        args.overlap_threshold,
        args.min_pair_count,
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
