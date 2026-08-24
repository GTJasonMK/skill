"""Run manifest models for reproducible Data-Quant workflows."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal
from urllib.parse import parse_qsl, urlsplit

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SourceFormat = Literal["csv", "parquet", "duckdb", "sqlite", "sql"]
AssetClass = Literal["equity", "futures", "options", "fixed_income", "fx", "crypto", "mixed", "generic"]
PipelineStage = Literal[
    "data",
    "research",
    "validation",
    "portfolio",
    "execution",
    "risk",
    "monitoring",
    "governance",
    "report",
]
ENVIRONMENT_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
SENSITIVE_URI_QUERY_KEYS = {
    "access_token",
    "api_key",
    "auth_token",
    "client_secret",
    "credential",
    "password",
    "passwd",
    "private_key",
    "pwd",
    "secret",
    "secret_key",
    "token",
}


def _default_pipeline_stages() -> list[PipelineStage]:
    return ["data", "report"]


def _sensitive_parameter_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        matches = [
            str(key)
            for key in value
            if str(key).lower().replace("-", "_") in SENSITIVE_URI_QUERY_KEYS
        ]
        for nested in value.values():
            matches.extend(_sensitive_parameter_keys(nested))
        return matches
    if isinstance(value, list):
        return [key for item in value for key in _sensitive_parameter_keys(item)]
    return []


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, hide_input_in_errors=True)


class ProjectSpec(StrictModel):
    name: str = Field(min_length=1)
    asset_class: AssetClass = "generic"
    base_currency: str = Field(default="USD", min_length=3, max_length=8)
    benchmark: str | None = None
    description: str | None = None


class DataSourceSpec(StrictModel):
    id: str = Field(min_length=1)
    uri: str = Field(min_length=1)
    format: SourceFormat
    table_type: str = Field(min_length=1)
    contract_version: str = "1.0"
    column_mapping: dict[str, str] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)
    credential_env: list[str] = Field(default_factory=list)

    @field_validator("uri")
    @classmethod
    def uri_cannot_embed_credentials(cls, value: str) -> str:
        if "://" not in value:
            return value
        try:
            parsed = urlsplit(value)
        except ValueError as exc:
            raise ValueError("uri is malformed.") from exc
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("uri cannot contain embedded credentials or userinfo.")
        query_keys = {
            key.casefold().replace("-", "_")
            for key, _ in parse_qsl(parsed.query, keep_blank_values=True)
        }
        if query_keys & SENSITIVE_URI_QUERY_KEYS:
            raise ValueError("uri cannot contain credential-bearing query parameters.")
        return value

    @field_validator("credential_env")
    @classmethod
    def credentials_are_names_only(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("credential_env names must be unique.")
        for value in values:
            if ENVIRONMENT_NAME.fullmatch(value) is None:
                raise ValueError("credential_env contains environment-variable names, never values.")
        return values


class CalendarSpec(StrictModel):
    calendar_id: str = Field(min_length=1)
    timezone: str = Field(min_length=1)
    sessions_source: str | None = Field(
        default=None,
        description="ID of the declared calendar_sessions data source for this calendar.",
    )


class ExecutionSpec(StrictModel):
    mode: Literal["offline_replay", "paper_simulation"] = "offline_replay"
    live_order_submission: Literal[False] = False
    fund_transfer: Literal[False] = False
    credential_storage: Literal[False] = False


class DiagnosticSpec(StrictModel):
    diagnostic_id: str = Field(min_length=1)
    stage: PipelineStage
    input_sources: list[str] = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("input_sources")
    @classmethod
    def input_sources_are_unique(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("Diagnostic input_sources must be unique.")
        return values

    @field_validator("parameters")
    @classmethod
    def parameters_cannot_contain_secrets(cls, values: dict[str, Any]) -> dict[str, Any]:
        sensitive = sorted(set(_sensitive_parameter_keys(values)))
        if sensitive:
            raise ValueError(f"Diagnostic parameters contain sensitive keys: {sensitive}")
        return values


class PipelineSpec(StrictModel):
    stages: list[PipelineStage] = Field(default_factory=_default_pipeline_stages)
    diagnostics: list[DiagnosticSpec] = Field(default_factory=list)
    required_diagnostics: list[str] = Field(default_factory=list)
    fail_closed: bool = True
    cache: bool = True

    @field_validator("stages", "required_diagnostics")
    @classmethod
    def identifiers_are_unique_and_nonempty(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("Pipeline stage and diagnostic identifiers cannot be empty.")
        if len(values) != len(set(values)):
            raise ValueError("Pipeline stage and diagnostic identifiers must be unique.")
        return values

    @model_validator(mode="after")
    def diagnostics_match_pipeline_stages(self) -> PipelineSpec:
        if not self.stages or self.stages[0] != "data":
            raise ValueError("Pipeline stages must start with data.")
        if "report" in self.stages and self.stages[-1] != "report":
            raise ValueError("The report stage must be last.")
        canonical_order: list[PipelineStage] = [
            "data",
            "research",
            "validation",
            "portfolio",
            "execution",
            "risk",
            "monitoring",
            "governance",
            "report",
        ]
        positions = [canonical_order.index(stage) for stage in self.stages]
        if positions != sorted(positions):
            raise ValueError("Pipeline stages must follow the canonical stage order.")
        diagnostic_ids = [spec.diagnostic_id for spec in self.diagnostics]
        if len(diagnostic_ids) != len(set(diagnostic_ids)):
            raise ValueError("Pipeline diagnostic_id values must be unique.")
        undeclared_stages = sorted({spec.stage for spec in self.diagnostics} - set(self.stages))
        if undeclared_stages:
            raise ValueError(f"Diagnostic stages are absent from pipeline.stages: {undeclared_stages}")
        return self


class RunManifest(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    project: ProjectSpec
    data_sources: list[DataSourceSpec] = Field(min_length=1)
    calendar: CalendarSpec | None = None
    universe: dict[str, Any] = Field(default_factory=dict)
    signals: dict[str, Any] = Field(default_factory=dict)
    labels: dict[str, Any] = Field(default_factory=dict)
    validation: dict[str, Any] = Field(default_factory=dict)
    portfolio: dict[str, Any] = Field(default_factory=dict)
    costs: dict[str, Any] = Field(default_factory=dict)
    execution: ExecutionSpec = Field(default_factory=ExecutionSpec)
    risk: dict[str, Any] = Field(default_factory=dict)
    monitoring: dict[str, Any] = Field(default_factory=dict)
    pipeline: PipelineSpec = Field(default_factory=PipelineSpec)
    output_dir: str = "runs"
    seed: int = 42
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("data_sources")
    @classmethod
    def unique_source_ids(cls, values: list[DataSourceSpec]) -> list[DataSourceSpec]:
        ids = [item.id for item in values]
        if len(ids) != len(set(ids)):
            raise ValueError("data_sources IDs must be unique.")
        return values

    @field_validator(
        "universe",
        "signals",
        "labels",
        "validation",
        "portfolio",
        "costs",
        "risk",
        "monitoring",
        "metadata",
    )
    @classmethod
    def freeform_sections_cannot_contain_secrets(cls, values: dict[str, Any]) -> dict[str, Any]:
        sensitive = sorted(set(_sensitive_parameter_keys(values)))
        if sensitive:
            raise ValueError(f"Manifest section contains sensitive keys: {sensitive}")
        return values

    @model_validator(mode="after")
    def calendar_sessions_source_is_declared(self) -> RunManifest:
        if self.calendar is None or self.calendar.sessions_source is None:
            return self
        sources = {source.id: source for source in self.data_sources}
        source = sources.get(self.calendar.sessions_source)
        if source is None:
            raise ValueError("calendar.sessions_source must reference a declared data source ID.")
        if source.table_type != "calendar_sessions":
            raise ValueError("calendar.sessions_source must reference a calendar_sessions table.")
        return self

    @model_validator(mode="after")
    def diagnostic_inputs_are_declared(self) -> RunManifest:
        source_ids = {source.id for source in self.data_sources}
        for diagnostic in self.pipeline.diagnostics:
            missing = sorted(set(diagnostic.input_sources) - source_ids)
            if missing:
                raise ValueError(
                    f"Diagnostic {diagnostic.diagnostic_id!r} references undeclared inputs: {missing}"
                )
        return self

    @classmethod
    def from_yaml(cls, path: str | Path) -> RunManifest:
        file_path = Path(path)
        payload = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Run manifest must contain a YAML object at the root.")
        return cls.model_validate(payload)
