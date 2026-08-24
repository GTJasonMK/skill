"""Auditable run and stage-gate records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Stage = Literal[
    "idea",
    "research_candidate",
    "validated_component",
    "portfolio_candidate",
    "paper_trading",
    "production_candidate",
    "live_monitoring",
    "retired",
]
Decision = Literal["pass", "conditional_pass", "review", "fail"]
Action = Literal["promote", "hold", "downgrade", "reject", "pause", "retire"]
ClaimStrength = Literal[
    "not_determinable",
    "research_only",
    "validated_component",
    "portfolio_candidate",
    "paper_candidate",
    "production_candidate",
]
HandoffStatus = Literal["ready", "needs_input", "blocked", "complete"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class StageHandoff(StrictModel):
    stage: str = Field(min_length=1)
    status: HandoffStatus
    primary_decision: str = Field(min_length=1)
    artifact_ids: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    checks_completed: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    next_stage: str | None = None


class ExperimentRecord(StrictModel):
    experiment_id: str = Field(min_length=1)
    baseline_id: str = Field(min_length=1)
    defect_hypothesis: str = Field(min_length=1)
    changed_element: str = Field(min_length=1)
    expected_change: str = Field(min_length=1)
    artifact_ids: list[str] = Field(default_factory=list)
    result: str | None = None
    decision: str | None = None


class GateRecord(StrictModel):
    gate: str = Field(min_length=1)
    decision: Decision
    action: Action
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)


class RunRecord(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    run_id: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    task_type: str = Field(min_length=1)
    object_type: str = Field(min_length=1)
    claim_side: str = Field(min_length=1)
    timing: dict[str, Any] = Field(default_factory=dict)
    baseline_id: str | None = None
    observed_phenomena: list[str] = Field(default_factory=list)
    defect_class: str | None = None
    references_used: list[str] = Field(default_factory=list)
    input_artifact_ids: list[str] = Field(default_factory=list)
    output_artifact_ids: list[str] = Field(default_factory=list)
    handoffs: list[StageHandoff] = Field(default_factory=list)
    experiments: list[ExperimentRecord] = Field(default_factory=list)
    rejected_variants: list[dict[str, Any]] = Field(default_factory=list)
    gates: list[GateRecord] = Field(default_factory=list)
    stage: Stage = "idea"
    decision: Decision = "review"
    action: Action = "hold"
    claim_strength: ClaimStrength = "not_determinable"
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    decision_changers: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
