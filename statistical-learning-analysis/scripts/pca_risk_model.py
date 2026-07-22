#!/usr/bin/env python3
"""Compute a simple PCA risk-model diagnostic from return columns.

Standard-library only. Uses a Jacobi eigenvalue algorithm for symmetric
covariance/correlation matrices. This is for diagnostics, not production risk
model estimation.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from quant_utils import mean, parse_float, read_dataframe, require_columns, stdev

import pandas as pd


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")




def covariance_matrix(data: list[list[float]]) -> list[list[float]]:
    n = len(data)
    p = len(data[0])
    cols = [[row[j] for row in data] for j in range(p)]
    means = [mean(col) or 0.0 for col in cols]
    return [
        [
            sum((row[i] - means[i]) * (row[j] - means[j]) for row in data) / (n - 1)
            for j in range(p)
        ]
        for i in range(p)
    ]


def correlation_matrix(data: list[list[float]]) -> list[list[float]]:
    cov = covariance_matrix(data)
    p = len(cov)
    vols = [math.sqrt(max(cov[i][i], 0.0)) for i in range(p)]
    return [
        [cov[i][j] / (vols[i] * vols[j]) if vols[i] > 0 and vols[j] > 0 else (1.0 if i == j else 0.0) for j in range(p)]
        for i in range(p)
    ]


def jacobi_eigen(matrix: list[list[float]], max_iter: int = 200, tol: float = 1e-12) -> tuple[list[float], list[list[float]]]:
    n = len(matrix)
    a = [row[:] for row in matrix]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(max_iter):
        p = 0
        q = 1 if n > 1 else 0
        max_off = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                if abs(a[i][j]) > max_off:
                    max_off = abs(a[i][j])
                    p, q = i, j
        if max_off < tol:
            break
        if a[p][p] == a[q][q]:
            angle = math.pi / 4
        else:
            angle = 0.5 * math.atan2(2 * a[p][q], a[q][q] - a[p][p])
        c = math.cos(angle)
        s = math.sin(angle)
        app = c * c * a[p][p] - 2 * s * c * a[p][q] + s * s * a[q][q]
        aqq = s * s * a[p][p] + 2 * s * c * a[p][q] + c * c * a[q][q]
        a[p][p] = app
        a[q][q] = aqq
        a[p][q] = 0.0
        a[q][p] = 0.0
        for r in range(n):
            if r in {p, q}:
                continue
            arp = c * a[r][p] - s * a[r][q]
            arq = s * a[r][p] + c * a[r][q]
            a[r][p] = a[p][r] = arp
            a[r][q] = a[q][r] = arq
        for r in range(n):
            vrp = c * v[r][p] - s * v[r][q]
            vrq = s * v[r][p] + c * v[r][q]
            v[r][p] = vrp
            v[r][q] = vrq
    eigenvalues = [a[i][i] for i in range(n)]
    eigenvectors = [[v[row][col] for row in range(n)] for col in range(n)]
    return eigenvalues, eigenvectors


def build_report(rows: list[dict[str, str]], columns: list[str], matrix_type: str, components: int) -> dict[str, Any]:
    data = []
    dropped = 0
    for row in rows:
        values = [parse_float(row.get(col)) for col in columns]
        if any(value is None for value in values):
            dropped += 1
            continue
        data.append([float(value) for value in values if value is not None])
    if len(data) < 2:
        raise SystemExit("Need at least two complete rows for PCA.")
    matrix = correlation_matrix(data) if matrix_type == "correlation" else covariance_matrix(data)
    eigenvalues, eigenvectors = jacobi_eigen(matrix)
    pairs = sorted(zip(eigenvalues, eigenvectors), key=lambda item: item[0], reverse=True)
    total = sum(max(value, 0.0) for value, _ in pairs)
    component_rows = []
    cumulative = 0.0
    for idx, (value, vector) in enumerate(pairs[:components], start=1):
        explained = max(value, 0.0) / total if total > 0 else None
        cumulative += explained if explained is not None else 0.0
        component_rows.append(
            {
                "component": idx,
                "eigenvalue": value,
                "explained_variance_ratio": explained,
                "cumulative_explained_variance_ratio": cumulative,
                "loadings": {col: loading for col, loading in zip(columns, vector)},
            }
        )
    asset_stats = []
    for j, col in enumerate(columns):
        values = [row[j] for row in data]
        asset_stats.append({"asset": col, "mean_return": mean(values), "volatility": stdev(values)})
    return {
        "columns": columns,
        "matrix_type": matrix_type,
        "components_requested": components,
        "observations_used": len(data),
        "rows_dropped_missing": dropped,
        "asset_stats": asset_stats,
        "matrix": {row_name: {col_name: matrix[i][j] for j, col_name in enumerate(columns)} for i, row_name in enumerate(columns)},
        "components": component_rows,
        "notes": [
            "PCA components are statistical factors; signs and rotations are not economic interpretations.",
            "Use rolling stability, loading sanity checks, and realized-risk validation before treating components as a risk model.",
            "Correlation PCA standardizes assets; covariance PCA lets high-volatility assets dominate components.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# PCA Risk Model Diagnostic",
        "",
        f"- Matrix type: {report['matrix_type']}",
        f"- Observations used: {report['observations_used']}",
        f"- Rows dropped missing: {report['rows_dropped_missing']}",
        "",
        "| Component | Eigenvalue | Explained variance | Cumulative explained |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["components"]:
        lines.append(
            f"| PC{item['component']} | {item['eigenvalue']} | {item['explained_variance_ratio']} | {item['cumulative_explained_variance_ratio']} |"
        )
    lines.extend(["", "## Loadings", ""])
    for item in report["components"]:
        top = sorted(item["loadings"].items(), key=lambda kv: abs(kv[1]), reverse=True)
        lines.append(f"- PC{item['component']}: " + ", ".join(f"{name}={value}" for name, value in top))
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute a simple PCA risk-model diagnostic from return columns.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--columns", required=True, help="Comma-separated return columns.")
    parser.add_argument("--matrix", choices=["correlation", "covariance"], default="correlation")
    parser.add_argument("--components", type=int, default=3)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    columns = [col.strip() for col in args.columns.split(",") if col.strip()]
    if len(columns) < 2:
        raise SystemExit("--columns must include at least two return columns.")
    if args.components < 1:
        raise SystemExit("--components must be at least 1.")
    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    require_columns(header, columns)
    report = build_report(rows, columns, args.matrix, min(args.components, len(columns)))
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

