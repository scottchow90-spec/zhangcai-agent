from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "canonical_business_adapter.py"
)


def load_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "limit_up_canonical_business_adapter", MODULE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_freshness_uses_fetch_time_not_trade_date() -> None:
    module = load_module()
    now = datetime.fromisoformat("2026-09-02T11:00:00+08:00")

    assert module._is_fresh_source_timestamp(
        "2026-09-02T10:59:00+08:00", now=now
    )
    assert not module._is_fresh_source_timestamp(
        "2026-08-31T10:59:00+08:00", now=now
    )
    assert not module._is_fresh_source_timestamp(
        "2026-09-02T10:59:00", now=now
    )


def test_full_mode_result_binds_generated_docx(
    tmp_path: Path, monkeypatch
) -> None:
    module = load_module()
    document_bytes = b"test-docx-content"
    output_dir = tmp_path / "final-output"

    def fake_run_child(command: list[str], timeout: int) -> dict:
        output_dir = Path(command[command.index("--out-dir") + 1])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "连板挖掘_2026-08-18.docx").write_bytes(document_bytes)
        return {
            "returncode": 0,
            "stdout": '{"status":"CLEAN_PASS"}',
            "stderr": "",
            "timed_out": False,
        }

    monkeypatch.setattr(module, "run_child", fake_run_child)
    monkeypatch.setenv("CODEX_STOCK_CANONICAL_EXECUTION", "1")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(MODULE_PATH),
            "--run-dir",
            str(tmp_path),
            "--mode",
            "full",
            "--date",
            "20260818",
            "--manual-confirm",
            "--out",
            str(output_dir),
        ],
    )

    assert module.main() == 0
    result = json.loads((tmp_path / "business_result.json").read_text("utf-8"))
    artifact = result["artifacts"]["docx"]

    assert artifact["path"] == str(
        output_dir / "连板挖掘_2026-08-18.docx"
    )
    assert artifact["size"] == len(document_bytes)
    assert artifact["sha256"] == hashlib.sha256(document_bytes).hexdigest()


def test_full_mode_blocks_when_generated_docx_is_missing(
    tmp_path: Path, monkeypatch
) -> None:
    module = load_module()

    def fake_run_child(command: list[str], timeout: int) -> dict:
        return {
            "returncode": 0,
            "stdout": '{"status":"CLEAN_PASS"}',
            "stderr": "",
            "timed_out": False,
        }

    monkeypatch.setattr(module, "run_child", fake_run_child)
    monkeypatch.setenv("CODEX_STOCK_CANONICAL_EXECUTION", "1")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(MODULE_PATH),
            "--run-dir",
            str(tmp_path),
            "--mode",
            "full",
            "--date",
            "20260818",
            "--manual-confirm",
        ],
    )

    assert module.main() == 2
    result = json.loads((tmp_path / "business_result.json").read_text("utf-8"))

    assert result["status"] == "BLOCKED"
    assert result["delivery_validation"] == {
        "status": "BLOCKED",
        "errors": ["delivery_docx_missing"],
    }


def test_full_mode_emits_clean_conclusion_data_gate(
    tmp_path: Path, monkeypatch
) -> None:
    module = load_module()
    fetched_at = datetime.now().astimezone().isoformat(timespec="seconds")
    raw_path = tmp_path / "raw.json"
    analyzed_path = tmp_path / "analyzed.json"
    raw = {
        "date": "20260818",
        "zt_pool": [{"code": "300413", "name": "芒果超媒"}],
        "qsyb_collection": {
            "codes_probed": 1,
            "review_complete_codes": 1,
            "errors": [],
        },
        "rdxz_collection": {"rows": 1, "errors": []},
        "risk_collection": {
            "codes_probed": 1,
            "review_complete_codes": 1,
            "errors": [],
        },
    }
    analyzed = {
        "date": "20260818",
        "zt_scored": [{
            "code": "300413",
            "name": "芒果超媒",
            "k_line_verify": "PASS",
            "k_line_detail": {"source_kind": "TDX_LOCAL_DAY"},
            "risk_review_complete": True,
            "risk_result": {"final_action": "PASS"},
        }],
        "picks": [{
            "code": "300413",
            "name": "芒果超媒",
            "line": "传媒",
            "topic": "内容产业",
            "qsyb_bound": True,
            "rdxz_bound": True,
        }],
        "lines": [{"line": "传媒"}],
    }
    raw_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    analyzed_path.write_text(json.dumps(analyzed, ensure_ascii=False), encoding="utf-8")

    def fake_run_child(command: list[str], timeout: int) -> dict:
        output_dir = Path(command[command.index("--out-dir") + 1])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "连板挖掘_2026-08-18.docx").write_bytes(b"docx")
        evidence_path = Path(command[command.index("--data-evidence") + 1])
        evidence_path.write_text(json.dumps({
            "status": "PASS",
            "trade_date": "2026-08-18",
            "business_data_trade_date": "2026-08-18",
            "business_data_path": str(raw_path),
            "business_data_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            "analysis_path": str(analyzed_path),
            "analysis_sha256": hashlib.sha256(analyzed_path.read_bytes()).hexdigest(),
            "market_date": "2026-08-18",
            "limit_up_count": 1,
            "local_tdx_limit_up_count": 1,
            "strict_intersection_count": 1,
            "risk_review_complete_count": 1,
            "risk_review_error_count": 0,
            "data_cutoff": fetched_at,
            "sources": [{
                "trade_date": "2026-08-18",
                "fetched_at": fetched_at,
            }],
        }, ensure_ascii=False), encoding="utf-8")
        return {
            "returncode": 0,
            "stdout": '{"status":"CLEAN_PASS"}',
            "stderr": "",
            "timed_out": False,
        }

    monkeypatch.setattr(module, "run_child", fake_run_child)
    monkeypatch.setenv("CODEX_STOCK_CANONICAL_EXECUTION", "1")
    monkeypatch.setenv("CODEX_STOCK_EVIDENCE_SET_ID", "sha256:test-evidence")
    monkeypatch.setenv("CODEX_STOCK_EVIDENCE_TRADING_DATE", "2026-08-18")
    monkeypatch.setenv("CODEX_STOCK_SHARED_EVIDENCE_STATUS", "CLEAN_PASS")
    monkeypatch.setattr(sys, "argv", [
        str(MODULE_PATH),
        "--run-dir",
        str(tmp_path / "run"),
        "--mode",
        "full",
        "--date",
        "20260818",
        "--manual-confirm",
    ])

    assert module.main() == 0
    result = json.loads(
        (tmp_path / "run" / "business_result.json").read_text("utf-8")
    )
    assert result["status"] == "CLEAN_PASS"
    assert result["data_gate"]["status"] == "CLEAN_PASS"
    assert set(result["data_gate"]["dimensions"]) == set(module.DATA_GATE_DIMENSIONS)


def test_daily_mode_preserves_documented_output_directory(
    tmp_path: Path, monkeypatch
) -> None:
    module = load_module()
    output_dir = tmp_path / "daily-output"

    def fake_run_child(command: list[str], timeout: int) -> dict:
        assert command[command.index("--mode") + 1] == "daily"
        assert command[command.index("--out") + 1] == str(output_dir.resolve())
        assert "--min-total-score" not in command
        assert "--k-line-mode" not in command
        return {
            "returncode": 0,
            "stdout": '{"status":"CLEAN_PASS"}',
            "stderr": "",
            "timed_out": False,
        }

    monkeypatch.setattr(module, "run_child", fake_run_child)
    monkeypatch.setenv("CODEX_STOCK_CANONICAL_EXECUTION", "1")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(MODULE_PATH),
            "--run-dir",
            str(tmp_path / "runtime"),
            "--mode",
            "daily",
            "--date",
            "20260818",
            "--manual-confirm",
            "--out",
            str(output_dir),
        ],
    )

    assert module.main() == 0
