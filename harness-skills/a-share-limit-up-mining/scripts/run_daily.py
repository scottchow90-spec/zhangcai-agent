#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_daily.py — 连板挖掘每日盘后快筛模式

数据源 (只 3 个):
  1. C:\\new_tdx_mock\\T0002\\blocknew\\ZTC.blk      本地涨停池 (主源)
  2. akshare.stock_zt_pool_em(date)        当日涨停池 (双源校验 + 字段补充)
  3. akshare.stock_lhb_detail_daily_sina(date)  当日龙虎榜 (资金验证)

输出:
  candidate_pool.csv / dragon_score.csv / report.md / audit_log.md

执行:
  python codex_entry.py run -- --mode daily --date YYYYMMDD --manual-confirm
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
import sys
import warnings
from datetime import datetime
from pathlib import Path

from _date_utils import resolve_latest_trade_date

warnings.filterwarnings('ignore')

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

WORKSPACE = Path(r'D:\C盘转移\日志\codex')
REPORTS = WORKSPACE / 'reports'
ZTC = Path(r'C:\new_tdx_mock\T0002\blocknew\ZTC.blk')

AUDIT = {
    'generated_at': datetime.now().astimezone().isoformat(timespec='seconds'),
    'date': None,
    'sources': {},
    'failures': [],
    'fallback_used': [],
}


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec='seconds')


def _aud(name: str, status: str, **extra) -> None:
    AUDIT['sources'][name] = {'status': status, 'checked_at': _now_iso(), **extra}


def _fail(msg: str) -> None:
    AUDIT['failures'].append({'time': _now_iso(), 'message': msg})


def _fallback(msg: str) -> None:
    AUDIT['fallback_used'].append({'time': _now_iso(), 'message': msg})


# ============================================================
# 数据源 1: 本地 ZTC.blk (涨停池主源)
# ============================================================
def load_ztc_local() -> dict[str, str]:
    """返回 {code: name} 字典, code 6 位."""
    if not ZTC.exists():
        _fail(f'ZTC.blk 不存在: {ZTC}')
        _aud('ztc_local', 'MISSING', path=str(ZTC))
        return {}
    try:
        raw = ZTC.read_text(encoding='gbk', errors='ignore')
    except Exception as e:
        _fail(f'ZTC.blk 读取失败: {e}')
        _aud('ztc_local', 'FAIL', error=str(e))
        return {}
    out = {}
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        digits = ''.join(ch for ch in s if ch.isdigit())
        if len(digits) < 6:
            continue
        code = digits[-6:]
        # 行格式: "1 002938 和远气体" — name 是数字后面那段
        m = re.match(r'^\s*\d+\s+\d{6}\s+(.+)$', s)
        name = m.group(1).strip() if m else ''
        out[code] = name
    _aud('ztc_local', 'OK', count=len(out), updated_at=ZTC.stat().st_mtime if ZTC.exists() else None)
    return out


# ============================================================
# 数据源 2: akshare 当日涨停池
# ============================================================
def load_ak_zt_pool(trade_date: str) -> list[dict]:
    """返回当日涨停池行列表, 每行 dict (含连板数/封板时间/炸板/换手率/成交额/封板资金)."""
    try:
        import akshare as ak
    except ImportError as e:
        _fail(f'akshare 未安装: {e}')
        _aud('ak_zt_pool', 'MISSING')
        return []
    try:
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
        if len(code) < 6:
            continue
        code6 = code[-6:]
        rows.append({
            'code': code6,
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
    """返回当日龙虎榜行."""
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
        _fail(f'龙虎榜未公布或返回空 ({trade_date})')
        _aud('ak_lhb', 'EMPTY')
        return []
    rows = []
    for _, r in df.iterrows():
        code = str(r.get('股票代码', '')).strip()
        if len(code) < 6:
            continue
        rows.append({
            'code': code[-6:],
            'name': str(r.get('股票名称', '')).strip(),
            'amount': float(r.get('成交额', 0) or 0),
            'indicator': str(r.get('指标', '')).strip(),
        })
    _aud('ak_lhb', 'OK', count=len(rows), date=trade_date)
    return rows


# ============================================================
# 候选池: 2 连板以上
# ============================================================
def build_candidate_pool(ak_rows: list[dict], local_codes: set[str]) -> list[dict]:
    """从双源交集筛真实 2 连板以上，按连板数倒序。"""
    pool = []
    for r in ak_rows:
        name_upper = str(r.get('name', '')).upper()
        excluded = r['code'].startswith(('4', '8', '9', '200', '688')) or 'ST' in name_upper or '退' in name_upper
        if r['board_count'] >= 2 and r['code'] in local_codes and not excluded:
            r['mechanism'] = '20cm' if r['code'].startswith('3') else '10cm'
            r['evidence_id'] = f'{AUDIT.get("date")}:ak_zt_pool+ztc#{r["code"]}'
            pool.append(r)
    pool.sort(key=lambda x: (x['mechanism'], -x['board_count'], x['first_limit_time']))
    return pool


# ============================================================
# 5 维评分 (满分 100, 全部本地计算, 不调外部)
# ============================================================
def score_one(r: dict, lhb_codes: set, all_rows: list[dict]) -> dict:
    """5 维评分: 连板梯队 25 + 封板质量 25 + 资金承接 20 + 板块确认 20 + 辨识度 10."""
    s = {}

    # 1. 连板梯队 25 分
    bc = r['board_count']
    if bc >= 4: s['board_ladder'] = 25
    elif bc == 3: s['board_ladder'] = 20
    elif bc == 2: s['board_ladder'] = 15
    else: s['board_ladder'] = 5

    # 2. 封板质量 25 分
    first = ''.join(ch for ch in str(r['first_limit_time']) if ch.isdigit()).ljust(6, '9')[:6]
    brk = r['break_count']
    if first <= '093500' and brk == 0:
        s['limit_quality'] = 25
    elif first <= '103000' and brk <= 1:
        s['limit_quality'] = 18
    elif brk <= 2:
        s['limit_quality'] = 10
    else:
        s['limit_quality'] = 4

    # 3. 资金承接 20 分 (成交额 1-5 亿 + 换手率 5-15% 为佳)
    amount_yi = r['amount'] / 1e8  # 亿
    turnover = r['turnover']
    if 1 <= amount_yi <= 5 and 5 <= turnover <= 15:
        s['capital'] = 20
    elif 0.5 <= amount_yi <= 10 and 3 <= turnover <= 25:
        s['capital'] = 14
    elif amount_yi < 0.5 or turnover < 2:
        s['capital'] = 6
    else:
        s['capital'] = 10

    # 4. 板块确认 20 分 (同行业涨停数)
    same_industry_count = sum(1 for x in all_rows if x['industry'] == r['industry'] and x['industry'])
    if same_industry_count >= 3:
        s['sector'] = 20
    elif same_industry_count == 2:
        s['sector'] = 12
    elif same_industry_count == 1:
        s['sector'] = 6
    else:
        s['sector'] = 0

    # 5. 辨识度 10 分 (是否在龙虎榜)
    lhb_status = AUDIT.get('sources', {}).get('ak_lhb', {}).get('status')
    if r['code'] in lhb_codes:
        s['visibility'] = 10
    elif lhb_status == 'OK':
        s['visibility'] = 4
    else:
        s['visibility'] = 0

    total = sum(s.values())
    s['total'] = total
    return s


# ============================================================
# CSV / Markdown 输出
# ============================================================
def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in fields})


def write_report_md(path: Path, scored: list[dict], pool: list[dict], trade_date: str) -> None:
    """Top 5 龙头 + 风险 + 缺失声明."""
    top5 = [s for s in scored if s.get('total', 0) >= 70][:5]
    lines = [
        f'# 每日连板龙头选股报告 ({trade_date})',
        '',
        f'> 生成时间: {_now_iso()}',
        f'> 数据源: ZTC.blk (本地) + akshare 当日数据',
        f'> 候选池: {len(pool)} 只 2 连板及以上 | Top 5 (≥70 分): {len(top5)} 只',
        '',
        '## 核心摘要',
        '',
    ]
    if not top5:
        lines += ['⚠️ 当日无 Top 5 龙头 (无 ≥70 分候选). 可能原因: 市场情绪差 / 涨停稀少 / 数据缺失.', '']
    else:
        for i, s in enumerate(top5, 1):
            r = s['row']
            lines.append(f'{i}. **{r["code"]} {r["name"]}** — {r["mechanism"]}/{r["board_count"]}板, 总分 **{s["total"]}**, 首封 {r["first_limit_time"]}, 行业: {r["industry"]}')

    lines += ['', '## Top 5 龙头明细', '']
    if top5:
        lines += ['| # | 代码 | 名称 | 机制 | 板数 | 首封 | 炸板 | 成交亿 | 换手% | 行业 | 梯队 | 封板 | 资金 | 板块 | 辨识 | **总分** |', '|---:|---|---|---|---:|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|']
        for i, s in enumerate(top5, 1):
            r = s['row']
            sc = s['scores']
            lines.append(f'| {i} | {r["code"]} | {r["name"]} | {r["mechanism"]} | {r["board_count"]} | {r["first_limit_time"]} | {r["break_count"]} | {r["amount"]/1e8:.2f} | {r["turnover"]:.1f} | {r["industry"]} | {sc["board_ladder"]} | {sc["limit_quality"]} | {sc["capital"]} | {sc["sector"]} | {sc["visibility"]} | **{s["total"]}** |')

    lines += ['', '## 风险与缺失声明', '']
    lines += ['- 本报告仅用于复盘研究, 不构成股票推荐或买卖依据.']
    lines += ['- 龙虎榜未按交易日真实返回时不计辨识度加分.']
    lines += ['- 任何数据缺失已写入 audit_log.md.']
    lines += ['- Top 5 仅作为研究线索, 须结合盘面竞价/封单/同题材助攻综合判断.']
    lines += ['']
    path.write_text('\n'.join(lines), encoding='utf-8')


# ============================================================
# 主流程
# ============================================================
def _gate_manual_only(
    trade_date: str,
    *,
    now: datetime | None = None,
) -> tuple[bool, str]:
    """
    硬闸: 强制手动触发, 禁止计划任务/后台轮询自动跑.
    检查项:
      1. 必须显式 --manual-confirm 参数
      2. 当日交易日必须 >= 15:05 (盘后); 历史交易日不受当前时钟限制
      3. 没有 CODEX_AUTOMATION_RUN 自动任务标记
      4. 没有 CODEX_BACKGROUND_RUN 后台任务标记
    返回 (ok, reason).
    """
    now = now or datetime.now()
    hhmm = now.strftime('%H%M')
    current_date = now.strftime('%Y%m%d')
    if trade_date > current_date:
        return False, f'交易日 {trade_date} 晚于当前日期 {current_date}, 禁止运行.'
    # 时间闸只约束当日正式结论；历史交易日已经完成收盘。
    if trade_date == current_date and int(hhmm) < 1505:
        return False, f'当前时间 {hhmm} < 15:05, 不允许盘前/盘中运行. 盘后手动执行即可.'
    # 环境闸: cron 自动触发标记
    if os.environ.get('CODEX_AUTOMATION_RUN') == '1':
        return False, '检测到 CODEX_AUTOMATION_RUN=1, 自动任务不得执行本流程.'
    if os.environ.get('CODEX_BACKGROUND_RUN') == '1':
        return False, '检测到 CODEX_BACKGROUND_RUN=1, 后台任务不得执行本流程.'
    # 参数闸: 必须有 --manual-confirm
    return True, 'OK'


def main() -> int:
    import os
    ap = argparse.ArgumentParser(description='连板挖掘每日盘后快筛 (强制手动)')
    ap.add_argument('--date', default=None,
                    help='交易日 YYYYMMDD (默认读取本地 TDX 最新交易日)')
    ap.add_argument('--out', default=None, help='输出目录 (默认 ~/.codex/reports/{date}_lianban_mining_daily)')
    ap.add_argument('--manual-confirm', action='store_true',
                    help='强制手动触发确认 (没有此参数脚本拒绝执行, 禁止任何自动/计划任务/后台触发)')
    args = ap.parse_args()
    try:
        args.date = args.date or resolve_latest_trade_date()
    except RuntimeError as exc:
        print(f'无法确定交易日: {exc}', file=sys.stderr)
        return 2
    AUDIT['date'] = args.date

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
    ok, reason = _gate_manual_only(args.date)
    if not ok:
        print('=' * 70, file=sys.stderr)
        print('⛔ 拒绝执行:', reason, file=sys.stderr)
        print('', file=sys.stderr)
        print('当日交易日必须在 15:05 之后手动执行；历史交易日仍受人工与后台标记闸门约束.', file=sys.stderr)
        print('=' * 70, file=sys.stderr)
        return 1

    out_dir = Path(args.out) if args.out else REPORTS / f'{args.date}_lianban_mining_daily'
    out_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: 加载数据
    print(f'[1/4] 加载本地 ZTC.blk ...')
    ztc_local = load_ztc_local()

    print(f'[2/4] 加载 akshare 当日涨停池 ({args.date}) ...')
    ak_rows = load_ak_zt_pool(args.date)

    print(f'[3/4] 加载 akshare 当日龙虎榜 ({args.date}) ...')
    lhb_rows = load_ak_lhb(args.date)
    lhb_codes = {r['code'] for r in lhb_rows}

    # 两个关键源必须真实成功；ZTC 不包含完整评分字段，不能伪造二连板兜底。
    if not ztc_local or not ak_rows:
        if not ztc_local:
            _fail('本地 ZTC 为空或不可读')
        if not ak_rows:
            _fail('当日涨停池字段源不可用，禁止用 ZTC 默认二连板并补零评分')
        (out_dir / 'source_failure.json').write_text(json.dumps(AUDIT, ensure_ascii=False, indent=2), encoding='utf-8')
        print('关键数据源未真实成功，已阻断正式 Top5；修复数据源后重跑。', file=sys.stderr)
        return 2

    # Step 2: 构建候选池
    print(f'[4/4] 评分 + 输出 ...')
    pool = build_candidate_pool(ak_rows, set(ztc_local))

    # Step 3: 评分
    scored = []
    for r in pool:
        s = score_one(r, lhb_codes, ak_rows)
        scored.append({'row': r, 'scores': s, 'total': s['total']})
    scored.sort(key=lambda x: (-x['total'], x['row']['mechanism']))
    mechanism_positions: dict[str, int] = {}
    for item in scored:
        mechanism = item['row']['mechanism']
        mechanism_positions[mechanism] = mechanism_positions.get(mechanism, 0) + 1
        item['mechanism_rank'] = mechanism_positions[mechanism]

    # Step 4: 写产物
    candidate_fields = ['evidence_id', 'code', 'name', 'board_count', 'first_limit_time',
                        'last_limit_time', 'break_count', 'limit_stat', 'amount', 'turnover',
                        'limit_capital', 'industry', 'mechanism']
    write_csv(out_dir / 'candidate_pool.csv', pool, candidate_fields)

    score_rows = []
    for s in scored:
        sc = s['scores']
        r = s['row']
        score_rows.append({
            'evidence_id': r['evidence_id'], 'code': r['code'], 'name': r['name'],
            'board_count': r['board_count'], 'first_limit_time': r['first_limit_time'],
            'board_ladder': sc['board_ladder'], 'limit_quality': sc['limit_quality'],
            'capital': sc['capital'], 'sector': sc['sector'], 'visibility': sc['visibility'],
            'total': sc['total'], 'industry': r['industry'],
            'mechanism': r['mechanism'], 'mechanism_rank': s['mechanism_rank'],
        })
    write_csv(out_dir / 'dragon_score.csv', score_rows,
              ['evidence_id', 'code', 'name', 'board_count', 'first_limit_time',
               'board_ladder', 'limit_quality', 'capital', 'sector', 'visibility',
               'total', 'industry', 'mechanism', 'mechanism_rank'])

    write_report_md(out_dir / 'report.md', scored, pool, args.date)

    # audit_log
    AUDIT['output_dir'] = str(out_dir)
    AUDIT['candidates'] = len(pool)
    AUDIT['top5_count'] = sum(1 for s in scored if s['total'] >= 70)
    (out_dir / 'audit_log.md').write_text(
        f'# Audit Log ({args.date})\n\n```json\n{json.dumps(AUDIT, ensure_ascii=False, indent=2)}\n```\n',
        encoding='utf-8'
    )

    print(f'\n=== 完成 ===')
    print(f'输出目录: {out_dir}')
    print(f'候选池: {len(pool)} 只 2 连板+')
    print(f'Top 5 (≥70 分): {AUDIT["top5_count"]} 只')
    print(f'数据源状态: {len([v for v in AUDIT["sources"].values() if v.get("status") == "OK"])} OK / {len(AUDIT["failures"])} 失败')
    return 0


if __name__ == '__main__':
    sys.exit(main())
