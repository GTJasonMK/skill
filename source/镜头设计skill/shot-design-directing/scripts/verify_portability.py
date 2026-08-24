#!/usr/bin/env python3
"""Verify that shot-design-directing is complete and self-contained."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path


LINK_RE = re.compile(r"\]\(([^)]+)\)")
ABSOLUTE_LOCAL_RE = re.compile(r"(?:/home/|/Users/|[A-Za-z]:\\\\)")
PAGE_RE = re.compile(r"PDF第(\d{3})页\.txt$")
MANIFEST_REL = Path("references/source/evidence-manifest.sha256")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify bundled notes, page text, PDF, links, hashes, and path portability."
    )
    parser.add_argument(
        "skill_dir",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Skill directory; defaults to the parent of this script directory.",
    )
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="Regenerate the SHA-256 manifest before verification.",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_files(root: Path) -> list[Path]:
    source_root = root / "references" / "source"
    manifest = root / MANIFEST_REL
    return sorted(
        path
        for path in source_root.rglob("*")
        if path.is_file() and path != manifest
    )


def write_manifest(root: Path) -> None:
    manifest = root / MANIFEST_REL
    manifest.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"{sha256(path)}  {path.relative_to(root).as_posix()}"
        for path in source_files(root)
    ]
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_manifest(root: Path, errors: list[str]) -> int:
    manifest = root / MANIFEST_REL
    if not manifest.is_file():
        errors.append(f"missing manifest: {MANIFEST_REL.as_posix()}")
        return 0

    expected: dict[Path, str] = {}
    for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            digest, rel = line.split("  ", 1)
        except ValueError:
            errors.append(f"malformed manifest line {line_no}")
            continue
        path = Path(rel)
        if path.is_absolute() or ".." in path.parts:
            errors.append(f"unsafe manifest path on line {line_no}: {rel}")
            continue
        expected[path] = digest

    actual = {path.relative_to(root) for path in source_files(root)}
    missing_entries = actual - set(expected)
    extra_entries = set(expected) - actual
    for path in sorted(missing_entries):
        errors.append(f"source file missing from manifest: {path.as_posix()}")
    for path in sorted(extra_entries):
        errors.append(f"manifest points to missing source file: {path.as_posix()}")

    checked = 0
    for rel, digest in expected.items():
        path = root / rel
        if not path.is_file():
            continue
        checked += 1
        actual_digest = sha256(path)
        if actual_digest != digest:
            errors.append(f"hash mismatch: {rel.as_posix()}")
    return checked


def verify_links(root: Path, errors: list[str]) -> int:
    checked = 0
    resolved_root = root.resolve()
    for markdown in sorted(root.rglob("*.md")):
        text = markdown.read_text(encoding="utf-8")
        if ABSOLUTE_LOCAL_RE.search(text):
            errors.append(f"machine-specific absolute path: {markdown.relative_to(root)}")
        for raw_target in LINK_RE.findall(text):
            target = raw_target.strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            target = target.split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            checked += 1
            resolved = (markdown.parent / target).resolve()
            try:
                resolved.relative_to(resolved_root)
            except ValueError:
                errors.append(
                    f"link escapes skill root: {markdown.relative_to(root)} -> {raw_target}"
                )
                continue
            if not resolved.exists():
                errors.append(
                    f"broken link: {markdown.relative_to(root)} -> {raw_target}"
                )
    return checked


def verify_structure(root: Path, errors: list[str]) -> tuple[int, int]:
    if not (root / "SKILL.md").is_file():
        errors.append("missing SKILL.md")

    symlinks = [path for path in root.rglob("*") if path.is_symlink()]
    for path in symlinks:
        errors.append(f"bundled path is a symlink: {path.relative_to(root)}")

    notes = sorted((root / "references" / "source" / "notes").glob("*.md"))
    if len(notes) != 41:
        errors.append(f"expected 41 bundled notes/indexes, found {len(notes)}")

    pages = sorted(
        (root / "references" / "source" / "pages" / "by-chapter").rglob(
            "PDF第*.txt"
        )
    )
    page_numbers = [
        int(match.group(1))
        for path in pages
        if (match := PAGE_RE.search(path.name)) is not None
    ]
    if len(pages) != 393:
        errors.append(f"expected 393 bundled page files, found {len(pages)}")
    if page_numbers != list(range(1, 394)):
        errors.append("bundled PDF page numbers are not exactly 001-393")

    pdf = root / "references" / "source" / "book.pdf"
    if not pdf.is_file() or pdf.stat().st_size == 0:
        errors.append("missing or empty bundled PDF: references/source/book.pdf")

    coverage = root / "references" / "core" / "source-coverage-map.md"
    if coverage.is_file():
        text = coverage.read_text(encoding="utf-8")
        if text.count("[TXT](../source/pages/by-chapter/") != 39:
            errors.append("source coverage does not contain 39 internal TXT links")
        if text.count("[Markdown](../source/notes/") != 39:
            errors.append("source coverage does not contain 39 internal note links")
    else:
        errors.append("missing source coverage map")

    return len(notes), len(pages)


def main() -> int:
    args = parse_args()
    root = args.skill_dir.expanduser().resolve()
    if args.write_manifest:
        write_manifest(root)

    errors: list[str] = []
    notes, pages = verify_structure(root, errors)
    links = verify_links(root, errors)
    hashes = verify_manifest(root, errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAILED: {len(errors)} portability error(s).", file=sys.stderr)
        return 1

    print(
        "OK: portable skill passed "
        f"({notes} notes/indexes, {pages} pages, {hashes} hashes, {links} links)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
