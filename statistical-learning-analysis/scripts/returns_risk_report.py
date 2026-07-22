#!/usr/bin/env python3
"""Compute return and risk diagnostics from return or price CSV data.

Supports wide CSVs where each selected column is an asset/strategy return
series or price series.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_utils import max_drawdown, read_dataframe


def _returns_from_series(s: pd.Series, mode: str) -> tuple[pd.Series, int]:
    rows_in = len(s)
    s = pd.to_numeric(s, errors="coerce").dropna()
    if mode == "returns":
        return s.reset_index(drop=True), rows_in - len(s)
    prev = s.shift(1)
    rets = (s / prev) - 1.0
    rets = rets.replace([np.inf, -np.inf], np.nan).dropna()
    dropped = rows_in - len(s) + (len(s) - 1 - len(rets))
    return rets.reset_index(drop=True), max(dropped, 0)


def summarize_returns_extended(returns: pd.Series, annualization: int,
                               risk_free_annual: float, var_level: float) -> dict[str, Any]:
    r = pd.Series(returns).dropna().reset_index(drop=True)
    n = int(len(r))
    rf_period = (1.0 + risk_free_annual) ** (1.0 / annualization) - 1.0 if risk_free_annual > -1.0 else 0.0
    excess = r - rf_period
    mean_ret = float(r.mean()) if n else None
    avg_excess = float(excess.mean()) if n else None
    vol = float(r.std(ddof=1)) if n >= 2 else None
    downside = np.minimum(0.0, (r - rf_period).to_numpy())
    downside_dev = float(np.sqrt((downside ** 2).sum() / (len(downside) - 1))) if len(downside) > 1 else None
    compounded = float((1.0 + r).prod()) if n else None
    ann_ret_geom = compounded ** (annualization / n) - 1.0 if compounded is not None and compounded > 0 and n else None
    ann_ret_arith = mean_ret * annualization if mean_ret is not None else None
    ann_vol = vol * np.sqrt(annualization) if vol is not None else None
    sharpe = (avg_excess / vol) * np.sqrt(annualization) if avg_excess is not None and vol not in {None, 0} and vol is not None and vol > 0 else None
    sortino = (avg_excess / downside_dev) * np.sqrt(annualization) if avg_excess is not None and downside_dev not in {None, 0} and downside_dev is not None and downside_dev > 0 else None
    q = float(np.quantile(r, 1.0 - var_level)) if n else None
    tail = r[r <= q] if q is not None else pd.Series([], dtype=float)
    var = -q if q is not None else None
    es = float(-tail.mean()) if len(tail) > 0 else None
    skew = float(r.skew()) if n >= 3 else None
    kurt = float(r.kurt()) if n >= 4 else None
    out = {
        "n": n,
        "mean_return": mean_ret,
        "annualized_return_arithmetic": ann_ret_arith,
        "annualized_return_geometric": ann_ret_geom,
        "volatility": vol,
        "annualized_volatility": ann_vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "skewness": skew,
        "excess_kurtosis": kurt,
        "historical_var": var,
        "historical_expected_shortfall": es,
        "var_level": var_level,
    }
    out.update(max_drawdown(r))
    return out


def build_report(df: pd.DataFrame, columns: list[str], mode: str, annualization: int,
                 risk_free_annual: float, var_level: float) -> dict[str, Any]:
    series_map: dict[str, pd.Series] = {}
    summaries = []
    for col in columns:
        rets, dropped = _returns_from_series(df[col], mode)
        series_map[col] = rets
        summary = summarize_returns_extended(rets, annualization, risk_free_annual, var_level)
        summary["asset"] = col
        summary["rows_dropped"] = dropped
        summaries.append(summary)
    # align by index for correlation
    aligned = pd.DataFrame({col: series_map[col] for col in columns})
    corr_df = aligned.corr()
    corr = {a: {b: (None if pd.isna(corr_df.at[a, b]) else float(corr_df.at[a, b])) for b in columns} for a in columns}
    return {
        "mode": mode,
        "annualization": annualization,
        "risk_free_annual": risk_free_annual,
        "var_level": var_level,
        "assets": summaries,
        "correlation": corr,
        "notes": [
            "Metrics are based on historical returns and are not forecasts.",
            "If mode=prices, returns are simple adjacent-period returns from non-missing prices.",
            "Sharpe and Sortino use the provided annual risk-free rate converted to a per-period rate.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Return and Risk Report",
        "",
        f"- Mode: {report['mode']}",
        f"- Annualization: {report['annualization']}",
        f"- Annual risk-free rate: {report['risk_free_annual']}",
        f"- VaR/ES level: {report['var_level']}",
        "",
        "| Asset | N | Ann. return geom | Ann. vol | Sharpe | Sortino | Max drawdown | Hist VaR | Hist ES | Skew | Ex. kurtosis |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["assets"]:
        lines.append(
            f"| {item['asset']} | {item['n']} | {item['annualized_return_geometric']} | {item['annualized_volatility']} | {item['sharpe']} | {item['sortino']} | {item['max_drawdown']} | {item['historical_var']} | {item['historical_expected_shortfall']} | {item['skewness']} | {item['excess_kurtosis']} |"
        )
    lines.extend(["", "## Correlation", ""])
    assets = [item["asset"] for item in report["assets"]]
    lines.append("| Asset | " + " | ".join(assets) + " |")
    lines.append("| --- | " + " | ".join("---" for _ in assets) + " |")
    for a in assets:
        lines.append("| " + a + " | " + " | ".join(str(report["correlation"][a][b]) for b in assets) + " |")
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute return and risk diagnostics from return or price CSV columns.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--columns", required=True, help="Comma-separated return or price columns.")
    parser.add_argument("--mode", choices=["returns", "prices"], default="returns")
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--risk-free-annual", type=float, default=0.0)
    parser.add_argument("--var-level", type=float, default=0.95)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    df = read_dataframe(args.csv_path)
    columns = [name.strip() for name in args.columns.split(",") if name.strip()]
    missing = [name for name in columns if name not in df.columns]
    if missing:
        raise SystemExit(f"Columns not found: {', '.join(missing)}")
    if not 0 < args.var_level < 1:
        raise SystemExit("--var-level must be between 0 and 1.")
    report = build_report(df, columns, args.mode, args.annualization, args.risk_free_annual, args.var_level)
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
