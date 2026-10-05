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
import math
import re
import statistics
import struct
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Iterable


TDX_ROOT = Path("C:/new_tdx_mock")
HQ_CACHE = TDX_ROOT / "T0002" / "hq_cache"
INFOHARBOR = HQ_CACHE / "infoharbor_block.dat"
NEWS_INDEX = TDX_ROOT / "T0002" / "msg_zx" / "msg_zx.idx"
APP_ROOT = Path(__file__).resolve().parents[3]
LOCAL_NEWS_SNAPSHOT = APP_ROOT / "data" / "news" / "latest.json"
TNF_FILES = {
    "SH": HQ_CACHE / "shs.tnf",
    "SZ": HQ_CACHE / "szs.tnf",
    "BJ": HQ_CACHE / "bjs.tnf",
}
DAY_DIRS = {
    "SH": TDX_ROOT / "vipdoc" / "sh" / "lday",
    "SZ": TDX_ROOT / "vipdoc" / "sz" / "lday",
    "BJ": TDX_ROOT / "vipdoc" / "bj" / "lday",
}
DAY_RECORD = struct.Struct("<IIIIIfII")
NEWS_RECORD_SIZE = 912
CN_TZ = timezone(timedelta(hours=8))

EQUITY_PREFIXES = (
    "000", "001", "002", "003", "300", "301", "600", "601", "603", "605",
    "688", "689", "830", "831", "832", "833", "834", "835", "836", "837",
    "838", "839", "870", "871", "872", "873", "874", "875", "876", "877",
    "878", "879", "880", "881", "882", "883", "884", "885", "886", "887",
    "888", "889", "890", "891", "892", "893", "894", "895", "896", "897",
    "898", "899",
)

# The mapping is intentionally explicit.  Generic market labels and event words
# do not become quality tracks merely because they are frequently mentioned.
TRACK_GROUPS: dict[str, tuple[str, ...]] = {
    "人工智能与算力": (
        "人工智能", "AI", "算力", "数据中心", "云计算", "服务器", "液冷", "CPO",
        "光通信", "光模块", "铜缆高速", "PCB", "存储芯片", "先进封装",
    ),
    "半导体自主可控": (
        "半导体", "芯片", "集成电路", "光刻机", "光刻胶", "第三代半导体",
        "先进封装", "存储芯片", "汽车芯片",
    ),
    "高端制造与机器人": (
        "机器人", "人形机器人", "工业母机", "机器视觉", "减速器", "传感器",
        "自动化", "新型工业化", "智能制造", "工业互联网",
    ),
    "新能源与电力设备": (
        "光伏", "储能", "锂电", "固态电池", "钠电池", "风电", "核电", "特高压",
        "智能电网", "电网设备", "充电桩", "新能源车", "换电", "氢能源",
    ),
    "航空航天与低空经济": (
        "低空经济", "商业航天", "卫星", "无人机", "航空", "航天", "大飞机",
        "军工信息化", "通用航空",
    ),
    "创新医药与生物科技": (
        "创新药", "生物医药", "医疗器械", "CRO", "CXO", "合成生物", "基因测序",
        "细胞治疗", "医药电商",
    ),
    "数字经济与信创": (
        "信创", "国产软件", "操作系统", "网络安全", "数据要素", "数字经济",
        "鸿蒙", "区块链", "智慧政务",
    ),
    "先进材料与资源安全": (
        "新材料", "稀土", "稀土永磁", "小金属", "钛金属", "碳纤维", "复合材料",
        "有色", "黄金", "战略资源",
    ),
}

SEVERE_RISK_TERMS = (
    "退市风险", "重大违法", "财务造假", "立案调查", "无法表示意见",
    "否定意见", "破产重整", "债务逾期", "被实施退市风险警示",
)
MEDIUM_RISK_TERMS = (
    "立案", "调查", "行政处罚", "监管措施", "诉讼", "冻结", "减持", "质押",
    "预亏", "亏损", "终止", "风险提示", "异常波动",
)
POSITIVE_EVENT_TERMS = (
    "中标", "合同", "订单", "获批", "增长", "预增", "回购", "投产", "量产",
    "合作", "突破", "创新高", "扩产", "收购",
)

BUSINESS_MATCH_TERMS: dict[str, tuple[str, ...]] = {
    "CPO概念": ("CPO", "光模块", "光通信", "光电", "光器件", "光纤", "光缆"),
    "PCB概念": ("PCB", "印制电路板", "线路板"),
    "光通信": ("光通信", "光模块", "光纤", "光缆", "光器件", "通信设备"),
    "存储芯片": ("存储芯片", "存储业务", "半导体", "芯片"),
    "数据中心": ("数据中心", "服务器", "算力", "云计算", "IDC", "机房"),
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def decode_zero(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("gb18030", errors="ignore").strip()


def market_from_code7(code7: str) -> str:
    if code7[0] == "1":
        return "SH"
    if code7[0] == "2":
        return "BJ"
    return "SZ"


def symbol_from_code7(code7: str) -> str:
    return f"{code7[1:]}.{market_from_code7(code7)}"


def quote_id_from_code7(code7: str) -> str:
    market_id = "1" if market_from_code7(code7) == "SH" else "0"
    return f"{market_id}.{code7[1:]}"


def quote_symbol_from_code7(code7: str) -> str:
    market = market_from_code7(code7).lower()
    return f"{market}{code7[1:]}"


def load_names() -> dict[str, str]:
    names: dict[str, str] = {}
    for market, path in TNF_FILES.items():
        data = path.read_bytes()
        if len(data) < 50 or (len(data) - 50) % 360:
            raise RuntimeError(f"TNF format mismatch: {path}")
        for offset in range(50, len(data), 360):
            record = data[offset : offset + 360]
            code = decode_zero(record[:6])
            name = decode_zero(record[31:49])
            if len(code) == 6 and code.startswith(EQUITY_PREFIXES) and name:
                names[f"{code}.{market}"] = name
    if len(names) < 5000:
        raise RuntimeError(f"equity name cache truncated: {len(names)}")
    return names


def load_concepts() -> list[dict[str, Any]]:
    text = INFOHARBOR.read_bytes().decode("gb18030", errors="ignore")
    concepts: list[dict[str, Any]] = []
    current_name = ""
    current_codes: list[str] = []

    def flush() -> None:
        if not current_name.startswith("GN_"):
            return
        codes = list(dict.fromkeys(
            item for item in current_codes if item[1:].startswith(EQUITY_PREFIXES)
        ))
        if codes:
            concepts.append({"name": current_name[3:], "source_name": current_name, "codes": codes})

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            flush()
            current_name = line[1:].split(",", 1)[0].strip()
            current_codes = []
            continue
        for token in line.split(","):
            match = re.fullmatch(r"([0123])#(\d{6})", token.strip())
            if match:
                current_codes.append(match.group(1) + match.group(2))
    flush()
    if len(concepts) < 200:
        raise RuntimeError(f"concept cache truncated: {len(concepts)}")
    return concepts


def news_source_path() -> Path:
    if NEWS_INDEX.is_file():
        return NEWS_INDEX
    if LOCAL_NEWS_SNAPSHOT.is_file():
        return LOCAL_NEWS_SNAPSHOT
    dated = sorted((APP_ROOT / "data" / "news").glob("*/eastmoney-fast-news-*.json"), reverse=True)
    return dated[0] if dated else NEWS_INDEX


def load_news() -> list[dict[str, Any]]:
    # 通达信完整安装会提供二进制 msg_zx.idx；精简/模拟终端没有该文件，
    # 此时使用每日由 Harness 数据更新任务落盘的东方财富快讯快照，保持同一字段契约。
    if NEWS_INDEX.is_file():
        # 通达信索引可能在客户端更新过程中短暂处于半写入状态；解析失败时继续
        # 走 Harness 落盘快照，避免把一次索引损坏升级成整个策略 BLOCKED。
        try:
            data = NEWS_INDEX.read_bytes()
            if len(data) % NEWS_RECORD_SIZE:
                raise ValueError(f"news index size is not divisible by {NEWS_RECORD_SIZE}")
            rows: list[dict[str, Any]] = []
            for index in range(len(data) // NEWS_RECORD_SIZE):
                record = data[index * NEWS_RECORD_SIZE : (index + 1) * NEWS_RECORD_SIZE]
                recid, category, channel = struct.unpack_from("<III", record, 0)
                title = decode_zero(record[12:140])
                excerpt = decode_zero(record[140:640])
                local_page = decode_zero(record[640:768])
                page_path = NEWS_INDEX.parent / local_page
                if not title:
                    continue
                rows.append({
                    "index": index,
                    "recid": recid,
                    "category": category,
                    "channel": channel,
                    "title": title,
                    "excerpt": excerpt,
                    "local_page": local_page,
                    "source_path": str(page_path),
                    "mtime": (
                        datetime.fromtimestamp(page_path.stat().st_mtime, CN_TZ).isoformat(timespec="seconds")
                        if page_path.is_file() else None
                    ),
                })
            if len(rows) >= 50:
                return rows
        except (OSError, ValueError, struct.error):
            pass

    candidates = [LOCAL_NEWS_SNAPSHOT]
    candidates.extend(sorted((APP_ROOT / "data" / "news").glob("*/eastmoney-fast-news-*.json"), reverse=True))
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            records = payload.get("source", {}).get("records") or payload.get("records") or []
            if not isinstance(records, list):
                continue
            rows = []
            for index, record in enumerate(records):
                if not isinstance(record, dict):
                    continue
                title = str(record.get("title") or "").strip()
                if not title:
                    continue
                published = record.get("publishedAt") or record.get("published_at")
                rows.append({
                    "index": index,
                    "recid": record.get("id") or index,
                    "category": 0,
                    "channel": 0,
                    "title": title,
                    "excerpt": str(record.get("summary") or record.get("excerpt") or ""),
                    "local_page": "",
                    "source_path": str(path),
                    "mtime": str(published) if published else datetime.fromtimestamp(path.stat().st_mtime, CN_TZ).isoformat(timespec="seconds"),
                })
            if len(rows) >= 50:
                return rows
        except (OSError, ValueError, TypeError):
            continue
    raise RuntimeError(f"news cache missing: {NEWS_INDEX} and {LOCAL_NEWS_SNAPSHOT}")


def day_path(code7: str) -> Path:
    market = market_from_code7(code7)
    lower = market.lower()
    return DAY_DIRS[market] / f"{lower}{code7[1:]}.day"


def read_day_rows(code7: str, limit: int | None = None) -> list[dict[str, float | int]]:
    path = day_path(code7)
    if not path.is_file() or path.stat().st_size < DAY_RECORD.size:
        return []
    size = path.stat().st_size
    if size % DAY_RECORD.size:
        raise RuntimeError(f"day file format mismatch: {path}")
    record_count = size // DAY_RECORD.size
    start = max(0, record_count - limit) if limit else 0
    rows: list[dict[str, float | int]] = []
    with path.open("rb") as handle:
        handle.seek(start * DAY_RECORD.size)
        for _ in range(record_count - start):
            raw = handle.read(DAY_RECORD.size)
            date_i, open_i, high_i, low_i, close_i, amount, volume, _unused = DAY_RECORD.unpack(raw)
            if not 19900101 <= date_i <= 20991231 or close_i <= 0:
                continue
            rows.append({
                "date": int(date_i),
                "open": float(open_i) / 100.0,
                "high": float(high_i) / 100.0,
                "low": float(low_i) / 100.0,
                "close": float(close_i) / 100.0,
                "amount": float(amount),
                "volume": int(volume),
            })
    return rows


def complete_trade_date() -> tuple[int, dict[str, Any]]:
    counts: Counter[int] = Counter()
    market_files: dict[str, int] = {}
    for market, directory in DAY_DIRS.items():
        file_count = 0
        if not directory.is_dir():
            market_files[market] = 0
            continue
        for path in directory.glob("*.day"):
            size = path.stat().st_size
            if size < DAY_RECORD.size or size % DAY_RECORD.size:
                continue
            with path.open("rb") as handle:
                handle.seek(-DAY_RECORD.size, 2)
                date_i = DAY_RECORD.unpack(handle.read(DAY_RECORD.size))[0]
            if 19900101 <= date_i <= 20991231:
                counts[int(date_i)] += 1
                file_count += 1
        market_files[market] = file_count
    if not counts:
        raise RuntimeError("no valid daily data")
    maximum_coverage = max(counts.values())
    threshold = max(1000, int(maximum_coverage * 0.8))
    eligible = [date_i for date_i, count in counts.items() if count >= threshold]
    if not eligible:
        raise RuntimeError("no complete cross-sectional trade date")
    selected = max(eligible)
    return selected, {
        "latest_observed_date": max(counts),
        "selected_complete_date": selected,
        "selected_coverage": counts[selected],
        "maximum_date_coverage": maximum_coverage,
        "coverage_threshold": threshold,
        "latest_observed_coverage": counts[max(counts)],
        "top_dates": counts.most_common(8),
        "market_file_counts": market_files,
    }


def map_track(concept_name: str) -> tuple[str, str] | None:
    upper = concept_name.upper()
    matches: list[tuple[int, str, str]] = []
    for group, terms in TRACK_GROUPS.items():
        for term in terms:
            term_upper = term.upper()
            if term_upper.isascii() and term_upper.isalpha():
                matched = upper.startswith(term_upper) or upper.endswith(term_upper)
            else:
                matched = term_upper in upper
            if matched:
                matches.append((len(term), group, term))
    if not matches:
        return None
    _length, group, term = max(matches, key=lambda item: (item[0], item[1], item[2]))
    return group, term


def safe_mean(values: Iterable[float]) -> float:
    items = list(values)
    return statistics.fmean(items) if items else 0.0


def percentile_map(values: dict[str, float]) -> dict[str, float]:
    groups: dict[float, list[str]] = defaultdict(list)
    for key, value in values.items():
        groups[value].append(key)
    ordered = sorted(groups)
    total = len(values)
    result: dict[str, float] = {}
    position = 0
    for value in ordered:
        keys = groups[value]
        midpoint = (position + position + len(keys) - 1) / 2.0
        percentile = 1.0 if total == 1 else midpoint / (total - 1)
        for key in keys:
            result[key] = percentile
        position += len(keys)
    return result


def atr(rows: list[dict[str, float | int]], period: int = 14) -> float:
    ranges: list[float] = []
    for index in range(1, len(rows)):
        previous_close = float(rows[index - 1]["close"])
        high = float(rows[index]["high"])
        low = float(rows[index]["low"])
        ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
    return safe_mean(ranges[-period:])


def limit_ratio(code7: str) -> float:
    code = code7[1:]
    if market_from_code7(code7) == "BJ":
        return 0.30
    if code.startswith(("300", "301", "688", "689")):
        return 0.20
    return 0.10


def stock_snapshot(
    code7: str,
    trade_date: int,
    history: int = 180,
    current_bar: dict[str, float | int] | None = None,
) -> dict[str, Any] | None:
    rows = [row for row in read_day_rows(code7, max(history + 30, 240)) if int(row["date"]) <= trade_date]
    if current_bar is not None:
        rows = [row for row in rows if int(row["date"]) < trade_date]
        rows.append(current_bar)
    if len(rows) < 120 or int(rows[-1]["date"]) != trade_date:
        return None
    closes = [float(row["close"]) for row in rows]
    amounts = [float(row["amount"]) for row in rows]
    volumes = [float(row["volume"]) for row in rows]
    if min(closes[-60:]) <= 0:
        return None
    previous_volumes = [item for item in volumes[-6:-1] if item > 0]
    previous_amounts = [item for item in amounts[-6:-1] if item > 0]
    if not previous_volumes or not previous_amounts:
        return None
    current_atr = atr(rows[-30:])
    close = closes[-1]
    return {
        "date": trade_date,
        "row_count": len(rows),
        "open": float(rows[-1]["open"]),
        "high": float(rows[-1]["high"]),
        "low": float(rows[-1]["low"]),
        "close": close,
        "return_1d": close / closes[-2] - 1.0,
        "return_5d": close / closes[-6] - 1.0,
        "return_20d": close / closes[-21] - 1.0,
        "ma20": safe_mean(closes[-20:]),
        "ma60": safe_mean(closes[-60:]),
        "ma20_prev5": safe_mean(closes[-25:-5]),
        "volume_ratio_5d": volumes[-1] / safe_mean(previous_volumes),
        "amount_ratio_5d": amounts[-1] / safe_mean(previous_amounts),
        "average_amount_20d": safe_mean(amounts[-20:]),
        "atr14": current_atr,
        "atr_pct": current_atr / close if close else 0.0,
        "drawdown_60d": close / max(closes[-60:]) - 1.0,
        "is_up": close > closes[-2],
        "is_limit_up": close / closes[-2] - 1.0 >= limit_ratio(code7) * 0.95,
    }


def news_evidence(concept: str, group: str, matched_term: str, news: list[dict[str, Any]]) -> list[dict[str, Any]]:
    terms = {concept, matched_term}
    terms.update(term for term in TRACK_GROUPS[group] if len(term) >= 3 and term in concept)
    evidence: list[dict[str, Any]] = []
    for row in news:
        text = f"{row['title']} {row['excerpt']}"
        hits = sorted(term for term in terms if term and term.upper() in text.upper())
        if hits:
            evidence.append({
                "recid": row["recid"],
                "mtime": row["mtime"],
                "title": row["title"],
                "matched_terms": hits,
                "source_path": row["source_path"],
            })
    return evidence


SECTOR_FIELDS = (
    "mean_return_1d", "median_return_1d", "mean_return_5d", "up_ratio",
    "limit_up_ratio", "median_volume_ratio_5d", "median_amount_ratio_5d",
)


def rank_sectors(
    concepts: list[dict[str, Any]],
    snapshots: dict[str, dict[str, Any]],
    news: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sectors: list[dict[str, Any]] = []
    for concept in concepts:
        mapped = map_track(str(concept["name"]))
        if mapped is None:
            continue
        group, matched_term = mapped
        rows = [snapshots[code] for code in concept["codes"] if code in snapshots]
        member_count = len(concept["codes"])
        coverage = len(rows)
        if coverage < 5 or coverage / member_count < 0.50:
            continue
        ret1 = [float(row["return_1d"]) for row in rows]
        ret5 = [float(row["return_5d"]) for row in rows]
        evidence = news_evidence(str(concept["name"]), group, matched_term, news)
        sectors.append({
            "name": concept["name"],
            "source_name": concept["source_name"],
            "track_group": group,
            "matched_track_term": matched_term,
            "codes": concept["codes"],
            "member_count": member_count,
            "coverage_count": coverage,
            "coverage_ratio": coverage / member_count,
            "mean_return_1d": safe_mean(ret1),
            "median_return_1d": statistics.median(ret1),
            "mean_return_5d": safe_mean(ret5),
            "up_ratio": sum(bool(row["is_up"]) for row in rows) / coverage,
            "limit_up_ratio": sum(bool(row["is_limit_up"]) for row in rows) / coverage,
            "median_volume_ratio_5d": statistics.median(float(row["volume_ratio_5d"]) for row in rows),
            "median_amount_ratio_5d": statistics.median(float(row["amount_ratio_5d"]) for row in rows),
            "event_evidence": evidence[:5],
            "event_hit_count": len(evidence),
        })
    if not sectors:
        return []
    for field in SECTOR_FIELDS:
        percentiles = percentile_map({str(item["source_name"]): float(item[field]) for item in sectors})
        for item in sectors:
            item.setdefault("percentiles", {})[field] = percentiles[str(item["source_name"])]
    for item in sectors:
        market_score = 100.0 * safe_mean(item["percentiles"].values())
        event_bonus = min(10.0, float(item["event_hit_count"]) * 2.0)
        item["market_score"] = market_score
        item["event_bonus"] = event_bonus
        item["quality_track_score"] = market_score * 0.90 + event_bonus
    scores = [float(item["quality_track_score"]) for item in sectors]
    score_median = statistics.median(scores)
    score_mad = statistics.median(abs(value - score_median) for value in scores)
    score_floor = score_median + score_mad
    volume_median = statistics.median(float(item["median_volume_ratio_5d"]) for item in sectors)
    for item in sectors:
        persistent_strength = float(item["mean_return_5d"]) > 0
        reversal_strength = bool(
            -0.20 < float(item["mean_return_5d"]) <= 0
            and float(item["mean_return_1d"]) >= 0.02
            and float(item["median_volume_ratio_5d"]) >= volume_median
        )
        item["qualification_gate"] = {
            "score_floor_median_plus_mad": score_floor,
            "score_above_floor": float(item["quality_track_score"]) > score_floor,
            "event_confirmed": item["event_hit_count"] > 0,
            "positive_mean_and_median_1d": float(item["mean_return_1d"]) > 0 and float(item["median_return_1d"]) > 0,
            "up_ratio_at_least_65pct": float(item["up_ratio"]) >= 0.65,
            "persistent_strength_route": persistent_strength,
            "volume_confirmed_reversal_route": reversal_strength,
            "reversal_route_enabled": False,
            "reversal_route_disabled_reason": "execution-layer backtest failed after costs",
        }
        item["strict_qualified"] = bool(
            item["qualification_gate"]["score_above_floor"]
            and item["qualification_gate"]["event_confirmed"]
            and item["qualification_gate"]["positive_mean_and_median_1d"]
            and item["qualification_gate"]["up_ratio_at_least_65pct"]
            and persistent_strength
        )
    sectors.sort(key=lambda item: (-float(item["quality_track_score"]), str(item["source_name"])))
    for index, item in enumerate(sectors, 1):
        item["rank"] = index
    return sectors


def company_news(name: str, code: str, news: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(name) < 3:
        return []
    result: list[dict[str, Any]] = []
    for row in news:
        text = f"{row['title']} {row['excerpt']}"
        if name in text or code in text:
            positive = sorted(term for term in POSITIVE_EVENT_TERMS if term in text)
            risk = sorted(term for term in MEDIUM_RISK_TERMS if term in text)
            result.append({
                "recid": row["recid"],
                "mtime": row["mtime"],
                "title": row["title"],
                "positive_terms": positive,
                "risk_terms": risk,
                "source_path": row["source_path"],
            })
    return result[:8]


def preliminary_candidates(
    selected_sectors: list[dict[str, Any]],
    snapshots: dict[str, dict[str, Any]],
    names: dict[str, str],
    news: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    membership: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sector in selected_sectors:
        for code7 in sector["codes"]:
            if code7 in snapshots:
                membership[code7].append(sector)
    rows: list[dict[str, Any]] = []
    for code7, sectors in membership.items():
        symbol = symbol_from_code7(code7)
        name = names.get(symbol)
        if not name:
            continue
        snap = snapshots[code7]
        exclusions: list[str] = []
        if re.match(r"^\*?ST", name, flags=re.IGNORECASE):
            exclusions.append("ST_OR_STAR_ST")
        if float(snap["close"]) < 2.0:
            exclusions.append("PRICE_BELOW_2")
        if float(snap["average_amount_20d"]) < 50_000_000:
            exclusions.append("AVERAGE_AMOUNT_20D_BELOW_50M")
        if bool(snap["is_limit_up"]):
            exclusions.append("CLOSE_AT_OR_NEAR_LIMIT_UP")
        if float(snap["return_5d"]) > 0.30:
            exclusions.append("FIVE_DAY_GAIN_ABOVE_30PCT")
        if float(snap["close"]) / float(snap["ma20"]) > 1.25:
            exclusions.append("PRICE_MORE_THAN_25PCT_ABOVE_MA20")

        best_sector = max(sectors, key=lambda item: float(item["quality_track_score"]))
        news_hits = company_news(name, code7[1:], news)
        role_signal = len(sectors) >= 2 or bool(news_hits)
        pct5 = float(snap["return_5d"])
        if 0.02 <= pct5 <= 0.15:
            momentum_score = 12.0
        elif 0 <= pct5 <= 0.20:
            momentum_score = 8.0
        elif -0.05 <= pct5 < 0:
            momentum_score = 3.0
        else:
            momentum_score = 0.0
        trend_score = (
            (8.0 if float(snap["close"]) > float(snap["ma20"]) else 0.0)
            + (5.0 if float(snap["close"]) > float(snap["ma60"]) else 0.0)
            + (5.0 if float(snap["ma20"]) > float(snap["ma20_prev5"]) else 0.0)
        )
        volume_ratio = float(snap["volume_ratio_5d"])
        volume_score = 7.0 if 1.0 <= volume_ratio <= 2.5 else 4.0 if 0.8 <= volume_ratio < 1.0 else 0.0
        volatility_score = 5.0 if float(snap["atr_pct"]) <= 0.06 else 2.0 if float(snap["atr_pct"]) <= 0.09 else 0.0
        company_event_score = min(8.0, 2.0 * sum(bool(item["positive_terms"]) for item in news_hits))
        risk_penalty = min(12.0, 2.0 * sum(len(item["risk_terms"]) for item in news_hits))
        liquidity_score = min(4.0, math.log10(max(1.0, float(snap["average_amount_20d"]) / 10_000_000.0)))
        raw_total = (
            float(best_sector["quality_track_score"]) * 0.50
            + trend_score + momentum_score + volume_score + volatility_score
            + company_event_score + (6.0 if role_signal else 0.0) - risk_penalty
            + liquidity_score
        )
        total = max(0.0, min(100.0, raw_total))
        rows.append({
            "code7": code7,
            "symbol": symbol,
            "code": code7[1:],
            "name": name,
            "disposition": "EXCLUDE" if exclusions else "PRELIMINARY",
            "preliminary_score": round(total, 4),
            "preliminary_score_raw": round(raw_total, 4),
            "score_contract": {
                "version": "QUALITY-TRACK-STOCK-100-V2",
                "scale": 100,
                "raw_max": 110,
                "bounded": True,
                "hard_exclusions_apply_before_final_selection": True,
            },
            "score_breakdown": {
                "sector": round(float(best_sector["quality_track_score"]) * 0.50, 4),
                "trend": trend_score,
                "momentum": momentum_score,
                "volume": volume_score,
                "volatility": volatility_score,
                "company_event": company_event_score,
                "role_candidate_signal": 6.0 if role_signal else 0.0,
                "company_news_risk_penalty": -risk_penalty,
                "liquidity": round(liquidity_score, 4),
            },
            "membership_evidence": [
                {
                    "concept": item["name"],
                    "source_section": item["source_name"],
                    "source_path": str(INFOHARBOR),
                    "track_group": item["track_group"],
                    "sector_score": round(float(item["quality_track_score"]), 4),
                }
                for item in sorted(sectors, key=lambda item: -float(item["quality_track_score"]))[:5]
            ],
            "industry_role": "待主营证据核验的核心候选",
            "role_candidate_signal": role_signal,
            "role_candidate_evidence": {
                "cross_concept_count": len(sectors),
                "company_news_direct_hit": bool(news_hits),
                "rule": "candidate signal only; final role requires current company profile or main-business evidence",
            },
            "company_news": news_hits,
            "technical": {key: round(value, 8) if isinstance(value, float) else value for key, value in snap.items()},
            "hard_exclusions": exclusions,
        })
    rows.sort(key=lambda item: (item["disposition"] == "EXCLUDE", -float(item["preliminary_score"]), item["symbol"]))
    for index, item in enumerate(rows, 1):
        item["preliminary_rank"] = index
    return rows


def http_json(url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CodexQualityTrack/3.0",
        "Referer": "https://quote.eastmoney.com/",
        "Connection": "close",
    }
    request_headers.update(headers or {})
    request = urllib.request.Request(url, headers=request_headers)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"HTTP JSON failed after retries: {url}: {last_error}")


def http_text(url: str, encoding: str) -> str:
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CodexQualityTrack/3.0",
        "Referer": "https://quote.eastmoney.com/",
        "Connection": "close",
    })
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.read().decode(encoding, errors="replace")
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"HTTP text failed after retries: {url}: {last_error}")


def parse_tencent_batch_bars(
    text: str,
    trade_date: int,
    by_quote_symbol: dict[str, str],
) -> dict[str, dict[str, float | int]]:
    bars: dict[str, dict[str, float | int]] = {}
    for match in re.finditer(r'v_([a-z]{2}\d{6})="([^"]*)";?', text):
        quote_symbol, payload = match.groups()
        code7 = by_quote_symbol.get(quote_symbol)
        fields = payload.split("~")
        if code7 is None or len(fields) < 39 or fields[2] != code7[1:]:
            continue
        if not fields[30] or int(fields[30][:8]) != trade_date:
            continue
        try:
            close = float(fields[3])
            previous_close = float(fields[4])
            open_price = float(fields[5])
            high = float(fields[33])
            low = float(fields[34])
            volume = int(float(fields[36]) * 100.0)
            detail = fields[35].split("/")
            amount = float(detail[2]) if len(detail) >= 3 else float(fields[37]) * 10_000.0
        except (TypeError, ValueError):
            continue
        if min(close, previous_close, open_price, high, low, amount, volume) <= 0:
            continue
        if high < max(open_price, close) or low > min(open_price, close):
            continue
        bars[code7] = {
            "date": trade_date,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "amount": amount,
            "volume": volume,
        }
    return bars


def fetch_batch_current_bars(code7s: list[str], trade_date: int, batch_size: int = 80) -> dict[str, dict[str, float | int]]:
    by_quote_symbol = {quote_symbol_from_code7(code7): code7 for code7 in code7s}
    bars: dict[str, dict[str, float | int]] = {}
    for start in range(0, len(code7s), batch_size):
        batch = code7s[start : start + batch_size]
        symbols = ",".join(quote_symbol_from_code7(code7) for code7 in batch)
        text = http_text(f"https://qt.gtimg.cn/q={urllib.parse.quote(symbols, safe=',')}", "gb18030")
        bars.update(parse_tencent_batch_bars(text, trade_date, by_quote_symbol))
    return bars


def fetch_live_quote(code7: str) -> dict[str, Any]:
    symbol = quote_symbol_from_code7(code7)
    text = http_text(f"https://qt.gtimg.cn/q={urllib.parse.quote(symbol)}", "gb18030")
    matched = re.search(r'=\"(.*)\";?$', text.strip())
    if not matched:
        raise RuntimeError(f"Tencent quote response mismatch: {symbol}")
    fields = matched.group(1).split("~")
    if len(fields) < 39 or fields[2] != code7[1:]:
        raise RuntimeError(f"Tencent quote identity mismatch: {symbol}")
    return {
        "source": "https://qt.gtimg.cn/",
        "name": fields[1],
        "code": fields[2],
        "price": float(fields[3]),
        "previous_close": float(fields[4]),
        "open": float(fields[5]),
        "high": float(fields[33]),
        "low": float(fields[34]),
        "change_pct": float(fields[32]),
        "turnover_rate": float(fields[38]) if fields[38] else None,
        "market_time": datetime.strptime(fields[30], "%Y%m%d%H%M%S").replace(tzinfo=CN_TZ).isoformat(timespec="seconds"),
    }


def fetch_valuation(code7: str) -> dict[str, Any]:
    fields = "f43,f57,f58,f86,f116,f117,f162,f167,f168"
    url = (
        "https://push2delay.eastmoney.com/api/qt/stock/get?"
        f"secid={quote_id_from_code7(code7)}&invt=2&fltt=2&fields={fields}"
    )
    data = http_json(url).get("data") or {}
    if str(data.get("f57")) != code7[1:]:
        raise RuntimeError(f"Eastmoney valuation identity mismatch: {code7}")
    return {
        "source": "https://push2delay.eastmoney.com/api/qt/stock/get",
        "pe_ttm": data.get("f162"),
        "pb": data.get("f167"),
        "turnover_rate": data.get("f168"),
        "total_market_cap": data.get("f116"),
        "float_market_cap": data.get("f117"),
    }


def fetch_announcements(code: str, limit: int = 30) -> list[dict[str, Any]]:
    url = (
        "https://np-anotice-stock.eastmoney.com/api/security/ann?sr=-1&"
        f"page_size={limit}&page_index=1&ann_type=A&client_source=web&stock_list={code}"
    )
    rows = ((http_json(url).get("data") or {}).get("list") or [])
    result: list[dict[str, Any]] = []
    for row in rows:
        title = str(row.get("title_ch") or row.get("title") or "")
        classification = classify_announcement_title(title)
        result.append({
            "art_code": row.get("art_code"),
            "title": title,
            "display_time": str(row.get("display_time") or "")[:19],
            "categories": [item.get("column_name") for item in row.get("columns") or []],
            "source": "https://np-anotice-stock.eastmoney.com/api/security/ann",
            **classification,
        })
    return result


def classify_announcement_title(title: str) -> dict[str, Any]:
    routine_fund_audit = bool(
        "非经营性资金占用及其他关联资金往来" in title
        and any(term in title for term in ("专项", "汇总表", "情况表", "说明"))
    )
    adverse_fund_occupation = bool(re.search(r"违规占用|被.{0,12}占用|占用资金.{0,12}(未归还|逾期)", title))
    severe_terms = [term for term in SEVERE_RISK_TERMS if term in title]
    if adverse_fund_occupation:
        severe_terms.append("实际或违规资金占用")
    medium_terms = [term for term in MEDIUM_RISK_TERMS if term in title]
    if routine_fund_audit:
        severe_terms = []
        medium_terms = []
    return {
        "routine_fund_occupation_audit": routine_fund_audit,
        "severe_risk_terms": sorted(set(severe_terms)),
        "medium_risk_terms": sorted(set(medium_terms)),
    }


def normalize_security_name(name: str) -> str:
    return re.sub(r"[-－](?:UW|U|W|V)$", "", name.strip(), flags=re.IGNORECASE)


def finite_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fetch_financials(symbol: str) -> dict[str, Any]:
    import akshare as ak

    frame = ak.stock_financial_analysis_indicator_em(symbol=symbol, indicator="按报告期")
    if frame.empty:
        raise RuntimeError(f"financial indicator empty: {symbol}")
    row = frame.iloc[0].to_dict()
    if str(row.get("SECUCODE")) != symbol:
        raise RuntimeError(f"financial identity mismatch: {symbol}")
    fields = {
        "report_date": str(row.get("REPORT_DATE") or "")[:10],
        "report_type": row.get("REPORT_TYPE"),
        "notice_date": str(row.get("NOTICE_DATE") or "")[:10],
        "revenue": finite_number(row.get("TOTALOPERATEREVE")),
        "revenue_yoy_pct": finite_number(row.get("TOTALOPERATEREVETZ")),
        "net_profit": finite_number(row.get("PARENTNETPROFIT")),
        "net_profit_yoy_pct": finite_number(row.get("PARENTNETPROFITTZ")),
        "roe_pct": finite_number(row.get("ROEJQ")),
        "gross_margin_pct": finite_number(row.get("XSMLL")),
        "net_margin_pct": finite_number(row.get("XSJLL")),
        "operating_cash_to_revenue": finite_number(row.get("JYXJLYYSR")),
        "debt_ratio_pct": finite_number(row.get("ZCFZL")),
        "current_ratio": finite_number(row.get("LD")),
        "quick_ratio": finite_number(row.get("SD")),
        "total_asset_turnover": finite_number(row.get("TOAZZL")),
        "inventory_turnover_days": finite_number(row.get("CHZZTS")),
        "receivable_turnover_days": finite_number(row.get("YSZKZZTS")),
    }
    dimensions = {
        "生产": {
            "pass": fields["gross_margin_pct"] is not None and fields["gross_margin_pct"] > 10,
            "evidence": {"gross_margin_pct": fields["gross_margin_pct"], "roe_pct": fields["roe_pct"]},
        },
        "供应": {
            "pass": fields["debt_ratio_pct"] is not None and fields["debt_ratio_pct"] < 75,
            "evidence": {"debt_ratio_pct": fields["debt_ratio_pct"], "current_ratio": fields["current_ratio"], "quick_ratio": fields["quick_ratio"]},
        },
        "销售": {
            "pass": fields["revenue_yoy_pct"] is not None and fields["revenue_yoy_pct"] > -10,
            "evidence": {"revenue": fields["revenue"], "revenue_yoy_pct": fields["revenue_yoy_pct"], "net_profit_yoy_pct": fields["net_profit_yoy_pct"]},
        },
        "运输": {
            "pass": fields["total_asset_turnover"] is not None and fields["total_asset_turnover"] > 0,
            "proxy": "总资产周转率是运营流转代理，不等同于物流运输事实",
            "evidence": {"total_asset_turnover": fields["total_asset_turnover"], "receivable_turnover_days": fields["receivable_turnover_days"]},
        },
        "仓储库存": {
            "pass": fields["inventory_turnover_days"] is not None and fields["inventory_turnover_days"] > 0,
            "evidence": {"inventory_turnover_days": fields["inventory_turnover_days"], "operating_cash_to_revenue": fields["operating_cash_to_revenue"]},
        },
    }
    return {
        "source": "Eastmoney RPT_F10_FINANCE_MAINFINADATA via AkShare 1.18.64",
        "source_url": "https://datacenter.eastmoney.com/securities/api/data/get",
        "fields": fields,
        "dimensions": dimensions,
        "dimension_pass_count": sum(bool(item["pass"]) for item in dimensions.values()),
    }


def fetch_business_evidence(code7: str) -> dict[str, Any]:
    import akshare as ak

    code = code7[1:]
    profile_frame = ak.stock_profile_cninfo(symbol=code)
    if profile_frame.empty:
        raise RuntimeError(f"CNInfo profile empty: {code}")
    profile = profile_frame.iloc[0].to_dict()
    if str(profile.get("A股代码")) != code:
        raise RuntimeError(f"CNInfo profile identity mismatch: {code}")
    market_prefix = "SH" if market_from_code7(code7) == "SH" else "SZ"
    composition_frame = ak.stock_zygc_em(symbol=f"{market_prefix}{code}")
    composition_rows: list[dict[str, Any]] = []
    if not composition_frame.empty:
        latest_report = composition_frame["报告日期"].max()
        latest = composition_frame[composition_frame["报告日期"] == latest_report]
        for _index, row in latest.iterrows():
            category = str(row.get("分类类型") or "")
            if category == "按地区分类":
                continue
            composition_rows.append({
                "category": category,
                "business": str(row.get("主营构成") or ""),
                "revenue_ratio": finite_number(row.get("收入比例")),
                "gross_margin": finite_number(row.get("毛利率")),
            })
    business_text = " ".join([
        str(profile.get("主营业务") or ""),
        str(profile.get("经营范围") or ""),
        *(row["business"] for row in composition_rows),
    ])
    return {
        "sources": {
            "profile": "CNInfo company profile via AkShare stock_profile_cninfo",
            "profile_url": "https://webapi.cninfo.com.cn/",
            "composition": "Eastmoney main business composition via AkShare stock_zygc_em",
            "composition_url": "https://datacenter.eastmoney.com/",
        },
        "company_name": profile.get("公司名称"),
        "short_name": profile.get("A股简称"),
        "industry": profile.get("所属行业"),
        "main_business": profile.get("主营业务"),
        "business_scope": profile.get("经营范围"),
        "latest_composition": composition_rows[:20],
        "search_text": business_text,
    }


def verify_business_role(candidate: dict[str, Any], business: dict[str, Any]) -> dict[str, Any]:
    matched: list[dict[str, Any]] = []
    for membership in candidate["membership_evidence"]:
        concept = str(membership["concept"])
        terms = BUSINESS_MATCH_TERMS.get(concept, (concept,))
        category_ratios: dict[str, float] = defaultdict(float)
        evidence_rows: list[dict[str, Any]] = []
        for row in business.get("latest_composition") or []:
            row_text = str(row.get("business") or "")
            hits = sorted(term for term in terms if term.upper() in row_text.upper())
            ratio = finite_number(row.get("revenue_ratio")) or 0.0
            if hits:
                category = str(row.get("category") or "unknown")
                category_ratios[category] += ratio
                evidence_rows.append({"category": category, "business": row_text, "revenue_ratio": ratio, "terms": hits})
        verified_ratio = max(category_ratios.values(), default=0.0)
        if verified_ratio >= 0.10:
            matched.append({
                "concept": concept,
                "verified_revenue_ratio": round(verified_ratio, 6),
                "composition_evidence": evidence_rows,
            })
    return {
        "verified": bool(matched),
        "role": "最新主营收入占比确认的核心板块公司" if matched else "概念成分但核心主营未确认",
        "matched_concepts": matched,
        "rule": "selected concept must match latest main-business composition with at least 10% revenue share in one classification",
    }


def enrich_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    result = dict(candidate)
    errors: list[str] = []
    try:
        quote = fetch_live_quote(candidate["code7"])
    except Exception as exc:
        quote = None
        errors.append(f"live_quote:{type(exc).__name__}:{exc}")
    try:
        valuation = fetch_valuation(candidate["code7"])
    except Exception as exc:
        valuation = None
        errors.append(f"valuation:{type(exc).__name__}:{exc}")
    try:
        announcements = fetch_announcements(candidate["code"], 30)
    except Exception as exc:
        announcements = []
        errors.append(f"announcements:{type(exc).__name__}:{exc}")
    try:
        financials = fetch_financials(candidate["symbol"])
    except Exception as exc:
        financials = None
        errors.append(f"financials:{type(exc).__name__}:{exc}")
    try:
        business = fetch_business_evidence(candidate["code7"])
        role_evidence = verify_business_role(candidate, business)
        business.pop("search_text", None)
    except Exception as exc:
        business = None
        role_evidence = {"verified": False, "role": "主营证据获取失败", "matched_concepts": [], "rule": "fail closed"}
        errors.append(f"business:{type(exc).__name__}:{exc}")

    severe_hits = [item for item in announcements if item["severe_risk_terms"]]
    medium_hits = [item for item in announcements if item["medium_risk_terms"]]
    hard_exclusions = list(candidate["hard_exclusions"])
    review_reasons: list[str] = []
    if severe_hits:
        hard_exclusions.append("COMPANY_SPECIFIC_SEVERE_ANNOUNCEMENT_RISK")
    if errors:
        review_reasons.append("EXTERNAL_EVIDENCE_FETCH_INCOMPLETE")
    if not announcements:
        review_reasons.append("NO_COMPANY_ANNOUNCEMENT_READBACK")
    if financials is None:
        review_reasons.append("NO_STRUCTURED_FINANCIAL_READBACK")
    elif int(financials["dimension_pass_count"]) < 4:
        review_reasons.append("FINANCIAL_DIMENSIONS_BELOW_4_OF_5")
    if valuation is None:
        review_reasons.append("NO_VALUATION_READBACK")
    else:
        market_cap = finite_number(valuation.get("total_market_cap"))
        pe_ttm = finite_number(valuation.get("pe_ttm"))
        pb = finite_number(valuation.get("pb"))
        if market_cap is None or market_cap < 3_000_000_000:
            review_reasons.append("MARKET_CAP_BELOW_3B_OR_UNKNOWN")
        if pe_ttm is None or pe_ttm <= 0 or pe_ttm > 150:
            review_reasons.append("PE_TTM_OUTSIDE_0_TO_150")
        if pb is None or pb <= 0 or pb > 15:
            review_reasons.append("PB_OUTSIDE_0_TO_15")
    if quote is None:
        review_reasons.append("NO_CURRENT_QUOTE")
    elif quote["code"] != candidate["code"]:
        hard_exclusions.append("LIVE_QUOTE_IDENTITY_MISMATCH")
    else:
        normalized_quote_name = normalize_security_name(str(quote["name"]))
        normalized_local_name = normalize_security_name(str(candidate["name"]))
        if normalized_quote_name != normalized_local_name:
            review_reasons.append("LIVE_QUOTE_NAME_VARIANT_REVIEW")
        quote_date = str(quote["market_time"])[:10].replace("-", "")
        today_cn = datetime.now(CN_TZ).strftime("%Y%m%d")
        if quote_date != today_cn:
            review_reasons.append("LIVE_QUOTE_DATE_NOT_CURRENT")
        live_change = float(quote["price"]) / float(quote["previous_close"]) - 1.0
        if live_change >= limit_ratio(candidate["code7"]) * 0.95:
            review_reasons.append("LIVE_PRICE_AT_OR_NEAR_LIMIT_UP")
        if float(quote["price"]) > float(candidate["technical"]["close"]) * 1.03:
            review_reasons.append("LIVE_PRICE_ABOVE_ENTRY_CEILING")
    if not bool(role_evidence.get("verified")):
        review_reasons.append("CORE_COMPANY_ROLE_NOT_BUSINESS_VERIFIED")
    if medium_hits:
        review_reasons.append("RECENT_COMPANY_ANNOUNCEMENT_RISK_REVIEW")

    if hard_exclusions:
        disposition = "EXCLUDE"
    elif review_reasons:
        disposition = "REVIEW"
    else:
        disposition = "PAPER_ELIGIBLE"

    close = float(quote["price"]) if quote is not None else float(candidate["technical"]["close"])
    atr_value = float(candidate["technical"]["atr14"])
    stop_price = max(close * 0.92, close - 2.0 * atr_value)
    stop_pct = max(0.001, 1.0 - stop_price / close)
    risk_budget = 0.008
    weight = min(0.20, risk_budget / stop_pct)
    if disposition != "PAPER_ELIGIBLE":
        weight = 0.0
    result.update({
        "disposition": disposition,
        "hard_exclusions": sorted(set(hard_exclusions)),
        "review_reasons": sorted(set(review_reasons)),
        "live_quote": quote,
        "valuation": valuation,
        "financials": financials,
        "business_evidence": business,
        "role_evidence": role_evidence,
        "industry_role": role_evidence["role"],
        "announcement_risk": {
            "source": "Eastmoney stock-specific announcement aggregator",
            "announcement_count": len(announcements),
            "severe_hits": severe_hits,
            "medium_hits": medium_hits[:10],
            "latest": announcements[:10],
        },
        "external_errors": errors,
        "paper_plan": {
            "reference_price": round(close, 2),
            "entry_condition": "next tradable price no more than 3% above reference close and not at limit-up",
            "entry_ceiling": round(close * 1.03, 2),
            "signal_close": round(float(candidate["technical"]["close"]), 2),
            "signal_entry_ceiling": round(float(candidate["technical"]["close"]) * 1.03, 2),
            "live_gap_from_signal_pct": round(
                (close / float(candidate["technical"]["close"]) - 1.0) * 100.0,
                2,
            ),
            "initial_stop": round(stop_price, 2),
            "stop_distance_pct": round(stop_pct * 100.0, 2),
            "max_portfolio_weight_pct": round(weight * 100.0, 2),
            "risk_budget_pct_of_portfolio": 0.8,
            "automatic_order": False,
        },
    })
    return result


def json_safe_sector(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if key != "codes"}


OBSERVATION_DISPOSITIONS = frozenset({"REVIEW", "WATCH_ONLY"})


def partition_candidate_lists(
    enriched: list[dict[str, Any]],
    final_limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    paper_eligible = [item for item in enriched if item["disposition"] == "PAPER_ELIGIBLE"]
    selected = paper_eligible[:final_limit]
    watch_candidates = [
        item for item in enriched
        if item["disposition"] in OBSERVATION_DISPOSITIONS
        and bool(item.get("role_evidence", {}).get("verified"))
    ][:final_limit]
    return paper_eligible, selected, watch_candidates


def validate_candidate_partitions(
    paper_eligible: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    watch_candidates: list[dict[str, Any]],
    counts: dict[str, int],
) -> None:
    selected_symbols = {str(item["symbol"]) for item in selected}
    watch_symbols = {str(item["symbol"]) for item in watch_candidates}
    overlap = selected_symbols & watch_symbols
    if overlap:
        raise RuntimeError(f"selected/watch candidate overlap: {sorted(overlap)}")
    if any(item["disposition"] != "PAPER_ELIGIBLE" for item in selected):
        raise RuntimeError("selected_candidates must contain only PAPER_ELIGIBLE items")
    if any(item["disposition"] not in OBSERVATION_DISPOSITIONS for item in watch_candidates):
        raise RuntimeError("watch_candidates must contain only REVIEW or WATCH_ONLY items")
    if any(not bool(item.get("role_evidence", {}).get("verified")) for item in watch_candidates):
        raise RuntimeError("watch_candidates must have verified business-role evidence")
    if any(float(item.get("paper_plan", {}).get("max_portfolio_weight_pct", 0.0)) != 0.0 for item in watch_candidates):
        raise RuntimeError("watch_candidates must have zero maximum portfolio weight")
    if any(float(item.get("paper_plan", {}).get("portfolio_scaled_weight_pct", 0.0)) != 0.0 for item in watch_candidates):
        raise RuntimeError("watch_candidates must have zero scaled portfolio weight")
    expected_counts = {
        "paper_eligible": len(paper_eligible),
        "selected": len(selected),
        "watch_candidates": len(watch_candidates),
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            raise RuntimeError(f"candidate count mismatch for {key}: {counts.get(key)} != {expected}")


def run(output_path: Path, enrich_limit: int = 12, final_limit: int = 5) -> dict[str, Any]:
    generated_at = datetime.now(CN_TZ)
    names = load_names()
    concepts = load_concepts()
    news = load_news()
    all_codes = sorted({code for concept in concepts if map_track(str(concept["name"])) for code in concept["codes"]})
    local_trade_date, coverage = complete_trade_date()
    trade_date = local_trade_date
    current_bars: dict[str, dict[str, float | int]] = {}
    freshness_status = "PASS"
    today_i = int(generated_at.strftime("%Y%m%d"))
    current_session_seen = int(coverage["latest_observed_date"]) == today_i
    after_close = generated_at.weekday() < 5 and (generated_at.hour, generated_at.minute) >= (15, 5)
    if current_session_seen and local_trade_date < today_i and after_close:
        current_bars = fetch_batch_current_bars(all_codes, today_i)
        required_current_coverage = max(500, int(len(all_codes) * 0.80))
        if len(current_bars) < required_current_coverage:
            raise RuntimeError(
                "current closed-session cross-sectional coverage unavailable: "
                f"quotes={len(current_bars)} required={required_current_coverage} local_complete={local_trade_date}"
            )
        trade_date = today_i
        coverage = {
            **coverage,
            "local_selected_complete_date": local_trade_date,
            "selected_complete_date": trade_date,
            "selected_coverage": len(current_bars),
            "coverage_threshold": required_current_coverage,
            "current_batch_quote_count": len(current_bars),
            "current_batch_quote_source": "Tencent qt.gtimg.cn batch close snapshot",
        }
    elif current_session_seen and local_trade_date < today_i:
        freshness_status = "PREVIOUS_COMPLETE_SESSION_INTRADAY"
    snapshots = {
        code: snapshot for code in all_codes
        if (snapshot := stock_snapshot(code, trade_date, current_bar=current_bars.get(code))) is not None
    }
    if len(snapshots) < 500:
        raise RuntimeError(f"insufficient quality-track stock coverage: {len(snapshots)}")
    sectors = rank_sectors(concepts, snapshots, news)
    strict = [item for item in sectors if item["strict_qualified"]]
    selected_sectors = strict[:5]
    watch_sector_pool = [
        item for item in sectors
        if item["event_hit_count"] > 0
        and bool(item.get("qualification_gate", {}).get("score_above_floor"))
    ]
    analysis_sectors = selected_sectors if selected_sectors else watch_sector_pool[:5]
    preliminary = preliminary_candidates(analysis_sectors, snapshots, names, news) if analysis_sectors else []
    eligible_preliminary = [item for item in preliminary if item["disposition"] == "PRELIMINARY"]

    enriched = [enrich_candidate(item) for item in eligible_preliminary[:enrich_limit]]
    status_order = {"PAPER_ELIGIBLE": 0, "REVIEW": 1, "EXCLUDE": 2}
    enriched.sort(key=lambda item: (status_order[item["disposition"]], -float(item["preliminary_score"]), item["symbol"]))
    if not strict:
        for item in enriched:
            if item["disposition"] != "EXCLUDE":
                item["review_reasons"] = sorted(set([
                    *item["review_reasons"],
                    "SECTOR_PERSISTENT_STRENGTH_NOT_CONFIRMED",
                ]))
            if item["disposition"] == "PAPER_ELIGIBLE":
                item["disposition"] = "WATCH_ONLY"
            item["paper_plan"]["max_portfolio_weight_pct"] = 0.0
        status_order["WATCH_ONLY"] = 0
        enriched.sort(key=lambda item: (status_order[item["disposition"]], -float(item["preliminary_score"]), item["symbol"]))
    paper_eligible, selected, watch_candidates = partition_candidate_lists(enriched, final_limit)
    gross_weight = sum(float(item["paper_plan"]["max_portfolio_weight_pct"]) for item in selected)
    scale = min(1.0, 60.0 / gross_weight) if gross_weight > 0 else 0.0
    for item in selected:
        raw_weight = float(item["paper_plan"]["max_portfolio_weight_pct"])
        item["paper_plan"]["portfolio_scaled_weight_pct"] = round(raw_weight * scale, 2)
    if not strict:
        run_status = "NO_TRADE"
    elif not selected:
        run_status = "NO_PAPER_ELIGIBLE"
    elif len(selected) < final_limit:
        run_status = "PARTIAL_PAPER_ELIGIBLE"
    else:
        run_status = "PASS"
    for index, item in enumerate(enriched, 1):
        item["enriched_rank"] = index
    for index, item in enumerate(selected, 1):
        item["paper_rank"] = index

    payload = {
        "workflow": "优质赛道图片工作流 V2 practical paper screener",
        "policy_version": "QUALITY-TRACK-PRACTICAL-20260722.1",
        "status": run_status,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "trade_date": str(trade_date),
        "mode": "paper_selection_only",
        "automatic_order": False,
        "freshness": {
            "status": freshness_status,
            **coverage,
            "news_index_mtime": datetime.fromtimestamp(news_source_path().stat().st_mtime, CN_TZ).isoformat(timespec="seconds"),
            "news_count": len(news),
            "partial_latest_date_excluded": coverage["latest_observed_date"] != trade_date,
            "current_batch_close_used": bool(current_bars),
        },
        "sources": {
            "names": [str(path) for path in TNF_FILES.values()],
            "concept_membership": str(INFOHARBOR),
            "daily_bars": [str(path) for path in DAY_DIRS.values()],
            "news": str(news_source_path()),
            "live_quote": "Tencent qt.gtimg.cn",
            "valuation": "Eastmoney push2delay stock endpoint",
            "financials": "Eastmoney F10 via AkShare 1.18.64",
            "announcements": "Eastmoney stock-specific announcement endpoint",
        },
        "method": {
            "event_to_track_gate": "exact local news hit plus positive complete-date concept breadth/momentum",
            "track_score": "90% * mean percentile of seven concept metrics + event bonus capped at 10",
            "company_gate": "exact concept constituent membership; liquidity; trend; no ST/limit-up/chasing",
            "financial_gate": "at least 4 of 5 structured dimensions; transport explicitly uses asset-turnover proxy",
            "risk_gate": "stock-specific announcement titles; severe terms hard exclude; medium terms review",
            "position_control": "0.8% portfolio risk budget per position; maximum 20%; 2 ATR stop capped at 8%",
        },
        "counts": {
            "equity_names": len(names),
            "concepts": len(concepts),
            "quality_track_stock_snapshots": len(snapshots),
            "eligible_quality_sectors": len(sectors),
            "strict_event_confirmed_sectors": len(strict),
            "preliminary_candidates": len(eligible_preliminary),
            "enriched_candidates": len(enriched),
            "paper_eligible": len(paper_eligible),
            "selected": len(selected),
            "watch_candidates": len(watch_candidates),
        },
        "selected_sectors": [json_safe_sector(item) for item in selected_sectors],
        "watch_sectors": [
            json_safe_sector(item) for item in sectors
            if item["event_hit_count"] > 0 and not item["strict_qualified"]
        ][:10],
        "selected_candidates": selected,
        "watch_candidates": watch_candidates,
        "portfolio_plan": {
            "gross_exposure_cap_pct": 60.0,
            "selected_gross_weight_pct": round(sum(float(item["paper_plan"]["portfolio_scaled_weight_pct"]) for item in selected), 2),
            "single_position_cap_pct": 20.0,
            "risk_budget_pct_per_position": 0.8,
            "unallocated_cash_required": True,
        },
        "enriched_candidates": enriched,
        "excluded_preliminary_sample": [item for item in preliminary if item["disposition"] == "EXCLUDE"][:20],
        "risk_boundary": "Decision support and paper execution only; no automatic order and no return guarantee.",
    }
    validate_candidate_partitions(paper_eligible, selected, watch_candidates, payload["counts"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    payload["output_path"] = str(output_path.resolve())
    payload["output_sha256"] = file_sha256(output_path)
    payload["output_size"] = output_path.stat().st_size
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="优质赛道图片工作流 V2 实战纸面选股入口")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--enrich-limit", type=int, default=12)
    parser.add_argument("--final-limit", type=int, default=5)
    args = parser.parse_args()
    result = run(args.output, args.enrich_limit, args.final_limit)
    print(
        "QUALITY_TRACK_PRACTICAL "
        f"status={result['status']} trade_date={result['trade_date']} "
        f"tracks={result['counts']['strict_event_confirmed_sectors']} "
        f"paper_eligible={result['counts']['paper_eligible']} selected={result['counts']['selected']} "
        f"watch={result['counts']['watch_candidates']} "
        f"sha256={result['output_sha256']}"
    )
    return 0 if result["status"] in {"PASS", "PARTIAL_PAPER_ELIGIBLE", "NO_TRADE"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
