#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_lianban_docx.py - End-to-end orchestrator for 连板挖掘 docx.

Usage:
    python run_lianban_docx.py --date YYYYMMDD [--skip-collect] [--skip-build]

Pipeline:
  1. prebuild_audit  (gate)        - validates data sources
  2. collect_zt_lhb  (script)      - collect ZT pool + LHB
  3. collect_qsyb    (script)      - collect research reports
  4. collect_rdxz    (script)      - collect news
  5. collect_risk    (script)      - stock-bound announcement risk scan
  6. analyze_picks   (script)      - strict K-line + 8-factor score + classify
  7. build_docx      (script)      - generate DOCX from template
  8. word_template_gate  (gate)    - validate output
  9. docx_template_diff  (gate)    - diff against template
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import date as calendar_date, datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
WORKSPACE_DATA = Path(r"D:\C盘转移\日志\codex\tmp_lb\data")
WORKSPACE_DATA.mkdir(parents=True, exist_ok=True)
OUT_DIR = Path(r"F:\小龙虾6月交付")
TEMPLATE = Path(r"F:\小龙虾6月交付\6月1日连板挖掘5标的.docx")
AUDIT_GATE = SCRIPT_DIR / "lianban_prebuild_audit_gate.py"
WORD_GATE = SCRIPT_DIR / "lianban_word_template_gate.py"
DIFF_GATE = SCRIPT_DIR / "lianban_docx_template_diff.py"
ENSURE_TEMPLATE = SCRIPT_DIR / "ensure_lianban_template.py"


def run_py(script, *args, capture=True, timeout=120, python_executable=None):
    """Run a python script and return (returncode, stdout, stderr)."""
    cmd = [str(python_executable or sys.executable), str(script), *args]
    print(f"\n>>> {' '.join(cmd)}")
    try:
        p = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        print(f"TIMEOUT after {timeout}s: {' '.join(cmd)}")
        if stdout:
            print(stdout.rstrip()[-1000:])
        if stderr:
            print(f"STDERR: {stderr.rstrip()[-500:]}")
        return 124, stdout, stderr
    if p.stdout:
        print(p.stdout.rstrip())
    if p.returncode != 0 and p.stderr:
        print(f"STDERR: {p.stderr.rstrip()[:500]}")
    return p.returncode, p.stdout, p.stderr


def step_audit(date):
    """Step 1: Prebuild audit with --date."""
    default_template = Path(r"F:\小龙虾6月交付\6月1日连板挖掘5标的.docx").resolve()
    if TEMPLATE == default_template and ENSURE_TEMPLATE.exists():
        rc, _, _ = run_py(ENSURE_TEMPLATE, timeout=90)
        if rc != 0:
            return rc, OUT_DIR / f"\u8fde\u677f\u6316\u6398_{date[:4]}-{date[4:6]}-{date[6:8]}_prebuild_audit.json"
    audit_json = OUT_DIR / f"\u8fde\u677f\u6316\u6398_{date[:4]}-{date[4:6]}-{date[6:8]}_prebuild_audit.json"
    if not AUDIT_GATE.exists():
        print(f"ERROR: prebuild audit gate missing: {AUDIT_GATE}")
        return 2, audit_json
    rc, _, _ = run_py(AUDIT_GATE, '--date', date, '--json', '--out', str(audit_json), '--template', str(TEMPLATE), timeout=240)
    return rc, audit_json


def step_collect(date):
    """Steps 2-5: Collect raw data."""
    # 1) ZT + LHB (script writes to raw_<date>.json)
    rc, _, _ = run_py(SCRIPT_DIR / 'collect_zt_lhb.py', date, timeout=90)
    if rc != 0:
        return rc

    # 2) QSYB (script appends qsyb to existing raw, writes to raw2_<date>.json)
    rc, _, _ = run_py(SCRIPT_DIR / 'collect_qsyb.py', date, timeout=240)
    if rc != 0:
        return rc

    # 3) RDXZ (script appends rdxz to existing raw, writes to raw3_<date>.json)
    rc, _, _ = run_py(SCRIPT_DIR / 'collect_rdxz.py', date, timeout=240)
    if rc != 0:
        return rc

    # 4) Risk evidence + final merged raw4.
    rc, _, _ = run_py(SCRIPT_DIR / 'collect_risk.py', date, timeout=300)
    if rc != 0:
        return rc
    target_raw = WORKSPACE_DATA / f"raw4_{date}.json"
    if not target_raw.exists():
        print(f"ERROR: {target_raw} not produced")
        return 1
    print(f"Final raw: {target_raw} ({target_raw.stat().st_size} bytes)")
    return 0


def step_analyze(date):
    """Step 6: Analyze + filter picks."""
    raw_path = WORKSPACE_DATA / f"raw4_{date}.json"
    out_path = WORKSPACE_DATA / f"analyzed2_{date}.json"
    if not raw_path.exists():
        return 1, None
    rc, _, _ = run_py(SCRIPT_DIR / 'analyze_picks.py', str(raw_path), str(out_path))
    return rc, out_path


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_trade_date(value):
    text = str(value or '').strip()
    digits = ''.join(char for char in text if char.isdigit())
    if len(digits) != 8:
        raise ValueError(f'invalid trade date: {value!r}')
    return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"


def collected_at_iso(raw, raw_path):
    value = str(raw.get('collected_at') or '').strip()
    if value:
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if parsed.tzinfo is None:
                parsed = parsed.astimezone()
            return parsed.astimezone().isoformat(timespec='seconds')
        except ValueError:
            pass
    return datetime.fromtimestamp(raw_path.stat().st_mtime).astimezone().isoformat(timespec='seconds')


def step_data_evidence(date, data_path, evidence_path):
    """Create evidence from the raw and analyzed files produced by this run."""
    raw_path = WORKSPACE_DATA / f"raw4_{date}.json"
    raw = json.loads(raw_path.read_text(encoding='utf-8'))
    analyzed = json.loads(data_path.read_text(encoding='utf-8'))
    expected_date = normalized_trade_date(date)
    raw_date = normalized_trade_date(raw.get('date'))
    analysis_date = normalized_trade_date(analyzed.get('date'))
    if raw_date != expected_date or analysis_date != expected_date:
        raise ValueError(
            f'trade date mismatch: expected={expected_date} raw={raw_date} analysis={analysis_date}'
        )

    fetched_at = collected_at_iso(raw, raw_path)
    local_codes = sorted({
        str(code).strip()
        for code in raw.get('ztc_local', [])
        if str(code).strip().isdigit()
        and len(str(code).strip()) == 6
        and str(code).strip() != '000000'
    })
    strict_stocks = analyzed.get('zt_scored', [])
    risk_complete = sum(stock.get('risk_review_complete') is True for stock in strict_stocks)
    risk_errors = len(strict_stocks) - risk_complete
    if risk_errors:
        raise ValueError(f'risk review incomplete for {risk_errors} analyzed stocks')

    source_groups = []
    if isinstance(raw.get('ztc_local_source'), dict):
        source_groups.append('通达信本地行情')
    if isinstance(raw.get('zt_pool'), list) or isinstance(raw.get('lhb'), list):
        source_groups.append('东方财富公开行情与龙虎榜')
    if isinstance(raw.get('qsyb_collection'), dict):
        source_groups.append('东方财富个股研报')
    if isinstance(raw.get('rdxz_collection'), dict):
        source_groups.append('公开个股新闻')
    if isinstance(raw.get('risk_collection'), dict):
        source_groups.append('东方财富公司公告')
    sources = [
        {
            'provider_group': provider_group,
            'trade_date': expected_date,
            'fetched_at': fetched_at,
        }
        for provider_group in source_groups
    ]

    local_source = raw.get('ztc_local_source') or {}
    local_ztc_sha256 = str(local_source.get('ztc_sha256') or '').strip()
    if not local_ztc_sha256:
        local_ztc_sha256 = hashlib.sha256(
            json.dumps(local_codes, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        ).hexdigest()

    evidence = {
        'status': 'PASS',
        'trade_date': expected_date,
        'business_data_trade_date': raw_date,
        'business_data_sha256': sha256_file(raw_path),
        'business_data_path': raw_path.resolve().as_posix(),
        'business_data_date_field': 'date',
        'business_data_size': raw_path.stat().st_size,
        'data_cutoff': fetched_at,
        'sources': sources,
        'analysis_sha256': sha256_file(data_path),
        'analysis_path': data_path.resolve().as_posix(),
        'analysis_size': data_path.stat().st_size,
        'market_date': analysis_date,
        'limit_up_count': len(raw.get('zt_pool', [])),
        'local_tdx_limit_up_count': len(local_codes),
        'strict_intersection_count': len(strict_stocks),
        'risk_review_complete_count': risk_complete,
        'risk_review_error_count': risk_errors,
        'local_ztc_sha256': local_ztc_sha256,
    }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(json.dumps({
        'status': 'DATA_EVIDENCE_PASS',
        'path': str(evidence_path),
        'trade_date': expected_date,
        'limit_up_count': evidence['limit_up_count'],
        'strict_intersection_count': evidence['strict_intersection_count'],
        'risk_review_complete_count': risk_complete,
    }, ensure_ascii=False))
    return evidence


def evaluate_source_roles(raw, analyzed):
    """Validate TDX K-line provenance while treating ZTC as passive reference data."""
    local_codes = {
        str(code).strip()
        for code in raw.get('ztc_local', [])
        if str(code).strip().isdigit()
        and len(str(code).strip()) == 6
        and str(code).strip() != '000000'
    }
    strict_stocks = analyzed.get('zt_scored', [])
    strict_codes = {
        str(stock.get('code', '')).strip()
        for stock in strict_stocks
        if str(stock.get('code', '')).strip()
    }
    bad_kline = []
    for stock in strict_stocks:
        detail = stock.get('k_line_detail') or {}
        source_path = str(detail.get('source_path', ''))
        if (
            stock.get('k_line_verify') != 'PASS'
            or detail.get('status') != 'PASS'
            or detail.get('source_kind') != 'TDX_LOCAL_DAY'
            or not source_path.upper().startswith('C:\\new_tdx_mockMONI\\')
        ):
            bad_kline.append(str(stock.get('code', '')))

    return {
        'blocks': [f"non_tdx_kline:{bad_kline}"] if bad_kline else [],
        'strict_codes': sorted(strict_codes),
        'ztc_reference_count': len(local_codes),
        'ztc_intersection': sorted(strict_codes & local_codes),
        'ztc_conflicts': sorted(strict_codes - local_codes),
        'ztc_excluded_count': 0,
        'tdx_kline_pass': len(strict_stocks) - len(bad_kline),
        'non_tdx_kline': bad_kline,
    }


def step_source_role_gate(date, data_path):
    raw_path = WORKSPACE_DATA / f"raw4_{date}.json"
    raw = json.loads(raw_path.read_text(encoding='utf-8'))
    analyzed = json.loads(data_path.read_text(encoding='utf-8'))
    result = evaluate_source_roles(raw, analyzed)
    blocks = result['blocks']
    if blocks:
        print(json.dumps({'status': 'SOURCE_ROLE_BLOCKED', 'blocks': blocks}, ensure_ascii=False))
        return 2
    print(json.dumps({
        'status': 'SOURCE_ROLE_CLEAN',
        'strict_codes': len(result['strict_codes']),
        'tdx_kline_pass': result['tdx_kline_pass'],
        'ztc_reference_count': result['ztc_reference_count'],
        'ztc_intersection_count': len(result['ztc_intersection']),
        'ztc_conflict_count': len(result['ztc_conflicts']),
        'ztc_excluded_count': result['ztc_excluded_count'],
    }, ensure_ascii=False))
    return 0


def step_build(date, data_path, authoring_python, data_evidence):
    """Step 7: Build docx."""
    date_pretty = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
    out_path = OUT_DIR / f"\u8fde\u677f\u6316\u6398_{date_pretty}.docx"
    raw_path = WORKSPACE_DATA / f"raw4_{date}.json"
    rc, _, _ = run_py(SCRIPT_DIR / 'build_docx.py',
                       '--date', date,
                       '--data', str(data_path),
                       '--raw', str(raw_path),
                       '--template', str(TEMPLATE),
                       '--out', str(out_path),
                       '--data-evidence', str(data_evidence),
                       python_executable=authoring_python)
    return rc, out_path


def step_word_gate(docx_path):
    """Step 8: Word template gate."""
    if not docx_path.exists():
        return 1
    rc, _, _ = run_py(WORD_GATE, '--docx', str(docx_path))
    return rc


def step_diff(docx_path):
    """Step 9: Template diff."""
    if not docx_path.exists():
        return 1
    json_out = OUT_DIR / 'tmp' / f"docx_diff_{Path(docx_path).stem}.json"
    md_out = OUT_DIR / 'tmp' / f"docx_diff_{Path(docx_path).stem}.md"
    json_out.parent.mkdir(parents=True, exist_ok=True)
    rc, _, _ = run_py(DIFF_GATE, '--template', str(TEMPLATE),
                      '--output', str(docx_path),
                      '--json-out', str(json_out),
                      '--md-out', str(md_out))
    return rc


def main():
    global OUT_DIR, TEMPLATE
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True, help='YYYYMMDD')
    ap.add_argument('--manual-confirm', action='store_true', help='确认由当前 Codex 主任务手动触发')
    ap.add_argument('--out-dir', default=str(OUT_DIR), help='DOCX 与审计输出目录')
    ap.add_argument('--template', default=str(TEMPLATE), help='Word 模板路径')
    ap.add_argument('--skip-collect', action='store_true')
    ap.add_argument('--skip-build', action='store_true')
    ap.add_argument('--skip-gate', action='store_true')
    ap.add_argument('--diagnostic', action='store_true', help='仅允许诊断时跳过交付闸，不得视为正式完成')
    ap.add_argument('--authoring-python', required=True, help='Office 交付锁指定的 bundled Python')
    ap.add_argument('--data-evidence', required=True, help='股票数据新鲜度证据 JSON')
    args = ap.parse_args()

    date = args.date
    if len(date) != 8 or not date.isdigit():
        raise SystemExit('--date 必须是 YYYYMMDD')
    if not args.manual_confirm:
        raise SystemExit('缺少 --manual-confirm；完整模式只允许主任务手动执行')
    if os.environ.get('CODEX_AUTOMATION_RUN') == '1' or os.environ.get('CODEX_BACKGROUND_RUN') == '1':
        raise SystemExit('检测到自动/后台触发标记，完整模式拒绝执行')
    if date == calendar_date.today().strftime('%Y%m%d') and int(datetime.now().strftime('%H%M')) < 1505:
        raise SystemExit('当日 15:05 前禁止生成正式连板挖掘结论')
    if args.skip_gate and not args.diagnostic:
        raise SystemExit('--skip-gate 只能与 --diagnostic 同时使用，且不能作为正式交付')
    OUT_DIR = Path(args.out_dir).expanduser().resolve()
    TEMPLATE = Path(args.template).expanduser().resolve()
    authoring_python = Path(args.authoring_python).expanduser().resolve()
    data_evidence = Path(args.data_evidence).expanduser().resolve()
    if not authoring_python.is_file():
        raise SystemExit(f'authoring Python 不存在: {authoring_python}')
    if data_evidence.exists() and not data_evidence.is_file():
        raise SystemExit(f'数据证据路径不是文件: {data_evidence}')
    data_evidence.parent.mkdir(parents=True, exist_ok=True)
    print(f"=== run_lianban_docx ===\ndate: {date}")

    print("\n[Step 1] Prebuild audit")
    rc, audit_path = step_audit(date)
    print(f"audit: {audit_path} rc={rc}")
    if rc != 0:
        sys.exit(f"prebuild audit failed (rc={rc}): {audit_path}")

    if not args.skip_collect:
        print("\n[Step 2-5] Collect data")
        rc = step_collect(date)
        if rc != 0:
            sys.exit(f"collect failed (rc={rc})")

    date_pretty = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
    docx_path = OUT_DIR / f"连板挖掘_{date_pretty}.docx"
    if not args.skip_build:
        print("\n[Step 6] Analyze picks")
        rc, data_path = step_analyze(date)
        if rc != 0 or not data_path or not data_path.exists():
            sys.exit(f"analyze failed (rc={rc})")

        print("\n[Step 6.5] Source role gate")
        rc = step_source_role_gate(date, data_path)
        if rc != 0:
            sys.exit(f"source role gate FAILED (rc={rc})")

        print("\n[Step 6.6] Build current-run data evidence")
        step_data_evidence(date, data_path, data_evidence)
        if not data_evidence.is_file():
            sys.exit(f"data evidence was not produced: {data_evidence}")

        print("\n[Step 7] Build docx")
        rc, docx_path = step_build(date, data_path, authoring_python, data_evidence)
        if rc != 0:
            sys.exit(f"build failed (rc={rc})")

    if not args.skip_gate:
        print("\n[Step 8] Word template gate")
        rc = step_word_gate(docx_path)
        if rc != 0:
            sys.exit(f"word gate FAILED (rc={rc})")
        print("CLEAN_PASS")

        print("\n[Step 9] Template diff")
        rc = step_diff(docx_path)
        print(f"diff rc={rc}")
        if rc != 0:
            sys.exit(f"template diff FAILED (rc={rc})")

    print("\n=== DIAGNOSTIC_ONLY ===" if args.skip_gate else "\n=== DONE ===")
    print(f"DOCX: {docx_path}")


if __name__ == '__main__':
    main()
