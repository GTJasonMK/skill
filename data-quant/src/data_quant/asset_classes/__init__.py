"""Asset-class-specific contracts and rules."""

from .crypto import annualized_basis, liquidation_buffer_fraction, perpetual_funding_cashflow
from .fixed_income import BondAnalytics, price_cashflows
from .futures import build_unadjusted_continuous_futures, futures_variation_margin
from .fx import convert_base_to_quote, fx_forward_outright, triangular_mispricing
from .options import OptionAnalytics, black_scholes, implied_volatility

__all__ = [
    "BondAnalytics",
    "OptionAnalytics",
    "annualized_basis",
    "black_scholes",
    "build_unadjusted_continuous_futures",
    "convert_base_to_quote",
    "futures_variation_margin",
    "fx_forward_outright",
    "implied_volatility",
    "liquidation_buffer_fraction",
    "perpetual_funding_cashflow",
    "price_cashflows",
    "triangular_mispricing",
]
