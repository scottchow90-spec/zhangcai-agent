#!/usr/bin/env python3
from pathlib import Path
import re, sys
root=Path(__file__).resolve().parents[1]
required=[root/'SKILL.md',root/'references'/'tongdaxin-v8.txt',root/'references'/'data-schema.md',root/'references'/'decision-rules.md',root/'references'/'regression-2026-09-11.md',root/'scripts'/'run_v8.py',root/'templates'/'result-template.md']
missing=[str(x) for x in required if not x.exists()]
if missing: raise SystemExit('缺失: '+','.join(missing))
text=(root/'SKILL.md').read_text(encoding='utf-8')
if not text.startswith('---\n'): raise SystemExit('SKILL.md缺少YAML frontmatter')
fm=text.split('---',2)[1]
if 'name: golden-ignition-strategy' not in fm or 'version: 8.0.0' not in fm: raise SystemExit('frontmatter异常')
formula=(root/'references'/'tongdaxin-v8.txt').read_text(encoding='utf-8')
if formula.count('XG:')!=1 or '模型C：黄金点火 V8' not in formula: raise SystemExit('公式异常')
print('OK: 黄金点火策略 WorkBuddy V8 package structure and formula checks passed')
