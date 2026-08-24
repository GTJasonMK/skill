#!/usr/bin/env python3
"""Compute simple covariate balance diagnostics for treated/control data.

Standard-library only. Produces standardized mean differences (SMDs) for numeric
covariates and one-vs-rest categorical levels. This is a design diagnostic, not
a causal estimator.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

MISSING = {"", "na", "n/a", "nan", "null", "none", "."}


def is_missing(value: str | None) -> bool:
    return value is None or value.strip().lower() in MISSING


def parse_float(value: str | None) -> float | None:
    if is_missing(value):
        return None
    try:
        out = float(str(value).replace(",", ""))
    except ValueError:
        return None
    return None if math.isnan(out) or math.isinf(out) else out


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]], csv.Dialect]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(handle, dialect=dialect)
        header = list(reader.fieldnames or [])
        rows = [{name: row.get(name, "") for name in header} for row in reader]
    return header, rows, dialect


def is_numeric(values: list[str]) -> bool:
    non_missing = [v for v in values if not is_missing(v)]
    if not non_missing:
        return False
    return sum(parse_float(v) is not None for v in non_missing) / len(non_missing) >= 0.9


def mean(values: Iterable[float]) -> float | None:
    vals = list(values)
    if not vals:
        return None
    return sum(vals) / len(vals)


def variance(values: Iterable[float]) -> float | None:
    vals = list(values)
    if len(vals) < 2:
        return None
    m = sum(vals) / len(vals)
    return sum((v - m) ** 2 for v in vals) / (len(vals) - 1)


def smd_numeric(
    treated_vals: list[float], control_vals: list[float]
) -> tuple[float | None, float | None, float | None]:
    mt = mean(treated_vals)
    mc = mean(control_vals)
    vt = variance(treated_vals) or 0.0
    vc = variance(control_vals) or 0.0
    if mt is None or mc is None:
        return None, mt, mc
    pooled = math.sqrt((vt + vc) / 2)
    if pooled == 0:
        return 0.0 if mt == mc else None, mt, mc
    return (mt - mc) / pooled, mt, mc


def balance_rows(
    rows: list[dict[str, str]], treatment: str, covariates: list[str], treated_value: str, control_value: str
) -> list[dict[str, object]]:
    treated = [row for row in rows if row.get(treatment, "") == treated_value]
    control = [row for row in rows if row.get(treatment, "") == control_value]
    output: list[dict[str, object]] = []
    for covariate in covariates:
        values = [row.get(covariate, "") for row in rows]
        if is_numeric(values):
            treated_vals = [
                v for v in (parse_float(row.get(covariate, "")) for row in treated) if v is not None
            ]
            control_vals = [
                v for v in (parse_float(row.get(covariate, "")) for row in control) if v is not None
            ]
            smd, mt, mc = smd_numeric(treated_vals, control_vals)
            output.append(
                {
                    "covariate": covariate,
                    "level": "",
                    "type": "numeric",
                    "treated_mean": mt,
                    "control_mean": mc,
                    "smd": smd,
                    "abs_smd": abs(smd) if smd is not None else None,
                    "flag_abs_smd_gt_0_1": bool(smd is not None and abs(smd) > 0.1),
                }
            )
        else:
            counts = Counter(v for v in values if not is_missing(v))
            levels = [level for level, _ in counts.most_common(20)]
            for level in levels:
                treated_vals = [1.0 if row.get(covariate, "") == level else 0.0 for row in treated]
                control_vals = [1.0 if row.get(covariate, "") == level else 0.0 for row in control]
                smd, mt, mc = smd_numeric(treated_vals, control_vals)
                output.append(
                    {
                        "covariate": covariate,
                        "level": level,
                        "type": "categorical_level",
                        "treated_mean": mt,
                        "control_mean": mc,
                        "smd": smd,
                        "abs_smd": abs(smd) if smd is not None else None,
                        "flag_abs_smd_gt_0_1": bool(smd is not None and abs(smd) > 0.1),
                    }
                )
    return output


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "covariate",
        "level",
        "type",
        "treated_mean",
        "control_mean",
        "smd",
        "abs_smd",
        "flag_abs_smd_gt_0_1",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def markdown(rows: list[dict[str, object]], limit: int = 30) -> str:
    lines = [
        "# Covariate Balance Check",
        "",
        "| Covariate | Level | Type | Treated mean | Control mean | SMD | Flag |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    sorted_rows = sorted(rows, key=lambda row: (row["abs_smd"] is None, -(row["abs_smd"] or 0)))
    for row in sorted_rows[:limit]:
        smd = "" if row["smd"] is None else f"{row['smd']:.4f}"
        lines.append(
            f"| {row['covariate']} | {row['level']} | {row['type']} | "
            f"{row['treated_mean']} | {row['control_mean']} | {smd} | "
            f"{row['flag_abs_smd_gt_0_1']} |"
        )
    flagged = sum(bool(row["flag_abs_smd_gt_0_1"]) for row in rows)
    lines.extend(
        [
            "",
            f"Flagged rows with |SMD| > 0.1: {flagged}",
            "This is a balance diagnostic, not proof of causal identification.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute standardized mean difference balance diagnostics.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--treatment", required=True, help="Binary treatment column.")
    parser.add_argument(
        "--treated-value", help="Value representing treated group. Defaults to the second sorted value."
    )
    parser.add_argument(
        "--control-value", help="Value representing control group. Defaults to the first sorted value."
    )
    parser.add_argument(
        "--covariates", help="Comma-separated covariates. Defaults to all columns except treatment."
    )
    parser.add_argument("--output-csv", type=Path, help="Optional output CSV path.")
    parser.add_argument("--output-md", type=Path, help="Optional output Markdown path.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    header, rows, _ = read_csv(args.csv_path)
    if args.treatment not in header:
        raise SystemExit(f"Treatment column '{args.treatment}' not found.")
    observed = sorted(
        {row.get(args.treatment, "") for row in rows if not is_missing(row.get(args.treatment, ""))}
    )
    if len(observed) != 2 and (args.treated_value is None or args.control_value is None):
        raise SystemExit(
            "Treatment must have exactly two observed values unless both "
            "--treated-value and --control-value are provided."
        )
    control_value = args.control_value or observed[0]
    treated_value = args.treated_value or observed[1]
    if args.covariates:
        covariates = [name.strip() for name in args.covariates.split(",") if name.strip()]
    else:
        covariates = [name for name in header if name != args.treatment]
    missing_covariates = [name for name in covariates if name not in header]
    if missing_covariates:
        raise SystemExit(f"Covariates not found: {', '.join(missing_covariates)}")
    result_rows = balance_rows(rows, args.treatment, covariates, treated_value, control_value)
    summary = {
        "treated_value": treated_value,
        "control_value": control_value,
        "n_treated": sum(row.get(args.treatment, "") == treated_value for row in rows),
        "n_control": sum(row.get(args.treatment, "") == control_value for row in rows),
        "flagged_abs_smd_gt_0_1": sum(bool(row["flag_abs_smd_gt_0_1"]) for row in result_rows),
        "rows": result_rows,
    }
    if args.output_csv:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        write_rows(args.output_csv, result_rows)
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown(result_rows), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(markdown(result_rows), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
