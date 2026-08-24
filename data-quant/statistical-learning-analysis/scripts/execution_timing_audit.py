#!/usr/bin/env python3
"""Audit signal, execution, and forward-return timing alignment.

Requires the shared bundle core dependencies. This script checks whether signal timestamps, rebalance
timestamps, execution timestamps, and forward-return windows follow a tradable
sequence. It complements point_in_time_audit.py: point-in-time audit checks
whether data was knowable; this script checks whether the simulated trade and
return window are executable.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import parse_float, read_dataframe


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")


def text(row: dict[str, str], col: str | None) -> str:
    return str(row.get(col or "", "")).strip()


def present(header: list[str], col: str | None) -> bool:
    return bool(col and col in header)


def parse_timestamp(value: str) -> tuple[datetime | None, bool]:
    clean = value.strip()
    if not clean:
        return None, False
    date_only = False
    if clean.endswith("Z"):
        clean = clean[:-1] + "+00:00"
    if len(clean) == 8 and clean.isdigit():
        clean = f"{clean[:4]}-{clean[4:6]}-{clean[6:]}"
        date_only = True
    elif len(clean) <= 10 and "T" not in clean and " " not in clean:
        date_only = True
    clean = clean.replace("/", "-")
    try:
        parsed = datetime.fromisoformat(clean)
    except ValueError:
        return None, date_only
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC), date_only


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def days_between(later: datetime, earlier: datetime) -> float:
    return (later - earlier).total_seconds() / 86400


def same_calendar_day(left: datetime, right: datetime) -> bool:
    return left.date() == right.date()


def same_price(left: str | None, right: str | None) -> bool | None:
    left_value = parse_float(left)
    right_value = parse_float(right)
    if left_value is None or right_value is None:
        return None
    return abs(left_value - right_value) <= 1e-12


def finding(
    severity: str,
    check: str,
    detail: str,
    row_number: int | None = None,
    entity: str | None = None,
    signal_date: str | None = None,
    metric: Any = None,
    threshold: Any = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {"severity": severity, "check": check, "detail": detail}
    if row_number is not None:
        out["row_number"] = row_number
    if entity:
        out["entity"] = entity
    if signal_date:
        out["signal_date"] = signal_date
    if metric is not None:
        out["metric"] = metric
    if threshold is not None:
        out["threshold"] = threshold
    return out


def severity_rank(item: dict[str, Any]) -> int:
    return {"info": 0, "warning": 1, "blocker": 2}.get(str(item.get("severity", "info")), 0)


def is_evidence_gap(item: dict[str, Any]) -> bool:
    check = str(item.get("check", ""))
    return (
        check.startswith("missing_")
        or check.startswith("invalid_")
        or "without_intraday_evidence" in check
        or check.startswith("date_only_")
    )


def add_issue(
    findings: list[dict[str, Any]],
    row_issues: list[str],
    severity: str,
    check: str,
    detail: str,
    row_number: int,
    entity: str,
    signal_date: str | None,
    metric: Any = None,
    threshold: Any = None,
) -> None:
    row_issues.append(check)
    findings.append(finding(severity, check, detail, row_number, entity, signal_date, metric, threshold))


def get_timestamp(
    header: list[str],
    row: dict[str, str],
    col: str | None,
    label: str,
    row_number: int,
    entity: str,
    signal_key: str | None,
    findings: list[dict[str, Any]],
    row_issues: list[str],
    invalid_severity: str = "warning",
) -> tuple[datetime | None, bool]:
    if not present(header, col):
        return None, False
    value = text(row, col)
    if not value:
        return None, False
    parsed, date_only = parse_timestamp(value)
    if parsed is None:
        add_issue(
            findings,
            row_issues,
            invalid_severity,
            f"invalid_{label}",
            f"{label} is not parseable as an ISO-style date or timestamp.",
            row_number,
            entity,
            signal_key,
            value,
        )
    return parsed, date_only


def first_available_timestamp(
    header: list[str],
    row: dict[str, str],
    candidates: list[tuple[str, str | None]],
    row_number: int,
    entity: str,
    findings: list[dict[str, Any]],
    row_issues: list[str],
) -> tuple[str | None, datetime | None, bool]:
    for label, col in candidates:
        if present(header, col) and text(row, col):
            parsed, date_only = get_timestamp(
                header, row, col, label, row_number, entity, None, findings, row_issues, "blocker"
            )
            return label, parsed, date_only
    return None, None, False


def compare_after(
    findings: list[dict[str, Any]],
    row_issues: list[str],
    left_name: str,
    left_value: datetime | None,
    right_name: str,
    right_value: datetime | None,
    check: str,
    detail: str,
    row_number: int,
    entity: str,
    signal_key: str | None,
    severity: str = "blocker",
) -> None:
    if left_value is not None and right_value is not None and left_value > right_value:
        add_issue(
            findings,
            row_issues,
            severity,
            check,
            detail,
            row_number,
            entity,
            signal_key,
            {
                "left": left_name,
                "left_value": iso(left_value),
                "right": right_name,
                "right_value": iso(right_value),
            },
        )


def column_coverage(header: list[str], args: argparse.Namespace) -> dict[str, bool]:
    columns = {
        "date_col": args.date_col,
        "entity_col": args.entity_col,
        "decision_date_col": args.decision_date_col,
        "signal_date_col": args.signal_date_col,
        "rebalance_date_col": args.rebalance_date_col,
        "execution_date_col": args.execution_date_col,
        "return_start_col": args.return_start_col,
        "return_end_col": args.return_end_col,
        "signal_price_col": args.signal_price_col,
        "execution_price_col": args.execution_price_col,
        "return_start_price_col": args.return_start_price_col,
        "return_end_price_col": args.return_end_price_col,
        "calendar_col": args.calendar_col,
        "venue_col": args.venue_col,
    }
    return {name: present(header, col) for name, col in columns.items()}


def entity_value(header: list[str], row: dict[str, str], args: argparse.Namespace, row_number: int) -> str:
    if present(header, args.entity_col):
        value = text(row, args.entity_col)
        if value:
            return value
    return f"portfolio_{row_number}" if args.portfolio_level else f"row_{row_number}"


def check_weekend(
    findings: list[dict[str, Any]],
    row_issues: list[str],
    label: str,
    value: datetime | None,
    row_number: int,
    entity: str,
    signal_key: str | None,
    severity: str,
) -> None:
    if value is not None and value.weekday() >= 5:
        add_issue(
            findings,
            row_issues,
            severity,
            f"{label}_on_weekend",
            f"{label} falls on a weekend; confirm the market calendar and timestamp convention.",
            row_number,
            entity,
            signal_key,
            iso(value),
        )


def audit_row(
    header: list[str],
    row: dict[str, str],
    row_number: int,
    args: argparse.Namespace,
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    entity = entity_value(header, row, args, row_number)
    row_issues: list[str] = []
    signal_label, signal_dt, signal_date_only = first_available_timestamp(
        header,
        row,
        [
            ("signal_date", args.signal_date_col),
            ("decision_date", args.decision_date_col),
            ("date", args.date_col),
        ],
        row_number,
        entity,
        findings,
        row_issues,
    )
    signal_key = iso(signal_dt)
    if signal_dt is None:
        add_issue(
            findings,
            row_issues,
            "blocker",
            "missing_signal_or_decision_date",
            "No parseable signal, decision, or generic date timestamp is available.",
            row_number,
            entity,
            None,
        )

    rebalance_dt, rebalance_date_only = get_timestamp(
        header,
        row,
        args.rebalance_date_col,
        "rebalance_date",
        row_number,
        entity,
        signal_key,
        findings,
        row_issues,
    )
    execution_dt, execution_date_only = get_timestamp(
        header,
        row,
        args.execution_date_col,
        "execution_date",
        row_number,
        entity,
        signal_key,
        findings,
        row_issues,
    )
    return_start_dt, return_start_date_only = get_timestamp(
        header,
        row,
        args.return_start_col,
        "return_start_date",
        row_number,
        entity,
        signal_key,
        findings,
        row_issues,
    )
    return_end_dt, return_end_date_only = get_timestamp(
        header,
        row,
        args.return_end_col,
        "return_end_date",
        row_number,
        entity,
        signal_key,
        findings,
        row_issues,
    )
    signal_execution_same_price = (
        same_price(text(row, args.signal_price_col), text(row, args.execution_price_col))
        if present(header, args.signal_price_col) and present(header, args.execution_price_col)
        else None
    )
    execution_return_start_same_price = (
        same_price(text(row, args.execution_price_col), text(row, args.return_start_price_col))
        if present(header, args.execution_price_col) and present(header, args.return_start_price_col)
        else None
    )

    if not present(header, args.execution_date_col):
        severity = "blocker" if args.strict_missing_execution else "warning"
        add_issue(
            findings,
            row_issues,
            severity,
            "missing_execution_date_column",
            "No execution timestamp column is present.",
            row_number,
            entity,
            signal_key,
        )
    elif execution_dt is None:
        severity = "blocker" if args.strict_missing_execution else "warning"
        add_issue(
            findings,
            row_issues,
            severity,
            "missing_execution_date",
            "Execution timestamp is missing.",
            row_number,
            entity,
            signal_key,
        )
    for col, dt, check, detail in [
        (
            args.return_start_col,
            return_start_dt,
            "missing_return_start_date",
            "Forward-return start timestamp is missing.",
        ),
        (
            args.return_end_col,
            return_end_dt,
            "missing_return_end_date",
            "Forward-return end timestamp is missing.",
        ),
    ]:
        if not present(header, col) or dt is None:
            add_issue(
                findings,
                row_issues,
                "warning",
                check if present(header, col) else f"{check}_column",
                detail,
                row_number,
                entity,
                signal_key,
            )

    compare_after(
        findings,
        row_issues,
        "signal_date",
        signal_dt,
        "rebalance_date",
        rebalance_dt,
        "signal_after_rebalance",
        "Signal timestamp is after rebalance timestamp.",
        row_number,
        entity,
        signal_key,
    )
    compare_after(
        findings,
        row_issues,
        "signal_date",
        signal_dt,
        "execution_date",
        execution_dt,
        "signal_after_execution",
        "Signal timestamp is after execution timestamp.",
        row_number,
        entity,
        signal_key,
    )
    compare_after(
        findings,
        row_issues,
        "rebalance_date",
        rebalance_dt,
        "execution_date",
        execution_dt,
        "rebalance_after_execution",
        "Rebalance timestamp is after execution timestamp.",
        row_number,
        entity,
        signal_key,
    )
    compare_after(
        findings,
        row_issues,
        "return_start_date",
        return_start_dt,
        "return_end_date",
        return_end_dt,
        "return_start_after_return_end",
        "Forward-return start is after return end.",
        row_number,
        entity,
        signal_key,
    )

    if return_start_dt is not None and return_end_dt is not None and return_start_dt == return_end_dt:
        add_issue(
            findings,
            row_issues,
            "blocker",
            "nonpositive_return_window",
            "Forward-return start and end timestamps are identical.",
            row_number,
            entity,
            signal_key,
            iso(return_start_dt),
        )
    if signal_dt is not None and return_start_dt is not None and return_start_dt < signal_dt:
        add_issue(
            findings,
            row_issues,
            "blocker",
            "return_starts_before_signal",
            "Forward-return window starts before the signal timestamp.",
            row_number,
            entity,
            signal_key,
            {"signal_date": iso(signal_dt), "return_start_date": iso(return_start_dt)},
        )
    if execution_dt is not None and return_start_dt is not None and return_start_dt < execution_dt:
        add_issue(
            findings,
            row_issues,
            "blocker",
            "return_starts_before_execution",
            "Forward-return window starts before execution timestamp.",
            row_number,
            entity,
            signal_key,
            {"execution_date": iso(execution_dt), "return_start_date": iso(return_start_dt)},
        )

    if (
        signal_dt is not None
        and execution_dt is not None
        and same_calendar_day(signal_dt, execution_dt)
        and (signal_date_only or execution_date_only)
    ):
        add_issue(
            findings,
            row_issues,
            args.same_day_execution_severity,
            "same_day_signal_execution_without_intraday_evidence",
            "Signal and execution are on the same date without intraday timestamp evidence.",
            row_number,
            entity,
            signal_key,
        )
        if signal_execution_same_price is True:
            add_issue(
                findings,
                row_issues,
                args.same_day_execution_severity,
                "same_day_signal_execution_same_price",
                "Signal and execution use the same date and same price; this often indicates same-close execution bias.",
                row_number,
                entity,
                signal_key,
            )
    if (
        signal_dt is not None
        and return_start_dt is not None
        and same_calendar_day(signal_dt, return_start_dt)
        and (signal_date_only or return_start_date_only)
    ):
        add_issue(
            findings,
            row_issues,
            "warning",
            "same_day_signal_return_start",
            "Signal and forward-return start are on the same date; confirm the execution price and return-window convention.",
            row_number,
            entity,
            signal_key,
        )
    if (
        execution_dt is not None
        and return_start_dt is not None
        and same_calendar_day(execution_dt, return_start_dt)
        and (execution_date_only or return_start_date_only)
    ):
        if execution_return_start_same_price is True:
            pass
        elif execution_return_start_same_price is False:
            add_issue(
                findings,
                row_issues,
                "warning",
                "execution_return_start_price_mismatch",
                "Execution and return-start dates match but prices differ; confirm the return window starts after the actual execution price.",
                row_number,
                entity,
                signal_key,
            )
        else:
            add_issue(
                findings,
                row_issues,
                "warning",
                "date_only_execution_return_start",
                "Execution and return-start dates match without intraday price convention evidence.",
                row_number,
                entity,
                signal_key,
            )

    if signal_dt is not None and execution_dt is not None:
        lag_days = days_between(execution_dt, signal_dt)
        if lag_days < args.min_signal_to_execution_lag_days:
            add_issue(
                findings,
                row_issues,
                args.signal_to_execution_lag_severity,
                "signal_to_execution_lag_too_short",
                "Signal-to-execution lag is shorter than the required minimum.",
                row_number,
                entity,
                signal_key,
                lag_days,
                args.min_signal_to_execution_lag_days,
            )
        if (
            args.max_signal_to_execution_lag_days is not None
            and lag_days > args.max_signal_to_execution_lag_days
        ):
            add_issue(
                findings,
                row_issues,
                "warning",
                "signal_to_execution_lag_too_long",
                "Signal may be stale before execution.",
                row_number,
                entity,
                signal_key,
                lag_days,
                args.max_signal_to_execution_lag_days,
            )
    if return_start_dt is not None and return_end_dt is not None:
        horizon_days = days_between(return_end_dt, return_start_dt)
        if horizon_days < args.min_return_horizon_days:
            add_issue(
                findings,
                row_issues,
                args.return_horizon_severity,
                "return_horizon_too_short",
                "Forward-return horizon is shorter than the required minimum.",
                row_number,
                entity,
                signal_key,
                horizon_days,
                args.min_return_horizon_days,
            )
        if (
            args.expected_horizon_days is not None
            and abs(horizon_days - args.expected_horizon_days) > args.horizon_tolerance_days
        ):
            add_issue(
                findings,
                row_issues,
                "warning",
                "unexpected_return_horizon",
                "Forward-return horizon differs from the expected horizon.",
                row_number,
                entity,
                signal_key,
                horizon_days,
                args.expected_horizon_days,
            )

    for label, value in [
        ("signal_date", signal_dt),
        ("rebalance_date", rebalance_dt),
        ("execution_date", execution_dt),
        ("return_start_date", return_start_dt),
        ("return_end_date", return_end_dt),
    ]:
        check_weekend(
            findings, row_issues, label, value, row_number, entity, signal_key, args.weekend_severity
        )

    return {
        "row_number": row_number,
        "entity": entity,
        "signal_source": signal_label,
        "signal_date": signal_key,
        "rebalance_date": iso(rebalance_dt),
        "execution_date": iso(execution_dt),
        "return_start_date": iso(return_start_dt),
        "return_end_date": iso(return_end_dt),
        "calendar": text(row, args.calendar_col) if present(header, args.calendar_col) else "",
        "venue": text(row, args.venue_col) if present(header, args.venue_col) else "",
        "issue_count": len(row_issues),
        "issues": row_issues,
    }


def duplicate_findings(row_checks: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[int]] = {}
    for item in row_checks:
        entity = str(item.get("entity") or "")
        signal = str(item.get("signal_date") or "")
        if not entity or not signal:
            continue
        groups.setdefault((entity, signal), []).append(int(item["row_number"]))
    out = []
    for (entity, signal), row_numbers in groups.items():
        if len(row_numbers) > 1:
            out.append(
                finding(
                    args.duplicate_severity,
                    "duplicate_entity_signal_date",
                    "Multiple rows share the same entity and signal timestamp.",
                    row_numbers[0],
                    entity,
                    signal,
                    {"duplicate_rows": row_numbers[:20], "duplicate_count": len(row_numbers)},
                    1,
                )
            )
    return out


def build_report(header: list[str], rows: list[dict[str, str]], args: argparse.Namespace) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    row_checks = [
        audit_row(header, row, row_number, args, findings) for row_number, row in enumerate(rows, start=1)
    ]
    duplicate_rows = duplicate_findings(row_checks, args)
    findings.extend(duplicate_rows)

    issue_counts: dict[str, int] = {}
    for item in findings:
        check = str(item["check"])
        issue_counts[check] = issue_counts.get(check, 0) + 1
    blockers = [item for item in findings if item["severity"] == "blocker"]
    warnings = [item for item in findings if item["severity"] == "warning"]
    evidence_gaps = [item for item in findings if is_evidence_gap(item)]
    problem_rows = [item for item in row_checks if item["issues"]]
    entities = {str(item.get("entity", "")) for item in row_checks if item.get("entity")}
    signal_dates = {str(item.get("signal_date", "")) for item in row_checks if item.get("signal_date")}
    ranked = sorted(
        findings,
        key=lambda item: (severity_rank(item), item["check"], str(item.get("row_number", ""))),
        reverse=True,
    )
    decision = "fail" if blockers else ("review" if warnings else "pass")
    return {
        "audit_type": "execution_timing_audit",
        "audit_decision": decision,
        "row_count": len(rows),
        "checked_row_count": len(row_checks),
        "problem_row_count": len(problem_rows),
        "entity_count": len(entities),
        "date_count": len(signal_dates),
        "duplicate_key_count": len(duplicate_rows),
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "evidence_gap_count": len(evidence_gaps),
        "finding_count": len(findings),
        "issue_counts": dict(sorted(issue_counts.items())),
        "column_coverage": column_coverage(header, args),
        "thresholds": {
            "min_signal_to_execution_lag_days": args.min_signal_to_execution_lag_days,
            "max_signal_to_execution_lag_days": args.max_signal_to_execution_lag_days,
            "min_return_horizon_days": args.min_return_horizon_days,
            "expected_horizon_days": args.expected_horizon_days,
            "horizon_tolerance_days": args.horizon_tolerance_days,
            "same_day_execution_severity": args.same_day_execution_severity,
            "weekend_severity": args.weekend_severity,
            "duplicate_severity": args.duplicate_severity,
            "strict_missing_execution": args.strict_missing_execution,
        },
        "top_findings": ranked[: args.finding_limit],
        "problem_rows": sorted(
            problem_rows,
            key=lambda item: (-int(item["issue_count"]), str(item["entity"]), str(item["signal_date"])),
        )[: args.finding_limit],
        "notes": [
            "This audit checks trading and return-window timing; it does not prove source data was point-in-time.",
            "Date-only same-day signal and execution rows are treated as timing evidence gaps unless configured as blockers.",
            "Evidence gaps include missing or invalid timing fields and date-only timing rows without intraday convention evidence.",
            "Run this before IC, quantile, regression, long/short backtest, portfolio construction, or paper-trading review.",
        ],
    }


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Execution Timing Audit",
        "",
        f"- Decision: {report['audit_decision']}",
        f"- Rows: {report['row_count']}",
        f"- Problem rows: {report['problem_row_count']}",
        f"- Entities: {report['entity_count']}",
        f"- Signal dates: {report['date_count']}",
        f"- Blockers: {report['blocker_count']}",
        f"- Warnings: {report['warning_count']}",
        f"- Evidence gaps: {report['evidence_gap_count']}",
        "",
        "## Issue Counts",
        "",
    ]
    if report["issue_counts"]:
        for issue, count in report["issue_counts"].items():
            lines.append(f"- {issue}: {count}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Top Findings",
            "",
            "| Severity | Check | Row | Entity | Signal date | Metric | Threshold | Detail |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if report["top_findings"]:
        for item in report["top_findings"]:
            lines.append(
                f"| {md_escape(item['severity'])} | {md_escape(item['check'])} | {md_escape(item.get('row_number', ''))} | {md_escape(item.get('entity', ''))} | {md_escape(item.get('signal_date', ''))} | {md_escape(item.get('metric', ''))} | {md_escape(item.get('threshold', ''))} | {md_escape(item['detail'])} |"
            )
    else:
        lines.append(
            "| info | no_findings |  |  |  |  |  | No execution-timing findings from supplied panel. |"
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit signal, execution, and forward-return timing alignment."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", default="date", help="Generic signal or decision date fallback column.")
    parser.add_argument("--entity-col", default="asset", help="Entity/asset identifier column.")
    parser.add_argument(
        "--portfolio-level",
        action="store_true",
        help="Treat rows as portfolio-level if entity column is absent.",
    )
    parser.add_argument("--decision-date-col", default="as_of_date")
    parser.add_argument("--signal-date-col", default="signal_date")
    parser.add_argument("--rebalance-date-col", default="rebalance_date")
    parser.add_argument("--execution-date-col", default="execution_date")
    parser.add_argument("--return-start-col", default="return_start_date")
    parser.add_argument("--return-end-col", default="return_end_date")
    parser.add_argument("--signal-price-col", default="signal_price")
    parser.add_argument("--execution-price-col", default="execution_price")
    parser.add_argument("--return-start-price-col", default="return_start_price")
    parser.add_argument("--return-end-price-col", default="return_end_price")
    parser.add_argument("--calendar-col", default="calendar")
    parser.add_argument("--venue-col", default="venue")
    parser.add_argument("--min-signal-to-execution-lag-days", type=float, default=0.0)
    parser.add_argument("--max-signal-to-execution-lag-days", type=float)
    parser.add_argument(
        "--signal-to-execution-lag-severity", choices=["warning", "blocker"], default="blocker"
    )
    parser.add_argument("--min-return-horizon-days", type=float, default=0.0)
    parser.add_argument("--return-horizon-severity", choices=["warning", "blocker"], default="blocker")
    parser.add_argument("--expected-horizon-days", type=float)
    parser.add_argument("--horizon-tolerance-days", type=float, default=0.0)
    parser.add_argument("--same-day-execution-severity", choices=["warning", "blocker"], default="warning")
    parser.add_argument("--weekend-severity", choices=["info", "warning", "blocker"], default="warning")
    parser.add_argument("--duplicate-severity", choices=["warning", "blocker"], default="warning")
    parser.add_argument(
        "--strict-missing-execution",
        action="store_true",
        help="Treat missing execution timestamps as blockers.",
    )
    parser.add_argument("--finding-limit", type=int, default=30)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.min_signal_to_execution_lag_days < 0 or args.min_return_horizon_days < 0:
        raise SystemExit(
            "--min-signal-to-execution-lag-days and --min-return-horizon-days must be non-negative."
        )
    if (
        args.max_signal_to_execution_lag_days is not None
        and args.max_signal_to_execution_lag_days < args.min_signal_to_execution_lag_days
    ):
        raise SystemExit("--max-signal-to-execution-lag-days must be >= --min-signal-to-execution-lag-days.")
    if args.expected_horizon_days is not None and args.expected_horizon_days < 0:
        raise SystemExit("--expected-horizon-days must be non-negative.")
    if args.horizon_tolerance_days < 0:
        raise SystemExit("--horizon-tolerance-days must be non-negative.")
    if args.finding_limit <= 0:
        raise SystemExit("--finding-limit must be positive.")

    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    if not any(present(header, col) for col in [args.signal_date_col, args.decision_date_col, args.date_col]):
        raise SystemExit("At least one signal, decision, or generic date column must be present.")
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
