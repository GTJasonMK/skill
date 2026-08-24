#!/usr/bin/env python3
"""Check portfolio weights against common risk and trading constraints.

Input is a long date-asset-weight CSV with optional category exposure
columns such as sector/country/currency.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import read_dataframe, require_columns, summarize_series


def split_cols(value: str | None) -> list[str]:
    return [col.strip() for col in value.split(",") if col.strip()] if value else []


def _turnover(prev: pd.Series | None, cur: pd.Series) -> float | None:
    if prev is None:
        return None
    combined = pd.concat([prev, cur], axis=1).fillna(0.0)
    return float(0.5 * (combined.iloc[:, 1] - combined.iloc[:, 0]).abs().sum())


def build_report(
    df: pd.DataFrame,
    date_col: str,
    asset_col: str,
    weight_col: str,
    category_cols: list[str],
    max_gross: float,
    min_net: float,
    max_net: float,
    max_abs_weight: float,
    max_turnover: float | None,
    max_category_abs_weight: float | None,
) -> dict[str, Any]:
    df = df.copy()
    df[weight_col] = pd.to_numeric(df[weight_col], errors="coerce")
    rows_in = len(df)
    df = df.dropna(subset=[date_col, asset_col, weight_col])
    df = df[df[asset_col].astype(str).str.len() > 0]
    dropped = rows_in - len(df)

    periods: list[dict[str, Any]] = []
    prev_weights: pd.Series | None = None
    for date, g in df.groupby(date_col, sort=True):
        weights = g.groupby(asset_col)[weight_col].sum()
        gross = float(weights.abs().sum())
        net = float(weights.sum())
        max_name = float(weights.abs().max()) if len(weights) > 0 else 0.0
        period_turnover = _turnover(prev_weights, weights)
        categories: dict[str, dict[str, float]] = {}
        for col in category_cols:
            valid = g[g[col].astype(str).str.len() > 0]
            cat = valid.groupby(col)[weight_col].sum()
            categories[col] = {k: float(v) for k, v in cat.items()}

        violations = []
        if gross > max_gross:
            violations.append({"constraint": "max_gross", "value": gross, "limit": max_gross})
        if net < min_net:
            violations.append({"constraint": "min_net", "value": net, "limit": min_net})
        if net > max_net:
            violations.append({"constraint": "max_net", "value": net, "limit": max_net})
        if max_name > max_abs_weight:
            violations.append({"constraint": "max_abs_weight", "value": max_name, "limit": max_abs_weight})
        if max_turnover is not None and period_turnover is not None and period_turnover > max_turnover:
            violations.append({"constraint": "max_turnover", "value": period_turnover, "limit": max_turnover})
        if max_category_abs_weight is not None:
            for col, exposure in categories.items():
                for label, value in exposure.items():
                    if abs(value) > max_category_abs_weight:
                        violations.append(
                            {
                                "constraint": f"max_abs_{col}",
                                "category": label,
                                "value": value,
                                "limit": max_category_abs_weight,
                            }
                        )
        periods.append(
            {
                "date": date if not isinstance(date, pd.Timestamp) else date.isoformat(),
                "n_assets": int(len(weights)),
                "gross_exposure": gross,
                "net_exposure": net,
                "max_abs_weight": max_name,
                "turnover": period_turnover,
                "category_exposures": categories,
                "violations": violations,
                "passed": not violations,
            }
        )
        prev_weights = weights

    return {
        "date_col": date_col,
        "asset_col": asset_col,
        "weight_col": weight_col,
        "category_cols": category_cols,
        "constraints": {
            "max_gross": max_gross,
            "min_net": min_net,
            "max_net": max_net,
            "max_abs_weight": max_abs_weight,
            "max_turnover": max_turnover,
            "max_category_abs_weight": max_category_abs_weight,
        },
        "periods_used": len(periods),
        "rows_dropped": dropped,
        "periods_passed": sum(item["passed"] for item in periods),
        "periods_failed": sum(not item["passed"] for item in periods),
        "gross_summary": summarize_series([item["gross_exposure"] for item in periods]),
        "net_summary": summarize_series([item["net_exposure"] for item in periods]),
        "turnover_summary": summarize_series(
            [item["turnover"] for item in periods if item["turnover"] is not None]
        ),
        "periods": periods,
        "notes": [
            "Constraints are checked on target weights by date; execution drift is not modeled.",
            "Category exposure constraints use net category weights, not absolute gross category exposure.",
            "Use this before optimization/backtest acceptance to surface leverage, concentration, and turnover breaches.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Portfolio Constraint Check",
        "",
        f"- Periods used: {report['periods_used']}",
        f"- Periods passed: {report['periods_passed']}",
        f"- Periods failed: {report['periods_failed']}",
        f"- Rows dropped: {report['rows_dropped']}",
        "",
        "| Date | Passed | Gross | Net | Max abs weight | Turnover | Violations |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["periods"]:
        violations = "; ".join(v["constraint"] for v in item["violations"])
        lines.append(
            f"| {item['date']} | {item['passed']} | {item['gross_exposure']} | {item['net_exposure']} | {item['max_abs_weight']} | {item['turnover']} | {violations} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check portfolio weights against common risk and trading constraints."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", required=True)
    parser.add_argument("--asset-col", required=True)
    parser.add_argument("--weight-col", required=True)
    parser.add_argument("--category-cols")
    parser.add_argument("--max-gross", type=float, default=1.0)
    parser.add_argument("--min-net", type=float, default=-0.1)
    parser.add_argument("--max-net", type=float, default=0.1)
    parser.add_argument("--max-abs-weight", type=float, default=0.05)
    parser.add_argument("--max-turnover", type=float)
    parser.add_argument("--max-category-abs-weight", type=float)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    category_cols = split_cols(args.category_cols)
    df = read_dataframe(args.csv_path)
    require_columns(df, [args.date_col, args.asset_col, args.weight_col] + category_cols)
    report = build_report(
        df,
        args.date_col,
        args.asset_col,
        args.weight_col,
        category_cols,
        args.max_gross,
        args.min_net,
        args.max_net,
        args.max_abs_weight,
        args.max_turnover,
        args.max_category_abs_weight,
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
