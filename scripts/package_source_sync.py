#!/usr/bin/env python3
"""Capture credential-free sources declared by the imported data skill.

This is a bounded supplementer, not an opaque scraper.  Every provider is
written below app-data/evidence/package-sources/<date>/ with the requested
date, actual provider response metadata, source hash, parsed data and errors.
Sources that require a key or are not stable public endpoints remain absent
from this collector and are reported by skill14_data_runtime.py.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests


APP_ROOT = Path(os.environ.get("ZHANGCAI_APP_ROOT", Path(__file__).resolve().parents[1]))
DATA_ROOT = Path(os.environ.get("ZHANGCAI_DATA_DIR", APP_ROOT / "app-data"))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ZhangcaiAgent/1.0", "Accept": "application/json,text/plain,*/*"}
TIMEOUT = 30


def compact_date(value: str) -> str:
    raw = re.sub(r"\D", "", str(value or ""))
    if len(raw) != 8:
        raise ValueError("--date 必须是 YYYYMMDD")
    return raw


def market_prefix(code: str) -> str:
    return "bj" if code.startswith("92") else "sh" if code.startswith(("5", "6", "9")) else "sz"


def normalize_codes(value: str) -> list[str]:
    values = []
    for raw in str(value or "").replace(",", " ").split():
        match = re.search(r"(\d{6})", raw)
        if match and match.group(1) not in values:
            values.append(match.group(1))
    return values


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def response_json(response: requests.Response) -> tuple[Any, dict[str, Any]]:
    raw = response.content
    return response.json(), {
        "url": response.url,
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type", ""),
        "bytes": len(raw),
        "response_sha256": sha256(raw),
    }


def result(provider: str, requested_date: str, *, status: str, records: Any = None, meta: dict[str, Any] | None = None, error: str = "", scope: str = "target_codes") -> dict[str, Any]:
    records = records if isinstance(records, list) else records if isinstance(records, dict) else []
    meta = meta or {}
    retrieved_at = iso_now()
    source_url = str(meta.get("url") or meta.get("endpoint") or meta.get("workbook_url") or "")
    source_hash = str(meta.get("response_sha256") or "")
    value: dict[str, Any] = {
        "schema": "ZHANGCAI_PACKAGE_SOURCE_SNAPSHOT_V1",
        "provider": provider,
        "source": provider,
        "requested_date": requested_date,
        "source_date": requested_date,
        "retrieved_at": retrieved_at,
        "fetched_at": retrieved_at,
        "source_url_or_local_root": source_url,
        "source_sha256": source_hash,
        "status": status,
        "scope": scope,
        "record_count": len(records) if isinstance(records, list) else None,
        "records": records,
        "meta": meta,
        "error_or_reason": error,
    }
    if error:
        value["error"] = error
    return value


def fetch_baidu(code: str, requested_date: str) -> dict[str, Any]:
    url = "https://finance.pae.baidu.com/selfselect/getstockquotation"
    params = {"all": "1", "isIndex": "false", "isBk": "false", "isBlock": "false", "isFutures": "false", "isStock": "true", "newFormat": "1", "group": "quotation_kline_ab", "finClientType": "pc", "code": code, "start_time": "", "ktype": "1"}
    try:
        response = requests.get(url, params=params, headers={**UA, "Accept": "application/vnd.finance-web.v1+json", "Origin": "https://gushitong.baidu.com", "Referer": "https://gushitong.baidu.com/"}, timeout=TIMEOUT)
        response.raise_for_status()
        body, meta = response_json(response)
        result_obj = body.get("Result", {}) if isinstance(body, dict) else {}
        market = result_obj.get("newMarketData", {}) if isinstance(result_obj, dict) else {}
        keys = market.get("keys", []) if isinstance(market, dict) else []
        raw_rows = str(market.get("marketData", "") or "").split(";") if isinstance(market, dict) else []
        records = []
        for raw in raw_rows:
            values = raw.split(",")
            if not raw or not isinstance(keys, list):
                continue
            records.append({str(key): values[index] if index < len(values) else None for index, key in enumerate(keys)})
        meta.update({"endpoint": url, "keys": keys, "code": code})
        return result("baidu", requested_date, status="available" if records else "empty", records=records, meta=meta)
    except Exception as exc:
        return result("baidu", requested_date, status="unavailable", meta={"endpoint": url, "code": code}, error=f"{type(exc).__name__}: {exc}")


def fetch_ths(code: str, requested_date: str) -> dict[str, Any]:
    url = f"https://basic.10jqka.com.cn/new/{code}/worth.html"
    try:
        response = requests.get(url, headers={**UA, "Referer": "https://basic.10jqka.com.cn/"}, timeout=TIMEOUT)
        response.raise_for_status()
        response.encoding = "gbk"
        frames = pd.read_html(io.StringIO(response.text))
        selected = next((frame for frame in frames if any("每股收益" in str(column) or "均值" in str(column) for column in frame.columns)), frames[0] if frames else pd.DataFrame())
        selected.columns = [str(column) for column in selected.columns]
        records = selected.where(pd.notna(selected), None).to_dict(orient="records")
        meta = {"url": response.url, "http_status": response.status_code, "bytes": len(response.content), "response_sha256": sha256(response.content), "endpoint": url, "code": code, "columns": list(selected.columns)}
        return result("ths", requested_date, status="available" if records else "empty", records=records, meta=meta)
    except Exception as exc:
        return result("ths", requested_date, status="unavailable", meta={"endpoint": url, "code": code}, error=f"{type(exc).__name__}: {exc}")


def cninfo_org_map() -> dict[str, str]:
    response = requests.get("http://www.cninfo.com.cn/new/data/szse_stock.json", headers=UA, timeout=TIMEOUT)
    body = response.json()
    rows = body.get("stockList", []) if isinstance(body, dict) else []
    return {str(row.get("code")): str(row.get("orgId")) for row in rows if isinstance(row, dict) and row.get("code") and row.get("orgId")}


def fetch_cninfo(code: str, requested_date: str, org_map: dict[str, str]) -> dict[str, Any]:
    url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
    org_id = org_map.get(code) or f"gs{market_prefix(code)}0{code}"
    data = {"stock": f"{code},{org_id}", "tabName": "fulltext", "pageSize": "30", "pageNum": "1", "column": "", "category": "", "plate": "", "seDate": "", "searchkey": "", "secid": "", "sortName": "", "sortType": "", "isHLtitle": "true"}
    headers = {**UA, "Content-Type": "application/x-www-form-urlencoded", "Referer": "https://www.cninfo.com.cn/new/disclosure", "Origin": "https://www.cninfo.com.cn"}
    try:
        response = requests.post(url, data=data, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        body, meta = response_json(response)
        rows = body.get("announcements", []) if isinstance(body, dict) else []
        records = []
        for row in rows if isinstance(rows, list) else []:
            stamp = row.get("announcementTime")
            if isinstance(stamp, (int, float)):
                date = datetime.fromtimestamp(stamp / 1000).strftime("%Y-%m-%d")
            else:
                date = str(stamp or "")[:10]
            records.append({"title": row.get("announcementTitle", ""), "type": row.get("announcementTypeName", ""), "date": date, "url": f"https://www.cninfo.com.cn/new/disclosure/detail?annoId={row.get('announcementId', '')}"})
        meta.update({"endpoint": url, "code": code, "org_id": org_id})
        return result("cninfo", requested_date, status="available" if records else "empty", records=records, meta=meta)
    except Exception as exc:
        return result("cninfo", requested_date, status="unavailable", meta={"endpoint": url, "code": code, "org_id": org_id}, error=f"{type(exc).__name__}: {exc}")


def fetch_sw(requested_date: str) -> dict[str, Any]:
    url = "https://www.swsresearch.com/swindex/pdf/SwClass2021/StockClassifyUse_stock.xls"
    try:
        tls_note = ""
        try:
            response = requests.get(url, headers=UA, timeout=60)
        except requests.exceptions.SSLError as exc:
            # The skill package documents this public XLS as credential-free.
            # Some Windows bundles lack the issuer in their CA store; retry
            # once explicitly and preserve that fact in the receipt.
            response = requests.get(url, headers=UA, timeout=60, verify=False)
            tls_note = f"certificate_verify_failed_then_explicit_insecure_retry: {type(exc).__name__}: {exc}"
        response.raise_for_status()
        frame = pd.read_excel(io.BytesIO(response.content))
        frame = frame.rename(columns={"股票代码": "code", "计入日期": "start_date", "行业代码": "industry_code", "更新日期": "update_date"})
        missing = {"code", "start_date", "industry_code"} - set(frame.columns)
        if missing:
            raise RuntimeError(f"缺少字段: {sorted(missing)}")
        frame["code"] = frame["code"].astype(str).str.zfill(6)
        frame["industry_code"] = frame["industry_code"].astype(str).str.zfill(6)
        frame["l1_code"] = frame["industry_code"].str[:2] + "0000"
        frame["l2_code"] = frame["industry_code"].str[:4] + "00"
        frame["start_date"] = pd.to_datetime(frame["start_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        frame["update_date"] = pd.to_datetime(frame["update_date"], errors="coerce").dt.strftime("%Y-%m-%d") if "update_date" in frame else None
        records = frame.where(pd.notna(frame), None).to_dict(orient="records")
        meta = {"url": response.url, "http_status": response.status_code, "bytes": len(response.content), "response_sha256": sha256(response.content), "endpoint": url, "rows": len(records), "symbols": len(set(row.get("code") for row in records)), "tls_note": tls_note}
        return result("sw", requested_date, status="available" if records else "empty", records=records, meta=meta, scope="full_history")
    except Exception as exc:
        return result("sw", requested_date, status="unavailable", meta={"endpoint": url}, error=f"{type(exc).__name__}: {exc}", scope="full_history")


def fetch_nbs(requested_date: str) -> dict[str, Any]:
    index_url = "https://www.stats.gov.cn/sj/zxfb/"
    try:
        index = requests.get(index_url, headers=UA, timeout=TIMEOUT)
        index.encoding = index.apparent_encoding or "utf-8"
        links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>\s*([^<]{6,100}?)\s*</a>', index.text)
        hit = next(((href, title.strip()) for href, title in links if "采购经理指数" in title), None)
        if not hit:
            raise RuntimeError("统计局发布页未找到采购经理指数")
        url = urljoin(index_url, hit[0])
        page = requests.get(url, headers=UA, timeout=TIMEOUT)
        page.encoding = page.apparent_encoding or "utf-8"
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", page.text, flags=re.S)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"[\s\u3000\xa0]+", "", text)
        grab = lambda pattern: float(re.search(pattern, text).group(1)) if re.search(pattern, text) else None
        period = re.search(r"(\d{4})年(\d{1,2})月", hit[1])
        records = [{"title": hit[1], "period": f"{period.group(1)}-{int(period.group(2)):02d}" if period else None, "manufacturing_pmi": grab(r"(?<!非)制造业采购经理指数（PMI）为([\d.]+)%"), "non_manufacturing_pmi": grab(r"非制造业商务活动指数为([\d.]+)%"), "composite_pmi": grab(r"综合PMI产出指数为([\d.]+)%"), "source_url": url}]
        if any(record is None for record in (records[0]["manufacturing_pmi"], records[0]["non_manufacturing_pmi"], records[0]["composite_pmi"])):
            raise RuntimeError("PMI 核心字段解析不完整")
        meta = {"index_url": index_url, "url": page.url, "http_status": page.status_code, "bytes": len(page.content), "response_sha256": sha256(page.content), "endpoint": index_url}
        return result("macro", requested_date, status="available", records=records, meta=meta, scope="latest_official_period")
    except Exception as exc:
        return result("macro", requested_date, status="unavailable", meta={"endpoint": index_url}, error=f"{type(exc).__name__}: {exc}", scope="latest_official_period")


def fetch_pbc(requested_date: str) -> dict[str, Any]:
    index_url = "https://www.pbc.gov.cn/diaochatongjisi/116219/116319/index.html"
    try:
        index = requests.get(index_url, headers=UA, timeout=TIMEOUT)
        index.encoding = index.apparent_encoding or "utf-8"
        years = re.findall(r"href=[\"']([^\"']+)[\"'][^>]*>\s*(\d{4})年统计数据\s*</a>", index.text)
        if not years:
            raise RuntimeError("人民银行索引页未找到年份")
        table = {int(year): href for href, year in years}
        target_year = max(table)
        year_url = urljoin("https://www.pbc.gov.cn", table[target_year])
        year_page = requests.get(year_url, headers=UA, timeout=TIMEOUT)
        year_page.encoding = year_page.apparent_encoding or "utf-8"
        topics = re.findall(r"href=[\"']([^\"']+)[\"'][^>]*>\s*(社会融资规模)\s*</a>", year_page.text)
        if not topics:
            raise RuntimeError("人民银行年份页未找到社会融资规模")
        topic_url = urljoin("https://www.pbc.gov.cn", topics[0][0])
        topic_page = requests.get(topic_url, headers=UA, timeout=TIMEOUT)
        topic_page.encoding = topic_page.apparent_encoding or "utf-8"
        books = re.findall(r"href=[\"']([^\"']+\.xlsx?)[\"']", topic_page.text, flags=re.I)
        if not books:
            raise RuntimeError("社融专题页未找到 xls/xlsx 附件")
        workbook_url = urljoin("https://www.pbc.gov.cn", books[0])
        workbook = requests.get(workbook_url, headers=UA, timeout=60)
        raw = pd.read_excel(io.BytesIO(workbook.content), header=None)
        start = next((index for index in range(len(raw)) if str(raw.iloc[index, 0]).strip() == "月份"), None)
        if start is None:
            raise RuntimeError("社融工作簿未找到月份表头")
        columns = ["month", "afre_total", "rmb_loans", "fx_loans", "entrusted_loans", "trust_loans", "undiscounted_bankers_acceptance", "corporate_bonds", "government_bonds", "equity_financing", "abs_by_depository", "loans_written_off"]
        frame = raw.iloc[start + 3:, :len(columns)].copy()
        frame.columns = columns
        frame = frame[frame["month"].astype(str).str.match(r"^\d{4}\.\d{1,2}$", na=False)].copy()
        for column in columns[1:]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame["month"] = frame["month"].map(lambda value: f"{int(float(value)):04d}-{int(round((float(value) % 1) * 100)):02d}")
        frame = frame[frame["month"].str.startswith(f"{target_year}-")].dropna(subset=["afre_total"])
        records = frame.where(pd.notna(frame), None).to_dict(orient="records")
        meta = {"index_url": index_url, "workbook_url": workbook_url, "http_status": workbook.status_code, "bytes": len(workbook.content), "response_sha256": sha256(workbook.content), "endpoint": index_url, "year": target_year}
        return result("macro", requested_date, status="available" if records else "empty", records=records, meta=meta, scope="latest_year_monthly")
    except Exception as exc:
        return result("macro", requested_date, status="unavailable", meta={"endpoint": index_url}, error=f"{type(exc).__name__}: {exc}", scope="latest_year_monthly")


def write_snapshot(root: Path, provider: str, value: dict[str, Any]) -> str:
    target = root / provider / "snapshot.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return str(target.relative_to(DATA_ROOT)).replace("\\", "/")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--codes", default="")
    parser.add_argument("--skip-sw", action="store_true")
    parser.add_argument("--skip-macro", action="store_true")
    args = parser.parse_args()
    compact = compact_date(args.date)
    requested_date = f"{compact[:4]}-{compact[4:6]}-{compact[6:]}"
    codes = normalize_codes(args.codes)
    if not codes:
        files = (DATA_ROOT / "evidence" / "supplemental" / compact).glob("[0-9][0-9][0-9][0-9][0-9][0-9].*.json")
        codes = sorted({path.name[:6] for path in files})
    root = DATA_ROOT / "evidence" / "package-sources" / compact
    snapshots: dict[str, Any] = {}
    for provider in ("baidu", "ths"):
        rows = [fetch_baidu(code, requested_date) if provider == "baidu" else fetch_ths(code, requested_date) for code in codes]
        value = {"schema": "ZHANGCAI_PACKAGE_SOURCE_BATCH_V1", "provider": provider, "requested_date": requested_date, "fetched_at": iso_now(), "scope": "target_codes", "codes": codes, "status": "available" if any(row.get("status") == "available" for row in rows) else "missing", "results": rows, "record_count": sum(int(row.get("record_count") or 0) for row in rows)}
        snapshots[provider] = {"path": write_snapshot(root, provider, value), "status": value["status"], "record_count": value["record_count"], "scope": value["scope"]}
    try:
        org_map = cninfo_org_map()
    except Exception:
        org_map = {}
    rows = [fetch_cninfo(code, requested_date, org_map) for code in codes]
    value = {"schema": "ZHANGCAI_PACKAGE_SOURCE_BATCH_V1", "provider": "cninfo", "requested_date": requested_date, "fetched_at": iso_now(), "scope": "target_codes", "codes": codes, "org_map_count": len(org_map), "status": "available" if any(row.get("status") == "available" for row in rows) else "missing", "results": rows, "record_count": sum(int(row.get("record_count") or 0) for row in rows)}
    snapshots["cninfo"] = {"path": write_snapshot(root, "cninfo", value), "status": value["status"], "record_count": value["record_count"], "scope": value["scope"]}
    if not args.skip_sw:
        value = fetch_sw(requested_date)
        snapshots["sw"] = {"path": write_snapshot(root, "sw", value), "status": value["status"], "record_count": value.get("record_count", 0), "scope": value["scope"]}
    if not args.skip_macro:
        macro_rows = [fetch_nbs(requested_date), fetch_pbc(requested_date)]
        value = {"schema": "ZHANGCAI_PACKAGE_SOURCE_BATCH_V1", "provider": "macro", "requested_date": requested_date, "fetched_at": iso_now(), "scope": "latest_official_period", "status": "available" if any(row.get("status") == "available" for row in macro_rows) else "missing", "results": macro_rows, "record_count": sum(int(row.get("record_count") or 0) for row in macro_rows)}
        snapshots["macro"] = {"path": write_snapshot(root, "macro", value), "status": value["status"], "record_count": value["record_count"], "scope": value["scope"]}
    receipt = {"schema": "ZHANGCAI_PACKAGE_SOURCE_SYNC_RECEIPT_V1", "requested_date": requested_date, "fetched_at": iso_now(), "codes": codes, "snapshots": snapshots, "rules": ["仅无凭据公开源；目标日期与源实际期间分开保存。", "按代码批次只标记 partial，不代表全市场覆盖。", "失败源保留 status/error，不用空数组替代真实数据。"]}
    receipt_path = root / "manifest.json"
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "available" if any(item.get("status") == "available" for item in snapshots.values()) else "degraded", "requested_date": requested_date, "codes": len(codes), "manifest": str(receipt_path), "snapshots": snapshots}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
