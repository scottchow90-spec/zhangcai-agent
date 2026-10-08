# V6.5 发布验收

必须全部通过：
```bash
python scripts/workbuddy_entry.py verify
python scripts/workbuddy_entry.py selftest
python scripts/workbuddy_entry.py deep-audit
python scripts/workbuddy_entry.py offline-e2e
python scripts/workbuddy_entry.py doctor
python scripts/consensus_engine.py selftest
python scripts/consensus_engine.py execute --bundle evidence/2026-09-11_consensus_bundle.json
```

重点回归：退出码4不得终止；同源二源必须拒绝；模拟数据必须拒绝；原生核心历史门必须与代码一致为120根；250根增强不应被伪装成全局硬门；共识路径不得冒充原生四模型；二源价格匹配率必须100%；13步必须13/13。
