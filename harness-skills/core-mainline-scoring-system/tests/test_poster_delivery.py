from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SKILL = Path(__file__).resolve().parents[1]
ADAPTER = SKILL / "scripts" / "canonical_business_adapter.py"
RUNTIME_DIR = SKILL.parents[1] / "scripts"
if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))

import stock_canonical_runtime


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


class CoreMainlinePosterDeliveryTests(unittest.TestCase):
    def test_poster_mode_builds_validated_receipt_manifest(self) -> None:
        fixture = {
            "pre_scored_boards": [
                complete_board(),
                complete_board(
                    name="农业",
                    rank=2,
                    sector_return_pct=2.1,
                    limit_up_count=23,
                    three_board_count=0,
                    two_board_count=6,
                    one_board_count=21,
                    constituent_count=47,
                ),
            ]
        }
        lianban = {
            "status": "CLEAN_PASS",
            "source_name": "连板网",
            "license": "CC BY 4.0",
            "sources": {
                "page": {"url": "https://lianban.net/days/2026-08-18.html"},
                "open_data": {"url": "https://lianban.net/opendata/2026-08-18.json"},
            },
            "market": {
                "limit_up": 79,
                "limit_down": 5,
                "consecutive": 18,
                "max_board": 4,
                "seal_rate": 77.5,
                "advancers": 2121,
                "decliners": 3292,
                "emotion_stage": "降温期",
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "run"
            fixture_path = root / "fixture.json"
            lianban_path = root / "lianban-daily.json"
            fixture_path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
            lianban_path.write_text(json.dumps(lianban, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER),
                    "--run-dir",
                    str(run_dir),
                    "--input-bundle",
                    str(fixture_path),
                    "--poster",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={
                    **os.environ,
                    "CODEX_STOCK_CANONICAL_EXECUTION": "1",
                    "CODEX_LIANBAN_STATUS": "CLEAN_PASS",
                    "CODEX_LIANBAN_SNAPSHOT": str(lianban_path),
                    "CODEX_LIANBAN_SOURCE_URL": lianban["sources"]["page"]["url"],
                    "CODEX_LIANBAN_OPEN_DATA_URL": lianban["sources"]["open_data"]["url"],
                    "CODEX_LIANBAN_ATTRIBUTION": "连板网",
                },
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            business = json.loads(completed.stdout)
            self.assertEqual(business["status"], "CLEAN_PASS")
            self.assertTrue(stock_canonical_runtime.manifest_validation_is_clean(business))

            poster = run_dir / "deliverables" / "核心主线评分8K海报.png"
            preview = run_dir / "deliverables" / "核心主线评分8K海报-preview-1920x1080.png"
            metadata = json.loads((run_dir / "poster-metadata.json").read_text(encoding="utf-8"))
            validation = json.loads((run_dir / "poster-validation.json").read_text(encoding="utf-8"))
            light_gate = json.loads((run_dir / "poster-light-background-gate.json").read_text(encoding="utf-8"))
            manifest = json.loads((run_dir / "poster-delivery-manifest.json").read_text(encoding="utf-8"))

            with Image.open(poster) as image:
                self.assertEqual(image.size, (7680, 4320))
            with Image.open(preview) as image:
                self.assertEqual(image.size, (1920, 1080))
            self.assertEqual(validation["status"], "PASS")
            self.assertEqual(light_gate["status"], "PASS")
            self.assertEqual(manifest["status"], "CLEAN_PASS")
            self.assertEqual(manifest["errors"], [])
            self.assertEqual(metadata["missing_glyphs"], [])
            self.assertGreaterEqual(min(run["font_px"] for run in metadata["text_runs"]), 96)
            self.assertFalse(any("..." in run["text"] for run in metadata["text_runs"]))
            declared = next(item for item in manifest["artifacts"] if Path(item["path"]) == poster)
            self.assertEqual(declared["sha256"], hashlib.sha256(poster.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main(verbosity=2)
