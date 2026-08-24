"""Versioned factor research diagnostics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.contracts.parameters import FactorICParameters, FamaMacBethParameters
from data_quant.io.validation import parse_date_or_utc_timestamp
from data_quant.registry import register_diagnostic
from data_quant.statistics import newey_west_mean_t_stat


def summarize_values(values: list[float]) -> dict[str, float | int | None]:
    series = pd.Series(values, dtype=float).dropna()
    count = int(len(series))
    if count == 0:
        return {
            "n": 0,
            "mean": None,
            "stdev": None,
            "t_stat": None,
            "t_stat_hac": None,
            "hac_lags": 0,
            "positive_rate": None,
            "min": None,
            "max": None,
        }
    mean = float(series.mean())
    stdev = float(series.std(ddof=1)) if count >= 2 else None
    t_stat = mean / (stdev / np.sqrt(count)) if stdev is not None and stdev > 0 else None
    t_stat_hac, hac_lags = newey_west_mean_t_stat(series.tolist())
    return {
        "n": count,
        "mean": mean,
        "stdev": stdev,
        "t_stat": t_stat,
        "t_stat_hac": t_stat_hac,
        "hac_lags": hac_lags,
        "positive_rate": float((series > 0).mean()),
        "min": float(series.min()),
        "max": float(series.max()),
    }


@register_diagnostic(
    "factor-ic",
    "factor_ic",
    required_table_types=("factor_panel", "return_labels"),
    manifest_stage="research",
    parameter_model=FactorICParameters,
    description="Compute per-period Pearson IC and Spearman rank IC without claiming executable alpha.",
)
def factor_ic_artifact(
    frame: pd.DataFrame,
    *,
    date_col: str,
    factor_col: str,
    forward_return_col: str,
    min_assets: int = 5,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    if min_assets < 2:
        raise ValueError("min_assets must be at least 2.")
    required = [date_col, factor_col, forward_return_col]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Factor IC input missing columns: {missing}")
    data = frame[required].copy()
    data["_date"] = parse_date_or_utc_timestamp(data[date_col], date_col)
    data[factor_col] = pd.to_numeric(data[factor_col], errors="coerce")
    data[forward_return_col] = pd.to_numeric(data[forward_return_col], errors="coerce")
    rows_in = len(data)
    data = data.dropna(subset=["_date", factor_col, forward_return_col])
    rows_dropped = rows_in - len(data)

    details: list[dict] = []
    for timestamp, group in data.sort_values("_date").groupby("_date", sort=True):
        if len(group) < min_assets:
            continue
        ic = group[factor_col].corr(group[forward_return_col])
        rank_ic = group[factor_col].corr(group[forward_return_col], method="spearman")
        details.append(
            {
                "date": timestamp.date().isoformat()
                if timestamp.time() == pd.Timestamp(0).time()
                else timestamp.isoformat(),
                "n_assets": int(len(group)),
                "ic": None if pd.isna(ic) else float(ic),
                "rank_ic": None if pd.isna(rank_ic) else float(rank_ic),
            }
        )

    ic_values = [item["ic"] for item in details if item["ic"] is not None]
    rank_values = [item["rank_ic"] for item in details if item["rank_ic"] is not None]
    warnings: list[DiagnosticMessage] = [
        DiagnosticMessage(
            code="iid_t_stat",
            message=(
                "t_stat is the IID time-series statistic. t_stat_hac is the Newey-West HAC statistic "
                "and is the primary significance reading for autocorrelated or overlapping horizons."
            ),
            severity="warning",
        )
    ]
    evidence_gaps: list[DiagnosticMessage] = [
        DiagnosticMessage(
            code="point_in_time_not_proven",
            message=(
                "This diagnostic assumes the supplied signal and forward-return columns already passed "
                "point-in-time, execution-timing, and tradability audits."
            ),
            severity="warning",
        )
    ]
    if len(details) < 10:
        warnings.append(
            DiagnosticMessage(
                code="short_history",
                message="Fewer than ten usable periods make IC inference unstable.",
                severity="warning",
            )
        )
    artifact = ArtifactEnvelope(
        artifact_type="factor_ic",
        run_id=run_id,
        producer=ProducerReference(name="factor-ic", version=__version__),
        parameters={
            "date_col": date_col,
            "factor_col": factor_col,
            "forward_return_col": forward_return_col,
            "min_assets_per_date": min_assets,
        },
        summary={
            "rows_dropped": rows_dropped,
            "periods_used": len(details),
            "ic_summary": summarize_values(ic_values),
            "rank_ic_summary": summarize_values(rank_values),
        },
        warnings=warnings,
        evidence_gaps=evidence_gaps,
        details=details,
    )
    return artifact.finalize()


@register_diagnostic(
    "fama-macbeth",
    "fama_macbeth",
    required_table_types=("factor_panel", "return_labels"),
    manifest_stage="research",
    parameter_model=FamaMacBethParameters,
    description=(
        "Run per-period cross-sectional OLS and report HAC t-stats on the "
        "time-series of coefficients."
    ),
)
def fama_macbeth_artifact(
    frame: pd.DataFrame,
    *,
    date_col: str,
    return_col: str,
    feature_cols: list[str],
    min_assets: int = 5,
    intercept: bool = True,
    annualization: int = 12,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    """Fama-MacBeth cross-sectional regressions with autocorrelation-robust inference.

    Each period fits ``return ~ features`` (plus intercept by default); the
    risk premium is the time-series mean of each coefficient, with both IID and
    Newey-West HAC t-statistics. The HAC statistic is the primary reading for
    overlapping or autocorrelated coefficient series.
    """
    if min_assets < 2:
        raise ValueError("min_assets must be at least 2.")
    if annualization <= 0:
        raise ValueError("annualization must be positive.")
    required = [date_col, return_col, *feature_cols]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Fama-MacBeth input missing columns: {missing}")
    if len(feature_cols) != len(set(feature_cols)):
        raise ValueError("feature_cols must be unique.")

    data = frame[required].copy()
    data["_date"] = parse_date_or_utc_timestamp(data[date_col], date_col)
    for column in [return_col, *feature_cols]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    rows_in = len(data)
    data = data.dropna(subset=["_date", return_col, *feature_cols])
    rows_dropped = rows_in - len(data)

    names = (["intercept"] if intercept else []) + feature_cols
    coefficient_series: dict[str, list[float]] = {name: [] for name in names}
    by_date: list[dict] = []
    skipped_dates = 0
    for timestamp, group in data.sort_values("_date").groupby("_date", sort=True):
        if len(group) < min_assets + len(feature_cols):
            skipped_dates += 1
            continue
        y = group[return_col].to_numpy(dtype=float)
        columns = [group[c].to_numpy(dtype=float) for c in feature_cols]
        if intercept:
            X = np.column_stack([np.ones(len(group)), *columns])
        else:
            X = np.column_stack(columns)
        try:
            beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        except np.linalg.LinAlgError:
            skipped_dates += 1
            continue
        if not np.isfinite(beta).all():
            skipped_dates += 1
            continue
        fitted = X @ beta
        residuals = y - fitted
        sse = float(residuals @ residuals)
        tss = float((y - y.mean()) @ (y - y.mean()))
        r2 = 1.0 - sse / tss if tss > 0 else None
        record: dict = {
            "date": timestamp.date().isoformat()
            if timestamp.time() == pd.Timestamp(0).time()
            else timestamp.isoformat(),
            "n_assets": int(len(group)),
            "r2": r2,
            "coefficients": {name: float(beta[i]) for i, name in enumerate(names)},
        }
        by_date.append(record)
        for i, name in enumerate(names):
            coefficient_series[name].append(float(beta[i]))

    coefficient_summary = []
    for name in names:
        values = coefficient_series[name]
        base = summarize_values(values)
        row = {**base, "name": name}
        if name == "intercept" and base["mean"] is not None:
            row["annualized_mean"] = base["mean"] * annualization
        coefficient_summary.append(row)

    if len(by_date) < 2:
        raise ValueError("Fama-MacBeth requires at least two usable cross-sections.")

    artifact = ArtifactEnvelope(
        artifact_type="fama_macbeth",
        run_id=run_id,
        producer=ProducerReference(name="fama-macbeth", version=__version__),
        parameters={
            "date_col": date_col,
            "return_col": return_col,
            "feature_cols": feature_cols,
            "min_assets_per_date": min_assets,
            "intercept": intercept,
            "annualization": annualization,
        },
        summary={
            "rows_dropped": rows_dropped,
            "periods_used": len(by_date),
            "dates_skipped": skipped_dates,
            "coefficient_summary": coefficient_summary,
        },
        warnings=[
            DiagnosticMessage(
                code="iid_t_stat",
                message=(
                    "coefficient_summary reports both IID (t_stat) and Newey-West HAC "
                    "(t_stat_hac) statistics. Use t_stat_hac as the primary significance reading."
                ),
                severity="warning",
            )
        ],
        evidence_gaps=[
            DiagnosticMessage(
                code="point_in_time_not_proven",
                message=(
                    "This diagnostic assumes the supplied characteristics and forward returns "
                    "already passed point-in-time and tradability audits."
                ),
                severity="warning",
            )
        ],
        details=by_date,
    )
    return artifact.finalize()


def factor_ic_legacy_payload(artifact: ArtifactEnvelope) -> dict:
    summary = artifact.summary
    parameters = artifact.parameters
    return {
        "schema_version": artifact.schema_version,
        "artifact_type": artifact.artifact_type,
        "artifact_id": artifact.artifact_id,
        "run_id": artifact.run_id,
        "producer": artifact.producer.model_dump(mode="json"),
        "content_digest": artifact.content_digest,
        "date_col": parameters["date_col"],
        "factor_col": parameters["factor_col"],
        "forward_return_col": parameters["forward_return_col"],
        "min_assets_per_date": parameters["min_assets_per_date"],
        "rows_dropped": summary["rows_dropped"],
        "periods_used": summary["periods_used"],
        "ic_summary": summary["ic_summary"],
        "rank_ic_summary": summary["rank_ic_summary"],
        "by_date": artifact.details,
        "parameters": parameters,
        "summary": summary,
        "warnings": [item.model_dump(mode="json") for item in artifact.warnings],
        "blockers": [item.model_dump(mode="json") for item in artifact.blockers],
        "evidence_gaps": [item.model_dump(mode="json") for item in artifact.evidence_gaps],
        "notes": [
            "IC is the per-date Pearson correlation between factor values and forward returns.",
            (
                "Rank IC is the per-date Spearman correlation and is usually more robust for "
                "cross-sectional factor research."
            ),
            (
                "Rows must already respect point-in-time signal availability and the intended "
                "forward-return horizon."
            ),
        ],
    }
