#!/usr/bin/env python3
"""Audit a quant model risk register for governance and review gaps.

Requires the shared bundle core dependencies. This script checks whether research models, alpha
signals, portfolio optimizers, execution models, or live strategies have
owners, risk tiers, validation status, approvals, review dates, monitoring,
rollback controls, and version evidence before promotion or scaling.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import parse_float, read_dataframe


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")


LIVE_STATUSES = {"limited_live", "live", "scaled_live", "production", "active", "trading"}
PRELIVE_STATUSES = {"research", "candidate", "paper", "paper_trading", "review"}
INACTIVE_STATUSES = {"retired", "disabled", "inactive", "closed"}
APPROVED_VALUES = {
    "approved",
    "pass",
    "passed",
    "signed_off",
    "complete",
    "completed",
    "yes",
    "y",
    "true",
    "1",
}
FAILED_VALUES = {"failed", "fail", "rejected", "blocked", "no", "n", "false", "0"}
VALIDATION_GOOD = {"validated", "approved", "pass", "passed", "complete", "completed"}
VALIDATION_BAD = {"failed", "fail", "rejected", "blocked"}
RISK_RANK = {
    "low": 1,
    "medium": 2,
    "med": 2,
    "moderate": 2,
    "high": 3,
    "critical": 4,
    "tier_1": 4,
    "tier_2": 3,
    "tier_3": 2,
    "tier_4": 1,
}


def normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def text(row: dict[str, str], col: str | None) -> str:
    return str(row.get(col or "", "")).strip()


def present(header: list[str], col: str | None) -> bool:
    return bool(col and col in header)


def parse_date(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def risk_rank(value: str) -> int:
    norm = normalize(value)
    if norm in RISK_RANK:
        return RISK_RANK[norm]
    numeric = parse_float(value)
    if numeric is not None:
        if numeric <= 1:
            return 4
        if numeric <= 2:
            return 3
        if numeric <= 3:
            return 2
        return 1
    return 0


def model_id(row: dict[str, str], id_col: str | None, index: int) -> str:
    value = text(row, id_col)
    if value:
        return value
    name = text(row, "model_name")
    return name or str(index)


def is_live(status: str) -> bool:
    return normalize(status) in LIVE_STATUSES


def is_active(status: str) -> bool:
    norm = normalize(status)
    return norm not in INACTIVE_STATUSES


def is_high_risk(tier: str) -> bool:
    return risk_rank(tier) >= 3


def is_approved(value: str) -> bool:
    return normalize(value) in APPROVED_VALUES


def is_failed(value: str) -> bool:
    return normalize(value) in FAILED_VALUES


def validation_ok(value: str) -> bool:
    return normalize(value) in VALIDATION_GOOD


def validation_failed(value: str) -> bool:
    return normalize(value) in VALIDATION_BAD


def finding(
    severity: str,
    check: str,
    detail: str,
    model: str | None = None,
    metric: Any = None,
    threshold: Any = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {"severity": severity, "check": check, "detail": detail}
    if model:
        out["model_id"] = model
    if metric is not None:
        out["metric"] = metric
    if threshold is not None:
        out["threshold"] = threshold
    return out


def severity_rank(item: dict[str, Any]) -> int:
    return {"info": 0, "warning": 1, "blocker": 2}.get(str(item.get("severity", "info")), 0)


def check_columns(header: list[str], args: argparse.Namespace) -> list[dict[str, Any]]:
    cols = {
        "model_id_col": args.model_id_col,
        "status_col": args.status_col,
        "risk_tier_col": args.risk_tier_col,
        "owner_col": args.owner_col,
        "validator_col": args.validator_col,
        "validation_status_col": args.validation_status_col,
        "approval_status_col": args.approval_status_col,
        "last_review_col": args.last_review_col,
        "next_review_due_col": args.next_review_due_col,
        "monitoring_col": args.monitoring_col,
        "rollback_col": args.rollback_col,
        "kill_switch_col": args.kill_switch_col,
        "data_version_col": args.data_version_col,
        "code_version_col": args.code_version_col,
        "evidence_col": args.evidence_col,
    }
    missing = [name for name, col in cols.items() if not present(header, col)]
    if missing:
        return [
            finding(
                "warning",
                "missing_register_columns",
                "Model risk register is missing expected columns.",
                metric=missing,
            )
        ]
    return []


def evaluate_row(
    row: dict[str, str], index: int, args: argparse.Namespace, as_of: date
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    mid = model_id(row, args.model_id_col, index)
    status = text(row, args.status_col)
    tier = text(row, args.risk_tier_col)
    rank = risk_rank(tier)
    live = is_live(status)
    active = is_active(status)
    high_risk = rank >= 3
    row_findings: list[dict[str, Any]] = []

    if active and not text(row, args.owner_col):
        row_findings.append(
            finding(
                "blocker" if live or high_risk else "warning",
                "missing_owner",
                "Active model has no owner.",
                mid,
            )
        )
    if active and rank == 0:
        row_findings.append(
            finding(
                "blocker" if live else "warning",
                "missing_or_invalid_risk_tier",
                "Model has no recognized risk tier.",
                mid,
                tier or None,
            )
        )

    validator = text(row, args.validator_col)
    validation_status = text(row, args.validation_status_col)
    if active and (live or high_risk):
        if not validator:
            row_findings.append(
                finding(
                    "blocker",
                    "missing_independent_validator",
                    "Live or high-risk model has no independent validator.",
                    mid,
                )
            )
        if not validation_status:
            row_findings.append(
                finding(
                    "blocker",
                    "missing_validation_status",
                    "Live or high-risk model has no validation status.",
                    mid,
                )
            )
        elif validation_failed(validation_status) or not validation_ok(validation_status):
            row_findings.append(
                finding(
                    "blocker",
                    "validation_not_approved",
                    "Live or high-risk model validation is not approved.",
                    mid,
                    validation_status,
                )
            )
    elif active and validation_failed(validation_status):
        row_findings.append(
            finding(
                "warning",
                "validation_failed",
                "Model validation is failed or blocked.",
                mid,
                validation_status,
            )
        )

    approval_status = text(row, args.approval_status_col)
    if live:
        if not approval_status:
            row_findings.append(
                finding("blocker", "missing_approval", "Live model has no approval status.", mid)
            )
        elif not is_approved(approval_status):
            row_findings.append(
                finding(
                    "blocker",
                    "approval_not_complete",
                    "Live model is not approved for current status.",
                    mid,
                    approval_status,
                )
            )

    last_review_text = text(row, args.last_review_col)
    next_due_text = text(row, args.next_review_due_col)
    last_review = parse_date(last_review_text)
    next_due = parse_date(next_due_text)
    max_age = args.high_risk_max_review_age_days if high_risk else args.max_review_age_days
    if active:
        if not last_review:
            row_findings.append(
                finding(
                    "warning" if not live else "blocker",
                    "missing_last_review_date",
                    "Active model has no parseable last review date.",
                    mid,
                    last_review_text or None,
                )
            )
        else:
            age = (as_of - last_review).days
            if age > max_age:
                row_findings.append(
                    finding(
                        "blocker" if live or high_risk else "warning",
                        "stale_model_review",
                        "Model review is older than allowed for its risk tier.",
                        mid,
                        age,
                        max_age,
                    )
                )
        if not next_due:
            row_findings.append(
                finding(
                    "warning" if not live else "blocker",
                    "missing_next_review_due",
                    "Active model has no parseable next review due date.",
                    mid,
                    next_due_text or None,
                )
            )
        else:
            days_until_due = (next_due - as_of).days
            if days_until_due < 0:
                row_findings.append(
                    finding(
                        "blocker" if live or high_risk else "warning",
                        "review_overdue",
                        "Model review due date has passed.",
                        mid,
                        days_until_due,
                        0,
                    )
                )
            elif days_until_due <= args.warn_due_within_days:
                row_findings.append(
                    finding(
                        "warning",
                        "review_due_soon",
                        "Model review is due soon.",
                        mid,
                        days_until_due,
                        args.warn_due_within_days,
                    )
                )

    for col, check, detail in [
        (args.monitoring_col, "missing_monitoring_plan", "Live model has no monitoring plan."),
        (args.rollback_col, "missing_rollback_plan", "Live model has no rollback plan."),
        (
            args.kill_switch_col,
            "missing_kill_switch",
            "Live model has no kill-switch or manual override evidence.",
        ),
    ]:
        if live and not text(row, col):
            row_findings.append(finding("blocker", check, detail, mid))

    for col, check, detail in [
        (args.data_version_col, "missing_data_version", "Active model has no data-version evidence."),
        (args.code_version_col, "missing_code_version", "Active model has no code-version evidence."),
        (
            args.evidence_col,
            "missing_evidence_link",
            "Active model has no evidence link or artifact reference.",
        ),
    ]:
        if active and not text(row, col):
            row_findings.append(finding("warning", check, detail, mid))

    issue_count = parse_float(text(row, args.issue_count_col))
    if issue_count is not None and issue_count > args.max_open_issues:
        row_findings.append(
            finding(
                "blocker" if live or high_risk else "warning",
                "open_issue_count",
                "Open model-risk issues exceed threshold.",
                mid,
                issue_count,
                args.max_open_issues,
            )
        )

    limitations = text(row, args.limitations_col)
    waiver = text(row, args.waiver_col)
    if active and limitations and not waiver:
        row_findings.append(
            finding(
                "warning",
                "unwaived_limitations",
                "Model limitations are recorded without waiver or mitigation evidence.",
                mid,
            )
        )

    summary = {
        "model_id": mid,
        "status": normalize(status) or "missing",
        "risk_tier": tier or "missing",
        "risk_rank": rank,
        "is_live": live,
        "is_active": active,
        "finding_count": len(row_findings),
        "blocker_count": sum(1 for item in row_findings if item["severity"] == "blocker"),
        "warning_count": sum(1 for item in row_findings if item["severity"] == "warning"),
    }
    return summary, row_findings


def build_report(header: list[str], rows: list[dict[str, str]], args: argparse.Namespace) -> dict[str, Any]:
    as_of = parse_date(args.as_of)
    if as_of is None:
        raise SystemExit("--as-of must be YYYY-MM-DD, YYYY/MM/DD, or YYYYMMDD.")
    findings = check_columns(header, args)
    models = []
    for idx, row in enumerate(rows, start=1):
        summary, row_findings = evaluate_row(row, idx, args, as_of)
        models.append(summary)
        findings.extend(row_findings)

    by_status: dict[str, int] = {}
    by_risk_tier: dict[str, int] = {}
    for item in models:
        by_status[item["status"]] = by_status.get(item["status"], 0) + 1
        by_risk_tier[item["risk_tier"]] = by_risk_tier.get(item["risk_tier"], 0) + 1

    blockers = [item for item in findings if item["severity"] == "blocker"]
    warnings = [item for item in findings if item["severity"] == "warning"]
    ranked = sorted(
        findings,
        key=lambda item: (severity_rank(item), item.get("check", ""), item.get("model_id", "")),
        reverse=True,
    )
    live_models = [item for item in models if item["is_live"]]
    high_risk_models = [item for item in models if item["risk_rank"] >= 3]
    register_decision = "fail" if blockers else ("review" if warnings else "pass")

    return {
        "report_type": "model_risk_register",
        "register_decision": register_decision,
        "as_of": str(as_of),
        "model_count": len(models),
        "live_model_count": len(live_models),
        "high_risk_model_count": len(high_risk_models),
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "finding_count": len(findings),
        "by_status": dict(sorted(by_status.items())),
        "by_risk_tier": dict(sorted(by_risk_tier.items())),
        "thresholds": {
            "max_review_age_days": args.max_review_age_days,
            "high_risk_max_review_age_days": args.high_risk_max_review_age_days,
            "warn_due_within_days": args.warn_due_within_days,
            "max_open_issues": args.max_open_issues,
        },
        "top_findings": ranked[: args.finding_limit],
        "models": sorted(
            models,
            key=lambda item: (
                item["blocker_count"],
                item["warning_count"],
                item["risk_rank"],
                item["model_id"],
            ),
            reverse=True,
        ),
        "notes": [
            "This report audits model-risk governance evidence; it does not validate alpha quality or production PnL.",
            "Live and high-risk models should have owners, independent validation, approval, review cadence, monitoring, rollback controls, and version evidence.",
            "A pass here does not replace alpha research, portfolio construction, execution, or go-live diagnostics.",
        ],
    }


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Model Risk Register Report",
        "",
        f"- Decision: {report['register_decision']}",
        f"- As of: {report['as_of']}",
        f"- Models: {report['model_count']}",
        f"- Live models: {report['live_model_count']}",
        f"- High-risk models: {report['high_risk_model_count']}",
        f"- Blockers: {report['blocker_count']}",
        f"- Warnings: {report['warning_count']}",
        "",
        "## Status Summary",
        "",
        "| Status | Count |",
        "| --- | --- |",
    ]
    for status, count in report["by_status"].items():
        lines.append(f"| {md_escape(status)} | {count} |")

    lines.extend(["", "## Risk Tier Summary", "", "| Risk tier | Count |", "| --- | --- |"])
    for tier, count in report["by_risk_tier"].items():
        lines.append(f"| {md_escape(tier)} | {count} |")

    lines.extend(
        [
            "",
            "## Top Findings",
            "",
            "| Severity | Check | Model | Metric | Threshold | Detail |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    if report["top_findings"]:
        for item in report["top_findings"]:
            lines.append(
                f"| {md_escape(item['severity'])} | {md_escape(item['check'])} | {md_escape(item.get('model_id', ''))} | {md_escape(item.get('metric', ''))} | {md_escape(item.get('threshold', ''))} | {md_escape(item['detail'])} |"
            )
    else:
        lines.append("| info | no_findings |  |  |  | No model-risk register findings from supplied data. |")

    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit a quant model risk register for governance and review gaps."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--as-of", default=str(date.today()))
    parser.add_argument("--model-id-col", default="model_id")
    parser.add_argument("--status-col", default="status")
    parser.add_argument("--risk-tier-col", default="risk_tier")
    parser.add_argument("--owner-col", default="owner")
    parser.add_argument("--validator-col", default="validator")
    parser.add_argument("--validation-status-col", default="validation_status")
    parser.add_argument("--approval-status-col", default="approval_status")
    parser.add_argument("--last-review-col", default="last_review_date")
    parser.add_argument("--next-review-due-col", default="next_review_due")
    parser.add_argument("--monitoring-col", default="monitoring")
    parser.add_argument("--rollback-col", default="rollback_plan")
    parser.add_argument("--kill-switch-col", default="kill_switch")
    parser.add_argument("--data-version-col", default="data_version")
    parser.add_argument("--code-version-col", default="code_version")
    parser.add_argument("--evidence-col", default="evidence")
    parser.add_argument("--limitations-col", default="limitations")
    parser.add_argument("--waiver-col", default="waiver")
    parser.add_argument("--issue-count-col", default="open_issue_count")
    parser.add_argument("--max-review-age-days", type=int, default=365)
    parser.add_argument("--high-risk-max-review-age-days", type=int, default=180)
    parser.add_argument("--warn-due-within-days", type=int, default=30)
    parser.add_argument("--max-open-issues", type=float, default=0.0)
    parser.add_argument("--finding-limit", type=int, default=30)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.max_review_age_days < 1 or args.high_risk_max_review_age_days < 1:
        raise SystemExit("--max-review-age-days and --high-risk-max-review-age-days must be positive.")
    if args.warn_due_within_days < 0 or args.max_open_issues < 0:
        raise SystemExit("--warn-due-within-days and --max-open-issues must be non-negative.")
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
