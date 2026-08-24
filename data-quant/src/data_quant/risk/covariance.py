"""Baseline covariance estimators with explicit assumptions."""

from __future__ import annotations

import numpy as np
import pandas as pd


def sample_covariance(returns: pd.DataFrame, *, annualization: float = 1.0) -> pd.DataFrame:
    if annualization <= 0:
        raise ValueError("annualization must be positive.")
    numeric = returns.apply(pd.to_numeric, errors="coerce")
    if numeric.shape[1] < 2:
        raise ValueError("At least two return columns are required.")
    covariance = numeric.cov(min_periods=2) * annualization
    if covariance.isna().any().any():
        raise ValueError("Insufficient overlapping observations for a complete covariance matrix.")
    return covariance


def ewma_covariance(
    returns: pd.DataFrame,
    *,
    decay: float = 0.94,
    annualization: float = 1.0,
) -> pd.DataFrame:
    if not 0 < decay < 1:
        raise ValueError("decay must be between 0 and 1.")
    if annualization <= 0:
        raise ValueError("annualization must be positive.")
    numeric = returns.apply(pd.to_numeric, errors="coerce").dropna()
    if len(numeric) < 2 or numeric.shape[1] < 2:
        raise ValueError("EWMA covariance requires at least two complete rows and two assets.")
    values = numeric.to_numpy(dtype=float)
    demeaned = values - values.mean(axis=0)
    powers = np.arange(len(values) - 1, -1, -1)
    weights = (1.0 - decay) * np.power(decay, powers)
    weights /= weights.sum()
    covariance = (demeaned * weights[:, None]).T @ demeaned
    return pd.DataFrame(covariance * annualization, index=numeric.columns, columns=numeric.columns)


def portfolio_volatility(weights: pd.Series, covariance: pd.DataFrame) -> float:
    assets = [str(asset) for asset in weights.index]
    covariance = covariance.copy()
    covariance.index = covariance.index.astype(str)
    covariance.columns = covariance.columns.astype(str)
    if set(assets) - set(covariance.index):
        raise ValueError("Covariance is missing portfolio assets.")
    matrix = covariance.loc[assets, assets].to_numpy(dtype=float)
    vector = weights.to_numpy(dtype=float)
    variance = float(vector @ matrix @ vector)
    if variance < -1e-10:
        raise ValueError("Portfolio variance is negative; covariance is invalid.")
    return float(np.sqrt(max(variance, 0.0)))


def shrinkage_covariance(
    returns: pd.DataFrame,
    *,
    annualization: float = 1.0,
    target: str = "constant_correlation",
) -> pd.DataFrame:
    """Ledoit-Wolf constant-correlation shrinkage estimator (diagonal target also supported)."""
    if annualization <= 0:
        raise ValueError("annualization must be positive.")
    if target not in {"constant_correlation", "diagonal_variance"}:
        raise ValueError("shrinkage_target must be constant_correlation or diagonal_variance.")
    numeric = returns.apply(pd.to_numeric, errors="coerce").dropna()
    if len(numeric) < 3 or numeric.shape[1] < 2:
        raise ValueError("Shrinkage covariance requires at least three complete rows and two assets.")
    sample = numeric.to_numpy(dtype=float)
    n_obs, n_assets = sample.shape
    sample_mean = sample.mean(axis=0)
    sample_cov = np.cov(sample, rowvar=False, ddof=1)

    variances = np.diag(sample_cov)
    std = np.sqrt(variances)

    if target == "constant_correlation":
        correlation = sample_cov / np.outer(std, std)
        np.fill_diagonal(correlation, 0.0)
        average_correlation = float(correlation[np.triu_indices(n_assets, k=1)].mean())
        target_cov = np.outer(std, std) * average_correlation
        np.fill_diagonal(target_cov, variances)
    else:
        target_cov = np.diag(variances)

    phi_matrix = np.zeros((n_assets, n_assets))
    for obs in sample:
        diff = np.outer(obs - sample_mean, obs - sample_mean) - sample_cov
        phi_matrix += diff * diff
    phi = float(phi_matrix.sum()) / n_obs

    diff = sample_cov - target_cov
    pi = float((diff * diff).sum())

    shrinkage_intensity = phi / pi if pi > 0 else 0.0
    shrinkage_intensity = min(max(shrinkage_intensity, 0.0), 1.0)
    shrunk = (1.0 - shrinkage_intensity) * sample_cov + shrinkage_intensity * target_cov
    covariance = shrunk * annualization
    return pd.DataFrame(covariance, index=numeric.columns, columns=numeric.columns)


def regime_covariance(
    returns: pd.DataFrame,
    *,
    annualization: float = 1.0,
    stress_regime: str = "high",
) -> pd.DataFrame:
    """Covariance conditional on a volatility-dispersion regime (stress = above-median dispersion)."""
    if annualization <= 0:
        raise ValueError("annualization must be positive.")
    if stress_regime not in {"high", "low"}:
        raise ValueError("stress_regime must be 'high' or 'low'.")
    numeric = returns.apply(pd.to_numeric, errors="coerce").dropna()
    if len(numeric) < 4 or numeric.shape[1] < 2:
        raise ValueError("Regime covariance requires at least four complete rows and two assets.")
    dispersion = numeric.std(axis=1)
    threshold = float(dispersion.median())
    if stress_regime == "high":
        regime = numeric[dispersion >= threshold]
    else:
        regime = numeric[dispersion < threshold]
    if len(regime) < 2:
        raise ValueError("The selected stress regime has too few observations for covariance.")
    covariance = np.cov(regime.to_numpy(dtype=float), rowvar=False, ddof=1) * annualization
    return pd.DataFrame(covariance, index=numeric.columns, columns=numeric.columns)


