"""Portfolio optimization artifacts."""

from __future__ import annotations

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.portfolio.optimizer import OptimizationResult


def optimization_artifact(
    result: OptimizationResult,
    *,
    parameters: dict,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    warnings = []
    if result.covariance_repaired:
        warnings.append(
            DiagnosticMessage(
                code="covariance_repaired",
                message="The covariance matrix was projected to a positive-semidefinite matrix.",
                severity="warning",
            )
        )
    return ArtifactEnvelope(
        artifact_type="portfolio_optimization",
        run_id=run_id,
        producer=ProducerReference(name="portfolio-optimizer", version=__version__),
        parameters=parameters,
        summary={
            "objective": result.objective,
            "objective_value": result.objective_value,
            "expected_return": result.expected_return,
            "volatility": result.volatility,
            "gross_exposure": result.gross_exposure,
            "net_exposure": result.net_exposure,
            "one_way_turnover": result.one_way_turnover,
            "covariance_repaired": result.covariance_repaired,
            "solver_message": result.solver_message,
        },
        warnings=warnings,
        details=[
            {"asset_id": str(asset), "weight": float(weight)}
            for asset, weight in result.weights.items()
        ],
    ).finalize()
