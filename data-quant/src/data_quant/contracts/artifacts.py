"""Versioned artifact envelope shared by every Data-Quant diagnostic."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Severity = Literal["info", "warning", "blocker"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class DiagnosticMessage(StrictModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    severity: Severity = "warning"
    context: dict[str, Any] = Field(default_factory=dict)


class InputReference(StrictModel):
    uri: str = Field(min_length=1)
    digest: str | None = None
    table_type: str | None = None
    schema_version: str | None = None
    row_count: int | None = Field(default=None, ge=0)


class ProducerReference(StrictModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


def _reject_non_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Non-finite numeric value at {path}; use null instead.")
    if isinstance(value, dict):
        for key, child in value.items():
            _reject_non_finite(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_non_finite(child, f"{path}[{index}]")


class ArtifactEnvelope(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    artifact_type: str = Field(min_length=1)
    artifact_id: str | None = None
    run_id: str | None = None
    producer: ProducerReference
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    content_digest: str | None = None
    inputs: list[InputReference] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)
    warnings: list[DiagnosticMessage] = Field(default_factory=list)
    blockers: list[DiagnosticMessage] = Field(default_factory=list)
    evidence_gaps: list[DiagnosticMessage] = Field(default_factory=list)
    details: list[dict[str, Any]] = Field(default_factory=list)
    details_uri: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_json_numbers(self) -> ArtifactEnvelope:
        _reject_non_finite(self.parameters, "$.parameters")
        _reject_non_finite(self.summary, "$.summary")
        _reject_non_finite(self.details, "$.details")
        _reject_non_finite(self.provenance, "$.provenance")
        if self.details and self.details_uri:
            raise ValueError("Use inline details or details_uri, not both.")
        if any(item.severity != "warning" for item in self.warnings):
            raise ValueError("warnings entries must use severity='warning'.")
        if any(item.severity != "blocker" for item in self.blockers):
            raise ValueError("blockers entries must use severity='blocker'.")
        return self

    def digest_payload(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json")
        for field in ("artifact_id", "run_id", "created_at", "content_digest"):
            payload.pop(field, None)
        return payload

    def compute_content_digest(self) -> str:
        encoded = json.dumps(
            self.digest_payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    def finalize(self) -> ArtifactEnvelope:
        self.content_digest = self.compute_content_digest()
        if self.artifact_id is None:
            self.artifact_id = self.content_digest
        return self
