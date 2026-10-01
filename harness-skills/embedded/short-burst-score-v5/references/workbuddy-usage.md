# WorkBuddy 使用 V5.0

技能目录根部为 `SKILL.md`，代码、参考资料和模板分别位于 `scripts/`、`references/`、`templates/`。

```bash
python scripts/workbuddy_entry.py verify
python scripts/workbuddy_entry.py doctor
python scripts/workbuddy_entry.py selftest
python scripts/workbuddy_entry.py audit-data --data-root data_raw --require-end 2026-09-10
python scripts/workbuddy_entry.py prepare-snapshot --data-root data_raw --trade-date 2026-09-10 --as-of 2026-09-10T21:00:00+08:00 --output snapshot.json
python scripts/workbuddy_entry.py analyze --input snapshot.json --format markdown
```

`prepare-snapshot` 会再次强制执行原始数据审计，不能因为已经运行过 `audit-data` 就省略内部检查。若目录中出现盘中/竞价数据目录、缺关键日线数据或截止日期不足，快照生成失败。

Markdown默认是完整版，包含工作流执行审计、数据覆盖、市场总闸门、全候选短线爆发力评分、六维分项、风险扣分和逐股证据链。展示层即使压缩，也不能跳过底层评分步骤。

日常 `analyze` 仅依赖Python标准库；原始数据管线需要 pandas/numpy；Tushare下载器额外需要 tushare 和 `TUSHARE_TOKEN`。下载器仅提供盘后接口白名单。

本次审计修订保持原技能名称与入口。实际候选是T日龙虎榜股票；合法空榜日输出空候选。历史CSV只用于研究参考，不能自报生产通过。下载默认截至中国标准时间当天；指数数据会刷新请求日期范围，None或失败不会写成空榜。Python及依赖版本要求见python-dependencies.md。
