#!/usr/bin/env python3
"""Public, read-only acquisition fallback for the merged sentiment workflow."""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import datetime as dt
import hashlib
import html
import json
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin, urlparse

import requests

from sentiment_quality_contracts import (
    REQUIRED_CAPTURE_FILES,
    validate_capture_accounting,
    validate_heat_evidence,
    validate_sentiment_record,
)


FALLBACK_CHANNEL = "public_readonly_fallback"
PUBLIC_READONLY_SNAPSHOT_DIR_ENV = "CODEX_PUBLIC_READONLY_SNAPSHOT_DIR"
USER_AGENT = "Mozilla/5.0"
UAPIS_HOTBOARD = "https://uapis.cn/api/v1/misc/hotboard"
SINA_ROLL = "https://feed.mix.sina.com.cn/api/roll/get"
XUEQIU_HOME = "https://xueqiu.com/hot/stock"
XUEQIU_HOT = "https://stock.xueqiu.com/v5/stock/hot_stock/list.json"
XUEQIU_TIMELINE = "https://xueqiu.com/v4/statuses/public_timeline_by_category.json"
TGB_HOME = "https://www.tgb.cn/"
TGB_MOBILE_HOME = "https://m.tgb.cn/"
GUBA_ROOT = "https://guba.eastmoney.com/"
WEIBO_FINANCE = "https://weibo.com/hot/new?gid=1028031288"
ZHIHU_STOCK = "https://www.zhihu.com/topic/19570359/hot"
WEIBO_HOT_BAND = "https://weibo.com/ajax/statuses/hot_band"
WEIBO_HOT_FEED = "https://weibo.com/ajax/feed/hottimeline"
WEIBO_VISITOR_SEED = "https://s.weibo.com/top/summary?cate=tech"
WEIBO_STOCK_GROUP_ID = "1028031288"
WEIBO_STOCK_CONTAINER_ID = "102803_ctg1_1288_-_ctg1_1288"
ZHIHU_HOT_LIST = "https://api.zhihu.com/topstory/hot-lists/total"
ZHIHU_RECOMMEND = "https://api.zhihu.com/topstory/recommend"
JIUYANGONGSHE_HOME = "https://www.jiuyangongshe.com/study_hot"
CLS_HOME = "https://www.cls.cn/telegraph"
CLS_TELEGRAPH_CACHE = "https://www.cls.cn/api/cache"
CLS_TELEGRAPH_ROLL = "https://www.cls.cn/v1/roll/get_roll_list"
JIN10_HOME = "https://www.jin10.com/"
JIN10_FLASH = "https://flash-api.jin10.com/get_flash_list"
JIN10_APP_ID = "SO1EJGmNgCtmpcPF"
BUSINESS_SOCIETY_HOME = "https://www.100ppi.com/"
BUSINESS_SOCIETY_NEWS = "https://www.100ppi.com/news/"
BUSINESS_SOCIETY_DOMAINS = ("100ppi.com", "ppi.cn")
MANDATORY_SITE_MINIMUM = 10
GUBA_ARTICLE_LIST = (
    "https://gbapi.eastmoney.com/webarticlelist/api/Article/Articlelist"
)
DUANXIANXIA_CLIENT = Path(
    r"D:\C盘转移\日志\codex\skills\a-share-hotspot-sentiment-analysis\scripts\duanxianxia_client.ps1"
)
DEFAULT_REVIEW_ROOT = Path(r"D:\C盘转移\日志\codex\reports")
FINANCE_TERMS = (
    "A股",
    "股票",
    "股市",
    "指数",
    "基金",
    "黄金",
    "半导体",
    "芯片",
    "AI",
    "机器人",
    "医药",
    "成交额",
    "涨停",
    "资金",
    "公告",
    "业绩",
    "订单",
    "政策",
)

WEIBO_A_SHARE_TERMS = (
    "A股",
    "股票",
    "股民",
    "上市公司",
    "科创板",
    "创业板",
    "涨停",
    "跌停",
    "跳水",
    "市值",
    "IPO",
    "发行",
    "打新",
    "中签",
    "成交量",
    "碳排放权",
    "半导体",
    "芯片",
    "存储",
    "机器人",
    "人工智能",
    "DeepSeek",
    "华为",
    "汽车",
    "新能源",
    "医药",
    "银行",
    "房地产",
    "消费",
    "教育",
    "餐饮",
    "食品",
    "电商",
    "直播",
    "影视",
    "电影",
    "剧集",
    "综艺",
    "游戏",
    "电竞",
    "传媒",
    "船舶",
    "造船",
    "医疗",
    "白血病",
)

ZHIHU_A_SHARE_TERMS = WEIBO_A_SHARE_TERMS + (
    "腾讯",
    "小米",
    "荣耀",
    "租金",
    "餐饮",
    "贸易",
    "WTO",
    "商业",
    "经济",
    "影院",
    "票房",
    "美债",
    "国债",
    "实际利率",
    "财政收入",
    "个税",
    "涉企网络谣言",
    "顺风车",
)


def _local_now() -> dt.datetime:
    return dt.datetime.now().astimezone()


def _as_datetime(value: dt.datetime | None) -> dt.datetime:
    value = value or _local_now()
    return value if value.tzinfo else value.replace(tzinfo=_local_now().tzinfo)


def _iso(value: dt.datetime) -> str:
    return value.astimezone().isoformat(timespec="seconds")


def _clean(value: Any, limit: int = 600) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _json_get(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    session: requests.Session | None = None,
    timeout: int = 30,
) -> Any:
    client = session or requests
    response = client.get(
        url,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def _hotboard(kind: str) -> list[dict[str, Any]]:
    payload = _json_get(UAPIS_HOTBOARD, params={"type": kind})
    rows = payload.get("list") if isinstance(payload, dict) else []
    return [row for row in rows or [] if isinstance(row, dict)]


def _has_a_share_mapping(text: str, terms: tuple[str, ...]) -> bool:
    normalized = _clean(text, 5000).lower()
    return any(term.lower() in normalized for term in terms)


def _within_rolling_hours(value: int | str, hours: int = 72) -> bool:
    if not str(value).isdigit():
        return False
    observed = dt.datetime.fromtimestamp(int(value), tz=_local_now().tzinfo)
    age = _local_now() - observed
    return dt.timedelta(0) <= age <= dt.timedelta(hours=hours)


def _parse_source_datetime(value: Any, timezone: dt.tzinfo) -> dt.datetime | None:
    if isinstance(value, dt.datetime):
        parsed = value
    else:
        text = _clean(value, 100)
        if not text:
            return None
        if text.isdigit():
            timestamp = int(text)
            if timestamp > 10_000_000_000:
                timestamp /= 1000
            try:
                return dt.datetime.fromtimestamp(timestamp, tz=timezone)
            except (OSError, OverflowError, ValueError):
                return None
        normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
        try:
            parsed = dt.datetime.fromisoformat(normalized)
        except ValueError:
            parsed = None
            for format_string in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    parsed = dt.datetime.strptime(text, format_string)
                    break
                except ValueError:
                    continue
            if parsed is None:
                return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone)
    return parsed.astimezone(timezone)


def _within_event_window(
    value: Any,
    collected_at: dt.datetime,
    hours: int = 72,
) -> bool:
    observed = _parse_source_datetime(value, collected_at.tzinfo)
    if observed is None:
        return False
    age = collected_at - observed
    return dt.timedelta(0) <= age <= dt.timedelta(hours=hours)


def _official_business_url(value: Any) -> bool:
    host = urlparse(str(value or "")).netloc.casefold().removeprefix("www.")
    return any(host == domain or host.endswith("." + domain) for domain in BUSINESS_SOCIETY_DOMAINS)


def _request_business_society_page(
    session: requests.Session,
    entry_url: str,
) -> requests.Response:
    """Pass the official site's short-lived read-only cookie challenge."""
    response = session.get(
        entry_url,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    challenge = re.search(r'var\s+_0x2\s*=\s*"([0-9a-f]{16,64})"', response.text)
    if challenge:
        session.cookies.set(
            "HW_CHECK",
            challenge.group(1),
            domain=urlparse(entry_url).netloc,
            path="/",
        )
        response = session.get(
            entry_url,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        response.raise_for_status()
    if "正在进行安全检查" in response.text or len(response.content) < 2000:
        raise RuntimeError("business_society_official_page_challenge_not_cleared")
    return response


def _business_society_public(limit: int = 80) -> list[dict[str, Any]]:
    """Collect fresh official Business Society rows without preset sector mapping."""
    from bs4 import BeautifulSoup

    now = _local_now()
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    session = requests.Session()
    for entry_url in (BUSINESS_SOCIETY_NEWS, BUSINESS_SOCIETY_HOME):
        response = _request_business_society_page(session, entry_url)
        response.encoding = response.apparent_encoding or response.encoding
        soup = BeautifulSoup(response.text, "html.parser")
        for anchor in soup.select("a[href]"):
            title = _clean(anchor.get_text(" ", strip=True), 240)
            href = urljoin(entry_url, str(anchor.get("href") or ""))
            if len(title) < 6 or href in seen or not _official_business_url(href):
                continue
            context = _clean(anchor.parent.get_text(" ", strip=True) if anchor.parent else title, 800)
            date_match = re.search(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})", context)
            if date_match:
                try:
                    published = dt.datetime(
                        int(date_match.group(1)),
                        int(date_match.group(2)),
                        int(date_match.group(3)),
                        12,
                        tzinfo=now.tzinfo,
                    )
                except ValueError:
                    continue
            else:
                short_match = re.search(r"(?<!\d)(\d{1,2})[-/.月](\d{1,2})(?:日)?(?!\d)", context)
                if not short_match:
                    continue
                try:
                    published = dt.datetime(
                        now.year,
                        int(short_match.group(1)),
                        int(short_match.group(2)),
                        12,
                        tzinfo=now.tzinfo,
                    )
                except ValueError:
                    continue
                if published - now > dt.timedelta(days=2):
                    published = published.replace(year=now.year - 1)
            if not _within_event_window(published, now):
                continue
            tokens = [
                token
                for token in re.findall(r"[\u4e00-\u9fff]{2,10}", title)
                if token not in {"生意社", "商品", "市场", "行情", "价格", "最新", "资讯"}
            ]
            seen.add(href)
            rows.append({
                "title": title,
                "text": context,
                "published_at": _iso(published),
                "href": href,
                "tags": list(dict.fromkeys(tokens))[:8],
                "heat_evidence": "生意社官方商品情报或涨跌榜",
                "source_url": entry_url,
            })
            if len(rows) >= limit:
                return rows
    return rows


def _parse_weibo_hot_band(payload: Any) -> list[dict[str, Any]]:
    source_rows = ((payload or {}).get("data") or {}).get("band_list") or []
    rows = []
    for item in source_rows:
        if not isinstance(item, dict):
            continue
        title = _clean(item.get("note") or item.get("word"), 240)
        onboard_time = item.get("onboard_time")
        heat = item.get("num") or item.get("raw_hot")
        context = " ".join(
            [
                title,
                _clean(item.get("category"), 120),
                _clean(item.get("channel_type"), 120),
                _clean(item.get("flag_desc"), 120),
            ]
        )
        if (
            not title
            or not str(onboard_time).isdigit()
            or not _within_rolling_hours(onboard_time)
            or heat in ("", None)
            or not _has_a_share_mapping(context, WEIBO_A_SHARE_TERMS)
        ):
            continue
        rows.append(
            {
                "title": title,
                "url": f"https://s.weibo.com/weibo?q={quote(f'#{title}#')}",
                "text": "；".join(
                    part
                    for part in (
                        f"分类：{_clean(item.get('category'), 120)}"
                        if _clean(item.get("category"), 120)
                        else "",
                        f"频道：{_clean(item.get('channel_type'), 120)}"
                        if _clean(item.get("channel_type"), 120)
                        else "",
                    )
                    if part
                ),
                "published_at": _iso(
                    dt.datetime.fromtimestamp(
                        int(onboard_time),
                        tz=_local_now().tzinfo,
                    )
                ),
                "hot_value": f"微博热榜热度{heat}",
                "time_basis": "微博话题上榜时间（源站字段 onboard_time）",
            }
        )
    return rows


def _weibo_visitor_session() -> requests.Session:
    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/139.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": WEIBO_VISITOR_SEED,
    }
    seed = session.get(WEIBO_VISITOR_SEED, headers=headers, timeout=30)
    seed.raise_for_status()
    request_id = re.search(r'var request_id = "([^"]+)"', seed.text)
    if request_id is None:
        raise RuntimeError("weibo visitor request_id missing")
    visitor = session.post(
        "https://passport.weibo.com/visitor/genvisitor2",
        data={
            "cb": "visitor_gray_callback",
            "ver": "20250916",
            "request_id": request_id.group(1),
            "tid": "",
            "from": "weibo",
            "webdriver": "undefined",
            "rid": str(int(time.time() * 1000)),
            "return_url": WEIBO_VISITOR_SEED,
        },
        headers=headers,
        timeout=30,
    )
    visitor.raise_for_status()
    callback = re.search(
        r"visitor_gray_callback\((\{.*\})\)\s*;?",
        visitor.text,
        flags=re.S,
    )
    if callback is None:
        raise RuntimeError("weibo visitor callback missing")
    result = json.loads(callback.group(1))
    if result.get("retcode") != 20000000:
        raise RuntimeError(f"weibo visitor rejected: {result.get('retcode')}")
    return session


def _parse_weibo_stock_channel(payload: Any) -> list[dict[str, Any]]:
    source_rows = payload.get("statuses") if isinstance(payload, dict) else []
    rows = []
    for item in source_rows or []:
        if not isinstance(item, dict):
            continue
        created_at = _clean(item.get("created_at"), 80)
        try:
            published = dt.datetime.strptime(
                created_at,
                "%a %b %d %H:%M:%S %z %Y",
            )
        except ValueError:
            continue
        if not _within_event_window(published, _local_now()):
            continue
        source_text = html.unescape(
            re.sub(
                r"<[^>]+>",
                " ",
                str(item.get("text_raw") or item.get("text") or ""),
            )
        )
        text = _clean(source_text, 1200)
        if not text or not _infer_a_share_mapping(text, source_key="weibo"):
            continue
        user = item.get("user") if isinstance(item.get("user"), dict) else {}
        user_id = str(user.get("idstr") or user.get("id") or "").strip()
        mblogid = str(item.get("mblogid") or "").strip()
        if not user_id or not mblogid:
            continue
        title = _clean(re.sub(r"https?://\S+", "", text), 220)
        rows.append(
            {
                "title": title,
                "url": f"https://weibo.com/{user_id}/{mblogid}",
                "text": text,
                "published_at": _iso(published),
                "hot_value": (
                    f"微博股市频道点赞{int(item.get('attitudes_count') or 0)}；"
                    f"评论{int(item.get('comments_count') or 0)}；"
                    f"转发{int(item.get('reposts_count') or 0)}"
                ),
                "time_basis": "微博原帖发布时间（源站字段 created_at）",
            }
        )
    return rows


def _weibo_stock_channel(limit: int = 50) -> list[dict[str, Any]]:
    session = _weibo_visitor_session()
    rows: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    seen_cursors: set[str] = set()
    max_id = ""
    for page in range(3):
        response = session.get(
            WEIBO_HOT_FEED,
            params={
                "since_id": 0,
                "refresh": 1 if page == 0 else 2,
                "group_id": WEIBO_STOCK_GROUP_ID,
                "containerid": WEIBO_STOCK_CONTAINER_ID,
                "extparam": "discover|new_feed",
                "max_id": max_id,
                "count": 50,
            },
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/139.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://weibo.com/hot/search",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("ok") != 1:
            raise RuntimeError(f"weibo stock channel rejected: {payload.get('ok')}")
        for row in _parse_weibo_stock_channel(payload):
            url = row["url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            rows.append(row)
            if len(rows) >= limit:
                return rows[:limit]
        next_cursor = str(payload.get("max_id") or "").strip()
        if not next_cursor or next_cursor == "0" or next_cursor in seen_cursors:
            break
        seen_cursors.add(next_cursor)
        max_id = next_cursor
    return rows[:limit]


def _weibo_global_hot_band(limit: int = 50) -> list[dict[str, Any]]:
    response = requests.get(
        WEIBO_HOT_BAND,
        params={"type": 0},
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/139.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://weibo.com/hot/search",
        },
        timeout=30,
    )
    response.raise_for_status()
    return _parse_weibo_hot_band(response.json())[:limit]


def _weibo_hot_band(limit: int = 50) -> list[dict[str, Any]]:
    rows = _weibo_stock_channel(limit)
    if len(rows) >= MANDATORY_SITE_MINIMUM:
        return rows[:limit]
    seen_urls = {str(row.get("url") or "") for row in rows}
    for row in _weibo_global_hot_band(limit):
        url = str(row.get("url") or "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        rows.append(row)
        if len(rows) >= limit:
            break
    return rows[:limit]


def _parse_zhihu_hot_list(payload: Any) -> list[dict[str, Any]]:
    source_rows = payload.get("data") if isinstance(payload, dict) else []
    rows = []
    for item in source_rows or []:
        if not isinstance(item, dict):
            continue
        target = item.get("target") if isinstance(item.get("target"), dict) else {}
        question_id = str(target.get("id") or "").strip()
        title = _clean(target.get("title"), 240)
        excerpt = _clean(target.get("excerpt"), 1200)
        created = target.get("created")
        context = f"{title} {excerpt}"
        if (
            not question_id.isdigit()
            or not title
            or not str(created).isdigit()
            or not _within_rolling_hours(created)
            or not _infer_a_share_mapping(context, source_key="zhihu")
        ):
            continue
        rows.append(
            {
                "title": title,
                "url": f"https://www.zhihu.com/question/{question_id}",
                "text": excerpt,
                "published_at": _iso(
                    dt.datetime.fromtimestamp(
                        int(created),
                        tz=_local_now().tzinfo,
                    )
                ),
                "hot_value": "；".join(
                    part
                    for part in (
                        _clean(item.get("detail_text"), 80),
                        f"回答{int(target.get('answer_count') or 0)}",
                        f"关注{int(target.get('follower_count') or 0)}",
                    )
                    if part
                ),
                "time_basis": "知乎问题创建时间（源站字段 created）",
            }
        )
    return rows


def _parse_zhihu_recommend_payload(payload: Any) -> list[dict[str, Any]]:
    source_rows = payload.get("data") if isinstance(payload, dict) else []
    rows = []
    for item in source_rows or []:
        if not isinstance(item, dict):
            continue
        target = item.get("target") if isinstance(item.get("target"), dict) else {}
        question = (
            target.get("question")
            if isinstance(target.get("question"), dict)
            else {}
        )
        question_id = str(question.get("id") or "").strip()
        answer_id = str(target.get("id") or "").strip()
        title = _clean(question.get("title"), 240)
        excerpt = _clean(
            re.sub(
                r"<[^>]+>",
                " ",
                html.unescape(str(target.get("excerpt") or "")),
            ),
            1200,
        )
        created = target.get("created_time")
        if (
            target.get("type") != "answer"
            or not question_id.isdigit()
            or not answer_id.isdigit()
            or not title
            or not str(created).isdigit()
            or not _within_rolling_hours(created)
            or not _infer_a_share_mapping(f"{title} {excerpt}", source_key="zhihu")
        ):
            continue
        rows.append(
            {
                "title": title,
                "url": (
                    f"https://www.zhihu.com/question/{question_id}/answer/{answer_id}"
                ),
                "text": excerpt,
                "published_at": _iso(
                    dt.datetime.fromtimestamp(
                        int(created),
                        tz=_local_now().tzinfo,
                    )
                ),
                "hot_value": "；".join(
                    (
                        f"赞同{int(target.get('voteup_count') or 0)}",
                        f"评论{int(target.get('comment_count') or 0)}",
                        f"浏览{int(target.get('visited_count') or 0)}",
                    )
                ),
                "time_basis": "知乎回答创建时间（源站字段 created_time）",
            }
        )
    return rows


def _zhihu_recommend_answers(limit: int, max_pages: int = 20) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    headers = {
        "User-Agent": "ZhihuHybrid/8.50.0 (iPhone; iOS 17.0)",
        "Accept": "application/json",
        "Referer": "https://www.zhihu.com/",
    }
    url = ZHIHU_RECOMMEND
    params: dict[str, Any] | None = {"limit": 20, "action": "down"}
    rows = []
    seen_urls = set()
    for _page in range(max_pages):
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        for row in _parse_zhihu_recommend_payload(payload):
            if row["url"] in seen_urls:
                continue
            seen_urls.add(row["url"])
            rows.append(row)
            if len(rows) >= limit:
                return rows
        paging = payload.get("paging") if isinstance(payload, dict) else {}
        next_url = str((paging or {}).get("next") or "").strip()
        if (
            bool((paging or {}).get("is_end"))
            or not next_url.startswith("https://api.zhihu.com/")
            or next_url == url
        ):
            break
        url = next_url
        params = None
    return rows


def _zhihu_hot_list(limit: int = 50) -> list[dict[str, Any]]:
    response = requests.get(
        ZHIHU_HOT_LIST,
        params={"limit": max(50, limit), "reverse_order": 0},
        headers={
            "User-Agent": "ZhihuHybrid/8.50.0 (iPhone; iOS 17.0)",
            "Accept": "application/json",
            "Referer": "https://www.zhihu.com/",
        },
        timeout=30,
    )
    response.raise_for_status()
    rows = _parse_zhihu_hot_list(response.json())
    required = min(MANDATORY_SITE_MINIMUM, max(0, limit))
    if len(rows) < required:
        seen_titles = {_clean(row.get("title"), 240).casefold() for row in rows}
        supplement_limit = max(30, (required - len(rows)) * 5)
        for row in _zhihu_recommend_answers(supplement_limit, max_pages=40):
            title_key = _clean(row.get("title"), 240).casefold()
            if not title_key or title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            rows.append(row)
            if len(rows) >= required:
                break
    return rows[:limit]


def _sina_roll(limit: int = 80) -> list[dict[str, Any]]:
    payload = _json_get(
        SINA_ROLL,
        params={"pageid": 153, "lid": 2516, "num": min(100, limit), "page": 1},
    )
    rows = ((payload or {}).get("result") or {}).get("data") or []
    return [row for row in rows[:limit] if isinstance(row, dict)]


def _xueqiu_hot(limit: int = 50) -> list[dict[str, Any]]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "application/json,text/plain,*/*",
            "Referer": XUEQIU_HOME,
        }
    )
    session.get(XUEQIU_HOME, timeout=30).raise_for_status()
    payload = _json_get(
        XUEQIU_HOT,
        params={"size": limit, "_type": 12, "type": 12},
        session=session,
    )
    rows = ((payload or {}).get("data") or {}).get("items") or []
    return [row for row in rows[:limit] if isinstance(row, dict)]


def _html_links(url: str, *, min_length: int = 8) -> list[dict[str, Any]]:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(response.text, "html.parser")
        pairs = [
            (_clean(node.get_text(" ", strip=True), 240), urljoin(url, node.get("href", "")))
            for node in soup.select("a[href]")
        ]
    except Exception:
        pairs = [
            (_clean(re.sub(r"<[^>]+>", "", text), 240), urljoin(url, href))
            for href, text in re.findall(
                r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                response.text,
                flags=re.I | re.S,
            )
        ]
    seen: set[tuple[str, str]] = set()
    rows = []
    for title, href in pairs:
        key = (title, href)
        if len(title) < min_length or key in seen:
            continue
        seen.add(key)
        rows.append({"title": title, "url": href})
    return rows


def _decode_js_string(value: Any) -> str:
    text = str(value or "")
    try:
        return str(json.loads(f'"{text}"'))
    except Exception:
        return text.replace(r"\/", "/")


def _parse_tgb_mobile_home(html: str) -> list[dict[str, Any]]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for node in soup.select("div.index-content-lists[data-topicid]"):
        title_node = node.select_one(".listscontent-tittle a[href]")
        if not title_node:
            continue
        title = _clean(title_node.get_text(" ", strip=True), 240)
        href = urljoin(TGB_MOBILE_HOME, title_node.get("href", ""))
        summary_node = node.select_one(".listscontent-zaiyao")
        meta_node = node.select_one(".listscontent-data")
        if not title or not href:
            continue
        rows.append(
            {
                "title": title,
                "url": href,
                "text": _clean(
                    summary_node.get_text(" ", strip=True) if summary_node else "",
                    600,
                ),
                "hot_value": _clean(
                    meta_node.get_text(" ", strip=True) if meta_node else "",
                    160,
                ),
            }
        )
    return rows


def _parse_tgb_mobile_details(
    rows: list[dict[str, Any]],
    fetcher,
) -> list[dict[str, Any]]:
    from bs4 import BeautifulSoup

    parsed = []
    for item in rows:
        try:
            html = fetcher(str(item.get("url") or ""))
        except Exception:
            continue
        visible = _clean(BeautifulSoup(html, "html.parser").get_text(" ", strip=True), 5000)
        published = re.search(
            r"\b(\d{2})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\b",
            visible,
        )
        if not published:
            continue
        year, month, day, hour, minute, second = published.groups()
        published_at = (
            f"20{year}-{month}-{day} {int(hour):02d}:{minute}:{int(second or 0):02d}"
        )
        views = re.search(r"([\d.]+)\s*(万)?\s*次浏览", visible)
        heat = _clean(item.get("hot_value"), 160)
        if views:
            view_value = f"{views.group(1)}{'万' if views.group(2) else ''}次浏览"
            heat = "；".join(part for part in [view_value, heat] if part)
        parsed.append({**item, "published_at": published_at, "hot_value": heat})
    return parsed


def _tgb_hot(limit: int = 40) -> list[dict[str, Any]]:
    session = requests.Session()
    headers = {"User-Agent": USER_AGENT, "Referer": TGB_MOBILE_HOME}
    response = session.get(TGB_MOBILE_HOME, headers=headers, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    seeds = _parse_tgb_mobile_home(response.text)[:limit]

    def fetcher(url: str) -> str:
        detail = session.get(url, headers=headers, timeout=30)
        detail.raise_for_status()
        detail.encoding = detail.apparent_encoding or "utf-8"
        return detail.text

    return _parse_tgb_mobile_details(seeds, fetcher)


def _parse_xueqiu_timeline(payload: Any) -> list[dict[str, Any]]:
    outer_rows = payload.get("list") if isinstance(payload, dict) else []
    rows = []
    for outer in outer_rows or []:
        if not isinstance(outer, dict):
            continue
        try:
            item = json.loads(str(outer.get("data") or "{}"))
        except Exception:
            continue
        title = _clean(item.get("title") or item.get("topic_title"), 240)
        created_at = item.get("created_at")
        target = str(item.get("target") or "")
        if not title or not str(created_at).isdigit() or not target:
            continue
        published_at = _iso(
            dt.datetime.fromtimestamp(
                int(created_at) / 1000,
                tz=_local_now().tzinfo,
            )
        )
        heat = (
            f"阅读{int(item.get('view_count') or 0)}；"
            f"点赞{int(item.get('like_count') or 0)}；"
            f"评论{int(item.get('reply_count') or 0)}；"
            f"转发{int(item.get('retweet_count') or 0)}"
        )
        rows.append(
            {
                "title": title,
                "url": urljoin("https://xueqiu.com/", target),
                "text": _clean(item.get("description") or item.get("topic_desc"), 600),
                "published_at": published_at,
                "hot_value": heat,
            }
        )
    return rows


def _xueqiu_timeline(limit: int = 50) -> list[dict[str, Any]]:
    session = requests.Session()
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,text/plain,*/*",
        "Referer": XUEQIU_HOME,
    }
    session.get(XUEQIU_HOME, headers=headers, timeout=30).raise_for_status()
    rows = []
    seen = set()
    for category in (-1, 105):
        payload = _json_get(
            XUEQIU_TIMELINE,
            params={"category": category},
            session=session,
        )
        for item in _parse_xueqiu_timeline(payload):
            key = item["url"]
            if key in seen:
                continue
            seen.add(key)
            rows.append(item)
            if len(rows) >= limit:
                return rows
    return rows


def _parse_guba_posts(code: str, posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for post in posts:
        if not isinstance(post, dict):
            continue
        title = _clean(post.get("post_title"), 240)
        post_id = str(post.get("post_id") or "").strip()
        published_at = _clean(post.get("post_publish_time"), 80)
        if not title or not post_id.isdigit() or not published_at:
            continue
        rows.append(
            {
                "title": title,
                "url": f"{GUBA_ROOT}news,{code},{post_id}.html",
                "a_share_context": f"A股股票代码{code}",
                "published_at": published_at,
                "hot_value": (
                    f"阅读{int(post.get('post_click_count') or 0)}；"
                    f"评论{int(post.get('post_comment_count') or 0)}；"
                    f"转发{int(post.get('post_forward_count') or 0)}"
                ),
            }
        )
    return rows


def _parse_jiuyangongshe_html(html: str) -> list[dict[str, Any]]:
    matches = list(re.finditer(r'article_id:"([^"]+)"', html))
    rows = []
    for index, match in enumerate(matches):
        block = html[match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(html)]

        def field(name: str) -> str:
            found = re.search(
                rf'{re.escape(name)}:"((?:\\.|[^"\\])*)"',
                block,
                flags=re.S,
            )
            return _decode_js_string(found.group(1)) if found else ""

        def count(name: str) -> str:
            found = re.search(rf"{re.escape(name)}:(\d+)", block)
            return found.group(1) if found else ""

        title = _clean(field("title"), 240)
        published_at = _clean(field("create_time"), 80)
        article_id = match.group(1)
        if not title or not published_at:
            continue
        heat_parts = []
        for name, label in (
            ("comment_count", "评论"),
            ("collect_count", "收藏"),
            ("like_count", "点赞"),
            ("forward_count", "转发"),
        ):
            value = count(name)
            if value:
                heat_parts.append(f"{label}{value}")
        rows.append(
            {
                "title": title,
                "url": f"https://www.jiuyangongshe.com/a/{article_id}",
                "text": _clean(field("content"), 600),
                "published_at": published_at,
                "hot_value": "；".join(heat_parts),
            }
        )
    return rows


def _jiuyangongshe_hot(limit: int = 50) -> list[dict[str, Any]]:
    response = requests.get(
        JIUYANGONGSHE_HOME,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    return _parse_jiuyangongshe_html(response.text)[:limit]


def _parse_cls_payload(payload: Any) -> list[dict[str, Any]]:
    roll_data = ((payload or {}).get("data") or {}).get("roll_data") or []
    rows = []
    for item in roll_data:
        if not isinstance(item, dict):
            continue
        title = _clean(item.get("title"), 240)
        ctime = item.get("ctime")
        item_id = str(item.get("id") or "").strip()
        if not title or not str(ctime).isdigit() or not item_id.isdigit():
            continue
        subjects = "、".join(
            _clean(subject.get("subject_name"), 80)
            for subject in item.get("subjects") or []
            if isinstance(subject, dict) and _clean(subject.get("subject_name"), 80)
        )
        detail = _clean(item.get("brief") or item.get("content"), 600)
        rows.append(
            {
                "title": title,
                "url": f"https://www.cls.cn/detail/{item_id}",
                "text": "；".join(part for part in [subjects, detail] if part),
                "published_at": _iso(
                    dt.datetime.fromtimestamp(int(ctime), tz=_local_now().tzinfo)
                ),
                "hot_value": (
                    f"阅读{int(item.get('reading_num') or 0)}；"
                    f"评论{int(item.get('comment_num') or 0)}；"
                    f"分享{int(item.get('share_num') or 0)}"
                ),
            }
        )
    return rows


def _xueqiu_hot_sentiment_rows(
    rows: list[dict[str, Any]],
    observed_at: dt.datetime,
) -> list[dict[str, Any]]:
    converted = []
    for rank, item in enumerate(rows, 1):
        name = _clean(item.get("name"), 80)
        symbol = _clean(item.get("symbol") or item.get("code"), 20)
        value = item.get("value")
        try:
            heat_value = float(value)
        except (TypeError, ValueError):
            continue
        if not name or not symbol or heat_value <= 0:
            continue
        percent = item.get("percent")
        percent_text = ""
        try:
            percent_text = f"；涨跌幅{float(percent):.2f}%"
        except (TypeError, ValueError):
            pass
        converted.append({
            "title": f"{name}（{symbol}）进入雪球热股榜第{rank}位",
            "url": f"https://xueqiu.com/S/{symbol}",
            "text": f"A股股票{name}（{symbol}）当前热度值{heat_value:g}{percent_text}。",
            "a_share_context": f"A股股票{name}（{symbol}）",
            "published_at": _iso(observed_at),
            "hot_value": f"雪球热股榜第{rank}位；热度值{heat_value:g}",
            "time_basis": "雪球官方热股榜实时观察时点",
        })
    return converted


def _xueqiu_sentiment(limit: int = 80) -> list[dict[str, Any]]:
    observed_at = _local_now()
    rows = _xueqiu_timeline(limit)
    seen_urls = {str(row.get("url") or "") for row in rows}
    for row in _xueqiu_hot_sentiment_rows(_xueqiu_hot(limit), observed_at):
        url = str(row.get("url") or "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        rows.append(row)
        if len(rows) >= limit:
            break
    return rows[:limit]


def _cls_signed_params(**params: Any) -> dict[str, Any]:
    signed = {
        key: params[key]
        for key in sorted(params, key=lambda value: value.upper())
    }
    canonical = "&".join(f"{key}={value}" for key, value in signed.items())
    sha1_hex = hashlib.sha1(canonical.encode("utf-8")).hexdigest()
    signed["sign"] = hashlib.md5(sha1_hex.encode("ascii")).hexdigest()
    return signed


def _cls_telegraph(limit: int = 60) -> list[dict[str, Any]]:
    payload = _json_get(
        CLS_TELEGRAPH_CACHE,
        params={"name": "telegraph"},
        timeout=30,
    )
    rows: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    def append_rows(candidates: list[dict[str, Any]]) -> int:
        added = 0
        for row in candidates:
            url = str(row.get("url") or "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            rows.append(row)
            added += 1
            if len(rows) >= limit:
                break
        return added

    append_rows(_parse_cls_payload(payload))
    page_rows = ((payload or {}).get("data") or {}).get("roll_data") or []
    last_time = int(_local_now().timestamp())
    for item in reversed(page_rows):
        ctime = item.get("ctime") if isinstance(item, dict) else None
        if str(ctime).isdigit():
            last_time = int(ctime)
            break

    for _page in range(10):
        if len(rows) >= limit or not page_rows:
            break
        requested = min(20, limit - len(rows))
        roll_payload = _json_get(
            CLS_TELEGRAPH_ROLL,
            params=_cls_signed_params(
                app="CailianpressWeb",
                os="web",
                sv="8.7.9",
                refresh_type=1,
                rn=requested,
                last_time=last_time,
            ),
            timeout=30,
        )
        page_rows = ((roll_payload or {}).get("data") or {}).get("roll_data") or []
        parsed = _parse_cls_payload(roll_payload)
        added = append_rows(parsed)
        next_time = None
        for item in reversed(page_rows):
            ctime = item.get("ctime") if isinstance(item, dict) else None
            if str(ctime).isdigit():
                next_time = int(ctime)
                break
        if (
            added == 0
            or next_time is None
            or next_time >= last_time
        ):
            break
        last_time = next_time
    return rows[:limit]


def _parse_jin10_payload(payload: Any) -> list[dict[str, Any]]:
    source_rows = payload.get("data") if isinstance(payload, dict) else []
    rows = []
    for item in source_rows or []:
        if not isinstance(item, dict):
            continue
        detail = item.get("data") if isinstance(item.get("data"), dict) else {}
        content = _clean(detail.get("content"), 800)
        title = _clean(detail.get("title"), 240) or _clean(
            re.sub(r"^【([^】]+)】.*$", r"\1", content),
            240,
        )
        item_id = str(item.get("id") or "").strip()
        published_at = _clean(item.get("time"), 80)
        if not title or not content or not item_id or not published_at:
            continue
        remarks = item.get("remark") if isinstance(item.get("remark"), list) else []
        rows.append(
            {
                "title": title,
                "url": f"https://www.jin10.com/flash/{item_id}",
                "text": content,
                "published_at": published_at,
                "hot_value": "；".join(
                    [
                        f"重要度{int(item.get('important') or 0)}",
                        *[_clean(value, 80) for value in remarks if _clean(value, 80)],
                    ]
                ),
            }
        )
    return rows


def _jin10_flash(limit: int = 400) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    cursor = ""
    for _page in range(30):
        response = requests.get(
            JIN10_FLASH,
            params={
                "channel": "-8200",
                "vip": 1,
                "max_time": cursor,
                "limit": min(50, max(1, limit - len(rows))),
            },
            headers={
                "User-Agent": USER_AGENT,
                "Referer": JIN10_HOME,
                "x-app-id": JIN10_APP_ID,
                "x-version": "1.0.0",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        source_rows = payload.get("data") if isinstance(payload, dict) else []
        parsed = _parse_jin10_payload(payload)
        for row in parsed:
            url = str(row.get("url") or "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            rows.append(row)
            if len(rows) >= limit:
                return rows
        if not source_rows or not parsed:
            break
        next_cursor = _clean(parsed[-1].get("published_at"), 80)
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
    return rows[:limit]


def _guba_hot(xueqiu_rows: list[dict[str, Any]], limit: int = 30) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in xueqiu_rows[:8]:
        code = _clean(row.get("code") or row.get("symbol"), 20)
        code = re.sub(r"^[A-Za-z]+", "", code)
        if not re.fullmatch(r"\d{6}", code):
            continue
        try:
            payload = _json_get(
                GUBA_ARTICLE_LIST,
                params={
                    "code": code,
                    "sorttype": 1,
                    "ps": min(20, limit),
                    "from": "CommonBaPost",
                    "version": 200,
                    "product": "Guba",
                    "plat": "Web",
                },
            )
            posts = payload.get("re") if isinstance(payload, dict) else []
            for item in _parse_guba_posts(code, posts or []):
                key = (item["title"], item["url"])
                if key in seen:
                    continue
                seen.add(key)
                results.append(item)
                if len(results) >= limit:
                    return results
        except Exception:
            pass
        try:
            links = _html_links(f"{GUBA_ROOT}list,{code}.html")
        except Exception:
            continue
        for item in links:
            href = item.get("url", "")
            if "/news," not in href and "caifuhao.eastmoney.com/news/" not in href:
                continue
            key = (_clean(item.get("title"), 240), href)
            if not key[0] or key in seen:
                continue
            seen.add(key)
            results.append({**item, "a_share_context": f"A股股票代码{code}"})
            if len(results) >= limit:
                return results
    return results


def _latest_review_dir(now: dt.datetime) -> Path | None:
    target = now.strftime("%Y%m%d")
    exact = DEFAULT_REVIEW_ROOT / f"{target}_limit_up_review_closed_loop"
    if exact.is_dir():
        return exact
    candidates = sorted(
        DEFAULT_REVIEW_ROOT.glob("*_limit_up_review_closed_loop"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _closed_session_date(now: dt.datetime) -> dt.date:
    anchor = now.date()
    if now.weekday() >= 5 or now.hour < 16:
        anchor -= dt.timedelta(days=1)
    while anchor.weekday() >= 5:
        anchor -= dt.timedelta(days=1)
    return anchor


def _market_breadth_date(now: dt.datetime) -> dt.date:
    if now.weekday() < 5 and now.hour >= 16:
        return now.date()
    return _closed_session_date(now)


def _eastmoney_market_breadth() -> dict[str, int]:
    url = "https://push2delay.eastmoney.com/api/qt/clist/get"
    params = {
        "pz": 100,
        "po": 1,
        "np": 1,
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
        "fields": "f3,f12",
    }
    session = requests.Session()
    rows: dict[str, float] = {}
    total = 0
    for page in range(1, 80):
        payload = _json_get(
            url,
            params={**params, "pn": page},
            session=session,
            timeout=30,
        )
        data = (payload or {}).get("data") or {}
        if not total:
            total = int(data.get("total") or 0)
        batch = data.get("diff") or []
        for item in batch:
            if not isinstance(item, dict):
                continue
            code = _clean(item.get("f12"), 20)
            try:
                change = float(item.get("f3"))
            except (TypeError, ValueError):
                continue
            if code:
                rows[code] = change
        if not batch or (total and page * params["pz"] >= total):
            break
    if len(rows) < 3000:
        raise ValueError(f"eastmoney market breadth sample too small: {len(rows)}")
    changes = list(rows.values())
    return {
        "up": sum(change > 0 for change in changes),
        "down": sum(change < 0 for change in changes),
        "flat": sum(change == 0 for change in changes),
        "valid": len(changes),
    }


def _sina_market_breadth() -> dict[str, int]:
    import akshare as ak

    frame = ak.stock_zh_a_spot()
    changes = frame["涨跌幅"].dropna()
    if len(changes) < 3000:
        raise ValueError(f"sina market breadth sample too small: {len(changes)}")
    return {
        "up": int((changes > 0).sum()),
        "down": int((changes < 0).sum()),
        "flat": int((changes == 0).sum()),
        "valid": int(len(changes)),
    }


def _lianban_market_breadth(now: dt.datetime) -> dict[str, Any]:
    snapshot_value = _clean(os.environ.get("CODEX_LIANBAN_SNAPSHOT"), 1000)
    if not snapshot_value:
        return {}
    path = Path(snapshot_value)
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("status") != "CLEAN_PASS":
        return {}
    target = _clean(payload.get("target_date"), 20)
    session_date = _market_breadth_date(_as_datetime(now)).isoformat()
    market = payload.get("market") if isinstance(payload.get("market"), dict) else {}
    up = market.get("advancers")
    down = market.get("decliners")
    if (
        target != session_date
        or not isinstance(up, int)
        or not isinstance(down, int)
        or up <= 0
        or down <= 0
    ):
        return {}
    sources = payload.get("sources") if isinstance(payload.get("sources"), dict) else {}
    page = sources.get("page") if isinstance(sources.get("page"), dict) else {}
    return {
        "source": "连板网",
        "source_key": "lianban.net",
        "up": up,
        "down": down,
        "url": _clean(page.get("url"), 1000)
        or _clean(os.environ.get("CODEX_LIANBAN_SOURCE_URL"), 1000),
    }


def _eastmoney_fund_flow_row(
    item: dict[str, Any],
    target_date: str,
) -> dict[str, Any] | None:
    code = _clean(item.get("代码") or item.get("code"), 20)
    name = _clean(item.get("名称") or item.get("name"), 80)
    if not re.fullmatch(r"\d{6}", code):
        return None
    market = 1 if code.startswith(("6", "9")) else 0
    secid = f"{market}.{code}"
    url = "https://push2delay.eastmoney.com/api/qt/stock/fflow/daykline/get"
    payload = _json_get(
        url,
        params={
            "secid": secid,
            "lmt": 1,
            "klt": 101,
            "fields1": "f1,f2,f3,f7",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63",
        },
        timeout=30,
    )
    klines = ((payload or {}).get("data") or {}).get("klines") or []
    if not klines:
        return None
    fields = str(klines[-1]).split(",")
    if len(fields) < 13 or fields[0] != target_date:
        return None
    values = []
    for value in fields[1:]:
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            values.append("")
    return {
        "代码": code,
        "名称": name,
        "市场": "沪市" if market == 1 else "深市",
        "secid": secid,
        "ok": True,
        "source": "push2_fflow_daykline",
        "url": url,
        "日期": fields[0],
        "主力净流入": values[0],
        "小单净流入": values[1],
        "中单净流入": values[2],
        "大单净流入": values[3],
        "超大单净流入": values[4],
        "主力净占比": values[5],
        "收盘价": values[10],
        "涨跌幅": values[11],
    }


def ensure_current_local_review(
    now: dt.datetime | None = None,
    *,
    review_root: Path = DEFAULT_REVIEW_ROOT,
    ak_module: Any = None,
    fund_flow_fetcher: Any = None,
    minimum_limitup_rows: int = 10,
    minimum_lhb_rows: int = 1,
    minimum_fund_rows: int = 20,
) -> dict[str, Any]:
    now = _as_datetime(now)
    session_date = _closed_session_date(now)
    ymd = session_date.strftime("%Y%m%d")
    target_date = session_date.isoformat()
    review_dir = Path(review_root) / f"{ymd}_limit_up_review_closed_loop"
    required = {
        "limitup": review_dir / f"ak_stock_zt_pool_em_{ymd}.csv",
        "lhb": review_dir / f"ak_stock_lhb_detail_em_{ymd}.csv",
        "fund": review_dir / f"push2_fund_flow_resolved_{ymd}.csv",
    }
    if all(path.is_file() and path.stat().st_size > 100 for path in required.values()):
        return {
            "status": "EXISTING",
            "review_dir": str(review_dir),
            "date": ymd,
            "files": {key: str(path) for key, path in required.items()},
        }
    if session_date == now.date() and (now.weekday() >= 5 or now.hour < 16):
        return {
            "status": "BLOCKED",
            "reason": "current_session_not_closed",
            "review_dir": str(review_dir),
            "date": ymd,
        }
    if ak_module is None:
        import akshare as ak_module
    fund_flow_fetcher = fund_flow_fetcher or _eastmoney_fund_flow_row
    zt_frame = ak_module.stock_zt_pool_em(date=ymd)
    lhb_frame = ak_module.stock_lhb_detail_em(start_date=ymd, end_date=ymd)
    if len(zt_frame) < minimum_limitup_rows or len(lhb_frame) < minimum_lhb_rows:
        return {
            "status": "BLOCKED",
            "reason": f"review_samples_too_small:zt={len(zt_frame)},lhb={len(lhb_frame)}",
            "review_dir": str(review_dir),
            "date": ymd,
        }
    fund_rows = []
    items = zt_frame.to_dict(orient="records")
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {
            executor.submit(fund_flow_fetcher, item, target_date): item
            for item in items
        }
        for future in as_completed(futures):
            try:
                row = future.result()
            except Exception:
                row = None
            if row:
                fund_rows.append(row)
    if len(fund_rows) < minimum_fund_rows:
        return {
            "status": "BLOCKED",
            "reason": f"fund_flow_samples_too_small:{len(fund_rows)}",
            "review_dir": str(review_dir),
            "date": ymd,
        }
    import pandas as pd

    review_dir.mkdir(parents=True, exist_ok=True)
    zt_frame.to_csv(required["limitup"], index=False, encoding="utf-8-sig")
    lhb_frame.to_csv(required["lhb"], index=False, encoding="utf-8-sig")
    pd.DataFrame(fund_rows).sort_values("代码").to_csv(
        required["fund"],
        index=False,
        encoding="utf-8-sig",
    )
    return {
        "status": "CREATED",
        "review_dir": str(review_dir),
        "date": ymd,
        "counts": {
            "limitup": len(zt_frame),
            "lhb": len(lhb_frame),
            "fund": len(fund_rows),
        },
        "files": {key: str(path) for key, path in required.items()},
    }


def _duanxianxia_snapshot(out_dir: Path) -> tuple[dict[str, Any], str]:
    out_path = out_dir / "duanxianxia_public_snapshot.json"
    if not DUANXIANXIA_CLIENT.is_file():
        return {}, "duanxianxia_client_missing"
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(DUANXIANXIA_CLIENT),
            "-Output",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    if completed.returncode != 0 or not out_path.is_file():
        return {}, _clean(completed.stderr or completed.stdout, 800)
    return json.loads(out_path.read_text(encoding="utf-8-sig")), ""


def _breadth_records(now: dt.datetime) -> list[dict[str, Any]]:
    now = _as_datetime(now)
    evidence_date = _market_breadth_date(now)
    date_text = f"{evidence_date.month}月{evidence_date.day}日"
    session_date = _closed_session_date(now)
    date_key = session_date.strftime("%Y%m%d")
    review_dir = _latest_review_dir(now)
    path = review_dir / f"market_breadth_{date_key}.json" if review_dir else None
    exact: dict[str, Any] = {}
    if path and path.is_file():
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        up = data.get("up_count")
        down = data.get("down_count")
        if isinstance(up, int) and isinstance(down, int) and up > 0 and down > 0:
            exact = {
                "source": data.get("source") or "东方财富",
                "source_key": "eastmoney.com",
                "up": up,
                "down": down,
                "url": data.get("source_url") or str(path),
            }
    is_current_closed_session = (
        session_date == now.date()
        and now.weekday() < 5
        and now.hour >= 16
    )
    lianban = _lianban_market_breadth(now)
    if not is_current_closed_session and lianban:
        exact = lianban
    if not exact and is_current_closed_session:
        try:
            breadth = _eastmoney_market_breadth()
            exact = {
                "source": "东方财富全A行情逐股涨跌幅延迟节点",
                "source_key": "eastmoney.com",
                "up": breadth["up"],
                "down": breadth["down"],
                "url": "https://push2delay.eastmoney.com/api/qt/clist/get",
            }
        except Exception:
            pass
    if not exact:
        return []
    records = [{
        "source": exact["source"],
        "source_key": exact["source_key"],
        "market_date": evidence_date.isoformat(),
        "event": (
            f"{date_text}全市场上涨家数{exact['up']}、"
            f"下跌家数{exact['down']}。"
        ),
        "url": exact["url"],
    }]
    if lianban and lianban["source_key"] != exact["source_key"]:
        records.append(
            {
                "source": lianban["source"],
                "source_key": lianban["source_key"],
                "market_date": evidence_date.isoformat(),
                "event": (
                    f"{date_text}全市场上涨家数{lianban['up']}、"
                    f"下跌家数{lianban['down']}。"
                ),
                "url": lianban["url"],
            }
        )
    if not is_current_closed_session:
        can_crosscheck_previous_close = (
            now.weekday() >= 5 or (now.hour, now.minute) < (9, 30)
        )
        if (
            can_crosscheck_previous_close
            and lianban
            and exact["source_key"] == lianban["source_key"]
        ):
            try:
                breadth = _eastmoney_market_breadth()
                records.append(
                    {
                        "source": "东方财富全A行情逐股涨跌幅延迟节点",
                        "source_key": "eastmoney.com",
                        "market_date": evidence_date.isoformat(),
                        "event": (
                            f"{date_text}全市场约{breadth['down']}只个股下跌"
                            f"（有效样本{breadth['valid']}只）。"
                        ),
                        "url": "https://push2delay.eastmoney.com/api/qt/clist/get",
                    }
                )
            except Exception:
                pass
        return records
    try:
        breadth = _sina_market_breadth()
        records.append(
            {
                "source": "新浪财经",
                "source_key": "sina.com.cn",
                "market_date": evidence_date.isoformat(),
                "event": f"{date_text}全市场约{breadth['down']}只个股下跌。",
                "url": "https://hq.sinajs.cn/",
            }
        )
    except Exception:
        pass
    return records


def collect_live_payloads(work_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[str]]:
    work_dir.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    payloads: dict[str, list[dict[str, Any]]] = {}
    try:
        review = ensure_current_local_review(_local_now())
        if review.get("status") == "BLOCKED":
            errors.append(f"local_review:{review.get('reason', 'blocked')}")
    except Exception as exc:
        errors.append(f"local_review:{type(exc).__name__}:{exc}")
    collectors = {
        "sina": _sina_roll,
        "business_society": _business_society_public,
        "xhs": lambda: _hotboard("xiaohongshu"),
        "douyin": lambda: _hotboard("douyin"),
        "weibo": _weibo_hot_band,
        "zhihu": _zhihu_hot_list,
        "xueqiu": _xueqiu_sentiment,
        "tgb": _tgb_hot,
        "jiuyangongshe": _jiuyangongshe_hot,
        "cls": _cls_telegraph,
        "jin10": _jin10_flash,
    }
    for name, collector in collectors.items():
        try:
            payloads[name] = collector()
        except Exception as exc:
            payloads[name] = []
            errors.append(f"{name}:{type(exc).__name__}:{exc}")
    try:
        payloads["guba"] = _guba_hot(_xueqiu_hot())
    except Exception as exc:
        payloads["guba"] = []
        errors.append(f"guba:{type(exc).__name__}:{exc}")
    try:
        snapshot, error = _duanxianxia_snapshot(work_dir)
        if error:
            errors.append(f"duanxianxia:{error}")
        payloads["duanxianxia"] = [snapshot] if snapshot else []
    except Exception as exc:
        payloads["duanxianxia"] = []
        errors.append(f"duanxianxia:{type(exc).__name__}:{exc}")
    return payloads, _breadth_records(_local_now()), errors


def _captured_item(
    *,
    label: str,
    title: str,
    text: str,
    href: str,
    source_url: str,
    collected_at: dt.datetime,
    observed_at: str = "",
    source_key: str = "",
    rank: int | str | None = None,
    heat_evidence: str = "",
    a_share_mapping: str = "",
) -> dict[str, Any]:
    return {
        "label": label,
        "title": _clean(title, 220),
        "text": _clean(text, 800),
        "href": href,
        "capturedUrl": source_url,
        "time": observed_at or _iso(collected_at),
        "capturedAt": _iso(collected_at),
        "acquisition_mode": FALLBACK_CHANNEL,
        "source_url": source_url,
        "source_key": source_key,
        "observation_time_only": not bool(observed_at),
        "rank": rank,
        "heat_evidence": _clean(heat_evidence, 240),
        "a_share_mapping": _clean(a_share_mapping, 360),
    }


def _infer_a_share_mapping(text: str, *, source_key: str = "") -> str:
    normalized = _clean(text, 3000)
    mapping_rules = (
        (("涉企网络谣言",), "上市公司舆情与企业经营风险"),
        (("顺风车",), "汽车出行服务与平台治理"),
        (("AI制药", "创新药", "生命科学", "CRO", "中药", "医药", "医疗器械", "糖肽"), "医药板块（创新药、AI制药及生命科学服务需求提升）"),
        (("单模光纤", "光通信", "光纤", "通信设备"), "通信板块（光通信与光纤产业链；反倾销政策延续）"),
        (("存储芯片", "NAND", "半导体", "芯片"), "芯片板块（存储与半导体产业链）"),
        (("机器人", "人形机器人"), "机器人板块"),
        (("算力", "数据中心", "IDC"), "算力与数据中心板块"),
        (("电网", "绿色电力", "电力", "火电"), "电力与智能电网板块"),
        (("影视", "电影", "影院", "院线", "票房"), "文化传媒与影视院线板块"),
        (("游戏", "PlayStation", "GTA"), "游戏与数字内容板块"),
        (("美债", "实际利率", "美国国债"), "黄金与贵金属板块"),
        (("乳业", "餐饮", "零售", "消费需求", "白酒"), "大消费板块"),
        (("黄金", "金价", "贵金属"), "黄金与贵金属板块"),
        (("铝企", "铝价", "铜价", "铜企", "有色金属"), "有色金属板块"),
        (("手机集体调价", "手机品牌正式涨价", "华为、小米、荣耀"), "消费电子板块（手机及供应链）"),
        (("智能手机", "消费电子"), "消费电子板块"),
        (("脑机接口",), "脑机接口与医疗科技板块"),
        (("港口", "REITs", "钢铁"), "基础设施与交通物流板块"),
        (("列车停运", "铁路运输", "铁路物流"), "交通运输板块"),
        (("石油", "油气", "原油"), "能源与油气产业链"),
        (("关税", "外贸", "贸易谈判"), "外贸与出口产业链"),
        (("福耀玻璃",), "汽车零部件板块"),
        (("校服", "纺织服装", "服装品牌"), "纺织服装与商贸零售板块"),
        (("科大讯飞",), "A股人工智能与教育信息化板块"),
        (("外商投资企业", "股息红利不再免征个税"), "A股外资与资本市场税制"),
        (("产业转移",), "出口制造与跨境产业链"),
        (("高铁", "12306", "轨道交通"), "轨道交通与铁路装备板块"),
        (("金融行业",), "银行、证券与保险板块"),
        (("肝吸血虫", "寄生虫病"), "医药检测与公共卫生板块"),
        (("编程语言", "基础软件", "国产软件"), "信创与基础软件板块"),
        (("特斯拉", "Model3", "新能源汽车"), "新能源汽车与汽车零部件板块"),
        (("一斤粮食", "粮食价格", "农产品价格"), "农业种植与食品饮料板块"),
    )
    normalized_lower = normalized.lower()
    mapped = []
    for markers, label in mapping_rules:
        matched_marker = next(
            (marker for marker in markers if marker.lower() in normalized_lower),
            "",
        )
        if matched_marker:
            mapped.append(f"{matched_marker}：{label}")
    if mapped:
        return "；".join(dict.fromkeys(mapped))
    tgb_marker = next(
        (
            marker
            for marker in (
            "复盘",
            "情绪",
            "补跌",
            "买点",
            "仓位",
            "止损",
            "上板",
            "看盘",
            "周期出清",
            "异动",
            "实盘",
            "涨跌",
            "龙头",
            "领涨",
            "被套",
        )
            if marker in normalized
        ),
        "",
    )
    if source_key == "tgb" and tgb_marker:
        return f"{tgb_marker}：A股短线交易情绪与风险偏好"
    direct_markers = (
        "A股",
        "上市公司",
        "股票",
        "股市",
        "科创板",
        "创业板",
        "涨停",
        "跌停",
        "市值",
        "IPO",
        "证券",
        "基金",
        "板块",
        "成交额",
        "主力资金",
        "融资资金",
        "股民",
        "炒股",
        "牛市",
        "熊市",
        "股价",
        "个股",
        "持股",
        "金叉",
        "死叉",
        "MACD",
    )
    direct_marker = next(
        (marker for marker in direct_markers if marker.lower() in normalized_lower),
        "",
    )
    if direct_marker:
        return f"{direct_marker}：A股市场、上市公司或板块的直接舆情映射"
    return ""


def _capture_payload(
    *,
    site: str,
    source_url: str,
    rows: list[dict[str, Any]],
    collected_at: dt.datetime,
    errors: list[str] | None = None,
    raw_count: int | None = None,
    collection_diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "schema": "A_SHARE_PUBLIC_READONLY_CAPTURE_V1",
        "channel": FALLBACK_CHANNEL,
        "site": site,
        "source_url": source_url,
        "collectedAt": _iso(collected_at),
        "rawCount": len(rows) if raw_count is None else int(raw_count),
        "cleanCount": len(rows),
        "clean": rows,
        "errors": list(errors or []),
    }
    if collection_diagnostics is not None:
        payload["collectionDiagnostics"] = collection_diagnostics
    return payload


def _business_capture_payload(
    rows: list[dict[str, Any]],
    collected_at: dt.datetime,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    clean_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in rows:
        if not isinstance(item, dict):
            continue
        href = str(item.get("href") or item.get("url") or "")
        published_at = _clean(
            item.get("published_at")
            or item.get("publishedAt")
            or item.get("date")
            or item.get("time"),
            80,
        )
        title = _clean(item.get("title") or item.get("name"), 240)
        if (
            not title
            or href in seen
            or not _official_business_url(href)
            or not _within_event_window(published_at, collected_at)
        ):
            continue
        seen.add(href)
        clean_rows.append({
            "commodity": _clean(item.get("commodity") or item.get("product") or item.get("name"), 80),
            "title": title,
            "text": _clean(item.get("text") or item.get("summary"), 800),
            "published_at": published_at,
            "href": href,
            "tags": item.get("tags") if isinstance(item.get("tags"), list) else [],
            "heat_evidence": _clean(item.get("heat_evidence"), 240)
            or "生意社官方商品情报或涨跌榜",
            "source_url": _clean(item.get("source_url"), 1000) or BUSINESS_SOCIETY_HOME,
        })
    return {
        "schema": "A_SHARE_BUSINESS_SOCIETY_CAPTURE_V1",
        "channel": "official_public_page_readonly",
        "site": "生意社",
        "source_url": BUSINESS_SOCIETY_HOME,
        "collectedAt": _iso(collected_at),
        "rawCount": len(rows),
        "cleanCount": len(clean_rows),
        "clean": clean_rows,
        "errors": list(errors or []),
        "preset_sector_pool_used": False,
    }


def _sina_capture_rows(rows: list[dict[str, Any]], collected_at: dt.datetime) -> list[dict[str, Any]]:
    captured = []
    for item in rows[:80]:
        title = _clean(item.get("title"), 220)
        intro = _clean(item.get("intro"), 600)
        if not title:
            continue
        observed = ""
        if str(item.get("ctime", "")).isdigit():
            observed = _iso(dt.datetime.fromtimestamp(int(item["ctime"]), tz=collected_at.tzinfo))
        captured.append(
            _captured_item(
                label=_clean(item.get("media_name")) or "新浪财经",
                title=title,
                text=intro,
                href=str(item.get("url") or ""),
                source_url=SINA_ROLL,
                collected_at=collected_at,
                observed_at=observed,
                source_key="sina.com.cn",
            )
        )
    return captured


def _duanxianxia_capture_rows(payloads: dict[str, list[dict[str, Any]]], collected_at: dt.datetime) -> list[dict[str, Any]]:
    snapshots = payloads.get("duanxianxia") or []
    if not snapshots:
        return []
    datasets = snapshots[0].get("datasets") or {}
    hotlist = ((datasets.get("hotlist") or {}).get("data") or {}).get("stock_topic") or []
    rows = []
    for item in hotlist[:30]:
        title = _clean(item.get("title"), 220)
        if not title:
            continue
        rows.append(
            _captured_item(
                label="主线热点",
                title=title,
                text=f"短线侠公开接口的当日热门话题热度为{_clean(item.get('rate'), 30)}。",
                href=urljoin("https://duanxianxia.com/", str(item.get("url") or "")),
                source_url="https://duanxianxia.com/",
                collected_at=collected_at,
                source_key="duanxianxia.com",
            )
        )
    return rows


def _breadth_capture_rows(rows: list[dict[str, Any]], collected_at: dt.datetime) -> list[dict[str, Any]]:
    return [
        _captured_item(
            label=_clean(row.get("source")) or "指数宽度",
            title="A股市场宽度交叉验证",
            text=_clean(row.get("event"), 600),
            href=str(row.get("url") or ""),
            source_url=str(row.get("url") or ""),
            collected_at=collected_at,
            observed_at=_clean(row.get("market_date"), 32),
            source_key=_clean(row.get("source_key"), 80),
        )
        for row in rows
        if _clean(row.get("event"))
    ]


def _mandatory_sentiment_rows(
    key: str,
    rows: list[dict[str, Any]],
    collected_at: dt.datetime,
    diagnostics: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    source_names = {
        "tgb": "淘股吧",
        "xueqiu": "雪球",
        "weibo": "微博",
        "zhihu": "知乎",
        "guba": "东方财富股吧",
        "jiuyangongshe": "韭研公社",
        "cls": "财联社",
        "jin10": "金十数据",
    }
    source_urls = {
        "tgb": TGB_HOME,
        "xueqiu": XUEQIU_HOME,
        "weibo": WEIBO_FINANCE,
        "zhihu": ZHIHU_STOCK,
        "guba": GUBA_ROOT,
        "jiuyangongshe": JIUYANGONGSHE_HOME,
        "cls": CLS_HOME,
        "jin10": JIN10_HOME,
    }
    source = source_names[key]
    captured = []
    mapping_rejections = []
    time_window_rejections = []
    heat_rejections = []
    mapping_accepted = 0
    evaluated = 0
    for index, item in enumerate(rows, 1):
        if index > 50 and len(captured) >= MANDATORY_SITE_MINIMUM:
            break
        evaluated = index
        title = _clean(item.get("title") or item.get("name"), 220)
        if not title:
            mapping_rejections.append({
                "rank": index,
                "title": "",
                "href": str(item.get("url") or item.get("href") or ""),
                "reason": "missing_title",
            })
            continue
        observed_at = _clean(
            item.get("published_at")
            or item.get("publishedAt")
            or item.get("publish_time")
            or item.get("publishTime")
            or item.get("datetime")
            or item.get("date_time")
            or item.get("time"),
            80,
        )
        if not observed_at and str(item.get("ctime", "")).isdigit():
            observed_at = _iso(
                dt.datetime.fromtimestamp(
                    int(item["ctime"]),
                    tz=collected_at.tzinfo,
                )
            )
        if not _within_event_window(observed_at, collected_at):
            time_window_rejections.append({
                "rank": index,
                "title": title,
                "href": str(item.get("url") or item.get("href") or ""),
                "published_at": observed_at,
                "reason": (
                    "outside_rolling_72_hours"
                    if observed_at
                    else "missing_published_at"
                ),
            })
            continue
        heat = item.get("hot_value") or item.get("value") or ""
        source_detail = _clean(
            ((item.get("extra") or {}).get("desc") if isinstance(item.get("extra"), dict) else "")
            or item.get("summary")
            or item.get("text"),
            500,
        )
        context_detail = _clean(item.get("a_share_context"), 200)
        detail = "；".join(
            part for part in (source_detail, context_detail) if part
        )
        a_share_mapping = _infer_a_share_mapping(
            f"{title} {detail}",
            source_key=key,
        )
        if not a_share_mapping:
            mapping_rejections.append({
                "rank": index,
                "title": title,
                "href": str(item.get("url") or item.get("href") or ""),
                "reason": "no_a_share_mapping",
            })
            continue
        mapping_accepted += 1
        heat_evidence = (
            f"站内公开热度{heat}"
            if heat not in ("", None)
            else f"站内高热页面第{index}位"
        )
        heat_quality = validate_heat_evidence(source, heat_evidence, index)
        if not heat_quality["ok"]:
            heat_rejections.append({
                "rank": index,
                "title": title,
                "href": str(item.get("url") or item.get("href") or ""),
                "heat_evidence": heat_evidence,
                "reasons": heat_quality["reasons"],
            })
            continue
        text = (
            f"{source}A股高热舆情第{index}位为“{title}”，"
            f"{heat_evidence}。{detail} A股映射：{a_share_mapping}"
        )
        href = str(item.get("url") or item.get("href") or "")
        if not href.startswith(("http://", "https://")):
            href = urljoin(source_urls[key], href)
        captured_item = _captured_item(
                label=source,
                title=title,
                text=text,
                href=href,
                source_url=source_urls[key],
                collected_at=collected_at,
                observed_at=observed_at,
                source_key=re.sub(r"^www\.", "", source_urls[key].split("/")[2]),
                rank=index,
                heat_evidence=heat_evidence,
                a_share_mapping=a_share_mapping,
            )
        captured_item["source_event_text"] = f"{title} {detail}".strip()
        captured.append(captured_item)
    if diagnostics is not None:
        mapping_evaluated = evaluated - len(time_window_rejections)
        diagnostics.update({
            "collector_returned": len(rows),
            "mapping_evaluated": mapping_evaluated,
            "mapping_accepted": mapping_accepted,
            "rejected_by_mapping": mapping_evaluated - mapping_accepted,
            "heat_rejected": len(heat_rejections),
            "heat_rejections": heat_rejections,
            "quality_candidate_accepted": len(captured),
            "rejected_by_time_window": len(time_window_rejections),
            "not_evaluated_due_limit": max(0, len(rows) - evaluated),
            "mapping_rejections": mapping_rejections,
            "time_window_rejections": time_window_rejections,
        })
    return captured


def _write_json_text(path: Path, payload: dict[str, Any]) -> None:
    io_path = Path(path)
    raw_path = os.path.abspath(str(io_path))
    if os.name == "nt" and len(raw_path) >= 260 and not raw_path.startswith("\\\\?\\"):
        if raw_path.startswith("\\\\"):
            raw_path = "\\\\?\\UNC\\" + raw_path[2:]
        else:
            raw_path = "\\\\?\\" + raw_path
        io_path = Path(raw_path)
    io_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _fresh_current_task_capture_rows(
    key: str,
    *,
    site: str,
    source_url: str,
    collected_at: dt.datetime,
) -> list[dict[str, Any]]:
    root_value = _clean(os.environ.get(PUBLIC_READONLY_SNAPSHOT_DIR_ENV), 1000)
    if not root_value:
        return []
    path = Path(root_value) / f"{key}.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if (
        payload.get("schema") != "A_SHARE_PUBLIC_READONLY_CAPTURE_V1"
        or payload.get("channel") != FALLBACK_CHANNEL
        or payload.get("site") != site
        or payload.get("source_url") != source_url
    ):
        return []
    try:
        snapshot_at = _as_datetime(
            dt.datetime.fromisoformat(str(payload.get("collectedAt") or ""))
        )
    except ValueError:
        return []
    age_seconds = (collected_at - snapshot_at).total_seconds()
    if age_seconds < -60 or age_seconds > 30 * 60:
        return []

    rows = []
    for item in payload.get("clean") or []:
        if not isinstance(item, dict) or item.get("observation_time_only") is True:
            continue
        href = str(item.get("href") or "")
        observed_at = _clean(item.get("time"), 80)
        heat_evidence = _clean(item.get("heat_evidence"), 240)
        title = _clean(item.get("title"), 220)
        source_text = re.sub(
            r"\s*A股映射[:：].*$",
            "",
            _clean(item.get("text"), 800),
        )
        a_share_mapping = _infer_a_share_mapping(
            f"{title} {source_text}",
            source_key=key,
        )
        if (
            not href.startswith(("http://", "https://"))
            or not observed_at
            or not heat_evidence
            or not a_share_mapping
        ):
            continue
        row = _captured_item(
            label=_clean(item.get("label"), 80) or site,
            title=title,
            text=source_text,
            href=href,
            source_url=source_url,
            collected_at=collected_at,
            observed_at=observed_at,
            source_key=_clean(item.get("source_key"), 80),
            rank=item.get("rank"),
            heat_evidence=heat_evidence,
            a_share_mapping=a_share_mapping,
        )
        if row["title"]:
            row["snapshot_reused"] = True
            row["snapshot_collected_at"] = _iso(snapshot_at)
            rows.append(row)
    return rows


def write_sentiment_capture_bundle(
    out_dir: Path,
    *,
    payloads: dict[str, list[dict[str, Any]]],
    breadth_records: list[dict[str, Any]],
    collected_at: dt.datetime | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    collected_at = _as_datetime(collected_at)
    primary = (
        _sina_capture_rows(payloads.get("sina") or [], collected_at)
        + _duanxianxia_capture_rows(payloads, collected_at)
        + _breadth_capture_rows(breadth_records, collected_at)
    )
    payload_map = {
        "primary": _capture_payload(
            site="A股公开主来源",
            source_url=SINA_ROLL,
            rows=primary,
            collected_at=collected_at,
            errors=errors,
        )
    }
    site_keys = (
        "tgb",
        "xueqiu",
        "weibo",
        "zhihu",
        "guba",
        "jiuyangongshe",
        "cls",
        "jin10",
    )
    site_names = {
        "tgb": "淘股吧",
        "xueqiu": "雪球",
        "weibo": "微博",
        "zhihu": "知乎",
        "guba": "东方财富股吧",
        "jiuyangongshe": "韭研公社",
        "cls": "财联社",
        "jin10": "金十数据",
    }
    site_urls = {
        "tgb": TGB_HOME,
        "xueqiu": XUEQIU_HOME,
        "weibo": WEIBO_FINANCE,
        "zhihu": ZHIHU_STOCK,
        "guba": GUBA_ROOT,
        "jiuyangongshe": JIUYANGONGSHE_HOME,
        "cls": CLS_HOME,
        "jin10": JIN10_HOME,
    }
    for key in site_keys:
        source_rows = payloads.get(key) or []
        collection_diagnostics: dict[str, Any] = {}
        captured_rows = _mandatory_sentiment_rows(
            key,
            source_rows,
            collected_at,
            diagnostics=collection_diagnostics,
        )
        rows = [
            row
            for row in captured_rows
            if not row.get("observation_time_only")
            and str(row.get("href", "")).startswith(("http://", "https://"))
            and _clean(row.get("heat_evidence"))
            and _clean(row.get("a_share_mapping"))
        ]
        post_validation_accepted = len(rows)
        if len(rows) < MANDATORY_SITE_MINIMUM:
            seen_urls = {str(row.get("href") or "") for row in rows}
            for row in _fresh_current_task_capture_rows(
                key,
                site=site_names[key],
                source_url=site_urls[key],
                collected_at=collected_at,
            ):
                href = str(row.get("href") or "")
                if not href or href in seen_urls:
                    continue
                seen_urls.add(href)
                rows.append(row)
                if len(rows) >= MANDATORY_SITE_MINIMUM:
                    break
        snapshot_supplemented = len(rows) - post_validation_accepted
        quality_rejections = []
        quality_rows = []
        for row in rows:
            quality = validate_sentiment_record(
                source=site_names[key],
                event=(
                    row.get("source_event_text")
                    or f"{row.get('title', '')} {row.get('text', '')}"
                ),
                heat_evidence=row.get("heat_evidence"),
                a_share_mapping=row.get("a_share_mapping"),
                rank=row.get("rank"),
            )
            if quality["ok"]:
                row["quality_contract"] = {
                    "schema": "A_SHARE_SENTIMENT_RECORD_QUALITY_V1",
                    "status": "PASS",
                    "relevance_score": quality["relevance_score"],
                    "grounded_mapping_terms": quality["mapping"]["grounded_mapping_terms"],
                    "event_signal_terms": quality["mapping"]["event_signal_terms"],
                }
                quality_rows.append(row)
            else:
                quality_rejections.append({
                    "title": row.get("title", ""),
                    "href": row.get("href", ""),
                    "reasons": quality["reasons"],
                })
        rows = quality_rows
        collection_diagnostics.update({
            "post_validation_accepted": post_validation_accepted,
            "snapshot_supplemented": snapshot_supplemented,
            "final_accepted": len(rows),
            "quality_rejected": len(quality_rejections),
            "quality_rejections": quality_rejections,
            "rejected_by_post_validation": (
                collection_diagnostics["quality_candidate_accepted"]
                - post_validation_accepted
            ),
        })
        accounting = validate_capture_accounting(
            raw_count=len(source_rows),
            clean_count=len(rows),
            clean_rows=rows,
            supplemented_count=max(0, int(collection_diagnostics.get("snapshot_supplemented", 0))),
        )
        collection_diagnostics["accounting"] = accounting
        if not accounting["ok"]:
            rows = []
            collection_diagnostics["final_accepted"] = 0
        payload_map[key] = _capture_payload(
            site=site_names[key],
            source_url=site_urls[key],
            rows=rows,
            collected_at=collected_at,
            errors=errors,
            raw_count=len(source_rows),
            collection_diagnostics=collection_diagnostics,
        )
    business_errors = [
        error
        for error in (errors or [])
        if str(error).startswith("business_society:")
    ]
    payload_map["business_society"] = _business_capture_payload(
        payloads.get("business_society") or [],
        collected_at,
        business_errors,
    )
    files = {}
    missing = []
    for key, payload in payload_map.items():
        path = out_dir / f"{key}.json"
        _write_json_text(path, payload)
        files[key] = str(path)
        if key in site_keys and len(payload["clean"]) < MANDATORY_SITE_MINIMUM:
            missing.append(key)
    reasons = []
    if missing:
        reasons.append("mandatory_source_count_lt_10")
    if len(primary) < 30:
        reasons.append("primary_count_lt_30")
    status = "PASS" if not reasons else "BLOCKED"
    manifest = {
        "schema": "A_SHARE_PUBLIC_READONLY_FALLBACK_MANIFEST_V1",
        "status": status,
        "collection_mode": FALLBACK_CHANNEL,
        "generated_at": _iso(collected_at),
        "files": files,
        "required_capture_files": list(REQUIRED_CAPTURE_FILES),
        "primary_count": len(primary),
        "minimum_per_mandatory_source": MANDATORY_SITE_MINIMUM,
        "mandatory_source_counts": {
            key: len(payload_map[key]["clean"]) for key in site_keys
        },
        "business_society_count": len(payload_map["business_society"]["clean"]),
        "duanxianxia_snapshot": str(out_dir / "duanxianxia_public_snapshot.json"),
        "missing_sources": missing,
        "reasons": reasons,
        "errors": list(errors or []),
    }
    manifest_path = out_dir / "public_readonly_fallback_manifest.json"
    _write_json_text(manifest_path, manifest)
    manifest["manifest"] = str(manifest_path)
    return manifest


def _social_item(
    platform: str,
    item: dict[str, Any],
    rank: int,
) -> dict[str, Any]:
    title = _clean(item.get("title") or item.get("name"), 180)
    heat = item.get("hot_value") or item.get("value") or item.get("heat") or ""
    extra = item.get("extra") if isinstance(item.get("extra"), dict) else {}
    detail = _clean(extra.get("desc") or item.get("summary") or item.get("text"), 420)
    platform_name = {"xhs": "小红书", "douyin": "抖音", "xueqiu": "雪球"}[platform]
    if platform == "xueqiu":
        summary = (
            f"雪球公开热股榜A股股票观察，代码{_clean(item.get('symbol') or item.get('code'), 20)}，"
            f"热度{heat}，涨跌幅{item.get('percent', '')}。{detail}"
        )
    else:
        summary = (
            f"{platform_name}公开热榜观察，作为A股舆情外部事件线索，公开热度{heat}。{detail}"
        )
    return {
        "rank": item.get("index") or item.get("rank") or rank,
        "title": title,
        "summary": summary,
        "heat": heat,
        "url": str(item.get("url") or item.get("href") or ""),
        "source": f"{platform_name}公开热榜",
        "acquisition_mode": FALLBACK_CHANNEL,
        "provider": "UApiPro第三方聚合" if platform in {"xhs", "douyin"} else "雪球公开热股接口",
    }


def _finance_hits(text: str) -> list[str]:
    return [term for term in FINANCE_TERMS if term.lower() in text.lower()]


def write_social_bundle(
    out_dir: Path,
    *,
    payloads: dict[str, list[dict[str, Any]]],
    collected_at: dt.datetime | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    collected_at = _as_datetime(collected_at)
    stamp = collected_at.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    datasets = {
        "xhs": [
            _social_item("xhs", item, index)
            for index, item in enumerate(payloads.get("xhs") or [], 1)
            if _clean(item.get("title") or item.get("name"))
        ],
        "douyin": [
            _social_item("douyin", item, index)
            for index, item in enumerate(payloads.get("douyin") or [], 1)
            if _clean(item.get("title") or item.get("name"))
        ],
        "xueqiu": [
            _social_item("xueqiu", item, index)
            for index, item in enumerate(payloads.get("xueqiu") or [], 1)
            if _clean(item.get("title") or item.get("name"))
        ],
    }
    files = {
        "xhs": out_dir / f"xhs_apify_dataset_{stamp}.json",
        "xhs_scan": out_dir / f"xhs_finance_scan_{stamp}.json",
        "douyin": out_dir / f"douyin_apify_dataset_{stamp}.json",
        "xueqiu": out_dir / f"xueqiu_apify_dataset_{stamp}.json",
        "structured": out_dir / f"structured_hot_topics_{stamp}.json",
    }
    files["xhs"].write_text(json.dumps(datasets["xhs"], ensure_ascii=False, indent=2), encoding="utf-8")
    files["douyin"].write_text(json.dumps(datasets["douyin"], ensure_ascii=False, indent=2), encoding="utf-8")
    files["xueqiu"].write_text(json.dumps(datasets["xueqiu"], ensure_ascii=False, indent=2), encoding="utf-8")
    xhs_scan_rows = []
    for item in datasets["xhs"]:
        text = f"{item.get('title', '')} {item.get('summary', '')}"
        row = {
            "rank": item.get("rank"),
            "title": item.get("title"),
            "score": item.get("heat"),
            "url": item.get("url"),
            "matched_finance_keywords": _finance_hits(text),
            "source": item.get("source"),
            "acquisition_mode": FALLBACK_CHANNEL,
        }
        if row["matched_finance_keywords"]:
            xhs_scan_rows.append(row)
    scan = {
        "source_file": files["xhs"].name,
        "collection_mode": FALLBACK_CHANNEL,
        "total": len(datasets["xhs"]),
        "finance_related": xhs_scan_rows,
        "top20": xhs_scan_rows[:20],
    }
    files["xhs_scan"].write_text(json.dumps(scan, ensure_ascii=False, indent=2), encoding="utf-8")
    structured = {
        "collection_mode": FALLBACK_CHANNEL,
        "source_disclosure": {
            "xhs": "UApiPro第三方公开热榜聚合",
            "douyin": "UApiPro第三方公开热榜聚合",
            "xueqiu": "雪球匿名公开热股接口",
        },
        "xueqiu_rebang": datasets["xueqiu"][:40],
        "douyin_rebang": datasets["douyin"][:40],
        "douyin_tophub": [],
    }
    files["structured"].write_text(
        json.dumps(structured, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    missing = [name for name, rows in datasets.items() if not rows]
    status = "PASS" if not missing else "BLOCKED"
    manifest = {
        "schema": "A_SHARE_MANDATORY_SENTIMENT_CAPTURE_MANIFEST_V1",
        "skill": "A股热点舆情研判",
        "status": status,
        "collection_mode": FALLBACK_CHANNEL,
        "generated_at": _iso(collected_at),
        "datasets": {name: len(rows) for name, rows in datasets.items()},
        "files": {name: str(path) for name, path in files.items()},
        "missing_sources": missing,
        "errors": list(errors or []),
    }
    manifest_path = out_dir / f"apify_collect_manifest_{stamp}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest["manifest"] = str(manifest_path)
    return manifest


def collect_and_write_sentiment(out_dir: Path) -> dict[str, Any]:
    payloads, breadth, errors = collect_live_payloads(Path(out_dir))
    return write_sentiment_capture_bundle(
        Path(out_dir),
        payloads=payloads,
        breadth_records=breadth,
        errors=errors,
    )


def collect_and_write_social(out_dir: Path) -> dict[str, Any]:
    return {
        "schema": "DEPRECATED_SOCIAL_WORKFLOW_V1",
        "status": "BLOCKED",
        "redirect": "A股热点舆情研判",
        "reason": "三端社媒财经简报已并入A股热点舆情研判，不再生成独立模板或独立Word。",
    }
