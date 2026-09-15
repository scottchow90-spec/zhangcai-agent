#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""analyze_picks.py - Score + classify + filter ZT picks (lianban wakuang).

Pipeline (固化): raw4_<date>.json -> scored + lines + picks + yijiner + risky
                 -> analyzed2_<date>.json

合并 r4_analyze.py 的 scoring 逻辑, 保留 ZTC 过滤与 FORBIDDEN 模板残留检查.
"""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import sys, os, json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')
try:
    from run_research import k_line_verify, risk_scan, find_tdx_day_path, read_tdx_day
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from run_research import k_line_verify, risk_scan, find_tdx_day_path, read_tdx_day
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ZTC = Path(r"C:\new_tdx_mock\T0002\blocknew\ZTC.blk")
try:
    from _date_utils import resolve_latest_trade_date
    _RESOLVED = resolve_latest_trade_date()
except Exception:
    _RESOLVED = None
DATE = sys.argv[1] if len(sys.argv) > 1 and str(sys.argv[1]).isdigit() else _RESOLVED
if not DATE:
    raise SystemExit("analyze_picks: cannot determine trading date (no --date and TDX lookup failed)")

# 模板残留禁选 (G11 硬闸): 6/1 模板的标的, 禁止作为精品
FORBIDDEN = {'\u8f6f\u901a\u52a8\u529b', '\u5317\u73bb\u80a1\u4efd', '\u7ca4\u7535\u529b',
             '\u7ca4\u7535\u529b\uff21', '\u5408\u953b\u667a\u80fd'}

# 板块归类规则 (与 r4_analyze.py 一致)
LINE_RULES = [
    (['\u5149\u4f0f', '\u50a8\u80fd', '\u9502\u7535', '\u7535\u6c60', '\u65b0\u80fd\u6e90',
      '\u5145\u7535\u6869', '\u98ce\u7535', '\u6838\u7535'], '\u65b0\u80fd\u6e90/\u7535\u529b', '\u65b0\u80fd\u6e90'),
    (['\u7535\u529b', '\u7535\u7f51', '\u53d1\u7535', '\u706b\u7535', '\u6c34\u7535', '\u6838\u7535'],
     '\u7535\u529b\u7535\u7f51/\u80fd\u6e90', '\u7535\u529b'),
    (['\u534a\u5bfc\u4f53', '\u82af\u7247', '\u7535\u5b50', 'PCB', '\u5143\u4ef6', '\u5b58\u50a8',
      '\u5c01\u6d4b', '\u5149\u523b'], '\u534a\u5bfc\u4f53\u7535\u5b50/AI\u786c\u4ef6', '\u534a\u5bfc\u4f53'),
    (['AI', '\u7b97\u529b', '\u5927\u6a21\u578b', '\u673a\u5668\u4eba', 'CPO', '\u5149\u6a21\u5757',
      '\u6db2\u51b7', 'PCB'], 'AI\u7b97\u529b/\u6570\u5b57\u7ecf\u6d4e', 'AI\u7b97\u529b'),
    (['\u901a\u4fe1', '\u5149\u901a\u4fe1', '5G', '\u5149\u7ea4', '\u536b\u661f', '\u901a\u4fe1\u8bbe\u5907'],
     '\u901a\u4fe1\u8bbe\u5907', '\u901a\u4fe1'),
    (['\u533b\u836f', '\u533b\u7597', '\u751f\u7269', '\u533b\u9662', '\u5316\u5b66\u5236\u836f',
      '\u4e2d\u836f', '\u5668\u68b0'], '\u533b\u836f\u751f\u7269', '\u533b\u836f'),
    (['\u6c7d\u8f66', '\u96f6\u90e8\u4ef6', '\u8f6e\u80ce', '\u6c7d\u96f6', '\u6574\u8f66'],
     '\u6c7d\u8f66/\u96f6\u90e8\u4ef6', '\u6c7d\u8f66'),
    (['\u94a2\u94c1', '\u7164\u70ad', '\u6709\u8272', '\u9ec4\u91d1', '\u94dd', '\u94dc', '\u7a00\u571f',
      '\u91d1\u5c5e', '\u77ff\u4e1a', '\u5316\u5de5', '\u5316\u5b66', '\u77f3\u5316'],
     '\u5468\u671f\u6da8\u4ef7/\u8d44\u6e90\u5316\u5de5', '\u5468\u671f\u6da8\u4ef7'),
    (['\u73bb\u7483', '\u5efa\u6750', '\u6c34\u6ce5', '\u73bb\u7ea4'],
     '\u5468\u671f\u6da8\u4ef7/\u8d44\u6e90\u5316\u5de5', '\u5468\u671f\u6da8\u4ef7'),
    (['\u673a\u68b0', '\u8bbe\u5907', '\u5de5\u7a0b', '\u8f68\u4ea4', '\u4e13\u7528\u8bbe\u5907',
      '\u901a\u7528\u8bbe\u5907'], '\u8bbe\u5907\u5efa\u8bbe/\u5de5\u7a0b', '\u8bbe\u5907'),
    (['\u6d88\u8d39', '\u98df\u54c1', '\u996e\u6599', '\u9152', '\u5bb6\u7535', '\u96f6\u552e',
      '\u7eba\u7ec7', '\u670d\u88c5'], '\u6d88\u8d39/\u98df\u54c1\u996e\u6599', '\u6d88\u8d39'),
    (['\u4f20\u5a92', '\u6e38\u620f', '\u5f71\u89c6', '\u5e7f\u544a', '\u6559\u80b2'],
     '\u4f20\u5a92/\u6559\u80b2', '\u4f20\u5a92'),
    (['\u91d1\u878d', '\u94f6\u884c', '\u8bc1\u5238', '\u4fdd\u9669', '\u4fe1\u6258'], '\u91d1\u878d', '\u91d1\u878d'),
    (['\u5730\u4ea7', '\u5efa\u7b51', '\u88c5\u9970', '\u7269\u4e1a', '\u5efa\u6750'],
     '\u5730\u4ea7/\u5efa\u7b51', '\u5730\u4ea7'),
    (['\u519b\u5de5', '\u56fd\u9632', '\u822a\u7a7a', '\u822a\u5929', '\u8239\u8236'],
     '\u519b\u5de5/\u88c5\u5907', '\u519b\u5de5'),
]


def assign_line(industry, name):
    s = (str(industry) + '|' + str(name))
    for kws, line, _ in LINE_RULES:
        for kw in kws:
            if kw in s:
                return line
    return '\u5176\u4ed6'


def assign_topic(line):
    for _, mapped_line, topic in LINE_RULES:
        if line == mapped_line:
            return topic
    return '\u5176\u4ed6'


def score_stock(z, lhb_row, line_count, market_breadth):
    """严格 8 因子 100 分；所有分项只使用当前记录中可核算字段。"""
    factors = {}
    lb = int(z.get('lb', 0) or 0)
    factors['board_ladder'] = 15 if lb >= 4 else (12 if lb == 3 else (9 if lb == 2 else 3))

    first_digits = ''.join(ch for ch in str(z.get('first_seal', '')) if ch.isdigit())[:6]
    break_count = int(z.get('break_count', 0) or 0)
    quality = 10 if break_count == 0 else (6 if break_count == 1 else (3 if break_count == 2 else 0))
    if len(first_digits) == 6:
        quality += 8 if first_digits <= '093500' else (6 if first_digits <= '103000' else 3)
    if z.get('last_seal') == z.get('first_seal') and z.get('first_seal') not in ('', '-'):
        quality += 2
    factors['limit_quality'] = min(20, quality)

    seal_funds = float(z.get('seal_funds', 0) or 0)
    turnover = float(z.get('turnover', 0) or 0)
    capital = 6 if seal_funds >= 1e8 else (3 if seal_funds >= 5e7 else 0)
    capital += 5 if lhb_row and float(lhb_row.get('net_buy', 0) or 0) > 0 else 0
    capital += 4 if 5 <= turnover <= 25 else (2 if turnover > 0 else 0)
    factors['capital'] = min(15, capital)

    factors['visibility'] = min(10, (5 if lhb_row else 0) + (5 if lb >= 3 else (3 if lb == 2 else 1)))
    factors['sector_main'] = min(15, int(line_count) * 3 + (3 if lb >= 2 else 0))
    factors['chip'] = 10 if 5 <= turnover <= 18 else (6 if 2 <= turnover <= 25 else (2 if turnover > 0 else 0))
    factors['sentiment'] = 10 if market_breadth >= 60 else (7 if market_breadth >= 30 else (4 if market_breadth >= 10 else 0))
    one_word_like = first_digits and first_digits <= '093000' and turnover < 1
    factors['executable'] = 1 if one_word_like else (5 if turnover > 0 else 0)
    score = sum(factors.values())
    factor_labels = {
        'board_ladder': '连板梯队',
        'limit_quality': '封板质量',
        'capital': '资金承接',
        'visibility': '辨识度',
        'sector_main': '题材主线',
        'chip': '筹码结构',
        'sentiment': '市场情绪',
        'executable': '次日可执行性',
    }
    notes = [factor_labels[name] for name, value in factors.items() if value > 0]
    return round(score, 1), '+'.join(notes), factors


def read_ztc():
    text = ZTC.read_text(encoding='gbk', errors='ignore')
    codes = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        c = s[-6:] if len(s) >= 6 else s
        if c.isdigit() and len(c) == 6:
            codes.append(c)
    return list(dict.fromkeys(codes))


def reconcile_scored_with_ztc(zt_scored, ztc_codes):
    """Keep the current AK pool intact; use local ZTC only as a passive cross-check."""
    raw_codes = [str(code).strip() for code in (ztc_codes or [])]
    real_ztc_codes = {
        code for code in raw_codes
        if code.isdigit() and len(code) == 6 and code != '000000'
    }
    scored_codes = {
        str(row.get('code', '')).strip()
        for row in zt_scored
        if str(row.get('code', '')).strip()
    }
    if not real_ztc_codes and '000000' in raw_codes:
        status = 'IGNORED_PLACEHOLDER'
    elif not real_ztc_codes:
        status = 'REFERENCE_EMPTY'
    else:
        status = 'CROSS_CHECKED'
    audit = {
        'status': status,
        'reference_count': len(real_ztc_codes),
        'intersection_codes': sorted(scored_codes & real_ztc_codes),
        'conflicts': sorted(scored_codes - real_ztc_codes),
        'excluded_count': 0,
    }
    return list(zt_scored), audit


def is_safe_name(name):
    return name not in FORBIDDEN


def is_hard_excluded(z):
    code = str(z.get('code', ''))
    name = str(z.get('name', '')).upper()
    return code.startswith(('4', '8', '9', '200', '688')) or 'ST' in name or '\u9000' in name


def is_risky(z):
    """风险判定: LHB 净卖 > 2 千万 或 炸板 > 7 次."""
    if z['lhb_net_buy'] < -2e7:
        return True
    if z['break_count'] > 7:
        return True
    return False


def build_k_line_detail(code: str, trade_iso: str) -> dict:
    """Return auditable D/D-1 price structure and next-session reference levels."""
    from datetime import datetime
    from decimal import Decimal, ROUND_HALF_UP

    path = find_tdx_day_path(code)
    records = read_tdx_day(path) if path else []
    trade_day = datetime.strptime(trade_iso, '%Y-%m-%d').date()
    index = next((i for i, row in enumerate(records) if row['date'] == trade_day), None)
    if index is None or index < 1:
        return {'status': 'MISSING'}

    def day_payload(row):
        return {
            'date': row['date'].isoformat(),
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
        }

    current = records[index]
    previous = records[index - 1]
    earlier = records[index - 2] if index >= 2 else None
    pct = (current['close'] - previous['close']) / previous['close'] * 100 if previous['close'] else 0
    previous_pct = (
        (previous['close'] - earlier['close']) / earlier['close'] * 100
        if earlier and earlier['close'] else None
    )
    limit_ratio = Decimal('1.20') if code.startswith('3') else Decimal('1.10')

    def price_round(value) -> float:
        return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    return {
        'status': 'PASS',
        'source_kind': 'TDX_LOCAL_DAY',
        'source_path': str(path),
        'd': day_payload(current),
        'd_minus_1': day_payload(previous),
        'd_minus_2': day_payload(earlier) if earlier else None,
        'd_pct_change': round(pct, 2),
        'd_minus_1_pct_change': round(previous_pct, 2) if previous_pct is not None else None,
        'closed_at_high': abs(current['high'] - current['close']) <= 0.011,
        'next_limit_reference': price_round(Decimal(str(current['close'])) * limit_ratio),
        'strong_open_reference': price_round(Decimal(str(current['close'])) * Decimal('0.98')),
        'invalidation_reference': price_round(current['low']),
    }


def main():
    # 命令行: sys.argv[1] = raw4 路径, sys.argv[2] = analyzed2 输出路径
    if len(sys.argv) >= 2:
        raw_path = Path(sys.argv[1])
    else:
        raw_path = Path(r"D:\C盘转移\日志\codex\tmp_lb\data\raw4_") \
            .with_name(f"raw4_{DATE}.json")
    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2])
    else:
        out_path = Path(r"D:\C盘转移\日志\codex\tmp_lb\data\analyzed2_") \
            .with_name(f"analyzed2_{DATE}.json")

    if not raw_path.exists():
        print(f"ERROR: {raw_path} not found", file=sys.stderr)
        return 1

    out = json.loads(raw_path.read_text(encoding='utf-8'))
    zt = out['zt_pool']
    lhb = out['lhb']
    lhb_by_code = {r['code']: r for r in lhb}

    qsyb_codes = {r.get('code') for r in out.get('qsyb', [])}
    rdxz_codes = {r.get('code') for r in out.get('rdxz', [])}
    risk_evidence = out.get('risk_evidence', {})
    line_by_code = {z['code']: assign_line(z['industry'], z['name']) for z in zt}
    line_counts = {}
    for line in line_by_code.values():
        line_counts[line] = line_counts.get(line, 0) + 1

    # 1) Score + line assignment
    zt_scored = []
    for z in zt:
        line = line_by_code[z['code']]
        topic = assign_topic(line)
        lhb_row = lhb_by_code.get(z['code'])
        score, notes, score_factors = score_stock(z, lhb_row, line_counts.get(line, 0), len(zt))
        trade_iso = f"{out['date'][:4]}-{out['date'][4:6]}-{out['date'][6:8]}"
        verify_mode = 'connected' if int(z.get('lb', 0) or 0) >= 2 else 'limit'
        k_verify = k_line_verify(z['code'], trade_iso, mode=verify_mode)
        k_detail = build_k_line_detail(z['code'], trade_iso)
        bound_risk = risk_evidence.get(z['code'], {})
        risk_result = risk_scan({
            'risk_flags': bound_risk.get('risk_flags', []),
            'risk_review_complete': bound_risk.get('review_complete') is True,
        })
        score = max(0, score - int(risk_result.get('score_penalty', 0)))
        zt_scored.append({
            **z,
            'line': line,
            'topic': topic,
            'lhb_net_buy': (lhb_row['net_buy'] if lhb_row else 0),
            'lhb_label': 'pure' if lhb_row and lhb_row['net_buy'] > 0
                else ('warn' if lhb_row and lhb_row['net_buy'] < 0 else 'none'),
            'score': score,
            'score_notes': notes,
            'score_factors': score_factors,
            'mechanism': '20cm' if str(z['code']).startswith('3') else '10cm',
            'qsyb_bound': z['code'] in qsyb_codes,
            'rdxz_bound': z['code'] in rdxz_codes,
            'k_line_verify': k_verify,
            'k_line_detail': k_detail,
            'risk_result': risk_result,
            'risk_review_complete': bound_risk.get('review_complete') is True,
        })
    zt_scored.sort(key=lambda x: x['score'], reverse=True)

    # 2) ZTC passive cross-check + actual business filters
    zt_scored, ztc_cross_check = reconcile_scored_with_ztc(zt_scored, read_ztc())
    print(
        'ZTC cross-check: '
        f"{ztc_cross_check['status']} "
        f"reference={ztc_cross_check['reference_count']} "
        f"intersection={len(ztc_cross_check['intersection_codes'])} "
        f"conflicts={len(ztc_cross_check['conflicts'])}"
    )
    zt_safe = []
    for z in zt_scored:
        if is_hard_excluded(z):
            print(f'  filter: {z["code"]} {z["name"]} (hard exclusion)')
            continue
        if z.get('k_line_verify') != 'PASS':
            print(f'  filter: {z["code"]} {z["name"]} (K-line {z.get("k_line_verify")})')
            continue
        if not is_safe_name(z['name']):
            print(f'  filter: {z["code"]} {z["name"]} (forbidden template residual)')
            continue
        zt_safe.append(z)
    print(f'After filter: {len(zt_safe)}')

    # 3) Line aggregation
    line_stats = {}
    for z in zt_safe:
        s = line_stats.setdefault(z['line'], {
            'line': z['line'],
            'topic': z['topic'],
            'count': 0, 'first_count': 0, 'lb_count': 0,
            'max_lb': 0, 'seal_funds': 0.0, 'lhb_net_buy': 0.0,
            'break_count_sum': 0,
        })
        s['count'] += 1
        if z['lb'] == 1:
            s['first_count'] += 1
        else:
            s['lb_count'] += 1
        s['max_lb'] = max(s['max_lb'], z['lb'])
        s['seal_funds'] += z['seal_funds']
        s['lhb_net_buy'] += z['lhb_net_buy']
        s['break_count_sum'] += z['break_count']
    for v in line_stats.values():
        n = v['count']
        s = v['count'] * 1.0 + v['lb_count'] * 3.0 + (v['seal_funds'] / 1e8) * 5.0 \
            + (v['lhb_net_buy'] / 1e8) * 5.0
        if n > 0:
            s -= (v['break_count_sum'] / n) * 3
        v['score'] = round(s, 1)
        v['avg_break'] = round(v['break_count_sum'] / n, 1) if n > 0 else 0
    line_list = sorted(line_stats.values(), key=lambda x: x['score'], reverse=True)

    # 4) Picks / Yijiner / Risky
    lianban = [z for z in zt_safe if z['lb'] >= 2]
    firstban = [z for z in zt_safe if z['lb'] == 1]
    risky = [z for z in zt_safe if is_risky(z) or z.get('risk_result', {}).get('final_action') in ('OUT', 'DOWNGRADE')]
    safe_lianban = [z for z in lianban if not is_risky(z) and z['score'] >= 70 and z['qsyb_bound'] and z['rdxz_bound'] and z['risk_result']['final_action'] == 'PASS']
    safe_firstban = [z for z in firstban if not is_risky(z) and z['score'] >= 70 and z['qsyb_bound'] and z['rdxz_bound'] and z['risk_result']['final_action'] == 'PASS']
    for z in zt_safe:
        if z in risky:
            z['classification'] = '剔除'
        elif z in safe_lianban and z['score'] >= 80:
            z['classification'] = '精品'
        elif (z in safe_lianban or z in safe_firstban) and z['score'] >= 70:
            z['classification'] = '狙击'
        else:
            z['classification'] = '观察'
    picks = safe_lianban[:5]
    yijiner = safe_firstban[:10]

    print(f'\nNew Top 5:')
    for i, z in enumerate(picks, 1):
        print(f'  {i}. {z["code"]} {z["name"]} (line={z["line"]} lb={z["lb"]} score={z["score"]})')
    print(f'\nRisky: {len(risky)}')

    out_analyzed = {
        'date': out['date'],
        'collected_at': out.get('collected_at'),
        'ztc_cross_check': ztc_cross_check,
        'summary': {
            'zt_total': len(zt),
            'zt_first': sum(1 for z in zt if z['lb'] == 1),
            'zt_lb': sum(1 for z in zt if z['lb'] >= 2),
            'lhb_total': len(lhb),
            'lhb_in_zt': sum(1 for r in lhb if r['code'] in {z['code'] for z in zt}),
            'qsyb_total': len(out.get('qsyb', [])),
            'rdxz_total': len(out.get('rdxz', [])),
            'line_count': len(line_list),
            'risky_count': len(risky),
            'pick_count': len(picks),
        },
        'lines': line_list,
        'zt_scored': zt_safe,
        'lhb_in_zt': [r for r in lhb if r['code'] in {z['code'] for z in zt}],
        'picks': picks,
        'yijiner': yijiner,
        'risky': risky,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_analyzed, ensure_ascii=False, indent=2, default=str),
                        encoding='utf-8')
    print(f'\nSaved: {out_path} ({out_path.stat().st_size} bytes)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
