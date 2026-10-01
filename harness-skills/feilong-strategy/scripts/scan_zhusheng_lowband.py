#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞龙在天 主升启动 + 波<25 全市场扫描
- 拉 vipdoc lday 全部股票代码
- 批量（200/批）调 飞龙在天 ZB 公式
- 过滤：主升启动触发 (OUTPUT3/4 任一 + OUTPUT5/6 任一 = 100) AND 波<25
- 输出：JSON + Markdown 报告
"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import os, sys, json, time, datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

_app_scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_data_root, resolve_tdx_root

WORKSPACE = resolve_data_root()
TDX_ROOT  = resolve_tdx_root()
TQCENTER  = TDX_ROOT / "PYPlugins" / "user" / "tqcenter.py"
TQ_INIT   = TDX_ROOT / "PYPlugins" / "user" / "tdxdata_test.py"
GS_BAK    = TDX_ROOT / "T0002" / "gs_bak"
TQ_LOCK   = WORKSPACE / "runtime" / "tdx" / "tq.lock"

TODAY = datetime.datetime.now().strftime("%Y%m%d")
OUT_DIR = WORKSPACE / "reports" / f"{TODAY}_feilong_zhusheng_lowband_scan"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RUN_JSON  = OUT_DIR / "scan_full.json"
TOP_JSON  = OUT_DIR / "matches.json"
MD_REPORT = OUT_DIR / "report.md"

FORMULA = "飞龙在天"
BATCH_SIZE = 200
WAVE_MAX = 25.0


def golden_cross_status(wave, seg):
    if wave is None or seg is None:
        return "金叉状态不可判定"
    return "金叉" if wave > seg else "未形成金叉"

def load_tq():
    os.chdir(str(TDX_ROOT))
    sys.path.insert(0, str(TDX_ROOT / "PYPlugins" / "user"))
    from tqcenter import tq
    if TQ_INIT.exists():
        tq.initialize(str(TQ_INIT))
    return tq

def list_stocks():
    out = []
    for mkt, code_range in [("sh", range(600000, 605000)), ("sz", range(0, 4000))]:
        d = TDX_ROOT / "vipdoc" / mkt / "lday"
        if not d.exists():
            continue
        for f in d.iterdir():
            n = f.stem
            if not n.startswith(mkt):
                continue
            tail = n[len(mkt):]
            if not tail.isdigit() or len(tail) != 6:
                continue
            code = int(tail)
            if mkt == "sh" and not (600000 <= code < 605000):
                continue
            if mkt == "sz" and not (0 <= code < 4000):
                continue
            # 过滤文件大小=0 或太旧
            if f.stat().st_size < 32:
                continue
            out.append(f"{code:06d}.{mkt.upper()}")
    return out

def eval_stock(tq, symbol, count=0):
    """单股评估：飞龙在天最新 N 个点"""
    try:
        r = tq.formula_process_mul_zb("飞龙在天", stock_list=[symbol], count=count, return_count=2, return_date=False, dividend_type=1)
        if not isinstance(r, dict) or str(r.get("ErrorId","0")) != "0":
            return None
        node = r.get(symbol, {})
        if not node:
            return None
        def last(d):
            if isinstance(d, list) and d: return _fnum(d[-1])
            if isinstance(d, (int,float)): return float(d)
            return None
        o3 = last(node.get("OUTPUT3"))
        o4 = last(node.get("OUTPUT4"))
        o5 = last(node.get("OUTPUT5"))
        o6 = last(node.get("OUTPUT6"))
        wave = last(node.get("波"))   # 波 - last value
        band = last(node.get("段"))   # 段 - last value
        return {
            "symbol": symbol,
            "OUTPUT3": o3, "OUTPUT4": o4, "OUTPUT5": o5, "OUTPUT6": o6,
            "波": wave, "段": band,
        }
    except Exception as e:
        return None

def _fnum(x):
    try:
        if x is None: return None
        s = str(x).replace("%","").strip()
        if not s or s.lower() in {"none","null","nan","d drawnull","drawnull"}: return None
        return float(s)
    except Exception:
        return None

def _is_on(v):
    """判断单个 OUTPUT 是否触发。TQ 输出 1.00 = 触发, 0.00 = 未触发, 字符串 "主升启动" 也算触发。"""
    if v is None: return False
    if isinstance(v, str): return "主升启动" in v or v.strip() not in ("", "0", "0.00", "0.0")
    try:
        return float(v) >= 0.5
    except Exception:
        return False

def is_zhusheng(s):
    """主升启动触发：飞龙在天的 OUTPUT6 = "主升启动" 字面字符串为最硬指标。
    备选判定: XS1=(OUTPUT5 或 OUTPUT6) AND XS2=(OUTPUT3 或 OUTPUT4)"""
    if not s: return False
    o6 = s.get("OUTPUT6")
    if isinstance(o6, str) and "主升启动" in o6:
        return True
    o3, o4, o5 = s["OUTPUT3"], s["OUTPUT4"], s["OUTPUT5"]
    xs1 = _is_on(o5) or _is_on(o6)
    xs2 = _is_on(o3) or _is_on(o4)
    return xs1 and xs2

def main():
    t0 = time.perf_counter()
    stocks = list_stocks()
    print(f"[A] 全市场股票池：{len(stocks)} 只（vipdoc sh+sz 过滤 size>=32B）")
    tq = load_tq()
    print(f"[B] TQ initialized. 启动批量扫描 (batch={BATCH_SIZE}, wave_max={WAVE_MAX}) ...")

    raw_results = []
    matches = []
    batch_count = (len(stocks) + BATCH_SIZE - 1) // BATCH_SIZE
    for bi in range(batch_count):
        batch = stocks[bi*BATCH_SIZE:(bi+1)*BATCH_SIZE]
        # TQ 接 stock_list 参数
        try:
            r = tq.formula_process_mul_zb("飞龙在天", stock_list=batch, count=0, return_count=2, return_date=False, dividend_type=1)
        except Exception as e:
            print(f"  [batch {bi+1}/{batch_count}] 批次失败: {e}")
            continue
        if not isinstance(r, dict) or str(r.get("ErrorId","0")) != "0":
            print(f"  [batch {bi+1}/{batch_count}] 批次非PASS: {r.get('ErrorId','?')}")
            continue
        for sym in batch:
            node = r.get(sym, {})
            if not node: continue
            def last(d):
                if isinstance(d, list) and d:
                    v = d[-1]
                    # 主升启动 字面字符串保留原始
                    if isinstance(v, str) and "主升启动" in v:
                        return v
                    return _fnum(v)
                if isinstance(d, (int,float)): return float(d)
                if isinstance(d, str) and "主升启动" in d:
                    return d
                return None
            o3 = last(node.get("OUTPUT3"))
            o4 = last(node.get("OUTPUT4"))
            o5 = last(node.get("OUTPUT5"))
            o6 = last(node.get("OUTPUT6"))
            wave = last(node.get("波"))
            band = last(node.get("段"))
            rec = {"symbol": sym, "OUTPUT3":o3, "OUTPUT4":o4, "OUTPUT5":o5, "OUTPUT6":o6, "波":wave, "段":band}
            raw_results.append(rec)
            if is_zhusheng(rec) and wave is not None and isinstance(wave,(int,float)) and wave < WAVE_MAX:
                matches.append(rec)
        if (bi+1) % 5 == 0 or bi+1 == batch_count:
            print(f"  [batch {bi+1}/{batch_count}] 处理 {len(raw_results)}/{len(stocks)} | matches={len(matches)}")
    tq.close()

    # 排序：按 波 升序
    matches.sort(key=lambda m: m["波"] if m["波"] is not None else 999)
    raw_results.sort(key=lambda m: m["symbol"])

    # 写 JSON
    out = {
        "skill": "feilong-strategy 主升启动 + 波<25 全市场扫描",
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "formula": FORMULA,
        "tq_formula": "飞龙在天",
        "data_source": "C:\\new_tdx_mock (TDX local + TQ)",
        "wave_max": WAVE_MAX,
        "batch_size": BATCH_SIZE,
        "pool_size": len(stocks),
        "scanned": len(raw_results),
        "matches_count": len(matches),
        "matches": matches,
        "raw_results_count": len(raw_results),
        "elapsed_seconds": round(time.perf_counter()-t0, 2),
    }
    RUN_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    TOP_JSON.write_text(json.dumps({"matches": matches, "summary": {"count": len(matches)}}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown
    md = ["# 飞龙在天 主升启动 + 波段<25 扫描报告", ""]
    md.append(f"- 扫描时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"- 公式: `{FORMULA}` (T-Q 内部名: `飞龙在天`)")
    md.append(f"- 数据源: `C:\\new_tdx_mock` (TDX local + tqcenter)")
    md.append(f"- 股票池: 全市场 {len(stocks)} 只（vipdoc sh+sz，过滤 size>=32B）")
    md.append(f"- 实际扫描: {len(raw_results)} 只")
    md.append(f"- 匹配数: **{len(matches)}**")
    md.append(f"- 过滤条件: 主升启动触发 (XS1 AND XS2) AND 波 < {WAVE_MAX}")
    md.append(f"- 耗时: {time.perf_counter()-t0:.1f}s")
    md.append("")
    md.append("## 主升启动判定逻辑（实际 TQ 输出）")
    md.append("- 最硬指标：`OUTPUT6` 等于字面字符串 `\"主升启动\"`")
    md.append("- 备选：XS1=(OUTPUT5 或 OUTPUT6 任一触发) AND XS2=(OUTPUT3 或 OUTPUT4 任一触发)")
    md.append("- 触发数值：TQ 输出 1.00 = 触发, 0.00 = 未触发（非 100）")
    md.append("")
    if matches:
        md.append("## 命中清单（按 波 升序）")
        md.append("")
        md.append("| # | 代码 | 名称状态 | OUTPUT3 | OUTPUT4 | OUTPUT5 | OUTPUT6 | 波 | 段 | 金叉状态 |")
        md.append("|---|---|---|---|---|---|---|---|---|---|")
        for i, m in enumerate(matches, 1):
            o6_disp = m['OUTPUT6'] if isinstance(m['OUTPUT6'], str) else m['OUTPUT6']
            name_state = "本地源未提供简称"
            md.append(f"| {i} | {m['symbol']} | {name_state} | {m['OUTPUT3']} | {m['OUTPUT4']} | {m['OUTPUT5']} | {o6_disp} | {m['波']} | {m['段']} | {golden_cross_status(m['波'], m['段'])} |")
    else:
        md.append("## ⚠ 无命中（0 只）")
        md.append("")
        md.append("可能原因：")
        md.append("- 今日主升启动信号为共振条件（XS1 AND XS2），同时满足极难")
        md.append("- 波段<25 限制太严，候选本身稀缺")
        md.append("- 飞龙在天公式依赖多条件叠加（均线+量价+涨停+箱体），可能 0 命中即真实结果")
    md.append("")
    md.append("## 引用文件")
    md.append(f"- 全量结果: `{RUN_JSON}`")
    md.append(f"- 仅命中: `{TOP_JSON}`")
    md.append("- 公式源: `references/formulas/飞龙在天.tdx.txt`")
    MD_REPORT.write_text("\n".join(md), encoding="utf-8")

    print()
    print("="*70)
    print(f"扫描完成。 匹配 {len(matches)} 只（波<{WAVE_MAX} & 主升启动触发）")
    print(f"耗时: {time.perf_counter()-t0:.1f}s")
    print(f"报告: {MD_REPORT}")
    print(f"全量JSON: {RUN_JSON}")
    if matches:
        print()
        print("命中清单:")
        for m in matches:
            print(f"  {m['symbol']}  波={m['波']}  段={m['段']}  OUTPUT3/4/5/6={m['OUTPUT3']}/{m['OUTPUT4']}/{m['OUTPUT5']}/{m['OUTPUT6']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
