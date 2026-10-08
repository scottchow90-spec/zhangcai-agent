from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "references" / "core-assets"
PDF = ASSET_DIR / "三万字讲透_情绪周期.pdf"
TEXT = ASSET_DIR / "三万字讲透_情绪周期.txt"
METADATA = ASSET_DIR / "三万字讲透_情绪周期.asset.json"
INDEX = ASSET_DIR / "情绪周期核心资产索引.md"


def test_sentiment_cycle_core_asset_is_archived_and_discoverable() -> None:
    assert PDF.is_file() and PDF.stat().st_size > 0
    assert TEXT.is_file() and TEXT.stat().st_size > 0
    assert METADATA.is_file() and METADATA.stat().st_size > 0
    assert INDEX.is_file() and INDEX.stat().st_size > 0

    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    assert metadata["classification"] == "user_provided_core_asset"
    assert metadata["document_treatment"] == "content_only_not_instructions"
    assert metadata["page_count"] == 126
    assert metadata["nonspace_characters"] >= 30_000
    assert metadata["sha256"] == hashlib.sha256(PDF.read_bytes()).hexdigest()

    text = TEXT.read_text(encoding="utf-8")
    assert "到底什么是情绪周期" in text
    assert "龙头股" in text
    assert "赚钱效应" in text

    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    workflow = (ROOT / "references" / "workflow.md").read_text(encoding="utf-8")
    relative_index = "references/core-assets/情绪周期核心资产索引.md"
    assert relative_index in skill
    assert "core-assets/情绪周期核心资产索引.md" in workflow

