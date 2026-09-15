from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import json
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "stock-unified.py"
SPEC = importlib.util.spec_from_file_location(
    "stock_unified_selftest_topology_test",
    SCRIPT,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def clean_child(skill_id: str) -> dict:
    return {
        "returncode": 0,
        "stdout": json.dumps(
            {
                "runtime": "stock-canonical-runtime-v3",
                "skill_id": skill_id,
                "status": "CLEAN_PASS",
                "errors": [],
            },
            ensure_ascii=False,
        ),
        "stderr": "",
        "timed_out": False,
    }


class SelftestTopologyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skills = [
            "alpha",
            "feilong-strategy",
            "other",
            "big-bull-analysis-scoring-system",
        ]

    def test_catalog_order_is_preserved_and_only_selftest_is_executed(self) -> None:
        def fake_child(command: list[str], cwd: Path, timeout: int) -> dict:
            del timeout
            return clean_child(cwd.name)

        with mock.patch.object(
            MODULE,
            "run_child",
            side_effect=fake_child,
        ) as run_mock:
            rows = MODULE.execute_all(self.skills, timeout=30)

        self.assertEqual([row["skill_id"] for row in rows], self.skills)
        self.assertEqual(
            [call.args[0] for call in run_mock.call_args_list],
            [
                [
                    sys.executable,
                    str(MODULE.SKILLS_ROOT / skill_id / "scripts" / "codex_entry.py"),
                    "selftest",
                ]
                for skill_id in self.skills
            ],
        )
        self.assertTrue(all(row["selftest_pass"] for row in rows))
        for call in run_mock.call_args_list:
            command = call.args[0]
            self.assertEqual(command[-1], "selftest")
            self.assertNotIn("run", command)

    def test_selftests_use_bounded_parallelism_and_preserve_result_order(self) -> None:
        active = 0
        peak_active = 0
        mutex = threading.Lock()

        def fake_selftest(skill_id: str, timeout: int) -> dict:
            nonlocal active, peak_active
            del timeout
            with mutex:
                active += 1
                peak_active = max(peak_active, active)
            time.sleep(0.03)
            with mutex:
                active -= 1
            return {"skill_id": skill_id, "selftest_pass": True}

        with mock.patch.object(
            MODULE,
            "run_one_selftest",
            side_effect=fake_selftest,
        ):
            rows = MODULE.execute_all(
                self.skills,
                timeout=30,
                max_workers=4,
            )

        self.assertEqual([row["skill_id"] for row in rows], self.skills)
        self.assertGreaterEqual(peak_active, 2)
        self.assertLessEqual(peak_active, 4)

    def test_aggregate_has_no_runtime_dependency_or_probe_surface(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("stock_runtime_dependencies.json", source)
        self.assertNotIn("load_runtime_dependencies", source)
        self.assertNotIn("run_shared_dependency_probe", source)
        self.assertNotIn("ordered_skills", source)

    def test_selftest_payload_requires_identity_clean_status_and_empty_errors(self) -> None:
        cases = [
            (
                {"skill_id": "wrong", "status": "CLEAN_PASS", "errors": []},
                "selftest_skill_id_mismatch",
            ),
            (
                {
                    "skill_id": "alpha",
                    "status": "PROCEDURAL",
                    "errors": [],
                },
                "selftest_status_not_pass",
            ),
            (
                {
                    "skill_id": "alpha",
                    "status": "CLEAN_PASS",
                    "errors": ["bad"],
                },
                "selftest_errors_not_empty",
            ),
        ]
        for payload, expected in cases:
            with self.subTest(expected=expected):
                errors = MODULE.selftest_payload_errors("alpha", payload)
                self.assertIn(expected, errors)

    def test_mixed_or_malformed_stdout_is_rejected(self) -> None:
        valid = json.dumps(
            {
                "skill_id": "alpha",
                "status": "CLEAN_PASS",
                "errors": [],
            }
        )
        for stdout in (
            "",
            "not-json",
            f"progress\n{valid}",
            f"{valid}\n{valid}",
            "[]",
        ):
            with self.subTest(stdout=stdout):
                child = {
                    "returncode": 0,
                    "stdout": stdout,
                    "stderr": "",
                    "timed_out": False,
                }
                with mock.patch.object(MODULE, "run_child", return_value=child):
                    row = MODULE.run_one_selftest("alpha", timeout=30)
                self.assertFalse(row["selftest_pass"])
                self.assertIn("selftest_stdout_not_single_json_object", row["errors"])


if __name__ == "__main__":
    unittest.main()
