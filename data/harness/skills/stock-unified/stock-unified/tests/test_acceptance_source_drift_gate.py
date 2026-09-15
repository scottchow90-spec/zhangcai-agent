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
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
AGGREGATE_PATH = ROOT / "scripts" / "stock-unified.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


AGGREGATE = load_module(
    "stock_unified_acceptance_source_drift_test",
    AGGREGATE_PATH,
)


class AcceptanceSourceDriftGateTests(unittest.TestCase):
    def test_business_spec_must_not_hardcode_catalog_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            business_spec = Path(temporary) / "business_spec.md"
            business_spec.write_text(
                "- 目录口径：目录中的 52 个当前唯一技能 ID。\n",
                encoding="utf-8",
            )
            with mock.patch.object(AGGREGATE, "BUSINESS_SPEC", business_spec):
                errors = AGGREGATE.acceptance_source_errors(["alpha", "beta"])

        self.assertIn("business_spec_hardcoded_catalog_count", errors)

    def test_source_manifest_hash_drift_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skills_root = Path(temporary) / "skills"
            component = (
                skills_root
                / "alpha"
                / "components"
                / "source-one"
                / "scripts"
                / "workflow.py"
            )
            component.parent.mkdir(parents=True)
            component.write_text("print('current')\n", encoding="utf-8")
            manifest = skills_root / "alpha" / "references" / "source-manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps({
                    "schema": "MERGED_SKILL_SOURCE_MANIFEST_V2",
                    "sources": ["source-one"],
                    "files": {
                        "source-one": {
                            "scripts/workflow.py": hashlib.sha256(
                                b"print('stale')\n"
                            ).hexdigest(),
                        }
                    },
                }),
                encoding="utf-8",
            )

            with mock.patch.object(AGGREGATE, "SKILLS_ROOT", skills_root), mock.patch.object(
                AGGREGATE,
                "BUSINESS_SPEC",
                Path(temporary) / "missing-business-spec.md",
            ):
                errors = AGGREGATE.acceptance_source_errors(["alpha"])

        self.assertIn(
            "alpha:source_manifest_hash_mismatch:source-one:scripts/workflow.py",
            errors,
        )

    def test_run_all_stops_before_child_selftests_on_acceptance_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            AGGREGATE,
            "RESULT_DIR",
            Path(temporary),
        ), mock.patch.object(
            AGGREGATE,
            "load_catalog",
            return_value=["alpha"],
        ), mock.patch.object(
            AGGREGATE,
            "contract_catalog_preflight",
            return_value={
                "status": "CLEAN_PASS",
                "errors": [],
                "failure_owner": None,
            },
        ), mock.patch.object(
            AGGREGATE,
            "acceptance_source_errors",
            return_value=["business_spec_hardcoded_catalog_count"],
        ), mock.patch.object(
            AGGREGATE,
            "execute_all",
        ) as execute_all:
            returncode = AGGREGATE.run_all()

        self.assertEqual(returncode, 2)
        execute_all.assert_not_called()


if __name__ == "__main__":
    unittest.main()
