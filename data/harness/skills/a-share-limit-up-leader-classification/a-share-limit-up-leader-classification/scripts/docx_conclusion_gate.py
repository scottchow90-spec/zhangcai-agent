from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{" + W_NS + "}"
TEMPLATE_TERMS = (
    "默认结论",
    "固定措辞",
    "兜底判断",
    "需要结合可用历史基线确认其相对位置",
    "这些字段构成次日风险分支的优先观察依据",
)
GENERIC_PATTERNS = (
    re.compile(r"重要方向"),
    re.compile(r"(?:重点)?看(?:成交额|涨停(?:扩散)?|扩散|承接|资金|情绪|首板|连板)"),
    re.compile(r"有望|后市可期|值得关注|通常|一般而言"),
)


def read_docx_paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    paragraphs: list[str] = []
    for paragraph in root.iter(W + "p"):
        text = "".join(node.text or "" for node in paragraph.iter(W + "t")).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def audit_paragraphs(paragraphs: list[str]) -> dict:
    body = "\n".join(paragraphs)
    blocks: list[str] = []
    if "__" in body:
        blocks.append("模板占位符未清理")
    for term in TEMPLATE_TERMS:
        if term in body:
            blocks.append(f"模板污染：{term}")
    for pattern in GENERIC_PATTERNS:
        match = pattern.search(body)
        if match:
            blocks.append(f"泛化判断：{match.group(0)}")

    records: list[dict] = []
    for index, paragraph in enumerate(paragraphs, start=1):
        if "结论：" not in paragraph:
            continue
        conclusion = paragraph.split("结论：", 1)[1].split("依据：", 1)[0].strip()
        evidence = paragraph.split("依据：", 1)[1].split("反证：", 1)[0].strip() if "依据：" in paragraph else ""
        counterevidence = paragraph.split("反证：", 1)[1].strip() if "反证：" in paragraph else ""
        records.append({"paragraph": index, "conclusion": conclusion, "evidence": evidence, "counterevidence": counterevidence})
        if not re.search(r"\d", conclusion):
            blocks.append(f"第{index}段结论缺少数字事实")
        if not evidence:
            blocks.append(f"第{index}段缺少依据")
        elif not re.search(r"\d", evidence):
            blocks.append(f"第{index}段依据缺少数字事实")
        if not counterevidence:
            blocks.append(f"第{index}段缺少反证")
    if not records:
        blocks.append("缺少同段的结论、依据、反证数据块")
    return {
        "status": "PASS" if not blocks else "BLOCKED",
        "conclusion_count": len(records),
        "conclusions": records,
        "blocks": blocks,
    }


def audit_docx(path: Path) -> dict:
    result = audit_paragraphs(read_docx_paragraphs(path))
    result["path"] = str(path.resolve())
    result["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result
