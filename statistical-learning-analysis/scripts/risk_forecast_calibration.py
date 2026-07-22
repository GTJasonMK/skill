#!/usr/bin/env python3
"""Check volatility or VaR-style risk forecast calibration.

Standard-library only. Input is a time-series CSV with realized returns and a
forecast volatility column. Forecast volatility is per-period by default.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any

from quant_utils import correlation, mean, parse_float, quantile, read_dataframe, require_columns, sorted_group_keys, stdev, summarize_values

import pandas as pd


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")




def kupiec_pof_test(hit_count: int, n: int, expected_rate: float) -> dict[str, float | int | None]:
    if n == 0 or expected_rate <= 0 or expected_rate >= 1:
        return {"hit_count": hit_count, "n": n, "lr_stat": None, "p_value_chi2_1": None}
    observed_rate = hit_count / n
    eps = 1e-12
    p = min(max(expected_rate, eps), 1 - eps)
    phat = min(max(observed_rate, eps), 1 - eps)
    ll_null = (n - hit_count) * math.log(1 - p) + hit_count * math.log(p)
    ll_alt = (n - hit_count) * math.log(1 - phat) + hit_count * math.log(phat)
    lr_stat = max(0.0, -2 * (ll_null - ll_alt))
    p_value = math.erfc(math.sqrt(lr_stat / 2))
    return {"hit_count": hit_count, "n": n, "lr_stat": lr_stat, "p_value_chi2_1": p_value}


def rms(values: list[float]) -> float | None:
    return math.sqrt(sum(value * value for value in values) / len(values)) if values else None


def split_bins(records: list[dict[str, Any]], bins: int) -> list[list[dict[str, Any]]]:
    if not records:
        return []
    bins = max(1, min(bins, len(records)))
    ordered = sorted(records, key=lambda item: item["forecast_vol"])
    out = []
    for i in range(bins):
        start = i * len(ordered) // bins
        end = (i + 1) * len(ordered) // bins
        out.append(ordered[start:end])
    return out


def build_report(
    rows: list[dict[str, str]],
    date_col: str,
    return_col: str,
    forecast_vol_col: str,
    annualization: int,
    forecast_vol_annualized: bool,
    var_level: float,
    bins: int,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    dropped = 0
    scale = math.sqrt(annualization) if forecast_vol_annualized else 1.0
    z_cutoff = NormalDist().inv_cdf(var_level)
    for row in rows:
        date = row.get(date_col, "")
        ret = parse_float(row.get(return_col))
        forecast_vol_raw = parse_float(row.get(forecast_vol_col))
        if not date or ret is None or forecast_vol_raw is None or forecast_vol_raw <= 0:
            dropped += 1
            continue
        forecast_vol = forecast_vol_raw / scale
        var_threshold = -z_cutoff * forecast_vol
        hit = 1 if ret < var_threshold else 0
        records.append(
            {
                "date": date,
                "return": ret,
                "forecast_vol": forecast_vol,
                "forecast_vol_raw": forecast_vol_raw,
                "standardized_return": ret / forecast_vol,
                "var_threshold": var_threshold,
                "var_breach": hit,
            }
        )

    records.sort(key=lambda item: item["date"])
    returns = [item["return"] for item in records]
    forecast_vols = [item["forecast_vol"] for item in records]
    standardized = [item["standardized_return"] for item in records]
    hits = [item["var_breach"] for item in records]
    expected_breach_rate = 1 - var_level
    hit_autocorr = correlation([float(v) for v in hits[:-1]], [float(v) for v in hits[1:]]) if len(hits) > 2 else None
    forecast_rms = rms(forecast_vols)
    realized_rms = rms(returns)

    calibration_bins = []
    for i, bin_records in enumerate(split_bins(records, bins), start=1):
        bin_returns = [item["return"] for item in bin_records]
        bin_forecast = [item["forecast_vol"] for item in bin_records]
        bin_hits = [item["var_breach"] for item in bin_records]
        bin_realized = rms(bin_returns)
        bin_forecast_rms = rms(bin_forecast)
        calibration_bins.append(
            {
                "bin": i,
                "n": len(bin_records),
                "min_forecast_vol": min(bin_forecast) if bin_forecast else None,
                "max_forecast_vol": max(bin_forecast) if bin_forecast else None,
                "mean_forecast_vol": mean(bin_forecast),
                "realized_rms_return": bin_realized,
                "realized_to_forecast_rms": bin_realized / bin_forecast_rms if bin_realized is not None and bin_forecast_rms not in {None, 0} else None,
                "var_breach_rate": sum(bin_hits) / len(bin_hits) if bin_hits else None,
            }
        )

    return {
        "date_col": date_col,
        "return_col": return_col,
        "forecast_vol_col": forecast_vol_col,
        "annualization": annualization,
        "forecast_vol_annualized": forecast_vol_annualized,
        "var_level": var_level,
        "normal_z_cutoff": z_cutoff,
        "expected_breach_rate": expected_breach_rate,
        "rows_used": len(records),
        "rows_dropped": dropped,
        "mean_forecast_vol": mean(forecast_vols),
        "realized_rms_return": realized_rms,
        "forecast_rms_vol": forecast_rms,
        "realized_to_forecast_rms": realized_rms / forecast_rms if realized_rms is not None and forecast_rms not in {None, 0} else None,
        "standardized_return_summary": summarize_values(standardized),
        "standardized_return_stdev": stdev(standardized),
        "standardized_return_abs_p95": quantile([abs(value) for value in standardized], 0.95),
        "var_breach_rate": sum(hits) / len(hits) if hits else None,
        "var_breach_autocorrelation_lag1": hit_autocorr,
        "kupiec_pof": kupiec_pof_test(sum(hits), len(hits), expected_breach_rate),
        "calibration_bins": calibration_bins,
        "notes": [
            "Forecast volatility should be known before the realized return period.",
            "Standardized returns should have volatility near 1 if the forecast scale is calibrated.",
            "Normal VaR breach checks are a simple diagnostic; they do not validate tail shape or model specification.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    std_summary = report["standardized_return_summary"]
    kupiec = report["kupiec_pof"]
    lines = [
        "# Risk Forecast Calibration Report",
        "",
        f"- Return column: {report['return_col']}",
        f"- Forecast volatility column: {report['forecast_vol_col']}",
        f"- Rows used: {report['rows_used']}",
        f"- Rows dropped: {report['rows_dropped']}",
        f"- Forecast volatility annualized: {report['forecast_vol_annualized']}",
        f"- Realized/forecast RMS ratio: {report['realized_to_forecast_rms']}",
        f"- Standardized return mean: {std_summary['mean']}",
        f"- Standardized return stdev: {report['standardized_return_stdev']}",
        f"- VaR breach rate: {report['var_breach_rate']}",
        f"- Expected breach rate: {report['expected_breach_rate']}",
        f"- Kupiec LR p-value: {kupiec['p_value_chi2_1']}",
        f"- Breach autocorrelation lag1: {report['var_breach_autocorrelation_lag1']}",
        "",
        "| Bin | N | Min forecast vol | Max forecast vol | Mean forecast vol | Realized RMS | Realized/forecast | VaR breach rate |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["calibration_bins"]:
        lines.append(
            f"| {item['bin']} | {item['n']} | {item['min_forecast_vol']} | {item['max_forecast_vol']} | {item['mean_forecast_vol']} | {item['realized_rms_return']} | {item['realized_to_forecast_rms']} | {item['var_breach_rate']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check volatility or VaR-style risk forecast calibration.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--return-col", required=True)
    parser.add_argument("--forecast-vol-col", required=True)
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--forecast-vol-annualized", action="store_true")
    parser.add_argument("--var-level", type=float, default=0.95)
    parser.add_argument("--bins", type=int, default=5)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.annualization <= 0:
        raise SystemExit("--annualization must be positive.")
    if not 0.5 < args.var_level < 1.0:
        raise SystemExit("--var-level must be between 0.5 and 1.0.")
    if args.bins <= 0:
        raise SystemExit("--bins must be positive.")
    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    require_columns(header, [args.date_col, args.return_col, args.forecast_vol_col])
    report = build_report(rows, args.date_col, args.return_col, args.forecast_vol_col, args.annualization, args.forecast_vol_annualized, args.var_level, args.bins)
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
