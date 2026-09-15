from __future__ import annotations
from pathlib import Path
from datetime import datetime, timedelta, timezone
import os, time
import pandas as pd

class TushareUnavailable(RuntimeError): pass

class TusharePostMarketAdapter:
    """仅下载盘后数据。严禁集合竞价和分钟线端点。"""
    INDEX_CODES=('000001.SH','399001.SZ','000300.SH','000905.SH','000852.SH','932000.CSI','399006.SZ','000688.SH')
    CORE_APIS=('daily','daily_basic','adj_factor','bak_basic','stock_st','stk_limit','top_list','top_inst')

    def __init__(self, token=None, out_dir='data_raw', sleep=.13, retries=3):
        self.token = token or os.getenv('TUSHARE_TOKEN')
        if not self.token: raise TushareUnavailable('缺少TUSHARE_TOKEN；禁止伪造真实历史数据')
        try: import tushare as ts
        except Exception as e: raise TushareUnavailable('未安装tushare；原始数据下载功能不可用') from e
        self.ts=ts; ts.set_token(self.token); self.pro=ts.pro_api(); self.out=Path(out_dir); self.out.mkdir(parents=True,exist_ok=True)
        self.sleep=float(sleep); self.retries=max(1,int(retries))

    def _call(self, fn, **kw):
        last=None
        for n in range(self.retries):
            try:
                result=fn(**kw)
                if not isinstance(result,pd.DataFrame):
                    raise TushareUnavailable('接口未返回数据表；不能当作有效空数据缓存')
                return result
            except Exception as ex:
                last=ex
                if n+1<self.retries: time.sleep(self.sleep*(2**n))
        raise last

    def _atomic_csv(self,p,df):
        p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+'.tmp')
        if not isinstance(df,pd.DataFrame) or not len(df.columns):
            raise TushareUnavailable('拒绝缓存无结构数据')
        df.to_csv(tmp,index=False,encoding='utf-8-sig'); tmp.replace(p); return p

    @staticmethod
    def _today():
        return datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d')

    def _range(self,start,end):
        start=str(start); end=self._today() if end is None else str(end)
        for value in (start,end):
            if len(value)!=8 or not value.isdigit(): raise ValueError('日期必须为YYYYMMDD')
            datetime.strptime(value,'%Y%m%d')
        if start>end or end>self._today(): raise ValueError('日期范围倒置或包含未来日期')
        return start,end

    @staticmethod
    def _validate_rows(df,dt=None,allow_empty=False):
        if not isinstance(df,pd.DataFrame) or not {'ts_code','trade_date'}.issubset(df.columns):
            raise TushareUnavailable('数据缺少股票代码或交易日期字段')
        if df.empty and not allow_empty: raise TushareUnavailable('必要行情数据为空')
        if df[['ts_code','trade_date']].isna().any().any(): raise TushareUnavailable('数据主键缺失')
        if dt is not None and not df.trade_date.astype(str).eq(dt).all():
            raise TushareUnavailable('接口数据日期与请求不一致')
        return df

    def _save(self,name,df): return self._atomic_csv(self.out/f'{name}.csv',df)

    def trade_calendar(self,start='20180101',end=None):
        start,end=self._range(start,end)
        return self._save('trade_cal', self._call(self.pro.trade_cal,exchange='',start_date=start,end_date=end,is_open='1'))

    def stock_basic_all(self):
        fs=[]
        for status in ['L','D','P']:
            z=self._call(self.pro.stock_basic,exchange='',list_status=status,fields='ts_code,symbol,name,area,industry,market,exchange,list_status,list_date,delist_date')
            if z is not None and len(z): fs.append(z)
        if not fs: raise TushareUnavailable('stock_basic无法获取')
        return self._save('stock_basic',pd.concat(fs,ignore_index=True).drop_duplicates('ts_code'))

    def industry_members(self):
        classes=[]
        for src in ['SW2014','SW2021']:
            z=self._call(self.pro.index_classify,level='L1',src=src)
            if z is not None and len(z):
                z=z.copy(); z['classification_version']=src; classes.append(z)
        if not classes: raise TushareUnavailable('申万一级行业分类无法获取')
        cls=pd.concat(classes,ignore_index=True).drop_duplicates(); self._save('sw_classify',cls)
        fs=[]
        for code in sorted(cls['index_code'].dropna().astype(str).unique()):
            for flag in ['Y','N']:
                z=self._call(self.pro.index_member_all,l1_code=code,is_new=flag); z=pd.DataFrame() if z is None else z
                if len(z)>=2000: raise TushareUnavailable(f'申万成分分片疑似截断:{code}:{flag}')
                if len(z): fs.append(z)
                time.sleep(self.sleep)
        if not fs: raise TushareUnavailable('申万历史成分无法获取')
        return self._save('sw_members',pd.concat(fs,ignore_index=True).drop_duplicates())

    def by_trade_date(self,api_name,dates):
        if api_name not in self.CORE_APIS: raise ValueError(f'非盘后白名单API: {api_name}')
        out=self.out/api_name; out.mkdir(exist_ok=True); api=getattr(self.pro,api_name)
        for dt in dates:
            dt,_=self._range(dt,dt)
            p=out/f'{dt}.csv'
            allow_empty=api_name in ('top_list','top_inst','stock_st')
            if p.exists():
                try:
                    self._validate_rows(pd.read_csv(p,dtype={'ts_code':str,'trade_date':str}),dt,allow_empty)
                    # Today's response may precede final postmarket publication.
                    if dt<self._today(): continue
                except (ValueError,OSError,pd.errors.ParserError,TushareUnavailable): pass
            df=self._validate_rows(self._call(api,trade_date=dt),dt,allow_empty)
            self._atomic_csv(p,df); time.sleep(self.sleep)
        return out

    def index_daily(self,start,end):
        start,end=self._range(start,end)
        out=self.out/'index_daily'; out.mkdir(exist_ok=True)
        for code in self.INDEX_CODES:
            p=out/f"{code.replace('.','_')}.csv"
            # Refresh the requested range; file existence does not prove coverage.
            # Split by year to stay below the endpoint's per-response row limit.
            frames=[]
            for year in range(int(start[:4]),int(end[:4])+1):
                lo=max(start,f'{year}0101'); hi=min(end,f'{year}1231')
                part=self._validate_rows(self._call(self.pro.index_daily,ts_code=code,start_date=lo,end_date=hi),allow_empty=True)
                if not part.empty:
                    dates=part.trade_date.astype(str)
                    if not part.ts_code.eq(code).all() or not dates.between(lo,hi).all():
                        raise TushareUnavailable('指数返回代码或日期越界')
                    part=part.copy(); part['trade_date']=dates
                frames.append(part)
                time.sleep(self.sleep)
            fresh=pd.concat(frames,ignore_index=True)
            if p.exists():
                try:
                    old=self._validate_rows(pd.read_csv(p,dtype={'ts_code':str,'trade_date':str}),allow_empty=True)
                    if not old.ts_code.eq(code).all(): raise TushareUnavailable('指数缓存代码不符')
                    fresh=pd.concat([old,fresh],ignore_index=True)
                except (ValueError,OSError,pd.errors.ParserError,TushareUnavailable): pass
            fresh=fresh.drop_duplicates(['ts_code','trade_date'],keep='last').sort_values('trade_date')
            self._atomic_csv(p,fresh)
            time.sleep(self.sleep)
        return out

    def download_core(self,start='20180101',end=None):
        start,end=self._range(start,end)
        cal=self._call(self.pro.trade_cal,exchange='',start_date=start,end_date=end,is_open='1')
        if 'cal_date' not in cal or cal.empty: raise TushareUnavailable('交易日历为空或结构无效')
        dates=sorted(set(cal['cal_date'].astype(str).tolist()))
        if any(dt<start or dt>end for dt in dates): raise TushareUnavailable('交易日历超出请求范围')
        self._save('trade_cal',cal); self.stock_basic_all(); self.industry_members(); self.index_daily(start,end)
        for api in self.CORE_APIS: self.by_trade_date(api,dates)
        return self.out
