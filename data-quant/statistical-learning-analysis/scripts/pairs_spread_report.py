#!/usr/bin/env python3
"""Estimate pair-trading spread diagnostics from two price series.

Requires the shared bundle core dependencies. This estimates a static hedge ratio and spread
diagnostics; it is not a formal cointegration test.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import mean, parse_float, quantile, read_dataframe, require_columns, stdev


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")


def ols_y_on_x(y: list[float], x: list[float]) -> dict[str, float | None]:
    n = min(len(y), len(x))
    if n < 2:
        return {"intercept": None, "beta": None, "r2": None}
    yy = y[:n]
    xx = x[:n]
    mx = mean(xx)
    my = mean(yy)
    if mx is None or my is None:
        return {"intercept": None, "beta": None, "r2": None}
    var_x = sum((value - mx) ** 2 for value in xx)
    if var_x == 0:
        return {"intercept": None, "beta": None, "r2": None}
    beta = sum((xi - mx) * (yi - my) for xi, yi in zip(xx, yy, strict=False)) / var_x
    intercept = my - beta * mx
    fitted = [intercept + beta * xi for xi in xx]
    sse = sum((yi - fi) ** 2 for yi, fi in zip(yy, fitted, strict=False))
    tss = sum((yi - my) ** 2 for yi in yy)
    return {"intercept": intercept, "beta": beta, "r2": 1 - sse / tss if tss > 0 else None}


def lag_autocorrelation(values: list[float]) -> float | None:
    if len(values) < 3:
        return None
    x = values[:-1]
    y = values[1:]
    mx = mean(x)
    my = mean(y)
    if mx is None or my is None:
        return None
    sx = math.sqrt(sum((value - mx) ** 2 for value in x))
    sy = math.sqrt(sum((value - my) ** 2 for value in y))
    if sx == 0 or sy == 0:
        return None
    return sum((xi - mx) * (yi - my) for xi, yi in zip(x, y, strict=False)) / (sx * sy)


def count_crossings(zscores: list[float], threshold: float) -> dict[str, int]:
    upper = 0
    lower = 0
    mean_reversions = 0
    prev = zscores[0] if zscores else 0.0
    for value in zscores[1:]:
        if prev < threshold <= value:
            upper += 1
        if prev > -threshold >= value:
            lower += 1
        if (prev > 0 >= value) or (prev < 0 <= value):
            mean_reversions += 1
        prev = value
    return {
        "upper_threshold_crossings": upper,
        "lower_threshold_crossings": lower,
        "zero_crossings": mean_reversions,
    }


def build_report(
    rows: list[dict[str, str]],
    date_col: str | None,
    asset_a_col: str,
    asset_b_col: str,
    formation_window: int | None,
    log_prices: bool,
    entry_z: float,
) -> dict[str, Any]:
    observations = []
    dropped = 0
    for row in rows:
        a = parse_float(row.get(asset_a_col))
        b = parse_float(row.get(asset_b_col))
        if a is None or b is None or a <= 0 or b <= 0:
            dropped += 1
            continue
        if log_prices:
            a = math.log(a)
            b = math.log(b)
        observations.append({"date": row.get(date_col) if date_col else None, "a": a, "b": b})
    fit_obs = observations[:formation_window] if formation_window else observations
    fit = ols_y_on_x([item["a"] for item in fit_obs], [item["b"] for item in fit_obs])
    intercept = fit["intercept"]
    beta = fit["beta"]
    spread_path = []
    if intercept is not None and beta is not None:
        for idx, item in enumerate(observations, start=1):
            spread_path.append(
                {"index": idx, "date": item["date"], "spread": item["a"] - intercept - beta * item["b"]}
            )
    spreads = [item["spread"] for item in spread_path]
    spread_mean = mean(spreads)
    spread_sd = stdev(spreads)
    z_path = [
        {
            **item,
            "zscore": (item["spread"] - spread_mean) / spread_sd
            if spread_mean is not None and spread_sd not in {None, 0}
            else None,
        }
        for item in spread_path
    ]
    zscores = [item["zscore"] for item in z_path if item["zscore"] is not None]
    rho = lag_autocorrelation(spreads)
    half_life = -math.log(2) / math.log(abs(rho)) if rho is not None and 0 < abs(rho) < 1 else None
    crossings = count_crossings(zscores, entry_z)
    return {
        "date_col": date_col,
        "asset_a_col": asset_a_col,
        "asset_b_col": asset_b_col,
        "formation_window": formation_window,
        "log_prices": log_prices,
        "entry_z": entry_z,
        "rows_dropped": dropped,
        "observations_used": len(observations),
        "fit": fit,
        "spread_summary": {
            "mean": spread_mean,
            "stdev": spread_sd,
            "min": min(spreads) if spreads else None,
            "max": max(spreads) if spreads else None,
            "q05": quantile(spreads, 0.05),
            "q95": quantile(spreads, 0.95),
            "lag1_autocorrelation": rho,
            "half_life_periods": half_life,
            "latest_spread": spreads[-1] if spreads else None,
            "latest_zscore": zscores[-1] if zscores else None,
            **crossings,
        },
        "path": z_path,
        "notes": [
            "Hedge ratio is estimated by OLS of asset A on asset B.",
            "These diagnostics do not prove cointegration; use out-of-sample formation/trading windows for strategy tests.",
            "Pair trading analysis must include borrow, shorting, costs, slippage, and regime-break checks.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    fit = report["fit"]
    spread = report["spread_summary"]
    lines = [
        "# Pairs Spread Report",
        "",
        f"- Asset A: {report['asset_a_col']}",
        f"- Asset B: {report['asset_b_col']}",
        f"- Observations: {report['observations_used']}",
        f"- Formation window: {report['formation_window'] or 'full sample'}",
        f"- Rows dropped: {report['rows_dropped']}",
        "",
        "## Hedge Ratio",
        "",
        f"- Intercept: {fit['intercept']}",
        f"- Beta: {fit['beta']}",
        f"- R-squared: {fit['r2']}",
        "",
        "## Spread",
        "",
        f"- Latest spread: {spread['latest_spread']}",
        f"- Latest z-score: {spread['latest_zscore']}",
        f"- Spread stdev: {spread['stdev']}",
        f"- Lag-1 autocorrelation: {spread['lag1_autocorrelation']}",
        f"- Approx. half-life periods: {spread['half_life_periods']}",
        f"- Upper threshold crossings: {spread['upper_threshold_crossings']}",
        f"- Lower threshold crossings: {spread['lower_threshold_crossings']}",
        f"- Zero crossings: {spread['zero_crossings']}",
        "",
        "Notes:",
    ]
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Estimate pair-trading spread diagnostics from two price series."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col")
    parser.add_argument("--asset-a-col", required=True)
    parser.add_argument("--asset-b-col", required=True)
    parser.add_argument("--formation-window", type=int)
    parser.add_argument("--log-prices", action="store_true")
    parser.add_argument("--entry-z", type=float, default=2.0)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.formation_window is not None and args.formation_window < 2:
        raise SystemExit("--formation-window must be at least 2.")
    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    require_columns(header, [args.asset_a_col, args.asset_b_col] + ([args.date_col] if args.date_col else []))
    report = build_report(
        rows,
        args.date_col,
        args.asset_a_col,
        args.asset_b_col,
        args.formation_window,
        args.log_prices,
        args.entry_z,
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
