#!/usr/bin/env python3
"""扫描版 PDF 全量 OCR 提取为 txt。"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import fitz
from rapidocr_onnxruntime import RapidOCR

PDF_PATH = Path("电影镜头设计-从构思到银幕-第2版.pdf")
OUT_TXT = Path("txt/电影镜头设计-从构思到银幕-第2版.txt")
PROGRESS = Path("txt/.ocr_progress.json")
ZOOM = 2.0  # 扫描页约 95dpi，2x 提升识别


def load_progress() -> dict:
    if PROGRESS.exists():
        return json.loads(PROGRESS.read_text(encoding="utf-8"))
    return {"done": {}, "started_at": time.time()}


def save_progress(prog: dict) -> None:
    PROGRESS.write_text(json.dumps(prog, ensure_ascii=False), encoding="utf-8")


def join_page_text(result) -> str:
    if not result:
        return ""
    # RapidOCR: [box, text, score]
    return "\n".join(line[1] for line in result if line and line[1])


def rebuild_txt(prog: dict, total: int) -> None:
    parts = []
    for i in range(total):
        key = str(i)
        if key not in prog["done"]:
            continue
        text = prog["done"][key]
        parts.append(f"\n\n===== 第 {i + 1} 页 =====\n\n{text}")
    OUT_TXT.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "电影镜头设计：从构思到银幕（插图第2版）\n"
        "OCR 提取文本（扫描版 PDF，可能存在识别误差）\n"
        f"总页数: {total}\n"
        f"已完成: {len(prog['done'])}\n"
        + "=" * 60
    )
    OUT_TXT.write_text(header + "".join(parts) + "\n", encoding="utf-8")


def main() -> int:
    if not PDF_PATH.exists():
        print(f"找不到 PDF: {PDF_PATH}", file=sys.stderr)
        return 1

    print("加载 OCR 引擎...")
    engine = RapidOCR()
    doc = fitz.open(PDF_PATH)
    total = doc.page_count
    prog = load_progress()
    mat = fitz.Matrix(ZOOM, ZOOM)

    print(f"总页数: {total}, 已完成: {len(prog['done'])}")
    t_start = time.time()
    done_this_run = 0

    for i in range(total):
        key = str(i)
        if key in prog["done"]:
            continue

        page = doc[i]
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("png")
        t0 = time.time()
        result, _ = engine(img_bytes)
        text = join_page_text(result)
        dt = time.time() - t0

        prog["done"][key] = text
        done_this_run += 1

        # 每页落盘进度，每 5 页重写完整 txt
        if done_this_run % 1 == 0:
            save_progress(prog)
        if done_this_run % 5 == 0 or i + 1 == total:
            rebuild_txt(prog, total)

        finished = len(prog["done"])
        elapsed = time.time() - t_start
        rate = done_this_run / elapsed if elapsed > 0 else 0
        remain = (total - finished) / rate if rate > 0 else 0
        print(
            f"[{finished}/{total}] 第{i+1}页 "
            f"{dt:.1f}s chars={len(text)} "
            f"ETA={remain/60:.1f}min",
            flush=True,
        )

    rebuild_txt(prog, total)
    save_progress(prog)
    print(f"完成: {OUT_TXT} ({OUT_TXT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
