from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENGINE = load_module("a_share_15d_custom_block_test", SCRIPTS / "run_a_share_15d.py")
ADAPTER = load_module("a_share_15d_adapter_test", SCRIPTS / "canonical_business_adapter.py")


def block_record(name: str, code: str) -> bytes:
    record = bytearray(120)
    name_bytes = name.encode("gbk")
    code_bytes = code.encode("ascii")
    record[: len(name_bytes)] = name_bytes
    record[50 : 50 + len(code_bytes)] = code_bytes
    return bytes(record)


def test_resolve_tdx_custom_block_uses_catalog_and_strict_member_order(tmp_path: Path):
    config_path = tmp_path / "blocknew.cfg"
    config_path.write_bytes(
        block_record("飞龙在天", "FLZT") + block_record("其他板块", "OTHER")
    )
    (tmp_path / "FLZT.blk").write_text(
        "0000011\n1603559\n2920001\n0000011\n",
        encoding="ascii",
    )

    result = ENGINE.resolve_candidate_block("飞龙在天", config_path)

    assert result["name"] == "飞龙在天"
    assert result["code"] == "FLZT"
    assert result["member_count"] == 3
    assert result["members"] == [
        {"market": "SZ", "code": "000011"},
        {"market": "SH", "code": "603559"},
        {"market": "BJ", "code": "920001"},
    ]
    assert len(result["sha256"]) == 64


def test_resolve_tdx_custom_block_rejects_malformed_member(tmp_path: Path):
    config_path = tmp_path / "blocknew.cfg"
    config_path.write_bytes(block_record("飞龙在天", "FLZT"))
    (tmp_path / "FLZT.blk").write_text("0000011\nBADROW\n", encoding="ascii")

    try:
        ENGINE.resolve_candidate_block("飞龙在天", config_path)
    except RuntimeError as exc:
        assert "invalid TDX block member" in str(exc)
    else:
        raise AssertionError("malformed block member must block execution")


def test_canonical_adapter_forwards_only_supported_candidate_block_argument(tmp_path: Path):
    command = ADAPTER.business_command(tmp_path, ["--candidate-block", "飞龙在天"])

    assert command[-2:] == ["--candidate-block", "飞龙在天"]
    assert ADAPTER.validate_business_args([]) == []
    assert ADAPTER.validate_business_args(["--candidate-block", "飞龙在天"]) == []
    assert ADAPTER.validate_business_args(["--unsafe-option"]) == [
        "unsupported_business_arguments:--unsafe-option"
    ]


def _write_gate_result(run_dir: Path, trade_date: str = "20260831") -> None:
    deliverables = run_dir / "deliverables"
    deliverables.mkdir(parents=True)
    payload = {
        "status": "CLEAN_PASS",
        "trade_date": trade_date,
        "pool_candidate_count": 1,
        "candidate_pool": {
            "member_count": 1,
            "members": [{"market": "SZ", "code": "000001"}],
        },
        "macro": {"scan_coverage": {"complete": True}},
        "ranking": [{
            "code": "000001",
            "name": "测试股票",
            "concepts": ["测试题材"],
            "evidence_status": "LOCAL_TEXT_COVERED",
            "score_contract": {"fundamental_positive_weight": 0},
            "hard_exclusions": [{"name": "立案调查或财务造假", "passed": True}],
        }],
        "excluded": [],
        "validation": {
            "complete_scan": True,
            "market_scope_complete": True,
            "current_trade_date": True,
        },
    }
    (deliverables / ADAPTER.RESULT_FILENAME).write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def test_canonical_adapter_builds_clean_seven_dimension_data_gate(tmp_path: Path, monkeypatch):
    _write_gate_result(tmp_path)
    monkeypatch.setenv("CODEX_STOCK_EVIDENCE_SET_ID", "sha256:test-evidence")
    monkeypatch.setenv("CODEX_STOCK_EVIDENCE_TRADING_DATE", "2026-08-31")
    monkeypatch.setenv("CODEX_STOCK_SHARED_EVIDENCE_STATUS", "CLEAN_PASS")

    gate = ADAPTER.build_data_gate(tmp_path)

    assert gate["status"] == "CLEAN_PASS"
    assert gate["errors"] == []
    assert gate["effective_trading_date"] == "2026-08-31"
    assert set(gate["dimensions"]) == set(ADAPTER.DATA_GATE_DIMENSIONS)
    assert all(row["status"] == "CLEAN_PASS" for row in gate["dimensions"].values())


def test_canonical_adapter_blocks_mismatched_evidence_date(tmp_path: Path, monkeypatch):
    _write_gate_result(tmp_path)
    monkeypatch.setenv("CODEX_STOCK_EVIDENCE_SET_ID", "sha256:test-evidence")
    monkeypatch.setenv("CODEX_STOCK_EVIDENCE_TRADING_DATE", "2026-08-28")
    monkeypatch.setenv("CODEX_STOCK_SHARED_EVIDENCE_STATUS", "CLEAN_PASS")

    gate = ADAPTER.build_data_gate(tmp_path)

    assert gate["status"] == "BLOCKED"
    assert "data_gate_dimension_failed:effective_trading_date" in gate["errors"]
    assert "data_gate_dimension_failed:source_freshness" in gate["errors"]
