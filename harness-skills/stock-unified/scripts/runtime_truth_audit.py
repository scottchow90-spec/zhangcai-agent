#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import json
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
REPORTS = WORKSPACE / 'skills' / 'stock-unified' / 'reports'

ACTIVE_TARGETS = [
    WORKSPACE / 'skills' / 'big-bull-line' / 'SKILL.md',
    WORKSPACE / 'skills' / 'feilong-strategy' / 'SKILL.md',
    WORKSPACE / 'skills' / 'a-share-15d-selection' / 'SKILL.md',
    WORKSPACE / 'skills' / 'stock-analysis' / 'SKILL.md',
    WORKSPACE / 'skills' / 'stock-picking' / 'SKILL.md',
    WORKSPACE / 'skills' / 'stock-unified' / 'SKILL.md',
    WORKSPACE / 'skills' / 'stock-unified' / 'references' / 'mandatory-tq-verification.md',
]

BAD_PATTERNS = [
    (r"formula_process_mul_zb\('大牛线'", 'old_daniuxian_name'),
    (r"formula_process_mul_zb\('飞龙在天'", 'old_feilong_name'),
    (r'全部OK', 'stale_all_ok_claim'),
    (r'ErrorId=0全部通过', 'stale_all_pass_claim'),
    (r'ZB\+XG ErrorId=0', 'stale_xg_pass_claim'),
    (r'澶х墰|椋為緳|娓歌祫|鏈烘瀯|搴勫', 'mojibake_formula_text'),
]


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    findings = []
    for path in ACTIVE_TARGETS:
        text = path.read_text(encoding='utf-8', errors='replace') if path.exists() else ''
        for pattern, tag in BAD_PATTERNS:
            if re.search(pattern, text):
                findings.append({'path': str(path), 'tag': tag, 'pattern': pattern})
    payload = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'checked_files': [str(path) for path in ACTIVE_TARGETS],
        'finding_count': len(findings),
        'findings': findings,
    }
    out = REPORTS / f'runtime-truth-audit-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'report': str(out), 'finding_count': len(findings)}, ensure_ascii=False, indent=2))
    return 0 if not findings else 1


if __name__ == '__main__':
    raise SystemExit(main())
