#!/usr/bin/env python3
"""Cluster quality diagnostics: silhouette + bootstrap stability.

Given a feature CSV and a cluster assignment column (or k-means k), the
report computes silhouette score, per-cluster sizes, and bootstrap-stability
estimates of cluster assignments.

Requires ``scikit-learn``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from quant_utils import read_dataframe, require_columns


def _require_sklearn():
    try:
        from sklearn.cluster import KMeans
        from sklearn.metrics import (
            adjusted_rand_score,
            calinski_harabasz_score,
            davies_bouldin_score,
            silhouette_score,
        )
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise SystemExit(
            "scikit-learn is required for cluster_quality_report.py; install via 'pip install scikit-learn'."
        ) from exc
    return {
        "KMeans": KMeans,
        "adjusted_rand_score": adjusted_rand_score,
        "calinski_harabasz_score": calinski_harabasz_score,
        "davies_bouldin_score": davies_bouldin_score,
        "silhouette_score": silhouette_score,
        "StandardScaler": StandardScaler,
    }


def build_report(
    df: pd.DataFrame,
    feature_cols: list[str],
    cluster_col: str | None,
    k: int | None,
    bootstrap: int,
    sample_frac: float,
    standardize: bool,
    seed: int,
) -> dict[str, Any]:
    sk = _require_sklearn()
    numeric = df[feature_cols].apply(lambda s: pd.to_numeric(s, errors="coerce"))
    rows_in = len(df)
    mask = numeric.notna().all(axis=1)
    df = df.loc[mask].reset_index(drop=True)
    X = numeric.loc[mask].to_numpy(dtype=float)
    dropped = rows_in - len(df)
    if standardize:
        X_std = sk["StandardScaler"]().fit_transform(X)
    else:
        X_std = X

    if cluster_col is not None:
        labels = df[cluster_col].astype(str).to_numpy()
        method = f"provided:{cluster_col}"
    else:
        if k is None or k < 2:
            raise SystemExit("Either provide --cluster-col or --k with k >= 2.")
        km = sk["KMeans"](n_clusters=k, n_init=10, random_state=seed)
        labels = km.fit_predict(X_std).astype(str)
        method = f"kmeans_k{k}"

    unique_labels, counts = np.unique(labels, return_counts=True)
    n_clusters = int(len(unique_labels))
    cluster_sizes = {str(lbl): int(c) for lbl, c in zip(unique_labels, counts, strict=False)}
    if n_clusters < 2 or n_clusters >= len(X_std):
        silhouette = None
        ch = None
        db = None
    else:
        silhouette = float(sk["silhouette_score"](X_std, labels))
        ch = float(sk["calinski_harabasz_score"](X_std, labels))
        db = float(sk["davies_bouldin_score"](X_std, labels))

    stability_scores: list[float] = []
    if bootstrap > 0 and cluster_col is None and k is not None and len(X_std) > k:
        rng = np.random.default_rng(seed)
        base_labels = labels
        n = len(X_std)
        for _ in range(bootstrap):
            idx = rng.choice(n, size=max(int(n * sample_frac), k + 1), replace=True)
            X_b = X_std[idx]
            km_b = sk["KMeans"](n_clusters=k, n_init=5, random_state=int(rng.integers(1 << 30)))
            labels_b = km_b.fit_predict(X_b)
            ari = float(sk["adjusted_rand_score"](base_labels[idx], labels_b.astype(str)))
            stability_scores.append(ari)

    stability_summary = None
    if stability_scores:
        arr = np.asarray(stability_scores)
        stability_summary = {
            "n_bootstraps": int(arr.size),
            "mean_ari": float(arr.mean()),
            "stdev_ari": float(arr.std(ddof=1)) if arr.size >= 2 else None,
            "min_ari": float(arr.min()),
            "max_ari": float(arr.max()),
        }

    return {
        "feature_cols": feature_cols,
        "cluster_col": cluster_col,
        "k": k,
        "method": method,
        "rows_used": int(len(df)),
        "rows_dropped": dropped,
        "n_clusters": n_clusters,
        "cluster_sizes": cluster_sizes,
        "standardize": standardize,
        "silhouette_score": silhouette,
        "calinski_harabasz_score": ch,
        "davies_bouldin_score": db,
        "stability_summary": stability_summary,
        "notes": [
            "Silhouette in [-1, 1]: higher is better; near zero means weak separation.",
            "Calinski-Harabasz higher is better; Davies-Bouldin lower is better.",
            "Bootstrap ARI measures the stability of k-means assignments to resampled "
            "data; low ARI suggests fragile clusters.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Cluster Quality Report",
        "",
        f"- Features: {', '.join(report['feature_cols'])}",
        f"- Method: {report['method']}",
        f"- Rows used: {report['rows_used']} (dropped {report['rows_dropped']})",
        f"- Clusters: {report['n_clusters']}",
        f"- Standardized: {report['standardize']}",
        "",
        "## Cluster Sizes",
        "",
        "| Cluster | N |",
        "| --- | --- |",
    ]
    for label, count in report["cluster_sizes"].items():
        lines.append(f"| {label} | {count} |")
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            f"- Silhouette: {report['silhouette_score']}",
            f"- Calinski-Harabasz: {report['calinski_harabasz_score']}",
            f"- Davies-Bouldin: {report['davies_bouldin_score']}",
        ]
    )
    if report["stability_summary"]:
        s = report["stability_summary"]
        lines.extend(
            [
                "",
                "## Bootstrap Stability (ARI)",
                "",
                f"- Bootstraps: {s['n_bootstraps']}",
                f"- Mean ARI: {s['mean_ari']}",
                f"- Stdev ARI: {s['stdev_ari']}",
                f"- Min/Max: {s['min_ari']} / {s['max_ari']}",
            ]
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cluster quality diagnostics with silhouette and bootstrap ARI stability."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--feature-cols", required=True, help="Comma-separated numeric feature columns.")
    parser.add_argument("--cluster-col", help="Optional precomputed cluster label column.")
    parser.add_argument("--k", type=int, help="If --cluster-col not given, run k-means with this k.")
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=20,
        help="Bootstrap iterations for stability (only when k-means is used).",
    )
    parser.add_argument("--sample-frac", type=float, default=0.8)
    parser.add_argument("--no-standardize", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    feature_cols = [c.strip() for c in args.feature_cols.split(",") if c.strip()]
    if not feature_cols:
        raise SystemExit("--feature-cols must include at least one column.")
    if args.cluster_col is None and args.k is None:
        raise SystemExit("Provide --cluster-col or --k.")
    df = read_dataframe(args.csv_path)
    require_columns(df, feature_cols + ([args.cluster_col] if args.cluster_col else []))
    report = build_report(
        df,
        feature_cols,
        args.cluster_col,
        args.k,
        args.bootstrap,
        args.sample_frac,
        not args.no_standardize,
        args.seed,
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
