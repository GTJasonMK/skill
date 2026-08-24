#!/usr/bin/env python3
"""Validate the Data-Quant bundle structure, contracts, links, and active children."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import yaml
from sync_source_skills import load_registry, validate_registry

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from data_quant import __version__  # noqa: E402
from data_quant import diagnostics as _diagnostics  # noqa: E402, F401
from data_quant.contracts.artifacts import ArtifactEnvelope  # noqa: E402
from data_quant.contracts.manifest import RunManifest  # noqa: E402
from data_quant.contracts.run_record import GateRecord, RunRecord  # noqa: E402
from data_quant.contracts.tables import CONTRACTS  # noqa: E402
from data_quant.registry import registry  # noqa: E402

EXPECTED_SCHEMAS = {
    "artifact-envelope.schema.json": ArtifactEnvelope,
    "run-manifest.schema.json": RunManifest,
    "run-record.schema.json": RunRecord,
    "stage-gate.schema.json": GateRecord,
}


def load_bundle_manifest() -> dict[str, Any]:
    payload = yaml.safe_load((ROOT / "BUNDLE-MANIFEST.yaml").read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("BUNDLE-MANIFEST.yaml must contain an object.")
    return payload


def check_frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError(f"{path.relative_to(ROOT)} lacks YAML frontmatter.")
    payload = yaml.safe_load(match.group(1))
    if not isinstance(payload, dict) or not payload.get("name") or not payload.get("description"):
        raise ValueError(f"{path.relative_to(ROOT)} needs frontmatter name and description.")
    return str(payload["name"])


def check_links() -> list[str]:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.md")):
        if ".venv" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            local = target.split("#", 1)[0]
            if not local or "://" in local or local.startswith(("mailto:", "/")):
                continue
            if not (path.parent / local).resolve().exists():
                errors.append(f"Broken link in {path.relative_to(ROOT)}: {target}")
    return errors


def check_schemas() -> list[str]:
    errors: list[str] = []
    for name, model in EXPECTED_SCHEMAS.items():
        path = ROOT / "schemas" / name
        if not path.exists():
            errors.append(f"Missing schema: schemas/{name}")
            continue
        actual = json.loads(path.read_text(encoding="utf-8"))
        expected = model.model_json_schema()
        if actual != expected:
            errors.append(f"Generated schema is stale: schemas/{name}")
    for table_type, contract in sorted(CONTRACTS.items()):
        path = ROOT / "schemas" / "tables" / f"{table_type}.schema.json"
        if not path.exists():
            errors.append(f"Missing table schema: schemas/tables/{table_type}.schema.json")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("x-contract-version") != contract.schema_version:
            errors.append(f"Stale table contract version: {table_type}")
        if payload.get("x-primary-key") != contract.primary_key:
            errors.append(f"Stale table primary key schema: {table_type}")
    diagnostic_output = ROOT / "schemas/diagnostics"
    expected_diagnostic_files: set[str] = set()
    for definition in registry.list():
        if definition.parameter_schema is None:
            continue
        name = f"{definition.diagnostic_id}.schema.json"
        expected_diagnostic_files.add(name)
        path = diagnostic_output / name
        expected = {
            **definition.parameter_schema,
            "x-diagnostic-id": definition.diagnostic_id,
            "x-manifest-stage": definition.manifest_stage,
        }
        if not path.exists():
            errors.append(f"Missing diagnostic parameter schema: {name}")
        elif json.loads(path.read_text(encoding="utf-8")) != expected:
            errors.append(f"Generated diagnostic parameter schema is stale: {name}")
    actual_diagnostic_files = (
        {path.name for path in diagnostic_output.glob("*.schema.json")}
        if diagnostic_output.exists()
        else set()
    )
    stale_diagnostic_files = sorted(actual_diagnostic_files - expected_diagnostic_files)
    if stale_diagnostic_files:
        errors.append(f"Orphaned diagnostic parameter schemas: {stale_diagnostic_files}")

    contracts_reference = ROOT / "quant-data-engineering/references/data-contracts.md"
    documented = set(
        re.findall(r"^\| `([^`]+)` \|", contracts_reference.read_text(encoding="utf-8"), re.MULTILINE)
    )
    missing_docs = sorted(set(CONTRACTS) - documented)
    if missing_docs:
        errors.append(f"Canonical tables missing from data-contracts reference: {missing_docs}")
    return errors


def check_dependency_lock() -> list[str]:
    path = ROOT / "pylock.toml"
    if not path.exists():
        return ["Missing pylock.toml"]
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    if payload.get("lock-version") != "1.0":
        return ["pylock.toml has an unsupported lock-version."]
    packages = payload.get("packages")
    if not isinstance(packages, list) or len(packages) < 20:
        return ["pylock.toml does not contain the full resolved environment."]
    errors: list[str] = []
    names = {str(package.get("name")) for package in packages if isinstance(package, dict)}
    if "data-quant-core" not in names:
        errors.append("pylock.toml does not include the local data-quant-core project.")
    for package in packages:
        if not isinstance(package, dict):
            errors.append("pylock.toml contains a non-object package entry.")
            continue
        for wheel in package.get("wheels", []):
            hashes = wheel.get("hashes", {}) if isinstance(wheel, dict) else {}
            if not hashes.get("sha256"):
                errors.append(f"Locked wheel lacks sha256: {package.get('name')}")
    return errors


def check_source_registry() -> list[str]:
    try:
        return validate_registry(load_registry())
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [f"Invalid source-registry.yaml: {exc}"]


def check_distribution_contract(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict):
        return ["BUNDLE-MANIFEST.yaml must declare the runtime distribution."]
    if runtime.get("distribution_scope") != "runtime_only":
        errors.append("Runtime wheel distribution_scope must be runtime_only.")
    if runtime.get("legacy_execution_requires_full_bundle") is not True:
        errors.append("Runtime must declare that legacy execution requires the full bundle.")
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if pyproject.get("project", {}).get("version") != __version__:
        errors.append("pyproject.toml version and data_quant.__version__ differ.")
    return errors


def check_git_hygiene() -> list[str]:
    errors = [
        f"Generated packaging metadata inside source tree: {path.relative_to(ROOT)}"
        for path in [*SRC.glob("*.egg-info"), ROOT / "build", ROOT / "dist"]
        if path.exists()
    ]
    try:
        result = subprocess.run(
            ["git", "ls-files", "data-quant/**"],
            cwd=ROOT.parent,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return errors
    forbidden = (
        "/.venv/",
        "/__pycache__/",
        "/runs/",
        "/examples/out/",
        ".egg-info/",
        "/build/",
        "/dist/",
    )
    for line in result.stdout.splitlines():
        normalized = "/" + line.replace("\\", "/") + "/"
        if any(token in normalized for token in forbidden):
            errors.append(f"Tracked generated file: {line}")
    return errors


def main() -> int:
    errors: list[str] = []
    manifest = load_bundle_manifest()
    active_children = 0
    for child in manifest.get("children", []):
        if not isinstance(child, dict):
            errors.append("Every child manifest entry must be an object.")
            continue
        path = ROOT / str(child.get("path", ""))
        status = child.get("status")
        if status == "active":
            active_children += 1
            if not path.is_file():
                errors.append(f"Active child missing: {path.relative_to(ROOT)}")
            else:
                actual_name = check_frontmatter(path)
                if actual_name != child.get("id"):
                    errors.append(
                        f"Child ID mismatch for {path.relative_to(ROOT)}: {child.get('id')} != {actual_name}"
                    )
        elif status not in {"planned", "disabled"}:
            errors.append(f"Unknown child status for {child.get('id')}: {status}")

    root_name = check_frontmatter(ROOT / "SKILL.md")
    if root_name != manifest.get("bundle", {}).get("id"):
        errors.append("Root SKILL name and bundle ID differ.")
    errors.extend(check_links())
    errors.extend(check_schemas())
    errors.extend(check_dependency_lock())
    errors.extend(check_source_registry())
    errors.extend(check_distribution_contract(manifest))
    errors.extend(check_git_hygiene())

    if errors:
        print("Data-Quant bundle validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"OK: root router, {active_children} active children, links, schemas, and hygiene checks pass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
