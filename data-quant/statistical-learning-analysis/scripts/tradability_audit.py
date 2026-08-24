#!/usr/bin/env python3
"""Audit whether requested assets were tradable at the simulated trade time.

Requires the shared bundle core dependencies. This script complements point-in-time and execution
timing audits: it checks whether rows used in factor tests, backtests, or
portfolio construction have enough market-state evidence to support execution.
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


TRUE_VALUES = {"1", "true", "t", "yes", "y"}
FALSE_VALUES = {"0", "false", "f", "no", "n"}


def text(row: dict[str, str], col: str | None) -> str:
    return str(row.get(col or "", "")).strip()


def present(header: list[str], col: str | None) -> bool:
    return bool(col and col in header)


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


def bool_value(
    value: str | None, true_terms: set[str] | None = None, false_terms: set[str] | None = None
) -> bool | None:
    clean = str(value or "").strip().lower()
    if not clean:
        return None
    if true_terms and clean in true_terms:
        return True
    if false_terms and clean in false_terms:
        return False
    if clean in TRUE_VALUES:
        return True
    if clean in FALSE_VALUES:
        return False
    return None


def infer_side(row: dict[str, str], header: list[str], args: argparse.Namespace) -> str | None:
    if present(header, args.side_col):
        raw = text(row, args.side_col).lower()
        if raw in {"buy", "b", "long", "cover", "increase"}:
            return "buy"
        if raw in {"sell", "s", "short", "short_sell", "decrease"}:
            return "sell"
    for col in [args.order_qty_col, args.trade_value_col, args.target_weight_col]:
        if present(header, col):
            value = parse_float(text(row, col))
            if value is None or value == 0:
                continue
            return "buy" if value > 0 else "sell"
    return None


def row_has_trade(row: dict[str, str], header: list[str], args: argparse.Namespace) -> bool:
    for col in [args.order_qty_col, args.trade_value_col, args.target_weight_col]:
        if present(header, col):
            value = parse_float(text(row, col))
            if value is not None and abs(value) > args.min_abs_trade:
                return True
    return not any(
        present(header, col) for col in [args.order_qty_col, args.trade_value_col, args.target_weight_col]
    )


def finding(
    severity: str,
    check: str,
    detail: str,
    row_number: int | None = None,
    entity: str | None = None,
    date: str | None = None,
    metric: Any = None,
    threshold: Any = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {"severity": severity, "check": check, "detail": detail}
    if row_number is not None:
        out["row_number"] = row_number
    if entity:
        out["entity"] = entity
    if date:
        out["date"] = date
    if metric is not None:
        out["metric"] = metric
    if threshold is not None:
        out["threshold"] = threshold
    return out


def severity_rank(item: dict[str, Any]) -> int:
    return {"info": 0, "warning": 1, "blocker": 2}.get(str(item.get("severity", "info")), 0)


def is_evidence_gap(item: dict[str, Any]) -> bool:
    check = str(item.get("check", ""))
    return check.startswith("missing_") or check.startswith("invalid_") or check.endswith("_evidence_gap")


def add_issue(
    findings: list[dict[str, Any]],
    row_issues: list[str],
    severity: str,
    check: str,
    detail: str,
    row_number: int,
    entity: str,
    date_key: str | None,
    metric: Any = None,
    threshold: Any = None,
) -> None:
    row_issues.append(check)
    findings.append(finding(severity, check, detail, row_number, entity, date_key, metric, threshold))


def column_coverage(header: list[str], args: argparse.Namespace) -> dict[str, bool]:
    columns = {
        "date_col": args.date_col,
        "entity_col": args.entity_col,
        "side_col": args.side_col,
        "order_qty_col": args.order_qty_col,
        "target_weight_col": args.target_weight_col,
        "trade_value_col": args.trade_value_col,
        "execution_price_col": args.execution_price_col,
        "close_price_col": args.close_price_col,
        "volume_col": args.volume_col,
        "adv_col": args.adv_col,
        "dollar_volume_col": args.dollar_volume_col,
        "tradable_col": args.tradable_col,
        "halted_col": args.halted_col,
        "suspended_col": args.suspended_col,
        "limit_up_col": args.limit_up_col,
        "limit_down_col": args.limit_down_col,
        "limit_status_col": args.limit_status_col,
        "shortable_col": args.shortable_col,
        "borrow_available_col": args.borrow_available_col,
        "borrow_rate_col": args.borrow_rate_col,
    }
    return {name: present(header, col) for name, col in columns.items()}


def entity_value(row: dict[str, str], header: list[str], args: argparse.Namespace, row_number: int) -> str:
    if present(header, args.entity_col):
        value = text(row, args.entity_col)
        if value:
            return value
    return f"row_{row_number}"


def limit_flags(
    row: dict[str, str], header: list[str], args: argparse.Namespace
) -> tuple[bool | None, bool | None]:
    up = (
        bool_value(
            text(row, args.limit_up_col),
            {"up", "locked", "limit", "limit_up", "limitup"},
            {"open", "active", "normal", "none"},
        )
        if present(header, args.limit_up_col)
        else None
    )
    down = (
        bool_value(
            text(row, args.limit_down_col),
            {"down", "locked", "limit", "limit_down", "limitdown"},
            {"open", "active", "normal", "none"},
        )
        if present(header, args.limit_down_col)
        else None
    )
    if present(header, args.limit_status_col):
        raw = text(row, args.limit_status_col).lower()
        if raw:
            if any(token in raw for token in ["up", "limitup", "limit_up"]):
                up = True
            if any(token in raw for token in ["down", "limitdown", "limit_down"]):
                down = True
    return up, down


def participation(
    row: dict[str, str], header: list[str], args: argparse.Namespace
) -> tuple[float | None, str]:
    qty = parse_float(text(row, args.order_qty_col)) if present(header, args.order_qty_col) else None
    volume = parse_float(text(row, args.volume_col)) if present(header, args.volume_col) else None
    if qty is not None and volume not in {None, 0}:
        return abs(qty) / abs(volume), "shares"
    trade_value = (
        parse_float(text(row, args.trade_value_col)) if present(header, args.trade_value_col) else None
    )
    dollar_volume = (
        parse_float(text(row, args.dollar_volume_col)) if present(header, args.dollar_volume_col) else None
    )
    if trade_value is not None and dollar_volume not in {None, 0}:
        return abs(trade_value) / abs(dollar_volume), "dollar_value"
    return None, ""


def audit_row(
    header: list[str],
    row: dict[str, str],
    row_number: int,
    args: argparse.Namespace,
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    entity = entity_value(row, header, args, row_number)
    row_issues: list[str] = []
    date_dt = parse_timestamp(text(row, args.date_col)) if present(header, args.date_col) else None
    date_key = iso(date_dt)
    if not present(header, args.date_col):
        add_issue(
            findings,
            row_issues,
            "warning",
            "missing_date_column",
            "No trade or evaluation date column is present.",
            row_number,
            entity,
            None,
        )
    elif date_dt is None:
        add_issue(
            findings,
            row_issues,
            "warning",
            "invalid_or_missing_date",
            "Date is missing or not parseable as an ISO-style date/timestamp.",
            row_number,
            entity,
            None,
            text(row, args.date_col),
        )

    has_trade = row_has_trade(row, header, args)
    side = infer_side(row, header, args)
    volume = parse_float(text(row, args.volume_col)) if present(header, args.volume_col) else None
    adv = parse_float(text(row, args.adv_col)) if present(header, args.adv_col) else None
    execution_price = (
        parse_float(text(row, args.execution_price_col))
        if present(header, args.execution_price_col)
        else None
    )
    close_price = (
        parse_float(text(row, args.close_price_col)) if present(header, args.close_price_col) else None
    )
    tradable = (
        bool_value(
            text(row, args.tradable_col),
            {"tradable", "open", "active", "available", "normal"},
            {"not_tradable", "halted", "suspended", "closed", "unavailable"},
        )
        if present(header, args.tradable_col)
        else None
    )
    halted = (
        bool_value(
            text(row, args.halted_col),
            {"halted", "halt", "stopped"},
            {"open", "active", "normal", "tradable"},
        )
        if present(header, args.halted_col)
        else None
    )
    suspended = (
        bool_value(
            text(row, args.suspended_col), {"suspended", "suspend"}, {"open", "active", "normal", "tradable"}
        )
        if present(header, args.suspended_col)
        else None
    )
    shortable = (
        bool_value(
            text(row, args.shortable_col),
            {"shortable", "available", "borrowable"},
            {"not_shortable", "unavailable", "restricted"},
        )
        if present(header, args.shortable_col)
        else None
    )
    borrow_available = (
        bool_value(
            text(row, args.borrow_available_col),
            {"available", "borrowable", "located"},
            {"unavailable", "none", "no_borrow", "not_available"},
        )
        if present(header, args.borrow_available_col)
        else None
    )
    borrow_rate = (
        parse_float(text(row, args.borrow_rate_col)) if present(header, args.borrow_rate_col) else None
    )
    limit_up, limit_down = limit_flags(row, header, args)
    part, part_basis = participation(row, header, args)

    if tradable is False:
        add_issue(
            findings,
            row_issues,
            "blocker",
            "not_tradable_flag",
            "Tradable flag is false on a row used for the strategy.",
            row_number,
            entity,
            date_key,
        )
    if halted is True:
        add_issue(
            findings,
            row_issues,
            "blocker",
            "halted_security",
            "Security is marked halted on the trade/evaluation date.",
            row_number,
            entity,
            date_key,
        )
    if suspended is True:
        add_issue(
            findings,
            row_issues,
            "blocker",
            "suspended_security",
            "Security is marked suspended on the trade/evaluation date.",
            row_number,
            entity,
            date_key,
        )

    if has_trade and present(header, args.execution_price_col):
        if execution_price is None or execution_price <= 0:
            add_issue(
                findings,
                row_issues,
                "blocker",
                "missing_or_nonpositive_execution_price",
                "Execution price is missing or nonpositive for a traded row.",
                row_number,
                entity,
                date_key,
                execution_price,
            )
    elif has_trade and not present(header, args.execution_price_col):
        add_issue(
            findings,
            row_issues,
            "warning",
            "missing_execution_price_column",
            "No execution price column is present; tradability evidence is incomplete.",
            row_number,
            entity,
            date_key,
        )

    if present(header, args.close_price_col) and close_price is not None and close_price <= 0:
        add_issue(
            findings,
            row_issues,
            "warning",
            "nonpositive_close_price",
            "Close price is nonpositive; market data may be invalid.",
            row_number,
            entity,
            date_key,
            close_price,
        )

    if present(header, args.volume_col):
        if volume is None:
            add_issue(
                findings,
                row_issues,
                "warning",
                "missing_volume",
                "Volume is missing; liquidity and zero-volume checks are incomplete.",
                row_number,
                entity,
                date_key,
            )
        elif volume <= args.min_volume:
            severity = "blocker" if has_trade or args.strict_zero_volume else "warning"
            add_issue(
                findings,
                row_issues,
                severity,
                "zero_or_tiny_volume",
                "Volume is zero or below the minimum tradable volume threshold.",
                row_number,
                entity,
                date_key,
                volume,
                args.min_volume,
            )
    elif has_trade:
        add_issue(
            findings,
            row_issues,
            "warning",
            "missing_volume_column",
            "No volume column is present; liquidity evidence is incomplete.",
            row_number,
            entity,
            date_key,
        )

    if present(header, args.adv_col) and adv is not None and adv <= args.min_adv:
        add_issue(
            findings,
            row_issues,
            "warning",
            "zero_or_tiny_adv",
            "ADV is zero or below the minimum ADV threshold.",
            row_number,
            entity,
            date_key,
            adv,
            args.min_adv,
        )

    if has_trade and part is not None and part > args.max_participation:
        add_issue(
            findings,
            row_issues,
            args.participation_severity,
            "participation_too_high",
            f"Trade participation is above threshold using {part_basis}.",
            row_number,
            entity,
            date_key,
            part,
            args.max_participation,
        )
    if (
        has_trade
        and part is None
        and not any(present(header, col) for col in [args.volume_col, args.dollar_volume_col, args.adv_col])
    ):
        add_issue(
            findings,
            row_issues,
            "warning",
            "missing_participation_evidence_gap",
            "No share or dollar volume evidence is available to estimate participation.",
            row_number,
            entity,
            date_key,
        )

    if side == "buy" and limit_up is True:
        add_issue(
            findings,
            row_issues,
            "blocker",
            "buy_at_limit_up",
            "Buy order is simulated while the asset is limit-up locked.",
            row_number,
            entity,
            date_key,
        )
    if side == "sell" and limit_down is True:
        add_issue(
            findings,
            row_issues,
            "blocker",
            "sell_at_limit_down",
            "Sell order is simulated while the asset is limit-down locked.",
            row_number,
            entity,
            date_key,
        )
    if side is None and (limit_up is True or limit_down is True):
        add_issue(
            findings,
            row_issues,
            "warning",
            "limit_lock_without_side",
            "Asset has a limit-lock flag but trade side is unavailable.",
            row_number,
            entity,
            date_key,
        )

    if side == "sell":
        if shortable is False:
            add_issue(
                findings,
                row_issues,
                "blocker",
                "short_not_allowed",
                "Sell/short row is not shortable according to the shortable flag.",
                row_number,
                entity,
                date_key,
            )
        if borrow_available is False:
            add_issue(
                findings,
                row_issues,
                "blocker",
                "borrow_unavailable",
                "Sell/short row lacks borrow availability.",
                row_number,
                entity,
                date_key,
            )
        if borrow_rate is not None and borrow_rate > args.max_borrow_rate:
            add_issue(
                findings,
                row_issues,
                "warning",
                "borrow_rate_too_high",
                "Borrow rate is above threshold and may invalidate net economics.",
                row_number,
                entity,
                date_key,
                borrow_rate,
                args.max_borrow_rate,
            )
        if args.require_short_evidence and not any(
            present(header, col) for col in [args.shortable_col, args.borrow_available_col]
        ):
            add_issue(
                findings,
                row_issues,
                "warning",
                "missing_short_evidence_gap",
                "No shortable or borrow-availability column is present for a sell/short row.",
                row_number,
                entity,
                date_key,
            )

    if not any(
        present(header, col)
        for col in [
            args.tradable_col,
            args.halted_col,
            args.suspended_col,
            args.volume_col,
            args.limit_status_col,
            args.limit_up_col,
            args.limit_down_col,
        ]
    ):
        add_issue(
            findings,
            row_issues,
            "warning",
            "missing_market_state_evidence_gap",
            "No tradable/halt/suspension/volume/limit evidence columns are present.",
            row_number,
            entity,
            date_key,
        )

    return {
        "row_number": row_number,
        "entity": entity,
        "date": date_key,
        "side": side or "",
        "has_trade": has_trade,
        "volume": volume,
        "adv": adv,
        "execution_price": execution_price,
        "tradable": tradable,
        "halted": halted,
        "suspended": suspended,
        "limit_up": limit_up,
        "limit_down": limit_down,
        "participation": part,
        "issue_count": len(row_issues),
        "issues": row_issues,
    }


def stale_price_findings(row_checks: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    by_entity: dict[str, list[dict[str, Any]]] = {}
    for row in row_checks:
        if row.get("date") and row.get("execution_price") is not None:
            by_entity.setdefault(str(row["entity"]), []).append(row)
    out: list[dict[str, Any]] = []
    for entity, rows in by_entity.items():
        ordered = sorted(rows, key=lambda item: str(item.get("date", "")))
        streak: list[dict[str, Any]] = []
        last_price: float | None = None
        for item in ordered:
            price = item.get("execution_price")
            if (
                isinstance(price, (int, float))
                and last_price is not None
                and abs(float(price) - float(last_price)) <= args.stale_price_tolerance
            ):
                streak.append(item)
            else:
                streak = [item]
            last_price = float(price) if isinstance(price, (int, float)) else None
            if len(streak) >= args.stale_price_days and all(
                (row.get("volume") or 0) <= args.min_volume for row in streak
            ):
                first = streak[0]
                out.append(
                    finding(
                        "warning",
                        "stale_price_with_tiny_volume",
                        "Execution price repeats across consecutive rows while volume is zero or tiny; confirm stale-price and suspension handling.",
                        int(first["row_number"]),
                        entity,
                        str(first.get("date") or ""),
                        {
                            "rows": [row["row_number"] for row in streak[-args.stale_price_days :]],
                            "price": last_price,
                        },
                        args.stale_price_days,
                    )
                )
                streak = []
    return out


def build_report(header: list[str], rows: list[dict[str, str]], args: argparse.Namespace) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    row_checks = [
        audit_row(header, row, row_number, args, findings) for row_number, row in enumerate(rows, start=1)
    ]
    findings.extend(stale_price_findings(row_checks, args))

    issue_counts: dict[str, int] = {}
    for item in findings:
        check = str(item["check"])
        issue_counts[check] = issue_counts.get(check, 0) + 1
    blockers = [item for item in findings if item["severity"] == "blocker"]
    warnings = [item for item in findings if item["severity"] == "warning"]
    evidence_gaps = [item for item in findings if is_evidence_gap(item)]
    problem_rows = [item for item in row_checks if item["issues"]]
    entities = {str(item.get("entity", "")) for item in row_checks if item.get("entity")}
    dates = {str(item.get("date", "")) for item in row_checks if item.get("date")}
    ranked = sorted(
        findings,
        key=lambda item: (severity_rank(item), item["check"], str(item.get("row_number", ""))),
        reverse=True,
    )
    decision = "fail" if blockers else ("review" if warnings else "pass")
    return {
        "audit_type": "tradability_audit",
        "audit_decision": decision,
        "row_count": len(rows),
        "checked_row_count": len(row_checks),
        "problem_row_count": len(problem_rows),
        "entity_count": len(entities),
        "date_count": len(dates),
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "evidence_gap_count": len(evidence_gaps),
        "finding_count": len(findings),
        "issue_counts": dict(sorted(issue_counts.items())),
        "column_coverage": column_coverage(header, args),
        "thresholds": {
            "min_abs_trade": args.min_abs_trade,
            "min_volume": args.min_volume,
            "min_adv": args.min_adv,
            "max_participation": args.max_participation,
            "participation_severity": args.participation_severity,
            "max_borrow_rate": args.max_borrow_rate,
            "require_short_evidence": args.require_short_evidence,
            "strict_zero_volume": args.strict_zero_volume,
            "stale_price_days": args.stale_price_days,
            "stale_price_tolerance": args.stale_price_tolerance,
        },
        "top_findings": ranked[: args.finding_limit],
        "problem_rows": sorted(
            problem_rows,
            key=lambda item: (-int(item["issue_count"]), str(item["entity"]), str(item.get("date", ""))),
        )[: args.finding_limit],
        "notes": [
            "This audit checks tradability and market-state evidence; it does not prove source data was point-in-time or that the execution timestamp was valid.",
            "Run it after point-in-time and execution timing checks, before interpreting IC, sorted portfolios, portfolio backtests, or construction gates.",
            "Evidence gaps include missing market-state, volume, participation, short, or date evidence needed to justify simulated execution.",
        ],
    }


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Tradability Audit",
        "",
        f"- Decision: {report['audit_decision']}",
        f"- Rows: {report['row_count']}",
        f"- Problem rows: {report['problem_row_count']}",
        f"- Entities: {report['entity_count']}",
        f"- Dates: {report['date_count']}",
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
            "| Severity | Check | Row | Entity | Date | Metric | Threshold | Detail |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if report["top_findings"]:
        for item in report["top_findings"]:
            lines.append(
                f"| {md_escape(item['severity'])} | {md_escape(item['check'])} | {md_escape(item.get('row_number', ''))} | {md_escape(item.get('entity', ''))} | {md_escape(item.get('date', ''))} | {md_escape(item.get('metric', ''))} | {md_escape(item.get('threshold', ''))} | {md_escape(item['detail'])} |"
            )
    else:
        lines.append("| info | no_findings |  |  |  |  |  | No tradability findings from supplied panel. |")
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit tradability and market-state evidence for factor, backtest, or portfolio rows."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date-col", default="date")
    parser.add_argument("--entity-col", default="asset")
    parser.add_argument("--side-col", default="side")
    parser.add_argument("--order-qty-col", default="order_qty")
    parser.add_argument("--target-weight-col", default="target_weight")
    parser.add_argument("--trade-value-col", default="trade_value")
    parser.add_argument("--execution-price-col", default="execution_price")
    parser.add_argument("--close-price-col", default="close")
    parser.add_argument("--volume-col", default="volume")
    parser.add_argument("--adv-col", default="adv")
    parser.add_argument("--dollar-volume-col", default="dollar_volume")
    parser.add_argument("--tradable-col", default="tradable")
    parser.add_argument("--halted-col", default="halted")
    parser.add_argument("--suspended-col", default="suspended")
    parser.add_argument("--limit-up-col", default="limit_up")
    parser.add_argument("--limit-down-col", default="limit_down")
    parser.add_argument("--limit-status-col", default="limit_status")
    parser.add_argument("--shortable-col", default="shortable")
    parser.add_argument("--borrow-available-col", default="borrow_available")
    parser.add_argument("--borrow-rate-col", default="borrow_rate")
    parser.add_argument("--min-abs-trade", type=float, default=0.0)
    parser.add_argument("--min-volume", type=float, default=0.0)
    parser.add_argument("--min-adv", type=float, default=0.0)
    parser.add_argument("--max-participation", type=float, default=0.1)
    parser.add_argument("--participation-severity", choices=["warning", "blocker"], default="blocker")
    parser.add_argument("--max-borrow-rate", type=float, default=0.2)
    parser.add_argument(
        "--require-short-evidence",
        action="store_true",
        help="Warn when sell/short rows lack shortable or borrow columns.",
    )
    parser.add_argument(
        "--strict-zero-volume",
        action="store_true",
        help="Treat zero/tiny volume as a blocker even when no trade-size column is present.",
    )
    parser.add_argument("--stale-price-days", type=int, default=3)
    parser.add_argument("--stale-price-tolerance", type=float, default=1e-12)
    parser.add_argument("--finding-limit", type=int, default=30)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.min_abs_trade < 0 or args.min_volume < 0 or args.min_adv < 0:
        raise SystemExit("--min-abs-trade, --min-volume, and --min-adv must be non-negative.")
    if args.max_participation < 0:
        raise SystemExit("--max-participation must be non-negative.")
    if args.max_borrow_rate < 0:
        raise SystemExit("--max-borrow-rate must be non-negative.")
    if args.stale_price_days < 2:
        raise SystemExit("--stale-price-days must be at least 2.")
    if args.stale_price_tolerance < 0:
        raise SystemExit("--stale-price-tolerance must be non-negative.")
    if args.finding_limit <= 0:
        raise SystemExit("--finding-limit must be positive.")

    df = read_dataframe(args.csv_path)
    header, rows = _df_to_rows(df)
    if args.entity_col not in header:
        raise SystemExit(f"Entity column not found: {args.entity_col}")
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
