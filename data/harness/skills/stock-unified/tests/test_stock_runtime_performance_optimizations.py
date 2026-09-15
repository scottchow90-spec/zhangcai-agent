from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HOME = Path(r"D:\C盘转移\日志\codex")
RUNTIME_PATH = HOME / "scripts" / "stock_canonical_runtime.py"
CONVERTIBLE_ENTRY = (
    HOME
    / "skills"
    / "convertible-bond-screening-strategy"
    / "scripts"
    / "codex_entry.py"
)


def load_runtime():
    spec = importlib.util.spec_from_file_location(
        "stock_runtime_performance_optimization_test",
        RUNTIME_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNTIME = load_runtime()


class StockRuntimePerformanceOptimizationTests(unittest.TestCase):
    def test_business_lock_is_sharded_by_workflow(self) -> None:
        first = RUNTIME.workflow_lock_path("a-share-15d-selection")
        second = RUNTIME.workflow_lock_path("technical-analysis")

        self.assertEqual(first, RUNTIME.workflow_lock_path("a-share-15d-selection"))
        self.assertNotEqual(first, second)
        self.assertEqual(first.parent, RUNTIME.STOCK_BUSINESS_LOCK_PATH.parent)

    def test_invalid_business_action_is_rejected_before_lock_wait(self) -> None:
        contract = {
            "workflow_guard": {
                "requires_explicit_business_args": False,
                "forbidden_business_actions": ["selftest"],
            },
            "timeout_seconds": 360,
        }
        entry = Path(r"D:\C盘转移\日志\codex\skills\example\scripts\codex_entry.py")
        with mock.patch.object(
            RUNTIME,
            "skill_context",
            return_value=(entry.parents[1], "example", contract),
        ), mock.patch.object(RUNTIME, "stock_business_lease") as lease_mock:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                returncode = RUNTIME.run(str(entry), ["selftest"])

        self.assertEqual(returncode, 2)
        lease_mock.assert_not_called()
        self.assertIn("non_business_action_forbidden:selftest", stderr.getvalue())

    def test_stable_contract_uses_one_full_preflight(self) -> None:
        clean = {"status": "CLEAN_PASS", "errors": []}
        with mock.patch.object(
            RUNTIME,
            "contract_surface_signature",
            return_value="stable-surface",
        ), mock.patch.object(
            RUNTIME,
            "global_contract_preflight",
            return_value=clean,
        ) as preflight_mock, mock.patch.object(RUNTIME.time, "sleep"):
            result = RUNTIME.wait_for_contract_stability(
                timeout_seconds=1.0,
                poll_seconds=0.01,
            )

        self.assertEqual(result["status"], "CLEAN_PASS")
        self.assertEqual(result["observations"], 2)
        self.assertEqual(preflight_mock.call_count, 1)

    def test_contract_surface_signature_tracks_content_not_only_metadata(self) -> None:
        with tempfile.TemporaryDirectory(dir=r"F:\Codex\cache") as temporary:
            root = Path(temporary)
            skills_root = root / "skills"
            entry = skills_root / "example" / "scripts" / "codex_entry.py"
            binding = skills_root / "example" / "SKILL.md"
            catalog = root / "stock_skill_ids.json"
            contracts = root / "stock_execution_contracts.json"
            entry.parent.mkdir(parents=True)
            entry.write_bytes(b"entry-a\n")
            binding.write_bytes(b"skill-a\n")
            catalog.write_text('{"skills":["example"]}\n', encoding="utf-8")
            contracts.write_text(
                json.dumps({
                    "contracts": [{
                        "skill_id": "example",
                        "business_bindings": [{"path": str(binding)}],
                    }],
                }),
                encoding="utf-8",
            )
            original = binding.stat()

            with mock.patch.object(RUNTIME, "SKILLS_ROOT", skills_root), mock.patch.object(
                RUNTIME,
                "CATALOG_PATH",
                catalog,
            ), mock.patch.object(RUNTIME, "CONTRACTS_PATH", contracts):
                before = RUNTIME.contract_surface_signature()
                binding.write_bytes(b"skill-b\n")
                os.utime(
                    binding,
                    ns=(original.st_atime_ns, original.st_mtime_ns),
                )
                after = RUNTIME.contract_surface_signature()

            self.assertNotEqual(before, after)

    def test_optional_lianban_source_reuses_runtime_cache(self) -> None:
        contract = {
            "supplemental_sources": {
                "lianban_daily": {
                    "enabled": True,
                    "required": False,
                    "client": str(RUNTIME.LIANBAN_CLIENT_PATH),
                    "date_mode": "exact",
                    "cache_ttl_seconds": 900,
                }
            }
        }
        resolution = {
            "status": "CLEAN_PASS",
            "target_date": "2026-08-29",
            "errors": [],
        }
        with tempfile.TemporaryDirectory(dir=r"F:\Codex\cache") as temporary:
            root = Path(temporary)
            cache_root = root / "lianban-cache"
            run_one = root / "run-one"
            run_two = root / "run-two"
            run_one.mkdir()
            run_two.mkdir()

            def fake_run_process(command, cwd, timeout, *args, **kwargs):
                del command, cwd, args, kwargs
                snapshot = run_one / "lianban-daily.json"
                snapshot.write_text(
                    json.dumps({
                        "schema": "LIANBAN_DAILY_SNAPSHOT_V1",
                        "status": "CLEAN_PASS",
                        "target_date": "2026-08-29",
                        "sources": {
                            "page": {"url": "https://lianban.net/days/2026-08-29.html"},
                            "open_data": {"url": "https://lianban.net/opendata/2026-08-29.json"},
                        },
                    }),
                    encoding="utf-8",
                )
                return {
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "",
                    "started_at": "2026-08-31T23:00:00+08:00",
                    "finished_at": "2026-08-31T23:00:01+08:00",
                    "elapsed_seconds": 1.0,
                }

            with mock.patch.object(
                RUNTIME,
                "STOCK_LIANBAN_CACHE_ROOT",
                cache_root,
            ), mock.patch.object(
                RUNTIME,
                "run_process",
                side_effect=fake_run_process,
            ) as run_mock:
                first = RUNTIME.prepare_lianban_daily_source(
                    contract,
                    run_one,
                    "2026-08-29",
                    resolution,
                )
                second = RUNTIME.prepare_lianban_daily_source(
                    contract,
                    run_two,
                    "2026-08-29",
                    resolution,
                )

            self.assertEqual(first["status"], "CLEAN_PASS")
            self.assertEqual(second["status"], "CLEAN_PASS")
            self.assertEqual(second["mode"], "shared_runtime_cache")
            self.assertTrue(second["cache_hit"])
            self.assertEqual(run_mock.call_count, 1)
            self.assertEqual(run_mock.call_args.args[2], 8)

    def test_convertible_bond_selftest_is_not_mapped_to_business(self) -> None:
        source = CONVERTIBLE_ENTRY.read_text(encoding="utf-8-sig")
        self.assertNotIn('"selftest": "business-selftest"', source)


if __name__ == "__main__":
    unittest.main()
