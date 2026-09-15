from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


HOME = Path(r"D:\C盘转移\日志\codex")
SKILLS = HOME / "skills"
CONTRACTS = SKILLS / "stock-unified" / "references" / "stock_execution_contracts.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def contract(skill_id: str) -> dict:
    payload = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    return next(row for row in payload["contracts"] if row["skill_id"] == skill_id)


class SharedEvidenceSetTests(unittest.TestCase):
    def test_batch_id_is_validated_before_runtime_path_use(self) -> None:
        module_path = HOME / "scripts" / "stock_evidence_set.py"
        evidence = load_module("stock_evidence_set_batch_id_test", module_path)
        with self.assertRaises(evidence.EvidenceSetError):
            evidence.validate_batch_id(r"..\escape")

    def test_evidence_set_rejects_cross_batch_date_and_hash_reuse(self) -> None:
        module_path = HOME / "scripts" / "stock_evidence_set.py"
        self.assertTrue(module_path.is_file(), "shared evidence-set module is missing")
        evidence = load_module("stock_evidence_set_optimization_test", module_path)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lianban = root / "lianban.json"
            duanxianxia = root / "duanxianxia.json"
            lianban.write_text('{"status":"CLEAN_PASS"}', encoding="utf-8")
            duanxianxia.write_text('{"status":"CLEAN_PASS"}', encoding="utf-8")
            manifest = root / "evidence-set.json"
            created = evidence.write_evidence_set(
                manifest,
                batch_id="batch-20260823-a",
                trading_date="2026-08-21",
                artifacts={"lianban_daily": lianban, "duanxianxia": duanxianxia},
            )
            loaded = evidence.load_evidence_set(
                manifest,
                expected_batch_id="batch-20260823-a",
                expected_trading_date="2026-08-21",
            )
            self.assertEqual(loaded["evidence_set_id"], created["evidence_set_id"])
            with self.assertRaises(evidence.EvidenceSetError):
                evidence.load_evidence_set(
                    manifest,
                    expected_batch_id="batch-20260823-b",
                    expected_trading_date="2026-08-21",
                )
            with self.assertRaises(evidence.EvidenceSetError):
                evidence.load_evidence_set(
                    manifest,
                    expected_batch_id="batch-20260823-a",
                    expected_trading_date="2026-08-22",
                )
            lianban.write_text('{"status":"BLOCKED"}', encoding="utf-8")
            with self.assertRaises(evidence.EvidenceSetError):
                evidence.load_evidence_set(
                    manifest,
                    expected_batch_id="batch-20260823-a",
                    expected_trading_date="2026-08-21",
                )

    def test_canonical_runtime_binds_evidence_set_to_receipt(self) -> None:
        source = (HOME / "scripts" / "stock_canonical_runtime.py").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("prepare_stock_evidence_set", source)
        self.assertIn('"evidence_set": evidence_set', source)
        self.assertIn("verify_receipt_evidence_set", source)

    def test_exact_lianban_source_rejects_shared_snapshot_for_other_date(self) -> None:
        runtime = load_module(
            "stock_canonical_runtime_lianban_date_test",
            HOME / "scripts" / "stock_canonical_runtime.py",
        )
        with tempfile.TemporaryDirectory() as temporary:
            snapshot_path = Path(temporary) / "lianban.json"
            snapshot_path.write_text(
                json.dumps(
                    {
                        "schema": "LIANBAN_DAILY_SNAPSHOT_V1",
                        "status": "CLEAN_PASS",
                        "target_date": "2026-08-21",
                        "sources": {
                            "page": {"url": "https://lianban.net/days/2026-08-21.html"},
                            "open_data": {
                                "url": "https://lianban.net/opendata/2026-08-21.json"
                            },
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            evidence_set = {
                "status": "CLEAN_PASS",
                "payload": {
                    "evidence_set_id": "sha256:test",
                    "trading_date": "2026-08-21",
                    "artifacts": [
                        {"id": "lianban_daily", "path": str(snapshot_path)}
                    ],
                },
            }
            shared = runtime._shared_lianban_daily_source(
                {"required": True, "date_mode": "exact"},
                evidence_set,
                "2026-08-20",
                None,
            )
            self.assertIsNone(shared)
            latest = runtime._shared_lianban_daily_source(
                {"required": True, "date_mode": "latest_available"},
                evidence_set,
                "2026-08-20",
                None,
            )
            self.assertEqual(latest["status"], "CLEAN_PASS")


class SubstantiveDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baimao = load_module(
            "baimao_adapter_optimization_test",
            SKILLS / "baimao-daily-intel-review" / "scripts" / "canonical_business_adapter.py",
        )
        cls.thinktank = load_module(
            "thinktank_adapter_optimization_test",
            SKILLS / "a-share-thinktank-brief" / "scripts" / "canonical_business_adapter.py",
        )
        cls.shortline = load_module(
            "shortline_adapter_optimization_test",
            SKILLS / "shortline-hotspot-mining" / "scripts" / "canonical_business_adapter.py",
        )

    def test_baimao_forwards_evidence_and_forces_canonical_output(self) -> None:
        run_dir = Path(r"C:\temp\baimao-run")
        command = self.baimao.business_command(
            run_dir, ["--evidence", r"C:\input\evidence.json", "--mode", "closing"]
        )
        self.assertIn("run", command)
        self.assertIn("--evidence", command)
        self.assertEqual(command[-2:], ["--output-dir", str(run_dir)])

    def test_thinktank_forwards_inputs_and_forces_canonical_output(self) -> None:
        run_dir = Path(r"C:\temp\thinktank-run")
        command = self.thinktank.business_command(
            run_dir,
            [
                "--thinktank-md",
                r"C:\input\thinktanks.md",
                "--brief-md",
                r"C:\input\brief.md",
            ],
        )
        self.assertIn("generate", command)
        self.assertIn("--thinktank-md", command)
        self.assertEqual(command[-2:], ["--out-dir", str(run_dir)])

    def test_explicit_input_workflows_are_documented(self) -> None:
        baimao = (SKILLS / "baimao-daily-intel-review" / "SKILL.md").read_text(
            encoding="utf-8-sig"
        )
        thinktank = (SKILLS / "a-share-thinktank-brief" / "SKILL.md").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("--evidence", baimao)
        self.assertIn("裸运行必须阻断", baimao)
        self.assertIn("--thinktank-md", thinktank)
        self.assertIn("--brief-md", thinktank)
        self.assertIn("裸运行必须阻断", thinktank)

    def test_thinktank_manifest_binds_layout_spec(self) -> None:
        layout = (
            SKILLS
            / "a-share-thinktank-brief"
            / "references"
            / "docx-layout-template.md"
        )
        self.assertTrue(layout.is_file())
        generator = load_module(
            "thinktank_generator_layout_test",
            SKILLS / "a-share-thinktank-brief" / "scripts" / "top_thinktank_brief.py",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            docx = root / "brief.docx"
            docx.write_bytes(b"PK-test-docx")
            manifest_path = generator.write_manifest(
                root,
                docx,
                {"status": "CLEAN_PASS"},
                "generate",
            )
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            binding = payload["layout_binding"]
            self.assertEqual(binding["path"], str(layout.resolve()))
            self.assertEqual(len(binding["sha256"]), 64)

    def test_shortline_manifest_binds_required_delivery_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in self.shortline.REQUIRED_DELIVERABLES:
                artifact = root / name
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text('{"status":"PASS"}', encoding="utf-8")
            payload = {
                "status": "CLEAN_PASS",
                "forecast_status": "VALIDATED_FORECAST",
                "snapshot_id": "snapshot-test",
                "resolved_trade_date": "2026-08-21",
                "errors": [],
            }
            manifest = self.shortline.build_business_artifact_manifest(root, payload)
            self.assertEqual(manifest["status"], "CLEAN_PASS")
            artifacts = {item["name"]: item for item in manifest["artifacts"]}
            self.assertEqual(set(artifacts), set(self.shortline.REQUIRED_DELIVERABLES))
            for name in self.shortline.REQUIRED_DELIVERABLES:
                self.assertEqual(artifacts[name]["path"], str((root / name).resolve()))
                self.assertEqual(len(artifacts[name]["sha256"]), 64)

    def test_contracts_require_explicit_inputs_and_real_manifests(self) -> None:
        for skill_id in ("baimao-daily-intel-review", "a-share-thinktank-brief"):
            with self.subTest(skill_id=skill_id):
                row = contract(skill_id)
                self.assertTrue(row["workflow_guard"]["requires_explicit_business_args"])
                required = {item["path"] for item in row["required_artifacts"]}
                self.assertIn(r"{run_dir}\business_artifact_manifest.json", required)
        shortline_required = {
            item["path"] for item in contract("shortline-hotspot-mining")["required_artifacts"]
        }
        self.assertIn(r"{run_dir}\business_artifact_manifest.json", shortline_required)

    def test_all_six_contracts_bind_shared_evidence_module(self) -> None:
        evidence_module = str((HOME / "scripts" / "stock_evidence_set.py").resolve())
        for skill_id in (
            "a-share-hotspot-sentiment-analysis",
            "baimao-daily-intel-review",
            "shortline-hotspot-mining",
            "a-share-short-term-market-sentiment",
            "a-share-thinktank-brief",
            "risk-mine-clearance",
        ):
            with self.subTest(skill_id=skill_id):
                bindings = {item["path"] for item in contract(skill_id)["business_bindings"]}
                self.assertIn(evidence_module, bindings)


class RiskSourceRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scan = load_module(
            "risk_scan_optimization_test",
            SKILLS / "risk-mine-clearance" / "scripts" / "a_share_risk_scan.py",
        )
        cls.validator = load_module(
            "risk_validator_optimization_test",
            SKILLS / "risk-mine-clearance" / "scripts" / "validate_risk_run.py",
        )

    def test_news_jsonp_parser_avoids_arrow_unicode_regex_failure(self) -> None:
        callback = "jQuery123"
        payload = {
            "result": {
                "cmsArticleWebOld": [
                    {
                        "date": "2026-08-21 10:00:00",
                        "mediaName": "测试媒体",
                        "code": "abc123",
                        "title": "<em>测试</em>新闻",
                        "content": "正文\u3000含空格",
                    }
                ]
            }
        }
        text = callback + "(" + json.dumps(payload, ensure_ascii=False) + ")"
        frame = self.scan.parse_eastmoney_news_jsonp(text, callback, "000001")
        self.assertEqual(frame.iloc[0]["新闻标题"], "测试新闻")
        self.assertNotIn("\u3000", frame.iloc[0]["新闻内容"])

    def test_non_trading_day_pledge_candidates_start_on_friday(self) -> None:
        candidates = self.scan.pledge_date_candidates("20260823", lookback_days=7)
        self.assertEqual(candidates[0], "20260821")
        self.assertNotIn("20260822", candidates)
        self.assertNotIn("20260823", candidates)

    def test_pledge_detail_no_longer_owns_45_second_tail(self) -> None:
        specs = {item.name: item for item in self.scan.base_source_specs(self.scan.date(2026, 8, 23))}
        self.assertLessEqual(specs["pledge_detail"].timeout_seconds, 12)

    def test_source_gate_requires_pledge_lawsuit_and_deep_news_domains(self) -> None:
        rows = [
            {"name": "notices", "status": "ok", "rows": "5"},
            {"name": "guarantees", "status": "ok", "rows": "10"},
            {"name": "lawsuits", "status": "failed", "rows": "0"},
            {"name": "pledge_ratio", "status": "failed", "rows": "0"},
            {"name": "eastmoney_comment", "status": "ok", "rows": "5000"},
            {"name": "xueqiu_tweet", "status": "ok", "rows": "5000"},
            {"name": "shcpe_enterprise_notices", "status": "ok", "rows": "1000"},
            {"name": "credit_gd_wage_arrears", "status": "ok", "rows": "50"},
            {"name": "credit_gd_court_defaulters_recent", "status": "ok", "rows": "50"},
            {"name": "news_000001", "status": "failed", "rows": "0"},
        ]
        result = self.validator.evaluate_source_health(rows)
        self.assertFalse(result["ok"])
        self.assertIn("lawsuit", result["failed_domains"])
        self.assertIn("pledge", result["failed_domains"])
        self.assertIn("deep_news", result["failed_domains"])

    def test_risk_contract_binds_substantive_outputs(self) -> None:
        required = {item["path"] for item in contract("risk-mine-clearance")["required_artifacts"]}
        for name in (
            "run_manifest.json",
            "source_health.csv",
            "risk_candidates.csv",
            "front_candidates.csv",
            "confirmed_risk_candidates.csv",
            "evidence.jsonl",
            "market_risk_warning.json",
            "integrated_risk_summary.json",
            "skill_validation.json",
        ):
            with self.subTest(name=name):
                self.assertIn("{run_dir}\\" + name, required)


class SentimentRedlineTests(unittest.TestCase):
    def test_delivery_sanitizer_frontloads_banned_stance_terms(self) -> None:
        module = load_module(
            "sentiment_redline_optimization_test",
            SKILLS
            / "a-share-hotspot-sentiment-analysis"
            / "components"
            / "a-share-sentiment-workflow"
            / "scripts"
            / "a-share-sentiment-workflow.py",
        )
        cleaned = module.sanitize_delivery_residue("多家机构看好该方向，另有观点看空高估值标的")
        self.assertNotIn("看好", cleaned)
        self.assertNotIn("看空", cleaned)
        self.assertFalse(module.report_banned_phrase_hits(cleaned))


if __name__ == "__main__":
    unittest.main(verbosity=2)
