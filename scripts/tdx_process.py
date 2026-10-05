"""Portable, conservative detection of an installed Tongdaxin client.

The desktop panel, TQ formula runner, and live-quote worker must agree on
whether the configured client is running.  In particular, a slow CIM query on
low-memory PCs must not be interpreted as proof that the client is closed.
"""
from __future__ import annotations

import csv
import io
import json
import ntpath
import os
import subprocess
from pathlib import Path
from typing import Any, Callable


_BASE_PROCESS_NAMES = {
    "tdxw.exe",
    "tdxw64.exe",
    "tdx.exe",
    "new_tdx_mock.exe",
    "new_tdx.exe",
    "通达信.exe",
    "通达信金融终端.exe",
}


def _process_names(root: str | Path) -> list[str]:
    names = set(_BASE_PROCESS_NAMES)
    for key in ("ZHANGCAI_TDX_EXE", "TDX_EXE"):
        configured = str(os.environ.get(key) or "").strip().strip('"')
        if configured:
            names.add(Path(configured).name.casefold())
    root_path = Path(root)
    for candidate in (
        root_path / "TdxW.exe",
        root_path / "TdxW64.exe",
        root_path / "tdx.exe",
        root_path / "new_tdx_mock.exe",
        root_path / "new_tdx.exe",
        root_path / "TdxW" / "TdxW.exe",
    ):
        if candidate.is_file():
            names.add(candidate.name.casefold())
    return sorted(names)


def _decode_console(value: str | bytes | None) -> str:
    if isinstance(value, str):
        return value
    raw = value or b""
    if os.name == "nt":
        try:
            return raw.decode("mbcs", errors="replace")
        except LookupError:
            pass
    return raw.decode("utf-8", errors="replace")


def _query_tasklist(names: set[str], runner: Callable[..., Any]) -> tuple[bool, list[dict[str, Any]], str]:
    try:
        result = runner(
            ["tasklist.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=False,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=3,
        )
        if int(getattr(result, "returncode", 1)) != 0:
            return False, [], f"tasklist_exit:{getattr(result, 'returncode', 'unknown')}"
        rows: list[dict[str, Any]] = []
        for row in csv.reader(io.StringIO(_decode_console(getattr(result, "stdout", b"")))):
            if not row:
                continue
            name = row[0].strip().casefold()
            if name in names:
                rows.append({"Name": row[0].strip(), "ProcessId": row[1].strip() if len(row) > 1 else "", "ExecutablePath": ""})
        return True, rows, ""
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        return False, [], f"tasklist_failed:{type(exc).__name__}:{exc}"


def _parse_json_rows(raw: str) -> list[dict[str, Any]]:
    text = raw.strip()
    if not text:
        raise ValueError("empty_process_json")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        # PowerShell profiles, endpoint protection, or CIM warnings can write
        # a short line before the JSON object. Parse from the first JSON token.
        start = min((index for index in (text.find("["), text.find("{")) if index >= 0), default=-1)
        if start < 0:
            raise
        value = json.loads(text[start:])
    if value is None:
        return []
    rows = value if isinstance(value, list) else [value]
    return [row for row in rows if isinstance(row, dict)]


def _query_cim(names: list[str], runner: Callable[..., Any]) -> tuple[bool, list[dict[str, Any]], str]:
    ps_names = ",".join("'" + name.replace("'", "''") + "'" for name in names)
    command = (
        "$ErrorActionPreference='Stop';"
        "[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false);"
        "$OutputEncoding=[Console]::OutputEncoding;"
        f"$names=@({ps_names});"
        "$rows=@(Get-CimInstance Win32_Process -ErrorAction Stop | "
        "Where-Object { $names -contains $_.Name.ToLowerInvariant() } | "
        "Select-Object Name,ProcessId,CreationDate,ExecutablePath);"
        "if ($rows.Count -eq 0) { [Console]::Write('[]') } "
        "else { ConvertTo-Json -InputObject $rows -Compress }"
    )
    try:
        result = runner(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=False,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=6,
        )
        stdout = getattr(result, "stdout", b"")
        raw = stdout.decode("utf-8-sig", errors="replace") if isinstance(stdout, bytes) else str(stdout or "")
        if int(getattr(result, "returncode", 1)) != 0:
            return False, [], f"cim_exit:{getattr(result, 'returncode', 'unknown')}:{_decode_console(getattr(result, 'stderr', b''))[:300]}"
        return True, _parse_json_rows(raw), ""
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError) as exc:
        return False, [], f"cim_failed:{type(exc).__name__}:{exc}"


def _process_root(executable: str) -> str:
    if not executable:
        return ""
    candidate = Path(executable).parent
    for _ in range(10):
        try:
            if (candidate / "vipdoc").is_dir() or (candidate / "T0002").is_dir():
                return str(candidate)
        except OSError:
            pass
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    return str(Path(executable).parent)


def _normalize_root(value: str | Path) -> str:
    return ntpath.normcase(ntpath.normpath(str(value).replace("/", "\\"))).rstrip("\\")


def same_tdx_root(left: str | Path, right: str | Path) -> bool:
    return bool(str(left or "").strip() and str(right or "").strip()) and _normalize_root(left) == _normalize_root(right)


def summarize_tdx_processes(
    rows: list[dict[str, Any]], root: str | Path, *, unknown_error: str = "", source: str = "powershell_cim"
) -> dict[str, Any]:
    processes: list[dict[str, Any]] = []
    running_roots: list[str] = []
    has_unresolved_path = False
    for raw in rows:
        row = dict(raw)
        executable = str(row.get("ExecutablePath") or row.get("executablePath") or "")
        process_root = _process_root(executable) if executable else ""
        root_matches: bool | None = same_tdx_root(process_root, root) if process_root else None
        row["tdxRoot"] = process_root
        row["rootMatches"] = root_matches
        processes.append(row)
        if process_root and process_root not in running_roots:
            running_roots.append(process_root)
        if root_matches is None:
            has_unresolved_path = True

    matching = [row for row in processes if row.get("rootMatches") is True]
    if matching:
        return {
            "running": True,
            "state": "open",
            "matching": matching,
            "processes": processes,
            "rootMatches": True,
            "runningRoots": running_roots,
            "detection": source,
        }
    if processes:
        roots_all_known = not has_unresolved_path
        return {
            "running": True,
            "state": "path_mismatch" if roots_all_known else "open_unresolved",
            "matching": [],
            "processes": processes,
            "rootMatches": False if roots_all_known else None,
            "runningRoots": running_roots,
            "detection": source,
        }
    if unknown_error:
        return {
            "running": None,
            "state": "unknown",
            "matching": [],
            "processes": [],
            "rootMatches": None,
            "runningRoots": [],
            "detection": "unavailable",
            "error": unknown_error[:500],
        }
    return {
        "running": False,
        "state": "closed",
        "matching": [],
        "processes": [],
        "rootMatches": None,
        "runningRoots": [],
        "detection": source,
    }


def detect_tdx_process(root: str | Path, runner: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Return tri-state process evidence, preserving uncertainty on query errors."""
    if os.name != "nt":
        return summarize_tdx_processes([], root, unknown_error="Windows process inspection is unavailable on this platform.", source="unsupported")
    run = runner or subprocess.run
    names = _process_names(root)
    names_set = {name.casefold() for name in names}
    tasklist_ok, tasklist_rows, tasklist_error = _query_tasklist(names_set, run)
    if tasklist_ok and not tasklist_rows:
        # tasklist is the fast, low-memory first tier. It already checks all
        # supported image aliases; avoid a slower CIM scan when none is open.
        return summarize_tdx_processes([], root, source="tasklist")
    cim_ok, cim_rows, cim_error = _query_cim(names, run)
    if cim_ok:
        if cim_rows:
            return summarize_tdx_processes(cim_rows, root)
        # If the fast process-name query observed the client but CIM raced or
        # could not expose its executable path, do not claim it is closed.
        if tasklist_rows:
            return summarize_tdx_processes(tasklist_rows, root, source="tasklist_fallback")
        return summarize_tdx_processes([], root)
    if tasklist_rows:
        return summarize_tdx_processes(tasklist_rows, root, source="tasklist_fallback")
    if tasklist_ok:
        # tasklist successfully enumerated all known TDX image names and found
        # none; it is sufficient to confirm that no supported client is open.
        return summarize_tdx_processes([], root, source="tasklist")
    return summarize_tdx_processes([], root, unknown_error=f"{tasklist_error}; {cim_error}")
