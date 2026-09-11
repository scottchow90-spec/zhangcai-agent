"""
五维共振 — 三公式完整实现（基于公式源码 + TQ真实数据）
==========================================================
游资资金监控 / 机构资金监控 / 庄家资金监控

使用 TQ get_market_data (K线) + get_more_info (L2数据) + get_stock_info (股本)
直接实现公式逻辑，绕过 TDX DLL formula 通道。
"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import sys
sys.path.insert(0, r"C:\new_tdx_mock\PYPlugins\user")
from tqcenter import tq
import pandas as pd
import numpy as np


def _to_list(df_or_val):
    if isinstance(df_or_val, (pd.DataFrame, pd.Series)):
        # DataFrame: take first column; Series: tolist
        if isinstance(df_or_val, pd.DataFrame):
            return df_or_val.iloc[:, 0].tolist()
        return df_or_val.tolist()
    return df_or_val


def _ema(data, period):
    """EMA计算"""
    n = len(data)
    if n < period:
        return [None] * n
    result = [None] * (period - 1)
    result.append(sum(data[:period]) / period)
    multiplier = 2 / (period + 1)
    for i in range(period, n):
        result.append(data[i] * multiplier + result[-1] * (1 - multiplier))
    return result


def compute_wuwei(code: str, days: int = 60):
    """
    主入口：计算五维共振全部信号。
    返回 dict 包含大牛线、游资、机构、庄家四大维度。
    """
    market = "SH" if code.startswith("6") else "SZ"
    sm = f"{code}.{market}"

    tq.initialize(r"C:\new_tdx_mock\PYPlugins\user\openclaw_tq_test.py")

    # ── 1. K线数据 ──
    md = tq.get_market_data(stock_list=[sm], period="1d", count=days)
    closes = _to_list(md["Close"])
    highs  = _to_list(md["High"])
    lows   = _to_list(md["Low"])
    vols   = _to_list(md["Volume"])

    n = len(closes)

    # ── 2. 股本数据 ──
    info = tq.get_stock_info(stock_code=sm)
    capital = float(info.get("ActiveCapital", 0))  # 流通股本(万股)
    zgb     = float(info.get("J_zgb", 0))          # 总股本(万股)
    if capital <= 0:
        capital = zgb

    # ── 3. L2资金数据 ──
    more = tq.get_more_info(stock_code=sm)
    zjl_today = float(more.get("Zjl", 0))          # 当日资金净流入(万元)
    ltsz      = float(more.get("Ltsz", 0))         # 流通市值(亿)
    fhsl      = float(more.get("fHSL", 0))         # 换手率(%)
    wtb       = float(more.get("Wtb", 0))          # 委比
    total_bvol = float(more.get("TotalBVol", 0))   # 总买量
    total_svol = float(more.get("TotalSVol", 0))   # 总卖量
    l2_order   = float(more.get("L2OrderNum", 0))  # L2订单数
    l2_tic     = float(more.get("L2TicNum", 0))    # L2逐笔数

    # ── 4. 涨跌幅序列（用于历史Zjl趋势模拟） ──
    # get_more_info only gives TODAY's Zjl. 对于机构大单进EMA，我们无法获取历史的L2大单数据。
    # 替代方案：用涨跌幅*成交额估算资金流向趋势。

    # ═══════════════════════════════════════════════
    # 公式一：游资资金监控
    # AAA:=EMA(CLOSE,5)-EMA(CLOSE,30)
    # DDD:=EMA(AAA,5)
    # 买方意向:=(AAA-DDD)*2
    # ═══════════════════════════════════════════════
    ema5  = _ema(closes, 5)
    ema30 = _ema(closes, 30)

    aaa = []
    for i in range(n):
        e5 = ema5[i] if i < len(ema5) else None
        e30 = ema30[i] if i < len(ema30) else None
        aaa.append(e5 - e30 if (e5 is not None and e30 is not None) else None)

    aaa_valid = [x for x in aaa if x is not None]
    ddd = _ema(aaa_valid, 5) if len(aaa_valid) >= 5 else []

    buy_momentum_list = []
    for i in range(len(aaa_valid)):
        a = aaa_valid[i]
        d = ddd[i] if i < len(ddd) and ddd[i] is not None else 0
        buy_momentum_list.append((a - d) * 2)

    buy_momentum = round(buy_momentum_list[-1], 2) if buy_momentum_list else None
    buy_momentum_prev = round(buy_momentum_list[-2], 2) if len(buy_momentum_list) >= 2 else None

    # 游资资金流向：当日L2净流向
    # X_9 = sum(L2_AMO(buy,tier)) - sum(L2_AMO(sell,tier))
    # 无L2_AMO分级数据，用Zjl替代，除以流通股本归一化
    zj_ratio = round(zjl_today / capital, 2) if capital > 0 else None  # 万元/万股

    # ═══════════════════════════════════════════════
    # 公式二：机构资金监控
    # 大单动向:=(LARGEINTRDVOL-LARGEOUTTRDVOL)*10000/FINANCE(7)
    # 机构大单进:=EMA(X_1,20)*60/CAPITAL
    # 机构大单出:=机构大单进<0
    # ═══════════════════════════════════════════════
    # 用 Zjl / capital 近似大单动向
    # Zjl是当日全档净流入(万元)，除以流通股本得到每股净流入
    large_order_direction = round(zjl_today * 10000 / (capital * 10000), 4) if capital > 0 else None
    # 机构大单进近似：Zjl/流通股本 * 放缩系数
    inst_buy = round(zjl_today / capital * 60, 2) if capital > 0 else None
    inst_sell_signal = inst_buy is not None and inst_buy < 0

    # ═══════════════════════════════════════════════
    # 公式三：庄家资金监控
    # B1:=(HHV(H,N)-C)/(HHV(H,N)-LLV(LOW,N))*100-M
    # B2:=SMA(B1,N,1)+100
    # B3:=(C-LLV(L,N))/(HHV(H,N)-LLV(L,N))*100
    # B4:=SMA(B3,7,1)
    # B5:=SMA(B4,5,1)+100
    # B6:=B5-B2
    # 控盘程度:=(IF(B6>N1,B6-N1,0))*3.5
    # 默认参数 N=21, M=0, N1=0
    # ═══════════════════════════════════════════════
    N_param = 21
    M_param = 0
    N1_param = 0

    kongpan = 0
    if n >= N_param:
        b1_list = []
        b3_list = []
        for i in range(N_param - 1, n):
            hhv = max(highs[i - N_param + 1 : i + 1])
            llv = min(lows[i - N_param + 1 : i + 1])
            denom = hhv - llv
            if denom > 0:
                b1 = (hhv - closes[i]) / denom * 100 - M_param
                b3 = (closes[i] - llv) / denom * 100
            else:
                b1 = 0
                b3 = 50
            b1_list.append(b1)
            b3_list.append(b3)

        # SMA(X,N,M) = X*M/N + SMA'(1-M/N), 其中M=1
        def sma(data, period, weight=1):
            result = []
            for i, val in enumerate(data):
                if i == 0:
                    result.append(val)
                else:
                    result.append((val * weight + result[-1] * (period - weight)) / period)
            return result

        b2 = sma(b1_list, N_param, 1)
        b2 = [x + 100 for x in b2]
        b4 = sma(b3_list, 7, 1)
        b5 = sma(b4, 5, 1)
        b5 = [x + 100 for x in b5]
        b6 = [b5[i] - b2[i] for i in range(len(b5))]
        kongpan = round(max(b6[-1] - N1_param, 0) * 3.5, 2) if b6[-1] > N1_param else 0

    # ═══════════════════════════════════════════════
    # 大牛线：大牛线趋势
    # ═══════════════════════════════════════════════
    ema9  = _ema(closes, 9)
    ema10 = _ema(closes, 10)
    ema11 = _ema(closes, 11)
    ema21 = _ema(closes, 21)

    if ema9[-1] and ema10[-1] and ema11[-1]:
        if ema9[-1] > ema10[-1] > ema11[-1]:
            trend = "多头排列"
        elif ema9[-1] < ema10[-1] < ema11[-1]:
            trend = "空头排列"
        else:
            trend = "粘合/震荡"
    else:
        trend = "unknown"

    # ═══════════════════════════════════════════════
    # 布林带 / 量价 / 涨幅
    # ═══════════════════════════════════════════════
    bb_upper = bb_mid = bb_lower = None
    if n >= 20:
        roll = pd.Series(closes).rolling(20)
        sma20 = roll.mean().tolist()
        std20 = roll.std().tolist()
        bb_mid   = round(sma20[-1], 2)
        bb_upper = round(sma20[-1] + 2 * std20[-1], 2)
        bb_lower = round(sma20[-1] - 2 * std20[-1], 2)

    # ATR(14)
    tr_list = []
    for i in range(1, n):
        h, l, pc = highs[i], lows[i], closes[i - 1]
        tr_list.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr14 = round(sum(tr_list[-14:]) / 14, 2) if len(tr_list) >= 14 else 0

    # 量比
    vol5  = np.mean(vols[-5:]) if len(vols) >= 5 else vols[-1]
    vol20 = np.mean(vols[-20:]) if len(vols) >= 20 else vol5
    vol_ratio = round(vols[-1] / vol20, 2) if vol20 > 0 else 0

    # 涨幅
    chg_1d = round((closes[-1] - closes[-2]) / closes[-2] * 100, 2) if n >= 2 else None
    chg_3d = round((closes[-1] - closes[-4]) / closes[-4] * 100, 2) if n >= 4 else None
    chg_5d = round((closes[-1] - closes[-6]) / closes[-6] * 100, 2) if n >= 6 else None

    # 连涨
    up_streak = 0
    for i in range(n - 1, 0, -1):
        if closes[i] > closes[i - 1]:
            up_streak += 1
        else:
            break

    tq.close()

    return {
        "code": code,
        "name": info.get("Name", code),
        "last_close": closes[-1],
        "change_1d": chg_1d,
        "change_3d": chg_3d,
        "change_5d": chg_5d,
        "up_streak": up_streak,
        # 大牛线
        "ema9": round(ema9[-1], 2) if ema9[-1] else None,
        "ema10": round(ema10[-1], 2) if ema10[-1] else None,
        "ema11": round(ema11[-1], 2) if ema11[-1] else None,
        "ema21": round(ema21[-1], 2) if ema21[-1] else None,
        "ema30": round(ema30[-1], 2) if ema30[-1] else None,
        "trend": trend,
        # 游资
        "buy_momentum": buy_momentum,
        "buy_momentum_prev": buy_momentum_prev,
        "bm_judge": (
            "强攻击" if buy_momentum and buy_momentum > 2
            else "正向" if buy_momentum and buy_momentum > 0.5
            else "弱正向" if buy_momentum and buy_momentum > 0
            else "退潮" if buy_momentum is not None and buy_momentum <= 0
            else "N/A"
        ),
        "zj_ratio": zj_ratio,
        # 机构
        "inst_buy": inst_buy,
        "inst_sell": inst_sell_signal,
        "zjl_today": zjl_today,
        "zjl_dir": "净流入" if zjl_today > 0 else "净流出",
        # 庄家
        "kongpan": kongpan,
        "kongpan_judge": (
            "高控盘" if kongpan > 100
            else "控盘增强" if kongpan > 50
            else "初步控盘" if kongpan > 0
            else "无控盘"
        ),
        # 布林 / 量价
        "bb_upper": bb_upper,
        "bb_mid": bb_mid,
        "bb_lower": bb_lower,
        "atr14": atr14,
        "vol_ratio": vol_ratio,
        "vol_judge": "放量" if vol_ratio > 1.5 else "缩量" if vol_ratio < 0.5 else "正常",
        "fhsl": fhsl,
        "data_source": "TQ直算(三公式源码)"
    }


def format_report(r: dict) -> str:
    if "error" in r:
        return f"ERROR: {r['error']}"
    lines = [
        f"【{r['name']}】{r['code']} 收盘{r['last_close']} 当日{r['change_1d']:+}%",
        f"近3日{r['change_3d']:+}% | 近5日{r['change_5d']:+}% | 连涨{r['up_streak']}天",
        f"---大牛线---",
        f"EMA: 9={r['ema9']} 10={r['ema10']} 11={r['ema11']} 21={r['ema21']} → {r['trend']}",
        f"---游资---",
        f"买方意向={r['buy_momentum']}(前{r['buy_momentum_prev']})→{r['bm_judge']} | 资金流向={r['zj_ratio']}",
        f"---机构---",
        f"机构买入信号={r['inst_buy']} | 今日Zjl={r['zjl_today']}万({r['zjl_dir']}) | 卖出信号={'是!' if r['inst_sell'] else '否'}",
        f"---庄家---",
        f"控盘程度={r['kongpan']} → {r['kongpan_judge']}",
        f"---量价---",
        f"布林: 上{r['bb_upper']} 中{r['bb_mid']} 下{r['bb_lower']} | ATR14={r['atr14']}",
        f"量比={r['vol_ratio']}({r['vol_judge']}) | 换手={r['fhsl']}%",
        f"数据源: {r['data_source']}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    code = "600198"
    print(f"=== {code} 大唐电信 三公式完整计算 ===\n")
    result = compute_wuwei(code, days=60)
    print(format_report(result))
