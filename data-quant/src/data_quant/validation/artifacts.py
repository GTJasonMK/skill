"""Artifact generation for time-aware validation folds."""

from __future__ import annotations

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, ProducerReference
from data_quant.validation.splits import TimeFold


def split_artifact(
    folds: list[TimeFold],
    *,
    method: str,
    parameters: dict,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    details = [
        {
            "fold": fold.fold,
            "train_count": len(fold.train_positions),
            "test_count": len(fold.test_positions),
            "train_start": fold.train_start.isoformat(),
            "train_end": fold.train_end.isoformat(),
            "test_start": fold.test_start.isoformat(),
            "test_end": fold.test_end.isoformat(),
            "purged_count": fold.purged_count,
            "embargoed_count": fold.embargoed_count,
        }
        for fold in folds
    ]
    return ArtifactEnvelope(
        artifact_type="validation_split",
        run_id=run_id,
        producer=ProducerReference(name=method, version=__version__),
        parameters=parameters,
        summary={
            "method": method,
            "fold_count": len(folds),
            "total_purged": sum(fold.purged_count for fold in folds),
            "total_embargoed": sum(fold.embargoed_count for fold in folds),
        },
        details=details,
    ).finalize()
