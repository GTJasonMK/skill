#!/usr/bin/env python3
"""Validate the structure of a book-to-skill project."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
LINK_RE = re.compile(r"\[[^\]]+\]\((?!https?://|mailto:|#)([^)]+)\)")
SOURCE_RE = re.compile(r"^(来源|Source)\s*[:：]\s*(.+)$", re.MULTILINE)
PAGE_RE = re.compile(r"PDF第(\d+)页\.txt$")
SOURCE_PAGE_RE = re.compile(r"PDF第(\d+)页(?:\.txt)?")
BACKTICK_PATH_RE = re.compile(r"`([^`]+)`")
SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$")
FRONTMATTER_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):", re.MULTILINE)
CHAPTER_HEADING_RE = re.compile(
    r"^##\s+(?:Chapter\s+\d+|CHAPTER\s+\d+|第\s*[一二三四五六七八九十百零〇两0-9]+\s*章)\b",
    re.MULTILINE,
)
PART_TITLE_RE = re.compile(
    r"(第\s*[一二三四五六七八九十百零〇两0-9]+\s*部分|\bPart\s+(?:[IVXLCDM]+|\d+)\b)",
    re.IGNORECASE,
)
NAVIGATION_NOTE_RE = re.compile(
    r"(书籍地图|TOC|目录|覆盖|coverage|source[-_ ]coverage|抽取质量|book[-_ ]map)",
    re.IGNORECASE,
)
TOC_COVERAGE_RE = re.compile(
    r"(TOC\s*(?:到|to|-)\s*md\s*覆盖表|TOC[-_ ]coverage|TOC[-_ ]to[-_ ]md|源书\s*TOC\s*项|Source\s+TOC\s+item|source[-_ ]unit\s+coverage)",
    re.IGNORECASE,
)
COVERAGE_STATUS_RE = re.compile(r"\b(complete|incomplete|deferred|non-substantive|synthesis)\b")
ABSTRACT_NOTE_RE = re.compile(r"(摘要|abstract|digest|brief)", re.IGNORECASE)
CHAPTER_UNIT_RE = re.compile(
    r"(?:\bChapter\s+\d+\b|第\s*[一二三四五六七八九十百零〇两0-9]+\s*章)",
    re.IGNORECASE,
)
PARTIAL_STATUS_TERMS = {
    "incomplete",
    "deferred",
    "partial",
    "pending",
    "todo",
    "wip",
    "未完成",
    "未完",
    "待补",
    "待处理",
    "待完成",
    "延期",
    "暂缓",
    "延后",
    "施工中",
}
FINAL_ALLOWED_STATUSES = {"complete", "non-substantive", "synthesis"}
NON_CONTENT_STATUSES = {"non-substantive", "synthesis"}
COMPLETENESS_AUDIT_HEADINGS = {
    "page/section coverage": re.compile(r"^##\s+(页/段落覆盖|逐页覆盖|章节覆盖|Page/Section Coverage)\s*$", re.MULTILINE),
    "omission audit": re.compile(r"^##\s+(遗漏审计|遗漏检查|Omission Audit)\s*$", re.MULTILINE),
    "iteration records": re.compile(r"^##\s+(迭代修订记录|修订记录|Revision Records?|Iteration Records?)\s*$", re.MULTILINE),
    "no-known-omissions statement": re.compile(
        r"^##\s+(最终无遗漏声明|无遗漏声明|No-Known-Omissions Statement|Final No-Known-Omissions Statement)\s*$",
        re.MULTILINE,
    ),
}
UNRESOLVED_OMISSION_TERMS = {
    "待补",
    "待处理",
    "待完成",
    "未解决",
    "未处理",
    "尚未",
    "pending",
    "unresolved",
    "not yet",
    "todo",
}

REQUIRED_CORE_REFERENCES = [
    "decision-core.md",
    "task-router.md",
    "reference-architecture.md",
    "source-coverage-map.md",
    "report-templates.md",
]

DEFAULT_SCAFFOLD_MARKERS = [
    "Use this skill as the domain workflow layer derived from the local book project.",
    "Book-derived domain workflow",
    "request -> task type -> source layer -> reasoning path -> output shape",
    "Use this file to route ordinary tasks to the smallest useful reference bundle.",
    "Source lookup | User asks where the book covers something",
    "Broad explanation | User asks for a book-derived explanation",
    "Review or critique | User asks whether something follows the book",
    "Use this when the generated skill's directory layout or load order is unclear.",
    "Use this after selecting the task-specific reference bundle.",
    "- Answer:\n- Source layer:\n- Uncertainty:\n- Next source to inspect:",
]

PLACEHOLDER_MARKERS = [
    "generated-skill-name",
    "generated-literary-skill",
    "/absolute/path/to/book-project",
    "<book-project>",
    "<generated-skill>",
    "<book>",
    "Use this skill to ...",
    "Book-derived workflow for ...",
    "Use when Codex needs to ...",
    "中文触发：...",
]

REQUIRED_OPENAI_YAML_MARKERS = [
    "interface:",
    "display_name:",
    "short_description:",
    "default_prompt:",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a book project containing txt/, md/, and a generated skill.")
    parser.add_argument("project_dir", type=Path, help="Book project directory.")
    parser.add_argument("--max-skill-lines", type=int, default=260, help="Warn when generated SKILL.md exceeds this length.")
    parser.add_argument(
        "--max-md-source-pages",
        type=int,
        default=40,
        help="Warn when a non-navigation md note covers more PDF pages than this.",
    )
    parser.add_argument(
        "--max-chapters-per-md-note",
        type=int,
        default=1,
        help="Warn when a single md note appears to contain more chapter-level headings than this.",
    )
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors for final handoff.")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def find_skill_dirs(project_dir: Path) -> list[Path]:
    return sorted(
        path.parent
        for path in project_dir.glob("*/SKILL.md")
        if path.parent.name not in {"txt", "md", "scripts", "references"}
    )


def check_markdown_links(path: Path, root: Path) -> list[str]:
    text = read_text(path)
    errors: list[str] = []
    for raw_link in LINK_RE.findall(text):
        target = raw_link.split("#", 1)[0].strip()
        if not target:
            continue
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        target_path = (path.parent / target).resolve()
        try:
            target_path.relative_to(root.resolve())
        except ValueError:
            # External local path. Accept it; source coverage may point outside the skill.
            continue
        if not target_path.exists():
            errors.append(f"{path.relative_to(root)} links to missing file: {raw_link}")
    return errors


def default_scaffold_hits(text: str) -> list[str]:
    return [marker for marker in DEFAULT_SCAFFOLD_MARKERS if marker in text]


def placeholder_hits(text: str) -> list[str]:
    return [marker for marker in PLACEHOLDER_MARKERS if marker in text]


def parse_frontmatter_value(body: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.*?)\s*$", body, re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1].strip()
    return value


def check_skill(skill_dir: Path, project_dir: Path, max_lines: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    text = read_text(skill_md)
    frontmatter = FRONTMATTER_RE.search(text)
    if not frontmatter:
        errors.append(f"{skill_md.relative_to(project_dir)} is missing YAML frontmatter.")
    else:
        body = frontmatter.group("body")
        if "name:" not in body or "description:" not in body:
            errors.append(f"{skill_md.relative_to(project_dir)} frontmatter must include name and description.")
        extra_keys = sorted({key for key in FRONTMATTER_KEY_RE.findall(body) if key not in {"name", "description"}})
        if extra_keys:
            errors.append(
                f"{skill_md.relative_to(project_dir)} frontmatter has unsupported fields: "
                + ", ".join(extra_keys)
            )
        skill_name = parse_frontmatter_value(body, "name")
        description = parse_frontmatter_value(body, "description")
        if not description:
            errors.append(f"{skill_md.relative_to(project_dir)} frontmatter description could not be parsed.")
        if not skill_name and "name:" in body:
            errors.append(f"{skill_md.relative_to(project_dir)} frontmatter name could not be parsed.")
        elif skill_name:
            if re.search(r"\s", skill_name):
                errors.append(f"{skill_md.relative_to(project_dir)} frontmatter name `{skill_name}` contains whitespace.")
            if skill_name != skill_dir.name:
                errors.append(
                    f"{skill_md.relative_to(project_dir)} frontmatter name `{skill_name}` "
                    f"does not match folder `{skill_dir.name}`."
                )
            if not SKILL_NAME_RE.fullmatch(skill_name):
                errors.append(
                    f"{skill_md.relative_to(project_dir)} frontmatter name `{skill_name}` "
                    "is not valid lowercase hyphen-case."
                )
        if "TODO" in body or "[TODO" in body:
            errors.append(f"{skill_md.relative_to(project_dir)} frontmatter still contains TODO text.")

    line_count = len(text.splitlines())
    if line_count > max_lines:
        warnings.append(f"{skill_md.relative_to(project_dir)} has {line_count} lines; check for context bloat.")
    if "TODO" in text or "[TODO" in text or "UNMAPPED" in text:
        warnings.append(f"{skill_md.relative_to(project_dir)} still contains TODO or UNMAPPED markers.")
    skill_placeholder_hits = placeholder_hits(text)
    if skill_placeholder_hits:
        warnings.append(
            f"{skill_md.relative_to(project_dir)} still contains template placeholders; "
            "replace them with book-specific values."
        )
    skill_scaffold_hits = default_scaffold_hits(text)
    if skill_scaffold_hits:
        warnings.append(
            f"{skill_md.relative_to(project_dir)} still contains default scaffold wording; "
            "replace it with book-specific domain guidance."
        )
    if "Reference Routing" not in text and "参考" not in text:
        warnings.append(f"{skill_md.relative_to(project_dir)} may lack explicit reference routing.")
    if "Hard Rules" not in text and "硬规则" not in text and "禁止" not in text:
        warnings.append(f"{skill_md.relative_to(project_dir)} may lack hard rules.")

    agents_yaml = skill_dir / "agents" / "openai.yaml"
    if not agents_yaml.exists():
        warnings.append(f"{skill_dir.relative_to(project_dir)} is missing agents/openai.yaml.")
    else:
        agents_text = read_text(agents_yaml)
        for marker in REQUIRED_OPENAI_YAML_MARKERS:
            if marker not in agents_text:
                warnings.append(f"{agents_yaml.relative_to(project_dir)} is missing `{marker}`.")
        agents_hits = default_scaffold_hits(agents_text)
        agents_placeholder_hits = placeholder_hits(agents_text)
        if agents_placeholder_hits:
            warnings.append(
                f"{agents_yaml.relative_to(project_dir)} still contains template placeholders; "
                "replace them with book-specific display text."
            )
        if agents_hits:
            warnings.append(
                f"{agents_yaml.relative_to(project_dir)} still contains default scaffold metadata; "
                "replace it with book-specific display text."
            )

    core_dir = skill_dir / "references" / "core"
    for filename in REQUIRED_CORE_REFERENCES:
        required_path = core_dir / filename
        if not required_path.exists():
            errors.append(f"{skill_dir.relative_to(project_dir)} is missing references/core/{filename}.")

    reference_files = sorted((skill_dir / "references").rglob("*.md")) if (skill_dir / "references").exists() else []
    for ref_path in reference_files:
        ref_text = read_text(ref_path)
        if "TODO" in ref_text or "[TODO" in ref_text or "UNMAPPED" in ref_text:
            warnings.append(f"{ref_path.relative_to(project_dir)} still contains TODO or UNMAPPED markers.")
        ref_placeholder_hits = placeholder_hits(ref_text)
        if ref_placeholder_hits:
            warnings.append(
                f"{ref_path.relative_to(project_dir)} still contains template placeholders; "
                "replace them with book-specific routing, rules, or templates."
            )
        ref_scaffold_hits = default_scaffold_hits(ref_text)
        if ref_scaffold_hits:
            warnings.append(
                f"{ref_path.relative_to(project_dir)} still contains default scaffold wording; "
                "replace it with book-specific routing, rules, or templates."
            )

    for md_path in [skill_md, *reference_files]:
        errors.extend(check_markdown_links(md_path, project_dir))
    return errors, warnings


def check_page_coverage(txt_files: list[Path], project_dir: Path) -> list[str]:
    warnings: list[str] = []
    pages: dict[int, list[Path]] = {}
    for path in txt_files:
        match = PAGE_RE.search(path.name)
        if not match:
            continue
        pages.setdefault(int(match.group(1)), []).append(path)

    duplicates = {page: paths for page, paths in pages.items() if len(paths) > 1}
    if duplicates:
        details = []
        for page, paths in sorted(duplicates.items()):
            rel_paths = ", ".join(str(path.relative_to(project_dir)) for path in paths)
            details.append(f"PDF page {page}: {rel_paths}")
        warnings.append("Duplicate PDF page text files found: " + "; ".join(details))

    if pages:
        ordered = sorted(pages)
        missing = [page for page in range(ordered[0], ordered[-1] + 1) if page not in pages]
        if missing:
            preview = ", ".join(str(page) for page in missing[:20])
            suffix = "..." if len(missing) > 20 else ""
            warnings.append(
                f"Missing PDF page text files within extracted range {ordered[0]}-{ordered[-1]}: "
                f"{preview}{suffix}"
            )
    return warnings


def txt_page_map(txt_files: list[Path]) -> dict[int, list[Path]]:
    pages: dict[int, list[Path]] = {}
    for path in txt_files:
        match = PAGE_RE.search(path.name)
        if not match:
            continue
        pages.setdefault(int(match.group(1)), []).append(path)
    return pages


def reported_short_or_empty_pages(project_dir: Path) -> tuple[set[int], list[str]]:
    pages: set[int] = set()
    warnings: list[str] = []
    txt_dir = project_dir / "txt"
    if not txt_dir.exists():
        return pages, warnings

    for report_path in sorted(txt_dir.rglob("extraction-report.json")):
        try:
            report = json.loads(read_text(report_path))
        except json.JSONDecodeError as exc:
            warnings.append(f"{report_path.relative_to(project_dir)} is not valid JSON: {exc}")
            continue
        raw_pages = report.get("short_or_empty_pages", [])
        if not isinstance(raw_pages, list):
            warnings.append(f"{report_path.relative_to(project_dir)} short_or_empty_pages is not a list.")
            continue
        for page in raw_pages:
            if isinstance(page, int):
                pages.add(page)
            elif isinstance(page, str) and page.isdigit():
                pages.add(int(page))
            else:
                warnings.append(f"{report_path.relative_to(project_dir)} has invalid short page value: {page!r}")
    return pages, warnings


def check_md_note_sources(md_files: list[Path], txt_files: list[Path], project_dir: Path) -> list[str]:
    warnings: list[str] = []
    pages = txt_page_map(txt_files)
    for path in md_files:
        text = read_text(path)
        source_match = SOURCE_RE.search(text)
        if not source_match:
            continue
        source = source_match.group(2)

        for raw_path in BACKTICK_PATH_RE.findall(source):
            if raw_path.startswith(("txt/", "md/")) and not (project_dir / raw_path).exists():
                warnings.append(f"{path.relative_to(project_dir)} source path does not exist: {raw_path}")

        source_pages = [int(number) for number in SOURCE_PAGE_RE.findall(source)]
        if not source_pages:
            warnings.append(f"{path.relative_to(project_dir)} source marker has no PDF page number: {source}")
            continue

        pages_to_check = set(source_pages)
        if len(source_pages) >= 2 and any(marker in source for marker in ("至", "到", "-", "–", "—", "to")):
            start, end = source_pages[0], source_pages[-1]
            if start <= end:
                pages_to_check.update(range(start, end + 1))

        missing = sorted(page for page in pages_to_check if page not in pages)
        if missing:
            preview = ", ".join(str(page) for page in missing[:20])
            suffix = "..." if len(missing) > 20 else ""
            warnings.append(
                f"{path.relative_to(project_dir)} references missing PDF page text files: "
                f"{preview}{suffix}"
            )
    return warnings


def source_page_numbers(text: str) -> list[int]:
    source_match = SOURCE_RE.search(text)
    if not source_match:
        return []
    return [int(number) for number in SOURCE_PAGE_RE.findall(source_match.group(2))]


def source_page_span(page_numbers: list[int]) -> tuple[int, int, int] | None:
    if not page_numbers:
        return None
    if len(page_numbers) == 1:
        page = page_numbers[0]
        return page, page, 1
    start = page_numbers[0]
    end = page_numbers[-1]
    if start > end:
        start, end = min(page_numbers), max(page_numbers)
    return start, end, end - start + 1


def is_navigation_note(path: Path, text: str) -> bool:
    title = "\n".join(text.splitlines()[:8])
    return bool(NAVIGATION_NOTE_RE.search(path.name) or NAVIGATION_NOTE_RE.search(title))


def first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return ""


def check_md_note_granularity(
    md_files: list[Path],
    project_dir: Path,
    max_md_source_pages: int,
    max_chapters_per_md_note: int,
) -> list[str]:
    warnings: list[str] = []
    for path in md_files:
        text = read_text(path)
        page_span = source_page_span(source_page_numbers(text))
        navigation_note = is_navigation_note(path, text)
        title = first_heading(text)
        part_like = bool(PART_TITLE_RE.search(path.stem) or PART_TITLE_RE.search(title))
        abstract_like = bool(ABSTRACT_NOTE_RE.search(path.stem) or ABSTRACT_NOTE_RE.search(title))
        chapter_headings = CHAPTER_HEADING_RE.findall(text)
        rel_path = path.relative_to(project_dir)

        if abstract_like and not navigation_note:
            warnings.append(
                f"{rel_path} looks like an abstract/digest file; md/ files must be complete content notes, "
                "not brief summaries."
            )

        if page_span:
            start, end, span = page_span
            if span > max_md_source_pages and not navigation_note:
                warnings.append(
                    f"{rel_path} covers PDF pages {start}-{end} ({span} pages), above "
                    f"--max-md-source-pages={max_md_source_pages}; split long source units or record a justified exception."
                )
            if part_like and span > max_md_source_pages:
                warnings.append(
                    f"{rel_path} looks part-level and covers PDF pages {start}-{end} ({span} pages); "
                    "part-level synthesis files do not replace complete per-chapter/source-unit notes."
                )

        if len(chapter_headings) > max_chapters_per_md_note:
            warnings.append(
                f"{rel_path} contains {len(chapter_headings)} chapter-level headings, above "
                f"--max-chapters-per-md-note={max_chapters_per_md_note}; "
                "write separate complete notes for each substantive source chapter."
            )
        if part_like and len(chapter_headings) > 1:
            warnings.append(
                f"{rel_path} is part-level and contains multiple chapter headings; "
                "this is a part guide, not complete child-chapter coverage."
            )
    return warnings


def check_md_completeness_audit(md_files: list[Path], project_dir: Path) -> list[str]:
    warnings: list[str] = []
    for path in md_files:
        text = read_text(path)
        if is_navigation_note(path, text):
            continue
        rel_path = path.relative_to(project_dir)
        missing = [
            label
            for label, pattern in COMPLETENESS_AUDIT_HEADINGS.items()
            if not pattern.search(text)
        ]
        if missing:
            warnings.append(
                f"{rel_path} lacks required completeness-audit sections: "
                + ", ".join(missing)
            )
            continue

        audit_text = text.split("## 遗漏审计", 1)[-1] if "## 遗漏审计" in text else text
        unresolved_terms = [term for term in sorted(UNRESOLVED_OMISSION_TERMS) if term.lower() in audit_text.lower()]
        if unresolved_terms:
            warnings.append(
                f"{rel_path} completeness audit still appears to contain unresolved omission markers: "
                + ", ".join(unresolved_terms[:8])
            )
    return warnings


def check_toc_coverage_table(md_files: list[Path], skill_dirs: list[Path], project_dir: Path) -> list[str]:
    warnings: list[str] = []
    candidates: list[Path] = list(md_files)
    for skill_dir in skill_dirs:
        coverage_map = skill_dir / "references" / "core" / "source-coverage-map.md"
        if coverage_map.exists():
            candidates.append(coverage_map)

    matching_paths: list[Path] = []
    status_paths: list[Path] = []
    matching_text = ""
    for path in candidates:
        text = read_text(path)
        if TOC_COVERAGE_RE.search(text):
            matching_paths.append(path)
            matching_text += "\n" + text
            if COVERAGE_STATUS_RE.search(text):
                status_paths.append(path)

    if not matching_paths:
        warnings.append(
            "No explicit TOC/source-unit coverage table found in md/ or references/core/source-coverage-map.md; "
            "final bundles must map every substantive source unit to a complete md note or an explicit status."
        )
    else:
        warnings.extend(check_coverage_rows(matching_text, project_dir))
    if matching_paths and not status_paths:
        paths = ", ".join(str(path.relative_to(project_dir)) for path in matching_paths[:5])
        warnings.append(
            "TOC/source-unit coverage table found but no valid coverage statuses "
            f"(complete, incomplete, deferred, non-substantive, synthesis) were detected: {paths}"
        )
    if matching_paths:
        missing_md_paths: list[str] = []
        for path in md_files:
            text = read_text(path)
            if is_navigation_note(path, text):
                continue
            rel_path = str(path.relative_to(project_dir))
            if rel_path not in matching_text:
                missing_md_paths.append(rel_path)
        if missing_md_paths:
            preview = ", ".join(missing_md_paths[:10])
            suffix = "..." if len(missing_md_paths) > 10 else ""
            warnings.append(
                "TOC/source-unit coverage table does not list every non-navigation md note: "
                f"{preview}{suffix}"
            )
    return warnings


def markdown_table_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    if cells and all(set(cell) <= {"-", ":", " "} for cell in cells):
        return []
    return cells


def normalize_status(cell: str) -> str | None:
    normalized = cell.strip().strip("`").lower()
    if normalized in FINAL_ALLOWED_STATUSES or normalized in PARTIAL_STATUS_TERMS:
        return normalized
    return None


def contains_partial_status(text: str) -> bool:
    normalized = text.lower()
    return any(term in normalized for term in PARTIAL_STATUS_TERMS)


def row_md_paths(row: str) -> list[str]:
    paths: list[str] = []
    for raw_path in BACKTICK_PATH_RE.findall(row):
        if raw_path.startswith("md/") and raw_path.endswith(".md"):
            paths.append(raw_path)
    return paths


def check_coverage_rows(text: str, project_dir: Path) -> list[str]:
    warnings: list[str] = []
    partial_rows: list[str] = []
    non_content_chapter_rows: list[str] = []
    complete_rows_without_md: list[str] = []
    coverage_rows_without_status: list[str] = []
    missing_paths: list[str] = []

    for line in text.splitlines():
        cells = markdown_table_cells(line)
        if not cells:
            continue
        status = next((status for cell in cells if (status := normalize_status(cell))), None)

        md_paths = row_md_paths(line)
        chapter_like = bool(CHAPTER_UNIT_RE.search(line))
        coverage_like = bool(md_paths or chapter_like)
        if coverage_like and not status:
            coverage_rows_without_status.append(line)
            continue

        if status in PARTIAL_STATUS_TERMS or contains_partial_status(line):
            partial_rows.append(line)
        if status == "complete" and not md_paths:
            complete_rows_without_md.append(line)
        if status in NON_CONTENT_STATUSES and chapter_like:
            non_content_chapter_rows.append(line)

        for md_path in md_paths:
            if not (project_dir / md_path).exists():
                missing_paths.append(md_path)

    if partial_rows:
        preview = "; ".join(row.strip() for row in partial_rows[:5])
        suffix = "; ..." if len(partial_rows) > 5 else ""
        warnings.append(
            "TOC/source-unit coverage table still contains incomplete/deferred/pending rows; "
            f"final strict validation requires complete, non-substantive, or synthesis coverage only: {preview}{suffix}"
        )
    if complete_rows_without_md:
        preview = "; ".join(row.strip() for row in complete_rows_without_md[:5])
        suffix = "; ..." if len(complete_rows_without_md) > 5 else ""
        warnings.append(
            "TOC/source-unit coverage table has complete rows without a concrete `md/...md` note path: "
            f"{preview}{suffix}"
        )
    if coverage_rows_without_status:
        preview = "; ".join(row.strip() for row in coverage_rows_without_status[:5])
        suffix = "; ..." if len(coverage_rows_without_status) > 5 else ""
        warnings.append(
            "TOC/source-unit coverage table has source-unit rows without an explicit final status: "
            f"{preview}{suffix}"
        )
    if non_content_chapter_rows:
        preview = "; ".join(row.strip() for row in non_content_chapter_rows[:5])
        suffix = "; ..." if len(non_content_chapter_rows) > 5 else ""
        warnings.append(
            "TOC/source-unit coverage table marks chapter-like rows as non-substantive or synthesis; "
            f"substantive chapters need complete md notes: {preview}{suffix}"
        )
    if missing_paths:
        unique_paths = sorted(set(missing_paths))
        preview = ", ".join(unique_paths[:10])
        suffix = "..." if len(unique_paths) > 10 else ""
        warnings.append(f"TOC/source-unit coverage table references missing md paths: {preview}{suffix}")
    return warnings


def main() -> int:
    args = parse_args()
    project_dir = args.project_dir.expanduser().resolve()
    if not project_dir.exists():
        print(f"ERROR: project directory not found: {project_dir}", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []

    txt_files = sorted((project_dir / "txt").rglob("*.txt")) if (project_dir / "txt").exists() else []
    md_files = sorted((project_dir / "md").rglob("*.md")) if (project_dir / "md").exists() else []
    pdf_files = sorted(
        path for path in project_dir.iterdir() if path.suffix.lower() == ".pdf" and (path.is_file() or path.is_symlink())
    )
    skill_dirs = find_skill_dirs(project_dir)
    reported_empty_pages, extraction_report_warnings = reported_short_or_empty_pages(project_dir)
    warnings.extend(extraction_report_warnings)

    if not pdf_files:
        errors.append("No PDF file found in the book project root.")
    else:
        broken_pdf_paths = [path for path in pdf_files if not path.exists()]
        if broken_pdf_paths:
            names = ", ".join(path.name for path in broken_pdf_paths)
            errors.append(f"PDF file path exists but target is missing: {names}")
    if len(pdf_files) > 1:
        names = ", ".join(path.name for path in pdf_files)
        warnings.append(f"Multiple PDF files found in the book project root; record the intended source PDF: {names}")
    if not txt_files:
        errors.append("No page-level TXT files found under txt/.")
    else:
        page_named_txt_files = [path for path in txt_files if PAGE_RE.search(path.name)]
        if not page_named_txt_files:
            errors.append("No page-named TXT files found under txt/; expected files like PDF第001页.txt.")
        non_page_named_txt_files = [path for path in txt_files if not PAGE_RE.search(path.name)]
        if non_page_named_txt_files:
            preview = ", ".join(str(path.relative_to(project_dir)) for path in non_page_named_txt_files[:10])
            suffix = "..." if len(non_page_named_txt_files) > 10 else ""
            warnings.append(f"TXT files not using PDF第NNN页.txt naming: {preview}{suffix}")
        empty_txt_files = [
            path
            for path in txt_files
            if not read_text(path).strip()
            and (PAGE_RE.search(path.name) is None or int(PAGE_RE.search(path.name).group(1)) not in reported_empty_pages)
        ]
        if empty_txt_files:
            preview = ", ".join(str(path.relative_to(project_dir)) for path in empty_txt_files[:10])
            suffix = "..." if len(empty_txt_files) > 10 else ""
            warnings.append(
                f"Empty page-level TXT files found but not listed in extraction-report.json: {preview}{suffix}"
            )
    if not md_files:
        errors.append("No Markdown source-unit note files found under md/.")
    if not skill_dirs:
        errors.append("No generated skill directory found as a direct child with SKILL.md.")
    elif len(skill_dirs) > 1:
        names = ", ".join(path.name for path in skill_dirs)
        warnings.append(
            "Multiple generated skill directories found as direct children; "
            f"record the intended generated skill or split the projects: {names}"
        )

    warnings.extend(check_page_coverage(txt_files, project_dir))
    warnings.extend(check_md_note_sources(md_files, txt_files, project_dir))
    warnings.extend(
        check_md_note_granularity(
            md_files,
            project_dir,
            args.max_md_source_pages,
            args.max_chapters_per_md_note,
        )
    )
    warnings.extend(check_md_completeness_audit(md_files, project_dir))
    warnings.extend(check_toc_coverage_table(md_files, skill_dirs, project_dir))

    for path in md_files:
        text = read_text(path)
        if not SOURCE_RE.search(text):
            warnings.append(f"{path.relative_to(project_dir)} has no source marker line like 来源：...")
        if "TODO" in text or "[TODO" in text or "UNMAPPED" in text:
            warnings.append(f"{path.relative_to(project_dir)} still contains TODO or UNMAPPED markers.")
        md_placeholder_hits = placeholder_hits(text)
        if md_placeholder_hits:
            warnings.append(
                f"{path.relative_to(project_dir)} still contains template placeholders; "
                "replace them with complete book-specific notes."
            )

    for skill_dir in skill_dirs:
        skill_errors, skill_warnings = check_skill(skill_dir, project_dir, args.max_skill_lines)
        errors.extend(skill_errors)
        warnings.extend(skill_warnings)

    print(f"Project: {project_dir}")
    print(f"PDF files: {len(pdf_files)}")
    print(f"TXT files: {len(txt_files)}")
    print(f"Markdown source-unit notes: {len(md_files)}")
    print(f"Generated skills: {len(skill_dirs)}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    if warnings and args.strict:
        print("\nERROR: strict mode treats warnings as failures.")
        return 1

    print("\nOK: book bundle structure passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
