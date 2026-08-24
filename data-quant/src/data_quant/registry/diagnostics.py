"""Registry for versioned diagnostic implementations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from data_quant.contracts.artifacts import ArtifactEnvelope

DiagnosticCallable = Callable[..., ArtifactEnvelope]


@dataclass(frozen=True)
class DiagnosticDefinition:
    diagnostic_id: str
    artifact_type: str
    implementation: DiagnosticCallable
    required_table_types: tuple[str, ...] = ()
    required_extras: tuple[str, ...] = ()
    manifest_stage: str | None = None
    parameter_model: type[BaseModel] | None = None
    description: str = ""

    @property
    def parameter_schema(self) -> dict[str, Any] | None:
        return self.parameter_model.model_json_schema() if self.parameter_model is not None else None


class DiagnosticRegistry:
    def __init__(self) -> None:
        self._items: dict[str, DiagnosticDefinition] = {}

    def register(self, definition: DiagnosticDefinition) -> None:
        if definition.diagnostic_id in self._items:
            raise ValueError(f"Diagnostic already registered: {definition.diagnostic_id}")
        if any(item.artifact_type == definition.artifact_type for item in self._items.values()):
            raise ValueError(f"Artifact type already registered: {definition.artifact_type}")
        self._items[definition.diagnostic_id] = definition

    def get(self, diagnostic_id: str) -> DiagnosticDefinition:
        try:
            return self._items[diagnostic_id]
        except KeyError as exc:
            known = ", ".join(sorted(self._items)) or "<none>"
            raise KeyError(f"Unknown diagnostic {diagnostic_id!r}. Known diagnostics: {known}") from exc

    def list(self) -> list[DiagnosticDefinition]:
        return [self._items[key] for key in sorted(self._items)]


registry = DiagnosticRegistry()


def register_diagnostic(
    diagnostic_id: str,
    artifact_type: str,
    *,
    required_table_types: tuple[str, ...] = (),
    required_extras: tuple[str, ...] = (),
    manifest_stage: str | None = None,
    parameter_model: type[BaseModel] | None = None,
    description: str = "",
) -> Callable[[DiagnosticCallable], DiagnosticCallable]:
    def decorator(function: DiagnosticCallable) -> DiagnosticCallable:
        registry.register(
            DiagnosticDefinition(
                diagnostic_id=diagnostic_id,
                artifact_type=artifact_type,
                implementation=function,
                required_table_types=required_table_types,
                required_extras=required_extras,
                manifest_stage=manifest_stage,
                parameter_model=parameter_model,
                description=description,
            )
        )
        return function

    return decorator
