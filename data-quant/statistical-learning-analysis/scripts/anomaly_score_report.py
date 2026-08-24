#!/usr/bin/env python3
"""Univariate and multivariate anomaly score diagnostics.

Computes per-row anomaly scores using one of three methods:

- ``zscore``: absolute z-score against the column mean/stdev.
- ``iqr``: distance from the 25th-75th percentile band, normalized by IQR.
- ``mahalanobis``: per-row Mahalanobis distance against multivariate mean
  and covariance (shrinks the covariance toward a diagonal when singular).

Outputs a scored CSV plus a summary report with score distribution,
threshold-based flag counts, and the top suspected anomalies.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from quant_utils import read_dataframe, require_columns
from scipy.stats import chi2


def _zscore(values: np.ndarray) -> np.ndarray:
    finite = values[np.isfinite(values)]
    if finite.size < 2:
        return np.zeros_like(values)
    mean = float(finite.mean())
    sd = float(finite.std(ddof=1))
    if sd == 0:
        return np.zeros_like(values)
    return np.abs((values - mean) / sd)


def _iqr(values: np.ndarray) -> np.ndarray:
    finite = values[np.isfinite(values)]
    if finite.size < 4:
        return np.zeros_like(values)
    q1, q3 = np.quantile(finite, [0.25, 0.75])
    iqr_val = q3 - q1
    if iqr_val == 0:
        return np.zeros_like(values)
    return np.maximum(values - q3, q1 - values) / iqr_val


def _mahalanobis(X: np.ndarray) -> np.ndarray:
    mask = np.all(np.isfinite(X), axis=1)
    finite = X[mask]
    if finite.shape[0] < finite.shape[1] + 2:
        return np.full(X.shape[0], np.nan)
    mean = finite.mean(axis=0)
    centered = finite - mean
    cov = (centered.T @ centered) / (finite.shape[0] - 1)
    diag = np.diag(np.diag(cov))
    # Ledoit-Wolf style shrinkage toward diagonal to handle near-singular cases.
    shrinkage = 0.1
    cov_shrunk = (1.0 - shrinkage) * cov + shrinkage * diag + 1e-8 * np.eye(cov.shape[0])
    try:
        cov_inv = np.linalg.pinv(cov_shrunk)
    except np.linalg.LinAlgError:
        return np.full(X.shape[0], np.nan)
    out = np.full(X.shape[0], np.nan)
    delta = X - mean
    for i in range(X.shape[0]):
        if not np.all(np.isfinite(delta[i])):
            continue
        out[i] = float(np.sqrt(max(delta[i] @ cov_inv @ delta[i], 0.0)))
    return out


def build_report(
    df: pd.DataFrame,
    columns: list[str],
    method: str,
    threshold: float,
    top_k: int,
    id_col: str | None,
) -> tuple[dict[str, Any], pd.DataFrame]:
    numeric = df[columns].apply(lambda s: pd.to_numeric(s, errors="coerce"))
    if method == "zscore":
        score_matrix = np.column_stack([_zscore(numeric[c].to_numpy()) for c in columns])
        per_row_score = np.nanmax(score_matrix, axis=1)
    elif method == "iqr":
        score_matrix = np.column_stack([_iqr(numeric[c].to_numpy()) for c in columns])
        per_row_score = np.nanmax(score_matrix, axis=1)
    elif method == "mahalanobis":
        per_row_score = _mahalanobis(numeric.to_numpy())
    else:
        raise SystemExit(f"Unknown --method: {method}")

    out_df = df.copy()
    out_df["anomaly_score"] = per_row_score
    out_df["is_anomaly"] = per_row_score >= threshold
    finite_scores = pd.Series(per_row_score).dropna()
    flagged = int(out_df["is_anomaly"].sum())
    top_indices = np.argsort(-np.nan_to_num(per_row_score, nan=-np.inf))[:top_k]
    top_rows = []
    for idx in top_indices:
        if not np.isfinite(per_row_score[idx]):
            continue
        row = {"row_index": int(idx), "score": float(per_row_score[idx])}
        if id_col:
            row[id_col] = str(df.iloc[idx][id_col])
        for col in columns:
            row[col] = float(numeric.iloc[idx][col]) if pd.notna(numeric.iloc[idx][col]) else None
        top_rows.append(row)

    report = {
        "method": method,
        "columns": columns,
        "threshold": threshold,
        "rows": int(len(df)),
        "scored_rows": int(finite_scores.size),
        "flagged_rows": flagged,
        "flag_rate": flagged / len(df) if len(df) else None,
        "score_summary": {
            "mean": float(finite_scores.mean()) if finite_scores.size else None,
            "stdev": float(finite_scores.std(ddof=1)) if finite_scores.size >= 2 else None,
            "q25": float(np.quantile(finite_scores, 0.25)) if finite_scores.size else None,
            "q50": float(np.quantile(finite_scores, 0.50)) if finite_scores.size else None,
            "q75": float(np.quantile(finite_scores, 0.75)) if finite_scores.size else None,
            "q95": float(np.quantile(finite_scores, 0.95)) if finite_scores.size else None,
            "max": float(finite_scores.max()) if finite_scores.size else None,
        },
        "top_rows": top_rows,
        "notes": [
            "Z-score and IQR methods produce per-column scores aggregated by max; "
            "tune --threshold per scale.",
            "Mahalanobis assumes approximate multivariate normality; covariance is "
            "shrunk toward the diagonal to handle near-singularity.",
            "Anomaly score >= threshold is a coarse flag; verify with domain context before acting on it.",
        ],
    }
    if method == "mahalanobis":
        dof = len(columns)
        report["chi2_p_at_threshold"] = float(1.0 - chi2.cdf(threshold**2, dof))
        report["notes"].append(
            f"For Mahalanobis with {dof} features, threshold {threshold} corresponds "
            f"to chi2 p ~ {report['chi2_p_at_threshold']:.4g}."
        )
    return report, out_df


def markdown(report: dict[str, Any]) -> str:
    s = report["score_summary"]
    lines = [
        "# Anomaly Score Report",
        "",
        f"- Method: {report['method']}",
        f"- Columns: {', '.join(report['columns'])}",
        f"- Threshold: {report['threshold']}",
        f"- Rows: {report['rows']} (scored {report['scored_rows']}, flagged {report['flagged_rows']})",
        f"- Flag rate: {report['flag_rate']}",
        "",
        "## Score Distribution",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Mean | {s['mean']} |",
        f"| Stdev | {s['stdev']} |",
        f"| Q25 | {s['q25']} |",
        f"| Median | {s['q50']} |",
        f"| Q75 | {s['q75']} |",
        f"| Q95 | {s['q95']} |",
        f"| Max | {s['max']} |",
        "",
        "## Top Suspected Anomalies",
        "",
        "| Row index | Score |",
        "| --- | --- |",
    ]
    for row in report["top_rows"]:
        lines.append(f"| {row['row_index']} | {row['score']} |")
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Univariate and multivariate anomaly score diagnostics.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--columns", required=True, help="Comma-separated numeric columns.")
    parser.add_argument("--method", choices=["zscore", "iqr", "mahalanobis"], default="zscore")
    parser.add_argument("--threshold", type=float, default=3.0)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--id-col")
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    columns = [c.strip() for c in args.columns.split(",") if c.strip()]
    if not columns:
        raise SystemExit("--columns must include at least one numeric column.")
    df = read_dataframe(args.csv_path)
    require_columns(df, columns + ([args.id_col] if args.id_col else []))
    report, scored = build_report(df, columns, args.method, args.threshold, args.top_k, args.id_col)
    if args.output_csv:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        scored.to_csv(args.output_csv, index=False, encoding="utf-8")
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
