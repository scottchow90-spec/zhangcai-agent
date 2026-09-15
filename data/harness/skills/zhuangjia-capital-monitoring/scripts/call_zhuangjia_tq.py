#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Execute the installed local TQ formula 庄家资金监控."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

FORMULA = "庄家资金监控"
REQUIRED_FIELDS = ("OUTPUT3", "OUTPUT4", "控盘程度", "控盘度")


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


def latest_fields(values: dict[str, Any]) -> dict[str, Any]:
    latest: dict[str, Any] = {}
    for key, value in values.items():
        if isinstance(value, list):
            latest[key] = value[-1] if value else None
        else:
            latest[key] = value
    return latest


def _display_value(value: Any) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "NA"


def build_subsystem_rows(payload: dict, is_index: bool = False) -> list[dict]:
    """Build the fixed four-row external table for all required outputs."""
    latest = (payload or {}).get("latest") or {}
    rows = []
    for number, field in enumerate(REQUIRED_FIELDS, start=1):
        value = latest.get(field)
        if field in {"OUTPUT3", "OUTPUT4"}:
            status = "输出有效" if value is not None else "状态不可判定"
            conclusion = (
                f"{field}绘图输出已取得"
                if value is not None
                else f"{field}绘图输出不可判定"
            )
            note = "适用；OUTPUT3与OUTPUT4为重复绘图输出，各保留固定行，不作为额外独立资金指标"
        else:
            try:
                number_value = float(value)
                status = "正值" if number_value > 0 else (
                    "负值" if number_value < 0 else "零值"
                )
            except (TypeError, ValueError):
                status = "状态不可判定"
            conclusion = f"{field}当前状态为{status}"
            note = "适用于指数与个股；仅按本机庄家资金监控公式输出解释"
        rows.append(
            {
                "公式": FORMULA,
                "序号": number,
                "子系统/输出": field,
                "当前值/证据": f"{field}={_display_value(value)}",
                "状态": status,
                "结论": conclusion,
                "适用性/备注": note,
            }
        )
    return rows


def execute(code: str, tdx_root: str, count: int, dividend_type: int) -> tuple[dict, int]:
    symbol = normalize_symbol(code)
    root = Path(tdx_root).resolve()
    user_dir = root / "PYPlugins" / "user"
    init_path = user_dir / "tdxdata_test.py"
    source_path = root / "T0002" / "gs_bak" / f"{FORMULA}.txt"
    base = {
        "skill": "zhuangjia-capital-monitoring",
        "formula": FORMULA,
        "symbol": symbol,
        "data_source": f"{root} TQ",
        "init_path": str(init_path),
        "formula_source": str(source_path),
        "parameters": {"N": 35, "M": 0, "N1": 3},
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    if not root.is_dir() or not init_path.is_file() or not source_path.is_file():
        missing = [
            str(path) for path in (root, init_path, source_path) if not path.exists()
        ]
        return {**base, "status": "BLOCKED", "errors": [
            f"missing_local_asset:{path}" for path in missing
        ]}, 2

    os.chdir(root)
    sys.path.insert(0, str(user_dir))
    sys.argv = ["tqcenter", "--run_tdx", "0"]
    tq = None
    try:
        from tqcenter import tq as tq_runtime

        tq = tq_runtime
        tq.initialize(str(init_path))
        setup = tq.formula_set_data_info(
            symbol, count=count, dividend_type=dividend_type
        )
        if not isinstance(setup, dict) or str(setup.get("ErrorId")) != "0":
            return {**base, "status": "BLOCKED", "step": "formula_set_data_info",
                    "setup": setup, "errors": ["formula_set_data_info_failed"]}, 2

        result = tq.formula_zb(FORMULA, symbol.split(".", 1)[0], xsflag=2)
        if not isinstance(result, dict) or str(result.get("ErrorId")) != "0":
            return {**base, "status": "BLOCKED", "step": "formula_zb",
                    "setup": {"ErrorId": setup.get("ErrorId")},
                    "formula_result": result, "errors": ["formula_zb_failed"]}, 2
        values = result.get("Value")
        if not isinstance(values, dict) or not values:
            return {**base, "status": "BLOCKED", "step": "formula_zb",
                    "errors": ["formula_value_empty"]}, 2
        missing_fields = [
            field for field in REQUIRED_FIELDS
            if field not in values or values[field] in (None, [], "")
        ]
        if missing_fields:
            return {**base, "status": "BLOCKED", "step": "field_validation",
                    "missing_fields": missing_fields,
                    "errors": ["required_formula_fields_missing"]}, 2
        return {
            **base,
            "status": "PASS",
            "setup": {"ErrorId": setup.get("ErrorId")},
            "formula_result": {"ErrorId": result.get("ErrorId")},
            "required_fields": list(REQUIRED_FIELDS),
            "available_fields": sorted(values),
            "latest": {
                key: latest_fields(values).get(key) for key in REQUIRED_FIELDS
            },
            "interpretation": {
                "OUTPUT3_OUTPUT4": "绘图重复输出，不作为额外独立资金指标",
            },
        }, 0
    except Exception as exc:
        return {**base, "status": "BLOCKED",
                "errors": [f"{type(exc).__name__}:{exc}"]}, 2
    finally:
        if tq is not None:
            try:
                tq.close()
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="本机庄家资金监控 TQ 调用器")
    parser.add_argument("--code", default="600000.SH")
    parser.add_argument("--tdx", default=r"C:\new_tdx_mock")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--div", type=int, default=0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload, returncode = execute(args.code, args.tdx, args.count, args.div)
    print(json.dumps(
        payload, ensure_ascii=False, indent=None if args.json else 2, default=str
    ))
    return returncode


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
