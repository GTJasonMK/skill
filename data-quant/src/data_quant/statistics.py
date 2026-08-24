"""Small autocorrelation-robust statistics for native diagnostics.

The bundled legacy CLIs implement HAC inference per-report, but the native
Manifest path previously reported only IID time-series t-statistics. These
helpers let factor/signal diagnostics default to a Newey-West HAC mean t-stat
so the reported significance no longer ignores serial dependence in IC and
other overlapping or autocorrelated series.

The module also carries Bailey & López de Prado's Probabilistic Sharpe Ratio
(PSR) and Deflated Sharpe Ratio (DSR), which account for non-normal return
skew/kurtosis and, for DSR, the number of trials behind a selected strategy.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import f as f_dist
from scipy.stats import kurtosis, norm, skew


def _newvey_west_lag_count(n: int) -> int:
    """Newey-West (1994) default truncation lag: floor(4*(n/100)^(2/9))."""
    return max(0, int(math.floor(4.0 * (n / 100.0) ** (2.0 / 9.0))))


def newey_west_mean_t_stat(values: list[float], lags: int | None = None) -> tuple[float | None, int]:
    """Return (HAC mean t-stat, lag count) for a scalar time series.

    Uses a Bartlett kernel long-run variance estimator. With ``lags=None`` the
    truncation lag follows Newey-West (1994). Returns ``(None, lag_count)`` when
    fewer than two observations or a zero variance make the statistic undefined.
    """
    series: np.ndarray = np.asarray([float(value) for value in values], dtype=float)
    n = series.size
    if n < 2:
        return None, 0
    lags = _newvey_west_lag_count(n) if lags is None else max(0, int(lags))
    residuals = series - series.mean()
    gamma_0 = float(residuals @ residuals) / n
    long_run = gamma_0
    for k in range(1, min(lags, n - 1) + 1):
        weight = 1.0 - k / (lags + 1.0)
        gamma_k = float(residuals[k:] @ residuals[:-k]) / n
        long_run += 2.0 * weight * gamma_k
    variance_of_mean = long_run / n
    if variance_of_mean <= 0:
        return None, lags
    return float(series.mean() / math.sqrt(variance_of_mean)), lags


def _annualized_moments(
    returns: list[float], periods_per_year: int
) -> tuple[float, float, float, int]:
    """Return (annualized SR, annualized volatility, skew, n) from periodic returns.

    Uses sample skewness (Fisher-Pearson, ddof-adjusted) and annualizes mean
    and volatility geometrically as ``sqrt(periods)``.
    """
    series: np.ndarray = np.asarray([float(value) for value in returns], dtype=float)
    n = series.size
    if n < 3 or periods_per_year <= 0:
        raise ValueError("PSR requires at least three returns and a positive periods_per_year.")
    if series.std(ddof=1) == 0:
        raise ValueError("PSR requires non-zero return volatility.")
    mean = float(series.mean())
    stdev = float(series.std(ddof=1))
    sharpe = mean / stdev * math.sqrt(periods_per_year)
    sample_skew = skew(series, bias=True)
    return sharpe, stdev * math.sqrt(periods_per_year), float(sample_skew), n


def probabilistic_sharpe_ratio(
    returns: list[float],
    *,
    benchmark_sr: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """Bailey & López de Prado Probabilistic Sharpe Ratio.

    Probability that the true Sharpe ratio exceeds ``benchmark_sr`` given the
    observed return sample, accounting for skewness and kurtosis through the
    non-normal correction. Returns a value in (0, 1).
    """
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive.")
    sharpe, annual_vol, skew, n = _annualized_moments(returns, periods_per_year)
    sample_kurtosis = kurtosis(returns, fisher=False, bias=True)
    numerator = (sharpe - benchmark_sr) * math.sqrt(n - 1)
    denominator = math.sqrt(
        1.0
        - skew * sharpe
        + (sample_kurtosis - 1.0) / 4.0 * sharpe**2
    )
    if denominator <= 0:
        return 0.0
    return float(norm.cdf(numerator / denominator))


def deflated_sharpe_ratio(
    returns: list[float],
    *,
    benchmark_sr: float = 0.0,
    periods_per_year: int = 252,
    num_trials: int = 1,
    sharpe_variance: float | None = None,
) -> float:
    """Bailey & López de Prado Deflated Sharpe Ratio.

    Shrinks the observed Sharpe by the expected maximum of ``num_trials`` draws
    before computing PSR, penalizing a strategy selected after many tests. When
    ``sharpe_variance`` is None the variance of the trial Sharpe ratios is
    estimated from the returns themselves.
    """
    if num_trials < 1:
        raise ValueError("num_trials must be at least 1.")
    sharpe, _, skew, n = _annualized_moments(returns, periods_per_year)
    if sharpe_variance is None:
        sharpe_variance = float(np.var(returns, ddof=1))
    if sharpe_variance < 0:
        raise ValueError("sharpe_variance must be non-negative.")
    if num_trials == 1:
        expected_max = 0.0
    else:
        euler_gamma = 0.5772156649015329
        expected_max = math.sqrt(sharpe_variance) * (
            (1.0 - euler_gamma) * norm.ppf(1.0 - 1.0 / num_trials)
            + euler_gamma * norm.ppf(1.0 - 1.0 / (num_trials * math.e))
        )
    deflated_sharpe = sharpe - expected_max
    sample_kurtosis = kurtosis(returns, fisher=False, bias=True)
    numerator = (deflated_sharpe - benchmark_sr) * math.sqrt(n - 1)
    denominator = math.sqrt(
        1.0
        - skew * deflated_sharpe
        + (sample_kurtosis - 1.0) / 4.0 * deflated_sharpe**2
    )
    if denominator <= 0:
        return 0.0
    return float(norm.cdf(numerator / denominator))


def gibbons_ross_shanken_test(
    asset_returns: list[list[float]],
    factor_returns: list[list[float]],
) -> dict[str, float | int]:
    """Gibbons, Ross & Shanken (1989) joint-alpha test.

    ``asset_returns`` is a ``T x N`` matrix (rows are periods, columns are test
    assets). ``factor_returns`` is a ``T x L`` matrix (rows are periods, columns
    are factors). Each test asset is regressed on the factors plus an intercept;
    the GRS statistic jointly tests that all intercepts are zero.

    Returns ``{"grs": ..., "p_value": ..., "n_assets": ..., "n_factors": ...,
    "n_periods": ...}``. The statistic is distributed F(N, T-N-L) under the
    null. Raises ``ValueError`` when the sample is too small to leave residual
    degrees of freedom or when the design is rank-deficient.
    """
    assets: np.ndarray = np.asarray(asset_returns, dtype=float)
    factors: np.ndarray = np.asarray(factor_returns, dtype=float)
    if assets.ndim != 2 or factors.ndim != 2:
        raise ValueError("GRS requires 2-D asset and factor return matrices.")
    if assets.shape[0] != factors.shape[0]:
        raise ValueError("GRS requires the same number of periods for assets and factors.")
    if not np.isfinite(assets).all() or not np.isfinite(factors).all():
        raise ValueError("GRS inputs must be finite.")
    t, n_assets = assets.shape
    n_factors = factors.shape[1]
    n_regressors = n_factors + 1  # factors + intercept
    residual_df = t - n_regressors
    if residual_df <= 0:
        raise ValueError(
            f"GRS needs at least {n_regressors + 1} periods; got {t}."
        )

    design = np.column_stack([np.ones(t), factors])
    alphas = np.empty(n_assets)
    residuals = np.empty((t, n_assets))
    for i in range(n_assets):
        beta, _, rank, _ = np.linalg.lstsq(design, assets[:, i], rcond=None)
        if rank < n_regressors:
            raise ValueError("GRS factor design is rank-deficient.")
        alphas[i] = beta[0]
        residuals[:, i] = assets[:, i] - design @ beta

    residual_cov = residuals.T @ residuals / residual_df
    try:
        residual_precision = np.linalg.inv(residual_cov)
    except np.linalg.LinAlgError as exc:
        raise ValueError("GRS residual covariance is singular.") from exc

    quadratic = float(alphas @ residual_precision @ alphas)

    factor_mean = factors.mean(axis=0)
    factor_cov = np.cov(factors, rowvar=False, ddof=1)
    try:
        factor_precision = np.linalg.inv(factor_cov)
    except np.linalg.LinAlgError as exc:
        raise ValueError("GRS factor covariance is singular.") from exc
    denominator = 1.0 + float(factor_mean @ factor_precision @ factor_mean)

    scale = (t / n_assets) * (t - n_assets - n_factors) / (t - n_factors - 1)
    grs = scale * quadratic / denominator
    if grs < 0 or not math.isfinite(grs):
        raise ValueError("GRS statistic is non-finite; check inputs.")
    p_value = float(f_dist.sf(grs, n_assets, residual_df))
    return {
        "grs": grs,
        "p_value": p_value,
        "n_assets": int(n_assets),
        "n_factors": int(n_factors),
        "n_periods": int(t),
    }
