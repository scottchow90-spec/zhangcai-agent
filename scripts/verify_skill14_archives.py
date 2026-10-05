#!/usr/bin/env python3
"""Check all declared Skill14 ZIPs against independently recorded release hashes."""
import os
import tempfile
from pathlib import Path

from release_verification import app_root, digest, emit, read_json
import skill14_data_runtime as runtime


def verify(root, archive_root):
    errors, checked = [], []
    catalog = read_json(root / 'config/skill14-catalog.json')['skills']
    lock = read_json(root / 'config/skill14-archive-lock.json')['archives']
    expected = {row['id']: row for row in lock}
    if len(catalog) != 14 or len(lock) != 14 or len(expected) != 14 or {row['id'] for row in catalog} != set(expected):
        raise ValueError('Skill14 catalog/lock must contain exactly fourteen unique IDs')
    for row in catalog:
        record = expected[row['id']]
        name = row['archive']
        if name != record['archive'] or Path(name).name != name or '\\' in name:
            errors.append(f"{row['id']}: archive mapping differs from release lock")
            continue
        archive = archive_root / name
        try:
            if not archive.is_file():
                raise ValueError(f'missing archive: {name}')
            if archive.stat().st_size != record['bytes'] or digest(archive) != record['sha256']:
                raise ValueError(f'archive hash/size mismatch: {name}')
            with tempfile.TemporaryDirectory(prefix='zhangcai-archive-check-') as temp:
                destination = Path(temp)
                with runtime.open_skill_zip(archive) as bundle:
                    corrupt = bundle.testzip()
                    if corrupt:
                        raise ValueError(f'ZIP CRC failed: {corrupt}')
                    runtime.extract_skill_zip(bundle, destination)
                    try:
                        skill_root = runtime.primary_skill_root(destination)
                    except RuntimeError as error:
                        if '没有找到主 SKILL.md' not in str(error):
                            raise
                        runtime.extract_nested_skill_archives(bundle, destination)
                        skill_root = runtime.primary_skill_root(destination)
                skill_name = runtime.skill_frontmatter_name(skill_root)
            checked.append({'id': row['id'], 'archive': name, 'sha256': record['sha256'], 'skill_name': skill_name})
        except Exception as error:
            errors.append(f"{row['id']}: {type(error).__name__}: {error}")
    return {'schema': 'ZHANGCAI_SKILL14_ARCHIVE_VERIFICATION_V1',
            'status': 'CLEAN_PASS' if not errors and len(checked) == 14 else 'BLOCKED',
            'checked_count': len(checked), 'expected_count': 14, 'archives': checked, 'errors': errors}


def main():
    try:
        root = app_root()
        result = verify(root, Path(os.environ.get('ZHANGCAI_SKILL_ARCHIVE_DIR', root / 'skill-archives')))
    except Exception as error:
        result = {'status': 'BLOCKED', 'checked_count': 0, 'errors': [f'{type(error).__name__}: {error}']}
    return emit(result)


if __name__ == '__main__':
    raise SystemExit(main())
