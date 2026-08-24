from __future__ import annotations

from data_quant.contracts.run_record import RunRecord, StageHandoff
from data_quant.reporting import render_html, render_markdown, render_report


def record() -> RunRecord:
    return RunRecord(
        run_id="run-1",
        task_type="test",
        object_type="equity",
        claim_side="data_readiness",
        stage="research_candidate",
        decision="conditional_pass",
        action="hold",
        claim_strength="research_only",
        input_artifact_ids=["sha256:input"],
        output_artifact_ids=["sha256:output"],
        warnings=["short history"],
        evidence_gaps=["execution not tested"],
        handoffs=[
            StageHandoff(
                stage="data",
                status="complete",
                primary_decision="Data contract passed.",
                artifact_ids=["sha256:output"],
                checks_completed=["schema"],
            )
        ],
    )


def test_markdown_and_html_render_from_same_record() -> None:
    markdown = render_markdown(record())
    html = render_html(record())
    assert "conditional_pass" in markdown
    assert "execution not tested" in markdown
    assert "conditional_pass" in html
    assert "execution not tested" in html


def test_json_render_is_valid_record_payload() -> None:
    text = render_report(record(), "json")
    assert '"run_id": "run-1"' in text
