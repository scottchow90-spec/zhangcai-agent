from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = ROOT / "scripts" / "sync_merged_source_manifests.py"
SPEC = importlib.util.spec_from_file_location("merged_source_manifest_sync_test", SYNC_SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MergedSourceManifestSyncTests(unittest.TestCase):
    def test_live_manifests_have_complete_file_sets_and_current_hashes(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT), "--check"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_unlisted_component_file_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill_root = Path(temporary) / "sample"
            component_root = skill_root / "components" / "source-one"
            references_root = skill_root / "references"
            component_root.mkdir(parents=True)
            references_root.mkdir()
            (component_root / "listed.txt").write_text("listed", encoding="utf-8")
            (component_root / "unlisted.txt").write_text("unlisted", encoding="utf-8")
            manifest_path = references_root / "source-manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "MERGED_SKILL_SOURCE_MANIFEST_V1",
                        "sources": ["source-one"],
                        "files": {
                            "source-one": {
                                "listed.txt": MODULE.sha256_file(component_root / "listed.txt")
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            _, changes, errors = MODULE.audit_manifest(manifest_path)
            self.assertFalse(changes)
            self.assertTrue(any(error.startswith("unlisted_component_file:") for error in errors))


if __name__ == "__main__":
    unittest.main()
