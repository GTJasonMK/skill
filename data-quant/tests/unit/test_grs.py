from __future__ import annotations

import numpy as np
import pytest

from data_quant.statistics import gibbons_ross_shanken_test


def _panels(with_alpha: bool) -> tuple[list[list[float]], list[list[float]]]:
    rng = np.random.default_rng(0)
    t, n_assets, n_factors = 200, 10, 3
    factors = rng.standard_normal((t, n_factors))
    betas = rng.standard_normal((n_assets, n_factors))
    noise = rng.standard_normal((t, n_assets)) * 0.05
    assets = factors @ betas.T + noise
    if with_alpha:
        assets = assets + 0.02  # large enough to dominate the residual noise
    return assets.tolist(), factors.tolist()


def test_grs_does_not_reject_zero_alpha() -> None:
    assets, factors = _panels(with_alpha=False)
    result = gibbons_ross_shanken_test(assets, factors)
    assert result["n_assets"] == 10
    assert result["n_factors"] == 3
    assert result["n_periods"] == 200
    assert result["p_value"] > 0.05


def test_grs_alpha_shifts_toward_rejection() -> None:
    no_alpha = gibbons_ross_shanken_test(*_panels(with_alpha=False))
    with_alpha = gibbons_ross_shanken_test(*_panels(with_alpha=True))
    assert with_alpha["grs"] > no_alpha["grs"]
    assert with_alpha["p_value"] < no_alpha["p_value"]


def test_grs_requires_enough_periods() -> None:
    with pytest.raises(ValueError):
        gibbons_ross_shanken_test([[1.0], [2.0], [3.0]], [[0.0], [0.0], [0.0]])


def test_grs_requires_aligned_periods() -> None:
    with pytest.raises(ValueError):
        gibbons_ross_shanken_test([[1.0], [2.0]], [[0.0], [0.0], [0.0]])
