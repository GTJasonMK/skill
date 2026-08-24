"""Minimal fail-closed manifest runner for canonical data stages."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml

from data_quant import __version__
from data_quant.calendars import canonicalize_sessions
from data_quant.contracts.manifest import DataSourceSpec, RunManifest
from data_quant.contracts.run_record import (
    Action,
    ClaimStrength,
    Decision,
    GateRecord,
    RunRecord,
    Stage,
    StageHandoff,
)
from data_quant.diagnostics.data_quality import data_contract_report
from data_quant.io import CanonicalTable, read_source, sha256_file
from data_quant.paths import source_bundle_root
from data_quant.reporting import render_markdown

from .diagnostics import execute_diagnostic, validate_diagnostic_specs


@dataclass(frozen=True)
class RunResult:
    run_dir: Path
    run_record: RunRecord


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return cleaned or "run"


def _json_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _resolve_source(spec: DataSourceSpec, base_dir: Path) -> DataSourceSpec:
    if spec.format in {"csv", "parquet", "duckdb", "sqlite"}:
        path = Path(spec.uri)
        if not path.is_absolute():
            path = (base_dir / path).resolve()
        return spec.model_copy(update={"uri": str(path)})
    return spec


def _default_run_root() -> Path:
    configured = os.environ.get("DATA_QUANT_RUN_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    state_home = os.environ.get("XDG_STATE_HOME")
    base = Path(state_home).expanduser() if state_home else Path.home() / ".local" / "state"
    return (base / "data-quant").resolve()


def _resolve_run_dir(configured: str, run_id: str, explicit: str | Path | None) -> Path:
    if explicit is not None:
        run_dir = Path(explicit).expanduser().resolve()
    else:
        configured_path = Path(configured).expanduser()
        if configured_path.is_absolute():
            run_dir = configured_path.resolve() / run_id
        else:
            run_root = _default_run_root()
            base_output = (run_root / configured_path).resolve()
            if not base_output.is_relative_to(run_root):
                raise ValueError("Relative output_dir cannot escape DATA_QUANT_RUN_ROOT.")
            run_dir = base_output / run_id
    bundle_root = source_bundle_root()
    if bundle_root is not None and run_dir.is_relative_to(bundle_root):
        raise ValueError("Run output must be outside the Data-Quant source bundle.")
    return run_dir


def _validate_calendar_source(table: CanonicalTable, manifest: RunManifest) -> None:
    calendar = manifest.calendar
    if calendar is None or calendar.sessions_source is None:
        return
    frame = table.frame
    calendar_ids = set(frame["calendar_id"].astype(str))
    timezones = set(frame["timezone"].astype(str))
    if calendar_ids != {calendar.calendar_id}:
        raise ValueError(
            f"calendar_sessions rows must all match the manifest calendar_id {calendar.calendar_id!r}."
        )
    if timezones != {calendar.timezone}:
        raise ValueError(
            f"calendar_sessions rows must all match the manifest timezone {calendar.timezone!r}."
        )
    canonicalize_sessions(frame, timezone=calendar.timezone)


def _manifest_digest(manifest: RunManifest) -> str:
    encoded = json.dumps(
        manifest.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_manifest(path: str | Path, *, output_dir: str | Path | None = None) -> RunResult:
    manifest_path = Path(path).resolve()
    manifest = RunManifest.from_yaml(manifest_path)
    diagnostics = validate_diagnostic_specs(manifest.pipeline.diagnostics)
    manifest = manifest.model_copy(
        update={"pipeline": manifest.pipeline.model_copy(update={"diagnostics": diagnostics})}
    )
    resolved_sources = [_resolve_source(spec, manifest_path.parent) for spec in manifest.data_sources]
    manifest = manifest.model_copy(update={"data_sources": resolved_sources})
    digest = _manifest_digest(manifest)
    now = datetime.now(UTC)
    run_id = f"{_slug(manifest.project.name)}-{now.strftime('%Y%m%dT%H%M%SZ')}-{digest[:10]}"

    run_dir = _resolve_run_dir(manifest.output_dir, run_id, output_dir)
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "artifacts" / "data").mkdir(parents=True)
    (run_dir / "logs").mkdir(parents=True)

    resolved_payload = manifest.model_dump(mode="json")
    (run_dir / "manifest.resolved.yaml").write_text(
        yaml.safe_dump(resolved_payload, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    input_records: list[dict[str, Any]] = []
    data_artifact_ids: list[str] = []
    tables: dict[str, CanonicalTable] = {}
    events: list[dict[str, Any]] = []
    blockers: list[str] = []

    for spec in manifest.data_sources:
        started = datetime.now(UTC)
        try:
            input_digest = None
            if spec.format in {"csv", "parquet", "duckdb", "sqlite"}:
                input_digest = sha256_file(spec.uri)
            table = read_source(spec)
            if manifest.calendar and manifest.calendar.sessions_source == spec.id:
                _validate_calendar_source(table, manifest)
            artifact = data_contract_report(
                table,
                source_uri=spec.uri,
                input_digest=input_digest,
                run_id=run_id,
            )
            artifact_path = run_dir / "artifacts" / "data" / f"{_slug(spec.id)}.json"
            _json_write(artifact_path, artifact.model_dump(mode="json"))
            if artifact.artifact_id is None:
                raise RuntimeError("Finalized data Artifact has no artifact_id.")
            data_artifact_ids.append(artifact.artifact_id)
            tables[spec.id] = table
            input_records.append(
                {
                    "source_id": spec.id,
                    "uri": spec.uri,
                    "format": spec.format,
                    "table_type": spec.table_type,
                    "digest": input_digest,
                    "row_count": artifact.summary["row_count"],
                    "artifact": str(artifact_path.relative_to(run_dir)),
                }
            )
            events.append(
                {
                    "event": "data_source_complete",
                    "source_id": spec.id,
                    "started_at": started.isoformat(),
                    "completed_at": datetime.now(UTC).isoformat(),
                    "artifact_id": artifact.artifact_id,
                }
            )
        except Exception as exc:
            message = f"Data source {spec.id!r} failed: {exc}"
            blockers.append(message)
            events.append(
                {
                    "event": "data_source_failed",
                    "source_id": spec.id,
                    "started_at": started.isoformat(),
                    "completed_at": datetime.now(UTC).isoformat(),
                    "error": str(exc),
                }
            )
            if manifest.pipeline.fail_closed:
                break

    data_blockers = list(blockers)
    data_success = not data_blockers and len(input_records) == len(manifest.data_sources)
    completed_diagnostics = {"data-contract"} if data_success else set()
    stage_artifacts: dict[str, list[str]] = {}
    stage_blockers: dict[str, list[str]] = {}
    stage_warnings: dict[str, list[str]] = {}
    stage_evidence_gaps: dict[str, list[str]] = {}
    pipeline_halted = not data_success

    for stage in manifest.pipeline.stages[1:]:
        if stage == "report":
            continue
        specs = [spec for spec in manifest.pipeline.diagnostics if spec.stage == stage]
        if (
            stage == "governance"
            and not specs
            and any(item not in {"data", "governance", "report"} for item in manifest.pipeline.stages)
        ):
            stage_artifacts[stage] = []
            stage_blockers[stage] = []
            stage_warnings[stage] = []
            stage_evidence_gaps[stage] = []
            continue
        stage_artifacts[stage] = []
        stage_blockers[stage] = []
        stage_warnings[stage] = []
        stage_evidence_gaps[stage] = []
        if pipeline_halted:
            stage_blockers[stage].append("Stage was not executed because an earlier stage is blocked.")
            continue
        if not specs:
            message = f"Requested stage {stage!r} has no declared executable diagnostic."
            stage_blockers[stage].append(message)
            blockers.append(message)
            pipeline_halted = manifest.pipeline.fail_closed
            continue
        for diagnostic in specs:
            started = datetime.now(UTC)
            try:
                artifact = execute_diagnostic(diagnostic, tables, run_id)
                if artifact.artifact_id is None:
                    raise RuntimeError("Finalized diagnostic Artifact has no artifact_id.")
                artifact_dir = run_dir / "artifacts" / stage
                artifact_dir.mkdir(parents=True, exist_ok=True)
                artifact_path = artifact_dir / f"{_slug(diagnostic.diagnostic_id)}.json"
                _json_write(artifact_path, artifact.model_dump(mode="json"))
                stage_artifacts[stage].append(artifact.artifact_id)
                completed_diagnostics.add(diagnostic.diagnostic_id)
                diagnostic_blockers = [
                    f"{diagnostic.diagnostic_id}: {message.message}" for message in artifact.blockers
                ]
                stage_blockers[stage].extend(diagnostic_blockers)
                blockers.extend(diagnostic_blockers)
                stage_warnings[stage].extend(
                    f"{diagnostic.diagnostic_id}: {message.message}" for message in artifact.warnings
                )
                stage_evidence_gaps[stage].extend(
                    f"{diagnostic.diagnostic_id}: {message.message}" for message in artifact.evidence_gaps
                )
                events.append(
                    {
                        "event": "diagnostic_complete",
                        "diagnostic_id": diagnostic.diagnostic_id,
                        "stage": stage,
                        "started_at": started.isoformat(),
                        "completed_at": datetime.now(UTC).isoformat(),
                        "artifact_id": artifact.artifact_id,
                    }
                )
                if diagnostic_blockers and manifest.pipeline.fail_closed:
                    pipeline_halted = True
                    break
            except Exception as exc:
                message = f"Diagnostic {diagnostic.diagnostic_id!r} failed: {exc}"
                stage_blockers[stage].append(message)
                blockers.append(message)
                events.append(
                    {
                        "event": "diagnostic_failed",
                        "diagnostic_id": diagnostic.diagnostic_id,
                        "stage": stage,
                        "started_at": started.isoformat(),
                        "completed_at": datetime.now(UTC).isoformat(),
                        "error": str(exc),
                    }
                )
                if manifest.pipeline.fail_closed:
                    pipeline_halted = True
                    break

    unmet_diagnostics = [
        identifier
        for identifier in manifest.pipeline.required_diagnostics
        if identifier not in completed_diagnostics
    ]
    required_blockers = [
        f"Required diagnostic {identifier!r} was declared but was not executed."
        for identifier in unmet_diagnostics
    ]
    blockers.extend(required_blockers)
    for identifier in unmet_diagnostics:
        events.append(
            {
                "event": "required_diagnostic_missing",
                "diagnostic_id": identifier,
                "completed_at": datetime.now(UTC).isoformat(),
            }
        )

    _json_write(run_dir / "inputs.json", input_records)
    with (run_dir / "logs" / "events.jsonl").open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    success = data_success and not blockers
    data_checks = ["input_fingerprint", "table_contract", "primary_key", "timestamp_parse"]
    if data_success and manifest.calendar and manifest.calendar.sessions_source:
        data_checks.append("calendar_sessions")
    completed_stages = {
        stage for stage, artifacts in stage_artifacts.items() if artifacts and not stage_blockers.get(stage)
    }
    evidence_gaps: list[str] = []
    if data_success and "execution" in completed_stages:
        absent = [
            stage
            for stage in ["research", "validation", "portfolio", "risk", "monitoring"]
            if stage not in completed_stages
        ]
        if absent:
            evidence_gaps.append(
                f"Execution promotion lacks completed evidence for stages: {', '.join(absent)}."
            )
    if data_success and manifest.calendar and manifest.calendar.sessions_source is None:
        evidence_gaps.append(
            "Calendar metadata has no sessions_source; exchange holidays and special sessions are unverified."
        )
    for stage in manifest.pipeline.stages:
        evidence_gaps.extend(stage_evidence_gaps.get(stage, []))
    warnings = [warning for stage in manifest.pipeline.stages for warning in stage_warnings.get(stage, [])]

    requested = list(manifest.pipeline.stages)
    handoffs = [
        StageHandoff(
            stage="data",
            status="complete" if data_success else "blocked",
            primary_decision=(
                "All declared data sources satisfy their canonical table contracts."
                if data_success
                else "At least one declared data source failed canonicalization."
            ),
            artifact_ids=data_artifact_ids,
            checks_completed=data_checks,
            open_questions=data_blockers,
            next_stage=requested[1] if data_success and len(requested) > 1 else None,
        )
    ]
    for index, stage in enumerate(requested[1:], start=1):
        if stage == "report":
            continue
        if stage == "governance":
            governance_blockers = list(blockers)
            handoffs.append(
                StageHandoff(
                    stage=stage,
                    status="complete" if not governance_blockers else "blocked",
                    primary_decision=(
                        "All declared gates are satisfied."
                        if not governance_blockers
                        else "One or more declared gates remain blocked."
                    ),
                    artifact_ids=[
                        artifact_id for values in stage_artifacts.values() for artifact_id in values
                    ],
                    checks_completed=["required_diagnostic_inventory"],
                    open_questions=governance_blockers,
                    next_stage=(
                        requested[index + 1]
                        if not governance_blockers and index + 1 < len(requested)
                        else None
                    ),
                )
            )
            continue
        specs = [spec for spec in manifest.pipeline.diagnostics if spec.stage == stage]
        completed = bool(specs) and all(spec.diagnostic_id in completed_diagnostics for spec in specs)
        stage_questions = stage_blockers.get(stage, [])
        stage_status: Literal["complete", "blocked", "needs_input"] = (
            "complete" if completed and not stage_questions else "blocked"
        )
        if stage_questions and all("earlier stage" in item for item in stage_questions):
            stage_status = "needs_input"
        handoffs.append(
            StageHandoff(
                stage=stage,
                status=stage_status,
                primary_decision=(
                    "Every declared stage diagnostic produced an Artifact."
                    if stage_status == "complete"
                    else "The stage lacks required executable evidence."
                ),
                artifact_ids=stage_artifacts.get(stage, []),
                checks_completed=[
                    f"diagnostic:{spec.diagnostic_id}"
                    for spec in specs
                    if spec.diagnostic_id in completed_diagnostics
                ],
                open_questions=stage_questions,
                next_stage=(
                    requested[index + 1]
                    if stage_status == "complete" and index + 1 < len(requested)
                    else None
                ),
            )
        )
    if unmet_diagnostics and "governance" not in requested:
        handoffs.append(
            StageHandoff(
                stage="governance",
                status="blocked",
                primary_decision="The declared required-diagnostic set is incomplete.",
                artifact_ids=[artifact_id for values in stage_artifacts.values() for artifact_id in values],
                checks_completed=["required_diagnostic_inventory"],
                open_questions=required_blockers,
            )
        )
    all_artifact_ids = data_artifact_ids + [
        artifact_id for values in stage_artifacts.values() for artifact_id in values
    ]
    if "report" in requested:
        handoffs.append(
            StageHandoff(
                stage="report",
                status="complete",
                primary_decision="The Run Record was rendered without recomputing metrics.",
                artifact_ids=all_artifact_ids,
                checks_completed=["run_record_render"],
            )
        )

    def gate_outcome(gate_blockers: list[str], gate_evidence_gaps: list[str]) -> tuple[Decision, Action]:
        if gate_blockers:
            return "fail", "hold"
        if gate_evidence_gaps:
            return "conditional_pass", "hold"
        return "pass", "promote"

    data_gate_decision, data_gate_action = gate_outcome(data_blockers, [])
    gates = [
        GateRecord(
            gate="data-contract",
            decision=data_gate_decision,
            action=data_gate_action,
            blockers=data_blockers,
            artifact_ids=data_artifact_ids,
        )
    ]
    if "governance" in requested:
        governance_blockers = list(blockers)
        governance_evidence_gaps = list(evidence_gaps)
        governance_decision, governance_action = gate_outcome(governance_blockers, governance_evidence_gaps)
        gates.append(
            GateRecord(
                gate="governance",
                decision=governance_decision,
                action=governance_action,
                blockers=governance_blockers,
                warnings=stage_warnings.get("governance", []),
                evidence_gaps=governance_evidence_gaps,
                artifact_ids=stage_artifacts.get("governance", []),
            )
        )
    for stage in requested:
        if stage in {"data", "governance", "report"}:
            continue
        stage_evidence = stage_evidence_gaps.get(stage, [])
        stage_decision, stage_action = gate_outcome(stage_blockers.get(stage, []), stage_evidence)
        gates.append(
            GateRecord(
                gate=f"{stage}-diagnostics",
                decision=stage_decision,
                action=stage_action,
                blockers=stage_blockers.get(stage, []),
                warnings=stage_warnings.get(stage, []),
                evidence_gaps=stage_evidence,
                artifact_ids=stage_artifacts.get(stage, []),
            )
        )
    gates.append(
        GateRecord(
            gate="required-diagnostics",
            decision="pass" if not unmet_diagnostics else "fail",
            action="promote" if not unmet_diagnostics else "hold",
            blockers=required_blockers,
            artifact_ids=all_artifact_ids,
        )
    )

    run_stage: Stage
    claim_strength: ClaimStrength
    if "execution" in completed_stages and not evidence_gaps:
        run_stage = "paper_trading"
        claim_strength = "paper_candidate"
    elif "portfolio" in completed_stages and not evidence_gaps:
        run_stage = "portfolio_candidate"
        claim_strength = "portfolio_candidate"
    elif "validation" in completed_stages and not evidence_gaps:
        run_stage = "validated_component"
        claim_strength = "validated_component"
    else:
        run_stage = "research_candidate" if data_success else "idea"
        claim_strength = "research_only" if data_success else "not_determinable"
    record = RunRecord(
        run_id=run_id,
        task_type="manifest_pipeline",
        object_type=manifest.project.asset_class,
        claim_side="pipeline_readiness",
        timing={
            "calendar": manifest.calendar.model_dump(mode="json") if manifest.calendar else None,
            "execution": manifest.execution.model_dump(mode="json"),
        },
        input_artifact_ids=data_artifact_ids,
        output_artifact_ids=all_artifact_ids,
        handoffs=handoffs,
        gates=gates,
        stage=run_stage,
        decision=("fail" if not success else "conditional_pass" if evidence_gaps else "pass"),
        action="promote" if success and not evidence_gaps else "hold",
        claim_strength=claim_strength,
        blockers=blockers,
        warnings=warnings,
        evidence_gaps=evidence_gaps,
        decision_changers=(
            (
                ["Execute every declared required diagnostic and attach its Artifact."]
                if unmet_diagnostics
                else []
            )
            + (["Resolve every evidence gap before promoting the run stage."] if evidence_gaps else [])
        ),
        provenance={
            "manifest": str(manifest_path),
            "manifest_digest": f"sha256:{digest}",
            "runtime_version": __version__,
            "offline_execution_only": True,
            "completed_diagnostics": sorted(completed_diagnostics),
            "unmet_diagnostics": unmet_diagnostics,
            "rendered_report": "reports/review.md" if "report" in requested else None,
        },
    )
    _json_write(run_dir / "run.json", record.model_dump(mode="json"))
    if "report" in requested:
        report_path = run_dir / "reports" / "review.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_markdown(record), encoding="utf-8")
    return RunResult(run_dir=run_dir, run_record=record)
