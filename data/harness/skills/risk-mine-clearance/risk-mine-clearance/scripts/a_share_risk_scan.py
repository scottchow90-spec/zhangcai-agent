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
import multiprocessing as mp
import os
import re
import sqlite3
import struct
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd


SHANGHAI = ZoneInfo("Asia/Shanghai")
LEVEL_ORDER = {"红色": 4, "橙色": 3, "黄色": 2, "观察": 1}
TDX_ROOT = Path(r"C:\new_tdx_mock")
TDX_DAY_RECORD = struct.Struct("<IIIIIfII")
TDX_TNF_HEADER_SIZE = 50
TDX_TNF_RECORD_SIZES = {"sh": 360, "sz": 360, "bj": 360}


@dataclass(frozen=True)
class SourceSpec:
    name: str
    function: str
    kwargs: dict[str, Any]
    timeout_seconds: int
    purpose: str


@dataclass
class SourceHealth:
    name: str
    purpose: str
    status: str
    rows: int
    elapsed_seconds: float
    error: str = ""


@dataclass
class Evidence:
    code: str
    name: str
    domain: str
    severity: int
    stage: str
    title: str
    detail: str
    source: str
    source_url: str
    observed_at: str


CANDIDATE_COLUMNS = (
    "level",
    "stage",
    "code",
    "name",
    "evidence_domains",
    "evidence_count",
    "max_severity",
    "price",
    "pct_change",
    "turnover",
    "attention",
    "top_reasons",
    "top_detail",
)
EVIDENCE_COLUMNS = tuple(Evidence.__dataclass_fields__)
SOURCE_HEALTH_COLUMNS = tuple(SourceHealth.__dataclass_fields__)


NOTICE_RULES: list[tuple[int, str, re.Pattern[str]]] = [
    (
        4,
        "重大监管/偿债/持续经营风险",
        re.compile(
            r"立案|退市风险|终止上市|重大违法|破产|预重整|重整|债务逾期|贷款逾期|"
            r"无法清偿|不能清偿|资金占用|违规担保|无法表示意见|否定意见|强制执行|"
            r"被执行人|账户冻结|司法冻结|实控人.{0,8}(拘留|留置|失联|被查)"
        ),
    ),
    (
        3,
        "诉讼/亏损/经营与控制风险",
        re.compile(
            r"重大诉讼|涉及诉讼|诉讼公告|仲裁|业绩预亏|预计亏损|大幅预减|商誉减值|"
            r"资产减值|暂停生产|停产|安全事故|行政处罚|警示函|监管措施|控制权变更|"
            r"股份冻结|业绩变脸|会计差错更正"
        ),
    ),
    (
        2,
        "风险提示/问询/治理变化",
        re.compile(
            r"风险提示|异常波动|延期披露|延期回复|监管问询|问询函|变更会计师事务所|"
            r"辞职|离任|对外担保|新增担保|补充质押|质押风险|可能被实施"
        ),
    ),
    (
        1,
        "股东行为与资本事项",
        re.compile(r"减持计划|集中竞价减持|大宗交易减持|限售股解禁|解除质押"),
    ),
]

DEEP_RISK_RE = re.compile(
    r"欠薪|拖欠工资|社保断缴|停工|停产|裁员|商票|票据逾期|拒付|供应商欠款|"
    r"砍单|取消订单|客户流失|质量问题|召回|爆炸|事故|失联|被查|拘留|立案|"
    r"诉讼|仲裁|冻结|查封|逾期|违约|无法兑付|重整|破产|资金占用|违规担保|"
    r"财务造假|虚增|空转贸易|会计差错|业绩预亏|大幅下降|减值|退市风险"
)

DENIAL_RE = re.compile(
    r"不存在.{0,18}(风险|重大事项)|经营状况.{0,8}(正常|良好)|现金流.{0,8}(稳健|健康)|"
    r"未发现.{0,12}(异常|风险)|不影响.{0,12}(经营|持续经营)|一切正常"
)

THIRD_PARTY_SUGGESTION_RE = re.compile(
    r"建议.{0,20}(参与|关注|收购|投资).{0,30}(重整|破产)|"
    r"(参与|关注).{0,20}(其他公司|华谊|恒大|第三方).{0,20}(重整|破产)"
)

SOURCE_URLS = {
    "notices": "https://data.eastmoney.com/notices/",
    "guarantees": "https://webapi.cninfo.com.cn/",
    "suspensions": "https://data.eastmoney.com/tfpxx/",
    "pledge": "https://data.eastmoney.com/gpzy/",
    "lawsuits": "https://data.eastmoney.com/notices/hsa/5.html",
    "eastmoney_comment": "https://data.eastmoney.com/stockcomment/",
    "eastmoney_hot_rank": "https://guba.eastmoney.com/rank/",
    "xueqiu": "https://xueqiu.com/",
    "weibo": "https://weibo.com/",
    "cninfo_irm": "https://irm.cninfo.com.cn/",
    "eastmoney_news": "https://so.eastmoney.com/news/s",
    "shcpe_enterprise_notices": "https://disclosure.cpisp.shcpe.com.cn/",
    "credit_gd_wage_arrears": "https://credit.gd.gov.cn/page/creditPublic/sxcjmd/tqnmggz.html",
    "credit_gd_court_defaulters": "https://credit.gd.gov.cn/page/creditPublic/sxcjmd/sxbzxrmd.html",
}


def now_shanghai() -> datetime:
    return datetime.now(tz=SHANGHAI)


def compact_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", "", str(value)).strip()


def stock_code(value: Any) -> str:
    match = re.search(r"(\d{6})", str(value or ""))
    return match.group(1) if match else ""


def stock_name(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip()


def safe_number(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        text = str(value).replace("%", "").replace(",", "").strip()
        if not text or text in {"-", "--", "None", "nan"}:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            pass
    return value


def sqlite_safe_frame(frame: pd.DataFrame) -> pd.DataFrame:
    safe = frame.copy()
    for column in safe.columns:
        if safe[column].dtype != "object":
            continue
        safe[column] = safe[column].map(
            lambda value: json.dumps(json_safe(value), ensure_ascii=False)
            if isinstance(value, (dict, list, tuple))
            else value
        )
    return safe


def pledge_date_candidates(value: str, lookback_days: int = 10) -> list[str]:
    text = str(value or "").strip()
    parsed = (
        datetime.strptime(text, "%Y%m%d").date()
        if re.fullmatch(r"\d{8}", text)
        else date.fromisoformat(text)
    )
    candidates: list[str] = []
    for offset in range(max(0, lookback_days) + 1):
        candidate = parsed - timedelta(days=offset)
        if candidate.weekday() < 5:
            candidates.append(candidate.strftime("%Y%m%d"))
    return candidates


def _tdx_is_a_share(market: str, code: str) -> bool:
    prefixes = {
        "sh": ("600", "601", "603", "605", "688", "689"),
        "sz": ("000", "001", "002", "003", "300", "301"),
        "bj": ("43", "83", "87", "88", "92"),
    }
    return len(code) == 6 and code.isdigit() and code.startswith(prefixes[market])


def _tdx_security_names() -> dict[str, str]:
    names: dict[str, str] = {}
    for market, filename in (("sh", "shs.tnf"), ("sz", "szs.tnf"), ("bj", "bjs.tnf")):
        path = TDX_ROOT / "T0002" / "hq_cache" / filename
        content = path.read_bytes()
        record_size = TDX_TNF_RECORD_SIZES[market]
        payload_size = len(content) - TDX_TNF_HEADER_SIZE
        if payload_size < 0 or payload_size % record_size != 0:
            raise RuntimeError(f"invalid_tdx_tnf:{path}")
        for offset in range(TDX_TNF_HEADER_SIZE, len(content), record_size):
            record = content[offset : offset + record_size]
            code = record[:6].decode("ascii", errors="ignore")
            if not _tdx_is_a_share(market, code):
                continue
            name = record[31:40].split(bytes([0]), 1)[0].decode("gbk", errors="strict").strip()
            if name:
                names[code] = name
    if not names:
        raise RuntimeError("tdx_security_name_map_empty")
    return names


def custom_tdx_market_spot(target_date: str) -> pd.DataFrame:
    target = date.fromisoformat(target_date).strftime("%Y%m%d")
    names = _tdx_security_names()
    records: list[dict[str, Any]] = []
    for market in ("sh", "sz", "bj"):
        lday = TDX_ROOT / "vipdoc" / market / "lday"
        for path in sorted(lday.glob(f"{market}*.day")):
            code = path.stem[2:]
            if code not in names or not _tdx_is_a_share(market, code):
                continue
            size = path.stat().st_size
            if size < TDX_DAY_RECORD.size or size % TDX_DAY_RECORD.size != 0:
                raise RuntimeError(f"invalid_tdx_day:{path}")
            with path.open("rb") as handle:
                handle.seek(-min(size, TDX_DAY_RECORD.size * 2), os.SEEK_END)
                previous_raw = (
                    handle.read(TDX_DAY_RECORD.size)
                    if size >= TDX_DAY_RECORD.size * 2
                    else None
                )
                latest_raw = handle.read(TDX_DAY_RECORD.size)
            previous = TDX_DAY_RECORD.unpack(previous_raw) if previous_raw else None
            latest = TDX_DAY_RECORD.unpack(latest_raw)
            if str(latest[0]) != target:
                continue
            latest_close = latest[4] / 100.0
            pct_change = (
                (latest_close / (previous[4] / 100.0) - 1.0) * 100.0
                if previous and previous[4] > 0
                else None
            )
            records.append(
                {
                    "代码": code,
                    "名称": names[code],
                    "最新价": latest_close,
                    "涨跌幅": pct_change,
                    "换手率": None,
                    "交易日": target_date,
                }
            )
    if not records:
        raise RuntimeError(f"tdx_market_spot_empty:{target_date}")
    return pd.DataFrame(records)


def custom_tdx_st_list() -> pd.DataFrame:
    records = [
        {"代码": code, "名称": name}
        for code, name in sorted(_tdx_security_names().items())
        if re.search(r"^(?:S\*ST|\*ST|SST|ST)|退$|退市", name, flags=re.I)
    ]
    if not records:
        raise RuntimeError("tdx_st_list_empty")
    return pd.DataFrame(records)


def custom_eastmoney_hot_rank(target_date: str) -> pd.DataFrame:
    import requests

    response = requests.post(
        "https://emappdata.eastmoney.com/stockrank/getAllCurrentList",
        json={
            "appId": "appId01",
            "globalId": "786e4c21-70dc-435a-93bb-38",
            "marketType": "",
            "pageNo": 1,
            "pageSize": 100,
        },
        timeout=10,
    )
    response.raise_for_status()
    ranks = (response.json() or {}).get("data") or []
    if not ranks:
        raise RuntimeError("eastmoney_hot_rank_empty")
    names = _tdx_security_names()
    spot = custom_tdx_market_spot(target_date)
    quotes = {str(row["代码"]): row for row in spot.to_dict(orient="records")}
    records: list[dict[str, Any]] = []
    for row in ranks:
        code = stock_code(row.get("sc"))
        quote = quotes.get(code, {})
        latest = safe_number(quote.get("最新价"))
        pct_change = safe_number(quote.get("涨跌幅"))
        records.append(
            {
                "当前排名": safe_number(row.get("rk")),
                "代码": code,
                "股票名称": names.get(code, code),
                "最新价": latest,
                "涨跌额": latest * pct_change / 100.0 if latest is not None and pct_change is not None else None,
                "涨跌幅": pct_change,
            }
        )
    return pd.DataFrame(records)


def custom_eastmoney_pledge_detail(start_date: str, end_date: str) -> pd.DataFrame:
    import requests

    response = requests.get(
        "https://datacenter-web.eastmoney.com/api/data/v1/get",
        params={
            "sortColumns": "NOTICE_DATE",
            "sortTypes": "-1",
            "pageSize": "500",
            "pageNumber": "1",
            "reportName": "RPTA_APP_ACCUMDETAILS",
            "columns": "ALL",
            "quoteColumns": "",
            "source": "WEB",
            "client": "WEB",
            "filter": f"(NOTICE_DATE>='{start_date}')(NOTICE_DATE<='{end_date}')",
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json() or {}
    result = payload.get("result") or {}
    records = result.get("data") or []
    if payload.get("success") is not True or int(result.get("pages") or 0) > 1 or not records:
        raise RuntimeError("eastmoney_pledge_detail_incomplete")
    frame = pd.DataFrame(records).rename(
        columns={
            "SECURITY_CODE": "股票代码",
            "SECURITY_NAME_ABBR": "股票简称",
            "HOLDER_NAME": "股东名称",
            "PF_NUM": "质押股份数量",
            "PF_HOLD_RATIO": "占所持股份比例",
            "PF_TSR": "占总股本比例",
            "PF_ORG": "质押机构",
            "NOTICE_DATE": "公告日期",
        }
    )
    columns = [
        "股票代码", "股票简称", "股东名称", "质押股份数量", "占所持股份比例",
        "占总股本比例", "质押机构", "公告日期",
    ]
    return frame.loc[:, columns]


def parse_eastmoney_news_jsonp(text: str, callback: str, symbol: str) -> pd.DataFrame:
    match = re.fullmatch(
        r"\s*[A-Za-z_$][A-Za-z0-9_$.]*\s*\((.*)\)\s*;?\s*",
        str(text or ""),
        flags=re.S,
    )
    if not match:
        raise ValueError(f"eastmoney_news_jsonp_invalid:{callback}")
    payload = json.loads(match.group(1))
    rows = (payload.get("result") or {}).get("cmsArticleWebOld") or []
    records: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        title = re.sub(r"</?em>", "", str(row.get("title") or ""), flags=re.I)
        content = re.sub(r"</?em>", "", str(row.get("content") or ""), flags=re.I)
        content = (
            content.replace("\\u3000", "")
            .replace("\u3000", "")
            .replace("\\r\\n", " ")
            .replace("\r", " ")
            .replace("\n", " ")
        )
        article_code = str(row.get("code") or "")
        records.append(
            {
                "关键词": symbol,
                "新闻标题": title,
                "新闻内容": content,
                "发布时间": row.get("date"),
                "文章来源": row.get("mediaName"),
                "新闻链接": (
                    f"https://finance.eastmoney.com/a/{article_code}.html"
                    if article_code
                    else ""
                ),
            }
        )
    return pd.DataFrame(
        records,
        columns=["关键词", "新闻标题", "新闻内容", "发布时间", "文章来源", "新闻链接"],
    )


def custom_eastmoney_stock_news(symbol: str) -> pd.DataFrame:
    from curl_cffi import requests

    callback = f"jQueryStockRisk{int(time.time() * 1000)}"
    inner = {
        "uid": "",
        "keyword": symbol,
        "type": ["cmsArticleWebOld"],
        "client": "web",
        "clientType": "web",
        "clientVersion": "curr",
        "param": {
            "cmsArticleWebOld": {
                "searchScope": "default",
                "sort": "default",
                "pageIndex": 1,
                "pageSize": 20,
                "preTag": "<em>",
                "postTag": "</em>",
            }
        },
    }
    response = requests.get(
        "https://search-api-web.eastmoney.com/search/jsonp",
        params={
            "cb": callback,
            "param": json.dumps(inner, ensure_ascii=False),
            "_": str(int(time.time() * 1000)),
        },
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": f"https://so.eastmoney.com/news/s?keyword={symbol}",
        },
        timeout=12,
    )
    response.raise_for_status()
    return parse_eastmoney_news_jsonp(response.text, callback, symbol)


def custom_cninfo_irm(symbol: str) -> pd.DataFrame:
    import requests

    columns = [
        "股票代码",
        "公司简称",
        "行业",
        "行业代码",
        "问题",
        "提问者",
        "来源",
        "提问时间",
        "更新时间",
        "提问者编号",
        "问题编号",
        "回答ID",
        "回答内容",
        "回答者",
    ]
    session = requests.Session()
    lookup = session.post(
        "https://irm.cninfo.com.cn/newircs/index/queryKeyboardInfo",
        params={"_t": str(int(time.time()))},
        data={"keyWord": symbol},
        timeout=10,
    )
    lookup.raise_for_status()
    matches = (lookup.json() or {}).get("data") or []
    if not matches:
        return pd.DataFrame(columns=columns)
    response = session.post(
        "https://irm.cninfo.com.cn/newircs/company/question",
        params={
            "_t": str(int(time.time())),
            "stockcode": symbol,
            "orgId": matches[0].get("secid", ""),
            "pageSize": "1000",
            "pageNum": "1",
            "keyWord": "",
            "startDay": "",
            "endDay": "",
        },
        timeout=12,
    )
    response.raise_for_status()
    rows = (response.json() or {}).get("rows") or []
    if not rows:
        return pd.DataFrame(columns=columns)
    records: list[dict[str, Any]] = []
    source_names = {"2": "APP", "5": "公众号", "4": "网站"}
    for row in rows:
        trade = row.get("trade") or []
        board = row.get("boardType") or []
        records.append(
            {
                "股票代码": row.get("stockCode") or symbol,
                "公司简称": row.get("companyShortName"),
                "行业": trade[0] if isinstance(trade, list) and trade else trade,
                "行业代码": board[0] if isinstance(board, list) and board else board,
                "问题": row.get("mainContent"),
                "提问者": row.get("authorName"),
                "来源": source_names.get(str(row.get("pubClient")), "网站"),
                "提问时间": row.get("pubDate"),
                "更新时间": row.get("updateDate"),
                "提问者编号": row.get("author"),
                "问题编号": row.get("indexId"),
                "回答ID": row.get("attachedId"),
                "回答内容": row.get("attachedContent"),
                "回答者": row.get("attachedAuthor"),
            }
        )
    return pd.DataFrame(records, columns=columns)


def custom_eastmoney_risk_notices(start_date: str, end_date: str) -> pd.DataFrame:
    from concurrent.futures import ThreadPoolExecutor
    import math
    import requests

    url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
    params = {
        "sr": "-1",
        "page_size": "100",
        "page_index": "1",
        "ann_type": "A",
        "client_source": "web",
        "f_node": "5",
        "s_node": "0",
        "begin_time": start_date,
        "end_time": end_date,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data") or {}
    pages = math.ceil(int(data.get("total_hits") or 0) / 100)
    def fetch_page(page: int) -> list[dict[str, Any]]:
        page_response = requests.get(
            url, params={**params, "page_index": str(page)}, timeout=10
        )
        page_response.raise_for_status()
        return ((page_response.json() or {}).get("data") or {}).get("list") or []

    batches = [data.get("list") or []]
    if pages > 1:
        with ThreadPoolExecutor(max_workers=min(6, pages - 1)) as executor:
            batches.extend(executor.map(fetch_page, range(2, pages + 1)))

    records: list[dict[str, Any]] = []
    for batch in batches:
        for item in batch:
            if not re.search(
                r"诉讼|仲裁|执行|冻结|查封", str(item.get("title") or "")
            ):
                continue
            code_rows = [
                code
                for code in item.get("codes") or []
                if str(code.get("ann_type") or "").startswith("A")
            ]
            if not code_rows:
                continue
            code_row = code_rows[0]
            code = str(code_row.get("stock_code") or "")
            art_code = str(item.get("art_code") or "")
            columns = item.get("columns") or []
            records.append(
                {
                    "代码": code,
                    "名称": code_row.get("short_name"),
                    "公告标题": item.get("title"),
                    "公告类型": columns[0].get("column_name") if columns else "风险提示",
                    "公告日期": item.get("notice_date"),
                    "网址": f"https://data.eastmoney.com/notices/detail/{code}/{art_code}.html",
                }
            )
    return pd.DataFrame(
        records, columns=["代码", "名称", "公告标题", "公告类型", "公告日期", "网址"]
    )


def custom_pledge_ratio_latest(end_date: str, lookback_days: int = 10) -> pd.DataFrame:
    import akshare as ak

    last_error: Exception | None = None
    for candidate in pledge_date_candidates(end_date, lookback_days):
        try:
            frame = ak.stock_gpzy_pledge_ratio_em(date=candidate)
        except Exception as exc:
            last_error = exc
            continue
        if isinstance(frame, pd.DataFrame) and not frame.empty:
            frame = frame.copy()
            frame["请求回退日期"] = candidate
            return frame
    if last_error is not None:
        raise RuntimeError(f"pledge_latest_unavailable:{type(last_error).__name__}:{last_error}")
    return pd.DataFrame()


def _credit_gd_feed(
    table_name: str,
    order_field: str,
    pages: int,
    rows_per_page: int,
    referer: str,
) -> pd.DataFrame:
    import requests

    url = "https://credit.gd.gov.cn/gdcreditwebApi2/company/web/booleanQueryListByPageV2"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": referer,
        "Accept": "application/json",
        "Request-Client-Set": "xygd-web",
    }
    rows: list[dict[str, Any]] = []
    with requests.Session() as session:
        for page in range(1, pages + 1):
            response = session.get(
                url,
                params={
                    "tableName": table_name,
                    "page": page,
                    "rows": rows_per_page,
                    "orderArgs": json.dumps([{order_field: "desc"}], ensure_ascii=False),
                },
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("code") != 200:
                raise RuntimeError(f"credit gd returned {payload.get('code')}: {payload.get('message')}")
            batch = (payload.get("data") or {}).get("rows") or []
            rows.extend(batch)
            if len(batch) < rows_per_page:
                break
    return pd.DataFrame(rows)


def custom_credit_gd_wage_arrears() -> pd.DataFrame:
    return _credit_gd_feed(
        table_name="V_XYDAK_XYPJ_TQNMGGZHMD_GSLM",
        order_field="LRRQ",
        pages=1,
        rows_per_page=50,
        referer=SOURCE_URLS["credit_gd_wage_arrears"],
    )


def custom_credit_gd_court_defaulters() -> pd.DataFrame:
    return _credit_gd_feed(
        table_name="V_XYDAK_SXCJ_SXBZXRMD_GSLM",
        order_field="FBRQ",
        pages=1,
        rows_per_page=50,
        referer=SOURCE_URLS["credit_gd_court_defaulters"],
    )


def custom_shcpe_enterprise_notices() -> pd.DataFrame:
    import requests

    url = "https://disclosure.cpisp.shcpe.com.cn/ent/public/article/enttodolist"
    response = requests.post(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": SOURCE_URLS["shcpe_enterprise_notices"],
            "Content-Type": "application/json;charset=UTF-8",
        },
        json={"userType": "ENT", "current": 1, "size": 1000, "acptOrgType": "1"},
        timeout=35,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != 200:
        raise RuntimeError(f"shcpe returned {payload.get('code')}: {payload.get('message')}")
    return pd.DataFrame((payload.get("data") or {}).get("dataList") or [])


CUSTOM_SOURCE_FUNCTIONS = {
    "custom:tdx_market_spot": custom_tdx_market_spot,
    "custom:tdx_st_list": custom_tdx_st_list,
    "custom:eastmoney_hot_rank": custom_eastmoney_hot_rank,
    "custom:eastmoney_pledge_detail": custom_eastmoney_pledge_detail,
    "custom:credit_gd_wage_arrears": custom_credit_gd_wage_arrears,
    "custom:credit_gd_court_defaulters": custom_credit_gd_court_defaulters,
    "custom:shcpe_enterprise_notices": custom_shcpe_enterprise_notices,
    "custom:eastmoney_stock_news": custom_eastmoney_stock_news,
    "custom:cninfo_irm": custom_cninfo_irm,
    "custom:eastmoney_risk_notices": custom_eastmoney_risk_notices,
    "custom:pledge_ratio_latest": custom_pledge_ratio_latest,
}


def _source_worker(spec: SourceSpec, child_conn: Any) -> None:
    started = time.monotonic()
    try:
        if spec.function.startswith("custom:"):
            function = CUSTOM_SOURCE_FUNCTIONS[spec.function]
        else:
            import akshare as ak

            function = getattr(ak, spec.function)
        frame = function(**spec.kwargs)
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"expected DataFrame, received {type(frame).__name__}")
        child_conn.send(
            {
                "ok": True,
                "frame": frame,
                "elapsed": time.monotonic() - started,
            }
        )
    except Exception as exc:
        child_conn.send(
            {
                "ok": False,
                "error": f"{type(exc).__name__}: {str(exc)[:800]}",
                "elapsed": time.monotonic() - started,
            }
        )
    finally:
        child_conn.close()


def fetch_sources(
    specs: list[SourceSpec], max_parallel: int = 4
) -> tuple[dict[str, pd.DataFrame], list[SourceHealth]]:
    ctx = mp.get_context("spawn")
    waiting = list(specs)
    active: dict[str, dict[str, Any]] = {}
    frames: dict[str, pd.DataFrame] = {}
    health: list[SourceHealth] = []

    while waiting or active:
        while waiting and len(active) < max_parallel:
            spec = waiting.pop(0)
            parent_conn, child_conn = ctx.Pipe(duplex=False)
            process = ctx.Process(target=_source_worker, args=(spec, child_conn))
            process.start()
            child_conn.close()
            active[spec.name] = {
                "spec": spec,
                "conn": parent_conn,
                "process": process,
                "started": time.monotonic(),
            }

        completed: list[str] = []
        for name, state in active.items():
            spec: SourceSpec = state["spec"]
            conn = state["conn"]
            process = state["process"]
            elapsed = time.monotonic() - state["started"]
            if conn.poll():
                result = conn.recv()
                process.join(timeout=2)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=2)
                if result.get("ok"):
                    frame = result["frame"]
                    frames[name] = frame
                    health.append(
                        SourceHealth(
                            name=name,
                            purpose=spec.purpose,
                            status="ok",
                            rows=int(len(frame)),
                            elapsed_seconds=round(float(result["elapsed"]), 2),
                        )
                    )
                else:
                    health.append(
                        SourceHealth(
                            name=name,
                            purpose=spec.purpose,
                            status="failed",
                            rows=0,
                            elapsed_seconds=round(float(result["elapsed"]), 2),
                            error=result.get("error", "unknown source failure"),
                        )
                    )
                conn.close()
                completed.append(name)
            elif elapsed > spec.timeout_seconds:
                process.terminate()
                process.join(timeout=3)
                conn.close()
                health.append(
                    SourceHealth(
                        name=name,
                        purpose=spec.purpose,
                        status="timeout",
                        rows=0,
                        elapsed_seconds=round(elapsed, 2),
                        error=f"exceeded {spec.timeout_seconds}s",
                    )
                )
                completed.append(name)

        for name in completed:
            active.pop(name, None)
        if active and not completed:
            time.sleep(0.1)

    health.sort(key=lambda item: item.name)
    return frames, health


def base_source_specs(run_date: date) -> list[SourceSpec]:
    end = run_date.strftime("%Y%m%d")
    start = (run_date - timedelta(days=14)).strftime("%Y%m%d")
    start_iso = (run_date - timedelta(days=14)).isoformat()
    end_iso = run_date.isoformat()
    return [
        SourceSpec(
            "market_spot",
            "custom:tdx_market_spot",
            {"target_date": end_iso},
            30,
            "本地通达信目标交易日全市场收盘行情",
        ),
        SourceSpec("st_list", "custom:tdx_st_list", {}, 30, "本地通达信当前ST股票列表"),
        SourceSpec(
            "suspensions",
            "stock_tfp_em",
            {"date": end},
            45,
            "停复牌及停牌原因",
        ),
        SourceSpec(
            "pledge_ratio",
            "custom:pledge_ratio_latest",
            {"end_date": end, "lookback_days": 10},
            90,
            "目标日向前回退到最新可用工作日的股权质押比例",
        ),
        SourceSpec(
            "pledge_detail",
            "custom:eastmoney_pledge_detail",
            {"start_date": start_iso, "end_date": end_iso},
            60,
            "东方财富官方近14日股权质押明细",
        ),
        SourceSpec(
            "lawsuits",
            "custom:eastmoney_risk_notices",
            {"start_date": start_iso, "end_date": end_iso},
            60,
            "东方财富官方近14日重大事项公告中的诉讼、仲裁、执行、冻结和查封证据",
        ),
        SourceSpec(
            "guarantees",
            "stock_cg_guarantee_cninfo",
            {"symbol": "全部", "start_date": start, "end_date": end},
            70,
            "近14日担保汇总及净资产占比",
        ),
        SourceSpec(
            "notices",
            "stock_notice_report",
            {"symbol": "全部", "date": end},
            70,
            "当日全部上市公司公告标题",
        ),
        SourceSpec(
            "eastmoney_comment",
            "stock_comment_em",
            {},
            80,
            "全市场价格、换手、关注指数和排名",
        ),
        SourceSpec(
            "eastmoney_hot_rank",
            "custom:eastmoney_hot_rank",
            {"target_date": end_iso},
            45,
            "东方财富股票热榜主接口与本地通达信收盘行情",
        ),
        SourceSpec(
            "xueqiu_follow",
            "stock_hot_follow_xq",
            {"symbol": "最热门"},
            80,
            "雪球关注度横截面",
        ),
        SourceSpec(
            "xueqiu_tweet",
            "stock_hot_tweet_xq",
            {"symbol": "最热门"},
            80,
            "雪球讨论度横截面",
        ),
        SourceSpec(
            "weibo_report",
            "stock_js_weibo_report",
            {"time_period": "CNHOUR12"},
            45,
            "近12小时微博热股",
        ),
        SourceSpec(
            "baidu_search",
            "stock_hot_search_baidu",
            {"symbol": "A股", "date": end, "time": "今日"},
            35,
            "百度A股搜索热度",
        ),
        SourceSpec(
            "shcpe_enterprise_notices",
            "custom:shcpe_enterprise_notices",
            {},
            45,
            "上海票据交易所最近1000条承兑人企业公告；不等于登录后逐企业逾期查询",
        ),
        SourceSpec(
            "credit_gd_wage_arrears",
            "custom:credit_gd_wage_arrears",
            {},
            60,
            "信用广东拖欠农民工工资失信名单按列入日期倒序最新50条；认定范围为广东省",
        ),
        SourceSpec(
            "credit_gd_court_defaulters_recent",
            "custom:credit_gd_court_defaulters",
            {},
            60,
            "信用广东转引最高人民法院失信被执行人按发布日期倒序最新50条；不等于全量逐企业执行查询",
        ),
    ]


def drill_source_specs(codes: list[str]) -> list[SourceSpec]:
    specs: list[SourceSpec] = []
    for code in codes:
        market_code = ("SH" if code.startswith(("5", "6", "9")) else "SZ") + code
        specs.extend(
            [
                SourceSpec(
                    f"news_{code}",
                    "custom:eastmoney_stock_news",
                    {"symbol": code},
                    18,
                    f"{code}个股新闻深挖",
                ),
                SourceSpec(
                    f"irm_{code}",
                    "custom:cninfo_irm",
                    {"symbol": code},
                    18,
                    f"{code}投资者互动问题深挖",
                ),
                SourceSpec(
                    f"keywords_{code}",
                    "stock_hot_keyword_em",
                    {"symbol": market_code},
                    18,
                    f"{code}股吧热门关键词深挖",
                ),
            ]
        )
    return specs


def append_evidence(
    evidence: list[Evidence],
    code: str,
    name: str,
    domain: str,
    severity: int,
    stage: str,
    title: str,
    detail: str,
    source: str,
    source_url: str = "",
    observed_at: str = "",
) -> None:
    if not code:
        return
    item = Evidence(
        code=code,
        name=name or code,
        domain=domain,
        severity=int(severity),
        stage=stage,
        title=title,
        detail=detail[:1200],
        source=source,
        source_url=source_url,
        observed_at=observed_at,
    )
    signature = (item.code, item.domain, item.title, item.detail[:250], item.source)
    existing = {
        (row.code, row.domain, row.title, row.detail[:250], row.source) for row in evidence
    }
    if signature not in existing:
        evidence.append(item)


def build_name_maps(frames: dict[str, pd.DataFrame]) -> tuple[dict[str, str], dict[str, str]]:
    code_to_name: dict[str, str] = {}
    for source, code_col, name_col in [
        ("eastmoney_comment", "代码", "名称"),
        ("notices", "代码", "名称"),
        ("lawsuits", "代码", "名称"),
        ("guarantees", "证券代码", "证券简称"),
        ("suspensions", "代码", "名称"),
        ("st_list", "代码", "名称"),
    ]:
        frame = frames.get(source)
        if frame is None or code_col not in frame.columns or name_col not in frame.columns:
            continue
        for _, row in frame.iterrows():
            code = stock_code(row.get(code_col))
            name = stock_name(row.get(name_col))
            if code and name:
                code_to_name[code] = name
    name_to_code = {stock_name(name): code for code, name in code_to_name.items() if name}
    return code_to_name, name_to_code


def market_snapshot(frames: dict[str, pd.DataFrame]) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    frame = frames.get("eastmoney_comment")
    if frame is not None:
        for _, row in frame.iterrows():
            code = stock_code(row.get("代码"))
            if not code:
                continue
            snapshot[code] = {
                "name": stock_name(row.get("名称")),
                "price": safe_number(row.get("最新价")),
                "pct_change": safe_number(row.get("涨跌幅")),
                "turnover": safe_number(row.get("换手率")),
                "attention": safe_number(row.get("关注指数")),
                "trade_date": str(row.get("交易日", "")),
            }
    spot = frames.get("market_spot")
    if spot is not None:
        for _, row in spot.iterrows():
            code = stock_code(row.get("代码"))
            if not code:
                continue
            current = snapshot.setdefault(code, {})
            updates = {
                "name": stock_name(row.get("名称")) or current.get("name", ""),
                "price": safe_number(row.get("最新价")),
                "pct_change": safe_number(row.get("涨跌幅")),
                "turnover": safe_number(row.get("换手率")),
                "trade_date": str(row.get("交易日") or now_shanghai().date().isoformat()),
            }
            current.update({key: value for key, value in updates.items() if value is not None})
    return snapshot


def classify_notice(title: str) -> tuple[int, str] | None:
    for severity, label, pattern in NOTICE_RULES:
        if pattern.search(title):
            if "参股子公司" in title:
                severity = min(severity, 2)
                label = "参股公司风险传导"
            elif "间接控股股东" in title:
                severity = min(severity, 3)
                label = "间接控股股东风险传导"
            elif "控股子公司" in title and severity >= 4:
                severity = 3
                label = "控股子公司重大风险"
            return severity, label
    return None


def parse_base_evidence(
    frames: dict[str, pd.DataFrame], run_timestamp: str
) -> tuple[list[Evidence], dict[str, dict[str, Any]], dict[str, set[str]], dict[str, str]]:
    evidence: list[Evidence] = []
    code_to_name, name_to_code = build_name_maps(frames)
    snapshot = market_snapshot(frames)

    notices = frames.get("notices")
    if notices is not None:
        for _, row in notices.iterrows():
            code = stock_code(row.get("代码"))
            title = compact_text(row.get("公告标题"))
            classified = classify_notice(title)
            if not code or not classified:
                continue
            severity, label = classified
            append_evidence(
                evidence,
                code,
                stock_name(row.get("名称")) or code_to_name.get(code, code),
                "监管披露",
                severity,
                "已公开风险",
                label,
                title,
                "上市公司公告",
                str(row.get("网址", SOURCE_URLS["notices"])),
                str(row.get("公告日期", run_timestamp)),
            )

    lawsuits = frames.get("lawsuits")
    if lawsuits is not None:
        for _, row in lawsuits.iterrows():
            code = stock_code(row.get("代码"))
            title = compact_text(row.get("公告标题"))
            if not code or not re.search(r"诉讼|仲裁|执行|冻结|查封", title):
                continue
            severity = 3 if re.search(r"重大|累计|大额|冻结|查封|强制执行", title) else 2
            append_evidence(
                evidence,
                code,
                stock_name(row.get("名称")) or code_to_name.get(code, code),
                "司法诉讼",
                severity,
                "已公开风险",
                "官方诉讼/仲裁/执行风险公告",
                title,
                "东方财富上市公司风险公告",
                str(row.get("网址", SOURCE_URLS["lawsuits"])),
                str(row.get("公告日期", run_timestamp)),
            )

    guarantees = frames.get("guarantees")
    if guarantees is not None:
        for _, row in guarantees.iterrows():
            code = stock_code(row.get("证券代码"))
            ratio = safe_number(row.get("担保金融占净资产比例"))
            if not code or ratio is None or ratio < 20:
                continue
            severity = 3 if ratio >= 100 else 2 if ratio >= 50 else 1
            append_evidence(
                evidence,
                code,
                stock_name(row.get("证券简称")) or code_to_name.get(code, code),
                "担保质押",
                severity,
                "已公开风险",
                "新增担保压力",
                f"近14日担保{row.get('担保笔数', '')}笔，担保金额{row.get('担保金额', '')}，"
                f"披露值占净资产{ratio:.2f}%",
                "巨潮资讯担保汇总",
                SOURCE_URLS["guarantees"],
                run_timestamp,
            )

    suspensions = frames.get("suspensions")
    if suspensions is not None:
        for _, row in suspensions.iterrows():
            code = stock_code(row.get("代码"))
            if not code:
                continue
            duration = compact_text(row.get("停牌期限"))
            market = compact_text(row.get("所属市场"))
            reason = compact_text(row.get("停牌原因"))
            severity = 2 if "连续" in duration or "风险警示" in market else 1
            append_evidence(
                evidence,
                code,
                stock_name(row.get("名称")) or code_to_name.get(code, code),
                "交易状态",
                severity,
                "已公开风险" if "风险警示" in market else "市场观察",
                "停牌/交易状态异常",
                f"{duration}；{reason}；{market}；预计复牌{row.get('预计复牌时间', '')}",
                "停复牌数据",
                SOURCE_URLS["suspensions"],
                str(row.get("停牌时间", run_timestamp)),
            )

    st_list = frames.get("st_list")
    if st_list is not None:
        for _, row in st_list.iterrows():
            code = stock_code(row.get("代码"))
            append_evidence(
                evidence,
                code,
                stock_name(row.get("名称")) or code_to_name.get(code, code),
                "交易状态",
                3,
                "已公开风险",
                "当前ST风险状态",
                "该股票出现在当前ST股票列表中",
                "ST股票列表",
                SOURCE_URLS["suspensions"],
                run_timestamp,
            )

    pledge_by_code: dict[str, dict[str, Any]] = {}
    for pledge in (frames.get("pledge_ratio"), frames.get("pledge_detail")):
        if pledge is None:
            continue
        code_columns = [col for col in pledge.columns if "代码" in str(col)]
        name_columns = [col for col in pledge.columns if "简称" in str(col) or "名称" in str(col)]
        ratio_columns = [
            col
            for col in pledge.columns
            if "质押比例" in str(col) or "占总股本" in str(col)
        ]
        if not code_columns or not ratio_columns:
            continue
        for _, row in pledge.iterrows():
            code = stock_code(row.get(code_columns[0]))
            ratios = [safe_number(row.get(column)) for column in ratio_columns]
            ratios = [value for value in ratios if value is not None]
            ratio = max(ratios) if ratios else None
            if not code or ratio is None:
                continue
            name = stock_name(row.get(name_columns[0])) if name_columns else code_to_name.get(code, code)
            if code not in pledge_by_code or ratio > float(pledge_by_code[code]["ratio"]):
                pledge_by_code[code] = {"ratio": ratio, "name": name or code_to_name.get(code, code)}
    for code, row in pledge_by_code.items():
        ratio = float(row["ratio"])
        if ratio < 30:
            continue
        severity = 3 if ratio >= 70 else 2 if ratio >= 50 else 1
        append_evidence(
            evidence,
            code,
            str(row["name"]),
            "担保质押",
            severity,
            "已公开风险",
            "高比例股权质押",
            f"最新可用质押比例字段最大值为{ratio:.2f}%",
            "股权质押数据",
            SOURCE_URLS["pledge"],
            run_timestamp,
        )

    for code, values in snapshot.items():
        pct = values.get("pct_change")
        turnover = values.get("turnover")
        attention = values.get("attention")
        if pct is None:
            continue
        severity = 0
        detail = ""
        if pct <= -9.5:
            severity = 2
            detail = f"涨跌幅{pct:.2f}%"
        elif pct <= -7 and (turnover or 0) >= 5:
            severity = 2
            detail = f"涨跌幅{pct:.2f}%，换手率{(turnover or 0):.2f}%"
        elif pct <= -5 and (attention or 0) >= 90:
            severity = 1
            detail = f"涨跌幅{pct:.2f}%，关注指数{attention:.1f}"
        if severity:
            append_evidence(
                evidence,
                code,
                values.get("name", code),
                "市场交易",
                severity,
                "市场观察",
                "价格与关注异常",
                detail,
                "东方财富舆情横截面",
                SOURCE_URLS["eastmoney_comment"],
                str(values.get("trade_date", run_timestamp)),
            )

    social_presence: dict[str, set[str]] = defaultdict(set)
    hot_rank = frames.get("eastmoney_hot_rank")
    if hot_rank is not None:
        for _, row in hot_rank.head(50).iterrows():
            code = stock_code(row.get("代码"))
            if code:
                social_presence[code].add("东方财富")
                code_to_name.setdefault(code, stock_name(row.get("股票名称")))

    comment_frame = frames.get("eastmoney_comment")
    if comment_frame is not None and "关注指数" in comment_frame.columns:
        attention_frame = comment_frame.copy()
        attention_frame["关注指数数值"] = pd.to_numeric(
            attention_frame["关注指数"], errors="coerce"
        )
        for _, row in attention_frame.nlargest(100, "关注指数数值").iterrows():
            code = stock_code(row.get("代码"))
            if code:
                social_presence[code].add("东方财富")

    for source in ["xueqiu_tweet", "xueqiu_follow"]:
        frame = frames.get(source)
        if frame is None:
            continue
        for _, row in frame.head(100).iterrows():
            code = stock_code(row.get("股票代码"))
            if code:
                social_presence[code].add("雪球")
                code_to_name.setdefault(code, stock_name(row.get("股票简称")))

    weibo = frames.get("weibo_report")
    if weibo is not None:
        for _, row in weibo.iterrows():
            name = stock_name(row.get("name"))
            code = name_to_code.get(name, "")
            if code:
                social_presence[code].add("微博")

    existing_codes = {item.code for item in evidence}
    for code, sources in social_presence.items():
        values = snapshot.get(code, {})
        pct = values.get("pct_change")
        if len(sources) < 2 or (code not in existing_codes and (pct is None or pct > -3)):
            continue
        severity = 2 if len(sources) >= 3 and pct is not None and pct <= -5 else 1
        append_evidence(
            evidence,
            code,
            code_to_name.get(code, values.get("name", code)),
            "跨平台舆情",
            severity,
            "前置线索",
            "跨平台关注共振",
            f"独立平台：{'、'.join(sorted(sources))}；涨跌幅{pct if pct is not None else '缺失'}%",
            "公开平台热度聚合",
            SOURCE_URLS["eastmoney_hot_rank"],
            run_timestamp,
        )

    return evidence, snapshot, social_presence, code_to_name


def listed_name_token(name: str) -> str:
    token = stock_name(name)
    token = re.sub(r"^(?:S\*ST|\*ST|ST|SST|N|C|XD|XR|DR)+", "", token, flags=re.I)
    return token


def literal_ticker_matches(
    text: str, code_to_name: dict[str, str]
) -> list[tuple[str, str, str]]:
    compact = compact_text(text)
    matches: list[tuple[str, str, str]] = []
    for code, name in code_to_name.items():
        token = listed_name_token(name)
        if len(token) >= 4 and token in compact:
            matches.append((code, name, token))
    return matches


def parse_connected_front_evidence(
    frames: dict[str, pd.DataFrame], code_to_name: dict[str, str], run_timestamp: str
) -> list[Evidence]:
    evidence: list[Evidence] = []

    tickets = frames.get("shcpe_enterprise_notices")
    if tickets is not None:
        for _, row in tickets.iterrows():
            title_text = compact_text(row.get("title"))
            if not re.search(r"逾期|拒付|未兑付|追索", title_text):
                continue
            resolved = bool(re.search(r"已结清|已兑付|已清偿", title_text))
            for code, name, token in literal_ticker_matches(title_text, code_to_name):
                append_evidence(
                    evidence,
                    code,
                    name,
                    "票据信用",
                    1 if resolved else 3,
                    "市场观察" if resolved else "前置线索",
                    "票交所历史逾期已结清" if resolved else "票交所未结清逾期/拒付名称命中",
                    f"上市简称字面命中={token}；公告标题={title_text}；"
                    f"articleId={row.get('articleId', '')}；关系需核验是否为发行人或其子公司",
                    "上海票据交易所企业公告",
                    SOURCE_URLS["shcpe_enterprise_notices"],
                    str(row.get("publishTime", run_timestamp)),
                )

    wage = frames.get("credit_gd_wage_arrears")
    if wage is not None:
        for _, row in wage.iterrows():
            subject = compact_text(row.get("ZTMC_STANDARD") or row.get("DXMC"))
            if not subject:
                continue
            amount = safe_number(row.get("SJJE")) or 0
            for code, name, token in literal_ticker_matches(subject, code_to_name):
                append_evidence(
                    evidence,
                    code,
                    name,
                    "员工与欠薪",
                    4 if amount >= 1_000_000 else 3,
                    "前置线索",
                    "官方欠薪失信名单名称命中",
                    f"上市简称字面命中={token}；名单主体={subject}；信用代码={row.get('TYSHXYDM') or row.get('ZJHM') or ''}；"
                    f"涉及金额={amount:.2f}；列入事由={compact_text(row.get('LRMDSY'))}；关系需核验",
                    "信用广东拖欠农民工工资失信名单",
                    SOURCE_URLS["credit_gd_wage_arrears"],
                    str(row.get("LRRQ", run_timestamp)),
                )

    court = frames.get("credit_gd_court_defaulters_recent")
    if court is not None:
        for _, row in court.iterrows():
            subject = compact_text(row.get("ZTMC_STANDARD") or row.get("SXBZXRMC"))
            if not subject:
                continue
            for code, name, token in literal_ticker_matches(subject, code_to_name):
                append_evidence(
                    evidence,
                    code,
                    name,
                    "司法执行",
                    4,
                    "前置线索",
                    "最高法失信被执行人名单名称命中",
                    f"上市简称字面命中={token}；失信主体={subject}；证件/组织代码={row.get('SFZHMHZZJGDM') or row.get('ZJHM') or ''}；"
                    f"案号={row.get('AH', '')}；执行法院={row.get('ZXFY', '')}；失信情形={compact_text(row.get('SXBZXRJTQX'))}；关系需核验",
                    "信用广东转引最高人民法院失信名单",
                    SOURCE_URLS["credit_gd_court_defaulters"],
                    str(row.get("FBRQ", run_timestamp)),
                )

    return evidence


def evidence_level(rows: list[Evidence]) -> str:
    if not rows:
        return "观察"
    max_severity = max(row.severity for row in rows)
    domains = {row.domain for row in rows}
    strong_domains = {row.domain for row in rows if row.severity >= 3}
    if max_severity >= 4:
        return "红色"
    if len(strong_domains) >= 2 or (max_severity >= 3 and len(domains) >= 2):
        return "橙色"
    if max_severity >= 3 or (max_severity >= 2 and len(domains) >= 2):
        return "黄色"
    return "观察"


def group_candidates(
    evidence: list[Evidence], snapshot: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    grouped: dict[str, list[Evidence]] = defaultdict(list)
    for item in evidence:
        grouped[item.code].append(item)
    candidates: list[dict[str, Any]] = []
    for code, rows in grouped.items():
        rows.sort(key=lambda item: (-item.severity, item.domain, item.title))
        market = snapshot.get(code, {})
        stages = {item.stage for item in rows}
        if "前置线索" in stages and "已公开风险" not in stages:
            stage = "前置线索"
        elif "已公开风险" in stages:
            stage = "已公开风险"
        else:
            stage = "市场观察"
        candidates.append(
            {
                "level": evidence_level(rows),
                "stage": stage,
                "code": code,
                "name": next((item.name for item in rows if item.name and item.name != code), code),
                "evidence_domains": len({item.domain for item in rows}),
                "evidence_count": len(rows),
                "max_severity": max(item.severity for item in rows),
                "price": market.get("price"),
                "pct_change": market.get("pct_change"),
                "turnover": market.get("turnover"),
                "attention": market.get("attention"),
                "top_reasons": "；".join(item.title for item in rows[:4]),
                "top_detail": "；".join(item.detail for item in rows[:3]),
            }
        )
    candidates.sort(
        key=lambda row: (
            -LEVEL_ORDER[row["level"]],
            -int(row["evidence_domains"]),
            -int(row["max_severity"]),
            -int(row["evidence_count"]),
            row["code"],
        )
    )
    return candidates


def row_text(row: pd.Series) -> str:
    parts: list[str] = []
    for value in row.to_dict().values():
        if value is None or pd.isna(value):
            continue
        text = str(value).strip()
        if text and text not in parts:
            parts.append(text)
    return " | ".join(parts)


def parse_deep_evidence(
    frames: dict[str, pd.DataFrame],
    codes: list[str],
    code_to_name: dict[str, str],
    run_timestamp: str,
) -> list[Evidence]:
    result: list[Evidence] = []
    for code in codes:
        for prefix, domain, source, url, stage in [
            ("news", "新闻线索", "东方财富个股新闻", SOURCE_URLS["eastmoney_news"], "前置线索"),
            ("irm", "投资者问答", "巨潮互动易", SOURCE_URLS["cninfo_irm"], "前置线索"),
            ("keywords", "跨平台舆情", "股吧热门关键词", SOURCE_URLS["eastmoney_hot_rank"], "前置线索"),
        ]:
            frame = frames.get(f"{prefix}_{code}")
            if frame is None or frame.empty:
                continue
            matches = 0
            for _, row in frame.head(250).iterrows():
                text = row_text(row)
                match = DEEP_RISK_RE.search(text)
                if not match:
                    continue
                severity = 2 if re.search(r"逾期|违约|失联|立案|冻结|停产|破产|重整|退市风险|财务造假", text) else 1
                if prefix == "irm":
                    question_columns = (
                        ["问题"]
                        if "问题" in frame.columns
                        else [column for column in frame.columns if str(column).endswith("问题")]
                    )
                    answer_columns = (
                        ["回答内容"]
                        if "回答内容" in frame.columns
                        else [
                            column
                            for column in frame.columns
                            if str(column).endswith("回答") or str(column).endswith("回复")
                        ]
                    )
                    question = " ".join(str(row.get(column, "")) for column in question_columns)
                    answer = " ".join(str(row.get(column, "")) for column in answer_columns)
                    question_match = DEEP_RISK_RE.search(question)
                    if not question_match:
                        continue
                    if THIRD_PARTY_SUGGESTION_RE.search(question):
                        continue
                    has_specificity = bool(
                        re.search(
                            r"\d|万元|亿元|客户|供应商|子公司|工厂|项目|订单|合同|账户|"
                            r"商票|债务|工资|社保|回款|减值|诉讼|仲裁",
                            question,
                        )
                    )
                    answer_denies = bool(DENIAL_RE.search(answer))
                    answer_confirms = bool(DEEP_RISK_RE.search(answer)) and not answer_denies
                    if not has_specificity and not answer_confirms:
                        continue
                    match = question_match
                    severity = 2 if answer_confirms else 1
                    stance = "公司回复含同类风险事项" if answer_confirms else "公司回复否认或未确认"
                else:
                    stance = "公开文本命中"
                append_evidence(
                    result,
                    code,
                    code_to_name.get(code, code),
                    domain,
                    severity,
                    stage,
                    f"具体风险线索：{match.group(0)}",
                    f"{stance}；{text[:950]}",
                    source,
                    url,
                    run_timestamp,
                )
                matches += 1
                if matches >= 5:
                    break
    return result


def trigrams(text: str) -> set[str]:
    normalized = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text).lower()
    if len(normalized) < 3:
        return {normalized} if normalized else set()
    return {normalized[index : index + 3] for index in range(len(normalized) - 2)}


def ingest_manual_rumors(path: Path, run_timestamp: str) -> list[Evidence]:
    if not path.exists():
        raise FileNotFoundError(f"manual rumor file does not exist: {path}")
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"code", "source", "claim"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("manual rumor CSV requires columns: code,source,claim")
        rows.extend({key: str(value or "") for key, value in item.items()} for item in reader)

    clusters: dict[str, list[dict[str, str]]] = defaultdict(list)
    cluster_texts: dict[str, set[str]] = {}
    for item in rows:
        code = stock_code(item.get("code"))
        claim = item.get("claim", "")
        grams = trigrams(claim)
        assigned = ""
        for cluster_id, existing in cluster_texts.items():
            if not grams or not existing:
                continue
            overlap = len(grams & existing) / max(1, len(grams | existing))
            if overlap >= 0.82:
                assigned = cluster_id
                break
        if not assigned:
            assigned = hashlib.sha256(f"{code}|{claim}".encode("utf-8")).hexdigest()[:16]
            cluster_texts[assigned] = grams
        item["code"] = code
        clusters[assigned].append(item)

    result: list[Evidence] = []
    for cluster_id, items in clusters.items():
        first = items[0]
        sources = sorted({item.get("source", "未知") for item in items})
        append_evidence(
            result,
            first["code"],
            first.get("name", first["code"]),
            "人工传闻",
            2 if len(sources) >= 2 else 1,
            "前置线索",
            f"人工传闻根源簇{cluster_id}",
            f"独立来源标签{len(sources)}个：{'、'.join(sources)}；原始陈述：{first.get('claim', '')}",
            "人工导入",
            first.get("url", ""),
            first.get("first_seen", run_timestamp),
        )
    return result


def write_outputs(
    output_dir: Path,
    run_id: str,
    run_timestamp: str,
    run_date: date,
    base_frames: dict[str, pd.DataFrame],
    base_health: list[SourceHealth],
    deep_health: list[SourceHealth],
    candidates: list[dict[str, Any]],
    evidence: list[Evidence],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_health = base_health + deep_health
    health_frame = pd.DataFrame(
        [asdict(item) for item in all_health], columns=SOURCE_HEALTH_COLUMNS
    )
    candidate_frame = pd.DataFrame(candidates, columns=CANDIDATE_COLUMNS)

    health_frame.to_csv(
        output_dir / "source_health.csv", index=False, encoding="utf-8-sig"
    )
    candidate_frame.to_csv(
        output_dir / "risk_candidates.csv", index=False, encoding="utf-8-sig"
    )
    front_candidates = [row for row in candidates if row["stage"] == "前置线索"]
    confirmed_candidates = [row for row in candidates if row["stage"] == "已公开风险"]
    front_candidate_frame = pd.DataFrame(front_candidates, columns=CANDIDATE_COLUMNS)
    confirmed_candidate_frame = pd.DataFrame(
        confirmed_candidates, columns=CANDIDATE_COLUMNS
    )
    evidence_frame = pd.DataFrame(
        [asdict(item) for item in evidence], columns=EVIDENCE_COLUMNS
    )
    front_candidate_frame.to_csv(
        output_dir / "front_candidates.csv", index=False, encoding="utf-8-sig"
    )
    confirmed_candidate_frame.to_csv(
        output_dir / "confirmed_risk_candidates.csv", index=False, encoding="utf-8-sig"
    )
    raw_front_files = {
        "shcpe_enterprise_notices": "front_source_shcpe_enterprise_notices.csv",
        "credit_gd_wage_arrears": "front_source_wage_arrears_gd.csv",
        "credit_gd_court_defaulters_recent": "front_source_court_defaulters_recent.csv",
    }
    for source_name, file_name in raw_front_files.items():
        frame = base_frames.get(source_name)
        if frame is not None:
            frame.to_csv(output_dir / file_name, index=False, encoding="utf-8-sig")
    with (output_dir / "evidence.jsonl").open("w", encoding="utf-8") as handle:
        for item in evidence:
            handle.write(json.dumps(json_safe(asdict(item)), ensure_ascii=False) + "\n")

    database = sqlite3.connect(output_dir / "risk_scan.sqlite")
    try:
        health_frame.to_sql(
            "source_health", database, if_exists="replace", index=False
        )
        candidate_frame.to_sql(
            "risk_candidates", database, if_exists="replace", index=False
        )
        front_candidate_frame.to_sql(
            "front_candidates", database, if_exists="replace", index=False
        )
        confirmed_candidate_frame.to_sql(
            "confirmed_risk_candidates", database, if_exists="replace", index=False
        )
        evidence_frame.to_sql(
            "evidence", database, if_exists="replace", index=False
        )
        for source_name in raw_front_files:
            frame = base_frames.get(source_name)
            if frame is not None:
                sqlite_safe_frame(frame).to_sql(
                    f"raw_{source_name}", database, if_exists="replace", index=False
                )
        database.execute(
            "CREATE TABLE IF NOT EXISTS run_manifest "
            "(run_id TEXT, run_timestamp TEXT, run_date TEXT, candidate_count INTEGER, evidence_count INTEGER)"
        )
        database.execute("DELETE FROM run_manifest")
        database.execute(
            "INSERT INTO run_manifest VALUES (?, ?, ?, ?, ?)",
            (run_id, run_timestamp, run_date.isoformat(), len(candidates), len(evidence)),
        )
        database.commit()
    finally:
        database.close()

    success = [item for item in base_health if item.status == "ok"]
    failed = [item for item in base_health if item.status != "ok"]
    level_counts = defaultdict(int)
    stage_counts = defaultdict(int)
    for row in candidates:
        level_counts[row["level"]] += 1
        stage_counts[row["stage"]] += 1

    report: list[str] = [
        "# A股前置风险扫描实际运行报告",
        "",
        f"- 运行编号：`{run_id}`",
        f"- 运行时间：{run_timestamp}",
        f"- 数据日期：{run_date.isoformat()}",
        f"- 基础数据源：成功 {len(success)}，失败/超时 {len(failed)}",
        f"- 候选股票：{len(candidates)}",
        f"- 证据记录：{len(evidence)}",
        "- 结果性质：工作队列优先级，不是暴雷概率，也不是买卖建议。",
        "",
        "## 分级结果",
        "",
        f"- 红色：{level_counts['红色']}",
        f"- 橙色：{level_counts['橙色']}",
        f"- 黄色：{level_counts['黄色']}",
        f"- 观察：{level_counts['观察']}",
        f"- 前置线索：{stage_counts['前置线索']}",
        f"- 已公开风险：{stage_counts['已公开风险']}",
        f"- 市场观察：{stage_counts['市场观察']}",
        "",
        "## 前置线索候选",
        "",
        "|等级|阶段|代码|名称|证据域|证据数|涨跌幅|主要原因|",
        "|---|---|---:|---|---:|---:|---:|---|",
    ]
    for row in front_candidates[:30]:
        pct = "" if row.get("pct_change") is None else f"{row['pct_change']:.2f}%"
        report.append(
            f"|{row['level']}|{row['stage']}|{row['code']}|{row['name']}|"
            f"{row['evidence_domains']}|{row['evidence_count']}|{pct}|{row['top_reasons']}|"
        )

    report.extend(
        [
            "",
            "## 已公开风险候选",
            "",
            "|等级|代码|名称|证据域|证据数|涨跌幅|主要原因|",
            "|---|---:|---|---:|---:|---:|---|",
        ]
    )
    for row in confirmed_candidates[:30]:
        pct = "" if row.get("pct_change") is None else f"{row['pct_change']:.2f}%"
        report.append(
            f"|{row['level']}|{row['code']}|{row['name']}|{row['evidence_domains']}|"
            f"{row['evidence_count']}|{pct}|{row['top_reasons']}|"
        )

    report.extend(["", "## 数据源健康", "", "|数据源|状态|行数|秒|用途/错误|", "|---|---|---:|---:|---|"])
    for item in base_health:
        note = item.purpose if item.status == "ok" else f"{item.purpose}；{item.error}"
        report.append(
            f"|{item.name}|{item.status}|{item.rows}|{item.elapsed_seconds:.2f}|{note}|"
        )

    report.extend(
        [
            "",
            "## 自动能力硬边界",
            "",
            "- 自动计分只使用 `source_health.csv` 中状态为 `ok` 且实际有返回行的数据源。",
            "- 新接入：票交所企业公告、广东欠薪失信名单、最高法失信被执行人最近数据镜像。",
            "- 已从自动能力删除：票交所登录后逐企业查询、法院全量执行查询、12315逐企业投诉、泛称供应商论坛、普通员工发帖。",
            "- 删除项不会产生空白分数或伪造的‘已覆盖’状态；机器边界见 `capability_manifest.json`。",
            "",
            "## 文件",
            "",
            "- `risk_candidates.csv`：候选工作队列。",
            "- `front_candidates.csv`：尚未形成正式风险公告的前置线索。",
            "- `confirmed_risk_candidates.csv`：已经公开的风险事项，单独存放避免冒充前置预警。",
            "- `evidence.jsonl`：逐条证据及链接。",
            "- `source_health.csv`：接口成功、失败和超时。",
            "- `front_source_shcpe_enterprise_notices.csv`：票交所企业公告原始返回。",
            "- `front_source_wage_arrears_gd.csv`：广东官方欠薪失信名单原始返回。",
            "- `front_source_court_defaulters_recent.csv`：最高法失信被执行人最近数据原始返回。",
            "- `capability_manifest.json`：已接通、已删除和真实范围的机器清单。",
            "- `risk_scan.sqlite`：可继续查询和追加历史运行的数据文件。",
        ]
    )
    (output_dir / "run_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    health_by_name = {item.name: item for item in base_health}
    capability_manifest = {
        "run_id": run_id,
        "policy": "只有本次实际返回数据的源才计入自动扫描；受登录、验证码、WAF或无稳定接口限制的源从自动能力中删除。",
        "connected": [
            {
                "id": "shcpe_enterprise_notices",
                "status": health_by_name.get("shcpe_enterprise_notices").status if health_by_name.get("shcpe_enterprise_notices") else "missing",
                "scope": "票交所最近1000条承兑人企业公告；不是登录后逐企业承兑信用查询",
                "rows": len(base_frames.get("shcpe_enterprise_notices", pd.DataFrame())),
                "output": raw_front_files["shcpe_enterprise_notices"],
            },
            {
                "id": "credit_gd_wage_arrears",
                "status": health_by_name.get("credit_gd_wage_arrears").status if health_by_name.get("credit_gd_wage_arrears") else "missing",
                "scope": "广东省认定的拖欠农民工工资失信名单按列入日期倒序最新50条",
                "rows": len(base_frames.get("credit_gd_wage_arrears", pd.DataFrame())),
                "output": raw_front_files["credit_gd_wage_arrears"],
            },
            {
                "id": "credit_gd_court_defaulters_recent",
                "status": health_by_name.get("credit_gd_court_defaulters_recent").status if health_by_name.get("credit_gd_court_defaulters_recent") else "missing",
                "scope": "信用广东转引最高人民法院失信被执行人按发布日期倒序最新50条",
                "rows": len(base_frames.get("credit_gd_court_defaulters_recent", pd.DataFrame())),
                "output": raw_front_files["credit_gd_court_defaulters_recent"],
            },
        ],
        "removed_from_automatic_scope": [
            {
                "id": "shcpe_per_enterprise_credit_query",
                "reason": "官网2026-07-15页面明确显示登录后解锁；未取得API注册和账户授权",
            },
            {
                "id": "court_all_execution_cases",
                "reason": "中国执行信息公开网逐企业查询要求验证码；不绕过验证码",
            },
            {
                "id": "complaints_12315_per_enterprise",
                "reason": "全国12315投诉公示官网及主列表接口在本机实测返回403/WAF",
            },
            {
                "id": "supplier_forums",
                "reason": "没有定义具体论坛、合法接口和主体映射，禁止以泛称冒充数据源",
            },
            {
                "id": "general_employee_posts",
                "reason": "没有稳定授权数据源；自动范围仅保留官方欠薪失信名单",
            },
        ],
    }
    (output_dir / "capability_manifest.json").write_text(
        json.dumps(capability_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    manifest = {
        "run_id": run_id,
        "run_timestamp": run_timestamp,
        "run_date": run_date.isoformat(),
        "candidate_count": len(candidates),
        "front_candidate_count": len(front_candidates),
        "confirmed_risk_candidate_count": len(confirmed_candidates),
        "evidence_count": len(evidence),
        "base_sources_ok": len(success),
        "base_sources_failed_or_timeout": len(failed),
        "output_files": sorted(path.name for path in output_dir.iterdir()),
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="风险排雷")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="结果目录；默认在脚本同级创建 run_时间戳",
    )
    parser.add_argument(
        "--deep-limit",
        type=int,
        default=8,
        help="对基础候选逐只深挖新闻、互动问答和热门关键词的数量",
    )
    parser.add_argument(
        "--rumors",
        type=Path,
        default=None,
        help="可选人工传闻CSV，至少包含 code,source,claim",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="运行数据日期 YYYY-MM-DD；默认上海当前日期",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_time = now_shanghai()
    run_date = date.fromisoformat(args.date) if args.date else run_time.date()
    run_id = run_time.strftime("risk-%Y%m%d-%H%M%S")
    output_dir = args.output_dir or Path(__file__).resolve().parent / f"run_{run_time:%Y%m%d_%H%M%S}"
    run_timestamp = run_time.isoformat(timespec="seconds")

    base_frames, base_health = fetch_sources(base_source_specs(run_date), max_parallel=4)
    evidence, snapshot, _, code_to_name = parse_base_evidence(base_frames, run_timestamp)
    evidence.extend(
        parse_connected_front_evidence(base_frames, code_to_name, run_timestamp)
    )
    if args.rumors:
        evidence.extend(ingest_manual_rumors(args.rumors, run_timestamp))

    preliminary = group_candidates(evidence, snapshot)
    front_first = [row for row in preliminary if row["stage"] == "前置线索"]
    other_rows = [row for row in preliminary if row["stage"] != "前置线索"]
    deep_codes = [
        row["code"] for row in (front_first + other_rows)[: max(0, args.deep_limit)]
    ]
    deep_frames: dict[str, pd.DataFrame] = {}
    deep_health: list[SourceHealth] = []
    if deep_codes:
        deep_frames, deep_health = fetch_sources(drill_source_specs(deep_codes), max_parallel=4)
        evidence.extend(parse_deep_evidence(deep_frames, deep_codes, code_to_name, run_timestamp))

    candidates = group_candidates(evidence, snapshot)
    write_outputs(
        output_dir,
        run_id,
        run_timestamp,
        run_date,
        base_frames,
        base_health,
        deep_health,
        candidates,
        evidence,
    )

    core_ok = {
        item.name for item in base_health if item.status == "ok"
    } & {"notices", "eastmoney_comment", "eastmoney_hot_rank", "xueqiu_tweet", "guarantees"}
    print(
        json.dumps(
            {
                "run_id": run_id,
                "output_dir": str(output_dir.resolve()),
                "core_sources_ok": sorted(core_ok),
                "candidates": len(candidates),
                "evidence": len(evidence),
            },
            ensure_ascii=False,
        )
    )
    return 0 if len(core_ok) >= 3 and len(candidates) > 0 else 3


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())
