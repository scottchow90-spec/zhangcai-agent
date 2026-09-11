#!/usr/bin/env python3
"""Canonical execution runtime for local Codex stock skills."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any
from collections.abc import Callable, Iterator

if os.name == "nt":
    import msvcrt
else:  # pragma: no cover - this runtime is deployed on Windows.
    import fcntl

RUNTIME_ID = "stock-canonical-runtime-v3"
PAYLOAD_ROOT = Path(__file__).resolve().parents[1]
_configured_skills_root = os.environ.get("STOCK_SKILLS_ROOT", "").strip()
_bundled_skills_root = PAYLOAD_ROOT / "harness-skills"
if not _bundled_skills_root.is_dir():
    _bundled_skills_root = PAYLOAD_ROOT / "skills"
SKILLS_ROOT = Path(_configured_skills_root) if _configured_skills_root else _bundled_skills_root
STOCK_UNIFIED_SCRIPTS = SKILLS_ROOT / "stock-unified" / "scripts"
if str(STOCK_UNIFIED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(STOCK_UNIFIED_SCRIPTS))

from stock_contract_catalog import (
    DELIVERY_POLICY,
    contract_catalog_preflight,
    load_stock_catalog,
    normalize_workflow_name,
)
from stock_evidence_set import (
    EvidenceSetError,
    artifact_path as evidence_artifact_path,
    load_evidence_set,
    validate_batch_id,
    write_evidence_set,
)
from stock_production_readiness import (
    DATA_GATE_SCHEMA,
    MAX_PROCESS_OUTPUT_BYTES,
    PRODUCTION_POLICY,
    PRODUCTION_READINESS_SCHEMA,
    RECEIPT_VERSION,
    atomic_write_json,
    atomic_write_text,
    classify_failure,
    evaluate_business_result,
    production_policy_sha256,
    request_fingerprint,
    validate_receipt_schema,
    validate_request_arguments,
)


CATALOG_PATH = SKILLS_ROOT / "stock-unified" / "references" / "stock_skill_ids.json"
CONTRACTS_PATH = SKILLS_ROOT / "stock-unified" / "references" / "stock_execution_contracts.json"
SYNC_CONTRACTS_PATH = STOCK_UNIFIED_SCRIPTS / "sync_stock_execution_contracts.py"
LIANBAN_CLIENT_PATH = Path(os.environ.get("STOCK_LIANBAN_CLIENT", str(Path(__file__).resolve().parent / "lianban_daily_client.py")))
DUANXIANXIA_CLIENT_PATH = (
    SKILLS_ROOT
    / "a-share-hotspot-sentiment-analysis"
    / "scripts"
    / "duanxianxia_client.ps1"
)
STOCK_EVIDENCE_ROOT = SKILLS_ROOT.parent / "reports" / "stock-evidence-sets"
STOCK_BATCH_ID_ENV = "CODEX_STOCK_BATCH_ID"
STOCK_BUSINESS_LOCK_PATH = Path(os.environ.get(
    "STOCK_BUSINESS_LOCK_PATH",
    str(PAYLOAD_ROOT / ".runtime" / "stock-business-runtime.lock"),
))
STOCK_LIANBAN_CACHE_ROOT = Path(os.environ.get(
    "CODEX_STOCK_LIANBAN_CACHE_ROOT",
    str(PAYLOAD_ROOT / ".cache" / "lianban-daily"),
))
STOCK_BUSINESS_MAX_WAIT_SECONDS = 600.0
STOCK_LIANBAN_OPTIONAL_TIMEOUT_SECONDS = 8
STOCK_LIANBAN_REQUIRED_TIMEOUT_SECONDS = 45
STOCK_LIANBAN_CACHE_TTL_SECONDS = 900
STOCK_LIANBAN_NEGATIVE_CACHE_SECONDS = 60
STOCK_BUSINESS_LEASE_ERROR = "STOCK_BUSINESS_LEASE_TIMEOUT"
STOCK_BUSINESS_LEASE_TOKEN_ENV = "CODEX_STOCK_BUSINESS_LEASE_TOKEN"
STOCK_BUSINESS_LEASE_ID_ENV = "CODEX_STOCK_BUSINESS_LEASE_ID"
STOCK_BUSINESS_LEASE_LOCK_ENV = "CODEX_STOCK_BUSINESS_LEASE_LOCK_PATH"
FAILURE_TOKENS = (
    '"status": "BLOCKED"',
    '"status":"BLOCKED"',
    '"status": "FAILED"',
    '"status":"FAILED"',
    '"status": "FAIL"',
    '"status":"FAIL"',
    '"status": "ERROR"',
    '"status":"ERROR"',
    '"status": "PROCEDURAL"',
    '"status":"PROCEDURAL"',
    '"status": "DATA_REQUIRED"',
    '"status":"DATA_REQUIRED"',
    '"status": "DATA_STALE"',
    '"status":"DATA_STALE"',
    "Traceback (most recent call last)",
    "TIMEOUT after ",
)
FORMATTED_DELIVERY_EXTENSIONS = {
    ".docx",
    ".htm",
    ".html",
    ".mp4",
    ".pdf",
    ".pptx",
    ".xlsx",
}
CLEAN_DELIVERY_STATUSES = {"CLEAN_PASS", "PASS", "SUCCESS", "VERIFIED"}
TEMPLATE_BINDING_TOKENS = ("template", "模板")
VALIDATOR_BINDING_TOKENS = (
    "audit",
    "check",
    "gate",
    "validate",
    "validation",
    "validator",
    "verify",
    "审计",
    "校验",
    "验证",
)
TDX_PROCESS_INTEGRITY_ERROR = "TDX_PROCESS_INTEGRITY_VIOLATION"
TDX_MAIN_PROCESS_NAME = "tdxw"
TDX_PROTECTED_PROCESS_NAMES = frozenset({"tdxw", "tdxcef"})
TDX_GUARD_BOOTSTRAP_DIR = (
    Path(__file__).resolve().parent / "stock_runtime_bootstrap"
)
TDX_GUARD_BOOTSTRAP_FILES = {
    "sitecustomize.py": "b101151ab8a66d264bad58bc82f8cb5d2e971d193f0d0b28799a7b882c3eba27",
    "tdx_process_guard.py": "884c84e8e69bdac0f35ba7f06c6f6e97925698a8af4a06d514b0631b3060f834",
}
TDX_EXECUTABLE_SOURCE_SUFFIXES = frozenset(
    {".bat", ".cmd", ".js", ".ps1", ".py", ".ts", ".vbs"}
)
TDX_SOURCE_TARGET_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:tdxw|tdxcef)(?:\.exe)?(?![A-Za-z0-9])",
    re.IGNORECASE,
)
TDX_SOURCE_CONTROL_RE = re.compile(
    r"(?:"
    r"Stop-Process|taskkill|tskill|TerminateProcess|CloseMainWindow|"
    r"\.Kill\s*\(|\.Terminate\s*\(|shutdown|Restart-Computer|Stop-Computer|"
    r"OpenProcess|VirtualAllocEx|WriteProcessMemory|CreateRemoteThread|"
    r"QueueUserAPC|NtSuspendProcess|SuspendThread|ResumeThread|"
    r"PostMessage|SendMessage|WM_CLOSE|0x0010"
    r")",
    re.IGNORECASE,
)
TDX_PROCESS_ROLES = frozenset({
    "authorize",
    "business",
    "contract_check",
    "contract_sync",
    "read_only",
    "route",
    "supplemental",
    "test",
    "verify",
})
MANIFEST_VALIDATION_TOKENS = (
    "audit",
    "check",
    "gate",
    "validate",
    "validation",
    "validator",
    "verify",
    "审计",
    "校验",
    "验证",
)


class StockBusinessLeaseTimeout(RuntimeError):
    pass


def workflow_lock_path(skill_id: str) -> Path:
    normalized = re.sub(r"[^a-z0-9-]+", "-", skill_id.casefold()).strip("-")
    if not normalized:
        raise ValueError("stock_business_lock_skill_id_invalid")
    return STOCK_BUSINESS_LOCK_PATH.with_name(
        f"{STOCK_BUSINESS_LOCK_PATH.stem}.{normalized}{STOCK_BUSINESS_LOCK_PATH.suffix}"
    )


def workflow_lock_timeout(contract: dict[str, Any]) -> float:
    configured = os.environ.get("CODEX_STOCK_BUSINESS_WAIT_SECONDS", "").strip()
    if configured:
        try:
            value = float(configured)
        except ValueError as exc:
            raise ValueError("stock_business_wait_seconds_invalid") from exc
        if value <= 0:
            raise ValueError("stock_business_wait_seconds_invalid")
        return min(value, STOCK_BUSINESS_MAX_WAIT_SECONDS)
    business_timeout = max(1.0, float(contract.get("timeout_seconds", 300)))
    return min(max(60.0, business_timeout + 60.0), STOCK_BUSINESS_MAX_WAIT_SECONDS)


def _lock_file_nonblocking(handle: Any) -> None:
    handle.seek(0)
    if os.name == "nt":
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:  # pragma: no cover - this runtime is deployed on Windows.
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_file(handle: Any) -> None:
    handle.seek(0)
    if os.name == "nt":
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:  # pragma: no cover - this runtime is deployed on Windows.
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _inherited_stock_business_lease(
    skill_id: str,
    path: Path,
    owner_path: Path,
) -> dict[str, Any] | None:
    token = os.environ.get(STOCK_BUSINESS_LEASE_TOKEN_ENV, "")
    inherited_lease_id = os.environ.get(STOCK_BUSINESS_LEASE_ID_ENV, "")
    inherited_lock_path = os.environ.get(STOCK_BUSINESS_LEASE_LOCK_ENV, "")
    if not token or not inherited_lease_id or not inherited_lock_path:
        return None
    try:
        if Path(inherited_lock_path).resolve() != path:
            return None
        owner = json.loads(owner_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    token_sha256 = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if (
        owner.get("lease_id") != inherited_lease_id
        or owner.get("lease_token_sha256") != token_sha256
        or owner.get("lock_path") != str(path)
    ):
        return None
    return {
        "status": "REENTRANT",
        "lease_id": f"{os.getpid()}-{time.time_ns()}",
        "root_lease_id": inherited_lease_id,
        "root_skill_id": owner.get("skill_id"),
        "skill_id": skill_id,
        "pid": os.getpid(),
        "owner_pid": owner.get("pid"),
        "lock_path": str(path),
        "acquired_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "waited_seconds": 0.0,
    }


@contextmanager
def stock_business_lease(
    skill_id: str,
    *,
    lock_path: Path = STOCK_BUSINESS_LOCK_PATH,
    timeout_seconds: float | None = None,
    poll_seconds: float = 0.1,
) -> Iterator[dict[str, Any]]:
    """Serialize callers sharing one explicit stock resource lock."""
    path = Path(lock_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    owner_path = path.with_name(path.name + ".owner.json")
    inherited = _inherited_stock_business_lease(skill_id, path, owner_path)
    if inherited is not None:
        yield inherited
        return
    started = time.monotonic()
    deadline = None if timeout_seconds is None else started + timeout_seconds
    lease_id = f"{os.getpid()}-{time.time_ns()}"
    lease_token = os.urandom(32).hex()
    lease_environment = {
        STOCK_BUSINESS_LEASE_TOKEN_ENV: lease_token,
        STOCK_BUSINESS_LEASE_ID_ENV: lease_id,
        STOCK_BUSINESS_LEASE_LOCK_ENV: str(path),
    }
    previous_environment = {
        key: os.environ.get(key) for key in lease_environment
    }
    handle = path.open("a+b")
    acquired = False
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        while True:
            try:
                _lock_file_nonblocking(handle)
                acquired = True
                break
            except OSError:
                if deadline is not None and time.monotonic() >= deadline:
                    raise StockBusinessLeaseTimeout(
                        f"{STOCK_BUSINESS_LEASE_ERROR}:{path}"
                    )
                time.sleep(max(0.01, poll_seconds))

        waited_seconds = round(time.monotonic() - started, 3)
        lease = {
            "status": "ACQUIRED",
            "lease_id": lease_id,
            "root_lease_id": lease_id,
            "root_skill_id": skill_id,
            "skill_id": skill_id,
            "pid": os.getpid(),
            "lock_path": str(path),
            "acquired_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "waited_seconds": waited_seconds,
        }
        owner = {
            **lease,
            "lease_token_sha256": hashlib.sha256(
                lease_token.encode("utf-8")
            ).hexdigest(),
        }
        atomic_write_json(owner_path, owner)
        os.environ.update(lease_environment)
        yield lease
    finally:
        for key, value in previous_environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if acquired:
            try:
                if owner_path.is_file():
                    owner = json.loads(owner_path.read_text(encoding="utf-8"))
                    if owner.get("lease_id") == lease_id:
                        owner_path.unlink()
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                pass
            _unlock_file(handle)
        handle.close()


def _dotted_ast_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_ast_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _python_tdx_control_line(source: str) -> int | None:
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    lines = source.splitlines()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        segment = ast.get_source_segment(source, node) or _dotted_ast_name(node.func)
        if not TDX_SOURCE_CONTROL_RE.search(segment):
            continue
        line_number = int(getattr(node, "lineno", 1))
        start = max(0, line_number - 4)
        end = min(len(lines), int(getattr(node, "end_lineno", line_number)) + 3)
        nearby = "\n".join(lines[start:end])
        if TDX_SOURCE_TARGET_RE.search(segment) or TDX_SOURCE_TARGET_RE.search(nearby):
            return line_number
    return None


def _script_tdx_control_line(source: str) -> int | None:
    lines = source.splitlines()
    executable = [
        "" if line.lstrip().startswith(("#", "//", ";")) else line
        for line in lines
    ]
    for index, line in enumerate(executable):
        if not TDX_SOURCE_CONTROL_RE.search(line):
            continue
        start = max(0, index - 3)
        end = min(len(executable), index + 4)
        if TDX_SOURCE_TARGET_RE.search("\n".join(executable[start:end])):
            return index + 1
    return None


def scan_tdx_process_control_paths(paths: list[Path]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    trusted_bootstrap_dir = TDX_GUARD_BOOTSTRAP_DIR.resolve()
    for raw_path in paths:
        path = Path(raw_path).resolve()
        if path.suffix.casefold() not in TDX_EXECUTABLE_SOURCE_SUFFIXES:
            continue
        expected_bootstrap_hash = (
            TDX_GUARD_BOOTSTRAP_FILES.get(path.name)
            if path.parent == trusted_bootstrap_dir
            else None
        )
        if expected_bootstrap_hash is not None:
            try:
                actual_bootstrap_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                actual_bootstrap_hash = ""
            if actual_bootstrap_hash == expected_bootstrap_hash:
                # The guard necessarily contains the forbidden process-control
                # vocabulary it intercepts.  Exempt only the exact hash-pinned
                # bootstrap file; any byte drift falls through to the normal scan.
                continue
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append({
                "path": str(path),
                "line": None,
                "reason": f"tdx_process_control_scan_failed:{type(exc).__name__}",
            })
            continue
        line = (
            _python_tdx_control_line(source)
            if path.suffix.casefold() == ".py"
            else _script_tdx_control_line(source)
        )
        if line is not None:
            findings.append({
                "path": str(path),
                "line": line,
                "reason": "tdx_process_control_detected",
            })
    return findings


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_hash(payload: dict[str, Any], excluded: str) -> str:
    material = {key: value for key, value in payload.items() if key != excluded}
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(encoded)


def contract_sha256(contract: dict[str, Any]) -> str:
    return canonical_hash(contract, "contract_sha256")


def receipt_integrity(receipt: dict[str, Any]) -> str:
    return canonical_hash(receipt, "receipt_integrity")


def load_contracts() -> dict[str, dict[str, Any]]:
    payload = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))
    rows = payload.get("contracts", [])
    return {str(row["skill_id"]): row for row in rows}


INTENT_ACTION_PATTERN = (
    r"(?:做成|将|把|做|使用|进行|合并|整合|综合|构建|建立|形成|设计|规划)"
)
INTENT_ORDER_ADVERB_PATTERN = r"(?:先|暂时?)?"
INTENT_NEGATION_CONTROL_PATTERN = (
    rf"(?:{INTENT_ORDER_ADVERB_PATTERN}"
    r"(?:禁止|无需|不需要|不必|不要|不能|不应|(?<!分)别|拒绝)"
    rf"|{INTENT_ORDER_ADVERB_PATTERN}不(?={INTENT_ACTION_PATTERN})|而非)"
)
INTENT_CANCELLATION_CONTROL_PATTERN = (
    rf"{INTENT_ORDER_ADVERB_PATTERN}(?:取消|停止|暂停|放弃|撤销|暂缓)"
)
INTENT_CONTROL_PATTERN = (
    rf"(?:{INTENT_NEGATION_CONTROL_PATTERN}|"
    rf"{INTENT_CANCELLATION_CONTROL_PATTERN})"
)
INTENT_CURRENT_CANCELLATION_TARGET_PATTERN = (
    r"(?:该任务|该评分|此任务|这个任务|上述评分|前述任务)"
)
INTENT_OTHER_CANCELLATION_TARGET_PATTERN = (
    r"(?:旧版|原有|旧(?:的)?|其他|别的|另一个?)"
)
INTENT_INTEGRATED_TARGET_CUE_PATTERN = (
    r"(?:大牛线|飞龙在天|游资资金监控|庄家资金监控|机构资金监控|"
    r"五公式|三公式|三体系|综合评分|评分体系|评分系统|30项|51项)"
)
INTENT_CONTINUATION_BOUNDARY_PATTERN = r"(?:然后|随后|接着)"
INTENT_CONTRAST_BOUNDARY_PATTERN = r"(?:但是|不过|可是|然而|却)"
INTENT_EXPLANATION_CUES = ("解释", "比较", "各自", "为什么")
INTENT_POSITIVE_ACTIONS = (
    "再将",
    "再使用",
    "并将",
    "并把",
    "并使用",
    "并做",
    "并进行",
    "做成",
    "构建",
    "建立",
    "形成",
    "整合",
    "合并",
    "设计",
    "规划",
    "使用",
    "仅保留",
    "优化",
)


def intent_segments(query: str) -> list[str]:
    return [
        segment
        for segment in re.split(
            r"[，,；;。！？!?\n]+|"
            r"(?=(?:而是|而非|但是|不过|可是|然而|反而|改为|然后|"
            r"随后|接着|再(?:将|使用|把)|并(?:将|把|使用|做|进行)|"
            r"但|却))",
            query,
        )
        if segment
    ]


def cancellation_target_kind(text_after_control: str) -> str:
    target = text_after_control.lstrip()
    target = re.sub(r"^(?:(?:了|掉|一下|执行|进行)\s*)+", "", target)
    if not target:
        return "implicit_current"
    if re.match(INTENT_CURRENT_CANCELLATION_TARGET_PATTERN, target):
        return "current"
    if re.match(INTENT_OTHER_CANCELLATION_TARGET_PATTERN, target):
        return "other"
    return "unspecified"


def control_targets_trigger(
    text_after_control: str,
    *,
    strip_leading_action: bool = False,
) -> bool:
    target = text_after_control.lstrip()
    if strip_leading_action:
        action = re.match(INTENT_ACTION_PATTERN, target)
        if action is not None:
            target = target[action.end():]
    target_kind = cancellation_target_kind(target)
    if target_kind in ("current", "implicit_current"):
        return True
    if target_kind == "other":
        return False
    return re.search(INTENT_INTEGRATED_TARGET_CUE_PATTERN, target) is not None


def cancellation_before_targets_trigger(before_window: str) -> bool:
    for control in re.finditer(INTENT_CANCELLATION_CONTROL_PATTERN, before_window):
        target_text = before_window[control.end():]
        if control_targets_trigger(target_text):
            return True
    return False


def cancellation_after_targets_trigger(after_window: str) -> bool:
    for control in re.finditer(INTENT_CANCELLATION_CONTROL_PATTERN, after_window):
        intervening = after_window[:control.start()]
        if re.search(INTENT_ACTION_PATTERN, intervening):
            continue
        if control_targets_trigger(after_window[control.end():]):
            return True
    return False


def following_segment_controls_trigger(
    segments: list[str],
    segment_index: int,
) -> bool:
    if segment_index + 1 >= len(segments):
        return False
    following = segments[segment_index + 1].lstrip()
    cancellation = re.match(
        rf"{INTENT_CONTINUATION_BOUNDARY_PATTERN}\s*"
        rf"{INTENT_CANCELLATION_CONTROL_PATTERN}",
        following,
    )
    if cancellation is not None:
        return control_targets_trigger(following[cancellation.end():])
    negation = re.match(
        rf"(?:{INTENT_CONTINUATION_BOUNDARY_PATTERN}|"
        rf"{INTENT_CONTRAST_BOUNDARY_PATTERN})\s*"
        rf"{INTENT_NEGATION_CONTROL_PATTERN}",
        following,
    )
    if negation is not None:
        return control_targets_trigger(
            following[negation.end():],
            strip_leading_action=True,
        )
    return False


def has_positive_integrated_intent(
    query: str,
    trigger_patterns: tuple[str, ...],
) -> bool:
    segments = intent_segments(query)
    for segment_index, segment in enumerate(segments):
        for pattern in trigger_patterns:
            for trigger in re.finditer(pattern, segment):
                before_window = segment[max(0, trigger.start() - 96):trigger.start()]
                after_window = segment[trigger.end():trigger.end() + 24]
                local_context = before_window + trigger.group(0)
                negated_action = re.search(
                    INTENT_NEGATION_CONTROL_PATTERN
                    + r".{0,3}"
                    + INTENT_ACTION_PATTERN,
                    before_window,
                )
                near_pre_negation = re.search(
                    INTENT_NEGATION_CONTROL_PATTERN + r".{0,4}$",
                    before_window,
                )
                post_negation = re.search(
                    INTENT_NEGATION_CONTROL_PATTERN,
                    after_window,
                )
                if (
                    negated_action
                    or near_pre_negation
                    or post_negation
                    or cancellation_before_targets_trigger(before_window)
                    or cancellation_after_targets_trigger(after_window)
                    or following_segment_controls_trigger(segments, segment_index)
                ):
                    continue
                explanation_position = max(
                    (local_context.rfind(cue) for cue in INTENT_EXPLANATION_CUES),
                    default=-1,
                )
                if explanation_position >= 0:
                    action_position = max(
                        (
                            local_context.rfind(action)
                            for action in INTENT_POSITIVE_ACTIONS
                        ),
                        default=-1,
                    )
                    if action_position <= explanation_position:
                        continue
                return True
    return False


def fold_integrated_workflows(
    selected: list[str],
    selected_matches: list[dict[str, Any]],
    *,
    owner: str,
    component_ids: tuple[str, ...],
    match_type: str,
) -> tuple[list[str], list[dict[str, Any]]]:
    component_set = set(component_ids)
    earliest_component_match = next(
        match
        for skill_id, match in zip(selected, selected_matches)
        if skill_id in component_set
    )
    integrated_match = {
        **earliest_component_match,
        "skill_id": owner,
        "match_type": match_type,
        "absorbed_skill_ids": [
            skill_id for skill_id in component_ids
            if skill_id != owner
        ],
    }
    folded_selected: list[str] = []
    folded_matches: list[dict[str, Any]] = []
    owner_emitted = False
    for skill_id, match in zip(selected, selected_matches):
        if skill_id in component_set:
            if not owner_emitted:
                folded_selected.append(owner)
                folded_matches.append(integrated_match)
                owner_emitted = True
            continue
        folded_selected.append(skill_id)
        folded_matches.append(match)
    return folded_selected, folded_matches


def route_stock_query(
    query: str,
    *,
    catalog_path: Path = CATALOG_PATH,
    skills_root: Path = SKILLS_ROOT,
) -> dict[str, Any]:
    catalog = load_stock_catalog(
        catalog_path=catalog_path,
        skills_root=skills_root,
    )
    skill_ids = list(catalog["skills"])
    normalized_query = normalize_workflow_name(query)
    matches: list[dict[str, Any]] = []
    custom_board_name_spans = [
        match.span("names")
        for match in re.finditer(
            r"(?:名为|名称为|叫做)(?P<names>.+?)的自定义板块",
            normalized_query,
        )
    ]

    explicit_pattern = re.compile(r"\$([a-z0-9][a-z0-9-]*)", re.IGNORECASE)
    for match in explicit_pattern.finditer(normalized_query):
        skill_id = match.group(1).casefold()
        if skill_id not in skill_ids:
            explicit_alias = f"${skill_id}"
            skill_id = next(
                (
                    canonical_skill_id
                    for canonical_skill_id, names in catalog["workflow_names"].items()
                    if explicit_alias
                    in {
                        normalize_workflow_name(raw_name)
                        for raw_name in names
                        if normalize_workflow_name(raw_name).startswith("$")
                    }
                ),
                "",
            )
            if not skill_id:
                raise ValueError(
                    f"unknown_explicit_stock_skill_id:{match.group(1).casefold()}"
                )
        matches.append({
            "start": match.start(),
            "end": match.end(),
            "skill_id": skill_id,
            "matched": match.group(0),
            "match_type": "explicit_skill_id",
        })

    workflow_candidates: list[dict[str, Any]] = []
    for skill_id, names in catalog["workflow_names"].items():
        for raw_name in names:
            name = normalize_workflow_name(raw_name)
            start = normalized_query.find(name)
            while start >= 0:
                end = start + len(name)
                if any(
                    span_start <= start and end <= span_end
                    for span_start, span_end in custom_board_name_spans
                ):
                    start = normalized_query.find(name, start + 1)
                    continue
                workflow_candidates.append({
                    "start": start,
                    "end": end,
                    "skill_id": skill_id,
                    "matched": raw_name,
                    "match_type": "exact_workflow_name",
                })
                start = normalized_query.find(name, start + 1)

    accepted_workflows: list[dict[str, Any]] = []
    for candidate in sorted(
        workflow_candidates,
        key=lambda row: (
            -(int(row["end"]) - int(row["start"])),
            int(row["start"]),
            str(row["skill_id"]),
        ),
    ):
        overlaps_longer = any(
            int(candidate["start"]) < int(existing["end"])
            and int(existing["start"]) < int(candidate["end"])
            for existing in accepted_workflows
        )
        if not overlaps_longer:
            accepted_workflows.append(candidate)

    matches.extend(accepted_workflows)
    matches.sort(
        key=lambda row: (
            int(row["start"]),
            0 if row["match_type"] == "explicit_skill_id" else 1,
            -(int(row["end"]) - int(row["start"])),
        )
    )

    selected: list[str] = []
    selected_matches: list[dict[str, Any]] = []
    for row in matches:
        skill_id = str(row["skill_id"])
        if skill_id in selected:
            continue
        selected.append(skill_id)
        selected_matches.append(row)

    # 五公式科学评分与既有三体系综合评分都由大牛线统一入口持有。
    # 普通多流程请求保留用户顺序，显式 $skill-id 绝不被吸收。
    composite_owner = "big-bull-analysis-scoring-system"
    five_formula_systems = (
        composite_owner,
        "feilong-strategy",
        "youzi-capital-monitoring",
        "zhuangjia-capital-monitoring",
        "jigou-capital-monitoring",
    )
    has_explicit_selection = any(
        row.get("match_type") == "explicit_skill_id"
        for row in selected_matches
    )
    five_formula_systems_selected = all(
        skill_id in selected for skill_id in five_formula_systems
    )
    explicit_five_formula_intent = has_positive_integrated_intent(
        normalized_query,
        (
            r"五公式科学评分",
            r"五公式综合评分",
            r"51项评分",
            r"科学规划评分权重",
            r"(?:做成|构建|建立|形成|整合|合并|设计|规划).{0,12}"
            r"科学的评分体系",
            r"回测基础上.{0,16}(?:评分|权重)",
        ),
    )
    five_formula_intent = (
        not has_explicit_selection
        and five_formula_systems_selected
        and explicit_five_formula_intent
    )
    if five_formula_intent:
        selected, selected_matches = fold_integrated_workflows(
            selected,
            selected_matches,
            owner=composite_owner,
            component_ids=five_formula_systems,
            match_type="integrated_five_formula_owner",
        )

    composite_systems = (
        composite_owner,
        "feilong-strategy",
        "zhuangjia-capital-monitoring",
    )
    composite_intent = has_positive_integrated_intent(
        normalized_query,
        (
            r"大牛线\s*16\s*项.{0,80}飞龙在天\s*10\s*项"
            r".{0,80}庄家资金监控\s*4\s*项",
            r"综合评分",
            r"三公式综合",
            r"三体系综合",
            r"30项评分",
            r"固定30项",
            r"评分系统.{0,24}(?:仅保留|优化|全局修改)",
        ),
    )
    if (
        not five_formula_intent
        and not five_formula_systems_selected
        and composite_intent
        and not has_explicit_selection
        and all(skill_id in selected for skill_id in composite_systems)
    ):
        selected, selected_matches = fold_integrated_workflows(
            selected,
            selected_matches,
            owner=composite_owner,
            component_ids=composite_systems,
            match_type="integrated_composite_owner",
        )

    if not selected:
        global_confusion_correction = (
            "全局" in normalized_query
            and "技能" in normalized_query
            and any(
                token in normalized_query
                for token in ("混淆", "冲突", "串用", "错用", "纠正")
            )
        )
        governance_scope = any(
            token in normalized_query
            for token in (
                "股票技能",
                "股票工作流",
                "股票技能工作流",
                "所有股票技能",
            )
        )
        governance_control = any(
            token in normalized_query
            for token in (
                "审计",
                "治理",
                "硬闸",
                "绕过",
                "模板",
                "漂移",
                "偏离",
                "严格按照",
                "确保",
            )
        )
        governance_inventory = any(
            token in normalized_query
            for token in (
                "几套",
                "多少套",
                "有哪些",
                "清单",
                "盘点",
                "统计",
                "数量",
            )
        )
        governance_exhaustive_continuation = (
            "每个技能" in normalized_query
            and "每个流程" in normalized_query
            and governance_control
        )
        if global_confusion_correction or (
            governance_scope and (governance_control or governance_inventory)
        ) or governance_exhaustive_continuation:
            selected = ["stock-unified"]
            selected_matches = [{
                "start": None,
                "end": None,
                "skill_id": "stock-unified",
                "matched": None,
                "match_type": (
                    "global_skill_confusion_correction"
                    if global_confusion_correction
                    else (
                        "governance_exhaustive_continuation"
                        if governance_exhaustive_continuation
                        else "governance_intent"
                    )
                ),
            }]
        else:
            selected = [str(catalog["default_skill"])]
            selected_matches = [{
                "start": None,
                "end": None,
                "skill_id": selected[0],
                "matched": None,
                "match_type": "generic_default",
            }]

    return {
        "schema": "STOCK_SKILL_ROUTE_V1",
        "catalog": str(catalog_path.resolve()),
        "catalog_authority": catalog["authority"],
        "query": query,
        "skill_ids": selected,
        "matches": selected_matches,
    }


def skill_context(entry_file: str) -> tuple[Path, str, dict[str, Any]]:
    entry = Path(entry_file).resolve()
    root = entry.parents[1]
    skill_id = root.name
    contract = load_contracts().get(skill_id)
    if contract is None:
        raise KeyError(f"contract_missing:{skill_id}")
    return root, skill_id, contract


def expand_text(value: str, variables: dict[str, str]) -> str:
    return value.format_map(variables)


def expanded_execution(
    contract: dict[str, Any],
    root: Path,
    run_dir: Path,
) -> tuple[list[str], Path, dict[str, str]]:
    variables = {
        "python": sys.executable,
        "skill_id": root.name,
        "skill_root": str(root),
        "skills_root": str(SKILLS_ROOT),
        "stock_data_root": os.environ.get(
            "ONESTOCK_STOCK_DATA_ROOT",
            str(root / "reports"),
        ),
        "run_dir": str(run_dir),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "date_ymd": datetime.now().strftime("%Y%m%d"),
    }
    command = [expand_text(str(item), variables) for item in contract["business_command"]]
    cwd = Path(expand_text(str(contract["cwd"]), variables)).resolve()
    return command, cwd, variables


def validate_tdx_formula_guard() -> dict[str, Any]:
    errors: list[str] = []
    files: list[dict[str, Any]] = []
    for name, expected_sha256 in TDX_GUARD_BOOTSTRAP_FILES.items():
        path = (TDX_GUARD_BOOTSTRAP_DIR / name).resolve()
        if not path.is_file():
            errors.append(f"tdx_formula_guard_missing:{name}")
            files.append({"path": str(path), "sha256": None})
            continue
        actual_sha256 = sha256_file(path)
        files.append({"path": str(path), "sha256": actual_sha256})
        if actual_sha256 != expected_sha256:
            errors.append(f"tdx_formula_guard_hash_mismatch:{name}")
    return {
        "status": "BLOCKED" if errors else "CLEAN_PASS",
        "errors": errors,
        "files": files,
    }


def capture_tdx_process_snapshot() -> dict[str, Any]:
    captured_at = datetime.now().astimezone().isoformat(timespec="seconds")
    command = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        "$p=Get-Process -Name TdxW,tdxcef -ErrorAction SilentlyContinue; "
        "if($p){$p | Select-Object ProcessName,Id,StartTime | "
        "ConvertTo-Json -Compress}; exit 0",
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except Exception as exc:
        return {
            "status": "BLOCKED",
            "captured_at": captured_at,
            "processes": [],
            "errors": [f"tdx_process_snapshot_failed:{type(exc).__name__}:{exc}"],
        }
    if completed.returncode != 0:
        return {
            "status": "BLOCKED",
            "captured_at": captured_at,
            "processes": [],
            "errors": [
                f"tdx_process_snapshot_returncode:{completed.returncode}",
                (completed.stderr or "").strip()[-500:],
            ],
        }
    raw = (completed.stdout or "").strip()
    if not raw:
        return {
            "status": "OK",
            "captured_at": captured_at,
            "processes": [],
            "errors": [],
        }
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {
            "status": "BLOCKED",
            "captured_at": captured_at,
            "processes": [],
            "errors": [f"tdx_process_snapshot_invalid_json:{exc}"],
        }
    rows = decoded if isinstance(decoded, list) else [decoded]
    processes = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("ProcessName") or "").strip()
        pid = row.get("Id")
        start_time = str(row.get("StartTime") or "").strip()
        normalized_name = name.casefold()
        if normalized_name.endswith(".exe"):
            normalized_name = normalized_name[:-4]
        if normalized_name not in TDX_PROTECTED_PROCESS_NAMES:
            continue
        if not name or not isinstance(pid, int) or not start_time:
            return {
                "status": "BLOCKED",
                "captured_at": captured_at,
                "processes": processes,
                "errors": ["tdx_process_snapshot_incomplete_identity"],
            }
        processes.append({"name": name, "pid": pid, "start_time": start_time})
    return {
        "status": "OK",
        "captured_at": captured_at,
        "processes": processes,
        "errors": [],
    }


def _tdx_main_identities(snapshot: dict[str, Any]) -> set[tuple[int, str]]:
    identities: set[tuple[int, str]] = set()
    for row in snapshot.get("processes", []):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name", "")).strip().casefold()
        if name.endswith(".exe"):
            name = name[:-4]
        if name != TDX_MAIN_PROCESS_NAME:
            continue
        pid = row.get("pid")
        start_time = str(row.get("start_time", "")).strip()
        if isinstance(pid, int) and start_time:
            identities.add((pid, start_time))
    return identities


def _tdx_protected_identities(
    snapshot: dict[str, Any],
) -> set[tuple[str, int, str]]:
    identities: set[tuple[str, int, str]] = set()
    for row in snapshot.get("processes", []):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name", "")).strip().casefold()
        if name.endswith(".exe"):
            name = name[:-4]
        if name not in TDX_PROTECTED_PROCESS_NAMES:
            continue
        pid = row.get("pid")
        start_time = str(row.get("start_time", "")).strip()
        if isinstance(pid, int) and start_time:
            identities.add((name, pid, start_time))
    return identities


def evaluate_tdx_process_integrity(
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    if before.get("status") != "OK":
        errors.append("tdx_process_snapshot_before_failed")
    if after.get("status") != "OK":
        errors.append("tdx_process_snapshot_after_failed")
    before_main = _tdx_main_identities(before)
    after_main = _tdx_main_identities(after)
    if not errors and before_main:
        if not after_main:
            errors.append("tdx_main_process_disappeared")
        elif before_main.isdisjoint(after_main):
            errors.append("tdx_main_process_identity_changed")
    if not errors:
        missing_helpers = sorted(
            identity
            for identity in (
                _tdx_protected_identities(before)
                - _tdx_protected_identities(after)
            )
            if identity[0] != TDX_MAIN_PROCESS_NAME
        )
        errors.extend(
            f"tdx_protected_process_disappeared:{name}:{pid}"
            for name, pid, _start_time in missing_helpers
        )
    return {
        "status": "BLOCKED" if errors else "CLEAN_PASS",
        "errors": errors,
        "before": before,
        "after": after,
    }


def evaluate_tdx_process_preflight(
    snapshot: dict[str, Any],
    process_role: str,
) -> dict[str, Any]:
    errors: list[str] = []
    if process_role not in TDX_PROCESS_ROLES:
        errors.append("tdx_process_role_unclassified")
    if snapshot.get("status") != "OK":
        errors.append("tdx_process_snapshot_before_failed")
    return {
        "status": "BLOCKED" if errors else "CLEAN_PASS",
        "errors": errors,
        "process_role": process_role,
        "before": snapshot,
        "after": {
            "status": "NOT_RUN",
            "captured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "processes": [],
            "errors": ["business_child_not_started"] if errors else [],
        },
    }


def prepare_tdx_guarded_python_command(command: list[str]) -> list[str]:
    if not command:
        raise ValueError("tdx_guarded_command_empty")
    executable_name = Path(command[0]).name.casefold()
    is_python = bool(
        re.fullmatch(r"python(?:\d+(?:\.\d+)*)?(?:\.exe)?", executable_name)
    )
    if not is_python:
        return list(command)
    if len(command) < 2 or Path(command[1]).suffix.casefold() != ".py":
        raise ValueError("tdx_python_command_not_guardable")
    bootstrap = (TDX_GUARD_BOOTSTRAP_DIR / "sitecustomize.py").resolve()
    target = Path(command[1]).resolve()
    if target == bootstrap:
        return list(command)
    return [command[0], str(bootstrap), *command[1:]]


def finalize_process_result(result: dict[str, Any]) -> dict[str, Any]:
    stdout = str(result.get("stdout") or "")
    stderr = str(result.get("stderr") or "")
    stdout_bytes = int(result.get("stdout_bytes", len(stdout.encode("utf-8"))))
    stderr_bytes = int(result.get("stderr_bytes", len(stderr.encode("utf-8"))))
    output_limited = bool(result.get("output_limited")) or (
        stdout_bytes + stderr_bytes > MAX_PROCESS_OUTPUT_BYTES
    )
    if output_limited:
        per_stream_limit = MAX_PROCESS_OUTPUT_BYTES // 2
        stdout = stdout.encode("utf-8")[:per_stream_limit].decode(
            "utf-8", "ignore"
        )
        stderr = stderr.encode("utf-8")[:per_stream_limit].decode(
            "utf-8", "ignore"
        )
        stderr = (
            stderr
            + "\nPROCESS_OUTPUT_LIMIT_EXCEEDED "
            + str(MAX_PROCESS_OUTPUT_BYTES)
        ).strip()
        result["business_returncode"] = result.get("returncode")
        result["returncode"] = 122
    result["stdout"] = stdout
    result["stderr"] = stderr
    result["stdout_bytes"] = stdout_bytes
    result["stderr_bytes"] = stderr_bytes
    result["output_limited"] = output_limited
    result["timed_out"] = int(result.get("returncode", 125)) == 124
    result["failure_class"] = classify_failure(
        int(result.get("returncode", 125)),
        bool(result["timed_out"]),
        output_limited,
    )
    return result


def communicate_bounded(
    command: list[str],
    cwd: Path,
    timeout: int,
    environment: dict[str, str],
) -> dict[str, Any]:
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    if process.stdout is None or process.stderr is None:
        process.kill()
        process.wait()
        raise RuntimeError("business_process_pipe_initialization_failed")

    lock = threading.Lock()
    limit_reached = threading.Event()
    byte_counts = {"stdout": 0, "stderr": 0}

    def read_stream(stream: Any, name: str) -> bytes:
        chunks: list[bytes] = []
        retained = 0
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            with lock:
                byte_counts[name] += len(chunk)
                total = byte_counts["stdout"] + byte_counts["stderr"]
                if total > MAX_PROCESS_OUTPUT_BYTES:
                    limit_reached.set()
            if retained < MAX_PROCESS_OUTPUT_BYTES:
                keep = chunk[: MAX_PROCESS_OUTPUT_BYTES - retained]
                chunks.append(keep)
                retained += len(keep)
        return b"".join(chunks)

    timed_out = False
    with ThreadPoolExecutor(max_workers=2) as executor:
        stdout_future = executor.submit(read_stream, process.stdout, "stdout")
        stderr_future = executor.submit(read_stream, process.stderr, "stderr")
        deadline = time.monotonic() + timeout
        while process.poll() is None:
            if limit_reached.is_set():
                process.kill()
                break
            if time.monotonic() >= deadline:
                timed_out = True
                process.kill()
                break
            time.sleep(0.01)
        process.wait()
        stdout_bytes = stdout_future.result()
        stderr_bytes = stderr_future.result()

    return {
        "returncode": (
            124 if timed_out else 122 if limit_reached.is_set() else process.returncode
        ),
        "stdout": stdout_bytes.decode("utf-8", "replace"),
        "stderr": stderr_bytes.decode("utf-8", "replace"),
        "stdout_bytes": byte_counts["stdout"],
        "stderr_bytes": byte_counts["stderr"],
        "output_limited": limit_reached.is_set(),
        "timed_out": timed_out,
    }


def run_process(
    command: list[str],
    cwd: Path,
    timeout: int,
    extra_environment: dict[str, str] | None = None,
    *,
    process_role: str = "business",
) -> dict[str, Any]:
    started_wall = datetime.now().astimezone().isoformat(timespec="seconds")
    started = time.monotonic()
    formula_guard = validate_tdx_formula_guard()
    if formula_guard["status"] != "CLEAN_PASS":
        return finalize_process_result({
            "started_at": started_wall,
            "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "returncode": 126,
            "stdout": "",
            "stderr": f"{TDX_PROCESS_INTEGRITY_ERROR}: "
            + ",".join(formula_guard["errors"]),
            "tdx_process_integrity": formula_guard,
        })
    tdx_before = capture_tdx_process_snapshot()
    preflight = evaluate_tdx_process_preflight(tdx_before, process_role)
    if preflight["status"] != "CLEAN_PASS":
        return finalize_process_result({
            "started_at": started_wall,
            "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "returncode": 126,
            "stdout": "",
            "stderr": f"{TDX_PROCESS_INTEGRITY_ERROR}: " + ",".join(preflight["errors"]),
            "tdx_process_integrity": preflight,
        })
    try:
        effective_command = prepare_tdx_guarded_python_command(command)
    except ValueError as exc:
        preflight["status"] = "BLOCKED"
        preflight["errors"] = [str(exc)]
        preflight["after"]["errors"] = ["business_child_not_started"]
        return finalize_process_result({
            "started_at": started_wall,
            "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "returncode": 126,
            "stdout": "",
            "stderr": f"{TDX_PROCESS_INTEGRITY_ERROR}: {exc}",
            "tdx_process_integrity": preflight,
        })
    environment = {
        **os.environ,
        **(extra_environment or {}),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "CODEX_STOCK_CANONICAL_EXECUTION": "1",
        "CODEX_TDX_PROCESS_GUARD": "1",
    }
    environment["CODEX_TDX_PROTECTED_PIDS"] = ",".join(
        str(row["pid"])
        for row in tdx_before.get("processes", [])
        if isinstance(row, dict) and isinstance(row.get("pid"), int)
    )
    inherited_pythonpath = str(environment.get("PYTHONPATH", "")).strip()
    environment["PYTHONPATH"] = os.pathsep.join(
        item
        for item in (
            str(TDX_GUARD_BOOTSTRAP_DIR),
            str(Path(__file__).resolve().parent),
            inherited_pythonpath,
        )
        if item
    )
    try:
        completed = communicate_bounded(
            effective_command,
            cwd,
            timeout,
            environment,
        )
        result = {
            "started_at": started_wall,
            "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            **completed,
            "effective_command": effective_command,
        }
    except Exception as exc:
        result = {
            "started_at": started_wall,
            "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "returncode": 125,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
            "effective_command": effective_command,
        }
    if result.get("timed_out"):
        result["stderr"] = (
            f"{result.get('stderr', '')}\nTIMEOUT after {timeout}s"
        ).strip()
    tdx_after = capture_tdx_process_snapshot()
    integrity = evaluate_tdx_process_integrity(tdx_before, tdx_after)
    result["tdx_process_integrity"] = integrity
    if integrity["status"] != "CLEAN_PASS":
        result["business_returncode"] = result["returncode"]
        result["returncode"] = 126
        suffix = f"{TDX_PROCESS_INTEGRITY_ERROR}: " + ",".join(integrity["errors"])
        result["stderr"] = f"{result['stderr']}\n{suffix}".strip()
    return finalize_process_result(result)


def file_artifact(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": str(path.resolve()),
        "size": len(data),
        "sha256": sha256_bytes(data),
    }


def load_tdx_process_guard_events(path: Path) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    if path.is_file():
        try:
            for line_number, raw_line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(),
                start=1,
            ):
                if not raw_line.strip():
                    continue
                try:
                    payload = json.loads(raw_line)
                except json.JSONDecodeError:
                    errors.append(f"tdx_process_guard_log_invalid:{line_number}")
                    continue
                if not isinstance(payload, dict) or payload.get("status") != "BLOCKED":
                    errors.append(f"tdx_process_guard_event_invalid:{line_number}")
                    continue
                events.append(payload)
        except OSError as exc:
            errors.append(f"tdx_process_guard_log_read_failed:{type(exc).__name__}")
    return {
        "schema": "TDX_PROCESS_GUARD_AUDIT_V1",
        "status": "CLEAN_PASS" if not events and not errors else "BLOCKED",
        "path": str(path.resolve()),
        "exists": path.is_file(),
        "event_count": len(events),
        "events": events,
        "errors": errors,
        "artifact": file_artifact(path) if path.is_file() else None,
    }


def lianban_client_command(
    client_path: Path,
    snapshot_path: Path,
    target_date: str,
    date_mode: str = "exact",
) -> list[str]:
    command = [sys.executable, str(client_path)]
    if date_mode == "latest_available":
        command.append("--latest")
    else:
        command.extend(["--date", target_date])
    command.extend(["--output", str(snapshot_path)])
    return command


def resolve_lianban_target_date(
    contract: dict[str, Any],
    root: Path,
    run_dir: Path,
    variables: dict[str, str],
) -> dict[str, Any]:
    fallback_date = str(variables["date"])
    source = contract.get("supplemental_sources", {}).get("lianban_daily", {})
    resolver = source.get("target_date_resolver") if isinstance(source, dict) else None
    if not isinstance(resolver, dict):
        return {
            "status": "CLEAN_PASS",
            "mode": "runtime_date",
            "target_date": fallback_date,
            "fallback_date": fallback_date,
            "errors": [],
        }
    raw_command = resolver.get("command")
    if not isinstance(raw_command, list) or not raw_command:
        return {
            "status": "DEGRADED",
            "mode": "contract_resolver",
            "target_date": fallback_date,
            "fallback_date": fallback_date,
            "errors": ["lianban_target_date_resolver_command_invalid"],
        }
    try:
        command = [expand_text(str(item), variables) for item in raw_command]
    except (KeyError, ValueError) as exc:
        return {
            "status": "DEGRADED",
            "mode": "contract_resolver",
            "target_date": fallback_date,
            "fallback_date": fallback_date,
            "errors": [f"lianban_target_date_resolver_expand_failed:{exc}"],
        }
    child = run_process(
        command,
        root,
        30 if source.get("required") is True else 5,
        {"ONESTOCK_STOCK_CANONICAL_CHILD": "1"},
        process_role="supplemental",
    )
    payload: dict[str, Any] = {}
    try:
        candidate = json.loads(str(child.get("stdout") or "").strip())
        if isinstance(candidate, dict):
            payload = candidate
    except json.JSONDecodeError:
        payload = {}
    target_date = str(payload.get("target_date") or "")
    valid_date = False
    try:
        datetime.strptime(target_date, "%Y-%m-%d")
        valid_date = True
    except ValueError:
        pass
    clean = (
        int(child.get("returncode", 1)) == 0
        and payload.get("status") == "CLEAN_PASS"
        and valid_date
    )
    errors = [] if clean else ["lianban_target_date_resolver_invalid"]
    return {
        "status": "CLEAN_PASS" if clean else "DEGRADED",
        "mode": "contract_resolver",
        "target_date": target_date if clean else fallback_date,
        "fallback_date": fallback_date,
        "command": command,
        "child": child,
        "errors": errors,
    }


def _shared_lianban_daily_source(
    source: dict[str, Any],
    evidence_set: dict[str, Any],
    target_date: str,
    target_date_resolution: dict[str, Any] | None,
) -> dict[str, Any] | None:
    payload = evidence_set.get("payload")
    if evidence_set.get("status") != "CLEAN_PASS" or not isinstance(payload, dict):
        return None
    try:
        snapshot_path = evidence_artifact_path(payload, "lianban_daily")
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (EvidenceSetError, OSError, UnicodeError, json.JSONDecodeError):
        return None
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("schema") != "LIANBAN_DAILY_SNAPSHOT_V1"
        or snapshot.get("status") != "CLEAN_PASS"
        or str(snapshot.get("target_date") or "") != payload.get("trading_date")
        or (
            str(source.get("date_mode") or "exact") == "exact"
            and str(payload.get("trading_date") or "") != target_date
        )
    ):
        return None
    page_url = str(snapshot.get("sources", {}).get("page", {}).get("url") or "")
    open_data_url = str(
        snapshot.get("sources", {}).get("open_data", {}).get("url") or ""
    )
    environment = {
        "CODEX_LIANBAN_STATUS": "CLEAN_PASS",
        "CODEX_LIANBAN_SNAPSHOT": str(snapshot_path),
        "CODEX_LIANBAN_SOURCE_URL": page_url,
        "CODEX_LIANBAN_OPEN_DATA_URL": open_data_url,
        "CODEX_LIANBAN_ATTRIBUTION": "连板网",
    }
    return {
        "enabled": True,
        "required": source.get("required") is True,
        "status": "CLEAN_PASS",
        "mode": "shared_evidence_set",
        "cache_hit": True,
        "client": str(source.get("client") or LIANBAN_CLIENT_PATH),
        "command": [],
        "snapshot": file_artifact(snapshot_path),
        "source_url": page_url,
        "open_data_url": open_data_url,
        "target_date_resolution": target_date_resolution,
        "child": None,
        "environment": environment,
        "evidence_set_id": payload["evidence_set_id"],
        "errors": [],
    }


def _lianban_cache_key(source: dict[str, Any], target_date: str) -> str:
    raw = f"{source.get('date_mode', 'exact')}|{target_date}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _valid_lianban_snapshot(
    snapshot: Any,
    source: dict[str, Any],
    target_date: str,
) -> bool:
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("schema") != "LIANBAN_DAILY_SNAPSHOT_V1"
        or snapshot.get("status") != "CLEAN_PASS"
    ):
        return False
    snapshot_date = str(snapshot.get("target_date") or "")
    try:
        datetime.strptime(snapshot_date, "%Y-%m-%d")
    except ValueError:
        return False
    return (
        str(source.get("date_mode") or "exact") != "exact"
        or snapshot_date == target_date
    )


def _cached_lianban_daily_source(
    source: dict[str, Any],
    target_date: str,
    target_date_resolution: dict[str, Any] | None,
) -> dict[str, Any] | None:
    key = _lianban_cache_key(source, target_date)
    manifest_path = STOCK_LIANBAN_CACHE_ROOT / "requests" / f"{key}.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        created_at_epoch = float(manifest["created_at_epoch"])
        ttl = max(
            0,
            int(source.get("cache_ttl_seconds", STOCK_LIANBAN_CACHE_TTL_SECONDS)),
        )
        if time.time() - created_at_epoch > ttl:
            return None
        artifact = manifest["artifact"]
        snapshot_path = Path(str(artifact["path"])).resolve()
        if (
            not snapshot_path.is_file()
            or snapshot_path.stat().st_size != int(artifact["size"])
            or sha256_file(snapshot_path) != str(artifact["sha256"])
        ):
            return None
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        if not _valid_lianban_snapshot(snapshot, source, target_date):
            return None
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    page_url = str(snapshot.get("sources", {}).get("page", {}).get("url") or "")
    open_data_url = str(
        snapshot.get("sources", {}).get("open_data", {}).get("url") or ""
    )
    return {
        "enabled": True,
        "required": source.get("required") is True,
        "status": "CLEAN_PASS",
        "mode": "shared_runtime_cache",
        "cache_hit": True,
        "cache_manifest": file_artifact(manifest_path),
        "client": str(source.get("client") or LIANBAN_CLIENT_PATH),
        "command": [],
        "snapshot": file_artifact(snapshot_path),
        "source_url": page_url,
        "open_data_url": open_data_url,
        "target_date_resolution": target_date_resolution,
        "child": None,
        "environment": {
            "CODEX_LIANBAN_STATUS": "CLEAN_PASS",
            "CODEX_LIANBAN_SNAPSHOT": str(snapshot_path),
            "CODEX_LIANBAN_SOURCE_URL": page_url,
            "CODEX_LIANBAN_OPEN_DATA_URL": open_data_url,
            "CODEX_LIANBAN_ATTRIBUTION": "连板网",
        },
        "errors": [],
    }


def _store_lianban_runtime_cache(
    source: dict[str, Any],
    target_date: str,
    snapshot_path: Path,
) -> dict[str, Any]:
    content_sha256 = sha256_file(snapshot_path)
    object_path = STOCK_LIANBAN_CACHE_ROOT / "objects" / f"{content_sha256}.json"
    object_path.parent.mkdir(parents=True, exist_ok=True)
    if object_path.is_file():
        if sha256_file(object_path) != content_sha256:
            raise RuntimeError("lianban_cache_object_hash_mismatch")
    else:
        object_path.write_bytes(snapshot_path.read_bytes())
        if sha256_file(object_path) != content_sha256:
            raise RuntimeError("lianban_cache_object_write_mismatch")
    key = _lianban_cache_key(source, target_date)
    manifest_path = STOCK_LIANBAN_CACHE_ROOT / "requests" / f"{key}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "STOCK_LIANBAN_RUNTIME_CACHE_V1",
        "requested_target_date": target_date,
        "date_mode": str(source.get("date_mode") or "exact"),
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "created_at_epoch": time.time(),
        "artifact": file_artifact(object_path),
    }
    atomic_write_json(manifest_path, manifest)
    return {"manifest": manifest_path, "object": object_path}


def _lianban_negative_cache_hit(
    source: dict[str, Any],
    target_date: str,
) -> bool:
    key = _lianban_cache_key(source, target_date)
    path = STOCK_LIANBAN_CACHE_ROOT / "requests" / f"{key}.negative.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        created_at_epoch = float(payload["created_at_epoch"])
        ttl = max(
            0,
            int(
                source.get(
                    "negative_cache_seconds",
                    STOCK_LIANBAN_NEGATIVE_CACHE_SECONDS,
                )
            ),
        )
        return time.time() - created_at_epoch <= ttl
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def _store_lianban_negative_cache(
    source: dict[str, Any],
    target_date: str,
    errors: list[str],
) -> None:
    key = _lianban_cache_key(source, target_date)
    path = STOCK_LIANBAN_CACHE_ROOT / "requests" / f"{key}.negative.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(
        path,
        {
            "schema": "STOCK_LIANBAN_NEGATIVE_CACHE_V1",
            "created_at_epoch": time.time(),
            "errors": errors,
        },
    )


def prepare_lianban_daily_source(
    contract: dict[str, Any],
    run_dir: Path,
    target_date: str,
    target_date_resolution: dict[str, Any] | None = None,
    evidence_set: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = contract.get("supplemental_sources", {}).get("lianban_daily", {})
    if not isinstance(source, dict) or source.get("enabled") is not True:
        return {
            "enabled": False,
            "required": False,
            "status": "DISABLED",
            "environment": {"CODEX_LIANBAN_STATUS": "DISABLED"},
            "target_date_resolution": target_date_resolution,
            "errors": [],
        }
    if evidence_set:
        shared = _shared_lianban_daily_source(
            source,
            evidence_set,
            target_date,
            target_date_resolution,
        )
        if shared is not None:
            return shared

    cached = _cached_lianban_daily_source(
        source,
        target_date,
        target_date_resolution,
    )
    if cached is not None:
        return cached

    snapshot_path = (run_dir / "lianban-daily.json").resolve()
    client_path = Path(str(source.get("client") or LIANBAN_CLIENT_PATH)).resolve()
    # Contracts migrated from the original workstation may point at a stale
    # D: drive. Fall back to the packaged client whenever that binding is gone.
    if not client_path.is_file() and LIANBAN_CLIENT_PATH.is_file():
        client_path = LIANBAN_CLIENT_PATH.resolve()
    page_url = f"https://lianban.net/days/{target_date}.html"
    open_data_url = f"https://lianban.net/opendata/{target_date}.json"
    command = lianban_client_command(
        client_path,
        snapshot_path,
        target_date,
        str(source.get("date_mode", "exact")),
    )
    errors: list[str] = []
    required = source.get("required") is True
    timeout_seconds = (
        STOCK_LIANBAN_REQUIRED_TIMEOUT_SECONDS
        if required
        else STOCK_LIANBAN_OPTIONAL_TIMEOUT_SECONDS
    )
    if (
        target_date_resolution is not None
        and target_date_resolution.get("status") != "CLEAN_PASS"
    ):
        errors.extend(target_date_resolution.get("errors") or [])
    cache_key = _lianban_cache_key(source, target_date)
    cache_lock_path = STOCK_LIANBAN_CACHE_ROOT / "locks" / f"{cache_key}.lock"
    snapshot: dict[str, Any] | None = None
    cache_binding: dict[str, Any] | None = None
    clean = False
    try:
        with stock_business_lease(
            f"lianban-cache-{cache_key}",
            lock_path=cache_lock_path,
            timeout_seconds=timeout_seconds + 2,
        ):
            cached = _cached_lianban_daily_source(
                source,
                target_date,
                target_date_resolution,
            )
            if cached is not None:
                return cached
            if not required and _lianban_negative_cache_hit(source, target_date):
                return {
                    "enabled": True,
                    "required": False,
                    "status": "DEGRADED",
                    "mode": "negative_runtime_cache",
                    "cache_hit": True,
                    "client": str(client_path),
                    "command": [],
                    "snapshot": {"path": str(snapshot_path), "exists": False},
                    "source_url": page_url,
                    "open_data_url": open_data_url,
                    "target_date_resolution": target_date_resolution,
                    "child": None,
                    "environment": {
                        "CODEX_LIANBAN_STATUS": "DEGRADED",
                        "CODEX_LIANBAN_SNAPSHOT": str(snapshot_path),
                        "CODEX_LIANBAN_SOURCE_URL": page_url,
                        "CODEX_LIANBAN_OPEN_DATA_URL": open_data_url,
                        "CODEX_LIANBAN_ATTRIBUTION": "连板网",
                    },
                    "errors": ["lianban_negative_runtime_cache_hit"],
                }
            if client_path.is_file():
                child = run_process(
                    command,
                    client_path.parent,
                    timeout_seconds,
                    process_role="supplemental",
                )
            else:
                child = {
                    "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "elapsed_seconds": 0.0,
                    "returncode": 125,
                    "stdout": "",
                    "stderr": f"lianban_client_missing:{client_path}",
                }
                errors.append(f"lianban_client_missing:{client_path}")

            if snapshot_path.is_file():
                try:
                    candidate = json.loads(snapshot_path.read_text(encoding="utf-8"))
                    if isinstance(candidate, dict):
                        snapshot = candidate
                    else:
                        errors.append("lianban_snapshot_not_object")
                except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                    errors.append(
                        f"lianban_snapshot_invalid:{type(exc).__name__}:{exc}"
                    )
            else:
                errors.append(f"lianban_snapshot_missing:{snapshot_path}")
            if snapshot is not None:
                page_url = str(
                    snapshot.get("sources", {}).get("page", {}).get("url")
                    or page_url
                )
                open_data_url = str(
                    snapshot.get("sources", {}).get("open_data", {}).get("url")
                    or open_data_url
                )
            clean = (
                (
                    target_date_resolution is None
                    or target_date_resolution.get("status") == "CLEAN_PASS"
                )
                and int(child.get("returncode", 1)) == 0
                and _valid_lianban_snapshot(snapshot, source, target_date)
            )
            if not clean and not errors:
                errors.append("lianban_source_degraded")
            if clean:
                try:
                    cache_binding = _store_lianban_runtime_cache(
                        source,
                        target_date,
                        snapshot_path,
                    )
                except (OSError, RuntimeError) as exc:
                    errors.append(
                        "lianban_runtime_cache_store_failed:"
                        f"{type(exc).__name__}"
                    )
            elif not required:
                try:
                    _store_lianban_negative_cache(source, target_date, errors)
                except OSError:
                    errors.append("lianban_negative_cache_store_failed")
    except StockBusinessLeaseTimeout as exc:
        child = {
            "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "elapsed_seconds": 0.0,
            "returncode": 124,
            "stdout": "",
            "stderr": str(exc),
        }
        errors.append("lianban_runtime_cache_lock_timeout")
    status = "CLEAN_PASS" if clean else ("BLOCKED" if required else "DEGRADED")
    if not clean and not errors:
        errors.append("lianban_source_degraded")
    environment = {
        "CODEX_LIANBAN_STATUS": status,
        "CODEX_LIANBAN_SNAPSHOT": str(snapshot_path),
        "CODEX_LIANBAN_SOURCE_URL": page_url,
        "CODEX_LIANBAN_OPEN_DATA_URL": open_data_url,
        "CODEX_LIANBAN_ATTRIBUTION": "连板网",
    }
    return {
        "enabled": True,
        "required": required,
        "status": status,
        "mode": "direct_fetch",
        "cache_hit": False,
        "cache_manifest": (
            file_artifact(cache_binding["manifest"])
            if cache_binding is not None
            else None
        ),
        "client": str(client_path),
        "command": command,
        "snapshot": (
            file_artifact(snapshot_path)
            if snapshot_path.is_file()
            else {"path": str(snapshot_path), "exists": False}
        ),
        "source_url": page_url,
        "open_data_url": open_data_url,
        "target_date_resolution": target_date_resolution,
        "child": child,
        "environment": environment,
        "errors": errors,
    }


def _evidence_set_environment(payload: dict[str, Any]) -> dict[str, str]:
    duanxianxia = evidence_artifact_path(payload, "duanxianxia")
    return {
        "CODEX_STOCK_SHARED_EVIDENCE_STATUS": "CLEAN_PASS",
        "CODEX_STOCK_EVIDENCE_SET_ID": str(payload["evidence_set_id"]),
        "CODEX_STOCK_EVIDENCE_SET_BATCH_ID": str(payload["batch_id"]),
        "CODEX_STOCK_EVIDENCE_TRADING_DATE": str(payload["trading_date"]),
        "CODEX_DUANXIANXIA_STATUS": "CLEAN_PASS",
        "CODEX_DUANXIANXIA_SNAPSHOT": str(duanxianxia),
    }


def _latest_completed_tdx_trading_date() -> str | None:
    """Return the last completed local A-share session from the configured TDX root."""
    tdx_root = Path(os.environ.get("TDX_ROOT", r"C:\new_tdx_mock"))
    day_path = tdx_root / "vipdoc" / "sh" / "lday" / "sh000001.day"
    record_size = 32
    try:
        if not day_path.is_file() or day_path.stat().st_size < record_size:
            return None
        with day_path.open("rb") as handle:
            handle.seek(-record_size, os.SEEK_END)
            raw_date = handle.read(4)
        if len(raw_date) != 4:
            return None
        date_value = int.from_bytes(raw_date, byteorder="little", signed=False)
        parsed = datetime.strptime(str(date_value), "%Y%m%d")
        if parsed.date() > datetime.now().astimezone().date():
            return None
        return parsed.strftime("%Y-%m-%d")
    except (OSError, ValueError):
        return None


def prepare_stock_evidence_set() -> dict[str, Any]:
    batch_id = os.environ.get(STOCK_BATCH_ID_ENV, "").strip()
    if not batch_id:
        return {
            "enabled": False,
            "status": "DISABLED",
            "environment": {},
            "errors": [],
        }
    try:
        batch_id = validate_batch_id(batch_id)
        completed_trading_date = _latest_completed_tdx_trading_date()
        batch_root = (STOCK_EVIDENCE_ROOT / batch_id).resolve()
        manifest_path = batch_root / "evidence-set.json"
        if manifest_path.is_file():
            payload = load_evidence_set(
                manifest_path,
                expected_batch_id=batch_id,
            )
            created_at = datetime.fromisoformat(str(payload["created_at"]))
            if created_at.astimezone().date() != datetime.now().astimezone().date():
                raise EvidenceSetError("cross_calendar_day_reuse_blocked")
            if (
                completed_trading_date is not None
                and str(payload.get("trading_date")) != completed_trading_date
            ):
                raise EvidenceSetError("latest_completed_trading_date_mismatch")
            return {
                "enabled": True,
                "status": "CLEAN_PASS",
                "mode": "read_only_reuse",
                "payload": payload,
                "manifest": file_artifact(manifest_path),
                "environment": _evidence_set_environment(payload),
                "collection": None,
                "errors": [],
            }
        if batch_root.exists() and any(batch_root.iterdir()):
            raise EvidenceSetError("partial_evidence_set_exists")
        batch_root.mkdir(parents=True, exist_ok=True)
        lianban_path = batch_root / "lianban-daily.json"
        duanxianxia_path = batch_root / "duanxianxia.json"
        lianban_command = [sys.executable, str(LIANBAN_CLIENT_PATH)]
        if completed_trading_date is not None:
            lianban_command.extend(["--date", completed_trading_date])
        else:
            lianban_command.append("--latest")
        lianban_command.extend(["--output", str(lianban_path)])
        duanxianxia_command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(DUANXIANXIA_CLIENT_PATH),
            "-Output",
            str(duanxianxia_path),
        ]
        with ThreadPoolExecutor(max_workers=2) as executor:
            lianban_future = executor.submit(
                run_process,
                lianban_command,
                LIANBAN_CLIENT_PATH.parent,
                45,
                process_role="supplemental",
            )
            duanxianxia_future = executor.submit(
                run_process,
                duanxianxia_command,
                DUANXIANXIA_CLIENT_PATH.parent,
                60,
                process_role="supplemental",
            )
            collection = {
                "lianban_daily": lianban_future.result(),
                "duanxianxia": duanxianxia_future.result(),
            }
        errors = [
            f"{name}_returncode:{child.get('returncode')}"
            for name, child in collection.items()
            if int(child.get("returncode", 1)) != 0
        ]
        try:
            lianban = json.loads(lianban_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise EvidenceSetError(
                f"lianban_snapshot_invalid:{type(exc).__name__}"
            ) from exc
        try:
            duanxianxia = json.loads(duanxianxia_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise EvidenceSetError(
                f"duanxianxia_snapshot_invalid:{type(exc).__name__}"
            ) from exc
        if errors:
            raise EvidenceSetError(",".join(errors))
        if (
            not isinstance(lianban, dict)
            or lianban.get("schema") != "LIANBAN_DAILY_SNAPSHOT_V1"
            or lianban.get("status") != "CLEAN_PASS"
            or not lianban.get("target_date")
        ):
            raise EvidenceSetError("lianban_snapshot_not_clean")
        datasets = duanxianxia.get("datasets") if isinstance(duanxianxia, dict) else None
        if (
            not isinstance(duanxianxia, dict)
            or duanxianxia.get("source_page") != "https://duanxianxia.com/web/main"
            or duanxianxia.get("access_scope")
            != "public HTTP data only; no browser credentials exported"
            or not isinstance(datasets, dict)
            or not datasets
            or not all(
                isinstance(item, dict) and item.get("success") is True
                for item in datasets.values()
            )
        ):
            raise EvidenceSetError("duanxianxia_snapshot_not_clean")
        payload = write_evidence_set(
            manifest_path,
            batch_id=batch_id,
            trading_date=str(lianban["target_date"]),
            artifacts={
                "duanxianxia": duanxianxia_path,
                "lianban_daily": lianban_path,
            },
        )
        return {
            "enabled": True,
            "status": "CLEAN_PASS",
            "mode": "parallel_collection",
            "payload": payload,
            "manifest": file_artifact(manifest_path),
            "environment": _evidence_set_environment(payload),
            "collection": {
                name: {
                    key: child.get(key)
                    for key in (
                        "started_at",
                        "finished_at",
                        "elapsed_seconds",
                        "returncode",
                        "stderr",
                    )
                }
                for name, child in collection.items()
            },
            "errors": [],
        }
    except (EvidenceSetError, OSError, ValueError) as exc:
        return {
            "enabled": True,
            "status": "BLOCKED",
            "mode": "blocked",
            "manifest": (
                file_artifact(manifest_path)
                if manifest_path.is_file()
                else {"path": str(manifest_path), "exists": False}
            ),
            "environment": {},
            "errors": [f"{type(exc).__name__}:{exc}"],
        }


def resolve_required_artifacts(
    requirements: list[dict[str, Any]],
    variables: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    artifacts: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    for requirement in requirements:
        raw = expand_text(str(requirement["path"]), variables)
        minimum = int(requirement.get("min_size", 1))
        matches = sorted(Path().glob(raw)) if not Path(raw).is_absolute() else []
        if Path(raw).is_absolute():
            candidate = Path(raw)
            matches = [candidate] if candidate.is_file() else []
        valid = [path for path in matches if path.is_file() and path.stat().st_size >= minimum]
        checks.append({
            "type": "required_artifact",
            "path": raw,
            "minimum_size": minimum,
            "matched": len(valid),
            "ok": bool(valid),
        })
        artifacts.extend(file_artifact(path) for path in valid)
    unique = {item["path"]: item for item in artifacts}
    return [unique[key] for key in sorted(unique)], checks


def evaluate_semantic_assertions(
    assertions: list[dict[str, Any]],
    returncode: int,
    stdout: str,
    stderr: str,
) -> list[dict[str, Any]]:
    combined = stdout + "\n" + stderr
    results: list[dict[str, Any]] = []
    for assertion in assertions:
        kind = str(assertion["type"])
        row: dict[str, Any] = {"type": kind}
        if kind == "returncode_zero":
            row.update({"actual": returncode, "ok": returncode == 0})
        elif kind == "stdout_nonempty":
            row.update({"actual_size": len(stdout.encode("utf-8")), "ok": bool(stdout.strip())})
        elif kind == "output_not_contains":
            values = [str(value) for value in assertion.get("values", [])]
            found = [value for value in values if value in combined]
            row.update({"values": values, "found": found, "ok": not found})
        elif kind == "output_contains_any":
            values = [str(value) for value in assertion.get("values", [])]
            found = [value for value in values if value in combined]
            row.update({"values": values, "found": found, "ok": bool(found)})
        else:
            row.update({"ok": False, "error": "unsupported_assertion"})
        results.append(row)
    return results


def evaluate_business_stdout(
    skill_id: str,
    stdout: str,
    *,
    require_data_gate: bool = False,
) -> dict[str, Any]:
    output_bytes = stdout.encode("utf-8")
    try:
        parsed = json.loads(stdout.strip())
    except (json.JSONDecodeError, TypeError):
        return {
            "ok": False,
            "errors": ["business_stdout_not_single_json_object"],
            "data_gate": None,
            "output_size": len(output_bytes),
            "output_sha256": sha256_bytes(output_bytes),
        }
    result = evaluate_business_result(
        parsed,
        skill_id=skill_id,
        require_data_gate=require_data_gate,
    )
    result["output_size"] = len(output_bytes)
    result["output_sha256"] = sha256_bytes(output_bytes)
    return result


def business_request_errors(
    contract: dict[str, Any],
    extra_args: list[str],
) -> list[str]:
    guard = contract.get("workflow_guard")
    if not isinstance(guard, dict):
        return ["workflow_guard_missing"]
    errors: list[str] = list(validate_request_arguments(extra_args))
    if (
        guard.get("requires_explicit_business_args") is True
        and not extra_args
    ):
        errors.append("explicit_business_action_required")
    if extra_args:
        action = str(extra_args[0]).strip().casefold()
        forbidden = {
            str(item).strip().casefold()
            for item in guard.get("forbidden_business_actions", [])
        }
        if action in forbidden:
            errors.append(f"non_business_action_forbidden:{action}")
    return errors


def validate_contract_bindings(
    entry: Path,
    contract: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    runtime = Path(__file__).resolve()
    if contract.get("delivery_policy") != DELIVERY_POLICY:
        errors.append("delivery_policy_invalid")
    if contract.get("production_policy") != PRODUCTION_POLICY:
        errors.append("production_policy_invalid")
    if contract.get("catalog_sha256") != sha256_file(CATALOG_PATH):
        errors.append("catalog_hash_mismatch")
    if contract.get("contract_sha256") != contract_sha256(contract):
        errors.append("contract_hash_mismatch")
    if contract.get("facade_sha256") != sha256_file(entry):
        errors.append("facade_hash_mismatch")
    if contract.get("executor_sha256") != sha256_file(runtime):
        errors.append("executor_hash_mismatch")
    for binding in contract.get("business_bindings", []):
        path = Path(str(binding["path"]))
        if not path.is_file():
            errors.append(f"business_file_missing:{path}")
        elif binding.get("sha256") != sha256_file(path):
            errors.append(f"business_file_hash_mismatch:{path}")
    return errors


def global_contract_preflight() -> dict[str, Any]:
    return contract_catalog_preflight(
        catalog_path=CATALOG_PATH,
        contracts_path=CONTRACTS_PATH,
        skills_root=SKILLS_ROOT,
        runtime_path=Path(__file__).resolve(),
    )


def contract_surface_signature() -> str:
    """Return a content signature for every contract-bound file."""
    paths = {
        CATALOG_PATH.resolve(),
        CONTRACTS_PATH.resolve(),
        Path(__file__).resolve(),
    }
    try:
        payload = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8-sig"))
        contracts = payload.get("contracts", []) if isinstance(payload, dict) else []
        for contract in contracts:
            if not isinstance(contract, dict):
                continue
            skill_id = str(contract.get("skill_id") or "").strip()
            if skill_id:
                paths.add(
                    (SKILLS_ROOT / skill_id / "scripts" / "codex_entry.py").resolve()
                )
            for binding in contract.get("business_bindings", []):
                if isinstance(binding, dict) and binding.get("path"):
                    paths.add(Path(str(binding["path"])).resolve())
    except (OSError, UnicodeError, json.JSONDecodeError):
        pass
    surface: list[dict[str, Any]] = []
    for path in sorted(paths, key=lambda item: str(item).casefold()):
        try:
            surface.append({
                "path": str(path),
                "sha256": sha256_file(path),
            })
        except OSError:
            surface.append({"path": str(path), "missing": True})
    encoded = json.dumps(
        surface,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def append_workflow_stage(
    stages: list[dict[str, Any]],
    name: str,
    started: float,
    *,
    status: str = "CLEAN_PASS",
    **details: Any,
) -> None:
    stage = {
        "name": name,
        "status": status,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    stage.update(details)
    stages.append(stage)


def write_receipt(
    root: Path,
    payload: dict[str, Any],
    stdout: str,
    stderr: str,
) -> Path:
    receipt_dir = Path(os.environ.get("ONESTOCK_STOCK_DATA_ROOT", str(root / "reports"))) / "executions"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{payload['skill_id']}-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
    stdout_path = receipt_dir / f"{stem}.stdout.txt"
    stderr_path = receipt_dir / f"{stem}.stderr.txt"
    receipt_path = receipt_dir / f"{stem}.receipt.json"
    payload["stdout_artifact"] = atomic_write_text(stdout_path, stdout)
    payload["stderr_artifact"] = atomic_write_text(stderr_path, stderr)
    payload["receipt_integrity"] = receipt_integrity(payload)
    atomic_write_json(receipt_path, payload)
    readback = json.loads(receipt_path.read_text(encoding="utf-8"))
    if readback.get("receipt_integrity") != receipt_integrity(readback):
        raise RuntimeError("receipt_readback_integrity_mismatch")
    return receipt_path


def info(entry_file: str) -> int:
    root, skill_id, contract = skill_context(entry_file)
    print(json.dumps({
        "runtime": RUNTIME_ID,
        "runtime_surface": "Codex",
        "skill_id": skill_id,
        "entry": str(Path(entry_file).resolve()),
        "contract_catalog": str(CONTRACTS_PATH),
        "contract_sha256": contract.get("contract_sha256"),
        "business_command": contract.get("business_command"),
        "cwd": contract.get("cwd"),
        "skill_root": str(root),
    }, ensure_ascii=False, indent=2))
    return 0


def compile_script_syntax(script: Path, errors: list[str]) -> None:
    try:
        compile(script.read_bytes(), str(script), "exec")
    except (OSError, SyntaxError, ValueError) as exc:
        errors.append(f"compile_error:{script}:{exc}")


def selftest(entry_file: str) -> int:
    entry = Path(entry_file).resolve()
    root, skill_id, contract = skill_context(entry_file)
    errors = validate_contract_bindings(entry, contract)
    for required in (root / "SKILL.md", root / "references" / "workflow.md", entry):
        if not required.is_file():
            errors.append(f"required_file_missing:{required}")
    for script in sorted((root / "scripts").glob("*.py")):
        compile_script_syntax(script, errors)
    payload = {
        "runtime": RUNTIME_ID,
        "skill_id": skill_id,
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "contract_sha256": contract.get("contract_sha256"),
        "semantic_assertions": contract.get("semantic_assertions", []),
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


def _run_with_business_lease(
    entry_file: str,
    extra: list[str],
    lease: dict[str, Any],
    *,
    root: Path | None = None,
    skill_id: str | None = None,
    contract: dict[str, Any] | None = None,
    contract_preflight: dict[str, Any] | None = None,
    preflight_signature: str | None = None,
    workflow_stages: list[dict[str, Any]] | None = None,
    runtime_started: float | None = None,
) -> int:
    entry = Path(entry_file).resolve()
    stages = workflow_stages if workflow_stages is not None else []
    inside_lease_started = time.monotonic()
    if root is None or skill_id is None or contract is None:
        root, skill_id, contract = skill_context(entry_file)
    if contract_preflight is None:
        preflight_started = time.monotonic()
        contract_preflight = global_contract_preflight()
        append_workflow_stage(
            stages,
            "global_contract_preflight",
            preflight_started,
            status=str(contract_preflight.get("status") or "BLOCKED"),
        )
    current_signature = contract_surface_signature()
    if preflight_signature is not None and current_signature != preflight_signature:
        revalidation_started = time.monotonic()
        contract_preflight = global_contract_preflight()
        current_signature = contract_surface_signature()
        root, skill_id, contract = skill_context(entry_file)
        append_workflow_stage(
            stages,
            "contract_drift_revalidation",
            revalidation_started,
            status=str(contract_preflight.get("status") or "BLOCKED"),
        )
    if contract_preflight.get("status") != "CLEAN_PASS":
        print(json.dumps({
            "runtime": RUNTIME_ID,
            "runtime_surface": "Codex",
            "status": "BLOCKED",
            "failure_owner": contract_preflight.get("failure_owner"),
            "errors": contract_preflight.get("errors", []),
            "contract_preflight": contract_preflight,
            "workflow_telemetry": stages,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    extra_args = [str(item) for item in extra]
    binding_started = time.monotonic()
    binding_errors = validate_contract_bindings(entry, contract)
    append_workflow_stage(
        stages,
        "binding_validation",
        binding_started,
        status="CLEAN_PASS" if not binding_errors else "BLOCKED",
        error_count=len(binding_errors),
    )
    if binding_errors:
        print(json.dumps({
            "runtime": RUNTIME_ID,
            "runtime_surface": "Codex",
            "skill_id": skill_id,
            "status": "BLOCKED",
            "failure_owner": "stock_contract_binding",
            "errors": binding_errors,
            "workflow_telemetry": stages,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    control_scan_started = time.monotonic()
    control_findings = scan_tdx_process_control_paths([
        Path(str(binding["path"]))
        for binding in contract.get("business_bindings", [])
        if isinstance(binding, dict) and binding.get("path")
    ])
    append_workflow_stage(
        stages,
        "tdx_control_scan",
        control_scan_started,
        status="CLEAN_PASS" if not control_findings else "BLOCKED",
        finding_count=len(control_findings),
    )
    if control_findings:
        print(json.dumps({
            "runtime": RUNTIME_ID,
            "runtime_surface": "Codex",
            "skill_id": skill_id,
            "status": "BLOCKED",
            "failure_owner": "tdx_process_control_guard",
            "errors": ["tdx_process_control_detected"],
            "findings": control_findings,
            "stock_business_lease": lease,
            "workflow_telemetry": stages,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    run_dir = Path(os.environ.get("ONESTOCK_STOCK_DATA_ROOT", str(root / "reports"))) / "executions" / "runs" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    run_dir.mkdir(parents=True, exist_ok=False)
    command, cwd, variables = expanded_execution(contract, root, run_dir)
    command.extend(extra_args)
    evidence_started = time.monotonic()
    evidence_set = prepare_stock_evidence_set()
    execution_purpose = (
        "stock_conclusion"
        if evidence_set.get("enabled") is True
        else "readiness_validation"
    )
    request_fingerprint_value = request_fingerprint(
        skill_id,
        str(contract["contract_sha256"]),
        extra_args,
        execution_purpose,
    )
    append_workflow_stage(
        stages,
        "evidence_set",
        evidence_started,
        status=str(evidence_set.get("status") or "BLOCKED"),
        mode=evidence_set.get("mode"),
    )
    if evidence_set.get("status") == "BLOCKED":
        print(json.dumps({
            "runtime": RUNTIME_ID,
            "runtime_surface": "Codex",
            "skill_id": skill_id,
            "status": "BLOCKED",
            "failure_owner": "stock_evidence_set",
            "errors": evidence_set.get("errors", []),
            "evidence_set": evidence_set,
            "workflow_telemetry": stages,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    target_date_started = time.monotonic()
    lianban_target_date = resolve_lianban_target_date(
        contract,
        root,
        run_dir,
        variables,
    )
    append_workflow_stage(
        stages,
        "supplemental_target_date",
        target_date_started,
        status=str(lianban_target_date.get("status") or "DEGRADED"),
        mode=lianban_target_date.get("mode"),
    )
    supplemental_started = time.monotonic()
    lianban_source = prepare_lianban_daily_source(
        contract,
        run_dir,
        lianban_target_date["target_date"],
        lianban_target_date,
        evidence_set,
    )
    append_workflow_stage(
        stages,
        "supplemental_lianban",
        supplemental_started,
        status=str(lianban_source.get("status") or "BLOCKED"),
        mode=lianban_source.get("mode"),
        cache_hit=bool(lianban_source.get("cache_hit")),
    )
    if (
        lianban_source.get("required") is True
        and lianban_source.get("status") != "CLEAN_PASS"
    ):
        print(json.dumps({
            "runtime": RUNTIME_ID,
            "runtime_surface": "Codex",
            "skill_id": skill_id,
            "status": "BLOCKED",
            "failure_owner": "required_supplemental_source",
            "errors": lianban_source.get("errors", []),
            "supplemental_source": lianban_source,
            "workflow_telemetry": stages,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    tdx_guard_log = run_dir / "tdx_process_guard.jsonl"
    child_environment = dict(evidence_set.get("environment") or {})
    child_environment.update(lianban_source.get("environment") or {})
    child_environment["CODEX_TDX_GUARD_LOG"] = str(tdx_guard_log)
    business_started = time.monotonic()
    child = run_process(
        command,
        cwd,
        int(contract["timeout_seconds"]),
        child_environment,
        process_role="business",
    )
    append_workflow_stage(
        stages,
        "business_process",
        business_started,
        status="CLEAN_PASS" if int(child.get("returncode", 1)) == 0 else "BLOCKED",
        returncode=int(child.get("returncode", 1)),
    )
    postflight_started = time.monotonic()
    postflight_signature_before = contract_surface_signature()
    postflight_preflight = global_contract_preflight()
    postflight_signature_after = contract_surface_signature()
    contract_stability_errors: list[str] = []
    if current_signature != postflight_signature_before:
        contract_stability_errors.append(
            "contract_surface_changed_during_business"
        )
    if postflight_signature_before != postflight_signature_after:
        contract_stability_errors.append(
            "contract_surface_changed_during_postflight"
        )
    if postflight_preflight.get("status") != "CLEAN_PASS":
        contract_stability_errors.extend(
            str(error)
            for error in postflight_preflight.get("errors", [])
        )
    contract_stability_errors = sorted(set(contract_stability_errors))
    append_workflow_stage(
        stages,
        "contract_surface_postflight",
        postflight_started,
        status=(
            "CLEAN_PASS" if not contract_stability_errors else "BLOCKED"
        ),
        surface_stable=(
            current_signature
            == postflight_signature_before
            == postflight_signature_after
        ),
        error_count=len(contract_stability_errors),
    )
    validation_started = time.monotonic()
    tdx_process_guard = load_tdx_process_guard_events(tdx_guard_log)
    if tdx_process_guard["status"] != "CLEAN_PASS":
        child["business_returncode"] = child["returncode"]
        child["returncode"] = 126
        guard_errors = ["tdx_process_guard_action_blocked", *tdx_process_guard["errors"]]
        suffix = f"{TDX_PROCESS_INTEGRITY_ERROR}: " + ",".join(guard_errors)
        child["stderr"] = f"{child['stderr']}\n{suffix}".strip()
    semantic_results = evaluate_semantic_assertions(
        contract.get("semantic_assertions", []),
        int(child["returncode"]),
        str(child["stdout"]),
        str(child["stderr"]),
    )
    required_artifacts, artifact_checks = resolve_required_artifacts(
        contract.get("required_artifacts", []),
        variables,
    )
    business_stdout_validation = evaluate_business_stdout(
        skill_id,
        str(child["stdout"]),
        require_data_gate=execution_purpose == "stock_conclusion",
    )
    all_assertions = semantic_results + artifact_checks
    accepted = (
        not binding_errors
        and not contract_stability_errors
        and tdx_process_guard["status"] == "CLEAN_PASS"
        and business_stdout_validation["ok"]
        and all(item.get("ok") for item in all_assertions)
    )
    append_workflow_stage(
        stages,
        "result_validation",
        validation_started,
        status="CLEAN_PASS" if accepted else "BLOCKED",
        semantic_check_count=len(all_assertions),
    )
    production_errors = sorted(set(
        list(binding_errors)
        + list(contract_stability_errors)
        + list(business_stdout_validation.get("errors", []))
        + [
            "tdx_process_guard_not_clean"
            for _ in (0,)
            if tdx_process_guard["status"] != "CLEAN_PASS"
        ]
        + [
            "semantic_or_artifact_assertion_failed"
            for _ in (0,)
            if not all(item.get("ok") for item in all_assertions)
        ]
    ))
    production_readiness = {
        "schema": PRODUCTION_READINESS_SCHEMA,
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "execution_purpose": execution_purpose,
        "conclusion_eligible": (
            accepted and execution_purpose == "stock_conclusion"
        ),
        "request_fingerprint": request_fingerprint_value,
        "policy_sha256": production_policy_sha256(),
        "data_gate": business_stdout_validation.get("data_gate"),
        "failure_class": child.get("failure_class") or classify_failure(
            int(child.get("returncode", 125)),
            bool(child.get("timed_out")),
            bool(child.get("output_limited")),
        ),
        "output_bytes": {
            "stdout": int(child.get("stdout_bytes", 0)),
            "stderr": int(child.get("stderr_bytes", 0)),
            "limit": MAX_PROCESS_OUTPUT_BYTES,
            "limited": bool(child.get("output_limited")),
        },
        "persistence": PRODUCTION_POLICY["persistence"],
        "errors": production_errors,
    }
    append_workflow_stage(
        stages,
        "production_gate",
        validation_started,
        status=production_readiness["status"],
        execution_purpose=execution_purpose,
        conclusion_eligible=production_readiness["conclusion_eligible"],
        error_count=len(production_errors),
    )
    append_workflow_stage(
        stages,
        "runtime_inside_lease",
        inside_lease_started,
        status="CLEAN_PASS" if accepted else "BLOCKED",
    )
    if runtime_started is not None:
        append_workflow_stage(
            stages,
            "total_runtime_to_receipt",
            runtime_started,
            status="CLEAN_PASS" if accepted else "BLOCKED",
        )
    payload = {
        "receipt_version": RECEIPT_VERSION,
        "runtime": RUNTIME_ID,
        "runtime_surface": "Codex",
        "skill_id": skill_id,
        "entry": str(entry),
        "run_dir": str(run_dir.resolve()),
        "command": command,
        "extra_args": extra_args,
        "cwd": str(cwd),
        "started_at": child["started_at"],
        "finished_at": child["finished_at"],
        "elapsed_seconds": child["elapsed_seconds"],
        "returncode": child["returncode"],
        "status": "CLEAN_PASS" if accepted else "BLOCKED",
        "execution_purpose": execution_purpose,
        "request_fingerprint": request_fingerprint_value,
        "failure_class": production_readiness["failure_class"],
        "production_policy_sha256": production_policy_sha256(),
        "production_readiness": production_readiness,
        "facade_sha256": sha256_file(entry),
        "executor_sha256": sha256_file(Path(__file__).resolve()),
        "contract_sha256": contract["contract_sha256"],
        "production_surface_signature": postflight_signature_after,
        "business_bindings": contract.get("business_bindings", []),
        "contract_preflight": {
            "status": contract_preflight.get("status"),
            "catalog_count": contract_preflight.get("catalog_count"),
            "contract_count": contract_preflight.get("contract_count"),
            "surface_signature": current_signature,
        },
        "contract_postflight": {
            "status": postflight_preflight.get("status"),
            "catalog_count": postflight_preflight.get("catalog_count"),
            "contract_count": postflight_preflight.get("contract_count"),
            "surface_signature_before": postflight_signature_before,
            "surface_signature_after": postflight_signature_after,
            "errors": contract_stability_errors,
        },
        "stock_business_lease": lease,
        "workflow_telemetry": stages,
        "tdx_process_integrity": child.get("tdx_process_integrity", {}),
        "tdx_process_guard": tdx_process_guard,
        "evidence_set": evidence_set,
        "supplemental_sources": {"lianban_daily": lianban_source},
        "binding_errors": binding_errors,
        "contract_stability_errors": contract_stability_errors,
        "business_stdout_validation": business_stdout_validation,
        "semantic_assertions": all_assertions,
        "required_artifacts": required_artifacts,
    }
    receipt = write_receipt(root, payload, str(child["stdout"]), str(child["stderr"]))
    if child["stdout"]:
        print(child["stdout"], end="" if str(child["stdout"]).endswith("\n") else "\n")
    if child["stderr"]:
        print(child["stderr"], file=sys.stderr, end="" if str(child["stderr"]).endswith("\n") else "\n")
    summary = {
        "runtime": RUNTIME_ID,
        "skill_id": skill_id,
        "status": payload["status"],
        "receipt": str(receipt.resolve()),
        "receipt_sha256": sha256_file(receipt),
    }
    print("STOCK_RUNTIME_RECEIPT " + json.dumps(summary, ensure_ascii=False), file=sys.stderr)
    return 0 if accepted else 2


def run(entry_file: str, extra: list[str]) -> int:
    entry = Path(entry_file).resolve()
    runtime_started = time.monotonic()
    stages: list[dict[str, Any]] = []
    request_started = time.monotonic()
    root, skill_id, contract = skill_context(entry_file)
    extra_args = [str(item) for item in extra]
    request_errors = business_request_errors(contract, extra_args)
    append_workflow_stage(
        stages,
        "request_validation",
        request_started,
        status="CLEAN_PASS" if not request_errors else "BLOCKED",
        error_count=len(request_errors),
    )
    if request_errors:
        print(json.dumps({
            "runtime": RUNTIME_ID,
            "runtime_surface": "Codex",
            "skill_id": skill_id,
            "status": "BLOCKED",
            "failure_owner": "stock_workflow_guard",
            "errors": request_errors,
            "workflow_telemetry": stages,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    preflight_started = time.monotonic()
    signature_before = contract_surface_signature()
    contract_preflight = global_contract_preflight()
    signature_after = contract_surface_signature()
    preflight_clean = (
        contract_preflight.get("status") == "CLEAN_PASS"
        and signature_before == signature_after
    )
    append_workflow_stage(
        stages,
        "global_contract_preflight",
        preflight_started,
        status="CLEAN_PASS" if preflight_clean else "BLOCKED",
        surface_stable=signature_before == signature_after,
    )
    if not preflight_clean:
        errors = list(contract_preflight.get("errors", []))
        if signature_before != signature_after:
            errors.append("contract_surface_changed_during_preflight")
        print(json.dumps({
            "runtime": RUNTIME_ID,
            "runtime_surface": "Codex",
            "skill_id": skill_id,
            "status": "BLOCKED",
            "failure_owner": contract_preflight.get("failure_owner"),
            "errors": errors,
            "contract_preflight": contract_preflight,
            "workflow_telemetry": stages,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    lock_path = workflow_lock_path(skill_id)
    lock_timeout = workflow_lock_timeout(contract)
    queue_started = time.monotonic()
    try:
        with stock_business_lease(
            skill_id,
            lock_path=lock_path,
            timeout_seconds=lock_timeout,
        ) as lease:
            append_workflow_stage(
                stages,
                "workflow_queue_wait",
                queue_started,
                waited_seconds=lease.get("waited_seconds", 0.0),
                lock_path=str(lock_path),
            )
            return _run_with_business_lease(
                entry_file,
                extra_args,
                lease,
                root=root,
                skill_id=skill_id,
                contract=contract,
                contract_preflight=contract_preflight,
                preflight_signature=signature_after,
                workflow_stages=stages,
                runtime_started=runtime_started,
            )
    except StockBusinessLeaseTimeout as exc:
        append_workflow_stage(
            stages,
            "workflow_queue_wait",
            queue_started,
            status="BLOCKED",
            lock_path=str(lock_path),
            timeout_seconds=lock_timeout,
        )
        print(json.dumps({
            "runtime": RUNTIME_ID,
            "runtime_surface": "Codex",
            "skill_id": skill_id,
            "status": "BLOCKED",
            "failure_owner": "stock_business_serialization_gate",
            "errors": [str(exc)],
            "workflow_telemetry": stages,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


def verify_receipt_evidence_set(receipt: dict[str, Any]) -> list[str]:
    evidence_set = receipt.get("evidence_set")
    if not isinstance(evidence_set, dict):
        return ["receipt_evidence_set_missing"]
    if evidence_set.get("enabled") is False:
        return [] if evidence_set.get("status") == "DISABLED" else [
            "receipt_evidence_set_disabled_status_invalid"
        ]
    if evidence_set.get("status") != "CLEAN_PASS":
        return ["receipt_evidence_set_status_not_clean"]
    manifest = evidence_set.get("manifest")
    payload = evidence_set.get("payload")
    if not isinstance(manifest, dict) or not isinstance(payload, dict):
        return ["receipt_evidence_set_binding_invalid"]
    manifest_path = Path(str(manifest.get("path") or "")).resolve()
    if not manifest_path.is_file():
        return [f"receipt_evidence_set_manifest_missing:{manifest_path}"]
    if (
        int(manifest.get("size", -1)) != manifest_path.stat().st_size
        or str(manifest.get("sha256") or "") != sha256_file(manifest_path)
    ):
        return ["receipt_evidence_set_manifest_hash_or_size_mismatch"]
    try:
        readback = load_evidence_set(
            manifest_path,
            expected_batch_id=str(payload.get("batch_id") or ""),
            expected_trading_date=str(payload.get("trading_date") or ""),
        )
    except EvidenceSetError as exc:
        return [f"receipt_evidence_set_invalid:{exc}"]
    if readback.get("evidence_set_id") != payload.get("evidence_set_id"):
        return ["receipt_evidence_set_id_mismatch"]
    return []


def verify_receipt_payload(
    entry_file: str,
    receipt_path: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    entry = Path(entry_file).resolve()
    root, skill_id, contract = skill_context(entry_file)
    path = Path(receipt_path).resolve()
    errors: list[str] = []
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return ({
            "runtime": RUNTIME_ID,
            "runtime_surface": "Codex",
            "skill_id": skill_id,
            "status": "BLOCKED",
            "receipt": str(path),
            "errors": [f"receipt_read_error:{type(exc).__name__}:{exc}"],
        }, None)
    errors.extend(validate_receipt_schema(receipt))
    surface_before = contract_surface_signature()
    current_preflight = global_contract_preflight()
    surface_after = contract_surface_signature()
    if current_preflight.get("status") != "CLEAN_PASS":
        errors.extend(
            f"authorization_{error}"
            for error in current_preflight.get("errors", [])
        )
    if surface_before != surface_after:
        errors.append("authorization_contract_surface_changed")
    if receipt.get("production_surface_signature") != surface_after:
        errors.append("receipt_production_surface_signature_mismatch")
    if receipt.get("receipt_integrity") != receipt_integrity(receipt):
        errors.append("receipt_integrity_mismatch")
    if receipt.get("skill_id") != skill_id:
        errors.append("receipt_skill_mismatch")
    if receipt.get("status") != "CLEAN_PASS":
        errors.append("receipt_status_not_clean")
    if receipt.get("entry") != str(entry):
        errors.append("receipt_entry_mismatch")
    errors.extend(validate_contract_bindings(entry, contract))
    errors.extend(verify_receipt_evidence_set(receipt))
    for key in ("facade_sha256", "executor_sha256", "contract_sha256"):
        if receipt.get(key) != contract.get(key):
            errors.append(f"receipt_{key}_mismatch")
    run_dir = Path(str(receipt.get("run_dir", "")))
    extra_args = receipt.get("extra_args", [])
    if (
        not isinstance(extra_args, list)
        or not all(isinstance(item, str) for item in extra_args)
    ):
        errors.append("receipt_extra_args_invalid")
        extra_args = []
    execution_purpose = str(receipt.get("execution_purpose") or "")
    expected_request_fingerprint = request_fingerprint(
        skill_id,
        str(contract["contract_sha256"]),
        extra_args,
        execution_purpose,
    )
    if receipt.get("request_fingerprint") != expected_request_fingerprint:
        errors.append("receipt_request_fingerprint_mismatch")
    expected_command, expected_cwd, _ = expanded_execution(contract, root, run_dir)
    expected_command.extend(extra_args)
    if receipt.get("command") != expected_command:
        errors.append("receipt_command_mismatch")
    if receipt.get("cwd") != str(expected_cwd):
        errors.append("receipt_cwd_mismatch")
    logs: dict[str, str] = {}
    for name in ("stdout_artifact", "stderr_artifact"):
        artifact = receipt.get(name, {})
        artifact_path = Path(str(artifact.get("path", "")))
        if not artifact_path.is_file():
            errors.append(f"{name}_missing")
            logs[name] = ""
            continue
        data = artifact_path.read_bytes()
        if artifact.get("size") != len(data) or artifact.get("sha256") != sha256_bytes(data):
            errors.append(f"{name}_hash_or_size_mismatch")
        logs[name] = data.decode("utf-8", "replace")
    for artifact in receipt.get("required_artifacts", []):
        artifact_path = Path(str(artifact.get("path", "")))
        if not artifact_path.is_file():
            errors.append(f"required_artifact_missing:{artifact_path}")
            continue
        data = artifact_path.read_bytes()
        if artifact.get("size") != len(data) or artifact.get("sha256") != sha256_bytes(data):
            errors.append(f"required_artifact_hash_or_size_mismatch:{artifact_path}")
    rerun = evaluate_semantic_assertions(
        contract.get("semantic_assertions", []),
        int(receipt.get("returncode", -999)),
        logs.get("stdout_artifact", ""),
        logs.get("stderr_artifact", ""),
    )
    recorded_semantic = [
        row for row in receipt.get("semantic_assertions", [])
        if row.get("type") != "required_artifact"
    ]
    if rerun != recorded_semantic:
        errors.append("semantic_assertions_recompute_mismatch")
    if not all(row.get("ok") for row in receipt.get("semantic_assertions", [])):
        errors.append("recorded_assertion_failure")
    rerun_business_stdout = evaluate_business_stdout(
        skill_id,
        logs.get("stdout_artifact", ""),
        require_data_gate=execution_purpose == "stock_conclusion",
    )
    if rerun_business_stdout != receipt.get("business_stdout_validation"):
        errors.append("business_stdout_validation_recompute_mismatch")
    errors.extend(rerun_business_stdout["errors"])
    payload = {
        "runtime": RUNTIME_ID,
        "runtime_surface": "Codex",
        "skill_id": skill_id,
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "receipt": str(path),
        "receipt_sha256": sha256_file(path),
        "contract_sha256": contract["contract_sha256"],
        "production_surface_signature": surface_after,
        "errors": errors,
    }
    return payload, receipt


def verify_receipt(entry_file: str, receipt_path: str) -> int:
    payload, _ = verify_receipt_payload(entry_file, receipt_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "CLEAN_PASS" else 2


def normalized_path_key(value: str | Path, base: Path | None = None) -> str:
    path = Path(str(value))
    if not path.is_absolute() and base is not None:
        path = base / path
    return os.path.normcase(str(path.resolve()))


def manifest_declared_hashes(
    payload: Any,
    target: Path,
    manifest_path: Path,
) -> list[str]:
    target_key = normalized_path_key(target)
    hashes: list[str] = []

    def add_if_target(path_value: Any, hash_value: Any) -> None:
        if not isinstance(path_value, str) or not isinstance(hash_value, str):
            return
        if normalized_path_key(path_value, manifest_path.parent) == target_key:
            hashes.append(hash_value.casefold())

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            add_if_target(node.get("path"), node.get("sha256"))
            for key, value in node.items():
                if isinstance(key, str) and key.casefold().endswith("_sha256"):
                    base_key = key[:-7]
                    add_if_target(node.get(base_key), value)
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(payload)
    return sorted(set(hashes))


def manifest_validation_is_clean(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    clean = True

    def visit(node: Any, parent_key: str | None = None) -> None:
        nonlocal clean
        if isinstance(node, dict):
            relevant = parent_key is None or any(
                token in parent_key.casefold()
                for token in MANIFEST_VALIDATION_TOKENS
            )
            if relevant:
                if "status" in node:
                    status = node.get("status")
                    if (
                        not isinstance(status, str)
                        or status.strip().upper() not in CLEAN_DELIVERY_STATUSES
                    ):
                        clean = False
                elif node and all(isinstance(value, bool) for value in node.values()):
                    if not all(node.values()):
                        clean = False
                recorded_errors = node.get("errors")
                if isinstance(recorded_errors, list) and recorded_errors:
                    clean = False
            for key, value in node.items():
                visit(value, str(key))
        elif isinstance(node, list):
            for value in node:
                visit(value, parent_key)

    visit(payload)
    return clean


def contract_has_binding_token(
    contract: dict[str, Any],
    tokens: tuple[str, ...],
) -> bool:
    for binding in contract.get("business_bindings", []):
        if not isinstance(binding, dict):
            continue
        path_text = str(binding.get("path", "")).casefold()
        if any(token in path_text for token in tokens):
            return True
    return False


def delivery_artifact_evidence(
    receipt: dict[str, Any],
    contract: dict[str, Any],
    artifact_path: Path,
) -> tuple[list[str], str | None, str | None]:
    errors: list[str] = []
    if not artifact_path.is_file():
        return (
            [f"delivery_artifact_missing:{artifact_path}"],
            None,
            None,
        )

    policy = contract.get("delivery_policy")
    if policy != DELIVERY_POLICY:
        return (["delivery_policy_invalid"], None, None)

    current_hash = sha256_file(artifact_path)
    target_key = normalized_path_key(artifact_path)
    binding_source: str | None = None
    manifest_source: str | None = None
    direct_mismatch = False

    if policy["allow_receipt_bound_artifact"]:
        for artifact in receipt.get("required_artifacts", []):
            if not isinstance(artifact, dict):
                continue
            if normalized_path_key(str(artifact.get("path", ""))) != target_key:
                continue
            if str(artifact.get("sha256", "")).casefold() == current_hash:
                binding_source = "receipt_required_artifact"
            else:
                direct_mismatch = True
            break

    manifest_binding_found = False
    manifest_hash_match = False
    manifest_clean = True
    if binding_source is None and policy["allow_manifest_bound_artifact"]:
        for artifact in receipt.get("required_artifacts", []):
            if not isinstance(artifact, dict):
                continue
            manifest_path = Path(str(artifact.get("path", ""))).resolve()
            if manifest_path.suffix.casefold() != ".json" or not manifest_path.is_file():
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            declared_hashes = manifest_declared_hashes(
                manifest,
                artifact_path,
                manifest_path,
            )
            if not declared_hashes:
                continue
            manifest_binding_found = True
            manifest_source = str(manifest_path)
            if current_hash in declared_hashes:
                manifest_hash_match = True
            if (
                policy["require_clean_manifest_validation"]
                and not manifest_validation_is_clean(manifest)
            ):
                manifest_clean = False
            break
        if manifest_binding_found and manifest_hash_match and manifest_clean:
            binding_source = "receipt_bound_manifest"

    if binding_source is None:
        if direct_mismatch:
            errors.append("artifact_receipt_hash_mismatch")
        elif manifest_binding_found and not manifest_hash_match:
            errors.append("artifact_manifest_hash_mismatch")
        elif manifest_binding_found and not manifest_clean:
            errors.append("manifest_validation_not_clean")
        else:
            errors.append("artifact_not_receipt_or_manifest_bound")
    elif manifest_binding_found and not manifest_clean:
        errors.append("manifest_validation_not_clean")

    if artifact_path.suffix.casefold() in FORMATTED_DELIVERY_EXTENSIONS:
        if (
            policy["formatted_artifact_requires_template_binding"]
            and not contract_has_binding_token(
                contract,
                TEMPLATE_BINDING_TOKENS,
            )
        ):
            errors.append("formatted_artifact_template_binding_missing")
        if (
            policy["formatted_artifact_requires_validator_binding"]
            and not contract_has_binding_token(
                contract,
                VALIDATOR_BINDING_TOKENS,
            )
        ):
            errors.append("formatted_artifact_validator_binding_missing")

    return errors, binding_source, manifest_source


def authorize_delivery(
    entry_file: str,
    receipt_path: str,
    artifact_path: str | None = None,
) -> int:
    _, skill_id, contract = skill_context(entry_file)
    receipt_verification, receipt = verify_receipt_payload(
        entry_file,
        receipt_path,
    )
    errors = list(receipt_verification.get("errors", []))
    artifact: dict[str, Any] | None = None
    binding_source: str | None = None
    manifest_source: str | None = None
    delivery_kind = "stock_conclusion"
    if artifact_path is not None:
        delivery_kind = "stock_artifact"
        target = Path(artifact_path).resolve()
        if receipt is not None:
            artifact_errors, binding_source, manifest_source = (
                delivery_artifact_evidence(receipt, contract, target)
            )
            errors.extend(artifact_errors)
        else:
            errors.append("receipt_unavailable_for_artifact_authorization")
        if target.is_file():
            artifact = file_artifact(target)
        else:
            artifact = {"path": str(target)}
    elif receipt is not None:
        readiness = receipt.get("production_readiness")
        if (
            receipt.get("execution_purpose") != "stock_conclusion"
            or not isinstance(readiness, dict)
            or readiness.get("conclusion_eligible") is not True
        ):
            errors.append("receipt_not_conclusion_eligible")

    receipt = receipt or {}
    receipt_file = Path(receipt_path).resolve()
    payload: dict[str, Any] = {
        "schema": "STOCK_DELIVERY_AUTHORIZATION_V1",
        "runtime": RUNTIME_ID,
        "runtime_surface": "Codex",
        "skill_id": skill_id,
        "status": "CLEAN_PASS" if not errors else "BLOCKED",
        "delivery_kind": delivery_kind,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "receipt": {
            "path": str(receipt_file),
            "sha256": sha256_file(receipt_file) if receipt_file.is_file() else None,
            "contract_sha256": receipt.get("contract_sha256"),
        },
        "artifact": artifact,
        "binding_source": binding_source,
        "manifest_source": manifest_source,
        "errors": sorted(set(errors)),
        "authorization": None,
    }
    if errors:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    suffix = "conclusion"
    if artifact is not None:
        suffix = str(artifact["sha256"])[:16]
    authorization_path = (
        receipt_file.parent
        / f"{receipt_file.stem}.{suffix}.delivery-authorization.json"
    )
    persisted = dict(payload)
    persisted["authorization_path"] = str(authorization_path)
    atomic_write_json(authorization_path, persisted)
    readback = json.loads(authorization_path.read_text(encoding="utf-8"))
    if readback != persisted:
        payload["status"] = "BLOCKED"
        payload["errors"] = ["authorization_readback_mismatch"]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    payload["authorization"] = file_artifact(authorization_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


RETRYABLE_COMPLETION_ERRORS = {
    "receipt_contract_sha256_mismatch",
    "receipt_executor_sha256_mismatch",
}
RETRYABLE_COMPLETION_ERROR_PREFIXES = (
    "business_file_hash_mismatch:",
)


def completion_errors_are_retryable(errors: set[str]) -> bool:
    return bool(errors) and all(
        error in RETRYABLE_COMPLETION_ERRORS
        or error.startswith(RETRYABLE_COMPLETION_ERROR_PREFIXES)
        for error in errors
    )


def complete_with_retry(
    run_attempt: Callable[[int], dict[str, Any]],
    authorize_attempt: Callable[[str], dict[str, Any]],
    *,
    prepare_retry: Callable[[set[str], int], dict[str, Any]] | None = None,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """Run and authorize until transient drift clears without rewriting contracts."""
    if max_attempts < 1:
        raise ValueError("max_attempts_must_be_positive")
    attempts: list[dict[str, Any]] = []
    for attempt in range(1, max_attempts + 1):
        run_result = run_attempt(attempt)
        receipt = str(run_result.get("receipt") or "")
        record: dict[str, Any] = {
            "attempt": attempt,
            "run": run_result,
            "authorization": None,
        }
        attempts.append(record)
        if run_result.get("status") != "CLEAN_PASS" or not receipt:
            return {
                "status": "BLOCKED",
                "attempt_count": attempt,
                "attempts": attempts,
                "errors": list(run_result.get("errors") or ["business_run_not_clean"]),
            }
        authorization = authorize_attempt(receipt)
        record["authorization"] = authorization
        if authorization.get("status") == "CLEAN_PASS":
            return {
                "status": "CLEAN_PASS",
                "attempt_count": attempt,
                "receipt": receipt,
                "authorization": authorization,
                "attempts": attempts,
                "errors": [],
            }
        errors = {str(item) for item in authorization.get("errors", [])}
        retryable = completion_errors_are_retryable(errors)
        if not retryable or attempt == max_attempts:
            return {
                "status": "BLOCKED",
                "attempt_count": attempt,
                "receipt": receipt,
                "authorization": authorization,
                "attempts": attempts,
                "errors": sorted(errors or {"authorization_not_clean"}),
            }
        if prepare_retry is not None:
            retry_preparation = prepare_retry(errors, attempt)
            record["retry_preparation"] = retry_preparation
            if retry_preparation.get("status") != "CLEAN_PASS":
                return {
                    "status": "BLOCKED",
                    "attempt_count": attempt,
                    "receipt": receipt,
                    "authorization": authorization,
                    "attempts": attempts,
                    "errors": list(
                        retry_preparation.get("errors")
                        or ["completion_retry_preparation_not_clean"]
                    ),
                }
    raise AssertionError("completion_loop_unreachable")


def parse_complete_request(arguments: list[str]) -> dict[str, Any]:
    artifact_relative: str | None = None
    max_attempts = 3
    business_args: list[str] = []
    index = 0
    while index < len(arguments):
        value = arguments[index]
        if value == "--":
            business_args = [str(item) for item in arguments[index + 1:]]
            break
        if value == "--artifact-relative":
            if index + 1 >= len(arguments):
                raise ValueError("artifact_relative_value_missing")
            artifact_relative = str(arguments[index + 1])
            index += 2
            continue
        if value == "--max-attempts":
            if index + 1 >= len(arguments):
                raise ValueError("max_attempts_value_missing")
            max_attempts = int(arguments[index + 1])
            index += 2
            continue
        raise ValueError(f"unknown_complete_argument:{value}")
    if not business_args:
        raise ValueError("complete_business_args_missing")
    if max_attempts < 1 or max_attempts > 5:
        raise ValueError("max_attempts_out_of_range")
    return {
        "artifact_relative": artifact_relative,
        "max_attempts": max_attempts,
        "business_args": business_args,
    }


def completion_run_command(entry: Path, business_args: list[str]) -> list[str]:
    """Build the facade run command without leaking the canonical `run` intent.

    `complete -- run` uses ``run`` as the explicit business-action marker required
    by the completion contract.  Canonical adapters already own the underlying
    legacy ``run`` command, so forwarding that lone marker makes argparse reject
    an otherwise valid completion.  All other action-specific argument vectors
    remain byte-for-byte ordered and are forwarded through the facade.
    """
    normalized = [str(item) for item in business_args]
    command = [sys.executable, str(entry), "run"]
    if len(normalized) == 1 and normalized[0].strip().casefold() == "run":
        return command
    return [*command, "--", *normalized]


def wait_for_contract_stability(
    *,
    timeout_seconds: float = 30.0,
    poll_seconds: float = 0.5,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_signature: str | None = None
    last_preflight: dict[str, Any] | None = None
    observations = 0
    while time.monotonic() < deadline:
        before = contract_surface_signature()
        observations += 1
        last_preflight = global_contract_preflight()
        after = contract_surface_signature()
        observations += 1
        last_signature = after
        if (
            last_preflight.get("status") == "CLEAN_PASS"
            and before == after
        ):
            return {
                "status": "CLEAN_PASS",
                "contract_catalog_sha256": (
                    sha256_file(CONTRACTS_PATH)
                    if CONTRACTS_PATH.is_file()
                    else None
                ),
                "contract_surface_signature": after,
                "observations": observations,
                "errors": [],
            }
        time.sleep(poll_seconds)
    return {
        "status": "BLOCKED",
        "contract_catalog_sha256": (
            sha256_file(CONTRACTS_PATH)
            if CONTRACTS_PATH.is_file()
            else None
        ),
        "contract_surface_signature": last_signature,
        "observations": observations,
        "errors": list((last_preflight or {}).get("errors", []) or ["contract_catalog_not_stable"]),
    }


def _receipt_summary_from_stderr(stderr: str) -> dict[str, Any] | None:
    marker = "STOCK_RUNTIME_RECEIPT "
    for line in reversed(stderr.splitlines()):
        if not line.startswith(marker):
            continue
        try:
            payload = json.loads(line[len(marker):])
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
    return None


def _json_object(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text.strip())
    except json.JSONDecodeError as exc:
        return {
            "status": "BLOCKED",
            "errors": [f"json_output_invalid:{exc}"],
        }
    return payload if isinstance(payload, dict) else {
        "status": "BLOCKED",
        "errors": ["json_output_not_object"],
    }


def reconcile_completion_contract_drift(
    errors: set[str],
    attempt: int,
) -> dict[str, Any]:
    check_child = run_process(
        [sys.executable, str(SYNC_CONTRACTS_PATH), "--check"],
        SKILLS_ROOT / "stock-unified",
        60,
        process_role="contract_check",
    )
    check_payload = _json_object(str(check_child.get("stdout", "")))
    if (
        check_child.get("returncode") != 0
        or check_payload.get("status") != "CLEAN_PASS"
    ):
        return {
            "status": "BLOCKED",
            "attempt": attempt,
            "trigger_errors": sorted(errors),
            "errors": ["completion_contract_drift_requires_explicit_sync"],
            "contract_check": check_payload,
        }
    stability = wait_for_contract_stability()
    return {
        "status": stability.get("status"),
        "attempt": attempt,
        "trigger_errors": sorted(errors),
        "errors": list(stability.get("errors", [])),
        "contract_check": check_payload,
        "contract_stability": stability,
    }


def complete_delivery(entry_file: str, arguments: list[str]) -> int:
    try:
        request = parse_complete_request(arguments)
    except Exception as exc:
        print(json.dumps({
            "schema": "STOCK_COMPLETION_GATE_V1",
            "status": "BLOCKED",
            "errors": [f"{type(exc).__name__}:{exc}"],
        }, ensure_ascii=False, indent=2))
        return 2

    entry = Path(entry_file).resolve()
    root, skill_id, contract = skill_context(entry_file)
    artifact_relative = request["artifact_relative"]

    def run_attempt(attempt: int) -> dict[str, Any]:
        stability = wait_for_contract_stability()
        if stability.get("status") != "CLEAN_PASS":
            return {
                "status": "BLOCKED",
                "attempt": attempt,
                "errors": stability.get("errors", []),
                "contract_stability": stability,
            }
        command = completion_run_command(entry, request["business_args"])
        child = run_process(
            command,
            root,
            int(contract["timeout_seconds"]) + 120,
            process_role="business",
        )
        summary = _receipt_summary_from_stderr(str(child.get("stderr", "")))
        if summary is None:
            return {
                "status": "BLOCKED",
                "attempt": attempt,
                "errors": ["runtime_receipt_summary_missing"],
                "returncode": child.get("returncode"),
                "contract_stability": stability,
            }
        return {
            **summary,
            "attempt": attempt,
            "returncode": child.get("returncode"),
            "contract_stability": stability,
        }

    def authorize_attempt(receipt_path: str) -> dict[str, Any]:
        conclusion_command = [
            sys.executable,
            str(entry),
            "authorize",
            "--receipt",
            receipt_path,
        ]
        conclusion_child = run_process(
            conclusion_command,
            root,
            60,
            process_role="authorize",
        )
        conclusion = _json_object(str(conclusion_child.get("stdout", "")))
        if conclusion.get("status") != "CLEAN_PASS":
            return conclusion
        if artifact_relative is None:
            return {
                "status": "CLEAN_PASS",
                "errors": [],
                "conclusion": conclusion,
                "artifact": None,
            }
        receipt = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
        run_dir = Path(str(receipt["run_dir"])).resolve()
        target = (run_dir / artifact_relative).resolve()
        if os.path.commonpath((str(run_dir), str(target))) != str(run_dir):
            return {
                "status": "BLOCKED",
                "errors": ["artifact_relative_escapes_run_dir"],
            }
        artifact_command = [
            sys.executable,
            str(entry),
            "authorize",
            "--receipt",
            receipt_path,
            "--artifact",
            str(target),
        ]
        artifact_child = run_process(
            artifact_command,
            root,
            60,
            process_role="authorize",
        )
        artifact = _json_object(str(artifact_child.get("stdout", "")))
        errors = list(artifact.get("errors", []))
        return {
            "status": "CLEAN_PASS" if artifact.get("status") == "CLEAN_PASS" else "BLOCKED",
            "errors": errors,
            "conclusion": conclusion,
            "artifact": artifact,
        }

    result = complete_with_retry(
        run_attempt,
        authorize_attempt,
        prepare_retry=reconcile_completion_contract_drift,
        max_attempts=int(request["max_attempts"]),
    )
    payload = {
        "schema": "STOCK_COMPLETION_GATE_V1",
        "runtime": RUNTIME_ID,
        "skill_id": skill_id,
        **result,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "CLEAN_PASS" else 2


def facade_main(entry_file: str) -> int:
    arguments = sys.argv[1:]
    command = arguments[0] if arguments else "info"
    if command == "info":
        return info(entry_file)
    if command == "selftest":
        return selftest(entry_file)
    if command == "run":
        extra = arguments[2:] if len(arguments) > 1 and arguments[1] == "--" else arguments[1:]
        return run(entry_file, extra)
    if command == "verify":
        if len(arguments) != 3 or arguments[1] != "--receipt":
            print("usage: codex_entry.py verify --receipt <path>", file=sys.stderr)
            return 2
        return verify_receipt(entry_file, arguments[2])
    if command == "authorize":
        if (
            len(arguments) not in (3, 5)
            or arguments[1] != "--receipt"
            or (len(arguments) == 5 and arguments[3] != "--artifact")
        ):
            print(
                "usage: codex_entry.py authorize --receipt <path> "
                "[--artifact <path>]",
                file=sys.stderr,
            )
            return 2
        artifact = arguments[4] if len(arguments) == 5 else None
        return authorize_delivery(entry_file, arguments[2], artifact)
    if command == "complete":
        return complete_delivery(entry_file, arguments[1:])
    print(
        "usage: codex_entry.py {info|selftest|run|verify|authorize|complete}",
        file=sys.stderr,
    )
    return 2


def runtime_main(arguments: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if arguments is None else arguments)
    if len(args) == 3 and args[0] == "route" and args[1] == "--query":
        try:
            result = route_stock_query(args[2])
        except Exception as exc:
            print(json.dumps({
                "schema": "STOCK_SKILL_ROUTE_V1",
                "status": "BLOCKED",
                "error": f"{type(exc).__name__}:{exc}",
            }, ensure_ascii=False, indent=2), file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(
        "usage: stock_canonical_runtime.py route --query <text>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(runtime_main())
