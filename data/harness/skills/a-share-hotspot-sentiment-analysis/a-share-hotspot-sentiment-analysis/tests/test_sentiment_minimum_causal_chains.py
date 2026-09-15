from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import json
from pathlib import Path


SKILL_ROOT = Path(r"D:\C盘转移\日志\codex\skills\a-share-hotspot-sentiment-analysis")
SCRIPT = (
    SKILL_ROOT
    / "components"
    / "a-share-sentiment-workflow"
    / "scripts"
    / "a-share-sentiment-workflow.py"
)
ZERO_CHAIN_FIXTURE = (
    SKILL_ROOT
    / "tests"
    / "fixtures"
    / "zero-causal-chain-run"
)


def load_workflow_module():
    spec = importlib.util.spec_from_file_location("a_share_sentiment_workflow", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_business_contract_requires_two_causal_chains():
    workflow = load_workflow_module()
    assert workflow.MIN_REPORT_CAUSAL_CHAINS == 2


def test_zero_chain_two_page_report_is_rejected():
    workflow = load_workflow_module()
    report = ZERO_CHAIN_FIXTURE / "A股三日舆情解读结果_Codex自动生成.docx"
    audit = workflow.delivery_report_audit(
        report,
        artifact_dir=ZERO_CHAIN_FIXTURE,
        write=False,
    )
    assert audit["ok"] is False
    assert "insufficient_industry_causal_clusters=0" in audit["reasons"]

    clusters = json.loads(
        (ZERO_CHAIN_FIXTURE / "a_share_sentiment_clusters.json").read_text(
            encoding="utf-8"
        )
    )
    assert clusters == []
