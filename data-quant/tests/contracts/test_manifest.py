from __future__ import annotations

import pytest
from pydantic import ValidationError

from data_quant.contracts.manifest import RunManifest


def manifest_payload():
    return {
        "schema_version": "1.0",
        "project": {"name": "example", "asset_class": "equity", "base_currency": "CNY"},
        "data_sources": [
            {
                "id": "bars",
                "uri": "bars.csv",
                "format": "csv",
                "table_type": "market_bars",
            }
        ],
    }


def test_minimal_manifest_is_valid() -> None:
    manifest = RunManifest.model_validate(manifest_payload())
    assert manifest.project.asset_class == "equity"
    assert manifest.pipeline.fail_closed is True


def test_duplicate_source_ids_are_rejected() -> None:
    payload = manifest_payload()
    payload["data_sources"].append(dict(payload["data_sources"][0]))
    with pytest.raises(ValidationError, match="unique"):
        RunManifest.model_validate(payload)


def test_manifest_requires_at_least_one_data_source() -> None:
    payload = manifest_payload()
    payload["data_sources"] = []
    with pytest.raises(ValidationError, match="at least 1"):
        RunManifest.model_validate(payload)


def test_pipeline_identifiers_must_be_unique() -> None:
    payload = manifest_payload()
    payload["pipeline"] = {"required_diagnostics": ["factor-ic", "factor-ic"]}
    with pytest.raises(ValidationError, match="must be unique"):
        RunManifest.model_validate(payload)


def test_pipeline_stage_order_and_diagnostic_inputs_are_validated() -> None:
    payload = manifest_payload()
    payload["pipeline"] = {
        "stages": ["research", "data"],
        "diagnostics": [],
    }
    with pytest.raises(ValidationError, match="must start with data"):
        RunManifest.model_validate(payload)

    payload["pipeline"] = {
        "stages": ["data", "report", "research"],
        "diagnostics": [],
    }
    with pytest.raises(ValidationError, match="report stage must be last"):
        RunManifest.model_validate(payload)

    payload["pipeline"] = {
        "stages": ["data", "research", "report"],
        "diagnostics": [
            {
                "diagnostic_id": "factor-ic",
                "stage": "research",
                "input_sources": ["missing"],
            }
        ],
    }
    with pytest.raises(ValidationError, match="undeclared inputs"):
        RunManifest.model_validate(payload)


def test_execution_contract_rejects_live_and_broker_configuration() -> None:
    for execution in [
        {"mode": "live"},
        {"mode": "offline_replay", "broker": "example"},
        {"live_order_submission": True},
        {"fund_transfer": True},
        {"credential_storage": True},
    ]:
        payload = manifest_payload()
        payload["execution"] = execution
        with pytest.raises(ValidationError):
            RunManifest.model_validate(payload)


def test_freeform_manifest_sections_reject_and_hide_secrets() -> None:
    secret = "do-not-persist-this-secret"
    payload = manifest_payload()
    payload["metadata"] = {"nested": {"private-key": secret}}
    with pytest.raises(ValidationError, match="sensitive keys") as error:
        RunManifest.model_validate(payload)
    assert secret not in str(error.value)


def test_diagnostic_parameters_reject_and_hide_sensitive_values() -> None:
    secret = "do-not-echo-this-token"
    payload = manifest_payload()
    payload["pipeline"] = {
        "stages": ["data", "research", "report"],
        "diagnostics": [
            {
                "diagnostic_id": "factor-ic",
                "stage": "research",
                "input_sources": ["bars"],
                "parameters": {"nested": {"access-token": secret}},
            }
        ],
    }
    with pytest.raises(ValidationError, match="sensitive keys") as error:
        RunManifest.model_validate(payload)
    assert secret not in str(error.value)


def test_pipeline_diagnostic_ids_must_be_unique() -> None:
    payload = manifest_payload()
    diagnostic = {
        "diagnostic_id": "factor-ic",
        "stage": "research",
        "input_sources": ["bars"],
    }
    payload["pipeline"] = {
        "stages": ["data", "research", "report"],
        "diagnostics": [diagnostic, diagnostic],
    }
    with pytest.raises(ValidationError, match="diagnostic_id values must be unique"):
        RunManifest.model_validate(payload)


def test_calendar_sessions_source_must_reference_declared_calendar_table() -> None:
    payload = manifest_payload()
    payload["calendar"] = {
        "calendar_id": "XNYS",
        "timezone": "America/New_York",
        "sessions_source": "sessions",
    }
    with pytest.raises(ValidationError, match="declared data source"):
        RunManifest.model_validate(payload)

    payload["calendar"]["sessions_source"] = "bars"
    with pytest.raises(ValidationError, match="calendar_sessions table"):
        RunManifest.model_validate(payload)


def test_credential_values_cannot_be_embedded_in_env_names() -> None:
    payload = manifest_payload()
    payload["data_sources"][0]["credential_env"] = ["TOKEN=secret"]
    with pytest.raises(ValidationError, match="never values"):
        RunManifest.model_validate(payload)


@pytest.mark.parametrize(
    "uri",
    [
        "postgresql://alice:super-secret@db.example/research",
        "postgresql://db.example/research?access_token=super-secret",
    ],
)
def test_credential_bearing_uri_is_rejected_without_echoing_secret(uri: str) -> None:
    payload = manifest_payload()
    payload["data_sources"][0].update({"uri": uri, "format": "sql"})
    with pytest.raises(ValidationError, match="uri cannot contain") as captured:
        RunManifest.model_validate(payload)
    assert "super-secret" not in str(captured.value)


def test_safe_sql_uri_uses_environment_variable_names_only() -> None:
    payload = manifest_payload()
    payload["data_sources"][0].update(
        {
            "uri": "postgresql://db.example/research?sslmode=require",
            "format": "sql",
            "credential_env": ["RESEARCH_DB_PASSWORD"],
        }
    )
    source = RunManifest.model_validate(payload).data_sources[0]
    assert source.credential_env == ["RESEARCH_DB_PASSWORD"]
