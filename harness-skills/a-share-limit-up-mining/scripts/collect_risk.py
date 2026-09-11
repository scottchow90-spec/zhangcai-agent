#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parents[2] / "tmp_lb" / "data"
sys.path.insert(0, str(SCRIPT_DIR))
from run_research import find_tdx_day_path, read_tdx_day
HARD_KEYWORDS = {
    "regulatory": ("立案", "重大违法", "行政处罚"),
    "delisting": ("退市风险", "终止上市", "退市整理"),
    "audit": ("否定意见", "无法表示意见", "非标准审计", "非标审计"),
}
SOFT_KEYWORDS = {
    "reduction": ("减持",),
    "unlock": ("解禁", "限售股上市流通"),
    "financial": ("预亏", "亏损", "业绩修正"),
    "litigation": ("诉讼", "仲裁"),
    "clarification": ("澄清", "风险提示", "异常波动"),
}


def classify(title: str, url: str, event_date: str) -> list[dict]:
    flags = []
    for category, keywords in HARD_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title:
                flags.append({
                    "severity": "hard", "category": category, "keyword": keyword,
                    "event_date": event_date, "within_5_trading_days": True,
                    "ongoing": category in {"regulatory", "delisting", "audit"},
                    "evidence_id": url, "title": title,
                })
                break
    for category, keywords in SOFT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in title:
                flags.append({
                    "severity": "soft", "category": category, "keyword": keyword,
                    "event_date": event_date, "within_5_trading_days": True,
                    "ongoing": False, "evidence_id": url, "title": title,
                })
                break
    return flags


def confirm_empty_notice_window(code: str, begin_date: str, end_date: str) -> bool:
    import requests

    response = requests.get(
        "https://np-anotice-stock.eastmoney.com/api/security/ann",
        params={
            "sr": "-1", "page_size": "1", "page_index": "1", "ann_type": "A",
            "client_source": "web", "f_node": "0", "s_node": "0",
            "stock_list": code, "begin_time": begin_date, "end_time": end_date,
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json().get("data") or {}
    return int(data.get("total_hits", -1)) == 0


def choose_risk_codes(all_zt_codes: list[str], ztc_codes: list[str] | set[str]) -> list[str]:
    """Review every real code in the dated limit-up pool.

    ZTC is a passive local cross-check only. Valid intersections are probed
    first, but an empty, stale, or placeholder-only ZTC must not remove real
    stocks from the dated AK limit-up business pool.
    """
    dated_codes = list(dict.fromkeys(
        str(code).strip()
        for code in all_zt_codes
        if str(code).strip().isdigit()
        and len(str(code).strip()) == 6
        and str(code).strip() != "000000"
    ))
    local_codes = {
        str(code).strip()
        for code in ztc_codes
        if str(code).strip().isdigit()
        and len(str(code).strip()) == 6
        and str(code).strip() != "000000"
    }
    preferred = [code for code in dated_codes if code in local_codes]
    remaining = [code for code in dated_codes if code not in local_codes]
    return preferred + remaining


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit() or len(sys.argv[1]) != 8:
        raise SystemExit("usage: collect_risk.py YYYYMMDD")
    trade_date = sys.argv[1]
    raw_path = DATA_DIR / f"raw3_{trade_date}.json"
    if not raw_path.is_file():
        raise SystemExit(f"raw input missing: {raw_path}")
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    all_zt_codes = list(dict.fromkeys(
        str(row.get("code", ""))
        for row in payload.get("zt_pool", [])
        if str(row.get("code", "")).isdigit()
        and len(str(row.get("code", ""))) == 6
        and str(row.get("code", "")) != "000000"
    ))
    ztc_codes = {
        str(code) for code in payload.get("ztc_local", [])
        if str(code).isdigit() and len(str(code)) == 6 and str(code) != "000000"
    }
    codes = choose_risk_codes(all_zt_codes, ztc_codes)
    if not codes:
        raise SystemExit("risk collection blocked: dated ZT pool has no real stock codes")
    trade_day = datetime.strptime(trade_date, "%Y%m%d").date()
    code_cutoffs = {}
    for code in codes:
        day_path = find_tdx_day_path(code)
        records = [row for row in read_tdx_day(day_path) if row["date"] <= trade_day] if day_path else []
        code_cutoffs[code] = records[-5]["date"] if len(records) >= 5 else None
    valid_cutoffs = [cutoff for cutoff in code_cutoffs.values() if cutoff is not None]
    begin_date = min(valid_cutoffs).isoformat() if valid_cutoffs else trade_day.isoformat()
    end_date = trade_day.isoformat()
    import akshare as ak

    def probe_code(code: str) -> tuple[str, dict, dict | None]:
        cutoff = code_cutoffs.get(code)
        if cutoff is None:
            error = "TDX 日线不足 5 个交易日，无法验证风险窗口"
            return code, {"review_complete": False, "risk_flags": [], "error": error}, {
                "code": code, "error": error,
            }
        try:
            frame = ak.stock_individual_notice_report(
                security=code, symbol="全部", begin_date=begin_date, end_date=end_date
            )
        except KeyError as exc:
            if str(exc).strip("'\"") == "代码":
                try:
                    if confirm_empty_notice_window(code, begin_date, end_date):
                        frame = None
                    else:
                        error = f"{type(exc).__name__}: {exc}"
                        return code, {"review_complete": False, "risk_flags": [], "error": error}, {
                            "code": code, "error": error,
                        }
                except Exception as confirm_exc:
                    error = f"{type(confirm_exc).__name__}: {confirm_exc}"
                    return code, {"review_complete": False, "risk_flags": [], "error": error}, {
                        "code": code, "error": error,
                    }
            else:
                error = f"{type(exc).__name__}: {exc}"
                return code, {"review_complete": False, "risk_flags": [], "error": error}, {
                    "code": code, "error": error,
                }
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            return code, {"review_complete": False, "risk_flags": [], "error": error}, {
                "code": code, "error": error,
            }
        flags = []
        if frame is not None and not frame.empty:
            for _, row in frame.iterrows():
                title = str(row.get("公告标题", "")).strip()
                url = str(row.get("网址", "")).strip()
                event_date = str(row.get("公告日期", ""))[:10]
                if not title or not url or not event_date:
                    continue
                try:
                    event_day = datetime.strptime(event_date, "%Y-%m-%d").date()
                except ValueError:
                    continue
                if event_day < cutoff or event_day > trade_day:
                    continue
                flags.extend(classify(title, url, event_date))
        return code, {
            "review_complete": True,
            "window": {"begin": cutoff.isoformat(), "end": end_date, "basis": "本地 TDX 最近5个交易日"},
            "risk_flags": flags,
        }, None

    risk_evidence = {}
    errors = []
    # Keep the full per-stock review within the orchestrator's fixed
    # 300-second window without changing source, scope, or risk rules.
    with ThreadPoolExecutor(max_workers=min(8, len(codes))) as pool:
        for code, evidence, error in pool.map(probe_code, codes):
            risk_evidence[code] = evidence
            if error:
                errors.append(error)

    payload["risk_evidence"] = risk_evidence
    payload["risk_collection"] = {
        "source": "akshare.stock_individual_notice_report",
        "scope": "full_current_zt_pool_with_passive_local_ztc_cross_check",
        "input_zt_pool_codes": len(all_zt_codes),
        "ztc_real_codes": len(ztc_codes),
        "ztc_intersection_codes": sum(1 for code in all_zt_codes if code in ztc_codes),
        "excluded_before_risk_review": 0,
        "codes_probed": len(codes),
        "review_complete_codes": sum(1 for item in risk_evidence.values() if item.get("review_complete") is True),
        "errors": errors,
    }
    out_path = DATA_DIR / f"raw4_{trade_date}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"risk_codes={len(codes)} complete={payload['risk_collection']['review_complete_codes']} errors={len(errors)} saved={out_path}")
    if payload["risk_collection"]["review_complete_codes"] != len(codes) or errors:
        print("ERROR: risk review is not complete for every audited code", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
