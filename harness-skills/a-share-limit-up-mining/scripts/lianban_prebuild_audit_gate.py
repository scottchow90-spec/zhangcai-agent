#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prebuild audit for the Lianban report.

This gate runs before a Word report is generated. It verifies source scope,
not just source connectivity: QSYB must be stock-level research rows and RDXZ
must be stock-level news rows. Generic market headlines are not acceptable
inputs for those template tables.
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_tdx_root

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKILL_ROOT = Path(__file__).resolve().parents[1]
ZTC = resolve_tdx_root() / "T0002" / "blocknew" / "ZTC.blk"
APPROVED_TEMPLATE = SKILL_ROOT / "assets" / "连板挖掘模板.docx"
TODAY_YYYYMMDD = datetime.now().strftime("%Y%m%d")
TODAY_ISO = datetime.now().strftime("%Y-%m-%d")
MIN_ZTC_CODES = 1
PROBE_LIMIT = 50
LHB_LOOKBACK_DAYS = 7
TRANSIENT_SOURCE_ATTEMPTS = 3
TRANSIENT_SOURCE_DELAYS = (0.5, 1.5)


def call_transient_source(
    operation,
    *,
    attempts: int = TRANSIENT_SOURCE_ATTEMPTS,
    delays: tuple[float, ...] = TRANSIENT_SOURCE_DELAYS,
    sleep=time.sleep,
):
    if attempts < 1:
        raise ValueError("attempts must be positive")
    for attempt in range(attempts):
        try:
            return operation()
        except json.JSONDecodeError:
            if attempt + 1 >= attempts:
                raise
            delay = delays[min(attempt, len(delays) - 1)] if delays else 0.0
            sleep(delay)
    raise RuntimeError("unreachable transient-source retry state")


def clean(value) -> str:
    return str(value or "").strip()


def is_stock_code(value) -> bool:
    return re.fullmatch(r"\d{6}", clean(value)) is not None


def has_cjk(value) -> bool:
    return re.search(r"[\u4e00-\u9fff]", clean(value)) is not None


def is_real_value(value) -> bool:
    return clean(value) not in {"", "-", "--", "N/A", "n/a", "\u6682\u65e0", "\u53c2\u8003"}


def read_ztc_codes() -> list[str]:
    text = ZTC.read_text(encoding="gbk", errors="ignore")
    codes = []
    for line in text.splitlines():
        item = line.strip()
        if not item:
            continue
        code = item[-6:] if len(item) >= 6 else item
        if is_stock_code(code) and code != "000000":
            codes.append(code)
    return list(dict.fromkeys(codes))


def choose_probe_codes(ztc_codes: list[str], ak_rows) -> list[str]:
    """Choose real stock probes from the dated AK limit-up pool.

    Local ZTC codes are only a preference signal. They must never narrow or
    replace the dated AK business pool, and placeholder 000000 is ignored.
    """
    real_ztc = {
        clean(code)
        for code in ztc_codes
        if is_stock_code(code) and clean(code) != "000000"
    }
    if ak_rows is None:
        return []

    if isinstance(ak_rows, list):
        records = ak_rows
    else:
        try:
            records = ak_rows.to_dict("records")
        except Exception:
            return []

    ak_codes = []
    code_fields = ("\u4ee3\u7801", "code", "\u8bc1\u5238\u4ee3\u7801", "\u80a1\u7968\u4ee3\u7801")
    for row in records:
        if not isinstance(row, dict):
            continue
        code = next((clean(row.get(field)) for field in code_fields if clean(row.get(field))), "")
        if is_stock_code(code) and code != "000000":
            ak_codes.append(code)
    ak_codes = list(dict.fromkeys(ak_codes))
    preferred = [code for code in ak_codes if code in real_ztc]
    remaining = [code for code in ak_codes if code not in real_ztc]
    return (preferred + remaining)[:PROBE_LIMIT]


def normalize_date(value: str | None) -> str:
    if not value:
        return TODAY_YYYYMMDD
    text = clean(value).replace("-", "")
    if not re.fullmatch(r"\d{8}", text):
        raise SystemExit(f"invalid --date: {value!r}; expected YYYYMMDD or YYYY-MM-DD")
    return text


def stock_name_map(ak) -> dict[str, str]:
    df = call_transient_source(ak.stock_info_a_code_name)
    out = {}
    if df is None or df.empty:
        return out
    code_col = next((c for c in df.columns if "\u4ee3\u7801" in str(c) or str(c).lower() == "code"), None)
    name_col = next((c for c in df.columns if "\u540d\u79f0" in str(c) or "\u7b80\u79f0" in str(c) or str(c).lower() == "name"), None)
    if not code_col or not name_col:
        return out
    for _, row in df.iterrows():
        code = clean(row.get(code_col))
        name = clean(row.get(name_col))
        if is_stock_code(code) and has_cjk(name):
            out[code] = name
    return out


def probe_research_rows(ak, codes: list[str]) -> dict:
    hits = []
    errors = []

    def fetch(code):
        try:
            df = ak.stock_research_report_em(symbol=code)
        except Exception as exc:
            return None, f"{code}:{type(exc).__name__}"
        if df is None or df.empty:
            return None, None
        for _, row in df.head(5).iterrows():
            row_code = clean(row.get("\u80a1\u7968\u4ee3\u7801", code))
            row_name = clean(row.get("\u80a1\u7968\u7b80\u79f0", ""))
            report = clean(row.get("\u62a5\u544a\u540d\u79f0", ""))
            rating = clean(row.get("\u4e1c\u8d22\u8bc4\u7ea7", ""))
            org = clean(row.get("\u673a\u6784", ""))
            industry = clean(row.get("\u884c\u4e1a", ""))
            date = clean(row.get("\u65e5\u671f", ""))
            if (
                row_code == code
                and is_stock_code(row_code)
                and has_cjk(row_name)
                and is_real_value(report)
                and is_real_value(rating)
                and is_real_value(org)
                and is_real_value(industry)
                and re.match(r"\d{4}-\d{2}-\d{2}", date)
            ):
                return {
                    "code": row_code,
                    "name": row_name,
                    "report": report[:80],
                    "rating": rating,
                    "org": org,
                    "industry": industry,
                    "date": date,
                }, None
        return None, None

    probe_codes = list(codes[:PROBE_LIMIT])
    if probe_codes:
        with ThreadPoolExecutor(max_workers=min(8, len(probe_codes))) as pool:
            for hit, error in pool.map(fetch, probe_codes):
                if hit:
                    hits.append(hit)
                if error:
                    errors.append(error)
    return {"count": len(hits), "sample": hits[:5], "errors": errors[:10]}


def probe_news_rows(ak, codes: list[str], names: dict[str, str]) -> dict:
    hits = []
    errors = []

    def fetch(item):
        code, name = item
        try:
            df = call_transient_source(lambda: ak.stock_news_em(symbol=code))
        except Exception as exc:
            return None, f"{code}:{type(exc).__name__}"
        if df is None or df.empty:
            return None, None
        for _, row in df.head(10).iterrows():
            title = clean(row.get("\u65b0\u95fb\u6807\u9898", ""))
            content = clean(row.get("\u65b0\u95fb\u5185\u5bb9", ""))
            published = clean(row.get("\u53d1\u5e03\u65f6\u95f4", ""))
            source = clean(row.get("\u6587\u7ae0\u6765\u6e90", row.get("\u6765\u6e90", "")))
            searchable = title + "\n" + content
            if (
                is_real_value(title)
                and is_real_value(content)
                and is_real_value(published)
                and is_real_value(source)
                and code in searchable
                and name in searchable
            ):
                return {
                    "code": code,
                    "name": name,
                    "title": title[:80],
                    "published": published,
                    "source": source,
                }, None
        return None, None

    probe_items = [
        (code, names.get(code, ""))
        for code in codes[:PROBE_LIMIT]
        if has_cjk(names.get(code, ""))
    ]
    if probe_items:
        with ThreadPoolExecutor(max_workers=min(8, len(probe_items))) as pool:
            for hit, error in pool.map(fetch, probe_items):
                if hit:
                    hits.append(hit)
                if error:
                    errors.append(error)
    return {"count": len(hits), "sample": hits[:5], "errors": errors[:10]}


def probe_risk_announcement_source(ak, codes: list[str], date_yyyymmdd: str) -> dict:
    errors = []
    end_date = datetime.strptime(date_yyyymmdd, "%Y%m%d")
    begin_date = (end_date - timedelta(days=20)).strftime("%Y-%m-%d")
    end_text = end_date.strftime("%Y-%m-%d")
    for code in codes[:5]:
        try:
            frame = ak.stock_individual_notice_report(
                security=code, symbol="全部", begin_date=begin_date, end_date=end_text
            )
            return {"ok": True, "code": code, "rows": 0 if frame is None else len(frame), "begin": begin_date, "end": end_text, "errors": errors}
        except Exception as exc:
            errors.append(f"{code}:{type(exc).__name__}")
    return {"ok": False, "code": "", "rows": 0, "begin": begin_date, "end": end_text, "errors": errors}


def fetch_recent_lhb(ak, date_yyyymmdd: str) -> dict:
    errors = []
    today = datetime.strptime(date_yyyymmdd, "%Y%m%d")
    for delta in range(LHB_LOOKBACK_DAYS + 1):
        day = (today - timedelta(days=delta)).strftime("%Y%m%d")
        try:
            df = ak.stock_lhb_detail_em(start_date=day, end_date=day)
        except Exception as exc:
            errors.append(f"{day}:{type(exc).__name__}")
            continue
        if df is not None and not df.empty:
            return {"ok": True, "date": day, "count": len(df), "columns": [str(c) for c in df.columns], "errors": errors}
        errors.append(f"{day}:empty")
    return {"ok": False, "date": "", "count": 0, "columns": [], "errors": errors}


def prepare_pandas_for_akshare_news() -> None:
    """Avoid pyarrow regex failure inside akshare.stock_news_em.

    akshare 1.18.64 calls Series.str.replace(r"\\u3000", regex=True).
    With pandas' Arrow string backend this raises ArrowInvalid, so force
    ordinary Python string storage before probing stock-bound news.
    """
    try:
        import pandas as pd

        pd.options.mode.string_storage = "python"
        pd.set_option("future.infer_string", False)
    except Exception:
        pass


def audit(date: str | None = None, template: str | None = None) -> dict:
    date_yyyymmdd = normalize_date(date)
    date_iso = datetime.strptime(date_yyyymmdd, "%Y%m%d").strftime("%Y-%m-%d")
    blocks = []
    evidence = {
        "date": date_iso,
        "date_yyyymmdd": date_yyyymmdd,
        "qsyb_required_source": "akshare.stock_research_report_em(symbol=<6-digit stock code>)",
        "rdxz_required_source": "akshare.stock_news_em(symbol=<6-digit stock code>) plus stock_info_a_code_name name binding",
        "forbidden_substitution": [
            "finance.eastmoney.com/a/czqyw.html generic securities-focus headlines",
            "akshare.stock_info_global_em generic global market news",
            "keyword-only hot-topic summaries without stock code/name binding",
        ],
    }

    evidence["tdx_ztc_exists"] = ZTC.exists()
    ztc_codes: list[str] = []
    if not ZTC.exists():
        evidence["tdx_ztc_cross_check"] = "UNAVAILABLE"
    else:
        ztc_codes = read_ztc_codes()
        evidence["tdx_ztc_count"] = len(ztc_codes)
        evidence["tdx_ztc_sample"] = ztc_codes[:10]
        if len(ztc_codes) < MIN_ZTC_CODES:
            evidence["tdx_ztc_cross_check"] = "IGNORED_PLACEHOLDER_OR_EMPTY"
        else:
            evidence["tdx_ztc_cross_check"] = "AVAILABLE"

    prepare_pandas_for_akshare_news()
    try:
        import akshare as ak
    except Exception as exc:
        blocks.append(f"AUDIT_BLOCKED_AKSHARE_IMPORT_FAIL: {type(exc).__name__}")
        return {"status": "AUDIT_BLOCKED", "blocks": blocks, "evidence": evidence}

    df = None
    try:
        df = ak.stock_zt_pool_em(date=date_yyyymmdd)
        evidence["ak_zt_ok"] = df is not None and not df.empty
        evidence["ak_zt_count"] = len(df) if df is not None else 0
        if df is None or df.empty:
            blocks.append("AUDIT_BLOCKED_AK_ZT_EMPTY")
    except Exception as exc:
        blocks.append(f"AUDIT_BLOCKED_AK_ZT_FAIL: {type(exc).__name__}")

    lhb_probe = fetch_recent_lhb(ak, date_yyyymmdd)
    evidence["ak_lhb_ok"] = lhb_probe["ok"]
    evidence["ak_lhb_date"] = lhb_probe["date"]
    evidence["ak_lhb_count"] = lhb_probe["count"]
    evidence["ak_lhb_lookback_days"] = LHB_LOOKBACK_DAYS
    evidence["ak_lhb_errors"] = lhb_probe["errors"][:10]
    evidence["ak_lhb_columns"] = lhb_probe["columns"][:25]
    evidence["ak_lhb_exact_trade_date"] = lhb_probe["date"] == date_yyyymmdd
    if not lhb_probe["ok"]:
        blocks.append(f"AUDIT_BLOCKED_AK_LHB_FAIL: {','.join(lhb_probe['errors'][:5])}")
    elif lhb_probe["date"] != date_yyyymmdd:
        blocks.append(f"AUDIT_BLOCKED_AK_LHB_NOT_EXACT_DATE: got={lhb_probe['date']} expected={date_yyyymmdd}")

    try:
        names = stock_name_map(ak)
        evidence["stock_name_map_count"] = len(names)
        if len(names) < 1000:
            blocks.append(f"AUDIT_BLOCKED_STOCK_NAME_MAP_TOO_SMALL: {len(names)}")
    except Exception as exc:
        names = {}
        blocks.append(f"AUDIT_BLOCKED_STOCK_NAME_MAP_FAIL: {type(exc).__name__}")

    probe_codes = choose_probe_codes(ztc_codes, df)
    evidence["probe_codes"] = probe_codes
    if not probe_codes:
        blocks.append("AUDIT_BLOCKED_AK_ZT_HAS_NO_REAL_STOCK_CODES")

    research_probe = probe_research_rows(ak, probe_codes)
    evidence["qsyb_stock_bound_research_probe"] = research_probe
    if research_probe["count"] < 1:
        blocks.append("AUDIT_BLOCKED_QSYB_NO_STOCK_BOUND_RESEARCH_ROWS")

    news_probe = probe_news_rows(ak, probe_codes, names)
    evidence["rdxz_stock_bound_news_probe"] = news_probe
    if news_probe["count"] < 1:
        blocks.append("AUDIT_BLOCKED_RDXZ_NO_STOCK_BOUND_NEWS_ROWS")

    risk_probe = probe_risk_announcement_source(ak, probe_codes, date_yyyymmdd)
    evidence["stock_bound_risk_announcement_probe"] = risk_probe
    if not risk_probe["ok"]:
        blocks.append("AUDIT_BLOCKED_STOCK_BOUND_RISK_SOURCE_FAIL")

    template_path = Path(template).expanduser().resolve() if template else APPROVED_TEMPLATE
    evidence["template_path"] = str(template_path)
    evidence["template_exists"] = template_path.exists()
    evidence["template_size"] = template_path.stat().st_size if template_path.exists() else 0
    if not template_path.exists():
        blocks.append("AUDIT_BLOCKED_TEMPLATE_MISSING")

    status = "AUDIT_CLEAN" if not blocks else "AUDIT_BLOCKED"
    return {"status": status, "blocks": blocks, "evidence": evidence}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="Audit trading date, YYYYMMDD or YYYY-MM-DD. Defaults to today.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", help="Write audit result JSON to this path.")
    ap.add_argument("--template", help="Template DOCX path to verify.")
    args = ap.parse_args()

    res = audit(args.date, args.template)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(res["status"])
    if res["status"] == "AUDIT_BLOCKED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
