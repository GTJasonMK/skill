#!/usr/bin/env python3
"""Summarize quant strategy go-live gate checklist status.

Requires the shared bundle core dependencies. Input is a checklist CSV with category, check, status,
severity, and optional evidence/owner fields.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import read_dataframe, require_columns, sorted_group_keys


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")


STATUS_ALIASES = {
    "pass": "pass",
    "passed": "pass",
    "ok": "pass",
    "green": "pass",
    "fail": "fail",
    "failed": "fail",
    "red": "fail",
    "block": "fail",
    "blocked": "fail",
    "warn": "warn",
    "warning": "warn",
    "yellow": "warn",
    "waive": "waived",
    "waived": "waived",
    "missing": "missing",
    "unknown": "unknown",
    "pending": "unknown",
    "na": "not_applicable",
    "n/a": "not_applicable",
    "not_applicable": "not_applicable",
}

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def normalize_status(value: str) -> str:
    clean = value.strip().lower().replace(" ", "_")
    return STATUS_ALIASES.get(clean, "unknown")


def normalize_severity(value: str) -> str:
    clean = value.strip().lower()
    return clean if clean in SEVERITY_ORDER else "medium"


def build_report(
    rows: list[dict[str, str]],
    category_col: str,
    check_col: str,
    status_col: str,
    severity_col: str,
    evidence_col: str | None,
    owner_col: str | None,
    block_severities: set[str],
    block_statuses: set[str],
) -> dict[str, Any]:
    checks = []
    status_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    category_counts: dict[str, dict[str, int]] = {}
    for row in rows:
        category = row.get(category_col, "").strip() or "uncategorized"
        check = row.get(check_col, "").strip()
        status = normalize_status(row.get(status_col, ""))
        severity = normalize_severity(row.get(severity_col, ""))
        evidence = row.get(evidence_col, "").strip() if evidence_col else ""
        owner = row.get(owner_col, "").strip() if owner_col else ""
        if not check:
            continue
        is_blocker = status in block_statuses and severity in block_severities
        item = {
            "category": category,
            "check": check,
            "status": status,
            "severity": severity,
            "evidence": evidence,
            "owner": owner,
            "is_blocker": is_blocker,
            "missing_evidence": status == "pass" and evidence_col is not None and not evidence,
        }
        checks.append(item)
        status_counts[status] = status_counts.get(status, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        category_counts.setdefault(category, {})
        category_counts[category][status] = category_counts[category].get(status, 0) + 1

    blockers = [item for item in checks if item["is_blocker"]]
    evidence_gaps = [item for item in checks if item["missing_evidence"]]
    warnings = [item for item in checks if item["status"] == "warn"]
    decision = "pass" if not blockers else "fail"
    if decision == "pass" and evidence_gaps:
        decision = "conditional_pass"

    return {
        "category_col": category_col,
        "check_col": check_col,
        "status_col": status_col,
        "severity_col": severity_col,
        "evidence_col": evidence_col,
        "owner_col": owner_col,
        "block_severities": sorted(block_severities, key=lambda item: -SEVERITY_ORDER.get(item, 0)),
        "block_statuses": sorted(block_statuses),
        "checks_total": len(checks),
        "decision": decision,
        "gate_decision": decision,
        "status_counts": status_counts,
        "severity_counts": severity_counts,
        "category_counts": category_counts,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "evidence_gap_count": len(evidence_gaps),
        "blockers": blockers,
        "warnings": warnings,
        "evidence_gaps": evidence_gaps,
        "checks": checks,
        "notes": [
            "A pass decision means no configured blocking severity/status combinations were found.",
            "Conditional pass means no blockers were found but passed checks are missing evidence fields.",
            "Waived checks should include explicit evidence and owner approval in the source checklist.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Go-Live Gate Report",
        "",
        f"- Gate decision: {report['gate_decision']}",
        f"- Checks total: {report['checks_total']}",
        f"- Blockers: {report['blocker_count']}",
        f"- Warnings: {report['warning_count']}",
        f"- Evidence gaps: {report['evidence_gap_count']}",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(report["status_counts"].items()):
        lines.append(f"- {status}: {count}")
    lines.extend(
        [
            "",
            "## Category Counts",
            "",
            "| Category | " + " | ".join(sorted(report["status_counts"])) + " |",
            "| --- | " + " | ".join("---" for _ in sorted(report["status_counts"])) + " |",
        ]
    )
    statuses = sorted(report["status_counts"])
    for category in sorted_group_keys(list(report["category_counts"])):
        counts = report["category_counts"][category]
        lines.append(
            "| " + category + " | " + " | ".join(str(counts.get(status, 0)) for status in statuses) + " |"
        )
    lines.extend(
        [
            "",
            "## Blockers",
            "",
            "| Severity | Category | Check | Status | Owner | Evidence |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in report["blockers"]:
        lines.append(
            f"| {item['severity']} | {item['category']} | {item['check']} | {item['status']} | {item['owner']} | {item['evidence']} |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize quant strategy go-live gate checklist status.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--category-col", default="category")
    parser.add_argument("--check-col", default="check")
    parser.add_argument("--status-col", default="status")
    parser.add_argument("--severity-col", default="severity")
    parser.add_argument("--evidence-col", default="evidence")
    parser.add_argument("--owner-col", default="owner")
    parser.add_argument("--block-severities", default="critical,high")
    parser.add_argument("--block-statuses", default="fail,missing,unknown")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    optional = [col for col in [args.evidence_col, args.owner_col] if col and col in header]
    require_columns(header, [args.category_col, args.check_col, args.status_col, args.severity_col])
    block_severities = {item.strip().lower() for item in args.block_severities.split(",") if item.strip()}
    block_statuses = {normalize_status(item) for item in args.block_statuses.split(",") if item.strip()}
    report = build_report(
        rows,
        args.category_col,
        args.check_col,
        args.status_col,
        args.severity_col,
        args.evidence_col if args.evidence_col in optional else None,
        args.owner_col if args.owner_col in optional else None,
        block_severities,
        block_statuses,
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
