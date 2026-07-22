#!/usr/bin/env python3
"""Initialize a book-to-skill project directory."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path


SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$")


def validate_skill_name(skill_name: str) -> None:
    if not SKILL_NAME_RE.fullmatch(skill_name):
        raise ValueError(
            "skill name must be lowercase hyphen-case, 2-64 characters, "
            "using only a-z, 0-9, and hyphen, and must not start or end with hyphen"
        )


def skill_title(skill_name: str) -> str:
    return " ".join(part.capitalize() for part in skill_name.replace("_", "-").split("-") if part)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a book project with PDF, txt/, md/, and a generated-skill folder.")
    parser.add_argument("project_dir", type=Path, help="Book project directory to create or update.")
    parser.add_argument("--pdf", type=Path, help="Source PDF path to copy or symlink into the project.")
    parser.add_argument("--skill-name", default="", help="Generated skill folder name to create under the project.")
    parser.add_argument(
        "--pdf-action",
        choices=("copy", "symlink"),
        default="copy",
        help="How to handle --pdf. Default copies the PDF into the project.",
    )
    return parser.parse_args()


def resolve_pdf_source(pdf: Path) -> Path:
    if not pdf:
        raise ValueError("PDF path is required")
    source = pdf.expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"PDF not found: {source}")
    if source.suffix.lower() != ".pdf":
        raise ValueError(f"PDF source must use a .pdf extension: {source}")
    return source


def link_or_copy_pdf(source: Path, project_dir: Path, action: str) -> str:

    target = project_dir / source.name
    if target.exists():
        return str(target.resolve())
    if action == "copy":
        shutil.copy2(source, target)
    elif action == "symlink":
        os.symlink(source, target)
    return str(target.resolve())


def write_if_missing(path: Path, text: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def scaffold_generated_skill(project_dir: Path, skill_name: str) -> None:
    validate_skill_name(skill_name)
    skill_dir = project_dir / skill_name
    title = skill_title(skill_name)
    write_if_missing(
        skill_dir / "SKILL.md",
        f"""---
name: {skill_name}
description: "Book-derived domain workflow for {title}. Use when Codex needs to explain, apply, review, interpret, or source-check this book's concepts, arguments, methods, scenes, themes, or evidence."
---

# {title}

## Overview

Use this skill as the domain workflow layer derived from the local book project.

The parent project keeps complete source-unit notes in `{project_dir}/md` and page-level source text in `{project_dir}/txt`.

## Reference Routing

- For broad tasks, read [references/core/decision-core.md](references/core/decision-core.md) first, then [references/core/task-router.md](references/core/task-router.md).
- For directory layout or load-order uncertainty, read [references/core/reference-architecture.md](references/core/reference-architecture.md).
- For exact source coverage, read [references/core/source-coverage-map.md](references/core/source-coverage-map.md).
- For final deliverables, read [references/core/report-templates.md](references/core/report-templates.md).

## Core Reasoning Spine

1. Classify the user's request.
2. Select the smallest relevant reference.
3. Separate book claim, agent interpretation, and recommendation.
4. Escalate to parent `md/` notes or `txt/` pages only when source fidelity matters.

## Output Contract

- Answer in the book's domain terms.
- Name the source layer when exactness matters.
- Surface uncertainty instead of filling gaps.

## Hard Rules

- Do not invent quotes, page numbers, formulas, table values, or scene details.
- Do not load the whole book for ordinary tasks.
- Do not treat generated references as a replacement for exact source lookup.
""",
    )
    write_if_missing(
        skill_dir / "agents" / "openai.yaml",
        f"""interface:
  display_name: "{title}"
  short_description: "Book-derived domain workflow"
  default_prompt: "Use ${skill_name} to answer with the book-derived workflow and source coverage."
""",
    )
    write_if_missing(
        skill_dir / "references" / "core" / "decision-core.md",
        """# Decision Core

Use this first for broad or ambiguous tasks.

## Core Decision Chain

```text
request -> task type -> source layer -> reasoning path -> output shape
```

## Load-Minimum Rule

Start from this file, then load only the reference needed for the current uncertainty.
""",
    )
    write_if_missing(
        skill_dir / "references" / "core" / "task-router.md",
        """# Task Router

Use this file to route ordinary tasks to the smallest useful reference bundle.

| Task | Use when | Minimum references | Add only if needed | Output shape |
| --- | --- | --- | --- | --- |
| Source lookup | User asks where the book covers something | `core/source-coverage-map.md` | parent `md/` or `txt/` | Source path and brief answer |
| Broad explanation | User asks for a book-derived explanation | `core/decision-core.md` | task-specific references | Book-specific answer |
| Review or critique | User asks whether something follows the book | `core/decision-core.md` | source coverage or task references | Findings and source basis |
""",
    )
    write_if_missing(
        skill_dir / "references" / "core" / "reference-architecture.md",
        """# Reference Architecture

Use this when the generated skill's directory layout or load order is unclear.

## Default Loading Order

```text
core/decision-core.md
-> core/task-router.md
-> one task-specific reference
-> core/source-coverage-map.md only for exact source lookup
-> core/report-templates.md when formatting the final answer
```
""",
    )
    write_if_missing(
        skill_dir / "references" / "core" / "source-coverage-map.md",
        f"""# Source Coverage Map

Parent book project: `{project_dir}`
Complete source-unit notes: `{project_dir}/md`
Raw page text: `{project_dir}/txt`

Use this map for source coverage, source-unit lookup, exact values, and completeness audits.

## TOC-to-md Coverage Table

Replace this build-time table with one row per source chapter or independently titled substantive source unit before final handoff.

| Source TOC item | PDF pages | Complete md note | Status | Notes |
| --- | --- | --- | --- | --- |
| UNMAPPED: replace with source unit |  |  | incomplete | Generated placeholder; map to complete, incomplete, deferred, non-substantive, or synthesis. |

Allowed statuses: `complete`, `incomplete`, `deferred`, `non-substantive`, `synthesis`.
""",
    )
    write_if_missing(
        skill_dir / "references" / "core" / "report-templates.md",
        """# Report Templates

Use this after selecting the task-specific reference bundle.

## Source-Grounded Answer

- Answer:
- Source layer:
- Uncertainty:
- Next source to inspect:
""",
    )


def main() -> int:
    args = parse_args()
    project_dir = args.project_dir.expanduser().resolve()

    try:
        if args.skill_name:
            validate_skill_name(args.skill_name)
        pdf_source = resolve_pdf_source(args.pdf) if args.pdf else None
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "txt").mkdir(exist_ok=True)
    (project_dir / "md").mkdir(exist_ok=True)

    try:
        source_pdf = link_or_copy_pdf(pdf_source, project_dir, args.pdf_action) if pdf_source else ""
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.skill_name:
        scaffold_generated_skill(project_dir, args.skill_name)

    print(f"OK: initialized {project_dir}")
    if source_pdf:
        print(f"PDF: {source_pdf}")
    if args.skill_name:
        print(f"Generated skill scaffold: {project_dir / args.skill_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
