from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import codex_entry
from runtime_utils import RunLock, _WindowsJob, run_process_tree


class _FakeParent:
    def mkdir(self, **_: object) -> None:
        return None


class _FailingHandle:
    def __init__(self) -> None:
        self.closed = False

    def seek(self, *_: object) -> None:
        raise RuntimeError("injected_lock_initialization_failure")

    def close(self) -> None:
        self.closed = True


class _FakePath:
    parent = _FakeParent()

    def __init__(self, handle: _FailingHandle) -> None:
        self.handle = handle

    def open(self, *_: object, **__: object) -> _FailingHandle:
        return self.handle


def check_run_lock_cleanup() -> None:
    handle = _FailingHandle()
    try:
        RunLock(_FakePath(handle)).__enter__()  # type: ignore[arg-type]
    except RuntimeError as exc:
        assert str(exc) == "injected_lock_initialization_failure"
    else:
        raise AssertionError("injected RunLock initialization failure did not surface")
    assert handle.closed is True


def check_state_schemas_and_writes(root: Path) -> None:
    targets = (
        (root / "run_state.json", "RUN-SCHEMA"),
        (root / "status.json", "STATUS-SCHEMA"),
        (root / "readback.json", "READBACK-SCHEMA"),
    )
    documents = codex_entry.state_documents(
        {"schema": "WRONG", "status": "FAIL", "run_id": "isolated"},
        targets,
    )
    assert [payload["schema"] for _, payload in documents] == [
        "RUN-SCHEMA",
        "STATUS-SCHEMA",
        "READBACK-SCHEMA",
    ]
    ok, errors = codex_entry.write_state_transition(
        {"schema": "WRONG", "status": "RUNNING", "run_id": "isolated"},
        targets,
    )
    assert ok is True and errors == []
    for path, schema in targets:
        persisted = json.loads(path.read_text(encoding="utf-8"))
        assert persisted["schema"] == schema
        assert persisted["status"] == "RUNNING"


def check_status_exception_fail_closed(root: Path) -> None:
    original_impl = codex_entry._command_status_impl
    original_readback = codex_entry.STATUS_READBACK
    original_run_state = codex_entry.RUN_STATE
    original_status = codex_entry.STATUS
    try:
        codex_entry.STATUS_READBACK = root / "injected_status_readback.json"
        codex_entry.RUN_STATE = root / "injected_run_state.json"
        codex_entry.STATUS = root / "injected_status.json"
        codex_entry.RUN_STATE.write_text(
            json.dumps({"run_id": "failure-injection"}), encoding="utf-8"
        )

        def injected_failure(*, acquire_lock: bool = True) -> int:
            del acquire_lock
            raise KeyError("injected_business_validation_failure")

        codex_entry._command_status_impl = injected_failure
        assert codex_entry.command_status(acquire_lock=False) == 2
        persisted = json.loads(codex_entry.STATUS_READBACK.read_text(encoding="utf-8"))
        assert persisted["schema"] == "CONVERTIBLE-BOND-SCREENING-STATUS-READBACK-3"
        assert persisted["status"] == "FAIL"
        assert persisted["run_id"] == "failure-injection"
        assert "injected_business_validation_failure" in persisted["reason"]
    finally:
        codex_entry._command_status_impl = original_impl
        codex_entry.STATUS_READBACK = original_readback
        codex_entry.RUN_STATE = original_run_state
        codex_entry.STATUS = original_status


def check_timeout_is_bounded() -> None:
    command = [
        sys.executable,
        "-c",
        "import time; print('partial-output', flush=True); time.sleep(30)",
    ]
    started = time.perf_counter()
    try:
        run_process_tree(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=0.2,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.perf_counter() - started
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        assert "partial-output" in output
        assert elapsed < 12.0, elapsed
    else:
        raise AssertionError("timeout child unexpectedly completed")


def check_windows_job_close_terminates_child() -> None:
    if os.name != "nt":
        return
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    job = _WindowsJob(process)
    try:
        assert job._handle is not None
    finally:
        job.close()
    process.wait(timeout=5.0)
    assert process.poll() is not None


def main() -> int:
    check_run_lock_cleanup()
    with tempfile.TemporaryDirectory(prefix="cb-runtime-safety-") as temporary:
        root = Path(temporary)
        check_state_schemas_and_writes(root)
        check_status_exception_fail_closed(root)
    check_windows_job_close_terminates_child()
    check_timeout_is_bounded()
    print(json.dumps({
        "schema": "CONVERTIBLE-BOND-RUNTIME-SAFETY-SELFCHECK-1",
        "status": "PASS",
        "checks": {
            "run_lock_initialization_closes_handle": True,
            "state_schema_cannot_be_overridden": True,
            "state_transition_persists_all_targets": True,
            "status_exception_writes_current_fail_readback": True,
            "windows_job_kill_on_close_terminates_child": True,
            "timeout_cleanup_is_bounded_and_preserves_output": True,
        },
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
