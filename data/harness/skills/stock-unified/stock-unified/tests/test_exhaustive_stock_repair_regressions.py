from __future__ import annotations

import json
import importlib.util
import os
import sqlite3
import sys
from datetime import date
from pathlib import Path

import pandas as pd


STOCK_UNIFIED = Path(__file__).resolve().parents[1]
SKILLS = STOCK_UNIFIED.parent


def load_module(relative: str, name: str):
    path = SKILLS / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_bottom_fishing_contract_does_not_require_unproduced_forecast_status() -> None:
    payload = json.loads(
        (STOCK_UNIFIED / "references" / "stock_execution_contracts.json").read_text(
            encoding="utf-8"
        )
    )
    contract = next(
        row for row in payload["contracts"]
        if row["skill_id"] == "a-share-bottom-fishing"
    )
    values = [
        value
        for assertion in contract["semantic_assertions"]
        for value in assertion.get("values", [])
    ]
    assert not any("forecast_status" in value for value in values)


def test_tq_dependency_manifest_covers_all_known_canonical_consumers() -> None:
    payload = json.loads(
        (STOCK_UNIFIED / "references" / "stock_runtime_dependencies.json").read_text(
            encoding="utf-8"
        )
    )
    declared = set(payload["dependencies"][0]["skills"])
    expected = {
        "convertible-bond-screening-strategy",
        "big-bull-analysis-scoring-system",
        "feilong-strategy",
        "jigou-capital-monitoring",
        "zhuangjia-capital-monitoring",
        "youzi-capital-monitoring",
        "technical-analysis",
        "dragon-pullback",
        "buzhang-leader-mining",
    }
    assert expected <= declared


def test_runtime_scripts_do_not_pin_the_migrated_user_profile() -> None:
    relative_paths = (
        "a-share-leader-deep-research/scripts/legacy_codex_entry.py",
        "a-share-leader-deep-research/scripts/word_com_render.py",
        "a-share-limit-up-mining/scripts/canonical_business_adapter.py",
        "limit-up-review/scripts/entry_limit_up_review.py",
        "a-share-sentiment-word-delivery/scripts/verify_a_share_sentiment_delivery.ps1",
        "baimao-teacher-system/scripts/baimao_workflow_acceptance.py",
    )
    for relative in relative_paths:
        text = (SKILLS / relative).read_text(encoding="utf-8-sig")
        assert "C:\\Users\\25296" not in text, relative


def test_baimao_auto_uses_current_acceptance_workflow() -> None:
    entry = (
        SKILLS / "baimao-teacher-system" / "scripts" / "baimao-teacher-system.py"
    ).read_text(encoding="utf-8-sig")
    acceptance = (
        SKILLS / "baimao-teacher-system" / "scripts" / "baimao_workflow_acceptance.py"
    ).read_text(encoding="utf-8-sig")
    assert "baimao_workflow_acceptance.py" in entry
    assert "LOCKED_PRODUCTION_SCRIPT" not in entry
    assert "skill_workflow_lock.py" not in acceptance
    assert "stock_workflow_substantive_gate.py" not in acceptance
    assert "openclaw_skill_visible_and_command" not in acceptance

    contracts = json.loads(
        (STOCK_UNIFIED / "references" / "stock_execution_contracts.json").read_text(
            encoding="utf-8"
        )
    )
    contract = next(
        row for row in contracts["contracts"]
        if row["skill_id"] == "baimao-teacher-system"
    )
    required = set(contract["workflow_guard"]["required_bindings"])
    assert "scripts/baimao_workflow_acceptance.py" in required
    assert "scripts/baimao-teacher-system_closure_gate.py" not in required


def test_risk_scan_summary_persists_component_error_details() -> None:
    source = (
        SKILLS / "risk-mine-clearance" / "scripts" / "audit_risk_scan.py"
    ).read_text(encoding="utf-8-sig")
    assert '"stderr_tail"' in source
    assert '"stdout_tail"' in source


def test_risk_scan_empty_candidate_groups_are_valid_sqlite_tables(tmp_path: Path) -> None:
    module = load_module(
        "risk-mine-clearance/scripts/a_share_risk_scan.py",
        "risk_scan_empty_candidates_regression",
    )
    health = [module.SourceHealth("probe", "regression", "ok", 0, 0.0)]
    base_frames = {
        name: pd.DataFrame({"empty": []})
        for name in (
            "shcpe_enterprise_notices",
            "credit_gd_wage_arrears",
            "credit_gd_court_defaulters_recent",
        )
    }
    module.write_outputs(
        tmp_path,
        "empty-regression",
        "2026-08-24T23:00:00+08:00",
        date(2026, 8, 24),
        base_frames,
        health,
        [],
        [],
        [],
    )
    with sqlite3.connect(tmp_path / "risk_scan.sqlite") as database:
        tables = {
            row[0]
            for row in database.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert {
        "risk_candidates",
        "front_candidates",
        "confirmed_risk_candidates",
        "evidence",
    } <= tables


def test_baimao_expected_trade_date_uses_multi_file_consensus(tmp_path: Path) -> None:
    module = load_module(
        "baimao-teacher-system/scripts/baimao_stock_score.py",
        "baimao_trade_date_consensus_regression",
    )
    module.VIPDOC = tmp_path
    dates = {
        "sh/lday/sh000001.day": 20260814,
        "sz/lday/sz399001.day": 20260821,
        "sz/lday/sz399006.day": 20260821,
        "sz/lday/sz000001.day": 20260824,
        "sh/lday/sh600000.day": 20260824,
        "sz/lday/sz300750.day": 20260824,
    }
    for relative, day in dates.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(module.DAY_RECORD.pack(day, 0, 0, 0, 0, 0.0, 0, 0))
    assert module.expected_trade_date() == "20260824"


def test_baimao_score_expected_trade_date_uses_multi_file_consensus(tmp_path: Path) -> None:
    module = load_module(
        "baimao-score-system/scripts/baimao_stock_score.py",
        "baimao_score_trade_date_consensus_regression",
    )
    module.VIPDOC = tmp_path
    dates = {
        "sh/lday/sh000001.day": 20260814,
        "sz/lday/sz399001.day": 20260821,
        "sz/lday/sz399006.day": 20260821,
        "sz/lday/sz000001.day": 20260824,
        "sh/lday/sh600000.day": 20260824,
        "sz/lday/sz300750.day": 20260824,
    }
    for relative, day in dates.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(module.DAY_RECORD.pack(day, 0, 0, 0, 0, 0.0, 0, 0))
    assert module.expected_trade_date() == "20260824"


def test_long_running_stock_contracts_have_consistent_timeout_budgets() -> None:
    payload = json.loads(
        (STOCK_UNIFIED / "references" / "stock_execution_contracts.json").read_text(
            encoding="utf-8"
        )
    )
    contracts = {row["skill_id"]: row for row in payload["contracts"]}
    core = contracts["core-mainline-scoring-system"]
    quality = contracts["quality-track-stock-selection"]
    quality_child_timeout = int(quality["business_command"][-1])
    assert core["timeout_seconds"] >= 900
    assert quality_child_timeout >= 480
    assert quality["timeout_seconds"] >= quality_child_timeout + 60


def test_baimao_score_contract_binds_direct_analysis_scripts() -> None:
    payload = json.loads(
        (STOCK_UNIFIED / "references" / "stock_execution_contracts.json").read_text(
            encoding="utf-8"
        )
    )
    contract = next(
        row for row in payload["contracts"] if row["skill_id"] == "baimao-score-system"
    )
    required = set(contract["workflow_guard"]["required_bindings"])
    bound_names = {Path(item["path"]).name for item in contract["business_bindings"]}
    assert {
        "scripts/baimao_comprehensive_analysis.py",
        "scripts/baimao_stock_score.py",
    } <= required
    assert {"baimao_comprehensive_analysis.py", "baimao_stock_score.py"} <= bound_names


def test_repaired_stock_runtime_paths_and_tq_signature_are_portable() -> None:
    quality_live = (
        SKILLS / "quality-track-stock-selection" / "scripts" / "quality_track_live.py"
    ).read_text(encoding="utf-8-sig")
    limit_up_adapter = (
        SKILLS / "a-share-limit-up-mining" / "scripts" / "canonical_business_adapter.py"
    ).read_text(encoding="utf-8-sig")
    buzhang_scripts = "\n".join(
        (SKILLS / "buzhang-leader-mining" / "scripts" / name).read_text(
            encoding="utf-8-sig"
        )
        for name in (
            "dynamic_hotspot_rank.py",
            "tdx_formula.py",
            "sync_roles_from_rank.py",
        )
    )

    assert 'TDX_ROOT = Path("C:/new_tdx_mock")' in quality_live
    assert "C:/new_tdx_mock" not in quality_live
    assert r"C:\Users\25296" not in limit_up_adapter
    assert "BUNDLED_AUTHORING_PYTHON = Path(sys.executable)" in limit_up_adapter
    assert "stock_list=" not in buzhang_scripts
    assert "stocks=" in buzhang_scripts


def test_five_dimension_lianban_refresh_degrades_on_timeout() -> None:
    adapter = (
        SKILLS / "five-dimension-resonance" / "scripts" / "canonical_business_adapter.py"
    ).read_text(encoding="utf-8-sig")
    refresh = adapter.split("def refresh_lianban_history", 1)[1].split(
        "def validate_mainline_report", 1
    )[0]

    assert "except subprocess.TimeoutExpired" in refresh
    assert '"status": "DEGRADED"' in refresh
    assert "continue" in refresh


def test_limit_up_review_uses_day_consensus_instead_of_block_mtime(tmp_path: Path) -> None:
    module = load_module(
        "limit-up-review/scripts/collect_limitup_data_strict.py",
        "limit_up_review_trade_date_consensus_regression",
    )
    module.TDX_BLOCK_DIR = tmp_path / "T0002" / "blocknew"
    module.TDX_VIPDOC = tmp_path / "vipdoc"
    block = module.TDX_BLOCK_DIR / "ZTC.blk"
    block.parent.mkdir(parents=True, exist_ok=True)
    block.write_text("0000001\n", encoding="ascii")
    weekend_timestamp = 1788019200
    os.utime(block, (weekend_timestamp, weekend_timestamp))
    dates = {
        "sh/lday/sh000001.day": 20260828,
        "sz/lday/sz399001.day": 20260828,
        "sz/lday/sz399006.day": 20260828,
        "sz/lday/sz000001.day": 20260828,
        "sh/lday/sh600000.day": 20260827,
        "sz/lday/sz300750.day": 20260828,
    }
    for relative, day in dates.items():
        target = module.TDX_VIPDOC / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(module.DAY_RECORD.pack(day, 0, 0, 0, 0, 0.0, 0, 0))

    assert module.tdx_block_snapshot_date("ZTC.blk") == "20260828"


def test_tdx_refresh_entry_requires_disk_change_and_never_launches_helper() -> None:
    source = (
        SKILLS / "tdx-local-hub" / "scripts" / "tdx_hub.py"
    ).read_text(encoding="utf-8-sig")
    refresh = source.split("def cmd_refresh_kline", 1)[1].split(
        "def cmd_blocks", 1
    )[0]

    assert 'sub.add_parser("refresh-kline")' in source
    assert '"status": "CLEAN_PASS" if disk_updated else "DATA_STALE"' in refresh
    assert '"helper_process_launch_allowed": False' in refresh
    assert "subprocess.Popen" not in refresh
    assert "ensure_runtime_helper" not in refresh


def test_tdx_primary_script_is_bound_into_execution_contract() -> None:
    payload = json.loads(
        (STOCK_UNIFIED / "references" / "stock_execution_contracts.json").read_text(
            encoding="utf-8"
        )
    )
    contract = next(
        row for row in payload["contracts"] if row["skill_id"] == "tdx-local-hub"
    )
    required = set(contract["workflow_guard"]["required_bindings"])
    bound_names = {Path(item["path"]).name for item in contract["business_bindings"]}

    assert "scripts/tdx_hub.py" in required
    assert "tdx_hub.py" in bound_names
