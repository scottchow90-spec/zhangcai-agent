from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import skill14_data_runtime as runtime


def make_skill_zip(*, nested: bool = False, traversal: bool = False) -> bytes:
    skill = b"---\nname: test-skill\ndescription: Offline package fixture\n---\nInstructions.\n"
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as bundle:
        if traversal:
            bundle.writestr("../escape.txt", "must not escape")
        elif nested:
            inner = io.BytesIO()
            with zipfile.ZipFile(inner, "w", zipfile.ZIP_DEFLATED) as nested_bundle:
                nested_bundle.writestr("a-share-test/SKILL.md", skill)
            bundle.writestr("nested/test-skill.zip", inner.getvalue())
        else:
            bundle.writestr("SKILL.md", skill)
    return result.getvalue()


class Skill14PackageRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.archive_root = self.root / "archives"
        self.archive_root.mkdir()
        self.data_root = self.root / "resource-library"
        self.data_root.mkdir()
        self.skill_id = "test-skill"
        self.archive = self.archive_root / "test-skill.zip"
        self.archive.write_bytes(make_skill_zip())
        self.catalog_patch = mock.patch.object(
            runtime,
            "catalog",
            return_value={
                "skills": [
                    {"id": self.skill_id, "name": "测试技能", "archive": self.archive.name}
                ]
            },
        )
        self.data_patch = mock.patch.object(runtime, "DATA_ROOT", self.data_root)
        self.archive_patch = mock.patch.object(runtime, "ARCHIVE_ROOT", self.archive_root)
        self.status_patch = mock.patch.object(runtime, "update_status", return_value={})
        self.catalog_patch.start()
        self.data_patch.start()
        self.archive_patch.start()
        self.status_patch.start()
        self.addCleanup(self.catalog_patch.stop)
        self.addCleanup(self.data_patch.stop)
        self.addCleanup(self.archive_patch.stop)
        self.addCleanup(self.status_patch.stop)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_on_demand_bundle_is_harness_discoverable_and_reused(self) -> None:
        first = runtime.prepare_harness_skill(self.skill_id)
        second = runtime.prepare_harness_skill(self.skill_id)
        self.assertEqual(first["status"], "available")
        self.assertEqual(first["skill_name"], "test-skill")
        self.assertTrue((Path(first["harness_skill_root"]) / "SKILL.md").is_file())
        with mock.patch.object(runtime, "sha256_file", side_effect=AssertionError("archive should use verified cache metadata")):
            second = runtime.prepare_harness_skill(self.skill_id)
        self.assertEqual(second["source"], "on_demand_cache")
        self.assertEqual(second["harness_skill_root"], first["harness_skill_root"])

    def test_legacy_package_manifest_is_not_reused_without_decoder_version(self) -> None:
        installed_root = self.data_root / "skills" / "packages" / self.skill_id
        installed_root.mkdir(parents=True)
        (installed_root / "SKILL.md").write_text(
            "---\nname: stale-skill\ndescription: Old extraction\n---\nOld body.\n",
            encoding="utf-8",
        )
        archive_sha = runtime.sha256_file(self.archive)
        runtime.write_json(
            self.data_root / "skills" / "manifest.json",
            {"skills": [{"id": self.skill_id, "sha256": archive_sha, "skill_root": f"skills/packages/{self.skill_id}"}]},
        )

        prepared = runtime.prepare_harness_skill(self.skill_id)

        self.assertEqual(prepared["source"], "on_demand_archive")
        self.assertEqual(prepared["skill_name"], "test-skill")
        self.assertNotEqual(Path(prepared["harness_skill_root"]), installed_root)

    def test_nested_archive_skill_entry_is_resolved(self) -> None:
        self.archive.write_bytes(make_skill_zip(nested=True))
        prepared = runtime.prepare_harness_skill(self.skill_id)
        skill_root = Path(prepared["harness_skill_root"])
        self.assertEqual(skill_root.name, "a-share-test")
        self.assertTrue((skill_root / "SKILL.md").is_file())

    def test_zip_path_traversal_is_rejected(self) -> None:
        with zipfile.ZipFile(io.BytesIO(make_skill_zip(traversal=True))) as bundle:
            with self.assertRaisesRegex(RuntimeError, "不安全路径"):
                runtime.extract_skill_zip(bundle, self.root / "extract")
        self.assertFalse((self.root / "escape.txt").exists())

    def test_bulk_prepare_preserves_previous_package_instead_of_deleting_it(self) -> None:
        destination = self.data_root / "skills" / "packages" / self.skill_id
        destination.mkdir(parents=True)
        (destination / "user-note.txt").write_text("preserve me", encoding="utf-8")
        runtime.write_json(
            self.data_root / "skills" / "manifest.json",
            {"skills": [{"id": self.skill_id, "sha256": "old-version"}]},
        )

        result = runtime.prepare_packages()

        self.assertEqual(result["skills"][0]["status"], "available")
        self.assertTrue((destination / "SKILL.md").is_file())
        backups = list(destination.parent.glob(f"{self.skill_id}.previous-old-version-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "user-note.txt").read_text(encoding="utf-8"), "preserve me")

    def test_bulk_prepare_reextracts_legacy_manifest_even_when_archive_hash_matches(self) -> None:
        destination = self.data_root / "skills" / "packages" / self.skill_id
        destination.mkdir(parents=True)
        (destination / "legacy-name.txt").write_text("preserve me", encoding="utf-8")
        archive_sha = runtime.sha256_file(self.archive)
        runtime.write_json(
            self.data_root / "skills" / "manifest.json",
            {"skills": [{"id": self.skill_id, "sha256": archive_sha}]},
        )

        result = runtime.prepare_packages()

        self.assertEqual(result["skills"][0]["status"], "available")
        self.assertEqual(result["skills"][0]["archive_decoder_version"], runtime.SKILL_ARCHIVE_DECODER_VERSION)
        backups = list(destination.parent.glob(f"{self.skill_id}.previous-{archive_sha[:12]}-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "legacy-name.txt").read_text(encoding="utf-8"), "preserve me")


if __name__ == "__main__":
    unittest.main()
