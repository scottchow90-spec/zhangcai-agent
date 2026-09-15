from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
CODEX_HOME = SKILL_ROOT.parents[1]
RUNTIME = CODEX_HOME / "scripts" / "stock_canonical_runtime.py"
SYNC = (
    CODEX_HOME
    / "skills"
    / "stock-unified"
    / "scripts"
    / "sync_stock_execution_contracts.py"
)
CONTRACTS = (
    CODEX_HOME
    / "skills"
    / "stock-unified"
    / "references"
    / "stock_execution_contracts.json"
)
VALID_CANARY = (
    "逐字回读 用户原话 禁止默认替代 禁止任务扩展 禁止单源结论 "
    "禁止热替换 输出结构服从用户 禁止缩窄范围 禁止子代理跑偏 "
    "禁止假交付"
)


def _load_preflight():
    script = SKILL_ROOT / "scripts" / "preflight.py"
    spec = importlib.util.spec_from_file_location("stock_hard_gate_preflight_test", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _route(query: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(RUNTIME), "route", "--query", query],
        cwd=CODEX_HOME,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


def test_route_ownership_is_exclusive_and_not_confused() -> None:
    assert _route("$stock-hard-gate")["skill_ids"] == ["stock-hard-gate"]
    assert _route("硬闸")["skill_ids"] == ["stock-hard-gate"]
    assert _route("股票技能总验收")["skill_ids"] == ["stock-unified"]
    assert _route("股票投研交付")["skill_ids"] == ["stock-deliverable"]


def test_public_entry_matches_the_canonical_stock_facade() -> None:
    public_entry = SKILL_ROOT / "scripts" / "codex_entry.py"
    canonical_entry = (
        CODEX_HOME
        / "skills"
        / "a-share-bottom-fishing"
        / "scripts"
        / "codex_entry.py"
    )

    assert public_entry.read_text(encoding="utf-8-sig").replace("\r\n", "\n") == (
        canonical_entry.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    )


def test_legacy_entry_direct_execution_is_rejected() -> None:
    environment = os.environ.copy()
    environment.pop("ONESTOCK_STOCK_CANONICAL_CHILD", None)
    completed = subprocess.run(
        [sys.executable, str(SKILL_ROOT / "scripts" / "legacy_codex_entry.py"), "info"],
        cwd=SKILL_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        env=environment,
        check=False,
    )
    assert completed.returncode == 2
    assert "canonical_stock_legacy_entry_direct_execution_blocked" in completed.stderr


def test_preflight_accepts_complete_positive_canary() -> None:
    ok, warnings = _load_preflight().preflight(VALID_CANARY, "preflight")

    assert ok is True
    assert warnings == []


def test_preflight_rejects_missing_guards_and_legacy_formula_name() -> None:
    ok, warnings = _load_preflight().preflight("大牛线 计划", "preflight")

    assert ok is False
    assert any(item.startswith("REPLAY:") for item in warnings)
    assert any(item.startswith("HARDCLASS:") for item in warnings)
    assert any(item.startswith("FORMULA:") for item in warnings)


def test_contract_has_exactly_ten_current_business_bindings() -> None:
    payload = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    contract = next(
        row for row in payload["contracts"] if row["skill_id"] == "stock-hard-gate"
    )
    bindings = contract["business_bindings"]

    assert len(bindings) == 10
    assert len({binding["path"] for binding in bindings}) == 10
    assert all(Path(binding["path"]).is_file() for binding in bindings)
    assert contract["workflow_identity"] == {
        "owner_skill_id": "stock-hard-gate",
        "exclusive_owner": True,
        "route_authority": "canonical_stock_skill_routing_catalog",
    }


def test_global_stock_contract_catalog_has_zero_drift() -> None:
    completed = subprocess.run(
        [sys.executable, str(SYNC), "--check"],
        cwd=CODEX_HOME,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
