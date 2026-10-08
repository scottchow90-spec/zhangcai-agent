from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX_HOME = ROOT.parents[1]
BOOTSTRAP = CODEX_HOME / "scripts" / "stock_runtime_bootstrap"
RUNTIME = CODEX_HOME / "scripts" / "stock_canonical_runtime.py"


class TdxRuntimeGuardTests(unittest.TestCase):
    def test_bootstrap_blocks_name_pid_os_kill_and_psutil_before_original_call(self) -> None:
        child_source = textwrap.dedent(
            r"""
            import json
            import os
            import subprocess
            import sys
            import types
            import tdx_process_guard as guard

            results = {}
            lifecycle_calls = []
            fake_tqcenter = types.ModuleType("tqcenter")
            class FakeTq:
                @classmethod
                def close(cls):
                    lifecycle_calls.append("tq.close")
                    return "close-called"
                @classmethod
                def _auto_close(cls):
                    lifecycle_calls.append("tq._auto_close")
                    return "auto-close-called"
                @classmethod
                def _release(cls):
                    lifecycle_calls.append("tq._release")
                    return "release-called"
            class FakeDll:
                def CloseConnect(self, run_id, run_mode):
                    lifecycle_calls.append(f"dll.CloseConnect:{run_id}:{run_mode}")
                    return "close-connect-called"
            fake_tqcenter.tq = FakeTq
            fake_tqcenter.dll = FakeDll()
            results["tqcenter_guard_marked"] = guard.protect_tqcenter_module(fake_tqcenter)
            results["tq_close"] = FakeTq.close()
            results["tq_auto_close"] = FakeTq._auto_close()
            results["tq_release"] = FakeTq._release()
            results["dll_close_connect"] = fake_tqcenter.dll.CloseConnect(7, 9)
            results["lifecycle_calls"] = lifecycle_calls
            results["connection_passthrough"] = bool(
                getattr(FakeTq, "_codex_tdx_connection_lifecycle_passthrough", False)
            )
            inert_canary = "raise SystemExit(0)  # INERT_PROCESS_CONTROL_CANARY"
            commands = {
                "taskkill_name": [sys.executable, "-c", inert_canary, "taskkill.exe", "/F", "/IM", "TdxW.exe"],
                "taskkill_pid": [sys.executable, "-c", inert_canary, "taskkill.exe", "/F", "/PID", "424242"],
                "stop_process": [sys.executable, "-c", inert_canary, "powershell.exe", "-Command", "Stop-Process -Name tdxcef"],
            }
            for label, command in commands.items():
                try:
                    subprocess.Popen(command)
                except PermissionError:
                    results[label] = "BLOCKED"
                else:
                    results[label] = "NOT_BLOCKED"

            try:
                os.kill(424242, 0)
            except PermissionError:
                results["os_kill"] = "BLOCKED"
            else:
                results["os_kill"] = "NOT_BLOCKED"

            fake_psutil = types.ModuleType("psutil")
            class FakeProcess:
                original_calls = []
                def __init__(self, pid, process_name):
                    self.pid = pid
                    self._process_name = process_name
                def name(self):
                    return self._process_name
                def terminate(self):
                    self.original_calls.append("terminate")
                    return "terminate-called"
                def kill(self):
                    self.original_calls.append("kill")
                    return "kill-called"
                def suspend(self):
                    self.original_calls.append("suspend")
                    return "suspend-called"
                def send_signal(self, signal):
                    self.original_calls.append(f"signal:{signal}")
                    return "signal-called"
            fake_psutil.Process = FakeProcess
            guard.protect_psutil_module(fake_psutil)

            class FakePopen:
                original_calls = []
                def __init__(self, pid):
                    self.pid = pid
                def terminate(self):
                    self.original_calls.append("terminate")
                    return "popen-terminate-called"
                def kill(self):
                    self.original_calls.append("kill")
                    return "popen-kill-called"
                def send_signal(self, signal):
                    self.original_calls.append(f"signal:{signal}")
                    return "popen-signal-called"
            guard.protect_subprocess_popen_type(FakePopen)

            protected_by_pid = FakeProcess(424242, "worker.exe")
            protected_by_name = FakeProcess(515151, "tdxcef.exe")
            for label, process, method, args in (
                ("psutil_terminate_pid", protected_by_pid, "terminate", ()),
                ("psutil_kill_pid", protected_by_pid, "kill", ()),
                ("psutil_suspend_name", protected_by_name, "suspend", ()),
                ("psutil_signal_name", protected_by_name, "send_signal", (9,)),
            ):
                try:
                    getattr(process, method)(*args)
                except PermissionError:
                    results[label] = "BLOCKED"
                else:
                    results[label] = "NOT_BLOCKED"

            protected_popen = FakePopen(424242)
            for label, method, args in (
                ("popen_terminate_pid", "terminate", ()),
                ("popen_kill_pid", "kill", ()),
                ("popen_signal_pid", "send_signal", (9,)),
            ):
                try:
                    getattr(protected_popen, method)(*args)
                except PermissionError:
                    results[label] = "BLOCKED"
                else:
                    results[label] = "NOT_BLOCKED"

            benign = FakeProcess(616161, "worker.exe")
            results["benign_psutil"] = benign.terminate()
            results["benign_popen"] = FakePopen(616161).terminate()
            benign_child = subprocess.run(
                [sys.executable, "-c", "print('SAFE_CHILD')"],
                capture_output=True,
                text=True,
                check=False,
            )
            results["benign_subprocess"] = {
                "returncode": benign_child.returncode,
                "stdout": benign_child.stdout.strip(),
            }
            results["original_psutil_calls"] = FakeProcess.original_calls
            results["original_popen_calls"] = FakePopen.original_calls
            print(json.dumps(results, sort_keys=True))
            """
        )
        with tempfile.TemporaryDirectory() as temporary:
            harness = Path(temporary) / "tdx_guard_failure_injection.py"
            harness.write_text(child_source, encoding="utf-8")
            guard_log = Path(temporary) / "tdx-guard.jsonl"
            environment = dict(os.environ)
            environment.update(
                {
                    "CODEX_TDX_PROCESS_GUARD": "1",
                    "CODEX_TDX_PROTECTED_PIDS": "424242",
                    "CODEX_TDX_GUARD_LOG": str(guard_log),
                    "PYTHONPATH": os.pathsep.join(
                        value
                        for value in (str(BOOTSTRAP), environment.get("PYTHONPATH", ""))
                        if value
                    ),
                }
            )
            completed = subprocess.run(
                [sys.executable, str(harness)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=environment,
                timeout=30,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            results = json.loads(completed.stdout)
            blocked_labels = {
                "taskkill_name",
                "taskkill_pid",
                "stop_process",
                "os_kill",
                "psutil_terminate_pid",
                "psutil_kill_pid",
                "psutil_suspend_name",
                "psutil_signal_name",
                "popen_terminate_pid",
                "popen_kill_pid",
                "popen_signal_pid",
            }
            self.assertEqual(
                {label for label in blocked_labels if results[label] == "BLOCKED"},
                blocked_labels,
            )
            self.assertEqual(results["benign_psutil"], "terminate-called")
            self.assertEqual(results["benign_popen"], "popen-terminate-called")
            self.assertEqual(results["benign_subprocess"], {"returncode": 0, "stdout": "SAFE_CHILD"})
            self.assertTrue(results["tqcenter_guard_marked"])
            self.assertTrue(results["connection_passthrough"])
            self.assertEqual(results["tq_close"], "close-called")
            self.assertEqual(results["tq_auto_close"], "auto-close-called")
            self.assertEqual(results["tq_release"], "release-called")
            self.assertEqual(results["dll_close_connect"], "close-connect-called")
            self.assertEqual(
                results["lifecycle_calls"],
                [
                    "tq.close",
                    "tq._auto_close",
                    "tq._release",
                    "dll.CloseConnect:7:9",
                ],
            )
            self.assertEqual(results["original_psutil_calls"], ["terminate"])
            self.assertEqual(results["original_popen_calls"], ["terminate"])
            events = [json.loads(line) for line in guard_log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(events), len(blocked_labels))
            self.assertTrue(all(event["status"] == "BLOCKED" for event in events))

    def test_guard_keeps_popen_subclassable_for_asyncio_imports(self) -> None:
        child_source = textwrap.dedent(
            """
            import asyncio
            import json
            import subprocess
            import sys

            class DerivedPopen(subprocess.Popen):
                pass

            child = subprocess.run(
                [sys.executable, "-c", "print('SAFE_CHILD')"],
                capture_output=True,
                text=True,
                check=False,
            )
            print(json.dumps({
                "asyncio_imported": asyncio.__name__ == "asyncio",
                "popen_is_type": isinstance(subprocess.Popen, type),
                "derived_is_subclass": issubclass(DerivedPopen, subprocess.Popen),
                "child_returncode": child.returncode,
                "child_stdout": child.stdout.strip(),
            }, sort_keys=True))
            """
        )
        with tempfile.TemporaryDirectory() as temporary:
            environment = dict(os.environ)
            environment.update(
                {
                    "CODEX_TDX_PROCESS_GUARD": "1",
                    "CODEX_TDX_PROTECTED_PIDS": "424242",
                    "CODEX_TDX_GUARD_LOG": str(Path(temporary) / "tdx-guard.jsonl"),
                    "PYTHONPATH": os.pathsep.join(
                        value
                        for value in (str(BOOTSTRAP), environment.get("PYTHONPATH", ""))
                        if value
                    ),
                }
            )
            completed = subprocess.run(
                [sys.executable, "-c", child_source],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=environment,
                timeout=30,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(
            json.loads(completed.stdout),
            {
                "asyncio_imported": True,
                "child_returncode": 0,
                "child_stdout": "SAFE_CHILD",
                "derived_is_subclass": True,
                "popen_is_type": True,
            },
        )

    def test_explicit_bootstrap_installs_guard_without_pythonpath(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "guard_probe.py"
            target.write_text(
                "import json, subprocess, sys\n"
                "print(json.dumps({\n"
                "    'guard_module_loaded': 'tdx_process_guard' in sys.modules,\n"
                "    'popen_init_guarded': bool(getattr(subprocess.Popen.__init__, '_codex_tdx_process_guard', False)),\n"
                "}))\n",
                encoding="utf-8",
                newline="\n",
            )
            environment = dict(os.environ)
            environment.pop("PYTHONPATH", None)
            environment["CODEX_TDX_PROCESS_GUARD"] = "1"
            completed = subprocess.run(
                [sys.executable, str(BOOTSTRAP / "sitecustomize.py"), str(target)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=environment,
                timeout=30,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(
            json.loads(completed.stdout),
            {"guard_module_loaded": True, "popen_init_guarded": True},
        )

    def test_runtime_wraps_python_script_with_explicit_guard_bootstrap(self) -> None:
        spec = importlib.util.spec_from_file_location("tdx_runtime_guard_wrap_test", RUNTIME)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        command = [sys.executable, str(Path("probe.py").resolve()), "argument"]

        guarded = module.prepare_tdx_guarded_python_command(command)

        self.assertEqual(
            guarded,
            [
                sys.executable,
                str((BOOTSTRAP / "sitecustomize.py").resolve()),
                str(Path("probe.py").resolve()),
                "argument",
            ],
        )

    def test_runtime_bootstrap_hash_gate_is_clean(self) -> None:
        spec = importlib.util.spec_from_file_location("tdx_runtime_guard_hash_test", RUNTIME)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        result = module.validate_tdx_formula_guard()
        self.assertEqual(result["status"], "CLEAN_PASS", result["errors"])

    def test_static_scan_exempts_only_hash_pinned_guard_and_blocks_real_control(self) -> None:
        spec = importlib.util.spec_from_file_location("tdx_runtime_guard_scan_test", RUNTIME)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        self.assertEqual(
            module.scan_tdx_process_control_paths([BOOTSTRAP / "tdx_process_guard.py"]),
            [],
        )
        with tempfile.TemporaryDirectory() as temporary:
            malicious = Path(temporary) / "control_tdx.py"
            malicious.write_text(
                "import subprocess\n"
                "subprocess.run(['taskkill.exe', '/F', '/IM', 'tdxw.exe'])\n",
                encoding="utf-8",
                newline="\n",
            )
            findings = module.scan_tdx_process_control_paths([malicious])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["reason"], "tdx_process_control_detected")


if __name__ == "__main__":
    unittest.main()
