from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class DataAudit:
    passed: bool
    errors: tuple[str,...]
    warnings: tuple[str,...]
    stats: dict

CORE_DIRS=('daily','daily_basic','adj_factor','bak_basic','stock_st','stk_limit','top_list','top_inst')
CORE_FILES=('trade_cal.csv','stock_basic.csv','sw_members.csv')
DIR_SCHEMA={
    'daily': {'ts_code','trade_date','open','high','low','close','vol','amount'},
    'daily_basic': {'ts_code','trade_date'},
    'adj_factor': {'ts_code','trade_date','adj_factor'},
    'bak_basic': {'ts_code','trade_date'},
    'stock_st': {'ts_code','trade_date'},
    'stk_limit': {'ts_code','trade_date','up_limit','down_limit'},
    'top_list': {'ts_code','trade_date'},
    'top_inst': {'ts_code','trade_date'},
}
STATIC_SCHEMA={
    'trade_cal.csv': {'cal_date'},
    'stock_basic.csv': {'ts_code','name','list_date'},
    'sw_members.csv': {'ts_code','l1_code','in_date','out_date'},
}
OPTIONAL_SCHEMA={
    'event_features.csv': {'trade_date','ts_code','public_time'},
    'theme_members.csv': {'ts_code','theme_code','in_date','out_date'},
}
INDEX_SCHEMA={'ts_code','trade_date','close'}
DATE_FILE_RE=re.compile(r'^(\d{8})\.csv$')
FORBIDDEN_DIRS={'stk_auction_o','mins_5m','sw_mins_5m','auction','minutes','intraday'}
SPARSE_EMPTY_OK={'stock_st','top_list','top_inst'}


def _csv_header(path:Path)->set[str]:
    try:return set(pd.read_csv(path,nrows=0).columns)
    except pd.errors.EmptyDataError:return set()


def _date_files(path:Path)->set[str]:
    out=set()
    if not path.exists():return out
    for p in path.glob('*.csv'):
        m=DATE_FILE_RE.match(p.name)
        if m:out.add(m.group(1))
    return out


def _audit_one_dated_file(path:Path, dirname:str, errors:list[str], stats:dict):
    """逐文件审计，不再只抽前3个文件。只读表头+主键/日期列，避免用抽样掩盖坏文件。"""
    h=_csv_header(path)
    if not h:
        if dirname not in SPARSE_EMPTY_OK:
            errors.append(f'{dirname}/{path.name}为空或无表头')
        return
    need=DIR_SCHEMA.get(dirname,set())
    miss=need-h
    if miss:
        errors.append(f'{dirname}/{path.name}缺字段:{sorted(miss)}')
        return
    # 文件名日期与内容日期必须一致；同时审计基础主键重复。
    m=DATE_FILE_RE.match(path.name)
    if not m or 'trade_date' not in h:return
    expected=m.group(1)
    use=['trade_date']+(['ts_code'] if 'ts_code' in h else [])
    try:
        x=pd.read_csv(path,dtype=str)
    except pd.errors.EmptyDataError:
        if dirname not in SPARSE_EMPTY_OK:errors.append(f'{dirname}/{path.name}为空')
        return
    except Exception as ex:
        errors.append(f'{dirname}/{path.name}读取失败:{ex}')
        return
    if x.empty:
        if dirname not in SPARSE_EMPTY_OK:errors.append(f'{dirname}/{path.name}无数据行')
        return
    if 'ts_code' in x and (x['ts_code'].isna()|x['ts_code'].str.strip().eq('')).any():
        errors.append(f'{dirname}/{path.name}存在空股票主键')
    numeric={
        'daily':['open','high','low','close','vol','amount'],
        'adj_factor':['adj_factor'], 'stk_limit':['up_limit','down_limit'],
        'daily_basic':['close','turnover_rate','total_share','float_share','free_share','circ_mv','total_mv'],
        'top_list':['l_buy','l_sell','l_amount','buy','sell','buy_amount','sell_amount'],
        'top_inst':['buy','sell','net_buy'],
    }.get(dirname,[])
    no_limit=pd.Series(False,index=x.index)
    if dirname=='stk_limit' and 'no_limit' in x:
        from .pit_risk_guard import _bool
        try: no_limit=x['no_limit'].map(_bool)
        except ValueError:
            errors.append(f'{dirname}/{path.name}无涨跌幅限制标记无效')
        if (no_limit & x[['up_limit','down_limit']].notna().any(axis=1)).any():
            errors.append(f'{dirname}/{path.name}无涨跌幅限制标记与限价冲突')
    converted={}
    for col in numeric:
        if col not in x: continue
        v=pd.to_numeric(x[col],errors='coerce');converted[col]=v
        bad=~np.isfinite(v)
        # 官方每日基础数据可有不适用空值；但已提供的坏值/无限值不能放行。
        if dirname=='daily_basic':bad=bad & x[col].notna()
        if col not in {'net_buy'}:bad=bad|(v<0)
        if col in {'open','high','low','close','adj_factor','up_limit','down_limit'}:bad=bad|(v<=0)
        if dirname=='stk_limit' and col in {'up_limit','down_limit'}:
            bad=bad & ~(no_limit & x[col].isna())
        if bad.any(): errors.append(f'{dirname}/{path.name}字段{col}存在无效数值')
    if dirname=='daily' and all(c in converted for c in ['open','high','low','close']):
        o,h,l,c=(converted[k] for k in ['open','high','low','close'])
        if ((h<l)|(h<o)|(h<c)|(l>o)|(l>c)).any():
            errors.append(f'{dirname}/{path.name}价格高低关系不成立')
    if dirname=='stk_limit' and all(c in converted for c in ['up_limit','down_limit']):
        if (converted['up_limit']<converted['down_limit']).any():
            errors.append(f'{dirname}/{path.name}涨跌停价格顺序错误')
    td=x['trade_date'].astype(str).str.replace('-','',regex=False).str[:8]
    wrong=td.ne(expected)&td.ne('')
    if bool(wrong.any()):
        errors.append(f'{dirname}/{path.name}存在与文件名不一致的trade_date')
    if dirname in {'daily','daily_basic','adj_factor','stk_limit','bak_basic','stock_st'} and 'ts_code' in x:
        dup=int(x.duplicated(['ts_code','trade_date']).sum())
        if dup:
            errors.append(f'{dirname}/{path.name}存在{dup}条重复主键')
            stats[f'{dirname}_duplicate_keys']=stats.get(f'{dirname}_duplicate_keys',0)+dup



def _audit_daily_security_coverage(root:Path, dates, errors, stats):
    """A date file proves no stock coverage by itself; audit every actual daily key."""
    from .pit_risk_guard import _bool
    for day in sorted(dates):
        try:
            daily=pd.read_csv(root/'daily'/f'{day}.csv',dtype=str)
            wanted=set(daily['ts_code'].dropna())
        except Exception as ex:
            errors.append(f'daily/{day}.csv股票覆盖读取失败:{ex}');continue
        for table in ['daily_basic','adj_factor','bak_basic','stk_limit','stock_st']:
            path=root/table/f'{day}.csv'
            if not path.exists():continue  # Existing file-date audit reports this.
            try:
                x=pd.read_csv(path,dtype=str)
                got=set(x['ts_code'].dropna()) if 'ts_code' in x else set()
                miss=sorted(wanted-got)
                if miss and table!='stock_st':
                    key=table+'_missing_security_days'
                    stats[key]=stats.get(key,0)+len(miss)
                    errors.append(f'{table}/{day}.csv缺少{len(miss)}只当日有行情股票，示例:{",".join(miss[:5])}')
                if table=='stock_st':
                    from .pit_risk_guard import attach_pit_risk
                    hbpath=root/'bak_basic'/f'{day}.csv'
                    hb=pd.read_csv(hbpath,dtype=str) if hbpath.exists() else None
                    try: attach_pit_risk(daily[['ts_code','trade_date']],x,hb)
                    except ValueError as exc:
                        stats['stock_st_unverified_security_days']=stats.get('stock_st_unverified_security_days',0)+len(wanted)
                        errors.append(f'stock_st/{day}.csv历史状态未获完整证明；稀疏名单不能单独证明正常:{exc}')
                if table=='bak_basic':
                    if 'name' not in x or x['name'].isna().any() or x['name'].str.strip().eq('').any():
                        errors.append(f'bak_basic/{day}.csv缺少同日历史名称')
            except Exception as ex:
                errors.append(f'{table}/{day}.csv股票覆盖审计失败:{ex}')


def audit_raw_data(root, *, require_end:str|None=None)->DataAudit:
    root=Path(root);errors=[];warnings=[];stats={}
    if not root.exists():return DataAudit(False,(f'数据目录不存在:{root}',),(),{})

    bad=[d for d in FORBIDDEN_DIRS if (root/d).exists()]
    if bad:
        errors.append('检测到禁止的盘中/竞价目录: '+','.join(sorted(bad))+'；为防误读与工作流漂移，原始数据审计直接失败')

    # 下载失败痕迹不能被静默忽略。
    err_files=sorted(root.rglob('ERROR_*.txt'))
    for f in err_files[:50]:
        msg=f.read_text(encoding='utf-8',errors='ignore').replace('\n',' ')[:180]
        errors.append(f'数据下载错误:{f.relative_to(root)}:{msg}')
    if len(err_files)>50:errors.append(f'另有{len(err_files)-50}个ERROR文件未展开')

    for f in CORE_FILES:
        p=root/f
        if not p.exists():
            errors.append('缺少:'+f);continue
        h=_csv_header(p);miss=STATIC_SCHEMA[f]-h
        if miss:errors.append(f'{f}缺字段:{sorted(miss)}')
        else:
            try:
                static=pd.read_csv(p,dtype=str)
                if static.empty:errors.append(f'{f}无数据行')
                keys={'stock_basic.csv':['ts_code'],'trade_cal.csv':['cal_date'],
                      'sw_members.csv':['ts_code','in_date']}[f]
                if static[keys].isna().any().any() or static[keys].apply(lambda c:c.str.strip().eq('')).any().any():
                    errors.append(f'{f}存在空主键')
                if static.duplicated(keys).any():errors.append(f'{f}存在重复主键')
                if f=='stock_basic.csv':
                    if pd.to_datetime(static['list_date'],errors='coerce').isna().any():errors.append(f'{f}存在无效上市日期')
                if f=='sw_members.csv':
                    start=pd.to_datetime(static['in_date'],errors='coerce')
                    end=pd.to_datetime(static['out_date'],errors='coerce')
                    if start.isna().any() or (static['out_date'].notna()&end.isna()).any() or (end<start).any():
                        errors.append(f'{f}存在无效归属日期区间')
                    check=static.assign(_start=start,_end=end.fillna(pd.Timestamp('2099-12-31'))).sort_values(['ts_code','_start'])
                    for _,g in check.groupby('ts_code'):
                        if (g['_start']<=g['_end'].cummax().shift()).any():
                            errors.append(f'{f}存在重叠行业归属区间');break
            except Exception as ex:errors.append(f'{f}内容审计失败:{ex}')


    # 所有逐日目录都必须实际存在且有日期快照；不再只抽样表头。
    for d in CORE_DIRS:
        p=root/d
        if not p.exists():
            errors.append('缺少目录:'+d);continue
        fs=sorted(p.glob('*.csv'));stats[d+'_files']=len(fs)
        if not fs:
            errors.append('目录无CSV:'+d);continue
        for f in fs:_audit_one_dated_file(f,d,errors,stats)

    # 交易日历与逐日文件覆盖：空龙虎榜日也应有空快照文件，避免“不知道是0还是没下载”。
    open_dates=[]
    calp=root/'trade_cal.csv'
    if calp.exists() and not (STATIC_SCHEMA['trade_cal.csv']-_csv_header(calp)):
        try:
            c=pd.read_csv(calp,dtype=str)
            if 'is_open' in c:c=c[c['is_open'].astype(str)=='1']
            open_dates=sorted(c['cal_date'].dropna().astype(str).str.replace('-','',regex=False).str[:8].unique())
            if open_dates:
                stats['open_sessions']=len(open_dates);stats['calendar_start']=open_dates[0];stats['calendar_end']=open_dates[-1]
        except Exception as ex:errors.append(f'trade_cal.csv读取失败:{ex}')

    dates={d:_date_files(root/d) for d in CORE_DIRS if (root/d).exists()}
    base=dates.get('daily',set())
    if base:
        lo,hi=min(base),max(base);stats['daily_start']=lo;stats['daily_end']=hi
        if open_dates:
            expected={x for x in open_dates if lo<=x<=hi}
            missing_daily=sorted(expected-base)
            extra_daily=sorted(base-set(open_dates))
            if missing_daily:errors.append(f'daily缺少{len(missing_daily)}个交易日快照，示例:{",".join(missing_daily[:5])}')
            if extra_daily:warnings.append(f'daily存在{len(extra_daily)}个不在交易日历中的日期文件，示例:{",".join(extra_daily[:5])}')
        else:expected=set(base)
        for d in CORE_DIRS:
            if d=='daily' or d not in dates:continue
            miss=sorted(expected-dates[d])
            if miss:errors.append(f'{d}缺少{len(miss)}个交易日快照，示例:{",".join(miss[:5])}')
    _audit_daily_security_coverage(root,base,errors,stats)
    if require_end:
        req=require_end.replace('-','')
        if not base:errors.append('daily无可审计日期文件')
        elif max(base)<req:errors.append(f'daily最新日期{max(base)}早于要求{require_end}')
        if open_dates and max(open_dates)<req:errors.append(f'交易日历最新日期{max(open_dates)}早于要求{require_end}')

    # 可选但重要的数据源也做真实schema审计，不允许“文件存在=模块已完成”。
    for item,need in OPTIONAL_SCHEMA.items():
        p=root/item;key='coverage_'+item.replace('.csv','')
        exists=p.exists();stats[key]=bool(exists)
        if not exists:
            warnings.append(f'可选但重要数据缺失:{item}；对应模块将明确降级，不允许静默跳过')
        else:
            h=_csv_header(p);miss=need-h
            if miss:errors.append(f'{item}缺字段:{sorted(miss)}')
            elif item=='event_features.csv':
                try:
                    ev=pd.read_csv(p,usecols=['trade_date','ts_code','public_time'])
                    if len(ev):
                        pt=pd.to_datetime(ev['public_time'],errors='coerce',utc=True)
                        if pt.isna().any():errors.append('event_features.csv存在无法解析的public_time')
                except Exception as ex:errors.append(f'event_features.csv读取失败:{ex}')

    ip=root/'index_daily';stats['coverage_index_daily']=bool(ip.exists() and any(ip.glob('*.csv')))
    if not stats['coverage_index_daily']:
        warnings.append('可选但重要数据缺失:index_daily；市场因果模块将明确降级')
    else:
        for f in sorted(ip.glob('*.csv')):
            h=_csv_header(f);miss=INDEX_SCHEMA-h
            if miss:errors.append(f'index_daily/{f.name}缺字段:{sorted(miss)}')

    return DataAudit(not errors,tuple(errors),tuple(warnings),stats)
