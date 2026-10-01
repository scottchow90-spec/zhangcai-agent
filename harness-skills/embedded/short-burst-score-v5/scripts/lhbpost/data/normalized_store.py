from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from ..utils import parse_date_series

class NormalizedStore:
    """盘后专用标准化存储。

    统一单位：价格=元；成交量=股；成交额/市值=元；收益率=小数。
    明确不读取集合竞价、分钟线或盘中数据目录。
    """
    def __init__(self, root, strict: bool = True):
        self.root = Path(root)
        self.strict = bool(strict)

    def read_concat(self, subdir):
        p = self.root / subdir
        fs = sorted(p.glob('*.csv')) if p.is_dir() else ([p] if p.exists() else [])
        frames = []
        for f in fs:
            try:
                x = pd.read_csv(f)
                frames.append(x)  # 保留合法空快照的字段，区分零条记录与缺少来源
            except pd.errors.EmptyDataError:
                continue
            except Exception as ex:
                if self.strict: raise ValueError(f'读取CSV失败:{f}: {ex}') from ex
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def _dates(self, df, cols=('trade_date',)):
        x = df.copy()
        for c in cols:
            if c in x: x[c] = parse_date_series(x[c])
        return x

    def daily(self):
        d = self._dates(self.read_concat('daily'))
        if len(d) and 'amount' in d: d['amount'] = pd.to_numeric(d['amount'], errors='coerce') * 1000.0
        if len(d) and 'vol' in d: d['vol'] = pd.to_numeric(d['vol'], errors='coerce') * 100.0
        if len(d) and 'pct_chg' in d: d['pct_chg'] = pd.to_numeric(d['pct_chg'], errors='coerce') / 100.0
        return d

    def daily_basic(self):
        b = self._dates(self.read_concat('daily_basic'))
        if not len(b): return b
        for c in ['total_share','float_share','free_share']:
            if c in b: b[c] = pd.to_numeric(b[c], errors='coerce') * 10000.0
        for c in ['total_mv','circ_mv']:
            if c in b: b[c] = pd.to_numeric(b[c], errors='coerce') * 10000.0
        b['free_mv'] = np.nan
        if 'free_share' in b and 'close' in b:
            b['free_mv'] = pd.to_numeric(b['free_share'], errors='coerce') * pd.to_numeric(b['close'], errors='coerce')
        return b

    def adj_factor(self):
        a = self._dates(self.read_concat('adj_factor'))
        if len(a) and 'adj_factor' in a: a['adj_factor'] = pd.to_numeric(a['adj_factor'], errors='coerce')
        return a

    def historical_basic(self): return self._dates(self.read_concat('bak_basic'))
    def top_list(self): return self._dates(self.read_concat('top_list'))
    def top_inst(self):
        result=self._dates(self.read_concat('top_inst'))
        sides=self._dates(self.read_concat('disclosed_sides'))
        if len(sides):
            import json
            proof=json.loads((self.root/'acquisition_manifest.json').read_text(encoding='utf-8'))
            side_proof=proof.get('disclosed_sides') or {}
            if side_proof.get('acquisition_complete') is not True or side_proof.get('rows')!=len(sides):
                raise ValueError('disclosed_side_acquisition_proof_incomplete')
            result.attrs['disclosed_sides']=sides.to_dict('records')
        return result
    def st(self): return self._dates(self.read_concat('stock_st'))
    def limits(self): return self._dates(self.read_concat('stk_limit'))
    def trade_calendar(self): return self._dates(self.read_concat('trade_cal.csv'), ('cal_date','trade_date'))
    def stock_basic(self): return self._dates(self.read_concat('stock_basic.csv'), ('list_date','delist_date'))
    def sw_members(self): return self._dates(self.read_concat('sw_members.csv'), ('in_date','out_date'))
    def theme_members(self): return self._dates(self.read_concat('theme_members.csv'), ('in_date','out_date'))

    def event_features(self):
        if not (self.root/'event_features.csv').exists(): return None
        x = self._dates(self.read_concat('event_features.csv'))
        from ..utils import normalize_event_features
        x = normalize_event_features(x)
        return x

    def index_daily(self):
        x = self._dates(self.read_concat('index_daily'))
        if len(x) and 'amount' in x: x['amount'] = pd.to_numeric(x['amount'], errors='coerce') * 1000.0
        if len(x) and 'vol' in x: x['vol'] = pd.to_numeric(x['vol'], errors='coerce') * 100.0
        if len(x) and 'pct_chg' in x: x['pct_chg'] = pd.to_numeric(x['pct_chg'], errors='coerce') / 100.0
        return x
