from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import json
import math
import os
import re
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable, Sequence


class RunInProgressError(RuntimeError):
    pass


_RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*", re.ASCII)
_MARKET_ATTEMPT_PATTERN = re.compile(r"[1-9][0-9]*", re.ASCII)
BUSINESS_FLOAT_DECIMAL_PLACES = 12
_BUSINESS_FLOAT_QUANTUM = Decimal(1).scaleb(-BUSINESS_FLOAT_DECIMAL_PLACES)
_WINDOWS_RESERVED_PATH_NAMES = {
    "AUX",
    "CON",
    "NUL",
    "PRN",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def canonicalize_business_payload(value: Any) -> Any:
    """Return JSON-compatible business data with deterministic float precision."""

    if isinstance(value, dict):
        return {
            key: canonicalize_business_payload(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [canonicalize_business_payload(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("business payload contains a non-finite float")
        with localcontext() as context:
            context.prec = 50
            quantized = Decimal(str(value)).quantize(
                _BUSINESS_FLOAT_QUANTUM,
                rounding=ROUND_HALF_EVEN,
            )
        return 0.0 if quantized.is_zero() else float(quantized)
    return value


def canonical_business_sum(values: Iterable[float]) -> float:
    """Sum canonical business decimals without interpreter-specific float tails."""

    with localcontext() as context:
        context.prec = 50
        total = sum(
            (
                Decimal(str(canonicalize_business_payload(float(value))))
                for value in values
            ),
            Decimal(0),
        )
        quantized = total.quantize(
            _BUSINESS_FLOAT_QUANTUM,
            rounding=ROUND_HALF_EVEN,
        )
    return 0.0 if quantized.is_zero() else float(quantized)


@dataclass(frozen=True)
class GenerationPaths:
    generation_dir: Path
    top1_dir: Path
    result: Path
    formula_evidence: Path
    day_input_manifest: Path
    redemption_announcements: Path
    verification: Path
    independent_heat_verification: Path
    summary: Path
    selftest: Path
    top1_validation: Path
    top1_golden: Path
    top1_feilong: Path
    top1_bigbull: Path
    top1_run_logs: Path


def validate_run_id(value: Any) -> str:
    """Return a canonical path-safe run id or raise ``ValueError``."""

    if not isinstance(value, str) or _RUN_ID_PATTERN.fullmatch(value) is None:
        raise ValueError("run_id must use only ASCII letters, digits, '_' or '-'")
    if value.upper() in _WINDOWS_RESERVED_PATH_NAMES:
        raise ValueError("run_id must not be a reserved Windows path name")
    return value


def validate_market_attempt(value: Any) -> int:
    """Return a positive integer attempt; strings and booleans are invalid."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("market_attempt must be a positive integer")
    return value


def parse_market_attempt(value: str) -> int:
    """Parse the canonical decimal form accepted from a CLI argument."""

    if not isinstance(value, str) or _MARKET_ATTEMPT_PATTERN.fullmatch(value) is None:
        raise ValueError("market_attempt must be canonical positive decimal text")
    return validate_market_attempt(int(value, 10))


def build_generation_paths(
    run_dir: str | os.PathLike[str],
    run_id: Any,
    market_attempt: Any,
) -> GenerationPaths:
    """Build isolated paths without creating directories on disk."""

    validated_run_id = validate_run_id(run_id)
    validated_attempt = validate_market_attempt(market_attempt)
    generation_dir = (
        Path(run_dir)
        / "generations"
        / validated_run_id
        / f"attempt-{validated_attempt}"
    )
    top1_dir = generation_dir / "top1"
    return GenerationPaths(
        generation_dir=generation_dir,
        top1_dir=top1_dir,
        result=generation_dir / "latest_result.json",
        formula_evidence=generation_dir / "latest_formula_evidence.json",
        day_input_manifest=generation_dir / "latest_day_input_manifest.json",
        redemption_announcements=generation_dir / "latest_early_redemption_announcements.json",
        verification=generation_dir / "latest_verification.json",
        independent_heat_verification=generation_dir / "latest_independent_heat_verification.json",
        summary=generation_dir / "latest_summary.json",
        selftest=generation_dir / "selftest.json",
        top1_validation=generation_dir / "top1_fixed_skill_validation.json",
        top1_golden=top1_dir / "top1_golden_ignition.json",
        top1_feilong=top1_dir / "top1_feilong.json",
        top1_bigbull=top1_dir / "top1_big_bull" / "analysis_report.txt",
        top1_run_logs=top1_dir / "fixed_skill_runs",
    )


class _WindowsJob:
    """Best-effort Windows Job Object used to terminate a complete process tree."""

    def __init__(self, process: subprocess.Popen[Any]):
        self._handle: int | None = None
        if os.name != "nt":
            return

        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
        ]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.TerminateJobObject.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        handle = kernel32.CreateJobObjectW(None, None)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        limits.BasicLimitInformation.LimitFlags = 0x00002000  # KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            handle,
            9,  # JobObjectExtendedLimitInformation
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            error = ctypes.get_last_error()
            kernel32.CloseHandle(handle)
            raise ctypes.WinError(error)
        if not kernel32.AssignProcessToJobObject(handle, wintypes.HANDLE(int(process._handle))):
            error = ctypes.get_last_error()
            kernel32.CloseHandle(handle)
            raise ctypes.WinError(error)

        self._kernel32 = kernel32
        self._handle = int(handle)

    def terminate(self, exit_code: int = 1) -> bool:
        if self._handle is None:
            return False
        return bool(self._kernel32.TerminateJobObject(self._handle, exit_code))

    def close(self) -> None:
        handle = self._handle
        self._handle = None
        if handle is not None:
            self._kernel32.CloseHandle(handle)


def _terminate_process_tree(
    process: subprocess.Popen[Any],
    windows_job: _WindowsJob | None,
) -> None:
    """Terminate *process* and descendants without depending on their cooperation."""

    if os.name == "nt":
        terminated = bool(windows_job and windows_job.terminate())
        if not terminated:
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                    check=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except (OSError, subprocess.SubprocessError):
                pass
        if process.poll() is None:
            try:
                process.kill()
            except OSError:
                pass
        return

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        if process.poll() is None:
            try:
                process.kill()
            except OSError:
                pass


def run_process_tree(
    args: Sequence[str | os.PathLike[str]] | str | os.PathLike[str],
    *,
    capture_output: bool = False,
    text: bool = False,
    encoding: str | None = None,
    errors: str | None = None,
    cwd: str | os.PathLike[str] | None = None,
    timeout: float | None = None,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[Any]:
    """Run a command and reliably tear down its whole process tree on timeout.

    The public behavior follows :func:`subprocess.run`: successful execution
    returns ``CompletedProcess`` and timeout raises ``TimeoutExpired`` after the
    process tree is gone.  On Windows a Job Object is preferred, with
    ``taskkill /T`` as a compatibility fallback.  POSIX children start in a new
    session and are killed by process group.
    """

    popen_kwargs: dict[str, Any] = {
        "cwd": cwd,
        "stdout": subprocess.PIPE if capture_output else None,
        "stderr": subprocess.PIPE if capture_output else None,
        "text": text,
        "encoding": encoding,
        "errors": errors,
    }
    if env is not None:
        popen_kwargs["env"] = env
    if os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        popen_kwargs["start_new_session"] = True

    process = subprocess.Popen(args, **popen_kwargs)
    windows_job: _WindowsJob | None = None
    if os.name == "nt":
        try:
            windows_job = _WindowsJob(process)
        except OSError:
            windows_job = None

    try:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            _terminate_process_tree(process, windows_job)
            stdout, stderr = exc.output, exc.stderr
            try:
                drained_stdout, drained_stderr = process.communicate(timeout=5.0)
                stdout = drained_stdout if drained_stdout is not None else stdout
                stderr = drained_stderr if drained_stderr is not None else stderr
            except subprocess.TimeoutExpired as drain_exc:
                stdout = drain_exc.output if drain_exc.output is not None else stdout
                stderr = drain_exc.stderr if drain_exc.stderr is not None else stderr
                if process.poll() is None:
                    try:
                        process.kill()
                    except OSError:
                        pass
                try:
                    drained_stdout, drained_stderr = process.communicate(timeout=1.0)
                    stdout = drained_stdout if drained_stdout is not None else stdout
                    stderr = drained_stderr if drained_stderr is not None else stderr
                except subprocess.TimeoutExpired as final_exc:
                    stdout = final_exc.output if final_exc.output is not None else stdout
                    stderr = final_exc.stderr if final_exc.stderr is not None else stderr
            exc.stdout = stdout
            exc.stderr = stderr
            raise
        result = subprocess.CompletedProcess(args, process.returncode, stdout, stderr)
        if check:
            result.check_returncode()
        return result
    finally:
        if windows_job is not None:
            windows_job.close()


class RunLock:
    """Cross-process, crash-releasing lock for the skill run directory."""

    def __init__(self, path: Path):
        self.path = path
        self._handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = None
        try:
            handle = self.path.open("a+b")
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
                os.fsync(handle.fileno())
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (OSError, BlockingIOError) as exc:
                raise RunInProgressError(f"RUN_IN_PROGRESS:{self.path}") from exc
            self._handle = handle
            return self
        except BaseException:
            if handle is not None:
                handle.close()
            raise

    def __exit__(self, exc_type, exc, traceback) -> None:
        handle = self._handle
        self._handle = None
        if handle is None:
            return
        try:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            newline="",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))
