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
from pathlib import Path
from types import SimpleNamespace


SOURCE = Path(r"D:\C盘转移\日志\codex\scripts\stock_support_pressure_adapter.py")


def load_module():
    spec = importlib.util.spec_from_file_location("stock_support_pressure_adapter_test", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_verified_support_candidates_maps_only_bound_report_fields(tmp_path: Path):
    module = load_module()
    artifact = tmp_path / "600000_SH.scientific_support_pressure.json"
    artifact_payload = {
        "status": "PASS",
        "symbol": "600000.SH",
        "data_provenance": {
            "source_type": "tdx_local_hub",
            "history_scope": "FULL_LOCAL_TDX_FILE",
            "full_history_verified": True,
            "data_path": r"C:\new_tdx_mock\vipdoc\sh\lday\sh600000.day",
            "data_sha256": "a" * 64,
            "source_end_date": "20260817",
        },
        "technical_context": {"close": 10.5, "rsi14": 31.0},
        "conclusion": {
            "location_state": "NEAR_SUPPORT_TEST",
            "primary_support_zone": {"lower": 9.8, "center": 10.0, "upper": 10.2},
            "primary_resistance_zone": {"lower": 11.0, "center": 11.2, "upper": 11.4},
            "support_scenario_invalidation": {"price": 9.5},
        },
    }
    raw = json.dumps(artifact_payload).encode("utf-8")
    artifact.write_bytes(raw)
    summary = tmp_path / "run_summary.json"
    summary.write_text(
        json.dumps(
            {
                "status": "PASS",
                "items": [
                    {
                        "symbol": "600000.SH",
                        "status": "PASS",
                        "data_end_date": "2026-08-17",
                        "artifact": {
                            "path": str(artifact),
                            "size": len(raw),
                            "sha256": hashlib.sha256(raw).hexdigest(),
                            "readback_status": "PASS",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = module.load_verified_support_candidates(summary)

    assert result["data_source"] == "support-pressure-analysis-system"
    assert result["fallback_used"] is False
    assert result["candidates"] == [
        {
            "code": "600000.SH",
            "name": "600000.SH",
            "latest": 10.5,
            "buy_low": 9.8,
            "invalid": 9.5,
            "rsi14": 31.0,
            "location_state": "NEAR_SUPPORT_TEST",
            "support_zone": {"lower": 9.8, "center": 10.0, "upper": 10.2},
            "resistance_zone": {"lower": 11.0, "center": 11.2, "upper": 11.4},
            "data_end_date": "2026-08-17",
            "source": "support-pressure-analysis-system",
            "source_artifact": str(artifact),
            "source_artifact_sha256": hashlib.sha256(raw).hexdigest(),
            "tdx_data_path": r"C:\new_tdx_mock\vipdoc\sh\lday\sh600000.day",
            "tdx_data_sha256": "a" * 64,
        }
    ]


def test_run_current_support_pressure_uses_canonical_root_entry(monkeypatch, tmp_path: Path):
    module = load_module()
    home = tmp_path / "Home"
    entry = home / "skills" / "support-pressure-analysis-system" / "scripts" / "codex_entry.py"
    entry.parent.mkdir(parents=True)
    entry.write_text("# root entry", encoding="utf-8")
    out_dir = tmp_path / "run"
    observed = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        artifact = out_dir / "000001_SH.scientific_support_pressure.json"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "status": "PASS",
            "symbol": "000001.SH",
            "data_provenance": {
                "source_type": "tdx_local_hub",
                "history_scope": "FULL_LOCAL_TDX_FILE",
                "full_history_verified": True,
                "data_path": r"C:\new_tdx_mock\vipdoc\sh\lday\sh000001.day",
                "data_sha256": "b" * 64,
            },
            "technical_context": {"close": 3982.65, "rsi14": 57.5},
            "conclusion": {
                "location_state": "NEAR_SUPPORT_TEST",
                "primary_support_zone": {"lower": 3954.0},
                "primary_resistance_zone": {"lower": 4021.0},
                "support_scenario_invalidation": {"price": 3941.0},
            },
        }
        raw = json.dumps(report).encode("utf-8")
        artifact.write_bytes(raw)
        (out_dir / "run_summary.json").write_text(
            json.dumps(
                {
                    "status": "PASS",
                    "items": [
                        {
                            "symbol": "000001.SH",
                            "status": "PASS",
                            "data_end_date": "2026-08-17",
                            "artifact": {
                                "path": str(artifact),
                                "size": len(raw),
                                "sha256": hashlib.sha256(raw).hexdigest(),
                                "readback_status": "PASS",
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0, stdout='{"status":"CLEAN_PASS"}', stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.run_current_support_pressure(home, out_dir, timeout=123)

    assert observed["command"][1:4] == [str(entry), "run", "--"]
    assert observed["command"][-6:] == [
        "--limit",
        "0",
        "--out-dir",
        str(out_dir),
        "--run-id",
        out_dir.name,
    ]
    assert observed["kwargs"]["timeout"] == 123
    assert result["candidates"][0]["code"] == "000001.SH"
