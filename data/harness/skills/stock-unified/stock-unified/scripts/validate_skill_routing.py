#!/usr/bin/env python3
"""Validate the canonical Codex skill root using machine-readable state."""

from __future__ import annotations

import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import tomllib
from collections import defaultdict
from pathlib import Path
from typing import Any

from stock_contract_catalog import load_stock_catalog


CANONICAL_HOME = Path(r"D:\C盘转移\日志\codex")
COMPAT_HOME = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".codex"
DESKTOP_RUNTIME_BIN = Path(r"F:\Codex\DesktopRuntime\bin")
DEFAULT_STOCK_SKILL = "stock-research-codex"
ACTIVE_AUTHORITY_FILENAMES = {
    "stock_skill_ids.json",
    "stock_execution_contracts.json",
    "stock_canonical_runtime.py",
    "skills_index.md",
    "skill_router.py",
}
INACTIVE_AUTHORITY_PARTS = {
    ".git",
    "__pycache__",
    "archive",
    "archives",
    "backup",
    "backups",
    "cache",
    "caches",
    "merged_sources",
    "reports",
    "runs",
    "temp",
    "tmp",
}
AGENTS_STOCK_ROUTING_MARKERS = (
    "# Canonical stock skill routing",
    "stock_skill_ids.json",
    "stock_execution_contracts.json",
    "stock_canonical_runtime.py",
)
AGENTS_STOCK_ROUTING_GUARD_ALTERNATIVES = (
    "不得由相近技能或组件重复抢占",
    "禁止旧技能、相近技能、组件入口、备份目录或第二套路由器抢占",
)


def resolve_app_server_executable() -> Path:
    configured_executable: Path | None = None
    try:
        with (CANONICAL_HOME / "config.toml").open("rb") as config_file:
            config = tomllib.load(config_file)
        configured_value = (
            config.get("mcp_servers", {})
            .get("node_repl", {})
            .get("env", {})
            .get("CODEX_CLI_PATH")
        )
        if isinstance(configured_value, str) and configured_value:
            configured_executable = Path(configured_value)
            mirrored = (
                DESKTOP_RUNTIME_BIN
                / configured_executable.parent.name
                / configured_executable.name
            )
            if mirrored.is_file():
                return mirrored
            if configured_executable.is_file():
                return configured_executable
    except (OSError, tomllib.TOMLDecodeError):
        pass

    candidates = sorted(DESKTOP_RUNTIME_BIN.glob("*/codex.exe"))
    if len(candidates) == 1:
        return candidates[0]
    if configured_executable is not None:
        return (
            DESKTOP_RUNTIME_BIN
            / configured_executable.parent.name
            / configured_executable.name
        )
    return DESKTOP_RUNTIME_BIN / "codex.exe"


APP_SERVER_EXE = resolve_app_server_executable()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def normalize_windows_path(value: str | Path | None) -> str | None:
    if value is None:
        return None
    return os.path.normcase(os.path.normpath(str(value)))


def is_under(path: str | Path, root: str | Path) -> bool:
    normalized_path = normalize_windows_path(path)
    normalized_root = normalize_windows_path(root)
    if normalized_path is None or normalized_root is None:
        return False
    try:
        return os.path.commonpath((normalized_path, normalized_root)) == normalized_root
    except ValueError:
        return False


def frontmatter_value(text: str, key: str) -> str | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return None
    frontmatter = "\n".join(lines[1:end])
    match = re.search(
        rf"(?m)^{re.escape(key)}:\s*(?P<value>.+?)\s*$",
        frontmatter,
    )
    if not match:
        return None
    return match.group("value").strip().strip("\"'")


def implicit_policy(text: str) -> bool | None:
    match = re.search(
        r"(?m)^\s*allow_implicit_invocation:\s*(true|false)\s*$",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    return match.group(1).lower() == "true"


def user_codex_home() -> str | None:
    if os.name != "nt":
        return None
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, "CODEX_HOME")
            return str(value)
    except FileNotFoundError:
        return None


def same_physical_home(left: Path, right: Path) -> bool:
    try:
        return left.exists() and right.exists() and os.path.samefile(left, right)
    except OSError:
        return False


def is_reparse_point(path: Path) -> bool:
    if not path.exists():
        return False
    if hasattr(os.path, "isjunction") and os.path.isjunction(path):
        return True
    try:
        return bool(path.stat().st_file_attributes & 0x400)
    except (AttributeError, OSError):
        return False


def validate_home_identity(
    *,
    canonical_home: Path,
    compat_home: Path,
    process_home: Path | None,
    user_home: Path | None,
) -> dict[str, Any]:
    errors: list[str] = []
    canonical_home_exists = canonical_home.is_dir()
    compat_home_is_reparse_point = is_reparse_point(compat_home)
    compat_home_same_physical_home = same_physical_home(
        compat_home,
        canonical_home,
    )
    verified_compat_fallback = (
        canonical_home_exists
        and compat_home_is_reparse_point
        and compat_home_same_physical_home
    )
    effective_process_home = (
        process_home
        if process_home is not None
        else canonical_home if verified_compat_fallback else None
    )
    effective_user_home = (
        user_home
        if user_home is not None
        else compat_home if verified_compat_fallback else None
    )
    checks = {
        "canonical_home": str(canonical_home),
        "compat_home": str(compat_home),
        "process_home": str(process_home) if process_home is not None else None,
        "user_home": str(user_home) if user_home is not None else None,
        "process_home_source": (
            "environment" if process_home is not None else "canonical_fallback"
        ),
        "user_home_source": (
            "registry" if user_home is not None else "compatibility_junction_fallback"
        ),
        "effective_process_home": (
            str(effective_process_home)
            if effective_process_home is not None
            else None
        ),
        "effective_user_home": (
            str(effective_user_home) if effective_user_home is not None else None
        ),
        "canonical_home_exists": canonical_home_exists,
        "compat_home_is_reparse_point": compat_home_is_reparse_point,
        "compat_home_same_physical_home": compat_home_same_physical_home,
        "verified_compat_fallback": verified_compat_fallback,
        "process_home_same_physical_home": (
            same_physical_home(effective_process_home, canonical_home)
            if effective_process_home is not None
            else False
        ),
        "user_home_same_physical_home": (
            same_physical_home(effective_user_home, canonical_home)
            if effective_user_home is not None
            else False
        ),
    }
    if not checks["canonical_home_exists"]:
        errors.append("canonical_home_missing")
    if not checks["compat_home_is_reparse_point"]:
        errors.append("compat_home_not_reparse_point")
    if not checks["compat_home_same_physical_home"]:
        errors.append("compat_home_wrong_target")
    if process_home is None and not verified_compat_fallback:
        errors.append("process_home_missing_without_verified_fallback")
    elif not checks["process_home_same_physical_home"]:
        errors.append("process_home_is_independent")
    if user_home is None and not verified_compat_fallback:
        errors.append("user_home_missing_without_verified_fallback")
    elif not checks["user_home_same_physical_home"]:
        errors.append("user_home_is_independent")
    return {"checks": checks, "errors": errors}


def active_authority_path(path: Path) -> bool:
    lowered_parts = {part.casefold() for part in path.parts}
    return not lowered_parts.intersection(INACTIVE_AUTHORITY_PARTS)


def validate_stock_authority_topology(home: Path) -> dict[str, Any]:
    expected = {
        "stock_skill_ids.json": (
            home
            / "skills"
            / "stock-unified"
            / "references"
            / "stock_skill_ids.json"
        ),
        "stock_execution_contracts.json": (
            home
            / "skills"
            / "stock-unified"
            / "references"
            / "stock_execution_contracts.json"
        ),
        "stock_canonical_runtime.py": (
            home / "scripts" / "stock_canonical_runtime.py"
        ),
    }
    found: defaultdict[str, list[Path]] = defaultdict(list)
    if home.is_dir():
        for current_root, directory_names, file_names in os.walk(home):
            directory_names[:] = [
                name
                for name in directory_names
                if name.casefold() not in INACTIVE_AUTHORITY_PARTS
            ]
            root = Path(current_root)
            for file_name in file_names:
                normalized_name = file_name.casefold()
                if normalized_name not in ACTIVE_AUTHORITY_FILENAMES:
                    continue
                candidate = root / file_name
                if active_authority_path(candidate.relative_to(home)):
                    found[normalized_name].append(candidate)

    errors: list[str] = []
    catalogs = found["stock_skill_ids.json"]
    contracts = found["stock_execution_contracts.json"]
    runtimes = found["stock_canonical_runtime.py"]
    aliases = found["skills_index.md"] + found["skill_router.py"]

    if len(catalogs) != 1:
        errors.append(
            "multiple_active_stock_catalogs"
            if len(catalogs) > 1
            else "canonical_stock_catalog_missing"
        )
    if len(contracts) != 1:
        errors.append(
            "multiple_active_stock_contracts"
            if len(contracts) > 1
            else "canonical_stock_contracts_missing"
        )
    if len(runtimes) != 1:
        errors.append(
            "multiple_active_stock_runtimes"
            if len(runtimes) > 1
            else "canonical_stock_runtime_missing"
        )
    if aliases:
        errors.append("alternate_stock_routing_authority")

    for file_name, expected_path in expected.items():
        candidates = found[file_name]
        if len(candidates) == 1:
            try:
                is_expected = os.path.samefile(candidates[0], expected_path)
            except OSError:
                is_expected = False
            if not is_expected:
                errors.append(f"noncanonical_{file_name}")

    return {
        "errors": errors,
        "active_catalogs": [str(path) for path in catalogs],
        "active_contracts": [str(path) for path in contracts],
        "active_runtimes": [str(path) for path in runtimes],
        "alternate_authorities": [str(path) for path in aliases],
    }


def validate_agents_stock_routing(agents_path: Path) -> list[str]:
    try:
        text = read_text(agents_path)
    except OSError:
        return ["stock_routing_agents_missing"]
    errors = [
        f"stock_routing_agents_marker_missing:{marker}"
        for marker in AGENTS_STOCK_ROUTING_MARKERS
        if marker not in text
    ]
    if not any(
        marker in text for marker in AGENTS_STOCK_ROUTING_GUARD_ALTERNATIVES
    ):
        errors.append("stock_routing_agents_semantic_guard_missing")
    return errors


def parse_json_lines(raw: str) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            messages.append(value)
    return messages


def find_response(
    messages: list[dict[str, Any]],
    request_id: int,
) -> dict[str, Any]:
    for message in messages:
        if message.get("id") == request_id:
            return message
    raise RuntimeError(f"response id {request_id} was not returned")


def summarize_skills(
    response: dict[str, Any],
    stock_skill_ids: list[str],
) -> dict[str, Any]:
    if "error" in response:
        raise RuntimeError(f"skills/list returned error: {response['error']}")

    result = response.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("skills/list response has no object result")
    data = result.get("data")
    if not isinstance(data, list):
        raise RuntimeError("skills/list result has no data array")

    skills: list[dict[str, Any]] = []
    scan_errors: list[Any] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        entry_skills = entry.get("skills")
        if isinstance(entry_skills, list):
            skills.extend(item for item in entry_skills if isinstance(item, dict))
        entry_errors = entry.get("errors")
        if isinstance(entry_errors, list):
            scan_errors.extend(entry_errors)

    by_name: defaultdict[str, list[str]] = defaultdict(list)
    normalized_paths: list[str] = []
    for skill in skills:
        name = str(skill.get("name", ""))
        path = str(skill.get("path", ""))
        by_name[name].append(path)
        normalized = normalize_windows_path(path)
        if normalized is not None:
            normalized_paths.append(normalized)

    duplicate_names = {
        name: paths for name, paths in by_name.items() if len(paths) > 1
    }
    missing_stock_names = sorted(set(stock_skill_ids) - set(by_name))
    unexpected_stock_paths: dict[str, list[str]] = {}
    for skill_id in stock_skill_ids:
        expected_path = normalize_windows_path(
            CANONICAL_HOME / "skills" / skill_id / "SKILL.md"
        )
        actual_paths = by_name.get(skill_id, [])
        if actual_paths and any(
            normalize_windows_path(path) != expected_path for path in actual_paths
        ):
            unexpected_stock_paths[skill_id] = actual_paths

    return {
        "data_entries": len(data),
        "skill_count": len(skills),
        "unique_name_count": len(by_name),
        "unique_path_count": len(set(normalized_paths)),
        "duplicate_names": duplicate_names,
        "missing_stock_names": missing_stock_names,
        "unexpected_stock_paths": unexpected_stock_paths,
        "c_alias_path_count": sum(
            is_under(path, COMPAT_HOME) for path in normalized_paths
        ),
        "f_canonical_path_count": sum(
            is_under(path, CANONICAL_HOME) for path in normalized_paths
        ),
        "scan_errors": scan_errors,
    }


def probe_app_server(
    home_env: Path,
    cwd: Path,
    stock_skill_ids: list[str],
) -> dict[str, Any]:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(home_env)
    env["NO_COLOR"] = "1"

    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        process = subprocess.Popen(
            [str(APP_SERVER_EXE), "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=str(cwd),
            bufsize=1,
            creationflags=creationflags,
        )
    except OSError as exc:
        return {
            "status": "FAIL",
            "requested_codex_home": str(home_env),
            "failure": f"temporary app-server could not start: {exc}",
        }

    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None

    stdout_lines: queue.Queue[str | None] = queue.Queue()
    stderr_chunks: list[str] = []

    def read_stdout() -> None:
        for line in iter(process.stdout.readline, ""):
            stdout_lines.put(line)
        stdout_lines.put(None)

    def read_stderr() -> None:
        stderr_chunks.append(process.stderr.read())

    stdout_thread = threading.Thread(target=read_stdout, daemon=True)
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    messages: list[dict[str, Any]] = []
    raw_stdout: list[str] = []
    deadline = time.monotonic() + 120

    def send(message: dict[str, Any]) -> None:
        process.stdin.write(
            json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n"
        )
        process.stdin.flush()

    def receive_until(required_ids: set[int]) -> None:
        received_ids = {
            message.get("id")
            for message in messages
            if message.get("id") in required_ids
        }
        while received_ids != required_ids:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                missing = sorted(required_ids - received_ids)
                raise RuntimeError(
                    f"temporary app-server timed out waiting for response ids {missing}"
                )
            try:
                line = stdout_lines.get(timeout=min(0.25, remaining))
            except queue.Empty:
                if process.poll() is not None:
                    break
                continue
            if line is None:
                break
            raw_stdout.append(line)
            parsed = parse_json_lines(line)
            messages.extend(parsed)
            received_ids.update(
                message.get("id")
                for message in parsed
                if message.get("id") in required_ids
            )
        missing = sorted(required_ids - received_ids)
        if missing:
            raise RuntimeError(
                f"temporary app-server exited before response ids {missing}"
            )

    report: dict[str, Any] = {
        "status": "FAIL",
        "requested_codex_home": str(home_env),
    }
    try:
        send(
            {
                "id": 1,
                "method": "initialize",
                "params": {
                    "clientInfo": {
                        "name": "stock-root-runtime-validator",
                        "version": "1.0.0",
                    }
                },
            }
        )
        receive_until({1})
        initialize_response = find_response(messages, 1)
        if "error" in initialize_response:
            raise RuntimeError(
                f"initialize returned error: {initialize_response['error']}"
            )

        send({"method": "initialized"})
        send(
            {
                "id": 2,
                "method": "config/read",
                "params": {
                    "cwd": str(cwd),
                    "includeLayers": True,
                },
            }
        )
        send(
            {
                "id": 3,
                "method": "skills/list",
                "params": {
                    "cwds": [str(cwd)],
                    "forceReload": True,
                },
            }
        )
        receive_until({2, 3})
        config_response = find_response(messages, 2)
        skills_response = find_response(messages, 3)

        initialize_result = initialize_response.get("result")
        if not isinstance(initialize_result, dict):
            raise RuntimeError("initialize response has no object result")

        if "error" in config_response:
            raise RuntimeError(f"config/read returned error: {config_response['error']}")
        config_result = config_response.get("result")
        if not isinstance(config_result, dict):
            raise RuntimeError("config/read response has no object result")
        config = config_result.get("config")
        if not isinstance(config, dict):
            raise RuntimeError("config/read result has no config object")
        desktop = config.get("desktop")
        locale = desktop.get("localeOverride") if isinstance(desktop, dict) else None

        report.update(
            {
                "initialize_codex_home": initialize_result.get("codexHome"),
                "user_agent": initialize_result.get("userAgent"),
                "config_locale_override": locale,
                "skills": summarize_skills(skills_response, stock_skill_ids),
            }
        )
        report["status"] = "PASS"
    except Exception as exc:
        report["failure"] = str(exc)
    finally:
        process.stdin.close()
        try:
            report["exit_code"] = process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            report["exit_code"] = None
            if report.get("status") == "PASS":
                report["status"] = "FAIL"
                report["failure"] = (
                    "temporary app-server did not exit after stdin EOF"
                )
        stdout_thread.join(timeout=2)
        stderr_thread.join(timeout=2)
        while True:
            try:
                line = stdout_lines.get_nowait()
            except queue.Empty:
                break
            if line:
                raw_stdout.append(line)
                messages.extend(parse_json_lines(line))
        stderr_text = "".join(stderr_chunks)
        if report.get("status") != "PASS":
            if raw_stdout:
                report["stdout_tail"] = "".join(raw_stdout)[-2000:]
            if stderr_text:
                report["stderr_tail"] = stderr_text[-2000:]
    return report


def find_named_skills(root: Path) -> tuple[dict[str, list[str]], list[str]]:
    by_name: defaultdict[str, list[str]] = defaultdict(list)
    errors: list[str] = []
    if not root.is_dir():
        return {}, errors
    try:
        skill_files = sorted(root.rglob("SKILL.md"))
    except OSError as exc:
        return {}, [f"cannot scan {root}: {exc}"]
    for skill_file in skill_files:
        try:
            name = frontmatter_value(read_text(skill_file), "name")
        except OSError as exc:
            errors.append(f"cannot read {skill_file}: {exc}")
            continue
        if name:
            by_name[name].append(str(skill_file))
    return dict(by_name), errors


def applicable_project_skill_roots(cwd: Path) -> list[Path]:
    roots: list[Path] = []
    candidates: list[Path] = []
    for parent in (cwd, *cwd.parents):
        candidates.extend((parent / ".agents" / "skills", parent / ".codex" / "skills"))
    canonical_skills = CANONICAL_HOME / "skills"
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        try:
            if os.path.samefile(candidate, canonical_skills):
                continue
        except OSError:
            pass
        if candidate not in roots:
            roots.append(candidate)
    return roots


def main() -> int:
    checks: dict[str, Any] = {}
    errors: list[str] = []

    script_home = Path(__file__).resolve().parents[3]
    checks["script_home"] = str(script_home)
    if normalize_windows_path(script_home) != normalize_windows_path(CANONICAL_HOME):
        errors.append(
            f"validator resolved under {script_home}, expected {CANONICAL_HOME}"
        )

    configured_home = user_codex_home()
    process_home_value = os.environ.get("CODEX_HOME")
    home_identity = validate_home_identity(
        canonical_home=CANONICAL_HOME,
        compat_home=COMPAT_HOME,
        process_home=Path(process_home_value) if process_home_value else None,
        user_home=Path(configured_home) if configured_home else None,
    )
    checks["home_identity"] = home_identity["checks"]
    errors.extend(home_identity["errors"])

    authority_topology = validate_stock_authority_topology(CANONICAL_HOME)
    checks["stock_authority_topology"] = authority_topology
    errors.extend(authority_topology["errors"])

    agents_errors = validate_agents_stock_routing(CANONICAL_HOME / "AGENTS.md")
    checks["stock_routing_agents_errors"] = agents_errors
    errors.extend(agents_errors)

    config_path = CANONICAL_HOME / "config.toml"
    config_locale: Any = None
    if not config_path.is_file():
        errors.append(f"active config is missing: {config_path}")
    else:
        try:
            with config_path.open("rb") as config_file:
                config = tomllib.load(config_file)
            desktop = config.get("desktop")
            if isinstance(desktop, dict):
                config_locale = desktop.get("localeOverride")
        except (OSError, tomllib.TOMLDecodeError) as exc:
            errors.append(f"cannot parse active config {config_path}: {exc}")
    checks["persisted_desktop_locale_override"] = config_locale
    checks["app_server_executable"] = str(APP_SERVER_EXE)

    skills_root = CANONICAL_HOME / "skills"
    manifest_path = (
        skills_root / "stock-unified" / "references" / "stock_skill_ids.json"
    )
    try:
        manifest = load_stock_catalog(
            catalog_path=manifest_path,
            skills_root=skills_root,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"cannot read stock skill manifest {manifest_path}: {exc}")
        manifest = {}
    skill_ids = manifest.get("skills")
    if not isinstance(skill_ids, list) or not all(
        isinstance(item, str) and item for item in skill_ids
    ):
        errors.append(f"invalid stock skill manifest: {manifest_path}")
        skill_ids = []

    checks["stock_skill_count"] = len(skill_ids)
    checks["stock_skill_directory_ids_unique"] = len(skill_ids) == len(set(skill_ids))
    if len(skill_ids) != len(set(skill_ids)):
        errors.append("stock skill manifest contains duplicate directory ids")

    stock_names: defaultdict[str, list[str]] = defaultdict(list)
    samefile_count = 0
    implicit_true: list[str] = []
    implicit_false: list[str] = []
    implicit_unset: list[str] = []

    for skill_id in skill_ids:
        canonical_skill = skills_root / skill_id / "SKILL.md"
        compat_skill = COMPAT_HOME / "skills" / skill_id / "SKILL.md"
        metadata_path = skills_root / skill_id / "agents" / "openai.yaml"

        if not canonical_skill.is_file():
            errors.append(f"stock skill entrypoint is missing: {canonical_skill}")
            continue
        try:
            skill_name = frontmatter_value(read_text(canonical_skill), "name")
        except OSError as exc:
            errors.append(f"cannot read stock skill {canonical_skill}: {exc}")
            continue
        if skill_name is None:
            errors.append(f"stock skill frontmatter name is missing: {canonical_skill}")
        else:
            stock_names[skill_name].append(str(canonical_skill))
            if skill_name != skill_id:
                errors.append(
                    f"stock skill name mismatch: directory={skill_id!r}, "
                    f"name={skill_name!r}"
                )

        if not compat_skill.is_file():
            errors.append(f"compatibility stock skill is missing: {compat_skill}")
        else:
            try:
                if os.path.samefile(canonical_skill, compat_skill):
                    samefile_count += 1
                else:
                    errors.append(
                        f"C/F stock skill files are different entities: {skill_id}"
                    )
            except OSError as exc:
                errors.append(f"cannot compare C/F stock skill {skill_id}: {exc}")

        if not metadata_path.is_file():
            implicit_unset.append(skill_id)
            errors.append(f"stock skill metadata is missing: {metadata_path}")
            continue
        try:
            policy = implicit_policy(read_text(metadata_path))
        except OSError as exc:
            implicit_unset.append(skill_id)
            errors.append(f"cannot read stock metadata {metadata_path}: {exc}")
            continue
        if policy is True:
            implicit_true.append(skill_id)
        elif policy is False:
            implicit_false.append(skill_id)
        else:
            implicit_unset.append(skill_id)
            errors.append(
                f"allow_implicit_invocation is not explicitly set: {metadata_path}"
            )

    duplicate_stock_names = {
        name: paths for name, paths in stock_names.items() if len(paths) > 1
    }
    checks["stock_frontmatter_name_count"] = len(stock_names)
    checks["duplicate_stock_frontmatter_names"] = duplicate_stock_names
    if duplicate_stock_names:
        errors.append(f"duplicate stock skill names: {duplicate_stock_names}")
    if len(stock_names) != len(skill_ids):
        errors.append(
            f"stock frontmatter has {len(stock_names)} unique names, "
            f"expected {len(skill_ids)}"
        )

    checks["c_f_samefile_count"] = samefile_count
    if samefile_count != len(skill_ids):
        errors.append(
            f"only {samefile_count}/{len(skill_ids)} C/F stock skill files "
            "are the same entity"
        )

    checks["implicit_true"] = implicit_true
    checks["implicit_false_count"] = len(implicit_false)
    checks["implicit_unset"] = implicit_unset
    if implicit_true != [DEFAULT_STOCK_SKILL]:
        errors.append(
            "implicit stock metadata must enable exactly "
            f"{DEFAULT_STOCK_SKILL!r}; found {implicit_true}"
        )
    if len(implicit_false) != max(0, len(skill_ids) - 1):
        errors.append(
            f"explicit-only stock metadata count is {len(implicit_false)}, "
            f"expected {max(0, len(skill_ids) - 1)}"
        )

    stock_id_set = set(skill_ids)
    project_intersections: dict[str, list[str]] = {}
    project_scan_errors: list[str] = []
    project_roots = applicable_project_skill_roots(Path.cwd().resolve())
    for root in project_roots:
        names, scan_errors = find_named_skills(root)
        project_scan_errors.extend(scan_errors)
        for name in sorted(stock_id_set.intersection(names)):
            project_intersections.setdefault(name, []).extend(names[name])
    checks["applicable_project_skill_roots"] = [str(root) for root in project_roots]
    checks["project_stock_name_intersections"] = project_intersections
    checks["project_skill_scan_errors"] = project_scan_errors
    if project_intersections:
        errors.append(
            f"project skill roots contain duplicate stock names: {project_intersections}"
        )
    errors.extend(project_scan_errors)

    plugin_root = CANONICAL_HOME / "plugins" / "cache"
    plugin_names, plugin_scan_errors = find_named_skills(plugin_root)
    plugin_intersections = {
        name: plugin_names[name]
        for name in sorted(stock_id_set.intersection(plugin_names))
    }
    checks["plugin_stock_name_intersections"] = plugin_intersections
    checks["plugin_skill_scan_errors"] = plugin_scan_errors
    if plugin_intersections:
        errors.append(
            f"plugin cache contains duplicate stock names: {plugin_intersections}"
        )
    errors.extend(plugin_scan_errors)

    if not APP_SERVER_EXE.is_file():
        errors.append(f"temporary app-server executable is missing: {APP_SERVER_EXE}")
        runtime_reports: dict[str, Any] = {}
    else:
        runtime_reports = {
            "canonical_env": probe_app_server(
                CANONICAL_HOME,
                Path.cwd().resolve(),
                skill_ids,
            ),
            "compat_env": probe_app_server(
                COMPAT_HOME,
                Path.cwd().resolve(),
                skill_ids,
            ),
        }
    checks["runtime_reports"] = runtime_reports

    for label, report in runtime_reports.items():
        if report.get("status") != "PASS":
            errors.append(f"{label} app-server probe failed: {report.get('failure')}")
            continue
        if report.get("exit_code") != 0:
            errors.append(
                f"{label} temporary app-server exit code is "
                f"{report.get('exit_code')!r}, expected 0"
            )
        initialize_home_value = report.get("initialize_codex_home")
        initialize_home = (
            Path(str(initialize_home_value))
            if initialize_home_value
            else None
        )
        if initialize_home is None or not same_physical_home(
            initialize_home,
            CANONICAL_HOME,
        ):
            errors.append(
                f"{label} initialize codexHome is "
                f"{initialize_home_value!r}, expected physical home "
                f"{str(CANONICAL_HOME)!r}"
            )
        summary = report.get("skills")
        if not isinstance(summary, dict):
            errors.append(f"{label} skills/list summary is missing")
            continue
        if summary.get("duplicate_names"):
            errors.append(
                f"{label} skills/list has duplicate names: "
                f"{summary.get('duplicate_names')}"
            )
        if summary.get("missing_stock_names"):
            errors.append(
                f"{label} skills/list is missing stock skills: "
                f"{summary.get('missing_stock_names')}"
            )
        if summary.get("unexpected_stock_paths"):
            errors.append(
                f"{label} stock skills resolved outside canonical paths: "
                f"{summary.get('unexpected_stock_paths')}"
            )
        if summary.get("c_alias_path_count") != 0:
            errors.append(
                f"{label} skills/list exposes "
                f"{summary.get('c_alias_path_count')} compatibility paths"
            )
        if summary.get("f_canonical_path_count") != summary.get("skill_count"):
            errors.append(
                f"{label} skills/list canonical path count "
                f"{summary.get('f_canonical_path_count')} does not match "
                f"skill count {summary.get('skill_count')}"
            )
        if summary.get("unique_name_count") != summary.get("skill_count"):
            errors.append(
                f"{label} skills/list unique name count "
                f"{summary.get('unique_name_count')} does not match "
                f"skill count {summary.get('skill_count')}"
            )
        if summary.get("unique_path_count") != summary.get("skill_count"):
            errors.append(
                f"{label} skills/list unique path count "
                f"{summary.get('unique_path_count')} does not match "
                f"skill count {summary.get('skill_count')}"
            )
        if summary.get("scan_errors"):
            errors.append(
                f"{label} skills/list reported scan errors: "
                f"{summary.get('scan_errors')}"
            )

    status = "PASS" if not errors else "FAIL"
    result = {
        "status": status,
        "checks": checks,
        "error_count": len(errors),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
