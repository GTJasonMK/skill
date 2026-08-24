"""Command-line entrypoint for the shared Data-Quant runtime."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from data_quant import __version__
from data_quant import diagnostics as _diagnostics  # noqa: F401
from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.contracts.manifest import RunManifest
from data_quant.paths import source_bundle_root
from data_quant.pipeline import run_manifest, validate_diagnostic_specs
from data_quant.registry import registry
from data_quant.registry.legacy_catalog import catalog as legacy_catalog
from data_quant.registry.legacy_catalog import run_legacy_cli
from data_quant.reporting import ReportFormat, render_run_file

CORE_MODULES = ("numpy", "pandas", "scipy", "pydantic", "yaml")
OPTIONAL_GROUPS = {
    "io": ("pyarrow", "duckdb", "sqlalchemy"),
    "ml": ("sklearn", "joblib"),
    "portfolio": ("statsmodels", "exchange_calendars", "cvxpy"),
}


def _module_status(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def doctor(as_json: bool) -> int:
    payload: dict[str, Any] = {
        "version": __version__,
        "python": sys.version.split()[0],
        "core": {module: _module_status(module) for module in CORE_MODULES},
        "optional": {
            group: {module: _module_status(module) for module in modules}
            for group, modules in OPTIONAL_GROUPS.items()
        },
    }
    payload["ok"] = all(payload["core"].values())
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"data-quant-core {payload['version']} on Python {payload['python']}")
        for module, present in payload["core"].items():
            print(f"  core {module}: {'OK' if present else 'MISSING'}")
        for group, modules in payload["optional"].items():
            status = ", ".join(f"{name}={'yes' if present else 'no'}" for name, present in modules.items())
            print(f"  optional[{group}]: {status}")
    return 0 if payload["ok"] else 1


def validate_manifest(path: Path) -> int:
    try:
        manifest = RunManifest.from_yaml(path)
        diagnostics = validate_diagnostic_specs(manifest.pipeline.diagnostics)
        manifest = manifest.model_copy(
            update={"pipeline": manifest.pipeline.model_copy(update={"diagnostics": diagnostics})}
        )
    except (OSError, ValueError, ValidationError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0


def verify_artifact(path: Path) -> int:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        artifact = ArtifactEnvelope.model_validate(data)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    expected = artifact.compute_content_digest()
    if artifact.content_digest != expected:
        print(f"INVALID: content_digest mismatch; expected {expected}", file=sys.stderr)
        return 1
    if artifact.artifact_id != expected:
        print(f"INVALID: artifact_id mismatch; expected {expected}", file=sys.stderr)
        return 1
    print(f"OK: {artifact.artifact_type} ({expected})")
    return 0


def list_capabilities(as_json: bool) -> int:
    items: list[dict[str, Any]] = [
        {
            "diagnostic_id": item.diagnostic_id,
            "artifact_type": item.artifact_type,
            "required_table_types": list(item.required_table_types),
            "required_extras": list(item.required_extras),
            "manifest_stage": item.manifest_stage,
            "parameter_schema": item.parameter_schema,
            "description": item.description,
            "execution_mode": "native",
            "available": True,
            "invocation": "python_api_or_manifest",
        }
        for item in registry.list()
    ]
    legacy_items = legacy_catalog()
    legacy_by_id = {str(item["diagnostic_id"]): item for item in legacy_items}
    native_ids = {str(item["diagnostic_id"]) for item in items}
    for item in items:
        legacy = legacy_by_id.get(str(item["diagnostic_id"]))
        if legacy is not None:
            item["legacy_cli_available"] = legacy["available"]
    items.extend(item for item in legacy_items if str(item["diagnostic_id"]) not in native_ids)
    items.sort(key=lambda item: str(item["diagnostic_id"]))
    if as_json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
    else:
        if not items:
            print("No diagnostics registered yet.")
        for item in items:
            availability = "" if item.get("available", True) else " [source bundle required]"
            print(f"{item['diagnostic_id']}: {item['artifact_type']}{availability} - {item['description']}")
    return 0


def run_pipeline(path: Path, output: Path | None) -> int:
    try:
        result = run_manifest(path, output_dir=output)
    except (OSError, ValueError, ValidationError, RuntimeError) as exc:
        print(f"RUN FAILED: {exc}", file=sys.stderr)
        return 1
    print(result.run_dir)
    return 0 if result.run_record.decision != "fail" else 1


def run_diagnostic(identifier: str, legacy_args: list[str], output: Path | None) -> int:
    try:
        artifact = run_legacy_cli(identifier, legacy_args)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"DIAGNOSTIC FAILED: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(output)
    else:
        print(text, end="")
    return 0


def validate_bundle() -> int:
    root = source_bundle_root()
    if root is None:
        print(
            "BUNDLE VALIDATION UNAVAILABLE: use the full source Skill bundle, not the runtime-only wheel.",
            file=sys.stderr,
        )
        return 1
    result = subprocess.run([sys.executable, str(root / "scripts" / "check_bundle.py")], cwd=root)
    return int(result.returncode)


def report_run(run_dir: Path, report_format: ReportFormat, output: Path | None) -> int:
    extension = {"json": "json", "markdown": "md", "html": "html"}[report_format]
    output_path = output or run_dir / "reports" / f"review.{extension}"
    try:
        rendered = render_run_file(run_dir / "run.json", output_path, report_format)
    except (OSError, ValueError, ValidationError) as exc:
        print(f"REPORT FAILED: {exc}", file=sys.stderr)
        return 1
    print(rendered)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quantctl", description="Data-Quant contracts and workflow CLI.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    doctor_parser = sub.add_parser("doctor", help="Check core and optional dependencies.")
    doctor_parser.add_argument("--json", action="store_true")

    caps = sub.add_parser("list-capabilities", help="List registered diagnostics.")
    caps.add_argument("--json", action="store_true")

    manifest_parser = sub.add_parser("validate-manifest", help="Validate and resolve a run manifest.")
    manifest_parser.add_argument("path", type=Path)

    artifact_parser = sub.add_parser("verify-artifact", help="Validate an artifact and verify its digest.")
    artifact_parser.add_argument("path", type=Path)

    run_parser = sub.add_parser("run", help="Run the fail-closed manifest pipeline.")
    run_parser.add_argument("path", type=Path)
    run_parser.add_argument("--output", type=Path, help="Exact run directory; must not already exist.")

    sub.add_parser("validate-bundle", help="Validate the local Skill bundle, links, and schemas.")

    report_parser = sub.add_parser("report", help="Render a Run Record without recomputing metrics.")
    report_parser.add_argument("run_dir", type=Path)
    report_parser.add_argument("--format", choices=["json", "markdown", "html"], default="markdown")
    report_parser.add_argument("--output", type=Path)

    diagnostic_parser = sub.add_parser("diagnostic", help="Run a cataloged compatibility diagnostic.")
    diagnostic_parser.add_argument("diagnostic_id")
    diagnostic_parser.add_argument("--output", type=Path)
    diagnostic_parser.add_argument("legacy_args", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        return doctor(args.json)
    if args.command == "list-capabilities":
        return list_capabilities(args.json)
    if args.command == "validate-manifest":
        return validate_manifest(args.path)
    if args.command == "verify-artifact":
        return verify_artifact(args.path)
    if args.command == "run":
        return run_pipeline(args.path, args.output)
    if args.command == "validate-bundle":
        return validate_bundle()
    if args.command == "report":
        return report_run(args.run_dir, args.format, args.output)
    if args.command == "diagnostic":
        return run_diagnostic(args.diagnostic_id, args.legacy_args, args.output)
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
