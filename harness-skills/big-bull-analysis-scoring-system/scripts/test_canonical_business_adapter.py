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

import pytest


MODULE_PATH = Path(__file__).with_name("canonical_business_adapter.py")
SPEC = importlib.util.spec_from_file_location("canonical_business_adapter", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_rejected_prediction_is_exposed_as_business_outcome(tmp_path: Path) -> None:
    write_json(
        tmp_path / "三公式综合评分回测证据.json",
        {
            "status": "PREDICTIVE_REJECTED",
            "predictive_validation": {
                "status": "PREDICTIVE_REJECTED",
                "failed_gates": ["test_ic_newey_west_ci_lower_positive"],
            },
            "validation_gates": {
                "status": "BLOCKED",
                "failed": ["test_ic_newey_west_ci_lower_positive"],
            },
        },
    )
    write_json(
        tmp_path / "三公式综合评分正式模型.json",
        {
            "status": "PREDICTIVE_REJECTED",
            "predictive_validation": {
                "status": "PREDICTIVE_REJECTED",
                "oos_row_count": 10,
                "oos_date_count": 5,
            },
            "model": None,
        },
    )
    (tmp_path / "三公式综合评分样本外明细.csv").write_text(
        "date,symbol\n20260101,600000.SH\n", encoding="utf-8"
    )
    (tmp_path / "三公式综合评分样本外分期.csv").write_text(
        "date,mean_ic\n20260101,0.01\n", encoding="utf-8"
    )

    outcome = MODULE.inspect_composite_scientific_outcome(tmp_path)

    assert outcome == {
        "status": "PREDICTIVE_REJECTED",
        "model_usable": False,
        "oos_rows_nonempty": True,
        "oos_dates_nonempty": True,
        "failed_gates": ["test_ic_newey_west_ci_lower_positive"],
    }


def test_rejected_prediction_cannot_retain_a_model(tmp_path: Path) -> None:
    write_json(
        tmp_path / "三公式综合评分回测证据.json",
        {
            "status": "PREDICTIVE_REJECTED",
            "predictive_validation": {"status": "PREDICTIVE_REJECTED"},
            "validation_gates": {"status": "BLOCKED", "failed": ["failed"]},
        },
    )
    write_json(
        tmp_path / "三公式综合评分正式模型.json",
        {
            "status": "PREDICTIVE_REJECTED",
            "predictive_validation": {"status": "PREDICTIVE_REJECTED"},
            "model": {"must_not": "survive"},
        },
    )
    (tmp_path / "三公式综合评分样本外明细.csv").write_text(
        "date\n20260101\n", encoding="utf-8"
    )
    (tmp_path / "三公式综合评分样本外分期.csv").write_text(
        "date\n20260101\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="预测拒绝结果仍携带可用模型"):
        MODULE.inspect_composite_scientific_outcome(tmp_path)


def test_only_thirty_item_contribution_artifact_is_bound_by_business_adapter() -> None:
    assert "三公式综合评分30项贡献明细.csv" in MODULE.DELIVERABLE_NAMES
    assert "三公式综合评分8K海报-preview-1920x1080.png" in MODULE.DELIVERABLE_NAMES
    assert all("31项" not in name for name in MODULE.DELIVERABLE_NAMES)
    assert all("sentiment" not in name.lower() for name in MODULE.DELIVERABLE_NAMES)
