#!/usr/bin/env python3
"""Regression contract: stock-unified must not control protected processes."""

from __future__ import annotations

from pathlib import Path
import re
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = SKILL_ROOT / "scripts"
RUNTIME_GUARD_TEST = SKILL_ROOT / "tests" / "test_tdx_runtime_guard.py"
SOURCE_SUFFIXES = {".py", ".ps1", ".psm1", ".cmd", ".bat", ".js", ".ts", ".mjs", ".cjs"}
FORBIDDEN_PROCESS_ACTIONS = {
    "powershell process termination": re.compile(r"\bStop-Process\b", re.IGNORECASE),
    "windows process termination": re.compile(r"\btaskkill(?:\.exe)?\b", re.IGNORECASE),
    "native process termination": re.compile(r"\bTerminateProcess\b", re.IGNORECASE),
    "window close": re.compile(r"\bCloseMainWindow\b|\bWM_CLOSE\b", re.IGNORECASE),
    "process suspension": re.compile(r"\bNtSuspendProcess\b|\bSuspendThread\b", re.IGNORECASE),
    "process injection": re.compile(
        r"\bWriteProcessMemory\b|\bCreateRemoteThread\b|\bQueueUserAPC\b",
        re.IGNORECASE,
    ),
    "desktop takeover": re.compile(
        r"\bSendKeys\b|\bSendInput\b|\bSetCursorPos\b|\bSetForegroundWindow\b",
        re.IGNORECASE,
    ),
    "system lifecycle": re.compile(
        r"\bshutdown(?:\.exe)?\b|\bRestart-Computer\b|\bStop-Computer\b",
        re.IGNORECASE,
    ),
}


def _static_scanner_canary() -> None:
    # This unreachable branch proves that only the hash-bound authority path is exempted.
    if False:  # pragma: no cover
        import subprocess

        subprocess.run(["taskkill.exe", "/F", "/IM", "TdxW.exe"], check=True)


class TdxProcessProtectionTests(unittest.TestCase):
    def test_runtime_guard_regression_uses_only_inert_process_control_canaries(self) -> None:
        source = RUNTIME_GUARD_TEST.read_text(encoding="utf-8")
        direct_process_control_commands = re.findall(
            r'"(?:taskkill_name|taskkill_pid|stop_process)"\s*:\s*'
            r'\[\s*"(?:taskkill(?:\.exe)?|powershell(?:\.exe)?)"',
            source,
            re.IGNORECASE,
        )
        self.assertEqual(
            [],
            direct_process_control_commands,
            "Runtime guard tests must not launch real process-control executables",
        )
        self.assertIn("INERT_PROCESS_CONTROL_CANARY", source)

    def test_stock_unified_scripts_do_not_control_protected_processes(self) -> None:
        scripts = sorted(
            path
            for path in SCRIPT_ROOT.rglob("*")
            if path.is_file() and path.suffix.casefold() in SOURCE_SUFFIXES
        )
        self.assertTrue(scripts, f"No scripts found under {SCRIPT_ROOT}")

        violations: list[str] = []
        for path in scripts:
            source = path.read_text(encoding="utf-8-sig", errors="replace")
            for label, pattern in FORBIDDEN_PROCESS_ACTIONS.items():
                if pattern.search(source):
                    violations.append(f"{path.relative_to(SKILL_ROOT)}: {label}")

        self.assertEqual([], violations, "Protected process actions found:\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main(verbosity=2)
