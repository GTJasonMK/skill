"""Point-in-time signal freshness, dispersion, and realized-performance health."""

from __future__ import annotations

import numpy as np
import pandas as pd

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.contracts.parameters import ModelCalibrationParameters, SignalHealthParameters
from data_quant.diagnostics.factor import factor_ic_artifact
from data_quant.io.validation import parse_utc_timestamp
from data_quant.registry import register_diagnostic


@register_diagnostic(
    "signal-health",
    "signal_health",
    required_table_types=("factor_panel", "return_labels"),
    manifest_stage="monitoring",
    parameter_model=SignalHealthParameters,
    description="Block stale, collapsed, under-covered, or materially degraded realized signal IC.",
)
def signal_health_artifact(
    frame: pd.DataFrame,
    *,
    evaluated_at: str,
    max_signal_age: str = "2D",
    min_assets: int = 5,
    recent_periods: int = 3,
    min_baseline_periods: int = 5,
    min_recent_rank_ic: float = 0.0,
    max_rank_ic_degradation: float = 0.10,
    min_latest_std: float = 1e-12,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    if min_assets < 2 or recent_periods < 1 or min_baseline_periods < 1:
        raise ValueError("Signal-health period and asset counts are invalid.")
    evaluated = parse_utc_timestamp(pd.Series([evaluated_at]), "evaluated_at").iloc[0]
    max_age = pd.Timedelta(max_signal_age)
    if max_age < pd.Timedelta(0):
        raise ValueError("max_signal_age must be non-negative.")
    data = frame.copy()
    data["as_of"] = parse_utc_timestamp(data["as_of"], "as_of")
    if (data["as_of"] > evaluated).any():
        raise ValueError("Signal-health input contains observations after evaluated_at.")
    latest = data["as_of"].max()
    latest_values = pd.to_numeric(
        data.loc[data["as_of"] == latest, "value"],
        errors="coerce",
    ).dropna()
    latest_std = float(latest_values.std(ddof=0)) if len(latest_values) else None
    age = evaluated - latest
    ic_artifact = factor_ic_artifact(
        data,
        date_col="as_of",
        factor_col="value",
        forward_return_col="return_value",
        min_assets=min_assets,
        run_id=run_id,
    )
    usable = [row for row in ic_artifact.details if row["rank_ic"] is not None]
    recent = usable[-recent_periods:]
    baseline = usable[: -recent_periods] if len(usable) > recent_periods else []
    recent_mean = (
        float(pd.Series([row["rank_ic"] for row in recent], dtype=float).mean())
        if recent
        else None
    )
    baseline_mean = (
        float(pd.Series([row["rank_ic"] for row in baseline], dtype=float).mean())
        if baseline
        else None
    )
    degradation = (
        baseline_mean - recent_mean
        if baseline_mean is not None and recent_mean is not None
        else None
    )
    blockers: list[DiagnosticMessage] = []
    if age > max_age:
        blockers.append(
            DiagnosticMessage(
                code="signal_stale",
                message="Latest signal observation exceeds max_signal_age.",
                severity="blocker",
                context={"age": str(age), "max_signal_age": str(max_age)},
            )
        )
    if len(latest_values) < min_assets:
        blockers.append(
            DiagnosticMessage(
                code="signal_coverage",
                message="Latest signal cross-section has insufficient assets.",
                severity="blocker",
                context={"asset_count": len(latest_values), "min_assets": min_assets},
            )
        )
    if latest_std is None or latest_std < min_latest_std:
        blockers.append(
            DiagnosticMessage(
                code="signal_dispersion_collapse",
                message="Latest signal cross-sectional dispersion is below its floor.",
                severity="blocker",
                context={"latest_std": latest_std, "min_latest_std": min_latest_std},
            )
        )
    if len(recent) < recent_periods or len(baseline) < min_baseline_periods:
        blockers.append(
            DiagnosticMessage(
                code="signal_health_history",
                message="Signal-health history is insufficient for baseline/recent comparison.",
                severity="blocker",
                context={
                    "baseline_periods": len(baseline),
                    "recent_periods": len(recent),
                },
            )
        )
    else:
        if recent_mean is not None and recent_mean < min_recent_rank_ic:
            blockers.append(
                DiagnosticMessage(
                    code="recent_rank_ic_floor",
                    message="Recent mean rank IC is below its configured floor.",
                    severity="blocker",
                    context={"recent_mean_rank_ic": recent_mean},
                )
            )
        if degradation is not None and degradation > max_rank_ic_degradation:
            blockers.append(
                DiagnosticMessage(
                    code="rank_ic_degradation",
                    message="Recent mean rank IC has degraded beyond its configured tolerance.",
                    severity="blocker",
                    context={"rank_ic_degradation": degradation},
                )
            )
    return ArtifactEnvelope(
        artifact_type="signal_health",
        run_id=run_id,
        producer=ProducerReference(name="signal-health", version=__version__),
        parameters={
            "evaluated_at": evaluated.isoformat(),
            "max_signal_age": str(max_age),
            "min_assets": min_assets,
            "recent_periods": recent_periods,
            "min_baseline_periods": min_baseline_periods,
            "min_recent_rank_ic": min_recent_rank_ic,
            "max_rank_ic_degradation": max_rank_ic_degradation,
            "min_latest_std": min_latest_std,
        },
        summary={
            "latest_signal_at": latest.isoformat(),
            "signal_age": str(age),
            "latest_asset_count": len(latest_values),
            "latest_cross_section_std": latest_std,
            "usable_ic_periods": len(usable),
            "baseline_mean_rank_ic": baseline_mean,
            "recent_mean_rank_ic": recent_mean,
            "rank_ic_degradation": degradation,
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            DiagnosticMessage(
                code="signal_health_scope",
                message=(
                    "IC health does not prove calibration, strategy PnL, causal stability, capacity, "
                    "execution quality, or production service availability."
                ),
                severity="warning",
            )
        ],
        details=usable,
        provenance={"live_order_submission": False},
    ).finalize()


@register_diagnostic(
    "model-calibration",
    "model_calibration",
    required_table_types=("model_predictions", "return_labels"),
    manifest_stage="monitoring",
    parameter_model=ModelCalibrationParameters,
    description="Monitor PIT probability calibration with Brier, log-loss, ECE, and linear reliability.",
)
def model_calibration_artifact(
    predictions: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    model_id: str,
    label: str,
    evaluated_at: str,
    model_version: str | None = None,
    return_basis: str = "gross",
    positive_return_threshold: float = 0.0,
    bins: int = 10,
    min_observations: int = 30,
    max_brier_score: float = 0.25,
    max_log_loss: float = 1.0,
    max_expected_calibration_error: float = 0.10,
    min_calibration_slope: float = 0.50,
    max_calibration_slope: float = 1.50,
    max_abs_calibration_intercept: float = 0.10,
    bootstrap_resamples: int = 200,
    bootstrap_confidence: float = 0.90,
    stability_min_class_observations: int = 20,
    max_class_conditional_ece_gap: float = 0.10,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    if (
        return_basis not in {"gross", "excess"}
        or bins < 2
        or min_observations < 10
        or not 0 <= max_brier_score <= 1
        or max_log_loss <= 0
        or not 0 <= max_expected_calibration_error <= 1
        or max_calibration_slope <= min_calibration_slope
        or max_abs_calibration_intercept < 0
        or bootstrap_resamples < 50
        or not 0.5 < bootstrap_confidence < 1
        or stability_min_class_observations < 10
        or max_class_conditional_ece_gap < 0
    ):
        raise ValueError("Model calibration basis, bins, sample size, or limits are invalid.")
    evaluated = parse_utc_timestamp(pd.Series([evaluated_at]), "evaluated_at").iloc[0]
    selected_predictions = predictions[
        (predictions["model_id"].astype(str) == model_id)
        & (predictions["target_label"].astype(str) == label)
    ].copy()
    versions = sorted(selected_predictions["model_version"].dropna().astype(str).unique())
    if model_version is None:
        if len(versions) != 1:
            raise ValueError(f"model-calibration requires one model_version; available: {versions}")
        model_version = versions[0]
    selected_predictions = selected_predictions[
        selected_predictions["model_version"].astype(str) == model_version
    ].copy()
    if selected_predictions.empty:
        raise ValueError("No predictions match the requested model, version, and target label.")
    if selected_predictions["prediction_type"].astype(str).ne("probability").any():
        raise ValueError("model-calibration requires probability predictions.")
    for column in ("decision_at", "available_at"):
        selected_predictions[column] = parse_utc_timestamp(selected_predictions[column], column)
    if (selected_predictions["available_at"] > selected_predictions["decision_at"]).any():
        raise ValueError("Model predictions must be available by their decision timestamps.")
    selected_predictions = selected_predictions[
        selected_predictions["decision_at"] <= evaluated
    ].copy()
    selected_predictions["prediction"] = pd.to_numeric(
        selected_predictions["prediction"], errors="coerce"
    )
    if (
        not np.isfinite(selected_predictions["prediction"]).all()
        or selected_predictions["prediction"].lt(0).any()
        or selected_predictions["prediction"].gt(1).any()
    ):
        raise ValueError("Probability predictions must be finite values from zero through one.")
    selected_labels = labels[labels["label"].astype(str) == label].copy()
    for column in ("decision_at", "return_end"):
        selected_labels[column] = parse_utc_timestamp(selected_labels[column], column)
    selected_labels = selected_labels[selected_labels["return_end"] <= evaluated].copy()
    if selected_labels.empty:
        raise ValueError("No realized labels are available by evaluated_at.")
    if (
        selected_labels["return_type"].astype(str).ne("simple").any()
        or selected_labels["return_basis"].astype(str).ne(return_basis).any()
    ):
        raise ValueError("Calibration labels must use the requested simple-return basis.")
    selected_labels["return_value"] = pd.to_numeric(
        selected_labels["return_value"], errors="coerce"
    )
    if not np.isfinite(selected_labels["return_value"]).all():
        raise ValueError("Calibration label returns must be finite.")
    aligned = selected_predictions.merge(
        selected_labels[["decision_at", "asset_id", "return_value"]],
        on=["decision_at", "asset_id"],
        how="inner",
        validate="one_to_one",
    )
    if aligned.empty:
        raise ValueError("No seasoned model predictions have realized labels at evaluated_at.")
    unseasoned_prediction_count = len(selected_predictions) - len(aligned)
    probabilities = aligned["prediction"].to_numpy(dtype=float)
    outcomes = (aligned["return_value"].to_numpy(dtype=float) > positive_return_threshold).astype(
        float
    )
    observation_count = len(aligned)
    brier_score = float(np.mean((probabilities - outcomes) ** 2))
    clipped = np.clip(probabilities, 1e-12, 1.0 - 1e-12)
    log_loss = float(
        -np.mean(outcomes * np.log(clipped) + (1.0 - outcomes) * np.log(1.0 - clipped))
    )
    bin_indexes = np.minimum((probabilities * bins).astype(int), bins - 1)
    details = []
    expected_calibration_error = 0.0
    for bin_index in range(bins):
        mask = bin_indexes == bin_index
        count = int(mask.sum())
        if count == 0:
            continue
        mean_prediction = float(probabilities[mask].mean())
        observed_rate = float(outcomes[mask].mean())
        absolute_gap = abs(mean_prediction - observed_rate)
        expected_calibration_error += count / observation_count * absolute_gap
        details.append(
            {
                "bin_index": bin_index,
                "lower_bound": bin_index / bins,
                "upper_bound": (bin_index + 1) / bins,
                "observation_count": count,
                "mean_prediction": mean_prediction,
                "observed_positive_rate": observed_rate,
                "absolute_calibration_gap": absolute_gap,
            }
        )

    def expected_calibration_error_of(probabilities_sample: np.ndarray, outcomes_sample: np.ndarray) -> float:
        sample_bins = np.minimum((probabilities_sample * bins).astype(int), bins - 1)
        ece = 0.0
        total = len(probabilities_sample)
        for bin_index in range(bins):
            mask = sample_bins == bin_index
            count = int(mask.sum())
            if count == 0:
                continue
            gap = abs(
                float(probabilities_sample[mask].mean()) - float(outcomes_sample[mask].mean())
            )
            ece += count / total * gap
        return ece

    rng = np.random.default_rng(0)
    bootstrap_ece_samples: list[float] = []
    for _ in range(bootstrap_resamples):
        indexes = rng.integers(0, observation_count, size=observation_count)
        bootstrap_ece_samples.append(
            expected_calibration_error_of(probabilities[indexes], outcomes[indexes])
        )
    bootstrap_ece: np.ndarray = np.asarray(bootstrap_ece_samples, dtype=float)
    alpha = (1.0 - bootstrap_confidence) / 2.0
    ece_ci_lower = float(np.quantile(bootstrap_ece, alpha))
    ece_ci_upper = float(np.quantile(bootstrap_ece, 1.0 - alpha))

    class_conditional_ece = {}
    for class_label in np.unique(outcomes):
        class_mask = outcomes == class_label
        class_observations = int(class_mask.sum())
        if class_observations < stability_min_class_observations:
            continue
        class_conditional_ece[float(class_label)] = expected_calibration_error_of(
            probabilities[class_mask], outcomes[class_mask]
        )
    ece_gap = 0.0
    class_eces = list(class_conditional_ece.values())
    if len(class_eces) >= 2:
        ece_gap = abs(class_eces[0] - class_eces[1])

    prediction_variance = float(np.var(probabilities))
    if prediction_variance > 0:
        calibration_slope = float(
            np.mean((probabilities - probabilities.mean()) * (outcomes - outcomes.mean()))
            / prediction_variance
        )
        calibration_intercept = float(outcomes.mean() - calibration_slope * probabilities.mean())
    else:
        calibration_slope = None
        calibration_intercept = None
    blockers: list[DiagnosticMessage] = []
    if observation_count < min_observations:
        blockers.append(
            DiagnosticMessage(
                code="model_calibration_sample_size",
                message="Calibration sample is smaller than the configured minimum.",
                severity="blocker",
                context={"observation_count": observation_count, "minimum": min_observations},
            )
        )
    if len(np.unique(outcomes)) < 2:
        blockers.append(
            DiagnosticMessage(
                code="model_calibration_outcome_class",
                message="Calibration sample does not contain both outcome classes.",
                severity="blocker",
            )
        )
    if calibration_slope is None or calibration_intercept is None:
        blockers.append(
            DiagnosticMessage(
                code="model_prediction_variance",
                message="Probability predictions have zero variance; calibration slope is undefined.",
                severity="blocker",
            )
        )
    else:
        if not min_calibration_slope <= calibration_slope <= max_calibration_slope:
            blockers.append(
                DiagnosticMessage(
                    code="model_calibration_slope",
                    message="Linear calibration slope lies outside the configured range.",
                    severity="blocker",
                    context={
                        "slope": calibration_slope,
                        "minimum": min_calibration_slope,
                        "maximum": max_calibration_slope,
                    },
                )
            )
        if abs(calibration_intercept) > max_abs_calibration_intercept:
            blockers.append(
                DiagnosticMessage(
                    code="model_calibration_intercept",
                    message="Absolute linear calibration intercept exceeds the configured limit.",
                    severity="blocker",
                    context={
                        "intercept": calibration_intercept,
                        "limit": max_abs_calibration_intercept,
                    },
                )
            )
    for code, message, value, limit in (
        (
            "model_brier_score",
            "Brier score exceeds the configured limit.",
            brier_score,
            max_brier_score,
        ),
        ("model_log_loss", "Log loss exceeds the configured limit.", log_loss, max_log_loss),
        (
            "model_expected_calibration_error",
            "Expected calibration error exceeds the configured limit.",
            expected_calibration_error,
            max_expected_calibration_error,
        ),
    ):
        if value > limit:
            blockers.append(
                DiagnosticMessage(
                    code=code,
                    message=message,
                    severity="blocker",
                    context={"value": value, "limit": limit},
                )
            )
    if ece_gap > max_class_conditional_ece_gap:
        blockers.append(
            DiagnosticMessage(
                code="model_class_conditional_ece_gap",
                message="Class-conditional calibration error gap exceeds the configured limit.",
                severity="blocker",
                context={
                    "class_conditional_ece": class_conditional_ece,
                    "ece_gap": ece_gap,
                    "limit": max_class_conditional_ece_gap,
                },
            )
        )
    return ArtifactEnvelope(
        artifact_type="model_calibration",
        run_id=run_id,
        producer=ProducerReference(name="model-calibration", version=__version__),
        parameters={
            "model_id": model_id,
            "model_version": model_version,
            "label": label,
            "evaluated_at": evaluated.isoformat(),
            "return_basis": return_basis,
            "positive_return_threshold": positive_return_threshold,
            "bins": bins,
            "min_observations": min_observations,
            "max_brier_score": max_brier_score,
            "max_log_loss": max_log_loss,
            "max_expected_calibration_error": max_expected_calibration_error,
            "min_calibration_slope": min_calibration_slope,
            "max_calibration_slope": max_calibration_slope,
            "max_abs_calibration_intercept": max_abs_calibration_intercept,
            "bootstrap_resamples": bootstrap_resamples,
            "bootstrap_confidence": bootstrap_confidence,
            "stability_min_class_observations": stability_min_class_observations,
            "max_class_conditional_ece_gap": max_class_conditional_ece_gap,
        },
        summary={
            "observation_count": observation_count,
            "unseasoned_prediction_count": unseasoned_prediction_count,
            "positive_rate": float(outcomes.mean()),
            "mean_prediction": float(probabilities.mean()),
            "prediction_variance": prediction_variance,
            "brier_score": brier_score,
            "log_loss": log_loss,
            "expected_calibration_error": expected_calibration_error,
            "calibration_slope": calibration_slope,
            "calibration_intercept": calibration_intercept,
            "ece_ci_lower": ece_ci_lower,
            "ece_ci_upper": ece_ci_upper,
            "class_conditional_ece": class_conditional_ece,
            "class_conditional_ece_gap": ece_gap,
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            DiagnosticMessage(
                code="model_calibration_scope",
                message=(
                    "Binary threshold calibration does not establish ranking quality, economic value, "
                    "confidence intervals for the calibration slope/intercept, causal validity, "
                    "strategy PnL, or online service health. ECE uncertainty is a bootstrap interval "
                    "and class-conditional stability is a two-class ECE gap."
                ),
                severity="warning",
            )
        ],
        details=details,
        provenance={
            "prediction_timing": "available_at_or_before_decision",
            "outcome_definition": "simple_return_strictly_above_threshold",
            "calibration_fit": "linear_reliability_outcome_on_probability",
            "ece_uncertainty": "bootstrap_percentile_interval",
            "class_conditional_stability": "two_class_ece_gap",
            "live_order_submission": False,
        },
    ).finalize()
