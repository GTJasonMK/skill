#!/usr/bin/env python3
"""Audit a quant research experiment registry for data-snooping risk.

Requires the shared bundle core dependencies. This script reads a CSV log of tested alpha factors,
strategy variants, parameter sweeps, or portfolio experiments and reports
whether the research trail is complete enough to support later gate decisions.
It complements p-value corrections and reality checks by checking whether the
full tested family, failed trials, final tests, and version evidence were
actually recorded.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import parse_float, read_dataframe
from quant_utils import summarize_series as summarize_values


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")


TRUE_VALUES = {
    "1",
    "true",
    "t",
    "yes",
    "y",
    "selected",
    "promoted",
    "approved",
    "pass",
    "passed",
    "winner",
    "live",
    "paper",
}
FALSE_VALUES = {
    "0",
    "false",
    "f",
    "no",
    "n",
    "rejected",
    "reject",
    "fail",
    "failed",
    "dropped",
    "abandoned",
    "killed",
}
SELECTED_STATUS = {
    "selected",
    "promoted",
    "approved",
    "pass",
    "passed",
    "winner",
    "paper",
    "paper_trading",
    "live",
}
FAILED_STATUS = {"rejected", "reject", "fail", "failed", "dropped", "abandoned", "killed", "retired"}


def present_columns(header: list[str], columns: dict[str, str]) -> dict[str, bool]:
    return {name: bool(col and col in header) for name, col in columns.items()}


def text(row: dict[str, str], col: str | None) -> str:
    return str(row.get(col or "", "")).strip()


def normalized(row: dict[str, str], col: str | None) -> str:
    return text(row, col).lower().replace(" ", "_").replace("-", "_")


def boolish(row: dict[str, str], col: str | None) -> bool | None:
    if not col or col not in row:
        return None
    value = normalized(row, col)
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    if value == "":
        return None
    return None


def experiment_id(row: dict[str, str], id_col: str | None, index: int) -> str:
    value = text(row, id_col)
    return value or str(index)


def is_selected(row: dict[str, str], selected_col: str | None, status_col: str | None) -> bool:
    selected = boolish(row, selected_col)
    if selected is not None:
        return selected
    status = normalized(row, status_col)
    return status in SELECTED_STATUS


def is_failed(row: dict[str, str], status_col: str | None) -> bool:
    return normalized(row, status_col) in FAILED_STATUS


def has_value(row: dict[str, str], col: str | None) -> bool:
    return bool(text(row, col))


def bh_adjust(pvalues: list[float]) -> list[float]:
    m = len(pvalues)
    indexed = sorted(enumerate(pvalues), key=lambda item: item[1], reverse=True)
    adjusted = [1.0] * m
    running = 1.0
    for reverse_rank, (idx, pvalue) in enumerate(indexed):
        rank = m - reverse_rank
        value = min(pvalue * m / rank, 1.0)
        running = min(running, value)
        adjusted[idx] = running
    return adjusted


def finding(
    severity: str,
    check: str,
    detail: str,
    metric: Any = None,
    threshold: Any = None,
    ids: list[str] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {"severity": severity, "check": check, "detail": detail}
    if metric is not None:
        out["metric"] = metric
    if threshold is not None:
        out["threshold"] = threshold
    if ids:
        out["experiment_ids"] = ids[:20]
    return out


def severity_rank(item: dict[str, Any]) -> int:
    return {"info": 0, "warning": 1, "blocker": 2}.get(str(item.get("severity", "info")), 0)


def pct(part: int, whole: int) -> float | None:
    return part / whole if whole else None


def compact_family_summary(
    family: str, rows: list[dict[str, str]], args: argparse.Namespace
) -> dict[str, Any]:
    selected = [row for row in rows if is_selected(row, args.selected_col, args.status_col)]
    failed = [row for row in rows if is_failed(row, args.status_col)]
    predeclared = [row for row in rows if boolish(row, args.predeclared_col) is True]
    final_tested = [
        row
        for row in rows
        if boolish(row, args.final_test_col) is True or has_value(row, args.test_metric_col)
    ]
    return {
        "family": family,
        "experiment_count": len(rows),
        "selected_count": len(selected),
        "failed_count": len(failed),
        "predeclared_count": len(predeclared),
        "final_tested_count": len(final_tested),
        "selected_rate": pct(len(selected), len(rows)),
    }


def metric_degradation(
    rows: list[dict[str, str]], args: argparse.Namespace
) -> tuple[list[dict[str, Any]], list[float], int]:
    records: list[dict[str, Any]] = []
    degradations: list[float] = []
    missing = 0
    if not args.validation_metric_col or not args.test_metric_col:
        return records, degradations, missing

    for i, row in enumerate(rows, start=1):
        validation = parse_float(row.get(args.validation_metric_col))
        test = parse_float(row.get(args.test_metric_col))
        if validation is None or test is None:
            if is_selected(row, args.selected_col, args.status_col):
                missing += 1
            continue
        degradation = validation - test if args.metric_direction == "higher" else test - validation
        degradations.append(degradation)
        records.append(
            {
                "experiment_id": experiment_id(row, args.id_col, i),
                "validation_metric": validation,
                "test_metric": test,
                "degradation": degradation,
                "selected": is_selected(row, args.selected_col, args.status_col),
            }
        )
    return records, degradations, missing


def multiple_testing_summary(rows: list[dict[str, str]], args: argparse.Namespace) -> dict[str, Any]:
    if not args.p_col:
        return {
            "p_col": args.p_col,
            "tests_used": 0,
            "rows_dropped": 0,
            "discoveries": {},
            "selected_raw_not_bh": [],
        }

    tests: list[dict[str, Any]] = []
    dropped = 0
    for i, row in enumerate(rows, start=1):
        pvalue = parse_float(row.get(args.p_col))
        if pvalue is None or pvalue < 0 or pvalue > 1:
            dropped += 1
            continue
        tests.append(
            {
                "experiment_id": experiment_id(row, args.id_col, i),
                "p_value": pvalue,
                "selected": is_selected(row, args.selected_col, args.status_col),
            }
        )

    adjusted = bh_adjust([item["p_value"] for item in tests]) if tests else []
    selected_raw_not_bh = []
    for item, qvalue in zip(tests, adjusted, strict=False):
        item["bh_fdr_p"] = qvalue
        item["significant_raw"] = item["p_value"] <= args.alpha
        item["significant_bh_fdr"] = qvalue <= args.alpha
        if item["selected"] and item["significant_raw"] and not item["significant_bh_fdr"]:
            selected_raw_not_bh.append(item["experiment_id"])

    return {
        "p_col": args.p_col,
        "alpha": args.alpha,
        "tests_used": len(tests),
        "rows_dropped": dropped,
        "discoveries": {
            "raw": sum(item["significant_raw"] for item in tests),
            "bh_fdr": sum(item["significant_bh_fdr"] for item in tests),
        },
        "selected_raw_not_bh": selected_raw_not_bh,
        "tests": sorted(tests, key=lambda item: item["p_value"])[:50],
    }


def build_report(header: list[str], rows: list[dict[str, str]], args: argparse.Namespace) -> dict[str, Any]:
    columns = {
        "id_col": args.id_col,
        "family_col": args.family_col,
        "status_col": args.status_col,
        "selected_col": args.selected_col,
        "predeclared_col": args.predeclared_col,
        "final_test_col": args.final_test_col,
        "validation_metric_col": args.validation_metric_col,
        "test_metric_col": args.test_metric_col,
        "p_col": args.p_col,
        "data_version_col": args.data_version_col,
        "code_version_col": args.code_version_col,
    }
    coverage = present_columns(header, columns)
    findings: list[dict[str, Any]] = []
    n = len(rows)
    if n == 0:
        findings.append(finding("blocker", "empty_registry", "The experiment registry has no rows."))

    missing_core = [
        name
        for name in ["family_col", "status_col", "predeclared_col", "final_test_col"]
        if not coverage.get(name)
    ]
    if missing_core:
        findings.append(
            finding("warning", "missing_audit_columns", "Core audit columns are missing.", missing_core)
        )

    selected_rows = [row for row in rows if is_selected(row, args.selected_col, args.status_col)]
    failed_rows = [row for row in rows if is_failed(row, args.status_col)]
    predeclared_false = [
        experiment_id(row, args.id_col, i)
        for i, row in enumerate(rows, start=1)
        if boolish(row, args.predeclared_col) is False
    ]
    predeclared_missing = [
        experiment_id(row, args.id_col, i)
        for i, row in enumerate(rows, start=1)
        if coverage.get("predeclared_col") and boolish(row, args.predeclared_col) is None
    ]
    final_missing_selected = [
        experiment_id(row, args.id_col, i)
        for i, row in enumerate(rows, start=1)
        if is_selected(row, args.selected_col, args.status_col)
        and not (boolish(row, args.final_test_col) is True or has_value(row, args.test_metric_col))
    ]
    data_version_missing = [
        experiment_id(row, args.id_col, i)
        for i, row in enumerate(rows, start=1)
        if coverage.get("data_version_col") and not has_value(row, args.data_version_col)
    ]
    code_version_missing = [
        experiment_id(row, args.id_col, i)
        for i, row in enumerate(rows, start=1)
        if coverage.get("code_version_col") and not has_value(row, args.code_version_col)
    ]

    if failed_rows == [] and n >= args.min_registry_size_for_failure_warning:
        findings.append(
            finding(
                "warning",
                "no_failed_trials_recorded",
                "No failed, rejected, dropped, or abandoned trials are recorded; the registry may omit unsuccessful experiments.",
                0,
                ">=1",
            )
        )
    if (
        pct(len(predeclared_false) + len(predeclared_missing), n) is not None
        and pct(len(predeclared_false) + len(predeclared_missing), n) > args.max_unregistered_rate
    ):
        findings.append(
            finding(
                "warning",
                "unregistered_experiments",
                "Some experiments are not predeclared or have missing predeclaration status.",
                pct(len(predeclared_false) + len(predeclared_missing), n),
                args.max_unregistered_rate,
                predeclared_false + predeclared_missing,
            )
        )
    if (
        final_missing_selected
        and pct(len(final_missing_selected), max(len(selected_rows), 1))
        > args.max_selected_missing_final_test_rate
    ):
        findings.append(
            finding(
                "blocker",
                "selected_missing_final_test",
                "Selected or promoted experiments are missing final-test evidence.",
                pct(len(final_missing_selected), max(len(selected_rows), 1)),
                args.max_selected_missing_final_test_rate,
                final_missing_selected,
            )
        )
    if coverage.get("data_version_col") and data_version_missing:
        findings.append(
            finding(
                "warning",
                "missing_data_version",
                "Some experiments lack data-version evidence.",
                len(data_version_missing),
                0,
                data_version_missing,
            )
        )
    if coverage.get("code_version_col") and code_version_missing:
        findings.append(
            finding(
                "warning",
                "missing_code_version",
                "Some experiments lack code-version evidence.",
                len(code_version_missing),
                0,
                code_version_missing,
            )
        )

    degradation_records, degradations, selected_metric_missing = metric_degradation(rows, args)
    selected_degraded = [
        item
        for item in degradation_records
        if item["selected"] and item["degradation"] > args.max_degradation
    ]
    if selected_metric_missing:
        findings.append(
            finding(
                "warning",
                "selected_missing_metric_pair",
                "Selected experiments are missing validation or final-test metric pairs.",
                selected_metric_missing,
                0,
            )
        )
    if selected_degraded:
        findings.append(
            finding(
                "warning",
                "selected_validation_test_degradation",
                "Selected experiments degrade from validation to final test beyond the allowed threshold.",
                max(item["degradation"] for item in selected_degraded),
                args.max_degradation,
                [item["experiment_id"] for item in selected_degraded],
            )
        )

    mt = (
        multiple_testing_summary(rows, args)
        if coverage.get("p_col")
        else {
            "p_col": args.p_col,
            "tests_used": 0,
            "rows_dropped": 0,
            "discoveries": {},
            "selected_raw_not_bh": [],
        }
    )
    if mt.get("selected_raw_not_bh"):
        findings.append(
            finding(
                "warning",
                "selected_raw_not_fdr",
                "Some selected experiments are raw-significant but do not survive Benjamini-Hochberg FDR.",
                len(mt["selected_raw_not_bh"]),
                0,
                mt["selected_raw_not_bh"],
            )
        )

    family_map: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        family = text(row, args.family_col) if coverage.get("family_col") else "all"
        family_map.setdefault(family or "missing_family", []).append(row)
    families = [
        compact_family_summary(family, family_rows, args)
        for family, family_rows in sorted(family_map.items())
    ]
    large_families = [item for item in families if item["experiment_count"] >= args.large_family_threshold]
    if large_families and not coverage.get("p_col"):
        findings.append(
            finding(
                "warning",
                "large_family_without_p_values",
                "Large experiment families exist but no p-value column is available for false-discovery review.",
                [item["family"] for item in large_families],
                args.large_family_threshold,
            )
        )

    blocker_count = sum(1 for item in findings if item["severity"] == "blocker")
    warning_count = sum(1 for item in findings if item["severity"] == "warning")
    top_findings = sorted(findings, key=lambda item: (severity_rank(item), item["check"]), reverse=True)
    return {
        "audit_type": "quant_experiment_audit",
        "experiment_count": n,
        "family_count": len(families),
        "selected_count": len(selected_rows),
        "failed_count": len(failed_rows),
        "predeclared_missing_or_false_count": len(predeclared_false) + len(predeclared_missing),
        "selected_missing_final_test_count": len(final_missing_selected),
        "data_version_missing_count": len(data_version_missing),
        "code_version_missing_count": len(code_version_missing),
        "blocker_count": blocker_count,
        "warning_count": warning_count,
        "finding_count": len(findings),
        "column_coverage": coverage,
        "rates": {
            "selected_rate": pct(len(selected_rows), n),
            "failed_recorded_rate": pct(len(failed_rows), n),
            "predeclared_missing_or_false_rate": pct(len(predeclared_false) + len(predeclared_missing), n),
            "selected_missing_final_test_rate": pct(len(final_missing_selected), max(len(selected_rows), 1)),
        },
        "metric_direction": args.metric_direction,
        "metric_degradation_summary": summarize_values(degradations),
        "largest_validation_test_degradations": sorted(
            degradation_records, key=lambda item: item["degradation"], reverse=True
        )[:20],
        "multiple_testing": mt,
        "families": families,
        "top_findings": top_findings[: args.finding_limit],
        "notes": [
            "This report audits the research trail; it does not prove a signal is predictive or tradable.",
            "The registry should include failed and abandoned trials, not only promoted variants.",
            "Use this before multiple-testing correction, reality checks, alpha gates, and committee review packs.",
        ],
    }


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Quant Experiment Audit",
        "",
        f"- Experiments: {report['experiment_count']}",
        f"- Families: {report['family_count']}",
        f"- Selected/promoted: {report['selected_count']}",
        f"- Failed/rejected recorded: {report['failed_count']}",
        f"- Blockers: {report['blocker_count']}",
        f"- Warnings: {report['warning_count']}",
        "",
        "## Column Coverage",
        "",
        "| Column role | Present |",
        "| --- | --- |",
    ]
    for name, present in report["column_coverage"].items():
        lines.append(f"| {name} | {present} |")

    lines.extend(
        [
            "",
            "## Family Summary",
            "",
            "| Family | Experiments | Selected | Failed | Predeclared | Final tested |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in report["families"]:
        lines.append(
            f"| {md_escape(item['family'])} | {item['experiment_count']} | {item['selected_count']} | {item['failed_count']} | {item['predeclared_count']} | {item['final_tested_count']} |"
        )

    mt = report["multiple_testing"]
    discoveries = mt.get("discoveries", {})
    lines.extend(
        [
            "",
            "## Multiple-Testing Trail",
            "",
            f"- P-value tests used: {mt.get('tests_used', 0)}",
            f"- Raw discoveries: {discoveries.get('raw', 0)}",
            f"- BH-FDR discoveries: {discoveries.get('bh_fdr', 0)}",
            f"- Selected raw-not-FDR count: {len(mt.get('selected_raw_not_bh', []))}",
            "",
            "## Top Findings",
            "",
            "| Severity | Check | Detail | Metric | Threshold | Experiment IDs |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    if report["top_findings"]:
        for item in report["top_findings"]:
            lines.append(
                f"| {item['severity']} | {md_escape(item['check'])} | {md_escape(item['detail'])} | {md_escape(item.get('metric', ''))} | {md_escape(item.get('threshold', ''))} | {md_escape(', '.join(item.get('experiment_ids', [])))} |"
            )
    else:
        lines.append("| info | no_findings | No audit findings from supplied registry. |  |  |  |")

    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit a quant research experiment registry for data-snooping and selective-reporting risk."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--id-col", default="experiment_id")
    parser.add_argument("--family-col", default="family")
    parser.add_argument("--status-col", default="status")
    parser.add_argument("--selected-col", default="selected")
    parser.add_argument("--predeclared-col", default="predeclared")
    parser.add_argument("--final-test-col", default="final_test_done")
    parser.add_argument("--validation-metric-col", default="validation_metric")
    parser.add_argument("--test-metric-col", default="test_metric")
    parser.add_argument("--p-col", default="p_value")
    parser.add_argument("--data-version-col", default="data_version")
    parser.add_argument("--code-version-col", default="code_version")
    parser.add_argument("--metric-direction", choices=["higher", "lower"], default="higher")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--max-unregistered-rate", type=float, default=0.0)
    parser.add_argument("--max-selected-missing-final-test-rate", type=float, default=0.0)
    parser.add_argument("--max-degradation", type=float, default=0.25)
    parser.add_argument("--min-registry-size-for-failure-warning", type=int, default=5)
    parser.add_argument("--large-family-threshold", type=int, default=20)
    parser.add_argument("--finding-limit", type=int, default=30)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.alpha <= 0 or args.alpha >= 1:
        raise SystemExit("--alpha must be in (0, 1).")
    for name in ["max_unregistered_rate", "max_selected_missing_final_test_rate"]:
        value = getattr(args, name)
        if value < 0 or value > 1:
            raise SystemExit(f"--{name.replace('_', '-')} must be in [0, 1].")
    if args.finding_limit <= 0:
        raise SystemExit("--finding-limit must be positive.")

    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    report = build_report(header, rows, args)
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
