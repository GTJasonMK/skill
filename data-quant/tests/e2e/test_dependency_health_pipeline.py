from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(tmp_path: Path, *, redundant: bool) -> Path:
    probes = pd.DataFrame(
        {
            "service_id": ["api"] * 3,
            "environment": ["production"] * 3,
            "probe_start": [
                "2024-01-01T09:50:00Z",
                "2024-01-01T09:55:00Z",
                "2024-01-01T09:58:00Z",
            ],
            "probe_end": [
                "2024-01-01T09:51:00Z",
                "2024-01-01T09:56:00Z",
                "2024-01-01T09:59:00Z",
            ],
            "available_at": [
                "2024-01-01T09:51:00Z",
                "2024-01-01T09:56:00Z",
                "2024-01-01T09:59:00Z",
            ],
            "probe_type": ["http"] * 3,
            "success": [True, True, True],
            "latency_ms": [100.0, 120.0, 110.0],
            "status_code": [200, 200, 200],
        }
    )
    dependency_rows = [
        {
            "service_id": "api",
            "environment": "production",
            "depends_on": "auth",
            "effective_from": "2024-01-01T00:00:00Z",
            "available_at": "2024-01-01T00:00:00Z",
            "recovery_time_objective": 300.0,
            "recovery_point_objective": 60.0,
            "region": "us-east",
        }
    ]
    if redundant:
        dependency_rows.append(
            {
                "service_id": "api",
                "environment": "production",
                "depends_on": "auth-dr",
                "effective_from": "2024-01-01T00:00:00Z",
                "available_at": "2024-01-01T00:00:00Z",
                "recovery_time_objective": 300.0,
                "recovery_point_objective": 60.0,
                "region": "us-west",
            }
        )
    dependencies = pd.DataFrame(dependency_rows)
    sources = []
    for source_id, frame, table_type in (
        ("probes", probes, "synthetic_probes"),
        ("dependencies", dependencies, "service_dependencies"),
    ):
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    manifest = {
        "project": {"name": "dependency-health", "asset_class": "equity"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "monitoring", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "dependency-health",
                    "stage": "monitoring",
                    "input_sources": ["probes", "dependencies"],
                    "parameters": {
                        "required_service_ids": ["api"],
                        "environment": "production",
                        "evaluated_at": "2024-01-01T10:00:00Z",
                        "lookback": "1h",
                        "minimum_probe_success_fraction": 0.99,
                        "maximum_synthetic_latency_ms": 500.0,
                        "minimum_dependency_redundancy": 2,
                    },
                }
            ],
            "required_diagnostics": ["dependency-health"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/monitoring/dependency-health.json").read_text(
            encoding="utf-8"
        )
    )


def test_dependency_health_manifest_passes_redundant_probes(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, redundant=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["minimum_probe_success_fraction"] == pytest.approx(1.0)
    assert artifact.summary["blocker_count"] == 0


def test_dependency_health_manifest_blocks_single_dependency(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, redundant=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    assert "dependency_redundancy" in {blocker.code for blocker in artifact.blockers}
