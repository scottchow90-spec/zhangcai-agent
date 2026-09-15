#!/usr/bin/env python3
"""
大牛线4.0 分析技能模块（成功路径固化）
========================================
一次写入，反复调用。禁止每次任务写新脚本。

TQ连接 → 数据采集 → 16子系统计算 → 报告输出

用法:
    from daniuxian_analysis import DaniuxianAnalyzer
    analyzer = DaniuxianAnalyzer('301372')
    data = analyzer.collect_all()          # 采集全部数据
    report = analyzer.analyze_all(data)     # 16子系统分析
    analyzer.print_report(report)           # 输出报告
    analyzer.save_report(report, 'output.txt')  # 保存文件
"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import sys, json, struct, math, os, re
from datetime import datetime
from pathlib import Path


def resolve_quote_fields(records: list[dict], snapshot: dict, bar_meta: dict) -> dict:
    """Use the canonical analysis bars for OHLCV; snapshot fields are ancillary only."""
    if len(records) < 2:
        raise RuntimeError('至少需要两条日线才能确定当前行情与昨收')
    current = records[-1]
    previous = records[-2]
    close_value = float(current['C'])
    open_value = float(current['O'])
    high_value = float(current['H'])
    low_value = float(current['L'])
    volume_value = int(current['V'])
    amount_raw = float(current.get('A') or 0.0)

    try:
        snapshot_now = float(snapshot.get('Now') or 0.0)
        snapshot_matches = (
            snapshot_now > 0
            and abs(snapshot_now - close_value) <= max(0.02, abs(close_value) * 0.00001)
        )
    except (TypeError, ValueError):
        snapshot_matches = False

    amount_value = amount_raw / 10000.0 if amount_raw > 0 else (
        float(snapshot.get('Amount') or 0.0) if snapshot_matches else 0.0
    )
    average_value = (
        float(snapshot.get('Average') or close_value) if snapshot_matches else close_value
    )
    inside_value = int(snapshot.get('Inside') or 0) if snapshot_matches else 0
    outside_value = int(snapshot.get('Outside') or 0) if snapshot_matches else 0
    return {
        'close': close_value,
        'open': open_value,
        'high': high_value,
        'low': low_value,
        'last_close': float(previous['C']),
        'volume': volume_value,
        'amount': amount_value,
        'average': average_value,
        'inside': inside_value,
        'outside': outside_value,
        'source': str(bar_meta.get('bar_source', 'unknown')),
    }


class DaniuxianAnalyzer:
    """大牛线4.0 分析器 — 固化成功路径"""

    # 大牛线4.0在本机TQ中的实际可调用注册名，与源码/显示名不同。
    FORMULA_RUNTIME_NAME = '大牛线撑压版'
    INDEX_SYMBOLS = {'000001.SH', '999999.SH'}

    # === 16子系统定义（唯一真相源） ===
    SUBSYSTEMS = [
        (1,  '主趋势线',     'EMA(EMA(C,10),10)',              '主趋势线',      'TQ'),
        (2,  'EMA均线分层',   'EMA5/10/20 + EMA173/193/213',    'EMA9,EMA10,EMA11','TQ'),
        (3,  'K线颜色信号',   'EMA5>EMA20=红K / < =绿K',        '内置渲染',       '手动'),
        (4,  '流通市值',      'FINANCE(40)/1e8',                '流通市值',       'TQ'),
        (5,  'DX动量指标',    '100*EMA(EMA(MTM,6),6)/EMA(EMA(ABS(MTM),6),6)', '内置','手动'),
        (6,  '参与与离场信号', '短线力量低位转强=参与提醒 / 高位转弱=离场提醒', '内置主图', '手动'),
        (7,  '控盘程度',      '(VAW1-REF)/REF*1000, VAW1=EMA(EMA(C,13),13)', '内置','手动'),
        (8,  '财神短线',      '(EMA(C,8)-EMA(C,21))*50 / EMA(财,3)', '内置',     '手动'),
        (9,  '庄进/庄出',     'OUTPUT4(庄进) + OUTPUT6(庄出)',   'OUTPUT4,OUTPUT6','TQ'),
        (10, '妖股识别',      '涨停+平台突破+量能放大',          '妖股标记',       'TQ'),
        (11, '龙头参与区',     '涨停缩量=第一参与区 / 涨幅大于百分之七且缩量=第二参与区', '内置主图', '手动'),
        (12, '龙回头',        '13日涨停+CP跌破震仓线',           'OUTPUT5',       'TQ'),
        (13, '点火信号',      'CROSS(EMA3,EMA21)',               'OUTPUT9',       'TQ'),
        (14, '起爆/题材共振', 'KDJ金叉+涨停',                    'OUTPUT3+起爆1',  'TQ'),
        (15, 'BOLL+多重均线', 'BOLL(20,2)+MA5/10/20/30/54/60/120','内置主图',     '手动'),
        (16, '核心黄金分割撑压', '大牛线撑压版核心黄金分割支撑/压力',
         '支撑一,支撑二,压力一,压力二,OUTPUT66', 'TQ'),
    ]

    # TDX 路径常量
    TDX_ROOT = r'C:\new_tdx_mock'
    TQCENTER_PATH = r'C:\new_tdx_mock\PYPlugins\user'
    TQ_INIT_PATH = r'C:\new_tdx_mock\PYPlugins\user\tdxdata_test.py'

    def __init__(self, stock_code: str):
        self._configure_symbol(stock_code)
        self._tq = None
        self._connected = False
        self._connect_tq()

    def _configure_symbol(self, stock_code: str):
        raw = str(stock_code).strip().upper()
        match = re.fullmatch(r'(\d{6})(?:\.(SH|SZ|BJ))?', raw)
        if not match:
            raise ValueError(f'invalid_stock_code:{stock_code}')
        code, market = match.groups()
        if not market:
            market = 'SH' if code.startswith(('5', '6', '9')) else (
                'BJ' if code.startswith(('4', '8')) else 'SZ'
            )
        self.code = code
        self.market = market
        self.symbol = f'{code}.{market}'
        self.is_index = (
            self.symbol in self.INDEX_SYMBOLS
            or (market == 'SH' and code.startswith('000'))
            or (market == 'SZ' and code.startswith('399'))
        )

    def _connect_tq(self):
        """TQ连接 — 固化正确路径"""
        if 'tqcenter' not in sys.path[0]:
            sys.path.insert(0, self.TQCENTER_PATH)
        # 确保sys.argv正确
        if '--run_tdx' not in sys.argv:
            sys.argv = ['tqcenter', '--run_tdx', '0']

        # 清理旧模块重新加载
        for m in list(sys.modules.keys()):
            if 'tqcenter' in m:
                del sys.modules[m]

        from tqcenter import tq
        self._tq = tq
        tq.initialize(self.TQ_INIT_PATH)
        self._connected = True

    def _ensure_connected(self):
        if not self._connected:
            self._connect_tq()

    def close(self):
        if self._tq:
            try:
                self._tq.close()
            except:
                pass
        self._connected = False

    # ===== 数据采集 =====
    def collect_all(self) -> dict:
        """采集全部数据：快照+基本面+TQ公式+日线历史"""
        self._ensure_connected()
        tq = self._tq

        sz_code = self.symbol

        # 1. 实时快照
        snap = tq.get_market_snapshot(sz_code)

        # 2. 基本面
        info = tq.get_stock_info(sz_code)

        # 3. 大牛线公式
        # The formula contains EMA173/193/213 and MA120; 60 bars produces
        # materially under-warmed long averages in the TQ runtime.
        tq.formula_set_data_info(sz_code, count=600, dividend_type=1)
        dnx = tq.formula_zb(self.FORMULA_RUNTIME_NAME, formula_arg=self.code)
        if not isinstance(dnx, dict) or not dnx.get('Value'):
            raise RuntimeError(
                f'大牛线4.0运行时公式调用失败: runtime_call={self.FORMULA_RUNTIME_NAME} result={dnx}'
            )

        # 4. 庄家资金监控是保留项；本机 TQ 未注册时不能阻断大牛线主流程。
        tq.formula_set_data_info(sz_code, count=5, dividend_type=1)
        try:
            zjj = tq.formula_zb('庄家资金监控', formula_arg=self.code)
        except Exception as exc:
            zjj = {'Value': {}, 'reserved': True, 'ok': False, 'error': str(exc)}

        # 5. 日线历史
        prefix = self.market.lower()
        lday_path = os.path.join(self.TDX_ROOT, 'vipdoc', prefix, 'lday', f'{prefix}{self.code}.day')
        records = self._read_day_file(lday_path)
        verified_trade_date = os.environ.get('BIG_BULL_VERIFIED_TRADE_DATE', '').strip()
        records, bar_meta = self._merge_verified_snapshot_bar(records, snap, verified_trade_date)

        return {
            'snap': snap,
            'info': info,
            'dnx': dnx,
            'zjj': zjj,
            'records': records,
            'formula_runtime_name': self.FORMULA_RUNTIME_NAME,
            'is_index': self.is_index,
            'bar_meta': bar_meta,
        }

    def _read_day_file(self, path):
        records = []
        if not os.path.exists(path):
            return records
        with open(path, 'rb') as f:
            data = f.read()
        for i in range(0, len(data), 32):
            if i + 32 > len(data): break
            rec = data[i:i+32]
            date_int = struct.unpack('I', rec[0:4])[0]
            records.append({
                'date': f'{date_int//10000}-{(date_int%10000)//100:02d}-{date_int%100:02d}',
                'O': struct.unpack('I', rec[4:8])[0]/100,
                'H': struct.unpack('I', rec[8:12])[0]/100,
                'L': struct.unpack('I', rec[12:16])[0]/100,
                'C': struct.unpack('I', rec[16:20])[0]/100,
                'A': struct.unpack('f', rec[20:24])[0],
                'V': struct.unpack('I', rec[24:28])[0],
            })
        return records

    @staticmethod
    def _normalize_verified_trade_date(value):
        """Normalize the verified trade date to YYYY-MM-DD."""
        raw_value = str(value or '').strip()
        if not raw_value:
            return ''
        for date_format in ('%Y%m%d', '%Y-%m-%d'):
            try:
                return datetime.strptime(raw_value, date_format).strftime('%Y-%m-%d')
            except ValueError:
                continue
        raise RuntimeError(
            'BIG_BULL_VERIFIED_TRADE_DATE must be YYYYMMDD or YYYY-MM-DD'
        )

    @staticmethod
    def _merge_verified_snapshot_bar(records, snap, verified_trade_date):
        """Merge a current snapshot only when its trade date was independently verified."""
        if not records:
            return records, {
                'bar_source': 'missing_local_history',
                'local_last_date': '',
                'analysis_trade_date': '',
                'snapshot_fetched_at': datetime.now().isoformat(timespec='seconds'),
                'persisted_records': 0,
            }

        fetched_at = datetime.now()
        local_last_date = records[-1]['date']
        meta = {
            'bar_source': 'persisted_tdx_day_only',
            'local_last_date': local_last_date,
            'analysis_trade_date': local_last_date,
            'snapshot_fetched_at': fetched_at.isoformat(timespec='seconds'),
            'persisted_records': len(records),
            'snapshot_date_verified': False,
        }
        if not verified_trade_date:
            return records, meta

        verified_trade_date = DaniuxianAnalyzer._normalize_verified_trade_date(
            verified_trade_date
        )
        trade_day = datetime.strptime(verified_trade_date, '%Y-%m-%d').date()
        if trade_day > fetched_at.date():
            raise RuntimeError(f'验证交易日晚于本机日期: {trade_day} > {fetched_at.date()}')
        if verified_trade_date < local_last_date:
            raise RuntimeError(
                f'验证交易日早于本地最新日线: verified={verified_trade_date} local={local_last_date}'
            )

        try:
            current_bar = {
                'date': verified_trade_date,
                'O': float(snap['Open']),
                'H': float(snap['Max']),
                'L': float(snap['Min']),
                'C': float(snap['Now']),
                'V': int(snap['Volume']),
                'synthetic': True,
            }
            previous_close = float(snap['LastClose'])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f'TQ快照字段不完整，不能合成当日日线: {snap}') from exc
        if current_bar['L'] <= 0 or current_bar['H'] < current_bar['L']:
            raise RuntimeError(f'TQ快照高低价非法: {current_bar}')
        if current_bar['H'] < max(current_bar['O'], current_bar['C']):
            raise RuntimeError(f'TQ快照最高价小于开盘或最新价: {current_bar}')
        if current_bar['L'] > min(current_bar['O'], current_bar['C']):
            raise RuntimeError(f'TQ快照最低价大于开盘或最新价: {current_bar}')
        if current_bar['V'] <= 0:
            raise RuntimeError(f'TQ快照成交量非法: {current_bar["V"]}')

        merged = list(records)
        reference_close = records[-1]['C'] if verified_trade_date > local_last_date else (
            records[-2]['C'] if len(records) > 1 else previous_close
        )
        close_tolerance = max(0.02, abs(previous_close) * 0.00001)
        if abs(reference_close - previous_close) > close_tolerance:
            raise RuntimeError(
                'TQ快照昨收与本地前一日收盘不一致，禁止混合数据: '
                f'snapshot={previous_close:.2f} local={reference_close:.2f}'
            )
        if verified_trade_date == local_last_date:
            merged[-1] = current_bar
            bar_source = 'verified_tq_snapshot_replace'
        else:
            merged.append(current_bar)
            bar_source = 'verified_tq_snapshot_append'
        meta.update({
            'bar_source': bar_source,
            'analysis_trade_date': verified_trade_date,
            'snapshot_date_verified': True,
        })
        return merged, meta

    # ===== 数学工具 =====
    @staticmethod
    def EMA(data, period):
        result, k = [data[0]], 2.0/(period+1)
        for i in range(1,len(data)): result.append(data[i]*k+result[-1]*(1-k))
        return result

    @staticmethod
    def MA(data, period):
        result = []
        for i in range(len(data)):
            if i<period-1: result.append(sum(data[:i+1])/(i+1))
            else: result.append(sum(data[i-period+1:i+1])/period)
        return result

    @staticmethod
    def SMA(data, nv, mv):
        result = [data[0]]
        for i in range(1,len(data)): result.append((data[i]*mv+result[-1]*(nv-mv))/nv)
        return result

    @staticmethod
    def STD(data, period):
        result = []
        for i in range(len(data)):
            if i<period-1: result.append(0)
            else:
                w = data[i-period+1:i+1]; m = sum(w)/period
                result.append(math.sqrt(sum((x-m)**2 for x in w)/period))
        return result

    @staticmethod
    def LLV(data, period):
        return [min(data[max(0,i-period+1):i+1]) for i in range(len(data))]

    @staticmethod
    def HHV(data, period):
        return [max(data[max(0,i-period+1):i+1]) for i in range(len(data))]

    @staticmethod
    def CROSS(a, b):
        return [a[i]>b[i] and a[i-1]<=b[i-1] if i>0 else False for i in range(len(a))]

    @staticmethod
    def COUNT(cond, period):
        return [sum(1 for j in range(max(0,i-period+1), i+1) if cond[j]) for i in range(len(cond))]

    def RSI(self, data, period):
        gains = [max(data[i]-data[i-1],0) if i>0 else 0 for i in range(len(data))]
        losses = [abs(min(data[i]-data[i-1],0)) if i>0 else 0 for i in range(len(data))]
        ag = self.SMA(gains,period,1); al = self.SMA(losses,period,1)
        return [100-100/(1+ag[i]/al[i]) if al[i]!=0 else 100 for i in range(len(data))]

    # ===== 16子系统计算 =====
    def analyze_all(self, raw: dict) -> dict:
        """16子系统完整计算"""
        snap, info, dnx, zjj, records = raw['snap'], raw['info'], raw['dnx'], raw['zjj'], raw['records']
        bar_meta = raw.get('bar_meta', {})
        if len(records) < 120:
            raise RuntimeError(f'本地日线不足120条，无法执行16子系统: code={self.code} records={len(records)}')
        v = dnx.get('Value', {})
        zjj_v = zjj.get('Value', {}) if isinstance(zjj, dict) else {}
        zjj_reserved_error = zjj.get('error') if isinstance(zjj, dict) and zjj.get('reserved') else ''
        n = len(records)
        idx = -1
        C = [r['C'] for r in records]
        H = [r['H'] for r in records]
        L = [r['L'] for r in records]
        V_arr = [r['V'] for r in records]

        # 预计算
        ema5 = self.EMA(C,5); ema10 = self.EMA(C,10); ema20 = self.EMA(C,20)
        ema3 = self.EMA(C,3); ema21 = self.EMA(C,21); ema13 = self.EMA(C,13)
        ema173 = self.EMA(C,173); ema193 = self.EMA(C,193); ema213 = self.EMA(C,213)
        main_trend_local = self.EMA(self.EMA(C,10),10)
        ma5 = self.MA(C,5); ma10 = self.MA(C,10); ma20 = self.MA(C,20)
        ma30 = self.MA(C,30); ma54 = self.MA(C,54); ma60 = self.MA(C,60); ma120 = self.MA(C,120)
        boll_ma = self.MA(C,20); boll_std = self.STD(C,20)
        UB = [boll_ma[i]+2*boll_std[i] for i in range(n)]
        LB = [boll_ma[i]-2*boll_std[i] for i in range(n)]

        # KDJ
        Nk=9
        rsv = [(C[i]-self.LLV(L,Nk)[i])/(self.HHV(H,Nk)[i]-self.LLV(L,Nk)[i])*100 if self.HHV(H,Nk)[i]!=self.LLV(L,Nk)[i] else 50 for i in range(n)]
        kdj_k = self.SMA(rsv,3,1); kdj_d = self.SMA(kdj_k,3,1)
        kdj_j = [3*kdj_k[i]-2*kdj_d[i] for i in range(n)]

        # MACD
        ema12 = self.EMA(C,12); ema26 = self.EMA(C,26)
        dif = [ema12[i]-ema26[i] for i in range(n)]
        dea = self.EMA(dif,9)
        macd_bar = [2*(dif[i]-dea[i]) for i in range(n)]

        # RSI
        rsi6 = self.RSI(C,6); rsi14 = self.RSI(C,14)

        # DX动量
        mtm_arr = [C[i]-C[i-1] if i>0 else 0 for i in range(n)]
        dx_ema6 = self.EMA(mtm_arr,6); dx_ema6b = self.EMA(dx_ema6,6)
        dx_abs6 = self.EMA([abs(m) for m in mtm_arr],6); dx_abs6b = self.EMA(dx_abs6,6)
        dx_vals = [100*dx_ema6b[i]/dx_abs6b[i] if dx_abs6b[i]!=0 else 0 for i in range(n)]

        # WR
        wr10 = [(self.HHV(H,10)[i]-C[i])/(self.HHV(H,10)[i]-self.LLV(L,10)[i])*100 if self.HHV(H,10)[i]!=self.LLV(L,10)[i] else 50 for i in range(n)]

        # 控盘
        vaw1 = self.EMA(ema13,13)
        kongpan = [(vaw1[i]-vaw1[i-1])/vaw1[i-1]*1000 if i>0 and vaw1[i-1]!=0 else 0 for i in range(n)]

        # 财神
        Pv=21
        ema8 = self.EMA(C,8)
        ema21_cai = self.EMA(C,Pv)
        cai_arr = [(ema8[i]-ema21_cai[i])*50 for i in range(n)]
        shen_arr = self.EMA(cai_arr,3)

        # CP
        max_diff = [max(C[i]-C[i-1],0) if i>0 else 0 for i in range(n)]
        abs_diff = [abs(C[i]-C[i-1]) if i>0 else 0 for i in range(n)]
        sma_max = self.SMA(max_diff,2,1); sma_abs = self.SMA(abs_diff,2,1)
        cp_vals = [sma_max[i]/sma_abs[i]*100 if sma_abs[i]!=0 else 0 for i in range(n)]

        # TQ数据；若公式接口返回空，禁止崩溃，切换到本地日线派生的新路径并在报告中保留真实可审计结果。
        def tq_seq(key: str, fallback):
            raw = v.get(key)
            if raw in (None, [], ""):
                raw = fallback
            if not isinstance(raw, list):
                raw = [raw]
            vals = []
            for item in raw:
                try:
                    vals.append(float(item))
                except Exception:
                    vals.append(0.0)
            if not vals:
                vals = [0.0]
            while len(vals) < 2:
                vals.insert(0, vals[-1])
            return vals

        def tq_text_seq(key: str, default: str = '0.00'):
            raw = v.get(key)
            if raw in (None, [], ""):
                raw = [default]
            if not isinstance(raw, list):
                raw = [raw]
            return [str(x) for x in raw] or [default]

        def tq_latest_value(key: str):
            raw_value = v.get(key)
            if isinstance(raw_value, list):
                return raw_value[-1] if raw_value else None
            return raw_value

        def tq_optional_float(key: str):
            raw_value = tq_latest_value(key)
            if raw_value is None or str(raw_value).strip().upper() in {'', 'NA', 'N/A', '--'}:
                return None
            try:
                numeric_value = float(raw_value)
            except (TypeError, ValueError):
                return None
            return numeric_value if math.isfinite(numeric_value) else None

        def tq_optional_text(key: str):
            raw_value = tq_latest_value(key)
            if raw_value is None or str(raw_value).strip().upper() in {'', 'NA', 'N/A', '--'}:
                return 'NA'
            return str(raw_value).strip()

        main_trend_tq = tq_seq('主趋势线', main_trend_local)
        main_trend = main_trend_local
        ema9_tq = tq_seq('EMA9', ema5)
        ema10_tq = tq_seq('EMA10', ema10)
        ema11_tq = tq_seq('EMA11', ema20)
        o3=tq_text_seq('OUTPUT3'); o4=tq_text_seq('OUTPUT4')
        o5=tq_text_seq('OUTPUT5'); o6=tq_text_seq('OUTPUT6'); o9=tq_text_seq('OUTPUT9')
        float_cap=tq_seq('流通市值',[0.0])[-1]
        zt_price=tq_seq('涨停价',[float(snap.get('LastClose', 0) or 0) * 1.1])[-1]
        dt_price=tq_seq('跌停价',[float(snap.get('LastClose', 0) or 0) * 0.9])[-1]
        blocks=tq_text_seq('OUTPUT47','')[-1]
        support_1=tq_optional_float('支撑一')
        support_2=tq_optional_float('支撑二')
        pressure_1=tq_optional_float('压力一')
        pressure_2=tq_optional_float('压力二')
        output66=tq_optional_text('OUTPUT66')

        # 行情字段必须与本次分析日线同源；未经日期核验的快照只可补充旁证字段。
        quote = resolve_quote_fields(records, snap, bar_meta)
        close_p = quote['close']; last_close = quote['last_close']
        open_p = quote['open']; high_p = quote['high']; low_p = quote['low']
        volume = quote['volume']; amount = quote['amount']; avg_p = quote['average']
        inside = quote['inside']; outside = quote['outside']
        valid_supports = [
            value for value in (support_1, support_2)
            if value is not None and value <= close_p
        ]
        valid_pressures = [
            value for value in (pressure_1, pressure_2)
            if value is not None and value >= close_p
        ]
        nearest_support = max(valid_supports) if valid_supports else None
        nearest_pressure = min(valid_pressures) if valid_pressures else None
        if nearest_support is not None and nearest_pressure is not None:
            support_pressure_status = '双向撑压有效'
        elif nearest_support is not None:
            support_pressure_status = '仅支撑有效'
        elif nearest_pressure is not None:
            support_pressure_status = '仅压力有效'
        else:
            support_pressure_status = '撑压不可判定'

        # 基本面
        name=info.get('Name','')
        j_zgb=float(info.get('J_zgb','0')); j_jzc=float(info.get('J_jzc','0'))
        j_mgjzc=float(info.get('J_mgjzc','0')); j_mgsy=float(info.get('J_mgsy','0'))

        # 判断
        change_pct=(close_p-last_close)/last_close*100
        avg_vol_5=sum(V_arr[-6:-1])/5 if n>=6 else 1; cb_r=volume/avg_vol_5 if avg_vol_5>0 else 1
        is_zt=close_p>=zt_price*0.999
        trend_up=main_trend[-1]>main_trend[-2]
        bullish=ema5[idx]>ema10[idx]>ema20[idx]
        jincha_kdj=kdj_k[idx]>kdj_d[idx]
        zhuangchu_tq=o6[-1] not in ('0.00','0')
        zhuangjin_tq=o4[-1] not in ('0.00','0')
        dianhuo_tq=o9[-1] not in ('0.00','0')
        jincha_tq=o3[-1] not in ('0.00','0')
        limit_up_flags = [
            bool(i > 0 and C[i - 1] * 1.1 - C[i] < 0.01)
            for i in range(n)
        ]
        zt_13d = sum(
            1 for i in range(max(0, n - 13), n) if limit_up_flags[i]
        )
        pp_45 = [
            bool(i > 0 and cp_vals[i] < 45 and cp_vals[i - 1] > 45)
            for i in range(n)
        ]
        pp_20 = [
            bool(i > 0 and cp_vals[i] < 20 and cp_vals[i - 1] > 20)
            for i in range(n)
        ]
        hh_13 = [
            any(limit_up_flags[max(0, i - 12) : i + 1])
            for i in range(n)
        ]
        lht_visible = bool(
            idx > 0
            and L[idx] > 0
            and (pp_45[idx - 1] or pp_20[idx - 1])
            and hh_13[idx]
        )
        body=abs(close_p-open_p)
        upper_shadow=high_p-max(open_p,close_p)
        lower_shadow=min(open_p,close_p)-low_p

        # 短线参与与离场信号
        dx_ma2=self.MA(dx_vals,2)
        hhv_dx2=self.HHV(dx_vals,2)[idx]; llv_dx2=self.LLV(dx_vals,2)[idx]
        hhv_dx7=self.HHV(dx_vals,7)[idx]; llv_dx7=self.LLV(dx_vals,7)[idx]
        cdx0=self.COUNT([d<0 for d in dx_vals],2)[idx]
        cdx50=self.COUNT([d>50 for d in dx_vals],2)[idx]
        buy_sig = math.isclose(llv_dx2, llv_dx7) and bool(cdx0) and self.CROSS(dx_vals,dx_ma2)[idx]
        sell_sig = math.isclose(hhv_dx2, hhv_dx7) and bool(cdx50) and self.CROSS(dx_ma2,dx_vals)[idx]
        dianhuo = self.CROSS(ema3,ema21)[idx]

        result = {
            'name': name, 'code': self.code,
            'is_index': raw.get('is_index', False),
            'formula_runtime_name': raw.get('formula_runtime_name', ''),
            'trade_date': records[-1]['date'],
            'local_last_date': bar_meta.get('local_last_date', records[-1]['date']),
            'bar_source': bar_meta.get('bar_source', 'unknown'),
            'snapshot_fetched_at': bar_meta.get('snapshot_fetched_at', ''),
            'snapshot_date_verified': bool(bar_meta.get('snapshot_date_verified', False)),
            'n_persisted_records': int(bar_meta.get('persisted_records', n)),
            'close': close_p, 'open': open_p, 'high': high_p, 'low': low_p, 'last_close': last_close,
            'volume': volume, 'amount': amount, 'avg': avg_p, 'inside': inside, 'outside': outside,
            'change_pct': change_pct, 'cb_ratio': cb_r,
            'float_cap': float_cap, 'zt_price': zt_price, 'dt_price': dt_price, 'blocks': blocks,
            'j_zgb': j_zgb, 'j_jzc': j_jzc, 'j_mgjzc': j_mgjzc, 'j_mgsy': j_mgsy,
            'n_records': n, 'zjj_v': zjj_v, 'zjj_reserved_error': zjj_reserved_error,
            # 子系统计算值
            'main_trend': main_trend[-1], 'main_trend_prev': main_trend[-2], 'trend_up': trend_up,
            'main_trend_tq': main_trend_tq[-1],
            'ema5': ema5[idx], 'ema10': ema10[idx], 'ema20': ema20[idx],
            'ema173': ema173[idx], 'ema193': ema193[idx], 'ema213': ema213[idx],
            'ema173_prev': ema173[idx-1], 'ema193_prev': ema193[idx-1], 'ema213_prev': ema213[idx-1],
            'bullish': bullish,
            'ema173_tq': ema9_tq[-1], 'ema193_tq': ema10_tq[-1], 'ema213_tq': ema11_tq[-1],
            'kline_type': '阳' if close_p>open_p else '阴', 'body': body, 'upper_shadow': upper_shadow, 'lower_shadow': lower_shadow,
            'dx': dx_vals[idx], 'dx_prev': dx_vals[idx-1], 'dx_dir': '增强' if dx_vals[idx]>dx_vals[idx-1] else '减弱',
            'sell_sig': sell_sig, 'buy_sig': buy_sig,
            'kongpan': kongpan[idx], 'kongpan_prev': kongpan[idx-1],
            'cai': cai_arr[idx], 'shen': shen_arr[idx],
            'o3': o3[-1], 'o4': o4[-1], 'o5': o5[-1], 'o6': o6[-1], 'o9': o9[-1],
            'zhuangchu': zhuangchu_tq, 'zhuangjin': zhuangjin_tq,
            'dianhuo': dianhuo, 'lht': lht_visible, 'jincha_tq': jincha_tq,
            'is_zt': is_zt, 'zt_13d': zt_13d,
            'lht_ref_pp45': pp_45[idx - 1] if idx > 0 else False,
            'lht_ref_pp20': pp_20[idx - 1] if idx > 0 else False,
            'lht_hh13': hh_13[idx],
            'kdj_k': kdj_k[idx], 'kdj_d': kdj_d[idx], 'kdj_j': kdj_j[idx], 'jincha_kdj': jincha_kdj,
            'dif': dif[idx], 'dea': dea[idx], 'macd_bar': macd_bar[idx],
            'rsi6': rsi6[idx], 'rsi14': rsi14[idx], 'wr10': wr10[idx],
            'UB': UB[idx], 'LB': LB[idx], 'boll_ma': boll_ma[idx],
            'ma5': ma5[idx], 'ma10': ma10[idx], 'ma20': ma20[idx],
            'ma30': ma30[idx], 'ma54': ma54[idx], 'ma60': ma60[idx], 'ma120': ma120[idx],
            'cp': cp_vals[idx], 'pp': cp_vals[idx]<45 and cp_vals[idx-1]>45 if idx>0 else False,
            'ema3': ema3[idx], 'ema21': ema21[idx],
            'support_1': support_1, 'support_2': support_2,
            'pressure_1': pressure_1, 'pressure_2': pressure_2,
            'output66': output66,
            'downtrend_breakout_verified': False,
            'downtrend_breakout_source': '大牛线撑压版未提供独立可计算字段',
            'nearest_support': nearest_support, 'nearest_pressure': nearest_pressure,
            'support_pressure_status': support_pressure_status,
            # 序列
            'main_trend_seq': main_trend_local,
            'main_trend_tq_seq': main_trend_tq,
            'ema9_seq': ema9_tq, 'ema10_seq': ema10_tq, 'ema11_seq': ema11_tq,
            'dx_seq': dx_vals, 'cai_seq': cai_arr, 'shen_seq': shen_arr,
            'kdj_k_seq': kdj_k, 'kdj_d_seq': kdj_d, 'kdj_j_seq': kdj_j,
            'ema3_seq': ema3, 'ema21_seq': ema21, 'ema5_seq': ema5, 'ema10_seq': ema10, 'ema20_seq': ema20,
            'records': records, 'kongpan_seq': kongpan,
        }
        result['comprehensive_assessment'] = build_comprehensive_assessment(result)
        return result

    # ===== 报告输出 =====
    def format_report(self, d: dict) -> str:
        """格式化完整报告"""
        f = d  # shorthand
        lines = []
        def p(s=""): lines.append(s)

        p("="*70)
        p(f"  大牛线撑压版 十六子系统完整分析 + 综合研判")
        p(f"  {f['name']}({f['code']}) -- {f['trade_date']}")
        p(f"  运行时公式:{f['formula_runtime_name']}  标的类型:{'指数' if f['is_index'] else '个股'}")
        p(f"  日线口径:{f['bar_source']}  本地持久日线截止:{f['local_last_date']}  快照抓取:{f['snapshot_fetched_at']}")
        p("="*70)

        # 基础行情
        p(); p("--- 基础行情 ---")
        p(f"  最新价:{f['close']:.2f}  涨跌幅:{f['change_pct']:+.2f}%  涨跌额:{f['close']-f['last_close']:+.2f}")
        p(f"  今开:{f['open']:.2f}  昨收:{f['last_close']:.2f}  最高:{f['high']:.2f}  最低:{f['low']:.2f}  均价:{f['avg']:.2f}")
        p(f"  成交量:{f['volume']}手  成交额:{f['amount']:.2f}万  内盘:{f['inside']}  外盘:{f['outside']}")
        if f['is_index']:
            p("  指数口径:流通市值、涨跌停价、个股板块不适用")
        else:
            p(f"  流通市值:{f['float_cap']:.2f}亿  涨停价:{f['zt_price']:.2f}  跌停价:{f['dt_price']:.2f}")
            p(f"  板块:{f['blocks'].strip()}")

        # 子系统1-16
        p(); p("--- 子系统1: 主趋势线 ---")
        p(f"  源码重算={f['main_trend']:.2f}  前日:{f['main_trend_prev']:.2f}  方向:{'向上' if f['trend_up'] else '向下'}")
        p(f"  TQ OUTPUT2复核={f['main_trend_tq']:.2f}")
        p(f"  价格{f['close']:.2f}在趋势线{('上' if f['close']>f['main_trend'] else '下')} {(f['close']-f['main_trend'])/f['main_trend']*100:+.1f}%")
        if f['is_index']:
            p(
                "  结论:"
                + (
                    '短周期主趋势线向上，仅说明短线修复，不代表中期偏多'
                    if f['trend_up'] else
                    '短周期主趋势线向下，短线仍承压'
                )
            )
        else:
            p(f"  结论:{'趋势向上偏多' if f['trend_up'] else '趋势向下偏空，需拐头确认反转'}")

        p(); p("--- 子系统2: EMA均线分层 ---")
        p(f"  EMA5={f['ema5']:.2f} EMA10={f['ema10']:.2f} EMA20={f['ema20']:.2f}")
        p(f"  排列:{'多头' if f['bullish'] else '交叉/空头'}  价格距EMA20:{(f['close']-f['ema20'])/f['ema20']*100:+.1f}%")
        p(f"  源码长线:EMA173={f['ema173']:.2f} EMA193={f['ema193']:.2f} EMA213={f['ema213']:.2f}")
        p(f"  TQ复核:EMA173={f['ema173_tq']:.2f} EMA193={f['ema193_tq']:.2f} EMA213={f['ema213_tq']:.2f}")
        long_ceiling = max(f['ema173'], f['ema193'], f['ema213'])
        p(f"  长线内部排序:{'EMA173>EMA193>EMA213' if f['ema173']>f['ema193']>f['ema213'] else '非顺序排列'}")
        p(f"  当前收盘站上全部中长期线:{'是' if f['close'] >= long_ceiling else '否'}  最高线={long_ceiling:.2f}")

        p(); p("--- 子系统3: K线颜色信号 ---")
        p(f"  {'红K' if f['ema5']>f['ema20'] else '绿/白K'} {f['kline_type']}线 实体:{f['body']:.2f} 上影:{f['upper_shadow']:.2f} 下影:{f['lower_shadow']:.2f}{'长支撑' if f['lower_shadow']>f['body'] else ''}")

        p(); p("--- 子系统4: 流通市值 ---")
        if f['is_index']:
            p("  不适用: 指数没有个股口径的流通市值、每股净资产、每股收益、市净率和市盈率")
        else:
            p(f"  TQ流通市值:{f['float_cap']:.2f}亿  总股本:{f['j_zgb']/10000:.2f}亿股  净资产:{f['j_jzc']/10000:.2f}亿")
            pb = f['close']/f['j_mgjzc'] if f['j_mgjzc'] else float('nan')
            pe = f['close']/f['j_mgsy'] if f['j_mgsy'] else float('nan')
            p(f"  每股净:{f['j_mgjzc']:.2f} 每股收益:{f['j_mgsy']:.2f}  市净率:{pb:.2f}  市盈率:{pe:.1f}")

        p(); p("--- 子系统5: DX动量指标 ---")
        p(f"  DX={f['dx']:.2f}  {f['dx_dir']}  区间:{'超买' if f['dx']>50 else ('多头' if f['dx']>20 else ('中性' if f['dx']>-20 else ('空头' if f['dx']>-50 else '超卖')))}")

        p(); p("--- 子系统6: 参与与离场信号 ---")
        p(f"  离场提醒:{'触发!' if f['sell_sig'] else '未触发'}  参与提醒:{'触发!' if f['buy_sig'] else '未触发'}")

        p(); p("--- 子系统7: 控盘程度 ---")
        p(f"  控盘={f['kongpan']:.4f}  前日={f['kongpan_prev']:.4f}  变化={f['kongpan']-f['kongpan_prev']:+.4f}")
        if f.get('zjj_reserved_error'):
            p(f"  TQ庄家资金监控为保留项，当前未参与阻断: {f['zjj_reserved_error']}")
        for kk in sorted(f['zjj_v'].keys()):
            arr=f['zjj_v'][kk]; lv=arr[-1] if isinstance(arr,list) and arr else arr
            p(f"  TQ庄家资金.{kk}:{lv}")

        p(); p("--- 子系统8: 财神短线 ---")
        p(f"  财={f['cai']:.4f}  神={f['shen']:.4f}  {'财>神偏多' if f['cai']>f['shen'] else '财<神偏空'}")

        p(); p("--- 子系统9: 庄进/庄出 ---")
        if f['is_index']:
            p("  不适用: 庄进/庄出为个股资金信号，不参与指数结论")
        else:
            p(f"  TQ OUTPUT4(庄进)={f['o4']}  OUTPUT6(庄出)={f['o6']}")
            p(f"  {'庄出触发!主力撤退!' if f['zhuangchu'] else '庄出未触发'}  {'庄进触发!' if f['zhuangjin'] else '庄进未触发'}")

        p(); p("--- 子系统10: 妖股识别 ---")
        p("  不适用: 妖股识别是个股专属子系统") if f['is_index'] else p(f"  涨停:{'是' if f['is_zt'] else '否'}  量比:{f['cb_ratio']:.2f}  判定:{'妖股!' if f['is_zt'] else '非妖股'}")

        p(); p("--- 子系统11: 龙头参与区 ---")
        if f['is_index']:
            p("  不适用: 龙头参与区是个股专属子系统")
        else:
            p(f"  涨幅:{f['change_pct']:+.2f}%  量比:{f['cb_ratio']:.2f}")
            p(f"  第一参与区(涨停+缩量):{'触发' if f['is_zt'] and f['cb_ratio']<1 else '未触发'}")
            p(f"  第二参与区(涨幅大于百分之七+缩量):{'触发' if f['change_pct']>=7 and f['cb_ratio']<1 else '未触发'}")

        p(); p("--- 子系统12: 龙回头 ---")
        if f['is_index']:
            p("  不适用: 龙回头是个股专属子系统；CP仅保留为技术辅助，不计入该信号")
        else:
            p(f"  图示四件套共同条件 -> {'触发!' if f['lht'] else '未触发'}")
            p(
                f"  13日涨停:{f['zt_13d']}次  "
                f"前一日跌破45:{'是' if f['lht_ref_pp45'] else '否'}  "
                f"前一日跌破20:{'是' if f['lht_ref_pp20'] else '否'}"
            )

        p(); p("--- 子系统13: 点火信号 ---")
        p(f"  源码CROSS(EMA3,EMA21) -> {'点火触发!' if f['dianhuo'] else '未触发'}")
        p(f"  EMA3={f['ema3']:.2f}  EMA21={f['ema21']:.2f}  差距:{abs(f['ema3']-f['ema21']):.2f}")

        p(); p("--- 子系统14: 起爆/题材共振 ---")
        if f['is_index']:
            p("  指数不适用个股涨停/市值/价格约束；仅保留KDJ与MACD动量观察")
        p(f"  KDJ:K={f['kdj_k']:.2f} D={f['kdj_d']:.2f} J={f['kdj_j']:.2f}  {'金叉' if f['jincha_kdj'] else '死叉'}")
        p(f"  MACD:DIF={f['dif']:.2f} DEA={f['dea']:.2f} BAR={f['macd_bar']:.2f}")
        p(f"  RSI6={f['rsi6']:.0f} RSI14={f['rsi14']:.0f}  WR10={f['wr10']:.0f}")

        p(); p("--- 子系统15: BOLL+多重均线 ---")
        p(f"  BOLL:上轨{f['UB']:.2f} 中轨{f['boll_ma']:.2f} 下轨{f['LB']:.2f}  带宽{(f['UB']-f['LB'])/f['boll_ma']*100:.1f}%")
        p(f"  MA5={f['ma5']:.2f} MA10={f['ma10']:.2f} MA20={f['ma20']:.2f} MA60={f['ma60']:.2f}")
        p(f"  CP={f['cp']:.2f}  震仓线=45")

        p(); p("--- 子系统16: 核心黄金分割撑压 ---")
        p(
            "  "
            f"支撑一={_display_number(f.get('support_1'))} "
            f"支撑二={_display_number(f.get('support_2'))} "
            f"压力一={_display_number(f.get('pressure_1'))} "
            f"压力二={_display_number(f.get('pressure_2'))}"
        )
        p(f"  OUTPUT66={_display_text(f.get('output66'))}")
        p(
            "  "
            f"状态={f.get('support_pressure_status', '撑压不可判定')} "
            f"最近有效支撑={_display_number(f.get('nearest_support'))} "
            f"最近有效压力={_display_number(f.get('nearest_pressure'))}"
        )

        assessment = f.get('comprehensive_assessment') or build_comprehensive_assessment(f)
        p(); p("="*70); p("  十六子系统综合分析与明确结论"); p("="*70)
        p(); p("一、五维综合评分")
        for name, dimension in assessment['dimensions'].items():
            subsystem_text = '/'.join(str(number) for number in dimension['subsystems'])
            p(
                f"  {name}:{dimension['score']:.1f}/100 "
                f"[子系统{subsystem_text}] {dimension['status']}；{dimension['evidence']}"
            )
        p(
            f"  综合评分:{assessment['score']}/100  "
            f"综合评级:{assessment['rating']}  "
            f"适用子系统:{assessment['applicable_subsystems']}/16"
        )
        if assessment['excluded_subsystems']:
            p(
                "  指数不适用但保留的子系统:"
                + ','.join(str(number) for number in assessment['excluded_subsystems'])
            )

        p(); p("二、综合状态")
        medium_gate = assessment.get('medium_term_confirmation') or {}
        p(f"  中期确认闸:{medium_gate.get('status', 'NOT_AVAILABLE')}")
        p(
            "  中期确认条件:"
            f"站稳全部中长期线={'是' if medium_gate.get('stood_above_all_long_emas') else '否'}；"
            f"黄金压力突破={'是' if medium_gate.get('golden_pressure_broken') else '否'}；"
            f"下降趋势线突破核验={'是' if medium_gate.get('downtrend_breakout_verified') else '否'}"
        )
        if medium_gate.get('reasons'):
            p("  未通过原因:" + '；'.join(medium_gate['reasons']))
        p(f"  市场阶段:{assessment['market_phase']}")
        p(f"  主方向:{assessment['primary_direction']}")
        p(f"  强弱性质:{assessment['strength_character']}")
        p(f"  核心矛盾:{assessment['primary_conflict']}")

        p(); p("三、明确结论")
        p(f"  明确结论:{assessment['clear_conclusion']}")

        p(); p("四、条件化执行判断")
        p(f"  转强条件:{assessment['bullish_trigger']}")
        p(f"  转弱条件:{assessment['bearish_trigger']}")
        p(f"  失效条件:{assessment['invalidation']}")
        p(f"  当前立场:{assessment['action_stance']}")
        snapshot_source = (
            '独立日期验证后的TQ快照'
            if f.get('snapshot_date_verified')
            else 'TQ快照仅作旁证，未并入当日K线'
        )
        p(
            f"  数据源:[TQ运行时公式={f['formula_runtime_name']}]"
            f"+[{snapshot_source}]"
            f"+[本地通达信日线{f['n_persisted_records']}条；当日栏={f['bar_source']}]"
        )

        return '\n'.join(lines)

    def print_report(self, d: dict):
        print(self.format_report(d))

    def save_report(self, d: dict, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.format_report(d))
        return filepath


def _display_number(value, digits=2):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return 'NA'
    if not math.isfinite(numeric_value):
        return 'NA'
    return f'{numeric_value:.{digits}f}'


def _display_text(value):
    if value is None:
        return 'NA'
    text = str(value).strip()
    if not text or text.upper() in {'NA', 'N/A', '--'}:
        return 'NA'
    return text


def _float_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp_score(value):
    return max(0.0, min(100.0, float(value)))


def _mean_score(values):
    numbers = [float(value) for value in values if value is not None]
    return sum(numbers) / len(numbers) if numbers else 50.0


def _dimension_status(score):
    if score >= 75:
        return '强势'
    if score >= 60:
        return '偏强'
    if score >= 45:
        return '中性'
    if score >= 30:
        return '偏弱'
    return '弱势'


def build_comprehensive_assessment(data: dict) -> dict:
    """Fuse the fixed 16 subsystems into one auditable directional decision."""
    d = data or {}
    is_index = bool(d.get('is_index'))
    excluded = [4, 9, 10, 11, 12] if is_index else []

    close = float(d.get('close') or 0.0)
    main_trend = float(d.get('main_trend') or 0.0)
    trend_gap = (
        (close - main_trend) / main_trend * 100.0
        if close > 0 and main_trend > 0 else 0.0
    )
    long_bullish = (
        d.get('ema173') is not None
        and d.get('ema193') is not None
        and d.get('ema213') is not None
        and d['ema173'] > d['ema193'] > d['ema213']
    )
    long_ema_values = [
        value for value in (
            _float_or_none(d.get('ema173')),
            _float_or_none(d.get('ema193')),
            _float_or_none(d.get('ema213')),
        ) if value is not None
    ]
    previous_long_ema_values = [
        value for value in (
            _float_or_none(d.get('ema173_prev')),
            _float_or_none(d.get('ema193_prev')),
            _float_or_none(d.get('ema213_prev')),
        ) if value is not None
    ]
    last_close = float(d.get('last_close') or 0.0)
    above_all_long_emas = (
        len(long_ema_values) == 3 and close >= max(long_ema_values)
    )
    above_all_long_emas_previous = (
        len(previous_long_ema_values) == 3
        and last_close > 0
        and last_close >= max(previous_long_ema_values)
    )
    stood_above_all_long_emas = (
        above_all_long_emas and above_all_long_emas_previous
    )
    golden_pressure_values = [
        value for value in (
            _float_or_none(d.get('pressure_1')),
            _float_or_none(d.get('pressure_2')),
        ) if value is not None
    ]
    if not golden_pressure_values:
        fallback_pressure = _float_or_none(d.get('nearest_pressure'))
        if fallback_pressure is not None:
            golden_pressure_values = [fallback_pressure]
    golden_pressure_broken = (
        bool(golden_pressure_values) and close > max(golden_pressure_values)
    )
    downtrend_breakout_verified = bool(d.get('downtrend_breakout_verified'))
    medium_term_reasons = []
    if is_index and not stood_above_all_long_emas:
        medium_term_reasons.append('收盘未站稳全部中长期趋势线')
    if is_index and not golden_pressure_broken:
        medium_term_reasons.append('黄金分割压力位未突破')
    if is_index and not downtrend_breakout_verified:
        medium_term_reasons.append('下降趋势线突破未核验')
    medium_term_confirmed = bool(
        is_index
        and stood_above_all_long_emas
        and golden_pressure_broken
        and downtrend_breakout_verified
    )
    medium_term_confirmation = {
        'status': 'CONFIRMED' if medium_term_confirmed else 'UNCONFIRMED' if is_index else 'NOT_APPLICABLE',
        'above_all_long_emas': above_all_long_emas,
        'above_all_long_emas_previous': above_all_long_emas_previous,
        'stood_above_all_long_emas': stood_above_all_long_emas,
        'golden_pressure_broken': golden_pressure_broken,
        'downtrend_breakout_verified': downtrend_breakout_verified,
        'downtrend_breakout_source': d.get('downtrend_breakout_source', '未提供'),
        'reasons': medium_term_reasons,
    }

    trend_line_score = 50.0
    trend_line_score += 15.0 if d.get('trend_up') else -20.0
    trend_line_score += 15.0 if close > main_trend else -20.0
    if trend_gap >= 1.0:
        trend_line_score += 5.0
    elif trend_gap <= -1.0:
        trend_line_score -= 5.0

    ema_structure_score = 50.0
    ema_structure_score += 15.0 if d.get('bullish') else -20.0
    ema_structure_score += 10.0 if long_bullish else -15.0
    ema213 = _float_or_none(d.get('ema213'))
    if ema213 is not None:
        ema_structure_score += 10.0 if close >= ema213 else -10.0

    kline_score = 50.0 + (12.0 if close >= float(d.get('open') or close) else -12.0)
    if float(d.get('lower_shadow') or 0.0) > float(d.get('body') or 0.0):
        kline_score += 8.0
    if float(d.get('upper_shadow') or 0.0) > float(d.get('body') or 0.0):
        kline_score -= 5.0

    dx = float(d.get('dx') or 0.0)
    if dx > 50:
        dx_score = 75.0
    elif dx > 20:
        dx_score = 68.0
    elif dx >= 0:
        dx_score = 58.0
    elif dx > -20:
        dx_score = 42.0
    elif dx > -50:
        dx_score = 30.0
    else:
        dx_score = 20.0
    dx_score += 8.0 if d.get('dx_dir') == '增强' else -10.0

    cai = float(d.get('cai') or 0.0)
    shen = float(d.get('shen') or 0.0)
    caishen_score = 75.0 if cai > shen else 30.0 if cai < shen else 50.0

    if d.get('buy_sig') and not d.get('sell_sig'):
        participation_signal_score = 85.0
    elif d.get('sell_sig'):
        participation_signal_score = 20.0
    else:
        participation_signal_score = 50.0

    kongpan = float(d.get('kongpan') or 0.0)
    kongpan_prev = float(d.get('kongpan_prev') or 0.0)
    control_score = 50.0
    control_score += 20.0 if kongpan > kongpan_prev else -20.0 if kongpan < kongpan_prev else 0.0
    control_score += 5.0 if kongpan > 0 else -5.0 if kongpan < 0 else 0.0

    participation_scores = [participation_signal_score, control_score]
    participation_subsystems = [6, 7]
    if not is_index:
        participation_subsystems.extend([4, 9])
        participation_scores.append(50.0)
        participation_scores.append(
            85.0 if d.get('zhuangjin') else 15.0 if d.get('zhuangchu') else 50.0
        )

    ema3 = float(d.get('ema3') or 0.0)
    ema21 = float(d.get('ema21') or 0.0)
    pointfire_score = 90.0 if d.get('dianhuo') else 58.0 if ema3 > ema21 else 30.0
    resonance_score = 50.0
    resonance_score += 15.0 if d.get('jincha_kdj') else -15.0
    resonance_score += 15.0 if float(d.get('macd_bar') or 0.0) > 0 else -15.0
    if float(d.get('kdj_k') or 0.0) > 80 or float(d.get('kdj_j') or 0.0) > 100:
        resonance_score -= 10.0

    attack_scores = [pointfire_score, resonance_score]
    attack_subsystems = [13, 14]
    if not is_index:
        attack_subsystems = [10, 11, 12, 13, 14]
        first_leader = (
            bool(d.get('is_zt'))
            and _float_or_none(d.get('cb_ratio')) is not None
            and float(d['cb_ratio']) < 1.0
        )
        second_leader = (
            float(d.get('change_pct') or 0.0) >= 7.0
            and _float_or_none(d.get('cb_ratio')) is not None
            and float(d['cb_ratio']) < 1.0
        )
        attack_scores = [
            75.0 if d.get('is_zt') else 50.0,
            80.0 if first_leader or second_leader else 45.0,
            80.0 if d.get('lht') else 45.0,
            pointfire_score,
            resonance_score,
        ]

    boll_mid = float(d.get('boll_ma') or 0.0)
    boll_upper = float(d.get('UB') or 0.0)
    ma60 = float(d.get('ma60') or 0.0)
    boll_score = 50.0
    boll_score += 12.0 if close >= boll_mid else -12.0
    boll_score += 10.0 if close >= ma60 else -5.0
    if close > 0 and boll_upper > close:
        upper_gap = (boll_upper - close) / close * 100.0
        if upper_gap <= 2.0:
            boll_score -= 8.0
    elif boll_upper > 0 and close >= boll_upper:
        boll_score -= 15.0

    support = _float_or_none(d.get('nearest_support'))
    pressure = _float_or_none(d.get('nearest_pressure'))
    support_pressure_score = 50.0
    if support is not None:
        support_pressure_score += 5.0
    if pressure is not None:
        support_pressure_score += 5.0 if pressure <= close else -10.0
    if support is not None and pressure is not None and close > support:
        downside = (close - support) / close
        upside = (pressure - close) / close
        if golden_pressure_broken and upside > downside * 1.15:
            support_pressure_score += 5.0
        elif downside > upside * 1.15:
            support_pressure_score -= 5.0

    trend_structure_score = round(_mean_score([
        _clamp_score(trend_line_score),
        _clamp_score(ema_structure_score),
    ]), 1)
    if is_index and not medium_term_confirmed:
        trend_structure_score = min(trend_structure_score, 59.0)

    dimensions = {
        '趋势结构': {
            'subsystems': [1, 2],
            'score': trend_structure_score,
            'evidence': (
                f"主趋势线{'向上' if d.get('trend_up') else '向下'}，"
                f"价格位于趋势线{'上方' if close >= main_trend else '下方'}；"
                f"短中期均线{'多头排列' if d.get('bullish') else '未形成多头排列'}，"
                f"长周期均线内部{'顺序排列' if long_bullish else '非顺序排列'}；"
                f"收盘{'已' if stood_above_all_long_emas else '未'}站稳全部中长期线"
            ),
        },
        '短线动量': {
            'subsystems': [3, 5, 8],
            'score': round(_mean_score([
                _clamp_score(kline_score),
                _clamp_score(dx_score),
                _clamp_score(caishen_score),
            ]), 1),
            'evidence': (
                f"{d.get('kline_type', '未知')}线，DX={dx:.2f}且{d.get('dx_dir', '方向不明')}，"
                f"财神结构{'偏多' if cai > shen else '偏空' if cai < shen else '持平'}"
            ),
        },
        '参与强度': {
            'subsystems': participation_subsystems,
            'score': round(_mean_score([_clamp_score(value) for value in participation_scores]), 1),
            'evidence': (
                f"参与提醒={'触发' if d.get('buy_sig') else '未触发'}，"
                f"离场提醒={'触发' if d.get('sell_sig') else '未触发'}，"
                f"控盘程度较前值{'增强' if kongpan > kongpan_prev else '减弱' if kongpan < kongpan_prev else '持平'}"
            ),
        },
        '进攻信号': {
            'subsystems': attack_subsystems,
            'score': round(_mean_score([_clamp_score(value) for value in attack_scores]), 1),
            'evidence': (
                f"点火信号={'触发' if d.get('dianhuo') else '未触发'}，"
                f"KDJ={'金叉' if d.get('jincha_kdj') else '死叉'}，"
                f"MACD柱={'为正' if float(d.get('macd_bar') or 0.0) > 0 else '为负'}"
            ),
        },
        '位置与风险': {
            'subsystems': [15, 16],
            'score': round(_mean_score([
                _clamp_score(boll_score),
                _clamp_score(support_pressure_score),
            ]), 1),
            'evidence': (
                f"价格位于BOLL中轨{'上方' if close >= boll_mid else '下方'}，"
                f"相对MA60为{'上方' if close >= ma60 else '下方'}；"
                f"撑压状态={d.get('support_pressure_status', '不可判定')}"
            ),
        },
    }
    for dimension in dimensions.values():
        dimension['status'] = _dimension_status(dimension['score'])

    weights = {
        '趋势结构': 0.30,
        '短线动量': 0.20,
        '参与强度': 0.20,
        '进攻信号': 0.15,
        '位置与风险': 0.15,
    }
    total_score = round(sum(
        dimensions[name]['score'] * weight
        for name, weight in weights.items()
    ))
    if is_index and not medium_term_confirmed:
        total_score = min(total_score, 57)
    if total_score >= 80:
        rating = '强势偏多'
    elif total_score >= 68:
        rating = '偏多'
    elif total_score >= 58:
        rating = '中性偏多'
    elif total_score >= 42:
        rating = '中性震荡'
    elif total_score >= 32:
        rating = '中性偏空'
    else:
        rating = '偏空'

    trend_score = dimensions['趋势结构']['score']
    momentum_score = dimensions['短线动量']['score']
    attack_score = dimensions['进攻信号']['score']
    high_momentum_position = (
        float(d.get('kdj_k') or 0.0) > 80
        or (close > 0 and boll_upper > close and (boll_upper - close) / close <= 0.02)
    )
    if is_index and not medium_term_confirmed:
        market_phase = '中期转强未确认的压力区震荡'
        primary_direction = '中期方向未确认，短线反弹受压'
        strength_character = '短线修复不等于中期趋势突破'
    elif trend_score >= 70:
        if momentum_score < 60 or attack_score < 70:
            market_phase = (
                '上升趋势中的高位震荡整固'
                if high_momentum_position else '上升趋势中的动能休整'
            )
            primary_direction = '中期偏多，短线转入震荡'
            strength_character = '趋势占优，但进攻动能不足'
        elif momentum_score >= 70 and attack_score >= 75:
            market_phase = '上升趋势中的加速阶段'
            primary_direction = '中短期同步偏多'
            strength_character = '趋势与进攻信号共振'
        else:
            market_phase = '上升趋势中的稳步推进'
            primary_direction = '中期偏多，短线温和偏强'
            strength_character = '趋势延续，动能尚未全面加速'
    elif trend_score < 40:
        market_phase = '下降趋势中的弱势阶段'
        primary_direction = '中短期偏空'
        strength_character = '趋势和动量共同承压'
    else:
        market_phase = '方向选择前的区间震荡'
        primary_direction = '中期中性，短线等待确认'
        strength_character = '多空证据相互抵消'

    resistance_values = sorted({
        value for value in (
            _float_or_none(d.get('ema213')),
            _float_or_none(d.get('ema193')),
            _float_or_none(d.get('ema173')),
            _float_or_none(d.get('UB')),
            _float_or_none(d.get('ma60')),
        )
        if value is not None and value > close
    })
    resistance_low = resistance_values[0] if resistance_values else pressure
    resistance_high = resistance_values[-1] if resistance_values else pressure
    defense_values = sorted({
        value for value in (
            _float_or_none(d.get('ema20')),
            _float_or_none(d.get('main_trend')),
            _float_or_none(d.get('boll_ma')),
        )
        if value is not None and value < close
    }, reverse=True)
    defense_high = defense_values[0] if defense_values else support
    defense_low = defense_values[-1] if defense_values else support

    primary_conflict = (
        '短周期主趋势线虽已转向上，但中长期趋势线、黄金分割压力和下降趋势线突破条件未同时确认。'
        if is_index and not medium_term_confirmed
        else
        '趋势保持向上，但短线动能边际减弱、点火未触发且上方压力密集，'
        '多头结构与短线追涨条件并未同步。'
        if trend_score >= 70 and (momentum_score < 60 or attack_score < 70)
        else '趋势、动量、参与和位置证据尚未形成完全一致的单边共振。'
    )
    trade_date = str(d.get('trade_date') or '').strip()
    long_ema_top = max(long_ema_values) if long_ema_values else None
    golden_pressure_top = max(golden_pressure_values) if golden_pressure_values else None
    confirmed_gate_count = sum((
        bool(stood_above_all_long_emas),
        bool(golden_pressure_broken),
        bool(downtrend_breakout_verified),
    )) if is_index else 0
    dimension_clause = '/'.join(
        f"{name}{float(dimensions[name]['score']):.1f}"
        for name in ('趋势结构', '短线动量', '参与强度', '进攻信号', '位置与风险')
    )
    current_fact_clauses = []
    if trade_date:
        current_fact_clauses.append(f'{trade_date}收盘{close:.2f}')
    else:
        current_fact_clauses.append(f'本次收盘{close:.2f}')
    current_fact_clauses.extend((
        f"主趋势线{main_trend:.2f}{'向上' if bool(d.get('trend_up')) else '向下'}",
        f"长期EMA最高{_display_number(long_ema_top)}、连续2日全站稳{'是' if stood_above_all_long_emas else '否'}",
        f"黄金压力{_display_number(golden_pressure_top)}突破{'是' if golden_pressure_broken else '否'}",
        f"下降趋势线核验{'是' if downtrend_breakout_verified else '否'}",
        f"DX{float(d.get('dx') or 0.0):.2f}{str(d.get('dx_dir') or '方向未标注')}",
        (
            f"KDJ{float(d.get('kdj_k') or 0.0):.2f}/"
            f"{float(d.get('kdj_d') or 0.0):.2f}/"
            f"{float(d.get('kdj_j') or 0.0):.2f}、MACD柱{float(d.get('macd_bar') or 0.0):.2f}"
        ),
        f"五维{dimension_clause}、综合{int(total_score)}分",
    ))
    if is_index:
        rule_decision = (
            f"中期确认闸{confirmed_gate_count}/3；"
            + (
                f"未通过项={'、'.join(medium_term_reasons)}，不能判定中期偏强，阶段={market_phase}。"
                if not medium_term_confirmed else
                f"三项全部通过，阶段={market_phase}，主方向={primary_direction}。"
            )
        )
    else:
        rule_decision = (
            f"五维加权{int(total_score)}分对应{rating}，阶段={market_phase}，"
            f"主方向={primary_direction}。"
        )
    clear_conclusion = '｜'.join(current_fact_clauses) + '；' + rule_decision
    legacy_fixed_conclusion_fragments = (
        '当前只确认短周期主趋势线修复',
        '仍处于中期上升结构',
        '多头证据占优，当前保持偏多判断',
        '空头证据占优，当前应以防守',
        '多空证据接近平衡，当前属于震荡等待确认',
    )
    conclusion_provenance = {
        'method': 'CURRENT_RUN_EVIDENCE_CLAUSES_V1',
        'fallback_used': False,
        'legacy_fixed_conclusion_match': any(
            fragment in clear_conclusion for fragment in legacy_fixed_conclusion_fragments
        ),
        'fact_count': len(current_fact_clauses) + 1,
        'trade_date': trade_date,
        'facts': current_fact_clauses,
        'rule_decision': rule_decision,
    }

    if is_index and not medium_term_confirmed:
        long_trigger = max(long_ema_values) if long_ema_values else None
        golden_trigger = max(golden_pressure_values) if golden_pressure_values else None
        bullish_trigger = (
            f"至少连续两个收盘站稳{_display_number(long_trigger)}以上，"
            f"有效突破黄金分割压力{_display_number(golden_trigger)}，"
            '并取得下降趋势线突破的可核验字段；三项缺一不得判定中期偏强。'
        )
    else:
        bullish_trigger = (
        f"有效突破并站稳{_display_number(resistance_low)}至"
        f"{_display_number(resistance_high)}压力区，同时DX重新增强或点火触发。"
        if resistance_low is not None else
        '突破最近有效压力，同时DX重新增强或点火触发。'
        )
    bearish_trigger = (
        f"先跌破{_display_number(defense_high)}，再失守"
        f"{_display_number(main_trend)}主趋势线，短线转弱得到确认。"
        if defense_high is not None and main_trend > 0 else
        '跌破最近有效防守位且主趋势线转向下，短线转弱得到确认。'
    )
    invalidation = (
        f"若收盘跌破{_display_number(defense_low)}并伴随短周期主趋势线拐头向下，"
        '当前短线反弹结构失效；中期偏强判断当前并未成立。'
        if is_index and not medium_term_confirmed and defense_low is not None else
        f"收盘有效跌破{_display_number(defense_low)}并伴随主趋势线拐头向下，"
        '当前“中期偏多”判断失效。'
        if defense_low is not None else
        '主趋势线拐头向下且价格跌破最近有效支撑，当前偏多判断失效。'
    )
    if is_index and not medium_term_confirmed:
        action_stance = '保持中性防守，等待中长期趋势线、黄金压力和下降趋势线三项突破条件同时确认。'
    elif market_phase == '上升趋势中的高位震荡整固':
        action_stance = (
            '以持有观察和等待确认突破为主，不把未触发的点火信号解释为追涨信号；'
            '回踩防守区企稳或突破压力区后再提高进攻判断。'
        )
    elif total_score >= 68:
        action_stance = '保持偏多观察，等待进攻信号确认后再提高参与强度。'
    elif total_score < 42:
        action_stance = '以风险控制为主，等待趋势和动量重新转强。'
    else:
        action_stance = '保持中性观察，等待突破或跌破给出方向。'

    return {
        'score': int(total_score),
        'rating': rating,
        'applicable_subsystems': 16 - len(excluded),
        'excluded_subsystems': excluded,
        'medium_term_confirmation': medium_term_confirmation,
        'dimensions': dimensions,
        'market_phase': market_phase,
        'primary_direction': primary_direction,
        'strength_character': strength_character,
        'primary_conflict': primary_conflict,
        'clear_conclusion': clear_conclusion,
        'conclusion_provenance': conclusion_provenance,
        'bullish_trigger': bullish_trigger,
        'bearish_trigger': bearish_trigger,
        'invalidation': invalidation,
        'action_stance': action_stance,
    }


def _subsystem_row(number, name, evidence, status, conclusion, note='适用'):
    return {
        '公式': DaniuxianAnalyzer.FORMULA_RUNTIME_NAME,
        '序号': number,
        '子系统/输出': name,
        '当前值/证据': str(evidence or '无可用证据'),
        '状态': str(status or '状态不可判定'),
        '结论': str(conclusion or '结论不可判定'),
        '适用性/备注': str(note or '适用性未说明'),
    }


def build_subsystem_rows(data: dict) -> list[dict]:
    """Build the fixed 16-row external table without parsing text reports."""
    d = data or {}
    is_index = bool(d.get('is_index'))

    def index_na(number, name, reason):
        return _subsystem_row(
            number, name, '指数不适用', '指数不适用',
            f'{reason}，不纳入指数技术结论', '保留固定子系统行',
        )

    trend_up = bool(d.get('trend_up'))
    bullish = bool(d.get('bullish'))
    close = d.get('close')
    main_trend = d.get('main_trend')
    main_trend_status = '向上' if trend_up else '向下'
    kline_color = '红K' if (
        d.get('ema5') is not None
        and d.get('ema20') is not None
        and d.get('ema5') > d.get('ema20')
    ) else '绿/白K'
    dx = d.get('dx')
    try:
        dx_value = float(dx)
        dx_zone = (
            '超买' if dx_value > 50 else
            '多头' if dx_value > 20 else
            '中性' if dx_value > -20 else
            '空头' if dx_value > -50 else
            '超卖'
        )
    except (TypeError, ValueError):
        dx_zone = '状态不可判定'
    buy_sig = bool(d.get('buy_sig'))
    sell_sig = bool(d.get('sell_sig'))
    if buy_sig and sell_sig:
        trade_state = '参与与离场提醒同时触发'
    elif buy_sig:
        trade_state = '参与提醒触发'
    elif sell_sig:
        trade_state = '离场提醒触发'
    else:
        trade_state = '未触发'
    kongpan = d.get('kongpan')
    kongpan_prev = d.get('kongpan_prev')
    try:
        kongpan_status = '增强' if float(kongpan) > float(kongpan_prev) else (
            '减弱' if float(kongpan) < float(kongpan_prev) else '持平'
        )
    except (TypeError, ValueError):
        kongpan_status = '状态不可判定'
    cai = d.get('cai')
    shen = d.get('shen')
    try:
        caishen_status = '偏多' if float(cai) > float(shen) else (
            '偏空' if float(cai) < float(shen) else '持平'
        )
    except (TypeError, ValueError):
        caishen_status = '状态不可判定'
    dianhuo = bool(d.get('dianhuo'))
    momentum_positive = bool(d.get('jincha_kdj')) and (
        d.get('macd_bar') is not None and d.get('macd_bar') > 0
    )
    cb_ratio_value = _float_or_none(d.get('cb_ratio'))
    change_pct_value = _float_or_none(d.get('change_pct'))
    first_leader_buy = (
        bool(d.get('is_zt'))
        and cb_ratio_value is not None
        and cb_ratio_value < 1
    )
    second_leader_buy = (
        change_pct_value is not None
        and change_pct_value >= 7
        and cb_ratio_value is not None
        and cb_ratio_value < 1
    )
    boll_position = '上半区' if (
        close is not None
        and d.get('boll_ma') is not None
        and close > d.get('boll_ma')
    ) else '下半区'

    rows = [
        _subsystem_row(
            1, '主趋势线',
            f"现值={_display_number(main_trend)}，前值={_display_number(d.get('main_trend_prev'))}，收盘={_display_number(close)}",
            main_trend_status,
            f'主趋势线{main_trend_status}，方向{"偏多" if trend_up else "偏空"}',
        ),
        _subsystem_row(
            2, 'EMA均线分层',
            f"EMA5/10/20={_display_number(d.get('ema5'))}/{_display_number(d.get('ema10'))}/{_display_number(d.get('ema20'))}；EMA173/193/213={_display_number(d.get('ema173'))}/{_display_number(d.get('ema193'))}/{_display_number(d.get('ema213'))}",
            '多头排列' if bullish else '非多头排列',
            '短中期均线结构偏多' if bullish else '短中期均线尚未形成多头排列',
        ),
        _subsystem_row(
            3, 'K线颜色信号',
            f"{kline_color}，{d.get('kline_type', 'NA')}线，实体={_display_number(d.get('body'))}，上影={_display_number(d.get('upper_shadow'))}，下影={_display_number(d.get('lower_shadow'))}",
            kline_color,
            f'当前按大牛线着色规则判定为{kline_color}',
        ),
    ]
    rows.append(
        index_na(4, '流通市值', '流通市值及每股财务指标属于个股口径')
        if is_index else _subsystem_row(
            4, '流通市值',
            f"流通市值={_display_number(d.get('float_cap'))}亿，总股本={_display_number((d.get('j_zgb') or 0) / 10000)}亿股",
            '已取得',
            '流通市值数据已纳入个股规模判断',
        )
    )
    rows.extend([
        _subsystem_row(
            5, 'DX动量指标',
            f"DX={_display_number(dx)}，前值={_display_number(d.get('dx_prev'))}，方向={d.get('dx_dir', 'NA')}",
            dx_zone,
            f'DX动量处于{dx_zone}区间',
        ),
        _subsystem_row(
            6, '参与与离场信号',
            f"参与提醒={buy_sig}，离场提醒={sell_sig}",
            trade_state,
            f'大牛线参与与离场信号当前为{trade_state}',
        ),
        _subsystem_row(
            7, '控盘程度',
            f"当前={_display_number(kongpan, 4)}，前值={_display_number(kongpan_prev, 4)}",
            kongpan_status,
            f'控盘程度较前值{kongpan_status}',
        ),
        _subsystem_row(
            8, '财神短线',
            f"财={_display_number(cai, 4)}，神={_display_number(shen, 4)}",
            caishen_status,
            f'财神短线结构{caishen_status}',
        ),
    ])
    rows.append(
        index_na(9, '庄进/庄出', '庄进和庄出属于个股资金信号')
        if is_index else _subsystem_row(
            9, '庄进/庄出',
            f"OUTPUT4={d.get('o4', 'NA')}，OUTPUT6={d.get('o6', 'NA')}",
            '庄进触发' if d.get('zhuangjin') else (
                '庄出触发' if d.get('zhuangchu') else '未触发'
            ),
            '庄进/庄出信号按本机大牛线公式输出判定',
        )
    )
    rows.append(
        index_na(10, '妖股识别', '妖股识别属于个股涨停与量能模型')
        if is_index else _subsystem_row(
            10, '妖股识别',
            f"涨停={bool(d.get('is_zt'))}，量比={_display_number(d.get('cb_ratio'))}",
            '妖股条件成立' if d.get('is_zt') else '妖股条件不成立',
            '按涨停、平台和量能条件综合判定',
        )
    )
    rows.append(
        index_na(11, '龙头参与区', '龙头参与区属于个股涨停与缩量模型')
        if is_index else _subsystem_row(
            11, '龙头参与区',
            f"涨幅={_display_number(d.get('change_pct'))}%，量比={_display_number(d.get('cb_ratio'))}",
            '第一参与区触发' if first_leader_buy else (
                '第二参与区触发' if second_leader_buy else '未触发'
            ),
            '龙头参与区按涨幅与缩量条件判定',
        )
    )
    rows.append(
        index_na(12, '龙回头', '龙回头属于个股涨停回撤模型')
        if is_index else _subsystem_row(
            12, '龙回头',
            (
                f"图示四件套共同条件，13日涨停={d.get('zt_13d', 'NA')}，"
                f"前一日跌破45={bool(d.get('lht_ref_pp45'))}，"
                f"前一日跌破20={bool(d.get('lht_ref_pp20'))}"
            ),
            '触发' if d.get('lht') else '未触发',
            '龙回头只按白横杠、红点、红箭头和红色买字共同条件判定',
        )
    )
    rows.extend([
        _subsystem_row(
            13, '点火信号',
            f"EMA3={_display_number(d.get('ema3'))}，EMA21={_display_number(d.get('ema21'))}，OUTPUT9={d.get('o9', 'NA')}",
            '点火触发' if dianhuo else '未触发',
            '短线点火条件已触发' if dianhuo else '短线点火条件尚未触发',
        ),
        _subsystem_row(
            14, '起爆/题材共振',
            f"KDJ K/D/J={_display_number(d.get('kdj_k'))}/{_display_number(d.get('kdj_d'))}/{_display_number(d.get('kdj_j'))}；MACD柱={_display_number(d.get('macd_bar'))}",
            '动量偏多' if momentum_positive else '动量未共振',
            '指数仅采用KDJ与MACD动量观察' if is_index else '起爆条件按KDJ、涨停和题材共振判定',
            '指数部分适用' if is_index else '适用',
        ),
        _subsystem_row(
            15, 'BOLL+多重均线',
            f"BOLL上/中/下={_display_number(d.get('UB'))}/{_display_number(d.get('boll_ma'))}/{_display_number(d.get('LB'))}；MA5/10/20/60={_display_number(d.get('ma5'))}/{_display_number(d.get('ma10'))}/{_display_number(d.get('ma20'))}/{_display_number(d.get('ma60'))}",
            boll_position,
            f'价格处于BOLL{boll_position}，结合多重均线判断趋势强弱',
        ),
        _subsystem_row(
            16, '核心黄金分割撑压',
            (
                f"支撑一={_display_number(d.get('support_1'))}，"
                f"支撑二={_display_number(d.get('support_2'))}，"
                f"压力一={_display_number(d.get('pressure_1'))}，"
                f"压力二={_display_number(d.get('pressure_2'))}，"
                f"OUTPUT66={_display_text(d.get('output66'))}"
            ),
            d.get('support_pressure_status', '撑压不可判定'),
            (
                f"最近有效支撑={_display_number(d.get('nearest_support'))}，"
                f"最近有效压力={_display_number(d.get('nearest_pressure'))}"
            ),
            'TQ核心黄金分割撑压输出',
        ),
    ])
    return rows


def build_analysis_poster_payload(data: dict) -> dict:
    """Build the compact, structured payload used by the index analysis poster."""
    assessment = data.get('comprehensive_assessment')
    if not isinstance(assessment, dict):
        assessment = build_comprehensive_assessment(data)
    return {
        'status': 'CLEAN_PASS',
        'name': str(data.get('name', '')),
        'code': str(data.get('code', '')),
        'trade_date': str(data.get('trade_date', '')),
        'close': float(data.get('close') or 0.0),
        'change_pct': float(data.get('change_pct') or 0.0),
        'data_source': (
            f"本机通达信日线{int(data.get('n_persisted_records') or 0)}条"
            f"｜当日栏{data.get('bar_source', 'unknown')}"
        ),
        'subsystems': build_subsystem_rows(data),
        'assessment': assessment,
    }


def save_analysis_poster(
    data: dict,
    output: str | os.PathLike[str],
    validation_output: str | os.PathLike[str],
) -> dict:
    """Render and persist the contract-verifiable index analysis poster."""
    from poster_builder import render_index_analysis_poster

    poster_path = Path(output).expanduser().resolve()
    validation_path = Path(validation_output).expanduser().resolve()
    validation = render_index_analysis_poster(
        build_analysis_poster_payload(data),
        poster_path,
    )
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    validation_path.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    return validation


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='大牛线4.0分析')
    parser.add_argument('code', nargs='?', default='002771', help='股票代码')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--poster', help='八千分析海报输出路径')
    parser.add_argument('--poster-validation', help='海报验收JSON输出路径')
    args = parser.parse_args()
    if bool(args.poster) != bool(args.poster_validation):
        parser.error('--poster 与 --poster-validation 必须同时提供')
    if not args.output:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        run_id = os.environ.get('SKILL_FULLFLOW_RUN_ID', '2026-06-12_skill_fullflow_all')
        out_dir = os.path.join(root, 'reports', run_id, 'big-bull-analysis-scoring-system')
        os.makedirs(out_dir, exist_ok=True)
        args.output = os.path.join(out_dir, f'daniuxian_analysis_{args.code}.txt')

    analyzer = DaniuxianAnalyzer(args.code)
    try:
        data = analyzer.collect_all()
        report = analyzer.analyze_all(data)
        analyzer.print_report(report)
        if args.output:
            analyzer.save_report(report, args.output)
            print(f"\n报告已保存: {args.output}")
        if args.poster:
            validation = save_analysis_poster(report, args.poster, args.poster_validation)
            print(f"海报已保存: {args.poster}")
            print(json.dumps({'poster_validation': validation}, ensure_ascii=False))
    finally:
        analyzer.close()
