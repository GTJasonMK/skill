"""European Black-Scholes option diagnostics and implied volatility."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from scipy.optimize import brentq
from scipy.stats import norm

OptionType = Literal["call", "put"]


@dataclass(frozen=True)
class OptionAnalytics:
    price: float
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float
    d1: float
    d2: float


def black_scholes(
    spot: float,
    strike: float,
    time_to_expiry: float,
    volatility: float,
    *,
    risk_free_rate: float = 0.0,
    dividend_yield: float = 0.0,
    option_type: OptionType = "call",
) -> OptionAnalytics:
    if spot <= 0 or strike <= 0 or time_to_expiry <= 0 or volatility <= 0:
        raise ValueError("spot, strike, time_to_expiry, and volatility must be positive.")
    if option_type not in {"call", "put"}:
        raise ValueError("option_type must be call or put.")
    sqrt_t = math.sqrt(time_to_expiry)
    d1 = (
        math.log(spot / strike)
        + (risk_free_rate - dividend_yield + 0.5 * volatility**2) * time_to_expiry
    ) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t
    discounted_spot = spot * math.exp(-dividend_yield * time_to_expiry)
    discounted_strike = strike * math.exp(-risk_free_rate * time_to_expiry)
    if option_type == "call":
        price = discounted_spot * norm.cdf(d1) - discounted_strike * norm.cdf(d2)
        delta = math.exp(-dividend_yield * time_to_expiry) * norm.cdf(d1)
        carry_theta = -risk_free_rate * discounted_strike * norm.cdf(d2)
        dividend_theta = dividend_yield * discounted_spot * norm.cdf(d1)
    else:
        price = discounted_strike * norm.cdf(-d2) - discounted_spot * norm.cdf(-d1)
        delta = -math.exp(-dividend_yield * time_to_expiry) * norm.cdf(-d1)
        carry_theta = risk_free_rate * discounted_strike * norm.cdf(-d2)
        dividend_theta = -dividend_yield * discounted_spot * norm.cdf(-d1)
    density = norm.pdf(d1)
    gamma = math.exp(-dividend_yield * time_to_expiry) * density / (
        spot * volatility * sqrt_t
    )
    vega = discounted_spot * density * sqrt_t
    if option_type == "call":
        rho = time_to_expiry * discounted_strike * norm.cdf(d2)
    else:
        rho = -time_to_expiry * discounted_strike * norm.cdf(-d2)
    diffusion_theta = -(discounted_spot * density * volatility) / (2.0 * sqrt_t)
    theta = diffusion_theta + carry_theta + dividend_theta
    return OptionAnalytics(price, delta, gamma, vega, theta, rho, d1, d2)


def implied_volatility(
    market_price: float,
    spot: float,
    strike: float,
    time_to_expiry: float,
    *,
    risk_free_rate: float = 0.0,
    dividend_yield: float = 0.0,
    option_type: OptionType = "call",
    minimum_volatility: float = 1e-6,
    maximum_volatility: float = 5.0,
) -> float:
    if market_price <= 0:
        raise ValueError("market_price must be positive.")

    def error(volatility: float) -> float:
        return black_scholes(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            option_type=option_type,
        ).price - market_price

    low_error = error(minimum_volatility)
    high_error = error(maximum_volatility)
    if low_error * high_error > 0:
        raise ValueError("Market price is outside the configured implied-volatility bracket.")
    return float(brentq(error, minimum_volatility, maximum_volatility))
