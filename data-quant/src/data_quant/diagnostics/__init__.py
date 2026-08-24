"""Bundled diagnostics registered with the shared runtime."""

from data_quant.monitoring import drift as monitoring

from . import asset_classes as asset_classes
from . import data_quality as data_quality
from . import execution as execution
from . import factor as factor
from . import governance as governance
from . import portfolio as portfolio
from . import risk as risk
from . import validation as validation

__all__ = [
    "asset_classes",
    "data_quality",
    "execution",
    "factor",
    "governance",
    "monitoring",
    "portfolio",
    "risk",
    "validation",
]
