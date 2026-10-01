#!/usr/bin/env python3
# -*- coding: utf-8-sig -*-
"""
首板涨停前选股扫描器 v1.1 (Enhanced Risk + TQ Verification)
============================================================
基于 TDX 全量 K 线 + TQ 公式 + 公告扫描, 7 大维度全量覆盖
"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import argparse, json, math, os, subprocess, sys, time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(APP_SCRIPTS))
from tdx_path_config import resolve_tdx_root

TDX_ROOT = resolve_tdx_root()
HUB_SCRIPT = Path(__file__).resolve().parent / "tdx_hub.py"
SH_LDAY = TDX_ROOT / "vipdoc" / "sh" / "lday"
SZ_LDAY = TDX_ROOT / "vipdoc" / "sz" / "lday"
SH_XINZENG = TDX_ROOT / "vipdoc" / "xinzeng" / "sh" / "lday"
SZ_XINZENG = TDX_ROOT / "vipdoc" / "xinzeng" / "sz" / "lday"

LOOKBACK_DAYS = 60; TREND_EMA_FAST = 10; TREND_EMA_SLOW = 30
CANDLE_BODY_MAX_PCT = 10.0; CANDLE_RANGE_MAX_PCT = 10.0
CANDLE_BODY_AVG_MAX_PCT = 3.5; BULLISH_MIN_RATIO = 0.50
VOL_MA_SHORT = 5; VOL_MA_LONG = 20; VOL_INCREASE_DAYS = 15
STACKED_VOL_MIN_DAYS = 2; STACKED_VOL_RATIO = 1.2
CAPITAL_DAYS = 3; GAIN_MAX_20D = 30

def run_hub(cmd): 
    r = subprocess.run([sys.executable, str(HUB_SCRIPT)] + cmd, capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
    try: return json.loads(r.stdout.strip())
    except: return {"error": "parse fail"}

def symbol_to_code(s): return s.replace(".SH","").replace(".SZ","").replace(".BJ","")
def normalize_symbol(s):
    s = s.strip().upper()
    if "." in s: return s
    if s.startswith("920") or s.startswith("4") or s.startswith("8"): return s+".BJ"
    if s.startswith("6") or s.startswith("9"): return s+".SH"
    if s.startswith("0") or s.startswith("3") or s.startswith("2"): return s+".SZ"
    return s+".SZ"

def read_kline(symbol, days=120):
    """Read daily K-line data. For historical analysis (>120), reads full file."""
    if days > 120:
        # Direct read for full history (end_date filter will trim)
        import struct
        code = symbol_to_code(normalize_symbol(symbol))
        for mkt in ['sz', 'sh']:
            path = TDX_ROOT / 'vipdoc' / mkt / 'lday' / f'{mkt}{code}.day'
            if path.exists():
                records = []
                data = path.read_bytes()
                for i in range(0, len(data), 32):
                    rec = data[i:i+32]
                    if len(rec) < 32: break
                    dt = struct.unpack('<I', rec[:4])[0]
                    o = struct.unpack('<I', rec[4:8])[0] / 100.0
                    h = struct.unpack('<I', rec[8:12])[0] / 100.0
                    l = struct.unpack('<I', rec[12:16])[0] / 100.0
                    c = struct.unpack('<I', rec[16:20])[0] / 100.0
                    amt = struct.unpack('<f', rec[20:24])[0]
                    vol = struct.unpack('<I', rec[24:28])[0]
                    records.append({"date":str(dt),"open":round(o,2),"high":round(h,2),"low":round(l,2),"close":round(c,2),"amount":amt,"volume":vol})
                return records
        return []
    r = run_hub(["kline", normalize_symbol(symbol), "--limit", str(days)])
    return r.get("records", []) if r.get("ok") else []

def get_all_stock_symbols():
    s = set()
    for d in [SH_LDAY, SZ_LDAY, SH_XINZENG, SZ_XINZENG]:
        if d.exists():
            for f in d.glob("*.day"):
                code = f.stem[2:]
                mkt = f.stem[:2].upper()
                s.add(code)  # dedup by code only, first mkt wins
    return sorted(s)

def calc_ema(prices, period):
    if not prices: return []
    k = 2.0/(period+1); ema = [prices[0]]
    for p in prices[1:]: ema.append(p*k + ema[-1]*(1-k))
    return ema

def calc_sma(vals, period):
    return [sum(vals[max(0,i-period+1):i+1])/min(i+1,period) for i in range(len(vals))]

def calc_slope(vals, window=5):
    if len(vals) < window: return 0
    recent = vals[-window:]; n = len(recent)
    xm = (n-1)/2.0; ym = sum(recent)/n
    num = sum((i-xm)*(recent[i]-ym) for i in range(n))
    den = sum((i-xm)**2 for i in range(n))
    return num/den if den else 0

# ── Dimension 1: Trend ──
def check_trend_position(kline):
    if len(kline) < 35: return {"pass":False,"score":0,"reason":"insufficient data"}
    closes = [r["close"] for r in kline]; ema_slow = calc_ema(closes, TREND_EMA_SLOW)
    sl_slope = calc_slope(ema_slow[-10:], 10)
    cc, ce = closes[-1], ema_slow[-1]
    above = cc > ce; trend_up = sl_slope > 0
    pct = (cc/ce-1)*100
    passed = above and trend_up and pct < 15
    score = min(10, max(0, pct)) if passed else 0
    return {"pass":passed,"close":round(cc,2),"trend_ema":round(ce,2),"above_trend":above,"trend_up":trend_up,"percent_above":round(pct,2),"slope":round(sl_slope,4),"score":score}

# ── Dimension 2-3: Candle ──
def analyze_candle_pattern(kline, lookback=30):
    if len(kline) < lookback: return {"pass":False,"score":0,"reason":"insufficient data"}
    recent = kline[-lookback:]
    bull = sum(1 for r in recent if r["close"] > r["open"])
    bodies = [abs(r["close"]-r["open"])/r["open"]*100 for r in recent]
    ranges = [(r["high"]-r["low"])/r["open"]*100 for r in recent]
    ratio = bull/len(recent); avg_body = sum(bodies)/len(bodies)
    max_body = max(bodies); max_range = max(ranges)
    cs = [r["close"] for r in recent]
    total_gain = (cs[-1]/cs[0]-1)*100
    no_large = max_body < CANDLE_BODY_MAX_PCT and max_range < CANDLE_RANGE_MAX_PCT
    small = avg_body < CANDLE_BODY_AVG_MAX_PCT
    more_bull = ratio >= BULLISH_MIN_RATIO
    slow_push = 0 < total_gain < GAIN_MAX_20D
    passed = no_large and small and more_bull and slow_push
    score = (3 if no_large else 0)+(3 if small else 0)+(3 if more_bull else 0)+(3 if slow_push else 0)
    return {"pass":passed,"bullish_ratio":round(ratio,2),"avg_body_pct":round(avg_body,2),"max_body_pct":round(max_body,2),"avg_range_pct":round(sum(ranges)/len(ranges),2),"max_range_pct":round(max_range,2),"total_gain_20d":round(total_gain,2),"no_large_candle":no_large,"small_candles":small,"more_bullish":more_bull,"slow_push":slow_push,"score":score}

# ── Dimension 4: Volume ──
def analyze_volume(kline):
    if len(kline) < VOL_MA_LONG+STACKED_VOL_MIN_DAYS: return {"pass":False,"score":0,"reason":"insufficient data"}
    vols = [r["volume"] for r in kline]
    sma5 = calc_sma(vols, VOL_MA_SHORT); sma20 = calc_sma(vols, VOL_MA_LONG)
    expanding = sma5[-1] > sma20[-1]*1.0; vol_ratio = sma5[-1]/sma20[-1] if sma20[-1] > 0 else 0
    recent_vol = vols[-VOL_INCREASE_DAYS:]; vol_slope = calc_slope(recent_vol, 5)
    stacked = 0; max_stacked = 0
    for v in vols[-VOL_INCREASE_DAYS:]:
        if v > sma20[-1]*STACKED_VOL_RATIO: stacked += 1; max_stacked = max(max_stacked, stacked)
        else: stacked = 0
    has_stacked = max_stacked >= STACKED_VOL_MIN_DAYS
    moderate = 1.0 < vol_ratio < 2.5
    passed = expanding and has_stacked and moderate
    score = (3 if expanding else 0)+(2 if vol_slope >= 0 else 0)+(3 if has_stacked else 0)+(2 if moderate else 0)
    return {"pass":passed,"vol_ratio":round(vol_ratio,2),"vol_slope":round(vol_slope,4),"max_stacked_days":max_stacked,"volume_expanding":expanding,"has_stacked":has_stacked,"moderate_volume":moderate,"score":score}

# ── Dimension 5: Money Flow ──
def analyze_money_flow(kline):
    if len(kline) < 15: return {"pass":False,"score":0,"reason":"insufficient data"}
    mfs = [(r["close"]-r["open"])/r["open"]*r["volume"] if r["open"] > 0 else 0 for r in kline]
    df5 = [sum(mfs[i-4:i+1]) for i in range(4, len(mfs))]
    recent_df5 = df5[-5:] if len(df5) >= 5 else df5
    rolling_pos = sum(1 for v in recent_df5 if v > 0) >= 3
    recent_mf = mfs[-CAPITAL_DAYS:]
    cumulative_pos = sum(recent_mf) > 0
    mf_slope = calc_slope(recent_df5, 3) if len(recent_df5) >= 3 else 0
    recent_10 = mfs[-10:] if len(mfs) >= 10 else mfs
    positive_days = sum(1 for mf in recent_10 if mf > 0)
    positive_ratio = positive_days / len(recent_10)
    net_10d = sum(recent_10)
    consecutive = 0
    for mf in reversed(recent_10):
        if mf > 0: consecutive += 1
        else: break
    passed = rolling_pos and cumulative_pos and positive_ratio >= 0.4
    score = (3 if rolling_pos else 0)+(3 if cumulative_pos else 0)+(2 if positive_ratio >= 0.5 else 0)+(2 if mf_slope > 0 else 0)
    return {"pass":passed,"consecutive_positive":consecutive,"positive_days_10d":positive_days,"positive_ratio":round(positive_ratio,2),"net_10d":round(net_10d,0),"rolling_positive":rolling_pos,"cumulative_positive":cumulative_pos,"mf_slope":round(mf_slope,4),"score":score}

# ── Dimension 6: Enhanced Risk Screening ──
def is_st_stock(symbol):
    st_pats = ['*ST', 'ST', 'SST', 'S*ST', 'NST', 'PT']
    r = run_hub(["kline", normalize_symbol(symbol), "--limit", "1"])
    if r.get("ok"):
        name = r.get("meta",{}).get("name","")
        if name:
            for p in st_pats:
                if name.startswith(p) or p in name[:6]:
                    return True, f"ST股 (名称: {name})"
    return False, ""

def scan_news_for_risk(symbol):
    risks = []; code = symbol_to_code(symbol)
    kws = ["立案调查","立案","减持","违规","处罚","退市风险","问询函","监管函","警示函","责令改正","暂停上市","终止上市","重大违法","强制退市"]
    dirs = [TDX_ROOT/"T0002"/d for d in ["msg_zx","msg_web","msg_jy","info_cache"]]
    for dn in dirs:
        if not dn.exists(): continue
        for f in list(dn.iterdir())[:200]:
            try:
                c = f.read_text(encoding="gbk", errors="ignore")[:5000]
                if code in c:
                    for kw in kws:
                        if kw in c:
                            idx = c.find(kw)
                            snippet = c[max(0,idx-15):idx+40].replace('\n',' ')[:70]
                            risks.append(f"负面公告({kw}): {snippet}")
                            break
            except: pass
    return risks

def risk_screening(kline, symbol=""):
    if len(kline) < 5: return {"pass":False,"reasons":["insufficient data"],"risk_count":1,"gain_20d":0}
    closes = [r["close"] for r in kline]; opens = [r["open"] for r in kline]
    highs = [r["high"] for r in kline]; lows = [r["low"] for r in kline]
    vols = [r["volume"] for r in kline]
    reasons = []; gain_20d = 0
    if len(closes) >= 20:
        gain_20d = (closes[-1]/closes[-20]-1)*100
        if gain_20d > GAIN_MAX_20D: reasons.append(f"[K线] 20日涨幅过大: {gain_20d:.1f}% > {GAIN_MAX_20D}%")
    if len(kline) >= 10:
        for bar in kline[-10:]:
            p = (bar["close"]/bar["open"]-1)*100
            if p < -7: reasons.append(f"[K线] 近期单日大跌: {p:.1f}% on {bar['date']}")
    if len(kline) >= 20:
        h20 = max(highs[-20:]); l20 = min(lows[-20:])
        r20 = (h20/l20-1)*100
        if r20 > 40: reasons.append(f"[K线] 20日波动过大: {r20:.1f}%")
    if len(closes) >= 20:
        e20 = calc_ema(closes, 20)
        if calc_slope(e20[-10:], 5) < -0.01: reasons.append("[K线] 近期持续下跌趋势")
    if len(vols) >= 20:
        v5 = sum(vols[-5:])/5; v20 = sum(vols[-20:])/20
        if v20 > 0 and v5/v20 < 0.5: reasons.append(f"[K线] 成交量严重萎缩: {v5/v20:.2f}")
    for i in range(1, min(20, len(kline))):
        idx = len(kline)-20+i
        if opens[idx] < closes[idx-1]*0.93 and closes[idx] < opens[idx]*0.95:
            reasons.append(f"[事件] 疑似利空跳空: {kline[idx]['date']} 跳空{(1-opens[idx]/closes[idx-1])*100:.1f}%")
            break
    if len(vols) >= 20:
        av = sum(vols[-20:])/20
        for i in range(len(kline)-5, len(kline)):
            if vols[i] > av*2.5 and closes[i] < opens[i] and (i==0 or closes[i] < closes[i-1]):
                reasons.append(f"[事件] 放量下跌: {kline[i]['date']}")
                break
    if symbol:
        is_st, st_reason = is_st_stock(symbol)
        if is_st: reasons.append(f"[基本面] {st_reason}")
        for nr in scan_news_for_risk(symbol)[:3]: reasons.append(f"[公告] {nr}")
    if len(closes) >= 10:
        for i in range(5, len(closes)):
            d5 = (closes[i-5]/closes[i]-1)*100
            if d5 > 25 and (len(closes)-i) < 30: reasons.append(f"[财务] 近期利空(5日暴跌{d5:.1f}%): {closes[i-5]:.2f}->{closes[i]:.2f}"); break
    # 9. 财务代理: 120日内高点腰斩且未恢复 (疑似基本面恶化)
    if len(closes) >= 120:
        h120 = max(closes[-120:])
        dd = (h120/closes[-1]-1)*100
        # Only flag if drawdown >50% AND close is still below 120d mid-point (not recovering)
        mid120 = (h120 + min(closes[-120:])) / 2
        if dd > 50 and closes[-1] < mid120:
            reasons.append(f"[财务] 高点腰斩未恢复(dd:{dd:.0f}%): {h120:.2f}->{closes[-1]:.2f}")
    passed = len(reasons) == 0
    return {"pass":passed,"reasons":reasons,"risk_count":len(reasons),"gain_20d":round(gain_20d,2)}

# ── Composite Analysis ──
def full_analysis(symbol, end_date=None):
    # Read all bars when end_date is in the past (need full history for historical analysis)
    kline = read_kline(symbol, 120 if not end_date else 99999)
    if end_date:
        ds = end_date.replace("-","")
        kline = [r for r in kline if r["date"] < ds]
    if len(kline) < 20: return {"symbol":symbol,"pass":False,"reason":"insufficient data","data_count":len(kline)}
    cb_lb = min(30, len(kline))
    trend = check_trend_position(kline)
    candle = analyze_candle_pattern(kline, cb_lb)
    volume = analyze_volume(kline)
    money = analyze_money_flow(kline)
    risk = risk_screening(kline, symbol)
    total_score = trend.get("score",0)+candle.get("score",0)+volume.get("score",0)+money.get("score",0)
    hard_pass = trend.get("pass",False) and risk.get("pass",False)
    all_pass = hard_pass and total_score >= 25
    return {"symbol":symbol,"pass":all_pass,"score":total_score,"score_pct":round(total_score/42*100,1),"trend":trend,"candle":candle,"volume":volume,"money":money,"risk":risk,"data_count":len(kline),"latest_date":kline[-1]["date"] if kline else None,"pass_details":{"trend":trend.get("pass",False),"candle":candle.get("pass",False),"volume":volume.get("pass",False),"money":money.get("pass",False),"risk":risk.get("pass",False)}}

# ── TQ Verification ──
def check_tq_formulas(symbol):
    code = normalize_symbol(symbol)
    results = {}
    def required_value(data, field):
        values = data.get(field)
        if not values:
            raise KeyError(field)
        return values[0]
    try:
        r = run_hub(["formula","大牛线4.0",code,"--count","1"])
        if r.get("ok"):
            data = r.get("result",{}).get(code.upper(),{})
            results["daniu"] = {"main_trend":required_value(data,"主趋势线"),"signal":required_value(data,"OUTPUT28")}
    except Exception as e: results["daniu"] = {"error":"missing_or_failed", "detail": str(e)}
    try:
        r = run_hub(["formula","游资资金监控",code,"--count","1"])
        if r.get("ok"):
            data = r.get("result",{}).get(code.upper(),{})
            results["capital"] = {"buy_intent":required_value(data,"买方意向")}
    except Exception as e: results["capital"] = {"error":"missing_or_failed", "detail": str(e)}
    return results

# ── CLI ──
def cmd_single(args):
    symbol = normalize_symbol(args.symbol); code = symbol_to_code(symbol)
    print(f"\n{'='*70}\n  首板前选股分析: {code}")
    if args.end_date: print(f"  截止日期: {args.end_date}")
    print(f"{'='*70}\n")
    result = full_analysis(symbol, args.end_date)
    if result.get("reason"): print(f"✗ {result['reason']}"); return
    print(f"日期: {result['data_count']}K线, 最新: {result['latest_date']}")
    print(f"结果: {'✅ 通过' if result['pass'] else '✗ 未通过'}")
    print(f"评分: {result['score']}/42 ({result['score_pct']}%)\n")
    for dim_name, key, fields in [
        ("趋势位置","trend",["close","trend_ema","above_trend","trend_up","percent_above"]),
        ("K线形态","candle",["bullish_ratio","avg_body_pct","max_body_pct","no_large_candle","small_candles","more_bullish","slow_push"]),
        ("成交量","volume",["vol_ratio","max_stacked_days","volume_expanding","has_stacked","moderate_volume"]),
        ("资金流","money",["consecutive_positive","positive_days_10d","net_10d","rolling_positive","cumulative_positive"]),
        ("风险扫描","risk",["risk_count","gain_20d"]),
    ]:
        data = result.get(key,{})
        status = "✅" if data.get("pass",False) else "✗"
        print(f"  [{status}] {dim_name} (得分: {data.get('score',0)})")
        for fld in fields:
            if fld not in data:
                raise RuntimeError(f"missing required analysis field: {key}.{fld}")
            print(f"      {fld}: {data[fld]}")
        for r in data.get("reasons",[]):
            print(f"      ⚠ {r}")
        print()
    if not args.skip_tq:
        print("  验证TQ公式...", end="", flush=True)
        tq = check_tq_formulas(symbol)
        print(" 完成")
        if tq.get("daniu"): print(f"  TQ 大牛线: {tq['daniu']}")
        if tq.get("capital"): print(f"  TQ 游资资金: {tq['capital']}")
    print(f"\n{'='*70}\n")

def cmd_backtest(args):
    stocks = [s.strip() for s in args.stocks.split(",")]
    print(f"\n回测日期: {args.date}\n")
    results = []
    for symbol in stocks:
        code = symbol_to_code(symbol)
        print(f"  检查 {code}...", end=" ", flush=True)
        result = full_analysis(normalize_symbol(symbol), args.date)
        status = "✅" if result.get("pass") else "✗"
        score = result.get("score",0)
        risk = result.get("risk",{})
        risk_info = f", 风险{risk.get('risk_count',0)}项" if risk.get("risk_count",0) > 0 else ""
        print(f"{status} (评分: {score}/42{risk_info})")
        details = result.get("pass_details",{})
        flags = [k for k,v in details.items() if not v]
        if flags: print(f"      未通过: {', '.join(flags)}")
        for r in risk.get("reasons",[]): print(f"      ⚠ {r}")
        results.append(result)
    passed = sum(1 for r in results if r.get("pass"))
    print(f"\n回测: {passed}/{len(results)} 通过")
    if passed < len(results):
        not_p = [r["symbol"] for r in results if not r.get("pass")]
        print(f"未通过: {', '.join(not_p)}")

def cmd_scan(args):
    print("全市场扫描...\n"); t0 = time.time()
    all_syms = get_all_stock_symbols()
    print(f"  共 {len(all_syms)} 只股票")
    if args.test: all_syms = all_syms[:100]; print(f"  (测试模式: 100只)")
    print("\n  Phase 1: 快速预筛选...")
    candidates = []; processed = 0; bt = time.time()
    for sym in all_syms:
        processed += 1
        if processed % 500 == 0:
            e = time.time()-bt; rate = processed/e if e > 0 else 0
            print(f"    已处理 {processed}/{len(all_syms)} ({rate:.0f}/s), 候选: {len(candidates)}")
        try:
            kl = read_kline(sym, 120)
            if len(kl) < 20: continue
            cl = [r["close"] for r in kl]; es = calc_ema(cl, TREND_EMA_SLOW)
            if len(es) < 2 or cl[-1] <= es[-1]: continue
            if calc_slope(es[-10:], 5) <= 0: continue
            vl = [r["volume"] for r in kl]
            if len(vl) < VOL_MA_LONG: continue
            if sum(vl[-5:])/5 <= sum(vl[-20:])/20: continue
            candidates.append(sym)
        except: continue
    print(f"  Phase 1: {len(candidates)}/{len(all_syms)} 候选 ({time.time()-t0:.1f}s)")
    print(f"\n  Phase 2: 7维度详细分析...")
    detailed = []
    for i, sym in enumerate(candidates):
        if i % 50 == 0 and i > 0: print(f"    详细分析: {i}/{len(candidates)}, 通过: {len(detailed)}")
        result = full_analysis(sym, args.date)
        if result.get("pass"): detailed.append(result)
    print(f"  Phase 2: {len(detailed)} 通过 ({time.time()-t0:.1f}s)")
    detailed.sort(key=lambda x: x.get("score",0), reverse=True)
    top = detailed[:args.top]
    print(f"\n{'='*70}\n  TOP {min(args.top, len(top))} 候选\n{'='*70}\n")
    if not top: print("  无符合条件的股票。"); return
    for i, result in enumerate(top):
        sym = result["symbol"]; code = symbol_to_code(sym)
        t = result.get("trend",{}); c = result.get("candle",{})
        v = result.get("volume",{}); m = result.get("money",{})
        r = result.get("risk",{})
        print(f"  {i+1:2d}. {code} 评分: {result['score']}/42 ({result['score_pct']}%)")
        print(f"      收盘: {t.get('close','-')} | 趋势: {t.get('percent_above','-')}% | K线: 阳{c.get('bullish_ratio','-')}/实体{c.get('avg_body_pct','-')}%")
        print(f"      量比: {v.get('vol_ratio','-')} | 堆量: {v.get('max_stacked_days','-')}天 | 资金: {m.get('consecutive_positive','-')}正天")
        if r.get("risk_count",0) > 0: print(f"      ⚠ 风险: {', '.join(r.get('reasons',[])[:2])}")
        print()
    print(f"  总耗时: {time.time()-t0:.1f}s")
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump({"scan_date":datetime.now().isoformat(),"total_stocks":len(all_syms),"phase1_candidates":len(candidates),"phase2_passed":len(detailed),"top_results":top}, f, ensure_ascii=False, indent=2)
        print(f"  结果: {args.output}")

def main():
    p = argparse.ArgumentParser(description="首板涨停前选股扫描器 v1.1")
    sp = p.add_subparsers(dest="command")
    sp_s = sp.add_parser("single", help="单股分析"); sp_s.add_argument("symbol"); sp_s.add_argument("--end-date"); sp_s.add_argument("--skip-tq", action="store_true")
    sp_b = sp.add_parser("backtest", help="回测"); sp_b.add_argument("--stocks", required=True); sp_b.add_argument("--date", required=True)
    sp_sc = sp.add_parser("scan", help="全市场扫描"); sp_sc.add_argument("--date"); sp_sc.add_argument("--top", type=int, default=20); sp_sc.add_argument("--output"); sp_sc.add_argument("--test", action="store_true")
    args = p.parse_args()
    if args.command == "single": cmd_single(args)
    elif args.command == "backtest": cmd_backtest(args)
    elif args.command == "scan": cmd_scan(args)
    else: p.print_help()

if __name__ == "__main__": main()
