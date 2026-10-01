"""Runtime guard that keeps TongDaXin formula access read-only in lifecycle terms."""
from __future__ import annotations

import builtins
import importlib.machinery
import json
import os
import re
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


_LOCK = threading.RLock()
_ORIGINAL_IMPORT: Callable[..., Any] | None = None
_ORIGINAL_SOURCE_EXEC_MODULE: Callable[..., Any] | None = None
_PROTECTED_MODULE_IDS: set[int] = set()
_PROTECTED_PROCESS_NAMES = frozenset({"tdxw", "tdxcef"})
_PROCESS_CONTROL_RE = re.compile(
    r"(?:\btaskkill(?:\.exe)?\b|\btskill(?:\.exe)?\b|\bStop-Process\b|"
    r"\bTerminateProcess\b|\bNtSuspendProcess\b|\bSuspendThread\b)",
    re.IGNORECASE,
)
_PROTECTED_NAME_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:tdxw|tdxcef)(?:\.exe)?(?![A-Za-z0-9])",
    re.IGNORECASE,
)
_INTEGER_TOKEN_RE = re.compile(r"(?<!\d)\d{1,10}(?!\d)")
_ORIGINAL_POPEN: Callable[..., Any] | None = None
_ORIGINAL_POPEN_INIT: Callable[..., Any] | None = None
_ORIGINAL_OS_KILL: Callable[..., Any] | None = None
_ORIGINAL_PSUTIL_METHODS: dict[str, Callable[..., Any]] = {}
_ORIGINAL_SUBPROCESS_METHODS: dict[str, Callable[..., Any]] = {}


def _record_blocked_action(action: str, target: str | int | None = None) -> None:
    log_path = os.environ.get("CODEX_TDX_GUARD_LOG", "").strip()
    if not log_path:
        return
    payload = {
        "schema": "TDX_PROCESS_GUARD_EVENT_V1",
        "status": "BLOCKED",
        "action": action,
        "target": target,
        "pid": os.getpid(),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    try:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except OSError:
        pass


def _normalized_process_name(value: object) -> str:
    name = Path(str(value)).name.casefold()
    return name[:-4] if name.endswith(".exe") else name


def _environment_protected_pids() -> set[int]:
    protected: set[int] = set()
    for token in os.environ.get("CODEX_TDX_PROTECTED_PIDS", "").split(","):
        token = token.strip()
        if token.isdigit() and int(token) > 0:
            protected.add(int(token))
    return protected


def _windows_pid_name(pid: int) -> str:
    if os.name != "nt" or pid <= 0:
        return ""
    try:
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        open_process = kernel32.OpenProcess
        open_process.argtypes = (ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32)
        open_process.restype = ctypes.c_void_p
        close_handle = kernel32.CloseHandle
        close_handle.argtypes = (ctypes.c_void_p,)
        query_name = kernel32.QueryFullProcessImageNameW
        query_name.argtypes = (
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_wchar_p,
            ctypes.POINTER(ctypes.c_uint32),
        )
        handle = open_process(0x1000, 0, int(pid))
        if not handle:
            return ""
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            length = ctypes.c_uint32(len(buffer))
            if not query_name(handle, 0, buffer, ctypes.byref(length)):
                return ""
            return _normalized_process_name(buffer.value)
        finally:
            close_handle(handle)
    except (AttributeError, ImportError, OSError, TypeError, ValueError):
        return ""


def _is_protected_pid(pid: object) -> bool:
    try:
        normalized = int(pid)
    except (TypeError, ValueError):
        return False
    return (
        normalized in _environment_protected_pids()
        or _windows_pid_name(normalized) in _PROTECTED_PROCESS_NAMES
    )


def _command_text(command: object) -> str:
    if isinstance(command, bytes):
        return command.decode("utf-8", "replace")
    if isinstance(command, str):
        return command
    if isinstance(command, (list, tuple)):
        return " ".join(_command_text(item) for item in command)
    return str(command)


def _command_targets_protected_process(command: object) -> bool:
    text = _command_text(command)
    if not _PROCESS_CONTROL_RE.search(text):
        return False
    if _PROTECTED_NAME_RE.search(text):
        return True
    return any(_is_protected_pid(token) for token in _INTEGER_TOKEN_RE.findall(text))


def _guarding_popen(*popenargs: Any, **kwargs: Any) -> Any:
    if _ORIGINAL_POPEN is None:
        raise RuntimeError("tdx_subprocess_guard_not_initialized")
    command = kwargs.get("args") if "args" in kwargs else (popenargs[0] if popenargs else None)
    if _command_targets_protected_process(command):
        target = _command_text(command)
        _record_blocked_action("subprocess.process_control", target)
        raise PermissionError("protected TongDaXin subprocess control blocked")
    return _ORIGINAL_POPEN(*popenargs, **kwargs)


def _guarding_popen_init(self: Any, *popenargs: Any, **kwargs: Any) -> Any:
    if _ORIGINAL_POPEN_INIT is None:
        raise RuntimeError("tdx_subprocess_guard_not_initialized")
    command = kwargs.get("args") if "args" in kwargs else (popenargs[0] if popenargs else None)
    if _command_targets_protected_process(command):
        target = _command_text(command)
        _record_blocked_action("subprocess.process_control", target)
        raise PermissionError("protected TongDaXin subprocess control blocked")
    return _ORIGINAL_POPEN_INIT(self, *popenargs, **kwargs)


_guarding_popen_init._codex_tdx_process_guard = True  # type: ignore[attr-defined]


def _guarding_os_kill(pid: int, sig: int) -> Any:
    if _ORIGINAL_OS_KILL is None:
        raise RuntimeError("tdx_os_kill_guard_not_initialized")
    if _is_protected_pid(pid):
        _record_blocked_action("os.kill", pid)
        raise PermissionError("protected TongDaXin os.kill blocked")
    return _ORIGINAL_OS_KILL(pid, sig)


def protect_psutil_module(module: ModuleType) -> bool:
    """Deny psutil lifecycle methods for protected process names or PIDs."""
    process_type = getattr(module, "Process", None)
    if not isinstance(process_type, type):
        return False
    protected_any = False
    for method_name in ("terminate", "kill", "suspend", "send_signal"):
        original = getattr(process_type, method_name, None)
        if not callable(original) or getattr(original, "_codex_tdx_process_guard", False):
            continue
        _ORIGINAL_PSUTIL_METHODS.setdefault(method_name, original)

        def guarded(self: Any, *args: Any, __name: str = method_name, __original: Callable[..., Any] = original, **kwargs: Any) -> Any:
            pid = getattr(self, "pid", None)
            process_name = ""
            try:
                process_name = _normalized_process_name(self.name())
            except Exception:
                pass
            if _is_protected_pid(pid) or process_name in _PROTECTED_PROCESS_NAMES:
                target = f"{process_name or 'unknown'}:{pid}"
                _record_blocked_action(f"psutil.Process.{__name}", target)
                raise PermissionError(f"protected TongDaXin psutil {__name} blocked")
            return __original(self, *args, **kwargs)

        guarded._codex_tdx_process_guard = True  # type: ignore[attr-defined]
        setattr(process_type, method_name, guarded)
        protected_any = True
    return protected_any


def protect_subprocess_popen_type(process_type: type[Any]) -> bool:
    """Deny Popen lifecycle methods when a handle resolves to a protected PID."""
    protected_any = False
    for method_name in ("terminate", "kill", "send_signal"):
        original = getattr(process_type, method_name, None)
        if not callable(original) or getattr(original, "_codex_tdx_process_guard", False):
            continue
        _ORIGINAL_SUBPROCESS_METHODS.setdefault(method_name, original)

        def guarded(self: Any, *args: Any, __name: str = method_name, __original: Callable[..., Any] = original, **kwargs: Any) -> Any:
            pid = getattr(self, "pid", None)
            if _is_protected_pid(pid):
                _record_blocked_action(f"subprocess.Popen.{__name}", pid)
                raise PermissionError(f"protected TongDaXin Popen {__name} blocked")
            return __original(self, *args, **kwargs)

        guarded._codex_tdx_process_guard = True  # type: ignore[attr-defined]
        setattr(process_type, method_name, guarded)
        protected_any = True
    return protected_any


def install_process_control_guard() -> None:
    """Install idempotent subprocess, os.kill, and psutil default-deny guards."""
    global _ORIGINAL_POPEN, _ORIGINAL_POPEN_INIT, _ORIGINAL_OS_KILL
    with _LOCK:
        current_popen = subprocess.Popen
        if isinstance(current_popen, type):
            if _ORIGINAL_POPEN is None:
                _ORIGINAL_POPEN = current_popen
            protect_subprocess_popen_type(current_popen)
            current_init = current_popen.__init__
            if not getattr(current_init, "_codex_tdx_process_guard", False):
                _ORIGINAL_POPEN_INIT = current_init
                current_popen.__init__ = _guarding_popen_init
        elif current_popen is not _guarding_popen:
            _ORIGINAL_POPEN = current_popen
            subprocess.Popen = _guarding_popen  # type: ignore[assignment]
        if hasattr(os, "kill") and os.kill is not _guarding_os_kill:
            _ORIGINAL_OS_KILL = os.kill
            os.kill = _guarding_os_kill  # type: ignore[assignment]
        existing = sys.modules.get("psutil")
        if isinstance(existing, ModuleType):
            protect_psutil_module(existing)


def protect_tqcenter_module(module: ModuleType) -> bool:
    """Mark TQ as guarded without blocking connection-only cleanup methods.

    ``tq.close()``, ``tq._auto_close()``, ``tq._release()`` and
    ``dll.CloseConnect()`` release a TPythClient connection; they do not stop,
    restart, suspend, inject into, or replace TdxW/tdxcef.  Blocking those
    methods leaks connection resources and creates false process-control
    events.  Actual protected-process controls remain default-denied by the
    subprocess, os.kill, psutil and Popen guards above.
    """
    tq = getattr(module, "tq", None)
    dll = getattr(module, "dll", None)
    if tq is None or dll is None:
        return False
    identity = id(module)
    with _LOCK:
        if identity in _PROTECTED_MODULE_IDS:
            return True
        setattr(tq, "_codex_tdx_process_guard_installed", True)
        setattr(tq, "_codex_tdx_connection_lifecycle_passthrough", True)
        _PROTECTED_MODULE_IDS.add(identity)
    return True


def _guarding_import(
    name: str,
    globals: dict[str, Any] | None = None,
    locals: dict[str, Any] | None = None,
    fromlist: tuple[str, ...] | list[str] = (),
    level: int = 0,
) -> Any:
    if _ORIGINAL_IMPORT is None:
        raise RuntimeError("tdx_import_guard_not_initialized")
    imported = _ORIGINAL_IMPORT(name, globals, locals, fromlist, level)
    module = sys.modules.get("tqcenter")
    if isinstance(module, ModuleType):
        protect_tqcenter_module(module)
    psutil_module = sys.modules.get("psutil")
    if isinstance(psutil_module, ModuleType):
        protect_psutil_module(psutil_module)
    return imported


def _guarding_source_exec_module(loader: Any, module: ModuleType) -> Any:
    if _ORIGINAL_SOURCE_EXEC_MODULE is None:
        raise RuntimeError("tdx_source_loader_guard_not_initialized")
    result = _ORIGINAL_SOURCE_EXEC_MODULE(loader, module)
    source_path = Path(str(getattr(loader, "path", "")))
    if source_path.name.casefold() == "tqcenter.py":
        protect_tqcenter_module(module)
    psutil_module = sys.modules.get("psutil")
    if isinstance(psutil_module, ModuleType):
        protect_psutil_module(psutil_module)
    return result


def install_tdx_import_guard() -> None:
    """Install lifecycle, process-control, and import guards before business code."""
    global _ORIGINAL_IMPORT, _ORIGINAL_SOURCE_EXEC_MODULE
    with _LOCK:
        existing = sys.modules.get("tqcenter")
        if isinstance(existing, ModuleType):
            protect_tqcenter_module(existing)
        if builtins.__import__ is not _guarding_import:
            _ORIGINAL_IMPORT = builtins.__import__
            builtins.__import__ = _guarding_import
        if (
            importlib.machinery.SourceFileLoader.exec_module
            is not _guarding_source_exec_module
        ):
            _ORIGINAL_SOURCE_EXEC_MODULE = (
                importlib.machinery.SourceFileLoader.exec_module
            )
            importlib.machinery.SourceFileLoader.exec_module = (
                _guarding_source_exec_module
            )
        install_process_control_guard()
