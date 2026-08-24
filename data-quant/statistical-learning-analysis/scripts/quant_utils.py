"""Shared pandas/numpy/scipy helpers for the bundled quant scripts.

The preferred tabular path is ``read_dataframe`` plus pandas/numpy/scipy
operations. Shared numerical routines include ``ols`` (SVD-based),
``newey_west_se``, ``solve_psd``, ``summarize_series``,
``summarize_returns``, ``max_drawdown``, ``cross_sectional_corr``, and
``rank_within``.

Several scalar helpers remain intentionally available for row-by-row audit
scripts and legacy report paths: ``parse_float``, ``is_missing``, ``mean``,
``stdev``, ``quantile``, ``correlation``, ``spearman``, ``sorted_group_keys``,
and the backward-compatible ``summarize_values`` alias. New DataFrame-heavy
scripts should prefer ``pd.to_numeric(..., errors="coerce")`` and native
pandas/numpy reductions instead of these scalar helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.linalg import LinAlgError, cho_factor, cho_solve


def read_dataframe(path: Path, parse_dates: list[str] | None = None) -> pd.DataFrame:
    """Read a CSV into a DataFrame, tolerant of utf-8 BOM."""
    kwargs: dict[str, Any] = {"encoding": "utf-8-sig"}
    if parse_dates:
        kwargs["parse_dates"] = parse_dates
    return pd.read_csv(path, **kwargs)


def require_columns(df_or_header, columns: list[str]) -> None:
    """Raise SystemExit if any expected column is missing.

    Accepts either a ``pd.DataFrame`` (preferred) or a list of column names
    (legacy header path used by row-by-row audit scripts).
    """
    if isinstance(df_or_header, pd.DataFrame):
        existing = set(df_or_header.columns)
    else:
        existing = set(df_or_header)
    missing = [col for col in columns if col and col not in existing]
    if missing:
        raise SystemExit(f"Columns not found: {', '.join(missing)}")


_MISSING_TOKENS = {"", "na", "n/a", "nan", "null", "none", "."}


def parse_float(value: Any) -> float | None:
    """Tolerant scalar float parser used by row-by-row audit scripts. For
    DataFrame columns prefer ``pd.to_numeric(..., errors='coerce')``."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _MISSING_TOKENS:
        return None
    try:
        out = float(text.replace(",", ""))
    except ValueError:
        return None
    if out != out or out in (float("inf"), float("-inf")):
        return None
    return out


def is_missing(value: Any) -> bool:
    """True if a scalar value is empty or a recognised missing token."""
    if value is None:
        return True
    if isinstance(value, float) and value != value:
        return True
    return str(value).strip().lower() in _MISSING_TOKENS


def mean(values) -> float | None:
    """Scalar mean of an iterable; None when empty. Use ``np.mean`` for arrays."""
    arr = [v for v in values if v is not None]
    if not arr:
        return None
    return float(np.mean(arr))


def stdev(values) -> float | None:
    """Sample standard deviation (ddof=1); None when fewer than 2 values."""
    arr = [v for v in values if v is not None]
    if len(arr) < 2:
        return None
    return float(np.std(arr, ddof=1))


def quantile(values, q: float) -> float | None:
    """Quantile of an iterable; None when empty."""
    arr = [v for v in values if v is not None]
    if not arr:
        return None
    return float(np.quantile(arr, q))


def sorted_group_keys(keys) -> list:
    """Sort a list of group keys (mixed types tolerated)."""
    try:
        return sorted(keys)
    except TypeError:
        return sorted(keys, key=str)


def ols(y: np.ndarray, X: np.ndarray) -> dict[str, Any]:
    """OLS via SVD; covariance via QR. Returns a JSON-serializable dict
    with the legacy schema (n, p, df_resid, coefficients,
    standard_errors_iid, t_stats_iid, r2, adj_r2, residuals, fitted,
    residual_std, sse)."""
    y_arr = np.asarray(y, dtype=float)
    X_arr = np.asarray(X, dtype=float)
    if X_arr.ndim != 2:
        raise ValueError("X must be 2-D")
    n, p = X_arr.shape
    if n <= p:
        raise ValueError("not enough observations for OLS degrees of freedom")
    beta, _, _, _ = np.linalg.lstsq(X_arr, y_arr, rcond=None)
    fitted = X_arr @ beta
    resid = y_arr - fitted
    df_resid = n - p
    sigma2 = float((resid @ resid) / df_resid)
    _, R = np.linalg.qr(X_arr)
    try:
        R_inv = np.linalg.inv(R)
        cov_beta = sigma2 * (R_inv @ R_inv.T)
    except np.linalg.LinAlgError:
        cov_beta = sigma2 * np.linalg.pinv(X_arr.T @ X_arr)
    se = np.sqrt(np.maximum(np.diag(cov_beta), 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        t_arr = np.where(se > 0, beta / se, np.nan)
    tss = float(((y_arr - y_arr.mean()) ** 2).sum())
    sse = float((resid**2).sum())
    r2 = 1.0 - sse / tss if tss > 0 else None
    adj_r2 = 1.0 - (1.0 - r2) * (n - 1) / df_resid if r2 is not None and df_resid > 0 else None
    return {
        "n": int(n),
        "p": int(p),
        "df_resid": int(df_resid),
        "coefficients": [float(b) for b in beta],
        "standard_errors_iid": [float(s) for s in se],
        "t_stats_iid": [float(t) if np.isfinite(t) else None for t in t_arr],
        "r2": r2,
        "adj_r2": adj_r2,
        "residuals": [float(r) for r in resid],
        "fitted": [float(f) for f in fitted],
        "residual_std": float(np.sqrt(sigma2)),
        "sse": sse,
    }


def newey_west_se(X: np.ndarray, resid: np.ndarray, lags: int) -> np.ndarray:
    """Bartlett-kernel HAC standard errors. Returns sqrt(diag(cov_hac))."""
    X_arr = np.asarray(X, dtype=float)
    u = np.asarray(resid, dtype=float)
    xtx_inv = np.linalg.pinv(X_arr.T @ X_arr)
    Xu = X_arr * u[:, None]
    S = Xu.T @ Xu
    for k in range(1, lags + 1):
        w = 1.0 - k / (lags + 1.0)
        Gamma_k = Xu[k:].T @ Xu[:-k]
        S = S + w * (Gamma_k + Gamma_k.T)
    cov_hac = xtx_inv @ S @ xtx_inv
    return np.sqrt(np.maximum(np.diag(cov_hac), 0.0))


def solve_psd(A: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Solve ``A x = b`` assuming A is symmetric PSD; falls back to pinv."""
    A_arr = np.asarray(A, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    try:
        c, lower = cho_factor(A_arr, lower=True)
        return cho_solve((c, lower), b_arr)
    except (LinAlgError, np.linalg.LinAlgError):
        return np.linalg.pinv(A_arr) @ b_arr


def summarize_series(s) -> dict[str, Any]:
    """Univariate summary: n, mean, stdev, t_stat, positive_rate, min, max."""
    series = pd.Series(s).dropna()
    n = int(len(series))
    if n == 0:
        return {
            "n": 0,
            "mean": None,
            "stdev": None,
            "t_stat": None,
            "positive_rate": None,
            "min": None,
            "max": None,
        }
    mean = float(series.mean())
    sd = float(series.std(ddof=1)) if n >= 2 else None
    t_stat = mean / (sd / np.sqrt(n)) if sd is not None and sd > 0 else None
    return {
        "n": n,
        "mean": mean,
        "stdev": sd,
        "t_stat": t_stat,
        "positive_rate": float((series > 0).mean()),
        "min": float(series.min()),
        "max": float(series.max()),
    }


# Backward-compatible alias for list-of-dict paths still using the legacy name.
summarize_values = summarize_series


def correlation(a, b) -> float | None:
    """Pearson correlation of two iterables; returns None when undefined."""
    sa = pd.Series(a)
    sb = pd.Series(b)
    n = min(len(sa), len(sb))
    if n < 2:
        return None
    out = sa.iloc[:n].corr(sb.iloc[:n])
    return None if pd.isna(out) else float(out)


def spearman(a, b) -> float | None:
    """Spearman rank correlation of two iterables; returns None when undefined."""
    sa = pd.Series(a)
    sb = pd.Series(b)
    n = min(len(sa), len(sb))
    if n < 2:
        return None
    out = sa.iloc[:n].corr(sb.iloc[:n], method="spearman")
    return None if pd.isna(out) else float(out)


def max_drawdown(returns) -> dict[str, Any]:
    """Max drawdown with 1-based peak/trough indices (legacy schema)."""
    r = pd.Series(returns).dropna().reset_index(drop=True)
    if len(r) == 0:
        return {"max_drawdown": 0.0, "drawdown_start_index": 0, "drawdown_trough_index": 0}
    wealth = (1.0 + r).cumprod()
    peak = wealth.cummax()
    dd = wealth / peak - 1.0
    trough_pos = int(np.argmin(dd.values))
    peak_pos = int(np.argmax(wealth.values[: trough_pos + 1])) if trough_pos > 0 else 0
    return {
        "max_drawdown": float(dd.min()),
        "drawdown_start_index": peak_pos + 1,
        "drawdown_trough_index": trough_pos + 1,
    }


def summarize_returns(returns, annualization: int, rf_annual: float = 0.0) -> dict[str, Any]:
    """Return/risk summary matching the legacy schema."""
    r = pd.Series(returns).dropna().reset_index(drop=True)
    n = int(len(r))
    if n == 0:
        out: dict[str, Any] = {
            "n": 0,
            "mean_return": None,
            "annualized_return_geometric": None,
            "annualized_return_arithmetic": None,
            "volatility": None,
            "annualized_volatility": None,
            "sharpe": None,
            "historical_var_95": None,
            "historical_expected_shortfall_95": None,
        }
        out.update(max_drawdown(r))
        return out
    mean_ret = float(r.mean())
    vol = float(r.std(ddof=1)) if n >= 2 else None
    rf_period = (1.0 + rf_annual) ** (1.0 / annualization) - 1.0 if rf_annual > -1.0 else 0.0
    excess = r - rf_period
    avg_excess = float(excess.mean())
    compounded = float((1.0 + r).prod())
    ann_ret = compounded ** (annualization / n) - 1.0 if compounded > 0 else None
    ann_vol = vol * np.sqrt(annualization) if vol is not None else None
    sharpe = (avg_excess / vol) * np.sqrt(annualization) if vol is not None and vol > 0 else None
    q05 = float(np.quantile(r, 0.05))
    tail = r[r <= q05]
    out = {
        "n": n,
        "mean_return": mean_ret,
        "annualized_return_geometric": ann_ret,
        "annualized_return_arithmetic": mean_ret * annualization,
        "volatility": vol,
        "annualized_volatility": ann_vol,
        "sharpe": sharpe,
        "historical_var_95": -q05,
        "historical_expected_shortfall_95": float(-tail.mean()) if len(tail) > 0 else None,
    }
    out.update(max_drawdown(r))
    return out


def cross_sectional_corr(df: pd.DataFrame, group: str, x: str, y: str, method: str = "pearson") -> pd.Series:
    """Per-group correlation between columns x and y, sorted by group key."""
    out: dict[Any, float] = {}
    for key, g in df.groupby(group, sort=True):
        out[key] = g[x].corr(g[y], method=method)
    return pd.Series(out, name=f"{method}_{x}_{y}")


def rank_within(df: pd.DataFrame, group: str, col: str) -> pd.Series:
    """Per-group ranks with average tie-breaking."""
    return df.groupby(group)[col].rank(method="average")
