#!/usr/bin/env python3
"""Compare simple JSON model reports and emit a leaderboard.

Standard-library only. Expects each JSON file to contain a flat metrics dict.
It is intentionally permissive so it can compare outputs from different scripts
and experiments.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_report(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    metrics = data.get("metrics", data)
    if not isinstance(metrics, dict):
        raise SystemExit(f"{path}: metrics must be a JSON object.")
    return {"path": str(path), "name": path.stem, "metrics": metrics}


def as_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def score_report(report: dict[str, object], metric: str, higher_is_better: bool) -> float | None:
    metrics = report["metrics"]
    assert isinstance(metrics, dict)
    value = metrics.get(metric)
    number = as_number(value)
    if number is None:
        return None
    return number if higher_is_better else -number


def markdown(rows: list[dict[str, object]], metric: str) -> str:
    lines = [
        "# Model Comparison",
        "",
        f"- Ranking metric: {metric}",
        "",
        "| Rank | Model | Metric value | Source |",
        "| --- | --- | --- | --- |",
    ]
    for i, row in enumerate(rows, start=1):
        lines.append(f"| {i} | {row['name']} | {row['metric_value']} | {row['path']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare JSON model reports.")
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--metric", required=True, help="Metric name to rank by.")
    parser.add_argument("--higher-is-better", action="store_true", help="Treat larger metric values as better.")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    loaded = []
    for path in args.reports:
        if not path.exists():
            raise SystemExit(f"Missing report: {path}")
        loaded.append(load_report(path))
    scored = []
    for report in loaded:
        score = score_report(report, args.metric, args.higher_is_better)
        if score is None:
            continue
        metrics = report["metrics"]
        assert isinstance(metrics, dict)
        scored.append(
            {
                "name": report["name"],
                "path": report["path"],
                "metric_value": metrics.get(args.metric),
                "score": score,
                "metrics": metrics,
            }
        )
    if not scored:
        raise SystemExit(f"No reports contained numeric metric '{args.metric}'.")
    scored.sort(key=lambda row: row["score"], reverse=True)
    result = {
        "metric": args.metric,
        "higher_is_better": args.higher_is_better,
        "leaderboard": scored,
    }
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown(scored, args.metric), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(markdown(scored, args.metric), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
