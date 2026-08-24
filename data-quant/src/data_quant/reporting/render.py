"""Render Run Records without recomputing any metric."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Literal

from data_quant.contracts.run_record import RunRecord

ReportFormat = Literal["json", "markdown", "html"]


def render_markdown(record: RunRecord) -> str:
    lines = [
        f"# Data-Quant Run: {record.run_id}",
        "",
        f"- Task: {record.task_type}",
        f"- Object: {record.object_type}",
        f"- Claim side: {record.claim_side}",
        f"- Stage: `{record.stage}`",
        f"- Decision: `{record.decision}`",
        f"- Action: `{record.action}`",
        f"- Claim strength: `{record.claim_strength}`",
        "",
        "## Evidence",
        "",
        f"- Input artifacts: {', '.join(record.input_artifact_ids) or 'none'}",
        f"- Output artifacts: {', '.join(record.output_artifact_ids) or 'none'}",
    ]
    for heading, values in (
        ("Blockers", record.blockers),
        ("Warnings", record.warnings),
        ("Evidence Gaps", record.evidence_gaps),
        ("Decision Changers", record.decision_changers),
    ):
        lines.extend(["", f"## {heading}", ""])
        lines.extend([f"- {value}" for value in values] or ["- None"])
    lines.extend(["", "## Stage Handoffs", ""])
    for handoff in record.handoffs:
        lines.extend(
            [
                f"### {handoff.stage}: {handoff.status}",
                "",
                handoff.primary_decision,
                "",
                f"- Artifacts: {', '.join(handoff.artifact_ids) or 'none'}",
                f"- Checks: {', '.join(handoff.checks_completed) or 'none'}",
                f"- Open questions: {', '.join(handoff.open_questions) or 'none'}",
            ]
        )
    return "\n".join(lines) + "\n"


def render_html(record: RunRecord) -> str:
    markdown = render_markdown(record)
    escaped = html.escape(markdown)
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>Data-Quant Run {html.escape(record.run_id)}</title>"
        "<style>body{max-width:1000px;margin:2rem auto;padding:0 1rem;font:15px/1.5 system-ui;}"
        "pre{white-space:pre-wrap;background:#f5f5f5;padding:1rem;border-radius:.5rem;}</style>"
        f"</head><body><pre>{escaped}</pre></body></html>\n"
    )


def render_report(record: RunRecord, report_format: ReportFormat) -> str:
    if report_format == "json":
        return json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
    if report_format == "markdown":
        return render_markdown(record)
    if report_format == "html":
        return render_html(record)
    raise ValueError(f"Unsupported report format: {report_format}")


def render_run_file(run_file: str | Path, output: str | Path, report_format: ReportFormat) -> Path:
    record = RunRecord.model_validate_json(Path(run_file).read_text(encoding="utf-8"))
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_report(record, report_format), encoding="utf-8")
    return output_path
