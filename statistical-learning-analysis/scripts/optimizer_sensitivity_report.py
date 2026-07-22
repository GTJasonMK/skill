#!/usr/bin/env python3
"""Assess simple mean-variance weight sensitivity to input perturbations.

This diagnostic uses inverse-covariance times expected returns with
optional long-only clipping. It is not a production optimizer, but it
surfaces fragility to expected-return and covariance noise.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_utils import read_dataframe, require_columns, solve_psd, summarize_series


def _read_expected_returns(df: pd.DataFrame, asset_col: str, mu_col: str) -> pd.Series:
    df = df.copy()
    df[mu_col] = pd.to_numeric(df[mu_col], errors="coerce")
    df = df.dropna(subset=[asset_col, mu_col])
    df = df[df[asset_col].astype(str).str.len() > 0]
    return df.set_index(asset_col)[mu_col]


def _read_covariance(df: pd.DataFrame, asset_col: str, other_asset_col: str,
                     cov_col: str, assets: list[str]) -> np.ndarray:
    df = df.copy()
    df[cov_col] = pd.to_numeric(df[cov_col], errors="coerce")
    df = df.dropna(subset=[asset_col, other_asset_col, cov_col])
    values: dict[tuple[str, str], float] = {}
    for _, row in df.iterrows():
        a = str(row[asset_col])
        b = str(row[other_asset_col])
        cov = float(row[cov_col])
        values[(a, b)] = cov
        values[(b, a)] = cov
    matrix = np.zeros((len(assets), len(assets)), dtype=float)
    for i, a in enumerate(assets):
        for j, b in enumerate(assets):
            if (a, b) not in values:
                raise SystemExit(f"Missing covariance for pair {a}, {b}")
            matrix[i, j] = values[(a, b)]
    return matrix


def _normalize_weights(raw: np.ndarray, long_only: bool) -> np.ndarray:
    values = np.maximum(raw, 0.0) if long_only else raw
    gross = float(np.abs(values).sum())
    if gross == 0:
        return np.full_like(values, 1.0 / len(values))
    return values / gross


def _optimize_weights(mu: np.ndarray, cov: np.ndarray, ridge: float, long_only: bool) -> np.ndarray:
    adjusted = cov + ridge * np.eye(cov.shape[0])
    try:
        raw = solve_psd(adjusted, mu)
    except Exception:
        raw = mu.copy()
    return _normalize_weights(raw, long_only)


def _perturb_cov(cov: np.ndarray, scale: float, rng: np.random.Generator) -> np.ndarray:
    n = cov.shape[0]
    noise = rng.standard_normal((n, n)) * scale
    noise = (noise + noise.T) / 2  # symmetric
    out = cov * (1.0 + noise)
    np.fill_diagonal(out, np.maximum(np.diag(out), 1e-12))
    return out


def build_report(
    mu_df: pd.DataFrame,
    cov_df: pd.DataFrame,
    asset_col: str,
    mu_col: str,
    cov_asset_col: str,
    cov_other_asset_col: str,
    cov_col: str,
    simulations: int,
    mu_noise: float,
    cov_noise: float,
    ridge: float,
    long_only: bool,
    seed: int,
) -> dict[str, Any]:
    mu_series = _read_expected_returns(mu_df, asset_col, mu_col)
    assets = sorted(mu_series.index.astype(str))
    if len(assets) < 2:
        raise SystemExit("Need at least two assets with expected returns.")
    mu = mu_series.loc[assets].to_numpy(dtype=float)
    cov = _read_covariance(cov_df, cov_asset_col, cov_other_asset_col, cov_col, assets)
    base_weights = _optimize_weights(mu, cov, ridge, long_only)
    rng = np.random.default_rng(seed)
    simulated_weights: list[np.ndarray] = []
    for _ in range(simulations):
        mu_sim = mu + rng.standard_normal(mu.shape) * mu_noise
        cov_sim = _perturb_cov(cov, cov_noise, rng)
        simulated_weights.append(_optimize_weights(mu_sim, cov_sim, ridge, long_only))
    sim_mat = np.array(simulated_weights)
    by_asset = []
    for idx, asset in enumerate(assets):
        values = sim_mat[:, idx].tolist()
        flips = int(np.sum((sim_mat[:, idx] >= 0) != (base_weights[idx] >= 0)))
        summary = summarize_series(values)
        by_asset.append({
            "asset": asset,
            "base_weight": float(base_weights[idx]),
            "mean_weight": summary["mean"],
            "stdev_weight": summary["stdev"],
            "min_weight": summary["min"],
            "max_weight": summary["max"],
            "sign_flip_rate": flips / len(values) if values else None,
        })
    l1_distances = [float(np.abs(weights - base_weights).sum()) for weights in simulated_weights]
    concentration = [float((weights ** 2).sum()) for weights in simulated_weights]
    return {
        "assets": assets,
        "simulations": simulations,
        "mu_noise": mu_noise,
        "cov_noise": cov_noise,
        "ridge": ridge,
        "long_only": long_only,
        "seed": seed,
        "base_weights": {asset: float(weight) for asset, weight in zip(assets, base_weights)},
        "weight_summary": by_asset,
        "l1_distance_summary": summarize_series(l1_distances),
        "concentration_hhi_summary": summarize_series(concentration),
        "notes": [
            "This is a sensitivity diagnostic for unconstrained inverse-covariance weights, not a full optimizer.",
            "Large weight dispersion, sign flips, or concentration changes indicate fragile optimization inputs.",
            "Use robust constraints, shrinkage, turnover limits, and out-of-sample monitoring before trading optimized weights.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    dist = report["l1_distance_summary"]
    hhi = report["concentration_hhi_summary"]
    lines = [
        "# Optimizer Sensitivity Report",
        "",
        f"- Simulations: {report['simulations']}",
        f"- Long only: {report['long_only']}",
        f"- Mean L1 distance from base weights: {dist['mean']}",
        f"- Mean concentration HHI: {hhi['mean']}",
        "",
        "| Asset | Base weight | Mean weight | Stdev | Min | Max | Sign flip rate |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["weight_summary"]:
        lines.append(f"| {item['asset']} | {item['base_weight']} | {item['mean_weight']} | {item['stdev_weight']} | {item['min_weight']} | {item['max_weight']} | {item['sign_flip_rate']} |")
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess simple mean-variance weight sensitivity to input perturbations.")
    parser.add_argument("--expected-returns-csv", type=Path, required=True)
    parser.add_argument("--covariance-csv", type=Path, required=True)
    parser.add_argument("--asset-col", default="asset")
    parser.add_argument("--mu-col", default="mu")
    parser.add_argument("--cov-asset-col", default="asset")
    parser.add_argument("--cov-other-asset-col", default="asset2")
    parser.add_argument("--cov-col", default="cov")
    parser.add_argument("--simulations", type=int, default=500)
    parser.add_argument("--mu-noise", type=float, default=0.01)
    parser.add_argument("--cov-noise", type=float, default=0.05)
    parser.add_argument("--ridge", type=float, default=1e-8)
    parser.add_argument("--long-only", action="store_true")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.simulations < 1:
        raise SystemExit("--simulations must be positive.")
    mu_df = read_dataframe(args.expected_returns_csv)
    cov_df = read_dataframe(args.covariance_csv)
    require_columns(mu_df, [args.asset_col, args.mu_col])
    require_columns(cov_df, [args.cov_asset_col, args.cov_other_asset_col, args.cov_col])
    report = build_report(mu_df, cov_df, args.asset_col, args.mu_col, args.cov_asset_col,
                         args.cov_other_asset_col, args.cov_col, args.simulations, args.mu_noise,
                         args.cov_noise, args.ridge, args.long_only, args.seed)
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
