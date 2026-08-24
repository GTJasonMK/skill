#!/usr/bin/env python3
"""Tune a classification threshold from score/probability predictions.

Standard-library only. Useful when you want an operating point for precision,
recall, F1, or simple cost-sensitive decisions.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

MISSING = {"", "na", "n/a", "nan", "null", "none", "."}


def is_missing(value: str | None) -> bool:
    return value is None or value.strip().lower() in MISSING


def parse_float(value: str | None) -> float | None:
    if is_missing(value):
        return None
    try:
        out = float(value.replace(",", ""))
    except ValueError:
        return None
    return None if math.isnan(out) or math.isinf(out) else out


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


def metrics(tp: int, fp: int, tn: int, fn: int) -> dict[str, float | None]:
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    specificity = tn / (tn + fp) if tn + fp else None
    accuracy = (tp + tn) / (tp + tn + fp + fn) if tp + tn + fp + fn else None
    f1 = (
        None
        if precision is None or recall is None or precision + recall == 0
        else 2 * precision * recall / (precision + recall)
    )
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "accuracy": accuracy,
        "f1": f1,
    }


def evaluate(
    y_true: list[str], scores: list[float], threshold: float, positive_label: str, negative_label: str
) -> dict[str, float | None]:
    preds = [positive_label if score >= threshold else negative_label for score in scores]
    tp = sum(1 for t, p in zip(y_true, preds, strict=False) if t == positive_label and p == positive_label)
    fp = sum(1 for t, p in zip(y_true, preds, strict=False) if t != positive_label and p == positive_label)
    tn = sum(1 for t, p in zip(y_true, preds, strict=False) if t != positive_label and p != positive_label)
    fn = sum(1 for t, p in zip(y_true, preds, strict=False) if t == positive_label and p != positive_label)
    out = metrics(tp, fp, tn, fn)
    out["threshold"] = threshold
    return out


def choose_threshold(
    rows: list[dict[str, str]],
    truth: str,
    score: str,
    positive_label: str | None,
    objective: str,
    min_precision: float | None,
    min_recall: float | None,
    fp_cost: float,
    fn_cost: float,
) -> dict[str, object]:
    values = [
        (row.get(truth, ""), parse_float(row.get(score)))
        for row in rows
        if not is_missing(row.get(truth, ""))
    ]
    y_true = [truth_value for truth_value, score_value in values if score_value is not None]
    scores = [score_value for truth_value, score_value in values if score_value is not None]
    if len(y_true) != len(scores) or not y_true:
        raise SystemExit("Need non-missing truth and numeric score values.")
    labels = sorted({value for value in y_true if not is_missing(value)})
    if len(labels) != 2:
        raise SystemExit("Threshold tuning requires binary labels.")
    if positive_label is None:
        positive_label = "1" if "1" in labels else labels[-1]
    negative_label = next(label for label in labels if label != positive_label)
    candidates = sorted(set(scores))
    if candidates:
        candidates = [min(candidates) - 1e-12] + candidates + [max(candidates) + 1e-12]
    results = []
    for threshold in candidates:
        result = evaluate(y_true, scores, threshold, positive_label, negative_label)
        if min_precision is not None and (result["precision"] is None or result["precision"] < min_precision):
            continue
        if min_recall is not None and (result["recall"] is None or result["recall"] < min_recall):
            continue
        result["expected_cost"] = fp_cost * result["fp"] + fn_cost * result["fn"]
        results.append(result)
    if not results:
        raise SystemExit("No thresholds satisfied the constraints.")
    if objective == "f1":

        def key(item):
            return (item["f1"] is not None, item["f1"] or -1)
    elif objective == "precision":

        def key(item):
            return (item["precision"] is not None, item["precision"] or -1)
    elif objective == "recall":

        def key(item):
            return (item["recall"] is not None, item["recall"] or -1)
    elif objective == "specificity":

        def key(item):
            return (item["specificity"] is not None, item["specificity"] or -1)
    elif objective == "cost":

        def key(item):
            return (-item["expected_cost"],)
    else:
        raise SystemExit("Unknown objective.")
    best = max(results, key=key)
    return {
        "positive_label": positive_label,
        "negative_label": negative_label,
        "objective": objective,
        "min_precision": min_precision,
        "min_recall": min_recall,
        "fp_cost": fp_cost,
        "fn_cost": fn_cost,
        "best": best,
        "candidates_evaluated": len(results),
        "top_results": sorted(results, key=lambda item: (item["f1"] is None, -(item["f1"] or -1)))[:20],
    }


def markdown(report: dict[str, object]) -> str:
    best = report["best"]
    assert isinstance(best, dict)
    lines = [
        "# Threshold Tuning",
        "",
        f"- Objective: {report['objective']}",
        f"- Positive label: {report['positive_label']}",
        f"- Negative label: {report['negative_label']}",
        f"- Evaluated thresholds: {report['candidates_evaluated']}",
        f"- Best threshold: {best['threshold']}",
        "",
        "| Threshold | Precision | Recall | Specificity | Accuracy | F1 | FP | FN | Expected cost |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["top_results"]:
        lines.append(
            f"| {item['threshold']} | {item['precision']} | {item['recall']} | "
            f"{item['specificity']} | {item['accuracy']} | {item['f1']} | "
            f"{item['fp']} | {item['fn']} | {item['expected_cost']} |"
        )
    lines.extend(
        [
            "",
            "The chosen threshold should be validated on held-out data, not reused as a "
            "final test statistic.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Tune a binary classification threshold from scores.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--truth", required=True)
    parser.add_argument("--score", required=True)
    parser.add_argument("--positive-label")
    parser.add_argument(
        "--objective", choices=["f1", "precision", "recall", "specificity", "cost"], default="f1"
    )
    parser.add_argument("--min-precision", type=float)
    parser.add_argument("--min-recall", type=float)
    parser.add_argument("--fp-cost", type=float, default=1.0)
    parser.add_argument("--fn-cost", type=float, default=1.0)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    header, rows, _ = read_csv(args.csv_path)
    if args.truth not in header:
        raise SystemExit(f"Truth column '{args.truth}' not found.")
    if args.score not in header:
        raise SystemExit(f"Score column '{args.score}' not found.")
    report = choose_threshold(
        rows,
        args.truth,
        args.score,
        args.positive_label,
        args.objective,
        args.min_precision,
        args.min_recall,
        args.fp_cost,
        args.fn_cost,
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
