from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_MANIFEST = ROOT / "examples/manifests/minimal.yaml"
FACTOR_MANIFEST = ROOT / "examples/manifests/factor-research.yaml"


def copied_manifest(path: Path) -> dict:
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    for source in manifest["data_sources"]:
        source["uri"] = str((path.parent / source["uri"]).resolve())
    return manifest


def copied_example_manifest() -> dict:
    return copied_manifest(EXAMPLE_MANIFEST)


def write_execution_manifest(tmp_path: Path, submitted_at: str) -> Path:
    orders = tmp_path / "orders.csv"
    orders.write_text(
        (
            "order_id,asset_id,decision_at,submitted_at,side,quantity,order_type,venue,status\n"
            f"o1,A,2024-01-02T09:00:00Z,{submitted_at},buy,5,market,SIM,planned\n"
        ),
        encoding="utf-8",
    )
    quotes = tmp_path / "quotes.csv"
    quotes.write_text(
        ("timestamp,asset_id,bid,ask,volume,currency,venue\n2024-01-02T09:00:02Z,A,9.9,10.1,100,USD,SIM\n"),
        encoding="utf-8",
    )
    manifest = {
        "project": {"name": "execution-stage", "asset_class": "equity"},
        "data_sources": [
            {
                "id": "orders",
                "uri": str(orders),
                "format": "csv",
                "table_type": "orders",
            },
            {
                "id": "quotes",
                "uri": str(quotes),
                "format": "csv",
                "table_type": "market_quotes",
            },
        ],
        "execution": {"mode": "offline_replay", "live_order_submission": False},
        "pipeline": {
            "stages": ["data", "execution", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "execution-replay",
                    "stage": "execution",
                    "input_sources": ["orders", "quotes"],
                    "parameters": {"initial_cash": 1_000.0, "max_participation": 0.1},
                }
            ],
            "required_diagnostics": ["execution-replay"],
        },
    }
    manifest_path = tmp_path / "execution.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return manifest_path


def test_minimal_manifest_resolves_relative_inputs_to_auditable_data_handoff(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"

    result = run_manifest(EXAMPLE_MANIFEST, output_dir=run_dir)

    assert result.run_record.decision == "pass"
    assert result.run_record.stage == "research_candidate"
    assert (run_dir / "run.json").is_file()
    assert (run_dir / "inputs.json").is_file()
    artifact_path = run_dir / "artifacts/data/bars.json"
    artifact = ArtifactEnvelope.model_validate_json(artifact_path.read_text(encoding="utf-8"))
    assert artifact.artifact_type == "data_contract"
    assert artifact.summary["row_count"] == 4
    assert artifact.content_digest == artifact.compute_content_digest()
    assert (run_dir / "artifacts/data/sessions.json").is_file()
    assert "calendar_sessions" in result.run_record.handoffs[0].checks_completed
    inputs = json.loads((run_dir / "inputs.json").read_text(encoding="utf-8"))
    assert all(Path(item["uri"]).is_absolute() for item in inputs)


def test_empty_governance_stage_fails_closed(tmp_path: Path) -> None:
    manifest = copied_example_manifest()
    manifest["pipeline"]["stages"] = ["data", "governance", "report"]
    manifest["pipeline"]["diagnostics"] = []
    manifest["pipeline"]["required_diagnostics"] = []
    manifest_path = tmp_path / "empty-governance.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    result = run_manifest(manifest_path, output_dir=tmp_path / "run")

    assert result.run_record.decision == "fail"
    governance = next(handoff for handoff in result.run_record.handoffs if handoff.stage == "governance")
    assert governance.status == "blocked"
    governance_gate = next(gate for gate in result.run_record.gates if gate.gate == "governance")
    assert governance_gate.decision == "fail"
    assert "no declared executable diagnostic" in governance_gate.blockers[0]


def test_factor_manifest_executes_research_gate_and_report(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"

    result = run_manifest(FACTOR_MANIFEST, output_dir=run_dir)

    assert result.run_record.decision == "conditional_pass"
    assert result.run_record.action == "hold"
    assert result.run_record.stage == "research_candidate"
    assert result.run_record.provenance["completed_diagnostics"] == ["data-contract", "factor-ic"]
    research = next(handoff for handoff in result.run_record.handoffs if handoff.stage == "research")
    assert research.status == "complete"
    research_gate = next(gate for gate in result.run_record.gates if gate.gate == "research-diagnostics")
    assert research_gate.decision == "conditional_pass"
    artifact = ArtifactEnvelope.model_validate_json(
        (run_dir / "artifacts/research/factor-ic.json").read_text(encoding="utf-8")
    )
    assert artifact.artifact_type == "factor_ic"
    assert artifact.summary["periods_used"] == 3
    assert artifact.summary["rank_ic_summary"]["mean"] == pytest.approx(1.0)
    assert (run_dir / "reports/review.md").read_text(encoding="utf-8").startswith("# Data-Quant Run:")


def test_factor_manifest_fails_closed_on_future_available_signal(tmp_path: Path) -> None:
    manifest = copied_manifest(FACTOR_MANIFEST)
    bad_factors = tmp_path / "factors.csv"
    original = (ROOT / "examples/data/factor_panel.csv").read_text(encoding="utf-8")
    bad_factors.write_text(
        original.replace("2024-01-02T06:59:00Z", "2024-01-02T08:00:00Z", 1),
        encoding="utf-8",
    )
    next(source for source in manifest["data_sources"] if source["id"] == "factors")["uri"] = str(bad_factors)
    manifest_path = tmp_path / "bad-factor.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    result = run_manifest(manifest_path, output_dir=tmp_path / "run")

    assert result.run_record.decision == "fail"
    assert "unavailable at the decision timestamp" in result.run_record.blockers[0]
    research = next(handoff for handoff in result.run_record.handoffs if handoff.stage == "research")
    assert research.status == "blocked"
    assert not (result.run_dir / "artifacts/research/factor-ic.json").exists()


@pytest.mark.parametrize(
    "parameters",
    [
        {"signal": "value_signal", "label": "next_close", "min_assets": 1},
        {"signal": "value_signal", "label": "next_close", "unknown": True},
    ],
)
def test_invalid_native_parameters_fail_before_creating_run_directory(
    tmp_path: Path,
    parameters: dict,
) -> None:
    manifest = copied_manifest(FACTOR_MANIFEST)
    manifest["pipeline"]["diagnostics"][0]["parameters"] = parameters
    manifest_path = tmp_path / "invalid-parameters.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    run_dir = tmp_path / "run"

    with pytest.raises(ValidationError):
        run_manifest(manifest_path, output_dir=run_dir)

    assert not run_dir.exists()


def test_execution_replay_manifest_stage_is_offline_and_auditable(tmp_path: Path) -> None:
    manifest_path = write_execution_manifest(tmp_path, "2024-01-02T09:00:01Z")

    result = run_manifest(manifest_path, output_dir=tmp_path / "run")

    assert result.run_record.decision == "conditional_pass"
    assert result.run_record.action == "hold"
    assert result.run_record.stage == "research_candidate"
    assert result.run_record.timing["execution"]["live_order_submission"] is False
    assert result.run_record.provenance["offline_execution_only"] is True
    artifact = ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/execution/execution-replay.json").read_text(encoding="utf-8")
    )
    assert artifact.artifact_type == "execution_replay"
    assert artifact.summary["status_counts"] == {"filled": 1}
    assert artifact.provenance["live_order_submission"] is False


def test_execution_manifest_replays_limit_order_lifecycle(tmp_path: Path) -> None:
    manifest_path = write_execution_manifest(tmp_path, "2024-01-02T09:00:01Z")
    (tmp_path / "orders.csv").write_text(
        (
            "order_id,asset_id,decision_at,submitted_at,side,quantity,order_type,limit_price,"
            "expires_at,time_in_force,venue,status\n"
            "o1,A,2024-01-02T09:00:00Z,2024-01-02T09:00:01Z,buy,5,limit,10.2,"
            "2024-01-02T09:00:03Z,day,SIM,planned\n"
        ),
        encoding="utf-8",
    )

    result = run_manifest(manifest_path, output_dir=tmp_path / "run")

    assert result.run_record.decision == "conditional_pass"
    assert result.run_record.action == "hold"
    assert result.run_record.stage == "research_candidate"
    artifact = ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/execution/execution-replay.json").read_text(encoding="utf-8")
    )
    assert artifact.details[0]["status"] == "filled"
    assert artifact.details[0]["time_in_force"] == "day"
    assert artifact.details[0]["implementation_shortfall_bps"] > 0


def test_execution_replay_rejects_submission_before_decision(tmp_path: Path) -> None:
    manifest_path = write_execution_manifest(tmp_path, "2024-01-02T08:59:59Z")

    result = run_manifest(manifest_path, output_dir=tmp_path / "run")

    assert result.run_record.decision == "fail"
    assert "submitted before their decision timestamp" in result.run_record.blockers[0]
    assert not (result.run_dir / "artifacts/execution/execution-replay.json").exists()


def test_portfolio_backtest_manifest_stage_executes_offline(tmp_path: Path) -> None:
    weights = tmp_path / "weights.csv"
    weights.write_text(
        (
            "decision_at,asset_id,weight,weight_type,currency\n"
            "2024-01-02T07:00:00Z,A,0.6,target,CNY\n"
            "2024-01-02T07:00:00Z,B,0.4,target,CNY\n"
            "2024-01-03T07:00:00Z,A,0.5,target,CNY\n"
            "2024-01-03T07:00:00Z,B,0.5,target,CNY\n"
        ),
        encoding="utf-8",
    )
    labels = tmp_path / "labels.csv"
    labels.write_text(
        (
            "decision_at,execution_at,return_start,return_end,asset_id,label,"
            "return_value,return_type,return_basis,corporate_action_policy,currency\n"
            "2024-01-02T07:00:00Z,2024-01-03T01:30:00Z,2024-01-03T01:30:00Z,"
            "2024-01-03T07:00:00Z,A,next_close,0.10,simple,gross,total_return,CNY\n"
            "2024-01-02T07:00:00Z,2024-01-03T01:30:00Z,2024-01-03T01:30:00Z,"
            "2024-01-03T07:00:00Z,B,next_close,0.00,simple,gross,total_return,CNY\n"
            "2024-01-03T07:00:00Z,2024-01-04T01:30:00Z,2024-01-04T01:30:00Z,"
            "2024-01-04T07:00:00Z,A,next_close,0.00,simple,gross,total_return,CNY\n"
            "2024-01-03T07:00:00Z,2024-01-04T01:30:00Z,2024-01-04T01:30:00Z,"
            "2024-01-04T07:00:00Z,B,next_close,0.10,simple,gross,total_return,CNY\n"
        ),
        encoding="utf-8",
    )
    manifest = {
        "project": {"name": "portfolio-stage", "asset_class": "equity"},
        "data_sources": [
            {
                "id": "weights",
                "uri": str(weights),
                "format": "csv",
                "table_type": "portfolio_weights",
            },
            {
                "id": "labels",
                "uri": str(labels),
                "format": "csv",
                "table_type": "return_labels",
            },
        ],
        "pipeline": {
            "stages": ["data", "portfolio", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "portfolio-backtest",
                    "stage": "portfolio",
                    "input_sources": ["weights", "labels"],
                    "parameters": {
                        "weight_type": "target",
                        "label": "next_close",
                        "cost_bps_per_one_way_turnover": 10.0,
                    },
                }
            ],
            "required_diagnostics": ["portfolio-backtest"],
        },
    }
    manifest_path = tmp_path / "portfolio.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    result = run_manifest(manifest_path, output_dir=tmp_path / "run")

    assert result.run_record.decision == "conditional_pass"
    assert result.run_record.action == "hold"
    assert result.run_record.stage == "research_candidate"
    artifact = ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/portfolio/portfolio-backtest.json").read_text(encoding="utf-8")
    )
    assert artifact.artifact_type == "portfolio_backtest"
    assert artifact.provenance["live_order_submission"] is False


def test_run_output_inside_source_bundle_is_rejected() -> None:
    with pytest.raises(ValueError, match="outside the Data-Quant source bundle"):
        run_manifest(EXAMPLE_MANIFEST, output_dir=ROOT / "runs/forbidden")


def test_pipeline_fails_closed_on_contract_error(tmp_path: Path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("timestamp,asset_id\n2024-01-01T00:00:00Z,A\n", encoding="utf-8")
    manifest = {
        "schema_version": "1.0",
        "project": {"name": "bad", "asset_class": "equity", "base_currency": "USD"},
        "data_sources": [{"id": "bars", "uri": str(bad_csv), "format": "csv", "table_type": "market_bars"}],
        "output_dir": str(tmp_path / "runs"),
    }
    manifest_path = tmp_path / "bad.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

    result = run_manifest(manifest_path)

    run_payload = json.loads((result.run_dir / "run.json").read_text(encoding="utf-8"))
    assert result.run_record.decision == "fail"
    assert result.run_record.handoffs[0].status == "blocked"
    assert run_payload["blockers"]


def test_automatic_data_contract_can_satisfy_a_required_diagnostic(tmp_path: Path) -> None:
    manifest = copied_example_manifest()
    manifest["pipeline"]["required_diagnostics"] = ["data-contract"]
    manifest_path = tmp_path / "required-data-contract.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    result = run_manifest(manifest_path, output_dir=tmp_path / "run")

    assert result.run_record.decision == "pass"
    assert result.run_record.gates[1].decision == "pass"
    assert result.run_record.provenance["completed_diagnostics"] == ["data-contract"]


def test_requested_stage_without_executor_fails_closed(tmp_path: Path) -> None:
    manifest = copied_example_manifest()
    manifest["pipeline"]["stages"] = ["data", "risk", "report"]
    manifest_path = tmp_path / "risk-without-diagnostic.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    result = run_manifest(manifest_path, output_dir=tmp_path / "run")

    assert result.run_record.decision == "fail"
    assert "no declared executable diagnostic" in result.run_record.blockers[0]
    risk = next(handoff for handoff in result.run_record.handoffs if handoff.stage == "risk")
    assert risk.status == "blocked"
    risk_gate = next(gate for gate in result.run_record.gates if gate.gate == "risk-diagnostics")
    assert risk_gate.decision == "fail"


def test_unexecuted_required_diagnostic_fails_closed(tmp_path: Path) -> None:
    manifest = copied_example_manifest()
    manifest["pipeline"]["required_diagnostics"] = ["not-a-real-diagnostic"]
    manifest_path = tmp_path / "unknown-diagnostic.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    result = run_manifest(manifest_path, output_dir=tmp_path / "run")

    assert result.run_record.decision == "fail"
    governance = next(handoff for handoff in result.run_record.handoffs if handoff.stage == "governance")
    assert governance.status == "blocked"
    assert "not-a-real-diagnostic" in result.run_record.blockers[-1]
    assert result.run_record.provenance["unmet_diagnostics"] == ["not-a-real-diagnostic"]


def test_calendar_sessions_must_match_manifest_identity_and_timezone(tmp_path: Path) -> None:
    bad_sessions = tmp_path / "sessions.csv"
    bad_sessions.write_text(
        (
            "calendar_id,session,timezone,open_at,close_at,is_half_day\n"
            "example-business-days,2024-01-02,UTC,"
            "2024-01-02T01:30:00Z,2024-01-02T07:00:00Z,false\n"
        ),
        encoding="utf-8",
    )
    manifest = copied_example_manifest()
    next(source for source in manifest["data_sources"] if source["id"] == "sessions")["uri"] = str(
        bad_sessions
    )
    manifest_path = tmp_path / "bad-calendar.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    result = run_manifest(manifest_path, output_dir=tmp_path / "run")

    assert result.run_record.decision == "fail"
    assert "manifest timezone" in result.run_record.blockers[0]
