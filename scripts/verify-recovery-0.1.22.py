#!/usr/bin/env python3
"""Verify supplied recovery hashes, preserved frontend, and packaging versions."""
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    audit = json.loads((root / 'docs/recovery-0.1.22/audit.json').read_text())
    failures = []
    records = audit['files'] + audit['frontendPreserved'] + audit['localChanges']
    for item in records:
        path = root / item['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            failures.append(item['path'])
    for item in audit['excludedRuntimeArtifacts']:
        path = root / item['path']
        if item['baseSha256'] is None:
            if path.exists():
                failures.append(item['path'] + ': excluded artifact reintroduced')
        elif not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['baseSha256']:
            failures.append(item['path'] + ': base runtime artifact changed')
    expected_dist = {item['path'] for item in audit['files'] if item['path'].startswith('dist/')}
    actual_dist = {p.relative_to(root).as_posix() for p in (root / 'dist').rglob('*') if p.is_file()}
    if actual_dist != expected_dist:
        failures.append('dist/: compiled evidence file set differs')
    for name in ['package.json', 'packaging/runtime-app-package.json', 'packaging/electron/package.json']:
        if json.loads((root / name).read_text())['version'] != '0.1.22':
            failures.append(name + ': incorrect product version')
    for name in ['electron-app/runtime-manifest.json', 'packaging/runtime-manifest.json']:
        if json.loads((root / name).read_text())['packageVersion'] != '0.1.22':
            failures.append(name + ': incorrect package version')
    if (root / 'packaging/environment-baseline-version.txt').read_text() != '0.1.9\n':
        failures.append('runtime baseline must remain 0.1.9')
    builder = (root / 'electron-app/electron-builder.yml').read_text()
    for needle in ['dist-installer/releases/0.1.22', 'packaging/staging/site-build-0.1.22/dist',
                   'electron-app/tdx-root.mjs', 'from: skill-archives', 'to: app/skill-archives']:
        if needle not in builder:
            failures.append('electron-builder.yml: missing ' + needle)
    print(json.dumps({'status': 'FAIL' if failures else 'PASS',
                      'recoveredFiles': len(audit['files']),
                      'frontendFilesPreserved': len(audit['frontendPreserved']),
                      'runtimeArtifactsExcluded': len(audit['excludedRuntimeArtifacts']),
                      'failures': failures}, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
