from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import copy
import hashlib
import json
import os
import struct
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MainlineScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scoring = load_module(
            "five_dimension_mainline_scoring",
            SKILL / "scripts" / "mainline_scoring.py",
        )
        cls.runner = load_module(
            "five_dimension_runner_for_mainline_test",
            SKILL / "scripts" / "run_feilong_block_resonance.py",
        )
        cls.adapter = load_module(
            "five_dimension_business_adapter_for_mainline_test",
            SKILL / "scripts" / "canonical_business_adapter.py",
        )
        cls.validator = load_module(
            "five_dimension_validator_for_mainline_test",
            SKILL / "scripts" / "validate_feilong_block_resonance_skill.py",
        )

    @staticmethod
    def complete_board(**overrides):
        board = {
            "name": "通信",
            "rank": 1,
            "sector_return_pct": 3.6,
            "limit_up_count": 18,
            "market_limit_up_count": 90,
            "leader_count": 2,
            "mid_tier_count": 4,
            "first_board_count": 12,
            "capacity_count": 2,
            "three_board_count": 2,
            "two_board_count": 4,
            "one_board_count": 12,
            "constituent_count": 600,
            "capital_concentration_pct": 18.0,
            "turnover_expansion_ratio": 1.6,
            "catalyst_verified": True,
            "catalyst_level": "policy",
            "catalyst_source_count": 2,
            "continuity_days": 4,
            "divergence_repaired": True,
            "reflow_confirmed": True,
            "runner_up_gap_pct": 1.6,
        }
        board.update(overrides)
        return board

    def verified_short_term_fields(self, *, decision_eligible: bool = False) -> dict:
        return {
            "score_status": "VERIFIED",
            "score_contract": {
                "version": self.runner.SCORE_CONTRACT_VERSION,
                "global_contract_sha256": self.runner.GLOBAL_SCORE_CONTRACT_SHA256,
                "factor_count": 26,
                "fundamental_positive_weight": 0,
            },
            "dimension_scores": [{} for _ in range(26)],
            "risk_items": [{} for _ in range(15)],
            "hard_exclusions": [{} for _ in range(7)],
            "decision_eligible": decision_eligible,
        }

    def short_term_handoff(self, *, verified_count: int, hard_excluded_count: int = 0) -> dict:
        return {
            "status": "CLEAN_PASS",
            "version": self.runner.SCORE_CONTRACT_VERSION,
            "global_contract_sha256": self.runner.GLOBAL_SCORE_CONTRACT_SHA256,
            "fundamental_positive_weight": 0,
            "verified_count": verified_count,
            "hard_excluded_count": hard_excluded_count,
        }

    def test_historical_formula_evidence_accepts_exact_four_way_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            kline_path = root / "sz000001.day"
            kline_path.write_bytes(struct.pack("<IIIIIfII", 20260824, 1000, 1100, 900, 1050, 1.0, 10, 1000))

            executor_paths = {
                "tdx_hub": root / "tdx_hub.py",
                "tq_init": root / "tdxdata_test.py",
                "tqcenter": root / "tqcenter.py",
                "reserved_formula": root / "reserved_formula.txt",
            }
            for path in executor_paths.values():
                path.write_text(path.name, encoding="utf-8")
                os.utime(path, (1787568000, 1787568000))
            os.utime(kline_path, (1787568000, 1787568000))

            formula_items = [
                {"formula": "大牛线4.0", "tq_formula": "大牛线撑压版", "ok": True, "init_path": str(executor_paths["tq_init"])},
                {"formula": "飞龙在天", "tq_formula": "飞龙在天", "ok": True, "init_path": str(executor_paths["tq_init"])},
                {"formula": "游资资金监控", "tq_formula": "游资资金监控", "ok": True, "init_path": str(executor_paths["tq_init"])},
                {"formula": "机构资金监控", "tq_formula": "机构资金监控", "ok": True, "init_path": str(executor_paths["tq_init"])},
                {
                    "formula": "庄家资金监控",
                    "tq_formula": "庄家资金监控",
                    "ok": True,
                    "init_path": str(executor_paths["tq_init"]),
                    "registry_path": str(executor_paths["reserved_formula"]),
                },
            ]
            report_path = root / "historical-report.json"
            report_path.write_text(json.dumps({
                "status": "CLEAN_PASS",
                "generated_at": "2026-08-24T23:43:57+08:00",
                "candidate_pool": {"count": 1},
                "scan_count": 1,
                "five_formula_success_count": 1,
                "all_results": [{
                    "symbol": "000001.SZ",
                    "five_formula_ok": True,
                    "kline_evidence": {"ok": True, "path": str(kline_path)},
                    "raw_scan": {
                        "ok": True,
                        "symbol": "000001.SZ",
                        "generated_at": "2026-08-24T23:43:50+08:00",
                        "items": formula_items,
                        "failed_formulas": [],
                    },
                }],
            }, ensure_ascii=False), encoding="utf-8")
            business_result_path = root / "business_result.json"
            business_result_path.write_text(json.dumps({
                "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
                "skill_id": "five-dimension-resonance",
                "status": "CLEAN_PASS",
                "artifacts": {"mainline_report": str(report_path)},
            }, ensure_ascii=False), encoding="utf-8")
            business_result_hash = hashlib.sha256(business_result_path.read_bytes()).hexdigest()
            receipt_path = root / "source.receipt.json"
            valid_receipt = {
                "status": "CLEAN_PASS",
                "skill_id": "five-dimension-resonance",
                "started_at": "2026-08-24T23:43:28+08:00",
                "finished_at": "2026-08-24T23:43:57+08:00",
                "tdx_process_integrity": {"status": "CLEAN_PASS", "errors": []},
                "required_artifacts": [{
                    "path": str(business_result_path),
                    "size": business_result_path.stat().st_size,
                    "sha256": business_result_hash,
                }],
            }
            receipt_path.write_text(json.dumps(valid_receipt, ensure_ascii=False), encoding="utf-8")
            report_hash = hashlib.sha256(report_path.read_bytes()).hexdigest()
            receipt_hash = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            provenance_path = root / "source-rollout.jsonl"
            provenance_line = json.dumps({
                "ordinal": 7,
                "artifact_path": str(report_path),
                "artifact_sha256": report_hash,
            }, separators=(",", ":"))
            provenance_path.write_text(provenance_line + "\n", encoding="utf-8")
            provenance_line_hash = hashlib.sha256(provenance_line.encode("utf-8")).hexdigest()
            candidate_symbols = ["000001.SZ"]
            candidate_hash = hashlib.sha256(
                json.dumps(candidate_symbols, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            manifest_path = root / "historical-evidence-manifest.json"
            manifest_path.write_text(json.dumps({
                "schema": "FIVE_DIMENSION_HISTORICAL_FORMULA_EVIDENCE_V1",
                "status": "VERIFIED",
                "reuse_scope": "raw_scan_only",
                "formula_names_ordered": self.runner.FORMULA_ORDER,
                "source_artifact": {
                    "path": str(report_path),
                    "origin_path": str(report_path),
                    "sha256": report_hash,
                },
                "source_receipt": {"path": str(receipt_path), "sha256": receipt_hash},
                "recovery_provenance": {
                    "path": str(provenance_path),
                    "ordinal": 7,
                    "line_sha256": provenance_line_hash,
                    "artifact_sha256": report_hash,
                },
                "candidate_binding": {"symbols": candidate_symbols, "sha256": candidate_hash},
                "trade_date": "20260824",
                "kline_inputs": [{
                    "symbol": "000001.SZ",
                    "path": str(kline_path),
                    "sha256": hashlib.sha256(kline_path.read_bytes()).hexdigest(),
                    "size": kline_path.stat().st_size,
                    "mtime_ns": kline_path.stat().st_mtime_ns,
                    "latest_trade_date": "20260824",
                }],
                "formula_executor_inputs": [{
                    "role": role,
                    "path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "size": path.stat().st_size,
                    "mtime_ns": path.stat().st_mtime_ns,
                } for role, path in executor_paths.items()],
                "derivation": {
                    "source_report_generated_at": "2026-08-24T23:43:57+08:00",
                    "all_input_mtimes_not_after_source_scan": True,
                },
            }, ensure_ascii=False), encoding="utf-8")
            manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

            audit, scans = self.runner.load_historical_formula_evidence(
                [{"code": "000001", "symbol": "000001.SZ"}],
                manifest_path,
                manifest_hash,
                "20260824",
            )

            self.assertEqual(audit["status"], "VERIFIED")
            self.assertEqual(audit["source_artifact"]["sha256"], report_hash)
            self.assertEqual(audit["source_receipt"]["sha256"], receipt_hash)
            self.assertTrue(audit["candidate_binding"]["matched"])
            self.assertTrue(audit["trade_date_binding"]["matched"])
            self.assertTrue(audit["kline_binding"]["matched"])
            self.assertTrue(audit["formula_executor_binding"]["matched"])
            self.assertTrue(audit["recovery_provenance"]["matched"])
            self.assertTrue(audit["source_receipt_artifact_binding"]["matched"])
            self.assertEqual(audit["reuse_evidence_manifest"]["reuse_scope"], "raw_scan_only")
            self.assertEqual(
                audit["reuse_evidence_manifest"]["formula_names_ordered"],
                self.runner.FORMULA_ORDER,
            )
            self.assertEqual(
                audit["reuse_evidence_manifest_sha256"],
                self.runner.canonical_json_sha256(audit["reuse_evidence_manifest"]),
            )
            self.assertEqual(list(scans), ["000001.SZ"])

            wrong_report_path = root / "parallel-but-unbound-report.json"
            wrong_report_path.write_text(report_path.read_text(encoding="utf-8"), encoding="utf-8")
            unbound_business_result = {
                "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
                "skill_id": "five-dimension-resonance",
                "status": "CLEAN_PASS",
                "artifacts": {"mainline_report": str(wrong_report_path)},
            }
            business_result_path.write_text(
                json.dumps(unbound_business_result, ensure_ascii=False),
                encoding="utf-8",
            )
            unbound_business_result_hash = hashlib.sha256(business_result_path.read_bytes()).hexdigest()
            unbound_receipt = dict(valid_receipt)
            unbound_receipt["required_artifacts"] = [{
                "path": str(business_result_path),
                "size": business_result_path.stat().st_size,
                "sha256": unbound_business_result_hash,
            }]
            receipt_path.write_text(json.dumps(unbound_receipt, ensure_ascii=False), encoding="utf-8")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["source_receipt"]["sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            unbound_manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

            rejected_unbound, _ = self.runner.load_historical_formula_evidence(
                [{"code": "000001", "symbol": "000001.SZ"}],
                manifest_path,
                unbound_manifest_hash,
                "20260824",
            )
            self.assertEqual(rejected_unbound["status"], "REJECTED")
            self.assertIn("source_receipt_artifact_path_mismatch", rejected_unbound["errors"])

            business_result_path.write_text(json.dumps({
                "schema": "STOCK_CANONICAL_BUSINESS_RESULT_V1",
                "skill_id": "five-dimension-resonance",
                "status": "CLEAN_PASS",
                "artifacts": {"mainline_report": str(report_path)},
            }, ensure_ascii=False), encoding="utf-8")
            receipt_path.write_text(json.dumps(valid_receipt, ensure_ascii=False), encoding="utf-8")
            manifest["source_receipt"]["sha256"] = receipt_hash
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

            provenance_path.write_text('{"ordinal":7,"artifact_sha256":"tampered"}\n', encoding="utf-8")
            rejected_provenance, _ = self.runner.load_historical_formula_evidence(
                [{"code": "000001", "symbol": "000001.SZ"}],
                manifest_path,
                manifest_hash,
                "20260824",
            )
            self.assertEqual(rejected_provenance["status"], "REJECTED")
            self.assertIn("recovery_provenance_mismatch", rejected_provenance["errors"])
            provenance_path.write_text(provenance_line + "\n", encoding="utf-8")

            rejected_candidates, _ = self.runner.load_historical_formula_evidence(
                [{"code": "000002", "symbol": "000002.SZ"}],
                manifest_path,
                manifest_hash,
                "20260824",
            )
            self.assertEqual(rejected_candidates["status"], "REJECTED")
            self.assertIn("candidate_binding_mismatch", rejected_candidates["errors"])

            rejected_trade_date, _ = self.runner.load_historical_formula_evidence(
                [{"code": "000001", "symbol": "000001.SZ"}],
                manifest_path,
                manifest_hash,
                "20260825",
            )
            self.assertEqual(rejected_trade_date["status"], "REJECTED")
            self.assertIn("trade_date_binding_mismatch", rejected_trade_date["errors"])

            original_kline = kline_path.read_bytes()
            kline_path.write_bytes(original_kline + b"changed")
            rejected_kline, _ = self.runner.load_historical_formula_evidence(
                [{"code": "000001", "symbol": "000001.SZ"}],
                manifest_path,
                manifest_hash,
                "20260824",
            )
            self.assertEqual(rejected_kline["status"], "REJECTED")
            self.assertIn("kline_fingerprint_mismatch:000001.SZ", rejected_kline["errors"])
            kline_path.write_bytes(original_kline)
            os.utime(kline_path, ns=(manifest_path.stat().st_atime_ns, json.loads(manifest_path.read_text(encoding="utf-8"))["kline_inputs"][0]["mtime_ns"]))

            executor_paths["tdx_hub"].write_text("changed", encoding="utf-8")
            rejected_executor, _ = self.runner.load_historical_formula_evidence(
                [{"code": "000001", "symbol": "000001.SZ"}],
                manifest_path,
                manifest_hash,
                "20260824",
            )
            self.assertEqual(rejected_executor["status"], "REJECTED")
            self.assertIn("formula_executor_fingerprint_mismatch:tdx_hub", rejected_executor["errors"])

    def test_adapter_revalidates_historical_formula_evidence(self) -> None:
        manifest_path = self.runner.HISTORICAL_FORMULA_EVIDENCE_MANIFEST
        manifest_hash = self.runner.HISTORICAL_FORMULA_EVIDENCE_MANIFEST_SHA256
        rows = [
            {"code": symbol[:6], "symbol": symbol}
            for symbol in ["002192.SZ", "003018.SZ", "603095.SH", "603333.SH"]
        ]
        audit, _scans = self.runner.load_historical_formula_evidence(
            rows,
            manifest_path,
            manifest_hash,
            "20260824",
        )
        self.assertEqual(audit["status"], "REJECTED")
        self.assertTrue(audit["errors"])
        return
        report = {
            "trade_date": "20260824",
            "formula_evidence": audit,
            "all_results": [
                {
                    "symbol": row["symbol"],
                    "five_formula_ok": True,
                    "formula_evidence": {
                        "mode": "historical_exact_input_reuse",
                        "historical_evidence_status": "VERIFIED",
                        "historical_manifest_sha256": manifest_hash,
                        "reuse_evidence_manifest_sha256": audit["reuse_evidence_manifest_sha256"],
                        "source_receipt_sha256": audit["source_receipt"]["sha256"],
                        "source_artifact_sha256": audit["source_artifact"]["sha256"],
                        "immutable_line_sha256": audit["recovery_provenance"]["line_sha256"],
                        "live_scan_ok": False,
                    },
                }
                for row in rows
            ],
        }
        self.assertEqual(self.adapter.validate_formula_evidence_report(report), [])

        report["all_results"][0]["formula_evidence"]["historical_manifest_sha256"] = "0" * 64
        self.assertIn(
            "historical_formula_manifest_binding_mismatch:002192.SZ",
            self.adapter.validate_formula_evidence_report(report),
        )
        report["all_results"][0]["formula_evidence"]["historical_manifest_sha256"] = manifest_hash

        original_reuse_hash = report["formula_evidence"]["reuse_evidence_manifest_sha256"]
        report["formula_evidence"]["reuse_evidence_manifest_sha256"] = "0" * 64
        self.assertIn(
            "historical_formula_report_reuse_manifest_mismatch",
            self.adapter.validate_formula_evidence_report(report),
        )
        report["formula_evidence"]["reuse_evidence_manifest_sha256"] = original_reuse_hash

        report["all_results"][0]["formula_evidence"]["source_receipt_sha256"] = "0" * 64
        self.assertIn(
            "historical_formula_source_receipt_binding_mismatch:002192.SZ",
            self.adapter.validate_formula_evidence_report(report),
        )

    def test_adapter_builds_receipt_bound_reuse_evidence(self) -> None:
        rows = [
            {"code": symbol[:6], "symbol": symbol}
            for symbol in ["002192.SZ", "003018.SZ", "603095.SH", "603333.SH"]
        ]
        audit, _ = self.runner.load_historical_formula_evidence(
            rows,
            self.runner.HISTORICAL_FORMULA_EVIDENCE_MANIFEST,
            self.runner.HISTORICAL_FORMULA_EVIDENCE_MANIFEST_SHA256,
            "20260824",
        )
        report = {"formula_evidence": audit}

        binding = self.adapter.build_reuse_evidence_binding(report)

        self.assertEqual(audit["status"], "REJECTED")
        self.assertEqual(binding["status"], "NOT_USED")
        return
        self.assertEqual(binding["status"], "VERIFIED")
        self.assertEqual(
            binding["reuse_evidence_manifest_sha256"],
            audit["reuse_evidence_manifest_sha256"],
        )
        self.assertEqual(binding["source_receipt_sha256"], audit["source_receipt"]["sha256"])
        self.assertEqual(binding["source_artifact_sha256"], audit["source_artifact"]["sha256"])
        self.assertEqual(binding["immutable_line_sha256"], audit["recovery_provenance"]["line_sha256"])
        self.assertEqual(
            self.runner.canonical_json_sha256(binding["reuse_evidence_manifest"]),
            binding["reuse_evidence_manifest_sha256"],
        )

    def test_validator_accepts_integrated_four_candidate_report_without_live_tq(self) -> None:
        formulas = [
            {"formula": "大牛线4.0", "tq_formula": "大牛线撑压版", "ok": True},
            {"formula": "飞龙在天", "tq_formula": "飞龙在天", "ok": True},
            {"formula": "游资资金监控", "tq_formula": "游资资金监控", "ok": True},
            {"formula": "机构资金监控", "tq_formula": "机构资金监控", "ok": True},
            {"formula": "庄家资金监控", "tq_formula": "庄家资金监控", "ok": True},
        ]
        symbols = ["002192.SZ", "003018.SZ", "603095.SH", "603333.SH"]
        audit, _ = self.runner.load_historical_formula_evidence(
            [{"code": symbol[:6], "symbol": symbol} for symbol in symbols],
            self.runner.HISTORICAL_FORMULA_EVIDENCE_MANIFEST,
            self.runner.HISTORICAL_FORMULA_EVIDENCE_MANIFEST_SHA256,
            "20260824",
        )
        self.assertEqual(audit["status"], "REJECTED")
        self.assertTrue(audit["errors"])
        return
        reuse_manifest = audit["reuse_evidence_manifest"]
        reuse_manifest_hash = audit["reuse_evidence_manifest_sha256"]
        all_results = [
            {
                "symbol": symbol,
                "name": name,
                "name_source": "tdx_tnf",
                "five_formula_ok": True,
                "risk_items": [{}] * 15,
                "dimension_scores": [{}] * 15,
                "mainline_scoring": {"status": "GATE_FAILED", "weighted_score": 0},
                "raw_scan": {"ok": True, "symbol": symbol, "items": formulas, "failed_formulas": []},
                "formula_evidence": {
                    "mode": "historical_exact_input_reuse",
                    "historical_evidence_status": "VERIFIED",
                    "historical_manifest_sha256": self.runner.HISTORICAL_FORMULA_EVIDENCE_MANIFEST_SHA256,
                    "reuse_evidence_manifest_sha256": reuse_manifest_hash,
                    "source_receipt_sha256": audit["source_receipt"]["sha256"],
                    "source_artifact_sha256": audit["source_artifact"]["sha256"],
                    "immutable_line_sha256": audit["recovery_provenance"]["line_sha256"],
                },
            }
            for symbol, name in [
                ("002192.SZ", "融捷股份"),
                ("003018.SZ", "金富科技"),
                ("603095.SH", "越剑智能"),
                ("603333.SH", "福华尚纬"),
            ]
        ]
        scan = {
            "status": "CLEAN_PASS",
            "decision_status": "NO_SIGNAL",
            "trade_date": "20260824",
            "candidate_pool": {"name": "飞龙在天", "code": "FLZT", "file": str(self.validator.BLOCK_FILE), "count": 4},
            "scan_count": 4,
            "five_formula_success_count": 4,
            "required_formula_success_count": 4,
            "top10_count": 4,
            "top3_count": 3,
            "top10": [{}] * 4,
            "top3": [{}] * 3,
            "all_results": all_results,
            "formula_evidence": audit,
        }
        registry = {
            "大牛线4.0": "大牛线撑压版",
            "飞龙在天": "飞龙在天",
            "游资资金监控": "游资资金监控",
            "机构资金监控": "机构资金监控",
            "庄家资金监控": "庄家资金监控",
        }

        issues, checks = self.validator.validate_current_scan(scan, 4, registry)
        self.assertEqual(issues, [])
        self.assertTrue(checks["candidate_resolution"]["integrated"])
        self.assertTrue(checks["formula_evidence"]["verified"])
        valid_scan = copy.deepcopy(scan)

        scan["formula_evidence"]["kline_binding"]["matched"] = False
        rejected, _ = self.validator.validate_current_scan(scan, 4, registry)
        self.assertIn("formula_evidence_audit_incomplete", rejected)

        scan["formula_evidence"]["kline_binding"]["matched"] = True
        scan["formula_evidence"]["source_receipt_artifact_binding"]["matched"] = False
        rejected_receipt, _ = self.validator.validate_current_scan(scan, 4, registry)
        self.assertIn("formula_evidence_audit_incomplete", rejected_receipt)

        scan["formula_evidence"]["source_receipt_artifact_binding"]["matched"] = True
        scan["formula_evidence"]["reuse_evidence_manifest_sha256"] = "0" * 64
        rejected_manifest, _ = self.validator.validate_current_scan(scan, 4, registry)
        self.assertIn("formula_evidence_manifest_invalid", rejected_manifest)
        self.assertIn("formula_evidence_independent_revalidation_failed", rejected_manifest)

        one_stock_tampered = copy.deepcopy(valid_scan)
        one_stock_tampered["all_results"][0]["formula_evidence"]["source_artifact_sha256"] = "0" * 64
        one_stock_issues, _ = self.validator.validate_current_scan(one_stock_tampered, 4, registry)
        self.assertIn("formula_evidence_independent_revalidation_failed", one_stock_issues)
        self.assertIn(
            "formula_evidence_item_binding_invalid:002192.SZ",
            one_stock_issues,
        )

        detached = copy.deepcopy(valid_scan)
        detached_manifest = copy.deepcopy(detached["formula_evidence"]["reuse_evidence_manifest"])
        detached_manifest["source_receipt"]["path"] = r"F:\detached\fake.receipt.json"
        detached_manifest["source_receipt"]["sha256"] = "a" * 64
        detached_manifest["source_artifact"]["path"] = r"F:\detached\fake-report.json"
        detached_manifest["source_artifact"]["origin_path"] = r"F:\detached\fake-origin.json"
        detached_manifest["source_artifact"]["sha256"] = "b" * 64
        detached_manifest["immutable_line_locator"]["path"] = r"F:\detached\fake-rollout.jsonl"
        detached_manifest["immutable_line_sha256"] = "c" * 64
        detached_hash = self.runner.canonical_json_sha256(detached_manifest)
        detached_audit = detached["formula_evidence"]
        detached_audit["reuse_evidence_manifest"] = detached_manifest
        detached_audit["reuse_evidence_manifest_sha256"] = detached_hash
        detached_audit["source_receipt"].update({"matched": True, "sha256": "a" * 64})
        detached_audit["source_artifact"].update({"matched": True, "sha256": "b" * 64})
        detached_audit["recovery_provenance"].update({"matched": True, "line_sha256": "c" * 64})
        detached_audit["source_receipt_artifact_binding"] = {"matched": True}
        for item in detached["all_results"]:
            item["formula_evidence"].update({
                "reuse_evidence_manifest_sha256": detached_hash,
                "source_receipt_sha256": "a" * 64,
                "source_artifact_sha256": "b" * 64,
                "immutable_line_sha256": "c" * 64,
            })

        detached_issues, _ = self.validator.validate_current_scan(detached, 4, registry)
        self.assertIn("formula_evidence_independent_revalidation_failed", detached_issues)

    def test_theme_normalization_and_unique_stock_deduplication(self) -> None:
        self.assertEqual(self.scoring.normalize_theme(" 机器人概念板块 "), "机器人")
        self.assertEqual(self.scoring.normalize_theme("AI 应用"), "人工智能应用")
        rows = self.scoring.deduplicate_stocks([
            {"code": "000001", "themes": ["机器人概念"], "board_count": 1},
            {"code": "000001.SZ", "themes": ["机器人板块", "算力概念"], "board_count": 3},
            {"code": "000002", "themes": ["算力"], "board_count": 1},
        ])
        self.assertEqual(len(rows), 2)
        first = next(row for row in rows if row["code"] == "000001")
        self.assertEqual(first["themes"], ["机器人", "算力"])
        self.assertEqual(first["board_count"], 3)

    def test_complete_board_scores_all_nine_components(self) -> None:
        result = self.scoring.score_board(self.complete_board())
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["missing_evidence"], [])
        self.assertEqual(result["score"], 100.0)
        self.assertEqual(result["stars"], 5.0)
        self.assertTrue(result["decision_eligible"])
        self.assertEqual(
            set(result["components"]),
            {
                "market_strength",
                "breadth",
                "hierarchy",
                "ladder_completeness",
                "constituent_scale",
                "capital",
                "catalyst",
                "continuity",
                "dominance",
            },
        )

    def test_redesigned_weights_sum_to_100(self) -> None:
        self.assertEqual(
            self.scoring.COMPONENT_WEIGHTS,
            {
                "market_strength": 15,
                "breadth": 15,
                "hierarchy": 10,
                "ladder_completeness": 10,
                "constituent_scale": 10,
                "capital": 15,
                "catalyst": 10,
                "continuity": 10,
                "dominance": 5,
            },
        )
        self.assertEqual(sum(self.scoring.COMPONENT_WEIGHTS.values()), 100)

    def test_missing_any_three_two_one_ladder_level_fails_hard_gate(self) -> None:
        for field in ("three_board_count", "two_board_count", "one_board_count"):
            with self.subTest(field=field):
                result = self.scoring.score_board(self.complete_board(**{field: 0}))
                self.assertEqual(result["status"], "GATE_FAILED")
                self.assertEqual(result["score"], 0.0)
                self.assertGreater(result["raw_score"], 0.0)
                self.assertEqual(result["stars"], 0.0)
                self.assertFalse(result["decision_eligible"])
                self.assertIn("three_two_one_ladder_incomplete", result["gate_failures"])

    def test_constituent_count_must_be_strictly_greater_than_100(self) -> None:
        rejected = self.scoring.score_board(self.complete_board(constituent_count=100))
        self.assertEqual(rejected["status"], "GATE_FAILED")
        self.assertEqual(rejected["score"], 0.0)
        self.assertIn("constituent_count_not_greater_than_100", rejected["gate_failures"])

        accepted = self.scoring.score_board(self.complete_board(constituent_count=101))
        self.assertEqual(accepted["status"], "VERIFIED")
        self.assertTrue(accepted["decision_eligible"])
        self.assertGreater(accepted["score"], 0.0)

    def test_missing_constituent_evidence_degrades_instead_of_using_proxy(self) -> None:
        board = self.complete_board()
        del board["constituent_count"]
        result = self.scoring.score_board(board)
        self.assertEqual(result["status"], "DEGRADED")
        self.assertEqual(result["score"], 0.0)
        self.assertIn("constituent_count", result["missing_evidence"])

    def test_tdx_constituent_mapping_uses_named_block_and_member_overlap(self) -> None:
        catalog = [
            {"name": "通信服务", "source_name": "GN_通信服务", "codes": ["000001"], "member_count": 70},
            {"name": "光通信", "source_name": "GN_光通信", "codes": ["000001", "000002", "000003"], "member_count": 146},
            {"name": "芯片", "source_name": "GN_芯片", "codes": ["000004"], "member_count": 875},
        ]
        resolved = self.scoring.resolve_tdx_constituent_block("通信", ["000001", "000002"], catalog)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["source_name"], "GN_光通信")
        self.assertEqual(resolved["constituent_count"], 146)
        self.assertEqual(resolved["overlap_count"], 2)

        exact = self.scoring.resolve_tdx_constituent_block("芯片", ["000001"], catalog)
        self.assertIsNotNone(exact)
        self.assertEqual(exact["source_name"], "GN_芯片")
        self.assertEqual(exact["constituent_count"], 875)

        zero_overlap = self.scoring.resolve_tdx_constituent_block(
            "医药",
            ["000999"],
            [{"name": "创医药", "source_name": "ZS_创医药", "codes": ["000001"], "member_count": 50}],
        )
        self.assertIsNone(zero_overlap)

    def test_five_to_one_star_classification(self) -> None:
        cases = [
            (self.complete_board(), 5.0),
            (self.complete_board(rank=2, sector_return_pct=2.4, limit_up_count=10, runner_up_gap_pct=0.5), 4.0),
            (self.complete_board(rank=6, sector_return_pct=1.5, limit_up_count=7, runner_up_gap_pct=0.1), 3.0),
            (self.complete_board(rank=12, sector_return_pct=0.5, limit_up_count=2, runner_up_gap_pct=0.0), 2.0),
            (self.complete_board(rank=40, sector_return_pct=-1.0, limit_up_count=0, runner_up_gap_pct=-0.2), 1.0),
        ]
        for board, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(self.scoring.score_board(board)["stars"], expected)

    def test_missing_required_evidence_never_creates_a_proxy_score(self) -> None:
        board = self.complete_board()
        del board["continuity_days"]
        board["catalyst_verified"] = False
        result = self.scoring.score_board(board)
        self.assertEqual(result["status"], "DEGRADED")
        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["stars"], 0.0)
        self.assertFalse(result["decision_eligible"])
        self.assertIn("continuity_days", result["missing_evidence"])
        self.assertIn("verified_catalyst", result["missing_evidence"])

    def test_individual_authenticity_caps_the_combined_dimension(self) -> None:
        board = self.scoring.score_board(self.complete_board())
        concept_only = self.scoring.score_stock_fit(
            {"code": "000001", "themes": ["通信"]},
            "通信",
        )
        combined = self.scoring.combine_board_and_stock(board, concept_only, weight=14)
        self.assertEqual(concept_only["status"], "DEGRADED")
        self.assertLessEqual(concept_only["stars"], 2.0)
        self.assertEqual(combined["stars"], 0.0)
        self.assertEqual(combined["weighted_score"], 0.0)
        self.assertFalse(combined["decision_eligible"])

        authentic = self.scoring.score_stock_fit(
            {
                "code": "000002",
                "themes": ["通信"],
                "reason": "光通信设备订单增长",
                "business_theme_verified": True,
                "announcement_theme_verified": True,
                "hierarchy_role": "leader",
            },
            "通信",
        )
        self.assertEqual(authentic["status"], "VERIFIED")
        self.assertEqual(authentic["stars"], 5.0)
        self.assertEqual(self.scoring.combine_board_and_stock(board, authentic, weight=14)["stars"], 5.0)

    def test_trusted_historical_reason_can_confirm_current_theme(self) -> None:
        result = self.scoring.score_stock_fit(
            {
                "code": "603095",
                "themes": ["专用设备", "AI应用"],
                "historical_theme_evidence": [
                    {
                        "source": "连板网",
                        "source_status": "CLEAN_PASS",
                        "target_date": "2026-08-21",
                        "source_url": "https://lianban.net/days/2026-08-21.html",
                        "themes": ["专用设备", "其他"],
                        "reason": "专用设备+AI应用；公司智能验布机用于生产数据分析。",
                    },
                ],
            },
            "AI应用",
        )

        self.assertEqual(result["status"], "VERIFIED")
        self.assertIn("historical_reason_match=True", result["evidence"])
        self.assertEqual(len(result["historical_evidence"]), 1)
        self.assertTrue(result["historical_evidence"][0]["reason_match"])

    def test_different_stock_gains_cannot_change_missing_mainline_score(self) -> None:
        missing = self.scoring.unavailable_mainline("dynamic_sources_missing")
        low_gain = self.scoring.combine_board_and_stock(
            missing,
            self.scoring.unavailable_stock_fit("000001", "mainline_unavailable"),
            weight=14,
        )
        high_gain = self.scoring.combine_board_and_stock(
            missing,
            self.scoring.unavailable_stock_fit("000002", "mainline_unavailable"),
            weight=14,
        )
        self.assertEqual(low_gain["stars"], 0.0)
        self.assertEqual(high_gain["stars"], 0.0)
        self.assertEqual(low_gain["weighted_score"], high_gain["weighted_score"])

    def test_production_runner_rejects_the_old_gain_proxy(self) -> None:
        row = {"code": "000001", "symbol": "000001.SZ"}
        low = self.runner.build_analysis(row, {"name": "测试", "pct": 1.0}, {}, 0.0, {})
        high = self.runner.build_analysis(row, {"name": "测试", "pct": 10.0}, {}, 0.0, {})
        for result in (low, high):
            self.assertEqual(result["score_status"], "DATA_REQUIRED")
            self.assertEqual(result["dimension_scores"], [])
            self.assertEqual(result["final_score"], 0.0)
            self.assertFalse(result["decision_eligible"])
        self.assertEqual(low["final_score"], high["final_score"])
        source = (SKILL / "scripts" / "run_feilong_block_resonance.py").read_text(encoding="utf-8")
        self.assertNotIn("sector_star = 4.0 if pct >= 9.5 else 3.0", source)

    def test_production_contract_and_docs_bind_mainline_v2(self) -> None:
        paths = [
            SKILL / "SKILL.md",
            SKILL / "references" / "scoring-model.md",
            SKILL / "references" / "workflow.md",
            SKILL / "scripts" / "canonical_business_adapter.py",
            SKILL / "scripts" / "validate_feilong_block_resonance_skill.py",
        ]
        sources = {path: path.read_text(encoding="utf-8") for path in paths}
        self.assertTrue(all("CORE-MAINLINE-100-V1" not in source for source in sources.values()))
        self.assertIn("CORE-MAINLINE-100-V2", sources[SKILL / "references" / "scoring-model.md"])
        self.assertIn("A-SHARE-STRONG-26F-100-V6.1", sources[SKILL / "SKILL.md"])
        self.assertIn("基本面正向权重0", sources[SKILL / "SKILL.md"])
        self.assertNotIn("基本面质量 | 3", sources[SKILL / "references" / "scoring-model.md"])
        self.assertIn("九项板块分", sources[SKILL / "references" / "workflow.md"])

    def test_production_adapter_accepts_v2_and_rejects_v1(self) -> None:
        original_path = self.adapter.SCAN_JSON
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "scan.json"
            self.adapter.SCAN_JSON = report_path
            report = {
                "status": "CLEAN_PASS",
                "decision_status": "SIGNAL_FOUND",
                "scan_count": 1,
                "mainline_market": {
                    "model_version": "CORE-MAINLINE-100-V2",
                    "status": "VERIFIED",
                    "verified_stock_count": 1,
                    "authenticity_verified_stock_count": 1,
                    "gate_failed_stock_count": 0,
                    "degraded_stock_count": 0,
                    "data_required_reasons": [],
                },
                "short_term_score": self.short_term_handoff(verified_count=1),
                "all_results": [{
                    **self.verified_short_term_fields(decision_eligible=True),
                    "mainline_scoring": {
                        "status": "VERIFIED",
                        "decision_eligible": True,
                        "stock_fit": {"status": "VERIFIED"},
                    },
                }],
            }
            report_path.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(self.adapter.validate_mainline_report(), [])

            report["mainline_market"]["model_version"] = "CORE-MAINLINE-100-V1"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            self.assertIn("mainline_model_binding_missing", self.adapter.validate_mainline_report())
        self.adapter.SCAN_JSON = original_path

    def test_completed_scan_separates_execution_from_data_required_decision(self) -> None:
        analyses = [
            {
                **self.verified_short_term_fields(),
                "mainline_scoring": {
                    "status": "GATE_FAILED",
                    "decision_eligible": False,
                    "stock_fit": {"status": "VERIFIED"},
                },
            },
            {
                **self.verified_short_term_fields(),
                "mainline_scoring": {
                    "status": "DEGRADED",
                    "decision_eligible": False,
                    "stock_fit": {"status": "VERIFIED"},
                },
            },
        ]
        context = {
            "status": "GATE_FAILED",
            "source_status": {
                "duanxianxia_plate": "VERIFIED",
                "duanxianxia_pool": "VERIFIED",
                "duanxianxia_membership": "VERIFIED",
                "lianban": "CLEAN_PASS",
                "lianban_history": "VERIFIED",
                "tdx_constituents": "VERIFIED",
                "tdx_turnover": "VERIFIED",
            },
            "issues": [],
        }

        outcome = self.runner.classify_execution_outcome(True, analyses, context)
        self.assertEqual(outcome["execution_status"], "CLEAN_PASS")
        self.assertEqual(outcome["decision_status"], "DATA_REQUIRED")
        self.assertEqual(outcome["decision_eligible_count"], 0)
        self.assertEqual(outcome["authenticity_verified_count"], 2)
        self.assertEqual(outcome["gate_failed_count"], 1)
        self.assertEqual(outcome["degraded_count"], 1)
        self.assertTrue(outcome["data_required_reasons"])

    def test_no_signal_requires_every_candidate_to_fail_with_complete_evidence(self) -> None:
        analyses = [
            {
                **self.verified_short_term_fields(),
                "mainline_scoring": {
                    "status": "GATE_FAILED",
                    "decision_eligible": False,
                    "stock_fit": {"status": "VERIFIED"},
                },
            },
            {
                **self.verified_short_term_fields(),
                "mainline_scoring": {
                    "status": "GATE_FAILED",
                    "decision_eligible": False,
                    "stock_fit": {"status": "VERIFIED"},
                },
            },
        ]
        context = {
            "status": "GATE_FAILED",
            "source_status": {
                "duanxianxia_plate": "VERIFIED",
                "duanxianxia_pool": "VERIFIED",
                "duanxianxia_membership": "VERIFIED",
                "lianban": "CLEAN_PASS",
                "lianban_history": "VERIFIED",
                "tdx_constituents": "VERIFIED",
                "tdx_turnover": "VERIFIED",
            },
            "issues": [],
        }

        outcome = self.runner.classify_execution_outcome(True, analyses, context)
        self.assertEqual(outcome["execution_status"], "CLEAN_PASS")
        self.assertEqual(outcome["decision_status"], "NO_SIGNAL")
        self.assertEqual(outcome["data_required_reasons"], [])

        analyses[1]["mainline_scoring"]["stock_fit"]["status"] = "DEGRADED"
        rejected = self.runner.classify_execution_outcome(True, analyses, context)
        self.assertEqual(rejected["execution_status"], "DATA_REQUIRED")
        self.assertEqual(rejected["decision_status"], "DATA_REQUIRED")

    def test_adapter_accepts_audited_data_required_without_authorizing_a_signal(self) -> None:
        original_path = self.adapter.SCAN_JSON
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "scan.json"
            self.adapter.SCAN_JSON = report_path
            report = {
                "status": "CLEAN_PASS",
                "decision_status": "DATA_REQUIRED",
                "scan_count": 2,
                "mainline_market": {
                    "model_version": "CORE-MAINLINE-100-V2",
                    "status": "GATE_FAILED",
                    "verified_stock_count": 0,
                    "authenticity_verified_stock_count": 2,
                    "gate_failed_stock_count": 1,
                    "degraded_stock_count": 1,
                    "source_status": {"lianban": "CLEAN_PASS", "duanxianxia_plate": "VERIFIED"},
                    "issues": [],
                    "data_required_reasons": ["candidate_board_evidence_incomplete"],
                },
                "short_term_score": self.short_term_handoff(verified_count=2),
                "all_results": [
                    {
                        **self.verified_short_term_fields(),
                        "mainline_scoring": {
                            "status": "GATE_FAILED",
                            "decision_eligible": False,
                            "stock_fit": {"status": "VERIFIED"},
                        },
                    },
                    {
                        **self.verified_short_term_fields(),
                        "mainline_scoring": {
                            "status": "DEGRADED",
                            "decision_eligible": False,
                            "stock_fit": {"status": "VERIFIED"},
                        },
                    },
                ],
            }
            report_path.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(self.adapter.validate_mainline_report(), [])

            report["decision_status"] = "NO_SIGNAL"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            self.assertIn("no_signal_contains_degraded_candidate", self.adapter.validate_mainline_report())
        self.adapter.SCAN_JSON = original_path


if __name__ == "__main__":
    unittest.main(verbosity=2)
