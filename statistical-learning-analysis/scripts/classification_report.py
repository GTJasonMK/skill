#!/usr/bin/env python3
"""Evaluate classification predictions from a CSV file.

Standard-library only. Accepts either predicted labels or numeric scores.
Useful for quick model review, threshold analysis, and report generation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


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


def sorted_labels(values: list[str]) -> list[str]:
    labels = [value for value in values if not is_missing(value)]
    return sorted(dict.fromkeys(labels))


def confusion_matrix(y_true: list[str], y_pred: list[str], labels: list[str]) -> dict[str, Any]:
    index = {label: i for i, label in enumerate(labels)}
    matrix = [[0 for _ in labels] for _ in labels]
    for truth, pred in zip(y_true, y_pred):
        matrix[index[truth]][index[pred]] += 1
    return {"labels": labels, "matrix": matrix}


def per_class_metrics(y_true: list[str], y_pred: list[str], labels: list[str]) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        tn = sum(1 for t, p in zip(y_true, y_pred) if t != label and p != label)
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        specificity = tn / (tn + fp) if tn + fp else None
        f1 = None if precision is None or recall is None or precision + recall == 0 else 2 * precision * recall / (precision + recall)
        metrics.append(
            {
                "label": label,
                "support": tp + fn,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "precision": precision,
                "recall": recall,
                "specificity": specificity,
                "f1": f1,
            }
        )
    return metrics


def macro_weighted(metrics: list[dict[str, Any]]) -> dict[str, float | None]:
    support = sum(item["support"] for item in metrics)
    def safe_mean(values: list[float | None]) -> float | None:
        vals = [v for v in values if v is not None]
        return sum(vals) / len(vals) if vals else None

    def weighted(key: str) -> float | None:
        if support == 0:
            return None
        vals = [item[key] for item in metrics if item[key] is not None]
        weights = [item["support"] for item in metrics if item[key] is not None]
        if not vals:
            return None
        return sum(v * w for v, w in zip(vals, weights)) / sum(weights)

    return {
        "precision_macro": safe_mean([item["precision"] for item in metrics]),
        "recall_macro": safe_mean([item["recall"] for item in metrics]),
        "f1_macro": safe_mean([item["f1"] for item in metrics]),
        "precision_weighted": weighted("precision"),
        "recall_weighted": weighted("recall"),
        "f1_weighted": weighted("f1"),
    }


def accuracy_score(y_true: list[str], y_pred: list[str]) -> float:
    return sum(t == p for t, p in zip(y_true, y_pred)) / len(y_true) if y_true else float("nan")


def balanced_accuracy(metrics: list[dict[str, Any]]) -> float | None:
    recalls = [item["recall"] for item in metrics if item["recall"] is not None]
    return sum(recalls) / len(recalls) if recalls else None


def rankdata(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


def roc_auc_score(y_true: list[str], scores: list[float], positive_label: str) -> float | None:
    labels = [1 if value == positive_label else 0 for value in y_true]
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    ranks = rankdata(scores)
    sum_pos = sum(rank for rank, label in zip(ranks, labels) if label == 1)
    return (sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def average_precision_score(y_true: list[str], scores: list[float], positive_label: str) -> float | None:
    labels = [1 if value == positive_label else 0 for value in y_true]
    n_pos = sum(labels)
    if n_pos == 0:
        return None
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    tp = 0
    ap = 0.0
    for rank, idx in enumerate(order, start=1):
        if labels[idx] == 1:
            tp += 1
            ap += tp / rank
    return ap / n_pos


def binary_loss(y_true: list[str], probs: list[float], positive_label: str) -> dict[str, float | None]:
    labels = [1 if value == positive_label else 0 for value in y_true]
    eps = 1e-15
    clipped = [min(max(p, eps), 1 - eps) for p in probs]
    brier = sum((p - y) ** 2 for p, y in zip(clipped, labels)) / len(labels) if labels else None
    log_loss = -sum(y * math.log(p) + (1 - y) * math.log(1 - p) for p, y in zip(clipped, labels)) / len(labels) if labels else None
    return {"brier": brier, "log_loss": log_loss}


def classification_report(rows: list[dict[str, str]], truth: str, prediction: str | None, score: str | None, positive_label: str | None, threshold: float) -> dict[str, Any]:
    y_true = [row.get(truth, "") for row in rows if not is_missing(row.get(truth, ""))]
    if not y_true:
        raise SystemExit("No non-missing truth values found.")
    if prediction:
        y_pred = [row.get(prediction, "") for row in rows if not is_missing(row.get(truth, ""))]
    else:
        if not score:
            raise SystemExit("Provide either --prediction or --score.")
        y_pred = []
    y_score = []
    if score:
        scores = [parse_float(row.get(score)) for row in rows if not is_missing(row.get(truth, ""))]
        if any(value is None for value in scores):
            raise SystemExit(f"Score column '{score}' contains non-numeric values.")
        y_score = [float(value) for value in scores if value is not None]
    if not y_pred and y_score:
        labels = sorted_labels(y_true)
        if positive_label is None:
            positive_label = "1" if "1" in labels else labels[-1]
        negative_candidates = [label for label in labels if label != positive_label]
        if not negative_candidates:
            raise SystemExit("Need at least two labels for score-based classification.")
        negative_label = negative_candidates[0]
        y_pred = [positive_label if p >= threshold else negative_label for p in y_score]
    labels = sorted_labels(y_true + y_pred)
    if positive_label is None:
        if "1" in labels and len(labels) == 2:
            positive_label = "1"
        elif len(labels) == 2:
            positive_label = labels[-1]
        else:
            positive_label = labels[-1]
    metrics_per_class = per_class_metrics(y_true, y_pred, labels)
    report: dict[str, Any] = {
        "n": len(y_true),
        "labels": labels,
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy(metrics_per_class),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels),
        "per_class": metrics_per_class,
        "summary": macro_weighted(metrics_per_class),
    }
    if len(labels) == 2:
        pos_metrics = next((item for item in metrics_per_class if item["label"] == positive_label), None)
        if pos_metrics:
            report["positive_label"] = positive_label
            report["precision"] = pos_metrics["precision"]
            report["recall"] = pos_metrics["recall"]
            report["f1"] = pos_metrics["f1"]
        if y_score:
            report["roc_auc"] = roc_auc_score(y_true, y_score, positive_label)
            report["average_precision"] = average_precision_score(y_true, y_score, positive_label)
            report.update(binary_loss(y_true, y_score, positive_label))
            report["threshold"] = threshold
    return report


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Classification Report",
        "",
        f"- N: {report['n']}",
        f"- Accuracy: {report['accuracy']}",
        f"- Balanced accuracy: {report['balanced_accuracy']}",
    ]
    if "positive_label" in report:
        lines.extend(
            [
                f"- Positive label: {report['positive_label']}",
                f"- Precision: {report.get('precision')}",
                f"- Recall: {report.get('recall')}",
                f"- F1: {report.get('f1')}",
            ]
        )
    if "roc_auc" in report:
        lines.extend(
            [
                f"- ROC AUC: {report.get('roc_auc')}",
                f"- Average precision: {report.get('average_precision')}",
                f"- Brier score: {report.get('brier')}",
                f"- Log loss: {report.get('log_loss')}",
                f"- Threshold: {report.get('threshold')}",
            ]
        )
    lines.extend(["", "## Confusion Matrix", ""])
    cm = report["confusion_matrix"]
    labels = cm["labels"]
    matrix = cm["matrix"]
    lines.append("| Truth \\ Pred | " + " | ".join(labels) + " |")
    lines.append("| --- | " + " | ".join("---" for _ in labels) + " |")
    for label, row in zip(labels, matrix):
        lines.append("| " + label + " | " + " | ".join(str(v) for v in row) + " |")
    lines.extend(["", "## Per Class", "", "| Label | Support | Precision | Recall | Specificity | F1 |", "| --- | --- | --- | --- | --- | --- |"])
    for item in report["per_class"]:
        lines.append(f"| {item['label']} | {item['support']} | {item['precision']} | {item['recall']} | {item['specificity']} | {item['f1']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate classification predictions stored in a CSV.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--truth", required=True, help="Ground-truth label column.")
    parser.add_argument("--prediction", help="Predicted label column.")
    parser.add_argument("--score", help="Numeric score/probability column for the positive class.")
    parser.add_argument("--positive-label", help="Positive class label for binary scoring.")
    parser.add_argument("--threshold", type=float, default=0.5, help="Threshold for converting scores to labels.")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    header, rows, _ = read_csv(args.csv_path)
    if args.truth not in header:
        raise SystemExit(f"Truth column '{args.truth}' not found.")
    if args.prediction and args.prediction not in header:
        raise SystemExit(f"Prediction column '{args.prediction}' not found.")
    if args.score and args.score not in header:
        raise SystemExit(f"Score column '{args.score}' not found.")
    report = classification_report(rows, args.truth, args.prediction, args.score, args.positive_label, args.threshold)
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
