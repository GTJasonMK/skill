#!/usr/bin/env python3
"""Expose a generated book skill through the Codex skill discovery directory."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from check_book_bundle import (
    FRONTMATTER_KEY_RE,
    FRONTMATTER_RE,
    SKILL_NAME_RE,
    check_skill,
    parse_frontmatter_value,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Symlink or copy a generated skill directory into $CODEX_HOME/skills or ~/.codex/skills."
    )
    parser.add_argument("skill_dir", type=Path, help="Generated skill directory containing SKILL.md.")
    parser.add_argument(
        "--skills-dir",
        type=Path,
        help="Destination skills directory. Default: $CODEX_HOME/skills or ~/.codex/skills.",
    )
    parser.add_argument(
        "--mode",
        choices=("symlink", "copy"),
        default="symlink",
        help="Install mode. Symlink avoids drift; copy is portable but must be refreshed.",
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing symlink or directory at the destination.")
    return parser.parse_args()


def default_skills_dir() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def remove_existing(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def validate_skill_dir(skill_dir: Path) -> None:
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    frontmatter = FRONTMATTER_RE.search(text)
    if not frontmatter:
        raise ValueError(f"{skill_md} is missing YAML frontmatter")

    body = frontmatter.group("body")
    extra_keys = sorted({key for key in FRONTMATTER_KEY_RE.findall(body) if key not in {"name", "description"}})
    if extra_keys:
        raise ValueError(f"{skill_md} frontmatter has unsupported fields: {', '.join(extra_keys)}")

    skill_name = parse_frontmatter_value(body, "name")
    if not skill_name or re.search(r"\s", skill_name):
        raise ValueError(f"{skill_md} frontmatter name could not be parsed")
    description = parse_frontmatter_value(body, "description")
    if not description:
        raise ValueError(f"{skill_md} frontmatter description could not be parsed")

    if not SKILL_NAME_RE.fullmatch(skill_name):
        raise ValueError(f"{skill_md} frontmatter name `{skill_name}` is not valid lowercase hyphen-case")
    if skill_name != skill_dir.name:
        raise ValueError(
            f"{skill_md} frontmatter name `{skill_name}` does not match folder `{skill_dir.name}`"
        )

    skill_errors, skill_warnings = check_skill(skill_dir, skill_dir.parent, max_lines=260)
    issues = [*skill_errors, *skill_warnings]
    if issues:
        details = "; ".join(issues[:5])
        suffix = "; ..." if len(issues) > 5 else ""
        raise ValueError(f"{skill_dir} is not ready to install: {details}{suffix}")

    validate_parent_book_bundle(skill_dir)


def validate_parent_book_bundle(skill_dir: Path) -> None:
    project_dir = skill_dir.parent
    if not (project_dir / "txt").exists() or not (project_dir / "md").exists():
        raise ValueError(
            f"{skill_dir} is not inside a complete book project with sibling txt/ and md/ directories"
        )

    checker = Path(__file__).with_name("check_book_bundle.py")
    result = subprocess.run(
        [sys.executable, str(checker), str(project_dir), "--strict"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        preview = "; ".join(lines[:8])
        suffix = "; ..." if len(lines) > 8 else ""
        raise ValueError(
            f"parent book project failed strict validation and cannot be installed: {preview}{suffix}"
        )


def main() -> int:
    args = parse_args()
    skill_dir = args.skill_dir.expanduser().resolve()
    if not skill_dir.exists():
        print(f"ERROR: skill directory not found: {skill_dir}", file=sys.stderr)
        return 2
    if not (skill_dir / "SKILL.md").exists():
        print(f"ERROR: {skill_dir} does not contain SKILL.md", file=sys.stderr)
        return 2
    try:
        validate_skill_dir(skill_dir)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    skills_dir = args.skills_dir.expanduser().resolve() if args.skills_dir else default_skills_dir().resolve()
    skills_dir.mkdir(parents=True, exist_ok=True)
    destination = skills_dir / skill_dir.name

    if destination.exists() or destination.is_symlink():
        if not args.force:
            print(f"ERROR: destination already exists: {destination}. Use --force to replace.", file=sys.stderr)
            return 1
        remove_existing(destination)

    if args.mode == "symlink":
        os.symlink(skill_dir, destination)
    else:
        shutil.copytree(skill_dir, destination)

    print(f"OK: {args.mode} installed {skill_dir} -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
