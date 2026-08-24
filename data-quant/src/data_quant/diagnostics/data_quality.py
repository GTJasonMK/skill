"""Canonical-table data contract diagnostics."""

from __future__ import annotations

from typing import Any

import pandas as pd

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, InputReference, ProducerReference
from data_quant.io.validation import CanonicalTable
from data_quant.registry import register_diagnostic


def _json_scalar(value: Any) -> Any:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


@register_diagnostic(
    "data-contract",
    "data_contract",
    manifest_stage="data",
    description="Summarize a canonical table and record its validated contract.",
)
def data_contract_report(
    table: CanonicalTable,
    *,
    source_uri: str,
    input_digest: str | None = None,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    frame = table.frame
    timestamp_ranges: dict[str, dict[str, Any]] = {}
    for column in table.contract.timestamp_fields:
        if column not in frame.columns:
            continue
        values = frame[column].dropna()
        timestamp_ranges[column] = {
            "min": _json_scalar(values.min()) if not values.empty else None,
            "max": _json_scalar(values.max()) if not values.empty else None,
        }
    missing_by_column = {column: int(frame[column].isna().sum()) for column in frame.columns}
    artifact = ArtifactEnvelope(
        artifact_type="data_contract",
        run_id=run_id,
        producer=ProducerReference(name="data-contract", version=__version__),
        inputs=[
            InputReference(
                uri=source_uri,
                digest=input_digest,
                table_type=table.contract.table_type,
                schema_version=table.contract.schema_version,
                row_count=len(frame),
            )
        ],
        parameters={"contract_version": table.contract.schema_version},
        summary={
            "table_type": table.contract.table_type,
            "row_count": int(len(frame)),
            "column_count": int(len(frame.columns)),
            "columns": [str(column) for column in frame.columns],
            "primary_key": table.contract.primary_key,
            "missing_by_column": missing_by_column,
            "timestamp_ranges": timestamp_ranges,
        },
        warnings=table.warnings,
        evidence_gaps=table.evidence_gaps,
        provenance={"source_uri": source_uri},
    )
    return artifact.finalize()
