#!/usr/bin/env python3
"""Turn monitoring metrics into strategy action recommendations.

Standard-library only. Input is a CSV with metric names, observed values,
thresholds, direction, and action. The strongest triggered action wins.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from quant_utils import parse_float, read_dataframe, require_columns, sorted_group_keys

import pandas as pd


def _df_to_rows(df: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    header = list(df.columns)
    str_df = df.astype(object).where(df.notna(), "").astype(str)
    return header, str_df.to_dict("records")




ACTION_RANK = {
    "maintain": 0,
    "review": 1,
    "watch": 1,
    "reduce": 2,
    "de-risk": 2,
    "pause": 3,
    "freeze": 3,
    "stop": 3,
    "retire": 4,
}


def normalize_action(value: str) -> str:
    clean = value.strip().lower()
    return clean if clean in ACTION_RANK else "review"


def normalize_direction(value: str) -> str:
    clean = value.strip().lower().replace(" ", "_")
    aliases = {
        "upper": "upper",
        "<=": "upper",
        "max": "upper",
        "lower": "lower",
        ">=": "lower",
        "min": "lower",
        "abs_upper": "abs_upper",
        "absolute": "abs_upper",
        "abs": "abs_upper",
    }
    return aliases.get(clean, "upper")


def triggered(value: float, threshold: float, direction: str) -> bool:
    if direction == "upper":
        return value > threshold
    if direction == "lower":
        return value < threshold
    if direction == "abs_upper":
        return abs(value) > threshold
    return value > threshold


def margin(value: float, threshold: float, direction: str) -> float:
    if direction == "upper":
        return value - threshold
    if direction == "lower":
        return threshold - value
    if direction == "abs_upper":
        return abs(value) - threshold
    return value - threshold


def build_report(
    rows: list[dict[str, str]],
    metric_col: str,
    value_col: str,
    threshold_col: str,
    direction_col: str | None,
    action_col: str,
    category_col: str | None,
    reason_col: str | None,
    owner_col: str | None,
    default_action: str,
) -> dict[str, Any]:
    rules = []
    dropped = 0
    for i, row in enumerate(rows, start=1):
        metric = row.get(metric_col, "").strip()
        value = parse_float(row.get(value_col))
        threshold = parse_float(row.get(threshold_col))
        direction = normalize_direction(row.get(direction_col, "")) if direction_col else "upper"
        action = normalize_action(row.get(action_col, ""))
        category = row.get(category_col, "").strip() if category_col else ""
        reason = row.get(reason_col, "").strip() if reason_col else ""
        owner = row.get(owner_col, "").strip() if owner_col else ""
        if not metric or value is None or threshold is None:
            dropped += 1
            continue
        is_triggered = triggered(value, threshold, direction)
        breach_margin = margin(value, threshold, direction)
        rules.append(
            {
                "row_number": i,
                "metric": metric,
                "category": category,
                "value": value,
                "threshold": threshold,
                "direction": direction,
                "action": action,
                "action_rank": ACTION_RANK[action],
                "reason": reason,
                "owner": owner,
                "triggered": is_triggered,
                "margin": breach_margin,
                "margin_ratio": breach_margin / abs(threshold) if threshold != 0 else None,
            }
        )

    default_action = normalize_action(default_action)
    triggered_rules = [rule for rule in rules if rule["triggered"]]
    if triggered_rules:
        max_rank = max(rule["action_rank"] for rule in triggered_rules)
        strongest = [rule for rule in triggered_rules if rule["action_rank"] == max_rank]
        recommended_action = sorted(strongest, key=lambda rule: (rule["category"], rule["metric"]))[0]["action"]
    else:
        recommended_action = default_action

    by_action: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for rule in triggered_rules:
        by_action[rule["action"]] = by_action.get(rule["action"], 0) + 1
        key = rule["category"] or "uncategorized"
        by_category[key] = by_category.get(key, 0) + 1

    return {
        "metric_col": metric_col,
        "value_col": value_col,
        "threshold_col": threshold_col,
        "direction_col": direction_col,
        "action_col": action_col,
        "category_col": category_col,
        "reason_col": reason_col,
        "owner_col": owner_col,
        "default_action": default_action,
        "recommended_action": recommended_action,
        "rows_used": len(rules),
        "rows_dropped": dropped,
        "triggered_count": len(triggered_rules),
        "triggered_by_action": by_action,
        "triggered_by_category": by_category,
        "triggered_rules": sorted(triggered_rules, key=lambda rule: (-rule["action_rank"], rule["category"], rule["metric"])),
        "rules": rules,
        "notes": [
            "The highest-ranked triggered action wins: maintain < review < reduce < pause < retire.",
            "This is a deterministic triage layer; final capital changes still require the strategy mandate and owner sign-off.",
            "Use explicit thresholds set before reviewing the monitoring period to avoid discretionary hindsight changes.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Strategy Action Decision",
        "",
        f"- Recommended action: {report['recommended_action']}",
        f"- Rules used: {report['rows_used']}",
        f"- Rules dropped: {report['rows_dropped']}",
        f"- Triggered rules: {report['triggered_count']}",
        "",
        "## Triggered by Action",
        "",
    ]
    if report["triggered_by_action"]:
        for action, count in sorted(report["triggered_by_action"].items(), key=lambda item: (-ACTION_RANK.get(item[0], 0), item[0])):
            lines.append(f"- {action}: {count}")
    else:
        lines.append("- none")
    lines.extend(["", "## Triggered Rules", "", "| Action | Category | Metric | Value | Threshold | Direction | Margin | Owner | Reason |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"])
    for rule in report["triggered_rules"]:
        lines.append(f"| {rule['action']} | {rule['category']} | {rule['metric']} | {rule['value']} | {rule['threshold']} | {rule['direction']} | {rule['margin']} | {rule['owner']} | {rule['reason']} |")
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Turn monitoring metrics into strategy action recommendations.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--metric-col", default="metric")
    parser.add_argument("--value-col", default="value")
    parser.add_argument("--threshold-col", default="threshold")
    parser.add_argument("--direction-col", default="direction")
    parser.add_argument("--action-col", default="action")
    parser.add_argument("--category-col", default="category")
    parser.add_argument("--reason-col", default="reason")
    parser.add_argument("--owner-col", default="owner")
    parser.add_argument("--default-action", default="maintain")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    df = read_dataframe(args.csv_path)

    header, rows = _df_to_rows(df)
    required = [args.metric_col, args.value_col, args.threshold_col, args.action_col]
    optional = [col for col in [args.direction_col, args.category_col, args.reason_col, args.owner_col] if col and col in header]
    require_columns(header, required)
    report = build_report(
        rows,
        args.metric_col,
        args.value_col,
        args.threshold_col,
        args.direction_col if args.direction_col in optional else None,
        args.action_col,
        args.category_col if args.category_col in optional else None,
        args.reason_col if args.reason_col in optional else None,
        args.owner_col if args.owner_col in optional else None,
        args.default_action,
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
