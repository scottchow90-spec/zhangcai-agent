from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import importlib.util
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from dynamic_hotspot_rank import stock_snapshot


TDX_ROOT = Path(r"C:\new_tdx_mock")
BLOCK_ROOT = TDX_ROOT / "T0002" / "blocknew"
TQ_PATH = TDX_ROOT / "PYPlugins" / "user" / "tqcenter.py"
FORMULA = "补涨龙头排序"
RD_ALIASES = ("RD01", "RD02", "RD03")
ROLE_BLOCKS = (("补涨龙1", "BZL1"), ("补涨龙2", "BZL2"), ("补涨龙3", "BZL3"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_codes(alias: str) -> list[str]:
    path = BLOCK_ROOT / f"{alias}.blk"
    return [
        code
        for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        if (code := raw.strip()) and len(code) == 7 and code[0] in "012" and code[1:].isdigit()
    ]


def stock_suffix(code7: str) -> str:
    market = "SH" if code7[0] == "1" else "BJ" if code7[0] == "2" else "SZ"
    return f"{code7[1:]}.{market}"


def last_float(series: object) -> float:
    if not isinstance(series, list) or not series:
        return 0.0
    try:
        return float(series[-1])
    except (TypeError, ValueError):
        return 0.0


def load_tq():
    spec = importlib.util.spec_from_file_location("tdx_role_sync_tq", TQ_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {TQ_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.tq.initialize(str(TQ_PATH))
    return module.tq


def run(rank_path: Path) -> dict[str, Any]:
    rank = json.loads(rank_path.read_text(encoding="utf-8"))
    trade_date = str(rank.get("trade_date") or "")
    end_date = datetime.strptime(trade_date, "%Y%m%d").date()
    start_time = (end_date - timedelta(days=240)).strftime("%Y%m%d")
    direction_codes = {alias: load_codes(alias) for alias in RD_ALIASES}
    selected_by_direction: dict[str, list[dict[str, Any]]] = {}
    candidate_pool_by_direction: dict[str, list[dict[str, Any]]] = {}
    errors: list[str] = []
    tq = load_tq()
    try:
        for alias, codes in direction_codes.items():
            scored: list[dict[str, Any]] = []
            for code7 in codes:
                stock_code = stock_suffix(code7)
                setup = tq.formula_set_data_info(
                    stock_code=stock_code,
                    stock_period="1d",
                    start_time=start_time,
                    end_time=trade_date,
                    dividend_type=1,
                )
                if isinstance(setup, dict) and str(setup.get("ErrorId")) != "0":
                    errors.append(f"{alias}:{stock_code}:setup:{setup}")
                    continue
                payload = tq.formula_zb(formula_name=FORMULA, formula_arg="", xsflag=6)
                values = payload.get("Value", {}) if isinstance(payload, dict) else {}
                gate = last_float(values.get("热点闸门"))
                excluded = last_float(values.get("剔除标记"))
                core_score = last_float(values.get("补涨总分"))
                sort_key = last_float(values.get("排序键"))
                if gate == 1.0 and excluded == 0.0 and sort_key > 0.0:
                    snapshot = stock_snapshot(code7) or {}
                    scored.append({
                        "code7": code7,
                        "stock_code": stock_code,
                        "score": round(sort_key, 6),
                        "core_score": round(core_score, 6),
                        "components": {
                            "热点强度": round(last_float(values.get("热点强度")), 6),
                            "直接映射": round(last_float(values.get("直接映射")), 6),
                            "梯队质量": round(last_float(values.get("梯队质量")), 6),
                            "资金承接": round(last_float(values.get("资金承接")), 6),
                            "相对位置": round(last_float(values.get("相对位置")), 6),
                            "风险执行": round(last_float(values.get("风险执行")), 6),
                        },
                        "market_snapshot": {
                            key: round(float(value), 8) if isinstance(value, float) else value
                            for key, value in snapshot.items()
                        },
                        "hotspot_gate": gate,
                        "excluded": excluded,
                    })
            scored.sort(key=lambda item: (-float(item["score"]), str(item["code7"])))
            candidate_pool_by_direction[alias] = scored[:10]
    finally:
        tq.close()

    used_codes: set[str] = set()
    for alias in RD_ALIASES:
        selected = [
            item for item in candidate_pool_by_direction.get(alias, [])
            if str(item["code7"]) not in used_codes
        ][:3]
        selected_by_direction[alias] = selected
        used_codes.update(str(item["code7"]) for item in selected)

    role_codes: dict[str, list[str]] = {alias: [] for _, alias in ROLE_BLOCKS}
    for selected in selected_by_direction.values():
        for index, item in enumerate(selected):
            role_codes[ROLE_BLOCKS[index][1]].append(str(item["code7"]))
    for alias in role_codes:
        role_codes[alias] = list(dict.fromkeys(role_codes[alias]))

    tq = load_tq()
    runtime: dict[str, dict[str, Any]] = {}
    try:
        existing = {str(row.get("Code")): row for row in tq.get_user_sector()}
        for role_name, alias in ROLE_BLOCKS:
            path = BLOCK_ROOT / f"{alias}.blk"
            path.write_bytes(("\r\n" + "\r\n".join(role_codes[alias])).encode("ascii"))
            if alias not in existing:
                tq.create_sector(block_code=alias, block_name=role_name)
            tq.clear_sector(block_code=alias)
            symbols = [stock_suffix(code7) for code7 in role_codes[alias]]
            if symbols:
                tq.send_user_block(block_code=alias, stocks=symbols, show=False)
            runtime_codes = list(tq.get_stock_list_in_sector(alias, block_type=1))
            runtime[alias] = {
                "runtime_count": len(runtime_codes),
                "runtime_match": len(runtime_codes) == len(role_codes[alias]),
                "path": str(path),
                "sha256": sha256(path),
                "size_bytes": path.stat().st_size,
            }
    finally:
        tq.close()

    active_directions = [alias for alias, codes in direction_codes.items() if codes]
    selections_complete = all(
        len(selected_by_direction.get(alias, [])) == 3
        for alias in active_directions
    )
    return {
        "status": "PASS" if not errors and all(item["runtime_match"] for item in runtime.values()) and selections_complete else "OBSERVE",
        "decision_status": "NO_SIGNAL" if not active_directions else "CANDIDATES_READY" if selections_complete else "CANDIDATES_INCOMPLETE",
        "trade_date": trade_date,
        "formula": FORMULA,
        "score_and_sort_formula_changed": False,
        "direction_codes": {alias: len(values) for alias, values in direction_codes.items()},
        "candidate_pool_by_direction": candidate_pool_by_direction,
        "selected_by_direction": selected_by_direction,
        "role_codes": role_codes,
        "runtime": runtime,
        "errors": errors,
    }
