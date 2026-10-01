#!/usr/bin/env python3
"""Daily read-only snapshots for public A-share data needed by 掌财智能体."""
from __future__ import annotations
import argparse, hashlib, json, math, urllib.parse, urllib.request
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("ZHANGCAI_DATA_DIR", Path(__file__).resolve().parents[1] / "data")) / "public"
UA = {
    "User-Agent": "Mozilla/5.0 (ZhangcaiAgent/1.0)",
    "Accept": "application/json,text/plain,*/*",
    # 东方财富 datacenter/push2 会校验来源；缺少该头时常见返回 403 或空 data。
    "Referer": "https://quote.eastmoney.com/",
}

def fetch(url):
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=25) as response:
        raw = response.read()
        return {"url": url, "status": response.status, "contentType": response.headers.get("content-type"), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "data": json.loads(raw.decode("utf-8-sig"))}

def source_available(name, data):
    if name == "eastmoneyLhb":
        return bool(data.get("success")) and isinstance((data.get("result") or {}).get("data"), list)
    if name == "eastmoneyLimitUp":
        return data.get("rc") == 0 and isinstance((data.get("data") or {}).get("pool"), list)
    if name == "lianban":
        return isinstance(data.get("kpi"), dict) and data.get("kpi", {}).get("date")
    return False

def attempt(name, url):
    try:
        result = fetch(url)
        if source_available(name, result["data"]):
            result["status"] = "available"
        else:
            result["status"] = "missing"
            result["error"] = str(result["data"].get("message") or result["data"].get("code") or "公开源未返回有效数据")
        return name, result
    except Exception as exc:
        return name, {"url": url, "status": "missing", "error": f"{type(exc).__name__}: {exc}"}

def _json_value(value):
    """把 AkShare DataFrame 中的 numpy/pandas 值转换为稳定 JSON。"""
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if hasattr(value, "item"):
        try:
            return _json_value(value.item())
        except Exception:
            pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return value

def _akshare_source(name, date_text, compact):
    """调用用户验证过的 AkShare 接口；未安装时保留可审计的 unavailable 状态。"""
    try:
        import akshare as ak
    except Exception as exc:
        return name, {"status": "unavailable", "provider": "akshare", "error": f"AkShare 未安装：{exc}"}
    try:
        if name == "akshareLhb":
            frame = ak.stock_lhb_detail_em(start_date=compact, end_date=compact)
        elif name == "akshareLhbSina":
            frame = ak.stock_lhb_detail_daily_sina(date=compact)
        elif name == "akshareLhbStockStatistic":
            frame = ak.stock_lhb_stock_statistic_em(symbol="近一月")
        elif name == "akshareLimitUpPool":
            frame = ak.stock_zt_pool_em(date=compact)
        else:
            return name, {"status": "missing", "provider": "akshare", "error": "未知 AkShare 方法"}
        records = []
        if frame is not None and hasattr(frame, "to_dict"):
            for row in frame.to_dict(orient="records"):
                records.append({str(key): _json_value(value) for key, value in row.items()})
        return name, {
            "status": "available" if records else "missing", "provider": "akshare",
            "method": name, "date": date_text, "data": {"records": records, "recordCount": len(records)},
        }
    except Exception as exc:
        return name, {"status": "missing", "provider": "akshare", "method": name, "date": date_text, "error": f"{type(exc).__name__}: {exc}"}

def _akshare_lhb_details(date_text, compact, overview_source):
    """补充龙虎榜席位明细；默认只取净买额靠前的 10 只，最多 3 路并发防限流。"""
    try:
        import akshare as ak
        overview = (overview_source.get("data") or {}).get("records") or []
        codes = []
        for row in overview:
            code = row.get("代码") or row.get("股票代码") or row.get("证券代码")
            if code and str(code) not in codes:
                codes.append(str(code).zfill(6))
        limit = max(1, int(os.environ.get("ZHANGCAI_AKSHARE_DETAIL_LIMIT", "10")))
        tasks = [(code, flag) for code in codes[:limit] for flag in ("买入", "卖出")]
        def load(item):
            code, flag = item
            frame = ak.stock_lhb_stock_detail_em(symbol=code, date=compact, flag=flag)
            rows = [] if frame is None or not hasattr(frame, "to_dict") else [
                {str(key): _json_value(value) for key, value in row.items()}
                for row in frame.to_dict(orient="records")
            ]
            return {"代码": code, "方向": flag, "records": rows}
        records = []
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(load, item) for item in tasks]
            for future in as_completed(futures):
                try:
                    value = future.result()
                    if value["records"]:
                        records.append(value)
                except Exception:
                    # 单只股票被限流或无席位时保留其他结果，不让整日同步失败。
                    continue
        return "akshareLhbStockDetail", {"status": "available" if records else "missing", "provider": "akshare", "method": "stock_lhb_stock_detail_em", "date": date_text, "data": {"records": records, "recordCount": len(records), "symbolLimit": limit}}
    except Exception as exc:
        return "akshareLhbStockDetail", {"status": "missing", "provider": "akshare", "method": "stock_lhb_stock_detail_em", "date": date_text, "error": f"{type(exc).__name__}: {exc}"}

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--date", required=True); args = parser.parse_args()
    compact = args.date.replace("-", "")
    if len(compact) != 8 or not compact.isdigit():
        raise SystemExit("--date 必须是 YYYY-MM-DD 或 YYYYMMDD")
    date_text = f"{compact[:4]}-{compact[4:6]}-{compact[6:]}"
    lhb = urllib.parse.urlencode({"sortColumns":"SECURITY_CODE,TRADE_DATE","sortTypes":"1,-1","pageSize":"5000","pageNumber":"1","reportName":"RPT_DAILYBILLBOARD_DETAILSNEW","columns":"SECURITY_CODE,SECURITY_NAME_ABBR,TRADE_DATE,BILLBOARD_NET_AMT,BILLBOARD_BUY_AMT,BILLBOARD_SELL_AMT,EXPLAIN","source":"WEB","client":"WEB","filter":f"(TRADE_DATE<='{date_text}')(TRADE_DATE>='{date_text}')"})
    jobs = {
      "lianban": f"https://lianban.net/opendata/{date_text}.json",
      "eastmoneyLimitUp": "https://push2ex.eastmoney.com/getTopicZTPool?" + urllib.parse.urlencode({"ut":"7eea3edcaed734bea9cbfc24409ed989","dpt":"wz.ztzt","Pageindex":"0","pagesize":"10000","sort":"fbt:asc","date":compact}),
      "eastmoneyLhb": "https://datacenter-web.eastmoney.com/api/data/v1/get?" + lhb,
    }
    rows = dict(attempt(name, url) for name, url in jobs.items())
    # AkShare 是可选增强源：exe 基座不强制捆绑 pandas/akshare，安装后每日同步会自动写入。
    # 源记录直接进入同一快照，Harness 可按 method/provider 读取并在报告中标注来源。
    for name in ("akshareLhb", "akshareLhbSina", "akshareLhbStockStatistic", "akshareLimitUpPool"):
        source_name, source = _akshare_source(name, date_text, compact)
        rows[source_name] = source
    detail_name, detail_source = _akshare_lhb_details(date_text, compact, rows.get("akshareLhb", {}))
    rows[detail_name] = detail_source
    payload = {"schema":"ZHANGCAI_PUBLIC_MARKET_V1","date":date_text,"fetchedAt":datetime.now().astimezone().isoformat(timespec="seconds"),"sources":rows}
    # 原始公开源是报告的可追溯证据：同一交易日的重试也追加保存，绝不覆盖旧快照。
    day_dir = ROOT / compact
    day_dir.mkdir(parents=True, exist_ok=True)
    output = day_dir / f"market-{datetime.now().strftime('%H%M%S')}.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    # 固定入口供网页在下一次构建/启动时读取；按交易日目录保留的原始快照仍是审计依据。
    (ROOT / "latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output":str(output),"statuses":{k:v["status"] for k,v in rows.items()}}, ensure_ascii=False))

if __name__ == "__main__": main()
