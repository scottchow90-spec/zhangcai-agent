"""Shared helpers for newly authored, offline release checks (not recovered source)."""
import hashlib
import json
import os
import re
from pathlib import Path


def app_root():
    return Path(os.environ.get('ZHANGCAI_RELEASE_APP_ROOT', Path(__file__).resolve().parents[1])).resolve()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def stock_skill_ids(root):
    value = read_json(root / 'config/stock-detail-release.json')
    ids = value['skills']
    if not isinstance(ids, list) or any(not isinstance(s, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', s) for s in ids) or len(ids) != 10 or len(set(ids)) != 10:
        raise ValueError('Invalid ten-skill stock detail release catalog')
    return ids


def emit(report):
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] in ('CLEAN_PASS', 'STATIC_PASS') else 1
