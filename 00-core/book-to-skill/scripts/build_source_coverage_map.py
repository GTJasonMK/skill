#!/usr/bin/env python3
"""Build references/core/source-coverage-map.md for a generated book skill."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SOURCE_RE = re.compile(r"^(来源|Source)\s*[:：]\s*(.+)$", re.MULTILINE)
HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
PAGE_RE = re.compile(r"PDF第(\d+)页\.txt$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the factor-style references/core/source-coverage-map.md file."
    )
    parser.add_argument("project_dir", type=Path, help="Book project directory containing txt/, md/, and a generated skill.")
    parser.add_argument(
        "--skill-dir",
        type=Path,
        help="Generated skill directory. Defaults to the only direct child directory containing SKILL.md.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing source-coverage-map.md.")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def find_skill_dirs(project_dir: Path) -> list[Path]:
    return sorted(
        path.parent
        for path in project_dir.glob("*/SKILL.md")
        if path.parent.name not in {"txt", "md", "scripts", "references"}
    )


def choose_skill_dir(project_dir: Path, requested: Path | None) -> Path:
    if requested is not None:
        skill_dir = requested.expanduser().resolve()
        if not (skill_dir / "SKILL.md").exists():
            raise FileNotFoundError(f"generated skill SKILL.md not found: {skill_dir / 'SKILL.md'}")
        return skill_dir

    skill_dirs = find_skill_dirs(project_dir)
    if not skill_dirs:
        raise FileNotFoundError("no generated skill directory with SKILL.md found as a direct child")
    if len(skill_dirs) > 1:
        names = ", ".join(str(path.relative_to(project_dir)) for path in skill_dirs)
        raise ValueError(f"multiple generated skills found; pass --skill-dir. Candidates: {names}")
    return skill_dirs[0]


def page_number(path: Path) -> int | None:
    match = PAGE_RE.search(path.name)
    return int(match.group(1)) if match else None


def md_rows(project_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    md_dir = project_dir / "md"
    if not md_dir.exists():
        return rows

    for path in sorted(md_dir.rglob("*.md")):
        text = read_text(path)
        heading = HEADING_RE.search(text)
        source = SOURCE_RE.search(text)
        rows.append(
            {
                "file": str(path.relative_to(project_dir)),
                "title": heading.group(1).strip() if heading else path.stem,
                "source": source.group(2).strip() if source else "",
            }
        )
    return rows


def txt_rows(project_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    txt_dir = project_dir / "txt"
    if not txt_dir.exists():
        return rows

    for directory in sorted(path for path in txt_dir.rglob("*") if path.is_dir()):
        files = sorted(directory.glob("*.txt"))
        if not files:
            continue
        pages = [page_number(path) for path in files]
        numeric_pages = [page for page in pages if page is not None]
        rows.append(
            {
                "dir": str(directory.relative_to(project_dir)),
                "files": len(files),
                "first_page": min(numeric_pages) if numeric_pages else "",
                "last_page": max(numeric_pages) if numeric_pages else "",
            }
        )
    return rows


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    if not rows:
        return "_None found._\n"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines) + "\n"


def build_map(project_dir: Path, skill_dir: Path) -> str:
    md = md_rows(project_dir)
    txt = txt_rows(project_dir)
    project_display = str(project_dir)

    lines = [
        "# Source Coverage Map",
        "",
        "Use this map when the user asks whether this skill covers a chapter, where a topic lives, or when exact source lookup is needed.",
        "",
        f"Parent book project: `{project_display}`",
        f"Complete source-unit notes: `{project_display}/md`",
        f"Raw page text: `{project_display}/txt`",
        "",
        "## Task Router Boundary",
        "",
        "Do not start ordinary domain tasks from this file. Use `core/decision-core.md` and `core/task-router.md` first. Use this file only for source coverage, chapter lookup, exact values, or completeness audits.",
        "",
        "## TOC-to-md Coverage Table",
        "",
        "Replace this build-time table with one row per source chapter or independently titled substantive source unit before final handoff. Part, volume, theme, and book-level rows are `synthesis` only and do not replace child source-unit notes.",
        "",
        markdown_table(
            ["Source TOC item", "PDF pages", "Complete md note", "Status", "Notes"],
            [["UNMAPPED: replace with source unit", "", "", "incomplete", "Generated placeholder; map to complete, incomplete, deferred, non-substantive, or synthesis."]],
        ),
        "Allowed statuses: `complete`, `incomplete`, `deferred`, `non-substantive`, `synthesis`.",
        "",
        "## Markdown Source-Unit Notes",
        "",
        markdown_table(
            ["Source-unit note", "Title", "Source range", "Generated reference coverage"],
            [[f"`{row['file']}`", row["title"], row["source"] or "**missing**", "UNMAPPED: map to generated references"] for row in md],
        ),
        "## Raw Text Groups",
        "",
        markdown_table(
            ["Raw text path", "Files", "First PDF page", "Last PDF page"],
            [[f"`{row['dir']}`", row["files"], row["first_page"], row["last_page"]] for row in txt],
        ),
        "## Exact-Source Lookup Rules",
        "",
        "Use the parent `md/` notes when the user asks for:",
        "",
        "1. Exact table values, dates, formulas, names, scene details, or page-linked claims.",
        "2. The full structure of a chapter or section.",
        "3. A source-grounded comparison between generated references and original source-unit notes.",
        "4. A passage that may require raw `txt/` or PDF inspection for exact wording.",
        "",
        "For ordinary domain explanation, application, review, or literary interpretation tasks, prefer generated references first and load parent `md/` only when the requested detail is source-specific.",
        "",
        "## Coverage Gaps",
        "",
        "- UNMAPPED: record missing, deferred, OCR-risk, visual-risk, or not-yet-distilled sections.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    project_dir = args.project_dir.expanduser().resolve()
    if not project_dir.exists():
        print(f"ERROR: project directory not found: {project_dir}", file=sys.stderr)
        return 2

    try:
        skill_dir = choose_skill_dir(project_dir, args.skill_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    output = skill_dir / "references" / "core" / "source-coverage-map.md"
    if output.exists() and not args.force:
        print(f"ERROR: output already exists: {output}. Use --force to overwrite.", file=sys.stderr)
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_map(project_dir, skill_dir), encoding="utf-8")
    print(f"OK: wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
