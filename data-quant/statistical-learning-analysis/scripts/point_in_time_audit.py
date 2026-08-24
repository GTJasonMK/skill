#!/usr/bin/env python3
"""Audit point-in-time data alignment and look-ahead leakage risks.

Requires the shared bundle core dependencies. This script checks whether a date-entity signal panel
uses source, availability, universe, revision, and execution timestamps that
were observable at the decision timestamp. Run it before IC, quantile tests,
cross-sectional regressions, or backtests.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from quant_utils import read_dataframe, require_columns


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")


TRUE_VALUES = {"1", "true", "t", "yes", "y", "in", "included", "eligible", "active"}
FALSE_VALUES = {"0", "false", "f", "no", "n", "out", "excluded", "ineligible", "inactive"}


def text(row: dict[str, str], col: str | None) -> str:
    return str(row.get(col or "", "")).strip()


def present(header: list[str], col: str | None) -> bool:
    return bool(col and col in header)


def normalize_bool(value: str) -> bool | None:
    clean = value.strip().lower().replace(" ", "_").replace("-", "_")
    if clean in TRUE_VALUES:
        return True
    if clean in FALSE_VALUES:
        return False
    if clean == "":
        return None
    return None


def parse_timestamp(value: str) -> datetime | None:
    clean = value.strip()
    if not clean:
        return None
    if clean.endswith("Z"):
        clean = clean[:-1] + "+00:00"
    if len(clean) == 8 and clean.isdigit():
        clean = f"{clean[:4]}-{clean[4:6]}-{clean[6:]}"
    clean = clean.replace("/", "-")
    try:
        parsed = datetime.fromisoformat(clean)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def days_between(later: datetime, earlier: datetime) -> float:
    return (later - earlier).total_seconds() / 86400


def finding(
    severity: str,
    check: str,
    detail: str,
    row_number: int | None = None,
    entity: str | None = None,
    as_of: str | None = None,
    metric: Any = None,
    threshold: Any = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {"severity": severity, "check": check, "detail": detail}
    if row_number is not None:
        out["row_number"] = row_number
    if entity:
        out["entity"] = entity
    if as_of:
        out["as_of"] = as_of
    if metric is not None:
        out["metric"] = metric
    if threshold is not None:
        out["threshold"] = threshold
    return out


def severity_rank(item: dict[str, Any]) -> int:
    return {"info": 0, "warning": 1, "blocker": 2}.get(str(item.get("severity", "info")), 0)


def add_issue(
    findings: list[dict[str, Any]],
    row_issues: list[str],
    severity: str,
    check: str,
    detail: str,
    row_number: int,
    entity: str,
    as_of: str | None,
    metric: Any = None,
    threshold: Any = None,
) -> None:
    row_issues.append(check)
    findings.append(finding(severity, check, detail, row_number, entity, as_of, metric, threshold))


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
    as_of: str | None,
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
            as_of,
            {
                "left": left_name,
                "left_value": iso(left_value),
                "right": right_name,
                "right_value": iso(right_value),
            },
        )


def check_optional_date(
    header: list[str],
    row: dict[str, str],
    col: str | None,
    label: str,
    row_number: int,
    entity: str,
    as_of: str | None,
    findings: list[dict[str, Any]],
    row_issues: list[str],
    invalid_severity: str = "warning",
) -> datetime | None:
    if not present(header, col):
        return None
    value = text(row, col)
    if not value:
        return None
    parsed = parse_timestamp(value)
    if parsed is None:
        add_issue(
            findings,
            row_issues,
            invalid_severity,
            f"invalid_{label}",
            f"{label} is not parseable as an ISO-style date or timestamp.",
            row_number,
            entity,
            as_of,
            value,
        )
    return parsed


def column_coverage(header: list[str], args: argparse.Namespace) -> dict[str, bool]:
    columns = {
        "as_of_col": args.as_of_col,
        "entity_col": args.entity_col,
        "available_date_col": args.available_date_col,
        "data_date_col": args.data_date_col,
        "period_end_col": args.period_end_col,
        "signal_date_col": args.signal_date_col,
        "rebalance_date_col": args.rebalance_date_col,
        "execution_date_col": args.execution_date_col,
        "universe_date_col": args.universe_date_col,
        "in_universe_col": args.in_universe_col,
        "revision_timestamp_col": args.revision_timestamp_col,
        "vendor_timestamp_col": args.vendor_timestamp_col,
        "source_col": args.source_col,
    }
    return {name: present(header, col) for name, col in columns.items()}


def audit_row(
    header: list[str],
    row: dict[str, str],
    row_number: int,
    args: argparse.Namespace,
    findings: list[dict[str, Any]],
) -> dict[str, Any] | None:
    entity = text(row, args.entity_col)
    as_of_raw = text(row, args.as_of_col)
    row_issues: list[str] = []
    as_of_dt = parse_timestamp(as_of_raw)
    if not entity:
        entity = f"row_{row_number}"
        add_issue(
            findings,
            row_issues,
            "blocker",
            "missing_entity",
            "Required entity identifier is missing.",
            row_number,
            entity,
            None,
        )
    if as_of_dt is None:
        add_issue(
            findings,
            row_issues,
            "blocker",
            "invalid_as_of_date",
            "Decision/as-of date is missing or invalid.",
            row_number,
            entity,
            as_of_raw or None,
            as_of_raw or None,
        )
        return {
            "row_number": row_number,
            "entity": entity,
            "as_of": as_of_raw or None,
            "source": text(row, args.source_col) if present(header, args.source_col) else "",
            "issue_count": len(row_issues),
            "issues": row_issues,
        }
    as_of_key = iso(as_of_dt)

    available_dt = check_optional_date(
        header,
        row,
        args.available_date_col,
        "available_date",
        row_number,
        entity,
        as_of_key,
        findings,
        row_issues,
        "blocker",
    )
    data_dt = check_optional_date(
        header,
        row,
        args.data_date_col,
        "data_date",
        row_number,
        entity,
        as_of_key,
        findings,
        row_issues,
        "blocker",
    )
    period_end_dt = check_optional_date(
        header,
        row,
        args.period_end_col,
        "period_end_date",
        row_number,
        entity,
        as_of_key,
        findings,
        row_issues,
        "warning",
    )
    signal_dt = check_optional_date(
        header,
        row,
        args.signal_date_col,
        "signal_date",
        row_number,
        entity,
        as_of_key,
        findings,
        row_issues,
        "warning",
    )
    rebalance_dt = check_optional_date(
        header,
        row,
        args.rebalance_date_col,
        "rebalance_date",
        row_number,
        entity,
        as_of_key,
        findings,
        row_issues,
        "warning",
    )
    execution_dt = check_optional_date(
        header,
        row,
        args.execution_date_col,
        "execution_date",
        row_number,
        entity,
        as_of_key,
        findings,
        row_issues,
        "warning",
    )
    universe_dt = check_optional_date(
        header,
        row,
        args.universe_date_col,
        "universe_date",
        row_number,
        entity,
        as_of_key,
        findings,
        row_issues,
        "warning",
    )
    revision_dt = check_optional_date(
        header,
        row,
        args.revision_timestamp_col,
        "revision_timestamp",
        row_number,
        entity,
        as_of_key,
        findings,
        row_issues,
        "warning",
    )
    vendor_dt = check_optional_date(
        header,
        row,
        args.vendor_timestamp_col,
        "vendor_timestamp",
        row_number,
        entity,
        as_of_key,
        findings,
        row_issues,
        "warning",
    )

    if present(header, args.available_date_col) and available_dt is None:
        severity = "blocker" if args.strict_missing_availability else "warning"
        add_issue(
            findings,
            row_issues,
            severity,
            "missing_available_date",
            "Availability/release timestamp is missing.",
            row_number,
            entity,
            as_of_key,
        )
    if not present(header, args.available_date_col):
        severity = "blocker" if args.strict_missing_availability else "warning"
        add_issue(
            findings,
            row_issues,
            severity,
            "missing_available_date_column",
            "No availability/release timestamp column is present.",
            row_number,
            entity,
            as_of_key,
        )
    if present(header, args.data_date_col) and data_dt is None:
        add_issue(
            findings,
            row_issues,
            "warning",
            "missing_data_date",
            "Source data date is missing.",
            row_number,
            entity,
            as_of_key,
        )

    compare_after(
        findings,
        row_issues,
        "available_date",
        available_dt,
        "as_of",
        as_of_dt,
        "available_date_after_as_of",
        "Data availability is after the decision date.",
        row_number,
        entity,
        as_of_key,
    )
    compare_after(
        findings,
        row_issues,
        "data_date",
        data_dt,
        "as_of",
        as_of_dt,
        "data_date_after_as_of",
        "Source data date is after the decision date.",
        row_number,
        entity,
        as_of_key,
    )
    compare_after(
        findings,
        row_issues,
        "period_end_date",
        period_end_dt,
        "as_of",
        as_of_dt,
        "period_end_after_as_of",
        "Reporting period end is after the decision date.",
        row_number,
        entity,
        as_of_key,
    )
    compare_after(
        findings,
        row_issues,
        "signal_date",
        signal_dt,
        "as_of",
        as_of_dt,
        "signal_date_after_as_of",
        "Signal timestamp is after the decision date.",
        row_number,
        entity,
        as_of_key,
    )
    compare_after(
        findings,
        row_issues,
        "available_date",
        available_dt,
        "signal_date",
        signal_dt,
        "available_date_after_signal_date",
        "Signal timestamp precedes the data availability timestamp.",
        row_number,
        entity,
        as_of_key,
    )
    compare_after(
        findings,
        row_issues,
        "period_end_date",
        period_end_dt,
        "available_date",
        available_dt,
        "period_end_after_available_date",
        "Reporting period end is after availability timestamp.",
        row_number,
        entity,
        as_of_key,
        "warning",
    )
    compare_after(
        findings,
        row_issues,
        "universe_date",
        universe_dt,
        "as_of",
        as_of_dt,
        "universe_date_after_as_of",
        "Universe eligibility timestamp is after the decision date.",
        row_number,
        entity,
        as_of_key,
    )
    compare_after(
        findings,
        row_issues,
        "revision_timestamp",
        revision_dt,
        "as_of",
        as_of_dt,
        "revision_after_as_of",
        "Revision timestamp is after the decision date; the row may use a later vintage.",
        row_number,
        entity,
        as_of_key,
    )
    compare_after(
        findings,
        row_issues,
        "vendor_timestamp",
        vendor_dt,
        "as_of",
        as_of_dt,
        "vendor_timestamp_after_as_of",
        "Vendor timestamp is after the decision date.",
        row_number,
        entity,
        as_of_key,
    )
    compare_after(
        findings,
        row_issues,
        "signal_date",
        signal_dt,
        "rebalance_date",
        rebalance_dt,
        "signal_after_rebalance",
        "Signal timestamp is after the rebalance timestamp.",
        row_number,
        entity,
        as_of_key,
    )
    compare_after(
        findings,
        row_issues,
        "rebalance_date",
        rebalance_dt,
        "execution_date",
        execution_dt,
        "rebalance_after_execution",
        "Rebalance timestamp is after the execution timestamp.",
        row_number,
        entity,
        as_of_key,
    )
    compare_after(
        findings,
        row_issues,
        "signal_date",
        signal_dt,
        "execution_date",
        execution_dt,
        "signal_after_execution",
        "Signal timestamp is after the execution timestamp.",
        row_number,
        entity,
        as_of_key,
    )

    if period_end_dt is not None and available_dt is not None:
        lag_days = days_between(available_dt, period_end_dt)
        if lag_days < args.min_availability_lag_days:
            add_issue(
                findings,
                row_issues,
                args.lag_severity,
                "availability_lag_too_short",
                "Availability lag from period end is shorter than the required minimum.",
                row_number,
                entity,
                as_of_key,
                lag_days,
                args.min_availability_lag_days,
            )
    if present(header, args.in_universe_col):
        in_universe = normalize_bool(text(row, args.in_universe_col))
        if in_universe is True and not present(header, args.universe_date_col):
            add_issue(
                findings,
                row_issues,
                "warning",
                "missing_universe_date_column",
                "Rows marked in-universe have no universe timestamp column.",
                row_number,
                entity,
                as_of_key,
            )
        elif in_universe is True and universe_dt is None:
            add_issue(
                findings,
                row_issues,
                "warning",
                "missing_universe_date",
                "Row is marked in-universe but has no universe timestamp.",
                row_number,
                entity,
                as_of_key,
            )

    return {
        "row_number": row_number,
        "entity": entity,
        "as_of": as_of_key,
        "source": text(row, args.source_col) if present(header, args.source_col) else "",
        "available_date": iso(available_dt),
        "data_date": iso(data_dt),
        "period_end_date": iso(period_end_dt),
        "signal_date": iso(signal_dt),
        "rebalance_date": iso(rebalance_dt),
        "execution_date": iso(execution_dt),
        "universe_date": iso(universe_dt),
        "revision_timestamp": iso(revision_dt),
        "vendor_timestamp": iso(vendor_dt),
        "issue_count": len(row_issues),
        "issues": row_issues,
    }


def duplicate_findings(row_checks: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[int]] = {}
    for item in row_checks:
        entity = str(item.get("entity") or "")
        as_of = str(item.get("as_of") or "")
        if not entity or not as_of:
            continue
        groups.setdefault((entity, as_of), []).append(int(item["row_number"]))
    out = []
    for (entity, as_of), row_numbers in groups.items():
        if len(row_numbers) > 1:
            out.append(
                finding(
                    args.duplicate_severity,
                    "duplicate_entity_as_of",
                    "Multiple rows share the same entity and decision/as-of timestamp.",
                    row_numbers[0],
                    entity,
                    as_of,
                    {"duplicate_rows": row_numbers[:20], "duplicate_count": len(row_numbers)},
                    1,
                )
            )
    return out


def build_report(header: list[str], rows: list[dict[str, str]], args: argparse.Namespace) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    coverage = column_coverage(header, args)
    row_checks = []
    for row_number, row in enumerate(rows, start=1):
        row_check = audit_row(header, row, row_number, args, findings)
        if row_check is not None:
            row_checks.append(row_check)

    dupes = duplicate_findings(row_checks, args)
    findings.extend(dupes)
    issue_counts: dict[str, int] = {}
    for item in findings:
        check = str(item["check"])
        issue_counts[check] = issue_counts.get(check, 0) + 1

    blockers = [item for item in findings if item["severity"] == "blocker"]
    warnings = [item for item in findings if item["severity"] == "warning"]
    ranked = sorted(
        findings,
        key=lambda item: (severity_rank(item), item["check"], str(item.get("row_number", ""))),
        reverse=True,
    )
    clean_rows = [item for item in row_checks if not item["issues"]]
    problem_rows = [item for item in row_checks if item["issues"]]
    entities = {str(item.get("entity", "")) for item in row_checks if item.get("entity")}
    as_of_dates = {str(item.get("as_of", "")) for item in row_checks if item.get("as_of")}
    sources: dict[str, int] = {}
    for item in row_checks:
        source = str(item.get("source", "") or "unspecified")
        sources[source] = sources.get(source, 0) + 1
    decision = "fail" if blockers else ("review" if warnings else "pass")

    return {
        "audit_type": "point_in_time_audit",
        "audit_decision": decision,
        "row_count": len(rows),
        "checked_row_count": len(row_checks),
        "clean_row_count": len(clean_rows),
        "problem_row_count": len(problem_rows),
        "entity_count": len(entities),
        "date_count": len(as_of_dates),
        "source_counts": dict(sorted(sources.items())),
        "duplicate_key_count": len(dupes),
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "finding_count": len(findings),
        "issue_counts": dict(sorted(issue_counts.items())),
        "column_coverage": coverage,
        "thresholds": {
            "min_availability_lag_days": args.min_availability_lag_days,
            "lag_severity": args.lag_severity,
            "duplicate_severity": args.duplicate_severity,
            "strict_missing_availability": args.strict_missing_availability,
        },
        "top_findings": ranked[: args.finding_limit],
        "problem_rows": sorted(
            problem_rows,
            key=lambda item: (-int(item["issue_count"]), str(item["entity"]), str(item["as_of"])),
        )[: args.finding_limit],
        "notes": [
            "This audit checks timestamp consistency; it cannot prove vendor data is historically correct without source-vintage evidence.",
            "Run this before IC, quantile, regression, long/short backtest, and alpha-gate interpretation.",
            "Fresh production data is not the same as point-in-time historical data; pair this with freshness and reconciliation checks.",
        ],
    }


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Point-in-Time Data Audit",
        "",
        f"- Decision: {report['audit_decision']}",
        f"- Rows: {report['row_count']}",
        f"- Checked rows: {report['checked_row_count']}",
        f"- Problem rows: {report['problem_row_count']}",
        f"- Entities: {report['entity_count']}",
        f"- As-of dates: {report['date_count']}",
        f"- Blockers: {report['blocker_count']}",
        f"- Warnings: {report['warning_count']}",
        "",
        "## Column Coverage",
        "",
        "| Column role | Present |",
        "| --- | --- |",
    ]
    for name, is_present in report["column_coverage"].items():
        lines.append(f"| {md_escape(name)} | {is_present} |")

    lines.extend(["", "## Issue Counts", ""])
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
            "| Severity | Check | Row | Entity | As of | Metric | Threshold | Detail |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if report["top_findings"]:
        for item in report["top_findings"]:
            lines.append(
                f"| {md_escape(item['severity'])} | {md_escape(item['check'])} | {md_escape(item.get('row_number', ''))} | {md_escape(item.get('entity', ''))} | {md_escape(item.get('as_of', ''))} | {md_escape(item.get('metric', ''))} | {md_escape(item.get('threshold', ''))} | {md_escape(item['detail'])} |"
            )
    else:
        lines.append("| info | no_findings |  |  |  |  |  | No point-in-time findings from supplied panel. |")

    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit point-in-time data alignment and look-ahead leakage risks."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--as-of-col", default="as_of_date", help="Decision timestamp column.")
    parser.add_argument("--entity-col", default="asset", help="Entity/asset identifier column.")
    parser.add_argument(
        "--available-date-col",
        default="available_date",
        help="Release, filing, or vendor availability timestamp column.",
    )
    parser.add_argument(
        "--data-date-col", default="data_date", help="Source data observation timestamp column."
    )
    parser.add_argument(
        "--period-end-col", default="period_end_date", help="Reporting period end timestamp column."
    )
    parser.add_argument("--signal-date-col", default="signal_date", help="Signal timestamp column.")
    parser.add_argument(
        "--rebalance-date-col", default="rebalance_date", help="Portfolio rebalance timestamp column."
    )
    parser.add_argument("--execution-date-col", default="execution_date", help="Execution timestamp column.")
    parser.add_argument(
        "--universe-date-col", default="universe_date", help="Universe eligibility timestamp column."
    )
    parser.add_argument(
        "--in-universe-col", default="in_universe", help="Optional boolean universe membership column."
    )
    parser.add_argument(
        "--revision-timestamp-col",
        default="revision_timestamp",
        help="Data revision or vintage timestamp column.",
    )
    parser.add_argument(
        "--vendor-timestamp-col",
        default="vendor_timestamp",
        help="Vendor ingest or effective timestamp column.",
    )
    parser.add_argument("--source-col", default="source", help="Optional data source/vendor column.")
    parser.add_argument("--min-availability-lag-days", type=float, default=0.0)
    parser.add_argument("--lag-severity", choices=["warning", "blocker"], default="warning")
    parser.add_argument("--duplicate-severity", choices=["warning", "blocker"], default="blocker")
    parser.add_argument(
        "--strict-missing-availability",
        action="store_true",
        help="Treat missing availability timestamps as blockers.",
    )
    parser.add_argument("--finding-limit", type=int, default=30)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.min_availability_lag_days < 0:
        raise SystemExit("--min-availability-lag-days must be non-negative.")
    if args.finding_limit <= 0:
        raise SystemExit("--finding-limit must be positive.")

    df = read_dataframe(args.csv_path)
    require_columns(df, [args.as_of_col, args.entity_col])
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
