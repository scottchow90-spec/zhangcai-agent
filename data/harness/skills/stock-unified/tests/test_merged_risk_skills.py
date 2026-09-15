from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT.parent
CATALOG_PATH = ROOT / "references" / "stock_skill_ids.json"
CONTRACTS_PATH = ROOT / "references" / "stock_execution_contracts.json"
RUNTIME_PATH = Path(r"D:\C盘转移\日志\codex\scripts\stock_canonical_runtime.py")
OWNER_ID = "risk-mine-clearance"
RETIRED_ID = "risk-warning"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNTIME = load_module("stock_canonical_runtime_risk_merge_test", RUNTIME_PATH)


class MergedRiskSkillTests(unittest.TestCase):
    def route(self, query: str) -> list[str]:
        return RUNTIME.route_stock_query(
            query,
            catalog_path=CATALOG_PATH,
            skills_root=SKILLS_ROOT,
        )["skill_ids"]

    def test_all_risk_names_route_to_one_integrated_owner(self) -> None:
        for query in (
            "风险排雷技能",
            "风险排雷",
            "个股风险排雷",
            "暴雷前排查",
            "风险预警",
            "$risk-warning",
        ):
            with self.subTest(query=query):
                self.assertEqual(self.route(query), [OWNER_ID])

        self.assertEqual(
            self.route("请用风险排雷和风险预警检查这只股票"),
            [OWNER_ID],
        )

    def test_retired_risk_skill_is_not_an_independent_authority(self) -> None:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        contracts = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))
        self.assertNotIn(RETIRED_ID, catalog["skills"])
        self.assertNotIn(RETIRED_ID, catalog["workflow_names"])
        self.assertNotIn(
            RETIRED_ID,
            {item["skill_id"] for item in contracts["contracts"]},
        )
        self.assertFalse((SKILLS_ROOT / RETIRED_ID).exists())

    def test_integrated_skill_uses_the_requested_chinese_name(self) -> None:
        owner = SKILLS_ROOT / OWNER_ID
        skill_text = (owner / "SKILL.md").read_text(encoding="utf-8-sig")
        agent_text = (owner / "agents" / "openai.yaml").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("# 风险排雷技能", skill_text)
        self.assertIn('display_name: "风险排雷技能"', agent_text)
        self.assertIn("风险预警", skill_text)
        self.assertIn("解禁减持", skill_text)
        self.assertIn("市场与技术风险", skill_text)

    def test_integrated_entry_has_no_fixed_historical_date(self) -> None:
        entry = (
            SKILLS_ROOT / OWNER_ID / "scripts" / "audit_risk_scan.py"
        ).read_text(encoding="utf-8-sig")
        adapter = (
            SKILLS_ROOT / OWNER_ID / "scripts" / "canonical_business_adapter.py"
        ).read_text(encoding="utf-8-sig")
        self.assertNotIn("2026-07-21", entry)
        self.assertIn("--output-dir", entry)
        self.assertIn('"--output-dir", str(run_dir)', adapter)

    def test_integrated_skill_uses_current_delivery_authorization(self) -> None:
        owner = SKILLS_ROOT / OWNER_ID
        skill_text = (owner / "SKILL.md").read_text(encoding="utf-8-sig")
        self.assertIn("complete --artifact-relative", skill_text)
        self.assertIn("authorize --receipt", skill_text)
        self.assertNotIn("stock-delivery-risk-gate", skill_text)
        self.assertFalse((owner / "scripts" / "risk_delivery_gate.py").exists())

    def test_market_warning_overlay_preserves_retired_business_signal(self) -> None:
        path = SKILLS_ROOT / OWNER_ID / "scripts" / "risk_warning_overlay.py"
        self.assertTrue(path.is_file())
        overlay = load_module("integrated_risk_warning_overlay_test", path)
        report = overlay.build_market_warning(
            {
                "上证指数": {"change_pct": -2.5},
                "深证成指": {"change_pct": -1.3},
                "创业板指": {"change_pct": 0.2},
            },
            limit_up_count=20,
            data_source="synthetic-test",
            generated_at="2026-08-17T12:00:00+08:00",
        )
        self.assertEqual(report["schema"], "INTEGRATED_RISK_WARNING_V1")
        self.assertEqual(report["risk_level"], "HIGH")
        self.assertEqual(report["limit_up_count"], 20)
        self.assertGreaterEqual(len(report["warnings"]), 3)

    def test_market_warning_overlay_prefers_stable_local_tdx_snapshot(self) -> None:
        path = SKILLS_ROOT / OWNER_ID / "scripts" / "risk_warning_overlay.py"
        overlay = load_module("integrated_risk_warning_overlay_precedence_test", path)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            indexes = {}
            for offset, (name, code) in enumerate(
                (("上证指数", "000001"), ("深证成指", "399001"), ("创业板指", "399006"))
            ):
                day = root / f"{code}.day"
                previous = struct.pack("<IIIIIfII", 20260817, 1000, 1010, 990, 1000, 1.0, 1, 0)
                latest = struct.pack("<IIIIIfII", 20260818, 1010, 1020, 1000, 1010 + offset, 1.0, 1, 0)
                day.write_bytes(previous + latest)
                indexes[name] = (code, day)
            with mock.patch.object(overlay, "TDX_INDEXES", indexes), mock.patch.object(
                overlay.urllib.request,
                "urlopen",
            ) as urlopen:
                response = urlopen.return_value.__enter__.return_value
                response.read.return_value = json.dumps(
                    {"data": {"diff": [{"f14": "网络指数", "f12": "999999", "f2": 1, "f3": 9}]}}
                ).encode("utf-8")
                values, source = overlay.fetch_index_quotes()
                urlopen.assert_not_called()
        self.assertEqual(source, "本地通达信日线")
        self.assertEqual(set(values), set(indexes))

    def test_integrated_skill_builds_validated_receipt_bound_8k_poster(self) -> None:
        owner = SKILLS_ROOT / OWNER_ID
        builder = owner / "scripts" / "poster_builder.py"
        validator = owner / "scripts" / "poster_validator.py"
        template = owner / "POSTER_TEMPLATE.md"
        self.assertTrue(builder.is_file())
        self.assertTrue(validator.is_file())
        self.assertTrue(template.is_file())

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "risk-mine-clearance-8k.png"
            metadata = Path(temporary) / "poster_metadata.json"
            validation = Path(temporary) / "poster_validation.json"
            subprocess.run(
                [
                    sys.executable,
                    str(builder),
                    "--output",
                    str(output),
                    "--metadata",
                    str(metadata),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    str(validator),
                    "--input",
                    str(output),
                    "--metadata",
                    str(metadata),
                    "--output",
                    str(validation),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            with Image.open(output) as image:
                self.assertEqual(image.size, (7680, 4320))
            metadata_payload = json.loads(metadata.read_text(encoding="utf-8"))
            validation_payload = json.loads(validation.read_text(encoding="utf-8"))
            self.assertGreaterEqual(metadata_payload["minimum_source_font_px"], 96)
            self.assertGreaterEqual(metadata_payload["minimum_body_font_px"], 128)
            self.assertGreaterEqual(metadata_payload["minimum_primary_font_px"], 136)
            self.assertEqual(validation_payload["status"], "PASS")

        contracts = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))
        contract = next(
            item for item in contracts["contracts"] if item["skill_id"] == OWNER_ID
        )
        required = {item["path"] for item in contract["required_artifacts"]}
        bindings = set(contract["workflow_guard"]["required_bindings"])
        self.assertIn(r"{run_dir}\risk-mine-clearance-8k.png", required)
        self.assertIn(r"{run_dir}\poster_validation.json", required)
        self.assertIn("POSTER_TEMPLATE.md", bindings)
        self.assertIn("scripts/poster_builder.py", bindings)
        self.assertIn("scripts/poster_validator.py", bindings)

        integrated_entry = (owner / "scripts" / "audit_risk_scan.py").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("poster_builder.py", integrated_entry)
        self.assertIn("poster_validator.py", integrated_entry)
        self.assertIn("poster_validation.json", integrated_entry)


if __name__ == "__main__":
    unittest.main(verbosity=2)
