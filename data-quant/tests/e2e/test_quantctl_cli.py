from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_MANIFEST = ROOT / "examples/manifests/minimal.yaml"


def copied_example_manifest() -> dict:
    manifest = yaml.safe_load(EXAMPLE_MANIFEST.read_text(encoding="utf-8"))
    for source in manifest["data_sources"]:
        source["uri"] = str((EXAMPLE_MANIFEST.parent / source["uri"]).resolve())
    return manifest


def quantctl(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "data_quant.cli", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_quantctl_run_verify_and_report_round_trip(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"

    run = quantctl("run", str(EXAMPLE_MANIFEST), "--output", str(run_dir))
    assert Path(run.stdout.strip()) == run_dir

    artifact_path = run_dir / "artifacts/data/bars.json"
    verified = quantctl("verify-artifact", str(artifact_path))
    assert verified.stdout.startswith("OK: data_contract")

    report_path = tmp_path / "review.md"
    rendered = quantctl(
        "report",
        str(run_dir),
        "--format",
        "markdown",
        "--output",
        str(report_path),
    )
    assert Path(rendered.stdout.strip()) == report_path
    assert report_path.read_text(encoding="utf-8").startswith("# Data-Quant Run:")
    assert json.loads((run_dir / "run.json").read_text(encoding="utf-8"))["decision"] == "pass"


def test_quantctl_verify_artifact_requires_matching_identity_digests(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    quantctl("run", str(EXAMPLE_MANIFEST), "--output", str(run_dir))
    artifact_path = run_dir / "artifacts/data/bars.json"
    original = json.loads(artifact_path.read_text(encoding="utf-8"))

    missing_digest = dict(original)
    missing_digest["content_digest"] = None
    artifact_path.write_text(json.dumps(missing_digest), encoding="utf-8")
    missing_result = subprocess.run(
        [sys.executable, "-m", "data_quant.cli", "verify-artifact", str(artifact_path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert missing_result.returncode == 1
    assert "content_digest mismatch" in missing_result.stderr

    wrong_id = dict(original)
    wrong_id["artifact_id"] = "sha256:" + "0" * 64
    artifact_path.write_text(json.dumps(wrong_id), encoding="utf-8")
    wrong_id_result = subprocess.run(
        [sys.executable, "-m", "data_quant.cli", "verify-artifact", str(artifact_path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert wrong_id_result.returncode == 1
    assert "artifact_id mismatch" in wrong_id_result.stderr


def test_quantctl_run_returns_failure_for_unmet_required_diagnostic(tmp_path: Path) -> None:
    manifest = copied_example_manifest()
    manifest["pipeline"]["required_diagnostics"] = ["unknown-diagnostic"]
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    run_dir = tmp_path / "run"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "data_quant.cli",
            "run",
            str(manifest_path),
            "--output",
            str(run_dir),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert json.loads((run_dir / "run.json").read_text(encoding="utf-8"))["decision"] == "fail"


def test_quantctl_default_output_uses_external_run_root(tmp_path: Path) -> None:
    run_root = tmp_path / "run-root"
    environment = os.environ.copy()
    environment["DATA_QUANT_RUN_ROOT"] = str(run_root)

    result = subprocess.run(
        [sys.executable, "-m", "data_quant.cli", "run", str(EXAMPLE_MANIFEST)],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    run_dir = Path(result.stdout.strip())
    assert run_dir.is_relative_to(run_root)
    assert not run_dir.is_relative_to(ROOT)
    assert (run_dir / "artifacts/data/sessions.json").is_file()


def test_quantctl_capability_catalog_includes_native_and_legacy_diagnostics() -> None:
    capabilities = json.loads(quantctl("list-capabilities", "--json").stdout)
    by_id = {item["diagnostic_id"]: item for item in capabilities}
    assert by_id["data-contract"]["execution_mode"] == "native"
    assert by_id["data-contract"]["available"] is True
    assert by_id["factor-ic"]["manifest_stage"] == "research"
    assert by_id["factor-ic"]["parameter_schema"]["additionalProperties"] is False
    assert by_id["factor-ic"]["parameter_schema"]["properties"]["min_assets"]["minimum"] == 2
    assert set(by_id["purged-walk-forward"]["parameter_schema"]["required"]) == {
        "train_periods",
        "test_periods",
    }
    assert by_id["portfolio-backtest"]["execution_mode"] == "native"
    assert by_id["portfolio-backtest"]["available"] is True
    assert by_id["portfolio-backtest"]["legacy_cli_available"] is True
    assert by_id["execution-replay"]["execution_mode"] == "native"
    assert by_id["purged-walk-forward"]["execution_mode"] == "native"
    assert by_id["corporate-action-adjustment"]["manifest_stage"] == "validation"
    assert by_id["covariance-risk"]["execution_mode"] == "native"
    assert by_id["credit-migration-stress"]["manifest_stage"] == "risk"
    assert by_id["factor-attribution"]["manifest_stage"] == "risk"
    assert by_id["factor-risk"]["manifest_stage"] == "risk"
    assert by_id["feature-drift"]["execution_mode"] == "native"
    assert by_id["futures-roll"]["manifest_stage"] == "research"
    assert by_id["futures-roll-execution"]["manifest_stage"] == "execution"
    assert by_id["option-surface-check"]["manifest_stage"] == "risk"
    assert by_id["option-surface-smooth"]["manifest_stage"] == "risk"
    assert by_id["fixed-income-shock"]["manifest_stage"] == "risk"
    assert by_id["fx-rollover"]["manifest_stage"] == "research"
    assert by_id["crypto-cross-margin-stress"]["manifest_stage"] == "risk"
    assert by_id["crypto-margin-stress"]["manifest_stage"] == "risk"
    assert by_id["fixed-income-curve-stress"]["manifest_stage"] == "risk"
    assert by_id["fixed-income-price-reconciliation"]["manifest_stage"] == "validation"
    assert by_id["fx-forward-check"]["manifest_stage"] == "research"
    assert by_id["model-calibration"]["manifest_stage"] == "monitoring"
    assert by_id["option-hedge-replay"]["manifest_stage"] == "risk"
    assert by_id["portfolio-eligibility"]["manifest_stage"] == "portfolio"
    assert by_id["portfolio-stress"]["manifest_stage"] == "risk"
    assert by_id["rebalance-replay"]["manifest_stage"] == "execution"
    assert by_id["service-health"]["manifest_stage"] == "monitoring"
    assert by_id["source-rule-freshness"]["manifest_stage"] == "governance"
    assert by_id["dependency-health"]["manifest_stage"] == "monitoring"
    assert by_id["short-borrow-capacity"]["manifest_stage"] == "portfolio"
    assert by_id["signal-health"]["manifest_stage"] == "monitoring"
    assert by_id["fama-macbeth"]["manifest_stage"] == "research"
    assert by_id["fama-macbeth"]["execution_mode"] == "native"
    assert len(by_id) == 96
    assert "portfolio-backtest: portfolio_backtest" in quantctl("list-capabilities").stdout
