#!/usr/bin/env python3
"""Split a CSV into train/test files with leakage-aware split strategies.

Standard-library only. Supports random, stratified, time-ordered, and grouped
splits. Use this before modeling when a quick reproducible split is needed.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


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


def write_csv(path: Path, header: list[str], rows: Iterable[dict[str, str]], dialect: csv.Dialect) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, dialect=dialect)
        writer.writeheader()
        writer.writerows(rows)


def test_count(n: int, test_size: float) -> int:
    if n <= 1:
        return 0
    return min(n - 1, max(1, math.ceil(n * test_size)))


def random_split(rows: list[dict[str, str]], test_size: float, seed: int) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    shuffled = list(rows)
    random.Random(seed).shuffle(shuffled)
    n_test = test_count(len(shuffled), test_size)
    return shuffled[n_test:], shuffled[:n_test]


def stratified_split(rows: list[dict[str, str]], target: str, test_size: float, seed: int) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(target, "")].append(row)
    train: list[dict[str, str]] = []
    test: list[dict[str, str]] = []
    rng = random.Random(seed)
    for _, group_rows in sorted(groups.items()):
        shuffled = list(group_rows)
        rng.shuffle(shuffled)
        n_test = test_count(len(shuffled), test_size)
        if len(shuffled) <= 1:
            train.extend(shuffled)
        else:
            test.extend(shuffled[:n_test])
            train.extend(shuffled[n_test:])
    rng.shuffle(train)
    rng.shuffle(test)
    return train, test


def time_split(rows: list[dict[str, str]], time_col: str, test_size: float) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    ordered = sorted(rows, key=lambda row: row.get(time_col, ""))
    n_test = test_count(len(ordered), test_size)
    return ordered[:-n_test], ordered[-n_test:]


def group_split(rows: list[dict[str, str]], group_col: str, test_size: float, seed: int) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_group[row.get(group_col, "")].append(row)
    group_ids = list(by_group)
    random.Random(seed).shuffle(group_ids)
    target_test_rows = test_count(len(rows), test_size)
    test_groups: set[str] = set()
    test_total = 0
    for group_id in group_ids:
        if test_total >= target_test_rows and test_groups:
            break
        test_groups.add(group_id)
        test_total += len(by_group[group_id])
    train = [row for row in rows if row.get(group_col, "") not in test_groups]
    test = [row for row in rows if row.get(group_col, "") in test_groups]
    return train, test


def summarize_split(rows: list[dict[str, str]], train: list[dict[str, str]], test: list[dict[str, str]], target: str | None, group_col: str | None) -> dict[str, object]:
    report: dict[str, object] = {
        "rows_total": len(rows),
        "rows_train": len(train),
        "rows_test": len(test),
        "test_rate": round(len(test) / len(rows), 4) if rows else None,
    }
    if target:
        report["target_distribution_total"] = dict(Counter(row.get(target, "") for row in rows))
        report["target_distribution_train"] = dict(Counter(row.get(target, "") for row in train))
        report["target_distribution_test"] = dict(Counter(row.get(target, "") for row in test))
    if group_col:
        train_groups = {row.get(group_col, "") for row in train}
        test_groups = {row.get(group_col, "") for row in test}
        report["group_overlap_count"] = len(train_groups & test_groups)
        report["groups_train"] = len(train_groups)
        report["groups_test"] = len(test_groups)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Split a CSV into train/test files.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("split_output"))
    parser.add_argument("--strategy", choices=["random", "stratified", "time", "group"], default="random")
    parser.add_argument("--target", help="Target column for stratified split and report.")
    parser.add_argument("--time-col", help="Time column for time split.")
    parser.add_argument("--group-col", help="Group/entity column for group split.")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not 0 < args.test_size < 1:
        raise SystemExit("--test-size must be between 0 and 1.")
    header, rows, dialect = read_csv(args.csv_path)
    if not rows:
        raise SystemExit("No data rows found.")
    if args.strategy == "stratified":
        if not args.target or args.target not in header:
            raise SystemExit("--target is required for stratified split.")
        train, test = stratified_split(rows, args.target, args.test_size, args.seed)
    elif args.strategy == "time":
        if not args.time_col or args.time_col not in header:
            raise SystemExit("--time-col is required for time split.")
        train, test = time_split(rows, args.time_col, args.test_size)
    elif args.strategy == "group":
        if not args.group_col or args.group_col not in header:
            raise SystemExit("--group-col is required for group split.")
        train, test = group_split(rows, args.group_col, args.test_size, args.seed)
    else:
        train, test = random_split(rows, args.test_size, args.seed)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "train.csv", header, train, dialect)
    write_csv(args.output_dir / "test.csv", header, test, dialect)
    report = summarize_split(rows, train, test, args.target, args.group_col)
    report["strategy"] = args.strategy
    report["seed"] = args.seed
    (args.output_dir / "split_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
