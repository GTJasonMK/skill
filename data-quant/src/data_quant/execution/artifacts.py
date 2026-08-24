"""Offline execution replay artifacts."""

from __future__ import annotations

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.execution.accounting import ReconciliationResult
from data_quant.execution.replay import ReplayResult


def replay_artifact(
    replay: ReplayResult,
    reconciliation: ReconciliationResult,
    *,
    parameters: dict,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    outcomes = replay.order_outcomes
    status_counts = outcomes["status"].value_counts().to_dict() if not outcomes.empty else {}
    quality = (
        outcomes.dropna(subset=["implementation_shortfall_bps"])
        if not outcomes.empty
        else outcomes
    )
    weighted_shortfall = (
        float(
            (quality["implementation_shortfall_bps"] * quality["filled_quantity"]).sum()
            / quality["filled_quantity"].sum()
        )
        if not quality.empty and quality["filled_quantity"].sum() > 0
        else None
    )
    return ArtifactEnvelope(
        artifact_type="execution_replay",
        run_id=run_id,
        producer=ProducerReference(name="offline-execution-replay", version=__version__),
        parameters=parameters,
        summary={
            "order_count": int(len(outcomes)),
            "fill_count": int(len(replay.fills)),
            "status_counts": {str(key): int(value) for key, value in status_counts.items()},
            "aggregate_fill_rate": (
                float(outcomes["filled_quantity"].sum() / outcomes["requested_quantity"].sum())
                if not outcomes.empty
                else None
            ),
            "traded_notional": reconciliation.traded_notional,
            "total_fees": reconciliation.total_fees,
            "quantity_weighted_implementation_shortfall_bps": weighted_shortfall,
            "mean_arrival_to_first_fill_seconds": (
                float(outcomes["arrival_to_first_fill_seconds"].dropna().mean())
                if not outcomes.empty
                and not outcomes["arrival_to_first_fill_seconds"].dropna().empty
                else None
            ),
            "ending_cash": reconciliation.cash,
            "market_value": reconciliation.market_value,
            "ending_nav": reconciliation.nav,
            "fidelity": "offline_quote_replay",
        },
        evidence_gaps=[
            DiagnosticMessage(
                code="execution_replay_scope",
                message=(
                    "Quote replay models participation, market/limit price, expiry, IOC, "
                    "linear/square-root impact, and explicit queue_priority; it does not reconstruct "
                    "hidden liquidity, amendments, or venue outages."
                ),
                severity="warning",
            )
        ],
        details=outcomes.to_dict("records"),
        provenance={"live_order_submission": False, "order_lifecycle": "deterministic_quote_replay"},
    ).finalize()
