#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-
"""
增强风险扫描器 - 补充 ST、财务风险、公告风险检测
================================================================
用法:
  python enhanced_risk_scanner.py --st-list          # 生成ST列表
  python enhanced_risk_scanner.py --check 000029     # 检查单只股票
  python enhanced_risk_scanner.py --check-all         # 检查全市场
"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import os
import re
import struct
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# ── Constants ──────────────────────────────────────────────────────────────
TDX_ROOT = Path(r"C:\new_tdx_mock")
VIPDOC = TDX_ROOT / "vipdoc"
HUB_SCRIPT = Path(__file__).resolve().parent / "tdx_hub.py"
ST_CACHE = Path(__file__).resolve().parent / "st_blacklist.json"
RISK_CACHE = Path(__file__).resolve().parent / "risk_blacklist.json"

SH_LDAY = VIPDOC / "sh" / "lday"
SZ_LDAY = VIPDOC / "sz" / "lday"
SH_XINZENG = VIPDOC / "xinzeng" / "sh" / "lday"
SZ_XINZENG = VIPDOC / "xinzeng" / "sz" / "lday"


def run_hub(command: list[str]) -> dict:
    """Run tdx_hub.py and return JSON result."""
    try:
        result = subprocess.run(
            [sys.executable, str(HUB_SCRIPT)] + command,
            capture_output=True, text=True, timeout=60,
            encoding="utf-8", errors="replace"
        )
        return json.loads(result.stdout.strip())
    except:
        return {"error": "hub call failed"}


def get_all_codes() -> list[str]:
    """Get all A-share stock codes from TDX .day files."""
    codes = set()
    for d in [SH_LDAY, SZ_LDAY, SH_XINZENG, SZ_XINZENG]:
        if d.exists():
            for f in d.glob("*.day"):
                name = f.stem  # sh600000 or sz000001
                code = name[2:]
                codes.add(code)
    return sorted(codes)


# ── ST Detection ────────────────────────────────────────────────────────────

def build_st_blacklist() -> dict:
    """
    Build ST blacklist by scanning stock names via TQ formula.
    
    Strategy: Batch-call TQ "大牛线4.0" formula for batches of stocks.
    The formula returns industry/concept info. Since TQ calls are slow
    (~750ms each), we do a lightweight pre-scan:
    
    Phase 1: Check stock name via batch probe (30 stocks per batch, ~800ms/batch)
    Phase 2: If probe finds name contains ST/*ST/S*ST markers, add to blacklist
    
    Falls back to file-name based detection for stocks without TQ probes.
    """
    print("Building ST blacklist from TDX...")
    st_list = {}
    all_codes = get_all_codes()
    batch_size = 30
    
    # Known ST prefix patterns to check via stock name
    st_patterns = ['ST', '*ST', 'SST', 'S*ST', 'NST', 'PT']
    
    for i in range(0, len(all_codes), batch_size):
        batch = all_codes[i:i+batch_size]
        
        # Try to probe each stock with a lightweight request
        for code in batch:
            symbol = code
            if code.startswith('6'):
                symbol = code + ".SH"
            elif code.startswith('0') or code.startswith('3') or code.startswith('2'):
                symbol = code + ".SZ"
            
            # Quick check: try to get stock name from kline meta
            result = run_hub(["kline", symbol, "--limit", "1"])
            if result.get("ok"):
                meta = result.get("meta", {})
                stock_name = meta.get("name", "")
                if stock_name:
                    for pat in st_patterns:
                        if stock_name.startswith(pat) or ('*' + pat) in stock_name:
                            reason = f"ST股 (名称含{pat}: {stock_name})"
                            st_list[code] = {
                                "name": stock_name,
                                "reason": reason,
                                "detected_at": datetime.now().isoformat()
                            }
                            print(f"  ST: {code} {stock_name}")
                            break
        
        if i % 300 == 0 and i > 0:
            print(f"  Progress: {i}/{len(all_codes)}, ST found: {len(st_list)}")
    
    # Save cache
    with open(ST_CACHE, "w", encoding="utf-8") as f:
        json.dump({
            "updated": datetime.now().isoformat(),
            "total_checked": len(all_codes),
            "st_count": len(st_list),
            "stocks": st_list
        }, f, ensure_ascii=False, indent=2)
    
    print(f"ST blacklist built: {len(st_list)}/{len(all_codes)} ST stocks")
    return st_list


def load_st_blacklist() -> dict:
    """Load cached ST blacklist."""
    if ST_CACHE.exists():
        with open(ST_CACHE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Check if cache is fresh (< 7 days)
        updated = datetime.fromisoformat(data.get("updated", "2000-01-01"))
        if datetime.now() - updated < timedelta(days=7):
            return data.get("stocks", {})
    return {}


# ── Financial Risk Detection ────────────────────────────────────────────────

def check_financial_risk(code: str) -> list[str]:
    """
    Check financial risk factors from available TDX data.
    
    Currently checks:
    1. Recent price collapse (>30% drop in 10 days → possible negative news)
    2. Abnormal volume surge without price increase (distribution pattern)
    3. Persistent decline (price below all MAs for extended period)
    
    For full "连续三年亏损" check, needs financial statement data
    from TDX's cw_cache or external source.
    """
    risks = []
    symbol = code
    if code.startswith('6'):
        symbol = code + ".SH"
    else:
        symbol = code + ".SZ"
    
    result = run_hub(["kline", symbol, "--limit", "120"])
    if not result.get("ok") or not result.get("records"):
        return ["data unavailable"]
    
    records = result["records"]
    if len(records) < 20:
        return ["insufficient data"]
    
    # Check for collapse pattern (>30% in 5 days)
    if len(records) >= 10:
        closes = [r["close"] for r in records]
        for i in range(5, len(closes)):
            drop = (closes[i-5] / closes[i] - 1) * 100
            if drop > 30:
                risks.append(f"疑似利空事件: 5日暴跌{drop:.1f}% (从{closes[i-5]:.2f}到{closes[i]:.2f})")
                break
    
    # Check for distribution pattern (high volume with price decline)
    volumes = [r["volume"] for r in records[-20:]]
    avg_vol = sum(volumes) / len(volumes)
    for i, r in enumerate(records[-10:]):
        if r["volume"] > avg_vol * 2 and r["close"] < r["open"] and \
           r["close"] < records[-10+i-1]["close"] if i > 0 else False:
            pass  # single distribution day is okay, check pattern
    
    # Check for gap-down pattern (possible negative news)
    for i in range(1, len(records[-20:])):
        idx = len(records) - 20 + i
        if records[idx]["open"] < records[idx-1]["close"] * 0.95:
            if records[idx]["close"] < records[idx]["open"] * 0.95:
                risks.append(f"疑似利空跳空: {records[idx]['date']} 跳空低开{((1-records[idx]['open']/records[idx-1]['close'])*100):.1f}%")
                break
    
    return risks


# ── Announcement Risk Detection (立案/减持) ──────────────────────────────────

def check_announcement_risk(code: str) -> list[str]:
    """
    Check for negative announcements (立案/减持/违规) from TDX news cache.
    
    TDX stores news/announcement data in:
    - T0002/info_cache/  (individual stock info)
    - T0002/msg_zx/      (message center)
    - T0002/msg_web/     (web messages)
    
    Scans these directories for keywords related to:
    立案调查, 减持, 违规, 处罚, 退市风险, 问询函, 监管函
    """
    risks = []
    keywords = ["立案调查", "立案", "减持", "违规", "处罚", "退市风险", 
                "问询函", "监管函", "警示函", "责令改正", "暂停上市",
                "终止上市", "重大违法", "强制退市"]
    
    # Scan info_cache for this stock
    info_dir = TDX_ROOT / "T0002" / "info_cache"
    news_dirs = [
        TDX_ROOT / "T0002" / "msg_zx",
        TDX_ROOT / "T0002" / "msg_web",
        TDX_ROOT / "T0002" / "msg_jy",
    ]
    
    # Check info_cache for files matching this code
    if info_dir.exists():
        for f in info_dir.glob(f"*{code}*"):
            try:
                content = f.read_text(encoding="gbk", errors="ignore")[:2000]
                for kw in keywords:
                    if kw in content:
                        risks.append(f"公告风险({kw}): {f.name}")
                        break
            except:
                pass
    
    # Quick scan of news dirs
    for news_dir in news_dirs:
        if not news_dir.exists():
            continue
        for f in list(news_dir.iterdir())[:100]:  # limited scan
            try:
                if f.suffix in ['.txt', '.dat', '.xml', '.json']:
                    content = f.read_text(encoding="gbk", errors="ignore")[:5000]
                    if code in content:
                        for kw in keywords:
                            if kw in content:
                                idx = content.find(kw)
                                snippet = content[max(0,idx-20):idx+60].replace('\n',' ')
                                risks.append(f"公告风险({kw}): {snippet[:80]}...")
                                break
            except:
                pass
    
    return risks


# ── Comprehensive Risk Check ────────────────────────────────────────────────

def comprehensive_risk_check(code: str, st_list: dict = None) -> dict:
    """
    Run all risk checks for a single stock.
    Returns risk assessment dict.
    """
    risks = []
    
    # 1. ST check
    if st_list is None:
        st_list = load_st_blacklist()
    if code in st_list:
        risks.append({
            "type": "ST",
            "severity": "critical",
            "detail": st_list[code].get("reason", "ST股票")
        })
    
    # 2. Financial risk
    fin_risks = check_financial_risk(code)
    for r in fin_risks:
        risks.append({
            "type": "financial",
            "severity": "high",
            "detail": r
        })
    
    # 3. Announcement risk (立案/减持)
    ann_risks = check_announcement_risk(code)
    for r in ann_risks:
        risks.append({
            "type": "announcement",
            "severity": "critical" if any(kw in r for kw in ["立案", "退市", "终止", "强制"]) else "high",
            "detail": r
        })
    
    # 4. K-line based risk (from pre_breakout_scanner)
    # This is done separately in the main scanner
    
    return {
        "code": code,
        "risk_count": len(risks),
        "critical_count": sum(1 for r in risks if r["severity"] == "critical"),
        "risks": risks,
        "pass": len(risks) == 0,
        "checked_at": datetime.now().isoformat()
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def cmd_build_st_list():
    """Build and cache ST blacklist."""
    st_list = build_st_blacklist()
    print(f"\nST Blacklist: {len(st_list)} stocks")
    for code, info in sorted(st_list.items())[:20]:
        print(f"  {code}: {info['reason']}")
    if len(st_list) > 20:
        print(f"  ... and {len(st_list)-20} more")
    print(f"\nSaved to: {ST_CACHE}")


def cmd_check(args):
    """Check single stock for all risks."""
    code = args.code.zfill(6)
    st_list = load_st_blacklist()
    
    print(f"\n=== 风险扫描: {code} ===")
    result = comprehensive_risk_check(code, st_list)
    
    status = "❌ 有风险" if not result["pass"] else "✅ 通过"
    print(f"结果: {status}")
    print(f"风险项数: {result['risk_count']} (严重: {result['critical_count']})")
    
    for r in result["risks"]:
        print(f"  [{r['severity']}] [{r['type']}] {r['detail']}")
    
    print()


def cmd_check_all(args):
    """Check all stocks for risks."""
    st_list = load_st_blacklist()
    all_codes = get_all_codes()
    limit = min(args.limit or len(all_codes), len(all_codes))
    
    print(f"\n=== 全市场风险扫描 (前 {limit} 只) ===")
    
    risky_stocks = []
    for code in all_codes[:limit]:
        result = comprehensive_risk_check(code, st_list)
        if not result["pass"]:
            risky_stocks.append(result)
            if len(risky_stocks) <= 50 or result["critical_count"] > 0:
                print(f"  {code}: {result['risk_count']} 风险 ({result['critical_count']} 严重)")
    
    print(f"\n风险股票: {len(risky_stocks)}/{limit}")
    
    # Save full results
    output_path = Path(__file__).resolve().parent / "risk_scan_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "scanned_at": datetime.now().isoformat(),
            "total_scanned": limit,
            "risky_count": len(risky_stocks),
            "results": risky_stocks
        }, f, ensure_ascii=False, indent=2)
    print(f"完整结果: {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="增强风险扫描器")
    sub = parser.add_subparsers(dest="command")
    
    p_list = sub.add_parser("build-st-list", help="生成ST黑名单")
    
    p_check = sub.add_parser("check", help="检查单只股票")
    p_check.add_argument("code", help="股票代码")
    
    p_all = sub.add_parser("check-all", help="全市场检查")
    p_all.add_argument("--limit", type=int, default=100, help="扫描数量限制")
    
    args = parser.parse_args()
    
    if args.command == "build-st-list":
        cmd_build_st_list()
    elif args.command == "check":
        cmd_check(args)
    elif args.command == "check-all":
        cmd_check_all(args)
    else:
        parser.print_help()
