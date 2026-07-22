#!/usr/bin/env python3
"""Compute portfolio volatility and component risk contributions.

Inputs are a weights CSV and a covariance long-table CSV with asset,
asset2, covariance columns.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from quant_utils import read_dataframe, require_columns


def _read_weights(df: pd.DataFrame, asset_col: str, weight_col: str) -> pd.Series:
    df = df.copy()
    df[weight_col] = pd.to_numeric(df[weight_col], errors="coerce")
    df = df.dropna(subset=[asset_col, weight_col])
    df = df[df[asset_col].astype(str).str.len() > 0]
    return df.groupby(asset_col)[weight_col].sum()


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


def build_report(
    weights_df: pd.DataFrame,
    cov_df: pd.DataFrame,
    asset_col: str,
    weight_col: str,
    cov_asset_col: str,
    cov_other_asset_col: str,
    cov_col: str,
    annualization: int,
) -> dict[str, Any]:
    weights_series = _read_weights(weights_df, asset_col, weight_col)
    assets = sorted(weights_series.index.astype(str))
    if len(assets) < 2:
        raise SystemExit("Need at least two assets with weights.")
    weights = weights_series.loc[assets].to_numpy(dtype=float)
    cov = _read_covariance(cov_df, cov_asset_col, cov_other_asset_col, cov_col, assets)
    cov_w = cov @ weights
    variance = float(weights @ cov_w)
    if variance < 0:
        raise SystemExit("Portfolio variance is negative; covariance matrix may be invalid.")
    volatility = float(np.sqrt(variance))
    annualized_volatility = volatility * float(np.sqrt(annualization))
    rows = []
    for asset, weight, marginal in zip(assets, weights, cov_w):
        component_variance = float(weight * marginal)
        pct = component_variance / variance if variance > 0 else None
        rows.append({
            "asset": asset,
            "weight": float(weight),
            "marginal_variance_contribution": float(marginal),
            "component_variance_contribution": component_variance,
            "percent_variance_contribution": pct,
            "component_volatility_contribution": pct * volatility if pct is not None else None,
            "annualized_component_volatility_contribution": pct * annualized_volatility if pct is not None else None,
        })
    return {
        "assets": assets,
        "annualization": annualization,
        "portfolio_variance": variance,
        "portfolio_volatility": volatility,
        "annualized_portfolio_volatility": annualized_volatility,
        "gross_exposure": float(np.abs(weights).sum()),
        "net_exposure": float(weights.sum()),
        "risk_contributions": sorted(rows, key=lambda item: abs(item["percent_variance_contribution"] or 0.0), reverse=True),
        "notes": [
            "Component variance contribution is weight_i * (Cov * weights)_i.",
            "Negative contributions can occur for hedging assets or short positions.",
            "Risk contribution depends entirely on the covariance estimate and should be monitored out of sample.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Risk Contribution Report",
        "",
        f"- Portfolio volatility: {report['portfolio_volatility']}",
        f"- Annualized portfolio volatility: {report['annualized_portfolio_volatility']}",
        f"- Gross exposure: {report['gross_exposure']}",
        f"- Net exposure: {report['net_exposure']}",
        "",
        "| Asset | Weight | Marginal variance | Component variance | Percent risk | Ann. vol contribution |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["risk_contributions"]:
        lines.append(
            f"| {item['asset']} | {item['weight']} | {item['marginal_variance_contribution']} | {item['component_variance_contribution']} | {item['percent_variance_contribution']} | {item['annualized_component_volatility_contribution']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute portfolio volatility and component risk contributions.")
    parser.add_argument("--weights-csv", type=Path, required=True)
    parser.add_argument("--covariance-csv", type=Path, required=True)
    parser.add_argument("--asset-col", default="asset")
    parser.add_argument("--weight-col", default="weight")
    parser.add_argument("--cov-asset-col", default="asset")
    parser.add_argument("--cov-other-asset-col", default="asset2")
    parser.add_argument("--cov-col", default="cov")
    parser.add_argument("--annualization", type=int, default=252)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    w_df = read_dataframe(args.weights_csv)
    c_df = read_dataframe(args.covariance_csv)
    require_columns(w_df, [args.asset_col, args.weight_col])
    require_columns(c_df, [args.cov_asset_col, args.cov_other_asset_col, args.cov_col])
    report = build_report(w_df, c_df, args.asset_col, args.weight_col,
                         args.cov_asset_col, args.cov_other_asset_col, args.cov_col, args.annualization)
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
