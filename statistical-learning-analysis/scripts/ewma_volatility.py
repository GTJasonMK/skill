#!/usr/bin/env python3
"""Compute EWMA volatility paths for return columns.

Uses variance_t = decay * variance_{t-1} + (1 - decay) * return_t^2 for
each selected return column.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_utils import read_dataframe, require_columns


def _ewma_variance(returns: np.ndarray, decay: float) -> np.ndarray:
    if returns.size == 0:
        return returns
    var = np.empty_like(returns, dtype=float)
    var[0] = returns[0] ** 2
    for i in range(1, returns.size):
        var[i] = decay * var[i - 1] + (1.0 - decay) * returns[i] ** 2
    return var


def build_report(
    df: pd.DataFrame,
    columns: list[str],
    date_col: str | None,
    decay: float,
    annualization: int,
    include_path: bool,
) -> dict[str, Any]:
    assets: list[dict[str, Any]] = []
    paths: dict[str, list[dict[str, Any]]] = {}
    for col in columns:
        series = pd.to_numeric(df[col], errors="coerce")
        mask = series.notna()
        dropped = int((~mask).sum())
        rets = series[mask].to_numpy(dtype=float)
        dates = (df.loc[mask, date_col].astype(str).tolist() if date_col else [None] * rets.size)
        variance = _ewma_variance(rets, decay)
        vol = np.sqrt(np.maximum(variance, 0.0))
        ann_vol = vol * np.sqrt(annualization)
        path: list[dict[str, Any]] = []
        for idx, (date, ret, v, vol_i, ann_i) in enumerate(zip(dates, rets, variance, vol, ann_vol), start=1):
            path.append({
                "index": idx,
                "date": date,
                "return": float(ret),
                "ewma_variance": float(v),
                "ewma_volatility": float(vol_i),
                "annualized_ewma_volatility": float(ann_i),
            })
        sample_vol = float(rets.std(ddof=1)) if rets.size >= 2 else None
        assets.append({
            "asset": col,
            "n": int(rets.size),
            "rows_dropped": dropped,
            "latest_ewma_volatility": float(vol[-1]) if vol.size else None,
            "latest_annualized_ewma_volatility": float(ann_vol[-1]) if ann_vol.size else None,
            "mean_ewma_volatility": float(vol.mean()) if vol.size else None,
            "mean_annualized_ewma_volatility": float(ann_vol.mean()) if ann_vol.size else None,
            "sample_volatility": sample_vol,
            "sample_annualized_volatility": sample_vol * np.sqrt(annualization) if sample_vol is not None else None,
        })
        if include_path:
            paths[col] = path
    report: dict[str, Any] = {
        "columns": columns,
        "date_col": date_col,
        "decay": decay,
        "annualization": annualization,
        "assets": assets,
        "notes": [
            "EWMA volatility reacts faster than a fixed-window sample volatility when returns cluster.",
            "The decay parameter controls responsiveness; lower decay reacts faster and is noisier.",
            "Returns must already be cleaned for splits, bad ticks, stale prices, and calendar alignment.",
        ],
    }
    if include_path:
        report["paths"] = paths
    return report


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EWMA Volatility Report",
        "",
        f"- Columns: {', '.join(report['columns'])}",
        f"- Decay: {report['decay']}",
        f"- Annualization: {report['annualization']}",
        "",
        "| Asset | N | Latest EWMA vol | Latest ann. EWMA vol | Mean ann. EWMA vol | Sample ann. vol | Rows dropped |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["assets"]:
        lines.append(
            f"| {item['asset']} | {item['n']} | {item['latest_ewma_volatility']} | {item['latest_annualized_ewma_volatility']} | {item['mean_annualized_ewma_volatility']} | {item['sample_annualized_volatility']} | {item['rows_dropped']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute EWMA volatility paths for return columns.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--columns", required=True, help="Comma-separated return columns.")
    parser.add_argument("--date-col")
    parser.add_argument("--decay", type=float, default=0.94)
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--include-path", action="store_true", help="Include full EWMA path in JSON output.")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.decay <= 0 or args.decay >= 1:
        raise SystemExit("--decay must be in (0, 1).")
    columns = [col.strip() for col in args.columns.split(",") if col.strip()]
    if not columns:
        raise SystemExit("--columns must include at least one return column.")
    df = read_dataframe(args.csv_path)
    require_columns(df, columns + ([args.date_col] if args.date_col else []))
    report = build_report(df, columns, args.date_col, args.decay, args.annualization, args.include_path)
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
