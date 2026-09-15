from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
EXPECTED_TOP1_SKILLS = (
    "stock-hard-gate",
    "tdx-local-hub",
    "golden-ignition",
    "feilong-strategy",
    "youzi-capital-monitoring",
    "big-bull-analysis-scoring-system",
)


def _load_validator():
    sys.path.insert(0, str(SCRIPTS))
    script = SCRIPTS / "validate_top1_fixed_skills.py"
    spec = importlib.util.spec_from_file_location("top1_fixed_skill_validator", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixed_skill_child_receives_canonical_authorization(monkeypatch, tmp_path: Path) -> None:
    module = _load_validator()
    captured = {}

    def fake_run_process_tree(args, **kwargs):
        captured["environment"] = kwargs.get("env")
        return subprocess.CompletedProcess(args, 0, "{}", "")

    monkeypatch.setattr(module, "run_process_tree", fake_run_process_tree)
    module.run_skill("tdx-local-hub", ["run"], tmp_path)

    assert captured["environment"]["ONESTOCK_STOCK_CANONICAL_CHILD"] == "1"


def test_fixed_skill_sequence_is_exactly_six_with_hard_gate_first() -> None:
    module = _load_validator()

    assert module.EXPECTED_TOP1_SKILLS == EXPECTED_TOP1_SKILLS
    assert len(module.EXPECTED_TOP1_SKILLS) == 6
    assert module.EXPECTED_TOP1_SKILLS[0] == "stock-hard-gate"


@pytest.mark.parametrize("missing_skill", EXPECTED_TOP1_SKILLS)
def test_fixed_skill_sequence_rejects_any_missing_dependency(missing_skill: str) -> None:
    module = _load_validator()
    commands = [
        (skill, ["run"])
        for skill in EXPECTED_TOP1_SKILLS
        if skill != missing_skill
    ]

    with pytest.raises(RuntimeError, match="fixed skill sequence mismatch"):
        module.validate_fixed_skill_commands(commands)


def test_fixed_skill_sequence_rejects_reordered_hard_gate() -> None:
    module = _load_validator()
    commands = [
        (skill, ["run"])
        for skill in (*EXPECTED_TOP1_SKILLS[1:], EXPECTED_TOP1_SKILLS[0])
    ]

    with pytest.raises(RuntimeError, match="fixed skill sequence mismatch"):
        module.validate_fixed_skill_commands(commands)


def test_business_artifact_path_reads_big_bull_report_from_receipt(tmp_path: Path) -> None:
    module = _load_validator()
    report = tmp_path / "analysis_report.txt"
    run = {
        "json_objects": [
            {
                "schema": "BIG_BULL_ANALYSIS_SCORING_RESULT_V1",
                "status": "CLEAN_PASS",
                "artifacts": {"analysis_report": {"path": str(report)}},
            }
        ]
    }

    assert module.business_artifact_path(run, "analysis_report") == report


def test_generation_paths_bind_the_big_bull_analysis_report(tmp_path: Path) -> None:
    sys.path.insert(0, str(SCRIPTS))
    from runtime_utils import build_generation_paths

    paths = build_generation_paths(tmp_path, "run-1", 1)

    assert paths.top1_bigbull == (
        tmp_path
        / "generations"
        / "run-1"
        / "attempt-1"
        / "top1"
        / "top1_big_bull"
        / "analysis_report.txt"
    )
