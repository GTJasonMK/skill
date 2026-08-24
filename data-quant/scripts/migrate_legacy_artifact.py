#!/usr/bin/env python3
"""Wrap one legacy JSON diagnostic in the Artifact Envelope v1 contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from data_quant import __version__  # noqa: E402
from data_quant.contracts.artifacts import (  # noqa: E402
    ArtifactEnvelope,
    DiagnosticMessage,
    ProducerReference,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("legacy_json", type=Path)
    parser.add_argument("--artifact-type", required=True)
    parser.add_argument("--producer", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.legacy_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("Legacy JSON root must be an object.")
    artifact = ArtifactEnvelope(
        artifact_type=args.artifact_type,
        run_id=args.run_id,
        producer=ProducerReference(name=args.producer, version=__version__),
        summary={"legacy_payload": payload},
        warnings=[
            DiagnosticMessage(
                code="legacy_payload_adapter",
                message=(
                    "Legacy payload requires field-level normalization in a later immutable "
                    "schema version."
                ),
                severity="warning",
            )
        ],
        provenance={"legacy_json": str(args.legacy_json.resolve())},
    ).finalize()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
