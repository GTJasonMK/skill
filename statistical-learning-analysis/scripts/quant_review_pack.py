#!/usr/bin/env python3
"""Generate a committee-style quant review pack from bundled JSON diagnostics.

Standard-library only. This script turns source diagnostics and gate outputs
into a structured review package for research, portfolio, risk, trading, data,
and operations reviewers. Source reports remain authoritative; this pack is a
decision and evidence map.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DECISION_RANK = {
    "pass": 0,
    "maintain": 0,
    "conditional_pass": 1,
    "review": 1,
    "watch": 1,
    "warn": 1,
    "warning": 1,
    "reduce": 2,
    "de-risk": 2,
    "pause": 3,
    "freeze": 3,
    "fail": 3,
    "stop": 3,
    "retire": 4,
}

ROLE_ORDER = ["research", "portfolio", "risk", "trading", "data", "operations"]

TYPE_ROLE = {
    "point_in_time_audit": "data",
    "execution_timing_audit": "trading",
    "tradability_audit": "trading",
    "factor_ic": "research",
    "factor_decay": "research",
    "signal_overlap": "research",
    "incremental_alpha": "research",
    "alpha_research_gate": "research",
    "experiment_audit": "research",
    "multiple_testing": "research",
    "bootstrap_reality_check": "research",
    "portfolio_backtest": "portfolio",
    "portfolio_constraints": "portfolio",
    "portfolio_exposure": "portfolio",
    "portfolio_construction_gate": "portfolio",
    "optimizer_sensitivity": "portfolio",
    "risk_contribution": "risk",
    "risk_forecast_calibration": "risk",
    "model_risk_register": "risk",
    "limit_breach": "risk",
    "regime_robustness": "risk",
    "transaction_cost": "trading",
    "capacity": "trading",
    "execution_slippage": "trading",
    "order_exception": "trading",
    "data_freshness": "data",
    "go_live_gate": "operations",
    "strategy_action_decision": "operations",
    "live_vs_paper": "operations",
    "signal_health": "operations",
}

ROLE_KEYWORDS = {
    "research": ["alpha", "ic", "signal", "factor", "incremental", "overlap", "multiple", "reality", "snooping", "forward-return"],
    "portfolio": ["portfolio", "constraint", "exposure", "optimizer", "weight", "turnover", "concentration", "construction", "rebalance"],
    "risk": ["risk", "model", "validation", "validator", "review", "governance", "volatility", "var", "drawdown", "breach", "limit", "leverage", "contribution", "stress"],
    "trading": ["cost", "capacity", "adv", "slippage", "execution", "order", "fill", "borrow", "spread", "participation", "timing", "return_start", "return-window", "tradability", "tradable", "halted", "suspended", "shortable", "volume", "liquidity", "limit_up", "limit_down", "limit-lock"],
    "data": ["data", "freshness", "missing", "stale", "dataset", "rows_dropped", "point-in-time", "point_in_time", "look-ahead", "lookahead", "leakage", "vendor", "universe", "market-state"],
    "operations": ["gate", "owner", "evidence", "monitor", "rollback", "action", "go-live", "approval", "sign-off"],
}

COMMON_METRIC_PATHS = [
    ("audit_decision", ("audit_decision",)),
    ("gate_decision", ("gate_decision",)),
    ("register_decision", ("register_decision",)),
    ("recommended_action", ("recommended_action",)),
    ("blocker_count", ("blocker_count",)),
    ("warning_count", ("warning_count",)),
    ("finding_count", ("finding_count",)),
    ("experiment_count", ("experiment_count",)),
    ("family_count", ("family_count",)),
    ("selected_count", ("selected_count",)),
    ("failed_count", ("failed_count",)),
    ("predeclared_missing_or_false_count", ("predeclared_missing_or_false_count",)),
    ("selected_missing_final_test_count", ("selected_missing_final_test_count",)),
    ("model_count", ("model_count",)),
    ("live_model_count", ("live_model_count",)),
    ("high_risk_model_count", ("high_risk_model_count",)),
    ("periods_used", ("periods_used",)),
    ("dates_used", ("dates_used",)),
    ("rows_dropped", ("rows_dropped",)),
    ("row_count", ("row_count",)),
    ("checked_row_count", ("checked_row_count",)),
    ("problem_row_count", ("problem_row_count",)),
    ("entity_count", ("entity_count",)),
    ("date_count", ("date_count",)),
    ("duplicate_key_count", ("duplicate_key_count",)),
    ("rank_ic_mean", ("rank_ic_summary", "mean")),
    ("rank_ic_t_stat", ("rank_ic_summary", "t_stat")),
    ("residual_rank_ic_mean", ("residual_rank_ic_summary", "mean")),
    ("delta_r2_mean", ("delta_r2_summary", "mean")),
    ("redundant_pair_count", ("redundant_pair_count",)),
    ("net_sharpe", ("net_return_summary", "sharpe")),
    ("net_annualized_return", ("net_return_summary", "annualized_return_geometric")),
    ("net_max_drawdown", ("net_return_summary", "max_drawdown")),
    ("turnover_mean", ("turnover_summary", "mean")),
    ("periods_failed", ("periods_failed",)),
    ("annualized_portfolio_volatility", ("annualized_portfolio_volatility",)),
    ("mean_cost_bps_per_period", ("mean_cost_bps_per_period",)),
    ("max_adv_participation", ("participation_summary", "max")),
    ("binding_capacity_min", ("binding_capacity_summary", "min")),
    ("live_paper_correlation", ("live_paper_correlation",)),
    ("annualized_tracking_error", ("annualized_tracking_error",)),
    ("problem_count", ("problem_count",)),
    ("breach_count", ("breach_count",)),
    ("evidence_gap_count", ("evidence_gap_count",)),
]


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def get_path(data: Any, path: tuple[str, ...]) -> Any:
    current = data
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def normalize_decision(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace(" ", "_")


def int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def compact_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 8)
    return value


def severity_rank(value: Any) -> int:
    text = str(value or "").lower()
    if text in {"critical", "fail", "blocker"}:
        return 4
    if text in {"high", "error"}:
        return 3
    if text in {"medium", "warning", "warn"}:
        return 2
    if text in {"low", "info"}:
        return 1
    return 0


def severity_label(value: Any, default: str = "info") -> str:
    text = str(value or default).lower()
    if text in {"critical", "fail", "blocker"}:
        return "blocker"
    if text in {"high", "error"}:
        return "high"
    if text in {"medium", "warning", "warn"}:
        return "warning"
    if text in {"low", "info"}:
        return "info"
    return text


def infer_report_type(data: Any, path: Path) -> str:
    if not isinstance(data, dict):
        return "unknown"
    if data.get("audit_type") == "point_in_time_audit":
        return "point_in_time_audit"
    if data.get("audit_type") == "execution_timing_audit":
        return "execution_timing_audit"
    if data.get("audit_type") == "tradability_audit":
        return "tradability_audit"
    if data.get("audit_type") == "quant_experiment_audit":
        return "experiment_audit"
    if data.get("report_type") == "model_risk_register":
        return "model_risk_register"
    if data.get("gate") == "alpha_research":
        return "alpha_research_gate"
    if data.get("gate") == "portfolio_construction":
        return "portfolio_construction_gate"
    if "checks_total" in data and "gate_decision" in data:
        return "go_live_gate"
    if "metric_summary" in data and "gate_decision" in data:
        return "limit_breach"
    if "recommended_action" in data:
        return "strategy_action_decision"
    if "residual_rank_ic_summary" in data and "candidate_explained_by_base_r2_summary" in data:
        return "incremental_alpha"
    if "rank_ic_summary" in data and "factor_col" in data:
        return "factor_ic"
    if "horizons" in data and "forward_return_cols" in data:
        return "factor_decay"
    if "redundant_pair_count" in data and "pair_summary" in data:
        return "signal_overlap"
    if "discoveries" in data and "tests_used" in data:
        return "multiple_testing"
    if "reality_check_p_value_mean" in data or "reality_check_p_value_t_stat" in data:
        return "bootstrap_reality_check"
    if "periods_failed" in data and "constraints" in data:
        return "portfolio_constraints"
    if "exposure_summary" in data and "numeric_exposure_summary" in data:
        return "portfolio_exposure"
    if "risk_contributions" in data and "annualized_portfolio_volatility" in data:
        return "risk_contribution"
    if "l1_distance_summary" in data and "weight_summary" in data:
        return "optimizer_sensitivity"
    if "gross_exposure_summary" in data and "net_return_summary" in data:
        return "portfolio_backtest"
    if "total_cost_summary" in data and "mean_cost_bps_per_period" in data:
        return "transaction_cost"
    if "cost_bps_summary" in data and "binding_capacity_summary" in data:
        return "capacity"
    if "recent_rank_ic_summary" in data:
        return "signal_health"
    if "live_return_summary" in data and "paper_return_summary" in data:
        return "live_vs_paper"
    if "problem_checks" in data and "fresh_count" in data:
        return "data_freshness"
    if "exceptions" in data and "overall" in data:
        return "order_exception"
    if "kupiec_pof" in data:
        return "risk_forecast_calibration"
    if "regimes" in data and "transition_counts" in data:
        return "regime_robustness"
    return path.stem


def infer_decision(data: Any) -> str:
    if not isinstance(data, dict):
        return "review"
    for field in ["recommended_action", "gate_decision", "register_decision", "audit_decision"]:
        decision = normalize_decision(data.get(field))
        if decision:
            return decision
    if int_or_zero(data.get("blocker_count")) > 0:
        return "fail"
    if int_or_zero(data.get("breach_count")) > 0 or int_or_zero(data.get("problem_count")) > 0:
        return "review"
    for field in ["top_findings", "findings", "alerts", "warnings", "evidence_gaps"]:
        items = data.get(field)
        if isinstance(items, list) and items:
            return "review"
    return "pass"


def key_metrics(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    out: dict[str, Any] = {}
    for name, path in COMMON_METRIC_PATHS:
        value = get_path(data, path)
        if value is not None:
            out[name] = compact_value(value)
    return out


def finding_from_item(source: str, report_type: str, kind: str, item: Any, default_severity: str) -> dict[str, Any]:
    if isinstance(item, dict):
        check = item.get("check") or item.get("name") or item.get("metric") or item.get("dataset") or item.get("constraint") or kind
        detail = item.get("detail") or item.get("reason") or item.get("status") or item.get("action") or item.get("issues") or ""
        severity = severity_label(item.get("severity"), default_severity)
        metric = item.get("metric")
        threshold = item.get("threshold")
    else:
        check = kind
        detail = str(item)
        severity = default_severity
        metric = None
        threshold = None
    finding = {
        "source": source,
        "report_type": report_type,
        "kind": kind,
        "severity": severity,
        "check": str(check),
        "detail": detail,
    }
    if metric is not None:
        finding["metric"] = metric
    if threshold is not None:
        finding["threshold"] = threshold
    finding["roles"] = roles_for_finding(report_type, finding)
    return finding


def extract_findings(data: Any, source: str, report_type: str, limit: int) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return [finding_from_item(source, report_type, "load", "Report JSON root is not an object.", "blocker")]

    findings: list[dict[str, Any]] = []
    prioritized = data.get("top_findings")
    if isinstance(prioritized, list) and prioritized:
        for item in prioritized[:limit]:
            findings.append(finding_from_item(source, report_type, "top_findings", item, "warning"))
    elif isinstance(data.get("findings"), list):
        for item in data["findings"][:limit]:
            findings.append(finding_from_item(source, report_type, "findings", item, "warning"))

    for field, default_severity in [
        ("blockers", "blocker"),
        ("warnings", "warning"),
        ("alerts", "warning"),
        ("evidence_gaps", "warning"),
        ("problem_checks", "warning"),
        ("breaches", "warning"),
        ("exceptions", "warning"),
        ("triggered_rules", "warning"),
    ]:
        items = data.get(field)
        if isinstance(items, list):
            for item in items[:limit]:
                findings.append(finding_from_item(source, report_type, field, item, default_severity))

    if not findings:
        for count_field in ["blocker_count", "warning_count", "breach_count", "problem_count", "evidence_gap_count", "rows_dropped"]:
            value = int_or_zero(data.get(count_field))
            if value > 0:
                severity = "blocker" if count_field == "blocker_count" else "warning"
                findings.append(finding_from_item(source, report_type, count_field, {"check": count_field, "detail": value, "severity": severity}, severity))
    return findings[:limit]


def roles_for_finding(report_type: str, item: dict[str, Any]) -> list[str]:
    roles = set()
    base = TYPE_ROLE.get(report_type)
    if base:
        roles.add(base)
    text = " ".join(str(item.get(key, "")) for key in ["check", "detail", "kind", "source", "report_type"]).lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            roles.add(role)
    return [role for role in ROLE_ORDER if role in roles] or ["operations"]


def role_summary(findings: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary = {role: {"blockers": 0, "warnings": 0, "findings": []} for role in ROLE_ORDER}
    for item in findings:
        severity = item.get("severity")
        for role in item.get("roles", []):
            if severity == "blocker":
                summary[role]["blockers"] += 1
            elif severity in {"warning", "high"}:
                summary[role]["warnings"] += 1
            if len(summary[role]["findings"]) < 5:
                summary[role]["findings"].append({"source": item["source"], "check": item["check"], "severity": severity})
    return summary


def next_actions(report: dict[str, Any]) -> list[str]:
    actions = []
    if report["overall_decision"] in {"fail", "pause", "stop", "retire"}:
        actions.append("Do not promote or scale until blocker findings are resolved and source diagnostics are regenerated.")
    elif report["overall_decision"] in {"review", "warn", "warning", "reduce", "de-risk"}:
        actions.append("Hold reviewer sign-off until warning findings and evidence gaps have explicit owners or waivers.")
    else:
        actions.append("Record reviewer sign-off, preserve source diagnostics, and define monitoring thresholds before the next stage.")
    for role in ROLE_ORDER:
        row = report["role_summary"][role]
        if row["blockers"] or row["warnings"]:
            actions.append(f"{role}: resolve {row['blockers']} blocker(s) and {row['warnings']} warning(s), or document approved waivers.")
    if not actions:
        actions.append("No action items generated from supplied diagnostics.")
    return actions


def build_report(paths: list[Path], args: argparse.Namespace) -> dict[str, Any]:
    reports = []
    findings: list[dict[str, Any]] = []
    decision_counts: dict[str, int] = {}
    worst_decision = "pass"
    worst_rank = -1

    for path in paths:
        data = load_json(path)
        report_type = infer_report_type(data, path)
        decision = infer_decision(data)
        rank = DECISION_RANK.get(decision, 1)
        if rank > worst_rank:
            worst_decision = decision
            worst_rank = rank
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        report_findings = extract_findings(data, path.name, report_type, args.finding_limit)
        findings.extend(report_findings)
        reports.append(
            {
                "path": str(path),
                "name": path.name,
                "type": report_type,
                "decision": decision,
                "decision_rank": rank,
                "key_metrics": key_metrics(data),
                "finding_count": len(report_findings),
                "roles": sorted({role for item in report_findings for role in item.get("roles", [])}),
            }
        )

    ranked_findings = sorted(findings, key=lambda item: (severity_rank(item.get("severity")), item.get("source", ""), item.get("check", "")), reverse=True)
    blockers = [item for item in findings if item.get("severity") == "blocker"]
    warnings = [item for item in findings if item.get("severity") in {"warning", "high"}]
    evidence_gaps = [
        item
        for item in findings
        if "missing" in str(item.get("check", "")).lower()
        or "evidence" in str(item.get("check", "")).lower()
        or "evidence" in str(item.get("detail", "")).lower()
    ]
    report = {
        "title": args.title,
        "strategy_name": args.strategy_name,
        "stage": args.stage,
        "report_count": len(reports),
        "overall_decision": worst_decision,
        "decision_counts": decision_counts,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "evidence_gap_count": len(evidence_gaps),
        "role_summary": role_summary(ranked_findings),
        "top_findings": ranked_findings[: args.finding_limit],
        "evidence_gaps": evidence_gaps[: args.finding_limit],
        "reports": reports,
        "notes": [
            "This review pack is a structured decision aid; source diagnostics remain authoritative.",
            "A favorable pack does not replace owner sign-off, mandate constraints, or production go-live approval.",
            "Thresholds, required diagnostics, and waiver rules should be predeclared before reviewing outcomes.",
        ],
    }
    report["next_actions"] = next_actions(report)
    return report


def md_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def markdown(report: dict[str, Any]) -> str:
    title = report["title"]
    strategy = report["strategy_name"] or "Unspecified"
    lines = [
        f"# {title}",
        "",
        f"- Strategy: {strategy}",
        f"- Stage: {report['stage']}",
        f"- Overall decision: {report['overall_decision']}",
        f"- Reports reviewed: {report['report_count']}",
        f"- Blockers: {report['blocker_count']}",
        f"- Warnings: {report['warning_count']}",
        f"- Evidence gaps: {report['evidence_gap_count']}",
        "",
        "## Decision Stack",
        "",
        "| Report | Type | Decision | Key metrics | Roles |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["reports"]:
        metrics = ", ".join(f"{key}={value}" for key, value in item["key_metrics"].items())
        roles = ", ".join(item["roles"]) or "-"
        lines.append(f"| {md_escape(item['name'])} | {md_escape(item['type'])} | {md_escape(item['decision'])} | {md_escape(metrics)} | {md_escape(roles)} |")

    lines.extend(["", "## Role Review", "", "| Role | Blockers | Warnings | Representative issues |", "| --- | --- | --- | --- |"])
    for role in ROLE_ORDER:
        row = report["role_summary"][role]
        issues = "; ".join(f"{item['source']}:{item['check']}" for item in row["findings"]) or "-"
        lines.append(f"| {role} | {row['blockers']} | {row['warnings']} | {md_escape(issues)} |")

    lines.extend(["", "## Top Findings", "", "| Severity | Roles | Source | Check | Detail | Metric | Threshold |", "| --- | --- | --- | --- | --- | --- | --- |"])
    for item in report["top_findings"]:
        roles = ", ".join(item.get("roles", []))
        lines.append(
            f"| {md_escape(item['severity'])} | {md_escape(roles)} | {md_escape(item['source'])} | {md_escape(item['check'])} | {md_escape(item.get('detail'))} | {md_escape(item.get('metric'))} | {md_escape(item.get('threshold'))} |"
        )

    lines.extend(["", "## Evidence Gaps", "", "| Source | Check | Detail |", "| --- | --- | --- |"])
    if report["evidence_gaps"]:
        for item in report["evidence_gaps"]:
            lines.append(f"| {md_escape(item['source'])} | {md_escape(item['check'])} | {md_escape(item.get('detail'))} |")
    else:
        lines.append("| - | - | None detected from supplied diagnostics. |")

    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {action}" for action in report["next_actions"])
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a committee-style quant review pack from bundled JSON diagnostics.")
    parser.add_argument("json_paths", nargs="+", type=Path)
    parser.add_argument("--title", default="Quant Review Pack")
    parser.add_argument("--strategy-name", default="")
    parser.add_argument("--stage", choices=["research", "portfolio", "production", "full"], default="full")
    parser.add_argument("--finding-limit", type=int, default=30)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.finding_limit <= 0:
        raise SystemExit("--finding-limit must be positive.")
    report = build_report(args.json_paths, args)
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
