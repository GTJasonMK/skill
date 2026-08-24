from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data_quant.monitoring import (
    dependency_health_artifact,
    drift_artifact,
    model_calibration_artifact,
    population_stability_index,
    service_health_artifact,
    signal_health_artifact,
)


def test_identical_distribution_has_zero_psi() -> None:
    series = pd.Series(np.linspace(-1, 1, 100))
    assert population_stability_index(series, series, bins=10) == pytest.approx(0.0)


def test_shifted_distribution_creates_blocker() -> None:
    reference = pd.DataFrame({"feature": np.linspace(0, 1, 200)})
    current = pd.DataFrame({"feature": np.linspace(2, 3, 200)})
    artifact = drift_artifact(reference, current, columns=["feature"], bins=10)
    assert artifact.artifact_type == "feature_drift"
    assert artifact.summary["blocker_count"] == 1
    assert artifact.blockers[0].code == "feature_drift_blocker"


def test_constant_reference_cannot_produce_misleading_psi() -> None:
    with pytest.raises(ValueError, match="distinct"):
        population_stability_index(pd.Series([1.0] * 20), pd.Series([1.0] * 20))


def signal_frame(*, degraded: bool) -> pd.DataFrame:
    rows = []
    for period in range(8):
        timestamp = pd.Timestamp("2024-01-01T09:00:00Z") + pd.Timedelta(days=period)
        for asset in range(5):
            value = float(asset)
            rows.append(
                {
                    "as_of": timestamp,
                    "asset_id": f"asset-{asset}",
                    "value": value,
                    "return_value": -value if degraded and period >= 5 else value,
                }
            )
    return pd.DataFrame(rows)


def test_signal_health_passes_stable_ic_and_blocks_degradation() -> None:
    stable = signal_health_artifact(
        signal_frame(degraded=False),
        evaluated_at="2024-01-08T10:00:00Z",
        max_signal_age="2h",
    )
    degraded = signal_health_artifact(
        signal_frame(degraded=True),
        evaluated_at="2024-01-08T10:00:00Z",
        max_signal_age="2h",
    )

    assert stable.summary["blocker_count"] == 0
    assert stable.summary["recent_mean_rank_ic"] == pytest.approx(1.0)
    assert {blocker.code for blocker in degraded.blockers} == {
        "rank_ic_degradation",
        "recent_rank_ic_floor",
    }


def calibration_frames(*, inverted: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    prediction_rows = []
    label_rows = []
    asset_index = 0
    for probability, positive_count in ((0.1, 1), (0.5, 5), (0.9, 9)):
        for within_group in range(10):
            asset_id = f"asset-{asset_index}"
            asset_index += 1
            prediction_rows.append(
                {
                    "decision_at": "2024-01-01T00:00:00Z",
                    "available_at": "2024-01-01T00:00:00Z",
                    "model_id": "M",
                    "model_version": "v1",
                    "asset_id": asset_id,
                    "target_label": "up",
                    "prediction": 1.0 - probability if inverted else probability,
                    "prediction_type": "probability",
                }
            )
            label_rows.append(
                {
                    "decision_at": "2024-01-01T00:00:00Z",
                    "return_end": "2024-01-02T00:00:00Z",
                    "asset_id": asset_id,
                    "label": "up",
                    "return_value": 0.01 if within_group < positive_count else -0.01,
                    "return_type": "simple",
                    "return_basis": "gross",
                }
            )
    return pd.DataFrame(prediction_rows), pd.DataFrame(label_rows)


def test_model_calibration_metrics_pass_reliable_and_block_inverted_probabilities() -> None:
    predictions, labels = calibration_frames(inverted=False)
    calibrated = model_calibration_artifact(
        predictions,
        labels,
        model_id="M",
        model_version="v1",
        label="up",
        evaluated_at="2024-01-03T00:00:00Z",
        bins=10,
        max_brier_score=0.20,
        max_expected_calibration_error=0.05,
    )
    inverted_predictions, labels = calibration_frames(inverted=True)
    inverted = model_calibration_artifact(
        inverted_predictions,
        labels,
        model_id="M",
        model_version="v1",
        label="up",
        evaluated_at="2024-01-03T00:00:00Z",
        bins=10,
        max_brier_score=0.20,
        max_expected_calibration_error=0.05,
    )

    assert calibrated.summary["brier_score"] == pytest.approx(0.1433333333)
    assert calibrated.summary["expected_calibration_error"] == pytest.approx(0.0)
    assert calibrated.summary["calibration_slope"] == pytest.approx(1.0)
    assert calibrated.summary["calibration_intercept"] == pytest.approx(0.0)
    assert calibrated.summary["blocker_count"] == 0
    assert {
        "model_brier_score",
        "model_calibration_intercept",
        "model_calibration_slope",
        "model_expected_calibration_error",
    } <= {blocker.code for blocker in inverted.blockers}


def test_model_calibration_reports_ece_uncertainty_and_class_conditional_gap() -> None:
    predictions, labels = calibration_frames(inverted=False)
    calibrated = model_calibration_artifact(
        predictions,
        labels,
        model_id="M",
        model_version="v1",
        label="up",
        evaluated_at="2024-01-03T00:00:00Z",
        bins=10,
        bootstrap_resamples=100,
        bootstrap_confidence=0.90,
        stability_min_class_observations=10,
        max_class_conditional_ece_gap=0.01,
    )

    assert calibrated.summary["ece_ci_lower"] <= calibrated.summary["ece_ci_upper"]
    assert calibrated.provenance["ece_uncertainty"] == "bootstrap_percentile_interval"
    assert calibrated.provenance["class_conditional_stability"] == "two_class_ece_gap"
    assert calibrated.summary["class_conditional_ece_gap"] == pytest.approx(0.0)
    assert calibrated.summary["blocker_count"] == 0


def test_service_health_aggregates_windows_and_blocks_outage_or_missing_service() -> None:
    healthy = pd.DataFrame(
        {
            "service_id": ["api", "api"],
            "environment": ["production", "production"],
            "window_start": ["2024-01-01T09:00:00Z", "2024-01-01T09:30:00Z"],
            "window_end": ["2024-01-01T09:30:00Z", "2024-01-01T10:00:00Z"],
            "available_at": ["2024-01-01T09:31:00Z", "2024-01-01T10:00:00Z"],
            "status": ["healthy", "healthy"],
            "request_count": [500, 500],
            "error_count": [0, 0],
            "uptime_fraction": [1.0, 1.0],
            "latency_p95_ms": [100.0, 120.0],
        }
    )
    artifact = service_health_artifact(
        healthy,
        required_service_ids=["api"],
        environment="production",
        evaluated_at="2024-01-01T10:00:00Z",
        lookback="1h",
        max_observation_age="5m",
        minimum_request_count=100,
    )
    unhealthy = healthy.copy()
    unhealthy["status"] = "outage"
    unhealthy["error_count"] = 50
    unhealthy["uptime_fraction"] = 0.90
    unhealthy["latency_p95_ms"] = 2_000.0
    blocked = service_health_artifact(
        unhealthy,
        required_service_ids=["api", "risk"],
        environment="production",
        evaluated_at="2024-01-01T10:00:00Z",
        lookback="1h",
        max_observation_age="5m",
        minimum_request_count=100,
    )

    assert artifact.summary["observed_service_count"] == 1
    assert artifact.summary["minimum_observed_uptime"] == pytest.approx(1.0)
    assert artifact.summary["maximum_observed_error_rate"] == pytest.approx(0.0)
    assert artifact.summary["blocker_count"] == 0
    assert {
        "service_error_rate",
        "service_latency",
        "service_observation_missing",
        "service_outage",
        "service_uptime",
    } <= {blocker.code for blocker in blocked.blockers}


def test_dependency_health_gates_probes_redundancy_and_missing_service() -> None:
    probes = pd.DataFrame(
        {
            "service_id": ["api", "api"],
            "environment": ["production", "production"],
            "probe_start": ["2024-01-01T09:50:00Z", "2024-01-01T09:55:00Z"],
            "probe_end": ["2024-01-01T09:51:00Z", "2024-01-01T09:56:00Z"],
            "available_at": ["2024-01-01T09:51:00Z", "2024-01-01T09:56:00Z"],
            "probe_type": ["http", "http"],
            "success": [True, False],
            "latency_ms": [100.0, 600.0],
            "status_code": [200, 500],
        }
    )
    dependencies = pd.DataFrame(
        [
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
    )
    artifact = dependency_health_artifact(
        probes,
        dependencies,
        required_service_ids=["api"],
        environment="production",
        evaluated_at="2024-01-01T10:00:00Z",
        lookback="1h",
        minimum_probe_success_fraction=0.99,
        maximum_synthetic_latency_ms=500.0,
        minimum_dependency_redundancy=2,
    )
    missing = dependency_health_artifact(
        probes,
        dependencies,
        required_service_ids=["api", "risk"],
        environment="production",
        evaluated_at="2024-01-01T10:00:00Z",
        lookback="1h",
        minimum_dependency_redundancy=2,
    )

    assert artifact.provenance["reachability_measure"] == "independent_synthetic_probe"
    assert artifact.summary["minimum_probe_success_fraction"] == pytest.approx(0.5)
    assert {
        "synthetic_probe_success",
        "synthetic_probe_latency",
        "dependency_redundancy",
    } <= {blocker.code for blocker in artifact.blockers}
    assert "synthetic_probe_missing" in {blocker.code for blocker in missing.blockers}

