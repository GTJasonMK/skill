"""Manifest-driven workflow execution."""

from .diagnostics import validate_diagnostic_specs
from .runner import RunResult, run_manifest

__all__ = ["RunResult", "run_manifest", "validate_diagnostic_specs"]
