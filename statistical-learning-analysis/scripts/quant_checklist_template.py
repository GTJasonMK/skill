#!/usr/bin/env python3
"""Generate default quant go-live, monitoring, or retirement checklists.

Standard-library only. Writes CSV, JSON, or Markdown templates that can be
filled in and passed to go_live_gate_report.py or strategy_action_decision.py.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


TEMPLATES: dict[str, list[dict[str, str]]] = {
    "go-live": [
        {"category": "data", "check": "Point-in-time data availability verified", "severity": "critical", "status": "missing", "owner": "data", "evidence": "", "notes": "Confirm report dates, vendor timestamps, restatements, and index membership timing."},
        {"category": "data", "check": "Survivorship and delisting handling documented", "severity": "critical", "status": "missing", "owner": "data", "evidence": "", "notes": "Include delisted assets and historical universe membership."},
        {"category": "signal", "check": "Signal definition frozen and versioned", "severity": "critical", "status": "missing", "owner": "research", "evidence": "", "notes": "Record code hash, formula, universe, rebalance schedule, and lag convention."},
        {"category": "signal", "check": "Multiple-testing and data-snooping review completed", "severity": "high", "status": "missing", "owner": "research", "evidence": "", "notes": "Include failed variants, p-value/FDR checks, or reality-check diagnostics."},
        {"category": "portfolio", "check": "Portfolio constraints checked before performance evaluation", "severity": "high", "status": "missing", "owner": "portfolio", "evidence": "", "notes": "Gross/net, single-name, sector/category, turnover, shorting, and leverage constraints."},
        {"category": "costs", "check": "Transaction cost and capacity assumptions documented", "severity": "high", "status": "missing", "owner": "trading", "evidence": "", "notes": "Commission, spread, slippage, borrow, financing, impact, ADV participation."},
        {"category": "risk", "check": "Risk model and forecast calibration reviewed", "severity": "high", "status": "missing", "owner": "risk", "evidence": "", "notes": "Volatility, VaR/ES breaches, stress scenarios, factor exposure, risk contribution."},
        {"category": "execution", "check": "Order generation, fill handling, and kill switch tested", "severity": "critical", "status": "missing", "owner": "ops", "evidence": "", "notes": "Include rejected/partial fills, stale data freeze, and manual override path."},
        {"category": "monitoring", "check": "Live-vs-paper, signal health, limits, and data freshness monitors configured", "severity": "critical", "status": "missing", "owner": "ops", "evidence": "", "notes": "Define alert thresholds and escalation owners before first live order."},
        {"category": "governance", "check": "Rollback and retirement criteria predeclared", "severity": "high", "status": "missing", "owner": "pm", "evidence": "", "notes": "Define reduce/pause/retire triggers and capital scaling rules."},
    ],
    "monitoring": [
        {"category": "data", "check": "Data freshness within tolerance", "severity": "critical", "status": "missing", "owner": "data", "evidence": "", "notes": "Run data_freshness_report.py before signal generation."},
        {"category": "signal", "check": "Recent rank IC and top-bottom spread within expected range", "severity": "high", "status": "missing", "owner": "research", "evidence": "", "notes": "Run signal_health_monitor.py and compare with research baseline."},
        {"category": "portfolio", "check": "Portfolio constraints and exposure limits clear", "severity": "high", "status": "missing", "owner": "portfolio", "evidence": "", "notes": "Check concentration, gross/net, factor, category, and turnover limits."},
        {"category": "limits", "check": "No unresolved critical/high limit breach", "severity": "critical", "status": "missing", "owner": "risk", "evidence": "", "notes": "Run limit_breach_report.py and require sign-off for unresolved breaches."},
        {"category": "execution", "check": "Order exception rate and aggregate fill rate within tolerance", "severity": "high", "status": "missing", "owner": "trading", "evidence": "", "notes": "Run order_exception_report.py and review reason/venue clustering."},
        {"category": "execution", "check": "Realized slippage within live assumptions", "severity": "high", "status": "missing", "owner": "trading", "evidence": "", "notes": "Run execution_slippage_report.py and compare with cost model."},
        {"category": "risk", "check": "Risk forecast calibration and VaR breaches acceptable", "severity": "high", "status": "missing", "owner": "risk", "evidence": "", "notes": "Run risk_forecast_calibration.py and review breach clustering."},
        {"category": "performance", "check": "Live-vs-paper drift within tolerance", "severity": "high", "status": "missing", "owner": "pm", "evidence": "", "notes": "Run live_vs_paper_report.py with identical timing and return definitions."},
    ],
    "retirement": [
        {"category": "signal", "check": "Recent signal evidence below retirement threshold", "severity": "high", "status": "missing", "owner": "research", "evidence": "", "notes": "Rank IC, positive rate, spread, and coverage relative to predeclared baseline."},
        {"category": "performance", "check": "Live-vs-paper drift or drawdown exceeds retirement threshold", "severity": "high", "status": "missing", "owner": "pm", "evidence": "", "notes": "Separate market loss from implementation drift before retirement decision."},
        {"category": "costs", "check": "Costs or capacity invalidate expected economic value", "severity": "high", "status": "missing", "owner": "trading", "evidence": "", "notes": "Review slippage, spread, borrow, impact, and ADV participation."},
        {"category": "risk", "check": "Risk model, exposure, or stress behavior no longer matches mandate", "severity": "critical", "status": "missing", "owner": "risk", "evidence": "", "notes": "Include limit breaches, risk contribution, regime behavior, and tail losses."},
        {"category": "operations", "check": "Operational burden or data reliability no longer acceptable", "severity": "medium", "status": "missing", "owner": "ops", "evidence": "", "notes": "Track manual overrides, stale data, order exceptions, and incident count."},
        {"category": "decision", "check": "Capital action selected and owner sign-off recorded", "severity": "critical", "status": "missing", "owner": "pm", "evidence": "", "notes": "Choose maintain, review, reduce, pause, or retire with rollback conditions."},
    ],
}


def markdown(rows: list[dict[str, str]], template: str) -> str:
    lines = [
        f"# Quant {template.title()} Checklist",
        "",
        "| Category | Check | Severity | Status | Owner | Evidence | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| {row['category']} | {row['check']} | {row['severity']} | {row['status']} | {row['owner']} | {row['evidence']} | {row['notes']} |")
    return "\n".join(lines) + "\n"


def write_csv(rows: list[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["category", "check", "severity", "status", "owner", "evidence", "notes"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate default quant go-live, monitoring, or retirement checklists.")
    parser.add_argument("--template", choices=sorted(TEMPLATES), default="go-live")
    parser.add_argument("--format", choices=["csv", "json", "markdown"], default="csv")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows = TEMPLATES[args.template]
    if args.format == "csv":
        if args.output:
            write_csv(rows, args.output)
        else:
            import sys

            writer = csv.DictWriter(sys.stdout, fieldnames=["category", "check", "severity", "status", "owner", "evidence", "notes"])
            writer.writeheader()
            writer.writerows(rows)
    elif args.format == "json":
        text = json.dumps({"template": args.template, "checks": rows}, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    else:
        text = markdown(rows, args.template)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
