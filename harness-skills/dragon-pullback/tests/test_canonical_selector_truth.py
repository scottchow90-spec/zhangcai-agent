from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LEGACY = load_module("dragon_pullback_legacy_entry", ROOT / "scripts" / "legacy_codex_entry.py")
ADAPTER = load_module("dragon_pullback_canonical_adapter", ROOT / "scripts" / "canonical_business_adapter.py")
BUSINESS_ENTRY = load_module("dragon_pullback_business_entry", ROOT / "scripts" / "dragon-pullback.py")


def write_report(directory: Path, symbol: str = "000001.SZ") -> Path:
    source = directory / "candidate.day"
    source.write_bytes(b"real-local-tdx-fixture")
    code, market = symbol.split(".")
    candidate = {
        "symbol": symbol,
        "code": code,
        "market": market,
        "name": "平安银行" if symbol == "000001.SZ" else "上证指数",
        "grade": "S",
        "score": 86,
        "selection_status": "SIGNAL",
        "metrics": {"date": "20260824"},
        "source": {
            "path": str(source),
            "size": source.stat().st_size,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        },
    }
    report = {
        "schema_version": 1,
        "strategy_id": "strong-leader-first-yin-v1",
        "status": "CLEAN_PASS",
        "selection_status": "SIGNAL",
        "latest_trade_date": "20260824",
        "data_source": {"type": "local_tdx_raw_daily"},
        "universe": {
            "eligible_security_records": 5200,
            "scan_stats": {"latest_trade_date": 5100},
        },
        "selection": {
            "candidate_count": 1,
            "candidates": [candidate],
            "strict_count": 1,
            "turnover_divergence_count": 0,
            "practical_count": 0,
            "technical_trade_ready_count": 1,
        },
        "historical_replay": {"signal_count": 12},
        "validation": {
            "selector_operational": True,
            "candidate_count_matches": True,
            "unique_stock_candidates": True,
        },
        "risk_boundary": {
            "decision_scope": "local_tdx_end_of_day_technical_selection",
            "external_event_data": "not_used_in_selection",
            "entry_timing": "not_a_trade_instruction",
            "historical_validation": "signal_trigger_replay_completed",
            "guaranteed_profit": False,
        },
    }
    path = directory / "strong-leader-first-yin.json"
    path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    return path


class CanonicalDragonSelectorTruthTests(unittest.TestCase):
    def test_fixed_entry_targets_full_market_selector(self) -> None:
        self.assertEqual(
            LEGACY.PRIMARY_REL,
            "scripts/run_strong_leader_first_yin.py",
        )
        self.assertEqual(
            BUSINESS_ENTRY.PRIMARY_BUSINESS_SCRIPT,
            "run_strong_leader_first_yin.py",
        )
        skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/run_strong_leader_first_yin.py", skill_text)
        self.assertNotIn("本地业务脚本：`scripts/run_dragon_pullback_smoke.py`", skill_text)

    def test_adapter_derives_business_evidence_from_full_market_report(self) -> None:
        with TemporaryDirectory() as temporary:
            report = write_report(Path(temporary))
            child_stdout = json.dumps(
                {
                    "status": "CLEAN_PASS",
                    "latest_trade_date": "20260824",
                    "report": str(report),
                },
                ensure_ascii=False,
            )

            result = ADAPTER.derive_validated_selector(child_stdout)

        self.assertEqual(result["strategy_id"], "strong-leader-first-yin-v1")
        self.assertEqual(result["selection_status"], "SIGNAL")
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["candidates"][0]["symbol"], "000001.SZ")

    def test_adapter_rejects_index_candidate(self) -> None:
        with TemporaryDirectory() as temporary:
            report = write_report(Path(temporary), symbol="000001.SH")
            child_stdout = json.dumps(
                {"status": "CLEAN_PASS", "report": str(report)},
                ensure_ascii=False,
            )

            with self.assertRaisesRegex(ValueError, "index_candidate"):
                ADAPTER.derive_validated_selector(child_stdout)

    def test_adapter_rejects_old_smoke_output(self) -> None:
        smoke = json.dumps(
            {
                "ok": True,
                "status": "CLEAN_PASS",
                "symbol": "000001.SH",
                "support_candidate": {"code": "000001.SH"},
            },
            ensure_ascii=False,
        )

        with self.assertRaises(ValueError):
            ADAPTER.derive_validated_selector(smoke)


if __name__ == "__main__":
    unittest.main(verbosity=2)
