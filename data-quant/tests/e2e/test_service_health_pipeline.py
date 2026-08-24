from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(tmp_path: Path, *, unhealthy: bool) -> Path:
    observations = pd.DataFrame(
        {
            "service_id": ["api", "api"],
            "environment": ["production", "production"],
            "window_start": ["2024-01-01T09:00:00Z", "2024-01-01T09:30:00Z"],
            "window_end": ["2024-01-01T09:30:00Z", "2024-01-01T10:00:00Z"],
            "available_at": ["2024-01-01T09:31:00Z", "2024-01-01T10:00:00Z"],
            "status": ["outage" if unhealthy else "healthy"] * 2,
            "request_count": [500, 500],
            "error_count": [50 if unhealthy else 0] * 2,
            "uptime_fraction": [0.90 if unhealthy else 1.0] * 2,
            "latency_p95_ms": [2_000.0 if unhealthy else 100.0] * 2,
        }
    )
    source_path = tmp_path / "service.csv"
    observations.to_csv(source_path, index=False)
    manifest = {
        "project": {"name": "service-health", "asset_class": "mixed"},
        "data_sources": [
            {
                "id": "service",
                "uri": str(source_path),
                "format": "csv",
                "table_type": "service_health_windows",
            }
        ],
        "pipeline": {
            "stages": ["data", "monitoring", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "service-health",
                    "stage": "monitoring",
                    "input_sources": ["service"],
                    "parameters": {
                        "required_service_ids": ["api", "risk"] if unhealthy else ["api"],
                        "environment": "production",
                        "evaluated_at": "2024-01-01T10:00:00Z",
                        "lookback": "1h",
                        "max_observation_age": "5m",
                        "minimum_window_coverage_fraction": 0.90,
                        "minimum_uptime_fraction": 0.999,
                        "maximum_error_rate": 0.01,
                        "maximum_latency_p95_ms": 1_000.0,
                        "minimum_request_count": 100,
                    },
                }
            ],
            "required_diagnostics": ["service-health"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/monitoring/service-health.json").read_text(encoding="utf-8")
    )


def test_service_health_manifest_passes_fresh_covered_service(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, unhealthy=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["observed_service_count"] == 1
    assert artifact.summary["minimum_observed_uptime"] == pytest.approx(1.0)
    assert artifact.summary["maximum_observed_error_rate"] == pytest.approx(0.0)
    assert artifact.summary["blocker_count"] == 0


def test_service_health_manifest_blocks_outage_and_missing_dependency(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, unhealthy=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    blocker_codes = {blocker.code for blocker in load_artifact(result).blockers}
    assert "service_outage" in blocker_codes
    assert "service_observation_missing" in blocker_codes
    assert "service_error_rate" in blocker_codes
