#!/usr/bin/env python3
"""Aggregate portfolio exposures from date-asset weights.

Supports numeric exposure columns such as beta/size and categorical
exposure columns such as sector/country/currency.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import read_dataframe, require_columns, summarize_series


def split_cols(value: str | None) -> list[str]:
    return [col.strip() for col in value.split(",") if col.strip()] if value else []


def build_report(
    df: pd.DataFrame,
    date_col: str,
    asset_col: str,
    weight_col: str,
    numeric_cols: list[str],
    category_cols: list[str],
) -> dict[str, Any]:
    df = df.copy()
    df[weight_col] = pd.to_numeric(df[weight_col], errors="coerce")
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    rows_in = len(df)
    df = df.dropna(subset=[date_col, asset_col, weight_col])
    df = df[df[asset_col].astype(str).str.len() > 0]
    dropped = rows_in - len(df)

    by_date: list[dict[str, Any]] = []
    for date, g in df.groupby(date_col, sort=True):
        weights = g.groupby(asset_col)[weight_col].sum()
        gross = float(weights.abs().sum())
        numeric_exposures: dict[str, float] = {}
        gross_weighted_numeric: dict[str, float] = {}
        for col in numeric_cols:
            valid = g.dropna(subset=[col])
            numeric_exposures[col] = float((valid[weight_col] * valid[col]).sum())
            gross_weighted_numeric[col] = float((valid[weight_col].abs() * valid[col]).sum())
        category_exposures: dict[str, dict[str, float]] = {}
        for col in category_cols:
            valid = g[g[col].astype(str).str.len() > 0]
            category_exposures[col] = valid.groupby(col)[weight_col].sum().to_dict()
            category_exposures[col] = {k: float(v) for k, v in category_exposures[col].items()}
        by_date.append(
            {
                "date": date if not isinstance(date, pd.Timestamp) else date.isoformat(),
                "n_assets": int(len(weights)),
                "gross_exposure": gross,
                "net_exposure": float(weights.sum()),
                "long_exposure": float(weights[weights > 0].sum()),
                "short_exposure": float(-weights[weights < 0].sum()),
                "concentration_hhi": float(((weights.abs() / gross) ** 2).sum()) if gross > 0 else None,
                "numeric_exposures": numeric_exposures,
                "gross_weighted_numeric_exposures": gross_weighted_numeric,
                "category_exposures": category_exposures,
            }
        )

    numeric_summary = []
    for col in numeric_cols:
        values = [item["numeric_exposures"][col] for item in by_date]
        numeric_summary.append({"name": col, **summarize_series(values)})
    exposure_summary = {
        "gross_exposure": summarize_series([item["gross_exposure"] for item in by_date]),
        "net_exposure": summarize_series([item["net_exposure"] for item in by_date]),
        "long_exposure": summarize_series([item["long_exposure"] for item in by_date]),
        "short_exposure": summarize_series([item["short_exposure"] for item in by_date]),
        "concentration_hhi": summarize_series(
            [item["concentration_hhi"] for item in by_date if item["concentration_hhi"] is not None]
        ),
    }
    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "weight_col": weight_col,
        "numeric_exposure_cols": numeric_cols,
        "category_exposure_cols": category_cols,
        "periods_used": len(by_date),
        "rows_dropped_or_partially_missing": dropped,
        "exposure_summary": exposure_summary,
        "numeric_exposure_summary": numeric_summary,
        "latest": by_date[-1] if by_date else None,
        "by_date": by_date,
        "notes": [
            "Numeric exposures are weight-weighted sums such as portfolio beta or style exposure.",
            "Category exposures are net weights by category, useful for sector/country/currency diagnostics.",
            "Validate exposure definitions, stale holdings, and timing before using these numbers as risk controls.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    latest = report["latest"] or {}
    lines = [
        "# Portfolio Exposure Report",
        "",
        f"- Periods used: {report['periods_used']}",
        f"- Numeric exposures: {', '.join(report['numeric_exposure_cols']) or 'None'}",
        f"- Category exposures: {', '.join(report['category_exposure_cols']) or 'None'}",
        f"- Rows dropped or partially missing: {report['rows_dropped_or_partially_missing']}",
        "",
        "## Latest Portfolio",
        "",
        f"- Date: {latest.get('date')}",
        f"- Gross exposure: {latest.get('gross_exposure')}",
        f"- Net exposure: {latest.get('net_exposure')}",
        f"- Concentration HHI: {latest.get('concentration_hhi')}",
        "",
        "## Numeric Exposure Summary",
        "",
        "| Exposure | N | Mean | Stdev | Min | Max |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["numeric_exposure_summary"]:
        lines.append(
            f"| {row['name']} | {row['n']} | {row['mean']} | {row['stdev']} | {row['min']} | {row['max']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate portfolio exposures from date-asset weights.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--weight-col", required=True)
    parser.add_argument("--numeric-exposure-cols", help="Comma-separated numeric exposure columns.")
    parser.add_argument("--category-exposure-cols", help="Comma-separated categorical exposure columns.")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    numeric_cols = split_cols(args.numeric_exposure_cols)
    category_cols = split_cols(args.category_exposure_cols)
    if not numeric_cols and not category_cols:
        raise SystemExit("Provide at least one numeric or categorical exposure column.")
    df = read_dataframe(args.csv_path)
    require_columns(df, [args.date_col, args.asset_col, args.weight_col] + numeric_cols + category_cols)
    report = build_report(df, args.date_col, args.asset_col, args.weight_col, numeric_cols, category_cols)
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
