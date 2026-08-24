#!/usr/bin/env python3
"""Gate portfolio construction using bundled JSON diagnostics.

Standard-library only. This script consumes JSON outputs from portfolio
backtest, constraint, exposure, risk-contribution, optimizer-sensitivity,
transaction-cost, and capacity diagnostics, then applies a construction-stage
pass/review/fail gate. Use it after a signal passes research review but before
paper trading, production go-live, or capital scaling.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_REQUIRED_TYPES = [
    "execution_timing_audit",
    "tradability_audit",
    "portfolio_backtest",
    "portfolio_constraints",
    "portfolio_exposure",
    "risk_contribution",
    "cost_or_capacity",
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


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def infer_report_type(data: Any, path: Path) -> str:
    if not isinstance(data, dict):
        return "unknown"
    declared_type = data.get("artifact_type") or data.get("diagnostic_type")
    if isinstance(declared_type, str) and declared_type:
        return declared_type
    if data.get("audit_type") == "execution_timing_audit":
        return "execution_timing_audit"
    if data.get("audit_type") == "tradability_audit":
        return "tradability_audit"
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
    if data.get("gate") == "alpha_research" or ("gate_decision" in data and "required_types" in data):
        return "alpha_research_gate"
    if "gate_decision" in data:
        return "gate_or_limit"
    return path.stem


def type_alias(report_type: str) -> str:
    if report_type in {"transaction_cost", "capacity"}:
        return "cost_or_capacity"
    return report_type


def severity_rank(severity: str) -> int:
    return {"info": 0, "warning": 1, "blocker": 2}.get(severity, 0)


def finding(
    severity: str, check: str, detail: str, source: str, metric: Any = None, threshold: Any = None
) -> dict[str, Any]:
    out = {"severity": severity, "check": check, "detail": detail, "source": source}
    if metric is not None:
        out["metric"] = metric
    if threshold is not None:
        out["threshold"] = threshold
    return out


def check_min(
    findings: list[dict[str, Any]],
    value: float | None,
    threshold: float,
    severity: str,
    check: str,
    source: str,
    missing_detail: str,
    fail_detail: str,
) -> None:
    if value is None:
        findings.append(finding("warning", check, missing_detail, source, None, threshold))
    elif value < threshold:
        findings.append(finding(severity, check, fail_detail, source, value, threshold))


def check_max(
    findings: list[dict[str, Any]],
    value: float | None,
    threshold: float,
    severity: str,
    check: str,
    source: str,
    missing_detail: str,
    fail_detail: str,
) -> None:
    if value is None:
        findings.append(finding("warning", check, missing_detail, source, None, threshold))
    elif value > threshold:
        findings.append(finding(severity, check, fail_detail, source, value, threshold))


def check_abs_max(
    findings: list[dict[str, Any]],
    value: float | None,
    threshold: float,
    severity: str,
    check: str,
    source: str,
    missing_detail: str,
    fail_detail: str,
) -> None:
    if value is None:
        findings.append(finding("warning", check, missing_detail, source, None, threshold))
    elif abs(value) > threshold:
        findings.append(finding(severity, check, fail_detail, source, value, threshold))


def max_abs_summary(summary: Any) -> float | None:
    if not isinstance(summary, dict):
        return None
    values = [as_float(summary.get("min")), as_float(summary.get("max"))]
    clean = [abs(value) for value in values if value is not None]
    return max(clean) if clean else None


def max_abs_category_exposure(latest: Any) -> float | None:
    if not isinstance(latest, dict):
        return None
    exposures = latest.get("category_exposures")
    if not isinstance(exposures, dict):
        return None
    values: list[float] = []
    for by_label in exposures.values():
        if isinstance(by_label, dict):
            values.extend(
                abs(value) for value in (as_float(v) for v in by_label.values()) if value is not None
            )
    return max(values) if values else None


def report_key_metrics(data: Any, report_type: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    paths: list[tuple[str, tuple[str, ...]]] = []
    if report_type == "execution_timing_audit":
        paths = [
            ("audit_decision", ("audit_decision",)),
            ("row_count", ("row_count",)),
            ("checked_row_count", ("checked_row_count",)),
            ("problem_row_count", ("problem_row_count",)),
            ("entity_count", ("entity_count",)),
            ("date_count", ("date_count",)),
            ("duplicate_key_count", ("duplicate_key_count",)),
            ("blocker_count", ("blocker_count",)),
            ("warning_count", ("warning_count",)),
            ("evidence_gap_count", ("evidence_gap_count",)),
        ]
    elif report_type == "tradability_audit":
        paths = [
            ("audit_decision", ("audit_decision",)),
            ("row_count", ("row_count",)),
            ("checked_row_count", ("checked_row_count",)),
            ("problem_row_count", ("problem_row_count",)),
            ("entity_count", ("entity_count",)),
            ("date_count", ("date_count",)),
            ("blocker_count", ("blocker_count",)),
            ("warning_count", ("warning_count",)),
            ("evidence_gap_count", ("evidence_gap_count",)),
        ]
    elif report_type == "portfolio_backtest":
        paths = [
            ("periods_used", ("periods_used",)),
            ("net_sharpe", ("net_return_summary", "sharpe")),
            ("net_ann_return", ("net_return_summary", "annualized_return_geometric")),
            ("net_max_drawdown", ("net_return_summary", "max_drawdown")),
            ("turnover_mean", ("turnover_summary", "mean")),
            ("gross_exposure_mean", ("gross_exposure_summary", "mean")),
        ]
    elif report_type == "portfolio_constraints":
        paths = [
            ("periods_used", ("periods_used",)),
            ("periods_failed", ("periods_failed",)),
            ("gross_max", ("gross_summary", "max")),
            ("net_min", ("net_summary", "min")),
            ("net_max", ("net_summary", "max")),
            ("turnover_mean", ("turnover_summary", "mean")),
        ]
    elif report_type == "portfolio_exposure":
        paths = [
            ("periods_used", ("periods_used",)),
            ("gross_max", ("exposure_summary", "gross_exposure", "max")),
            ("net_min", ("exposure_summary", "net_exposure", "min")),
            ("net_max", ("exposure_summary", "net_exposure", "max")),
            ("concentration_hhi_max", ("exposure_summary", "concentration_hhi", "max")),
        ]
    elif report_type == "risk_contribution":
        paths = [
            ("ann_vol", ("annualized_portfolio_volatility",)),
            ("gross_exposure", ("gross_exposure",)),
            ("net_exposure", ("net_exposure",)),
        ]
    elif report_type == "optimizer_sensitivity":
        paths = [
            ("simulations", ("simulations",)),
            ("l1_distance_mean", ("l1_distance_summary", "mean")),
            ("concentration_hhi_mean", ("concentration_hhi_summary", "mean")),
        ]
    elif report_type == "transaction_cost":
        paths = [
            ("periods_used", ("periods_used",)),
            ("mean_cost_bps_per_period", ("mean_cost_bps_per_period",)),
            ("turnover_mean", ("turnover_summary", "mean")),
            ("max_adv_participation", ("max_adv_participation_summary", "max")),
        ]
    elif report_type == "capacity":
        paths = [
            ("periods_used", ("periods_used",)),
            ("participation_max", ("participation_summary", "max")),
            ("cost_bps_mean", ("cost_bps_summary", "mean")),
            ("binding_capacity_min", ("binding_capacity_summary", "min")),
        ]
    elif report_type == "alpha_research_gate":
        paths = [
            ("gate_decision", ("gate_decision",)),
            ("blocker_count", ("blocker_count",)),
            ("warning_count", ("warning_count",)),
        ]
    metrics = {}
    for name, path in paths:
        value = get_path(data, path)
        if value is not None:
            metrics[name] = value
    if report_type == "risk_contribution":
        top = top_risk_share(data)
        if top is not None:
            metrics["top_abs_risk_share"] = top
    if report_type == "portfolio_exposure":
        latest_category = max_abs_category_exposure(data.get("latest"))
        if latest_category is not None:
            metrics["latest_max_abs_category_exposure"] = latest_category
    if report_type == "optimizer_sensitivity":
        flip = max_sign_flip_rate(data)
        if flip is not None:
            metrics["max_sign_flip_rate"] = flip
    return metrics


def top_risk_share(data: dict[str, Any]) -> float | None:
    rows = data.get("risk_contributions")
    if not isinstance(rows, list):
        return None
    values = [as_float(item.get("percent_variance_contribution")) for item in rows if isinstance(item, dict)]
    clean = [abs(value) for value in values if value is not None]
    return max(clean) if clean else None


def max_sign_flip_rate(data: dict[str, Any]) -> float | None:
    rows = data.get("weight_summary")
    if not isinstance(rows, list):
        return None
    values = [as_float(item.get("sign_flip_rate")) for item in rows if isinstance(item, dict)]
    clean = [value for value in values if value is not None]
    return max(clean) if clean else None


def evaluate_report(
    data: Any, source: str, report_type: str, args: argparse.Namespace
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not isinstance(data, dict):
        return [finding("blocker", "json_object", "Report JSON root must be an object.", source)]

    if report_type == "execution_timing_audit":
        top = data.get("top_findings")
        if isinstance(top, list):
            for item in top[:10]:
                if isinstance(item, dict):
                    severity = str(item.get("severity", "warning"))
                    check = str(item.get("check", "execution_timing_audit"))
                    detail = str(item.get("detail", "Execution timing audit finding."))
                    metric = item.get("metric")
                    threshold = item.get("threshold")
                    if severity in {"blocker", "warning"}:
                        findings.append(finding(severity, check, detail, source, metric, threshold))
        if not findings:
            blockers = as_int(data.get("blocker_count")) or 0
            warnings = as_int(data.get("warning_count")) or 0
            if blockers > 0:
                findings.append(
                    finding(
                        "blocker",
                        "execution_timing_blockers",
                        "Execution timing audit has blocker findings.",
                        source,
                        blockers,
                        0,
                    )
                )
            if warnings > 0:
                findings.append(
                    finding(
                        "warning",
                        "execution_timing_warnings",
                        "Execution timing audit has warning findings.",
                        source,
                        warnings,
                        0,
                    )
                )
    elif report_type == "tradability_audit":
        top = data.get("top_findings")
        if isinstance(top, list):
            for item in top[:10]:
                if isinstance(item, dict):
                    severity = str(item.get("severity", "warning"))
                    check = str(item.get("check", "tradability_audit"))
                    detail = str(item.get("detail", "Tradability audit finding."))
                    metric = item.get("metric")
                    threshold = item.get("threshold")
                    if severity in {"blocker", "warning"}:
                        findings.append(finding(severity, check, detail, source, metric, threshold))
        if not findings:
            blockers = as_int(data.get("blocker_count")) or 0
            warnings = as_int(data.get("warning_count")) or 0
            if blockers > 0:
                findings.append(
                    finding(
                        "blocker",
                        "tradability_blockers",
                        "Tradability audit has blocker findings.",
                        source,
                        blockers,
                        0,
                    )
                )
            if warnings > 0:
                findings.append(
                    finding(
                        "warning",
                        "tradability_warnings",
                        "Tradability audit has warning findings.",
                        source,
                        warnings,
                        0,
                    )
                )
    elif report_type == "portfolio_backtest":
        check_min(
            findings,
            as_float(data.get("periods_used")),
            args.min_periods,
            "blocker",
            "backtest_sample",
            source,
            "Missing backtest sample length.",
            "Too few portfolio backtest periods.",
        )
        check_min(
            findings,
            as_float(get_path(data, ("net_return_summary", "sharpe"))),
            args.min_net_sharpe,
            "warning",
            "net_sharpe",
            source,
            "Missing net Sharpe.",
            "Net Sharpe is below threshold.",
        )
        check_min(
            findings,
            as_float(get_path(data, ("net_return_summary", "annualized_return_geometric"))),
            args.min_net_annual_return,
            "warning",
            "net_return",
            source,
            "Missing net annualized return.",
            "Net annualized return is below threshold.",
        )
        drawdown = as_float(get_path(data, ("net_return_summary", "max_drawdown")))
        if drawdown is None:
            findings.append(
                finding(
                    "warning",
                    "net_drawdown",
                    "Missing net max drawdown.",
                    source,
                    None,
                    args.max_drawdown_abs,
                )
            )
        elif abs(drawdown) > args.max_drawdown_abs:
            findings.append(
                finding(
                    "warning",
                    "net_drawdown",
                    "Net max drawdown exceeds threshold.",
                    source,
                    drawdown,
                    args.max_drawdown_abs,
                )
            )
        check_max(
            findings,
            as_float(get_path(data, ("turnover_summary", "mean"))),
            args.max_turnover,
            "warning",
            "backtest_turnover",
            source,
            "Missing turnover mean.",
            "Backtest turnover is above threshold.",
        )
        check_max(
            findings,
            as_float(get_path(data, ("gross_exposure_summary", "max"))),
            args.max_gross_exposure,
            "blocker",
            "gross_exposure",
            source,
            "Missing gross exposure summary.",
            "Gross exposure exceeds threshold.",
        )
    elif report_type == "portfolio_constraints":
        failed = as_int(data.get("periods_failed"))
        if failed is None:
            findings.append(
                finding(
                    "warning",
                    "constraint_failures",
                    "Missing constraint failure count.",
                    source,
                    None,
                    args.max_constraint_failures,
                )
            )
        elif failed > args.max_constraint_failures:
            findings.append(
                finding(
                    "blocker",
                    "constraint_failures",
                    "Portfolio constraint violations exceed allowed count.",
                    source,
                    failed,
                    args.max_constraint_failures,
                )
            )
        dropped = as_int(data.get("rows_dropped"))
        if dropped and dropped > 0:
            findings.append(
                finding(
                    "warning", "constraint_rows_dropped", "Constraint report dropped rows.", source, dropped
                )
            )
    elif report_type == "portfolio_exposure":
        check_min(
            findings,
            as_float(data.get("periods_used")),
            args.min_periods,
            "warning",
            "exposure_sample",
            source,
            "Missing exposure sample length.",
            "Too few exposure periods.",
        )
        check_max(
            findings,
            as_float(get_path(data, ("exposure_summary", "gross_exposure", "max"))),
            args.max_gross_exposure,
            "blocker",
            "exposure_gross",
            source,
            "Missing gross exposure summary.",
            "Gross exposure exceeds threshold.",
        )
        check_abs_max(
            findings,
            max_abs_summary(get_path(data, ("exposure_summary", "net_exposure"))),
            args.max_abs_net_exposure,
            "blocker",
            "net_exposure",
            source,
            "Missing net exposure summary.",
            "Net exposure exceeds threshold.",
        )
        check_max(
            findings,
            as_float(get_path(data, ("exposure_summary", "concentration_hhi", "max"))),
            args.max_concentration_hhi,
            "warning",
            "concentration_hhi",
            source,
            "Missing concentration HHI.",
            "Concentration HHI exceeds threshold.",
        )
        if args.max_numeric_exposure_abs is not None:
            for item in data.get("numeric_exposure_summary", []):
                if isinstance(item, dict):
                    value = max_abs_summary(item)
                    if value is not None and value > args.max_numeric_exposure_abs:
                        findings.append(
                            finding(
                                "warning",
                                "numeric_exposure",
                                f"Numeric exposure {item.get('name')} exceeds absolute threshold.",
                                source,
                                value,
                                args.max_numeric_exposure_abs,
                            )
                        )
        if args.max_category_abs_exposure is not None:
            value = max_abs_category_exposure(data.get("latest"))
            if value is not None and value > args.max_category_abs_exposure:
                findings.append(
                    finding(
                        "warning",
                        "category_exposure",
                        "Latest category exposure exceeds absolute threshold.",
                        source,
                        value,
                        args.max_category_abs_exposure,
                    )
                )
    elif report_type == "risk_contribution":
        check_max(
            findings,
            as_float(data.get("annualized_portfolio_volatility")),
            args.max_annualized_volatility,
            "warning",
            "portfolio_volatility",
            source,
            "Missing annualized portfolio volatility.",
            "Annualized portfolio volatility exceeds threshold.",
        )
        check_max(
            findings,
            top_risk_share(data),
            args.max_single_asset_risk_share,
            "blocker",
            "risk_concentration",
            source,
            "Missing risk contribution concentration.",
            "Single asset risk contribution exceeds threshold.",
        )
    elif report_type == "optimizer_sensitivity":
        check_max(
            findings,
            as_float(get_path(data, ("l1_distance_summary", "mean"))),
            args.max_optimizer_l1_distance,
            "warning",
            "optimizer_l1_distance",
            source,
            "Missing optimizer L1 distance.",
            "Optimized weights are too sensitive to input perturbations.",
        )
        check_max(
            findings,
            max_sign_flip_rate(data),
            args.max_sign_flip_rate,
            "warning",
            "optimizer_sign_flip",
            source,
            "Missing optimizer sign flip rate.",
            "Optimized weights have high sign-flip sensitivity.",
        )
        check_max(
            findings,
            as_float(get_path(data, ("concentration_hhi_summary", "mean"))),
            args.max_concentration_hhi,
            "warning",
            "optimizer_concentration",
            source,
            "Missing optimizer concentration.",
            "Optimizer concentration exceeds threshold.",
        )
    elif report_type == "transaction_cost":
        check_max(
            findings,
            as_float(data.get("mean_cost_bps_per_period")),
            args.max_cost_bps,
            "blocker",
            "cost_bps",
            source,
            "Missing mean cost bps per period.",
            "Mean implementation cost exceeds threshold.",
        )
        check_max(
            findings,
            as_float(get_path(data, ("max_adv_participation_summary", "max"))),
            args.max_adv_participation,
            "warning",
            "adv_participation",
            source,
            "Missing ADV participation; capacity evidence may be incomplete.",
            "ADV participation exceeds threshold.",
        )
    elif report_type == "capacity":
        check_max(
            findings,
            as_float(get_path(data, ("participation_summary", "max"))),
            args.max_adv_participation,
            "blocker",
            "adv_participation",
            source,
            "Missing max ADV participation.",
            "ADV participation exceeds threshold.",
        )
        check_max(
            findings,
            as_float(get_path(data, ("cost_bps_summary", "mean"))),
            args.max_cost_bps,
            "blocker",
            "capacity_cost_bps",
            source,
            "Missing capacity cost bps.",
            "Estimated capacity cost exceeds threshold.",
        )
        if args.min_binding_capacity is not None:
            check_min(
                findings,
                as_float(get_path(data, ("binding_capacity_summary", "min"))),
                args.min_binding_capacity,
                "blocker",
                "binding_capacity",
                source,
                "Missing binding capacity estimate.",
                "Binding NAV capacity is below required minimum.",
            )
    elif report_type == "alpha_research_gate":
        decision = str(data.get("gate_decision", "")).lower()
        if decision == "fail":
            findings.append(
                finding(
                    "blocker",
                    "alpha_research_gate",
                    "Alpha research gate failed before portfolio construction.",
                    source,
                    decision,
                )
            )
        elif decision == "review":
            findings.append(
                finding(
                    "warning",
                    "alpha_research_gate",
                    "Alpha research gate still requires review before portfolio construction.",
                    source,
                    decision,
                )
            )
    return findings


def build_report(paths: list[Path], args: argparse.Namespace) -> dict[str, Any]:
    reports = []
    all_findings: list[dict[str, Any]] = []
    present_types: set[str] = set()

    for path in paths:
        data = load_json(path)
        report_type = infer_report_type(data, path)
        present_types.add(report_type)
        present_types.add(type_alias(report_type))
        findings = evaluate_report(data, path.name, report_type, args)
        all_findings.extend(findings)
        reports.append(
            {
                "path": str(path),
                "name": path.name,
                "type": report_type,
                "alias": type_alias(report_type),
                "key_metrics": report_key_metrics(data, report_type),
                "finding_count": len(findings),
                "findings": findings,
            }
        )

    required = [item.strip() for item in args.required_types.split(",") if item.strip()]
    missing = [item for item in required if item not in present_types]
    for item in missing:
        severity = "blocker" if args.strict_missing else "warning"
        all_findings.append(
            finding(
                severity,
                "missing_required_diagnostic",
                f"Required diagnostic type is missing: {item}.",
                "gate",
                item,
            )
        )

    blocker_count = sum(1 for item in all_findings if item["severity"] == "blocker")
    warning_count = sum(1 for item in all_findings if item["severity"] == "warning")
    gate_decision = "fail" if blocker_count else ("review" if warning_count else "pass")
    ranked_findings = sorted(
        all_findings,
        key=lambda item: (severity_rank(item["severity"]), item["check"], item["source"]),
        reverse=True,
    )

    return {
        "gate": "portfolio_construction",
        "decision": gate_decision,
        "gate_decision": gate_decision,
        "report_count": len(reports),
        "required_types": required,
        "present_types": sorted(present_types),
        "missing_required_types": missing,
        "blocker_count": blocker_count,
        "warning_count": warning_count,
        "finding_count": len(all_findings),
        "thresholds": {
            "min_periods": args.min_periods,
            "min_net_sharpe": args.min_net_sharpe,
            "min_net_annual_return": args.min_net_annual_return,
            "max_drawdown_abs": args.max_drawdown_abs,
            "max_turnover": args.max_turnover,
            "max_gross_exposure": args.max_gross_exposure,
            "max_abs_net_exposure": args.max_abs_net_exposure,
            "max_constraint_failures": args.max_constraint_failures,
            "max_concentration_hhi": args.max_concentration_hhi,
            "max_numeric_exposure_abs": args.max_numeric_exposure_abs,
            "max_category_abs_exposure": args.max_category_abs_exposure,
            "max_annualized_volatility": args.max_annualized_volatility,
            "max_single_asset_risk_share": args.max_single_asset_risk_share,
            "max_optimizer_l1_distance": args.max_optimizer_l1_distance,
            "max_sign_flip_rate": args.max_sign_flip_rate,
            "max_cost_bps": args.max_cost_bps,
            "max_adv_participation": args.max_adv_participation,
            "min_binding_capacity": args.min_binding_capacity,
        },
        "blockers": [item for item in ranked_findings if item["severity"] == "blocker"],
        "warnings": [item for item in ranked_findings if item["severity"] == "warning"],
        "evidence_gaps": [item for item in ranked_findings if item["check"] == "missing_required_diagnostic"],
        "top_findings": ranked_findings,
        "reports": reports,
        "notes": [
            "This is a portfolio-construction gate, not a replacement for alpha research review or production go-live approval.",
            "Required diagnostic types and thresholds should be set before reviewing the candidate portfolio.",
            "A pass means the supplied diagnostics did not trigger this gate; execution readiness, owners, monitoring, and live controls still need separate approval.",
        ],
    }


def md_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Portfolio Construction Gate Report",
        "",
        f"- Gate decision: {report['gate_decision']}",
        f"- Reports reviewed: {report['report_count']}",
        f"- Blockers: {report['blocker_count']}",
        f"- Warnings: {report['warning_count']}",
        f"- Missing required diagnostics: {', '.join(report['missing_required_types']) or 'None'}",
        "",
        "## Reports",
        "",
        "| Report | Type | Key metrics | Findings |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["reports"]:
        metrics = ", ".join(f"{key}={value}" for key, value in item["key_metrics"].items())
        lines.append(
            f"| {md_escape(item['name'])} | {md_escape(item['type'])} | {md_escape(metrics)} | {item['finding_count']} |"
        )

    lines.extend(
        [
            "",
            "## Findings",
            "",
            "| Severity | Check | Source | Metric | Threshold | Detail |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in report["top_findings"]:
        lines.append(
            f"| {md_escape(item['severity'])} | {md_escape(item['check'])} | {md_escape(item['source'])} | {md_escape(item.get('metric'))} | {md_escape(item.get('threshold'))} | {md_escape(item['detail'])} |"
        )

    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gate portfolio construction using bundled quant JSON diagnostics."
    )
    parser.add_argument("json_paths", nargs="+", type=Path)
    parser.add_argument(
        "--required-types",
        default=",".join(DEFAULT_REQUIRED_TYPES),
        help="Comma-separated required diagnostic type aliases.",
    )
    parser.add_argument(
        "--strict-missing",
        action="store_true",
        help="Treat missing required diagnostics as blockers instead of warnings.",
    )
    parser.add_argument("--min-periods", type=int, default=20)
    parser.add_argument("--min-net-sharpe", type=float, default=0.5)
    parser.add_argument("--min-net-annual-return", type=float, default=0.0)
    parser.add_argument("--max-drawdown-abs", type=float, default=0.2)
    parser.add_argument("--max-turnover", type=float, default=0.5)
    parser.add_argument("--max-gross-exposure", type=float, default=1.5)
    parser.add_argument("--max-abs-net-exposure", type=float, default=0.2)
    parser.add_argument("--max-constraint-failures", type=int, default=0)
    parser.add_argument("--max-concentration-hhi", type=float, default=0.15)
    parser.add_argument("--max-numeric-exposure-abs", type=float)
    parser.add_argument("--max-category-abs-exposure", type=float)
    parser.add_argument("--max-annualized-volatility", type=float, default=0.25)
    parser.add_argument("--max-single-asset-risk-share", type=float, default=0.35)
    parser.add_argument("--max-optimizer-l1-distance", type=float, default=0.5)
    parser.add_argument("--max-sign-flip-rate", type=float, default=0.2)
    parser.add_argument("--max-cost-bps", type=float, default=25.0)
    parser.add_argument("--max-adv-participation", type=float, default=0.1)
    parser.add_argument("--min-binding-capacity", type=float)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.min_periods < 1:
        raise SystemExit("--min-periods must be positive.")
    for name in [
        "max_drawdown_abs",
        "max_turnover",
        "max_abs_net_exposure",
        "max_concentration_hhi",
        "max_single_asset_risk_share",
        "max_sign_flip_rate",
        "max_adv_participation",
    ]:
        value = getattr(args, name)
        if value < 0 or value > 1:
            raise SystemExit(f"--{name.replace('_', '-')} must be in [0, 1].")
    if args.max_gross_exposure <= 0:
        raise SystemExit("--max-gross-exposure must be positive.")
    if args.max_constraint_failures < 0:
        raise SystemExit("--max-constraint-failures must be non-negative.")
    if args.max_cost_bps < 0 or args.max_optimizer_l1_distance < 0 or args.max_annualized_volatility < 0:
        raise SystemExit(
            "--max-cost-bps, --max-optimizer-l1-distance, and --max-annualized-volatility must be non-negative."
        )

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
