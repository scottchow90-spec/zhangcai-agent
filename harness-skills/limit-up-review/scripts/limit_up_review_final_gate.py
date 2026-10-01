#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final hard gate for strict limit-up review artifacts."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from limit_up_review_workflow_contract import (
    BUSINESS_RESULT_SCHEMA_VERSION,
    RECOMPUTED_METRICS,
    code6 as contract_code6,
    validate_business_result_payload,
)
from entry_limit_up_review import DEFAULT_DELIVERY_ROOT, evaluate_date_gate, path_is_within
from official_pool_date_reconciliation import is_cross_validated_official_pool_date

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEFAULT_SKILL_DIR = Path(__file__).resolve().parents[1]
DELISTING_HARD_EXCLUSION = "delisting_hard_exclusion"
VISIBLE_LATIN_GATE = "visible_latin_gate"
VISIBLE_FORBIDDEN = [
    "结论：",
    "依据：",
    "但要注意：",
    "上面判断就不成立",
    "冻结账本",
    "冻结预测账本",
    "本地上一交易日表",
    "从观察池提取代码",
    "只保留当日涨停池确认样本",
    "事实来源",
    "研究动作",
    "论点状态与证伪条件",
    "次日四分支情景树",
    "本版纠偏口径",
    "数据状态与数据来源",
    "口径纪律",
    "数据来源清单",
    "今日全部涨停股票穷举清单",
    "全量股票名单穷举",
    "正文固定17章",
    "TDX",
    "AK",
    "Codex",
    "工作流",
    "ZTC",
    "ELB",
    "未实采",
    "未纳入",
    "保留框架",
    "等待独立采集",
    "修复强度",
    "修复中带分歧",
    "盘面有修复",
    "主线板块",
    "主线板块龙1龙2龙3",
    "今日最强主线",
    "最强主线",
    "主线评分",
    "主线生命周期",
    "发酵",
    "主升",
    "高潮",
    "发酵偏分歧",
    "强度评分",
    "数量领先",
    "决定强度上限",
    "龙1",
    "龙2",
    "龙3",
    "龙头",
    "评级",
    "龙1带动",
    "看延续与降级",
    "偏强确认",
    "偏弱确认",
    "强势信号",
    "弱势信号",
    "情绪温度",
    "宽度约束分",
    "集中度分",
    "仅按排序分排列",
    "技术辅助只展示",
    "不参与股票池生成",
    "不输出买卖",
    "不作买卖依据",
    "只核验数据变化",
    "不预设方向",
    "只比对同一股票集合",
    "只记录样本数",
    "默认结论",
    "固定措辞",
    "兜底判断",
    "字段",
    "预测账本哈希",
    "内部启发式",
    "CLEAN_PASS",
    "SHA-256",
    "sha256",
    "验证通过",
    "自验证",
    "71只涨停股",
    "游资主要在个股和分散热点中做进攻",
    "机构买盘更多落在有基本面辨识度的医药、游戏等个股",
    "游资分散进攻，没有合力打一条主线",
    "机构在挑股票，不是整板块扫货",
]
UNCERTAINTY_FORBIDDEN = ["估计值", "大概", "可能是", "待确认", "未确认", "__"]
NON_ANALYTICAL_CONCLUSION = [
    "仅按",
    "只展示",
    "不参与",
    "不输出",
    "不作",
    "只核验",
    "不预设",
    "只比对",
    "只记录",
]


def now_iso() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def code6(value: Any) -> str:
    text = str(value or "").strip()
    match = re.search(r"(\d{6})", text)
    return match.group(1) if match else text.zfill(6)


def parse_verified_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"true", "1", "yes", "y"}


def read_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    root = ET.fromstring(xml.encode("utf-8"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", ns):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", ns)]
        if texts:
            paragraphs.append("".join(texts))
    return "\n".join(paragraphs)


def read_text_any(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    if path.suffix.lower() == ".docx":
        return read_docx_text(path)
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def validate_chapter_conclusions(text: str, label: str) -> list[str]:
    blocks: list[str] = []
    forbidden = [
        "结论：", "依据：", "但要注意：", "上面判断就不成立",
        "冻结账本", "冻结预测账本", "本地上一交易日表", "从观察池提取代码",
        "只保留当日涨停池确认样本", "事实来源", "研究动作", "论点状态与证伪条件",
        "次日四分支情景树", "工作流", "脚本", "接口", "字段",
    ]
    for chapter in range(17):
        pattern = re.compile(
            rf"(?ms)(?:^|\n)\s*(?:#{{1,4}}\s*)?{chapter}\.\s+[^\n]*\n(?P<body>.*?)(?=(?:^|\n)\s*(?:#{{1,4}}\s*)?(?:[0-9]|1[0-6])\.\s+|\Z)"
        )
        match = pattern.search(text)
        if not match:
            blocks.append(f"{label} missing chapter {chapter}")
            continue
        body = match.group("body")
        if chapter == 0:
            for marker in ("对象", "观察角度", "今日判断", "明日验证"):
                if marker not in body:
                    blocks.append(f"{label} chapter 0 missing classified conclusion matrix marker: {marker}")
            continue
        hits = [term for term in forbidden if term in body]
        if hits:
            blocks.append(f"{label} chapter {chapter} contains fixed/process text: {hits}")
        if not re.search(r"\d", body):
            blocks.append(f"{label} chapter {chapter} lacks current numeric facts")
        if not re.search(r"(上涨|下跌|涨停|连板|首板|开板|跌停|封板|资金|龙虎榜|热点|市场|留存|接力|风险)", body):
            blocks.append(f"{label} chapter {chapter} lacks market analysis")
    return blocks


def validate_section_analysis_visibility(text: str, payload: dict[str, Any], label: str) -> list[str]:
    blocks: list[str] = []
    sections = payload.get("section_analysis") if isinstance(payload.get("section_analysis"), list) else []
    for item in sections:
        if not isinstance(item, dict):
            continue
        chapter = item.get("chapter")
        heading = str(item.get("heading") or "")
        analysis = str(item.get("analysis") or "")
        facts = str(item.get("facts") or "")
        heading_pos = text.find(heading)
        analysis_pos = text.find(analysis, max(heading_pos, 0))
        facts_pos = text.find(facts, max(analysis_pos, 0))
        if min(heading_pos, analysis_pos, facts_pos) < 0:
            blocks.append(f"{label} chapter {chapter} structured analysis is not fully visible")
        elif not (heading_pos < analysis_pos < facts_pos):
            blocks.append(f"{label} chapter {chapter} structured analysis order mismatch")
    return blocks


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return rows, reader.fieldnames or []


def infer_date(report: Path | None, table: Path | None, task_dir: Path | None) -> str:
    for path in [report, table, task_dir]:
        if not path:
            continue
        text = path.name
        match = re.search(r"(20\d{2})[-_]?(\d{2})[-_]?(\d{2})", text)
        if match:
            return "".join(match.groups())
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d")


def validate_visible_report(label: str, path: Path | None) -> list[str]:
    if path is None:
        return [f"missing required {label} path"]
    if not path.exists() or path.stat().st_size == 0:
        return [f"missing_or_empty {label}: {path}"]
    text = read_text_any(path)
    blocks: list[str] = []
    latin_hits = sorted(set(re.findall(r"[A-Za-z]+", text)))
    if latin_hits:
        blocks.append(f"{label} {VISIBLE_LATIN_GATE}: {latin_hits}")
    hits = [term for term in VISIBLE_FORBIDDEN if term in text]
    if hits:
        blocks.append(f"{label} contains forbidden visible text: {hits}")
    if "所属行业" in text:
        blocks.append(f"{label} uses 所属行业 as a visible direction field")
    uncertainty_hits = [term for term in UNCERTAINTY_FORBIDDEN if term in text]
    if uncertainty_hits:
        blocks.append(f"{label} contains weak placeholders: {uncertainty_hits}")
    if "涨停结构与前五热点" not in text:
        blocks.append(f"{label} missing 涨停结构与前五热点")
    if re.search(r"(?:^|\n|\r)\s*(?:#{1,4}\s*)?17\.\s+", text):
        blocks.append(f"{label} still contains chapter 17")
    chapter_numbers = set(int(x) for x in re.findall(r"(?:^|\n|\r)\s*(?:#{1,4}\s*)?([0-9]|1[0-6])\.\s+", text))
    missing = [n for n in range(0, 17) if n not in chapter_numbers]
    if missing:
        blocks.append(f"{label} missing chapters: {missing}")
    blocks.extend(validate_chapter_conclusions(text, label))
    return blocks


def validate_visible_auxiliary(label: str, path: Path | None) -> list[str]:
    if path is None or not path.exists() or path.stat().st_size == 0:
        return [f"missing_or_empty {label}: {path}"]
    text = read_text_any(path)
    latin_hits = sorted(set(re.findall(r"[A-Za-z]+", text)))
    blocks = [f"{label} {VISIBLE_LATIN_GATE}: {latin_hits}"] if latin_hits else []
    if label == "watchlist" and "所属行业" in text:
        blocks.append("watchlist uses 所属行业 as a direction field")
    return blocks


def validate_table(table: Path | None, task_dir: Path | None, date: str) -> tuple[list[str], dict[str, Any]]:
    if table is None or not table.exists() or table.stat().st_size == 0:
        return [f"missing_or_empty table: {table}"], {}
    rows, fields = read_csv_rows(table)
    blocks: list[str] = []
    required = ["代码", "名称", "连板数", "投资板块", "题材归属", "题材证据", "所属行业"]
    missing = [col for col in required if col not in fields]
    if missing:
        blocks.append(f"table missing columns: {missing}")
    codes = [code6(row.get("代码", "")) for row in rows]
    if len(codes) != len(set(codes)):
        blocks.append("table contains duplicate stock codes")
    if not missing:
        for index, row in enumerate(rows, start=2):
            code = code6(row.get("代码", ""))
            values = {column: str(row.get(column, "") or "").strip() for column in required[3:]}
            empty = [column for column, value in values.items() if not value]
            if empty:
                blocks.append(f"table row {index}/{code} has empty direction fields: {empty}")
                continue
            investment_sector = values["投资板块"]
            if investment_sector == values["所属行业"]:
                blocks.append(f"table row {index}/{code} investment sector equals official industry")
            themes = {item.strip() for item in values["题材归属"].split("；") if item.strip()}
            if investment_sector not in themes:
                blocks.append(f"table row {index}/{code} investment sector absent from theme list")
            evidence = values["题材证据"]
            required_evidence = [
                f"东方财富核心题材：{investment_sector}",
                f"东方财富核心题材原始记录#{code}",
            ]
            evidence_missing = [item for item in required_evidence if item not in evidence]
            if evidence_missing:
                blocks.append(f"table row {index}/{code} theme evidence mismatch: {evidence_missing}")
    official_path = task_dir / f"ak_stock_zt_pool_em_{date}.csv" if task_dir else None
    official_rows: list[dict[str, str]] = []
    if official_path is None or not official_path.exists():
        blocks.append(f"missing official limit-up pool csv: {official_path}")
    else:
        official_rows, official_fields = read_csv_rows(official_path)
        if "代码" not in official_fields:
            blocks.append("official limit-up pool missing 代码 column")
        else:
            official_codes = {code6(row.get("代码", "")) for row in official_rows}
            table_codes = set(codes)
            audit_path = task_dir / "data_integrity_audit.json" if task_dir else None
            eligible_codes: set[str] = set()
            if audit_path is None or not audit_path.exists() or audit_path.stat().st_size == 0:
                blocks.append("missing data integrity audit for eligible official pool")
            else:
                try:
                    audit = json.loads(audit_path.read_text(encoding="utf-8-sig"))
                    eligible_codes = {code6(value) for value in (audit.get("eligible_official_codes") or [])}
                except Exception as exc:
                    blocks.append(f"eligible official pool audit unreadable: {type(exc).__name__}: {exc}")
            if not eligible_codes:
                blocks.append("eligible official pool is empty")
            if not eligible_codes.issubset(official_codes):
                blocks.append("eligible official pool contains code outside raw official pool")
            if table_codes != eligible_codes:
                extra = sorted(table_codes - eligible_codes)[:20]
                missing_codes = sorted(eligible_codes - table_codes)[:20]
                blocks.append(f"table code set mismatch eligible official pool: extra={extra}, missing={missing_codes}")
            if len(rows) != len(eligible_codes):
                blocks.append(f"table row count mismatch eligible official pool: table={len(rows)} eligible={len(eligible_codes)}")
    facts = {
        "table_rows": len(rows),
        "table_unique_codes": len(set(codes)),
        "official_rows": len(official_rows),
        "eligible_official_rows": len(set(codes)),
        "date": date,
    }
    return blocks, facts


def validate_fund_flow(fund_flow: Path | None, table: Path | None) -> list[str]:
    if fund_flow is None:
        return ["missing required fund_flow path"]
    if not fund_flow.exists() or fund_flow.stat().st_size == 0:
        return [f"missing_or_empty fund_flow: {fund_flow}"]
    rows, fields = read_csv_rows(fund_flow)
    required = ["代码", "名称", "ok", "source"]
    missing = [col for col in required if col not in fields]
    blocks = [f"fund_flow missing columns: {missing}"] if missing else []
    if "ok" in fields:
        invalid_ok = [str(row.get("ok")) for row in rows if str(row.get("ok") or "").strip().lower() not in {"true", "false", "1", "0", "yes", "no", "y", "n"}]
        if invalid_ok:
            blocks.append(f"fund_flow contains invalid ok values: {invalid_ok[:5]}")
    if table and table.exists() and "代码" in fields:
        table_rows, _ = read_csv_rows(table)
        table_codes = {code6(row.get("代码", "")) for row in table_rows}
        fund_codes = {code6(row.get("代码", "")) for row in rows}
        if fund_codes != table_codes:
            blocks.append("fund_flow code set mismatch table")
    return blocks


def validate_truth_snapshot(
    task_dir: Path | None,
    report: Path | None,
    docx: Path | None,
    table: Path | None,
    watchlist: Path | None,
    fund_flow: Path | None,
    analysis: Path | None,
    expected_run_id: str,
) -> list[str]:
    if task_dir is None:
        return ["missing required task_dir for final_evidence"]
    path = task_dir / "final_evidence.json"
    if not path.exists() or path.stat().st_size == 0:
        return [f"missing_or_empty final_evidence.json: {path}"]
    blocks: list[str] = []
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"cannot read final_evidence.json: {exc}"]
    if evidence.get("status") != "CLEAN_PASS":
        blocks.append("final_evidence status is not CLEAN_PASS")
    if evidence.get("run_id") != expected_run_id:
        blocks.append("final_evidence run_id mismatch")
    analysis_ref = evidence.get("analysis") if isinstance(evidence.get("analysis"), dict) else {}
    if analysis is None or str(analysis_ref.get("path") or "") != str(analysis):
        blocks.append("final_evidence analysis path mismatch")
    if analysis is None or not analysis.exists() or analysis_ref.get("sha256") != sha256(analysis):
        blocks.append("final_evidence analysis sha256 mismatch")
    if analysis_ref.get("run_id") != expected_run_id:
        blocks.append("final_evidence analysis run_id mismatch")
    snapshot = evidence.get("truth_snapshot") or {}
    if snapshot.get("run_id") != expected_run_id:
        blocks.append("truth_snapshot run_id mismatch")
    required_hashes = {
        "md": ("md_sha256", report),
        "docx": ("docx_sha256", docx),
        "csv": ("csv_sha256", table),
        "watchlist": ("watchlist_sha256", watchlist),
        "fund_flow": ("fund_flow_sha256", fund_flow),
        "analysis": ("analysis_sha256", analysis),
    }
    for label, (key, artifact) in required_hashes.items():
        if not snapshot.get(key):
            blocks.append(f"truth_snapshot missing required hash: {key}")
            continue
        if artifact is None or not artifact.exists() or sha256(artifact) != snapshot[key]:
            blocks.append(f"{label} sha256 mismatch vs truth_snapshot")
    date = infer_date(report, table, task_dir)
    extra_hashes = {
        "market_breadth_sha256": task_dir / f"market_breadth_{date}.json",
        "formula_sample_sha256": task_dir / f"tq_core_sample_{date}.json",
    }
    for key, artifact in extra_hashes.items():
        if not snapshot.get(key):
            blocks.append(f"truth_snapshot missing required hash: {key}")
        elif not artifact.exists() or sha256(artifact) != snapshot[key]:
            blocks.append(f"{key} mismatch vs artifact")
    return blocks


def validate_market_breadth_evidence(task_dir: Path | None, date: str) -> list[str]:
    if task_dir is None:
        return ["missing task_dir for market breadth evidence"]
    breadth_path = task_dir / f"market_breadth_{date}.json"
    if not breadth_path.exists() or breadth_path.stat().st_size == 0:
        return [f"missing_or_empty market_breadth evidence: {breadth_path}"]
    try:
        breadth = json.loads(breadth_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return [f"cannot read market_breadth evidence: {exc}"]
    blocks: list[str] = []
    if breadth.get("status") != "CLEAN_PASS":
        blocks.append("market_breadth status is not CLEAN_PASS")
    if breadth.get("source") == "tdx_local_day_files":
        if str(breadth.get("date")) != date:
            blocks.append(f"TDX market_breadth date mismatch: {breadth.get('date')} != {date}")
        try:
            scanned = int(breadth.get("scanned_day_files") or 0)
            covered = int(breadth.get("valid_change_rows") or 0)
            coverage = covered / scanned if scanned else 0.0
        except Exception:
            scanned, covered, coverage = 0, 0, 0.0
        if covered < 3000 or coverage < 0.85:
            blocks.append(f"TDX market_breadth coverage insufficient: covered={covered}, scanned={scanned}")
        if breadth.get("source_tier") != "primary_local_tdx_same_day":
            blocks.append(f"TDX market_breadth source tier invalid: {breadth.get('source_tier')}")
    required = ["up_count", "down_count", "flat_count", "source", "source_url"]
    missing = [key for key in required if breadth.get(key) in (None, "")]
    if missing:
        blocks.append(f"market_breadth missing fields: {missing}")
    try:
        up = int(breadth.get("up_count"))
        down = int(breadth.get("down_count"))
        flat = int(breadth.get("flat_count"))
        valid = up + down + flat
    except Exception:
        valid = 0
    if valid <= 0:
        blocks.append("market_breadth counts are invalid")
    return blocks


def validate_business_result_artifact(
    analysis: Path | None,
    table: Path | None,
    expected_date: str,
    expected_run_id: str,
) -> tuple[list[str], dict[str, Any]]:
    if analysis is None or not analysis.exists() or analysis.stat().st_size == 0:
        return [f"missing_or_empty business_result: {analysis}"], {}
    try:
        payload = json.loads(analysis.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return [f"cannot read business_result: {type(exc).__name__}: {exc}"], {}
    blocks = validate_business_result_payload(
        payload,
        expected_date=expected_date,
        expected_run_id=expected_run_id,
    )
    if payload.get("schema_version") != BUSINESS_RESULT_SCHEMA_VERSION:
        blocks.append("business_result schema_version mismatch")
    if payload.get("status") != "CLEAN_PASS" or payload.get("blocks_delivery") is not False:
        blocks.append("business_result is not delivery-clean")
    direction_outputs = {
        key: payload.get(key)
        for key in ("theses", "section_analysis", "scenario_tree", "watchlist")
    }
    if "所属行业" in json.dumps(direction_outputs, ensure_ascii=False, sort_keys=True):
        blocks.append("business_result uses 所属行业 in conclusion or watchlist outputs")
    if table is None or not table.exists():
        blocks.append("cannot recompute business_result without table")
        return blocks, {"payload": payload}
    rows, fields = read_csv_rows(table)
    if "代码" not in fields or "连板数" not in fields:
        blocks.append("table lacks 代码/连板数 for business invariant recomputation")
        return blocks, {"payload": payload}
    table_codes = [code6(row.get("代码")) for row in rows]
    universe = payload.get("official_universe") if isinstance(payload.get("official_universe"), dict) else {}
    analysis_codes = [code6(code) for code in universe.get("codes", [])] if isinstance(universe.get("codes"), list) else []
    if set(analysis_codes) != set(table_codes) or len(analysis_codes) != len(table_codes):
        blocks.append("business_result official_universe differs from final table")

    boards: list[int] = []
    for row in rows:
        try:
            boards.append(int(float(row.get("连板数") or 1)))
        except Exception:
            blocks.append(f"invalid 连板数 for {row.get('代码')}")
    recomputed = {
        "official_limit_up_count": len(rows),
        "first_board_count": sum(board == 1 for board in boards),
        "continuation_count": sum(board >= 2 for board in boards),
        "max_board": max(boards) if boards else 0,
    }
    metrics_raw = payload.get("metrics")
    metrics = metrics_raw if isinstance(metrics_raw, dict) else {
        str(item.get("id") or item.get("metric_id")): item
        for item in metrics_raw or []
        if isinstance(item, dict)
    }
    for metric_id in RECOMPUTED_METRICS:
        record = metrics.get(metric_id) if isinstance(metrics, dict) else None
        if not isinstance(record, dict):
            blocks.append(f"business_result missing metric: {metric_id}")
            continue
        try:
            actual = int(float(record.get("value")))
        except Exception:
            blocks.append(f"business_result metric is not numeric: {metric_id}")
            continue
        if actual != recomputed[metric_id]:
            blocks.append(f"business_result metric mismatch {metric_id}: {actual} != {recomputed[metric_id]}")
    row_by_code = {code6(row.get("代码")): row for row in rows}
    evidence_raw = payload.get("evidence_records")
    evidence_items = evidence_raw.values() if isinstance(evidence_raw, dict) else evidence_raw if isinstance(evidence_raw, list) else []
    for evidence in evidence_items:
        if not isinstance(evidence, dict) or str(evidence.get("kind") or "") != "row_field":
            continue
        code = code6(evidence.get("code"))
        field = str(evidence.get("field") or "")
        row = row_by_code.get(code)
        if row is None:
            blocks.append(f"row evidence code absent from final table: {code}")
            continue
        if field not in row:
            blocks.append(f"row evidence field absent from final table: {code}/{field}")
            continue
        expected_value = evidence.get("observed_value")
        actual_value = row.get(field)
        try:
            numeric_match = abs(float(expected_value) - float(actual_value)) < 1e-6
        except (TypeError, ValueError):
            numeric_match = str(expected_value).strip() == str(actual_value).strip()
        if not numeric_match:
            blocks.append(f"row evidence value mismatch: {code}/{field}")
    return blocks, {
        "run_id": ((payload.get("run") or {}).get("run_id") if isinstance(payload.get("run"), dict) else ""),
        "schema_version": payload.get("schema_version"),
        "analysis_sha256": sha256(analysis),
        "recomputed_metrics": recomputed,
        "thesis_count": len(payload.get("theses") or []),
        "scenario_count": len(payload.get("scenario_tree") or {}),
        "watchlist_count": len(payload.get("watchlist") or []),
    }


def self_test(skill_dir: Path = DEFAULT_SKILL_DIR) -> dict[str, Any]:
    required = [
        skill_dir / "SKILL.md",
        skill_dir / "TEMPLATE.md",
        skill_dir / "references" / "workflow.md",
        skill_dir / "references" / "business_spec.md",
        skill_dir / "scripts" / "codex_entry.py",
        skill_dir / "scripts" / "limit_up_review_workflow_contract.py",
        skill_dir / "scripts" / "entry_limit_up_review.py",
        skill_dir / "scripts" / "collect_limitup_data_strict.py",
        skill_dir / "scripts" / "fetch_push2_fund_flow_strict.py",
        skill_dir / "scripts" / "generate_limit_up_review_strict.py",
        skill_dir / "scripts" / "limit_up_review_final_gate.py",
    ]
    blocks = [f"missing_or_empty: {path}" for path in required if not path.exists() or path.stat().st_size == 0]
    if not validate_business_result_payload({}):
        blocks.append("empty business_result negative canary unexpectedly passed")
    return {
        "status": "CLEAN_PASS" if not blocks else "BLOCKED",
        "checked_at": now_iso(),
        "blocks": blocks,
        "skill_dir": str(skill_dir),
    }


def validate_entry_date_gate(task_dir: Path | None, date: str, expected_run_id: str, docx: Path | None = None) -> list[str]:
    if task_dir is None:
        return ["ENTRY_DATE_GATE_TASK_DIR_MISSING"]
    path = task_dir / "preflight_audit.json"
    if not path.exists() or path.stat().st_size == 0:
        return ["ENTRY_DATE_GATE_MISSING"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return [f"ENTRY_DATE_GATE_UNREADABLE:{type(exc).__name__}:{exc}"]
    gate = payload.get("date_gate") if isinstance(payload.get("date_gate"), dict) else {}
    blocks: list[str] = []
    if payload.get("status") != "CLEAN_PASS" or gate.get("status") != "CLEAN_PASS":
        blocks.append("ENTRY_DATE_GATE_NOT_CLEAN")
    if str(payload.get("run_id") or "") != expected_run_id:
        blocks.append("ENTRY_DATE_GATE_RUN_ID_MISMATCH")
    if str(payload.get("date") or "").replace("-", "") != date:
        blocks.append("ENTRY_DATE_GATE_AUDIT_DATE_MISMATCH")
    if str(gate.get("target_date") or "").replace("-", "") != date:
        blocks.append("ENTRY_DATE_GATE_TARGET_DATE_MISMATCH")
    mode = str(gate.get("mode") or "")
    if mode not in {"latest", "historical"}:
        blocks.append("ENTRY_DATE_GATE_MODE_INVALID")
    if gate.get("blocks"):
        blocks.append("ENTRY_DATE_GATE_HAS_BLOCKS")
    if mode == "historical" and docx is not None and path_is_within(docx, DEFAULT_DELIVERY_ROOT):
        blocks.append(f"HISTORICAL_MODE_DEFAULT_DELIVERY_ROOT_FORBIDDEN:{docx}")
    if mode == "latest":
        runtime_gate = evaluate_date_gate("", "latest")
        if runtime_gate.get("status") != "CLEAN_PASS":
            blocks.extend(f"RUNTIME_LATEST_DATE_GATE:{item}" for item in runtime_gate.get("blocks", []))
        if str(runtime_gate.get("target_date") or "").replace("-", "") != date:
            blocks.append("RUNTIME_LATEST_DATE_MISMATCH")
    return blocks


def validate_source_freshness(task_dir: Path | None, date: str, table: Path | None) -> list[str]:
    if task_dir is None:
        return ["DATA_INTEGRITY_TASK_DIR_MISSING"]
    audit_path = task_dir / "data_integrity_audit.json"
    if not audit_path.exists() or audit_path.stat().st_size == 0:
        return ["DATA_INTEGRITY_AUDIT_MISSING"]
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return [f"DATA_INTEGRITY_AUDIT_UNREADABLE:{type(exc).__name__}:{exc}"]
    blocks: list[str] = []
    if audit.get("status") != "CLEAN_PASS" or audit.get("blocks"):
        blocks.append("DATA_INTEGRITY_AUDIT_NOT_CLEAN")
    if str(audit.get("date") or "").replace("-", "") != date:
        blocks.append("DATA_INTEGRITY_AUDIT_DATE_MISMATCH")
    qdate = str(audit.get("official_source_qdate") or "")
    date_reconciliation = audit.get("official_source_date_reconciliation")
    if qdate != date and not is_cross_validated_official_pool_date(
        date_reconciliation,
        date,
    ):
        blocks.append(f"OFFICIAL_SOURCE_DATE_MISMATCH:{qdate}!={date}")
    source_codes = {contract_code6(value) for value in (audit.get("official_source_codes") or [])}
    if not source_codes:
        blocks.append("OFFICIAL_SOURCE_CODES_MISSING")
    try:
        source_count = int(audit.get("official_source_count") or 0)
    except (TypeError, ValueError):
        source_count = -1
        blocks.append("OFFICIAL_SOURCE_COUNT_INVALID")
    if source_count != len(source_codes):
        blocks.append("OFFICIAL_SOURCE_COUNT_MISMATCH")
    source_hash = hashlib.sha256("\n".join(sorted(source_codes)).encode("utf-8")).hexdigest()
    if str(audit.get("official_source_codes_sha256") or "") != source_hash:
        blocks.append("OFFICIAL_SOURCE_CODES_HASH_MISMATCH")
    eligible_codes = {contract_code6(value) for value in (audit.get("eligible_official_codes") or [])}
    exclusion_items = audit.get("hard_exclusions") if isinstance(audit.get("hard_exclusions"), list) else []
    exclusion_codes = {
        contract_code6(item.get("code"))
        for item in exclusion_items
        if isinstance(item, dict) and item.get("code")
    }
    if not eligible_codes:
        blocks.append("ELIGIBLE_OFFICIAL_CODES_MISSING")
    if not eligible_codes.issubset(source_codes):
        blocks.append("ELIGIBLE_OFFICIAL_CODES_OUTSIDE_RAW_SOURCE")
    if source_codes - eligible_codes != exclusion_codes:
        blocks.append("DELISTING_HARD_EXCLUSION_MISMATCH")
    try:
        eligible_count = int(audit.get("eligible_official_count") or 0)
    except (TypeError, ValueError):
        eligible_count = -1
        blocks.append("ELIGIBLE_OFFICIAL_COUNT_INVALID")
    if eligible_count != len(eligible_codes):
        blocks.append("ELIGIBLE_OFFICIAL_COUNT_MISMATCH")
    eligible_hash = hashlib.sha256("\n".join(sorted(eligible_codes)).encode("utf-8")).hexdigest()
    if str(audit.get("eligible_official_codes_sha256") or "") != eligible_hash:
        blocks.append("ELIGIBLE_OFFICIAL_CODES_HASH_MISMATCH")
    snapshot_raw = str(audit.get("official_source_snapshot") or "")
    snapshot_path = Path(snapshot_raw) if snapshot_raw else None
    if snapshot_path is None or not snapshot_path.exists() or not snapshot_path.is_file() or snapshot_path.stat().st_size == 0:
        blocks.append("OFFICIAL_SOURCE_SNAPSHOT_MISSING")
    else:
        try:
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
            snapshot_codes = {contract_code6(value) for value in (snapshot.get("source_codes") or [])}
            if (
                str(snapshot.get("qdate") or "") != date
                and not is_cross_validated_official_pool_date(snapshot, date)
            ):
                blocks.append("OFFICIAL_SOURCE_SNAPSHOT_DATE_MISMATCH")
            if snapshot_codes != source_codes:
                blocks.append("OFFICIAL_SOURCE_SNAPSHOT_UNIVERSE_MISMATCH")
        except Exception as exc:
            blocks.append(f"OFFICIAL_SOURCE_SNAPSHOT_UNREADABLE:{type(exc).__name__}:{exc}")
    if table is None or not table.exists() or table.stat().st_size == 0:
        blocks.append("VERIFIED_TABLE_MISSING_FOR_SOURCE_CHECK")
    else:
        try:
            rows, fields = read_csv_rows(table)
            table_codes = {contract_code6(row.get("代码", "")) for row in rows} if "代码" in fields else set()
            if table_codes != eligible_codes:
                blocks.append("OFFICIAL_UNIVERSE_MISMATCH")
        except Exception as exc:
            blocks.append(f"VERIFIED_TABLE_UNREADABLE_FOR_SOURCE_CHECK:{type(exc).__name__}:{exc}")
    return blocks


def validate_delisting_hard_exclusion(
    task_dir: Path | None,
    report: Path | None,
    docx: Path | None,
    table: Path | None,
    watchlist: Path | None,
) -> list[str]:
    if task_dir is None:
        return ["DELISTING_HARD_EXCLUSION_TASK_DIR_MISSING"]
    audit_path = task_dir / "data_integrity_audit.json"
    if not audit_path.exists() or audit_path.stat().st_size == 0:
        return ["DELISTING_HARD_EXCLUSION_AUDIT_MISSING"]
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return [f"DELISTING_HARD_EXCLUSION_AUDIT_UNREADABLE:{type(exc).__name__}:{exc}"]
    blocks: list[str] = []
    if audit.get("hard_exclusion_rule") != DELISTING_HARD_EXCLUSION:
        blocks.append("DELISTING_HARD_EXCLUSION_RULE_MISSING")
    items = audit.get("hard_exclusions") if isinstance(audit.get("hard_exclusions"), list) else []
    visible_paths = [("report_md", report), ("report_docx", docx), ("final_table", table), ("watchlist", watchlist)]
    for item in items:
        if not isinstance(item, dict):
            blocks.append("DELISTING_HARD_EXCLUSION_ITEM_INVALID")
            continue
        code = contract_code6(item.get("code"))
        name = str(item.get("name") or "").strip()
        for label, path in visible_paths:
            text = read_text_any(path)
            if (code and code in text) or (name and name in text):
                blocks.append(f"{label} contains excluded delisting stock: {code} {name}".strip())
    if table is not None and table.exists() and table.stat().st_size:
        rows, fields = read_csv_rows(table)
        if "名称" in fields:
            leaked = [f"{code6(row.get('代码'))} {row.get('名称')}" for row in rows if "退" in str(row.get("名称") or "")]
            if leaked:
                blocks.append(f"final_table contains delisting-name rows: {leaked}")
    return blocks


def validate(
    report: Path | None = None,
    table: Path | None = None,
    watchlist: Path | None = None,
    fund_flow: Path | None = None,
    docx: Path | None = None,
    task_dir: Path | None = None,
    analysis: Path | None = None,
    expected_run_id: str = "",
) -> dict[str, Any]:
    date = infer_date(report, table, task_dir)
    blocks: list[str] = []
    if not expected_run_id:
        blocks.append("missing required expected_run_id")
    if task_dir is None or not task_dir.exists() or not task_dir.is_dir():
        blocks.append(f"missing required task_dir: {task_dir}")
    blocks.extend(validate_entry_date_gate(task_dir, date, expected_run_id, docx))
    blocks.extend(validate_source_freshness(task_dir, date, table))
    blocks.extend(validate_visible_report("report_md", report))
    blocks.extend(validate_visible_report("report_docx", docx))
    blocks.extend(validate_visible_auxiliary("final_table", table))
    blocks.extend(validate_visible_auxiliary("watchlist", watchlist))
    blocks.extend(validate_delisting_hard_exclusion(task_dir, report, docx, table, watchlist))
    blocks.extend(validate_fund_flow(fund_flow, table))
    table_blocks, facts = validate_table(table, task_dir, date)
    blocks.extend(table_blocks)
    analysis_blocks, analysis_facts = validate_business_result_artifact(
        analysis,
        table,
        date,
        expected_run_id,
    )
    blocks.extend(analysis_blocks)
    if analysis is not None and analysis.exists() and analysis.stat().st_size:
        try:
            analysis_payload = json.loads(analysis.read_text(encoding="utf-8"))
            blocks.extend(validate_section_analysis_visibility(read_text_any(report), analysis_payload, "report_md"))
            blocks.extend(validate_section_analysis_visibility(read_text_any(docx), analysis_payload, "report_docx"))
        except Exception as exc:
            blocks.append(f"cannot validate visible section analysis: {type(exc).__name__}: {exc}")
    blocks.extend(validate_truth_snapshot(task_dir, report, docx, table, watchlist, fund_flow, analysis, expected_run_id))
    blocks.extend(validate_market_breadth_evidence(task_dir, date))
    if watchlist is None or not watchlist.exists() or watchlist.stat().st_size == 0:
        blocks.append(f"missing_or_empty watchlist: {watchlist}")
    result = {
        "status": "CLEAN_PASS" if not blocks else "BLOCKED",
        "checked_at": now_iso(),
        "run_id": expected_run_id,
        "schema_version": BUSINESS_RESULT_SCHEMA_VERSION,
        "report": str(report) if report else "",
        "docx": str(docx) if docx else "",
        "table": str(table) if table else "",
        "watchlist": str(watchlist) if watchlist else "",
        "fund_flow": str(fund_flow) if fund_flow else "",
        "analysis": str(analysis) if analysis else "",
        "task_dir": str(task_dir) if task_dir else "",
        "facts": facts,
        "analysis_facts": analysis_facts,
        "blocks": blocks,
    }
    if task_dir:
        try:
            result_path = task_dir / "final_gate_result.json"
            result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            readback = json.loads(result_path.read_text(encoding="utf-8"))
            if readback.get("status") != result["status"] or readback.get("run_id") != expected_run_id:
                blocks.append("final_gate_result readback mismatch")
                result["status"] = "BLOCKED"
                result["blocks"] = blocks
                result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            blocks.append(f"final_gate_result write/readback failed: {type(exc).__name__}: {exc}")
            result["status"] = "BLOCKED"
            result["blocks"] = blocks
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="")
    parser.add_argument("--table", default="")
    parser.add_argument("--watchlist", default="")
    parser.add_argument("--fund-flow", default="")
    parser.add_argument("--docx", default="")
    parser.add_argument("--task-dir", default="")
    parser.add_argument("--analysis", default="")
    parser.add_argument("--expected-run-id", default="")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        result = self_test()
    else:
        result = validate(
            report=Path(args.report) if args.report else None,
            table=Path(args.table) if args.table else None,
            watchlist=Path(args.watchlist) if args.watchlist else None,
            fund_flow=Path(args.fund_flow) if args.fund_flow else None,
            docx=Path(args.docx) if args.docx else None,
            task_dir=Path(args.task_dir) if args.task_dir else None,
            analysis=Path(args.analysis) if args.analysis else None,
            expected_run_id=args.expected_run_id,
        )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"])
        for block in result.get("blocks", []):
            print(f"BLOCKED: {block}")
    return 0 if result.get("status") == "CLEAN_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
