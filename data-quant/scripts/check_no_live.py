#!/usr/bin/env python3
"""Fail when the Data-Quant bundle gains obvious live-trading capabilities."""

from __future__ import annotations

import argparse
import ast
import re
import tomllib
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROHIBITED_CAPABILITIES = {"credential_storage", "fund_transfer", "live_order_submission"}
PROHIBITED_PACKAGES = {
    "alpaca-py",
    "alpaca-trade-api",
    "ccxt",
    "ib-insync",
    "ibapi",
    "metatrader5",
    "oandapyv20",
    "python-binance",
    "tqsdk",
    "vnpy",
    "xtquant",
}
PROHIBITED_IMPORT_ROOTS = {
    "alpaca",
    "binance",
    "ccxt",
    "ib_insync",
    "ibapi",
    "metatrader5",
    "oandapyv20",
    "tqsdk",
    "vnpy",
    "xtquant",
}
PROHIBITED_CALLS = {
    "create_market_order",
    "create_order",
    "place_order",
    "send_order",
    "submit_order",
    "transfer_funds",
    "withdraw",
}
EXCLUDED_PARTS = {
    ".git",
    ".hypothesis",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}


def _load_object(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain an object.")
    return payload


def _dependency_name(requirement: str) -> str:
    return re.split(r"[<>=!~;\s\[]", requirement, maxsplit=1)[0].lower().replace("_", "-")


def _check_bundle_policy(root: Path) -> list[str]:
    path = root / "BUNDLE-MANIFEST.yaml"
    if not path.is_file():
        return ["Missing BUNDLE-MANIFEST.yaml no-live policy."]
    payload = _load_object(path)
    bundle = payload.get("bundle")
    errors: list[str] = []
    if not isinstance(bundle, dict) or bundle.get("offline_execution_only") is not True:
        errors.append("BUNDLE-MANIFEST.yaml must set bundle.offline_execution_only: true.")
    declared = payload.get("prohibited_capabilities")
    declared_set = set(declared) if isinstance(declared, list) else set()
    missing = sorted(PROHIBITED_CAPABILITIES - declared_set)
    if missing:
        errors.append(f"BUNDLE-MANIFEST.yaml is missing prohibited capabilities: {missing}")
    return errors


def _check_dependencies(root: Path) -> list[str]:
    path = root / "pyproject.toml"
    if not path.is_file():
        return ["Missing pyproject.toml dependency policy input."]
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    project = payload.get("project", {})
    requirements = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        requirements.extend(group)
    found = sorted(
        name
        for name in (_dependency_name(str(requirement)) for requirement in requirements)
        if name in PROHIBITED_PACKAGES
    )
    return [f"Prohibited live-trading dependency declared: {name}" for name in found]


def _python_files(root: Path) -> list[Path]:
    return [
        path
        for path in sorted(root.rglob("*.py"))
        if not any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts)
    ]


def _call_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _check_python(path: Path, root: Path) -> list[str]:
    relative = path.relative_to(root)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(relative))
    except (OSError, SyntaxError) as exc:
        return [f"Cannot inspect {relative}: {exc}"]
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots = {alias.name.split(".", 1)[0].lower() for alias in node.names}
            for name in sorted(roots & PROHIBITED_IMPORT_ROOTS):
                errors.append(f"{relative}:{node.lineno}: prohibited import {name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            name = node.module.split(".", 1)[0].lower()
            if name in PROHIBITED_IMPORT_ROOTS:
                errors.append(f"{relative}:{node.lineno}: prohibited import {name}")
        elif isinstance(node, ast.Call):
            name = _call_name(node)
            if name in PROHIBITED_CALLS:
                errors.append(f"{relative}:{node.lineno}: prohibited live-action call {name}")
    return errors


def collect_errors(root: Path) -> tuple[list[str], int]:
    files = _python_files(root)
    errors = _check_bundle_policy(root) + _check_dependencies(root)
    for path in files:
        errors.extend(_check_python(path, root))
    return errors, len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    errors, file_count = collect_errors(root)
    if errors:
        print("Data-Quant no-live check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"OK: offline-only policy, dependencies, and {file_count} Python files pass no-live checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
