#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strict local technical analysis using all three installed TQ formula systems."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


FORMULA_NAMES = ("大牛线撑压版", "飞龙在天", "庄家资金监控")
TABLE_COLUMNS = (
    "公式",
    "序号",
    "子系统/输出",
    "当前值/证据",
    "状态",
    "结论",
    "适用性/备注",
)
BIG_BULL_SUBSYSTEMS = (
    "主趋势线",
    "EMA均线分层",
    "K线颜色信号",
    "流通市值",
    "DX动量指标",
    "参与与离场信号",
    "控盘程度",
    "财神短线",
    "庄进/庄出",
    "妖股识别",
    "龙头参与区",
    "龙回头",
    "点火信号",
    "起爆/题材共振",
    "BOLL+多重均线",
    "核心黄金分割撑压",
)
FEILONG_SUBSYSTEMS = (
    "龙头战法",
    "趋势过滤/中长期均线强势条件",
    "四日实体重叠箱体/波段密码底层形态",
    "首板/唯一涨停确认",
    "波段密码打板",
    "量价模型/暴涨启动",
    "波段随机强弱-波",
    "波段随机强弱-段",
    "私募秘进",
    "主升启动共振",
)
ZHUANGJIA_SUBSYSTEMS = ("OUTPUT3", "OUTPUT4", "控盘程度", "控盘度")
EXPECTED_SUBSYSTEMS = tuple(
    ("大牛线撑压版", number, name)
    for number, name in enumerate(BIG_BULL_SUBSYSTEMS, start=1)
) + tuple(
    ("飞龙在天", number, name)
    for number, name in enumerate(FEILONG_SUBSYSTEMS, start=1)
) + tuple(
    ("庄家资金监控", number, name)
    for number, name in enumerate(ZHUANGJIA_SUBSYSTEMS, start=1)
)
EXPECTED_COUNTS = {"大牛线撑压版": 16, "飞龙在天": 10, "庄家资金监控": 4}
FORBIDDEN_FEILONG_RELATION_PATTERNS = (
    "波高于段",
    "波低于段",
    "波大于段",
    "波小于段",
    "波在段上方",
    "波在段下方",
    "波上穿段",
    "波下穿段",
    "波与段差值",
)


def normalize_symbol(value: str) -> str:
    raw = value.strip().upper()
    match = re.fullmatch(r"(\d{6})(?:\.(SH|SZ|BJ))?", raw)
    if not match:
        raise ValueError(f"invalid_stock_code:{value}")
    code, market = match.groups()
    if not market:
        market = "SH" if code.startswith(("5", "6", "9")) else (
            "BJ" if code.startswith(("4", "8")) else "SZ"
        )
    return f"{code}.{market}"


def is_index_symbol(symbol: str) -> bool:
    code, market = symbol.split(".", 1)
    return (
        symbol in {"000001.SH", "999999.SH"}
        or (market == "SH" and code.startswith("000"))
        or (market == "SZ" and code.startswith("399"))
    )


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot_load_module:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _skill_script(skill_name: str, script_name: str) -> Path:
    skills_root = Path(__file__).resolve().parents[2]
    return skills_root / skill_name / "scripts" / script_name


def validate_subsystem_table(rows: list[dict[str, Any]]) -> dict[str, int]:
    if len(rows) != len(EXPECTED_SUBSYSTEMS):
        raise ValueError(
            f"subsystem_count_mismatch:expected={len(EXPECTED_SUBSYSTEMS)} actual={len(rows)}"
        )
    actual_order = []
    identities = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"subsystem_row_not_object:index={index}")
        missing_columns = [column for column in TABLE_COLUMNS if column not in row]
        if missing_columns:
            raise ValueError(
                f"subsystem_columns_missing:index={index} columns={missing_columns}"
            )
        blank_columns = [
            column for column in TABLE_COLUMNS
            if row[column] is None or not str(row[column]).strip()
        ]
        if blank_columns:
            raise ValueError(
                f"subsystem_columns_blank:index={index} columns={blank_columns}"
            )
        identity = (str(row["公式"]), int(row["序号"]), str(row["子系统/输出"]))
        actual_order.append(identity)
        identities.append(identity)
    if tuple(actual_order) != EXPECTED_SUBSYSTEMS:
        raise ValueError("subsystem_order_or_identity_mismatch")
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate_subsystem_rows")
    counts = Counter(row["公式"] for row in rows)
    actual_counts = {name: counts.get(name, 0) for name in FORMULA_NAMES}
    if actual_counts != EXPECTED_COUNTS:
        raise ValueError(
            f"subsystem_group_count_mismatch:expected={EXPECTED_COUNTS} actual={actual_counts}"
        )
    feilong_cross_row = rows[23]
    if feilong_cross_row["状态"] not in {
        "金叉",
        "未形成金叉",
        "金叉状态不可判定",
    }:
        raise ValueError("invalid_feilong_golden_cross_state")
    rendered_text = json.dumps(rows, ensure_ascii=False, default=str)
    forbidden_hits = [
        pattern
        for pattern in FORBIDDEN_FEILONG_RELATION_PATTERNS
        if pattern in rendered_text
    ]
    if forbidden_hits:
        raise ValueError(f"forbidden_feilong_relation_text:{forbidden_hits}")
    return actual_counts


def _escape_markdown(value: Any) -> str:
    return (
        str(value)
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("|", r"\|")
        .strip()
    )


def render_subsystem_table_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| 公式 | 序号 | 子系统/输出 | 当前值/证据 | 状态 | 结论 | 适用性/备注 |",
        "|---|---:|---|---|---|---|---|",
    ]
    for row in rows:
        cells = [_escape_markdown(row[column]) for column in TABLE_COLUMNS]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _run_big_bull(symbol: str, root: Path) -> tuple[list[dict], dict]:
    module = _load_module(
        "technical_analysis_big_bull_runtime",
        _skill_script("big-bull-analysis-scoring-system", "daniuxian_analysis.py"),
    )
    analyzer_class = module.DaniuxianAnalyzer
    analyzer_class.TDX_ROOT = str(root)
    analyzer_class.TQCENTER_PATH = str(root / "PYPlugins" / "user")
    analyzer_class.TQ_INIT_PATH = str(root / "PYPlugins" / "user" / "tdxdata_test.py")
    analyzer = analyzer_class(symbol)
    try:
        raw = analyzer.collect_all()
        data = analyzer.analyze_all(raw)
        rows = module.build_subsystem_rows(data)
        return rows, {
            "status": "PASS",
            "formula": analyzer_class.FORMULA_RUNTIME_NAME,
            "subsystem_count": len(rows),
            "is_index": bool(data.get("is_index")),
            "bar_date": data.get("trade_date"),
            "bar_source": data.get("bar_source"),
        }
    finally:
        analyzer.close()


def _run_feilong(symbol: str, root: Path, is_index: bool) -> tuple[list[dict], dict]:
    module = _load_module(
        "technical_analysis_feilong_runtime",
        _skill_script("feilong-strategy", "feilong_realtime_report.py"),
    )
    module.TDX_ROOT = root
    result = module.analyze(symbol, persist_artifacts=False)
    summary = result["summary"]
    rows = module.build_subsystem_rows(summary, is_index=is_index)
    date_context = summary.get("date_context") or {}
    return rows, {
        "status": "PASS",
        "formula": module.FORMULA_CALL_NAME,
        "subsystem_count": len(rows),
        "analysis_as_of_date": date_context.get("analysis_as_of_date"),
        "data_mode": date_context.get("mode"),
        "artifacts_persisted": False,
    }


def _run_zhuangjia(
    symbol: str,
    root: Path,
    is_index: bool,
) -> tuple[list[dict], dict]:
    module = _load_module(
        "technical_analysis_zhuangjia_runtime",
        _skill_script("zhuangjia-capital-monitoring", "call_zhuangjia_tq.py"),
    )
    payload, returncode = module.execute(symbol, str(root), 5, 0)
    if returncode != 0 or payload.get("status") != "PASS":
        raise RuntimeError(
            "zhuangjia_formula_failed:"
            + json.dumps(payload, ensure_ascii=False, default=str)
        )
    rows = module.build_subsystem_rows(payload, is_index=is_index)
    return rows, {
        "status": "PASS",
        "formula": module.FORMULA,
        "subsystem_count": len(rows),
        "parameters": payload.get("parameters"),
    }


def _blocked_payload(
    base: dict[str, Any],
    failed_formulas: list[str],
    errors: list[str],
    formula_results: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], int]:
    return {
        **base,
        "status": "BLOCKED",
        "analysis_complete": False,
        "failed_formulas": failed_formulas,
        "formula_results": formula_results or {},
        "errors": errors,
    }, 2


def execute(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    try:
        symbol = normalize_symbol(args.code)
    except Exception as exc:
        return {
            "skill": "technical-analysis",
            "status": "BLOCKED",
            "analysis_complete": False,
            "failed_formulas": list(FORMULA_NAMES),
            "errors": [f"{type(exc).__name__}:{exc}"],
        }, 2

    root = Path(args.tdx).resolve()
    init_path = root / "PYPlugins" / "user" / "tdxdata_test.py"
    base = {
        "skill": "technical-analysis",
        "symbol": symbol,
        "target_type": "指数" if is_index_symbol(symbol) else "个股",
        "data_source": f"{root} TQ",
        "init_path": str(init_path),
        "required_formulas": list(FORMULA_NAMES),
        "required_subsystem_counts": dict(EXPECTED_COUNTS),
        "required_total_subsystems": len(EXPECTED_SUBSYSTEMS),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }

    injected_failure = getattr(args, "test_fail_formula", None)
    if injected_failure:
        return _blocked_payload(
            base,
            [injected_failure],
            [f"injected_formula_failure:{injected_failure}"],
            {injected_failure: {"status": "BLOCKED"}},
        )

    missing_paths = [
        str(path)
        for path in (root, init_path)
        if not path.exists()
    ]
    if missing_paths:
        return _blocked_payload(
            base,
            list(FORMULA_NAMES),
            [f"missing_local_asset:{path}" for path in missing_paths],
        )

    all_rows: list[dict] = []
    formula_results: dict[str, Any] = {}
    runners = (
        ("大牛线撑压版", lambda: _run_big_bull(symbol, root)),
        (
            "飞龙在天",
            lambda: _run_feilong(symbol, root, is_index_symbol(symbol)),
        ),
        (
            "庄家资金监控",
            lambda: _run_zhuangjia(symbol, root, is_index_symbol(symbol)),
        ),
    )
    for formula_name, runner in runners:
        try:
            rows, result = runner()
            all_rows.extend(rows)
            formula_results[formula_name] = result
        except BaseException as exc:
            formula_results[formula_name] = {
                "status": "BLOCKED",
                "error": f"{type(exc).__name__}:{exc}",
            }
            return _blocked_payload(
                base,
                [formula_name],
                [f"mandatory_formula_execution_failed:{formula_name}:{type(exc).__name__}:{exc}"],
                formula_results,
            )

    try:
        counts = validate_subsystem_table(all_rows)
        table_markdown = render_subsystem_table_markdown(all_rows)
        if table_markdown.count("| 公式 | 序号 | 子系统/输出 |") != 1:
            raise ValueError("markdown_table_header_count_mismatch")
        if table_markdown.count("|---|---:|---|---|---|---|---|") != 1:
            raise ValueError("markdown_table_separator_count_mismatch")
    except Exception as exc:
        return _blocked_payload(
            base,
            list(FORMULA_NAMES),
            [f"subsystem_table_validation_failed:{type(exc).__name__}:{exc}"],
            formula_results,
        )

    return {
        **base,
        "status": "PASS",
        "analysis_complete": True,
        "failed_formulas": [],
        "formula_results": formula_results,
        "subsystem_counts": counts,
        "subsystem_table": all_rows,
        "subsystem_table_markdown": table_markdown,
    }, 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="本机三公式全子系统技术分析执行器"
    )
    parser.add_argument("--code", default="600000.SH")
    parser.add_argument("--tdx", default=r"C:\new_tdx_mock")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--test-fail-formula",
        choices=list(FORMULA_NAMES),
        help="仅用于验证任一必需公式失败时必须阻断",
    )
    args = parser.parse_args()
    payload, returncode = execute(args)
    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=None if args.json else 2,
            default=str,
        )
    )
    return returncode


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
