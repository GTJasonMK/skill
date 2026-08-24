"""Crypto perpetual funding and basis diagnostics."""

from __future__ import annotations


def perpetual_funding_cashflow(
    signed_quantity: float,
    mark_price: float,
    funding_rate: float,
) -> float:
    """Cashflow to the position; positive funding means longs pay shorts."""
    if mark_price <= 0:
        raise ValueError("mark_price must be positive.")
    return -signed_quantity * mark_price * funding_rate


def annualized_basis(
    derivative_price: float,
    spot_price: float,
    *,
    days_to_expiry: float,
) -> float:
    if derivative_price <= 0 or spot_price <= 0 or days_to_expiry <= 0:
        raise ValueError("prices and days_to_expiry must be positive.")
    return (derivative_price / spot_price - 1.0) * 365.0 / days_to_expiry


def liquidation_buffer_fraction(
    equity: float,
    maintenance_margin: float,
    position_notional: float,
) -> float:
    if position_notional <= 0:
        raise ValueError("position_notional must be positive.")
    return (equity - maintenance_margin) / position_notional
