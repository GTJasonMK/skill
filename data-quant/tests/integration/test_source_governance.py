from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.sync_source_skills import file_digest, tree_digest, validate_registry  # noqa: E402


def registry_for(root: Path) -> dict:
    target = root / "mirror"
    target.mkdir()
    (target / "SKILL.md").write_text("governed snapshot\n", encoding="utf-8")
    return {
        "schema_version": "1.0",
        "sources": [
            {
                "source_id": "frozen-mirror",
                "source_kind": "local_mirror",
                "publisher": "test",
                "jurisdiction_or_venue": "test",
                "url_or_document": "../unavailable-source",
                "authoring_path": "../unavailable-source/skill",
                "mirror_target": "mirror",
                "content_digest": f"sha256-tree-v1:{tree_digest(target)}",
                "effective_from": None,
                "effective_to": None,
                "accessed_at": "2026-08-15T08:00:00Z",
                "applies_to": "test mirror",
                "confidence": "corroborated",
                "notes": "frozen source test",
            }
        ],
    }


def test_frozen_mirror_is_verified_when_authoring_tree_is_unavailable(tmp_path: Path) -> None:
    payload = registry_for(tmp_path)
    assert validate_registry(payload, root=tmp_path) == []

    (tmp_path / "mirror/SKILL.md").write_text("drifted\n", encoding="utf-8")
    assert any("mirror digest is stale" in error for error in validate_registry(payload, root=tmp_path))


def test_source_registry_requires_timezone_aware_access_timestamp(tmp_path: Path) -> None:
    payload = registry_for(tmp_path)
    payload["sources"][0]["accessed_at"] = "2026-08-15T08:00:00"

    assert any("explicit-timezone" in error for error in validate_registry(payload, root=tmp_path))


def test_local_file_rejects_paths_outside_registry_root(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside.txt"
    outside.write_text("outside registry root\n", encoding="utf-8")
    payload = {
        "schema_version": "1.0",
        "sources": [
            {
                "source_id": "unsafe-local-file",
                "source_kind": "local_file",
                "publisher": "test",
                "jurisdiction_or_venue": "test",
                "url_or_document": f"../{outside.name}",
                "content_digest": f"sha256:{file_digest(outside)}",
                "effective_from": None,
                "effective_to": None,
                "accessed_at": "2026-08-15T08:00:00Z",
                "applies_to": "test file",
                "confidence": "corroborated",
                "notes": "unsafe path test",
            }
        ],
    }

    assert any("local file is unsafe" in error for error in validate_registry(payload, root=tmp_path))


def official_registry_for(root: Path) -> tuple[dict, Path]:
    snapshot = root / "official.yaml"
    card = {
        "schema_version": "1.0",
        "source_id": "official-test",
        "publisher": "Official Test Publisher",
        "url": "https://example.test/rules",
        "accessed_at": "2026-08-15T08:00:00Z",
        "effective_from": "2026-08-15",
        "effective_to": None,
        "retrieval": {
            "status": "retrieved",
            "response_digest": f"sha256:{'a' * 64}",
        },
        "claims": [
            {
                "claim_id": "bounded-rule",
                "summary": "Current rules require effective-dated evidence.",
                "implementation_use": "Fail closed without current rule inputs.",
                "requires_fresh_check": True,
            }
        ],
    }
    snapshot.write_text(yaml.safe_dump(card, sort_keys=False), encoding="utf-8")
    payload = {
        "schema_version": "1.0",
        "sources": [
            {
                "source_id": "official-test",
                "source_kind": "official_snapshot",
                "publisher": "Official Test Publisher",
                "jurisdiction_or_venue": "test venue",
                "url_or_document": "https://example.test/rules",
                "snapshot_path": "official.yaml",
                "content_digest": f"sha256:{file_digest(snapshot)}",
                "effective_from": "2026-08-15",
                "effective_to": None,
                "accessed_at": "2026-08-15T08:00:00Z",
                "applies_to": "bounded test rule",
                "confidence": "authoritative",
                "notes": "test",
            }
        ],
    }
    return payload, snapshot


def test_official_snapshot_requires_matching_digest_metadata_and_bounded_claims(
    tmp_path: Path,
) -> None:
    payload, snapshot = official_registry_for(tmp_path)
    assert validate_registry(payload, root=tmp_path) == []

    snapshot.write_text("tampered\n", encoding="utf-8")
    assert any(
        "snapshot digest is stale" in error
        for error in validate_registry(payload, root=tmp_path)
    )

    payload, snapshot = official_registry_for(tmp_path)
    card = yaml.safe_load(snapshot.read_text(encoding="utf-8"))
    card["claims"][0]["requires_fresh_check"] = False
    snapshot.write_text(yaml.safe_dump(card, sort_keys=False), encoding="utf-8")
    payload["sources"][0]["content_digest"] = f"sha256:{file_digest(snapshot)}"
    assert any(
        "invalid or unbounded claim" in error
        for error in validate_registry(payload, root=tmp_path)
    )


def test_source_rule_freshness_gates_missing_and_stale_cards() -> None:
    import pandas as pd

    from data_quant.diagnostics.governance import source_rule_freshness_artifact

    cards = pd.DataFrame(
        [
            {
                "source_id": "official-venue-product-rules",
                "source_kind": "official_snapshot",
                "publisher": "Exchange",
                "accessed_at": "2026-08-15T12:41:53Z",
                "effective_from": "2026-08-15",
                "confidence": "authoritative",
                "content_digest": "sha256:" + "a" * 64,
            }
        ]
    )
    fresh = source_rule_freshness_artifact(
        cards,
        required_source_ids=["official-venue-product-rules"],
        evaluated_at="2026-08-16T00:00:00Z",
        max_card_age="30D",
    )
    assert fresh.summary["blocker_count"] == 0
    stale = source_rule_freshness_artifact(
        cards,
        required_source_ids=["official-venue-product-rules", "official-vendor-data-dictionary"],
        evaluated_at="2028-08-16T00:00:00Z",
        max_card_age="30D",
    )
    assert {
        "source_card_missing",
        "source_card_stale",
    } <= {blocker.code for blocker in stale.blockers}

    approvals = pd.DataFrame(
        [
            {
                "source_id": "official-venue-product-rules",
                "requested_at": "2026-08-01T00:00:00Z",
                "approved_at": "2026-08-02T00:00:00Z",
                "approver": "governance",
                "action": "refresh",
                "status": "approved",
            }
        ]
    )
    approved = source_rule_freshness_artifact(
        cards,
        approvals,
        required_source_ids=["official-venue-product-rules"],
        evaluated_at="2026-08-16T00:00:00Z",
        max_card_age="30D",
        require_change_approval=True,
        max_approval_age="30D",
    )
    assert approved.summary["blocker_count"] == 0
    unapproved = source_rule_freshness_artifact(
        cards,
        approvals.iloc[0:0],
        required_source_ids=["official-venue-product-rules"],
        evaluated_at="2026-08-16T00:00:00Z",
        require_change_approval=True,
    )
    assert "source_change_unapproved" in {blocker.code for blocker in unapproved.blockers}
