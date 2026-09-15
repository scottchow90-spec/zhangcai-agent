from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


sys.dont_write_bytecode = True
SKILL_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = SKILL_DIR / "workflow_manifest.json"
TEMPLATE_CONTRACT_PATH = SKILL_DIR / "references" / "report_template_contract.json"
REPORT_BUILDER = SKILL_DIR / "scripts" / "report_builder.py"
REPORT_VALIDATOR = SKILL_DIR / "scripts" / "report_validator.py"
WORD_COM_RENDERER = SKILL_DIR / "scripts" / "word_com_render.py"
DEFAULT_DOCUMENT_PYTHON = (
    Path.home()
    / ".cache"
    / "codex-runtimes"
    / "codex-primary-runtime"
    / "dependencies"
    / "python"
    / "python.exe"
)
from audit_payload import PayloadAuditError, audit_payload, load_and_audit
from live_data_pipeline import collect_payload
from logic_analysis import analyze_board
from market_data import resolve_market_snapshot, run_selftests as freshness_selftests, validate_data_evidence


def emit(value: dict) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def read_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def command_info(_: argparse.Namespace) -> int:
    emit(
        {
            "status": "PASS",
            "skill_name": "a-share-leader-deep-research",
            "display_name": "龙头深度研究",
            "skill_dir": str(SKILL_DIR),
            "manifest": read_manifest(),
            "commands": ["info", "live-market", "run", "replay", "validate", "verify-report", "selftest"],
        }
    )
    return 0


def command_live_market(_: argparse.Namespace) -> int:
    try:
        snapshot = resolve_market_snapshot()
    except Exception as exc:
        emit({"status": "BLOCKED", "error": f"{type(exc).__name__}:{exc}"})
        return 2
    emit(snapshot)
    return 0


def validate_file(path: Path) -> tuple[dict, int]:
    try:
        structural = load_and_audit(path)
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        snapshot = resolve_market_snapshot()
        freshness = validate_data_evidence(payload, snapshot)
    except (OSError, json.JSONDecodeError, PayloadAuditError, ValueError, RuntimeError) as exc:
        return {"status": "BLOCKED", "error": str(exc)}, 2
    phase = snapshot["market_phase"]
    expected_mode = "intraday" if phase in {"active", "midday_pause", "preopen_with_current_data"} else "close"
    errors = list(freshness.get("errors") or [])
    if payload.get("data_mode") != expected_mode:
        errors.append(f"data_mode_mismatch:{payload.get('data_mode')}!={expected_mode}")
    result = {
        "status": "PASS" if not errors else "BLOCKED",
        "structural_audit": structural,
        "market_snapshot": snapshot,
        "freshness_audit": freshness,
        "expected_data_mode": expected_mode,
        "errors": errors,
        "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    return result, 0 if not errors else 2


def command_validate(args: argparse.Namespace) -> int:
    result, code = validate_file(Path(args.input).resolve())
    emit(result)
    return code


def run_child(command: list[str], cwd: Path, timeout: int, stdout_path: Path, stderr_path: Path) -> int:
    environment = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    }
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=environment,
    )
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    return completed.returncode


def document_python() -> Path:
    override = os.environ.get("CODEX_WORKSPACE_PYTHON")
    candidate = Path(override).resolve() if override else DEFAULT_DOCUMENT_PYTHON
    if not candidate.is_file():
        raise RuntimeError(f"workspace_document_python_missing:{candidate}")
    return candidate


def default_output_path(workflow_dir: Path, trade_date: str) -> Path:
    return workflow_dir / f"龙头深度研究_{trade_date}.docx"


def command_run(args: argparse.Namespace) -> int:
    try:
        snapshot = resolve_market_snapshot()
        if snapshot.get("status") != "PASS":
            raise RuntimeError(f"market_snapshot_blocked:{snapshot.get('errors')}")
        compact_date = str(snapshot["latest_available_trade_date"])
        trade_date = f"{compact_date[:4]}-{compact_date[4:6]}-{compact_date[6:8]}"
        run_dir = (
            Path(args.run_dir).resolve()
            if args.run_dir
            else SKILL_DIR / "reports" / "production_runs" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        )
        workflow_dir = run_dir / "leader_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        output_path = (
            Path(args.output).resolve()
            if args.output
            else default_output_path(workflow_dir, trade_date)
        )
        payload_path = workflow_dir / "leader_payload.json"
        payload, manifest_path = collect_payload(
            trade_date,
            str(snapshot["market_phase"]),
            workflow_dir,
            payload_path,
            TEMPLATE_CONTRACT_PATH,
        )
        validation, validation_code = validate_file(payload_path)
        (workflow_dir / "payload_validation.json").write_text(
            json.dumps(validation, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if validation_code != 0:
            emit({"status": "BLOCKED", "stage": "payload_validation", "detail": validation})
            return 2

        builder_code = run_child(
            [
                str(document_python()),
                str(REPORT_BUILDER),
                "--input",
                str(payload_path),
                "--manifest",
                str(manifest_path),
                "--output",
                str(output_path),
                "--template-contract",
                str(TEMPLATE_CONTRACT_PATH),
            ],
            SKILL_DIR,
            180,
            workflow_dir / "report_builder.stdout.txt",
            workflow_dir / "report_builder.stderr.txt",
        )
        if builder_code != 0:
            emit({"status": "BLOCKED", "stage": "report_build", "returncode": builder_code})
            return 2

        render_dir = workflow_dir / "render"
        word_render_stdout = workflow_dir / "word_render.stdout.txt"
        word_render_code = run_child(
            [
                str(document_python()),
                str(WORD_COM_RENDERER),
                str(output_path),
                "--output-dir",
                str(render_dir),
            ],
            workflow_dir,
            300,
            word_render_stdout,
            workflow_dir / "word_render.stderr.txt",
        )
        if word_render_code != 0:
            emit({
                "status": "BLOCKED",
                "stage": "word_com_render",
                "word_com_returncode": word_render_code,
            })
            return 2
        word_render = json.loads(word_render_stdout.read_text(encoding="utf-8"))
        template_contract = json.loads(TEMPLATE_CONTRACT_PATH.read_text(encoding="utf-8"))
        required_renderer = template_contract["render"]["required_renderer"]
        if (
            word_render.get("status") != "PASS"
            or word_render.get("renderer") != required_renderer
        ):
            emit({
                "status": "BLOCKED",
                "stage": "word_com_render_identity",
                "required_renderer": required_renderer,
                "detail": word_render,
            })
            return 2

        verifier_stdout = workflow_dir / "report_validation.stdout.txt"
        verifier_code = run_child(
            [
                str(document_python()),
                str(REPORT_VALIDATOR),
                "--docx",
                str(output_path),
                "--input",
                str(payload_path),
                "--manifest",
                str(manifest_path),
                "--template-contract",
                str(TEMPLATE_CONTRACT_PATH),
                "--render-dir",
                str(render_dir),
            ],
            SKILL_DIR,
            120,
            verifier_stdout,
            workflow_dir / "report_validation.stderr.txt",
        )
        verifier = json.loads(verifier_stdout.read_text(encoding="utf-8"))
        if verifier_code != 0 or verifier.get("status") != "PASS":
            emit({"status": "BLOCKED", "stage": "report_validation", "detail": verifier})
            return 2
        result = {
            "status": "PASS",
            "workflow_name": "龙头深度研究",
            "trade_date": trade_date,
            "market_phase": snapshot["market_phase"],
            "run_dir": str(workflow_dir),
            "payload": str(payload_path),
            "payload_sha256": hashlib.sha256(payload_path.read_bytes()).hexdigest(),
            "docx": str(output_path),
            "docx_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
            "pdf": str(render_dir / f"{output_path.stem}.pdf"),
            "renderer": word_render["renderer"],
            "word_page_count": word_render["word_page_count"],
            "render_page_count": verifier["render"]["page_count"],
            "stock_count": len(payload["stocks"]),
            "concept_count": len(payload["concept_summary"]),
            "morning_count": len(payload["morning_limit_ups"]),
            "lhb_count": len(payload["lhb_net_buy_ge_100m"]),
            "validation": verifier,
        }
        (workflow_dir / "run_result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        emit(result)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        emit({"status": "BLOCKED", "stage": "run", "error": f"{type(exc).__name__}:{exc}"})
        return 2


DYNAMIC_BOARD_ROLES = {
    "高度锚",
    "机制锚",
    "时序领先",
    "容量核心",
    "换手回封核心",
}


def _sha256_json(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _fact_view(payload: dict) -> dict:
    result = copy.deepcopy(payload)
    result.pop("replay_provenance", None)
    for stock in result.get("stocks", []):
        if isinstance(stock, dict):
            stock.pop("leader_roles", None)
    for concept in result.get("concept_summary", []):
        if not isinstance(concept, dict):
            continue
        for key in (
            "logic_model",
            "logic_summary",
            "mechanism_evidence",
            "validation_constraints",
            "nature_top",
            "position_top",
        ):
            concept.pop(key, None)
    return result


def _authorized_replay_source(path: Path) -> tuple[dict, Path, dict]:
    executions = (SKILL_DIR / "reports" / "executions").resolve()
    runs = (executions / "runs").resolve()
    source = path.resolve()
    try:
        source.relative_to(runs)
    except ValueError as exc:
        raise RuntimeError("replay_source_outside_canonical_runs") from exc
    if not source.is_file() or source.name != "leader_payload.json":
        raise RuntimeError("replay_source_payload_missing")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    for receipt_path in sorted(executions.glob("*.receipt.json"), reverse=True):
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        readiness = receipt.get("production_readiness")
        if (
            receipt.get("status") != "CLEAN_PASS"
            or receipt.get("execution_purpose") != "stock_conclusion"
            or not isinstance(readiness, dict)
            or readiness.get("conclusion_eligible") is not True
        ):
            continue
        bound = next(
            (
                item
                for item in receipt.get("required_artifacts", [])
                if isinstance(item, dict)
                and Path(str(item.get("path") or "")).resolve() == source
                and str(item.get("sha256") or "") == source_sha
            ),
            None,
        )
        if not bound:
            continue
        authorization_path = receipt_path.with_name(
            receipt_path.name.replace(
                ".receipt.json",
                ".receipt.conclusion.delivery-authorization.json",
            )
        )
        if not authorization_path.is_file():
            continue
        authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
        if authorization.get("status") != "CLEAN_PASS":
            continue
        evidence_set = receipt.get("evidence_set")
        evidence_payload = (
            evidence_set.get("payload") if isinstance(evidence_set, dict) else None
        )
        if not isinstance(evidence_payload, dict):
            continue
        required_environment = {
            "CODEX_STOCK_EVIDENCE_SET_BATCH_ID": evidence_payload.get("batch_id"),
            "CODEX_STOCK_EVIDENCE_SET_ID": evidence_payload.get("evidence_set_id"),
            "CODEX_STOCK_EVIDENCE_TRADING_DATE": evidence_payload.get("trading_date"),
        }
        mismatches = [
            name
            for name, expected in required_environment.items()
            if str(os.environ.get(name) or "") != str(expected or "")
        ]
        if mismatches:
            raise RuntimeError(
                "replay_evidence_environment_mismatch:" + ",".join(mismatches)
            )
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
        if payload.get("trade_date") != evidence_payload.get("trading_date"):
            raise RuntimeError("replay_trade_date_mismatch")
        return payload, receipt_path, receipt
    raise RuntimeError("replay_source_not_bound_to_authorized_conclusion")


def _stock_evidence_ids(stock: dict) -> list[str]:
    field_evidence = stock.get("field_evidence")
    if not isinstance(field_evidence, dict):
        return []
    values: list[str] = []
    for items in field_evidence.values():
        if isinstance(items, list):
            values.extend(str(item) for item in items if str(item).strip())
    return list(dict.fromkeys(values))


def recompute_authorized_payload(payload: dict, source_receipt: Path) -> dict:
    result = copy.deepcopy(payload)
    fact_sha_before = _sha256_json(_fact_view(result))
    stocks = result.get("stocks") if isinstance(result.get("stocks"), list) else []
    concepts = (
        result.get("concept_summary")
        if isinstance(result.get("concept_summary"), list)
        else []
    )
    for stock in stocks:
        roles = stock.get("leader_roles") if isinstance(stock.get("leader_roles"), list) else []
        stock["leader_roles"] = [
            role
            for role in roles
            if not isinstance(role, dict)
            or str(role.get("name") or "") not in DYNAMIC_BOARD_ROLES
        ]
    lhb_codes = {
        str(row.get("stock_code") or "")
        for row in result.get("lhb_net_buy_ge_100m", [])
        if isinstance(row, dict)
    }
    supplemental_context = (
        result.get("supplemental_context")
        if isinstance(result.get("supplemental_context"), dict)
        else {}
    )
    for index, concept in enumerate(concepts):
        if index >= 3 or not isinstance(concept, dict):
            continue
        board = str(concept.get("concept") or "")
        members = [
            stock for stock in stocks if str(stock.get("primary_concept") or "") == board
        ]
        analysis = analyze_board(
            board,
            members,
            lhb_codes=lhb_codes,
            supplemental_context=supplemental_context,
        )
        stock_by_code = {str(stock["stock_code"]): stock for stock in members}
        for row in analysis["nature_top"]:
            stock = stock_by_code[str(row["stock_code"])]
            row["evidence_ids"] = _stock_evidence_ids(stock)
            for role_name in row["nature_names"]:
                stock["leader_roles"].append(
                    {
                        "name": role_name,
                        "reason": row["reason"],
                        "evidence_ids": row["evidence_ids"],
                    }
                )
        for row in analysis["position_top"]:
            row["evidence_ids"] = _stock_evidence_ids(
                stock_by_code[str(row["stock_code"])]
            )
        concept.update(
            {
                "logic_model": analysis,
                "logic_summary": analysis["logic_statement"],
                "mechanism_evidence": analysis["mechanism_statement"],
                "validation_constraints": analysis["validation_statement"],
                "nature_top": analysis["nature_top"],
                "position_top": analysis["position_top"],
            }
        )
    fact_sha_after = _sha256_json(_fact_view(result))
    if fact_sha_after != fact_sha_before:
        raise RuntimeError("replay_fact_surface_changed")
    result["replay_provenance"] = {
        "mode": "authorized_historical_logic_recompute",
        "source_receipt": str(source_receipt.resolve()),
        "fact_surface_sha256_before": fact_sha_before,
        "fact_surface_sha256_after": fact_sha_after,
        "recomputed_blocks": [
            "logic_model",
            "logic_summary",
            "mechanism_evidence",
            "validation_constraints",
            "nature_top",
            "position_top",
            "stocks.leader_roles",
        ],
    }
    return result


def _deliver_replay(
    workflow_dir: Path,
    payload_path: Path,
    manifest_path: Path,
    output_path: Path,
    payload: dict,
) -> int:
    builder_code = run_child(
        [
            str(document_python()),
            str(REPORT_BUILDER),
            "--input",
            str(payload_path),
            "--manifest",
            str(manifest_path),
            "--output",
            str(output_path),
            "--template-contract",
            str(TEMPLATE_CONTRACT_PATH),
        ],
        SKILL_DIR,
        180,
        workflow_dir / "report_builder.stdout.txt",
        workflow_dir / "report_builder.stderr.txt",
    )
    if builder_code != 0:
        emit({"status": "BLOCKED", "stage": "report_build", "returncode": builder_code})
        return 2
    render_dir = workflow_dir / "render"
    word_render_stdout = workflow_dir / "word_render.stdout.txt"
    word_render_code = run_child(
        [
            str(document_python()),
            str(WORD_COM_RENDERER),
            str(output_path),
            "--output-dir",
            str(render_dir),
        ],
        workflow_dir,
        300,
        word_render_stdout,
        workflow_dir / "word_render.stderr.txt",
    )
    if word_render_code != 0:
        emit({"status": "BLOCKED", "stage": "word_com_render", "word_com_returncode": word_render_code})
        return 2
    word_render = json.loads(word_render_stdout.read_text(encoding="utf-8"))
    required_renderer = json.loads(
        TEMPLATE_CONTRACT_PATH.read_text(encoding="utf-8")
    )["render"]["required_renderer"]
    if word_render.get("status") != "PASS" or word_render.get("renderer") != required_renderer:
        emit({"status": "BLOCKED", "stage": "word_com_render_identity", "detail": word_render})
        return 2
    verifier_stdout = workflow_dir / "report_validation.stdout.txt"
    verifier_code = run_child(
        [
            str(document_python()),
            str(REPORT_VALIDATOR),
            "--docx",
            str(output_path),
            "--input",
            str(payload_path),
            "--manifest",
            str(manifest_path),
            "--template-contract",
            str(TEMPLATE_CONTRACT_PATH),
            "--render-dir",
            str(render_dir),
        ],
        SKILL_DIR,
        120,
        verifier_stdout,
        workflow_dir / "report_validation.stderr.txt",
    )
    verifier = json.loads(verifier_stdout.read_text(encoding="utf-8"))
    if verifier_code != 0 or verifier.get("status") != "PASS":
        emit({"status": "BLOCKED", "stage": "report_validation", "detail": verifier})
        return 2
    result = {
        "status": "PASS",
        "workflow_name": "龙头深度研究",
        "trade_date": payload["trade_date"],
        "market_phase": "historical_close_replay",
        "run_dir": str(workflow_dir),
        "payload": str(payload_path),
        "payload_sha256": hashlib.sha256(payload_path.read_bytes()).hexdigest(),
        "docx": str(output_path),
        "docx_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "pdf": str(render_dir / f"{output_path.stem}.pdf"),
        "renderer": word_render["renderer"],
        "word_page_count": word_render["word_page_count"],
        "render_page_count": verifier["render"]["page_count"],
        "stock_count": len(payload["stocks"]),
        "concept_count": len(payload["concept_summary"]),
        "morning_count": len(payload["morning_limit_ups"]),
        "lhb_count": len(payload["lhb_net_buy_ge_100m"]),
        "validation": verifier,
    }
    (workflow_dir / "run_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    emit(result)
    return 0


def command_replay(args: argparse.Namespace) -> int:
    try:
        input_path = Path(args.input).resolve()
        source_payload, source_receipt_path, _ = _authorized_replay_source(input_path)
        payload = recompute_authorized_payload(source_payload, source_receipt_path)
        trade_date = str(payload["trade_date"])
        run_dir = (
            Path(args.run_dir).resolve()
            if args.run_dir
            else SKILL_DIR / "reports" / "production_runs" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        )
        workflow_dir = run_dir / "leader_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        payload_path = workflow_dir / "leader_payload.json"
        payload_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        payload_sha = hashlib.sha256(payload_path.read_bytes()).hexdigest()
        manifest_path = workflow_dir / "result_manifest.json"
        manifest = {
            "schema": "LEADER_DEEP_RESEARCH_RUN_MANIFEST_V1",
            "trade_date": trade_date,
            "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
            "result_path": str(payload_path),
            "result_sha256": payload_sha,
            "template_contract_path": str(TEMPLATE_CONTRACT_PATH),
            "template_contract_sha256": hashlib.sha256(TEMPLATE_CONTRACT_PATH.read_bytes()).hexdigest(),
            "replay_source_path": str(input_path),
            "replay_source_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
            "replay_source_receipt": str(source_receipt_path.resolve()),
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        structural = audit_payload(payload)
        validation = {
            "status": "PASS",
            "mode": "authorized_historical_logic_recompute",
            "structural_audit": structural,
            "trade_date": trade_date,
            "source_receipt": str(source_receipt_path.resolve()),
            "fact_surface_sha256": payload["replay_provenance"]["fact_surface_sha256_after"],
            "input_sha256": payload_sha,
            "errors": [],
        }
        (workflow_dir / "payload_validation.json").write_text(
            json.dumps(validation, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        output_path = (
            Path(args.output).resolve()
            if args.output
            else default_output_path(workflow_dir, trade_date)
        )
        return _deliver_replay(
            workflow_dir,
            payload_path,
            manifest_path,
            output_path,
            payload,
        )
    except (OSError, ValueError, RuntimeError, PayloadAuditError, json.JSONDecodeError) as exc:
        emit({"status": "BLOCKED", "stage": "replay", "error": f"{type(exc).__name__}:{exc}"})
        return 2


def command_verify_report(args: argparse.Namespace) -> int:
    render_dir = Path(args.render_dir).resolve() if args.render_dir else None
    stdout_path = Path(args.output_json).resolve() if args.output_json else None
    command = [
        str(document_python()),
        str(REPORT_VALIDATOR),
        "--docx",
        str(Path(args.file).resolve()),
        "--input",
        str(Path(args.input).resolve()),
        "--manifest",
        str(Path(args.manifest).resolve()),
        "--template-contract",
        str(TEMPLATE_CONTRACT_PATH),
    ]
    if render_dir:
        command.extend(["--render-dir", str(render_dir)])
    completed = subprocess.run(
        command,
        cwd=str(SKILL_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if stdout_path:
        stdout_path.write_text(completed.stdout, encoding="utf-8")
    print(completed.stdout, end="")
    return completed.returncode


def source(source_id: str, group: str) -> dict:
    digest = hashlib.sha256(f"{source_id}-{group}".encode()).hexdigest()
    return {
        "source_id": source_id,
        "source_name": f"合成来源{source_id}",
        "provider_group": group,
        "source_type": "行情数据",
        "trade_date": "2099-01-05",
        "fetched_at": "2099-01-05T10:00:00+08:00",
        "locator": f"synthetic://{source_id}",
        "sha256": digest,
    }


def evidence(evidence_id: str, source_id: str, field: str, value: object) -> dict:
    return {
        "evidence_id": evidence_id,
        "source_id": source_id,
        "stock_code": "999001",
        "field": field,
        "value": value,
        "trade_date": "2099-01-05",
        "captured_at": "2099-01-05T10:00:00+08:00",
        "locator": f"synthetic://{source_id}/{field}",
    }


def synthetic_fixture() -> dict:
    sources = [source("S1", "甲组"), source("S2", "乙组")]
    evidence_rows = [
        evidence("E1", "S1", "涨停池", True), evidence("E2", "S2", "涨停池", True),
        evidence("E3", "S1", "主概念", "大科技"), evidence("E4", "S2", "主概念", "大科技"),
        evidence("E5", "S1", "封板时间", "10:00:00"), evidence("E6", "S2", "封板时间", "10:00:00"),
    ]
    stock = {
        "stock_code": "999001",
        "stock_name": "合成样本",
        "exchange": "合成交易所",
        "primary_concept": "大科技",
        "secondary_concepts": ["人工智能"],
        "event_drivers": ["1项合成事件"],
        "classification_basis": "2个独立来源均归入大科技。",
        "limit_up_price": 10.0,
        "at_limit_at_cutoff": True,
        "close_at_limit": True,
        "first_limit_time": "10:00:00",
        "latest_seal_time_at_cutoff": "10:00:00",
        "final_limit_time": "10:00:00",
        "open_count": 0,
        "consecutive_limit_count": 1,
        "recent_limit_count": 1,
        "recent_limit_up_label": "1天1板",
        "amount": 100_000_000,
        "turnover_rate": 5.0,
        "source_nature": "人工智能",
        "field_evidence": {"pool": ["E1", "E2"], "concept": ["E3", "E4"], "times": ["E5", "E6"]},
        "leader_roles": [{"name": "先锋龙头", "reason": "1只样本最早封板。", "evidence_ids": ["E5", "E6"]}],
    }
    logic_model = analyze_board("大科技", [stock])
    for row in logic_model["nature_top"]:
        row["evidence_ids"] = ["E5", "E6"]
    for row in logic_model["position_top"]:
        row["evidence_ids"] = ["E5", "E6"]
    return {
        "workflow_name": "龙头深度研究",
        "schema_version": "3.2",
        "trade_date": "2099-01-05",
        "data_mode": "close",
        "generated_at": "2099-01-05T15:10:00+08:00",
        "data_cutoff": "2099-01-05T15:05:00+08:00",
        "sources": sources,
        "evidence": evidence_rows,
        "stocks": [stock],
        "concept_summary": [{
            "concept": "大科技",
            "verified_limit_up_count": 1,
            "earliest_first_limit_time": "10:00:00",
            "logic_model": logic_model,
            "logic_summary": logic_model["logic_statement"],
            "mechanism_evidence": logic_model["mechanism_statement"],
            "validation_constraints": logic_model["validation_statement"],
            "nature_top": logic_model["nature_top"],
            "position_top": logic_model["position_top"],
        }],
        "morning_limit_ups": [{"stock_code": "999001"}],
        "lhb_status": "not_published",
        "lhb_net_buy_ge_100m": [],
        "report_claims": [{"claim_id": "C1", "text": "大科技共有1只涨停样本。", "evidence_ids": ["E1", "E2"]}],
        "unresolved_critical_conflicts": [],
    }


def command_selftest(_: argparse.Namespace) -> int:
    checks: list[dict] = []
    try:
        audit_payload(synthetic_fixture())
        checks.append({"name": "有效结构样本", "status": "PASS"})
    except Exception as exc:
        checks.append({"name": "有效结构样本", "status": "FAIL", "error": str(exc)})
    invalid = synthetic_fixture()
    invalid["stocks"][0]["primary_concept"] = "其他"
    try:
        audit_payload(invalid)
        checks.append({"name": "含糊概念拦截", "status": "FAIL"})
    except PayloadAuditError:
        checks.append({"name": "含糊概念拦截", "status": "PASS"})
    invalid = synthetic_fixture()
    invalid["report_claims"][0]["text"] = "该股有望后市可期。"
    try:
        audit_payload(invalid)
        checks.append({"name": "模板结论拦截", "status": "FAIL"})
    except PayloadAuditError:
        checks.append({"name": "模板结论拦截", "status": "PASS"})
    freshness = freshness_selftests()
    checks.append({"name": "技能内市场新鲜度九项", "status": freshness.get("status"), "detail": freshness})
    try:
        contract = json.loads(TEMPLATE_CONTRACT_PATH.read_text(encoding="utf-8"))
        required = contract.get("required_section_order") or []
        checks.append({
            "name": "正式模板合同",
            "status": (
                "PASS"
                if len(required) >= 8
                and required[0] == "A股每日涨停板"
                and "涨停家数前三板块深度分析" in required
                else "FAIL"
            ),
        })
    except Exception as exc:
        checks.append({"name": "正式模板合同", "status": "FAIL", "error": str(exc)})
    checks.append({
        "name": "正式报告生成与验收脚本",
        "status": "PASS" if REPORT_BUILDER.is_file() and REPORT_VALIDATOR.is_file() else "FAIL",
    })
    status = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    emit({"status": status, "checked_at": datetime.now(timezone.utc).isoformat(), "checks": checks})
    return 0 if status == "PASS" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="龙头深度研究唯一执行入口")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("info").set_defaults(func=command_info)
    sub.add_parser("live-market").set_defaults(func=command_live_market)
    run = sub.add_parser("run")
    run.add_argument("--run-dir")
    run.add_argument("--output")
    run.set_defaults(func=command_run)
    replay = sub.add_parser("replay")
    replay.add_argument("--input", required=True)
    replay.add_argument("--run-dir")
    replay.add_argument("--output")
    replay.set_defaults(func=command_replay)
    validate = sub.add_parser("validate")
    validate.add_argument("--input", required=True)
    validate.set_defaults(func=command_validate)
    delivery = sub.add_parser("verify-report")
    delivery.add_argument("--file", required=True)
    delivery.add_argument("--input", required=True)
    delivery.add_argument("--manifest", required=True)
    delivery.add_argument("--render-dir", required=True)
    delivery.add_argument("--output-json")
    delivery.set_defaults(func=command_verify_report)
    sub.add_parser("selftest").set_defaults(func=command_selftest)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
