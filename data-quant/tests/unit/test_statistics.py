from __future__ import annotations

import numpy as np
import pytest

from data_quant.statistics import (
    deflated_sharpe_ratio,
    newey_west_mean_t_stat,
    probabilistic_sharpe_ratio,
)


def test_hac_t_stat_penalizes_autocorrelation() -> None:
    rng = np.random.default_rng(0)
    persistent = np.cumsum(rng.standard_normal(300) * 0.1)
    series = persistent.tolist()
    iid_t = persistent.mean() / (persistent.std(ddof=1) / np.sqrt(len(persistent)))
    hac_t, lags = newey_west_mean_t_stat(series)
    assert lags > 0
    assert hac_t is not None
    # Strong positive autocorrelation inflates the IID t-stat; HAC must shrink it.
    assert abs(hac_t) < abs(iid_t)


def test_hac_t_stat_matches_iid_for_white_noise() -> None:
    rng = np.random.default_rng(1)
    white = rng.standard_normal(3000)
    iid_t = white.mean() / (white.std(ddof=1) / np.sqrt(len(white)))
    hac_t, _ = newey_west_mean_t_stat(white.tolist())
    assert hac_t is not None
    # White noise carries no serial dependence, so HAC and IID agree within
    # the ddof and Bartlett-weight conventions used by the two estimators.
    assert abs(hac_t - iid_t) < 0.8


def test_hac_t_stat_undefined_for_short_or_constant_series() -> None:
    assert newey_west_mean_t_stat([1.0]) == (None, 0)
    hac_t, lags = newey_west_mean_t_stat([2.0, 2.0, 2.0])
    assert hac_t is None
    assert lags >= 0


def _strong_returns() -> list[float]:
    rng = np.random.default_rng(42)
    return list(rng.standard_normal(500) * 0.01 + 0.0006)  # moderate positive SR


def _weak_returns() -> list[float]:
    rng = np.random.default_rng(7)
    noise = rng.standard_normal(100) * 0.01
    noise = noise - noise.mean()  # zero out the finite-sample drift
    # SR = 0.0001/0.01*sqrt(252) ~ 0.16 keeps PSR strictly inside (0, 1), so
    # the deflation penalty is observable instead of saturating at 1.0.
    return list(noise + 0.0001)


def test_psr_increases_with_sharpe() -> None:
    strong = _strong_returns()
    psr_high = probabilistic_sharpe_ratio(strong, benchmark_sr=0.0)
    psr_low = probabilistic_sharpe_ratio(strong, benchmark_sr=1.0)
    assert 0.0 < psr_high <= 1.0
    assert psr_low < psr_high


def test_psr_requires_variation() -> None:
    with pytest.raises(ValueError):
        probabilistic_sharpe_ratio([0.01, 0.01, 0.01, 0.01])


def test_dsr_penalizes_many_trials() -> None:
    returns = _weak_returns()
    dsr_one = deflated_sharpe_ratio(returns, num_trials=1)
    dsr_many = deflated_sharpe_ratio(returns, num_trials=1000)
    assert 0.0 <= dsr_many <= 1.0
    assert dsr_many < dsr_one


def test_dsr_num_trials_one_matches_psr() -> None:
    returns = _strong_returns()
    assert deflated_sharpe_ratio(returns, num_trials=1) == pytest.approx(
        probabilistic_sharpe_ratio(returns), abs=1e-12
    )
