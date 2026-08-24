from __future__ import annotations

import numpy as np
import pandas as pd

from data_quant.diagnostics.factor import fama_macbeth_artifact
from data_quant.registry import registry


def frame() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    rows = []
    for day in range(40):
        for _asset in range(20):
            x = rng.standard_normal()
            r = 0.3 * x + rng.standard_normal() * 0.5 + 0.01
            rows.append({"date": dates[day].date().isoformat(), "x": x, "r": r})
    return pd.DataFrame(rows)


def test_fama_macbeth_reports_hac_and_iid_t_stats() -> None:
    artifact = fama_macbeth_artifact(
        frame(), date_col="date", return_col="r", feature_cols=["x"], min_assets=5
    )
    summary = {row["name"]: row for row in artifact.summary["coefficient_summary"]}
    x = summary["x"]
    assert x["t_stat"] is not None
    assert x["t_stat_hac"] is not None
    assert x["hac_lags"] > 0
    assert x["n"] == artifact.summary["periods_used"]


def test_fama_macbeth_intercept_annualizes() -> None:
    artifact = fama_macbeth_artifact(
        frame(),
        date_col="date",
        return_col="r",
        feature_cols=["x"],
        min_assets=5,
        annualization=12,
    )
    intercept = next(r for r in artifact.summary["coefficient_summary"] if r["name"] == "intercept")
    assert "annualized_mean" in intercept


def test_fama_macbeth_is_registered() -> None:
    definition = registry.get("fama-macbeth")
    assert definition.artifact_type == "fama_macbeth"
    assert definition.manifest_stage == "research"
