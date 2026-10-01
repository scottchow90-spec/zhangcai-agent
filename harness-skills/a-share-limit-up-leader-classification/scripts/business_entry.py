from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import hashlib
import importlib.util
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

sys.dont_write_bytecode = True

from audit_payload import PayloadAuditError, audit_payload, load_and_audit
from docx_conclusion_gate import audit_docx, audit_paragraphs


SKILL_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = SKILL_DIR / "workflow_manifest.json"


def read_manifest() -> dict:
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def emit(value: dict) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def command_info(_: argparse.Namespace) -> int:
    manifest = read_manifest()
    emit(
        {
            "status": "PASS",
            "workflow": manifest,
            "skill_dir": str(SKILL_DIR),
            "allowed_now": ["info", "review", "selftest", "validate", "verify-docx"],
        }
    )
    return 0


def command_review(_: argparse.Namespace) -> int:
    manifest = read_manifest()
    emit(
        {
            "status": "REVIEW_PENDING" if not manifest.get("live_run_allowed") else "APPROVED",
            "workflow_name": manifest.get("workflow_name"),
            "live_run_allowed": bool(manifest.get("live_run_allowed")),
            "review_files": [
                str(SKILL_DIR / "references" / "workflow.md"),
                str(SKILL_DIR / "references" / "data_contract.md"),
                str(SKILL_DIR / "references" / "classification_rules.md"),
                str(SKILL_DIR / "references" / "report_spec.md"),
            ],
            "message": "未获用户明确审核通过前，禁止采集当日数据和生成实盘结论。",
        }
    )
    return 0


def _source(source_id: str, group: str, source_type: str) -> dict:
    digest = hashlib.sha256(f"{source_id}-{group}".encode("utf-8")).hexdigest()
    return {
        "source_id": source_id,
        "source_name": f"合成来源{source_id}",
        "provider_group": group,
        "source_type": source_type,
        "trade_date": "2099-01-05",
        "fetched_at": "2099-01-05T19:00:00+08:00",
        "locator": f"synthetic://{source_id}",
        "sha256": digest,
    }


def _evidence(evidence_id: str, source_id: str, code: str, field: str, value: object) -> dict:
    return {
        "evidence_id": evidence_id,
        "source_id": source_id,
        "stock_code": code,
        "field": field,
        "value": value,
        "trade_date": "2099-01-05",
        "captured_at": "2099-01-05T19:00:00+08:00",
        "locator": f"synthetic://{source_id}/{code}/{field}",
    }


def synthetic_fixture() -> dict:
    code = "999001"
    sources = [
        _source("S1", "甲组", "涨停池"),
        _source("S2", "乙组", "分时"),
        _source("S3", "交易所", "交易所公开信息"),
        _source("S4", "丙组", "复核数据"),
    ]
    evidence = [
        _evidence("E1", "S1", code, "涨停池", True),
        _evidence("E2", "S2", code, "涨停池", True),
        _evidence("E3", "S1", code, "主概念", "合成概念"),
        _evidence("E4", "S4", code, "主概念", "合成概念"),
        _evidence("E5", "S1", code, "封板时间", "10:00:00"),
        _evidence("E6", "S2", code, "封板时间", "10:00:00"),
        _evidence("E7", "S1", code, "性质", "先锋龙头"),
        _evidence("E8", "S4", code, "性质", "先锋龙头"),
        _evidence("E9", "S3", code, "龙虎榜净买入额", 120000000),
        _evidence("E10", "S4", code, "龙虎榜净买入额", 120000000),
    ]
    stock = {
        "stock_code": code,
        "stock_name": "合成样本甲",
        "exchange": "合成交易所",
        "close_price": 10.0,
        "limit_up_price": 10.0,
        "close_at_limit": True,
        "primary_concept": "合成概念",
        "secondary_concepts": [],
        "first_limit_time": "10:00:00",
        "final_limit_time": "10:05:00",
        "break_count": 1,
        "consecutive_limit_days": 2,
        "recent_limit_days": 2,
        "turnover_rate": 12.0,
        "traded_amount": 800000000,
        "float_market_cap": 5000000000,
        "field_evidence": {"pool": ["E1", "E2"], "concept": ["E3", "E4"], "times": ["E5", "E6"]},
        "leader_roles": [{"name": "先锋龙头", "reason": "先封板并有合成跟随证据。", "evidence_ids": ["E7", "E8"]}],
        "lhb": {
            "is_listed": True,
            "buy_amount": 300000000,
            "sell_amount": 180000000,
            "net_amount": 120000000,
            "evidence_ids": ["E9", "E10"],
        },
    }
    return {
        "workflow_name": "每日涨停板龙头分类",
        "schema_version": "1.0",
        "trade_date": "2099-01-05",
        "latest_completed_trade_date": "2099-01-05",
        "generated_at": "2099-01-05T19:10:00+08:00",
        "data_cutoff": "2099-01-05T19:00:00+08:00",
        "sources": sources,
        "evidence": evidence,
        "stocks": [stock],
        "concept_summary": [
            {
                "concept": "合成概念",
                "verified_limit_up_count": 1,
                "nature_top": [{"rank": 1, "stock_code": code, "nature_names": ["先锋龙头"], "reason": "合成性质理由。", "evidence_ids": ["E7", "E8"]}],
                "position_top": [{"rank": 1, "stock_code": code, "reason": "合成地位理由。", "evidence_ids": ["E7", "E8"]}],
            }
        ],
        "morning_limit_ups": [{"stock_code": code}],
        "lhb_net_buy_ge_100m": [{"stock_code": code}],
        "report_claims": [{"claim_id": "C1", "text": "合成样本在合成概念中最早封板。", "evidence_ids": ["E5", "E6"]}],
        "unresolved_critical_conflicts": [],
    }


def command_selftest(_: argparse.Namespace) -> int:
    checks: list[dict] = []
    try:
        result = audit_payload(synthetic_fixture())
        checks.append({"name": "合成有效样本", "status": result.get("status")})
    except Exception as exc:
        checks.append({"name": "合成有效样本", "status": "FAIL", "error": str(exc)})

    invalid = synthetic_fixture()
    invalid["stocks"][0]["primary_concept"] = "其他"
    try:
        audit_payload(invalid)
        checks.append({"name": "含糊概念拦截", "status": "FAIL", "error": "未拦截"})
    except PayloadAuditError:
        checks.append({"name": "含糊概念拦截", "status": "PASS"})

    invalid = synthetic_fixture()
    invalid["lhb_net_buy_ge_100m"] = []
    try:
        audit_payload(invalid)
        checks.append({"name": "龙虎榜漏项拦截", "status": "FAIL", "error": "未拦截"})
    except PayloadAuditError:
        checks.append({"name": "龙虎榜漏项拦截", "status": "PASS"})

    invalid = synthetic_fixture()
    invalid["morning_limit_ups"] = []
    try:
        audit_payload(invalid)
        checks.append({"name": "上午名单漏项拦截", "status": "FAIL", "error": "未拦截"})
    except PayloadAuditError:
        checks.append({"name": "上午名单漏项拦截", "status": "PASS"})

    invalid = synthetic_fixture()
    invalid["sources"][1]["provider_group"] = "甲组"
    try:
        audit_payload(invalid)
        checks.append({"name": "同源伪交叉验证拦截", "status": "FAIL", "error": "未拦截"})
    except PayloadAuditError:
        checks.append({"name": "同源伪交叉验证拦截", "status": "PASS"})

    invalid = synthetic_fixture()
    invalid["sources"][0]["trade_date"] = "2099-01-04"
    try:
        audit_payload(invalid)
        checks.append({"name": "旧交易日来源拦截", "status": "FAIL", "error": "未拦截"})
    except PayloadAuditError:
        checks.append({"name": "旧交易日来源拦截", "status": "PASS"})

    invalid = synthetic_fixture()
    invalid["report_claims"][0]["text"] = "该股有望后市可期。"
    try:
        audit_payload(invalid)
        checks.append({"name": "模板式结论拦截", "status": "FAIL", "error": "未拦截"})
    except PayloadAuditError:
        checks.append({"name": "模板式结论拦截", "status": "PASS"})

    valid_docx_paragraphs = ["结论：1只样本满足条件。依据：核验池共1只。反证：若样本数变为0只，该结论随数据改写。"]
    checks.append({"name": "结论同段结构", "status": audit_paragraphs(valid_docx_paragraphs)["status"]})
    invalid_docx_paragraphs = ["结论一", "1只样本满足条件。", "依据一", "核验池共1只。"]
    checks.append({
        "name": "分散结论结构拦截",
        "status": "PASS" if audit_paragraphs(invalid_docx_paragraphs)["status"] == "BLOCKED" else "FAIL",
    })

    manifest = read_manifest()
    state = manifest.get("status")
    live_allowed = manifest.get("live_run_allowed")
    state_ok = (state == "review_pending" and live_allowed is False) or (state == "approved" and live_allowed is True)
    checks.append({"name": "审批状态与实跑开关一致", "status": "PASS" if state_ok else "FAIL"})
    status = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    emit({"status": status, "checked_at": datetime.now(timezone.utc).isoformat(), "checks": checks})
    return 0 if status == "PASS" else 1


def command_validate(args: argparse.Namespace) -> int:
    try:
        result = load_and_audit(args.input)
    except (OSError, json.JSONDecodeError, PayloadAuditError) as exc:
        emit({"status": "BLOCKED", "error": str(exc)})
        return 2
    emit(result)
    return 0


def _latest_global_conclusion_gate() -> Path | None:
    root = Path.home() / ".codex" / "plugins" / "cache" / "personal" / "correction-lock-gate"
    candidates = list(root.glob("*/scripts/correction_gate_hook.py"))
    return max(candidates, key=lambda path: path.stat().st_mtime_ns) if candidates else None


def command_verify_docx(args: argparse.Namespace) -> int:
    path = Path(args.file).expanduser().resolve()
    try:
        business_audit = audit_docx(path)
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        emit({"status": "BLOCKED", "error": f"Word读取失败：{type(exc).__name__}"})
        return 2

    global_path = _latest_global_conclusion_gate()
    global_audit = None
    if global_path is not None:
        spec = importlib.util.spec_from_file_location("active_global_conclusion_gate", global_path)
        if spec is None or spec.loader is None:
            emit({"status": "BLOCKED", "error": "当前全局结论硬闸无法载入"})
            return 2
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        global_audit = module.audit_docx_conclusion_content(path)

    blocked = business_audit["status"] != "PASS"
    if global_audit is not None:
        blocked = blocked or bool(global_audit.get("blocks")) or int(global_audit.get("conclusion_count") or 0) < 1
    result = {
        "status": "BLOCKED" if blocked else "PASS",
        "business_audit": business_audit,
        "global_gate_path": str(global_path) if global_path else None,
        "global_audit": global_audit,
    }
    emit(result)
    return 2 if blocked else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="每日涨停板龙头分类审核入口")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("info").set_defaults(func=command_info)
    subparsers.add_parser("review").set_defaults(func=command_review)
    subparsers.add_parser("selftest").set_defaults(func=command_selftest)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--input", required=True)
    validate_parser.set_defaults(func=command_validate)
    docx_parser = subparsers.add_parser("verify-docx")
    docx_parser.add_argument("--file", required=True)
    docx_parser.set_defaults(func=command_verify_docx)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
