#!/usr/bin/env python3
"""Compare live strategy returns with paper or backtest returns.

Requires the shared bundle core dependencies. Input is a time-series CSV with date, live return, and
paper return columns. Positive gap means live outperformed paper.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import (
    correlation,
    parse_float,
    read_dataframe,
    require_columns,
    summarize_returns,
    summarize_values,
)


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")


def max_streak(values: list[float], threshold: float) -> int:
    best = 0
    current = 0
    for value in values:
        if value < threshold:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def rolling_gap(records: list[dict[str, Any]], window: int, annualization: int) -> list[dict[str, Any]]:
    if window <= 1 or len(records) < window:
        return []
    out = []
    for i in range(window - 1, len(records)):
        subset = records[i - window + 1 : i + 1]
        gaps = [item["gap"] for item in subset]
        gap_summary = summarize_values(gaps)
        out.append(
            {
                "end_date": subset[-1]["date"],
                "window": window,
                "mean_gap": gap_summary["mean"],
                "annualized_mean_gap": gap_summary["mean"] * annualization
                if gap_summary["mean"] is not None
                else None,
                "tracking_error": gap_summary["stdev"] * math.sqrt(annualization)
                if gap_summary["stdev"] is not None
                else None,
                "live_paper_correlation": correlation(
                    [item["live_return"] for item in subset], [item["paper_return"] for item in subset]
                ),
                "live_underperformed_periods": sum(item["gap"] < 0 for item in subset),
            }
        )
    return out


def build_report(
    rows: list[dict[str, str]],
    date_col: str,
    live_return_col: str,
    paper_return_col: str,
    benchmark_return_col: str | None,
    annualization: int,
    risk_free_annual: float,
    rolling_window: int,
) -> dict[str, Any]:
    records = []
    dropped = 0
    for row in rows:
        date = row.get(date_col, "")
        live_return = parse_float(row.get(live_return_col))
        paper_return = parse_float(row.get(paper_return_col))
        benchmark_return = parse_float(row.get(benchmark_return_col)) if benchmark_return_col else None
        if not date or live_return is None or paper_return is None:
            dropped += 1
            continue
        if benchmark_return_col and benchmark_return is None:
            dropped += 1
            continue
        records.append(
            {
                "date": date,
                "live_return": live_return,
                "paper_return": paper_return,
                "benchmark_return": benchmark_return,
                "gap": live_return - paper_return,
                "abs_gap": abs(live_return - paper_return),
                "live_active_return": live_return - benchmark_return
                if benchmark_return is not None
                else None,
                "paper_active_return": paper_return - benchmark_return
                if benchmark_return is not None
                else None,
            }
        )
    records.sort(key=lambda item: item["date"])

    live_returns = [item["live_return"] for item in records]
    paper_returns = [item["paper_return"] for item in records]
    gaps = [item["gap"] for item in records]
    abs_gaps = [item["abs_gap"] for item in records]
    gap_summary = summarize_values(gaps)
    abs_gap_summary = summarize_values(abs_gaps)
    worst_gap = min(records, key=lambda item: item["gap"], default=None)
    best_gap = max(records, key=lambda item: item["gap"], default=None)
    tracking_error = (
        gap_summary["stdev"] * math.sqrt(annualization) if gap_summary["stdev"] is not None else None
    )
    benchmark_returns = [item["benchmark_return"] for item in records if item["benchmark_return"] is not None]
    live_active = [item["live_active_return"] for item in records if item["live_active_return"] is not None]
    paper_active = [
        item["paper_active_return"] for item in records if item["paper_active_return"] is not None
    ]

    return {
        "date_col": date_col,
        "live_return_col": live_return_col,
        "paper_return_col": paper_return_col,
        "benchmark_return_col": benchmark_return_col,
        "annualization": annualization,
        "risk_free_annual": risk_free_annual,
        "rolling_window": rolling_window,
        "rows_used": len(records),
        "rows_dropped": dropped,
        "live_return_summary": summarize_returns(live_returns, annualization, risk_free_annual),
        "paper_return_summary": summarize_returns(paper_returns, annualization, risk_free_annual),
        "benchmark_return_summary": summarize_returns(benchmark_returns, annualization, risk_free_annual)
        if benchmark_returns
        else None,
        "live_active_summary": summarize_returns(live_active, annualization, risk_free_annual)
        if live_active
        else None,
        "paper_active_summary": summarize_returns(paper_active, annualization, risk_free_annual)
        if paper_active
        else None,
        "gap_summary": gap_summary,
        "absolute_gap_summary": abs_gap_summary,
        "annualized_mean_gap": gap_summary["mean"] * annualization
        if gap_summary["mean"] is not None
        else None,
        "annualized_tracking_error": tracking_error,
        "live_paper_correlation": correlation(live_returns, paper_returns),
        "live_outperformance_rate": sum(gap > 0 for gap in gaps) / len(gaps) if gaps else None,
        "max_live_underperformance_streak": max_streak(gaps, 0.0),
        "worst_gap_date": worst_gap["date"] if worst_gap else None,
        "worst_gap": worst_gap["gap"] if worst_gap else None,
        "best_gap_date": best_gap["date"] if best_gap else None,
        "best_gap": best_gap["gap"] if best_gap else None,
        "rolling_gap": rolling_gap(records, rolling_window, annualization),
        "records": records,
        "notes": [
            "Positive gap means live return exceeded paper return for the same period.",
            "Paper returns must use the same timing convention as live returns before interpreting drift.",
            "Persistent negative gap usually points to costs, slippage, borrow, data differences, capacity, or implementation bugs.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    live = report["live_return_summary"]
    paper = report["paper_return_summary"]
    gap = report["gap_summary"]
    lines = [
        "# Live vs Paper Report",
        "",
        f"- Rows used: {report['rows_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        f"- Live annualized return: {live['annualized_return_geometric']}",
        f"- Paper annualized return: {paper['annualized_return_geometric']}",
        f"- Annualized mean gap: {report['annualized_mean_gap']}",
        f"- Annualized tracking error: {report['annualized_tracking_error']}",
        f"- Live-paper correlation: {report['live_paper_correlation']}",
        f"- Live outperformance rate: {report['live_outperformance_rate']}",
        f"- Max live underperformance streak: {report['max_live_underperformance_streak']}",
        f"- Worst gap date: {report['worst_gap_date']} ({report['worst_gap']})",
        "",
        "| Series | N | Ann. return | Ann. vol | Sharpe | Max drawdown |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| Live | {live['n']} | {live['annualized_return_geometric']} | {live['annualized_volatility']} | {live['sharpe']} | {live['max_drawdown']} |",
        f"| Paper | {paper['n']} | {paper['annualized_return_geometric']} | {paper['annualized_volatility']} | {paper['sharpe']} | {paper['max_drawdown']} |",
        "",
        "## Gap Summary",
        "",
        f"- Mean gap: {gap['mean']}",
        f"- Gap t-stat: {gap['t_stat']}",
        f"- Mean absolute gap: {report['absolute_gap_summary']['mean']}",
        "",
        "## Rolling Gap",
        "",
        "| End date | Window | Mean gap | Annualized mean gap | Tracking error | Correlation | Underperform periods |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["rolling_gap"]:
        lines.append(
            f"| {item['end_date']} | {item['window']} | {item['mean_gap']} | {item['annualized_mean_gap']} | {item['tracking_error']} | {item['live_paper_correlation']} | {item['live_underperformed_periods']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare live strategy returns with paper or backtest returns."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--live-return-col", required=True)
    parser.add_argument("--paper-return-col", required=True)
    parser.add_argument("--benchmark-return-col")
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--risk-free-annual", type=float, default=0.0)
    parser.add_argument("--rolling-window", type=int, default=20)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.annualization <= 0:
        raise SystemExit("--annualization must be positive.")
    if args.rolling_window <= 0:
        raise SystemExit("--rolling-window must be positive.")
    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    require_columns(
        header,
        [args.date_col, args.live_return_col, args.paper_return_col]
        + ([args.benchmark_return_col] if args.benchmark_return_col else []),
    )
    report = build_report(
        rows,
        args.date_col,
        args.live_return_col,
        args.paper_return_col,
        args.benchmark_return_col,
        args.annualization,
        args.risk_free_annual,
        args.rolling_window,
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
