#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import math
import os
import re
import struct
import subprocess
import sys
import shutil
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_tdx_root

from audit_engine import validate_artifacts, validate_candidate_score

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


SKILL_DIR = Path(__file__).resolve().parent.parent
# The packaged desktop passes the user-selected TDX directory through the
# environment. Keep the development default behind an explicit variable so a
# copied EXE never silently reads C:\\new_tdx_mock on another computer.
TDX_ROOT = resolve_tdx_root()


def runtime_home(skill_dir: Path) -> Path:
    # 迁移包中的技能位于同一个 harness-skills 目录，不能假设项目根存在 skills/。
    return skill_dir.parent


CODEX_HOME = runtime_home(SKILL_DIR)
REPORT_TEMPLATE = SKILL_DIR / "assets" / "15维选股_教学案例精美Word模板.docx"
REPORT_TEMPLATE_SHA256 = "EC71F04176CB13FBF56AC73D60EE6701CCC71AB877C457D365E130A1795993F5"
TRADING_CALENDAR = SKILL_DIR / "references" / "trading-calendar.json"
LDAY_DIRS = {
    "SH": TDX_ROOT / "vipdoc" / "sh" / "lday",
    "SZ": TDX_ROOT / "vipdoc" / "sz" / "lday",
    "BJ": TDX_ROOT / "vipdoc" / "bj" / "lday",
}
TNF_FILES = [
    ("SH", TDX_ROOT / "T0002" / "hq_cache" / "shs.tnf"),
    ("SZ", TDX_ROOT / "T0002" / "hq_cache" / "szs.tnf"),
    ("BJ", TDX_ROOT / "T0002" / "hq_cache" / "bjs.tnf"),
]
TDX_ENTRY = CODEX_HOME / "tdx-local-hub" / "scripts" / "legacy_codex_entry.py"
TDX_NEWS_DIRS = [
    TDX_ROOT / "T0002" / "msg_zx",
    TDX_ROOT / "T0002" / "cache",
    TDX_ROOT / "T0002" / "info_cache",
]
HQ_CACHE = TDX_ROOT / "T0002" / "hq_cache"
BLOCK_CONFIG = TDX_ROOT / "T0002" / "blocknew" / "blocknew.cfg"
# Some TDX installations (including the local mock/portable client) persist
# the .blk files but do not generate blocknew.cfg until the client has saved a
# custom block.  Keep the known built-in aliases here so the scorer can still
# use the exact block file when the catalog is absent, while unknown names
# remain strict and continue to fail closed.
BLOCK_FILE_ALIASES = {
    "飞龙在天": "FLZT",
    "FLZT": "FLZT",
    "涨停池": "ZTC",
    "ZTC": "ZTC",
}
BLOCK_RECORD_SIZE = 120
BLOCK_NAME_SIZE = 50
DAY_RECORD = struct.Struct("<IIIIIfII")
TNF_HEADER_SIZE = 50
TNF_RECORD_SIZE = 360
TNF_NAME_OFFSET = 31
TNF_NAME_SIZE = 18

GLOBAL_SCORE_CONTRACT = CODEX_HOME / "stock-unified" / "references" / "short_term_strong_stock_scoring_contract.json"
GLOBAL_SCORE_CONTRACT_PAYLOAD = json.loads(GLOBAL_SCORE_CONTRACT.read_text(encoding="utf-8"))
GLOBAL_SCORE_CONTRACT_SHA256 = hashlib.sha256(GLOBAL_SCORE_CONTRACT.read_bytes()).hexdigest()
if GLOBAL_SCORE_CONTRACT_PAYLOAD.get("version") != "A-SHARE-STRONG-26F-100-V6.1":
    raise RuntimeError("global_short_term_score_contract_version_mismatch")
if GLOBAL_SCORE_CONTRACT_PAYLOAD.get("fundamental_policy", {}).get("positive_weight") != 0:
    raise RuntimeError("global_short_term_score_contract_fundamental_weight_not_zero")

POSITIVE_DIMENSIONS = [
    (str(row["name"]), float(row["weight"]))
    for row in GLOBAL_SCORE_CONTRACT_PAYLOAD["factors"]
]
FACTOR_AXES = {str(row["name"]): str(row["axis"]) for row in GLOBAL_SCORE_CONTRACT_PAYLOAD["factors"]}
FACTOR_ROLES = {str(row["name"]): str(row["role"]) for row in GLOBAL_SCORE_CONTRACT_PAYLOAD["factors"]}
RANKING_FACTOR_ROLES = {"candidate_ranking", "candidate_evidence"}
AXIS_MAX_SCORES = {str(key): float(value) for key, value in GLOBAL_SCORE_CONTRACT_PAYLOAD["axes"].items()}
SCORE_CONTRACT_VERSION = str(GLOBAL_SCORE_CONTRACT_PAYLOAD["version"])
PENDING_FACTORS = list(GLOBAL_SCORE_CONTRACT_PAYLOAD["pending_factors"])
REJECTED_FACTORS = list(GLOBAL_SCORE_CONTRACT_PAYLOAD["rejected_factors"])
RISK_NAMES = [str(row["name"]) for row in GLOBAL_SCORE_CONTRACT_PAYLOAD["risk_deductions"]]
if len(POSITIVE_DIMENSIONS) != 26 or round(sum(weight for _name, weight in POSITIVE_DIMENSIONS), 6) != 100.0:
    raise RuntimeError("global_short_term_score_contract_factor_invariant_failed")
if len(RISK_NAMES) != 15 or len(GLOBAL_SCORE_CONTRACT_PAYLOAD["hard_exclusions"]) != 7:
    raise RuntimeError("global_short_term_score_contract_gate_invariant_failed")

REQUIRED_FORMULA_FIELDS = {
    "大牛线4.0": ("主趋势线", "EMA9", "EMA10", "EMA11"),
    "飞龙在天": ("波", "段"),
    "游资资金监控": ("买方意向", "AAA", "DDD"),
    "机构资金监控": ("机构大单进", "机构大单出", "大单动向", "大户大单进", "散户资金进"),
}

HARD_NAMES = [
    "风险警示或退市整理",
    "立案调查或财务造假",
    "当日一字板无法参与",
    "波大于90且无主升启动信号",
    "近3日极端加速且无启动承接",
    "近5日或10日极端加速且无资金承接",
    "飞龙在天段大于80或字段缺失",
]

RISK_KEYWORDS = ["立案调查", "财务造假", "退市风险", "重大违法", "审计无法表示意见"]
MAJOR_RISK_KEYWORDS = ["重大诉讼", "行政处罚", "监管问询", "债务逾期", "资金占用", "业绩预亏", "大额亏损"]
REDUCTION_KEYWORDS = ["大额减持", "减持比例", "解禁市值", "限售股上市"]
CATALYST_KEYWORDS = ["中标", "订单", "回购", "增持", "战略合作", "政策支持"]
FUNDAMENTAL_KEYWORDS = ["营收增长", "净利润增长", "扣非净利润增长", "毛利率提升", "业绩预增", "扭亏为盈"]
FINANCIAL_SAFETY_KEYWORDS = ["现金流改善", "负债率下降", "偿债能力提升", "完成债务偿还", "无逾期债务"]
LHB_POSITIVE_KEYWORDS = ["龙虎榜净买入", "机构专用买入", "营业部净买入", "游资净买入"]


def now_cn() -> datetime:
    return datetime.now(ZoneInfo("Asia/Shanghai"))


def expected_completed_trade_date(moment: datetime) -> str:
    calendar = json.loads(TRADING_CALENDAR.read_text(encoding="utf-8"))
    supported_years = {int(value) for value in calendar.get("years", [])}
    if moment.year not in supported_years:
        raise RuntimeError(f"trading calendar year unavailable: {moment.year}")
    closed_dates = set(calendar.get("closed_dates", []))
    day = moment.date()
    # A 股连续竞价在 15:00 收市；TDX may persist the completed daily bar
    # before the broader 17:00 post-close window.  When the local day-file
    # scan proves full coverage, accept today's completed bar after 15:00.
    if moment.weekday() < 5 and moment.hour < 15:
        day -= timedelta(days=1)
    while day.weekday() >= 5 or day.strftime("%Y%m%d") in closed_dates:
        day -= timedelta(days=1)
    return day.strftime("%Y%m%d")


def fnum(value: Any, default: float | None = None) -> float | None:
    if isinstance(value, list):
        value = value[-1] if value else None
    if value is None or value == "":
        return default
    try:
        result = float(str(value).replace("%", "").strip())
        return result if math.isfinite(result) else default
    except Exception:
        return default


def positive_signal_active(value: Any) -> bool:
    if isinstance(value, list):
        value = value[-1] if value else None
    if value is None:
        return False
    numeric = fnum(value)
    if numeric is not None:
        return numeric > 0
    text = str(value).strip()
    if not text:
        return False
    return any(token in text for token in ("启动", "打板", "秘进", "龙头", "点火", "金叉", "庄进"))


def exit_signal_active(value: Any) -> bool:
    if isinstance(value, list):
        value = value[-1] if value else None
    if value is None:
        return False
    numeric = fnum(value)
    if numeric is not None:
        return numeric > 0
    text = str(value).strip()
    return bool(text) and any(token in text for token in ("庄出", "卖出", "离场", "转弱"))


def last_value(fields: dict[str, Any], key: str, default: Any = None) -> Any:
    value = fields.get(key, default)
    if isinstance(value, list):
        return value[-1] if value else default
    return value


def decode_tnf(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("gbk", errors="ignore").strip()


def load_names() -> dict[str, str]:
    names: dict[str, str] = {}
    for market, path in TNF_FILES:
        data = path.read_bytes()
        for offset in range(TNF_HEADER_SIZE, len(data) - TNF_RECORD_SIZE + 1, TNF_RECORD_SIZE):
            record = data[offset : offset + TNF_RECORD_SIZE]
            code = decode_tnf(record[:6])
            name = decode_tnf(record[TNF_NAME_OFFSET : TNF_NAME_OFFSET + TNF_NAME_SIZE])
            if len(code) == 6 and code.isdigit() and name:
                names[f"{market}:{code}"] = name
    if len(names) < 3000:
        raise RuntimeError(f"TDX name map incomplete: {len(names)}")
    return names


def resolve_candidate_block(
    block_name: str,
    config_path: Path = BLOCK_CONFIG,
) -> dict[str, Any]:
    requested_name = str(block_name).strip()
    if not requested_name:
        raise RuntimeError("TDX candidate block name is empty")
    config_path = Path(config_path).resolve()
    # Portable TDX copies can contain FLZT.blk/ZTC.blk without the optional
    # catalog.  Only apply the fallback for the default live TDX path; an
    # explicitly supplied catalog in tests or another installation must keep
    # the strict catalog contract.
    if not config_path.is_file():
        default_config = BLOCK_CONFIG.resolve()
        if config_path == default_config and requested_name in BLOCK_FILE_ALIASES:
            block_code = BLOCK_FILE_ALIASES[requested_name]
            block_path = config_path.parent / f"{block_code}.blk"
            if not block_path.is_file():
                raise RuntimeError(f"TDX candidate block file missing: {block_path}")
            data = None
            catalog_path = None
            catalog_sha256 = None
        else:
            raise RuntimeError(f"TDX block catalog missing: {config_path}")
    else:
        data = config_path.read_bytes()
        catalog_path = config_path
        catalog_sha256 = hashlib.sha256(data).hexdigest().upper()
    if data is not None:
        if not data or len(data) % BLOCK_RECORD_SIZE != 0:
            raise RuntimeError(f"TDX block catalog malformed: {config_path}")
        catalog: dict[str, str] = {}
        for offset in range(0, len(data), BLOCK_RECORD_SIZE):
            record = data[offset : offset + BLOCK_RECORD_SIZE]
            name = record[:BLOCK_NAME_SIZE].split(b"\x00", 1)[0].decode("gbk", errors="strict").strip()
            code = record[BLOCK_NAME_SIZE:].split(b"\x00", 1)[0].decode("ascii", errors="strict").strip()
            if name and re.fullmatch(r"[A-Za-z0-9_]{1,16}", code):
                catalog[name] = code.upper()
        if requested_name not in catalog:
            raise RuntimeError(f"TDX candidate block not found: {requested_name}")
        block_code = catalog[requested_name]
        block_path = config_path.parent / f"{block_code}.blk"
        if not block_path.is_file():
            raise RuntimeError(f"TDX candidate block file missing: {block_path}")
    members: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for line_number, raw_line in enumerate(block_path.read_text(encoding="ascii").splitlines(), 1):
        entry = raw_line.strip()
        if not entry:
            continue
        if not re.fullmatch(r"[012]\d{6}", entry):
            raise RuntimeError(
                f"invalid TDX block member at line {line_number}: {entry}"
            )
        market = {"0": "SZ", "1": "SH", "2": "BJ"}[entry[0]]
        code = entry[1:]
        if not valid_a_code(market, code):
            raise RuntimeError(
                f"unsupported A-share block member at line {line_number}: {entry}"
            )
        key = (market, code)
        if key not in seen:
            seen.add(key)
            members.append({"market": market, "code": code})
    if not members:
        raise RuntimeError(f"TDX candidate block has no valid members: {requested_name}")
    return {
        "mode": "tdx_custom_block",
        "name": requested_name,
        "code": block_code,
        "path": str(block_path),
        "sha256": hashlib.sha256(block_path.read_bytes()).hexdigest().upper(),
        "catalog_path": str(catalog_path) if catalog_path else None,
        "catalog_sha256": catalog_sha256,
        "catalog_fallback": data is None,
        "member_count": len(members),
        "members": members,
    }


def decode_day_record(raw: bytes) -> dict[str, Any]:
    date, open_i, high_i, low_i, close_i, amount, volume, _ = DAY_RECORD.unpack(raw)
    return {
        "date": str(date),
        "open": round(open_i / 100.0, 2),
        "high": round(high_i / 100.0, 2),
        "low": round(low_i / 100.0, 2),
        "close": round(close_i / 100.0, 2),
        "amount": float(amount),
        "volume": int(volume),
    }


def load_day(path: Path, limit: int = 140) -> list[dict[str, Any]]:
    size = path.stat().st_size
    count = size // DAY_RECORD.size
    if count <= 0:
        return []
    take = min(count, limit)
    with path.open("rb") as handle:
        handle.seek((count - take) * DAY_RECORD.size)
        data = handle.read(take * DAY_RECORD.size)
    rows = []
    for offset in range(0, len(data), DAY_RECORD.size):
        raw = data[offset : offset + DAY_RECORD.size]
        if len(raw) == DAY_RECORD.size:
            row = decode_day_record(raw)
            if len(row["date"]) == 8 and row["close"] > 0:
                rows.append(row)
    return rows


def valid_a_code(market: str, code: str) -> bool:
    if market == "SH":
        return code.startswith(("600", "601", "603", "605", "688", "689"))
    if market == "SZ":
        return code.startswith(("000", "001", "002", "003", "300", "301"))
    if market == "BJ":
        return code.startswith(("4", "8", "9")) and not code.startswith("899")
    return False


def limit_rate(market: str, code: str) -> float:
    if market == "BJ":
        return 0.30
    return 0.20 if code.startswith(("300", "301", "688", "689")) else 0.10


def limit_price(prev_close: float, rate: float) -> float:
    return float((Decimal(str(prev_close)) * (Decimal("1") + Decimal(str(rate)))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def one_price_limit_streak(rows: list[dict[str, Any]], rate: float) -> int:
    streak = 0
    for index in range(len(rows) - 1, 0, -1):
        current, previous = rows[index], rows[index - 1]
        theoretical = limit_price(previous["close"], rate)
        one_price = all(abs(current[key] - current["close"]) < 0.001 for key in ("open", "high", "low"))
        at_limit = current["close"] >= theoretical - 0.011
        if not (one_price and at_limit):
            break
        streak += 1
    return streak


def gain(rows: list[dict[str, Any]], days: int) -> float | None:
    if len(rows) < days + 1:
        return None
    base = rows[-days - 1]["close"]
    return round((rows[-1]["close"] / base - 1) * 100, 4) if base else None


def ma(rows: list[dict[str, Any]], days: int, field: str = "close") -> float | None:
    if len(rows) < days:
        return None
    return sum(float(row[field]) for row in rows[-days:]) / days


def ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2.0 / (period + 1)
    result = [values[0]]
    for value in values[1:]:
        result.append(alpha * value + (1 - alpha) * result[-1])
    return result


def macd_hist(rows: list[dict[str, Any]]) -> list[float]:
    values = [float(row["close"]) for row in rows]
    e12, e26 = ema(values, 12), ema(values, 26)
    dif = [a - b for a, b in zip(e12, e26)]
    dea = ema(dif, 9)
    return [(a - b) * 2 for a, b in zip(dif, dea)]


def macd_bearish_divergence(closes: list[float], hist: list[float]) -> bool:
    if len(closes) < 10 or len(hist) < 10 or closes[-1] < max(closes[-10:]):
        return False
    prior_positive_peak = max(hist[-10:-1])
    return prior_positive_peak > 0 and hist[-1] >= 0 and hist[-1] < prior_positive_peak * 0.75


def scan_market(
    names: dict[str, str],
    candidate_members: set[tuple[str, str]] | None = None,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    files: list[tuple[str, str, Path]] = []
    missing_directories = [str(folder) for folder in LDAY_DIRS.values() if not folder.is_dir()]
    if missing_directories:
        raise RuntimeError(f"TDX lday directories missing: {','.join(missing_directories)}")
    for market, folder in LDAY_DIRS.items():
        for path in folder.glob(f"{market.lower()}*.day"):
            code = path.stem[-6:]
            if not valid_a_code(market, code):
                continue
            files.append((market, code, path))
    date_counts: Counter[str] = Counter()
    read_errors: list[str] = []
    for market, code, path in files:
        try:
            with path.open("rb") as handle:
                handle.seek(-DAY_RECORD.size, 2)
                last_record = handle.read(DAY_RECORD.size)
            if len(last_record) == DAY_RECORD.size:
                date_value = str(DAY_RECORD.unpack(last_record)[0])
                if len(date_value) == 8:
                    date_counts[date_value] += 1
        except OSError as exc:
            read_errors.append(f"{market}:{code}:{type(exc).__name__}")
    if read_errors:
        raise RuntimeError(f"TDX latest-record scan failed: {','.join(read_errors[:20])}")
    complete_dates = [date for date, count in date_counts.items() if count >= 3000]
    if not complete_dates:
        raise RuntimeError(f"no complete TDX trade date: {date_counts.most_common(5)}")
    latest_date = max(complete_dates)
    market_rows: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    limit_up_count = 0
    stale_or_short_count = 0
    for index, (market, code, path) in enumerate(files, 1):
        if index % 800 == 0:
            print(f"MARKET_SCAN {index}/{len(files)}", flush=True)
        try:
            rows = load_day(path, 140)
        except Exception as exc:
            read_errors.append(f"{market}:{code}:{type(exc).__name__}")
            continue
        if len(rows) < 11 or rows[-1]["date"] != latest_date:
            stale_or_short_count += 1
            continue
        name = names.get(f"{market}:{code}", "")
        last, prev = rows[-1], rows[-2]
        pct = round((last["close"] / prev["close"] - 1) * 100, 4) if prev["close"] else 0.0
        market_rows.append({
            "code": code,
            "name": name,
            "pct": pct,
            "gain3": gain(rows, 3),
            "gain5": gain(rows, 5),
            "gain10": gain(rows, 10),
            "amount": last["amount"],
        })
        bad_name = not name or bool(re.search(r"(?:\*?ST|退市)", name, re.I))
        no_limit_name = bool(re.search(r"^[NC]", name, re.I))
        theoretical = limit_price(prev["close"], limit_rate(market, code))
        is_limit = not no_limit_name and last["close"] >= theoretical - 0.011 and last["high"] >= theoretical - 0.011 and last["amount"] > 0
        if is_limit and not bad_name:
            limit_up_count += 1
        selected = (
            (market, code) in candidate_members
            if candidate_members is not None
            else is_limit and not bad_name
        )
        if selected:
            if not name:
                raise RuntimeError(f"TDX identity missing for candidate: {market}:{code}")
            one_price_streak = one_price_limit_streak(rows, limit_rate(market, code))
            candidates.append({
                "market": market,
                "code": code,
                "symbol": f"{code}.{market}",
                "name": name,
                "path": str(path),
                "rows": rows,
                "pct": pct,
                "limit_price": theoretical,
                "is_limit_up": is_limit,
                "is_one_price": one_price_streak > 0,
                "one_price_streak": one_price_streak,
                "recent_gain_3d_pct": gain(rows, 3),
                "recent_gain_5d_pct": gain(rows, 5),
                "recent_gain_10d_pct": gain(rows, 10),
            })
    if len(market_rows) < 3000:
        raise RuntimeError(f"latest TDX market rows incomplete: {len(market_rows)}")
    if read_errors:
        raise RuntimeError(f"TDX day-file scan failed: {','.join(read_errors[:20])}")
    return_cohorts = {
        "1d": sorted(round(float(row["pct"]), 4) for row in market_rows),
        "3d": sorted(round(float(row["gain3"]), 4) for row in market_rows if row["gain3"] is not None),
        "5d": sorted(round(float(row["gain5"]), 4) for row in market_rows if row["gain5"] is not None),
        "10d": sorted(round(float(row["gain10"]), 4) for row in market_rows if row["gain10"] is not None),
    }
    macro = {
        "trade_date": latest_date,
        "market_count": len(market_rows),
        "advancers": sum(1 for row in market_rows if row["pct"] > 0),
        "decliners": sum(1 for row in market_rows if row["pct"] < 0),
        "flat": sum(1 for row in market_rows if row["pct"] == 0),
        "total_amount_yi": round(sum(row["amount"] for row in market_rows) / 100000000, 2),
        "limit_up_count": limit_up_count,
        "market_return_cohorts": return_cohorts,
        "scan_coverage": {
            "eligible_file_count": len(files),
            "current_row_count": len(market_rows),
            "stale_or_short_count": stale_or_short_count,
            "read_error_count": len(read_errors),
            "markets": sorted(LDAY_DIRS),
            "complete": len(read_errors) == 0 and len(market_rows) >= 3000,
        },
    }
    if candidate_members is not None:
        resolved_members = {(item["market"], item["code"]) for item in candidates}
        missing_members = sorted(candidate_members - resolved_members)
        if missing_members:
            missing_text = ",".join(f"{market}:{code}" for market, code in missing_members)
            raise RuntimeError(
                f"TDX candidate block members missing current complete K-line: {missing_text}"
            )
    return latest_date, candidates, macro


def run_hub(args: list[str], timeout: int = 180) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(TDX_ENTRY), "run", "--", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    text = (proc.stdout or "").strip()
    try:
        payload = json.loads(text)
    except Exception:
        payload = {"ok": False, "stdout_tail": text[-1000:], "stderr_tail": (proc.stderr or "")[-1000:]}
    payload["returncode"] = proc.returncode
    return payload


def formula_fields(scan: dict[str, Any], formula: str, symbol: str) -> dict[str, Any]:
    for item in scan.get("items", []):
        if item.get("formula") == formula:
            result = item.get("result") or {}
            return result.get(symbol, {}) if isinstance(result, dict) else {}
    return {}


def formula_ok(scan: dict[str, Any], formula: str) -> bool:
    return any(item.get("formula") == formula and item.get("ok") is True for item in scan.get("items", []))


def required_formula_result_ok(formula: str, fields: dict[str, Any]) -> bool:
    required_fields = REQUIRED_FORMULA_FIELDS.get(formula, ())
    return bool(required_fields) and all(fnum(last_value(fields, field)) is not None for field in required_fields)


def collect_local_text() -> list[tuple[str, str]]:
    cutoff = datetime.now().timestamp() - timedelta(days=14).total_seconds()
    paths: list[Path] = []
    for folder in TDX_NEWS_DIRS:
        if folder.exists():
            paths.extend(path for path in folder.glob("*") if path.is_file())
            paths.extend(path for path in folder.glob("*/*") if path.is_file())
    for name in ["speclhbyzyc.txt", "specmeeting.txt", "specgpext.txt", "infoharbor_ex.code"]:
        path = HQ_CACHE / name
        if path.is_file():
            paths.append(path)
    result: list[tuple[str, str]] = []
    total = 0
    for path in sorted(set(paths), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            if path.stat().st_mtime < cutoff or path.stat().st_size > 2_000_000:
                continue
            data = path.read_bytes()
            total += len(data)
            if total > 30_000_000:
                break
            text = data.decode("gbk", errors="ignore")
            if text.strip():
                result.append((str(path), text))
        except Exception:
            continue
    return result


def text_hits(corpus: list[tuple[str, str]], code: str, name: str, keywords: list[str]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for source, text in corpus:
        for anchor in [code, name]:
            start = 0
            while anchor and (index := text.find(anchor, start)) >= 0:
                left = max(text.rfind(mark, 0, index) for mark in ("。", "；", "\n", "\r"))
                right_values = [position for mark in ("。", "；", "\n", "\r") if (position := text.find(mark, index)) >= 0]
                right = min(right_values) if right_values else min(len(text), index + 420)
                snippet = text[max(left + 1, index - 160) : min(right + 1, index + 420)]
                found = []
                for word in keywords:
                    position = snippet.find(word)
                    if position < 0:
                        continue
                    prefix = snippet[max(0, position - 8) : position]
                    if any(token in prefix for token in ("未", "无", "不存在", "否认", "不涉及")):
                        continue
                    found.append(word)
                if found:
                    hits.append({"source": source, "keywords": "、".join(found), "snippet": re.sub(r"\s+", " ", snippet)[:220]})
                    break
                start = index + len(anchor)
            if hits:
                break
        if len(hits) >= 3:
            break
    return hits


def candidate_text_source_count(corpus: list[tuple[str, str]], code: str, name: str) -> int:
    return sum(1 for _source, text in corpus if code in text or (name and name in text))


def stars(weight: float, value: float) -> float:
    return round(max(0.0, min(5.0, value)) / 5.0 * weight, 2)


def cross_sectional_stars(value: float, cohort: list[float]) -> float:
    if value <= 0:
        return 0.0
    valid = [float(peer) for peer in cohort if math.isfinite(float(peer)) and float(peer) > 0]
    if len(valid) < 5:
        return 5.0
    stronger = sum(peer > value + 1e-12 for peer in valid)
    percentile = stronger / len(valid)
    if percentile < 0.10:
        return 5.0
    if percentile < 0.30:
        return 4.0
    if percentile < 0.60:
        return 3.0
    return 1.5


def percentile_rank(value: float | None, cohort: list[float]) -> float:
    if value is None or not math.isfinite(float(value)):
        return 0.0
    valid = [float(peer) for peer in cohort if math.isfinite(float(peer))]
    if not valid:
        return 0.0
    numeric = float(value)
    below = sum(peer < numeric - 1e-12 for peer in valid)
    equal = sum(abs(peer - numeric) <= 1e-12 for peer in valid)
    return (below + 0.5 * equal) / len(valid)


def percentile_stars(percentile: float) -> float:
    return 5.0 if percentile >= 0.90 else 4.0 if percentile >= 0.70 else 3.0 if percentile >= 0.40 else 1.5 if percentile >= 0.20 else 0.0


def ratio_to_prior_average(rows: list[dict[str, Any]], field: str, days: int = 20) -> float:
    history = rows[-days - 1:-1] if len(rows) >= days + 1 else rows[:-1]
    values = [float(row[field]) for row in history if fnum(row.get(field), 0.0) and float(row[field]) > 0]
    return float(rows[-1][field]) / (sum(values) / len(values)) if values else 0.0


def return_acceleration(item: dict[str, Any]) -> float:
    gain3 = fnum(item.get("recent_gain_3d_pct"))
    gain10 = fnum(item.get("recent_gain_10d_pct"))
    if gain3 is None or gain10 is None:
        return 0.0
    return gain3 / 3.0 - (gain10 - gain3) / 7.0


def relative_strength_metric(item: dict[str, Any]) -> float:
    gain3 = fnum(item.get("recent_gain_3d_pct"))
    gain5 = fnum(item.get("recent_gain_5d_pct"))
    gain10 = fnum(item.get("recent_gain_10d_pct"))
    if None in (gain3, gain5, gain10):
        return 0.0
    return 0.25 * gain3 + 0.35 * gain5 + 0.40 * gain10


def volume_quality_metric(item: dict[str, Any]) -> float:
    ratio = ratio_to_prior_average(item.get("rows") or [], "volume") if item.get("rows") else 0.0
    if not 0.4 <= ratio <= 6.0:
        return 0.0
    return math.exp(-abs(math.log(ratio / 1.8)))


def trend_slope_metric(rows: list[dict[str, Any]]) -> float:
    if len(rows) < 10:
        return 0.0
    current = sum(float(row["close"]) for row in rows[-5:]) / 5
    prior = sum(float(row["close"]) for row in rows[-10:-5]) / 5
    return (current / prior - 1) * 100 if prior > 0 else 0.0


def trend_efficiency_metric(rows: list[dict[str, Any]], days: int = 10) -> float:
    if len(rows) < days + 1:
        return 0.0
    values = [float(row["close"]) for row in rows[-days - 1:]]
    path = sum(abs(right - left) for left, right in zip(values, values[1:]))
    return max(0.0, (values[-1] - values[0]) / path) if path > 0 else 0.0


def price_volume_consistency(rows: list[dict[str, Any]], days: int = 10) -> float:
    sample = rows[-days - 1:]
    if len(sample) < 3:
        return 0.0
    matches = 0
    observations = 0
    for previous, current in zip(sample, sample[1:]):
        price_change = float(current["close"]) - float(previous["close"])
        volume_change = float(current["volume"]) - float(previous["volume"])
        if price_change == 0:
            continue
        observations += 1
        matches += int((price_change > 0 and volume_change >= 0) or (price_change < 0 and volume_change <= 0))
    return matches / observations if observations else 0.0


def institution_strength(item: dict[str, Any]) -> float:
    fields = item.get("formula_fields", {}).get("机构资金监控", {})
    values = [fnum(last_value(fields, key)) for key in ("机构大单进", "机构大单出", "大单动向", "大户大单进", "散户资金进")]
    if any(value is None for value in values):
        return 0.0
    inst_in, inst_out, big_order, large_in, retail_in = values
    scale = abs(inst_in) + abs(inst_out) + 1e-9
    normalized_net = max(0.0, inst_in - inst_out) / scale
    breadth = sum((big_order > 0, large_in > 0, retail_in < 0)) / 3.0
    return normalized_net + breadth


def liquidity_stability_metric(rows: list[dict[str, Any]], days: int = 20) -> float:
    values = [float(row["amount"]) for row in rows[-days:] if float(row["amount"]) > 0]
    if len(values) < 5:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return 1.0 / (1.0 + math.sqrt(variance) / mean) if mean > 0 else 0.0


def atr_percent(rows: list[dict[str, Any]], days: int = 10) -> float:
    if len(rows) < days + 1:
        return 0.0
    ranges = []
    for previous, current in zip(rows[-days - 1:-1], rows[-days:]):
        high, low, prev_close = float(current["high"]), float(current["low"]), float(previous["close"])
        ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    close = float(rows[-1]["close"])
    return sum(ranges) / len(ranges) / close * 100 if close > 0 else 0.0


def volatility_quality_metric(rows: list[dict[str, Any]]) -> float:
    atr_value = atr_percent(rows)
    if atr_value <= 0:
        return 0.0
    return math.exp(-abs(math.log(atr_value / 5.0)))


def market_breadth_stars(macro: dict[str, Any]) -> float:
    advancers = int(macro.get("advancers") or 0)
    decliners = int(macro.get("decliners") or 0)
    breadth = advancers / (advancers + decliners) if advancers + decliners else 0.0
    return 5.0 if breadth >= 0.60 else 4.0 if breadth >= 0.52 else 3.0 if breadth >= 0.45 else 1.5 if breadth >= 0.38 else 0.0


def limit_up_ecology_stars(macro: dict[str, Any]) -> float:
    market_count = int(macro.get("market_count") or 0)
    density = int(macro.get("limit_up_count") or 0) / market_count if market_count else 0.0
    return 5.0 if density >= 0.015 else 4.0 if density >= 0.010 else 3.0 if density >= 0.005 else 1.5 if density >= 0.002 else 0.0


def short_fund_strength(item: dict[str, Any]) -> float:
    rows = item.get("rows") or []
    fields = item.get("formula_fields", {}).get("游资资金监控", {})
    if not rows or not isinstance(fields, dict):
        return 0.0
    close = fnum(rows[-1].get("close"))
    buyer = fnum(last_value(fields, "买方意向"))
    aaa = fnum(last_value(fields, "AAA"))
    ddd = fnum(last_value(fields, "DDD"))
    if None in (close, buyer, aaa, ddd) or close <= 0 or buyer <= 0 or aaa <= ddd or aaa <= 0:
        return 0.0
    return buyer / close


def theme_strength(item: dict[str, Any], concept_frequency: Counter[str], population: int) -> float:
    peer_counts = sorted(
        (max(0, int(concept_frequency[token]) - 1) for token in set(item.get("concepts", []))),
        reverse=True,
    )
    return sum(peer_counts[:3]) / max(1, population)


def build_scoring_context(
    items: list[dict[str, Any]],
    concept_frequency: Counter[str],
    macro: dict[str, Any] | None = None,
) -> dict[str, Any]:
    population = max(1, len(items))
    return {
        "short_fund_strengths": [short_fund_strength(item) for item in items],
        "institution_strengths": [institution_strength(item) for item in items],
        "theme_strengths": [theme_strength(item, concept_frequency, population) for item in items],
        "return_accelerations": [return_acceleration(item) for item in items],
        "relative_strengths": [relative_strength_metric(item) for item in items],
        "volume_qualities": [volume_quality_metric(item) for item in items],
        "amount_ratios": [ratio_to_prior_average(item["rows"], "amount") for item in items],
        "trend_slopes": [trend_slope_metric(item["rows"]) for item in items],
        "trend_efficiencies": [trend_efficiency_metric(item["rows"]) for item in items],
        "amounts": [float(item["rows"][-1]["amount"]) for item in items],
        "liquidity_stabilities": [liquidity_stability_metric(item["rows"]) for item in items],
        "volatility_qualities": [volatility_quality_metric(item["rows"]) for item in items],
        "macro": dict(macro or {}),
    }


def concept_tokens(text: str) -> list[str]:
    cleaned = re.sub(r"[：:，,；;/|]+", " ", text or "")
    tokens: list[str] = []
    for raw in cleaned.split():
        token = raw.strip()
        generic = {
            "概念版块", "综合类", "黑龙江", "海峡西岸", "粤港澳", "含H股",
            "含可转债", "通达信88", "融资融券", "沪股通", "深股通", "标准普尔",
        }
        if (
            not (2 <= len(token) <= 12)
            or token in generic
            or token.endswith(("板块", "省", "市", "自治区"))
            or token.startswith("含")
            or token.startswith("通达信")
        ):
            continue
        if token not in tokens:
            tokens.append(token)
    return tokens


def preliminary_hard(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        {"name": HARD_NAMES[0], "passed": not bool(re.search(r"(?:\*?ST|退市)", candidate["name"], re.I)), "evidence": f"名称={candidate['name']}"},
        {"name": HARD_NAMES[2], "passed": int(candidate.get("one_price_streak") or 0) == 0, "evidence": f"当日一字涨停={int(candidate.get('one_price_streak') or 0) > 0}，连续数={int(candidate.get('one_price_streak') or 0)}"},
    ]
    return checks


def enrich_candidate(candidate: dict[str, Any], corpus: list[tuple[str, str]]) -> dict[str, Any]:
    scan = run_hub(["five", candidate["symbol"]], timeout=240)
    big = formula_fields(scan, "大牛线4.0", candidate["symbol"])
    fly = formula_fields(scan, "飞龙在天", candidate["symbol"])
    hot = formula_fields(scan, "游资资金监控", candidate["symbol"])
    inst = formula_fields(scan, "机构资金监控", candidate["symbol"])
    dealer = formula_fields(scan, "庄家资金监控", candidate["symbol"])
    fields_by_formula = {
        "大牛线4.0": big,
        "飞龙在天": fly,
        "游资资金监控": hot,
        "机构资金监控": inst,
    }
    required_ok = {
        name: formula_ok(scan, name) and required_formula_result_ok(name, fields)
        for name, fields in fields_by_formula.items()
    }
    wave = fnum(last_value(fly, "波"))
    segment = fnum(last_value(fly, "段"))
    ignition = any(positive_signal_active(last_value(fly, key)) for key in ["OUTPUT3", "OUTPUT4", "OUTPUT5", "OUTPUT6"])
    buyer = fnum(last_value(hot, "买方意向"))
    aaa = fnum(last_value(hot, "AAA"))
    ddd = fnum(last_value(hot, "DDD"))
    inst_in = fnum(last_value(inst, "机构大单进"))
    inst_out = fnum(last_value(inst, "机构大单出"))
    fund_support = (
        buyer is not None and aaa is not None and ddd is not None and buyer > 0 and aaa > ddd
    ) or (
        inst_in is not None and inst_out is not None and inst_in > inst_out
    )
    risk_hits = text_hits(corpus, candidate["code"], candidate["name"], RISK_KEYWORDS)
    major_risk_hits = text_hits(corpus, candidate["code"], candidate["name"], MAJOR_RISK_KEYWORDS)
    reduction_hits = text_hits(corpus, candidate["code"], candidate["name"], REDUCTION_KEYWORDS)
    catalyst_hits = text_hits(corpus, candidate["code"], candidate["name"], CATALYST_KEYWORDS)
    fundamental_hits = text_hits(corpus, candidate["code"], candidate["name"], FUNDAMENTAL_KEYWORDS)
    financial_safety_hits = text_hits(corpus, candidate["code"], candidate["name"], FINANCIAL_SAFETY_KEYWORDS)
    lhb_hits = text_hits(corpus, candidate["code"], candidate["name"], LHB_POSITIVE_KEYWORDS)
    text_source_count = candidate_text_source_count(corpus, candidate["code"], candidate["name"])
    hard = preliminary_hard(candidate)
    hard.extend([
        {"name": HARD_NAMES[1], "passed": text_source_count > 0 and not risk_hits, "evidence": ("候选本地资讯未覆盖，硬风险核验不放行" if text_source_count == 0 else "候选本地资讯未命中硬风险词") if not risk_hits else risk_hits[0]["keywords"]},
        {"name": HARD_NAMES[3], "passed": wave is not None and not (wave > 90 and not ignition), "evidence": f"波={wave}，启动信号={ignition}"},
        {
            "name": HARD_NAMES[4],
            "passed": candidate.get("recent_gain_3d_pct") is not None and (
                float(candidate["recent_gain_3d_pct"]) <= 40 or ignition or fund_support
            ),
            "evidence": f"近3日={candidate.get('recent_gain_3d_pct')}%，启动={ignition}，资金承接={fund_support}",
        },
        {
            "name": HARD_NAMES[5],
            "passed": candidate.get("recent_gain_5d_pct") is not None and candidate.get("recent_gain_10d_pct") is not None and (
                (float(candidate["recent_gain_5d_pct"]) <= 60 and float(candidate["recent_gain_10d_pct"]) <= 90) or fund_support
            ),
            "evidence": f"近5/10日={candidate.get('recent_gain_5d_pct')}/{candidate.get('recent_gain_10d_pct')}%，资金承接={fund_support}",
        },
        {"name": HARD_NAMES[6], "passed": segment is not None and segment <= 80, "evidence": f"段={segment}" if segment is not None else "段字段缺失"},
    ])
    hard_by_name = {item["name"]: item for item in hard}
    hard = [hard_by_name[name] for name in HARD_NAMES]
    passed = all(item["passed"] for item in hard) and all(required_ok.values())
    return {
        **{key: value for key, value in candidate.items() if key != "rows"},
        "rows": candidate["rows"],
        "formula_scan": scan,
        "formula_required_ok": required_ok,
        "formula_fields": {"大牛线4.0": big, "飞龙在天": fly, "游资资金监控": hot, "机构资金监控": inst, "庄家资金监控": dealer},
        "wave": wave,
        "segment": segment,
        "ignition": ignition,
        "risk_hits": risk_hits,
        "major_risk_hits": major_risk_hits,
        "reduction_hits": reduction_hits,
        "catalyst_hits": catalyst_hits,
        "fundamental_hits": fundamental_hits,
        "financial_safety_hits": financial_safety_hits,
        "lhb_hits": lhb_hits,
        "candidate_text_source_count": text_source_count,
        "local_text_source_count": len(corpus),
        "evidence_status": "LOCAL_TEXT_COVERED" if text_source_count > 0 else "BLOCKED_NO_CANDIDATE_NEWS",
        "evidence_scope": "local_tdx_text_only",
        "hard_exclusions": hard,
        "passed_hard_gate": passed,
        "concepts": concept_tokens(str(last_value(big, "OUTPUT47", ""))),
    }


def score_candidate(
    item: dict[str, Any],
    concept_frequency: Counter[str],
    universe_size: int | None = None,
    scoring_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = item["rows"]
    last = rows[-1]
    closes = [float(row["close"]) for row in rows]
    big, fly, hot, inst, dealer = (item["formula_fields"][name] for name in ["大牛线4.0", "飞龙在天", "游资资金监控", "机构资金监控", "庄家资金监控"])
    trend = fnum(last_value(big, "主趋势线"))
    ema9 = fnum(last_value(big, "EMA9"))
    ema10 = fnum(last_value(big, "EMA10"))
    ema11 = fnum(last_value(big, "EMA11"))
    buyer = fnum(last_value(hot, "买方意向"))
    aaa = fnum(last_value(hot, "AAA"))
    ddd = fnum(last_value(hot, "DDD"))
    inst_in = fnum(last_value(inst, "机构大单进"))
    inst_out = fnum(last_value(inst, "机构大单出"))
    big_order = fnum(last_value(inst, "大单动向"))
    large_in = fnum(last_value(inst, "大户大单进"))
    retail_in = fnum(last_value(inst, "散户资金进"))
    ma5, ma10, ma20, ma60 = (ma(rows, n) for n in [5, 10, 20, 60])
    history20 = rows[-21:-1] if len(rows) >= 21 else rows[:-1]
    vol_ratio = ratio_to_prior_average(rows, "volume")
    amount_ratio = ratio_to_prior_average(rows, "amount")
    support20 = min((float(row["low"]) for row in history20), default=float(last["low"]))
    pressure20 = max((float(row["high"]) for row in history20), default=0.0)
    peer_candidates = [
        (token, max(0, int(concept_frequency[token]) - 1))
        for token in item.get("concepts", [])
    ]
    winning_concept, peer_strength = max(peer_candidates, key=lambda row: row[1], default=(None, 0))
    population = max(1, int(universe_size or max(concept_frequency.values(), default=1)))
    peer_ratio = (peer_strength + 1) / population if winning_concept else 0.0
    hot_strength = short_fund_strength(item)
    inst_strength = institution_strength(item)
    theme_metric = theme_strength(item, concept_frequency, population)
    context = scoring_context or build_scoring_context([item], concept_frequency)
    macro = context.get("macro") if isinstance(context.get("macro"), dict) else {}
    dimensions: list[dict[str, Any]] = []

    def add_factor(index: int, star_value: float, evidence: str, raw_value: Any = None, available: bool = True) -> None:
        name, weight = POSITIVE_DIMENSIONS[index]
        bounded = round(max(0.0, min(5.0, float(star_value))), 4)
        dimensions.append({
            "name": name,
            "axis": FACTOR_AXES[name],
            "role": FACTOR_ROLES[name],
            "ranking_relevant": FACTOR_ROLES[name] in RANKING_FACTOR_ROLES,
            "weight": weight,
            "stars": bounded,
            "score": stars(weight, bounded),
            "available": bool(available),
            "raw_value": raw_value,
            "evidence": evidence,
        })

    previous_close = float(rows[-2]["close"]) if len(rows) >= 2 else 0.0
    theoretical_limit = fnum(item.get("limit_price"))
    at_limit = theoretical_limit is not None and float(last["close"]) >= theoretical_limit - 0.011
    strength_ratio = fnum(item.get("pct"), 0.0) / (limit_rate(str(item.get("market") or "SZ"), str(item.get("code") or "000001")) * 100)
    s1 = 5.0 if at_limit else 4.0 if strength_ratio >= 0.85 else 3.0 if strength_ratio >= 0.60 else 1.5 if strength_ratio > 0 else 0.0
    add_factor(0, s1, f"涨幅={item.get('pct')}%，理论涨停价={theoretical_limit}，收盘={last['close']}，强度比={strength_ratio:.4f}", strength_ratio)

    breakout_pct = (float(last["close"]) / pressure20 - 1) * 100 if pressure20 > 0 else None
    s2 = 5.0 if breakout_pct is not None and breakout_pct >= 3 else 4.0 if breakout_pct is not None and breakout_pct >= 1 else 3.0 if breakout_pct is not None and breakout_pct > 0 else 1.5 if breakout_pct is not None and breakout_pct >= -2 else 0.0
    add_factor(1, s2, f"前20日压力={pressure20}，突破幅度={None if breakout_pct is None else round(breakout_pct, 2)}%", breakout_pct, breakout_pct is not None)

    acceleration = return_acceleration(item)
    s3 = cross_sectional_stars(acceleration, context.get("return_accelerations", []))
    add_factor(2, s3, f"近3/10日涨幅={item.get('recent_gain_3d_pct')}/{item.get('recent_gain_10d_pct')}%，收益加速度={acceleration:.4f}，横截面星级={s3}", acceleration)

    volume_quality = volume_quality_metric(item)
    s4 = cross_sectional_stars(volume_quality, context.get("volume_qualities", []))
    add_factor(3, s4, f"20日量比={vol_ratio:.4f}，健康放量指标={volume_quality:.4f}，横截面星级={s4}", volume_quality)

    s5 = cross_sectional_stars(amount_ratio, context.get("amount_ratios", []))
    add_factor(4, s5, f"成交额={float(last['amount'])/100000000:.2f}亿元，20日成交额比={amount_ratio:.4f}，横截面星级={s5}", amount_ratio)

    big_signal = any(positive_signal_active(last_value(big, field)) for field in ("OUTPUT3", "OUTPUT4", "OUTPUT5", "OUTPUT9"))
    s6 = 1.25 * sum((
        trend is not None and float(last["close"]) >= trend,
        None not in (ema9, ema10, ema11) and ema9 >= ema10 >= ema11,
        ema9 is not None and float(last["close"]) >= ema9,
        big_signal,
    ))
    add_factor(5, s6, f"收盘={last['close']}，主趋势线={trend}，均线={ema9}/{ema10}/{ema11}，主图信号={big_signal}")

    ignition = item.get("ignition") is True
    add_factor(6, 5.0 if ignition else 0.0, f"飞龙启动信号={ignition}", ignition)

    s8 = cross_sectional_stars(hot_strength, context.get("short_fund_strengths", []))
    add_factor(7, s8, f"买方意向={buyer}，甲值={aaa}，丁值={ddd}，归一强度={hot_strength:.6f}，横截面星级={s8}", hot_strength)

    s9 = cross_sectional_stars(inst_strength, context.get("institution_strengths", []))
    institution_net = round(inst_in - inst_out, 4) if inst_in is not None and inst_out is not None else None
    add_factor(8, s9, f"机构净额={institution_net}，资金广度强度={inst_strength:.4f}，横截面星级={s9}", inst_strength)

    relative_strength = relative_strength_metric(item)
    s10 = cross_sectional_stars(relative_strength, context.get("relative_strengths", []))
    add_factor(9, s10, f"近3/5/10日={item.get('recent_gain_3d_pct')}/{item.get('recent_gain_5d_pct')}/{item.get('recent_gain_10d_pct')}%，多周期强度={relative_strength:.4f}，横截面星级={s10}", relative_strength)

    trend_mas_complete = None not in (ma5, ma10, ma20)
    s11 = 5.0 if trend_mas_complete and last["close"] >= ma5 >= ma10 >= ma20 else 3.0 if trend_mas_complete and last["close"] >= ma20 and ma5 >= ma10 else 1.5 if ma20 is not None and last["close"] >= ma20 else 0.0
    add_factor(10, s11, f"收盘/MA5/MA10/MA20={last['close']}/{None if ma5 is None else round(ma5,2)}/{None if ma10 is None else round(ma10,2)}/{None if ma20 is None else round(ma20,2)}", s11, trend_mas_complete)

    slope_metric = trend_slope_metric(rows)
    s12 = cross_sectional_stars(slope_metric, context.get("trend_slopes", []))
    add_factor(11, s12, f"五日均价相对前五日斜率={slope_metric:.4f}%，横截面星级={s12}", slope_metric)

    efficiency = trend_efficiency_metric(rows)
    s13 = cross_sectional_stars(efficiency, context.get("trend_efficiencies", []))
    add_factor(12, s13, f"10日净位移/价格路径={efficiency:.4f}，横截面星级={s13}", efficiency)

    segment = fnum(item.get("segment"))
    wave = fnum(item.get("wave"))
    wave_valid = wave is not None and segment is not None and 0 <= wave <= 100 and 0 <= segment <= 80
    s14 = (
        5.0 if wave_valid and 20 <= segment <= 65 and 20 <= wave <= 85 and wave >= segment
        else 3.5 if wave_valid and 10 <= segment <= 70 and 10 <= wave <= 90
        else 1.5 if wave_valid
        else 0.0
    )
    add_factor(13, s14, f"波={wave}，段={segment}", None if not wave_valid else {"wave": wave, "segment": segment}, wave_valid)

    downside = (float(last["close"]) / trend - 1) * 100 if trend is not None and trend > 0 else None
    s15 = 5.0 if downside is not None and 0 <= downside <= 8 else 4.0 if downside is not None and 0 <= downside <= 12 else 2.0 if downside is not None and 0 <= downside <= 18 else 0.0
    add_factor(14, s15, f"主趋势线={trend}，乖离={None if downside is None else round(downside,2)}%", downside, downside is not None)

    consistency = price_volume_consistency(rows)
    s16 = 5.0 if consistency >= 0.70 else 4.0 if consistency >= 0.55 else 3.0 if consistency >= 0.40 else 1.5 if consistency >= 0.25 else 0.0
    add_factor(15, s16, f"近10日价量同向比例={consistency:.2%}", consistency)

    institution_complete = None not in (inst_in, inst_out, big_order, large_in, retail_in)
    lhb_hits = item.get("lhb_hits") or []
    capital_checks = [hot_strength > 0, inst_strength > 0, institution_complete and big_order > 0, institution_complete and large_in > 0, institution_complete and retail_in < 0, bool(lhb_hits)]
    s17 = sum(capital_checks) / len(capital_checks) * 5.0
    add_factor(16, s17, f"游资/机构/大单/大户/散户/LHB合力={capital_checks}", sum(capital_checks), institution_complete)

    catalyst_hits = item.get("catalyst_hits") or []
    add_factor(17, 5.0 if catalyst_hits else 0.0, catalyst_hits[0]["keywords"] if catalyst_hits else "候选资讯未取得可核验短线催化，本项0分", bool(catalyst_hits), int(item.get("candidate_text_source_count") or 0) > 0)

    s19 = market_breadth_stars(macro)
    breadth_denominator = int(macro.get("advancers") or 0) + int(macro.get("decliners") or 0)
    breadth = int(macro.get("advancers") or 0) / breadth_denominator if breadth_denominator else 0.0
    add_factor(18, s19, f"上涨/下跌={macro.get('advancers')}/{macro.get('decliners')}，市场广度={breadth:.2%}", breadth, breadth_denominator > 0)

    s20 = limit_up_ecology_stars(macro)
    market_count = int(macro.get("market_count") or 0)
    limit_density = int(macro.get("limit_up_count") or 0) / market_count if market_count else 0.0
    add_factor(19, s20, f"涨停数/市场数={macro.get('limit_up_count')}/{macro.get('market_count')}，涨停密度={limit_density:.2%}", limit_density, market_count > 0)

    s21 = cross_sectional_stars(theme_metric, context.get("theme_strengths", []))
    add_factor(20, s21, f"主概念={winning_concept}，其他候选共振={peer_strength}，覆盖率={peer_ratio:.2%}，主题强度={theme_metric:.4f}，横截面星级={s21}", theme_metric, bool(item.get("concepts")))

    cohorts = macro.get("market_return_cohorts") if isinstance(macro.get("market_return_cohorts"), dict) else {}
    return_values = {
        "1d": fnum(item.get("pct")),
        "3d": fnum(item.get("recent_gain_3d_pct")),
        "5d": fnum(item.get("recent_gain_5d_pct")),
        "10d": fnum(item.get("recent_gain_10d_pct")),
    }
    market_percentiles = {
        horizon: percentile_rank(value, cohorts.get(horizon, []))
        for horizon, value in return_values.items()
    }
    market_relative = 0.15 * market_percentiles["1d"] + 0.35 * market_percentiles["3d"] + 0.30 * market_percentiles["5d"] + 0.20 * market_percentiles["10d"]
    market_relative_available = all(isinstance(cohorts.get(horizon), list) and cohorts[horizon] for horizon in return_values)
    s22 = percentile_stars(market_relative) if market_relative_available else 0.0
    add_factor(21, s22, f"全市场1/3/5/10日分位={market_percentiles}，加权分位={market_relative:.4f}", market_relative, market_relative_available)

    amount = float(last["amount"])
    s23 = cross_sectional_stars(amount, context.get("amounts", []))
    add_factor(22, s23, f"成交额={amount/100000000:.2f}亿元，横截面星级={s23}", amount)

    recovery_pct = (float(last["close"]) - float(last["low"])) / previous_close * 100 if previous_close > 0 else 0.0
    gap_pct = (float(last["open"]) / previous_close - 1) * 100 if previous_close > 0 else 0.0
    accessible = not bool(item.get("is_one_price"))
    s24 = 5.0 if accessible and 1 <= recovery_pct <= 10 and gap_pct <= 7 else 4.0 if accessible and 0.3 <= recovery_pct <= 14 and gap_pct <= 9 else 2.0 if accessible and recovery_pct <= 16 else 0.0
    add_factor(23, s24, f"一字={not accessible}，日内低点回收={recovery_pct:.2f}%，开盘缺口={gap_pct:.2f}%", recovery_pct, previous_close > 0)

    liquidity_stability = liquidity_stability_metric(rows)
    s25 = cross_sectional_stars(liquidity_stability, context.get("liquidity_stabilities", []))
    add_factor(24, s25, f"20日成交额稳定指标={liquidity_stability:.4f}，横截面星级={s25}", liquidity_stability)

    atr10 = atr_percent(rows)
    volatility_quality = volatility_quality_metric(rows)
    s26 = cross_sectional_stars(volatility_quality, context.get("volatility_qualities", []))
    add_factor(25, s26, f"ATR10/收盘={atr10:.2f}%，以5%为适中中心的波动质量={volatility_quality:.4f}，横截面星级={s26}", volatility_quality)

    hist = macd_hist(rows)
    divergence = macd_bearish_divergence(closes, hist)
    dealer_exit = exit_signal_active(last_value(big, "OUTPUT6"))
    high_wave_divergence = wave is not None and segment is not None and wave >= 85 and abs(wave - segment) <= 5
    wave_weakening = wave is not None and segment is not None and wave < segment and not high_wave_divergence
    amplitude = (float(last["high"]) - float(last["low"])) / float(last.get("prev_close") or rows[-2]["close"] or 1.0) * 100 if len(rows) >= 2 else 0.0
    fund_support = hot_strength > 0 or inst_strength > 0
    risks = [
        {"name": RISK_NAMES[0], "deduction": 2 if dealer_exit else 0, "evidence": f"大牛线庄出信号={last_value(big, 'OUTPUT6')}"},
        {"name": RISK_NAMES[1], "deduction": 2 if high_wave_divergence else 0, "evidence": f"波/段={wave}/{segment}"},
        {"name": RISK_NAMES[2], "deduction": 2 if wave_weakening else 0, "evidence": f"波/段={wave}/{segment}"},
        {"name": RISK_NAMES[3], "deduction": 2 if inst_in is not None and inst_out is not None and inst_out > inst_in and inst_out > 0 else 0, "evidence": f"机构进/出={inst_in}/{inst_out}"},
        {"name": RISK_NAMES[4], "deduction": 2 if buyer is not None and buyer < 0 else 0, "evidence": f"买方意向={buyer}"},
        {"name": RISK_NAMES[5], "deduction": 3 if trend is not None and last["close"] < trend else 0, "evidence": f"收盘={last['close']}，主趋势线={trend}"},
        {"name": RISK_NAMES[6], "deduction": 2 if vol_ratio > 3.5 and amplitude >= 8 else 0, "evidence": f"较前二十日量比={vol_ratio:.2f}，振幅={amplitude:.2f}%"},
        {"name": RISK_NAMES[7], "deduction": 3 if item.get("major_risk_hits") else 0, "evidence": item["major_risk_hits"][0]["keywords"] if item.get("major_risk_hits") else "候选资讯未命中软性重大风险词"},
        {"name": RISK_NAMES[8], "deduction": 3 if wave is not None and wave >= 80 and not fund_support else 0, "evidence": f"波={wave}，游资/机构承接={fund_support}"},
        {"name": RISK_NAMES[9], "deduction": 2 if item.get("reduction_hits") else 0, "evidence": item["reduction_hits"][0]["keywords"] if item.get("reduction_hits") else "候选资讯未命中大额减持解禁词"},
        {"name": RISK_NAMES[10], "deduction": 2 if ((item.get("recent_gain_3d_pct") or 0) > 25 or (item.get("recent_gain_5d_pct") or 0) > 35) and not (ignition or fund_support) else 0, "evidence": f"近3/5/10日={item.get('recent_gain_3d_pct')}/{item.get('recent_gain_5d_pct')}/{item.get('recent_gain_10d_pct')}%，启动={ignition}，资金承接={fund_support}"},
        {"name": RISK_NAMES[11], "deduction": 2 if segment is not None and segment >= 70 else 0, "evidence": f"段={segment}"},
        {"name": RISK_NAMES[12], "deduction": 1 if pressure20 > 0 and pressure20 * 0.98 <= float(last["close"]) <= pressure20 * 1.005 else 0, "evidence": f"收盘={last['close']}，前二十日压力={pressure20}"},
        {"name": RISK_NAMES[13], "deduction": 2 if divergence else 0, "evidence": f"日线量价指标背离={divergence}"},
        {"name": RISK_NAMES[14], "deduction": 1 if ma60 is not None and last["close"] < ma60 and item.get("pct", 0) >= 9.5 else 0, "evidence": f"收盘={last['close']}，六十日均线={None if ma60 is None else round(ma60,2)}"},
    ]
    positive_score = round(sum(row["score"] for row in dimensions), 2)
    risk_deduction = int(sum(row["deduction"] for row in risks))
    final_score = round(max(0.0, positive_score - risk_deduction), 2)
    axis_scores = {}
    for axis, maximum in AXIS_MAX_SCORES.items():
        raw = round(sum(row["score"] for row in dimensions if row["axis"] == axis), 2)
        axis_scores[axis] = {"raw": raw, "max": maximum, "normalized": round(raw / maximum * 100, 2)}
    explosion = axis_scores["爆发力"]["normalized"]
    persistence = axis_scores["持续性"]["normalized"]
    style_profile = (
        "爆发延续型" if explosion >= 75 and persistence >= 70
        else "爆发脉冲型" if explosion >= 75
        else "趋势接力型" if persistence >= 70
        else "观察型"
    )
    available_weight = sum(row["weight"] for row in dimensions if row["available"])
    score_coverage = round(available_weight, 2)
    leaders = sorted(dimensions, key=lambda row: row["score"] / row["weight"], reverse=True)[:3]
    triggered = [row for row in risks if row["deduction"] > 0]
    conclusion = f"{style_profile}：爆发力{explosion}，持续性{persistence}；主要得分来自{'、'.join(row['name'] for row in leaders)}；风险扣分来自{'、'.join(row['name'] for row in triggered) if triggered else '零项触发'}。"
    fallback_trend = trend if trend is not None else ma20
    invalidation = f"收盘跌破主趋势线{fallback_trend if fallback_trend is not None else '缺失'}元，或机构大单出转强，或飞龙段升至80以上时取消观察资格。"
    audit_inputs = {
        "rows": rows,
        "formula": {
            "big": {key: last_value(big, key) for key in ("主趋势线", "EMA9", "EMA10", "EMA11", "OUTPUT3", "OUTPUT4", "OUTPUT5", "OUTPUT6", "OUTPUT9")},
            "fly": {key: last_value(fly, key) for key in ("波", "段", "OUTPUT3", "OUTPUT4", "OUTPUT5", "OUTPUT6")},
            "hot": {key: last_value(hot, key) for key in ("买方意向", "AAA", "DDD", "OUTPUT4")},
            "institution": {key: last_value(inst, key) for key in ("机构大单进", "机构大单出", "大单动向", "大户大单进", "散户资金进")},
            "dealer": {"控盘度": last_value(dealer, "控盘度")},
        },
        "evidence": {
            "risk": bool(item.get("risk_hits")),
            "major_risk": bool(item.get("major_risk_hits")),
            "reduction": bool(item.get("reduction_hits")),
            "fundamental": bool(item.get("fundamental_hits")),
            "financial_safety": bool(item.get("financial_safety_hits")),
            "catalyst": bool(catalyst_hits),
            "lhb": bool(lhb_hits),
            "candidate_text_source_count": int(item.get("candidate_text_source_count") or 0),
        },
        "concepts": list(item.get("concepts", [])),
        "state": {
            "name": item.get("name"),
            "market": item.get("market"),
            "code": item.get("code"),
            "limit_price": fnum(item.get("limit_price")),
            "is_limit_up": bool(item.get("is_limit_up")),
            "is_one_price": bool(item.get("is_one_price")),
            "one_price_streak": int(item.get("one_price_streak") or 0),
            "pct": fnum(item.get("pct"), 0.0),
            "recent_gain_3d_pct": fnum(item.get("recent_gain_3d_pct")),
            "recent_gain_5d_pct": fnum(item.get("recent_gain_5d_pct")),
            "recent_gain_10d_pct": fnum(item.get("recent_gain_10d_pct")),
            "universe_size": population,
            "short_fund_strength": round(hot_strength, 8),
            "theme_strength": round(theme_metric, 8),
            "market_context": {
                key: macro.get(key)
                for key in ("market_count", "advancers", "decliners", "flat", "limit_up_count")
            },
            "market_percentiles": {key: round(value, 8) for key, value in market_percentiles.items()},
        },
    }
    return {
        **{key: value for key, value in item.items() if key not in {"rows", "formula_scan", "formula_fields"}},
        "latest": last["close"],
        "amount_yi": round(last["amount"] / 100000000, 4),
        "volume_ratio": round(vol_ratio, 4),
        "trend_line": trend,
        "support20": support20,
        "pressure20": pressure20,
        "formula_summary": {
            "大牛线": {"主趋势线": trend, "均线9": ema9, "均线10": ema10, "均线11": ema11},
            "飞龙在天": {"波": wave, "段": segment, "启动信号": item.get("ignition")},
            "游资资金": {"买方意向": buyer, "甲值": aaa, "丁值": ddd},
            "机构资金": {"机构大单进": inst_in, "机构大单出": inst_out, "大单动向": big_order},
            "庄家资金": {"控盘度": fnum(last_value(dealer, "控盘度"))},
        },
        "audit_inputs": audit_inputs,
        "positive_dimensions": dimensions,
        "factor_count": len(dimensions),
        "axis_scores": axis_scores,
        "style_profile": style_profile,
        "score_coverage": score_coverage,
        "risks": risks,
        "positive_score": positive_score,
        "risk_deduction": risk_deduction,
        "final_score": final_score,
        "score_contract": {
            "version": SCORE_CONTRACT_VERSION,
            "global_contract_path": str(GLOBAL_SCORE_CONTRACT),
            "global_contract_sha256": GLOBAL_SCORE_CONTRACT_SHA256,
            "scale": 100,
            "factor_count": len(POSITIVE_DIMENSIONS),
            "axis_weights": AXIS_MAX_SCORES,
            "positive_weight_total": round(sum(weight for _name, weight in POSITIVE_DIMENSIONS), 2),
            "missing_evidence_policy": "zero_without_renormalization",
            "risk_policy": "explicit_deductions_after_hard_exclusions",
            "fundamental_positive_weight": 0,
            "model_purpose": "short_term_breakout_and_persistence",
            "factor_role_policy": "pool_and_regime_factors_calibrate_absolute_context_but_do_not_claim_cross_sectional_ranking_power",
            "tie_break": "final_score_desc,positive_score_desc,amount_yi_desc,code_asc",
        },
        "conclusion": conclusion,
        "invalidation": invalidation,
    }


def factor_diagnostics(ranking: list[dict[str, Any]]) -> dict[str, Any]:
    rows_by_name: dict[str, list[float]] = {name: [] for name, _weight in POSITIVE_DIMENSIONS}
    for item in ranking:
        by_name = {row.get("name"): row for row in item.get("positive_dimensions", []) if isinstance(row, dict)}
        for name, _weight in POSITIVE_DIMENSIONS:
            rows_by_name[name].append(float(by_name.get(name, {}).get("stars", 0.0)))

    factors = []
    for name, weight in POSITIVE_DIMENSIONS:
        values = rows_by_name[name]
        distinct = len({round(value, 4) for value in values})
        count = len(values)
        factors.append({
            "name": name,
            "axis": FACTOR_AXES[name],
            "role": FACTOR_ROLES[name],
            "ranking_relevant": FACTOR_ROLES[name] in RANKING_FACTOR_ROLES,
            "weight": weight,
            "sample_count": count,
            "distinct_star_count": distinct,
            "zero_rate": round(sum(value == 0 for value in values) / count, 4) if count else None,
            "full_rate": round(sum(value == 5 for value in values) / count, 4) if count else None,
            "discriminating": distinct > 1,
        })

    high_correlations = []
    if len(ranking) >= 5:
        for left_index, (left_name, _left_weight) in enumerate(POSITIVE_DIMENSIONS):
            left = rows_by_name[left_name]
            left_mean = sum(left) / len(left)
            left_var = sum((value - left_mean) ** 2 for value in left)
            if left_var <= 1e-12:
                continue
            for right_name, _right_weight in POSITIVE_DIMENSIONS[left_index + 1:]:
                right = rows_by_name[right_name]
                right_mean = sum(right) / len(right)
                right_var = sum((value - right_mean) ** 2 for value in right)
                if right_var <= 1e-12:
                    continue
                covariance = sum((lvalue - left_mean) * (rvalue - right_mean) for lvalue, rvalue in zip(left, right))
                correlation = covariance / math.sqrt(left_var * right_var)
                if abs(correlation) >= 0.85:
                    high_correlations.append({"left": left_name, "right": right_name, "pearson": round(correlation, 4)})

    ranking_factors = [row for row in factors if row["ranking_relevant"]]
    return {
        "sample_scope": "current_scored_pool_cross_section",
        "sample_count": len(ranking),
        "effective_factor_count": sum(row["discriminating"] for row in factors),
        "ranking_eligible_factor_count": len(ranking_factors),
        "ranking_effective_factor_count": sum(row["discriminating"] for row in ranking_factors),
        "context_factor_count": len(factors) - len(ranking_factors),
        "dead_factors": [row["name"] for row in factors if row["sample_count"] and row["zero_rate"] == 1.0],
        "saturated_factors": [row["name"] for row in factors if row["sample_count"] and row["full_rate"] is not None and row["full_rate"] >= 0.80],
        "ranking_dead_factors": [row["name"] for row in ranking_factors if row["sample_count"] and row["zero_rate"] == 1.0],
        "ranking_saturated_factors": [row["name"] for row in ranking_factors if row["sample_count"] and row["full_rate"] is not None and row["full_rate"] >= 0.80],
        "high_correlation_pairs": high_correlations,
        "factors": factors,
        "interpretation": "个股排序区分力只统计candidate_ranking/candidate_evidence；pool_confirmation与market_regime仅校准绝对环境。该诊断不等同前瞻预测有效性。",
    }


def clean_for_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: clean_for_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean_for_json(item) for item in value]
    if isinstance(value, float):
        return round(value, 4) if math.isfinite(value) else None
    if isinstance(value, Path):
        return str(value)
    return value


NAVY = "17365D"
GREEN = "1F6B5B"
GOLD = "B7791F"
LIGHT_BLUE = "EAF0F7"
LIGHT_GRAY = "F3F5F7"
WHITE = "FFFFFF"
TEXT = "243447"


def _set_cell_shading(cell: Any, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def _set_cell_margins(cell: Any, top: int = 60, start: int = 80, bottom: int = 60, end: int = 80) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for edge, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def _set_repeat_table_header(row: Any) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def _set_font(run: Any, size: float, bold: bool = False, color: str = TEXT) -> None:
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def _display(value: Any) -> str:
    if value is True:
        return "是"
    if value is False:
        return "否"
    return str(value).replace("True", "是").replace("False", "否").replace("CXO", "医药研发服务")


def _add_paragraph(doc: Document, text: str, size: float = 10.5, bold: bool = False,
                   color: str = TEXT, align: int = WD_ALIGN_PARAGRAPH.LEFT,
                   before: float = 0, after: float = 5, keep_next: bool = False) -> Any:
    paragraph = doc.add_paragraph()
    paragraph.alignment = align
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.line_spacing = 1.18
    paragraph.paragraph_format.keep_with_next = keep_next
    run = paragraph.add_run(str(text))
    _set_font(run, size, bold, color)
    return paragraph


def _add_heading(doc: Document, text: str, level: int = 1) -> Any:
    if level == 1:
        return _add_paragraph(doc, text, 15, True, NAVY, before=10, after=6, keep_next=True)
    return _add_paragraph(doc, text, 12, True, GREEN, before=8, after=4, keep_next=True)


def _add_table(doc: Document, headers: list[str], rows: list[list[Any]], widths_cm: list[float],
               font_size: float = 8.5, accent: str = NAVY) -> Any:
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = "Table Grid"
    header = table.rows[0]
    _set_repeat_table_header(header)
    for index, label in enumerate(headers):
        cell = header.cells[index]
        cell.width = Cm(widths_cm[index])
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        _set_cell_shading(cell, accent)
        _set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        _set_font(p.add_run(_display(label)), font_size, True, WHITE)
    for row_index, values in enumerate(rows):
        row = table.add_row()
        row.height = None
        for col_index, value in enumerate(values):
            cell = row.cells[col_index]
            cell.width = Cm(widths_cm[col_index])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            _set_cell_margins(cell)
            if row_index % 2:
                _set_cell_shading(cell, LIGHT_GRAY)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_index < len(values) - 1 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.05
            _set_font(p.add_run(_display(value)), font_size, False, TEXT)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def _remove_template_body_after_risk_poster(doc: Document) -> None:
    body = doc._element.body
    children = list(body)
    poster_index = next((i for i, child in enumerate(children) if child.tag == qn("w:tbl")), None)
    if poster_index is None:
        raise RuntimeError("fixed template risk poster table not found")
    for child in children[poster_index + 1:]:
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def _add_page_number(section: Any) -> None:
    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("第 ")
    _set_font(run, 8, False, "6B7280")
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_begin, instr, fld_end])
    run2 = paragraph.add_run(" 页")
    _set_font(run2, 8, False, "6B7280")


def render_report_from_json(json_path: Path, docx_path: Path) -> Path:
    if not REPORT_TEMPLATE.exists():
        raise FileNotFoundError(REPORT_TEMPLATE)
    template_hash = hashlib.sha256(REPORT_TEMPLATE.read_bytes()).hexdigest().upper()
    if template_hash != REPORT_TEMPLATE_SHA256:
        raise RuntimeError(f"fixed template hash mismatch: {template_hash}")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    checks = data.get("validation", {})
    top5 = data.get("top5", [])
    ranking = data.get("ranking", [])
    candidate_pool = data.get("candidate_pool", {})
    result_count = data.get("result_count")
    expected_selection_status = (
        "TOP5" if result_count == 5 else "NO_CANDIDATES" if result_count == 0 else "PARTIAL"
    )
    required = [
        "complete_scan", "result_count_matches", "result_count_lte_target",
        "scarcity_disclosed", "all_top5_hard_gates", "all_top5_26_factors",
        "all_top5_15_risks", "all_top5_7_hard_exclusions",
        "all_top5_required_formulas", "all_top5_segment_le_80", "market_scope_complete", "current_trade_date",
    ]
    if (
        data.get("status") != "CLEAN_PASS"
        or not isinstance(top5, list)
        or not isinstance(result_count, int)
        or result_count != len(top5)
        or not 0 <= result_count <= 5
        or checks.get("top5_count") != result_count
        or data.get("selection_status") != expected_selection_status
        or not all(checks.get(key) for key in required)
    ):
        raise RuntimeError("report data gate blocked")
    if docx_path.exists():
        docx_path.unlink()
    shutil.copy2(REPORT_TEMPLATE, docx_path)
    doc = Document(docx_path)
    _remove_template_body_after_risk_poster(doc)
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.25)
    section.bottom_margin = Cm(1.25)
    section.left_margin = Cm(1.35)
    section.right_margin = Cm(1.35)
    section.header_distance = Cm(0.55)
    section.footer_distance = Cm(0.55)
    _add_page_number(section)
    normal = doc.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(10.5)

    _add_paragraph(doc, "本页为教学案例风险提示，后续内容依据当前交易日数据计算。", 9, False, "6B7280", WD_ALIGN_PARAGRAPH.CENTER, after=0)
    doc.add_page_break()
    trade_date = datetime.strptime(data["trade_date"], "%Y%m%d").strftime("%Y-%m-%d")
    pool_name = str(candidate_pool.get("name") or "当日真实涨停池")
    _add_paragraph(doc, f"A股短线强势股26因子｜{pool_name}评分结果", 21, True, NAVY, WD_ALIGN_PARAGRAPH.CENTER, after=4)
    generated_time = datetime.fromisoformat(data["generated_at"]).strftime("%Y-%m-%d %H:%M:%S")
    _add_paragraph(doc, f"交易日 {trade_date}｜生成时间 {generated_time}", 9.5, False, "6B7280", WD_ALIGN_PARAGRAPH.CENTER, after=10)

    _add_heading(doc, "一、当日排序结论")
    if top5:
        lead = top5[0]
        last_item = top5[-1]
        score_gap = round(float(lead["final_score"]) - float(last_item["final_score"]), 2)
        lead_dims = "、".join(row["name"] for row in sorted(lead["positive_dimensions"], key=lambda row: row["score"], reverse=True)[:3])
        lead_risks = "、".join(row["name"] for row in lead["risks"] if int(row["deduction"]) > 0) or "无风险扣分项"
        _add_paragraph(
            doc,
            f"结论：截至{trade_date}，共{result_count}只股票通过全部硬闸，首位为{lead['name']}（{lead['code']}），最终得分{lead['final_score']}，较本轮末位{last_item['final_score']}高{score_gap}分。"
            f"依据：候选池{data['pool_candidate_count']}只、完整评分{data['scored_count']}只、当日全市场真实涨停{data['raw_limit_up_count']}只；首位爆发力{lead['axis_scores']['爆发力']['normalized']}、持续性{lead['axis_scores']['持续性']['normalized']}、正向得分{lead['positive_score']}、风险扣分{lead['risk_deduction']}，主要得分项为{lead_dims}，扣分项为{lead_risks}。"
            f"反证：{lead['invalidation']}",
            11,
            True,
        )
    else:
        _add_paragraph(
            doc,
            f"结论：截至{trade_date}，本轮无候选。候选池{data['pool_candidate_count']}只已完整扫描，但没有股票通过全部硬闸；未补足或伪造名单。",
            11,
            True,
        )
    _add_heading(doc, "二、市场与筛选概览")
    macro = data["macro"]
    overview_rows = [
        ["本地日线股票", macro["market_count"], "上涨", macro["advancers"], "下跌", macro["decliners"]],
        ["平盘", macro["flat"], "成交额（亿元）", macro["total_amount_yi"], "全市场真实涨停", data["raw_limit_up_count"]],
        ["前置硬闸后", data["preliminary_count"], "完整评分", data["scored_count"], "排除", data["excluded_count"]],
    ]
    _add_table(doc, ["指标", "数值", "指标", "数值", "指标", "数值"], overview_rows, [3.0, 2.0, 3.0, 2.0, 3.0, 2.0], 9)
    if candidate_pool.get("mode") == "tdx_custom_block":
        _add_paragraph(doc, f"候选池来自通达信自定义板块“{pool_name}”（{candidate_pool.get('code')}），共{candidate_pool.get('member_count')}只；全部成员均核验至当前交易日。", 9.5, False, "6B7280")
    else:
        _add_paragraph(doc, "候选池由本地日线全量复算得出，过期的涨停池板块文件未参与当日排名。", 9.5, False, "6B7280")

    _add_heading(doc, "三、通过硬闸的全量评分排名")
    top_rows = [[item["rank"], item["code"], item["name"], item["latest"], f"{item['pct']}%", item["axis_scores"]["爆发力"]["normalized"], item["axis_scores"]["持续性"]["normalized"], item["risk_deduction"], item["final_score"]] for item in ranking]
    _add_table(doc, ["序", "代码", "名称", "现价", "涨幅", "爆发", "持续", "扣分", "最终"], top_rows, [0.8, 2.0, 2.4, 1.7, 1.8, 1.6, 1.6, 1.4, 1.6], 8.2)

    _add_heading(doc, "四、五公式摘要")
    formula_rows = []
    for item in data["top5"]:
        summary = item["formula_summary"]
        formula_rows.append([item["name"], summary["大牛线"]["主趋势线"], summary["飞龙在天"]["波"], summary["飞龙在天"]["段"], summary["游资资金"]["买方意向"], f"{summary['机构资金']['机构大单进']}/{summary['机构资金']['机构大单出']}", summary["庄家资金"]["控盘度"]])
    _add_table(doc, ["名称", "主趋势线", "飞龙波", "飞龙段", "买方意向", "机构进/出", "控盘度"], formula_rows, [2.5, 2.2, 2.0, 2.0, 2.2, 2.7, 2.0], 8.3)

    _add_heading(doc, "五、逐股四轴26因子、十五风险与七条硬闸")
    for item_index, item in enumerate(data["top5"]):
        _add_heading(doc, f"{item['rank']}｜{item['name']}（{item['code']}）｜最终 {item['final_score']}", 2)
        dynamic_dims = "、".join(row["name"] for row in sorted(item["positive_dimensions"], key=lambda row: row["score"], reverse=True)[:3])
        dynamic_risks = "、".join(row["name"] for row in item["risks"] if int(row["deduction"]) > 0) or "无风险扣分项"
        _add_paragraph(doc, f"类型：{item['style_profile']}；爆发力={item['axis_scores']['爆发力']['normalized']}，持续性={item['axis_scores']['持续性']['normalized']}，市场协同={item['axis_scores']['市场协同']['normalized']}，可交易性={item['axis_scores']['可交易性']['normalized']}；得分主因：{dynamic_dims}；扣分项：{dynamic_risks}。", 10.5, True)
        _add_paragraph(doc, item["invalidation"], 9.5, False, "6B7280")
        _add_paragraph(doc, "四轴26因子正向评分", 10.5, True, GREEN, before=4, after=3, keep_next=True)
        dim_rows = [[row["axis"], row["name"], row["weight"], row["stars"], row["score"], row["evidence"]] for row in item["positive_dimensions"]]
        _add_table(doc, ["轴", "因子", "权重", "星级", "得分", "证据"], dim_rows, [1.5, 3.0, 1.0, 1.0, 1.0, 9.2], 7.5, GREEN)
        _add_paragraph(doc, "十五项风险扣分", 10.5, True, GOLD, before=4, after=3, keep_next=True)
        risk_rows = [[row["name"], row["deduction"], row["evidence"]] for row in item["risks"]]
        _add_table(doc, ["风险项", "扣分", "证据"], risk_rows, [4.2, 1.4, 11.1], 7.8, GOLD)
        _add_paragraph(doc, "七条硬剔除", 10.5, True, NAVY, before=4, after=3, keep_next=True)
        hard_rows = [[row["name"], "通过" if row["passed"] else "剔除", row["evidence"]] for row in item["hard_exclusions"]]
        _add_table(doc, ["硬闸", "状态", "证据"], hard_rows, [5.0, 1.5, 10.2], 7.8)

    _add_heading(doc, "六、排除记录")
    excluded_rows = []
    for row in data["excluded"]:
        reason = "；".join(f"{reason_row['name']}：{reason_row['evidence']}" for reason_row in row["reasons"])
        excluded_rows.append([row["code"], row["name"], row["stage"], reason])
    _add_table(doc, ["代码", "名称", "阶段", "原因"], excluded_rows, [1.8, 2.2, 2.8, 10.0], 7.8)
    _add_heading(doc, "七、因子质量与前瞻验证边界")
    diagnostics = data.get("factor_diagnostics", {})
    registry = data.get("factor_registry", {})
    _add_paragraph(
        doc,
        f"已启用可复算因子{registry.get('enabled_count', 0)}项，待接入时点数据因子{registry.get('pending_count', 0)}项，主动拒绝价值偏置或重复因子{registry.get('rejected_count', 0)}项。"
        f"本期个股排序候选因子{diagnostics.get('ranking_eligible_factor_count', 0)}项，其中有效区分{diagnostics.get('ranking_effective_factor_count', 0)}项；环境/候选池校准因子{diagnostics.get('context_factor_count', 0)}项；排序全零因子：{'、'.join(diagnostics.get('ranking_dead_factors', [])) or '无'}；排序高饱和因子：{'、'.join(diagnostics.get('ranking_saturated_factors', [])) or '无'}。",
        9.5,
    )
    _add_paragraph(doc, "前瞻预测状态：未验证。必须按下一交易日开盘进入、未来1/3/5日收益及MFE/MAE做滚动样本外检验；本报告只证明当期计算和证据可复算。", 9.5, True, GOLD)

    _add_heading(doc, "八、数据与使用边界")
    if top5:
        formula_boundary = f"通过硬闸的{result_count}只股票，其必需公式均返回有效结果。"
    else:
        formula_boundary = "本轮没有股票通过全部硬闸，因此没有补足名单或虚构公式结果。"
    _add_paragraph(doc, f"日线范围：D盘通达信最新交易日 {trade_date}；股票数 {macro['market_count']}；{formula_boundary}", 10)
    _add_paragraph(doc, "结果用于教学案例与规则训练，不作为股票推荐，不构成投资建议，不作为买卖依据。", 10, True, NAVY)
    doc.save(docx_path)
    return docx_path


def execute(outdir: Path, candidate_block: str | None = None, generate_formatted_artifacts: bool = True) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    started = now_cn()
    print("STAGE names", flush=True)
    names = load_names()
    print(f"STAGE names_done count={len(names)}", flush=True)
    print("STAGE market_scan", flush=True)
    if candidate_block:
        candidate_pool = resolve_candidate_block(candidate_block)
        member_keys = {
            (item["market"], item["code"])
            for item in candidate_pool["members"]
        }
        trade_date, candidates, macro = scan_market(names, member_keys)
    else:
        trade_date, candidates, macro = scan_market(names)
        candidate_pool = {
            "mode": "current_limit_up",
            "name": "当日真实涨停池",
            "code": None,
            "path": None,
            "sha256": None,
            "member_count": len(candidates),
            "members": [
                {"market": item["market"], "code": item["code"]}
                for item in candidates
            ],
        }
    print(f"STAGE market_done trade_date={trade_date} pool={len(candidates)} limit_up={macro['limit_up_count']}", flush=True)
    expected_date = expected_completed_trade_date(started)
    if trade_date != expected_date:
        raise RuntimeError(f"TDX latest trade date is stale: {trade_date}, expected completed session {expected_date}")
    print("STAGE local_news", flush=True)
    corpus = collect_local_text()
    print(f"STAGE local_news_done files={len(corpus)}", flush=True)
    prelim: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for candidate in candidates:
        checks = preliminary_hard(candidate)
        if all(item["passed"] for item in checks):
            prelim.append(candidate)
        else:
            excluded.append({"code": candidate["code"], "name": candidate["name"], "stage": "前置硬剔除", "reasons": [item for item in checks if not item["passed"]]})
    print(f"STAGE preliminary_done passed={len(prelim)} excluded={len(excluded)}", flush=True)
    enriched: list[dict[str, Any]] = []
    for index, candidate in enumerate(prelim, 1):
        print(f"FORMULA_SCAN {index}/{len(prelim)} {candidate['code']} {candidate['name']}", flush=True)
        item = enrich_candidate(candidate, corpus)
        if item["passed_hard_gate"]:
            enriched.append(item)
        else:
            formula_failed = [name for name, ok in item["formula_required_ok"].items() if not ok]
            excluded.append({
                "code": item["code"],
                "name": item["name"],
                "stage": "公式与完整硬剔除",
                "reasons": [row for row in item["hard_exclusions"] if not row["passed"]] + ([{"name": "四个必需公式字段", "evidence": "、".join(formula_failed)}] if formula_failed else []),
            })
    concept_frequency: Counter[str] = Counter(token for item in enriched for token in item["concepts"])
    scoring_context = build_scoring_context(enriched, concept_frequency, macro)
    scored = [score_candidate(item, concept_frequency, len(enriched), scoring_context) for item in enriched]
    scored.sort(key=lambda item: (-item["final_score"], -item["positive_score"], -item["amount_yi"], item["code"]))
    for rank, item in enumerate(scored, 1):
        item["rank"] = rank
    ranking = scored
    top5 = scored[:5]
    result_count = len(top5)
    selection_status = (
        "TOP5" if result_count == 5 else "NO_CANDIDATES" if result_count == 0 else "PARTIAL"
    )
    run_id = started.strftime("%Y%m%d-%H%M%S")
    json_path = outdir / "a-share-15d-selection-result.json"
    csv_path = outdir / "a-share-15d-selection-result.csv"
    result = {
        "status": "CLEAN_PASS",
        "selection_status": selection_status,
        "target_count": 5,
        "result_count": result_count,
        "run_id": run_id,
        "generated_at": started.isoformat(timespec="seconds"),
        "trade_date": trade_date,
        "source": {
            "market": "C:\\new_tdx_mock\\vipdoc 全量最新日线复算",
            "names": [str(path) for _, path in TNF_FILES],
            "formulas": str(TDX_ENTRY),
            "score_contract": str(GLOBAL_SCORE_CONTRACT),
            "score_contract_sha256": GLOBAL_SCORE_CONTRACT_SHA256,
            "template_sha256": "EC71F04176CB13FBF56AC73D60EE6701CCC71AB877C457D365E130A1795993F5",
            "stale_ztc_not_used": True,
        },
        "candidate_pool": candidate_pool,
        "macro": macro,
        "pool_candidate_count": len(candidates),
        "raw_limit_up_count": macro["limit_up_count"],
        "preliminary_count": len(prelim),
        "scored_count": len(scored),
        "excluded_count": len(excluded),
        "ranking_count": len(ranking),
        "ranking": ranking,
        "top5": top5,
        "excluded": excluded,
        "factor_registry": {
            "contract_path": str(GLOBAL_SCORE_CONTRACT),
            "contract_sha256": GLOBAL_SCORE_CONTRACT_SHA256,
            "contract_version": SCORE_CONTRACT_VERSION,
            "enabled": [
                {
                    "name": name,
                    "axis": FACTOR_AXES[name],
                    "role": FACTOR_ROLES[name],
                    "ranking_relevant": FACTOR_ROLES[name] in RANKING_FACTOR_ROLES,
                    "weight": weight,
                    "status": "ENABLED_REPRODUCIBLE",
                }
                for name, weight in POSITIVE_DIMENSIONS
            ],
            "pending_data": PENDING_FACTORS,
            "rejected": REJECTED_FACTORS,
            "enabled_count": len(POSITIVE_DIMENSIONS),
            "pending_count": len(PENDING_FACTORS),
            "rejected_count": len(REJECTED_FACTORS),
        },
        "factor_diagnostics": factor_diagnostics(ranking),
        "evaluation_contract": {
            "decision_time": "trade_date_after_close",
            "entry_assumption": "next_trade_day_open",
            "forward_horizons": [1, 3, 5],
            "labels": ["close_return", "market_excess_return", "maximum_favorable_excursion", "maximum_adverse_excursion"],
            "walk_forward_required": True,
            "lookahead_policy": "features_and_evidence_timestamp_at_or_before_decision_time",
        },
        "predictive_validation": {
            "status": "UNVERIFIED_REQUIRES_POINT_IN_TIME_FORWARD_LABELS",
            "reason": "当前全市场运行证明计算、证据和排序可复算，不代表已经证明未来1/3/5日收益预测能力。",
        },
        "validation": {
            "top5_count": len(top5),
            "complete_scan": macro.get("scan_coverage", {}).get("complete") is True,
            "result_count_matches": result_count == len(top5),
            "result_count_lte_target": result_count <= 5,
            "scarcity_disclosed": (result_count < 5) == (selection_status != "TOP5"),
            "all_top5_hard_gates": all(item["passed_hard_gate"] for item in top5),
            "all_top5_26_factors": all(len(item["positive_dimensions"]) == 26 for item in top5),
            "all_top5_15_risks": all(len(item["risks"]) == 15 for item in top5),
            "all_top5_7_hard_exclusions": all(len(item["hard_exclusions"]) == 7 for item in top5),
            "all_top5_required_formulas": all(all(item["formula_required_ok"].values()) for item in top5),
            "all_top5_segment_le_80": all(item["segment"] is not None and item["segment"] <= 80 for item in top5),
            "all_top5_score_math": all(not validate_candidate_score(item, index, concept_frequency, scoring_context) for index, item in enumerate(top5, 1)),
            "ranking_consistent": top5 == sorted(top5, key=lambda item: (-item["final_score"], -item["positive_score"], -item["amount_yi"], item["code"])),
            "score_contract_v6": all(item.get("score_contract", {}).get("version") == SCORE_CONTRACT_VERSION for item in top5),
            "ranking_count_matches": len(ranking) == len(scored),
            "all_ranked_hard_gates": all(item["passed_hard_gate"] for item in ranking),
            "all_ranked_26_factors": all(len(item["positive_dimensions"]) == 26 for item in ranking),
            "all_ranked_15_risks": all(len(item["risks"]) == 15 for item in ranking),
            "all_ranked_7_hard_exclusions": all(len(item["hard_exclusions"]) == 7 for item in ranking),
            "all_ranked_required_formulas": all(all(item["formula_required_ok"].values()) for item in ranking),
            "all_ranked_segment_le_80": all(item["segment"] is not None and item["segment"] <= 80 for item in ranking),
            "all_ranked_score_math": all(not validate_candidate_score(item, index, concept_frequency, scoring_context) for index, item in enumerate(ranking, 1)),
            "full_ranking_consistent": ranking == sorted(ranking, key=lambda item: (-item["final_score"], -item["positive_score"], -item["amount_yi"], item["code"])),
            "top5_is_ranking_prefix": top5 == ranking[:5],
            "pool_coverage_complete": macro.get("scan_coverage", {}).get("complete") is True and len(candidates) == candidate_pool["member_count"] and len(ranking) + len(excluded) == len(candidates),
            "market_scope_complete": set(macro.get("scan_coverage", {}).get("markets", [])) == {"SH", "SZ", "BJ"},
            "current_trade_date": trade_date == expected_date,
        },
    }
    json_path.write_text(json.dumps(clean_for_json(result), ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["排名", "代码", "名称", "现价", "涨幅", "正向得分", "风险扣分", "最终得分", "飞龙波", "飞龙段", "主趋势线", "失效条件"])
        for item in ranking:
            writer.writerow([item["rank"], item["code"], item["name"], item["latest"], item["pct"], item["positive_score"], item["risk_deduction"], item["final_score"], item["wave"], item["segment"], item["trend_line"], item["invalidation"]])
    docx_path: Path | None = None
    validation_path: Path | None = None
    if generate_formatted_artifacts:
        docx_path = outdir / "a-share-15d-selection-result.docx"
        render_report_from_json(json_path, docx_path)
        validation_path = outdir / "artifact_validation.json"
        artifact_validation = validate_artifacts(
            json_path,
            csv_path,
            docx_path,
            validation_path,
        )
        if artifact_validation["status"] != "CLEAN_PASS":
            raise RuntimeError(
                "artifact validation blocked: "
                + ",".join(artifact_validation["errors"])
            )
    print(json.dumps({"status": result["status"], "json_path": str(json_path), "csv_path": str(csv_path), "docx_path": str(docx_path) if docx_path else None, "artifact_validation_path": str(validation_path) if validation_path else None, "trade_date": trade_date, "candidate_pool": candidate_pool["name"], "pool_candidate_count": len(candidates), "raw_limit_up_count": macro["limit_up_count"], "scored_count": len(scored), "top5": [{"rank": item["rank"], "code": item["code"], "name": item["name"], "score": item["final_score"]} for item in top5]}, ensure_ascii=False, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Fixed TDX-backed A-share 15-dimension limit-up-pool Top5 selection.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--outdir")
    mode.add_argument("--render-json")
    parser.add_argument("--docx")
    parser.add_argument("--candidate-block")
    args = parser.parse_args()
    if args.render_json:
        json_path = Path(args.render_json).resolve()
        docx_path = Path(args.docx).resolve() if args.docx else json_path.with_suffix(".docx")
        result_path = render_report_from_json(json_path, docx_path)
        print(json.dumps({"status": "DOCX_SAVED", "docx_path": str(result_path), "template_path": str(REPORT_TEMPLATE), "template_sha256": REPORT_TEMPLATE_SHA256}, ensure_ascii=False, indent=2))
    else:
        execute(Path(args.outdir).resolve(), args.candidate_block)
    return 0


if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
