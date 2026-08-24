"""Numeric feature and missingness drift diagnostics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.contracts.parameters import FeatureDriftParameters
from data_quant.registry import register_diagnostic


def population_stability_index(
    reference: pd.Series,
    current: pd.Series,
    *,
    bins: int = 10,
    epsilon: float = 1e-6,
) -> float:
    if bins < 2:
        raise ValueError("bins must be at least 2.")
    ref = pd.to_numeric(reference, errors="coerce").dropna().to_numpy(dtype=float)
    cur = pd.to_numeric(current, errors="coerce").dropna().to_numpy(dtype=float)
    if len(ref) < bins or len(cur) == 0:
        raise ValueError("PSI requires at least bins reference values and one current value.")
    quantiles = np.linspace(0.0, 1.0, bins + 1)
    edges = np.unique(np.quantile(ref, quantiles))
    if len(edges) < 3:
        raise ValueError("Reference values do not contain enough distinct values for PSI.")
    edges[0] = -np.inf
    edges[-1] = np.inf
    ref_counts, _ = np.histogram(ref, bins=edges)
    cur_counts, _ = np.histogram(cur, bins=edges)
    ref_share = np.maximum(ref_counts / ref_counts.sum(), epsilon)
    cur_share = np.maximum(cur_counts / cur_counts.sum(), epsilon)
    return float(np.sum((cur_share - ref_share) * np.log(cur_share / ref_share)))


@register_diagnostic(
    "feature-drift",
    "feature_drift",
    manifest_stage="monitoring",
    parameter_model=FeatureDriftParameters,
    description="Compare numeric feature distributions with PSI and fail-closed thresholds.",
)
def drift_artifact(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    *,
    columns: list[str],
    bins: int = 10,
    warning_threshold: float = 0.10,
    blocker_threshold: float = 0.25,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    if warning_threshold < 0 or blocker_threshold <= warning_threshold:
        raise ValueError("Require 0 <= warning_threshold < blocker_threshold.")
    missing = [column for column in columns if column not in reference or column not in current]
    if missing:
        raise ValueError(f"Drift columns missing from reference/current data: {missing}")
    details: list[dict] = []
    warnings: list[DiagnosticMessage] = []
    blockers: list[DiagnosticMessage] = []
    for column in columns:
        psi = population_stability_index(reference[column], current[column], bins=bins)
        reference_missing = float(reference[column].isna().mean())
        current_missing = float(current[column].isna().mean())
        row = {
            "column": column,
            "psi": psi,
            "reference_missing_rate": reference_missing,
            "current_missing_rate": current_missing,
            "missing_rate_change": current_missing - reference_missing,
        }
        details.append(row)
        if psi >= blocker_threshold:
            blockers.append(
                DiagnosticMessage(
                    code="feature_drift_blocker",
                    message=f"Feature {column!r} PSI {psi:.6f} exceeds blocker threshold.",
                    severity="blocker",
                    context=row,
                )
            )
        elif psi >= warning_threshold:
            warnings.append(
                DiagnosticMessage(
                    code="feature_drift_warning",
                    message=f"Feature {column!r} PSI {psi:.6f} exceeds warning threshold.",
                    severity="warning",
                    context=row,
                )
            )
    return ArtifactEnvelope(
        artifact_type="feature_drift",
        run_id=run_id,
        producer=ProducerReference(name="feature-drift", version=__version__),
        parameters={
            "columns": columns,
            "bins": bins,
            "warning_threshold": warning_threshold,
            "blocker_threshold": blocker_threshold,
        },
        summary={
            "column_count": len(columns),
            "warning_count": len(warnings),
            "blocker_count": len(blockers),
            "max_psi": max(row["psi"] for row in details) if details else None,
        },
        warnings=warnings,
        blockers=blockers,
        details=details,
    ).finalize()
