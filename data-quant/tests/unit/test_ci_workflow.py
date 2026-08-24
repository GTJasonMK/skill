from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_github_actions_matrix_covers_two_python_versions() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    versions = workflow["jobs"]["full-check"]["strategy"]["matrix"]["python-version"]
    assert versions == ["3.11", "3.12"]
    validation = workflow["jobs"]["full-check"]["steps"][-1]["run"]
    assert "scripts/full_check.sh" in validation
    assert "src/*.egg-info" in validation


def test_parent_workflow_installs_before_bundle_check() -> None:
    workflow = yaml.safe_load((ROOT.parent / ".github/workflows/data-quant.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["validate"]["steps"]
    names = [step.get("name") for step in steps]
    install = names.index("Install bundle and development dependencies")
    cleanup = names.index("Remove generated build metadata before bundle verification")
    verify = names.index("Verify committed schemas and bundle")
    assert install < cleanup < verify
    assert "src/*.egg-info" in steps[cleanup]["run"]
