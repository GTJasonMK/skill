"""Fixed-income cashflow pricing and interest-rate risk diagnostics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BondAnalytics:
    price: float
    macaulay_duration: float
    modified_duration: float
    convexity: float


def price_cashflows(
    times_years: np.ndarray,
    cashflows: np.ndarray,
    *,
    yield_rate: float,
    compounding_frequency: int = 2,
) -> BondAnalytics:
    times = np.asarray(times_years, dtype=float)
    amounts = np.asarray(cashflows, dtype=float)
    if times.ndim != 1 or amounts.ndim != 1 or len(times) != len(amounts) or len(times) == 0:
        raise ValueError(
            "times_years and cashflows must be non-empty one-dimensional arrays of equal length."
        )
    if (times <= 0).any() or not np.isfinite(times).all() or not np.isfinite(amounts).all():
        raise ValueError("Cashflow times must be finite and positive; amounts must be finite.")
    if compounding_frequency <= 0:
        raise ValueError("compounding_frequency must be positive.")
    periodic_yield = yield_rate / compounding_frequency
    if periodic_yield <= -1:
        raise ValueError("yield_rate implies a non-positive discount base.")
    periods = times * compounding_frequency
    discount = np.power(1.0 + periodic_yield, -periods)
    present_values = amounts * discount
    price = float(present_values.sum())
    if price <= 0:
        raise ValueError("Discounted cashflows must produce a positive price.")
    macaulay = float((times * present_values).sum() / price)
    modified = macaulay / (1.0 + periodic_yield)
    convexity = float(
        (
            present_values
            * times
            * (times + 1.0 / compounding_frequency)
        ).sum()
        / (price * (1.0 + periodic_yield) ** 2)
    )
    return BondAnalytics(price, macaulay, modified, convexity)
