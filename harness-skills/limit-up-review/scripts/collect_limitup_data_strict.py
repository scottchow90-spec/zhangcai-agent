#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strict limit-up data collector.

Data red line:
- The visible report's stock universe is the official same-day limit-up pool.
- Local custom blocks may only annotate/cross-check existing rows.
- If the official pool is missing or empty, block instead of fabricating.
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import hashlib
import os
import re
import struct
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import akshare as ak
import pandas as pd
import requests

from entry_limit_up_review import evaluate_date_gate

_app_scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_data_root, resolve_tdx_root

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DATA_ROOT = resolve_data_root()
TASK_DIR = Path(os.environ.get("LIMITUP_TASK_DIR", DATA_ROOT / "reports" / "limit_up_review")).expanduser().resolve()
TASK_DIR.mkdir(parents=True, exist_ok=True)
DATE = os.environ.get("LIMITUP_DATE", datetime.now().strftime("%Y%m%d"))
DATE_H = os.environ.get("LIMITUP_DATE_H", f"{DATE[:4]}-{DATE[4:6]}-{DATE[6:]}")
RUN_ID = os.environ.get("LIMITUP_RUN_ID", "")
TDX_ROOT = resolve_tdx_root()
TDX_BLOCK_DIR = TDX_ROOT / "T0002" / "blocknew"
TDX_VIPDOC = TDX_ROOT / "vipdoc"
DAY_RECORD = struct.Struct("<IIIIIfII")
OFFICIAL_POOL_URL = "https://push2ex.eastmoney.com/getTopicZTPool"
CORE_CONCEPTION_URL = "https://emweb.securities.eastmoney.com/PC_HSF10/CoreConception/PageAjax"
DELISTING_HARD_EXCLUSION = "delisting_hard_exclusion"
MIN_INDEPENDENT_POOL_OVERLAP = 0.95

# 这里只排除地域、交易状态、指数成分和资本运作标签，不预设任何投资板块名单。
NON_INVESTMENT_TOPIC_PATTERNS = (
    r"板块$", r"昨日", r"近期", r"最近", r"热股", r"题材股", r"反转股", r"破.*价",
    r"融资", r"融券", r"转融", r"股权转让", r"高送转", r"增持", r"回购", r"减持",
    r"重仓", r"持股", r"沪股通", r"深股通", r"陆股通", r"标普", r"富时", r"MSCI",
    r"可转债", r"破净", r"低价股", r"微盘股", r"同花顺", r"东方财富", r"央企改革",
    r"国企改革", r"参股", r"摘帽", r"ST", r"退市", r"次新股", r"新股",
)


def code6(value: Any) -> str:
    text = str(value or "").strip()
    match = re.search(r"(\d{6})", text)
    return match.group(1) if match else text.zfill(6)


def is_delisting_name(value: Any) -> bool:
    """Keep raw official evidence, but never promote delisting shares to delivery."""
    return "退" in str(value or "").strip()


def market_for(code: str) -> str:
    code = code6(code)
    if code.startswith(("43", "83", "87", "88", "92")):
        return "北交所"
    if code.startswith(("0", "1", "2", "3")):
        return "深市"
    return "沪市"


def codes_sha256(codes: set[str]) -> str:
    return hashlib.sha256("\n".join(sorted(codes)).encode("utf-8")).hexdigest()


def load_lianban_snapshot() -> dict[str, Any]:
    path_value = os.environ.get("CODEX_LIANBAN_SNAPSHOT", "").strip()
    if not path_value:
        return {}
    path = Path(path_value)
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def tdx_block_snapshot_date(filename: str) -> str:
    path = TDX_BLOCK_DIR / filename
    if not path.is_file():
        return ""
    probes = (
        TDX_VIPDOC / "sh" / "lday" / "sh000001.day",
        TDX_VIPDOC / "sz" / "lday" / "sz399001.day",
        TDX_VIPDOC / "sz" / "lday" / "sz399006.day",
        TDX_VIPDOC / "sz" / "lday" / "sz000001.day",
        TDX_VIPDOC / "sh" / "lday" / "sh600000.day",
        TDX_VIPDOC / "sz" / "lday" / "sz300750.day",
    )
    observed_dates: list[int] = []
    for probe in probes:
        try:
            if probe.is_file() and probe.stat().st_size >= DAY_RECORD.size:
                with probe.open("rb") as handle:
                    handle.seek(-DAY_RECORD.size, os.SEEK_END)
                    date_i, *_rest = DAY_RECORD.unpack(handle.read(DAY_RECORD.size))
                if 19900101 <= int(date_i) <= 20991231:
                    observed_dates.append(int(date_i))
        except (OSError, ValueError, struct.error):
            continue
    if observed_dates:
        date_i, _count = max(
            Counter(observed_dates).items(), key=lambda item: (item[1], item[0])
        )
        return str(date_i)
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y%m%d")


def reconcile_official_pool_date_metadata(
    snapshot: dict[str, Any],
    *,
    akshare_codes: set[str],
    tdx_codes: set[str],
    tdx_snapshot_date: str,
    lianban_snapshot: dict[str, Any],
) -> dict[str, Any]:
    result = dict(snapshot)
    result["blocks"] = list(snapshot.get("blocks") or [])
    result["warnings"] = list(snapshot.get("warnings") or [])
    request_date = str(snapshot.get("request_date") or "").replace("-", "")
    qdate = str(snapshot.get("qdate") or "").replace("-", "")
    source_codes = {code6(value) for value in snapshot.get("source_codes") or []}

    if request_date and qdate == request_date:
        result["date_metadata_status"] = "VERIFIED"
        return result

    lianban_date = str(lianban_snapshot.get("target_date") or "").replace("-", "")
    lianban_codes = {
        code6(item.get("code"))
        for item in (lianban_snapshot.get("page_details") or {}).get("stock_items") or []
        if isinstance(item, dict) and int(item.get("board_count") or 0) > 0
    }
    denominator = max(len(akshare_codes), 1)
    tdx_overlap_ratio = len(akshare_codes & tdx_codes) / denominator
    lianban_overlap_ratio = len(akshare_codes & lianban_codes) / denominator
    akshare_exact = bool(akshare_codes) and source_codes == akshare_codes
    tdx_same_date = bool(request_date) and tdx_snapshot_date == request_date
    lianban_same_date = (
        lianban_snapshot.get("status") == "CLEAN_PASS"
        and bool(request_date)
        and lianban_date == request_date
    )
    lianban_count_matches = (
        int((lianban_snapshot.get("market") or {}).get("limit_up") or -1)
        == len(akshare_codes)
    )
    verified = (
        akshare_exact
        and tdx_same_date
        and tdx_overlap_ratio >= MIN_INDEPENDENT_POOL_OVERLAP
        and lianban_same_date
        and lianban_count_matches
        and lianban_overlap_ratio >= MIN_INDEPENDENT_POOL_OVERLAP
    )
    result["date_verification"] = {
        "requested_date": request_date,
        "reported_qdate": qdate,
        "akshare_exact_set_match": akshare_exact,
        "tdx_snapshot_date": tdx_snapshot_date,
        "tdx_same_date": tdx_same_date,
        "tdx_overlap_ratio": round(tdx_overlap_ratio, 6),
        "lianban_target_date": lianban_date,
        "lianban_same_date": lianban_same_date,
        "lianban_limit_up_count": (lianban_snapshot.get("market") or {}).get(
            "limit_up"
        ),
        "lianban_count_matches": lianban_count_matches,
        "lianban_overlap_ratio": round(lianban_overlap_ratio, 6),
        "minimum_independent_overlap": MIN_INDEPENDENT_POOL_OVERLAP,
    }
    mismatch = f"OFFICIAL_SOURCE_DATE_MISMATCH:{qdate}!={request_date}"
    if verified:
        result["blocks"] = [item for item in result["blocks"] if item != mismatch]
        result["warnings"].append(
            f"OFFICIAL_SOURCE_QDATE_METADATA_DRIFT:{qdate}!={request_date}"
        )
        result["date_metadata_status"] = "CROSS_VALIDATED_DEGRADED"
        result["status"] = "CLEAN_PASS" if not result["blocks"] else "BLOCKED"
    else:
        result["date_metadata_status"] = "BLOCKED"
        result["status"] = "BLOCKED"
    return result


def persist_official_source_snapshot(snapshot: dict[str, Any]) -> None:
    path_value = str(snapshot.get("snapshot_path") or "")
    if not path_value:
        raise ValueError("official source snapshot path is missing")
    payload = dict(snapshot)
    payload.pop("snapshot_path", None)
    Path(path_value).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def validate_bound_preflight() -> list[str]:
    path = TASK_DIR / "preflight_audit.json"
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
    if str(payload.get("run_id") or "") != RUN_ID:
        blocks.append("ENTRY_DATE_GATE_RUN_ID_MISMATCH")
    if str(payload.get("date") or "").replace("-", "") != DATE:
        blocks.append("ENTRY_DATE_GATE_AUDIT_DATE_MISMATCH")
    if str(gate.get("target_date") or "").replace("-", "") != DATE:
        blocks.append("ENTRY_DATE_GATE_TARGET_DATE_MISMATCH")
    mode = str(gate.get("mode") or "")
    if mode not in {"latest", "historical"}:
        blocks.append("ENTRY_DATE_GATE_MODE_INVALID")
    if gate.get("blocks"):
        blocks.append("ENTRY_DATE_GATE_HAS_BLOCKS")
    if mode == "latest":
        runtime_gate = evaluate_date_gate("", "latest")
        if runtime_gate.get("status") != "CLEAN_PASS":
            blocks.extend(f"RUNTIME_LATEST_DATE_GATE:{item}" for item in runtime_gate.get("blocks", []))
        if str(runtime_gate.get("target_date") or "").replace("-", "") != DATE:
            blocks.append("RUNTIME_LATEST_DATE_MISMATCH")
    return blocks


def fetch_official_source_snapshot() -> tuple[dict[str, Any], set[str]]:
    snapshot_path = TASK_DIR / f"official_pool_source_snapshot_{DATE}.json"
    try:
        response = requests.get(
            OFFICIAL_POOL_URL,
            params={
                "ut": "7eea3edcaed734bea9cbfc24409ed989",
                "dpt": "wz.ztzt",
                "Pageindex": "0",
                "pagesize": "10000",
                "sort": "fbt:asc",
                "date": DATE,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise ValueError("official source data is missing")
        pool = data.get("pool")
        if not isinstance(pool, list):
            raise ValueError("official source pool is missing")
        qdate = str(data.get("qdate") or "")
        codes = {code6(item.get("c")) for item in pool if isinstance(item, dict) and item.get("c")}
        blocks: list[str] = []
        if qdate != DATE:
            blocks.append(f"OFFICIAL_SOURCE_DATE_MISMATCH:{qdate}!={DATE}")
        if not codes:
            blocks.append("OFFICIAL_SOURCE_POOL_EMPTY")
        if int(data.get("tc") or 0) != len(pool):
            blocks.append(f"OFFICIAL_SOURCE_COUNT_MISMATCH:tc={data.get('tc')} pool={len(pool)}")
        snapshot = {
            "status": "BLOCKED" if blocks else "CLEAN_PASS",
            "request_date": DATE,
            "qdate": qdate,
            "source_count": len(codes),
            "source_codes_sha256": codes_sha256(codes),
            "source_codes": sorted(codes),
            "endpoint": OFFICIAL_POOL_URL,
            "blocks": blocks,
        }
    except Exception as exc:
        codes = set()
        snapshot = {
            "status": "BLOCKED",
            "request_date": DATE,
            "qdate": "",
            "source_count": 0,
            "source_codes_sha256": codes_sha256(codes),
            "source_codes": [],
            "endpoint": OFFICIAL_POOL_URL,
            "blocks": [f"OFFICIAL_SOURCE_FETCH_FAILED:{type(exc).__name__}:{exc}"],
        }
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    snapshot["snapshot_path"] = str(snapshot_path)
    return snapshot, codes


def save_df(df: pd.DataFrame, stem: str) -> str:
    csv_path = TASK_DIR / f"{stem}.csv"
    json_path = TASK_DIR / f"{stem}.json"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    return str(csv_path)


def safe_fetch(label: str, fn, *args, **kwargs) -> tuple[dict[str, Any], pd.DataFrame]:
    try:
        df = fn(*args, **kwargs)
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"{label} did not return a DataFrame")
        save_df(df, f"{label}_{DATE}")
        return {"ok": True, "label": label, "rows": int(len(df)), "columns": list(df.columns)}, df
    except Exception as exc:
        return {
            "ok": False,
            "label": label,
            "error": f"{type(exc).__name__}: {str(exc)[:500]}",
        }, pd.DataFrame()


def read_block_codes(filename: str) -> set[str]:
    path = TDX_BLOCK_DIR / filename
    if not path.exists():
        return set()
    codes: set[str] = set()
    for line in path.read_text(encoding="gbk", errors="ignore").splitlines():
        match = re.search(r"(\d{6})$", line.strip())
        if match:
            codes.add(match.group(1))
    return codes


def require_columns(df: pd.DataFrame, required: list[str]) -> list[str]:
    return [col for col in required if col not in df.columns]


def eastmoney_secu_code(code: str) -> str:
    value = code6(code)
    if value.startswith(("8", "9")):
        return "BJ" + value
    return ("SZ" if value.startswith(("0", "1", "2", "3")) else "SH") + value


def valid_investment_topic(name: Any, rank: Any, precise: Any, industry: Any) -> bool:
    text = re.sub(r"\s+", "", str(name or "").strip())
    if not text or len(text) < 2 or len(text) > 24:
        return False
    # 东方财富返回的前三项为行业层级；投资板块只能来自其后的精确核心题材。
    try:
        if int(rank or 999) <= 3:
            return False
    except Exception:
        return False
    if str(precise or "").strip() != "1":
        return False
    if text == re.sub(r"\s+", "", str(industry or "").strip()):
        return False
    return not any(re.search(pattern, text, flags=re.I) for pattern in NON_INVESTMENT_TOPIC_PATTERNS)


def fetch_core_conceptions(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any], list[str]]:
    session = requests.Session()
    raw_records: list[dict[str, Any]] = []
    row_topics: dict[str, list[dict[str, Any]]] = {}
    blocks: list[str] = []
    for _, row in df.iterrows():
        code = code6(row.get("代码"))
        url_code = eastmoney_secu_code(code)
        try:
            response = session.get(CORE_CONCEPTION_URL, params={"code": url_code}, timeout=20)
            response.raise_for_status()
            payload = response.json()
            boards = payload.get("ssbk") if isinstance(payload, dict) else None
            core = payload.get("hxtc") if isinstance(payload, dict) else None
            if not isinstance(boards, list) or not boards:
                raise ValueError("ssbk is missing or empty")
            candidates: list[dict[str, Any]] = []
            for item in boards:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("BOARD_NAME") or "").strip()
                if valid_investment_topic(name, item.get("BOARD_RANK"), item.get("IS_PRECISE"), row.get("所属行业")):
                    candidates.append({
                        "name": name,
                        "rank": int(item.get("BOARD_RANK") or 999),
                        "precise": True,
                        "board_code": str(item.get("BOARD_CODE") or ""),
                    })
            candidates = list({item["name"]: item for item in candidates}.values())
            # Newly listed stocks can temporarily have no IS_PRECISE=1 concept.
            # Keep the report complete with Eastmoney's narrowest industry
            # subclass (rank 3), while recording the fallback explicitly.
            if not candidates:
                industry = re.sub(r"\s+", "", str(row.get("所属行业") or "").strip())
                for item in boards:
                    if not isinstance(item, dict):
                        continue
                    name = re.sub(r"\s+", "", str(item.get("BOARD_NAME") or "").strip())
                    try:
                        rank = int(item.get("BOARD_RANK") or 999)
                    except Exception:
                        continue
                    if (
                        rank == 3
                        and 2 <= len(name) <= 24
                        and name != industry
                        and not any(re.search(pattern, name, flags=re.I) for pattern in NON_INVESTMENT_TOPIC_PATTERNS)
                    ):
                        candidates.append({
                            "name": name,
                            "rank": rank,
                            "precise": False,
                            "source_type": "industry_subclass_fallback",
                            "board_code": str(item.get("BOARD_CODE") or ""),
                        })
                        break
            if not candidates:
                raise ValueError("no usable concept or industry subclass after exclusions")
            row_topics[code] = candidates
            raw_records.append({
                "code": code,
                "name": str(row.get("名称") or ""),
                "source_code": url_code,
                "source_url": response.url,
                "ssbk": boards,
                "hxtc": core if isinstance(core, list) else [],
                "accepted_topics": candidates,
            })
        except Exception as exc:
            blocks.append(f"CORE_CONCEPTION_FAILED:{code}:{type(exc).__name__}:{exc}")

    snapshot_path = TASK_DIR / f"eastmoney_core_conception_{DATE}.json"
    snapshot = {
        "status": "BLOCKED" if blocks else "CLEAN_PASS",
        "date": DATE,
        "source": CORE_CONCEPTION_URL,
        "requested_count": int(len(df)),
        "resolved_count": int(len(row_topics)),
        "records": raw_records,
        "blocks": blocks,
    }
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    if blocks:
        return df, snapshot | {"snapshot_path": str(snapshot_path)}, blocks

    topic_stats: dict[str, dict[str, Any]] = {}
    board_by_code = {code6(row.get("代码")): int(float(row.get("连板数") or 1)) for _, row in df.iterrows()}
    for code, topics in row_topics.items():
        board = board_by_code.get(code, 1)
        for item in topics:
            stat = topic_stats.setdefault(item["name"], {"support": 0, "connected": 0, "max_board": 1, "codes": []})
            stat["support"] += 1
            stat["connected"] += int(board >= 2)
            stat["max_board"] = max(int(stat["max_board"]), board)
            stat["codes"].append(code)
    shared_topics = {name for name, stat in topic_stats.items() if int(stat["support"]) >= 2}
    if not shared_topics:
        blocks.append("NO_SHARED_INVESTMENT_TOPIC")
        snapshot["status"] = "BLOCKED"
        snapshot["topic_stats"] = topic_stats
        snapshot["blocks"] = blocks
        snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        return df, snapshot | {"snapshot_path": str(snapshot_path)}, blocks

    selected: dict[str, str] = {}
    selected_fallback: dict[str, bool] = {}
    for code, topics in row_topics.items():
        ranked = sorted(
            topics,
            key=lambda item: (
                int(item["name"] in shared_topics),
                int(topic_stats[item["name"]]["connected"]),
                int(topic_stats[item["name"]]["support"]),
                int(topic_stats[item["name"]]["max_board"]),
                -int(item["rank"]),
            ),
            reverse=True,
        )
        selected[code] = ranked[0]["name"]
        selected_fallback[code] = not bool(ranked[0].get("precise"))
    result = df.copy()
    result["题材归属"] = result["代码"].map(lambda code: "；".join(item["name"] for item in row_topics[code6(code)]))
    result["投资板块"] = result["代码"].map(lambda code: selected[code6(code)])
    result["题材证据"] = result.apply(
        lambda row: (
            f"东方财富核心题材：{row['投资板块']}；"
            + ("归类口径：行业细分兜底；" if selected_fallback.get(code6(row["代码"])) else "")
            + f"原始证据：东方财富核心题材原始记录#{code6(row['代码'])}"
        ),
        axis=1,
    )
    if result["投资板块"].isna().any() or (result["投资板块"].astype(str).str.strip() == "").any():
        blocks.append("INVESTMENT_BOARD_EMPTY")
    if (result["投资板块"].astype(str).str.strip() == result["所属行业"].astype(str).str.strip()).any():
        blocks.append("INVESTMENT_BOARD_EQUALS_INDUSTRY")
    selected_counts = result["投资板块"].value_counts()
    if selected_counts.empty or int(selected_counts.max()) < 2:
        blocks.append("SELECTED_INVESTMENT_BOARDS_HAVE_NO_SHARED_STOCKS")
    for _, row in result.iterrows():
        if str(row["投资板块"]) not in str(row["题材归属"]).split("；"):
            blocks.append(f"INVESTMENT_BOARD_WITHOUT_TOPIC_EVIDENCE:{code6(row['代码'])}")
    snapshot["status"] = "BLOCKED" if blocks else "CLEAN_PASS"
    snapshot["topic_stats"] = topic_stats
    snapshot["selected_boards"] = selected
    snapshot["selected_fallback"] = selected_fallback
    snapshot["blocks"] = blocks
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return result, snapshot | {"snapshot_path": str(snapshot_path)}, blocks


def main() -> int:
    status: list[dict[str, Any]] = []

    preflight_blocks = validate_bound_preflight()
    if preflight_blocks:
        audit = {
            "status": "BLOCKED",
            "date": DATE,
            "date_h": DATE_H,
            "run_id": RUN_ID,
            "blocks": preflight_blocks,
        }
        (TASK_DIR / "data_integrity_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(audit, ensure_ascii=False, indent=2))
        return 2

    official_source, official_source_codes = fetch_official_source_snapshot()

    st, zt = safe_fetch("ak_stock_zt_pool_em", ak.stock_zt_pool_em, date=DATE)
    status.append(st)
    st, zbgc = safe_fetch("ak_stock_zt_pool_zbgc_em", ak.stock_zt_pool_zbgc_em, date=DATE)
    status.append(st)
    st, dtgc = safe_fetch("ak_stock_zt_pool_dtgc_em", ak.stock_zt_pool_dtgc_em, date=DATE)
    status.append(st)
    st, strong = safe_fetch("ak_stock_zt_pool_strong_em", ak.stock_zt_pool_strong_em, date=DATE)
    status.append(st)
    st, lhb_em = safe_fetch("ak_stock_lhb_detail_em", ak.stock_lhb_detail_em, start_date=DATE, end_date=DATE)
    status.append(st)
    st, lhb_sina = safe_fetch("ak_stock_lhb_detail_daily_sina", ak.stock_lhb_detail_daily_sina, date=DATE_H)
    status.append(st)

    blocks: list[str] = []
    if zt.empty:
        blocks.append("official limit-up pool is empty")
    missing = require_columns(zt, ["代码", "名称", "涨跌幅", "最新价", "连板数", "所属行业"])
    if missing:
        blocks.append(f"official limit-up pool missing columns: {missing}")
    akshare_codes = {code6(value) for value in zt["代码"].tolist()} if "代码" in zt.columns else set()
    ztc_codes = read_block_codes("ZTC.blk")
    official_source = reconcile_official_pool_date_metadata(
        official_source,
        akshare_codes=akshare_codes,
        tdx_codes=ztc_codes,
        tdx_snapshot_date=tdx_block_snapshot_date("ZTC.blk"),
        lianban_snapshot=load_lianban_snapshot(),
    )
    persist_official_source_snapshot(official_source)
    status.insert(0, {
        "ok": official_source.get("status") == "CLEAN_PASS",
        "label": "eastmoney_official_pool_source",
        "qdate": official_source.get("qdate"),
        "date_metadata_status": official_source.get("date_metadata_status"),
        "rows": official_source.get("source_count"),
        "snapshot_path": official_source.get("snapshot_path"),
    })
    blocks.extend(official_source.get("blocks") or [])
    if official_source_codes != akshare_codes:
        blocks.append(
            "OFFICIAL_UNIVERSE_MISMATCH:"
            f"source={len(official_source_codes)} akshare={len(akshare_codes)} "
            f"source_only={sorted(official_source_codes - akshare_codes)[:20]} "
            f"akshare_only={sorted(akshare_codes - official_source_codes)[:20]}"
        )

    if blocks:
        audit = {
            "status": "BLOCKED",
            "date": DATE,
            "date_h": DATE_H,
            "status_items": status,
            "official_source": official_source,
            "blocks": blocks,
        }
        (TASK_DIR / "data_integrity_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(audit, ensure_ascii=False, indent=2))
        return 2

    df = zt.copy()
    df["代码"] = df["代码"].map(code6)
    df = df.drop_duplicates(subset=["代码"], keep="first").reset_index(drop=True)
    raw_official_codes = set(df["代码"])
    delisting_mask = df["名称"].map(is_delisting_name)
    excluded_df = df[delisting_mask].copy()
    hard_exclusions = [
        {
            "code": code6(row.get("代码")),
            "name": str(row.get("名称") or "").strip(),
            "reason": "退市整理或退市标识",
            "rule": DELISTING_HARD_EXCLUSION,
        }
        for _, row in excluded_df.iterrows()
    ]
    df = df[~delisting_mask].copy().reset_index(drop=True)
    if df.empty:
        audit = {
            "status": "BLOCKED",
            "date": DATE,
            "date_h": DATE_H,
            "official_source_codes": sorted(raw_official_codes),
            "hard_exclusions": hard_exclusions,
            "blocks": ["ELIGIBLE_OFFICIAL_POOL_EMPTY_AFTER_DELISTING_EXCLUSION"],
        }
        (TASK_DIR / "data_integrity_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(audit, ensure_ascii=False, indent=2))
        return 2
    df.insert(0, "清单序号", range(1, len(df) + 1))
    df["市场"] = df["代码"].map(market_for)

    df, conception_snapshot, conception_blocks = fetch_core_conceptions(df)
    status.append({
        "ok": conception_snapshot.get("status") == "CLEAN_PASS",
        "label": "eastmoney_core_conception",
        "rows": conception_snapshot.get("resolved_count"),
        "snapshot_path": conception_snapshot.get("snapshot_path"),
    })
    if conception_blocks:
        audit = {
            "status": "BLOCKED",
            "date": DATE,
            "date_h": DATE_H,
            "status_items": status,
            "official_source": official_source,
            "core_conception": conception_snapshot,
            "blocks": conception_blocks,
        }
        (TASK_DIR / "data_integrity_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(audit, ensure_ascii=False, indent=2))
        return 2

    lb2_codes = read_block_codes("JDN_LB2.blk") or read_block_codes("ELB.blk")
    official_codes = set(df["代码"])
    df["本地涨停块命中"] = df["代码"].map(lambda c: "是" if c in ztc_codes else "否")
    df["本地连板块命中"] = df["代码"].map(lambda c: "是" if c in lb2_codes else "否")
    df["数据确认"] = "当日涨停池确认"

    ordered_cols = [
        "清单序号", "代码", "名称", "涨跌幅", "最新价", "成交额", "流通市值", "总市值", "换手率",
        "封板资金", "首次封板时间", "最后封板时间", "炸板次数", "涨停统计", "连板数", "投资板块",
        "题材归属", "题材证据", "所属行业",
        "市场", "本地涨停块命中", "本地连板块命中", "数据确认",
    ]
    cols = [c for c in ordered_cols if c in df.columns] + [c for c in df.columns if c not in ordered_cols]
    df = df[cols]
    verified_csv = save_df(df, f"verified_limitup_union_{DATE}")

    audit = {
        "status": "CLEAN_PASS",
        "date": DATE,
        "date_h": DATE_H,
        "official_limitup_count": int(len(df)),
        "official_unique_codes": int(len(official_codes)),
        "official_source_qdate": official_source.get("qdate"),
        "official_source_count": official_source.get("source_count"),
        "official_source_codes_sha256": official_source.get("source_codes_sha256"),
        "official_source_codes": official_source.get("source_codes"),
        "official_source_snapshot": official_source.get("snapshot_path"),
        "official_source_date_reconciliation": {
            "status": official_source.get("status"),
            "request_date": official_source.get("request_date"),
            "qdate": official_source.get("qdate"),
            "date_metadata_status": official_source.get("date_metadata_status"),
            "date_verification": official_source.get("date_verification"),
            "warnings": list(official_source.get("warnings") or []),
            "blocks": list(official_source.get("blocks") or []),
        },
        "eligible_official_count": int(len(official_codes)),
        "eligible_official_codes_sha256": codes_sha256(official_codes),
        "eligible_official_codes": sorted(official_codes),
        "hard_exclusion_rule": DELISTING_HARD_EXCLUSION,
        "hard_exclusions": hard_exclusions,
        "zbgc_count": int(len(zbgc)),
        "dtgc_count": int(len(dtgc)),
        "strong_count": int(len(strong)),
        "lhb_em_count": int(len(lhb_em)),
        "lhb_sina_count": int(len(lhb_sina)),
        "tdx_ztc_count": int(len(ztc_codes)),
        "tdx_ztc_intersection_count": int(len(official_codes & ztc_codes)),
        "tdx_ztc_excluded_count": int(len(ztc_codes - official_codes)),
        "local_lb2_count": int(len(lb2_codes)),
        "local_lb2_intersection_count": int(len(official_codes & lb2_codes)),
        "core_conception_snapshot": conception_snapshot.get("snapshot_path"),
        "core_conception_resolved_count": conception_snapshot.get("resolved_count"),
        "verified_csv": verified_csv,
        "status_items": status,
        "blocks": [],
    }
    (TASK_DIR / "data_integrity_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
