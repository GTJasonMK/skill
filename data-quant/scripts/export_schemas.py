#!/usr/bin/env python3
"""Export canonical JSON Schemas from the Pydantic contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from data_quant import diagnostics as _diagnostics  # noqa: E402, F401
from data_quant.contracts.artifacts import ArtifactEnvelope  # noqa: E402
from data_quant.contracts.manifest import RunManifest  # noqa: E402
from data_quant.contracts.run_record import GateRecord, RunRecord  # noqa: E402
from data_quant.contracts.tables import CONTRACTS, TableContract  # noqa: E402
from data_quant.registry import registry  # noqa: E402

SCHEMAS = {
    "artifact-envelope.schema.json": ArtifactEnvelope,
    "run-manifest.schema.json": RunManifest,
    "run-record.schema.json": RunRecord,
    "stage-gate.schema.json": GateRecord,
}


def table_row_schema(contract: TableContract) -> dict:
    type_map = {
        "string": {"type": "string"},
        "integer": {"type": "integer"},
        "number": {"type": "number"},
        "boolean": {"type": "boolean"},
        "date": {"type": "string", "format": "date"},
        "timestamp": {"type": "string", "format": "date-time"},
        "json": {},
    }
    properties: dict[str, dict] = {}
    required: list[str] = []
    for field in contract.fields:
        definition = dict(type_map[field.logical_type])
        if field.description:
            definition["description"] = field.description
        if field.unit:
            definition["x-unit"] = field.unit
        if field.nullable and definition.get("type"):
            definition["type"] = [definition["type"], "null"]
        properties[field.name] = definition
        if field.required:
            required.append(field.name)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": contract.table_type,
        "description": contract.description,
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": True,
        "x-contract-version": contract.schema_version,
        "x-primary-key": contract.primary_key,
        "x-timestamp-fields": contract.timestamp_fields,
    }


def main() -> int:
    output = ROOT / "schemas"
    output.mkdir(parents=True, exist_ok=True)
    for name, model in SCHEMAS.items():
        path = output / name
        path.write_text(
            json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(path.relative_to(ROOT))

    table_output = output / "tables"
    table_output.mkdir(parents=True, exist_ok=True)
    for table_type, contract in sorted(CONTRACTS.items()):
        path = table_output / f"{table_type}.schema.json"
        path.write_text(
            json.dumps(table_row_schema(contract), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(path.relative_to(ROOT))

    diagnostic_output = output / "diagnostics"
    diagnostic_output.mkdir(parents=True, exist_ok=True)
    for definition in registry.list():
        if definition.parameter_schema is None:
            continue
        path = diagnostic_output / f"{definition.diagnostic_id}.schema.json"
        schema = {
            **definition.parameter_schema,
            "x-diagnostic-id": definition.diagnostic_id,
            "x-manifest-stage": definition.manifest_stage,
        }
        path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
