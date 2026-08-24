from __future__ import annotations

import pandas as pd

from data_quant.diagnostics.factor import factor_ic_artifact, factor_ic_legacy_payload
from data_quant.registry import registry


def factor_frame() -> pd.DataFrame:
    rows = []
    for day in range(1, 5):
        for asset in range(6):
            rows.append(
                {
                    "date": f"2024-01-{day:02d}",
                    "factor": float(asset),
                    "forward_return": float(asset) * 0.01 + day * 0.0001,
                }
            )
    return pd.DataFrame(rows)


def test_factor_ic_artifact_and_legacy_aliases() -> None:
    artifact = factor_ic_artifact(
        factor_frame(),
        date_col="date",
        factor_col="factor",
        forward_return_col="forward_return",
        min_assets=5,
    )
    assert artifact.artifact_type == "factor_ic"
    assert artifact.summary["periods_used"] == 4
    assert artifact.summary["rank_ic_summary"]["mean"] == 1.0
    legacy = factor_ic_legacy_payload(artifact)
    assert legacy["rank_ic_summary"] == artifact.summary["rank_ic_summary"]
    assert legacy["artifact_type"] == "factor_ic"
    assert legacy["by_date"] == artifact.details


def test_factor_ic_is_registered() -> None:
    definition = registry.get("factor-ic")
    assert definition.artifact_type == "factor_ic"
