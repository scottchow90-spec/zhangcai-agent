#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse, gzip, json, os, re, subprocess, sys, time, urllib.parse, urllib.request
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from poster_builder import POLICY as POSTER_POLICY, build_pages, finalize

DIRECT_GUARD = "canonical_stock_legacy_entry_direct_execution_blocked"
ROOT = Path(__file__).resolve().parents[1]
DXX_CLIENT = Path(r"D:\C盘转移\日志\codex\skills\a-share-hotspot-sentiment-analysis\scripts\duanxianxia_client.ps1")
LIANBAN_CLIENT = Path(r"D:\C盘转移\日志\codex\scripts\lianban_daily_client.py")
SUMMARY_REPORT = "RPT_DAILYBILLBOARD_DETAILSNEW"
EQUITY_PREFIXES = ("000", "001", "002", "003", "300", "301", "600", "601", "603", "605", "688", "689")
YOUZI_PROFILES = Path(r"D:\C盘转移\日志\codex\knowledge-base\personal-investment\historical-a-share-kb\data\youzi\youzi_profiles.json")
LIANBAN_SEAT_INDEX_URL = "https://lianban.net/xiwei/"
OFFICIAL_CONCEPT_URL = "https://emweb.securities.eastmoney.com/PC_HSF10/CoreConception/PageAjax?code={market}{code}"
FORBIDDEN_PLACEHOLDER_TEXT = ("未可靠识别", "未识别", "其他主题", "题材识别不足", "方向识别不足", "无可靠题材标签", "默认结论", "固定措辞", "兜底判断")
DIRECTION_KEYWORDS = {
    "科技硬件": ("芯片", "半导体", "先进封装", "PCB", "通信", "CPO", "MPO", "算力", "液冷", "洁净室", "玻璃基板", "光模块", "服务器", "AI"),
    "医药生物": ("创新药", "医药", "制药", "生物"),
    "电力设备": ("特高压", "智能电网", "电网", "电力设备", "新能源"),
    "农业消费": ("农业", "种业", "食品", "消费"),
}
BUSINESS_QUANTUM = Decimal("0.000000000001")

def _business_decimal(value: Any) -> Decimal:
    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"invalid_business_number:{value!r}") from exc
    if not number.is_finite():
        raise ValueError(f"non_finite_business_number:{value!r}")
    return number

def _decimal_sum(values: Any) -> Decimal:
    with localcontext() as context:
        context.prec = 50
        return sum((_business_decimal(value) for value in values), Decimal(0))

def _decimal_divide(value: Any, total: Any) -> Decimal:
    with localcontext() as context:
        context.prec = 50
        return _business_decimal(value) / _business_decimal(total)

def quantize_business_float(value: Any) -> float:
    with localcontext() as context:
        context.prec = 50
        normalized = _business_decimal(value).quantize(
            BUSINESS_QUANTUM,
            rounding=ROUND_HALF_EVEN,
        )
    return float(normalized)

def fetch_json(url: str, retries: int = 3) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json,text/plain,*/*"})
    error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                body = response.read()
                if body.startswith(b"\x1f\x8b"):
                    body = gzip.decompress(body)
                return json.loads(body.decode("utf-8-sig"))
        except Exception as exc:
            error = exc
            if attempt + 1 < retries: time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"fetch_failed:{url}:{type(error).__name__}:{error}")

def fetch_text(url: str, retries: int = 3) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html,application/xhtml+xml,*/*"})
    error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                return response.read().decode("utf-8-sig", errors="replace")
        except Exception as exc:
            error = exc
            if attempt + 1 < retries: time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"fetch_failed:{url}:{type(error).__name__}:{error}")

def summary_url(trade_date: str) -> str:
    params = {"sortColumns": "BILLBOARD_NET_AMT", "sortTypes": "-1", "pageSize": "5000", "pageNumber": "1", "reportName": SUMMARY_REPORT, "columns": "ALL", "source": "WEB", "client": "WEB", "filter": f"(TRADE_DATE<='{trade_date}')(TRADE_DATE>='{trade_date}')"}
    return "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(params)

def resolve_latest_date() -> tuple[str, dict[str, Any], str]:
    current = date.today()
    for offset in range(12):
        candidate = (current - timedelta(days=offset)).isoformat(); url = summary_url(candidate); payload = fetch_json(url)
        if ((payload.get("result") or {}).get("data") or []): return candidate, payload, url
    raise RuntimeError("latest_longhubang_trade_date_not_found")

def select_equities(rows: list[dict[str, Any]], threshold_yuan: float = 50_000_000) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for row in rows:
        code = str(row.get("SECURITY_CODE") or "").strip()
        if not re.fullmatch(r"\d{6}", code) or not code.startswith(EQUITY_PREFIXES): continue
        net = float(row.get("BILLBOARD_NET_AMT") or row.get("NET_BS_AMT") or 0)
        if net <= threshold_yuan: continue
        reason = str(row.get("EXPLANATION") or row.get("EXPLAIN") or "").strip()
        item = {"code": code, "name": str(row.get("SECURITY_NAME_ABBR") or "").strip(), "net_amount": net, "buy_amount": float(row.get("BILLBOARD_BUY_AMT") or row.get("SUM_BUY_AMT") or 0), "sell_amount": float(row.get("BILLBOARD_SELL_AMT") or row.get("SUM_SELL_AMT") or 0), "reason": reason, "three_day": any(token in reason for token in ("连续三个交易日", "连续3个交易日", "三个交易日内"))}
        if code not in selected or net > selected[code]["net_amount"]: selected[code] = item
    return sorted(selected.values(), key=lambda item: item["net_amount"], reverse=True)

def details_url(report: str, trade_date: str, code: str, sort_column: str) -> str:
    params = {"sortColumns": sort_column, "sortTypes": "-1", "pageSize": "50", "pageNumber": "1", "reportName": report, "columns": "ALL", "filter": f"(TRADE_DATE='{trade_date}')(SECURITY_CODE=\"{code}\")"}
    return "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(params)

def normalize_seats(container: Any) -> list[dict[str, Any]]:
    if not isinstance(container, list): return []
    result = []
    for row in container:
        name = str(row.get("OPERATEDEPT_NAME") or row.get("交易营业部名称") or "").strip()
        if not name: continue
        buy = float(row.get("BUY") or row.get("买入金额") or 0); sell = float(row.get("SELL") or row.get("卖出金额") or 0)
        net = float(row.get("NET") if row.get("NET") is not None else row.get("净额") if row.get("净额") is not None else buy - sell)
        result.append({"name": name, "buy": buy, "sell": sell, "net": net})
    return result

def coalesce_seats(seats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for seat in seats:
        name = str(seat.get("name") or "").strip()
        if not name: continue
        row = merged.setdefault(name, {"name": name, "buy": 0.0, "sell": 0.0, "net": 0.0})
        row["buy"] += float(seat.get("buy") or 0); row["sell"] += float(seat.get("sell") or 0)
    for row in merged.values(): row["net"] = row["buy"] - row["sell"]
    return list(merged.values())

def normalize_seat_name(value: str) -> str:
    text = str(value or "").strip().replace("（", "(").replace("）", ")")
    text = re.sub(r"\([^)]*(?:公开归因|席位标签)[^)]*\)", "", text)
    for token in ("股份有限公司", "有限责任公司", "有限公司"): text = text.replace(token, "")
    text = re.sub(r"证券营业部$", "", text)
    return re.sub(r"[\s·•,，。:：;；/\\()（）\-]", "", text).casefold()

class _SeatIndexParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(); self._href: str | None = None; self._parts: list[str] = []; self.items: list[dict[str, str]] = []
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "a": return
        href = dict(attrs).get("href") or ""
        if re.search(r"/xiwei/[0-9a-f]{8,}\.html$", href): self._href = urllib.parse.urljoin(LIANBAN_SEAT_INDEX_URL, href); self._parts = []
    def handle_data(self, data: str) -> None:
        if self._href: self._parts.append(data)
    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() != "a" or not self._href: return
        name = re.sub(r"\s+", " ", "".join(self._parts)).strip()
        name = re.split(r"上榜\s*\d+\s*日", name, maxsplit=1)[0].strip()
        if name: self.items.append({"name": name, "url": self._href})
        self._href = None; self._parts = []

def load_youzi_profiles(path: Path = YOUZI_PROFILES) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig")); profiles = payload.get("游资档案") if isinstance(payload, dict) else None
    if not isinstance(profiles, list) or not profiles: raise RuntimeError("youzi_profile_catalog_invalid")
    return profiles

def fetch_public_seats() -> list[dict[str, str]]:
    parser = _SeatIndexParser(); parser.feed(fetch_text(LIANBAN_SEAT_INDEX_URL)); deduped: dict[str, dict[str, str]] = {}
    for item in parser.items:
        key = normalize_seat_name(item["name"])
        if key: deduped.setdefault(key, item)
    if not deduped: raise RuntimeError("lianban_public_seat_catalog_empty")
    return list(deduped.values())

def build_seat_catalog(profiles: list[dict[str, Any]], public_seats: list[dict[str, Any]]) -> dict[str, Any]:
    named: dict[str, dict[str, Any]] = {}; public: dict[str, dict[str, Any]] = {}; profile_by_url: dict[str, str] = {}
    for profile in profiles:
        label = str(profile.get("name") or profile.get("规范名称") or profile.get("标准化名称") or "").strip(); url = str(profile.get("url") or profile.get("龙虎榜聚合详情网址") or "").strip()
        if label and url.startswith("http"): profile_by_url[url] = label
        seats = profile.get("seats") or profile.get("关联席位") or []
        for seat in seats if isinstance(seats, list) else []:
            key = normalize_seat_name(str(seat))
            if key and label: named.setdefault(key, {"label": label, "source": "本机公开游资档案", "url": url or None})
    for item in public_seats:
        name = str(item.get("name") or "").strip(); url = str(item.get("url") or "").strip(); key = normalize_seat_name(name)
        if not key: continue
        if url in profile_by_url: named.setdefault(key, {"label": profile_by_url[url], "source": "连板网公开席位页", "url": url})
        public.setdefault(key, {"label": name, "source": "连板网公开席位页", "url": url or None})
    return {"named": named, "public": public, "profile_count": len(profiles), "public_seat_count": len(public_seats)}

def attribute_seat(name: str, catalog: dict[str, Any]) -> dict[str, Any]:
    value = str(name or "").strip(); key = normalize_seat_name(value)
    if "机构专用" in value or "机构投资者" in value: return {"category": "institution", "label": "机构席位", "match_method": "seat_type_exact", "source": "东方财富席位名称", "url": None}
    if value in ("沪股通专用", "深股通专用"): return {"category": "northbound", "label": "沪深股通席位", "match_method": "seat_type_exact", "source": "东方财富席位名称", "url": None}
    match = (catalog.get("named") or {}).get(key)
    if match: return {"category": "named_trader", "label": match["label"], "match_method": "full_normalized_name_exact", "source": match["source"], "url": match.get("url")}
    match = (catalog.get("public") or {}).get(key)
    if match: return {"category": "public_active_seat", "label": match["label"], "match_method": "full_normalized_name_exact", "source": match["source"], "url": match.get("url")}
    if not value: return {"category": "missing", "label": "席位数据缺失", "match_method": "no_seat_data", "source": "东方财富", "url": None}
    return {"category": "ordinary_brokerage", "label": "普通营业部（公开游资名录无精确匹配）", "match_method": "full_normalized_name_no_match", "source": "本次公开游资名录精确核对", "url": None}

def summarize_seat_attribution(seats: list[dict[str, Any]], catalog: dict[str, Any]) -> dict[str, Any]:
    ranked = sorted(seats, key=lambda seat: (float(seat.get("net") or 0), float(seat.get("buy") or 0)), reverse=True)
    representative = next((seat for seat in ranked if float(seat.get("net") or 0) > 0), ranked[0] if ranked else None); matches: list[dict[str, Any]] = []
    for seat in ranked:
        attribution = attribute_seat(str(seat.get("name") or ""), catalog)
        if attribution["category"] in {"named_trader", "public_active_seat"}: matches.append({**attribution, "seat": seat["name"], "buy": seat.get("buy", 0), "sell": seat.get("sell", 0), "net": seat.get("net", 0)})
    representative_name = str((representative or {}).get("name") or ""); representative_attribution = attribute_seat(representative_name, catalog)
    representative_match = next((match for match in matches if match["seat"] == representative_name), None)
    named = [match for match in matches if match["category"] == "named_trader"]
    no_public_match = {"category": "no_public_trader_match", "label": "本股榜单无公开游资名录席位", "match_method": "all_seats_exact_scan_no_match", "source": "本次公开游资名录精确核对", "url": None}
    primary = representative_match or (named[0] if named else (matches[0] if matches else no_public_match))
    return {"representative_seat": representative_name or "席位数据缺失", "top_trader": primary["label"], "seat_category": representative_attribution["category"], "seat_attribution": primary, "representative_seat_attribution": representative_attribution, "public_trader_matches": matches, "seat_count_scanned": len(seats)}

def official_concept_url(code: str) -> str:
    market = "SH" if str(code).startswith(("600", "601", "603", "605", "688", "689")) else "SZ"
    return OFFICIAL_CONCEPT_URL.format(market=market, code=code)

def extract_official_concepts(payload: dict[str, Any]) -> dict[str, Any]:
    precise: list[str] = []
    for row in payload.get("ssbk") or []:
        name = str(row.get("BOARD_NAME") or "").strip()
        if str(row.get("IS_PRECISE") or "") == "1" and name and name not in precise: precise.append(name)
    main_business: list[str] = []
    for row in payload.get("hxtc") or []:
        if str(row.get("KEY_CLASSIF") or "").strip() != "主营业务": continue
        keyword = str(row.get("KEYWORD") or "").strip()
        if keyword and keyword not in main_business: main_business.append(keyword)
    return {"precise_concepts": precise, "main_business": main_business, "concepts": precise}

def ratio(value: Any, total: Any) -> float:
    denominator = _business_decimal(total)
    if denominator <= 0:
        return 0.0
    return quantize_business_float(_decimal_divide(value, denominator))

def pct(value: float) -> str:
    return f"{value * 100:.1f}%"

def concept_labels(value: str) -> list[str]:
    ignored = {"", "-"}
    labels: list[str] = []
    for part in re.split(r"[,，、/；;]", str(value or "")):
        label = part.strip()
        if label not in ignored and label not in labels:
            labels.append(label)
    return labels

def direction_for_theme(theme: str) -> str:
    for direction, keywords in DIRECTION_KEYWORDS.items():
        if any(keyword.casefold() in theme.casefold() for keyword in keywords): return direction
    return str(theme).strip()

def board_group(code: str) -> str:
    if str(code).startswith(("300", "301")): return "创业板"
    if str(code).startswith(("688", "689")): return "科创板"
    return "主板"

def trigger_group(record: dict[str, Any]) -> str:
    reason = str(record.get("reason") or "")
    if record.get("three_day") or any(token in reason for token in ("连续三个交易日", "连续3个交易日", "三个交易日内")): return "三日累计"
    if "换手率" in reason: return "高换手"
    if "振幅" in reason: return "高振幅"
    if "涨幅" in reason: return "上涨偏离"
    if "跌幅" in reason: return "下跌偏离"
    return reason or "上榜原因字段为空"

def _bucket_rows(records: list[dict[str, Any]], key_getter: Any) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    total = _decimal_sum(record.get("net_amount") or 0 for record in records)
    for record in records:
        key = str(key_getter(record))
        bucket = buckets.setdefault(key, {"name": key, "net_amount": Decimal(0), "stock_count": 0})
        bucket["net_amount"] = _decimal_sum((bucket["net_amount"], record.get("net_amount") or 0))
        bucket["stock_count"] += 1
    for bucket in buckets.values():
        amount = bucket["net_amount"]
        bucket["net_amount"] = quantize_business_float(amount)
        bucket["net_share"] = ratio(amount, total)
    return sorted(buckets.values(), key=lambda row: (-row["net_amount"], row["name"]))

def derive_conclusions(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records: raise ValueError("analysis_records_missing")
    ranked = sorted(records, key=lambda row: _business_decimal(row.get("net_amount") or 0), reverse=True)
    total_decimal = _decimal_sum(row.get("net_amount") or 0 for row in ranked)
    if total_decimal <= 0: raise ValueError("analysis_total_net_amount_invalid")
    total = quantize_business_float(total_decimal)
    top_share = lambda count: ratio(_decimal_sum(row.get("net_amount") or 0 for row in ranked[:count]), total_decimal)

    theme_amounts: dict[str, Decimal] = {}; theme_stocks: dict[str, set[str]] = {}; theme_covered_net = Decimal(0)
    for row in ranked:
        labels = concept_labels(str(row.get("concept") or ""))
        if not labels: continue
        net = _business_decimal(row.get("net_amount") or 0); theme_covered_net = _decimal_sum((theme_covered_net, net)); allocated = _decimal_divide(net, len(labels))
        for label in labels:
            theme_amounts[label] = _decimal_sum((theme_amounts.get(label, Decimal(0)), allocated))
            theme_stocks.setdefault(label, set()).add(str(row.get("code") or ""))
    theme_focus = [
        {"theme": theme, "allocated_net_amount": quantize_business_float(amount), "share_of_identified": ratio(amount, theme_covered_net), "stock_count": len(theme_stocks[theme])}
        for theme, amount in sorted(theme_amounts.items(), key=lambda item: (-item[1], item[0]))
    ]
    direction_amounts: dict[str, Decimal] = {}; direction_stocks: dict[str, set[str]] = {}
    for row in ranked:
        directions = sorted({direction_for_theme(label) for label in concept_labels(str(row.get("concept") or ""))})
        if not directions: continue
        net = _business_decimal(row.get("net_amount") or 0); allocated = _decimal_divide(net, len(directions))
        for direction in directions:
            direction_amounts[direction] = _decimal_sum((direction_amounts.get(direction, Decimal(0)), allocated))
            direction_stocks.setdefault(direction, set()).add(str(row.get("code") or ""))
    direction_focus = [
        {"direction": direction, "allocated_net_amount": quantize_business_float(amount), "share_of_identified": ratio(amount, theme_covered_net), "share_of_all": ratio(amount, total_decimal), "stock_count": len(direction_stocks[direction])}
        for direction, amount in sorted(direction_amounts.items(), key=lambda item: (-item[1], item[0]))
    ]

    def seat_kind(row: dict[str, Any]) -> str:
        category = str(row.get("seat_category") or ""); trader = str(row.get("top_trader") or "")
        if category == "northbound": return "沪深股通代表席位"
        if category == "institution": return "机构代表席位"
        if category in {"named_trader", "public_active_seat"}: return "公开游资席位"
        if category == "ordinary_brokerage": return "普通营业部"
        if category == "missing": return "席位数据缺失"
        if trader.startswith("北向"): return "沪深股通代表席位"
        if trader.startswith("机构"): return "机构代表席位"
        if trader and "普通营业部" not in trader and "未" not in trader: return "公开游资席位"
        return "普通营业部"

    seats = _bucket_rows(ranked, seat_kind); boards = _bucket_rows(ranked, lambda row: board_group(str(row.get("code") or ""))); triggers = _bucket_rows(ranked, trigger_group)
    seat_map = {row["name"]: row for row in seats}; board_map = {row["name"]: row for row in boards}; trigger_map = {row["name"]: row for row in triggers}
    north_share = quantize_business_float((seat_map.get("沪深股通代表席位") or {}).get("net_share", 0)); institution_share = quantize_business_float((seat_map.get("机构代表席位") or {}).get("net_share", 0)); public_trader_share = quantize_business_float((seat_map.get("公开游资席位") or {}).get("net_share", 0)); ordinary_share = quantize_business_float((seat_map.get("普通营业部") or {}).get("net_share", 0))
    growth_share = quantize_business_float(_decimal_sum(((board_map.get("创业板") or {}).get("net_share", 0), (board_map.get("科创板") or {}).get("net_share", 0))))
    three_day_rows = [row for row in ranked if row.get("three_day")]; three_day_net = _decimal_sum(row.get("net_amount") or 0 for row in three_day_rows); three_day_share = ratio(three_day_net, total_decimal)
    theme_coverage = ratio(theme_covered_net, total_decimal); top1 = top_share(1); top3 = top_share(3); top5 = top_share(5)

    concentration_label = "高度集中" if top3 >= 0.65 else "中度集中" if top3 >= 0.45 else "相对分散"
    board_label = "偏高弹性成长" if growth_share >= 0.55 else "偏主板权重" if growth_share <= 0.35 else "主板与成长均衡"
    persistence_label = "延续性较强" if three_day_share >= 0.35 else "延续性一般" if three_day_share >= 0.15 else "延续性偏弱"
    if not theme_focus or not direction_focus: raise ValueError("analysis_precise_concepts_missing")
    theme_evidence = "、".join(f"{row['theme']} {pct(row['share_of_identified'])}({row['stock_count']}股)" for row in theme_focus[:3])
    dominant_direction = direction_focus[0]
    direction_label = f"大资金金额主攻{dominant_direction['direction']}" if dominant_direction["share_of_all"] >= 0.45 else f"{dominant_direction['direction']}相对领先但方向不集中"
    single_driver = next((row for row in theme_focus if row["stock_count"] == 1 and row["share_of_identified"] >= 0.15), None)
    driver_note = f"；{single_driver['theme']} {pct(single_driver['share_of_identified'])}由单股驱动" if single_driver else ""
    trigger_top = triggers[0]
    seat_top = sorted(seats, key=lambda row: (-float(row["net_share"]), row["name"]))[0]
    seat_label = f"{seat_top['name']}对应标的净买额占比最高，为{pct(float(seat_top['net_share']))}"
    if trigger_top["name"] == "上涨偏离": trigger_label = "偏进攻与价格加速"
    elif trigger_top["name"] == "高换手": trigger_label = "偏高换手博弈"
    elif trigger_top["name"] == "三日累计": trigger_label = "偏连续趋势"
    else: trigger_label = f"以{trigger_top['name']}触发为主"

    sections = [
        {"key": "capital_concentration", "title": "资金集中度", "conclusion": f"前3股合计占{pct(top3)}，本次{len(ranked)}股净买额呈{concentration_label}。", "evidence": [f"首位{ranked[0]['name']}占{pct(top1)}，前5股占{pct(top5)}，样本净买额合计{total/100000000:.2f}亿元。"], "confidence": "HIGH", "limitations": ["只衡量本次净买额严格超过门槛的榜单样本。"]},
        {"key": "capital_focus", "title": "大资金主攻方向", "conclusion": f"{direction_label}。", "evidence": [f"{dominant_direction['direction']}占全部入选净买额{pct(dominant_direction['share_of_all'])}，覆盖{dominant_direction['stock_count']}股；细分题材为{theme_evidence}{driver_note}。"], "confidence": "HIGH" if theme_coverage >= 0.80 else "MEDIUM" if theme_coverage >= 0.60 else "LOW", "limitations": ["方向簇按公开题材关键词确定性归类；多题材股票在不同方向簇间等额分摊，避免重复计算。"]},
        {"key": "seat_style", "title": "代表席位风格", "conclusion": f"{seat_label}。", "evidence": [f"沪深股通{pct(north_share)}、机构{pct(institution_share)}、公开游资{pct(public_trader_share)}、普通营业部{pct(ordinary_share)}。"], "confidence": "HIGH", "limitations": ["逐股扫描全部买卖席位并按完整规范化名称精确核对；占比按标的净买额归类，不等于席位贡献了该股全部净买额。"]},
        {"key": "board_style", "title": "板块风格", "conclusion": f"上榜净买额结构{board_label}。", "evidence": [f"创业板与科创板合计占{pct(growth_share)}，主板占{pct(1 - growth_share)}。"], "confidence": "HIGH", "limitations": ["板块风格按证券代码板别划分。"]},
        {"key": "persistence", "title": "持续性", "conclusion": f"三日累计信号显示{persistence_label}。", "evidence": [f"三日累计上榜{len(three_day_rows)}股，对应净买额占{pct(three_day_share)}。"], "confidence": "HIGH", "limitations": ["单日龙虎榜不能替代后续交易日确认。"]},
        {"key": "trigger_style", "title": "上榜触发风格", "conclusion": f"{trigger_label}。", "evidence": [f"{trigger_top['name']}触发{trigger_top['stock_count']}股，对应净买额占{pct(float(trigger_top['net_share']))}。"], "confidence": "HIGH", "limitations": ["触发类型依据交易所公开上榜原因归类。"]},
        {"key": "risk_boundary", "title": "证据边界", "conclusion": f"精确题材覆盖{pct(theme_coverage)}，普通营业部对应标的占{pct(ordinary_share)}；结论只描述{len(ranked)}股当日榜单结构。", "evidence": [f"三日累计样本{len(three_day_rows)}股；全部题材金额均来自本次逐股精确概念，游资归属采用完整席位名称核对。"], "confidence": "HIGH", "limitations": ["单日龙虎榜不能外推为后续行情，也不构成交易建议。"]},
    ]
    poster_bullets = [
        f"集中度：前3股占{pct(top3)}，资金{concentration_label}",
        f"主攻方向：{dominant_direction['direction']}{pct(dominant_direction['share_of_all'])}（{dominant_direction['stock_count']}股）{driver_note}",
        f"席位样本：股通{pct(north_share)}、机构{pct(institution_share)}、公开游资{pct(public_trader_share)}、普通营业部{pct(ordinary_share)}",
        f"板块风格：成长板占{pct(growth_share)}，{board_label}",
        f"持续性：三日累计{len(three_day_rows)}股、占{pct(three_day_share)}，{persistence_label}",
        f"上榜风格：{trigger_top['name']}占{pct(float(trigger_top['net_share']))}，{trigger_label}",
        f"证据边界：精确题材覆盖{pct(theme_coverage)}，仅反映当日{len(ranked)}股",
    ]
    return {"schema": "LONGHUBANG_CONCLUSIONS_V1", "status": "CLEAN_PASS", "headline": f"前3股占{pct(top3)}，{dominant_direction['direction']}占{pct(dominant_direction['share_of_all'])}，成长板占{pct(growth_share)}，三日累计占{pct(three_day_share)}", "metrics": {"total_net_amount": total, "top1_net_share": top1, "top3_net_share": top3, "top5_net_share": top5, "theme_coverage_share": theme_coverage, "northbound_representative_share": north_share, "institution_representative_share": institution_share, "public_trader_representative_share": public_trader_share, "ordinary_brokerage_representative_share": ordinary_share, "growth_board_share": growth_share, "three_day_net_share": three_day_share}, "direction_focus": direction_focus, "theme_focus": theme_focus[:5], "seat_structure": seats, "board_structure": boards, "trigger_structure": triggers, "sections": sections, "poster_bullets": poster_bullets}

def validate_analysis_payload(payload: dict[str, Any]) -> None:
    conclusions = payload.get("conclusions")
    if not isinstance(conclusions, dict): raise ValueError("analysis_conclusions_missing")
    if conclusions.get("schema") != "LONGHUBANG_CONCLUSIONS_V1" or conclusions.get("status") != "CLEAN_PASS": raise ValueError("analysis_conclusions_invalid")
    if not str(conclusions.get("headline") or "").strip(): raise ValueError("analysis_headline_missing")
    required = {"capital_concentration", "capital_focus", "seat_style", "board_style", "persistence", "trigger_style", "risk_boundary"}
    sections = conclusions.get("sections") or []; keys = {str(section.get("key")) for section in sections if isinstance(section, dict)}
    if keys != required: raise ValueError("analysis_conclusion_dimensions_incomplete")
    if any(not str(section.get("conclusion") or "").strip() or not section.get("evidence") for section in sections): raise ValueError("analysis_conclusion_evidence_missing")
    if len(conclusions.get("poster_bullets") or []) < 7: raise ValueError("analysis_poster_conclusions_incomplete")
    if int(payload.get("stock_count") or 0) != len(payload.get("stocks") or []): raise ValueError("analysis_stock_count_mismatch")
    texts: list[str] = []
    def collect(value: Any) -> None:
        if isinstance(value, str): texts.append(value)
        elif isinstance(value, dict):
            for item in value.values(): collect(item)
        elif isinstance(value, list):
            for item in value: collect(item)
    collect(payload)
    if any(token in text for text in texts for token in FORBIDDEN_PLACEHOLDER_TEXT): raise ValueError("analysis_placeholder_text_forbidden")
    for stock in payload.get("stocks") or []:
        labels = concept_labels(str(stock.get("concept") or ""))
        if not labels or any(label in {"其他", "未知", "题材股"} for label in labels): raise ValueError("analysis_placeholder_text_forbidden")
        seat_source = ((payload.get("sources") or {}).get("seats") or {})
        if seat_source and int(stock.get("seat_count_scanned") or 0) <= 0 and stock.get("representative_seat") != "席位数据缺失": raise ValueError("analysis_seat_scan_evidence_missing")
    seat_source = ((payload.get("sources") or {}).get("seats") or {})
    if seat_source and seat_source.get("all_seats_scanned") is not True: raise ValueError("analysis_full_seat_scan_not_verified")

def _powershell_quote(value: Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"

def duanxianxia_command(target: Path) -> list[str]:
    command = f"& {_powershell_quote(DXX_CLIENT)} -Dataset @('hotlist','ztplate') -Output {_powershell_quote(target)}"
    return ["powershell.exe", "-NoProfile", "-Command", command]

def load_lianban(path: Path | None, trade_date: str, run_dir: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    target = run_dir / "lianban-daily.json"
    if path:
        payload = json.loads(path.read_text(encoding="utf-8-sig")); target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        child = subprocess.run([sys.executable, str(LIANBAN_CLIENT), "--date", trade_date, "--output", str(target)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        payload = json.loads(target.read_text(encoding="utf-8")) if target.is_file() else {"status": "DEGRADED", "errors": [child.stderr]}
    items = ((payload.get("page_details") or {}).get("stock_items") or [])
    return payload, {str(item.get("code")): item for item in items}

def load_dxx(path: Path | None, run_dir: Path) -> dict[str, Any]:
    target = run_dir / "duanxianxia.json"
    if path:
        payload = json.loads(path.read_text(encoding="utf-8-sig")); target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"); return {"status": "CLEAN_PASS", "path": str(target), "fixture": True}
    try:
        child = subprocess.run(duanxianxia_command(target), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=75)
        return {"status": "CLEAN_PASS" if child.returncode == 0 and target.is_file() else "DEGRADED", "path": str(target), "returncode": child.returncode, "errors": [] if child.returncode == 0 else [child.stderr.strip()]}
    except Exception as exc:
        return {"status": "DEGRADED", "errors": [f"{type(exc).__name__}:{exc}"]}

def enrich(records: list[dict[str, Any]], trade_date: str, details_fixture: Path | None, lianban_items: dict[str, dict[str, Any]], seat_catalog: dict[str, Any], dxx_payload: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    fixture = json.loads(details_fixture.read_text(encoding="utf-8-sig")) if details_fixture else {"stocks": {}}
    fixture_stocks = fixture.get("stocks") or {}; missing = []
    for item in records:
        code = item["code"]; stored = fixture_stocks.get(code) or {}; seats = normalize_seats(stored.get("buy"))
        if not details_fixture:
            seats = []
            for report, sort in (("RPT_BILLBOARD_DAILYDETAILSBUY", "BUY"), ("RPT_BILLBOARD_DAILYDETAILSSELL", "SELL")):
                payload = fetch_json(details_url(report, trade_date, code, sort)); seats.extend(normalize_seats(((payload.get("result") or {}).get("data") or [])))
        seats = coalesce_seats(seats); seat_summary = summarize_seat_attribution(seats, seat_catalog); item.update(seat_summary)
        if details_fixture:
            concepts = stored.get("concepts") or stored.get("concept") or []
            if isinstance(concepts, str): concepts = [part for part in re.split(r"[,，、]", concepts) if part]
            concept_evidence = {"precise_concepts": list(concepts), "main_business": [], "concepts": list(concepts), "source": "offline-fixture"}
        else:
            url = official_concept_url(code); concept_evidence = extract_official_concepts(fetch_json(url)); concept_evidence["source"] = url
        concepts = concept_evidence["concepts"]
        if not concepts: raise RuntimeError(f"official_precise_concepts_missing:{code}")
        item["concept"] = "、".join(concepts[:2]); item["concept_evidence"] = concept_evidence
        lb = lianban_items.get(code) or {}
        item["theme_cross_validation"] = {"lianban": [value for value in (str(lb.get("theme") or "").strip(), str(lb.get("board") or "").strip()) if value], "duanxianxia_status": str((dxx_payload or {}).get("status") or "DEGRADED")}
        if not seats: missing.append(code)
    return records, {"status": "CLEAN_PASS" if not missing else "DEGRADED", "missing_seat_codes": missing, "seat_catalog_profile_count": seat_catalog["profile_count"], "lianban_public_seat_count": seat_catalog["public_seat_count"], "match_rule": "full_normalized_name_exact", "all_seats_scanned": True}

def write_report(payload: dict[str, Any], path: Path) -> None:
    conclusions = payload["conclusions"]
    lines = [f"# {payload['trade_date']} A股龙虎榜净买额分析", "", f"筛选口径：净买额严格大于{payload['threshold_yuan']/10000:.0f}万元；共{payload['stock_count']}股。", "", "## 核心结论", "", f"**总判断：{conclusions['headline']}。**", ""]
    for section in conclusions["sections"]:
        lines += [f"### {section['title']}", "", section["conclusion"], "", "证据：" + "；".join(section["evidence"]), "", "边界：" + "；".join(section["limitations"]), ""]
    lines += ["## 逐股证据", "", "| 股票 | 代码 | 净买额 | 代表席位 | 全席位公开游资 | 核心概念 |", "|---|---:|---:|---|---|---|"]
    for row in payload["stocks"]:
        lines.append(f"| {row['name']} | {row['code']} | {row['net_amount']/100000000:.2f}亿元 | {row['representative_seat']} | {row['top_trader']} | {row['concept']} |")
    lines += ["", "## 全席位精确核对", ""]
    for row in payload["stocks"]:
        matches = row.get("public_trader_matches") or []
        detail = "；".join(f"{match['seat']} => {match['label']}（{match['source']}）" for match in matches) if matches else "本股榜单无公开游资名录精确命中席位"
        lines.append(f"- {row['name']}（{row['code']}）：扫描{int(row.get('seat_count_scanned') or 0)}个席位；{detail}。")
    lines += ["", "注：每股全部席位均以完整规范化名称核对；普通营业部明确标注为公开游资名录无精确匹配。连板网仅作席位、题材与情绪补充旁证。"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--run-dir", required=True); parser.add_argument("--date"); parser.add_argument("--threshold-yuan", type=float, default=50_000_000); parser.add_argument("--summary-fixture"); parser.add_argument("--details-fixture"); parser.add_argument("--duanxianxia-fixture"); parser.add_argument("--lianban-fixture"); parser.add_argument("--poster-draft", action="store_true"); parser.add_argument("--inspection-json")
    args = parser.parse_args(); run_dir = Path(args.run_dir).resolve(); run_dir.mkdir(parents=True, exist_ok=True)
    if args.summary_fixture:
        summary = json.loads(Path(args.summary_fixture).read_text(encoding="utf-8-sig")); trade_date = args.date or str(summary["result"]["data"][0]["TRADE_DATE"])[:10]; source_url = "offline-fixture"
    elif args.date:
        trade_date = args.date; source_url = summary_url(trade_date); summary = fetch_json(source_url)
    else: trade_date, summary, source_url = resolve_latest_date()
    rows = ((summary.get("result") or {}).get("data") or []); records = select_equities(rows, args.threshold_yuan)
    if not records: raise RuntimeError("no_equities_above_threshold")
    lianban, lianban_items = load_lianban(Path(args.lianban_fixture) if args.lianban_fixture else None, trade_date, run_dir)
    dxx = load_dxx(Path(args.duanxianxia_fixture) if args.duanxianxia_fixture else None, run_dir)
    profiles = load_youzi_profiles(); public_seats = fetch_public_seats(); seat_catalog = build_seat_catalog(profiles, public_seats)
    records, seat_status = enrich(records, trade_date, Path(args.details_fixture) if args.details_fixture else None, lianban_items, seat_catalog, dxx)
    payload = {"schema": "A_SHARE_LONGHUBANG_ANALYSIS_V1", "status": "CLEAN_PASS", "trade_date": trade_date, "threshold_yuan": args.threshold_yuan, "stock_count": len(records), "sources": {"eastmoney": {"status": "CLEAN_PASS", "url": source_url, "concept_method": "逐股东方财富核心题材精确标签"}, "seats": seat_status, "youzi_profiles": {"status": "CLEAN_PASS", "path": str(YOUZI_PROFILES), "profile_count": len(profiles)}, "lianban_seat_index": {"status": "CLEAN_PASS", "url": LIANBAN_SEAT_INDEX_URL, "seat_count": len(public_seats)}, "duanxianxia": dxx, "lianban": {"status": lianban.get("status", "DEGRADED"), "attribution": "连板网", "source_url": ((lianban.get("sources") or {}).get("page") or {}).get("url")}}, "poster_policy": POSTER_POLICY, "stocks": records, "conclusions": derive_conclusions(records)}
    validate_analysis_payload(payload)
    (run_dir / "longhubang-analysis.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); write_report(payload, run_dir / "longhubang-analysis.md")
    if args.poster_draft:
        draft = build_pages(records, trade_date, args.threshold_yuan, payload["conclusions"], run_dir); payload["poster_draft"] = draft["manifest"]
        if args.inspection_json: payload["posters"] = [str(path) for path in finalize(draft, Path(args.inspection_json), run_dir)]
        (run_dir / "longhubang-analysis.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"schema": payload["schema"], "status": "CLEAN_PASS", "trade_date": trade_date, "stock_count": len(records), "analysis": str(run_dir / "longhubang-analysis.json"), "report": str(run_dir / "longhubang-analysis.md"), "poster_draft": payload.get("poster_draft"), "posters": payload.get("posters", [])}, ensure_ascii=False))
    return 0

if __name__ == "__main__" and os.environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print(DIRECT_GUARD, file=sys.stderr); raise SystemExit(2)
if __name__ == "__main__": raise SystemExit(main())
