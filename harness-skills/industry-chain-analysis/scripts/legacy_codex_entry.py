from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import hashlib
import json
import os
import py_compile
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = ROOT.parent
RUN_ROOT = ROOT / "run"
RUNS_ROOT = RUN_ROOT / "runs"
TEST_RUNS_ROOT = RUN_ROOT / "test-runs"
LATEST = RUN_ROOT / "latest.json"
LATEST_TEST = RUN_ROOT / "latest_test.json"
SELFTEST = RUN_ROOT / "selftest.json"
STATUS_READBACK = RUN_ROOT / "status_readback.json"
TEST_STATUS_READBACK = RUN_ROOT / "test_status_readback.json"
TDX_SMOKE = RUN_ROOT / "tdx_smoke.json"
TDX_SMOKE_READBACK = RUN_ROOT / "tdx_smoke_readback.json"
TDX_ENTRY = SKILLS_ROOT / "tdx-local-hub" / "scripts" / "codex_entry.py"
TDX_HQ_CACHE = Path("C:/new_tdx_mock/T0002/hq_cache")
TDX_TNF = {
    "SH": TDX_HQ_CACHE / "shs.tnf",
    "SZ": TDX_HQ_CACHE / "szs.tnf",
    "BJ": TDX_HQ_CACHE / "bjs.tnf",
}
SCHEMA = "INDUSTRY-CHAIN-ANALYSIS-INPUT-1"
RESULT_SCHEMA = "INDUSTRY-CHAIN-ANALYSIS-RESULT-1"
MANIFEST_SCHEMA = "INDUSTRY-CHAIN-ANALYSIS-MANIFEST-1"
READBACK_SCHEMA = "INDUSTRY-CHAIN-ANALYSIS-READBACK-1"
MODES = {"industry", "beneficiary-review", "mindset"}
STANCES = {"SUPPORTED", "WATCH", "AVOID", "INSUFFICIENT_EVIDENCE", "NOT_APPLICABLE"}
REQUIRED_FILES = [
    ROOT / "SKILL.md",
    ROOT / "agents" / "openai.yaml",
    ROOT / "references" / "industry_chain.md",
    ROOT / "references" / "stock.md",
    ROOT / "references" / "mindset.md",
    ROOT / "references" / "quantification.md",
    ROOT / "references" / "evidence_schema.md",
    Path(__file__).resolve(),
]


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_tdx_symbol(value: str) -> tuple[str, str, str]:
    match = re.fullmatch(r"(\d{6})\.(SH|SZ|BJ)", value.strip().upper())
    if not match:
        raise ValueError("TDX smoke symbol must use CODE.SH, CODE.SZ, or CODE.BJ")
    code, market = match.groups()
    return f"{code}.{market}", code, market


def lookup_tdx_name(code: str, market: str) -> tuple[str, Path]:
    path = TDX_TNF[market]
    if not path.is_file():
        raise FileNotFoundError(f"TDX name table missing: {path}")
    text = path.read_bytes().decode("gbk", errors="ignore")
    match = re.search(rf"{re.escape(code)}\x00{{2,}}([^\x00]{{2,16}})", text)
    if not match or not match.group(1).strip():
        raise ValueError(f"symbol name not found in {path}: {code}.{market}")
    return match.group(1).strip(), path


def decode_json_stream(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    index = 0
    values: list[dict[str, Any]] = []
    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            break
        value, index = decoder.raw_decode(text, index)
        if not isinstance(value, dict):
            raise ValueError("TDX entry emitted a non-object JSON value")
        values.append(value)
    return values


def invoke_tdx(arguments: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not TDX_ENTRY.is_file():
        raise FileNotFoundError(f"TDX canonical entry missing: {TDX_ENTRY}")
    invocation_nonce = uuid.uuid4().hex
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["CODEX_TDX_INVOCATION_NONCE"] = invocation_nonce
    command = [str(Path(sys.executable).resolve()), str(TDX_ENTRY), "run", "--", *arguments]
    completed = subprocess.run(
        command,
        cwd=TDX_ENTRY.parent,
        capture_output=True,
        env=environment,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"tdx-local-hub failed with exit code {completed.returncode}: "
            f"{completed.stderr.decode('utf-8', errors='replace').strip()}"
        )
    try:
        business = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"tdx-local-hub business stdout is not strict UTF-8 JSON: {exc}") from exc
    if not isinstance(business, dict):
        raise ValueError("tdx-local-hub business JSON root is not an object")
    try:
        stderr_text = completed.stderr.decode("utf-8")
        summary_line = next(line for line in reversed(stderr_text.splitlines()) if line.strip())
        receipt = json.loads(summary_line)
    except (UnicodeDecodeError, StopIteration, json.JSONDecodeError) as exc:
        raise ValueError(f"tdx-local-hub receipt summary is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(receipt, dict) or receipt.get("status") != "CLEAN_PASS":
        raise ValueError("tdx-local-hub CLEAN_PASS receipt missing")
    if receipt.get("schema") != "TDX-LOCAL-HUB-RECEIPT-SUMMARY-2":
        raise ValueError("tdx-local-hub receipt summary schema mismatch")
    if receipt.get("invocation_nonce") != invocation_nonce:
        raise ValueError("tdx-local-hub receipt nonce does not match this invocation")
    if receipt.get("arguments") != arguments:
        raise ValueError("tdx-local-hub receipt arguments do not match this invocation")

    execution_root = TDX_ENTRY.parents[1] / "reports" / "executions"
    receipt_path = Path(require_text(receipt, "receipt", "tdx_receipt_summary")).resolve()
    if receipt_path.parent != execution_root.resolve() or not receipt_path.is_file():
        raise ValueError("tdx-local-hub receipt path is outside the canonical execution directory")
    if receipt.get("receipt_sha256") != sha256(receipt_path):
        raise ValueError("tdx-local-hub receipt SHA-256 readback mismatch")
    if receipt.get("receipt_size_bytes") != receipt_path.stat().st_size:
        raise ValueError("tdx-local-hub receipt size readback mismatch")
    persisted = read_json(receipt_path)
    if persisted.get("schema") != "TDX-LOCAL-HUB-EXECUTION-RECEIPT-2":
        raise ValueError("tdx-local-hub persisted receipt schema mismatch")
    for field, expected in {
        "status": "CLEAN_PASS",
        "skill": "tdx-local-hub",
        "run_id": receipt.get("run_id"),
        "invocation_nonce": invocation_nonce,
        "arguments": arguments,
        "returncode": 0,
    }.items():
        if persisted.get(field) != expected:
            raise ValueError(f"tdx-local-hub persisted receipt field mismatch: {field}")
    acceptance = persisted.get("acceptance")
    if not isinstance(acceptance, dict) or not acceptance or not all(value is True for value in acceptance.values()):
        raise ValueError("tdx-local-hub persisted receipt acceptance is not fully CLEAN_PASS")

    expected_primary = TDX_ENTRY.parent / "tdx_hub.py"
    for label, expected_path in (("entry_artifact", TDX_ENTRY), ("primary_artifact", expected_primary)):
        summary_artifact = receipt.get(label)
        persisted_artifact = persisted.get(label)
        if not isinstance(summary_artifact, dict) or summary_artifact != persisted_artifact:
            raise ValueError(f"tdx-local-hub {label} summary/readback mismatch")
        artifact_path = Path(require_text(summary_artifact, "path", label)).resolve()
        if artifact_path != expected_path.resolve() or not artifact_path.is_file():
            raise ValueError(f"tdx-local-hub {label} path mismatch")
        if summary_artifact.get("size_bytes") != artifact_path.stat().st_size or summary_artifact.get("sha256") != sha256(artifact_path):
            raise ValueError(f"tdx-local-hub {label} current hash or size mismatch")

    stdout_artifact = persisted.get("stdout_artifact")
    if not isinstance(stdout_artifact, dict) or stdout_artifact != receipt.get("stdout_artifact"):
        raise ValueError("tdx-local-hub stdout artifact summary/readback mismatch")
    stdout_path = Path(require_text(stdout_artifact, "path", "stdout_artifact")).resolve()
    if stdout_path.parent != execution_root.resolve() or not stdout_path.is_file():
        raise ValueError("tdx-local-hub stdout artifact path mismatch")
    if stdout_path.read_bytes() != completed.stdout:
        raise ValueError("tdx-local-hub persisted stdout does not match this invocation")
    if stdout_artifact.get("size_bytes") != len(completed.stdout) or stdout_artifact.get("sha256") != sha256_bytes(completed.stdout):
        raise ValueError("tdx-local-hub stdout artifact hash or size mismatch")
    business_receipt = persisted.get("business")
    if not isinstance(business_receipt, dict) or business_receipt.get("stdout_sha256") != sha256_bytes(completed.stdout):
        raise ValueError("tdx-local-hub business stdout binding mismatch")
    return business, receipt


def parse_iso(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty ISO timestamp")
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field} is not a valid ISO timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone offset")
    return parsed


def parse_tdx_trade_date(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{8}", value):
        raise ValueError("TDX trade date must use YYYYMMDD")
    try:
        return datetime.strptime(value, "%Y%m%d").date().isoformat()
    except ValueError as exc:
        raise ValueError(f"TDX trade date is invalid: {value}") from exc


def require_text(container: dict[str, Any], field: str, context: str) -> str:
    value = container.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{field} must be a non-empty string")
    return value.strip()


def require_text_list(container: dict[str, Any], field: str, context: str) -> list[str]:
    value = container.get(field)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{context}.{field} must be a non-empty list")
    cleaned: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{context}.{field}[{index}] must be a non-empty string")
        cleaned.append(item.strip())
    return cleaned


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != SCHEMA:
        raise ValueError(f"schema must equal {SCHEMA}")
    mode = require_text(payload, "mode", "input")
    if mode not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}")
    subject = require_text(payload, "subject", "input")
    if len(subject) > 200:
        raise ValueError("subject must be 200 characters or fewer")
    as_of = require_text(payload, "as_of", "input")
    as_of_dt = parse_iso(as_of, "input.as_of")
    if as_of_dt.astimezone(timezone.utc) > datetime.now(timezone.utc).replace(microsecond=0):
        raise ValueError("input.as_of cannot be in the future")
    market_scope = require_text(payload, "market_scope", "input")
    test_mode = payload.get("test_mode", False)
    if not isinstance(test_mode, bool):
        raise ValueError("input.test_mode must be boolean")

    raw_evidence = payload.get("evidence")
    if not isinstance(raw_evidence, list):
        raise ValueError("input.evidence must be a list")
    if not test_mode and not raw_evidence:
        raise ValueError("production input requires at least one evidence item")
    evidence: list[dict[str, str]] = []
    evidence_ids: set[str] = set()
    for index, item in enumerate(raw_evidence):
        if not isinstance(item, dict):
            raise ValueError(f"input.evidence[{index}] must be an object")
        context = f"input.evidence[{index}]"
        evidence_id = require_text(item, "id", context)
        if evidence_id in evidence_ids:
            raise ValueError(f"duplicate evidence id: {evidence_id}")
        evidence_ids.add(evidence_id)
        normalized = {
            "id": evidence_id,
            "claim": require_text(item, "claim", context),
            "source_name": require_text(item, "source_name", context),
            "source_date": require_text(item, "source_date", context),
            "retrieved_at": require_text(item, "retrieved_at", context),
            "source_locator": require_text(item, "source_locator", context),
        }
        parse_iso(normalized["retrieved_at"], f"{context}.retrieved_at")
        if not test_mode and "example." in normalized["source_locator"].lower():
            raise ValueError("production input cannot use example domains")
        evidence.append(normalized)

    raw_sections = payload.get("sections")
    if not isinstance(raw_sections, list) or not raw_sections:
        raise ValueError("input.sections must be a non-empty list")
    sections: list[dict[str, Any]] = []
    for index, item in enumerate(raw_sections):
        if not isinstance(item, dict):
            raise ValueError(f"input.sections[{index}] must be an object")
        context = f"input.sections[{index}]"
        references = item.get("evidence_ids")
        if not isinstance(references, list):
            raise ValueError(f"{context}.evidence_ids must be a list")
        cleaned_references: list[str] = []
        for ref in references:
            if not isinstance(ref, str) or ref not in evidence_ids:
                raise ValueError(f"{context} references unknown evidence id: {ref}")
            cleaned_references.append(ref)
        if not test_mode and not cleaned_references:
            raise ValueError(f"{context} requires at least one evidence id in production mode")
        sections.append({
            "title": require_text(item, "title", context),
            "content": require_text_list(item, "content", context),
            "evidence_ids": cleaned_references,
        })

    conclusion = payload.get("conclusion")
    if not isinstance(conclusion, dict):
        raise ValueError("input.conclusion must be an object")
    stance = require_text(conclusion, "stance", "input.conclusion").upper()
    if stance not in STANCES:
        raise ValueError(f"conclusion.stance must be one of {sorted(STANCES)}")
    normalized_payload = {
        "schema": SCHEMA,
        "mode": mode,
        "subject": subject,
        "as_of": as_of_dt.isoformat(timespec="seconds"),
        "market_scope": market_scope,
        "test_mode": test_mode,
        "evidence": evidence,
        "sections": sections,
        "conclusion": {
            "stance": stance,
            "summary": require_text(conclusion, "summary", "input.conclusion"),
        },
        "risks": require_text_list(payload, "risks", "input"),
        "unverified": require_text_list(payload, "unverified", "input"),
    }
    return normalized_payload


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_report(payload: dict[str, Any]) -> str:
    mode_label = {
        "industry": "产业链深度研究",
        "beneficiary-review": "受益公司核验",
        "mindset": "研究纪律与风险框架",
    }[payload["mode"]]
    lines = [
        f"# {payload['subject']} - {mode_label}",
        "",
        f"- 数据截止时间：{payload['as_of']}",
        f"- 市场范围：{payload['market_scope']}",
        f"- 执行模式：{'合成自测，非市场结论' if payload['test_mode'] else '实际研究'}",
        "",
    ]
    for section in payload["sections"]:
        lines.extend([f"## {section['title']}", ""])
        lines.extend(f"- {item}" for item in section["content"])
        refs = ", ".join(section["evidence_ids"]) if section["evidence_ids"] else "无（仅限合成自测）"
        lines.extend([f"- 证据：{refs}", ""])
    lines.extend(["## 证据", "", "| ID | 事实 | 来源 | 来源日期 | 定位 |", "|---|---|---|---|---|"])
    for item in payload["evidence"]:
        lines.append(
            "| {id} | {claim} | {source_name} | {source_date} | {source_locator} |".format(
                **{key: markdown_cell(value) for key, value in item.items() if key != "retrieved_at"}
            )
        )
    if not payload["evidence"]:
        lines.append("| - | 合成自测未使用市场事实 | 本地自测 | - | - |")
    lines.extend([
        "",
        "## 结论",
        "",
        f"- 状态：{payload['conclusion']['stance']}",
        f"- 摘要：{payload['conclusion']['summary']}",
        "",
        "## 风险",
        "",
    ])
    lines.extend(f"- {item}" for item in payload["risks"])
    lines.extend(["", "## 未验证", ""])
    lines.extend(f"- {item}" for item in payload["unverified"])
    lines.extend([
        "",
        "本文基于公开信息提供研究与决策支持，不构成任何投资建议；市场有风险，决策需独立审慎。",
        "",
    ])
    return "\n".join(lines)


def make_run_id() -> str:
    return datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%f%z")


def run_analysis(payload: dict[str, Any], output_root: Path, latest_path: Path | None = None) -> dict[str, Any]:
    normalized = validate_payload(payload)
    run_dir = output_root / make_run_id()
    run_dir.mkdir(parents=True, exist_ok=False)
    input_path = run_dir / "input.json"
    result_path = run_dir / "result.json"
    report_path = run_dir / "report.md"
    write_json(input_path, normalized)
    result = {
        "schema": RESULT_SCHEMA,
        "skill": "industry-chain-analysis",
        "status": "PASS_TEST" if normalized["test_mode"] else "PASS",
        "generated_at": now_iso(),
        "mode": normalized["mode"],
        "subject": normalized["subject"],
        "as_of": normalized["as_of"],
        "market_scope": normalized["market_scope"],
        "test_mode": normalized["test_mode"],
        "evidence_count": len(normalized["evidence"]),
        "section_count": len(normalized["sections"]),
        "stance": normalized["conclusion"]["stance"],
        "summary": normalized["conclusion"]["summary"],
        "risks": normalized["risks"],
        "unverified": normalized["unverified"],
    }
    write_json(result_path, result)
    report_path.write_text(render_report(normalized), encoding="utf-8")
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "skill": "industry-chain-analysis",
        "status": result["status"],
        "generated_at": now_iso(),
        "run_dir": str(run_dir.resolve()),
        "test_mode": normalized["test_mode"],
        "subject": normalized["subject"],
        "artifacts": [artifact(input_path), artifact(result_path), artifact(report_path)],
    }
    manifest_path = run_dir / "manifest.json"
    write_json(manifest_path, manifest)
    if latest_path is not None:
        if normalized["test_mode"] and latest_path.resolve() == LATEST.resolve():
            raise ValueError("test_mode input cannot update the production latest.json pointer")
        write_json(latest_path, {
            "schema": MANIFEST_SCHEMA,
            "manifest_path": str(manifest_path.resolve()),
            "manifest_sha256": sha256(manifest_path),
            "manifest_size_bytes": manifest_path.stat().st_size,
            "updated_at": now_iso(),
        })
    return {"manifest": manifest, "manifest_path": manifest_path}


def verify_manifest(manifest_path: Path) -> dict[str, Any]:
    manifest = read_json(manifest_path)
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise ValueError("manifest schema mismatch")
    checks: list[dict[str, Any]] = []
    for expected in manifest.get("artifacts", []):
        path = Path(expected["path"])
        actual = artifact(path) if path.is_file() else {"path": str(path), "missing": True}
        ok = bool(
            path.is_file()
            and actual.get("size_bytes") == expected.get("size_bytes")
            and actual.get("sha256") == expected.get("sha256")
        )
        checks.append({"ok": ok, "expected": expected, "actual": actual})
    status = "PASS" if checks and all(item["ok"] for item in checks) else "FAIL"
    return {
        "schema": READBACK_SCHEMA,
        "status": status,
        "verified_at": now_iso(),
        "manifest_path": str(manifest_path.resolve()),
        "manifest_sha256": sha256(manifest_path),
        "business_status": manifest.get("status"),
        "test_mode": manifest.get("test_mode"),
        "subject": manifest.get("subject"),
        "artifact_checks": checks,
    }


def frontmatter_keys(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md frontmatter start missing")
    keys: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            return keys
        if line and not line.startswith((" ", "\t")) and ":" in line:
            keys.append(line.split(":", 1)[0].strip())
    raise ValueError("SKILL.md frontmatter end missing")


def command_info() -> int:
    integrations = {}
    for name in ["stock-analysis", "quality-track-stock-selection", "tdx-local-hub"]:
        integrations[name] = (SKILLS_ROOT / name / "SKILL.md").is_file()
    print(json.dumps({
        "name": "industry-chain-analysis",
        "display_name": "产业链深度研究",
        "target_system": "local Codex",
        "entry": str(Path(__file__).resolve()),
        "skills_root": str(SKILLS_ROOT.resolve()),
        "commands": ["info", "selftest", "tdx-smoke", "tdx-status", "run", "status"],
        "runtime": "Python standard library only",
        "integrations": integrations,
    }, ensure_ascii=False, indent=2))
    return 0


def tdx_ui_login_state(user_confirmed_login: bool) -> dict[str, Any]:
    if user_confirmed_login:
        return {
            "status": "user_confirmed",
            "source": "explicit_user_statement",
            "programmatic_ui_inspection": False,
            "statement": "通达信登录状态由用户确认",
        }
    return {
        "status": "not_assessed_by_command",
        "source": "none",
        "programmatic_ui_inspection": False,
        "statement": "本命令未判断通达信可见界面登录状态",
    }


def command_tdx_smoke(symbol_value: str, limit: int, user_confirmed_login: bool) -> int:
    if not 1 <= limit <= 120:
        raise ValueError("tdx-smoke limit must be between 1 and 120")
    symbol, code, market = normalize_tdx_symbol(symbol_value)
    name, tnf_path = lookup_tdx_name(code, market)
    status_payload, status_receipt = invoke_tdx(["status"])
    if not status_payload.get("ok") or not status_payload.get("tdx_process", {}).get("running"):
        raise ValueError("TDX status did not confirm a running TdxW process")
    kline_payload, kline_receipt = invoke_tdx(["kline", symbol, "--period", "day", "--limit", str(limit)])
    if not kline_payload.get("ok") or kline_payload.get("symbol") != symbol:
        raise ValueError("TDX kline response did not match the requested symbol")
    records = kline_payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("TDX kline response contained no records")
    kline_path = Path(require_text(kline_payload, "path", "tdx_kline"))
    status_receipt_path = Path(require_text(status_receipt, "receipt", "tdx_status_receipt"))
    kline_receipt_path = Path(require_text(kline_receipt, "receipt", "tdx_kline_receipt"))
    source_artifacts = [artifact(path) for path in [tnf_path, kline_path, status_receipt_path, kline_receipt_path]]
    ui_login_state = tdx_ui_login_state(user_confirmed_login)
    latest_record = records[-1]
    if not isinstance(latest_record, dict):
        raise ValueError("TDX latest record must be an object")
    latest_trade_date = parse_tdx_trade_date(latest_record.get("date"))
    payload = {
        "schema": "INDUSTRY-CHAIN-ANALYSIS-TDX-SMOKE-2",
        "skill": "industry-chain-analysis",
        "status": "PASS",
        "generated_at": now_iso(),
        "target_system": "local Codex -> tdx-local-hub -> C:\\new_tdx_mock",
        "symbol": symbol,
        "code": code,
        "name": name,
        "market": market,
        "tdx_ui_login_state": ui_login_state,
        "tdx_process": status_payload["tdx_process"],
        "formula_count": status_payload.get("formula_count"),
        "kline_period": kline_payload.get("period"),
        "kline_count": kline_payload.get("count"),
        "latest_trade_date": latest_trade_date,
        "latest_record": latest_record,
        "tdx_status_receipt": status_receipt,
        "tdx_kline_receipt": kline_receipt,
        "source_artifacts": source_artifacts,
        "verification_boundary": (
            f"{ui_login_state['statement']}。本命令证据覆盖 TdxW 进程状态、"
            "本地代码/名称/市场映射和可读取的日 K 线；不覆盖财报、公告或产业结论。"
        ),
    }
    write_json(TDX_SMOKE, payload)
    print(json.dumps({
        "status": payload["status"],
        "symbol": symbol,
        "name": name,
        "market": market,
        "tdx_ui_login_state": ui_login_state,
        "latest_trade_date": latest_trade_date,
        "latest_record": payload["latest_record"],
        "result_artifact": artifact(TDX_SMOKE),
    }, ensure_ascii=False, indent=2))
    return 0


def command_tdx_status() -> int:
    if not TDX_SMOKE.is_file():
        raise FileNotFoundError("tdx_smoke.json missing; run tdx-smoke first")
    smoke = read_json(TDX_SMOKE)
    checks: list[dict[str, Any]] = []
    for expected in smoke.get("source_artifacts", []):
        path = Path(expected["path"])
        actual = artifact(path) if path.is_file() else {"path": str(path), "missing": True}
        ok = bool(
            path.is_file()
            and actual.get("size_bytes") == expected.get("size_bytes")
            and actual.get("sha256") == expected.get("sha256")
        )
        checks.append({"ok": ok, "expected": expected, "actual": actual})
    current_name, current_tnf = lookup_tdx_name(smoke["code"], smoke["market"])
    identity_ok = bool(
        smoke.get("symbol") == f"{smoke['code']}.{smoke['market']}"
        and smoke.get("name") == current_name
        and str(current_tnf.resolve()) == smoke["source_artifacts"][0]["path"]
    )
    payload = {
        "schema": "INDUSTRY-CHAIN-ANALYSIS-TDX-READBACK-2",
        "status": "PASS" if checks and all(item["ok"] for item in checks) and identity_ok else "FAIL",
        "verified_at": now_iso(),
        "tdx_smoke_artifact": artifact(TDX_SMOKE),
        "symbol": smoke.get("symbol"),
        "name": smoke.get("name"),
        "market": smoke.get("market"),
        "tdx_ui_login_state": smoke.get("tdx_ui_login_state"),
        "latest_trade_date": smoke.get("latest_trade_date"),
        "latest_record": smoke.get("latest_record"),
        "identity_matches_tnf": identity_ok,
        "source_artifact_checks": checks,
        "verification_boundary": smoke.get("verification_boundary"),
    }
    write_json(TDX_SMOKE_READBACK, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


def command_selftest() -> int:
    checks: list[dict[str, Any]] = []
    for path in REQUIRED_FILES:
        checks.append({"check": f"required:{path.relative_to(ROOT)}", "ok": path.is_file()})
    keys = frontmatter_keys(ROOT / "SKILL.md")
    checks.append({"check": "frontmatter_keys", "ok": keys == ["name", "description"], "actual": keys})
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)
    checks.append({"check": "python_compile", "ok": True})
    text_surface = "\n".join(path.read_text(encoding="utf-8") for path in REQUIRED_FILES if path.suffix == ".md")
    forbidden = [token for token in ["neodata.query", "westock data", ".openclaw\\workspace"] if token in text_surface.lower()]
    checks.append({"check": "forbidden_runtime_dependencies", "ok": not forbidden, "actual": forbidden})
    integrations = {
        name: (SKILLS_ROOT / name / "SKILL.md").is_file()
        for name in ["stock-analysis", "quality-track-stock-selection", "tdx-local-hub"]
    }
    checks.append({"check": "local_stock_integrations", "ok": all(integrations.values()), "actual": integrations})
    checks.append({
        "check": "sibling_skills_root",
        "ok": SKILLS_ROOT == ROOT.parent and SKILLS_ROOT.is_dir(),
        "actual": str(SKILLS_ROOT.resolve()),
    })
    source_text = Path(__file__).read_text(encoding="utf-8")
    legacy_cli_name = "".join(["产业链研究与", "受益公司核验固定入口"])
    current_cli_name = "产业链深度研究固定入口"
    checks.append({
        "check": "cli_display_name",
        "ok": legacy_cli_name not in source_text and current_cli_name in source_text,
        "actual": current_cli_name if current_cli_name in source_text else "missing",
    })
    confirmed_login = tdx_ui_login_state(True)
    unassessed_login = tdx_ui_login_state(False)
    checks.append({
        "check": "tdx_user_confirmed_login_semantics",
        "ok": bool(
            confirmed_login == {
                "status": "user_confirmed",
                "source": "explicit_user_statement",
                "programmatic_ui_inspection": False,
                "statement": "通达信登录状态由用户确认",
            }
            and unassessed_login == {
                "status": "not_assessed_by_command",
                "source": "none",
                "programmatic_ui_inspection": False,
                "statement": "本命令未判断通达信可见界面登录状态",
            }
        ),
        "confirmed": confirmed_login,
        "without_confirmation": unassessed_login,
    })
    checks.append({
        "check": "tdx_trade_date_conversion",
        "ok": parse_tdx_trade_date("20260727") == "2026-07-27",
        "actual": parse_tdx_trade_date("20260727"),
    })
    invalid_trade_dates_rejected = True
    for invalid_trade_date in ["2026-07-27", "20260230", 20260727, None]:
        try:
            parse_tdx_trade_date(invalid_trade_date)
            invalid_trade_dates_rejected = False
        except ValueError:
            pass
    checks.append({
        "check": "tdx_invalid_trade_dates_rejected",
        "ok": invalid_trade_dates_rejected,
    })
    fixture = {
        "schema": SCHEMA,
        "mode": "industry",
        "subject": "合成产业链执行链自测",
        "as_of": now_iso(),
        "market_scope": "synthetic",
        "test_mode": True,
        "evidence": [{
            "id": "T1",
            "claim": "该事实仅用于验证证据绑定和报告渲染。",
            "source_name": "local selftest fixture",
            "source_date": datetime.now().date().isoformat(),
            "retrieved_at": now_iso(),
            "source_locator": "local://industry-chain-analysis/selftest",
        }],
        "sections": [{
            "title": "执行链",
            "content": ["入口能够校验证据引用并生成结构化结果。"],
            "evidence_ids": ["T1"],
        }],
        "conclusion": {"stance": "NOT_APPLICABLE", "summary": "仅验证技能执行链。"},
        "risks": ["合成输入不能证明实时市场研究能力。"],
        "unverified": ["实时数据采集未在自测中执行。"],
    }
    production_latest_before = artifact(LATEST) if LATEST.is_file() else None
    output = run_analysis(fixture, TEST_RUNS_ROOT, latest_path=LATEST_TEST)
    readback = verify_manifest(output["manifest_path"])
    latest_test = read_json(LATEST_TEST)
    latest_test_manifest = Path(require_text(latest_test, "manifest_path", "latest_test"))
    latest_test_ok = bool(
        latest_test_manifest.resolve() == output["manifest_path"].resolve()
        and latest_test.get("manifest_sha256") == sha256(output["manifest_path"])
        and latest_test.get("manifest_size_bytes") == output["manifest_path"].stat().st_size
    )
    checks.append({
        "check": "synthetic_run_and_readback",
        "ok": readback["status"] == "PASS" and readback["business_status"] == "PASS_TEST",
        "report_sha256": output["manifest"]["artifacts"][2]["sha256"],
    })
    checks.append({
        "check": "test_latest_pointer",
        "ok": latest_test_ok,
        "actual": str(latest_test_manifest.resolve()),
    })
    production_latest_after = artifact(LATEST) if LATEST.is_file() else None
    checks.append({
        "check": "production_latest_unchanged_by_selftest",
        "ok": production_latest_before == production_latest_after,
        "before": production_latest_before,
        "after": production_latest_after,
    })
    payload = {
        "schema": "INDUSTRY-CHAIN-ANALYSIS-SELFTEST-1",
        "skill": "industry-chain-analysis",
        "status": "PASS" if all(item["ok"] for item in checks) else "FAIL",
        "generated_at": now_iso(),
        "python": str(Path(sys.executable).resolve()),
        "checks": checks,
    }
    write_json(SELFTEST, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


def command_run(input_path: Path) -> int:
    payload = read_json(input_path.resolve())
    normalized = validate_payload(payload)
    output_root = TEST_RUNS_ROOT if normalized["test_mode"] else RUNS_ROOT
    latest_path = LATEST_TEST if normalized["test_mode"] else LATEST
    output = run_analysis(normalized, output_root, latest_path=latest_path)
    result_path = Path(output["manifest"]["artifacts"][1]["path"])
    result = read_json(result_path)
    print(json.dumps({
        "status": result["status"],
        "subject": result["subject"],
        "stance": result["stance"],
        "manifest": str(output["manifest_path"].resolve()),
        "manifest_sha256": sha256(output["manifest_path"]),
        "manifest_size_bytes": output["manifest_path"].stat().st_size,
    }, ensure_ascii=False, indent=2))
    return 0


def command_status(scope: str) -> int:
    latest_path = LATEST if scope == "production" else LATEST_TEST
    status_readback_path = STATUS_READBACK if scope == "production" else TEST_STATUS_READBACK
    if not latest_path.is_file():
        raise FileNotFoundError(f"{latest_path.name} missing; run the skill first")
    latest = read_json(latest_path)
    manifest_path = Path(require_text(latest, "manifest_path", "latest"))
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest missing: {manifest_path}")
    if sha256(manifest_path) != latest.get("manifest_sha256") or manifest_path.stat().st_size != latest.get("manifest_size_bytes"):
        raise ValueError(f"{latest_path.name} manifest hash or size mismatch")
    readback = verify_manifest(manifest_path)
    expected_test_mode = scope == "test"
    if readback.get("test_mode") is not expected_test_mode:
        raise ValueError(f"{latest_path.name} points to the wrong execution scope")
    write_json(status_readback_path, readback)
    print(json.dumps(readback, ensure_ascii=False, indent=2))
    return 0 if readback["status"] == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="产业链深度研究固定入口")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("info")
    subparsers.add_parser("selftest")
    tdx_smoke_parser = subparsers.add_parser("tdx-smoke")
    tdx_smoke_parser.add_argument("--symbol", required=True)
    tdx_smoke_parser.add_argument("--limit", type=int, default=5)
    tdx_smoke_parser.add_argument(
        "--user-confirmed-login",
        action="store_true",
        help="记录当前用户已明确确认通达信登录；该参数不表示程序执行过界面检查",
    )
    subparsers.add_parser("tdx-status")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--input", type=Path, required=True)
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--scope", choices=["production", "test"], default="production")
    args = parser.parse_args()
    if args.command == "info":
        return command_info()
    if args.command == "selftest":
        return command_selftest()
    if args.command == "tdx-smoke":
        return command_tdx_smoke(args.symbol, args.limit, args.user_confirmed_login)
    if args.command == "tdx-status":
        return command_tdx_status()
    if args.command == "run":
        return command_run(args.input)
    if args.command == "status":
        return command_status(args.scope)
    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
