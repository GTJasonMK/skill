"""Official source-card freshness and confidence gates."""

from __future__ import annotations

import pandas as pd

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.contracts.parameters import SourceRuleFreshnessParameters
from data_quant.io.validation import parse_utc_timestamp
from data_quant.registry import register_diagnostic


@register_diagnostic(
    "source-rule-freshness",
    "source_rule_freshness",
    required_table_types=("source_cards",),
    manifest_stage="governance",
    parameter_model=SourceRuleFreshnessParameters,
    description="Gate required official/vendor source cards on presence, freshness, and confidence.",
)
def source_rule_freshness_artifact(
    cards: pd.DataFrame,
    approvals: pd.DataFrame | None = None,
    *,
    required_source_ids: list[str],
    evaluated_at: str,
    max_card_age: str = "365D",
    require_authoritative: bool = True,
    require_change_approval: bool = False,
    max_approval_age: str = "365D",
    run_id: str | None = None,
) -> ArtifactEnvelope:
    maximum_age = pd.Timedelta(max_card_age)
    maximum_approval_age = pd.Timedelta(max_approval_age)
    if (
        not required_source_ids
        or len(required_source_ids) != len(set(required_source_ids))
        or maximum_age <= pd.Timedelta(0)
    ):
        raise ValueError("Source-rule IDs or max_card_age are invalid.")
    evaluated = parse_utc_timestamp(pd.Series([evaluated_at]), "evaluated_at").iloc[0]
    frame = cards.copy()
    frame["accessed_at"] = parse_utc_timestamp(frame["accessed_at"], "accessed_at")
    frame = frame[frame["accessed_at"] <= evaluated].copy()
    approval_frame = None
    if require_change_approval:
        if approvals is None:
            raise ValueError("require_change_approval needs a source_change_approvals input.")
        approval_frame = approvals.copy()
        for column in ("requested_at", "approved_at"):
            approval_frame[column] = parse_utc_timestamp(approval_frame[column], column)
        approval_frame = approval_frame[
            (approval_frame["approved_at"] <= evaluated)
            & approval_frame["status"].astype(str).eq("approved")
            & approval_frame["action"].astype(str).isin({"refresh", "add", "retire"})
        ].copy()
        if (approval_frame["approved_at"] < approval_frame["requested_at"]).any():
            raise ValueError("Source approvals cannot precede their request timestamps.")
    blockers: list[DiagnosticMessage] = []
    details = []
    for source_id in required_source_ids:
        matches = frame[frame["source_id"].astype(str) == source_id]
        if matches.empty:
            blockers.append(
                DiagnosticMessage(
                    code="source_card_missing",
                    message=f"Required source card {source_id!r} is not observable by evaluated_at.",
                    severity="blocker",
                    context={"source_id": source_id},
                )
            )
            details.append({"source_id": source_id, "status": "missing"})
            continue
        card = matches.sort_values("accessed_at").iloc[-1]
        age = evaluated - pd.Timestamp(card["accessed_at"])
        confidence = str(card["confidence"])
        detail = {
            "source_id": source_id,
            "source_kind": str(card["source_kind"]),
            "accessed_at": pd.Timestamp(card["accessed_at"]).isoformat(),
            "confidence": confidence,
            "age": str(age),
            "status": "pass",
        }
        if age > maximum_age:
            detail["status"] = "stale"
            blockers.append(
                DiagnosticMessage(
                    code="source_card_stale",
                    message=f"Source card {source_id!r} exceeds max_card_age.",
                    severity="blocker",
                    context=detail,
                )
            )
        elif require_authoritative and confidence != "authoritative":
            detail["status"] = "confidence"
            blockers.append(
                DiagnosticMessage(
                    code="source_card_confidence",
                    message=f"Source card {source_id!r} is not authoritative.",
                    severity="blocker",
                    context=detail,
                )
            )
        elif require_change_approval and approval_frame is not None:
            latest = approval_frame[approval_frame["source_id"].astype(str) == source_id]
            if latest.empty:
                detail["status"] = "unapproved"
                blockers.append(
                    DiagnosticMessage(
                        code="source_change_unapproved",
                        message=f"Source card {source_id!r} has no approved change record.",
                        severity="blocker",
                        context=detail,
                    )
                )
            else:
                approved_at = pd.Timestamp(latest.sort_values("approved_at").iloc[-1]["approved_at"])
                if evaluated - approved_at > maximum_approval_age:
                    detail["status"] = "approval_stale"
                    blockers.append(
                        DiagnosticMessage(
                            code="source_change_approval_stale",
                            message=f"Source card {source_id!r} approval exceeds max_approval_age.",
                            severity="blocker",
                            context={**detail, "approved_at": approved_at.isoformat()},
                        )
                    )
                else:
                    detail["approved_at"] = approved_at.isoformat()
        details.append(detail)
    return ArtifactEnvelope(
        artifact_type="source_rule_freshness",
        run_id=run_id,
        producer=ProducerReference(name="source-rule-freshness", version=__version__),
        parameters={
            "required_source_ids": required_source_ids,
            "evaluated_at": evaluated.isoformat(),
            "max_card_age": str(maximum_age),
            "require_authoritative": require_authoritative,
            "require_change_approval": require_change_approval,
            "max_approval_age": str(maximum_approval_age),
        },
        summary={
            "required_source_count": len(required_source_ids),
            "observed_source_count": sum(1 for row in details if row["status"] != "missing"),
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            DiagnosticMessage(
                code="source_rule_freshness_scope",
                message=(
                    "Card presence, age, and offline change approvals do not retrieve upstream "
                    "documents or prove that runtime adapters ingested the current rule values."
                ),
                severity="warning",
            )
        ],
        details=details,
        provenance={
            "card_selection": "latest_accessed_at_or_before_evaluation",
            "change_approval": "offline_approved_refresh_add_or_retire",
            "live_order_submission": False,
        },
    ).finalize()
