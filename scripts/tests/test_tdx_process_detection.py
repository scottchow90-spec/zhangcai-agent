from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from subprocess import TimeoutExpired
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tdx_process


class TdxProcessDetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="tdx-process-root-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "T0002").mkdir()

    @staticmethod
    def result(stdout: str | bytes, returncode: int = 0) -> SimpleNamespace:
        return SimpleNamespace(stdout=stdout, stderr=b"", returncode=returncode)

    def runner_for(self, tasklist: str, cim: str | bytes | Exception):
        def runner(command, **_kwargs):
            if command[0].casefold() == "tasklist.exe":
                return self.result(tasklist)
            if isinstance(cim, Exception):
                raise cim
            return self.result(cim)

        return runner

    def test_matches_mock_process_root_with_spaces_and_non_ascii(self) -> None:
        root = self.root / "Program Files" / "通达信 Mock"
        (root / "T0002").mkdir(parents=True)
        executable = root / "new_tdx_mock.exe"
        payload = json.dumps([{
            "Name": executable.name,
            "ProcessId": 17,
            "CreationDate": "2026-09-25T09:00:00",
            "ExecutablePath": str(executable),
        }], ensure_ascii=False).encode("utf-8")
        state = tdx_process.detect_tdx_process(
            str(root),
            runner=self.runner_for('"new_tdx_mock.exe","17","Console","1","20 K"\r\n', payload),
        )
        self.assertIs(state["running"], True)
        self.assertIs(state["rootMatches"], True)
        self.assertEqual(state["processes"][0]["tdxRoot"], str(root))

    def test_slow_cim_uses_tasklist_evidence_instead_of_false_closed(self) -> None:
        def runner(command, **_kwargs):
            if command[0].casefold() == "tasklist.exe":
                return self.result('"TdxW.exe","41","Console","1","50 K"\r\n')
            raise TimeoutExpired(command, timeout=12)

        state = tdx_process.detect_tdx_process(str(self.root), runner=runner)
        self.assertIs(state["running"], True)
        self.assertIsNone(state["rootMatches"])
        self.assertEqual(state["state"], "open_unresolved")
        self.assertEqual(state["detection"], "tasklist_fallback")

    def test_no_process_is_reported_closed_only_after_successful_enumeration(self) -> None:
        state = tdx_process.detect_tdx_process(
            str(self.root),
            runner=self.runner_for("", "[]"),
        )
        self.assertIs(state["running"], False)
        self.assertEqual(state["state"], "closed")

    def test_other_installation_is_reported_as_path_mismatch(self) -> None:
        other = self.root / "other" / "client"
        (other / "vipdoc").mkdir(parents=True)
        executable = other / "TdxW.exe"
        payload = json.dumps([{
            "Name": "TdxW.exe",
            "ProcessId": 9,
            "ExecutablePath": str(executable),
        }]).encode("utf-8")
        state = tdx_process.detect_tdx_process(
            str(self.root),
            runner=self.runner_for('"TdxW.exe","9","Console","1","40 K"\r\n', payload),
        )
        self.assertIs(state["running"], True)
        self.assertIs(state["rootMatches"], False)
        self.assertEqual(state["state"], "path_mismatch")

    def test_unavailable_enumerators_remain_unknown_not_closed(self) -> None:
        def runner(command, **_kwargs):
            raise TimeoutExpired(command, timeout=4)

        state = tdx_process.detect_tdx_process(str(self.root), runner=runner)
        self.assertIsNone(state["running"])
        self.assertEqual(state["state"], "unknown")


if __name__ == "__main__":
    unittest.main(verbosity=2)
