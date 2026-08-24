"""Runtime paths that distinguish the core wheel from the full source Skill bundle."""

from __future__ import annotations

from pathlib import Path


def source_bundle_root() -> Path | None:
    """Return the full Skill bundle root when running from a source checkout."""

    for parent in Path(__file__).resolve().parents:
        if (parent / "BUNDLE-MANIFEST.yaml").is_file() and (
            parent / "statistical-learning-analysis/scripts"
        ).is_dir():
            return parent
    return None
