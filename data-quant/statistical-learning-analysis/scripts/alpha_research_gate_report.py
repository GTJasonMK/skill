#!/usr/bin/env python3
"""Gate a candidate alpha research package using bundled JSON diagnostics.

Standard-library only. This script consumes JSON reports from the bundled
experiment-audit, factor, overlap, incremental-alpha, cost, capacity, backtest,
and multiple-testing diagnostics, then applies research-stage promotion checks.
Use it before moving a candidate signal into paper trading, portfolio
construction, or a larger alpha library.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_REQUIRED_TYPES = [
    "point_in_time_audit",
    "execution_timing_audit",
    "tradability_audit",
    "experiment_audit",
    "factor_ic",
    "incremental_alpha",
    "signal_overlap",
    "turnover",
    "cost_or_capacity",
    "multiple_testing",
]


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out


def as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_path(data: Any, path: tuple[str, ...]) -> Any:
    current = data
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def infer_report_type(data: Any, path: Path) -> str:
    if not isinstance(data, dict):
        return "unknown"
    declared_type = data.get("artifact_type") or data.get("diagnostic_type")
    if isinstance(declared_type, str) and declared_type:
        return declared_type
    if data.get("audit_type") == "point_in_time_audit":
        return "point_in_time_audit"
    if data.get("audit_type") == "execution_timing_audit":
        return "execution_timing_audit"
    if data.get("audit_type") == "tradability_audit":
        return "tradability_audit"
    if data.get("audit_type") == "quant_experiment_audit":
        return "experiment_audit"
    if "residual_rank_ic_summary" in data and "candidate_explained_by_base_r2_summary" in data:
        return "incremental_alpha"
    if "rank_ic_summary" in data and "ic_summary" in data and "factor_col" in data:
        return "factor_ic"
    if "horizons" in data and "forward_return_cols" in data:
        return "factor_decay"
    if "redundant_pair_count" in data and "pair_summary" in data:
        return "signal_overlap"
    if "turnover_summary" in data and "membership_overlap_summary" in data:
        return "turnover"
    if "total_cost_summary" in data and "mean_cost_bps_per_period" in data:
        return "transaction_cost"
    if "cost_bps_summary" in data and "binding_capacity_summary" in data:
        return "capacity"
    if "discoveries" in data and "tests_used" in data:
        return "multiple_testing"
    if "reality_check_p_value_mean" in data or "reality_check_p_value_t_stat" in data:
        return "bootstrap_reality_check"
    if "net_return_summary" in data and "gross_return_summary" in data and "turnover_summary" in data:
        return "long_short_backtest"
    if "gate_decision" in data:
        return "gate_or_limit"
    return path.stem


def type_alias(report_type: str) -> str:
    if report_type in {"transaction_cost", "capacity"}:
        return "cost_or_capacity"
    if report_type in {"multiple_testing", "bootstrap_reality_check"}:
        return "multiple_testing"
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


def report_key_metrics(data: Any, report_type: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    paths: list[tuple[str, tuple[str, ...]]] = []
    if report_type == "point_in_time_audit":
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
        ]
    elif report_type == "execution_timing_audit":
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
    elif report_type == "experiment_audit":
        paths = [
            ("experiment_count", ("experiment_count",)),
            ("family_count", ("family_count",)),
            ("selected_count", ("selected_count",)),
            ("failed_count", ("failed_count",)),
            ("predeclared_missing_or_false_count", ("predeclared_missing_or_false_count",)),
            ("selected_missing_final_test_count", ("selected_missing_final_test_count",)),
            ("blocker_count", ("blocker_count",)),
            ("warning_count", ("warning_count",)),
        ]
    elif report_type == "factor_ic":
        paths = [
            ("periods_used", ("periods_used",)),
            ("rank_ic_mean", ("rank_ic_summary", "mean")),
            ("rank_ic_t_stat", ("rank_ic_summary", "t_stat")),
            ("rank_ic_positive_rate", ("rank_ic_summary", "positive_rate")),
        ]
    elif report_type == "incremental_alpha":
        paths = [
            ("dates_used", ("dates_used",)),
            ("assessment", ("assessment",)),
            ("residual_rank_ic_mean", ("residual_rank_ic_summary", "mean")),
            ("residual_rank_ic_positive_rate", ("residual_rank_ic_summary", "positive_rate")),
            ("delta_r2_mean", ("delta_r2_summary", "mean")),
            ("candidate_base_r2_mean", ("candidate_explained_by_base_r2_summary", "mean")),
        ]
    elif report_type == "signal_overlap":
        paths = [
            ("pair_count", ("pair_count",)),
            ("redundant_pair_count", ("redundant_pair_count",)),
        ]
    elif report_type == "turnover":
        paths = [
            ("periods_used", ("periods_used",)),
            ("turnover_mean", ("turnover_summary", "mean")),
            ("rank_autocorrelation_mean", ("rank_autocorrelation_summary", "mean")),
        ]
    elif report_type == "transaction_cost":
        paths = [
            ("periods_used", ("periods_used",)),
            ("mean_cost_bps_per_period", ("mean_cost_bps_per_period",)),
            ("turnover_mean", ("turnover_summary", "mean")),
        ]
    elif report_type == "capacity":
        paths = [
            ("periods_used", ("periods_used",)),
            ("max_participation_mean", ("participation_summary", "mean")),
            ("max_participation_max", ("participation_summary", "max")),
            ("cost_bps_mean", ("cost_bps_summary", "mean")),
            ("binding_capacity_min", ("binding_capacity_summary", "min")),
        ]
    elif report_type == "multiple_testing":
        paths = [
            ("tests_used", ("tests_used",)),
            ("raw_discoveries", ("discoveries", "raw")),
            ("bh_fdr_discoveries", ("discoveries", "bh_fdr")),
        ]
    elif report_type == "bootstrap_reality_check":
        paths = [
            ("observations_used", ("observations_used",)),
            ("reality_check_p_value_mean", ("reality_check_p_value_mean",)),
            ("reality_check_p_value_t_stat", ("reality_check_p_value_t_stat",)),
        ]
    elif report_type == "long_short_backtest":
        paths = [
            ("periods_used", ("periods_used",)),
            ("net_sharpe", ("net_return_summary", "sharpe")),
            ("net_annualized_return", ("net_return_summary", "annualized_return_geometric")),
            ("net_max_drawdown", ("net_return_summary", "max_drawdown")),
            ("turnover_mean", ("turnover_summary", "mean")),
        ]
    metrics = {}
    for name, path in paths:
        value = get_path(data, path)
        if value is not None:
            metrics[name] = value
    return metrics


def evaluate_report(
    data: Any, source: str, report_type: str, args: argparse.Namespace
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not isinstance(data, dict):
        return [finding("blocker", "json_object", "Report JSON root must be an object.", source)]

    if report_type == "point_in_time_audit":
        top = data.get("top_findings")
        if isinstance(top, list):
            for item in top[:10]:
                if isinstance(item, dict):
                    severity = str(item.get("severity", "warning"))
                    check = str(item.get("check", "point_in_time_audit"))
                    detail = str(item.get("detail", "Point-in-time audit finding."))
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
                        "point_in_time_blockers",
                        "Point-in-time audit has blocker findings.",
                        source,
                        blockers,
                        0,
                    )
                )
            if warnings > 0:
                findings.append(
                    finding(
                        "warning",
                        "point_in_time_warnings",
                        "Point-in-time audit has warning findings.",
                        source,
                        warnings,
                        0,
                    )
                )
    elif report_type == "execution_timing_audit":
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
    elif report_type == "experiment_audit":
        top = data.get("top_findings")
        if isinstance(top, list):
            for item in top[:10]:
                if isinstance(item, dict):
                    severity = str(item.get("severity", "warning"))
                    check = str(item.get("check", "experiment_audit"))
                    detail = str(item.get("detail", "Experiment audit finding."))
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
                        "experiment_audit_blockers",
                        "Experiment audit has blocker findings.",
                        source,
                        blockers,
                        0,
                    )
                )
            if warnings > 0:
                findings.append(
                    finding(
                        "warning",
                        "experiment_audit_warnings",
                        "Experiment audit has warning findings.",
                        source,
                        warnings,
                        0,
                    )
                )
    elif report_type == "factor_ic":
        check_min(
            findings,
            as_float(get_path(data, ("periods_used",))),
            args.min_dates,
            "blocker",
            "factor_ic_sample",
            source,
            "Missing IC sample length.",
            "Too few IC periods for research gate.",
        )
        check_min(
            findings,
            as_float(get_path(data, ("rank_ic_summary", "mean"))),
            args.min_rank_ic_mean,
            "blocker",
            "rank_ic_mean",
            source,
            "Missing rank IC mean.",
            "Rank IC mean is below threshold.",
        )
        check_min(
            findings,
            as_float(get_path(data, ("rank_ic_summary", "positive_rate"))),
            args.min_rank_ic_positive_rate,
            "warning",
            "rank_ic_positive_rate",
            source,
            "Missing rank IC positive rate.",
            "Rank IC positive rate is weak.",
        )
        check_min(
            findings,
            as_float(get_path(data, ("rank_ic_summary", "t_stat"))),
            args.min_rank_ic_t_stat,
            "warning",
            "rank_ic_t_stat",
            source,
            "Missing rank IC t-stat.",
            "Rank IC t-stat is weak.",
        )
    elif report_type == "incremental_alpha":
        assessment = str(data.get("assessment", ""))
        check_min(
            findings,
            as_float(get_path(data, ("dates_used",))),
            args.min_dates,
            "blocker",
            "incremental_sample",
            source,
            "Missing incremental-alpha sample length.",
            "Too few incremental-alpha dates for research gate.",
        )
        check_min(
            findings,
            as_float(get_path(data, ("residual_rank_ic_summary", "mean"))),
            args.min_residual_rank_ic_mean,
            "blocker",
            "residual_rank_ic_mean",
            source,
            "Missing residual rank IC mean.",
            "Residual rank IC mean is below threshold.",
        )
        check_min(
            findings,
            as_float(get_path(data, ("residual_rank_ic_summary", "positive_rate"))),
            args.min_residual_positive_rate,
            "warning",
            "residual_rank_ic_positive_rate",
            source,
            "Missing residual rank IC positive rate.",
            "Residual rank IC positive rate is weak.",
        )
        if assessment in {
            "weak_or_negative_incremental_evidence",
            "insufficient_signal_variation",
            "insufficient_dates",
        }:
            findings.append(
                finding(
                    "blocker",
                    "incremental_assessment",
                    "Incremental alpha assessment does not support promotion.",
                    source,
                    assessment,
                )
            )
        check_max(
            findings,
            as_float(get_path(data, ("candidate_explained_by_base_r2_summary", "mean"))),
            args.max_candidate_base_r2,
            "warning",
            "candidate_spanned_by_base",
            source,
            "Missing candidate-spanned-by-base R-squared.",
            "Candidate is highly explained by existing signals or exposures.",
        )
    elif report_type == "signal_overlap":
        redundant = as_int(data.get("redundant_pair_count"))
        if redundant is None:
            findings.append(
                finding("warning", "signal_overlap_redundancy", "Missing redundant pair count.", source)
            )
        elif redundant > args.max_redundant_pairs:
            severity = "blocker" if args.fail_on_redundant_pairs else "warning"
            findings.append(
                finding(
                    severity,
                    "signal_overlap_redundancy",
                    "Too many redundant signal pairs.",
                    source,
                    redundant,
                    args.max_redundant_pairs,
                )
            )
    elif report_type == "turnover":
        check_max(
            findings,
            as_float(get_path(data, ("turnover_summary", "mean"))),
            args.max_turnover,
            "warning",
            "turnover_mean",
            source,
            "Missing turnover mean.",
            "Turnover is above research gate threshold.",
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
            "Mean implementation cost is above threshold.",
        )
        check_max(
            findings,
            as_float(get_path(data, ("max_adv_participation_summary", "max"))),
            args.max_adv_participation,
            "warning",
            "adv_participation",
            source,
            "Missing ADV participation; capacity evidence may be incomplete.",
            "ADV participation is above threshold.",
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
            "ADV participation is above threshold.",
        )
        check_max(
            findings,
            as_float(get_path(data, ("cost_bps_summary", "mean"))),
            args.max_cost_bps,
            "blocker",
            "capacity_cost_bps",
            source,
            "Missing capacity cost bps.",
            "Estimated capacity cost is above threshold.",
        )
        min_capacity = as_float(get_path(data, ("binding_capacity_summary", "min")))
        if args.min_binding_capacity is not None:
            check_min(
                findings,
                min_capacity,
                args.min_binding_capacity,
                "blocker",
                "binding_capacity",
                source,
                "Missing binding capacity estimate.",
                "Binding NAV capacity is below required minimum.",
            )
    elif report_type == "multiple_testing":
        raw = as_int(get_path(data, ("discoveries", "raw"))) or 0
        bh = as_int(get_path(data, ("discoveries", "bh_fdr"))) or 0
        if raw > 0 and bh <= 0:
            findings.append(
                finding(
                    "blocker",
                    "multiple_testing",
                    "Raw discoveries do not survive Benjamini-Hochberg FDR.",
                    source,
                    {"raw": raw, "bh_fdr": bh},
                )
            )
        if as_int(data.get("tests_used")) is None:
            findings.append(
                finding("warning", "multiple_testing_scope", "Missing tested family size.", source)
            )
    elif report_type == "bootstrap_reality_check":
        p_mean = as_float(data.get("reality_check_p_value_mean"))
        p_t = as_float(data.get("reality_check_p_value_t_stat"))
        p_best = p_t if p_t is not None else p_mean
        check_max(
            findings,
            p_best,
            args.max_reality_check_p_value,
            "blocker",
            "reality_check_p_value",
            source,
            "Missing reality-check p-value.",
            "Reality-check p-value is too high after strategy search.",
        )
    elif report_type == "long_short_backtest":
        check_min(
            findings,
            as_float(get_path(data, ("periods_used",))),
            args.min_dates,
            "blocker",
            "backtest_sample",
            source,
            "Missing backtest sample length.",
            "Too few backtest periods for research gate.",
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
        check_max(
            findings,
            as_float(get_path(data, ("turnover_summary", "mean"))),
            args.max_turnover,
            "warning",
            "backtest_turnover",
            source,
            "Missing backtest turnover.",
            "Backtest turnover is above threshold.",
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
        "gate": "alpha_research",
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
            "min_dates": args.min_dates,
            "min_rank_ic_mean": args.min_rank_ic_mean,
            "min_rank_ic_positive_rate": args.min_rank_ic_positive_rate,
            "min_rank_ic_t_stat": args.min_rank_ic_t_stat,
            "min_residual_rank_ic_mean": args.min_residual_rank_ic_mean,
            "min_residual_positive_rate": args.min_residual_positive_rate,
            "max_candidate_base_r2": args.max_candidate_base_r2,
            "max_redundant_pairs": args.max_redundant_pairs,
            "max_turnover": args.max_turnover,
            "max_cost_bps": args.max_cost_bps,
            "max_adv_participation": args.max_adv_participation,
            "min_binding_capacity": args.min_binding_capacity,
            "max_reality_check_p_value": args.max_reality_check_p_value,
            "min_net_sharpe": args.min_net_sharpe,
            "min_net_annual_return": args.min_net_annual_return,
        },
        "blockers": [item for item in ranked_findings if item["severity"] == "blocker"],
        "warnings": [item for item in ranked_findings if item["severity"] == "warning"],
        "evidence_gaps": [item for item in ranked_findings if item["check"] == "missing_required_diagnostic"],
        "top_findings": ranked_findings,
        "reports": reports,
        "notes": [
            "This is a research-stage gate for candidate alpha promotion, not a production go-live approval.",
            "Required diagnostic types and the experiment registry should be predeclared "
            "before reviewing results; missing diagnostics are evidence gaps.",
            "Passing this gate does not remove the need for point-in-time data review, "
            "implementation-cost calibration, risk-owner approval, and out-of-sample monitoring.",
        ],
    }


def md_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Alpha Research Gate Report",
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
            f"| {md_escape(item['name'])} | {md_escape(item['type'])} | "
            f"{md_escape(metrics)} | {item['finding_count']} |"
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
            f"| {md_escape(item['severity'])} | {md_escape(item['check'])} | "
            f"{md_escape(item['source'])} | {md_escape(item.get('metric'))} | "
            f"{md_escape(item.get('threshold'))} | {md_escape(item['detail'])} |"
        )

    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gate candidate alpha research using bundled quant JSON diagnostics."
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
    parser.add_argument("--min-dates", type=int, default=20)
    parser.add_argument("--min-rank-ic-mean", type=float, default=0.02)
    parser.add_argument("--min-rank-ic-positive-rate", type=float, default=0.55)
    parser.add_argument("--min-rank-ic-t-stat", type=float, default=2.0)
    parser.add_argument("--min-residual-rank-ic-mean", type=float, default=0.01)
    parser.add_argument("--min-residual-positive-rate", type=float, default=0.55)
    parser.add_argument("--max-candidate-base-r2", type=float, default=0.8)
    parser.add_argument("--max-redundant-pairs", type=int, default=0)
    parser.add_argument("--fail-on-redundant-pairs", action="store_true")
    parser.add_argument("--max-turnover", type=float, default=0.5)
    parser.add_argument("--max-cost-bps", type=float, default=25.0)
    parser.add_argument("--max-adv-participation", type=float, default=0.1)
    parser.add_argument("--min-binding-capacity", type=float)
    parser.add_argument("--max-reality-check-p-value", type=float, default=0.1)
    parser.add_argument("--min-net-sharpe", type=float, default=0.5)
    parser.add_argument("--min-net-annual-return", type=float, default=0.0)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    if args.min_dates < 1:
        raise SystemExit("--min-dates must be positive.")
    for name in [
        "min_rank_ic_positive_rate",
        "min_residual_positive_rate",
        "max_candidate_base_r2",
        "max_adv_participation",
        "max_reality_check_p_value",
    ]:
        value = getattr(args, name)
        if value < 0 or value > 1:
            raise SystemExit(f"--{name.replace('_', '-')} must be in [0, 1].")
    if args.max_redundant_pairs < 0:
        raise SystemExit("--max-redundant-pairs must be non-negative.")
    if args.max_turnover < 0 or args.max_cost_bps < 0:
        raise SystemExit("--max-turnover and --max-cost-bps must be non-negative.")

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
