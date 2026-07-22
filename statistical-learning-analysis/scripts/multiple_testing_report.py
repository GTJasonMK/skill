#!/usr/bin/env python3
"""Apply multiple-testing corrections to factor or model p-values.

Standard-library only. Supports Bonferroni, Holm, and Benjamini-Hochberg FDR
adjustments for a CSV of candidate signals/tests.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from quant_utils import parse_float, read_dataframe, require_columns

import pandas as pd


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")




def bonferroni(pvalues: list[float]) -> list[float]:
    m = len(pvalues)
    return [min(p * m, 1.0) for p in pvalues]


def holm(pvalues: list[float]) -> list[float]:
    m = len(pvalues)
    indexed = sorted(enumerate(pvalues), key=lambda item: item[1])
    adjusted = [1.0] * m
    running = 0.0
    for rank, (idx, p) in enumerate(indexed):
        value = min((m - rank) * p, 1.0)
        running = max(running, value)
        adjusted[idx] = min(running, 1.0)
    return adjusted


def benjamini_hochberg(pvalues: list[float]) -> list[float]:
    m = len(pvalues)
    indexed = sorted(enumerate(pvalues), key=lambda item: item[1], reverse=True)
    adjusted = [1.0] * m
    running = 1.0
    for reverse_rank, (idx, p) in enumerate(indexed):
        rank = m - reverse_rank
        value = min(p * m / rank, 1.0)
        running = min(running, value)
        adjusted[idx] = running
    return adjusted


def build_report(rows: list[dict[str, str]], p_col: str, id_col: str | None, alpha: float) -> dict[str, Any]:
    tests = []
    dropped = 0
    for i, row in enumerate(rows, start=1):
        p = parse_float(row.get(p_col))
        if p is None or p < 0 or p > 1:
            dropped += 1
            continue
        tests.append({"id": row.get(id_col, str(i)) if id_col else str(i), "p_value": p, "row": row})
    pvalues = [item["p_value"] for item in tests]
    bonf = bonferroni(pvalues)
    holm_adj = holm(pvalues)
    bh = benjamini_hochberg(pvalues)
    output = []
    for item, p_bonf, p_holm, p_bh in zip(tests, bonf, holm_adj, bh):
        output.append(
            {
                "id": item["id"],
                "p_value": item["p_value"],
                "bonferroni_p": p_bonf,
                "holm_p": p_holm,
                "bh_fdr_p": p_bh,
                "significant_raw": item["p_value"] <= alpha,
                "significant_bonferroni": p_bonf <= alpha,
                "significant_holm": p_holm <= alpha,
                "significant_bh_fdr": p_bh <= alpha,
            }
        )
    return {
        "p_col": p_col,
        "id_col": id_col,
        "alpha": alpha,
        "tests_used": len(output),
        "rows_dropped": dropped,
        "discoveries": {
            "raw": sum(item["significant_raw"] for item in output),
            "bonferroni": sum(item["significant_bonferroni"] for item in output),
            "holm": sum(item["significant_holm"] for item in output),
            "bh_fdr": sum(item["significant_bh_fdr"] for item in output),
        },
        "tests": sorted(output, key=lambda item: item["p_value"]),
        "notes": [
            "Bonferroni and Holm control family-wise error rate; Benjamini-Hochberg controls expected false discovery rate under standard assumptions.",
            "The test family must be defined before looking at results.",
            "Multiple-testing adjustment does not fix leakage, repeated backtest tuning, or unreported failed trials.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    disc = report["discoveries"]
    lines = [
        "# Multiple Testing Report",
        "",
        f"- P-value column: {report['p_col']}",
        f"- Tests used: {report['tests_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        f"- Alpha: {report['alpha']}",
        "",
        "| Method | Discoveries |",
        "| --- | --- |",
        f"| Raw | {disc['raw']} |",
        f"| Bonferroni | {disc['bonferroni']} |",
        f"| Holm | {disc['holm']} |",
        f"| Benjamini-Hochberg FDR | {disc['bh_fdr']} |",
        "",
        "## Top Tests",
        "",
        "| ID | p | Bonferroni p | Holm p | BH FDR p | BH significant |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["tests"][:20]:
        lines.append(f"| {item['id']} | {item['p_value']} | {item['bonferroni_p']} | {item['holm_p']} | {item['bh_fdr_p']} | {item['significant_bh_fdr']} |")
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply multiple-testing corrections to factor or model p-values.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--p-col", required=True)
    parser.add_argument("--id-col")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.alpha <= 0 or args.alpha >= 1:
        raise SystemExit("--alpha must be in (0, 1).")
    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    require_columns(header, [args.p_col] + ([args.id_col] if args.id_col else []))
    report = build_report(rows, args.p_col, args.id_col, args.alpha)
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

