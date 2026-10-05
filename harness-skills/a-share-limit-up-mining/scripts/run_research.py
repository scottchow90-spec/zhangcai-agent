#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
run_research.py — 连板挖掘严格研究模式

数据源 (3 个, 全部 TDX 本地或 akshare, 不搜网页):
  1. 本地 TDX 涨停池 (主源, 自定义板块 ZTC.blk)
  2. akshare.stock_zt_pool_em(date)  当日涨停池 (双源校验 + 字段补充)
  3. akshare.stock_lhb_detail_daily_sina(date)  当日龙虎榜 (资金验证)

K 线复算:
  - 当涨停池字段与本地 TDX K 线冲突时, 按 full_workflow.md 5.1.1 规则复算
  - 5 步: 剔除 → D 日涨停 → D-1 日涨停 → 去重 → 边界

8 因子评分:
  - 连板梯队位置 / 封板质量 / 资金承接 / 辨识度 / 题材主线 / 筹码 / 市场情绪 / 次日可执行性
  - 满分 100, ≥ 70 进入 Top 5

风险扫描 5.4.1 组合规则:
  - A 任一硬剔除触发即出局
  - B 多条降权升级硬剔除
  - C 跨类组合降权加权
  - D 风险时间窗口 (> 5 个交易日失效)
  - E 人工覆盖 (manual_override)

输出 (4 件套):
  candidate_pool.csv / dragon_score.csv / report.md / audit_log.md

长期运行集成 (Codex skill 本地 scripts):
  - health_monitor.py (start/record/finish)
  - data_source_health.py (recommend)
  - archive_prediction.py (落盘快照)

执行:
  python run.py --date 2026-06-21 --manual-confirm
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import warnings
from datetime import datetime
from pathlib import Path

_APP_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(_APP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_APP_SCRIPTS))
from tdx_path_config import resolve_data_root, resolve_tdx_root

from _date_utils import resolve_latest_trade_date

warnings.filterwarnings('ignore')

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

WORKSPACE = resolve_data_root()
SKILL_DIR = Path(__file__).resolve().parents[1]
REPORTS = WORKSPACE / 'reports' / 'skills' / 'a-share-limit-up-mining'
TDX_ROOT = resolve_tdx_root()
ZTC_CANDIDATES = [TDX_ROOT / 'T0002' / 'blocknew' / 'ZTC.blk']
TDX_DAY_CANDIDATES = [TDX_ROOT / 'vipdoc' / market / 'lday' for market in ('sh', 'sz', 'bj')]

# 长期运行配套脚本路径必须收束在本 skill 内，禁止跳到旧外部基础设施目录。
INFRA_SCRIPTS = SKILL_DIR / 'scripts'

AUDIT: dict = {
    'generated_at': datetime.now().astimezone().isoformat(timespec='seconds'),
    'date': None,
    'sources': {},
    'failures': [],
    'fallback_used': [],
    'gate_status': {},
}


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec='seconds')


def _aud(name: str, status: str, **extra) -> None:
    AUDIT['sources'][name] = {'status': status, 'checked_at': _now_iso(), **extra}


def _fail(msg: str) -> None:
    AUDIT['failures'].append({'time': _now_iso(), 'message': msg})


def _fallback(msg: str) -> None:
    AUDIT['fallback_used'].append({'time': _now_iso(), 'message': msg})


def is_real_stock_code(value: object) -> bool:
    code = str(value or '').strip()
    return re.fullmatch(r'\d{6}', code) is not None and code != '000000'


def reconcile_ztc_with_ak(ztc_local: dict[str, str], ak_rows: list[dict]) -> list[dict]:
    """Use ZTC only as a local cross-check; AK supplies the dated business pool."""
    local_codes = {str(code) for code in ztc_local if is_real_stock_code(code)}
    ak_codes = {
        str(row.get('code', '')).strip()
        for row in ak_rows
        if is_real_stock_code(row.get('code'))
    }

    if not local_codes:
        _aud(
            'ztc_cross_check',
            'IGNORED_PLACEHOLDER',
            raw_count=len(ztc_local),
            valid_count=0,
        )
        return list(ak_rows)

    remote_only = sorted(ak_codes - local_codes)
    local_only = sorted(local_codes - ak_codes)
    _aud(
        'ztc_cross_check',
        'RECORDED',
        local_count=len(local_codes),
        ak_count=len(ak_codes),
        overlap_count=len(local_codes & ak_codes),
    )
    if remote_only:
        _aud(
            'ztc_remote_conflicts',
            'RECORDED',
            count=len(remote_only),
            sample=remote_only[:20],
        )
    if local_only:
        _aud(
            'ztc_local_conflicts',
            'RECORDED',
            count=len(local_only),
            sample=local_only[:20],
        )
    return list(ak_rows)


# ============================================================
# 手动闸
# ============================================================
def _gate_manual_only() -> tuple[bool, str]:
    """
    硬闸 1-4: 强制手动触发
      1. 当前时间 >= 15:05 (盘后)
      2. CODEX_AUTOMATION_RUN != 1
      3. CODEX_BACKGROUND_RUN != 1
      4. --manual-confirm 参数 (在 main 里检查)
    """
    now = datetime.now()
    hhmm = now.strftime('%H%M')
    if int(hhmm) < 1505:
        return False, f'当前时间 {hhmm} < 15:05, 不允许盘前/盘中运行'
    if os.environ.get('CODEX_AUTOMATION_RUN') == '1':
        return False, '检测到 CODEX_AUTOMATION_RUN=1, 自动任务不得执行本流程'
    if os.environ.get('CODEX_BACKGROUND_RUN') == '1':
        return False, '检测到 CODEX_BACKGROUND_RUN=1, 后台任务不得执行本流程'
    return True, 'OK'


# ============================================================
# 数据源 1: 本地 ZTC.blk (涨停池主源)
# ============================================================
def find_ztc() -> Path | None:
    for p in ZTC_CANDIDATES:
        if p.exists():
            return p
    return None


def load_tdx_stock_name_index() -> dict[str, str]:
    """从 TDX hq_cache\\infoharbor_ex.code 加载 {code: name} 索引.

    2026-06-21 加固: 给本地 ZTC 单源模式补真实股票名
      文件格式: '000001|平安银行|平安保险,...'
      size: 180 KB / 5535 行 (覆盖全 A 股)
    """
    index_path = TDX_ROOT / 'T0002' / 'hq_cache' / 'infoharbor_ex.code'
    if not index_path.exists():
        _fallback('TDX 股票名索引缺失, 将用 "涨停池" 作为默认名')
        return {}
    try:
        text = index_path.read_bytes().decode('gbk', errors='ignore')
        out = {}
        for line in text.split('\r\n'):
            line = line.strip()
            if not line or '|' not in line:
                continue
            parts = line.split('|')
            if len(parts) >= 2 and len(parts[0]) == 6 and parts[0].isdigit():
                name = parts[1].strip()
                if name:
                    out[parts[0]] = name
        _aud('stock_name_index', 'OK', count=len(out), path=str(index_path))
        return out
    except Exception as e:
        _fail(f'TDX 股票名索引加载失败: {e}')
        _aud('stock_name_index', 'FAIL', error=str(e))
        return {}


def load_ztc_local() -> dict[str, str]:
    """返回 {code: name} 字典, code 6 位.

    2026-06-21 加固: 兼容两种 .blk 格式 + 加载 TDX 股票名索引补真实名
      - 格式 A: "数字 6位代码 名称" (老式, line 158 正则期望)
      - 格式 B: "纯数字代码" (实际 ZTC.blk 格式, 7 位 = 市场码 + 6 位股票码)
                 例如 '1603358' = '1'+'603358' = sh603358
      - 优先用 TDX 股票名索引 (infoharbor_ex.code) 补真实名; 缺省时 '涨停池'
    """
    ztc = find_ztc()
    if not ztc:
        _fail(f'本地 ZTC 路径不存在 (尝试: {[str(p) for p in ZTC_CANDIDATES]})')
        _aud('ztc_local', 'MISSING')
        return {}
    # 加载股票名索引
    name_index = load_tdx_stock_name_index()
    try:
        if ztc.is_dir():
            # 目录情况: 列出所有 .blk 文件
            out = {}
            for blk in ztc.glob('*.blk'):
                try:
                    raw = blk.read_text(encoding='gbk', errors='ignore')
                    blk_name = blk.stem  # e.g. "ZTC", "LBC", "FLZT"
                    for line in raw.splitlines():
                        s = line.strip()
                        if not s:
                            continue
                        digits = ''.join(ch for ch in s if ch.isdigit())
                        if len(digits) < 6:
                            continue
                        code = digits[-6:]
                        m = re.match(r'^\s*\d+\s+\d{6}\s+(.+)$', s)
                        name = m.group(1).strip() if m else ''
                        # 2026-06-21 加固: 优先用 TDX 股票名索引
                        final_name = name_index.get(code) or name or blk_name
                        out[code] = final_name
                except Exception:
                    continue
            _aud('ztc_local', 'OK', count=len(out), path=str(ztc), mode='directory')
            return out
        else:
            # 单文件 (典型 ZTC.blk 格式 B: 7 位 = 市场码 + 6 位股票码)
            raw = ztc.read_text(encoding='gbk', errors='ignore')
            out = {}
            for line in raw.splitlines():
                s = line.strip()
                if not s:
                    continue
                digits = ''.join(ch for ch in s if ch.isdigit())
                if len(digits) < 6:
                    continue
                code = digits[-6:]
                m = re.match(r'^\s*\d+\s+\d{6}\s+(.+)$', s)
                name = m.group(1).strip() if m else ''
                # 2026-06-21 加固: 优先用 TDX 股票名索引
                final_name = name_index.get(code) or name or '涨停池'
                out[code] = final_name
            _aud('ztc_local', 'OK', count=len(out), path=str(ztc))
            return out
    except Exception as e:
        _fail(f'本地 ZTC 读取失败: {e}')
        _aud('ztc_local', 'FAIL', error=str(e))
        return {}


# ============================================================
# 数据源 2: akshare 当日涨停池
# ============================================================
def load_ak_zt_pool(trade_date: str) -> list[dict]:
    try:
        import akshare as ak
    except ImportError as e:
        _fail(f'akshare 未安装: {e}')
        _aud('ak_zt_pool', 'MISSING')
        return []
    try:
        # ak.stock_zt_pool_em expects YYYYMMDD; passing YYYY-MM-DD returns an
        # empty frame on this runtime and incorrectly degrades the workflow.
        df = ak.stock_zt_pool_em(date=trade_date)
    except Exception as e:
        _fail(f'ak.stock_zt_pool_em({trade_date}) 失败: {e}')
        _aud('ak_zt_pool', 'FAIL', error=str(e))
        return []
    if df is None or len(df) == 0:
        _fail(f'ak.stock_zt_pool_em({trade_date}) 返回空')
        _aud('ak_zt_pool', 'EMPTY')
        return []
    rows = []
    for _, r in df.iterrows():
        code = str(r.get('代码', '')).strip()
        if len(code) != 6 or not code.isdigit():
            continue
        rows.append({
            'code': code,
            'name': str(r.get('名称', '')).strip(),
            'pct_change': float(r.get('涨跌幅', 0) or 0),
            'price': float(r.get('最新价', 0) or 0),
            'amount': float(r.get('成交额', 0) or 0),
            'turnover': float(r.get('换手率', 0) or 0),
            'limit_capital': float(r.get('封板资金', 0) or 0),
            'first_limit_time': str(r.get('首次封板时间', '')).strip(),
            'last_limit_time': str(r.get('最后封板时间', '')).strip(),
            'break_count': int(r.get('炸板次数', 0) or 0),
            'limit_stat': str(r.get('涨停统计', '')).strip(),
            'board_count': int(r.get('连板数', 0) or 0),
            'industry': str(r.get('所属行业', '')).strip(),
        })
    _aud('ak_zt_pool', 'OK', count=len(rows), date=trade_date)
    return rows


# ============================================================
# 数据源 3: akshare 当日龙虎榜
# ============================================================
def load_ak_lhb(trade_date: str) -> list[dict]:
    try:
        import akshare as ak
    except ImportError:
        _aud('ak_lhb', 'MISSING')
        return []
    try:
        date_str = f'{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}'
        df = ak.stock_lhb_detail_daily_sina(date=date_str)
    except Exception as e:
        _fail(f'ak.stock_lhb_detail_daily_sina({trade_date}) 失败: {e}')
        _aud('ak_lhb', 'FAIL', error=str(e))
        return []
    if df is None or len(df) == 0:
        _aud('ak_lhb', 'EMPTY', note='T+1 未公布或已下架')
        return []
    rows = []
    for _, r in df.iterrows():
        code = str(r.get('股票代码', '')).strip()
        if len(code) != 6 or not code.isdigit():
            continue
        rows.append({
            'code': code,
            'name': str(r.get('股票名称', '')).strip(),
            'amount': float(r.get('成交额', 0) or 0),
        })
    _aud('ak_lhb', 'OK', count=len(rows), date=trade_date)
    return rows


# ============================================================
# K 线复算 (5.1.1 规则)
# ============================================================
def tdx_market_for_code(code: str) -> str:
    if code.startswith(('4', '8', '92')):
        return 'bj'
    return 'sh' if code.startswith(('5', '6', '9')) else 'sz'


def find_tdx_day_path(code: str) -> Path | None:
    market = tdx_market_for_code(code)
    fname = f'{market}{code}.day'
    for root in TDX_DAY_CANDIDATES:
        if market in str(root):
            p = root / fname
            if p.exists():
                return p
    # 尝试所有候选根
    p = TDX_ROOT / 'vipdoc' / market / 'lday' / fname
    if p.exists():
        return p
    return None


def read_tdx_day(path: Path) -> list[dict]:
    """读 TDX .day 文件, 返回 [(date, close, high, low), ...]"""
    import struct
    if not path or not path.exists():
        return []
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except Exception:
        return []
    records = []
    record_size = 32
    for i in range(0, len(data), record_size):
        chunk = data[i:i + record_size]
        if len(chunk) < record_size:
            break
        try:
            d_int, o, h, l, c, amount, vol = struct.unpack('<7I', chunk[:28])
            if d_int == 0:
                break
            year, month, day = d_int // 10000, (d_int // 100) % 100, d_int % 100
            try:
                from datetime import date as _date
                dt = _date(year, month, day)
            except Exception:
                continue
            records.append({'date': dt, 'open': o / 100, 'high': h / 100, 'low': l / 100, 'close': c / 100})
        except Exception:
            break
    return records


def k_line_limit_run(code: str, trade_date: str, threshold: float | None = None) -> tuple[str, int]:
    """用前收盘价复算连续涨停，且每个交易日都要求 HIGH==CLOSE。"""
    if code.startswith(('4', '8', '9', '200', '688')):
        return 'SKIP_EXCLUDED_BOARD', 0
    path = find_tdx_day_path(code)
    records = read_tdx_day(path) if path else []
    if not records:
        return 'MISSING', 0
    from datetime import datetime as _dt
    trade_dt = _dt.strptime(trade_date, '%Y-%m-%d').date()
    index = next((i for i, row in enumerate(records) if row['date'] == trade_dt), None)
    if index is None or index < 1:
        return 'MISSING', 0
    limit_threshold = threshold if threshold is not None else (19.8 if code.startswith('3') else 9.8)

    def is_limit_at(i: int) -> bool:
        if i < 1:
            return False
        row = records[i]
        previous_close = records[i - 1]['close']
        if previous_close <= 0:
            return False
        pct = (row['close'] - previous_close) / previous_close * 100
        closed_at_high = abs(row['high'] - row['close']) <= 0.011
        return pct >= limit_threshold and closed_at_high

    if not is_limit_at(index):
        return 'FAIL', 0
    count = 0
    cursor = index
    while cursor >= 1 and is_limit_at(cursor):
        count += 1
        cursor -= 1
    return 'PASS', count


def k_line_verify(code: str, trade_date: str, threshold: float | None = None,
                  mode: str = 'connected') -> str:
    status, count = k_line_limit_run(code, trade_date, threshold)
    if status != 'PASS':
        return status
    required = 2 if mode == 'connected' else 1
    return 'PASS' if count >= required else 'FAIL'


# ============================================================
# 8 因子评分 (简化版, 完整定义见 references/full_workflow.md)
# ============================================================
SCORE_FACTORS = {
    'board_ladder': {'weight': 15, 'desc': '连板梯队位置'},
    'limit_quality': {'weight': 20, 'desc': '封板质量'},
    'capital': {'weight': 15, 'desc': '资金承接'},
    'visibility': {'weight': 10, 'desc': '辨识度'},
    'sector_main': {'weight': 15, 'desc': '题材主线贴合'},
    'chip': {'weight': 10, 'desc': '筹码与流通盘'},
    'sentiment': {'weight': 10, 'desc': '市场情绪'},
    'executable': {'weight': 5, 'desc': '次日可执行性'},
}


def score_one(row: dict, lhb_codes: set, all_rows: list[dict]) -> dict:
    """对单只股票做 8 因子评分, 返回各因子分和总分"""
    scores = {}

    # 1. 连板梯队 (15)
    bc = row.get('board_count', 0)
    if bc >= 3:
        scores['board_ladder'] = 14
    elif bc >= 2:
        scores['board_ladder'] = 11
    else:
        scores['board_ladder'] = 6

    # 2. 封板质量 (20)
    fq = 20
    if row.get('break_count', 0) > 0:
        fq -= min(row['break_count'] * 3, 12)
    if not row.get('first_limit_time'):
        fq -= 3
    if not row.get('last_limit_time'):
        fq -= 2
    scores['limit_quality'] = max(0, fq)

    # 3. 资金承接 (15)
    cap = 15
    amount = row.get('amount', 0)
    turnover = row.get('turnover', 0)
    if amount < 1e8:
        cap -= 5
    elif amount > 10e8:
        cap -= 2
    if turnover < 1:
        cap -= 5
    elif turnover > 30:
        cap -= 3
    elif 5 <= turnover <= 15:
        cap += 0
    scores['capital'] = max(0, min(15, cap))

    # 4. 辨识度 (10)：只使用可验证的龙虎榜和真实名称，不给本地占位名加分。
    lhb_status = AUDIT.get('sources', {}).get('ak_lhb', {}).get('status')
    scores['visibility'] = 10 if row.get('code') in lhb_codes else (4 if lhb_status == 'OK' else 0)

    # 5. 题材主线贴合 (15)：无行业/题材证据即 0 分。
    industry = row.get('industry', '')
    if industry:
        same_industry = sum(1 for r in all_rows if r.get('industry') == industry)
        scores['sector_main'] = min(15, 5 + same_industry * 2)
    else:
        scores['sector_main'] = 0

    # 6. 筹码与流通盘 (10)：当前字段只支持换手代理；缺失不加分。
    scores['chip'] = 8 if 5 <= turnover <= 20 else (4 if turnover > 0 else 0)

    # 7. 市场情绪 (10)：用当日涨停池广度作可复算代理。
    breadth = len(all_rows)
    scores['sentiment'] = 10 if breadth >= 60 else (7 if breadth >= 30 else (4 if breadth >= 10 else 0))

    # 8. 次日可执行性 (5)
    ex = 5
    if row.get('limit_capital', 0) > 0 and amount > 0:
        if row['limit_capital'] / amount > 0.5:
            ex -= 2  # 一字板, 不易买入
    scores['executable'] = max(0, ex)

    scores['total'] = sum(scores[k] for k in SCORE_FACTORS.keys())
    return scores


# ============================================================
# 风险扫描 5.4.1 组合规则 (简化版)
# ============================================================
def risk_scan(row: dict) -> dict:
    """执行 A-E 组合规则；无风险证据时只能进入待复核观察池。"""
    flags = [flag for flag in row.get('risk_flags', []) if isinstance(flag, dict)]
    active_flags = [
        flag for flag in flags
        if flag.get('ongoing') is True or flag.get('within_5_trading_days') is True or flag.get('severity') == 'soft'
    ]
    hard = [flag for flag in active_flags if flag.get('severity') == 'hard']
    soft = [flag for flag in active_flags if flag.get('severity') == 'soft']
    # Rule B requires independent soft-risk events.  Multiple documents in the
    # same category on the same date are treated as one event cluster unless
    # the source has already supplied a distinct event_group identifier.
    independent_groups: dict[str, set[str]] = {}
    for flag in soft:
        category = str(flag.get('category') or 'unknown')
        event_key = str(
            flag.get('event_group')
            or flag.get('event_date')
            or flag.get('evidence_id')
            or flag.get('title')
            or 'unknown'
        )
        independent_groups.setdefault(category, set()).add(event_key)
    category_counts = {category: len(groups) for category, groups in independent_groups.items()}
    same_category_upgrade = any(count >= 2 for count in category_counts.values())
    cross_category_penalty = len(category_counts) >= 3
    if hard:
        action, combo = 'OUT', 'A'
    elif same_category_upgrade:
        action, combo = 'OUT', 'B'
    elif cross_category_penalty:
        action, combo = 'DOWNGRADE', 'C'
    elif not active_flags and row.get('risk_review_complete') is True:
        action, combo = 'PASS', 'PASS'
    elif not active_flags:
        action, combo = 'REVIEW_REQUIRED', 'UNVERIFIED'
    else:
        action, combo = 'PASS', 'PASS'
    return {
        'trigger_combo': combo,
        'final_action': action,
        'risk_flags': active_flags,
        'context_flags': [flag for flag in flags if flag not in active_flags],
        'independent_soft_event_counts': category_counts,
        'score_penalty': 10 if cross_category_penalty else 0,
        'manual_override': row.get('manual_override'),
        'note': '人工覆盖只留审计痕迹，不能删除原风险。' if row.get('manual_override') else '',
    }


def load_risk_evidence(path_text: str | None) -> dict[str, dict]:
    """读取按股票代码绑定的风险证据；缺少文件时只允许待复核观察池。"""
    if not path_text:
        return {}
    path = Path(path_text).expanduser().resolve()
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('risk JSON root must be an object keyed by 6-digit stock code')
    normalized: dict[str, dict] = {}
    for code, item in payload.items():
        if not re.fullmatch(r'\d{6}', str(code)) or not isinstance(item, dict):
            raise ValueError(f'invalid risk evidence item: {code!r}')
        flags = item.get('risk_flags', [])
        if not isinstance(flags, list):
            raise ValueError(f'risk_flags must be a list: {code}')
        if item.get('review_complete') is not True:
            raise ValueError(f'review_complete=true is required for bound risk evidence: {code}')
        for flag in flags:
            if not isinstance(flag, dict) or flag.get('severity') not in ('hard', 'soft') or not flag.get('category') or not flag.get('evidence_id'):
                raise ValueError(f'invalid risk flag schema: {code}')
            if flag.get('severity') == 'hard' and flag.get('within_5_trading_days') is not True and flag.get('ongoing') is not True:
                flag['usage'] = 'historical_context_only'
        normalized[str(code)] = {
            'risk_flags': flags,
            'manual_override': item.get('manual_override'),
            'risk_review_complete': True,
        }
    return normalized


# ============================================================
# 输出
# ============================================================
def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_report_md(path: Path, scored: list, pool: list, trade_date: str, min_total_score: int = 70) -> None:
    # 2026-06-21 加固 v2: 自动生成简化结论（不再依赖主控 prompt 补全）
    # 基于现有数据: 涨幅 / 连板梯队 / K 线复算 / 板块分类 → 直接写结论/晋级逻辑/风险/观察点
    # 不替代主控 prompt 深度分析，但保证报告非空洞
    eligible = [
        item for item in scored
        if item['scores']['total'] >= min_total_score and item['risk']['final_action'] == 'PASS'
    ][:5]
    lines = [
        f'# 连板龙头研究报告 ({trade_date})',
        '',
        f'**生成时间**: {_now_iso()}',
        '**类型**: 盘后研究输出 (不构成买卖建议)',
        '**数据通道**: 本地 TDX + akshare (3 个数据源)',
        '',
        f'## 候选池概况',
        f'- 总候选 (2 连板+): {len(pool)} 只',
        f'- 正式 Top 5 (≥{min_total_score} 分且风险证据通过): {len(eligible)} 只',
        f'- 数据源状态: {sum(1 for v in AUDIT["sources"].values() if v.get("status") == "OK")} OK',
        '',
        '## Top 5 龙头候选',
        '',
    ]
    if not eligible:
        lines += ['当前没有同时满足分数、K 线和风险证据闭环的正式候选。', '']
    for s in eligible:
        r = s['row']
        sc = s['scores']
        code = r.get('code', '?')
        name = r.get('name', '?')
        board_count = r.get('board_count', 0)
        k_verify = r.get('k_line_verify')
        if not k_verify:
            raise RuntimeError(f"k_line_verify missing for {code}; refuse to generate candidate conclusion")
        industry = r.get('industry', '') or '未提供行业证据'

        # === 2026-06-21 自动生成结论 ===
        # 1. 结论
        tier = '研究候选'
        conclusion = f'{tier}（{sc["total"]} 分），连板 {board_count}，K 线复算 {k_verify}。'

        # 2. 晋级逻辑
        ladder_str = '梯队前排 (≥3 板)' if board_count >= 3 else ('梯队中排 (2 板)' if board_count >= 2 else '梯队后补 (1 板)')
        ladder_logic = (
            f'连板梯队 {ladder_str} (得分 {sc["board_ladder"]}/15)；'
            f'封板质量 {sc["limit_quality"]}/20 (炸板 {r.get("break_count", 0)} 次)；'
            f'资金承接 {sc["capital"]}/15'
        )

        # 3. 证据
        evidence_id = r.get('evidence_id', f'local_ztc#{code}')
        k_label = {
            'PASS': '本地 TDX K 线验证通过',
            'FAIL': '本地 TDX K 线验证未通过 (单日涨幅未达阈值或连板断裂)',
            'MISSING': '本地 TDX K 线数据缺失',
            'SKIP_EXCLUDED_BOARD': '北交所/科创板等排除市场',
        }.get(k_verify, 'UNSUPPORTED_K_VERIFY_STATUS')
        if k_label == 'UNSUPPORTED_K_VERIFY_STATUS':
            raise RuntimeError(f"unsupported k_line_verify={k_verify} for {code}")
        evidence = f'证据编号: `{evidence_id}`；TDX 板块: {industry}；K 线复算: {k_label}'

        # 4. 风险
        risks = []
        if k_verify == 'FAIL':
            risks.append('K 线复算 FAIL — 单日涨幅未达 9.50%/19.50% 阈值, 出局风险高')
        if sc.get('capital', 0) < 8:
            risks.append('资金承接维度低分或字段不足')
        if r.get('industry', '') == '':
            risks.append('无行业/题材归属证据')
        if board_count >= 3:
            risks.append('梯队位置前排 — 注意次日分歧风险, 高标容易炸板')
        if not risks:
            risks.append('未发现已编码风险，但仍需核对公告、监管和减持/解禁证据')

        # 5. 观察点
        watchpoints = [
            f'次日 9:25 集合竞价 — 看是否有高开溢价 / 低开核按钮',
            f'9:30-10:30 板块联动 — 看 {name} 是否带领同板块股票上涨',
            f'10:30 后封板稳定性 — 看是否出现炸板回封',
            f'14:30 后资金承接 — 看尾盘是否有资金博弈',
        ]

        lines += [
            f'### #{s.get("rank", "?")} {name} ({code})',
            '',
            f'**总分**: {sc["total"]} / 100 (连板梯队 {sc["board_ladder"]}/15 + 封板质量 {sc["limit_quality"]}/20 + 资金承接 {sc["capital"]}/15 + 辨识度 {sc["visibility"]}/10 + 题材主线 {sc["sector_main"]}/15 + 筹码 {sc["chip"]}/10 + 情绪 {sc["sentiment"]}/10 + 次日可执行 {sc["executable"]}/5)',
            f'**连板数**: {board_count}',
            f'**封板资金**: {r.get("limit_capital", 0):,.0f}',
            f'**首次封板**: {r.get("first_limit_time", "") or "(字段缺失)"}',
            f'**最后封板**: {r.get("last_limit_time", "") or "(字段缺失)"}',
            f'**炸板次数**: {r.get("break_count", 0)}',
            f'**K 线复算**: {k_verify}',
            f'**所属行业**: {industry}',
            '',
            f'**结论**: {conclusion}',
            f'**晋级逻辑**: {ladder_logic}',
            f'**证据**: {evidence}',
            f'**风险**:',
        ]
        for rk in risks:
            lines.append(f'  - {rk}')
        lines += ['**观察点**:']
        for wp in watchpoints:
            lines.append(f'  - {wp}')
        lines.append('')
    lines += [
        '## 风险与缺失声明',
        '',
        '- 本报告仅用于复盘研究, 不构成股票推荐或买卖依据',
        '- 龙虎榜未按交易日真实返回时不计辨识度加分',
        '- ZTC 只用于本地涨停池交叉核验，不能替代板数、封板和资金字段',
        '- 风险证据未闭环的标的仅列观察池，不进入正式 Top 5',
        '- 任何数据缺失已写入 audit_log.md',
        '- Top 5 仅作为研究线索, 须结合盘面竞价/封单/同题材助攻综合判断',
        '',
    ]
    path.write_text('\n'.join(lines), encoding='utf-8')


# ============================================================
# 长期运行集成 (调用本 skill 本地 scripts)
# ============================================================
def call_infra_script(script_name: str, *args: str) -> dict:
    """调用长期运行配套脚本, 返回 {returncode, stdout, stderr}"""
    script_path = INFRA_SCRIPTS / script_name
    if not script_path.exists():
        return {'returncode': -1, 'stdout': '', 'stderr': f'script not found: {script_path}'}
    try:
        r = subprocess.run(
            [sys.executable, str(script_path), *args],
            capture_output=True, text=True, timeout=30, encoding='utf-8'
        )
        return {
            'returncode': r.returncode,
            'stdout': r.stdout.strip(),
            'stderr': r.stderr.strip(),
        }
    except Exception as e:
        return {'returncode': -1, 'stdout': '', 'stderr': str(e)}


# ============================================================
# 主流程
# ============================================================
def main() -> int:
    import os
    ap = argparse.ArgumentParser(description='连板挖掘严格研究模式 (强制手动)')
    ap.add_argument('--date', default=None,
                    help='交易日 YYYYMMDD (默认读取本地 TDX 最新交易日)')
    ap.add_argument('--out', default=None,
                    help='输出目录 (默认 ~/.codex/reports/{date}_lianban_mining_research)')
    ap.add_argument('--manual-confirm', action='store_true',
                    help='强制手动触发确认 (没有此参数脚本拒绝执行)')
    ap.add_argument('--skip-infra', action='store_true',
                    help='跳过本地长期运行配套脚本调用 (仅用于故障排查, 主流程审计仍写入 audit_log)')
    ap.add_argument('--diagnostic', action='store_true', help='允许 limit 单日验证；诊断输出不得视为正式连板结论')
    ap.add_argument('--min-total-score', type=int, default=70,
                    help='研究 Top 5 进入阈值 (默认 70；不得因数据缺失降低)')
    ap.add_argument('--k-line-mode', choices=['limit', 'connected'], default='connected',
                    help='K 线复算: connected=严格连板(默认)，limit=仅调试当日涨停')
    ap.add_argument('--risk-json', help='按 6 位代码绑定 risk_flags/manual_override 的 JSON；缺失时仅输出待复核观察池')
    args = ap.parse_args()
    try:
        args.date = args.date or resolve_latest_trade_date()
    except RuntimeError as exc:
        print(f'无法确定交易日: {exc}', file=sys.stderr)
        return 2
    AUDIT['date'] = args.date
    AUDIT['min_total_score'] = args.min_total_score
    AUDIT['k_line_mode'] = args.k_line_mode
    if args.min_total_score < 70:
        print('正式研究阈值不得低于 70 分', file=sys.stderr)
        return 2
    if args.k_line_mode != 'connected' and not args.diagnostic:
        print('正式研究必须使用 connected；limit 仅可与 --diagnostic 同时使用', file=sys.stderr)
        return 2

    # 硬闸 1: 必须 --manual-confirm
    if not args.manual_confirm:
        print('=' * 70, file=sys.stderr)
        print('⛔ 拒绝执行: 缺少 --manual-confirm 参数', file=sys.stderr)
        print('', file=sys.stderr)
        print('本脚本是 Codex 手动盘后工作流, 禁止任何自动触发:', file=sys.stderr)
        print('  - Windows 计划任务', file=sys.stderr)
        print('  - Codex 定时任务 / 后台轮询', file=sys.stderr)
        print('  - 子代理自动调用', file=sys.stderr)
        print('  - 任何脚本自动化', file=sys.stderr)
        print('', file=sys.stderr)
        print('正确用法: 在 Codex 主会话中手动输入', file=sys.stderr)
        print(f'  python run.py --date {args.date} --manual-confirm', file=sys.stderr)
        print('=' * 70, file=sys.stderr)
        return 1

    # 硬闸 2-4: 时间 + 环境
    ok, reason = _gate_manual_only()
    AUDIT['gate_status']['manual_gate'] = {'ok': ok, 'reason': reason}
    if not ok:
        print('=' * 70, file=sys.stderr)
        print('⛔ 拒绝执行:', reason, file=sys.stderr)
        print('', file=sys.stderr)
        print('本脚本必须手动在 15:05 之后从 Codex 主会话执行.', file=sys.stderr)
        print('=' * 70, file=sys.stderr)
        return 1

    # 长期运行: health_monitor start
    if not args.skip_infra:
        result = call_infra_script('health_monitor.py', 'start',
                                   '--workflow', 'lianban-mining-research',
                                   '--trade-date', args.date[:4] + '-' + args.date[4:6] + '-' + args.date[6:8],
                                   '--run-id', '01')
        AUDIT.setdefault('infra', {})['health_monitor_start'] = result

    out_dir = Path(args.out) if args.out else REPORTS / f'{args.date}_lianban_mining_research'
    out_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: 加载本地 ZTC
    print(f'[1/4] 加载本地 TDX ZTC ...')
    ztc_local = load_ztc_local()

    # Step 2: akshare 涨停池
    print(f'[2/4] 加载 akshare 当日涨停池 ({args.date}) ...')
    ak_rows = load_ak_zt_pool(args.date)

    # Step 3: 龙虎榜
    print(f'[3/4] 加载 akshare 当日龙虎榜 ({args.date}) ...')
    lhb_rows = load_ak_lhb(args.date)
    lhb_codes = {r['code'] for r in lhb_rows}

    # AK supplies the dated board-count/limit-up fields. ZTC is only a passive
    # local cross-check and must never erase a valid dated AK pool.
    if not ak_rows:
        _fail('当日涨停池字段源不可用；ZTC 不含板数/封板/资金字段，禁止伪造二连板后评分')
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / 'source_failure.json').write_text(json.dumps(AUDIT, ensure_ascii=False, indent=2), encoding='utf-8')
        print('数据源未提供等价字段，已阻断正式研究输出；修复数据源后重跑。', file=sys.stderr)
        return 2
    ak_rows = reconcile_ztc_with_ak(ztc_local, ak_rows)
    try:
        risk_evidence = load_risk_evidence(args.risk_json)
    except Exception as exc:
        _fail(f'风险证据文件无效: {exc}')
        (out_dir / 'source_failure.json').write_text(json.dumps(AUDIT, ensure_ascii=False, indent=2), encoding='utf-8')
        return 2
    _aud('risk_evidence', 'OK' if risk_evidence else 'UNVERIFIED', count=len(risk_evidence))
    for row in ak_rows:
        bound = risk_evidence.get(row['code'], {})
        row['risk_flags'] = bound.get('risk_flags', [])
        row['manual_override'] = bound.get('manual_override')
        row['risk_review_complete'] = bound.get('risk_review_complete', False)

    # Step 4: K 线复算 + 评分 + 输出
    print(f'[4/4] K 线复算 + 8 因子评分 + 输出 ...')
    trade_date_iso = f'{args.date[:4]}-{args.date[4:6]}-{args.date[6:8]}'

    pool = []
    for r in ak_rows:
        upper_name = str(r.get('name', '')).upper()
        if r['code'].startswith(('4', '8', '9', '200', '688')) or 'ST' in upper_name or '退' in upper_name:
            continue
        # 只保留 2 连板及以上
        if r['board_count'] < 2:
            continue
        # K 线复算
        r['k_line_verify'] = k_line_verify(r['code'], trade_date_iso, mode=args.k_line_mode)
        r['evidence_id'] = f"raw_zt_pool.csv#code_{r['code']}"
        if r['k_line_verify'] == 'FAIL':
            continue  # 5.1.1 规则: FAIL 的票必须出局
        if r['k_line_verify'] == 'MISSING':
            _fallback(f"剔除 {r['code']}: 本地 TDX K线数据缺失，不能进入候选结论")
            continue
        pool.append(r)

    # 评分
    scored = []
    for idx, r in enumerate(pool, 1):
        s = score_one(r, lhb_codes, ak_rows)
        rk = risk_scan(r)
        s['total'] = max(0, s['total'] - int(rk.get('score_penalty', 0)))
        scored.append({
            'rank': idx,
            'row': r,
            'scores': s,
            'risk': rk,
        })
    scored.sort(key=lambda x: -x['scores']['total'])
    for final_rank, item in enumerate(scored, 1):
        item['rank'] = final_rank

    # 输出 4 件套
    candidate_fields = ['evidence_id', 'code', 'name', 'board_count', 'first_limit_time',
                        'last_limit_time', 'break_count', 'limit_stat', 'amount', 'turnover',
                        'limit_capital', 'industry', 'k_line_verify']
    write_csv(out_dir / 'candidate_pool.csv', pool, candidate_fields)

    score_rows = []
    for s in scored:
        sc = s['scores']
        r = s['row']
        score_rows.append({
            'evidence_id': r['evidence_id'],
            'rank': s['rank'],
            'code': r['code'],
            'name': r['name'],
            'board_count': r['board_count'],
            'first_limit_time': r['first_limit_time'],
            'board_ladder': sc['board_ladder'],
            'limit_quality': sc['limit_quality'],
            'capital': sc['capital'],
            'visibility': sc['visibility'],
            'sector_main': sc['sector_main'],
            'chip': sc['chip'],
            'sentiment': sc['sentiment'],
            'executable': sc['executable'],
            'total': sc['total'],
            'industry': r['industry'],
            'k_line_verify': r.get('k_line_verify', ''),
            'risk_combo': s['risk']['trigger_combo'],
            'risk_action': s['risk']['final_action'],
        })
    score_fields = ['evidence_id', 'rank', 'code', 'name', 'board_count', 'first_limit_time',
                    'board_ladder', 'limit_quality', 'capital', 'visibility', 'sector_main',
                    'chip', 'sentiment', 'executable', 'total', 'industry', 'k_line_verify',
                    'risk_combo', 'risk_action']
    write_csv(out_dir / 'dragon_score.csv', score_rows, score_fields)

    write_report_md(out_dir / 'report.md', scored, pool, args.date, min_total_score=args.min_total_score)

    # audit_log
    AUDIT['output_dir'] = str(out_dir)
    AUDIT['candidates'] = len(pool)
    AUDIT['top5_count'] = sum(
        1 for s in scored
        if s['scores']['total'] >= args.min_total_score and s['risk']['final_action'] == 'PASS'
    )
    (out_dir / 'audit_log.md').write_text(
        f'# Audit Log ({args.date})\n\n```json\n{json.dumps(AUDIT, ensure_ascii=False, indent=2)}\n```\n',
        encoding='utf-8'
    )

    # 长期运行: health_monitor finish + record
    if not args.skip_infra:
        iso_date = args.date[:4] + '-' + args.date[4:6] + '-' + args.date[6:8]
        # record steps_completed
        for step in ['candidate_pool_1', 'candidate_pool_2', 'candidate_pool_3', 'risk_scan']:
            r = call_infra_script('health_monitor.py', 'record',
                                  '--trade-date', iso_date, '--workflow', 'lianban-mining-research',
                                  '--run-id', '01', '--section', 'steps_completed',
                                  '--key', step, '--value', 'true')
            AUDIT.setdefault('infra', {})[f'health_monitor_record_{step}'] = r

        # finish
        status = 'healthy' if not AUDIT['failures'] else 'degraded'
        r = call_infra_script('health_monitor.py', 'finish',
                              '--trade-date', iso_date, '--workflow', 'lianban-mining-research',
                              '--run-id', '01', '--status', status)
        AUDIT['infra']['health_monitor_finish'] = r

        # archive_prediction 落盘快照
        manifest = {
            'trade_date': iso_date,
            'workflow': 'lianban-mining-research',
            'workflow_version': 'v2.0.0',
            'run_id': '01',
            'operator': 'codex',
            'evidence_dir': str(out_dir),
            'market_context': {},
            'data_sources_used': [k for k, v in AUDIT['sources'].items() if v.get('status') == 'OK'],
            'data_sources_failed': [k for k, v in AUDIT['sources'].items() if v.get('status') in ('FAIL', 'MISSING', 'EMPTY')],
            'anti_hallucination_ah1_ah2_ah3': True,
            'candidates': [
                {
                    'rank': s['rank'],
                    'type': 'stock',
                    'code': s['row']['code'],
                    'name': s['row']['name'],
                    'score': s['scores']['total'],
                    'predicted_window': 'T+1~3',
                    'predicted_action': 'research_watch',
                }
                for s in scored
                if s['scores']['total'] >= args.min_total_score and s['risk']['final_action'] == 'PASS'
            ],
        }
        manifest_path = out_dir / 'run_manifest.json'
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

        r = call_infra_script('archive_prediction.py', '--from-manifest', str(manifest_path))
        AUDIT['infra']['archive_prediction'] = r

        # 重新写 audit_log 包含 infra 调用结果
        (out_dir / 'audit_log.md').write_text(
            f'# Audit Log ({args.date})\n\n```json\n{json.dumps(AUDIT, ensure_ascii=False, indent=2)}\n```\n',
            encoding='utf-8'
        )

    print('\n=== DIAGNOSTIC_ONLY ===' if args.diagnostic else '\n=== 完成 ===')
    print(f'输出目录: {out_dir}')
    print(f'候选池: {len(pool)} 只 2 连板+')
    print(f'Top 5 (≥{AUDIT.get("min_total_score", 70)} 分): {AUDIT["top5_count"]} 只')
    print(f'数据源状态: {len([v for v in AUDIT["sources"].values() if v.get("status") == "OK"])} OK / {len(AUDIT["failures"])} 失败')
    print(f'长期运行: {"已调用" if not args.skip_infra else "已跳过 (--skip-infra)"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
