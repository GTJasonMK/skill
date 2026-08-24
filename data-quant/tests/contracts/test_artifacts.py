from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference


def make_artifact(**overrides):
    values = {
        "artifact_type": "test_metric",
        "producer": ProducerReference(name="test", version="1"),
        "parameters": {"seed": 42},
        "summary": {"value": 1.25},
    }
    values.update(overrides)
    return ArtifactEnvelope(**values)


def test_content_digest_ignores_runtime_metadata() -> None:
    first = make_artifact(run_id="run-a").finalize()
    second = make_artifact(run_id="run-b").finalize()
    assert first.content_digest == second.content_digest
    assert first.artifact_id == first.content_digest


def test_non_finite_numbers_are_rejected() -> None:
    with pytest.raises(ValidationError, match="Non-finite"):
        make_artifact(summary={"bad": math.nan})


def test_warning_and_blocker_severity_are_enforced() -> None:
    with pytest.raises(ValidationError, match="warnings entries"):
        make_artifact(
            warnings=[DiagnosticMessage(code="bad", message="wrong severity", severity="blocker")]
        )


def test_inline_and_sidecar_details_are_mutually_exclusive() -> None:
    with pytest.raises(ValidationError, match="not both"):
        make_artifact(details=[{"x": 1}], details_uri="details.parquet")
