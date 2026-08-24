#!/usr/bin/env python3
"""Probability calibration diagnostics: reliability curve, ECE, Brier.

Input is a CSV with a binary label column (0/1) and a predicted-probability
column for the positive class. Reports per-bin reliability, the expected
calibration error (ECE), maximum calibration error (MCE), Brier score, and
log loss.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from quant_utils import read_dataframe, require_columns


def _label_to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1 if value else 0
    text = str(value).strip().lower()
    if text in {"1", "true", "t", "yes", "y", "pos", "positive"}:
        return 1
    if text in {"0", "false", "f", "no", "n", "neg", "negative"}:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return None


def build_report(
    df: pd.DataFrame,
    label_col: str,
    score_col: str,
    bins: int,
    binning: str,
) -> dict[str, Any]:
    rows_in = len(df)
    df = df.copy()
    df[score_col] = pd.to_numeric(df[score_col], errors="coerce")
    df["_label_int"] = df[label_col].map(_label_to_int)
    df = df.dropna(subset=[score_col, "_label_int"])
    df = df[(df[score_col] >= 0) & (df[score_col] <= 1)]
    dropped = rows_in - len(df)
    if df.empty:
        raise SystemExit("No valid rows after filtering.")
    y = df["_label_int"].astype(int).to_numpy()
    p = df[score_col].to_numpy(dtype=float)

    if binning == "equal_width":
        edges = np.linspace(0.0, 1.0, bins + 1)
    elif binning == "equal_frequency":
        edges = np.unique(np.quantile(p, np.linspace(0.0, 1.0, bins + 1)))
        if len(edges) < 3:
            edges = np.linspace(0.0, 1.0, 3)
    else:
        raise SystemExit(f"Unknown --binning: {binning}")
    edges[0] = 0.0
    edges[-1] = 1.0
    bin_idx = np.clip(np.digitize(p, edges[1:-1], right=False), 0, len(edges) - 2)

    n = len(p)
    bin_rows = []
    ece = 0.0
    mce = 0.0
    for b in range(len(edges) - 1):
        mask = bin_idx == b
        count = int(mask.sum())
        if count == 0:
            bin_rows.append(
                {
                    "bin": b,
                    "lower": float(edges[b]),
                    "upper": float(edges[b + 1]),
                    "count": 0,
                    "mean_score": None,
                    "fraction_positive": None,
                    "abs_gap": None,
                }
            )
            continue
        mean_score = float(p[mask].mean())
        frac_pos = float(y[mask].mean())
        gap = abs(mean_score - frac_pos)
        ece += (count / n) * gap
        mce = max(mce, gap)
        bin_rows.append(
            {
                "bin": b,
                "lower": float(edges[b]),
                "upper": float(edges[b + 1]),
                "count": count,
                "mean_score": mean_score,
                "fraction_positive": frac_pos,
                "abs_gap": float(gap),
            }
        )

    brier = float(np.mean((p - y) ** 2))
    # log loss with clipping to avoid log(0)
    eps = 1e-15
    p_clip = np.clip(p, eps, 1.0 - eps)
    log_loss = float(-np.mean(y * np.log(p_clip) + (1 - y) * np.log(1 - p_clip)))
    return {
        "label_col": label_col,
        "score_col": score_col,
        "bins": bins,
        "binning": binning,
        "rows_used": int(n),
        "rows_dropped": dropped,
        "positive_rate": float(y.mean()),
        "mean_predicted": float(p.mean()),
        "ece": float(ece),
        "mce": float(mce),
        "brier_score": brier,
        "log_loss": log_loss,
        "bin_table": bin_rows,
        "notes": [
            "ECE is the count-weighted mean absolute gap between predicted probability "
            "and observed positive rate.",
            "MCE is the worst per-bin gap; large values indicate localized miscalibration.",
            "Brier score is the mean squared error of the probability forecast; lower is better.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Calibration Report",
        "",
        f"- Label column: {report['label_col']}",
        f"- Score column: {report['score_col']}",
        f"- Bins: {report['bins']} ({report['binning']})",
        f"- Rows used: {report['rows_used']} (dropped {report['rows_dropped']})",
        f"- Positive rate: {report['positive_rate']}",
        f"- Mean predicted: {report['mean_predicted']}",
        "",
        f"- ECE: {report['ece']}",
        f"- MCE: {report['mce']}",
        f"- Brier score: {report['brier_score']}",
        f"- Log loss: {report['log_loss']}",
        "",
        "## Reliability Table",
        "",
        "| Bin | Range | Count | Mean score | Fraction positive | |Gap| |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["bin_table"]:
        rng = f"[{row['lower']:.3f}, {row['upper']:.3f})"
        lines.append(
            f"| {row['bin']} | {rng} | {row['count']} | {row['mean_score']} | "
            f"{row['fraction_positive']} | {row['abs_gap']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probability calibration diagnostics (reliability + ECE + Brier)."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--label-col", required=True)
    parser.add_argument("--score-col", required=True)
    parser.add_argument("--bins", type=int, default=10)
    parser.add_argument("--binning", choices=["equal_width", "equal_frequency"], default="equal_width")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.bins < 2:
        raise SystemExit("--bins must be at least 2.")
    df = read_dataframe(args.csv_path)
    require_columns(df, [args.label_col, args.score_col])
    report = build_report(df, args.label_col, args.score_col, args.bins, args.binning)
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
