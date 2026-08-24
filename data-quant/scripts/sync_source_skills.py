#!/usr/bin/env python3
"""Validate or synchronize governed local sources and distribution mirrors."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "source-registry.yaml"
TREE_DIGEST = re.compile(r"^sha256-tree-v1:[0-9a-f]{64}$")
FILE_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
HTTPS_URL = re.compile(r"^https://[^\s]+$")
IGNORED_PARTS = {".git", ".venv", "__pycache__"}


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_map(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): file_digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and not IGNORED_PARTS.intersection(path.parts)
        and path.name != ".DS_Store"
    }


def tree_digest(root: Path) -> str:
    payload = "".join(f"{name}\0{digest}\n" for name, digest in tree_map(root).items())
    return hashlib.sha256(payload.encode()).hexdigest()


def load_registry() -> dict[str, Any]:
    payload = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("source-registry.yaml must contain an object.")
    return payload


def mirror_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    sources = payload.get("sources", [])
    return [
        source
        for source in sources
        if isinstance(source, dict) and source.get("source_kind") == "local_mirror"
    ]


def _valid_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _valid_date(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _validate_official_snapshot(
    source: dict[str, Any],
    *,
    root: Path,
    check_content: bool,
) -> list[str]:
    source_id = str(source.get("source_id", ""))
    errors: list[str] = []
    if source.get("confidence") != "authoritative":
        errors.append(f"Official source {source_id} must be authoritative.")
    url = source.get("url_or_document")
    if not isinstance(url, str) or not HTTPS_URL.fullmatch(url):
        errors.append(f"Official source {source_id} needs an HTTPS URL.")
    if source.get("effective_from") is None:
        errors.append(f"Official source {source_id} needs effective_from.")
    digest = str(source.get("content_digest", ""))
    if not FILE_DIGEST.fullmatch(digest):
        errors.append(f"Official source {source_id} needs a sha256 snapshot digest.")
        return errors
    snapshot_value = source.get("snapshot_path")
    if not isinstance(snapshot_value, str):
        errors.append(f"Official source {source_id} needs snapshot_path.")
        return errors
    snapshot = (root / snapshot_value).resolve()
    if not snapshot.is_relative_to(root.resolve()) or not snapshot.is_file():
        errors.append(f"Official source {source_id} snapshot is unsafe or unavailable: {snapshot}")
        return errors
    if check_content and file_digest(snapshot) != digest.removeprefix("sha256:"):
        errors.append(f"Official source {source_id} snapshot digest is stale.")
        return errors
    try:
        card = yaml.safe_load(snapshot.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        errors.append(f"Official source {source_id} snapshot is unreadable: {exc}")
        return errors
    if not isinstance(card, dict) or card.get("schema_version") != "1.0":
        errors.append(f"Official source {source_id} snapshot must use schema_version 1.0.")
        return errors
    for card_key, source_key in (
        ("source_id", "source_id"),
        ("publisher", "publisher"),
        ("url", "url_or_document"),
        ("accessed_at", "accessed_at"),
        ("effective_from", "effective_from"),
        ("effective_to", "effective_to"),
    ):
        if card.get(card_key) != source.get(source_key):
            errors.append(f"Official source {source_id} snapshot {card_key} differs from registry.")
    retrieval = card.get("retrieval")
    if not isinstance(retrieval, dict) or retrieval.get("status") not in {
        "retrieved",
        "metadata_only",
    }:
        errors.append(f"Official source {source_id} snapshot needs a retrieval status.")
    elif retrieval["status"] == "retrieved" and not FILE_DIGEST.fullmatch(
        str(retrieval.get("response_digest", ""))
    ):
        errors.append(f"Official source {source_id} retrieved response needs a sha256 digest.")
    claims = card.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append(f"Official source {source_id} snapshot needs at least one bounded claim.")
    elif any(
        not isinstance(claim, dict)
        or not isinstance(claim.get("claim_id"), str)
        or not claim.get("claim_id")
        or not isinstance(claim.get("summary"), str)
        or not claim.get("summary")
        or not isinstance(claim.get("implementation_use"), str)
        or not claim.get("implementation_use")
        or claim.get("requires_fresh_check") is not True
        for claim in claims
    ):
        errors.append(f"Official source {source_id} has an invalid or unbounded claim.")
    return errors


def validate_registry(
    payload: dict[str, Any],
    *,
    root: Path = ROOT,
    check_content: bool = True,
) -> list[str]:
    if payload.get("schema_version") != "1.0" or not isinstance(payload.get("sources"), list):
        return ["source-registry.yaml must use schema_version 1.0 and contain a sources list."]
    required = {
        "source_id",
        "source_kind",
        "publisher",
        "jurisdiction_or_venue",
        "url_or_document",
        "content_digest",
        "effective_from",
        "effective_to",
        "accessed_at",
        "applies_to",
        "confidence",
        "notes",
    }
    errors: list[str] = []
    root_path = root.resolve()
    seen_ids: set[str] = set()
    seen_targets: set[str] = set()
    for index, source in enumerate(payload["sources"]):
        if not isinstance(source, dict):
            errors.append(f"Source entry {index} must be an object.")
            continue
        missing = sorted(required - source.keys())
        if missing:
            errors.append(f"Source entry {index} missing fields: {missing}")
        source_id = str(source.get("source_id", ""))
        if not source_id or source_id in seen_ids:
            errors.append(f"Source ID is empty or duplicated: {source_id!r}")
        seen_ids.add(source_id)
        if source.get("confidence") not in {"authoritative", "corroborated", "provisional"}:
            errors.append(f"Invalid source confidence for {source_id}.")
        if not _valid_timestamp(source.get("accessed_at")):
            errors.append(f"Source {source_id} needs an explicit-timezone accessed_at timestamp.")
        if not _valid_date(source.get("effective_from")) or not _valid_date(
            source.get("effective_to")
        ):
            errors.append(f"Source {source_id} has an invalid effective date.")
        effective_from = source.get("effective_from")
        effective_to = source.get("effective_to")
        if effective_from is not None and effective_to is not None and effective_to < effective_from:
            errors.append(f"Source {source_id} effective_to precedes effective_from.")

        kind = source.get("source_kind")
        digest = str(source.get("content_digest", ""))
        if kind == "local_mirror":
            if not TREE_DIGEST.fullmatch(digest):
                errors.append(f"Source {source_id} needs a sha256-tree-v1 content digest.")
                continue
            authoring_value = source.get("authoring_path")
            target_value = source.get("mirror_target")
            if not isinstance(authoring_value, str) or not isinstance(target_value, str):
                errors.append(f"Source {source_id} needs authoring_path and mirror_target.")
                continue
            target = (root / target_value).resolve()
            if not target.is_relative_to(root.resolve()) or target_value in seen_targets:
                errors.append(f"Source {source_id} has an unsafe or duplicate mirror_target.")
                continue
            seen_targets.add(target_value)
            if not target.is_dir():
                errors.append(f"Source {source_id} mirror target is unavailable: {target}")
                continue
            if check_content:
                expected = digest.removeprefix("sha256-tree-v1:")
                target_digest = tree_digest(target)
                if target_digest != expected:
                    errors.append(f"Source {source_id} mirror digest is stale: {target_digest}")
                authoring = (root / authoring_value).resolve()
                if authoring.exists() and tree_digest(authoring) != expected:
                    errors.append(f"Source {source_id} authoring digest differs from the registry.")
        elif kind == "official_snapshot":
            errors.extend(
                _validate_official_snapshot(source, root=root, check_content=check_content)
            )
        elif kind == "local_file":
            if not FILE_DIGEST.fullmatch(digest):
                errors.append(f"Source {source_id} needs a sha256 file content digest.")
                continue
            location = str(source.get("url_or_document", ""))
            path = (root / location).resolve()
            if not path.is_relative_to(root_path):
                errors.append(f"Source {source_id} local file is unsafe: {path}")
            elif not path.is_file():
                errors.append(f"Source {source_id} local file is unavailable: {path}")
            elif check_content and file_digest(path) != digest.removeprefix("sha256:"):
                errors.append(f"Source {source_id} file digest is stale.")
        else:
            errors.append(f"Source {source_id} has unsupported source_kind {kind!r}.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync", action="store_true", help="Refresh mirrors and governed digests.")
    args = parser.parse_args()

    payload = load_registry()
    errors = validate_registry(payload, check_content=not args.sync)
    if errors:
        print("Source governance validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    available = 0
    for entry in mirror_entries(payload):
        source = (ROOT / str(entry["authoring_path"])).resolve()
        target = (ROOT / str(entry["mirror_target"])).resolve()
        if args.sync:
            if not source.is_dir():
                errors.append(f"Cannot synchronize unavailable authoring source: {source}")
                continue
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target, ignore=shutil.ignore_patterns(*IGNORED_PARTS, ".DS_Store"))
            digest = tree_digest(source)
            entry["content_digest"] = f"sha256-tree-v1:{digest}"
            entry["accessed_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
            print(f"SYNC: {entry['mirror_target']}")
        if source.is_dir():
            available += 1
            if tree_map(source) != tree_map(target):
                errors.append(f"Source mirror drift detected for {entry['mirror_target']}.")
            else:
                print(f"OK: {entry['mirror_target']} source mirror matches.")
        else:
            print(f"OK: {entry['mirror_target']} frozen mirror matches its governed digest.")

    if args.sync:
        for source in payload["sources"]:
            if isinstance(source, dict) and source.get("source_kind") == "local_file":
                path = (ROOT / str(source["url_or_document"])).resolve()
                source["content_digest"] = f"sha256:{file_digest(path)}"
                source["accessed_at"] = datetime.now(UTC).isoformat().replace(
                    "+00:00", "Z"
                )
            elif isinstance(source, dict) and source.get("source_kind") == "official_snapshot":
                path = (ROOT / str(source["snapshot_path"])).resolve()
                source["content_digest"] = f"sha256:{file_digest(path)}"
        REGISTRY_PATH.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    errors.extend(validate_registry(payload))
    if errors:
        print("Source governance validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    official_snapshots = sum(
        source.get("source_kind") == "official_snapshot"
        for source in payload["sources"]
        if isinstance(source, dict)
    )
    print(
        f"OK: verified {len(mirror_entries(payload))} governed mirror(s), "
        f"{official_snapshots} official snapshot(s); "
        f"{available} authoring source(s) available."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
