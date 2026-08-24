from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(tmp_path: Path, *, borrowable: bool) -> Path:
    frames = {
        "weights": (
            pd.DataFrame(
                {
                    "decision_at": ["2024-01-02T09:00:00Z"] * 2,
                    "asset_id": ["A", "B"],
                    "weight": [0.6, -0.2],
                    "weight_type": ["target", "target"],
                    "currency": ["USD", "USD"],
                }
            ),
            "portfolio_weights",
        ),
        "labels": (
            pd.DataFrame(
                {
                    "decision_at": ["2024-01-02T09:00:00Z"] * 2,
                    "execution_at": ["2024-01-02T09:01:00Z"] * 2,
                    "return_start": ["2024-01-02T09:01:00Z"] * 2,
                    "return_end": ["2024-01-02T10:00:00Z"] * 2,
                    "asset_id": ["A", "B"],
                    "label": ["intraday", "intraday"],
                    "return_value": [0.01, -0.005],
                    "return_type": ["simple", "simple"],
                    "return_basis": ["gross", "gross"],
                    "corporate_action_policy": ["total_return", "total_return"],
                    "currency": ["USD", "USD"],
                }
            ),
            "return_labels",
        ),
        "membership": (
            pd.DataFrame(
                {
                    "universe_id": ["research", "research"],
                    "asset_id": ["A", "B"],
                    "effective_from": ["2024-01-01T00:00:00Z"] * 2,
                    "available_at": ["2024-01-01T00:00:00Z"] * 2,
                    "eligible": [True, True],
                }
            ),
            "universe_membership",
        ),
        "actions": (
            pd.DataFrame(
                {
                    "action_id": ["div-A"],
                    "asset_id": ["A"],
                    "action_type": ["cash_dividend"],
                    "announced_at": ["2024-01-01T00:00:00Z"],
                    "available_at": ["2024-01-01T00:00:00Z"],
                    "effective_at": ["2024-01-02T09:30:00Z"],
                    "value": [0.1],
                    "currency": ["USD"],
                }
            ),
            "corporate_actions",
        ),
        "borrow": (
            pd.DataFrame(
                {
                    "asset_id": ["B"],
                    "effective_from": ["2024-01-01T00:00:00Z"],
                    "available_at": ["2024-01-02T08:59:00Z"],
                    "borrowable": [borrowable],
                    "fee_rate_annual": [0.12],
                    "max_quantity": [1_000.0],
                    "currency": ["USD"],
                }
            ),
            "borrow_availability",
        ),
    }
    sources = []
    for source_id, (frame, table_type) in frames.items():
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    manifest = {
        "project": {"name": "portfolio-eligibility", "asset_class": "equity"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "portfolio", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "portfolio-eligibility",
                    "stage": "portfolio",
                    "input_sources": [
                        "weights",
                        "labels",
                        "membership",
                        "actions",
                        "borrow",
                    ],
                    "parameters": {
                        "universe_id": "research",
                        "weight_type": "target",
                        "label": "intraday",
                    },
                },
                {
                    "diagnostic_id": "portfolio-backtest",
                    "stage": "portfolio",
                    "input_sources": ["weights", "labels"],
                    "parameters": {
                        "weight_type": "target",
                        "label": "intraday",
                        "annualization": 252,
                        "cash_rate_annual": 0.03,
                        "short_borrow_rate_annual": 0.12,
                    },
                },
            ],
            "required_diagnostics": ["portfolio-eligibility", "portfolio-backtest"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result, diagnostic_id: str) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / f"artifacts/portfolio/{diagnostic_id}.json").read_text(encoding="utf-8")
    )


def test_portfolio_eligibility_and_funding_pass_with_pit_evidence(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, borrowable=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    eligibility = load_artifact(result, "portfolio-eligibility")
    backtest = load_artifact(result, "portfolio-backtest")
    assert eligibility.summary["corporate_action_count"] == 1
    assert eligibility.summary["short_position_period_count"] == 1
    assert eligibility.summary["blocker_count"] == 0
    assert backtest.summary["total_cash_financing_return"] > 0
    assert backtest.summary["total_short_borrow_cost"] > 0


def test_unavailable_short_borrow_blocks_portfolio_stage(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, borrowable=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    eligibility = load_artifact(result, "portfolio-eligibility")
    assert eligibility.blockers[0].code == "borrow_unavailable_or_ambiguous"
