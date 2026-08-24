"""Diagnostic and adapter registries."""

from .diagnostics import DiagnosticDefinition, DiagnosticRegistry, register_diagnostic, registry

__all__ = ["DiagnosticDefinition", "DiagnosticRegistry", "register_diagnostic", "registry"]
