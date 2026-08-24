#!/usr/bin/env python3
"""Check SKILL.md / implementation-map.md / scripts/ / references/ consistency.

Standard-library only. Fails non-zero when:

1. A script in ``scripts/`` (excluding ``_*.py`` and shared helpers) is not
   referenced in SKILL.md's ``## Scripts`` and ``## References`` sections.
2. A reference in ``references/*.md`` is not linked in SKILL.md's
   ``## References`` section.
3. SKILL.md references a script or reference path that does not exist.
4. A bundled script is missing from the "Bundled Scripts" table in
   ``references/implementation-map.md``.

Run via ``python3 scripts/_check_skill_index.py`` from the repository root.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = ROOT / "SKILL.md"
SCRIPTS_DIR = ROOT / "scripts"
REFERENCES_DIR = ROOT / "references"
IMPLEMENTATION_MAP = REFERENCES_DIR / "implementation-map.md"

SHARED_HELPERS = {"quant_utils.py"}
EXCLUDE_PREFIX = "_"  # underscore-prefixed scripts are internal


def list_scripts() -> set[str]:
    return {
        p.name
        for p in SCRIPTS_DIR.iterdir()
        if p.is_file()
        and p.suffix == ".py"
        and not p.name.startswith(EXCLUDE_PREFIX)
        and p.name not in SHARED_HELPERS
    }


def list_references() -> set[str]:
    return {p.name for p in REFERENCES_DIR.iterdir() if p.is_file() and p.suffix == ".md"}


def parse_skill_md() -> tuple[set[str], set[str], set[str]]:
    text = SKILL_MD.read_text(encoding="utf-8")
    # Find which scripts appear in the ## Scripts section vs ## References section
    scripts_section = re.search(r"## Scripts\n(.+?)(?=\n## )", text, re.DOTALL)
    references_section = re.search(r"## References\n(.+?)(?=\n## |\Z)", text, re.DOTALL)
    scripts_in_scripts_section = set()
    if scripts_section:
        scripts_in_scripts_section = set(re.findall(r"scripts/([A-Za-z0-9_]+\.py)", scripts_section.group(1)))
    scripts_in_references_section = set()
    references_in_references_section = set()
    if references_section:
        scripts_in_references_section = set(
            re.findall(r"scripts/([A-Za-z0-9_]+\.py)", references_section.group(1))
        )
        references_in_references_section = set(
            re.findall(r"references/([A-Za-z0-9_\-]+\.md)", references_section.group(1))
        )
    return (
        scripts_in_scripts_section,
        scripts_in_references_section,
        references_in_references_section,
    )


def parse_implementation_map() -> set[str]:
    text = IMPLEMENTATION_MAP.read_text(encoding="utf-8")
    bundled_section = re.search(r"##\s*Bundled Scripts\b(.+?)(?=\n##\s|\Z)", text, re.DOTALL)
    if not bundled_section:
        return set()
    return set(re.findall(r"`scripts/([A-Za-z0-9_]+\.py)`", bundled_section.group(1)))


def main() -> int:
    if not SKILL_MD.exists():
        print(f"FATAL: {SKILL_MD} not found", file=sys.stderr)
        return 2
    actual_scripts = list_scripts()
    actual_refs = list_references()
    skill_scripts_section, skill_refs_section_scripts, skill_refs_section_refs = parse_skill_md()
    imap_scripts = parse_implementation_map()

    errors: list[str] = []

    # 1. Every actual script must be in SKILL.md ## Scripts section
    missing_in_scripts = actual_scripts - skill_scripts_section
    if missing_in_scripts:
        errors.append("Missing from SKILL.md ## Scripts section: " + ", ".join(sorted(missing_in_scripts)))

    # 2. Every actual script must be in SKILL.md ## References section
    missing_in_refs = actual_scripts - skill_refs_section_scripts
    if missing_in_refs:
        errors.append(
            "Missing from SKILL.md ## References section (script links): "
            + ", ".join(sorted(missing_in_refs))
        )

    # 3. Every reference markdown must be linked in SKILL.md
    missing_md_in_skill = actual_refs - skill_refs_section_refs
    if missing_md_in_skill:
        errors.append(
            "Missing from SKILL.md ## References section (doc links): "
            + ", ".join(sorted(missing_md_in_skill))
        )

    # 4. SKILL.md must not link to nonexistent files
    real_scripts_on_disk = {p.name for p in SCRIPTS_DIR.iterdir() if p.suffix == ".py"}
    referenced_scripts = skill_scripts_section | skill_refs_section_scripts
    nonexistent_scripts = referenced_scripts - real_scripts_on_disk
    if nonexistent_scripts:
        errors.append("SKILL.md links to nonexistent scripts: " + ", ".join(sorted(nonexistent_scripts)))
    nonexistent_refs = skill_refs_section_refs - actual_refs
    if nonexistent_refs:
        errors.append("SKILL.md links to nonexistent references: " + ", ".join(sorted(nonexistent_refs)))

    # 5. Implementation-map should include each script in its Bundled Scripts table
    missing_in_imap = actual_scripts - imap_scripts
    if missing_in_imap:
        errors.append(
            "Missing from references/implementation-map.md Bundled Scripts table: "
            + ", ".join(sorted(missing_in_imap))
        )

    if errors:
        print("Index inconsistencies:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"OK: {len(actual_scripts)} scripts and {len(actual_refs)} references are fully indexed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
