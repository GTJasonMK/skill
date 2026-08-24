"""Shared runtime for the Data-Quant skill bundle."""

from .contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, InputReference
from .contracts.manifest import RunManifest
from .contracts.run_record import RunRecord

__all__ = [
    "ArtifactEnvelope",
    "DiagnosticMessage",
    "InputReference",
    "RunManifest",
    "RunRecord",
]

__version__ = "0.1.0"
