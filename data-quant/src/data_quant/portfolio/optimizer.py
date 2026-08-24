"""Convex portfolio optimization via CVXPY."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import cvxpy as cp
import numpy as np
import pandas as pd

from data_quant.portfolio.costs import one_way_turnover

Objective = Literal["minimum_variance", "mean_variance"]


class OptimizationError(ValueError):
    """Raised when inputs are invalid or no feasible optimizer solution exists."""


@dataclass(frozen=True)
class PortfolioConstraints:
    target_sum: float = 1.0
    min_weight: float = 0.0
    max_weight: float = 1.0
    gross_limit: float | None = None
    turnover_limit: float | None = None
    minimum_expected_return: float | None = None


@dataclass(frozen=True)
class OptimizationResult:
    objective: Objective
    weights: pd.Series
    objective_value: float
    expected_return: float
    volatility: float
    gross_exposure: float
    net_exposure: float
    one_way_turnover: float | None
    covariance_repaired: bool
    solver_message: str


DEFAULT_CONSTRAINTS = PortfolioConstraints()


def _validate_and_align(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    current_weights: pd.Series | None,
    *,
    repair_covariance: bool,
) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray | None, bool]:
    if expected_returns.index.has_duplicates:
        raise OptimizationError("Expected-return asset index contains duplicates.")
    assets = [str(asset) for asset in expected_returns.index]
    if len(assets) < 2:
        raise OptimizationError("At least two assets are required.")
    if set(covariance.index.astype(str)) != set(assets) or set(covariance.columns.astype(str)) != set(assets):
        raise OptimizationError("Covariance rows and columns must match expected-return assets exactly.")
    covariance = covariance.copy()
    covariance.index = covariance.index.astype(str)
    covariance.columns = covariance.columns.astype(str)
    covariance = covariance.loc[assets, assets]
    mu = pd.to_numeric(expected_returns, errors="coerce").to_numpy(dtype=float)
    cov = covariance.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(mu).all() or not np.isfinite(cov).all():
        raise OptimizationError("Expected returns and covariance must be finite.")
    if not np.allclose(cov, cov.T, atol=1e-10):
        raise OptimizationError("Covariance matrix must be symmetric.")
    cov, repaired = _project_psd(cov, repair_covariance=repair_covariance)

    current = None
    if current_weights is not None:
        current_numeric = pd.to_numeric(current_weights, errors="coerce")
        if current_numeric.index.has_duplicates:
            raise OptimizationError("Current-weight asset index contains duplicates.")
        current = current_numeric.reindex(expected_returns.index, fill_value=0.0).to_numpy(dtype=float)
        if not np.isfinite(current).all():
            raise OptimizationError("Current weights must be finite.")
    return assets, mu, cov, current, repaired


def _project_psd(cov: np.ndarray, *, repair_covariance: bool) -> tuple[np.ndarray, bool]:
    """Return (covariance, repaired).

    Uses a spectral projection: zero out negative eigenvalues below tolerance
    and symmetrize. A matrix that is already PSD within tolerance is returned
    unchanged with ``repaired=False``.
    """
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    if eigenvalues.min() >= -1e-10:
        return cov, False
    if not repair_covariance:
        raise OptimizationError("Covariance matrix is not positive semidefinite.")
    eigenvalues = np.clip(eigenvalues, 0.0, None)
    projected = (eigenvectors * eigenvalues) @ eigenvectors.T
    projected = (projected + projected.T) / 2.0
    return projected, True


def optimize_portfolio(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    *,
    objective: Objective = "minimum_variance",
    constraints: PortfolioConstraints = DEFAULT_CONSTRAINTS,
    current_weights: pd.Series | None = None,
    risk_aversion: float = 1.0,
    turnover_penalty: float = 0.0,
    repair_covariance: bool = False,
    tolerance: float = 1e-8,
) -> OptimizationResult:
    if constraints.min_weight > constraints.max_weight:
        raise OptimizationError("min_weight cannot exceed max_weight.")
    if constraints.gross_limit is not None and constraints.gross_limit < abs(constraints.target_sum):
        raise OptimizationError("gross_limit is below the absolute target net exposure.")
    if constraints.turnover_limit is not None and current_weights is None:
        raise OptimizationError("turnover_limit requires current_weights.")
    if risk_aversion <= 0:
        raise OptimizationError("risk_aversion must be positive.")
    if turnover_penalty < 0:
        raise OptimizationError("turnover_penalty must be non-negative.")

    assets, mu, cov, current, repaired = _validate_and_align(
        expected_returns, covariance, current_weights, repair_covariance=repair_covariance
    )
    n_assets = len(assets)

    weights = cp.Variable(n_assets)
    portfolio_variance = cp.quad_form(weights, cov, assume_PSD=True)
    expected_return_expr = mu @ weights

    if objective == "mean_variance":
        expression = 0.5 * risk_aversion * portfolio_variance - expected_return_expr
    else:
        expression = portfolio_variance

    if current is not None and turnover_penalty:
        expression = expression + turnover_penalty * cp.norm1(weights - current)

    constraint_list = [cp.sum(weights) == constraints.target_sum]
    if constraints.gross_limit is not None:
        constraint_list.append(cp.norm1(weights) <= constraints.gross_limit)
    if constraints.turnover_limit is not None and current is not None:
        constraint_list.append(cp.norm1(weights - current) <= 2.0 * constraints.turnover_limit)
    if constraints.minimum_expected_return is not None:
        constraint_list.append(expected_return_expr >= constraints.minimum_expected_return)

    problem = cp.Problem(
        cp.Minimize(expression),
        constraint_list + [weights >= constraints.min_weight, weights <= constraints.max_weight],
    )
    try:
        problem.solve(solver=cp.CLARABEL)
    except cp.error.SolverError as exc:
        raise OptimizationError(f"Portfolio optimization failed: {exc}") from exc

    if problem.status not in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE}:
        raise OptimizationError(f"Portfolio optimization failed: {problem.status}")

    weights_array = np.asarray(weights.value, dtype=float).ravel()
    if weights_array.size != n_assets or not np.isfinite(weights_array).all():
        raise OptimizationError("Optimizer returned non-finite weights.")
    if abs(weights_array.sum() - constraints.target_sum) > tolerance:
        raise OptimizationError("Optimizer result violates the target net exposure.")
    gross = float(np.abs(weights_array).sum())
    if constraints.gross_limit is not None and gross > constraints.gross_limit + tolerance:
        raise OptimizationError("Optimizer result violates gross_limit.")
    if (weights_array < constraints.min_weight - tolerance).any() or (
        weights_array > constraints.max_weight + tolerance
    ).any():
        raise OptimizationError("Optimizer result violates weight bounds.")

    weights_series = pd.Series(weights_array, index=expected_returns.index, name="weight")
    turnover = None
    if current_weights is not None:
        turnover = one_way_turnover(current_weights, weights_series)
        if constraints.turnover_limit is not None and turnover > constraints.turnover_limit + tolerance:
            raise OptimizationError("Optimizer result violates turnover_limit.")
    portfolio_variance_value = float(weights_array @ cov @ weights_array)
    return OptimizationResult(
        objective=objective,
        weights=weights_series,
        objective_value=float(problem.value),
        expected_return=float(mu @ weights_array),
        volatility=float(np.sqrt(max(portfolio_variance_value, 0.0))),
        gross_exposure=gross,
        net_exposure=float(weights_array.sum()),
        one_way_turnover=turnover,
        covariance_repaired=repaired,
        solver_message=str(problem.status),
    )
