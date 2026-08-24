"""Foreign-exchange quote, forward, and triangular-consistency helpers."""

from __future__ import annotations

import math


def fx_forward_outright(
    spot_quote_per_base: float,
    *,
    base_rate: float,
    quote_rate: float,
    time_years: float,
) -> float:
    """Covered-interest-parity forward for quote currency units per base unit."""
    if spot_quote_per_base <= 0 or time_years < 0:
        raise ValueError("spot must be positive and time_years non-negative.")
    return spot_quote_per_base * math.exp((quote_rate - base_rate) * time_years)


def convert_base_to_quote(amount_base: float, quote_per_base: float) -> float:
    if quote_per_base <= 0:
        raise ValueError("quote_per_base must be positive.")
    return amount_base * quote_per_base


def triangular_mispricing(
    quote_b_per_a: float,
    quote_c_per_b: float,
    quote_c_per_a: float,
) -> float:
    if min(quote_b_per_a, quote_c_per_b, quote_c_per_a) <= 0:
        raise ValueError("FX quotes must be positive.")
    synthetic_c_per_a = quote_b_per_a * quote_c_per_b
    return synthetic_c_per_a / quote_c_per_a - 1.0
