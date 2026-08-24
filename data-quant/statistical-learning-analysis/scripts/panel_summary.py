#!/usr/bin/env python3
"""Summarize panel-style CSV data for grouped/time-aware analysis.

Standard-library only. Identifies repeated entities, time ordering, balance
of observations per entity, and likely leakage risks.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]], csv.Dialect]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(handle, dialect=dialect)
        header = list(reader.fieldnames or [])
        rows = [{name: row.get(name, "") for name in header} for row in reader]
    return header, rows, dialect


def summarize(rows: list[dict[str, str]], entity: str, time_col: str | None) -> dict[str, object]:
    by_entity: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_entity[row.get(entity, "")].append(row)
    obs_per_entity = [len(group_rows) for group_rows in by_entity.values()]
    time_ranges = []
    if time_col:
        for ent, group_rows in by_entity.items():
            times = [row.get(time_col, "") for row in group_rows if row.get(time_col, "")]
            if times:
                time_ranges.append({"entity": ent, "min": min(times), "max": max(times), "n": len(times)})
    repeat_rate = sum(count > 1 for count in obs_per_entity) / len(obs_per_entity) if obs_per_entity else 0
    entity_counts = Counter(obs_per_entity)
    return {
        "rows": len(rows),
        "entities": len(by_entity),
        "time_column": time_col,
        "mean_observations_per_entity": mean(obs_per_entity) if obs_per_entity else None,
        "median_observations_per_entity": sorted(obs_per_entity)[len(obs_per_entity) // 2]
        if obs_per_entity
        else None,
        "max_observations_per_entity": max(obs_per_entity) if obs_per_entity else None,
        "min_observations_per_entity": min(obs_per_entity) if obs_per_entity else None,
        "entity_count_distribution": dict(sorted(entity_counts.items())),
        "repeat_entity_rate": repeat_rate,
        "time_ranges": time_ranges[:50],
        "likely_panel": bool(repeat_rate > 0 or len(rows) > len(by_entity)),
    }


def markdown(report: dict[str, object]) -> str:
    lines = [
        "# Panel Summary",
        "",
        f"- Rows: {report['rows']}",
        f"- Entities: {report['entities']}",
        f"- Likely panel data: {report['likely_panel']}",
        f"- Repeat entity rate: {report['repeat_entity_rate']}",
        f"- Mean observations per entity: {report['mean_observations_per_entity']}",
        f"- Median observations per entity: {report['median_observations_per_entity']}",
        f"- Max observations per entity: {report['max_observations_per_entity']}",
        f"- Min observations per entity: {report['min_observations_per_entity']}",
        "",
        "## Entity Count Distribution",
        "",
        "| Observations per entity | Count |",
        "| --- | --- |",
    ]
    for observations, count in report["entity_count_distribution"].items():
        lines.append(f"| {observations} | {count} |")
    if report["time_column"]:
        lines.extend(["", "## Time Ranges", "", "| Entity | Min | Max | N |", "| --- | --- | --- | --- |"])
        for item in report["time_ranges"]:
            lines.append(f"| {item['entity']} | {item['min']} | {item['max']} | {item['n']} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize panel data structure from CSV.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--entity", required=True, help="Entity/group identifier column.")
    parser.add_argument("--time-col", help="Optional time/order column.")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    header, rows, _ = read_csv(args.csv_path)
    if args.entity not in header:
        raise SystemExit(f"Entity column '{args.entity}' not found.")
    if args.time_col and args.time_col not in header:
        raise SystemExit(f"Time column '{args.time_col}' not found.")
    report = summarize(rows, args.entity, args.time_col)
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
