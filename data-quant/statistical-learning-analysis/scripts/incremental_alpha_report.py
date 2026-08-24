#!/usr/bin/env python3
"""Diagnose incremental value of a candidate alpha signal.

Input is a long date-asset CSV with a candidate signal, forward return,
and existing signal/exposure columns. For each date, the script compares
a base cross-sectional model with a full model that adds the candidate,
and reports residual IC-style diagnostics after controlling for the base
set.
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


def _base_design(
    sub: pd.DataFrame, numeric_base_cols: list[str], category_base_cols: list[str], intercept: bool
) -> tuple[np.ndarray, int]:
    parts: list[np.ndarray] = []
    if intercept:
        parts.append(np.ones((len(sub), 1)))
    if numeric_base_cols:
        parts.append(sub[numeric_base_cols].to_numpy(dtype=float))
    dummy_levels = _category_levels(sub, category_base_cols)
    for col, levels in dummy_levels.items():
        for lvl in levels:
            parts.append((sub[col].astype(str) == lvl).astype(float).to_numpy().reshape(-1, 1))
    if not parts:
        X = np.empty((len(sub), 0))
    else:
        X = np.hstack(parts)
    n_dummies = sum(len(levels) for levels in dummy_levels.values())
    return X, n_dummies


def date_incremental_diagnostic(
    date: str,
    g: pd.DataFrame,
    return_col: str,
    candidate_col: str,
    numeric_base_cols: list[str],
    category_base_cols: list[str],
    min_assets: int,
    intercept: bool,
) -> dict[str, Any]:
    cols = [return_col, candidate_col] + numeric_base_cols
    sub = g.copy()
    for col in cols:
        sub[col] = pd.to_numeric(sub[col], errors="coerce")
    rows_in = len(sub)
    sub = sub.dropna(subset=cols)
    if category_base_cols:
        sub = sub.dropna(subset=category_base_cols)
    dropped = rows_in - len(sub)
    n = len(sub)
    X_base, n_dummies = _base_design(sub, numeric_base_cols, category_base_cols, intercept)
    p_base = X_base.shape[1]
    p_full = p_base + 1
    base_summary = {
        "date": date,
        "n_raw": int(len(g)),
        "n": int(n),
        "dropped": int(dropped),
        "p_base": int(p_base),
        "p_full": int(p_full),
    }
    if n < min_assets:
        return {**base_summary, "status": "skipped: too_few_assets"}
    if n <= p_full:
        return {**base_summary, "status": "skipped: not_enough_degrees_of_freedom"}
    y = sub[return_col].to_numpy(dtype=float)
    cand = sub[candidate_col].to_numpy(dtype=float)
    try:
        base_fit = ols(y, X_base)
        candidate_fit = ols(cand, X_base)
    except ValueError as exc:
        return {**base_summary, "status": f"skipped: {exc}"}
    X_full = np.column_stack([X_base, cand])
    try:
        full_fit = ols(y, X_full)
        full_model_status = "ok"
        full_r2 = full_fit["r2"]
        full_adj_r2 = full_fit["adj_r2"]
        candidate_coef = full_fit["coefficients"][-1]
        candidate_t = full_fit["t_stats_iid"][-1]
    except ValueError as exc:
        full_model_status = f"skipped: {exc}"
        full_r2 = base_fit["r2"]
        full_adj_r2 = base_fit["adj_r2"]
        candidate_coef = None
        candidate_t = None
    base_resid = np.asarray(base_fit["residuals"], dtype=float)
    candidate_resid = np.asarray(candidate_fit["residuals"], dtype=float)
    raw_ic = float(np.corrcoef(cand, y)[0, 1]) if np.std(cand) > 0 and np.std(y) > 0 else None
    raw_rank_ic = float(pd.Series(cand).corr(pd.Series(y), method="spearman"))
    if pd.isna(raw_rank_ic):
        raw_rank_ic = None
    if np.std(candidate_resid) > 0 and np.std(base_resid) > 0:
        residual_ic = float(np.corrcoef(candidate_resid, base_resid)[0, 1])
    else:
        residual_ic = None
    residual_rank_ic = float(pd.Series(candidate_resid).corr(pd.Series(base_resid), method="spearman"))
    if pd.isna(residual_rank_ic):
        residual_rank_ic = None
    delta_r2 = (full_r2 - base_fit["r2"]) if full_r2 is not None and base_fit["r2"] is not None else None
    delta_adj_r2 = (
        (full_adj_r2 - base_fit["adj_r2"])
        if full_adj_r2 is not None and base_fit["adj_r2"] is not None
        else None
    )
    return {
        **base_summary,
        "status": "ok",
        "full_model_status": full_model_status,
        "base_r2": base_fit["r2"],
        "full_r2": full_r2,
        "delta_r2": delta_r2,
        "base_adj_r2": base_fit["adj_r2"],
        "full_adj_r2": full_adj_r2,
        "delta_adj_r2": delta_adj_r2,
        "candidate_coef": candidate_coef,
        "candidate_t_stat_iid": candidate_t,
        "candidate_explained_by_base_r2": candidate_fit["r2"],
        "raw_ic": raw_ic,
        "raw_rank_ic": raw_rank_ic,
        "residual_ic": residual_ic,
        "residual_rank_ic": residual_rank_ic,
    }


def assessment(
    dates_used: int,
    min_dates: int,
    residual_rank_summary: dict[str, Any],
    delta_r2_summary: dict[str, Any],
    min_residual_rank_ic: float,
    min_positive_rate: float,
) -> str:
    if dates_used < min_dates:
        return "insufficient_dates"
    residual_mean = residual_rank_summary["mean"]
    residual_positive = residual_rank_summary["positive_rate"]
    delta_mean = delta_r2_summary["mean"]
    if residual_mean is None or residual_positive is None:
        return "insufficient_signal_variation"
    if (
        residual_mean >= min_residual_rank_ic
        and residual_positive >= min_positive_rate
        and (delta_mean is None or delta_mean >= 0)
    ):
        return "candidate_has_incremental_evidence"
    if residual_mean <= 0 or residual_positive < 0.5:
        return "weak_or_negative_incremental_evidence"
    return "mixed_incremental_evidence"


def build_report(
    df: pd.DataFrame,
    date_col: str,
    asset_col: str,
    return_col: str,
    candidate_col: str,
    numeric_base_cols: list[str],
    category_base_cols: list[str],
    min_assets: int,
    min_dates: int,
    intercept: bool,
    min_residual_rank_ic: float,
    min_positive_rate: float,
) -> dict[str, Any]:
    rows_in = len(df)
    df = df[df[date_col].astype(str).str.len() > 0]
    df = df[df[asset_col].astype(str).str.len() > 0]
    rows_without_date_asset = rows_in - len(df)

    by_date: list[dict[str, Any]] = []
    for date, g in df.groupby(date_col, sort=True):
        date_str = date if not isinstance(date, pd.Timestamp) else date.isoformat()
        by_date.append(
            date_incremental_diagnostic(
                date_str,
                g,
                return_col,
                candidate_col,
                numeric_base_cols,
                category_base_cols,
                min_assets,
                intercept,
            )
        )
    ok_dates = [item for item in by_date if item["status"] == "ok"]
    skipped_dates = [item for item in by_date if item["status"] != "ok"]
    raw_ic_values = [item["raw_ic"] for item in ok_dates if item["raw_ic"] is not None]
    raw_rank_values = [item["raw_rank_ic"] for item in ok_dates if item["raw_rank_ic"] is not None]
    residual_ic_values = [item["residual_ic"] for item in ok_dates if item["residual_ic"] is not None]
    residual_rank_values = [
        item["residual_rank_ic"] for item in ok_dates if item["residual_rank_ic"] is not None
    ]
    coef_values = [item["candidate_coef"] for item in ok_dates if item["candidate_coef"] is not None]
    t_values = [item["candidate_t_stat_iid"] for item in ok_dates if item["candidate_t_stat_iid"] is not None]
    delta_r2_values = [item["delta_r2"] for item in ok_dates if item["delta_r2"] is not None]
    delta_adj_r2_values = [item["delta_adj_r2"] for item in ok_dates if item["delta_adj_r2"] is not None]
    candidate_base_r2_values = [
        item["candidate_explained_by_base_r2"]
        for item in ok_dates
        if item["candidate_explained_by_base_r2"] is not None
    ]
    residual_rank_summary = summarize_series(residual_rank_values)
    delta_r2_summary = summarize_series(delta_r2_values)
    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "return_col": return_col,
        "candidate_col": candidate_col,
        "numeric_base_cols": numeric_base_cols,
        "category_base_cols": category_base_cols,
        "intercept": intercept,
        "min_assets_per_date": min_assets,
        "min_dates": min_dates,
        "min_residual_rank_ic": min_residual_rank_ic,
        "min_positive_rate": min_positive_rate,
        "dates_used": len(ok_dates),
        "dates_skipped": len(skipped_dates),
        "rows_without_date_asset": rows_without_date_asset,
        "rows_dropped_missing": sum(item.get("dropped", 0) for item in by_date),
        "raw_ic_summary": summarize_series(raw_ic_values),
        "raw_rank_ic_summary": summarize_series(raw_rank_values),
        "residual_ic_summary": summarize_series(residual_ic_values),
        "residual_rank_ic_summary": residual_rank_summary,
        "candidate_coef_summary": summarize_series(coef_values),
        "candidate_t_stat_iid_summary": summarize_series(t_values),
        "delta_r2_summary": delta_r2_summary,
        "delta_adj_r2_summary": summarize_series(delta_adj_r2_values),
        "candidate_explained_by_base_r2_summary": summarize_series(candidate_base_r2_values),
        "assessment": assessment(
            len(ok_dates),
            min_dates,
            residual_rank_summary,
            delta_r2_summary,
            min_residual_rank_ic,
            min_positive_rate,
        ),
        "by_date": by_date,
        "notes": [
            "Residual IC correlates the candidate signal residual with forward-return residuals after controlling for the base columns within each date.",
            "Delta R-squared compares the base cross-sectional return model with a full model that adds the candidate signal.",
            "The candidate coefficient t-stat is an IID cross-sectional diagnostic by date; serious inference should use out-of-sample validation and time-series or clustered error treatment.",
            "A high candidate-explained-by-base R-squared means the candidate signal is largely spanned by existing signals or exposures.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Incremental Alpha Report",
        "",
        f"- Candidate signal: {report['candidate_col']}",
        f"- Forward return: {report['return_col']}",
        f"- Numeric base columns: {', '.join(report['numeric_base_cols']) or 'None'}",
        f"- Category base columns: {', '.join(report['category_base_cols']) or 'None'}",
        f"- Dates used: {report['dates_used']}",
        f"- Dates skipped: {report['dates_skipped']}",
        f"- Rows dropped missing: {report['rows_dropped_missing']}",
        f"- Assessment: {report['assessment']}",
        "",
        "| Metric | N | Mean | Stdev | t-stat | Positive rate | Min | Max |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    metrics = [
        ("Raw IC", report["raw_ic_summary"]),
        ("Raw rank IC", report["raw_rank_ic_summary"]),
        ("Residual IC", report["residual_ic_summary"]),
        ("Residual rank IC", report["residual_rank_ic_summary"]),
        ("Candidate coefficient", report["candidate_coef_summary"]),
        ("Candidate IID t-stat", report["candidate_t_stat_iid_summary"]),
        ("Delta R-squared", report["delta_r2_summary"]),
        ("Delta adjusted R-squared", report["delta_adj_r2_summary"]),
        ("Candidate explained by base R-squared", report["candidate_explained_by_base_r2_summary"]),
    ]
    for name, summary in metrics:
        lines.append(
            f"| {name} | {summary['n']} | {summary['mean']} | {summary['stdev']} | {summary['t_stat']} | {summary['positive_rate']} | {summary['min']} | {summary['max']} |"
        )
    lines.extend(
        [
            "",
            "## By Date",
            "",
            "| Date | Status | N | Raw rank IC | Residual rank IC | Delta R2 | Candidate coef | Candidate base R2 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in report["by_date"]:
        lines.append(
            f"| {item['date']} | {item['status']} | {item.get('n')} | {item.get('raw_rank_ic')} | {item.get('residual_rank_ic')} | {item.get('delta_r2')} | {item.get('candidate_coef')} | {item.get('candidate_explained_by_base_r2')} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose incremental value of a candidate alpha signal after controlling for existing signals or exposures."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--forward-return-col", required=True)
    parser.add_argument("--candidate-col", required=True)
    parser.add_argument("--base-cols", help="Comma-separated numeric base signal/exposure columns.")
    parser.add_argument("--category-base-cols", help="Comma-separated categorical base exposure columns.")
    parser.add_argument("--min-assets-per-date", type=int, default=10)
    parser.add_argument("--min-dates", type=int, default=5)
    parser.add_argument("--min-residual-rank-ic", type=float, default=0.02)
    parser.add_argument("--min-positive-rate", type=float, default=0.55)
    parser.add_argument("--no-intercept", action="store_true")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    numeric_base_cols = split_cols(args.base_cols)
    category_base_cols = split_cols(args.category_base_cols)
    if not numeric_base_cols and not category_base_cols:
        raise SystemExit("Provide at least one --base-cols or --category-base-cols column.")
    if args.min_assets_per_date < 3:
        raise SystemExit("--min-assets-per-date must be at least 3.")
    if args.min_dates < 1:
        raise SystemExit("--min-dates must be at least 1.")
    if not 0 <= args.min_positive_rate <= 1:
        raise SystemExit("--min-positive-rate must be in [0, 1].")

    df = read_dataframe(args.csv_path)
    require_columns(
        df,
        [args.date_col, args.asset_col, args.forward_return_col, args.candidate_col]
        + numeric_base_cols
        + category_base_cols,
    )
    report = build_report(
        df,
        args.date_col,
        args.asset_col,
        args.forward_return_col,
        args.candidate_col,
        numeric_base_cols,
        category_base_cols,
        args.min_assets_per_date,
        args.min_dates,
        not args.no_intercept,
        args.min_residual_rank_ic,
        args.min_positive_rate,
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
