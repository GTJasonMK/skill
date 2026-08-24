#!/usr/bin/env python3
"""Neutralize a factor signal against exposures within each date.

Regresses the signal on numeric exposures and optional categorical dummies
within each date, then writes/returns residualized signal values. Use this
before IC, quantile, or portfolio tests when risk neutrality is part of the
research design.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from quant_utils import ols, read_dataframe, require_columns, summarize_series


def split_cols(value: str | None) -> list[str]:
    return [col.strip() for col in value.split(",") if col.strip()] if value else []


def _category_levels(g: pd.DataFrame, category_cols: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for col in category_cols:
        labels = sorted(set(g[col].astype(str)) - {""})
        out[col] = labels[1:] if len(labels) > 1 else []
    return out


def _design_matrix(
    sub: pd.DataFrame, numeric_cols: list[str], category_cols: list[str]
) -> tuple[np.ndarray, dict[str, list[str]]]:
    dummy_levels = _category_levels(sub, category_cols)
    parts = [np.ones((len(sub), 1))]
    if numeric_cols:
        parts.append(sub[numeric_cols].to_numpy(dtype=float))
    for col, levels in dummy_levels.items():
        for lvl in levels:
            parts.append((sub[col].astype(str) == lvl).astype(float).to_numpy().reshape(-1, 1))
    X = np.hstack(parts)
    return X, dummy_levels


def neutralize_group(
    g: pd.DataFrame, signal_col: str, numeric_cols: list[str], category_cols: list[str]
) -> tuple[pd.DataFrame | None, dict[str, Any]]:
    needed = [signal_col] + numeric_cols
    sub = g.copy()
    for col in needed:
        sub[col] = pd.to_numeric(sub[col], errors="coerce")
    rows_in = len(sub)
    sub = sub.dropna(subset=needed)
    if category_cols:
        sub = sub.dropna(subset=category_cols)
    dropped = rows_in - len(sub)
    if sub.empty:
        return None, {"status": "no_valid_rows", "n": 0, "dropped": dropped}
    try:
        X, dummy_levels = _design_matrix(sub, numeric_cols, category_cols)
        y = sub[signal_col].to_numpy(dtype=float)
        fit = ols(y, X)
    except ValueError as exc:
        return None, {"status": f"skipped: {exc}", "n": len(sub), "dropped": dropped}
    residuals = np.asarray(fit["residuals"], dtype=float)
    resid_std = float(residuals.std(ddof=1)) if residuals.size >= 2 else 0.0
    if resid_std > 0:
        z = (residuals - residuals.mean()) / resid_std
    else:
        z = np.zeros_like(residuals)
    out = sub.copy()
    out["neutralized_signal"] = residuals
    out["neutralized_zscore"] = z
    return out, {
        "status": "ok",
        "n": fit["n"],
        "dropped": dropped,
        "r2": fit["r2"],
        "residual_std": fit["residual_std"],
        "n_numeric_exposures": len(numeric_cols),
        "n_dummy_exposures": sum(len(levels) for levels in dummy_levels.values()),
    }


def build_report(
    df: pd.DataFrame,
    date_col: str,
    asset_col: str,
    signal_col: str,
    numeric_cols: list[str],
    category_cols: list[str],
    min_assets: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    df = df[df[date_col].astype(str).str.len() > 0]
    output_parts: list[pd.DataFrame] = []
    by_date: list[dict[str, Any]] = []
    skipped_dates = 0
    residual_values: list[float] = []
    for date, g in df.groupby(date_col, sort=True):
        date_str = date if not isinstance(date, pd.Timestamp) else date.isoformat()
        if len(g) < min_assets:
            skipped_dates += 1
            by_date.append({"date": date_str, "status": "skipped: too_few_assets", "n_raw": int(len(g))})
            continue
        out, summary = neutralize_group(g, signal_col, numeric_cols, category_cols)
        summary["date"] = date_str
        summary["n_raw"] = int(len(g))
        by_date.append(summary)
        if summary["status"] != "ok" or out is None:
            skipped_dates += 1
            continue
        output_parts.append(out)
        residual_values.extend(out["neutralized_signal"].tolist())

    output_df = pd.concat(output_parts, ignore_index=True) if output_parts else df.iloc[0:0].copy()
    report = {
        "date_col": date_col,
        "asset_col": asset_col,
        "signal_col": signal_col,
        "numeric_exposure_cols": numeric_cols,
        "category_exposure_cols": category_cols,
        "min_assets_per_date": min_assets,
        "dates_used": sum(1 for item in by_date if item.get("status") == "ok"),
        "dates_skipped": skipped_dates,
        "rows_output": int(len(output_df)),
        "residual_summary": summarize_series(residual_values),
        "by_date": by_date,
        "notes": [
            "Neutralized signal is the residual from a within-date OLS regression of signal on exposures.",
            "Categorical exposures are one-hot encoded with the first observed level dropped per date.",
            "Neutralization choices can remove intended signal; compare neutralized and unneutralized diagnostics.",
        ],
    }
    return report, output_df


def markdown(report: dict[str, Any]) -> str:
    summary = report["residual_summary"]
    lines = [
        "# Factor Neutralization Report",
        "",
        f"- Signal column: {report['signal_col']}",
        f"- Numeric exposures: {', '.join(report['numeric_exposure_cols']) or 'None'}",
        f"- Category exposures: {', '.join(report['category_exposure_cols']) or 'None'}",
        f"- Dates used: {report['dates_used']}",
        f"- Dates skipped: {report['dates_skipped']}",
        f"- Rows output: {report['rows_output']}",
        "",
        f"- Residual mean: {summary['mean']}",
        f"- Residual stdev: {summary['stdev']}",
        "",
        "| Date | Status | N raw | N used | R-squared | Residual std |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["by_date"]:
        lines.append(
            f"| {item['date']} | {item['status']} | {item.get('n_raw')} | {item.get('n')} | {item.get('r2')} | {item.get('residual_std')} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Neutralize a factor signal against exposures within each date."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--signal-col", required=True)
    parser.add_argument("--numeric-exposure-cols")
    parser.add_argument("--category-exposure-cols")
    parser.add_argument("--min-assets-per-date", type=int, default=5)
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    numeric_cols = split_cols(args.numeric_exposure_cols)
    category_cols = split_cols(args.category_exposure_cols)
    if not numeric_cols and not category_cols:
        raise SystemExit("Provide at least one numeric or categorical exposure column.")
    df = read_dataframe(args.csv_path)
    require_columns(df, [args.date_col, args.asset_col, args.signal_col] + numeric_cols + category_cols)
    report, output_df = build_report(
        df,
        args.date_col,
        args.asset_col,
        args.signal_col,
        numeric_cols,
        category_cols,
        args.min_assets_per_date,
    )
    if args.output_csv:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        output_df.to_csv(args.output_csv, index=False, encoding="utf-8")
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
