#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import json
import os
import re
import subprocess
import time
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

from logic_analysis import analyze_board


CHINA_TZ = timezone(timedelta(hours=8))
ALL_BOARDS = [
    "大消费",
    "医药生物",
    "大科技",
    "高端制造",
    "新能源",
    "基建公用",
    "金融地产",
    "周期资源",
]
DXX_CLIENT = Path(
    r"D:\C盘转移\日志\codex\skills\a-share-hotspot-sentiment-analysis\scripts\duanxianxia_client.ps1"
)
TDX_ZTC = Path(r"C:\new_tdx_mock\T0002\blocknew\ZTC.blk")
EASTMONEY_UT = "7eea3edcaed734bea9cbfc24409ed989"
CROSS_SOURCE_MAX_ATTEMPTS = 4
CROSS_SOURCE_RETRY_DELAY_SECONDS = 5.0


def now_china() -> datetime:
    return datetime.now(CHINA_TZ)


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def code6(value: object) -> str:
    match = re.search(r"(\d{6})", str(value or ""))
    return match.group(1) if match else str(value or "").zfill(6)


def stock_exclusion_reason(code: object, *names: object) -> str | None:
    normalized_code = code6(code)
    if normalized_code.startswith(("4", "8", "92")):
        return "北交所"

    for value in names:
        normalized_name = re.sub(r"\s+", "", str(value or "")).upper()
        if "退市" in normalized_name:
            return "退市"
        if normalized_name.startswith(("*ST", "ST", "S*ST", "SST")):
            return "ST"
    return None


def fmt_clock(value: object) -> str:
    digits = re.sub(r"\D", "", str(value or "")).zfill(6)[-6:]
    return f"{digits[:2]}:{digits[2:4]}:{digits[4:]}"


def money_yi(value: object) -> str:
    return f"{float(value or 0) / 100_000_000:.2f}亿元"


def fetch_json(
    url: str,
    params: dict[str, str] | None = None,
) -> tuple[dict[str, Any], bytes]:
    last_error: Exception | None = None
    raw = b""
    for attempt in range(1, 3):
        try:
            response = requests.get(url, params=params, timeout=25)
            response.raise_for_status()
            raw = response.content
            break
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(0.8)
    if not raw:
        raise RuntimeError(
            f"http_fetch_failed_after_retry:{type(last_error).__name__}:{last_error}:{url}"
        )
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"json_payload_invalid:{url}")
    return payload, raw


def write_raw(path: Path, raw: bytes) -> None:
    path.write_bytes(raw)


def split_items(value: str) -> list[str]:
    values = [clean_text(item) for item in re.split(r"[+、，,/；;]", clean_text(value))]
    return [item for item in values if item]


def board_for(industry: str, plate: str, concepts: str, reason: str) -> str:
    industry_plate = "|".join([industry, plate])
    concept_reason = "|".join([concepts, reason])
    medical_core = (
        r"医药|医疗|生物制品|化学制药|中药|医疗器械|医药商业|医疗服务|药品"
    )
    medical_theme = (
        r"CRO|CDMO|CXO|创新药|原料药|疫苗|基因检测|医美|药物|制药|"
        r"减肥药|ADC|药店|医药零售|医药流通"
    )
    if re.search(medical_core, industry_plate, re.I) or re.search(
        medical_theme,
        concept_reason,
        re.I,
    ):
        return "医药生物"

    text = "|".join([industry, plate, concepts, reason])
    rules = (
        ("金融地产", r"证券|银行|保险|多元金融|房地产|地产|物业|券商|信托"),
        ("新能源", r"光伏|风电|储能|新能源|电池|锂电|固态电池|氢能|核电|绿色电力|充电桩"),
        (
            "周期资源",
            r"黄金|白银|贵金属|稀土|有色|金属|矿|钢铁|煤炭|石油|天然气|化工|"
            r"化学制品|特钢|水泥|塑料|非金属|铜箔|锗|铟|铋|靶材|树脂|气体",
        ),
        (
            "基建公用",
            r"基础建设|建筑|装修|装饰|工程|建材|水务|环保|燃气|公用|电力|电网|"
            r"交通设施|园林|幕墙|民爆",
        ),
        (
            "大消费",
            r"食品|饮料|家电|家居|服装|母婴|零售|商业|保健品|宠物|消费|美容|"
            r"旅游|酒店|传媒|文化|游戏|农业",
        ),
        (
            "高端制造",
            r"机器人|自动化|通用设备|专用设备|汽车|机械|机床|工业|航空|航天|军工|"
            r"船舶|电机|仪器|装备|3D打印|材料设备",
        ),
        (
            "大科技",
            r"AI|人工智能|算力|芯片|半导体|通信|光模块|PCB|元件|电子|软件|计算机|"
            r"光学|光纤|卫星|6G|存储|数据中心|安全|先进封装|玻璃基板|折叠屏",
        ),
    )
    for board, pattern in rules:
        if re.search(pattern, text, re.I):
            return board
    return "高端制造"


def leading_boards(board_counts: Counter[str]) -> tuple[list[str], int]:
    if not board_counts:
        raise ValueError("board_counts_empty")
    top_count = max(board_counts.values())
    leaders = [
        board
        for board in ALL_BOARDS
        if board_counts.get(board, 0) == top_count
    ]
    return leaders, top_count


def collect_duanxianxia(run_dir: Path) -> tuple[dict[str, Any], Path]:
    if not DXX_CLIENT.is_file():
        raise RuntimeError(f"duanxianxia_client_missing:{DXX_CLIENT}")
    output = run_dir / "duanxianxia.json"
    script_literal = str(DXX_CLIENT).replace("'", "''")
    output_literal = str(output).replace("'", "''")
    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        (
            f"& '{script_literal}' "
            "-Dataset @('ztpool','ztplate','ztcount') "
            f"-Output '{output_literal}'"
        ),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    if completed.returncode != 0 or not output.is_file():
        raise RuntimeError(
            "duanxianxia_collection_failed:"
            f"rc={completed.returncode}:stderr={completed.stderr[-500:]}"
        )
    payload = json.loads(output.read_text(encoding="utf-8-sig"))
    for dataset in ("ztpool", "ztplate", "ztcount"):
        row = (payload.get("datasets") or {}).get(dataset) or {}
        if row.get("success") is not True:
            raise RuntimeError(f"duanxianxia_dataset_failed:{dataset}:{row.get('error')}")
    return payload, output


def collect_eastmoney_pool(trade_date: str, run_dir: Path) -> tuple[dict[str, Any], Path, str]:
    compact = trade_date.replace("-", "")
    params = {
        "ut": EASTMONEY_UT,
        "dpt": "wz.ztzt",
        "Pageindex": "0",
        "pagesize": "10000",
        "sort": "fbt:asc",
        "date": compact,
    }
    url = "https://push2ex.eastmoney.com/getTopicZTPool?" + urllib.parse.urlencode(params)
    shared_snapshot = os.environ.get("CODEX_LEADER_SHARED_POOL_SNAPSHOT", "").strip()
    if shared_snapshot:
        shared_path = Path(shared_snapshot).resolve()
        if not shared_path.is_file():
            raise RuntimeError(f"shared_eastmoney_pool_missing:{shared_path}")
        raw = shared_path.read_bytes()
        try:
            payload = json.loads(raw.decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"shared_eastmoney_pool_invalid:{exc}") from exc
        snapshot_date = str((payload.get("data") or {}).get("qdate") or "").replace("-", "")
        if snapshot_date != compact:
            raise RuntimeError(
                f"shared_eastmoney_pool_date_mismatch:{snapshot_date}!={compact}"
            )
    else:
        payload, raw = fetch_json(url)
    rows = ((payload.get("data") or {}).get("pool") or [])
    if not rows:
        raise RuntimeError("eastmoney_limit_up_pool_empty")
    output = run_dir / f"eastmoney_ztpool_{compact}.json"
    write_raw(output, raw)
    return payload, output, url


def normalized_limit_up_source_view(
    dxx: dict[str, Any],
    em: dict[str, Any],
) -> dict[str, Any]:
    dxx_rows = dxx["datasets"]["ztpool"]["data"]["list"]
    plate_rows = dxx["datasets"]["ztplate"]["data"]["list"]
    em_rows = em["data"]["pool"]
    dxx_map = {code6(row[0]): row for row in dxx_rows}
    plate_map = {code6(row["code"]): row for row in plate_rows}
    em_map = {code6(row["c"]): row for row in em_rows}
    excluded_stocks: list[dict[str, str]] = []
    all_codes = sorted(set(dxx_map) | set(em_map))
    for code in all_codes:
        dxx_row = dxx_map.get(code)
        em_row = em_map.get(code)
        dxx_name = dxx_row[1] if dxx_row else ""
        em_name = em_row.get("n") if em_row else ""
        reason = stock_exclusion_reason(code, dxx_name, em_name)
        if reason is None:
            continue
        excluded_stocks.append(
            {
                "stock_code": code,
                "stock_name": clean_text(em_name or dxx_name),
                "reason": reason,
            }
        )
        dxx_map.pop(code, None)
        em_map.pop(code, None)
        plate_map.pop(code, None)

    return {
        "dxx_map": dxx_map,
        "plate_map": plate_map,
        "em_map": em_map,
        "excluded_stocks": excluded_stocks,
    }


def limit_up_source_differences(view: dict[str, Any]) -> dict[str, list[str]]:
    dxx_codes = set(view["dxx_map"])
    em_codes = set(view["em_map"])
    plate_codes = set(view["plate_map"])
    return {
        "eastmoney_only": sorted(em_codes - dxx_codes),
        "duanxianxia_only": sorted(dxx_codes - em_codes),
        "plate_missing": sorted(em_codes - plate_codes),
    }


def collect_stable_limit_up_sources(
    trade_date: str,
    run_dir: Path,
    *,
    max_attempts: int = CROSS_SOURCE_MAX_ATTEMPTS,
    retry_delay_seconds: float = CROSS_SOURCE_RETRY_DELAY_SECONDS,
) -> dict[str, Any]:
    if max_attempts < 1:
        raise ValueError(f"max_attempts_invalid:{max_attempts}")
    if retry_delay_seconds < 0:
        raise ValueError(f"retry_delay_seconds_invalid:{retry_delay_seconds}")

    sync_dir = run_dir / "cross_source_sync"
    sync_dir.mkdir(parents=True, exist_ok=True)
    comparison_log = sync_dir / "comparisons.json"
    attempts: list[dict[str, Any]] = []
    last_result: dict[str, Any] | None = None

    for attempt in range(1, max_attempts + 1):
        attempt_started_at = now_china().isoformat()
        attempt_dir = sync_dir / f"attempt-{attempt:02d}"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        dxx, dxx_path = collect_duanxianxia(attempt_dir)
        em, em_path, em_url = collect_eastmoney_pool(trade_date, attempt_dir)
        view = normalized_limit_up_source_view(dxx, em)
        differences = limit_up_source_differences(view)
        matched = not any(differences.values())
        attempt_result = {
            "attempt": attempt,
            "started_at": attempt_started_at,
            "finished_at": now_china().isoformat(),
            "status": "MATCHED" if matched else "MISMATCH",
            "duanxianxia_fetched_at": clean_text(dxx.get("generated_at")),
            "duanxianxia_snapshot": str(dxx_path),
            "eastmoney_snapshot": str(em_path),
            "duanxianxia_count": len(view["dxx_map"]),
            "eastmoney_count": len(view["em_map"]),
            "plate_count": len(view["plate_map"]),
            **differences,
        }
        attempts.append(attempt_result)
        log_status = (
            "CLEAN_PASS"
            if matched
            else ("BLOCKED" if attempt == max_attempts else "RETRYING")
        )
        comparison_log.write_text(
            json.dumps(
                {
                    "schema": "LEADER_CROSS_SOURCE_SYNC_V1",
                    "status": log_status,
                    "trade_date": trade_date,
                    "max_attempts": max_attempts,
                    "retry_delay_seconds": retry_delay_seconds,
                    "attempts": attempts,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        last_result = {
            "status": log_status,
            "attempt_count": attempt,
            "attempts": attempts,
            "comparison_log": str(comparison_log),
            "duanxianxia": dxx,
            "duanxianxia_path": dxx_path,
            "eastmoney": em,
            "eastmoney_path": em_path,
            "eastmoney_url": em_url,
        }
        if matched:
            return last_result
        if attempt < max_attempts and retry_delay_seconds:
            time.sleep(retry_delay_seconds)

    assert last_result is not None
    final = attempts[-1]
    raise RuntimeError(
        "cross_source_limit_up_not_stable:"
        f"attempts={max_attempts}:"
        f"eastmoney_only={final['eastmoney_only']}:"
        f"duanxianxia_only={final['duanxianxia_only']}:"
        f"plate_missing={final['plate_missing']}:"
        f"comparison_log={comparison_log}"
    )


def collect_eastmoney_lhb(
    trade_date: str,
    run_dir: Path,
    *,
    allow_not_published: bool = False,
) -> tuple[dict[str, Any], Path, str]:
    columns = (
        "SECURITY_CODE,SECUCODE,SECURITY_NAME_ABBR,TRADE_DATE,EXPLAIN,CLOSE_PRICE,"
        "CHANGE_RATE,BILLBOARD_NET_AMT,BILLBOARD_BUY_AMT,BILLBOARD_SELL_AMT,"
        "BILLBOARD_DEAL_AMT,ACCUM_AMOUNT,DEAL_NET_RATIO,DEAL_AMOUNT_RATIO,"
        "TURNOVERRATE,FREE_MARKET_CAP,EXPLANATION,D1_CLOSE_ADJCHRATE,"
        "D2_CLOSE_ADJCHRATE,D5_CLOSE_ADJCHRATE,D10_CLOSE_ADJCHRATE,SECURITY_TYPE_CODE"
    )
    params = {
        "sortColumns": "SECURITY_CODE,TRADE_DATE",
        "sortTypes": "1,-1",
        "pageSize": "5000",
        "pageNumber": "1",
        "reportName": "RPT_DAILYBILLBOARD_DETAILSNEW",
        "columns": columns,
        "source": "WEB",
        "client": "WEB",
        "filter": f"(TRADE_DATE<='{trade_date}')(TRADE_DATE>='{trade_date}')",
    }
    base_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    payload, raw = fetch_json(base_url, params)
    if payload.get("success") is not True and allow_not_published:
        payload = {
            **payload,
            "success": True,
            "result": {"data": []},
            "_lhb_status": "not_published",
        }
    elif payload.get("success") is not True:
        raise RuntimeError(f"eastmoney_lhb_failed:{payload.get('message')}")
    output = run_dir / f"eastmoney_lhb_{trade_date.replace('-', '')}.json"
    write_raw(output, raw)
    locator = requests.Request("GET", base_url, params=params).prepare().url or base_url
    return payload, output, locator


def collect_lhb_details(
    trade_date: str,
    run_dir: Path,
    summary_rows: list[dict[str, Any]],
    pool_codes: set[str],
) -> tuple[list[dict[str, Any]], Path]:
    deduped: dict[str, dict[str, Any]] = {}
    for row in summary_rows:
        code = code6(row.get("SECURITY_CODE"))
        if code not in pool_codes:
            continue
        previous = deduped.get(code)
        if previous is None or float(row.get("BILLBOARD_DEAL_AMT") or 0) > float(
            previous.get("BILLBOARD_DEAL_AMT") or 0
        ):
            deduped[code] = row
    eligible = [
        row for row in deduped.values()
        if float(row.get("BILLBOARD_NET_AMT") or 0) >= 100_000_000
    ]
    eligible.sort(key=lambda row: float(row.get("BILLBOARD_NET_AMT") or 0), reverse=True)

    output: list[dict[str, Any]] = []
    raw_details: dict[str, Any] = {}
    for summary in eligible:
        code = code6(summary.get("SECURITY_CODE"))
        combined: dict[str, dict[str, Any]] = {}
        raw_details[code] = {}
        for report, sort_column in (
            ("RPT_BILLBOARD_DAILYDETAILSBUY", "BUY"),
            ("RPT_BILLBOARD_DAILYDETAILSSELL", "SELL"),
        ):
            params = {
                "sortColumns": sort_column,
                "sortTypes": "-1",
                "pageSize": "50",
                "pageNumber": "1",
                "reportName": report,
                "columns": "ALL",
                "filter": f"(TRADE_DATE='{trade_date}')(SECURITY_CODE=\"{code}\")",
            }
            url = "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(params)
            payload, _raw = fetch_json(url)
            rows = ((payload.get("result") or {}).get("data") or []) if payload.get("success") else []
            raw_details[code][report] = {"url": url, "rows": rows}
            for row in rows:
                name = clean_text(row.get("OPERATEDEPT_NAME"))
                if not name:
                    continue
                previous = combined.get(name)
                amount = float(row.get("BUY") or 0) + float(row.get("SELL") or 0)
                previous_amount = (
                    float(previous.get("BUY") or 0) + float(previous.get("SELL") or 0)
                    if previous else -1
                )
                if amount > previous_amount:
                    combined[name] = row
        seats = []
        for name, row in sorted(
            combined.items(),
            key=lambda item: abs(float(item[1].get("NET") or 0)),
            reverse=True,
        )[:10]:
            identity = (
                "深股通专用席位" if name == "深股通专用"
                else "机构专用席位" if "机构专用" in name
                else "营业部席位"
            )
            buy = float(row.get("BUY") or 0)
            sell = float(row.get("SELL") or 0)
            seats.append(
                {
                    "seat_name": name,
                    "seat_identity": identity,
                    "buy_amount": buy,
                    "sell_amount": sell,
                    "net_amount": buy - sell,
                }
            )
        if not seats:
            raise RuntimeError(f"lhb_seats_missing:{code}")
        output.append(
            {
                "stock_code": code,
                "stock_name": clean_text(summary.get("SECURITY_NAME_ABBR")),
                "buy_amount": float(summary.get("BILLBOARD_BUY_AMT") or 0),
                "sell_amount": float(summary.get("BILLBOARD_SELL_AMT") or 0),
                "net_amount": float(summary.get("BILLBOARD_NET_AMT") or 0),
                "reason": clean_text(summary.get("EXPLANATION")),
                "seats": seats,
            }
        )
    detail_path = run_dir / f"eastmoney_lhb_details_{trade_date.replace('-', '')}.json"
    detail_path.write_text(json.dumps(raw_details, ensure_ascii=False, indent=2), encoding="utf-8")
    return output, detail_path


def read_tdx_status(trade_date: str) -> dict[str, Any]:
    if not TDX_ZTC.is_file():
        return {"status": "DEGRADED", "detail": f"本地通达信涨停池不存在：{TDX_ZTC}"}
    modified = datetime.fromtimestamp(TDX_ZTC.stat().st_mtime, CHINA_TZ)
    current = modified.date().isoformat() == trade_date
    return {
        "status": "CURRENT" if current else "DEGRADED",
        "path": str(TDX_ZTC),
        "last_write": modified.isoformat(),
        "detail": (
            "本地通达信涨停池与研究日同日，可作本地旁证"
            if current
            else f"本地通达信涨停池更新时间为{modified.date().isoformat()}，早于研究日，仅记录降级状态"
        ),
    }


def load_lianban_context(trade_date: str, run_dir: Path) -> dict[str, Any]:
    candidates = []
    configured = clean_text(os.environ.get("CODEX_LIANBAN_SNAPSHOT"))
    if configured:
        candidates.append(Path(configured))
    candidates.append(run_dir.parent / "lianban-daily.json")
    for path in candidates:
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            payload.get("status") == "CLEAN_PASS"
            and payload.get("target_date") == trade_date
        ):
            return {
                "status": "CLEAN_PASS",
                "path": str(path),
                "requested_at": payload.get("requested_at"),
                "target_date": trade_date,
                "source_name": "连板网",
                "license": payload.get("license"),
                "source_url": ((payload.get("sources") or {}).get("page") or {}).get("url"),
                "open_data_url": (
                    (payload.get("sources") or {}).get("open_data") or {}
                ).get("url"),
                "market": payload.get("market") or {},
                "topics": payload.get("topics") or [],
                "sha256": sha256_path(path),
            }
    return {
        "status": "DEGRADED",
        "target_date": trade_date,
        "detail": "连板网当日补充快照不可用，未参与题材与情绪交叉验证。",
    }


def add_evidence(
    evidence: list[dict[str, Any]],
    evidence_id: str,
    source_id: str,
    stock_code: str,
    field: str,
    value: object,
    trade_date: str,
    captured_at: str,
    locator: str,
) -> str:
    evidence.append(
        {
            "evidence_id": evidence_id,
            "source_id": source_id,
            "stock_code": stock_code,
            "field": field,
            "value": value,
            "trade_date": trade_date,
            "captured_at": captured_at,
            "locator": locator,
        }
    )
    return evidence_id


def build_payload(
    trade_date: str,
    market_phase: str,
    run_dir: Path,
    dxx: dict[str, Any],
    dxx_path: Path,
    em: dict[str, Any],
    em_path: Path,
    em_url: str,
    lhb: dict[str, Any],
    lhb_path: Path,
    lhb_url: str,
    supplemental_context: dict[str, Any],
    source_sync: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fetched_at = now_china().isoformat()
    lhb_status = str(lhb.get("_lhb_status") or "published")
    dxx_fetched = clean_text(dxx.get("generated_at")) or fetched_at
    source_view = normalized_limit_up_source_view(dxx, em)
    differences = limit_up_source_differences(source_view)
    if any(differences.values()):
        raise RuntimeError(
            "limit_up_sources_inconsistent:"
            f"eastmoney_only={differences['eastmoney_only'][:20]}:"
            f"duanxianxia_only={differences['duanxianxia_only'][:20]}:"
            f"plate_missing={differences['plate_missing'][:20]}"
        )
    dxx_map = source_view["dxx_map"]
    plate_map = source_view["plate_map"]
    em_map = source_view["em_map"]
    excluded_stocks = source_view["excluded_stocks"]

    lhb_rows, lhb_detail_path = collect_lhb_details(
        trade_date,
        run_dir,
        (lhb.get("result") or {}).get("data") or [],
        set(em_map),
    )
    sources = [
        {
            "source_id": "EM-ZT",
            "source_name": "东方财富涨停池",
            "provider_group": "东方财富",
            "source_type": "当日涨停池与封板时间",
            "trade_date": trade_date,
            "fetched_at": fetched_at,
            "locator": em_url,
            "sha256": sha256_path(em_path),
        },
        {
            "source_id": "DXX-ZT",
            "source_name": "短线侠涨停池与板块",
            "provider_group": "短线侠",
            "source_type": "涨停池、板块和推动因素交叉验证",
            "trade_date": trade_date,
            "fetched_at": dxx_fetched,
            "locator": "https://duanxianxia.com/web/main",
            "sha256": sha256_path(dxx_path),
        },
        {
            "source_id": "EM-LHB",
            "source_name": "东方财富龙虎榜",
            "provider_group": "东方财富",
            "source_type": "龙虎榜公开数据汇总与席位明细",
            "trade_date": trade_date,
            "fetched_at": fetched_at,
            "locator": lhb_url,
            "sha256": sha256_path(lhb_detail_path),
        },
    ]
    if supplemental_context.get("status") == "CLEAN_PASS":
        sources.append(
            {
                "source_id": "LB-DAILY",
                "source_name": "连板网当日复盘",
                "provider_group": "连板网",
                "source_type": "市场情绪、题材结构与连板梯队补充交叉验证",
                "trade_date": trade_date,
                "fetched_at": supplemental_context["requested_at"],
                "locator": supplemental_context["source_url"],
                "sha256": supplemental_context["sha256"],
            }
        )

    evidence: list[dict[str, Any]] = []
    stocks: list[dict[str, Any]] = []
    evidence_pairs: dict[str, list[str]] = {}
    for index, code in enumerate(sorted(em_map), start=1):
        em_row = em_map[code]
        dx_row = dxx_map[code]
        plate_row = plate_map[code]
        industry = clean_text(em_row.get("hybk"))
        plate = clean_text(plate_row.get("plate"))
        concepts_text = clean_text(plate_row.get("concept"))
        reason = clean_text(dx_row[6])
        board = board_for(industry, plate, concepts_text, reason)
        em_id = f"E{index:03d}A"
        dx_id = f"E{index:03d}B"
        add_evidence(
            evidence,
            em_id,
            "EM-ZT",
            code,
            "涨停池、封板时间与行业",
            {
                "name": em_row.get("n"),
                "first_limit_time": em_row.get("fbt"),
                "latest_seal_time": em_row.get("lbt"),
                "industry": industry,
            },
            trade_date,
            fetched_at,
            f"eastmoney://ztpool/{trade_date}/{code}",
        )
        add_evidence(
            evidence,
            dx_id,
            "DXX-ZT",
            code,
            "涨停池、封板时间、细分方向与推动因素",
            {
                "name": dx_row[1],
                "first_limit_time": dx_row[12],
                "latest_seal_time": dx_row[5],
                "plate": plate,
                "concept": concepts_text,
                "reason": reason,
            },
            trade_date,
            dxx_fetched,
            f"duanxianxia://ztpool/{trade_date}/{code}",
        )
        evidence_pairs[code] = [em_id, dx_id]
        secondary = [item for item in split_items(concepts_text) if item != board]
        if not secondary:
            secondary = [industry or plate or "产业方向"]
        drivers = [item for item in split_items(reason) if item != board]
        if not drivers:
            drivers = ["当日涨停原因由两套当前数据确认"]
        consecutive = int(em_row.get("lbc") or 1)
        recent_days = int((em_row.get("zttj") or {}).get("days") or 1)
        recent_count = int((em_row.get("zttj") or {}).get("ct") or 1)
        stocks.append(
            {
                "stock_code": code,
                "stock_name": clean_text(em_row.get("n")),
                "exchange": "深市" if code.startswith(("0", "2", "3")) else "沪市",
                "primary_concept": board,
                "secondary_concepts": secondary[:4],
                "event_drivers": drivers[:5],
                "classification_basis": (
                    f"行业“{industry}”、板块“{plate}”、概念“{concepts_text}”及当日原因"
                    f"“{reason}”共同指向{board}的主要价值来源。"
                ),
                "limit_up_price": round(float(em_row.get("p") or 0) / 1000, 3),
                "at_limit_at_cutoff": True,
                "close_at_limit": market_phase not in {"active", "midday_pause", "preopen_with_current_data"},
                "first_limit_time": fmt_clock(em_row.get("fbt")),
                "latest_seal_time_at_cutoff": fmt_clock(em_row.get("lbt")),
                "final_limit_time": fmt_clock(em_row.get("lbt")),
                "open_count": int(em_row.get("zbc") or 0),
                "consecutive_limit_count": consecutive,
                "consecutive_limit_ups": consecutive,
                "recent_limit_days": recent_days,
                "recent_limit_count": recent_count,
                "recent_limit_up_hits": recent_count,
                "recent_limit_up_label": f"{recent_days}天{recent_count}板",
                "turnover_rate": float(em_row.get("hs") or 0),
                "amount": float(em_row.get("amount") or 0),
                "turnover_amount": float(em_row.get("amount") or 0),
                "free_market_cap": float(em_row.get("ltsz") or 0),
                "seal_fund": float(em_row.get("fund") or 0),
                "source_nature": clean_text(dx_row[10]),
                "field_evidence": {
                    "pool": [em_id, dx_id],
                    "concept": [em_id, dx_id],
                    "times": [em_id, dx_id],
                },
                "leader_roles": [],
            }
        )

    def rank_key(stock: dict[str, Any]) -> tuple[Any, ...]:
        return (
            -int(stock["consecutive_limit_count"]),
            -int(stock["recent_limit_count"]),
            stock["first_limit_time"],
            int(stock["open_count"]),
            -float(stock["amount"]),
            stock["stock_code"],
        )

    max_recent = max(stock["recent_limit_count"] for stock in stocks)
    max_recent_rows = [stock for stock in stocks if stock["recent_limit_count"] == max_recent]
    if len(max_recent_rows) == 1:
        leader = max_recent_rows[0]
        leader["leader_roles"].append(
            {
                "name": "市场总龙头",
                "reason": (
                    f"全市场唯一达到{leader['recent_limit_up_label']}，"
                    f"标准连板{leader['consecutive_limit_count']}板。"
                ),
                "evidence_ids": evidence_pairs[leader["stock_code"]],
            }
        )

    by_board: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for stock in stocks:
        by_board[stock["primary_concept"]].append(stock)
    board_order = sorted(by_board, key=lambda board: (-len(by_board[board]), ALL_BOARDS.index(board)))
    concept_summary: list[dict[str, Any]] = []
    lhb_codes = {str(row["stock_code"]) for row in lhb_rows}
    for board_index, board in enumerate(board_order):
        members = sorted(by_board[board], key=rank_key)
        if board_index < 3:
            analysis = analyze_board(
                board,
                members,
                lhb_codes=lhb_codes,
                supplemental_context=supplemental_context,
            )
            for row in analysis["nature_top"]:
                row["evidence_ids"] = evidence_pairs[row["stock_code"]]
                stock = next(
                    stock for stock in members if stock["stock_code"] == row["stock_code"]
                )
                for role_name in row["nature_names"]:
                    stock["leader_roles"].append(
                        {
                            "name": role_name,
                            "reason": row["reason"],
                            "evidence_ids": row["evidence_ids"],
                        }
                    )
            for row in analysis["position_top"]:
                row["evidence_ids"] = evidence_pairs[row["stock_code"]]
            concept_summary.append(
                {
                    "concept": board,
                    "verified_limit_up_count": len(members),
                    "earliest_first_limit_time": members[0]["first_limit_time"],
                    "logic_model": analysis,
                    "logic_summary": analysis["logic_statement"],
                    "mechanism_evidence": analysis["mechanism_statement"],
                    "validation_constraints": analysis["validation_statement"],
                    "nature_top": analysis["nature_top"],
                    "position_top": analysis["position_top"],
                }
            )
        else:
            concept_summary.append(
                {
                    "concept": board,
                    "verified_limit_up_count": len(members),
                    "earliest_first_limit_time": members[0]["first_limit_time"],
                    "logic_model": {},
                    "logic_summary": "",
                    "mechanism_evidence": "",
                    "validation_constraints": "",
                    "nature_top": [],
                    "position_top": [],
                }
            )

    morning = [
        {"stock_code": stock["stock_code"]}
        for stock in sorted(
            stocks,
            key=lambda row: (
                row["first_limit_time"],
                row["latest_seal_time_at_cutoff"],
                row["stock_code"],
            ),
        )
        if stock["latest_seal_time_at_cutoff"] <= "11:30:00"
    ]
    aggregate_evidence = [
        add_evidence(
            evidence,
            "E-AGG-EM",
            "EM-ZT",
            "000000",
            "全市场涨停池汇总",
            {"count": len(stocks), "morning": len(morning)},
            trade_date,
            fetched_at,
            f"eastmoney://ztpool/{trade_date}/summary",
        ),
        add_evidence(
            evidence,
            "E-AGG-DXX",
            "DXX-ZT",
            "000000",
            "全市场涨停池汇总",
            {"count": len(dxx_map), "morning": len(morning)},
            trade_date,
            dxx_fetched,
            f"duanxianxia://ztpool/{trade_date}/summary",
        ),
    ]
    if supplemental_context.get("status") == "CLEAN_PASS":
        aggregate_evidence.append(
            add_evidence(
                evidence,
                "E-AGG-LB",
                "LB-DAILY",
                "000000",
                "市场情绪与题材结构补充",
                {
                    "market": supplemental_context.get("market"),
                    "topics": supplemental_context.get("topics"),
                },
                trade_date,
                supplemental_context["requested_at"],
                supplemental_context["source_url"],
            )
        )
    board_counts = Counter(stock["primary_concept"] for stock in stocks)
    top_boards, top_count = leading_boards(board_counts)
    top_board_text = "、".join(top_boards)
    if len(top_boards) == 1:
        leading_text = (
            f"{top_board_text}以{top_count}只居首，"
            f"占涨停池{top_count / len(stocks) * 100:.1f}%。"
        )
        leading_basis = f"八类唯一归类后，{top_board_text}计数为{top_count}只。"
    else:
        leading_text = (
            f"{top_board_text}并列居首，各{top_count}只，"
            f"各占涨停池{top_count / len(stocks) * 100:.1f}%。"
        )
        leading_basis = (
            f"八类唯一归类后，{top_board_text}均为{top_count}只，"
            "不存在单一数量第一板块。"
        )
    linked_count = sum(stock["consecutive_limit_count"] >= 2 for stock in stocks)
    zero_open_count = sum(stock["open_count"] == 0 for stock in stocks)
    max_standard_height = max(stock["consecutive_limit_count"] for stock in stocks)
    standard_height_leaders = [
        stock for stock in stocks
        if stock["consecutive_limit_count"] == max_standard_height
    ]
    market_leader = next(
        (
            stock for stock in stocks
            if any(role["name"] == "市场总龙头" for role in stock["leader_roles"])
        ),
        None,
    )
    if market_leader:
        height_text = (
            f"{market_leader['stock_name']}以{market_leader['recent_limit_up_label']}"
            f"形成全市场唯一最高近期涨停高度，标准连板{market_leader['consecutive_limit_count']}板。"
        )
    else:
        height_names = "、".join(stock["stock_name"] for stock in standard_height_leaders[:3])
        height_text = (
            f"最高标准连板高度为{max_standard_height}板，"
            f"{height_names}处于当日最高梯队，未形成唯一市场总龙头。"
        )
    if lhb_rows:
        top_lhb = lhb_rows[0]
        lhb_names = "、".join(row["stock_name"] for row in lhb_rows[:4])
        lhb_text = (
            f"龙虎榜过亿净买入集中在{lhb_names}等{len(lhb_rows)}只涨停股，"
            f"其中{top_lhb['stock_name']}净买入{top_lhb['net_amount'] / 100_000_000:.2f}亿元居首。"
        )
    elif lhb_status == "not_published":
        lhb_text = f"截至{trade_date}当前盘中时点，交易所龙虎榜尚未发布。"
    else:
        lhb_text = "当日涨停股中龙虎榜单日净买入过亿元标的为0只。"
    top_analysis = concept_summary[0]["logic_model"]
    top_constraints = "；".join(top_analysis["constraints"][:2])
    claims = [
        {
            "claim_id": "C1",
            "label": "市场高度",
            "text": height_text,
            "evidence_ids": aggregate_evidence,
        },
        {
            "claim_id": "C2",
            "label": "主导板块",
            "text": (
                f"{leading_text}{concept_summary[0]['concept']}呈"
                f"{top_analysis['logic_type']}，共同机制覆盖"
                f"{top_analysis['shared_mechanisms'][0]['stock_count']}/"
                f"{concept_summary[0]['verified_limit_up_count']}只；"
                f"主要约束为{top_constraints}。"
            ),
            "evidence_ids": aggregate_evidence,
        },
        {
            "claim_id": "C3",
            "label": "连板梯队",
            "text": (
                f"连板股{linked_count}只，占当日{len(stocks)}只涨停股的"
                f"{linked_count / len(stocks) * 100:.1f}%；最高标准连板高度为"
                f"{max_standard_height}板。"
                + (
                    "全市场2板至最高板梯队连续。"
                    if not [
                        level
                        for level in range(2, max_standard_height + 1)
                        if not any(
                            stock["consecutive_limit_count"] == level for stock in stocks
                        )
                    ]
                    else "全市场连板梯队存在断层，接力结构并不完整。"
                )
            ),
            "evidence_ids": aggregate_evidence,
        },
        {
            "claim_id": "C4",
            "label": "封板强度",
            "text": (
                f"上午最终封板{len(morning)}只，占涨停股"
                f"{len(morning) / len(stocks) * 100:.1f}%；零开板"
                f"{zero_open_count}只，占{zero_open_count / len(stocks) * 100:.1f}%。"
                + (
                    "早盘定价与封板稳定性同时较强。"
                    if len(morning) / len(stocks) >= 0.6
                    and zero_open_count / len(stocks) >= 0.5
                    else "早盘定价或封板稳定性至少一项不足，强度需要折扣。"
                )
            ),
            "evidence_ids": aggregate_evidence,
        },
        {
            "claim_id": "C5",
            "label": "龙虎榜资金",
            "text": lhb_text,
            "evidence_ids": aggregate_evidence,
        },
    ]
    close_mode = market_phase not in {"active", "midday_pause", "preopen_with_current_data"}
    cutoff = (
        f"{trade_date}T15:00:00+08:00"
        if close_mode else now_china().isoformat()
    )
    tdx = read_tdx_status(trade_date)
    return {
        "workflow_name": "龙头深度研究",
        "schema_version": "3.2",
        "trade_date": trade_date,
        "data_mode": "close" if close_mode else "intraday",
        "generated_at": fetched_at,
        "data_cutoff": cutoff,
        "sources": sources,
        "evidence": evidence,
        "stocks": sorted(
            stocks,
            key=lambda row: (ALL_BOARDS.index(row["primary_concept"]), rank_key(row)),
        ),
        "concept_summary": concept_summary,
        "morning_limit_ups": morning,
        "lhb_status": lhb_status,
        "lhb_net_buy_ge_100m": lhb_rows,
        "report_claims": claims,
        "supplemental_context": supplemental_context,
        "unresolved_critical_conflicts": [],
        "source_notes": {
            "eastmoney_duanxianxia_code_set_difference": 0,
            "cross_source_sync_status": (
                source_sync.get("status") if source_sync else "NOT_RECORDED"
            ),
            "cross_source_sync_attempt_count": (
                source_sync.get("attempt_count") if source_sync else 0
            ),
            "sample_exclusion_policy": "剔除北交所、ST及退市股票后进行双源逐只对账。",
            "excluded_stocks": excluded_stocks,
            "tdx_ztc_path": tdx.get("path", str(TDX_ZTC)),
            "tdx_ztc_last_write": tdx.get("last_write"),
            "tdx_ztc_status": tdx["detail"],
        },
        "collection_artifacts": {
            "duanxianxia": str(dxx_path),
            "eastmoney_pool": str(em_path),
            "eastmoney_lhb": str(lhb_path),
            "eastmoney_lhb_details": str(lhb_detail_path),
            "cross_source_comparison": (
                source_sync.get("comparison_log") if source_sync else ""
            ),
        },
    }


def collect_payload(
    trade_date: str,
    market_phase: str,
    run_dir: Path,
    output_path: Path,
    template_contract_path: Path,
) -> tuple[dict[str, Any], Path]:
    run_dir.mkdir(parents=True, exist_ok=True)
    source_sync = collect_stable_limit_up_sources(trade_date, run_dir)
    dxx = source_sync["duanxianxia"]
    dxx_path = source_sync["duanxianxia_path"]
    em = source_sync["eastmoney"]
    em_path = source_sync["eastmoney_path"]
    em_url = source_sync["eastmoney_url"]
    intraday = market_phase in {"active", "midday_pause", "preopen_with_current_data"}
    lhb, lhb_path, lhb_url = collect_eastmoney_lhb(
        trade_date,
        run_dir,
        allow_not_published=intraday,
    )
    supplemental_context = load_lianban_context(trade_date, run_dir)
    payload = build_payload(
        trade_date,
        market_phase,
        run_dir,
        dxx,
        dxx_path,
        em,
        em_path,
        em_url,
        lhb,
        lhb_path,
        lhb_url,
        supplemental_context,
        source_sync,
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "schema": "LEADER_DEEP_RESEARCH_RUN_MANIFEST_V1",
        "trade_date": trade_date,
        "generated_at": now_china().isoformat(),
        "result_path": str(output_path),
        "result_sha256": sha256_path(output_path),
        "template_contract_path": str(template_contract_path),
        "template_contract_sha256": sha256_path(template_contract_path),
    }
    manifest_path = run_dir / "result_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload, manifest_path
