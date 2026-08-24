from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def run_wheel_module(
    install_dir: Path,
    working_dir: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(install_dir)
    return subprocess.run(
        [sys.executable, "-m", "data_quant.cli", *arguments],
        cwd=working_dir,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


def test_runtime_wheel_is_truthful_and_core_pipeline_remains_runnable(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    shutil.copy2(ROOT / "pyproject.toml", project / "pyproject.toml")
    shutil.copy2(ROOT / "README.md", project / "README.md")
    shutil.copytree(ROOT / "src", project / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    wheel_dir = tmp_path / "wheel"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(wheel_dir)],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(wheel_dir.glob("*.whl"))
    install_dir = tmp_path / "install"
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-deps", "--target", str(install_dir), str(wheel)],
        check=True,
        capture_output=True,
        text=True,
    )

    capabilities = run_wheel_module(install_dir, tmp_path, "list-capabilities", "--json")
    assert capabilities.returncode == 0, capabilities.stderr
    items = json.loads(capabilities.stdout)
    legacy = [item for item in items if "legacy_script" in item]
    assert len(legacy) == 63
    assert all(item["available"] is False for item in legacy)
    assert {item["execution_mode"] for item in legacy} == {"source_bundle_required"}
    portfolio = next(item for item in items if item["diagnostic_id"] == "portfolio-backtest")
    assert portfolio["execution_mode"] == "native"
    assert portfolio["legacy_cli_available"] is False

    unavailable = run_wheel_module(
        install_dir,
        tmp_path,
        "diagnostic",
        "profile-dataset",
        "--",
        "--help",
    )
    assert unavailable.returncode == 1
    assert "runtime-only wheel" in unavailable.stderr

    bundle_validation = run_wheel_module(install_dir, tmp_path, "validate-bundle")
    assert bundle_validation.returncode == 1
    assert "runtime-only wheel" in bundle_validation.stderr

    bars = tmp_path / "bars.csv"
    bars.write_text(
        (
            "timestamp,asset_id,close,currency,adjustment_state\n"
            "2024-01-02T07:00:00Z,A,10.0,CNY,raw\n"
        ),
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "project": {"name": "wheel-smoke", "asset_class": "equity"},
                "data_sources": [
                    {
                        "id": "bars",
                        "uri": str(bars),
                        "format": "csv",
                        "table_type": "market_bars",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    run_dir = tmp_path / "run"
    run = run_wheel_module(
        install_dir,
        tmp_path,
        "run",
        str(manifest),
        "--output",
        str(run_dir),
    )
    assert run.returncode == 0, run.stderr
    assert (run_dir / "run.json").is_file()
