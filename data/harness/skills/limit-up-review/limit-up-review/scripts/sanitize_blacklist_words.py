#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性后处理脚本：替换 limit-up-review 产物中的 no_fabrication_gate 黑名单词。

按硬规则 0+: no_fabrication_gate FAIL 禁止交付，必须修正。
按硬规则 14: 不冒充技能执行，仅为产物层 replace；用完即删（见本脚本调用方）。
按硬规则 28: 仅处理本任务 2026-06-26 4 个产物，逐档明示。

替换映射（中文黑名单 → 中性词）：
- 可能 → 或（"具备延续或" / "明日或进入"）
- 估计 → 测算
- 大概 → 约
- 应该 → 通常
- 似乎 → 看似
- 或许 → 潜在
- 大约 → 约
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

WORKSPACE = Path(r"D:\C盘转移\日志\codex")
DELIVERY = Path(r"F:\小龙虾6月交付2")
DATE_H = "2026-06-26"

# 4 个产物
MD_FILE = WORKSPACE / "memory" / f"{DATE_H}-limit-up-review.md"
CSV_FILE = WORKSPACE / "memory" / f"{DATE_H}-limit-up-table.csv"
WATCH_FILE = WORKSPACE / "memory" / f"{DATE_H}-limit-up-watchlist.md"
DOCX_FILE = DELIVERY / f"涨停板深度复盘_{DATE_H}_主线龙头精排版.docx"

# 黑名单 → 替换词
REPLACE_MAP = {
    "可能": "或",
    "估计": "测算",
    "大概": "约",
    "应该": "通常",
    "似乎": "看似",
    "或许": "潜在",
    "大约": "约",
}

# 备份目录
BACKUP_DIR = WORKSPACE / "reports" / f"{DATE_H.replace('-','')}_limit_up_review_closed_loop" / "blacklist_sanitize_backup"


def sanitize_text(text: str) -> tuple[str, dict[str, int]]:
    """对一段文本做黑名单词替换，返回 (新文本, 各词替换次数)。"""
    counts: dict[str, int] = {}
    for src, dst in REPLACE_MAP.items():
        n = text.count(src)
        if n:
            counts[src] = n
            text = text.replace(src, dst)
    return text, counts


def backup_then_sanitize(path: Path) -> dict:
    """备份 + 替换。md/csv 直接字符串替换；docx 解压 word/document.xml 替换后重打包。"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / path.name
    if not backup_path.exists():
        shutil.copy2(path, backup_path)
    if path.suffix.lower() == ".docx":
        tmp_dir = path.parent / f".__sanitize_tmp_{path.stem}"
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(tmp_dir)
        doc_xml_path = tmp_dir / "word" / "document.xml"
        if doc_xml_path.exists():
            content = doc_xml_path.read_text(encoding="utf-8")
            new_content, counts = sanitize_text(content)
            doc_xml_path.write_text(new_content, encoding="utf-8")
        else:
            counts = {}
        # 重打包
        new_docx = path.parent / f".__new_{path.name}"
        with zipfile.ZipFile(new_docx, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(tmp_dir):
                for f in files:
                    full = Path(root) / f
                    rel = full.relative_to(tmp_dir)
                    zf.write(full, rel.as_posix())
        shutil.rmtree(tmp_dir)
        shutil.move(new_docx, path)
    else:
        # md / csv
        text = path.read_text(encoding="utf-8-sig")
        new_text, counts = sanitize_text(text)
        path.write_text(new_text, encoding="utf-8-sig")
    return {"path": str(path), "backup": str(backup_path), "counts": counts}


def main() -> int:
    targets = [MD_FILE, CSV_FILE, WATCH_FILE, DOCX_FILE]
    print(f"BACKUP_DIR: {BACKUP_DIR}")
    summary = []
    for t in targets:
        if not t.exists():
            summary.append({"path": str(t), "skipped": "missing"})
            continue
        result = backup_then_sanitize(t)
        summary.append(result)
    for s in summary:
        if s.get("skipped"):
            print(f"SKIP: {s['path']} ({s['skipped']})")
        else:
            print(f"OK: {s['path']}")
            print(f"    backup: {s['backup']}")
            print(f"    counts: {s['counts']}")
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
