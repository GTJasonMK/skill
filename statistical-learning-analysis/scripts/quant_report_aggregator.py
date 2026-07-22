#!/usr/bin/env python3
"""Aggregate bundled quant JSON diagnostics into one review report.

Standard-library only. This is a schema-tolerant combiner for JSON outputs from
the bundled quant scripts. It extracts common decisions, alerts, blockers,
breaches, key metrics, and report-specific notes into a strategy review or
production health summary.
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


COMMON_METRIC_PATHS = [
    ("audit_decision", ("audit_decision",)),
    ("rows_used", ("rows_used",)),
    ("rows_dropped", ("rows_dropped",)),
    ("row_count", ("row_count",)),
    ("checked_row_count", ("checked_row_count",)),
    ("problem_row_count", ("problem_row_count",)),
    ("entity_count", ("entity_count",)),
    ("date_count", ("date_count",)),
    ("duplicate_key_count", ("duplicate_key_count",)),
    ("gate_decision", ("gate_decision",)),
    ("register_decision", ("register_decision",)),
    ("recommended_action", ("recommended_action",)),
    ("blocker_count", ("blocker_count",)),
    ("breach_count", ("breach_count",)),
    ("problem_count", ("problem_count",)),
    ("warning_count", ("warning_count",)),
    ("evidence_gap_count", ("evidence_gap_count",)),
    ("triggered_count", ("triggered_count",)),
    ("experiment_count", ("experiment_count",)),
    ("family_count", ("family_count",)),
    ("selected_count", ("selected_count",)),
    ("failed_count", ("failed_count",)),
    ("predeclared_missing_or_false_count", ("predeclared_missing_or_false_count",)),
    ("selected_missing_final_test_count", ("selected_missing_final_test_count",)),
    ("model_count", ("model_count",)),
    ("live_model_count", ("live_model_count",)),
    ("high_risk_model_count", ("high_risk_model_count",)),
    ("annualized_mean_gap", ("annualized_mean_gap",)),
    ("annualized_tracking_error", ("annualized_tracking_error",)),
    ("live_paper_correlation", ("live_paper_correlation",)),
    ("max_live_underperformance_streak", ("max_live_underperformance_streak",)),
    ("recent_rank_ic_mean", ("recent_rank_ic_summary", "mean")),
    ("recent_rank_ic_t_stat", ("recent_rank_ic_summary", "t_stat")),
    ("recent_turnover_mean", ("recent_turnover_summary", "mean")),
    ("realized_to_forecast_rms", ("realized_to_forecast_rms",)),
    ("var_breach_rate", ("var_breach_rate",)),
    ("regime_count", ("regime_count",)),
    ("worst_regime_by_mean_return", ("worst_regime_by_mean_return",)),
    ("order_exception_rate", ("overall", "exception_rate")),
    ("aggregate_fill_rate", ("overall", "aggregate_fill_rate")),
    ("slippage_bps", ("overall", "notional_weighted_slippage_bps")),
    ("total_cost_dollars", ("overall", "total_cost_dollars")),
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
    text = str(value).strip().lower().replace(" ", "_")
    return text if text in DECISION_RANK else text


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
    if "recommended_action" in data:
        return "strategy_action_decision"
    if "checks_total" in data and "gate_decision" in data:
        return "go_live_gate"
    if "metric_summary" in data and "gate_decision" in data:
        return "limit_breach"
    if "live_return_summary" in data and "paper_return_summary" in data:
        return "live_vs_paper"
    if "recent_rank_ic_summary" in data:
        return "signal_health"
    if "problem_checks" in data and "fresh_count" in data:
        return "data_freshness"
    if "exceptions" in data and "overall" in data:
        return "order_exception"
    if "kupiec_pof" in data:
        return "risk_forecast_calibration"
    if "regimes" in data and "transition_counts" in data:
        return "regime_robustness"
    if "risk_contributions" in data or "component_risk" in data:
        return "risk_contribution"
    if "periods" in data and "cost_bps_summary" in data:
        return "capacity_or_cost"
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
    if int_or_zero(data.get("breach_count")) > 0:
        return "warn"
    if int_or_zero(data.get("problem_count")) > 0:
        return "warn"
    alerts = data.get("alerts")
    if isinstance(alerts, list) and alerts:
        return "warn"
    return "pass"


def int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def compact_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 8)
    return value


def key_metrics(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    metrics: dict[str, Any] = {}
    for name, path in COMMON_METRIC_PATHS:
        value = get_path(data, path)
        if value is not None:
            metrics[name] = compact_value(value)
    return metrics


def append_items(findings: list[dict[str, Any]], source: str, kind: str, items: Any, limit: int) -> None:
    if not isinstance(items, list):
        return
    for item in items[:limit]:
        if isinstance(item, dict):
            name = item.get("name") or item.get("check") or item.get("metric") or item.get("dataset") or kind
            detail = item.get("detail") or item.get("reason") or item.get("status") or item.get("issues") or item.get("action") or ""
            severity = item.get("severity") or ("warning" if kind in {"alerts", "warnings"} else "info")
        else:
            name = kind
            detail = str(item)
            severity = "info"
        findings.append({"source": source, "kind": kind, "severity": severity, "name": name, "detail": detail})


def report_findings(data: Any, source: str, limit: int) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not isinstance(data, dict):
        findings.append({"source": source, "kind": "load", "severity": "warning", "name": "non_object_json", "detail": "Report JSON root is not an object."})
        return findings
    for field, kind in [
        ("top_findings", "top_findings"),
        ("alerts", "alerts"),
        ("blockers", "blockers"),
        ("warnings", "warnings"),
        ("evidence_gaps", "evidence_gaps"),
        ("problem_checks", "problem_checks"),
        ("exceptions", "exceptions"),
        ("breaches", "breaches"),
        ("triggered_rules", "triggered_rules"),
    ]:
        append_items(findings, source, kind, data.get(field), limit)
    for count_field, kind in [
        ("rows_dropped", "dropped_rows"),
        ("problem_count", "problem_count"),
        ("blocker_count", "blocker_count"),
        ("breach_count", "breach_count"),
        ("evidence_gap_count", "evidence_gap_count"),
        ("triggered_count", "triggered_count"),
    ]:
        value = int_or_zero(data.get(count_field))
        if value > 0:
            findings.append({"source": source, "kind": kind, "severity": "info", "name": count_field, "detail": value})
    return findings[:limit]


def summarize_reports(paths: list[Path], finding_limit: int) -> dict[str, Any]:
    reports = []
    all_findings: list[dict[str, Any]] = []
    decisions: dict[str, int] = {}
    worst_decision = "pass"
    worst_rank = -1
    for path in paths:
        data = load_json(path)
        report_type = infer_report_type(data, path)
        decision = infer_decision(data)
        rank = DECISION_RANK.get(decision, 1)
        if rank > worst_rank:
            worst_rank = rank
            worst_decision = decision
        decisions[decision] = decisions.get(decision, 0) + 1
        findings = report_findings(data, path.name, finding_limit)
        all_findings.extend(findings)
        reports.append(
            {
                "path": str(path),
                "name": path.name,
                "type": report_type,
                "decision": decision,
                "decision_rank": rank,
                "key_metrics": key_metrics(data),
                "finding_count": len(findings),
                "findings": findings,
            }
        )
    ranked_findings = sorted(all_findings, key=lambda item: (severity_rank(item.get("severity")), item.get("source", ""), item.get("kind", "")), reverse=True)
    return {
        "report_count": len(reports),
        "overall_decision": worst_decision,
        "decision_counts": decisions,
        "finding_count": len(all_findings),
        "top_findings": ranked_findings[:finding_limit],
        "reports": reports,
        "notes": [
            "The overall decision is the highest-ranked decision inferred from input reports.",
            "This aggregator is schema-tolerant and should be treated as a review index, not a replacement for reading the source diagnostics.",
            "Use predeclared thresholds and owner sign-off before changing capital, risk, or trading state.",
        ],
    }


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


def md_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def markdown(report: dict[str, Any], title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- Reports aggregated: {report['report_count']}",
        f"- Overall decision: {report['overall_decision']}",
        f"- Findings: {report['finding_count']}",
        "",
        "## Decision Counts",
        "",
    ]
    if report["decision_counts"]:
        for decision, count in sorted(report["decision_counts"].items(), key=lambda item: (-DECISION_RANK.get(item[0], 0), item[0])):
            lines.append(f"- {decision}: {count}")
    else:
        lines.append("- none")

    lines.extend(["", "## Reports", "", "| Report | Type | Decision | Key metrics | Findings |", "| --- | --- | --- | --- | --- |"])
    for item in report["reports"]:
        metrics = ", ".join(f"{key}={value}" for key, value in item["key_metrics"].items())
        lines.append(f"| {md_escape(item['name'])} | {md_escape(item['type'])} | {md_escape(item['decision'])} | {md_escape(metrics)} | {item['finding_count']} |")

    lines.extend(["", "## Top Findings", "", "| Source | Kind | Severity | Name | Detail |", "| --- | --- | --- | --- | --- |"])
    for item in report["top_findings"]:
        lines.append(f"| {md_escape(item['source'])} | {md_escape(item['kind'])} | {md_escape(item['severity'])} | {md_escape(item['name'])} | {md_escape(item['detail'])} |")

    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate bundled quant JSON diagnostics into one review report.")
    parser.add_argument("json_paths", nargs="+", type=Path)
    parser.add_argument("--title", default="Quant Strategy Review")
    parser.add_argument("--finding-limit", type=int, default=20)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.finding_limit <= 0:
        raise SystemExit("--finding-limit must be positive.")
    report = summarize_reports(args.json_paths, args.finding_limit)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown(report, args.title), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(markdown(report, args.title), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
