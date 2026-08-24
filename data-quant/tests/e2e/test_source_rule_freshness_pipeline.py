from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from data_quant.contracts.artifacts import ArtifactEnvelope
from data_quant.pipeline import run_manifest


def write_manifest(tmp_path: Path, *, approved: bool) -> Path:
    cards = pd.DataFrame(
        [
            {
                "source_id": "official-venue-product-rules",
                "source_kind": "official_snapshot",
                "publisher": "Exchange",
                "venue": "XCME",
                "accessed_at": "2026-08-15T12:41:53Z",
                "effective_from": "2026-08-15",
                "confidence": "authoritative",
                "content_digest": "sha256:" + "a" * 64,
            }
        ]
    )
    approvals = pd.DataFrame(
        [
            {
                "source_id": "official-venue-product-rules",
                "requested_at": "2026-08-01T00:00:00Z" if approved else "2023-12-01T00:00:00Z",
                "approved_at": "2026-08-02T00:00:00Z" if approved else "2024-01-01T00:00:00Z",
                "approver": "governance",
                "action": "refresh",
                "status": "approved",
            }
        ]
    )
    sources = []
    for source_id, frame, table_type in (
        ("cards", cards, "source_cards"),
        ("approvals", approvals, "source_change_approvals"),
    ):
        path = tmp_path / f"{source_id}.csv"
        frame.to_csv(path, index=False)
        sources.append(
            {"id": source_id, "uri": str(path), "format": "csv", "table_type": table_type}
        )
    manifest = {
        "project": {"name": "source-rules", "asset_class": "equity"},
        "data_sources": sources,
        "pipeline": {
            "stages": ["data", "governance", "report"],
            "diagnostics": [
                {
                    "diagnostic_id": "source-rule-freshness",
                    "stage": "governance",
                    "input_sources": ["cards", "approvals"],
                    "parameters": {
                        "required_source_ids": ["official-venue-product-rules"],
                        "evaluated_at": "2026-08-16T00:00:00Z",
                        "max_card_age": "30D",
                        "require_authoritative": True,
                        "require_change_approval": True,
                        "max_approval_age": "30D",
                    },
                }
            ],
            "required_diagnostics": ["source-rule-freshness"],
            "fail_closed": True,
        },
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def load_artifact(result) -> ArtifactEnvelope:
    return ArtifactEnvelope.model_validate_json(
        (result.run_dir / "artifacts/governance/source-rule-freshness.json").read_text(
            encoding="utf-8"
        )
    )


def test_source_rule_freshness_manifest_passes_fresh_approved_card(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, approved=True),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "conditional_pass"
    artifact = load_artifact(result)
    assert artifact.summary["observed_source_count"] == 1
    assert artifact.summary["blocker_count"] == 0


def test_source_rule_freshness_manifest_blocks_stale_approval(tmp_path: Path) -> None:
    result = run_manifest(
        write_manifest(tmp_path, approved=False),
        output_dir=tmp_path / "run",
    )

    assert result.run_record.decision == "fail"
    artifact = load_artifact(result)
    assert "source_change_approval_stale" in {blocker.code for blocker in artifact.blockers}
