#!/usr/bin/env python3
"""Evaluate strategy return robustness across market regimes.

Requires the shared bundle core dependencies. Input is a time-series CSV with a strategy return column
and a regime label column, optionally with benchmark returns.
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
    sorted_group_keys,
    stdev,
    summarize_returns,
)


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")


def build_report(
    rows: list[dict[str, str]],
    date_col: str,
    return_col: str,
    regime_col: str,
    benchmark_col: str | None,
    annualization: int,
    risk_free_annual: float,
    min_count: int,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    dropped = 0
    for row in rows:
        date = row.get(date_col, "")
        regime = row.get(regime_col, "").strip()
        ret = parse_float(row.get(return_col))
        benchmark = parse_float(row.get(benchmark_col)) if benchmark_col else None
        if not date or not regime or ret is None:
            dropped += 1
            continue
        if benchmark_col and benchmark is None:
            dropped += 1
            continue
        records.append({"date": date, "regime": regime, "return": ret, "benchmark": benchmark})

    records.sort(key=lambda item: item["date"])
    by_regime: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_regime.setdefault(record["regime"], []).append(record)

    regime_summaries = []
    for regime in sorted_group_keys(list(by_regime)):
        items = by_regime[regime]
        returns = [item["return"] for item in items]
        summary = summarize_returns(returns, annualization, risk_free_annual)
        benchmark_returns = [item["benchmark"] for item in items if item["benchmark"] is not None]
        corr = (
            correlation(returns, benchmark_returns)
            if benchmark_col and len(benchmark_returns) == len(returns)
            else None
        )
        regime_summaries.append(
            {
                "regime": regime,
                "n": len(returns),
                "share_periods": len(returns) / len(records) if records else None,
                "meets_min_count": len(returns) >= min_count,
                "benchmark_correlation": corr,
                **summary,
            }
        )

    transitions: dict[str, dict[str, int]] = {}
    for prev, cur in zip(records, records[1:], strict=False):
        transitions.setdefault(prev["regime"], {})
        transitions[prev["regime"]][cur["regime"]] = transitions[prev["regime"]].get(cur["regime"], 0) + 1

    valid_regimes = [item for item in regime_summaries if item["n"] >= min_count]
    mean_returns = [item["mean_return"] for item in valid_regimes if item["mean_return"] is not None]
    worst_mean = min(
        valid_regimes,
        key=lambda item: item["mean_return"] if item["mean_return"] is not None else float("inf"),
        default=None,
    )
    worst_drawdown = min(
        valid_regimes,
        key=lambda item: item["max_drawdown"] if item["max_drawdown"] is not None else 0.0,
        default=None,
    )
    dominant_share = max((item["share_periods"] or 0.0 for item in regime_summaries), default=None)

    return {
        "date_col": date_col,
        "return_col": return_col,
        "regime_col": regime_col,
        "benchmark_col": benchmark_col,
        "annualization": annualization,
        "risk_free_annual": risk_free_annual,
        "min_count": min_count,
        "rows_used": len(records),
        "rows_dropped": dropped,
        "regime_count": len(regime_summaries),
        "dominant_regime_share": dominant_share,
        "overall_return_summary": summarize_returns(
            [item["return"] for item in records], annualization, risk_free_annual
        ),
        "regime_mean_return_dispersion": stdev(mean_returns),
        "worst_regime_by_mean_return": worst_mean["regime"] if worst_mean else None,
        "worst_regime_by_drawdown": worst_drawdown["regime"] if worst_drawdown else None,
        "regimes": regime_summaries,
        "transition_counts": transitions,
        "notes": [
            "Regime labels must be assigned using information available at the evaluation date.",
            "Small regime samples are unstable; use min_count to mark regimes with weak evidence.",
            "Regime robustness is descriptive and does not prove the regime classification is tradable.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    overall = report["overall_return_summary"]
    lines = [
        "# Regime Robustness Report",
        "",
        f"- Return column: {report['return_col']}",
        f"- Regime column: {report['regime_col']}",
        f"- Rows used: {report['rows_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        f"- Regime count: {report['regime_count']}",
        f"- Overall annualized return: {overall['annualized_return_geometric']}",
        f"- Overall annualized volatility: {overall['annualized_volatility']}",
        f"- Overall Sharpe: {overall['sharpe']}",
        f"- Worst regime by mean return: {report['worst_regime_by_mean_return']}",
        f"- Worst regime by drawdown: {report['worst_regime_by_drawdown']}",
        "",
        "| Regime | N | Share | Mean return | Ann. return | Ann. vol | Sharpe | Max drawdown | Benchmark corr | Meets min N |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["regimes"]:
        lines.append(
            f"| {item['regime']} | {item['n']} | {item['share_periods']} | {item['mean_return']} | {item['annualized_return_geometric']} | {item['annualized_volatility']} | {item['sharpe']} | {item['max_drawdown']} | {item['benchmark_correlation']} | {item['meets_min_count']} |"
        )
    lines.extend(["", "## Transition Counts", ""])
    for src in sorted_group_keys(list(report["transition_counts"])):
        dests = report["transition_counts"][src]
        lines.append(f"- {src}: " + ", ".join(f"{dst}={count}" for dst, count in sorted(dests.items())))
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate strategy return robustness across market regimes.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--return-col", required=True)
    parser.add_argument("--regime-col", required=True)
    parser.add_argument("--benchmark-col")
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--risk-free-annual", type=float, default=0.0)
    parser.add_argument("--min-count", type=int, default=5)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    df = read_dataframe(args.csv_path)

    header, rows = _df_to_rows(df)
    require_columns(
        header,
        [args.date_col, args.return_col, args.regime_col]
        + ([args.benchmark_col] if args.benchmark_col else []),
    )
    report = build_report(
        rows,
        args.date_col,
        args.return_col,
        args.regime_col,
        args.benchmark_col,
        args.annualization,
        args.risk_free_annual,
        args.min_count,
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
