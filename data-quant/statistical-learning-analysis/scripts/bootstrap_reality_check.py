#!/usr/bin/env python3
"""Run a simple block-bootstrap reality check across strategy return columns.

Requires the shared bundle core dependencies. This is a first-pass data-snooping diagnostic: compare
the best observed mean return across many strategies to a bootstrap null where
each strategy's mean return is centered to zero and time blocks are resampled.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import mean, parse_float, quantile, read_dataframe, require_columns, stdev, summarize_values


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")


def read_return_matrix(rows: list[dict[str, str]], columns: list[str]) -> tuple[list[list[float]], int]:
    matrix: list[list[float]] = []
    dropped = 0
    for row in rows:
        values = [parse_float(row.get(col)) for col in columns]
        if any(value is None for value in values):
            dropped += 1
            continue
        matrix.append([float(value) for value in values if value is not None])
    return matrix, dropped


def sample_block_indices(n: int, block_length: int, rng: random.Random) -> list[int]:
    indices: list[int] = []
    while len(indices) < n:
        start = rng.randrange(0, n)
        for offset in range(block_length):
            indices.append((start + offset) % n)
            if len(indices) == n:
                break
    return indices


def build_report(
    rows: list[dict[str, str]],
    columns: list[str],
    block_length: int,
    bootstrap_samples: int,
    seed: int,
    annualization: int,
) -> dict[str, Any]:
    matrix, dropped = read_return_matrix(rows, columns)
    if len(matrix) < 2:
        raise SystemExit("Need at least two complete return rows.")
    n = len(matrix)
    k = len(columns)
    cols = [[row[j] for row in matrix] for j in range(k)]
    means = [mean(col) or 0.0 for col in cols]
    vols = [stdev(col) for col in cols]
    t_stats = [
        m / (vol / (n**0.5)) if vol not in {None, 0} else None for m, vol in zip(means, vols, strict=False)
    ]
    best_idx = max(range(k), key=lambda i: means[i])
    centered = [[row[j] - means[j] for j in range(k)] for row in matrix]
    rng = random.Random(seed)
    boot_best_means = []
    boot_best_tstats = []
    for _ in range(bootstrap_samples):
        idxs = sample_block_indices(n, block_length, rng)
        sampled = [centered[i] for i in idxs]
        sample_cols = [[row[j] for row in sampled] for j in range(k)]
        sample_means = [mean(col) or 0.0 for col in sample_cols]
        sample_vols = [stdev(col) for col in sample_cols]
        sample_t = [
            sample_mean / (sample_vol / (n**0.5)) if sample_vol not in {None, 0} else 0.0
            for sample_mean, sample_vol in zip(sample_means, sample_vols, strict=False)
        ]
        boot_best_means.append(max(sample_means))
        boot_best_tstats.append(max(sample_t))
    observed_best_mean = means[best_idx]
    observed_best_t = t_stats[best_idx]
    p_mean = (
        sum(value >= observed_best_mean for value in boot_best_means) / len(boot_best_means)
        if boot_best_means
        else None
    )
    p_t = (
        sum(value >= observed_best_t for value in boot_best_tstats) / len(boot_best_tstats)
        if boot_best_tstats and observed_best_t is not None
        else None
    )
    strategies = []
    for col, avg, vol, t_stat in zip(columns, means, vols, t_stats, strict=False):
        strategies.append(
            {
                "strategy": col,
                "mean_return": avg,
                "annualized_return_arithmetic": avg * annualization,
                "volatility": vol,
                "annualized_volatility": vol * (annualization**0.5) if vol is not None else None,
                "t_stat_mean": t_stat,
            }
        )
    return {
        "columns": columns,
        "observations_used": n,
        "rows_dropped": dropped,
        "block_length": block_length,
        "bootstrap_samples": bootstrap_samples,
        "seed": seed,
        "annualization": annualization,
        "best_strategy": columns[best_idx],
        "observed_best_mean": observed_best_mean,
        "observed_best_t_stat": observed_best_t,
        "reality_check_p_value_mean": p_mean,
        "reality_check_p_value_t_stat": p_t,
        "bootstrap_best_mean_summary": summarize_values(boot_best_means),
        "bootstrap_best_t_stat_summary": summarize_values(boot_best_tstats),
        "bootstrap_best_mean_q95": quantile(boot_best_means, 0.95),
        "bootstrap_best_t_stat_q95": quantile(boot_best_tstats, 0.95),
        "strategies": sorted(strategies, key=lambda item: item["mean_return"], reverse=True),
        "notes": [
            "This is a simple centered block-bootstrap reality check, not a full "
            "White Reality Check implementation.",
            "Use block length consistent with autocorrelation and holding-period overlap.",
            "The tested strategy family must include all tried variants, not only the survivors.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Bootstrap Reality Check",
        "",
        f"- Best strategy: {report['best_strategy']}",
        f"- Observed best mean: {report['observed_best_mean']}",
        f"- Observed best t-stat: {report['observed_best_t_stat']}",
        f"- Reality-check p-value by mean: {report['reality_check_p_value_mean']}",
        f"- Reality-check p-value by t-stat: {report['reality_check_p_value_t_stat']}",
        f"- Observations used: {report['observations_used']}",
        f"- Bootstrap samples: {report['bootstrap_samples']}",
        "",
        "| Strategy | Mean return | Ann. return | Volatility | t-stat |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["strategies"]:
        lines.append(
            f"| {item['strategy']} | {item['mean_return']} | "
            f"{item['annualized_return_arithmetic']} | {item['volatility']} | "
            f"{item['t_stat_mean']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a simple block-bootstrap reality check across strategy return columns."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--columns", required=True, help="Comma-separated strategy return columns.")
    parser.add_argument("--block-length", type=int, default=5)
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    columns = [col.strip() for col in args.columns.split(",") if col.strip()]
    if len(columns) < 2:
        raise SystemExit("--columns must include at least two strategy return columns.")
    if args.block_length < 1 or args.bootstrap_samples < 1:
        raise SystemExit("--block-length and --bootstrap-samples must be positive.")
    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    require_columns(header, columns)
    report = build_report(
        rows, columns, args.block_length, args.bootstrap_samples, args.seed, args.annualization
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
