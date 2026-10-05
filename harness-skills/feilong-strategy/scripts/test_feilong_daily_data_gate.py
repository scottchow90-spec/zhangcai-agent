#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import canonical_business_adapter as adapter


def evidence(path: Path) -> dict:
    return {
        "path": str(path.resolve()),
        "size": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class DailyDataGateTests(unittest.TestCase):
    def fixture(self, root: Path) -> tuple[str, Path]:
        manifest = root / "飞龙在天_实战评分清单.json"
        decision = root / "飞龙在天_生产评分决策.csv"
        today = root / "飞龙在天_当日32维实战评分.csv"
        drift = root / "飞龙在天_生产漂移锁.json"
        zero = root / "飞龙在天_零缺失审计.json"
        legacy = root / "飞龙在天_全局旧版剔除审计.json"
        duanxianxia = root / "duanxianxia.json"
        finance = root / "base.dbf"
        finance.write_bytes(b"fixture-finance")
        manifest.write_text("{}\n", encoding="utf-8")
        write_csv(
            decision,
            [
                {
                    "symbol": "600001.SH",
                    "name": "测试甲",
                    "first_board_date": "20260831",
                    "production_decision": "ACCEPT_SCORE_B",
                    "decision_rule_version": "FEILONG_32D_DECISION_V2",
                    "factor_completeness": "COMPLETE",
                },
                {
                    "symbol": "000002.SZ",
                    "name": "测试乙",
                    "first_board_date": "20260831",
                    "production_decision": "REJECT_HARD_GATE",
                    "decision_rule_version": "FEILONG_32D_DECISION_V2",
                    "factor_completeness": "COMPLETE",
                },
            ],
        )
        write_csv(
            today,
            [
                {
                    "symbol": "600001.SH",
                    "name": "测试甲",
                    "first_board_date": "20260831",
                    "formula_resolved": "True",
                    "hard_exclusion": "False",
                    "production_decision": "ACCEPT_SCORE_B",
                    "announcement_verification_status": "本机近14日本地资讯已扫描",
                }
            ],
        )
        write_json(
            drift,
            {
                "status": "CLEAN_PASS",
                "same_run_input_snapshot_stable": True,
                "tdx_input_snapshot": {"file_count": 10, "sha256": "a" * 64},
                "risk_corpus_snapshot": {"file_count": 2, "sha256": "b" * 64},
            },
        )
        write_json(
            zero,
            {
                "status": "CLEAN_PASS",
                "source_invalid_cells": 0,
                "source_nan_cells": 0,
                "production_missing_cells": 0,
                "production_nonfinite_cells": 0,
                "rejected_incomplete_rows": 0,
                "target_rejected_incomplete_rows": 0,
            },
        )
        write_json(
            legacy,
            {
                "status": "CLEAN_PASS",
                "active_executable_old_formula_references": 0,
            },
        )
        write_json(
            duanxianxia,
            {
                "source_page": "https://duanxianxia.com/web/main",
                "datasets": {"themes": {"success": True}},
            },
        )
        payload = {
            "schema": "FEILONG_DAILY_YAOGU_PRODUCTION_V2",
            "status": "CLEAN_PASS",
            "checks": {
                "target_date": "20260831",
                "tdx_latest_date": "20260831",
                "target_scored_count": 1,
                "target_hard_excluded_outside_model_domain_count": 1,
                "target_rejected_incomplete_count": 0,
                "stale": False,
                "tdx_input_snapshot_stable": True,
                "tdx_mainboard_readable_count": 10,
                "tdx_mainboard_at_latest_count": 9,
                "local_risk_corpus_file_count": 2,
            },
            "inputs": {"finance": evidence(finance)},
            "artifacts": {
                path.name: evidence(path)
                for path in (manifest, decision, today, drift, zero, legacy)
            },
        }
        return json.dumps(payload, ensure_ascii=False), duanxianxia

    def environment(self, duanxianxia: Path, trading_date: str = "2026-08-31") -> dict:
        return {
            "CODEX_STOCK_EVIDENCE_SET_ID": "sha256:" + "c" * 64,
            "CODEX_STOCK_EVIDENCE_TRADING_DATE": trading_date,
            "CODEX_STOCK_SHARED_EVIDENCE_STATUS": "CLEAN_PASS",
            "CODEX_DUANXIANXIA_SNAPSHOT": str(duanxianxia.resolve()),
        }

    def test_clean_gate_has_all_seven_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            stdout, duanxianxia = self.fixture(Path(temp))
            with (
                mock.patch.dict(os.environ, self.environment(duanxianxia), clear=False),
                mock.patch.object(adapter, "_file_evidence_is_current", return_value=True),
            ):
                result = adapter.build_daily_data_gate(stdout)
        self.assertEqual(result["status"], "CLEAN_PASS")
        self.assertEqual(set(result["dimensions"]), set(adapter.DATA_GATE_DIMENSIONS))
        self.assertTrue(all(row["status"] == "CLEAN_PASS" for row in result["dimensions"].values()))
        self.assertEqual(result["errors"], [])

    def test_trading_date_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            stdout, duanxianxia = self.fixture(Path(temp))
            with (
                mock.patch.dict(
                    os.environ,
                    self.environment(duanxianxia, trading_date="2026-08-30"),
                    clear=False,
                ),
                mock.patch.object(adapter, "_file_evidence_is_current", return_value=True),
            ):
                result = adapter.build_daily_data_gate(stdout)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["dimensions"]["effective_trading_date"]["status"], "BLOCKED")
        self.assertIn("data_gate_dimension_failed:source_freshness", result["errors"])

    def test_missing_identity_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stdout, duanxianxia = self.fixture(root)
            decision = root / "飞龙在天_生产评分决策.csv"
            rows = adapter._csv_rows(decision)
            rows[0]["name"] = ""
            write_csv(decision, rows)
            payload = json.loads(stdout)
            payload["artifacts"][decision.name] = evidence(decision)
            with (
                mock.patch.dict(os.environ, self.environment(duanxianxia), clear=False),
                mock.patch.object(adapter, "_file_evidence_is_current", return_value=True),
            ):
                result = adapter.build_daily_data_gate(
                    json.dumps(payload, ensure_ascii=False)
                )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("data_gate_dimension_failed:identity", result["errors"])


if __name__ == "__main__":
    unittest.main()
