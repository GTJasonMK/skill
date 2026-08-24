"""Observable service availability, error, traffic, and latency health."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.contracts.parameters import DependencyHealthParameters, ServiceHealthParameters
from data_quant.io.validation import parse_utc_timestamp
from data_quant.registry import register_diagnostic


@register_diagnostic(
    "service-health",
    "service_health",
    required_table_types=("service_health_windows",),
    manifest_stage="monitoring",
    parameter_model=ServiceHealthParameters,
    description="Gate required services on observable freshness, coverage, uptime, errors, and latency.",
)
def service_health_artifact(
    observations: pd.DataFrame,
    *,
    required_service_ids: list[str],
    environment: str,
    evaluated_at: str,
    lookback: str = "1h",
    max_observation_age: str = "10m",
    minimum_window_coverage_fraction: float = 0.90,
    minimum_uptime_fraction: float = 0.999,
    maximum_error_rate: float = 0.01,
    maximum_latency_p95_ms: float = 1_000.0,
    minimum_request_count: int = 1,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    lookback_duration = pd.Timedelta(lookback)
    maximum_age = pd.Timedelta(max_observation_age)
    if (
        not required_service_ids
        or len(required_service_ids) != len(set(required_service_ids))
        or lookback_duration <= pd.Timedelta(0)
        or maximum_age <= pd.Timedelta(0)
        or not 0 <= minimum_window_coverage_fraction <= 1
        or not 0 <= minimum_uptime_fraction <= 1
        or not 0 <= maximum_error_rate <= 1
        or maximum_latency_p95_ms < 0
        or minimum_request_count < 0
    ):
        raise ValueError("Service-health IDs, durations, or thresholds are invalid.")
    evaluated = parse_utc_timestamp(pd.Series([evaluated_at]), "evaluated_at").iloc[0]
    frame = observations[
        (observations["environment"].astype(str) == environment)
        & observations["service_id"].astype(str).isin(required_service_ids)
    ].copy()
    for column in ("window_start", "window_end", "available_at"):
        frame[column] = parse_utc_timestamp(frame[column], column)
    frame = frame[
        (frame["window_end"] <= evaluated)
        & (frame["available_at"] <= evaluated)
        & (frame["window_end"] > evaluated - lookback_duration)
    ].copy()
    for column in ("request_count", "error_count", "uptime_fraction", "latency_p95_ms"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    numeric_columns = ["request_count", "error_count", "uptime_fraction", "latency_p95_ms"]
    if not np.isfinite(frame[numeric_columns].to_numpy(dtype=float)).all():
        raise ValueError("Service-health counts, uptime, and latency must be finite.")
    if (
        (frame["window_start"] >= frame["window_end"]).any()
        or (frame["request_count"] < 0).any()
        or (frame["error_count"] < 0).any()
        or (frame["error_count"] > frame["request_count"]).any()
        or (frame["request_count"] % 1 != 0).any()
        or (frame["error_count"] % 1 != 0).any()
        or frame["uptime_fraction"].lt(0).any()
        or frame["uptime_fraction"].gt(1).any()
        or frame["latency_p95_ms"].lt(0).any()
        or not frame["status"].astype(str).isin({"healthy", "degraded", "outage"}).all()
    ):
        raise ValueError("Service-health windows contain invalid intervals or metrics.")
    details = []
    blockers: list[DiagnosticMessage] = []
    warnings: list[DiagnosticMessage] = []
    lookback_seconds = lookback_duration.total_seconds()
    for service_id in required_service_ids:
        service = frame[frame["service_id"].astype(str) == service_id].sort_values(
            ["window_start", "window_end"]
        )
        if service.empty:
            blockers.append(
                DiagnosticMessage(
                    code="service_observation_missing",
                    message=f"Required service {service_id!r} has no observable lookback window.",
                    severity="blocker",
                    context={"service_id": service_id},
                )
            )
            details.append({"service_id": service_id, "status": "missing"})
            continue
        starts = service["window_start"].to_list()
        ends = service["window_end"].to_list()
        if any(starts[index] < ends[index - 1] for index in range(1, len(service))):
            raise ValueError(f"Service-health windows overlap for {service_id!r}.")
        effective_starts = service["window_start"].clip(lower=evaluated - lookback_duration)
        durations = (service["window_end"] - effective_starts).dt.total_seconds()
        covered_seconds = float(durations.sum())
        coverage_fraction = min(1.0, covered_seconds / lookback_seconds)
        uptime_fraction = float(
            np.average(service["uptime_fraction"].to_numpy(dtype=float), weights=durations)
        )
        request_count = int(service["request_count"].sum())
        error_count = int(service["error_count"].sum())
        error_rate = error_count / request_count if request_count else 0.0
        maximum_observed_latency = float(service["latency_p95_ms"].max())
        latest_end = pd.Timestamp(service["window_end"].max())
        observation_age = evaluated - latest_end
        latest_rows = service[service["window_end"] == latest_end]
        latest_statuses = set(latest_rows["status"].astype(str))
        latest_status = "healthy"
        if "outage" in latest_statuses:
            latest_status = "outage"
        elif "degraded" in latest_statuses:
            latest_status = "degraded"
        detail = {
            "service_id": service_id,
            "environment": environment,
            "window_count": len(service),
            "latest_window_end": latest_end.isoformat(),
            "observation_age": str(observation_age),
            "coverage_fraction": coverage_fraction,
            "uptime_fraction": uptime_fraction,
            "request_count": request_count,
            "error_count": error_count,
            "error_rate": error_rate,
            "maximum_observed_latency_p95_ms": maximum_observed_latency,
            "latest_status": latest_status,
        }
        details.append(detail)
        checks = (
            (
                observation_age > maximum_age,
                "service_observation_stale",
                "Latest service-health observation is stale.",
            ),
            (
                coverage_fraction < minimum_window_coverage_fraction,
                "service_window_coverage",
                "Service-health windows do not cover enough of the configured lookback.",
            ),
            (
                uptime_fraction < minimum_uptime_fraction,
                "service_uptime",
                "Service uptime is below the configured minimum.",
            ),
            (
                request_count < minimum_request_count,
                "service_request_count",
                "Observed request count is below the configured minimum.",
            ),
            (
                error_rate > maximum_error_rate,
                "service_error_rate",
                "Service error rate exceeds the configured maximum.",
            ),
            (
                maximum_observed_latency > maximum_latency_p95_ms,
                "service_latency",
                "Observed service p95 latency exceeds the configured maximum.",
            ),
            (
                latest_status == "outage",
                "service_outage",
                "Latest service status is outage.",
            ),
        )
        for breached, code, message in checks:
            if breached:
                blockers.append(
                    DiagnosticMessage(
                        code=code,
                        message=message,
                        severity="blocker",
                        context=detail,
                    )
                )
        if latest_status == "degraded":
            warnings.append(
                DiagnosticMessage(
                    code="service_degraded",
                    message="Latest service status is degraded without breaching a hard metric.",
                    severity="warning",
                    context={"service_id": service_id},
                )
            )
    observed_details = [detail for detail in details if detail.get("status") != "missing"]
    return ArtifactEnvelope(
        artifact_type="service_health",
        run_id=run_id,
        producer=ProducerReference(name="service-health", version=__version__),
        parameters={
            "required_service_ids": required_service_ids,
            "environment": environment,
            "evaluated_at": evaluated.isoformat(),
            "lookback": str(lookback_duration),
            "max_observation_age": str(maximum_age),
            "minimum_window_coverage_fraction": minimum_window_coverage_fraction,
            "minimum_uptime_fraction": minimum_uptime_fraction,
            "maximum_error_rate": maximum_error_rate,
            "maximum_latency_p95_ms": maximum_latency_p95_ms,
            "minimum_request_count": minimum_request_count,
        },
        summary={
            "required_service_count": len(required_service_ids),
            "observed_service_count": len(observed_details),
            "minimum_observed_uptime": min(
                (float(detail["uptime_fraction"]) for detail in observed_details),
                default=None,
            ),
            "maximum_observed_error_rate": max(
                (float(detail["error_rate"]) for detail in observed_details),
                default=None,
            ),
            "maximum_observed_latency_p95_ms": max(
                (float(detail["maximum_observed_latency_p95_ms"]) for detail in observed_details),
                default=None,
            ),
            "blocker_count": len(blockers),
        },
        warnings=warnings,
        blockers=blockers,
        evidence_gaps=[
            DiagnosticMessage(
                code="service_health_scope",
                message=(
                    "Reported windows do not prove independent synthetic reachability, dependency "
                    "health, regional redundancy, tail latency beyond supplied p95, incident response, "
                    "or recovery objectives."
                ),
                severity="warning",
            )
        ],
        details=details,
        provenance={"live_order_submission": False},
    ).finalize()


@register_diagnostic(
    "dependency-health",
    "dependency_health",
    required_table_types=("synthetic_probes", "service_dependencies"),
    manifest_stage="monitoring",
    parameter_model=DependencyHealthParameters,
    description="Gate independent synthetic reachability, dependency health, and regional RTO/RPO.",
)
def dependency_health_artifact(
    probes: pd.DataFrame,
    dependencies: pd.DataFrame,
    *,
    required_service_ids: list[str],
    environment: str,
    evaluated_at: str,
    lookback: str = "1h",
    minimum_probe_success_fraction: float = 0.99,
    maximum_synthetic_latency_ms: float = 500.0,
    minimum_dependency_redundancy: int = 2,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    lookback_duration = pd.Timedelta(lookback)
    if (
        not required_service_ids
        or len(required_service_ids) != len(set(required_service_ids))
        or lookback_duration <= pd.Timedelta(0)
        or not 0 <= minimum_probe_success_fraction <= 1
        or maximum_synthetic_latency_ms < 0
        or minimum_dependency_redundancy < 1
    ):
        raise ValueError("Dependency-health IDs, durations, or thresholds are invalid.")
    evaluated = parse_utc_timestamp(pd.Series([evaluated_at]), "evaluated_at").iloc[0]
    selected_probes = probes[
        (probes["environment"].astype(str) == environment)
        & probes["service_id"].astype(str).isin(required_service_ids)
    ].copy()
    for column in ("probe_start", "probe_end", "available_at"):
        selected_probes[column] = parse_utc_timestamp(selected_probes[column], column)
    selected_probes = selected_probes[
        (selected_probes["probe_end"] <= evaluated)
        & (selected_probes["available_at"] <= evaluated)
        & (selected_probes["probe_end"] > evaluated - lookback_duration)
    ].copy()
    selected_probes["success"] = selected_probes["success"].astype(bool)
    selected_probes["latency_ms"] = pd.to_numeric(selected_probes["latency_ms"], errors="coerce")
    if (
        (selected_probes["probe_start"] >= selected_probes["probe_end"]).any()
        or selected_probes["latency_ms"].lt(0).any()
        or not np.isfinite(selected_probes["latency_ms"].to_numpy(dtype=float)).all()
    ):
        raise ValueError("Synthetic probes contain invalid intervals or latency values.")

    selected_dependencies = dependencies[
        (dependencies["environment"].astype(str) == environment)
        & dependencies["service_id"].astype(str).isin(required_service_ids)
    ].copy()
    for column in ("effective_from", "available_at"):
        selected_dependencies[column] = parse_utc_timestamp(selected_dependencies[column], column)
    selected_dependencies = selected_dependencies[
        (selected_dependencies["effective_from"] <= evaluated)
        & (selected_dependencies["available_at"] <= evaluated)
    ].copy()
    selected_dependencies["recovery_time_objective"] = pd.to_numeric(
        selected_dependencies["recovery_time_objective"], errors="coerce"
    )
    selected_dependencies["recovery_point_objective"] = pd.to_numeric(
        selected_dependencies["recovery_point_objective"], errors="coerce"
    )
    if (
        not np.isfinite(
            selected_dependencies[
                ["recovery_time_objective", "recovery_point_objective"]
            ].to_numpy(dtype=float)
        ).all()
        or selected_dependencies["recovery_time_objective"].lt(0).any()
        or selected_dependencies["recovery_point_objective"].lt(0).any()
    ):
        raise ValueError("Dependency RTO/RPO values must be finite and non-negative.")
    if "effective_to" in selected_dependencies and selected_dependencies["effective_to"].notna().any():
        effective_to = parse_utc_timestamp(
            selected_dependencies["effective_to"].dropna(), "effective_to"
        )
        if (effective_to < evaluated).any():
            raise ValueError("Dependency graph contains expired effective_to before evaluated_at.")

    blockers: list[DiagnosticMessage] = []
    details: list[dict[str, Any]] = []
    for service_id in required_service_ids:
        service_probes = selected_probes[selected_probes["service_id"].astype(str) == service_id]
        if service_probes.empty:
            blockers.append(
                DiagnosticMessage(
                    code="synthetic_probe_missing",
                    message=f"Required service {service_id!r} has no synthetic probes in lookback.",
                    severity="blocker",
                    context={"service_id": service_id},
                )
            )
            details.append({"service_id": service_id, "probe_count": 0})
            continue
        probe_count = len(service_probes)
        success_fraction = float(service_probes["success"].mean())
        maximum_latency = float(service_probes["latency_ms"].max())
        service_deps = selected_dependencies[
            selected_dependencies["service_id"].astype(str) == service_id
        ]
        dependency_regions = (
            set(service_deps["region"].dropna().astype(str)) if "region" in service_deps else set()
        )
        dependency_count = int(service_deps["depends_on"].nunique())
        detail = {
            "service_id": service_id,
            "probe_count": probe_count,
            "probe_success_fraction": success_fraction,
            "maximum_synthetic_latency_ms": maximum_latency,
            "dependency_count": dependency_count,
            "dependency_regions": sorted(dependency_regions),
        }
        details.append(detail)
        if success_fraction < minimum_probe_success_fraction:
            blockers.append(
                DiagnosticMessage(
                    code="synthetic_probe_success",
                    message=f"Service {service_id!r} synthetic probe success is below the limit.",
                    severity="blocker",
                    context=detail,
                )
            )
        if maximum_latency > maximum_synthetic_latency_ms:
            blockers.append(
                DiagnosticMessage(
                    code="synthetic_probe_latency",
                    message=f"Service {service_id!r} synthetic probe latency exceeds the limit.",
                    severity="blocker",
                    context=detail,
                )
            )
        if dependency_count > 0 and dependency_count < minimum_dependency_redundancy:
            blockers.append(
                DiagnosticMessage(
                    code="dependency_redundancy",
                    message=f"Service {service_id!r} has fewer redundant dependencies than required.",
                    severity="blocker",
                    context=detail,
                )
            )

    observed: list[dict[str, Any]] = [
        detail for detail in details if detail.get("probe_count", 0) > 0
    ]
    return ArtifactEnvelope(
        artifact_type="dependency_health",
        run_id=run_id,
        producer=ProducerReference(name="dependency-health", version=__version__),
        parameters={
            "required_service_ids": required_service_ids,
            "environment": environment,
            "evaluated_at": evaluated.isoformat(),
            "lookback": str(lookback_duration),
            "minimum_probe_success_fraction": minimum_probe_success_fraction,
            "maximum_synthetic_latency_ms": maximum_synthetic_latency_ms,
            "minimum_dependency_redundancy": minimum_dependency_redundancy,
        },
        summary={
            "required_service_count": len(required_service_ids),
            "probed_service_count": len(observed),
            "minimum_probe_success_fraction": min(
                (float(detail["probe_success_fraction"]) for detail in observed),
                default=None,
            ),
            "maximum_synthetic_latency_ms": max(
                (float(detail["maximum_synthetic_latency_ms"]) for detail in observed),
                default=None,
            ),
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            DiagnosticMessage(
                code="dependency_health_scope",
                message=(
                    "Synthetic probes prove reachability only; they do not prove correctness, data "
                    "freshness, incident response, or recovery drill execution. Regional redundancy is "
                    "inferred from the dependency graph's declared regions, and RTO/RPO values are "
                    "reported metadata rather than measured recovery."
                ),
                severity="warning",
            )
        ],
        details=details,
        provenance={
            "reachability_measure": "independent_synthetic_probe",
            "redundancy_measure": "declared_dependency_region_count",
            "live_order_submission": False,
        },
    ).finalize()

