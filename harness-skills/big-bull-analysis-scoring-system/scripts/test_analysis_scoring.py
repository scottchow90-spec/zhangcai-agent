from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("analysis_scoring.py")
SPEC = importlib.util.spec_from_file_location("analysis_scoring", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_research_composite_entry_always_enables_structural_mode(
    monkeypatch,
    tmp_path,
) -> None:
    captured = {}

    def fake_run(output_dir, args, timeout=900):
        captured["output_dir"] = output_dir
        captured["args"] = args
        captured["timeout"] = timeout
        return {"status": "CLEAN_PASS"}

    monkeypatch.setattr(MODULE, "run_composite_scoring", fake_run)

    result = MODULE.run_research_composite_scoring(
        tmp_path,
        ["--board-name", "黄金点火", "--board-code", "HJDH"],
        timeout=17,
    )

    assert result["status"] == "CLEAN_PASS"
    assert captured["args"] == [
        "--research-structural",
        "--board-name",
        "黄金点火",
        "--board-code",
        "HJDH",
    ]
    assert captured["timeout"] == 17


def test_skill_documents_define_exact_thirty_item_research_composite() -> None:
    documents = "\n".join(
        [
            (MODULE.ROOT / "SKILL.md").read_text(encoding="utf-8"),
            (MODULE.ROOT / "references" / "workflow.md").read_text(
                encoding="utf-8"
            ),
            (
                MODULE.ROOT
                / "references"
                / "three_formula_composite_scoring.md"
            ).read_text(encoding="utf-8"),
        ]
    )

    assert "score-research-composite" in documents
    assert "未来5至10个交易日" in documents
    assert "RULE_BASED_STRUCTURAL_FORECAST" in documents
    assert "固定30项" in documents
    assert "大牛线40%" in documents
    assert "飞龙在天35%" in documents
    assert "庄家资金监控25%" in documents
    assert "forecast_is_probability=false" in documents
