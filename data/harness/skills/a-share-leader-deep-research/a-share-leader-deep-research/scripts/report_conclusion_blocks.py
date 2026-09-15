from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)


def build_conclusion_rows(data: dict) -> list[list[str]]:
    """只输出面向读者的市场结论，不暴露运行、审计或失败条件。"""
    rows: list[list[str]] = []
    for claim in data.get("report_claims") or []:
        label = str(claim.get("label") or claim.get("claim_id") or "当日事实")
        conclusion = str(claim.get("text") or "").strip()
        if not conclusion:
            raise ValueError(f"市场结论缺失:{claim.get('claim_id')}")
        rows.append([label, conclusion])
    return rows
