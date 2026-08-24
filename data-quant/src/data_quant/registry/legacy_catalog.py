"""Inventory and Artifact adapters for the 64 legacy diagnostic CLIs."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.paths import source_bundle_root

LEGACY_SCRIPT_NAMES = (
    "alpha_research_gate_report.py",
    "anomaly_score_report.py",
    "bootstrap_reality_check.py",
    "calibration_report.py",
    "capacity_impact_report.py",
    "causal_balance_check.py",
    "classification_report.py",
    "cluster_quality_report.py",
    "compare_model_reports.py",
    "covariance_report.py",
    "cross_sectional_return_regression.py",
    "data_freshness_report.py",
    "event_study_report.py",
    "ewma_volatility.py",
    "execution_slippage_report.py",
    "execution_timing_audit.py",
    "factor_decay_report.py",
    "factor_exposure_regression.py",
    "factor_ic_report.py",
    "factor_neutralization.py",
    "factor_quantile_report.py",
    "factor_turnover_report.py",
    "fama_macbeth_regression.py",
    "go_live_gate_report.py",
    "incremental_alpha_report.py",
    "limit_breach_report.py",
    "live_vs_paper_report.py",
    "long_short_backtest.py",
    "missingness_report.py",
    "model_risk_register_report.py",
    "multiple_testing_report.py",
    "newey_west_regression.py",
    "optimizer_sensitivity_report.py",
    "order_exception_report.py",
    "pairs_spread_report.py",
    "panel_summary.py",
    "pca_risk_model.py",
    "performance_attribution_report.py",
    "point_in_time_audit.py",
    "portfolio_backtest.py",
    "portfolio_constraint_check.py",
    "portfolio_construction_gate_report.py",
    "portfolio_exposure_report.py",
    "profile_dataset.py",
    "quant_checklist_template.py",
    "quant_experiment_audit.py",
    "quant_report_aggregator.py",
    "quant_review_pack.py",
    "regime_robustness_report.py",
    "returns_risk_report.py",
    "risk_contribution_report.py",
    "risk_forecast_calibration.py",
    "rolling_beta.py",
    "signal_health_monitor.py",
    "signal_overlap_report.py",
    "sklearn_tabular_model.py",
    "split_dataset.py",
    "strategy_action_decision.py",
    "survival_km_report.py",
    "threshold_tuning.py",
    "time_series_backtest.py",
    "tradability_audit.py",
    "transaction_cost_report.py",
    "walk_forward_stability.py",
)

ARTIFACT_TYPE_OVERRIDES = {
    "alpha-research-gate-report": "alpha_research_gate",
    "factor-ic-report": "factor_ic",
    "point-in-time-audit": "point_in_time_audit",
    "execution-timing-audit": "execution_timing_audit",
    "tradability-audit": "tradability_audit",
    "portfolio-construction-gate-report": "portfolio_construction_gate",
    "go-live-gate-report": "go_live_gate",
}


def diagnostic_id(script_name: str) -> str:
    return Path(script_name).stem.replace("_", "-")


def artifact_type(script_name: str) -> str:
    identifier = diagnostic_id(script_name)
    return ARTIFACT_TYPE_OVERRIDES.get(identifier, Path(script_name).stem)


def catalog() -> list[dict[str, str | bool]]:
    directory = legacy_script_dir()
    items: list[dict[str, str | bool]] = []
    for name in LEGACY_SCRIPT_NAMES:
        available = directory is not None and (directory / name).is_file()
        items.append(
            {
                "diagnostic_id": diagnostic_id(name),
                "artifact_type": artifact_type(name),
                "legacy_script": name,
                "execution_mode": "legacy_cli" if available else "source_bundle_required",
                "available": available,
                "invocation": "quantctl_diagnostic" if available else "source_bundle_required",
                "description": (
                    "Compatibility CLI from the full source Skill bundle."
                    if available
                    else "Catalog entry only; install or use the full source Skill bundle to execute it."
                ),
            }
        )
    return items


def legacy_script_dir() -> Path | None:
    root = source_bundle_root()
    return None if root is None else root / "statistical-learning-analysis" / "scripts"


def run_legacy_cli(
    identifier: str,
    arguments: list[str],
    *,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    entries = {str(entry["diagnostic_id"]): entry for entry in catalog()}
    if identifier not in entries:
        raise ValueError(f"Unknown legacy diagnostic: {identifier}")
    entry = entries[identifier]
    directory = legacy_script_dir()
    if directory is None:
        raise RuntimeError(
            "Legacy diagnostics require the full source Skill bundle; the runtime-only wheel "
            "contains the Python core but not compatibility scripts."
        )
    script = directory / str(entry["legacy_script"])
    if not script.is_file():
        raise RuntimeError(f"Legacy diagnostic script is unavailable: {entry['legacy_script']}")
    caller_cwd = Path.cwd()
    source = script.read_text(encoding="utf-8")
    command_args = list(arguments)
    if command_args and command_args[0] == "--":
        command_args = command_args[1:]

    with tempfile.TemporaryDirectory(prefix="data-quant-legacy-") as temporary:
        report_path: Path | None = None
        if identifier == "sklearn-tabular-model":
            if "--output-dir" in command_args:
                index = command_args.index("--output-dir")
                if index + 1 >= len(command_args):
                    raise ValueError("--output-dir requires a path.")
                output_dir = Path(command_args[index + 1])
                if not output_dir.is_absolute():
                    output_dir = (caller_cwd / output_dir).resolve()
                command_args[index + 1] = str(output_dir)
            else:
                output_dir = Path(temporary)
                command_args.extend(["--output-dir", str(output_dir)])
            report_path = output_dir / "model_report.json"
        elif identifier == "split-dataset":
            if "--output-dir" in command_args:
                index = command_args.index("--output-dir")
                if index + 1 >= len(command_args):
                    raise ValueError("--output-dir requires a path.")
                output_dir = Path(command_args[index + 1])
                if not output_dir.is_absolute():
                    output_dir = (caller_cwd / output_dir).resolve()
                command_args[index + 1] = str(output_dir)
            else:
                command_args.extend(["--output-dir", temporary])
        elif "--format" in source:
            if "--format" not in command_args:
                command_args.extend(["--format", "json"])
        elif identifier != "split-dataset":
            raise ValueError(
                f"Legacy diagnostic {identifier!r} does not expose a supported JSON result."
            )

        result = subprocess.run(
            [sys.executable, str(script), *command_args],
            cwd=caller_cwd,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Legacy diagnostic {identifier!r} failed with exit {result.returncode}: "
                f"{result.stderr.strip()}"
            )
        json_text = report_path.read_text(encoding="utf-8") if report_path else result.stdout
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Legacy diagnostic {identifier!r} did not emit valid JSON.") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("Legacy diagnostic JSON root must be an object.")
    return ArtifactEnvelope(
        artifact_type=str(entry["artifact_type"]),
        run_id=run_id,
        producer=ProducerReference(name=identifier, version=__version__),
        parameters={"legacy_arguments": command_args},
        summary={"legacy_payload": payload},
        warnings=[
            DiagnosticMessage(
                code="legacy_payload_adapter",
                message=(
                    "This Artifact wraps a compatibility CLI payload. Migrate consumers to the normalized "
                    "summary/details contract before removing legacy aliases."
                ),
                severity="warning",
            )
        ],
        provenance={"legacy_script": str(script), "legacy_exit_code": result.returncode},
    ).finalize()
