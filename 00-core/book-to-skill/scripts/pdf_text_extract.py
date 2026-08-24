#!/usr/bin/env python3
"""Extract PDF pages into stable per-page text files.

The script prefers Python ``pypdf`` when available and can fall back to the
``pdftotext`` CLI. It writes ``PDF第001页.txt`` style files plus an extraction
report so downstream ``md/`` source-unit notes can keep source traceability.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class ExtractedPage:
    page_number: int
    text: str


def normalize_text(text: str) -> str:
    lines = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n").split("\n"):
        lines.append(line.rstrip())
    return "\n".join(lines).strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a PDF into page-level TXT files named PDF第001页.txt."
    )
    parser.add_argument("pdf", type=Path, help="Input PDF path.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Output directory for page text files.",
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "pypdf", "pdftotext"),
        default="auto",
        help="Extraction backend. Default: auto.",
    )
    parser.add_argument("--start-page", type=int, default=1, help="First PDF page to extract, 1-indexed.")
    parser.add_argument("--end-page", type=int, help="Last PDF page to extract, inclusive.")
    parser.add_argument(
        "--min-chars-warning",
        type=int,
        default=20,
        help="Warn when an extracted page has fewer non-space characters.",
    )
    parser.add_argument(
        "--combined-out",
        type=Path,
        help="Optional path for a combined text file containing all extracted pages.",
    )
    return parser.parse_args()


def extract_with_pypdf(pdf: Path, page_numbers: Iterable[int]) -> list[ExtractedPage]:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise RuntimeError("pypdf is not installed. Install it or use --backend pdftotext.") from exc

    reader = PdfReader(str(pdf))
    total_pages = len(reader.pages)
    pages: list[ExtractedPage] = []
    for page_number in page_numbers:
        if page_number < 1 or page_number > total_pages:
            raise ValueError(f"Page {page_number} is outside PDF range 1..{total_pages}.")
        text = reader.pages[page_number - 1].extract_text() or ""
        pages.append(ExtractedPage(page_number=page_number, text=normalize_text(text)))
    return pages


def extract_with_pdftotext(pdf: Path, page_numbers: Iterable[int]) -> list[ExtractedPage]:
    if shutil.which("pdftotext") is None:
        raise RuntimeError("pdftotext CLI was not found on PATH.")

    pages: list[ExtractedPage] = []
    for page_number in page_numbers:
        cmd = [
            "pdftotext",
            "-layout",
            "-enc",
            "UTF-8",
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            str(pdf),
            "-",
        ]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            stderr = proc.stderr.strip()
            raise RuntimeError(f"pdftotext failed on page {page_number}: {stderr}")
        pages.append(ExtractedPage(page_number=page_number, text=normalize_text(proc.stdout)))
    return pages


def infer_total_pages_with_pypdf(pdf: Path) -> int | None:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        return None
    return len(PdfReader(str(pdf)).pages)


def infer_total_pages_with_pdfinfo(pdf: Path) -> int | None:
    if shutil.which("pdfinfo") is None:
        return None
    proc = subprocess.run(["pdfinfo", str(pdf)], check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    for line in proc.stdout.splitlines():
        if line.startswith("Pages:"):
            value = line.split(":", 1)[1].strip()
            if value.isdigit():
                return int(value)
    return None


def infer_total_pages(pdf: Path, backend: str) -> int:
    total = infer_total_pages_with_pypdf(pdf)
    if total is None and backend in {"auto", "pdftotext"}:
        total = infer_total_pages_with_pdfinfo(pdf)
    if total is None:
        raise RuntimeError("Could not infer PDF page count. Install pypdf or pdfinfo.")
    return total


def choose_backend(requested: str) -> str:
    if requested != "auto":
        return requested
    try:
        import pypdf  # noqa: F401

        return "pypdf"
    except ImportError:
        if shutil.which("pdftotext"):
            return "pdftotext"
    raise RuntimeError("No extraction backend available. Install pypdf or pdftotext.")


def write_pages(pages: list[ExtractedPage], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for page in pages:
        page_path = out_dir / f"PDF第{page.page_number:03d}页.txt"
        page_path.write_text(page.text, encoding="utf-8")


def write_combined(pages: list[ExtractedPage], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    chunks = []
    for page in pages:
        chunks.append(f"\n\n===== PDF第{page.page_number:03d}页 =====\n\n{page.text.rstrip()}\n")
    output.write_text("".join(chunks).lstrip(), encoding="utf-8")


def main() -> int:
    args = parse_args()
    pdf = args.pdf.expanduser().resolve()
    if not pdf.exists():
        print(f"ERROR: PDF not found: {pdf}", file=sys.stderr)
        return 2
    if args.start_page < 1:
        print("ERROR: --start-page must be >= 1", file=sys.stderr)
        return 2

    backend = choose_backend(args.backend)
    total_pages = infer_total_pages(pdf, backend)
    end_page = args.end_page or total_pages
    if end_page < args.start_page:
        print("ERROR: --end-page must be >= --start-page", file=sys.stderr)
        return 2
    if end_page > total_pages:
        print(f"ERROR: --end-page {end_page} exceeds PDF page count {total_pages}", file=sys.stderr)
        return 2

    page_numbers = list(range(args.start_page, end_page + 1))
    if backend == "pypdf":
        pages = extract_with_pypdf(pdf, page_numbers)
    else:
        pages = extract_with_pdftotext(pdf, page_numbers)

    out_dir = args.out_dir.expanduser().resolve()
    write_pages(pages, out_dir)
    if args.combined_out:
        write_combined(pages, args.combined_out.expanduser().resolve())

    short_pages = [
        page.page_number
        for page in pages
        if len("".join(page.text.split())) < args.min_chars_warning
    ]
    report = {
        "pdf": str(pdf),
        "backend": backend,
        "total_pdf_pages": total_pages,
        "start_page": args.start_page,
        "end_page": end_page,
        "pages_written": len(pages),
        "out_dir": str(out_dir),
        "short_or_empty_pages": short_pages,
    }
    report_path = out_dir / "extraction-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"OK: wrote {len(pages)} page files to {out_dir}")
    if short_pages:
        print("WARN: short or empty pages: " + ", ".join(str(p) for p in short_pages))
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
