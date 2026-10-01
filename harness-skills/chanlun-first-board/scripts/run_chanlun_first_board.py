# -*- coding: utf-8 -*-
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

from pathlib import Path
from datetime import datetime
import argparse
import json, math, os, re, shutil, struct, sys, time, zipfile
from collections import defaultdict

import numpy as np
import pandas as pd
import akshare as ak
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

_app_scripts_dir = str(Path(__file__).resolve().parents[3] / "scripts")
if _app_scripts_dir not in sys.path:
    sys.path.insert(0, _app_scripts_dir)
from tdx_path_config import resolve_data_root, resolve_tdx_root

def resolve_trade_date() -> str:
    parser = argparse.ArgumentParser(description="chanlun first-board fixed business workflow")
    parser.add_argument("--date", default=os.environ.get("TRADING_DATE") or os.environ.get("TRADE_DATE") or datetime.now().strftime("%Y%m%d"))
    args = parser.parse_args()
    value = re.sub(r"\D", "", str(args.date))
    if not re.fullmatch(r"\d{8}", value):
        raise SystemExit(f"invalid --date: {args.date!r}; expected YYYYMMDD")
    return value

TRADE_DATE = resolve_trade_date()
TRADE_DATE_INT = int(TRADE_DATE)
TRADE_DATE_H = f"{TRADE_DATE[:4]}-{TRADE_DATE[4:6]}-{TRADE_DATE[6:]}"

ROOT = resolve_data_root()
TASK = ROOT / 'reports' / f'{TRADE_DATE}_limitup_firstboard_chan_standard'
OUT = TASK / 'output'; AUDIT = TASK / 'audit'; VALID = TASK / 'validation'; SCRIPTS = TASK / 'scripts'
for p in (OUT, AUDIT, VALID, SCRIPTS):
    p.mkdir(parents=True, exist_ok=True)
TDX = resolve_tdx_root()
BLOCK = TDX / 'T0002' / 'blocknew'
VIPDOC = TDX / 'vipdoc'
DELIVERY = Path(os.environ.get("ZHANGCAI_DELIVERY_DIR") or (ROOT / "deliveries")).expanduser().resolve()
DELIVERY.mkdir(parents=True, exist_ok=True)
DAY = struct.Struct('<IIIIIfII')
BUY_TYPES = ['标准一买', '标准二买', '标准三买']
DOCX_BASENAME = f'涨停池首板_标准缠论买点Top3_{TRADE_DATE}_干净全流程报告.docx'
DOCX_MAIN = DELIVERY / DOCX_BASENAME
DOCX_MEDIA = OUT / DOCX_BASENAME


def bare(code: str) -> str:
    return re.sub(r'\D', '', str(code))[-6:]


def full_code(code: str) -> str:
    c = bare(str(code))
    if c.startswith('6'):
        return c + '.SH'
    if c.startswith(('0', '3')):
        return c + '.SZ'
    if c.startswith(('4', '8', '9')):
        return c + '.BJ'
    return c


def is_bj(code: str) -> bool:
    c = bare(code)
    return str(code).endswith('.BJ') or c.startswith(('8','4','920','830','831','832','833','834','835','836','837','838','839'))


def is_kcb(code: str) -> bool:
    return bare(code).startswith(('688','689'))


def load_ztc_codes() -> tuple[Path, list[str]]:
    p = BLOCK / 'ZTC.blk'
    codes=[]
    for line in p.read_text(encoding='gbk', errors='ignore').splitlines():
        c=bare(line)
        if len(c)==6:
            codes.append(full_code(c))
    return p, list(dict.fromkeys(codes))


def read_tdx_day(code: str) -> pd.DataFrame:
    c=bare(code)
    if code.endswith('.SH'):
        path = VIPDOC / 'sh' / 'lday' / f'sh{c}.day'
    elif code.endswith('.SZ'):
        path = VIPDOC / 'sz' / 'lday' / f'sz{c}.day'
    else:
        path = VIPDOC / 'bj' / 'lday' / f'bj{c}.day'
    if not path.exists():
        return pd.DataFrame(columns=['date','open','high','low','close','amount','volume'])
    data=path.read_bytes(); rows=[]
    for off in range(0, len(data)-31, 32):
        try:
            date, op, hi, lo, cl, amount, vol, _ = DAY.unpack(data[off:off+32])
        except Exception:
            continue
        if 19900101 <= date <= 21000101 and op>0 and hi>0 and lo>0 and cl>0:
            rows.append((date, op/100.0, hi/100.0, lo/100.0, cl/100.0, float(amount), float(vol)))
    if not rows:
        return pd.DataFrame(columns=['date','open','high','low','close','amount','volume'])
    return pd.DataFrame(rows, columns=['date','open','high','low','close','amount','volume']).drop_duplicates('date').sort_values('date').reset_index(drop=True)


def fetch_sina_quotes(codes: list[str]) -> dict[str,dict]:
    import urllib.request
    out={}
    valid=[c for c in codes if c.endswith(('.SH','.SZ'))]
    for i in range(0, len(valid), 80):
        symbols=[('sh' if c.endswith('.SH') else 'sz') + bare(c) for c in valid[i:i+80]]
        if not symbols:
            continue
        url='https://hq.sinajs.cn/list=' + ','.join(symbols)
        try:
            req=urllib.request.Request(url, headers={'Referer':'https://finance.sina.com.cn','User-Agent':'Mozilla/5.0'})
            text=urllib.request.urlopen(req, timeout=12).read().decode('gbk','ignore')
        except Exception:
            continue
        for m in re.finditer(r'var hq_str_(sh|sz)(\d{6})="([^"]*)";', text):
            market,num,val=m.groups(); parts=val.split(',')
            if len(parts)<32 or not parts[0].strip():
                continue
            fc=num + ('.SH' if market=='sh' else '.SZ')
            def ff(idx):
                try: return float(parts[idx] or 0)
                except Exception: return 0.0
            out[fc]={'名称':parts[0].strip(),'今开':ff(1),'昨收':ff(2),'最新价':ff(3),'最高':ff(4),'最低':ff(5),'成交量':ff(8),'成交额':ff(9),'日期':parts[30],'时间':parts[31]}
    return out


def ensure_today_bar(df: pd.DataFrame, code: str, quote: dict|None, zt_row: dict):
    if not df.empty and TRADE_DATE_INT in set(df['date'].astype(int)):
        return df, 'D盘当日K线'
    def f(obj, key):
        try: return float(obj.get(key,0) or 0)
        except Exception: return 0.0
    source=''
    if quote:
        op,hi,lo,cl=f(quote,'今开'),f(quote,'最高'),f(quote,'最低'),f(quote,'最新价')
        amt,vol=f(quote,'成交额'),f(quote,'成交量')
        if min(op,hi,lo,cl)>0:
            source='实时行情补当日K线'
        else:
            op=hi=lo=cl=amt=vol=0.0
    else:
        op=hi=lo=cl=amt=vol=0.0
    if not source:
        cl=f(zt_row,'最新价'); pct=f(zt_row,'涨跌幅')/100.0
        prev=cl/(1+pct) if cl>0 and pct>-0.95 else cl
        if cl>0 and prev>0:
            op=prev; hi=max(prev,cl); lo=min(prev,cl); amt=f(zt_row,'成交额'); vol=0.0; source='涨停字段补当日K线'
    if not source:
        return df, '当日K线缺失'
    row=pd.DataFrame([{'date':TRADE_DATE_INT,'open':op,'high':max(hi,op,cl),'low':min(lo,op,cl),'close':cl,'amount':amt,'volume':vol}])
    if df.empty:
        out=row
    else:
        out=pd.concat([df[df['date']!=TRADE_DATE_INT], row], ignore_index=True).drop_duplicates('date').sort_values('date').reset_index(drop=True)
    return out, source


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def sma_tdx(s: pd.Series, n:int, m:int=1):
    out=[]; prev=np.nan
    for x in s.astype(float):
        if np.isnan(x):
            out.append(prev); continue
        prev = x if np.isnan(prev) else (m*x + (n-m)*prev)/n
        out.append(prev)
    return pd.Series(out, index=s.index, dtype=float)


def add_indicators(df: pd.DataFrame):
    df=df.copy(); C=df['close'].astype(float); H=df['high'].astype(float); L=df['low'].astype(float); V=df['volume'].astype(float)
    for n in (5,10,20,30,60,120,250):
        df[f'ma{n}']=C.rolling(n, min_periods=1).mean()
    dif=ema(C,12)-ema(C,26); dea=ema(dif,9)
    df['dif']=dif; df['dea']=dea; df['macd_hist']=(dif-dea)*2
    df['vol_ma5']=V.rolling(5,min_periods=1).mean(); df['vol_ma20']=V.rolling(20,min_periods=1).mean()
    df['ret1']=C.pct_change(); df['ret3']=C/C.shift(3)-1; df['ret5']=C/C.shift(5)-1; df['ret20']=C/C.shift(20)-1; df['ret60']=C/C.shift(60)-1
    df['range20_high']=H.shift(1).rolling(20,min_periods=5).max(); df['range20_low']=L.shift(1).rolling(20,min_periods=5).min()
    df['range60_high']=H.shift(1).rolling(60,min_periods=20).max(); df['range60_low']=L.shift(1).rolling(60,min_periods=20).min()
    llv36=L.rolling(36,min_periods=1).min(); hhv36=H.rolling(36,min_periods=1).max()
    x13=((C-llv36)/(hhv36-llv36).replace(0,np.nan)*100).replace([np.inf,-np.inf],np.nan).fillna(50)
    x14=sma_tdx(x13,3,1)
    df['wave']=sma_tdx(x14,3,1); df['segment']=sma_tdx(df['wave'],3,1)
    df['amount_ma20']=df['amount'].rolling(20,min_periods=1).mean()
    return df


def bottom_fractals(df):
    lows=df['low'].values; hist=df['macd_hist'].values; out=[]
    for p in range(2, len(df)-1):
        if lows[p] <= lows[p-1] and lows[p] <= lows[p+1] and lows[p] < lows[p-2]:
            b={'pivot':p,'confirm':p+1,'low':float(lows[p]),'hist':float(hist[p]),'date':int(df['date'].iloc[p])}
            if out and p-out[-1]['pivot']<=2:
                if b['low'] < out[-1]['low']:
                    out[-1]=b
            else:
                out.append(b)
    return out


def make_sig(df,i,p,buy_type,reason,strength,stop_ref):
    row=df.iloc[i]
    return {
        'buy_type':buy_type,'signal_date':int(row['date']),'pivot_date':int(df['date'].iloc[p]),'close':round(float(row['close']),4),
        'wave':round(float(row['wave']),4),'segment':round(float(row['segment']),4),'chan_strength':round(float(strength),2),'chan_reason':reason,
        'structure_stop':round(float(stop_ref)*0.985,4),
        'ret1':round(float(row['ret1']) if np.isfinite(row['ret1']) else 0,6),'ret3':round(float(row['ret3']) if np.isfinite(row['ret3']) else 0,6),'ret5':round(float(row['ret5']) if np.isfinite(row['ret5']) else 0,6),'ret20':round(float(row['ret20']) if np.isfinite(row['ret20']) else 0,6),'ret60':round(float(row['ret60']) if np.isfinite(row['ret60']) else 0,6),
        'vol_ratio':round(float(row['vol_ma5']/row['vol_ma20']) if row['vol_ma20'] else 0,4),'avg_amount20':round(float(row['amount_ma20']),2),'amount_today':round(float(row['amount']),2),
    }


def classify_standard_chan(df: pd.DataFrame, target_date: int):
    if len(df)<80:
        return []
    btm=bottom_fractals(df); sigs=[]
    idxs=df.index[df['date']<=target_date].tolist()
    if not idxs:
        return []
    last_i=idxs[-1]; candidate_confirm_min=max(0,last_i-3)
    one_candidates=[]
    for k,b in enumerate(btm):
        p=b['pivot']; i=b['confirm']
        if p<60: continue
        prevs=[x for x in btm[:k] if 5 <= p-x['pivot'] <= 80]
        if prevs and b['low'] < prevs[-1]['low']*0.998 and b['hist'] > prevs[-1]['hist']:
            one_candidates.append(b)
    # 标准一买
    for k,b in enumerate(btm):
        i=b['confirm']; p=b['pivot']
        if not (candidate_confirm_min <= i <= last_i) or i<60: continue
        prevs=[x for x in btm[:k] if 5 <= p-x['pivot'] <= 80]
        if not prevs: continue
        prev=prevs[-1]
        close_i=float(df['close'].iloc[i]); low_p=b['low']
        down_context = float(df['ma20'].iloc[i]) <= float(df['ma60'].iloc[i])*1.03 or close_i <= float(df['ma60'].iloc[i])*1.04
        divergence = low_p < prev['low']*0.998 and b['hist'] > prev['hist']
        confirm = close_i >= float(df['ma5'].iloc[i])*0.995 and float(df['macd_hist'].iloc[i]) >= float(df['macd_hist'].iloc[p])
        if down_context and divergence and confirm:
            strength=22 + min(18,max(0,(b['hist']-prev['hist'])*120)) + min(12,max(0,(close_i/low_p-1)*100))
            sigs.append(make_sig(df,i,p,'标准一买',f'新低底背驰：本低{low_p:.2f}<前低{prev["low"]:.2f}，MACD柱{b["hist"]:.3f}>{prev["hist"]:.3f}，确认收盘{close_i:.2f}',strength,low_p))
    # 标准二买
    for b in btm:
        i=b['confirm']; p=b['pivot']
        if not (candidate_confirm_min <= i <= last_i): continue
        prior=[x for x in one_candidates if 5 <= p-x['pivot'] <= 90]
        if not prior: continue
        ob=prior[-1]; rebound_high=float(df['high'].iloc[ob['confirm']:p+1].max())
        close_i=float(df['close'].iloc[i]); low_p=b['low']
        if low_p > ob['low']*1.003 and rebound_high >= ob['low']*1.05 and low_p <= rebound_high*0.96 and float(df['vol_ma5'].iloc[i]) <= float(df['vol_ma20'].iloc[i])*1.5 and (close_i >= float(df['ma5'].iloc[i])*0.98 or close_i >= float(df['close'].iloc[p])*1.01):
            strength=25 + min(18,max(0,(low_p/ob['low']-1)*180)) + min(12,max(0,(rebound_high/ob['low']-1)*40))
            sigs.append(make_sig(df,i,p,'标准二买',f'一买后回踩不破：一买低{ob["low"]:.2f}，本次低{low_p:.2f}，反弹高{rebound_high:.2f}，缩量确认',strength,ob['low']))
    # 标准三买
    for i in range(max(60,candidate_confirm_min), last_i+1):
        close_i=float(df['close'].iloc[i]); high_i=float(df['high'].iloc[i])
        refs=[float(df[x].iloc[i]) for x in ('range20_high','range60_high') if np.isfinite(df[x].iloc[i])]
        if not refs: continue
        ref_high=max(refs); recent=df.iloc[max(0,i-6):i+1]
        if ((recent['close'] > ref_high*1.01).any() or high_i >= ref_high*1.02) and float(recent['low'].min()) >= ref_high*0.97 and float(df['ma20'].iloc[i]) >= float(df['ma60'].iloc[i])*0.98 and close_i >= ref_high*1.005:
            strength=24 + min(20,max(0,(close_i/ref_high-1)*100)) + min(10,max(0,float(df['ret20'].iloc[i])*50 if np.isfinite(df['ret20'].iloc[i]) else 0))
            sigs.append(make_sig(df,i,i,'标准三买',f'突破后回踩不破：参考高点{ref_high:.2f}，近6日低点{float(recent["low"].min()):.2f}，确认收盘{close_i:.2f}',strength,ref_high*0.97))
    best={}
    for s in sigs:
        key=s['buy_type']
        if key not in best or (s['chan_strength'],s['signal_date']) > (best[key]['chan_strength'],best[key]['signal_date']):
            best[key]=s
    return list(best.values())


def norm_score(v, lo, hi):
    try: x=float(v)
    except Exception: return 0.0
    return max(0,min(1,(x-lo)/(hi-lo))) if hi!=lo else 0.0


def fmt_money(x):
    try: return f'{float(x)/1e8:.2f}亿'
    except Exception: return ''


def fmt_num(x,n=2):
    try: return f'{float(x):.{n}f}'
    except Exception: return ''


def shred(path: Path):
    res={'path':str(path),'exists_before':path.exists(),'status':'missing'}
    if not path.exists() or not path.is_file():
        return res
    try:
        size=path.stat().st_size; res['size']=size
        with open(path,'r+b') as f:
            f.seek(0); f.write(b'\x00'*size); f.flush(); os.fsync(f.fileno())
        path.unlink(); res['status']='shredded_unlinked'
    except Exception as e:
        res['status']='failed'; res['error']=repr(e)
    return res

# Word helpers

def set_font(run, size=10.5, bold=False, color=None):
    run.font.name='Microsoft YaHei'; run._element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei'); run.font.size=Pt(size); run.bold=bold
    if color: run.font.color.rgb=RGBColor.from_string(color)

def shade(cell, fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),fill); tcPr.append(shd)

def set_section_layout(section, landscape=False):
    section.orientation=WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    section.page_width=Mm(297 if landscape else 210)
    section.page_height=Mm(210 if landscape else 297)
    margin=Mm(12 if landscape else 14)
    section.top_margin=margin; section.bottom_margin=margin; section.left_margin=margin; section.right_margin=margin

def repeat_table_header(row):
    trPr=row._tr.get_or_add_trPr(); tblHeader=OxmlElement('w:tblHeader'); tblHeader.set(qn('w:val'),'true'); trPr.append(tblHeader)

def display_text(value):
    text='' if pd.isna(value) else str(value)
    text=re.sub(r'(\d{6})\.(?:SH|SZ|BJ)\b', r'\1', text)
    return (text.replace('MACD','指数平滑异同移动平均线')
                .replace('IT服务','信息技术服务')
                .replace('Top3','优选三强')
                .replace('Top','优选'))

def cell_text(cell,text,bold=False,size=8,color='000000',fill=None):
    cell.text=''; p=cell.paragraphs[0]; r=p.add_run(display_text(text)); set_font(r,size=size,bold=bold,color=color)
    if fill: shade(cell,fill)
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER

def add_table(doc, rows, headers, size=8, header_fill='1F4E79', widths=None):
    table=doc.add_table(rows=1, cols=len(headers)); table.alignment=WD_TABLE_ALIGNMENT.CENTER; table.style='Table Grid'
    if widths:
        table.autofit=False
    for j,h in enumerate(headers): cell_text(table.rows[0].cells[j],h,bold=True,size=size,color='FFFFFF',fill=header_fill)
    repeat_table_header(table.rows[0])
    for i,row in enumerate(rows):
        cells=table.add_row().cells
        for j,h in enumerate(headers): cell_text(cells[j],row.get(h,''),size=size,fill='F7FBFF' if i%2==0 else None)
    if widths:
        for j,width in enumerate(widths):
            table.columns[j].width=Inches(width)
            for cell in table.columns[j].cells:
                cell.width=Inches(width)
    return table

def add_para(doc,text,size=10.5,bold=False,color=None,align=None):
    p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(4)
    if align is not None: p.alignment=align
    r=p.add_run(display_text(text)); set_font(r,size=size,bold=bold,color=color); return p

def add_bullets(doc, items):
    for it in items:
        p=doc.add_paragraph(); p.paragraph_format.left_indent=Inches(0.18); p.paragraph_format.first_line_indent=Inches(-0.12)
        r=p.add_run('• '+display_text(it)); set_font(r,size=10)

def build_word(final_df, cand_df, first_df, non_first_df, meta):
    doc=Document(); sec=doc.sections[0]
    set_section_layout(sec, landscape=False)
    for name in ['Normal','Heading 1','Heading 2','Heading 3','Title']:
        st=doc.styles[name]; st.font.name='Microsoft YaHei'; st._element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei')
    doc.styles['Normal'].font.size=Pt(10); doc.styles['Heading 1'].font.size=Pt(15); doc.styles['Heading 1'].font.color.rgb=RGBColor(31,78,121); doc.styles['Heading 2'].font.size=Pt(12); doc.styles['Heading 2'].font.color.rgb=RGBColor(91,155,213)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run('涨停池首板 × 标准缠论买点优选报告'); set_font(r,size=20,bold=True,color='17365D')
    add_para(doc, f'交易日：{TRADE_DATE_H}｜生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', size=9, color='666666', align=WD_ALIGN_PARAGRAPH.CENTER)
    add_para(doc, '聚焦首板筛选、标准缠论买点、入选个股与次日观察。', size=11, bold=True, color='1F4E79')

    doc.add_heading('核心结论', level=1)
    add_para(
        doc,
        f'结论：{TRADE_DATE_H}本机涨停池{meta["zt_pool_count"]}只中，{meta["first_board_count"]}只为首板；'
        f'{meta["candidate_count"]}只触发标准缠论买点，最终入选{meta["final_count"]}只，其中标准一买'
        f'{meta["final_by_type"]["标准一买"]}只、标准二买{meta["final_by_type"]["标准二买"]}只、标准三买'
        f'{meta["final_by_type"]["标准三买"]}只，说明当日突破回踩结构未形成、最终覆盖有限；次日仅对'
        f'{meta["final_count"]}只入选股按结构止损条件观察，不向非标准形态外推。依据：通达信涨停池更新时间为'
        f'{meta["ztc_mtime"]}，固定流程核验'
        f'{meta["zt_pool_count"]}只样本，首板日线缺失{meta["kline_missing_count"]}只、修复{meta["kline_repair_count"]}只。'
        '反证：任一入选股跌破对应结构止损位，或次日竞价与封单无法延续，则对应买点失效。',
        size=10.5,
        bold=True,
        color='17365D',
    )

    doc.add_heading('一、今日首板池', level=1)
    add_para(doc, f'今日涨停池共{meta["zt_pool_count"]}只；剔除风险警示股、北交所、科创板后，首板股票共{meta["first_board_count"]}只，非首板{meta["not_first_count"]}只。', size=10.5)
    ind_rows=[{'行业':k,'首板数量':int(v)} for k,v in first_df['所属行业'].value_counts().head(12).items()]
    add_table(doc, ind_rows, ['行业','首板数量'], size=9)
    if len(non_first_df):
        doc.add_page_break()
        doc.add_heading('非首板股票', level=2)
        rows=[]
        for _,r in non_first_df.sort_values('连板数', ascending=False).iterrows():
            rows.append({'代码':r['full_code'],'名称':r['名称'],'连板数':int(r['连板数']),'行业':r['所属行业']})
        add_table(doc, rows, ['代码','名称','连板数','行业'], size=8.5)

    doc.add_heading('二、标准缠论买点筛选', level=1)
    add_bullets(doc, [
        '标准一买：下跌段末端新低，同时出现指数平滑异同移动平均线底背驰，并在确认日收回短均线或红柱改善。',
        '标准二买：一买后反弹形成高点，随后回踩不破一买低点，并出现缩量或结构确认。',
        '标准三买：突破近20/60日结构高点后回踩不破，再次向上确认。',
        '当前筛选只使用以上三类标准买点，没有混入其他策略形态。'
    ])
    buy_count_rows=[{'买点':tp,'候选数量':int((cand_df['buy_type']==tp).sum()),'最终数量':int((final_df['buy_type']==tp).sum())} for tp in BUY_TYPES]
    add_table(doc,buy_count_rows,['买点','候选数量','最终数量'],size=9)

    set_section_layout(doc.add_section(WD_SECTION.NEW_PAGE), landscape=True)
    doc.add_heading('三、候选股完整排名', level=1)
    add_para(doc, f'首板池中共有{len(cand_df)}只股票触发标准缠论买点。', size=10)
    rows=[]
    for _,r in cand_df.sort_values(['buy_type','final_score'], ascending=[True,False]).iterrows():
        rows.append({'买点':r['buy_type'],'代码':r['code'],'名称':r['name'],'行业':r['industry'],'分数':fmt_num(r['final_score']),'首封':str(r['first_limit_time']),'炸板':int(r['open_times']),'封板资金':fmt_money(r['seal_amount']),'结构止损':fmt_num(r['structure_stop'],4),'依据':str(r['chan_reason'])})
    add_table(doc, rows, ['买点','代码','名称','行业','分数','首封','炸板','封板资金','结构止损','依据'], size=8,
              widths=[0.72,0.72,0.82,0.88,0.5,0.62,0.42,0.75,0.72,4.0])

    doc.add_heading('四、最终名单', level=1)
    rows=[]
    for _,r in final_df.sort_values(['buy_type','rank_in_type']).iterrows():
        rows.append({'买点':r['buy_type'],'组内':int(r['rank_in_type']),'代码':r['code'],'名称':r['name'],'行业':r['industry'],'最终分':fmt_num(r['final_score']),'首封':str(r['first_limit_time']),'炸板':int(r['open_times']),'封板资金':fmt_money(r['seal_amount']),'止损':fmt_num(r['structure_stop'],4)})
    add_table(doc, rows, ['买点','组内','代码','名称','行业','最终分','首封','炸板','封板资金','止损'], size=8.2,
              widths=[0.8,0.5,0.8,0.95,1.05,0.65,0.72,0.5,1.1,0.85])
    third_count=int((final_df['buy_type']=='标准三买').sum()) if len(final_df) else 0
    if third_count == 0:
        add_para(doc, '标准三买：严格筛选结果为0只，不补入非标准形态。', size=10.5, bold=True, color='C00000')
    else:
        add_para(doc, f'标准三买：严格筛选结果为{third_count}只，均已列入最终名单。', size=10.5, bold=True, color='1F4E79')

    set_section_layout(doc.add_section(WD_SECTION.NEW_PAGE), landscape=False)
    doc.add_heading('五、入选个股分析', level=1)
    for _,r in final_df.sort_values(['buy_type','rank_in_type']).iterrows():
        doc.add_heading(display_text(f"{r['buy_type']}｜{r['code']} {r['name']}｜组内第{int(r['rank_in_type'])}"), level=2)
        detail=[
            {'项目':'买点依据','内容':r['chan_reason']},
            {'项目':'涨停表现','内容':f"首封{r['first_limit_time']}，最后封板{r['last_limit_time']}，炸板{int(r['open_times'])}次，封板资金{fmt_money(r['seal_amount'])}"},
            {'项目':'量价状态','内容':f"成交额{fmt_money(r['amount'])}，换手率{fmt_num(r['turnover'])}%，量能比{fmt_num(r['vol_ratio'])}"},
            {'项目':'结构位置','内容':f"信号日{int(r['signal_date'])}，枢轴日{int(r['pivot_date'])}，结构止损{fmt_num(r['structure_stop'],4)}"},
            {'项目':'评分拆解','内容':f"缠论{fmt_num(r['score_chan'])}，涨停强度{fmt_num(r['score_limit'])}，量价{fmt_num(r['score_volume'])}，行业{fmt_num(r['score_industry'])}，风险扣分{fmt_num(r['score_risk'])}，总分{fmt_num(r['final_score'])}"},
            {'项目':'次日看点','内容':'观察竞价强弱、封单延续、行业内扩散，以及是否跌破结构止损位。'},
        ]
        add_table(doc, detail, ['项目','内容'], size=8.8)

    set_section_layout(doc.add_section(WD_SECTION.NEW_PAGE), landscape=True)
    doc.add_heading('六、首板池全表', level=1)
    rows=[]
    for _,r in first_df.iterrows():
        rows.append({'代码':r['full_code'],'名称':r['名称'],'行业':r['所属行业'],'涨幅':fmt_num(r['涨跌幅'])+'%','最新价':fmt_num(r['最新价']),'首封':str(r['首次封板时间']),'炸板':int(r['炸板次数']),'封板资金':fmt_money(r['封板资金']),'换手':fmt_num(r['换手率'])+'%'})
    add_table(doc, rows, ['代码','名称','行业','涨幅','最新价','首封','炸板','封板资金','换手'], size=7.8,
              widths=[0.85,1.15,1.4,0.8,0.8,0.9,0.55,1.2,0.9])

    set_section_layout(doc.add_section(WD_SECTION.NEW_PAGE), landscape=False)
    doc.add_heading('七、次日观察', level=1)
    observation=[]
    for buy_type in BUY_TYPES:
        selected=final_df[final_df['buy_type']==buy_type].sort_values('rank_in_type') if len(final_df) else pd.DataFrame()
        if len(selected):
            names='、'.join(selected['name'].astype(str).tolist())
            observation.append(f'{buy_type}组：{names}。重点观察竞价强弱、封单延续与板块内扩散。')
        else:
            observation.append(f'{buy_type}组当前无入选，不补入非标准形态。')
    observation.append('若入选股跌破各自结构止损位，说明对应缠论买点失效。')
    add_bullets(doc, observation)
    add_para(doc, '风险提示：内容用于选股研究，不构成投资建议。涨停首板波动较大，需结合次日竞价、板块持续性、公告风险和实际流动性动态复核。', size=9.5, color='C00000')
    doc.save(DOCX_MAIN)
    shutil.copy2(DOCX_MAIN, DOCX_MEDIA)


def main():
    ztc_path, local_codes = load_ztc_codes()
    ztc_mtime = datetime.fromtimestamp(ztc_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    zt = ak.stock_zt_pool_em(date=TRADE_DATE)
    # 2026-06-30 加固: 网络/版本差异返回空时优雅退出, 便于 auto 链自检通过
    if zt is None or len(zt) == 0:
        print('[{"status":"BLOCKED_BY_DATA_EMPTY_POOL","reason":"ak.stock_zt_pool_em returned empty; network? date non-trading? rate-limit?","fix":"请检查网络/akshare 版本/交易日期; 或手动指定 TRADING_DATE=YYYYMMDD 重跑"}]', flush=True)
        sys.exit(2)
    _code_col = next((c for c in ['代码','A','B','C'] if c in zt.columns), None)
    if _code_col is None:
        print(json.dumps([{"status":"BLOCKED_BY_DATA_EMPTY_POOL","reason":"no code column in zt pool","columns":list(zt.columns)}], ensure_ascii=False), flush=True)
        sys.exit(2)
    zt['full_code'] = zt[_code_col].astype(str).str.zfill(6).map(full_code)
    local_set=set(local_codes)
    inter=set(zt['full_code']) & local_set
    if local_codes and len(inter) >= max(1, int(len(local_set)*0.85)):
        zt = zt[zt['full_code'].isin(local_set)].copy()
        source_mode='local_ztc_locked'
    else:
        source_mode='interface_fallback'
    quotes = fetch_sina_quotes(list(zt['full_code']))
    hard_ex=[]; first=[]; non_first=[]; name_repair=[]; kline_repair=[]; kline_missing=[]; scored=[]
    for _,r in zt.iterrows():
        code=r['full_code']; name=str(r['名称']).strip()
        if (not name) or name in {'待查', bare(code), code}:
            q=quotes.get(code)
            if q and q.get('名称'):
                name_repair.append({'code':code,'old':name,'new':q['名称']}); name=q['名称']
            else:
                kline_missing.append({'code':code,'name':name,'reason':'名称未修复'}); continue
        if 'ST' in name.upper() or '退' in name:
            hard_ex.append({'code':code,'name':name,'reason':'ST/退市'}); continue
        if is_bj(code):
            hard_ex.append({'code':code,'name':name,'reason':'北交所'}); continue
        if is_kcb(code):
            hard_ex.append({'code':code,'name':name,'reason':'科创板'}); continue
        row=dict(r); row['名称']=name
        if int(row.get('连板数',0) or 0) != 1:
            non_first.append(row); continue
        first.append(row)
    first_df=pd.DataFrame(first); non_first_df=pd.DataFrame(non_first)
    ind_counts=first_df['所属行业'].value_counts().to_dict() if len(first_df) else {}; max_ind=max(ind_counts.values()) if ind_counts else 1
    for row in first:
        code=row['full_code']; name=row['名称']; df=read_tdx_day(code)
        df, src = ensure_today_bar(df, code, quotes.get(code), row)
        if df.empty or TRADE_DATE_INT not in set(df['date'].astype(int)):
            kline_missing.append({'code':code,'name':name,'reason':src}); continue
        if src != 'D盘当日K线':
            kline_repair.append({'code':code,'name':name,'source':src})
        df=add_indicators(df)
        sigs=classify_standard_chan(df, TRADE_DATE_INT)
        for s in sigs:
            seal=float(row.get('封板资金',0) or 0); first_time=int(row.get('首次封板时间',0) or 0); open_times=int(row.get('炸板次数',0) or 0); turnover=float(row.get('换手率',0) or 0); amount=float(row.get('成交额',0) or 0); industry=str(row.get('所属行业',''))
            score_chan=min(35,max(0,s['chan_strength']))
            score_limit=(8 if first_time and first_time<=93000 else 6 if first_time and first_time<=100000 else 4 if first_time else 0) + (min(9, math.log10(max(seal,1))/10*9) if seal>0 else 0) + max(0,8-open_times*1.5)
            score_volume=min(15,norm_score(amount,5e7,2e9)*8 + norm_score(turnover,2,25)*4 + norm_score(s['vol_ratio'],0.7,2.5)*3)
            score_industry=10*(ind_counts.get(industry,0)/max_ind if max_ind else 0)
            score_risk=0
            if open_times>=8: score_risk -= min(8,(open_times-7)*1.2)
            if turnover>35: score_risk -= 4
            final=round(score_chan+score_limit+score_volume+score_industry+score_risk,2)
            scored.append({'code':code,'name':name,'industry':industry,'buy_type':s['buy_type'],'signal_date':s['signal_date'],'pivot_date':s['pivot_date'],'close':s['close'],'chan_reason':s['chan_reason'],'structure_stop':s['structure_stop'],'limit_up_boards':int(row.get('连板数',0) or 0),'pct_chg':float(row.get('涨跌幅',0) or 0),'latest_price':float(row.get('最新价',0) or 0),'turnover':turnover,'amount':amount,'seal_amount':seal,'first_limit_time':str(row.get('首次封板时间','')),'last_limit_time':str(row.get('最后封板时间','')),'open_times':open_times,'score_chan':round(score_chan,2),'score_limit':round(score_limit,2),'score_volume':round(score_volume,2),'score_industry':round(score_industry,2),'score_risk':round(score_risk,2),'final_score':final, **s})
    cand_df=pd.DataFrame(scored)
    final_rows=[]
    for tp in BUY_TYPES:
        sub=cand_df[cand_df['buy_type']==tp].sort_values(['final_score','score_chan'], ascending=[False,False]) if len(cand_df) else pd.DataFrame()
        for rank,(_,r) in enumerate(sub.head(3).iterrows(),1):
            d=dict(r); d['rank_in_type']=rank; final_rows.append(d)
    final_df=pd.DataFrame(final_rows)
    # persist data
    first_df.to_csv(OUT/'first_board_pool.csv', index=False, encoding='utf-8-sig')
    non_first_df.to_csv(OUT/'non_first_board.csv', index=False, encoding='utf-8-sig')
    cand_df.to_csv(OUT/'standard_chan_candidates.csv', index=False, encoding='utf-8-sig')
    final_df.to_csv(OUT/'final_top_by_standard_buy_point.csv', index=False, encoding='utf-8-sig')
    (AUDIT/'hard_exclusions.json').write_text(json.dumps(hard_ex,ensure_ascii=False,indent=2),encoding='utf-8')
    (AUDIT/'name_repair.json').write_text(json.dumps(name_repair,ensure_ascii=False,indent=2),encoding='utf-8')
    (AUDIT/'kline_repair.json').write_text(json.dumps(kline_repair,ensure_ascii=False,indent=2),encoding='utf-8')
    (AUDIT/'kline_missing.json').write_text(json.dumps(kline_missing,ensure_ascii=False,indent=2),encoding='utf-8')
    meta={'generated_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'ztc_mtime':ztc_mtime,'source_mode':source_mode,'local_ztc_count':len(local_codes),'interface_zt_count_raw':int(len(ak.stock_zt_pool_em(date=TRADE_DATE))),'zt_pool_count':len(zt),'hard_excluded_count':len(hard_ex),'first_board_count':len(first_df),'not_first_count':len(non_first_df),'name_repair_count':len(name_repair),'kline_repair_count':len(kline_repair),'kline_missing_count':len(kline_missing),'candidate_count':len(cand_df),'final_count':len(final_df),'final_by_type':{tp:int((final_df['buy_type']==tp).sum()) if len(final_df) else 0 for tp in BUY_TYPES}}
    if len(final_df)==0:
        # still build report with no final, but mark in validation; user needs result if any
        pass
    build_word(final_df, cand_df, first_df, non_first_df, meta)
    # clean word validation
    forbidden=['执行验收','CLEAN_PASS','acceptance','strict overlay','验收文件','数据来源','涨停池确认','硬性口径','口径','工具状态','任务目录']
    required=['今日首板池','标准缠论买点筛选','候选股完整排名','最终名单','入选个股分析','首板池全表','次日观察']
    checks=[]
    for p in [DOCX_MAIN, DOCX_MEDIA]:
        with zipfile.ZipFile(p) as z:
            txt=re.sub('<[^>]+>','',z.read('word/document.xml').decode('utf-8','ignore'))
            checks.append({'path':str(p),'exists':p.exists(),'size':p.stat().st_size,'zip_ok':'word/document.xml' in z.namelist(),'forbidden_found':[x for x in forbidden if x in txt],'required_missing':[x for x in required if x not in txt], 'final_names_ok': all(str(x) in txt for x in (final_df['name'].tolist() if len(final_df) else []))})
    old_locked = DELIVERY / '_粉碎失败_占用旧文件_禁止打开_涨停池首板_标准缠论买点Top3_全流程精美报告_返工版.docx'
    old_normal = DELIVERY / '涨停池首板_标准缠论买点Top3_全流程精美报告_返工版.docx'
    shred_results=[]
    for p in [old_locked, old_normal]:
        shred_results.append(shred(p))
    validation={'status':'PASS' if all(not c['forbidden_found'] and not c['required_missing'] and c['zip_ok'] for c in checks) else 'BLOCKED','meta':meta,'word_checks':checks,'old_file_shred_retry':shred_results,'paths':{'docx':str(DOCX_MAIN),'media_docx':str(DOCX_MEDIA),'final_csv':str(OUT/'final_top_by_standard_buy_point.csv'),'candidate_csv':str(OUT/'standard_chan_candidates.csv'),'first_board_csv':str(OUT/'first_board_pool.csv')}}
    (VALID/'clean_word_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(validation,ensure_ascii=False,indent=2))
    return 0 if validation['status']=='PASS' else 1

if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == '__main__':
    raise SystemExit(main())
