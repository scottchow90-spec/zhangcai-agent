---
name: old-leader-oversold-rebound
description: 固化近一年A股老龙头超跌反弹选股流程。用于用户提出老龙头超跌反弹、历史题材龙头大回撤后二连板、3天2板、金牛化工或赤天化同类筛选、复核漏票及涨停核心逻辑分析时；先运行机械扫描，再核验反弹启动前或同期催化，最终分为核心、观察、剔除。
---

# 老龙头超跌反弹

## 执行原则

本技能只处理“近一年老龙头大幅回撤后再次连续涨停”的识别与复核。必须先机械扫描，再做催化核验，禁止用反弹后的公告倒推启动原因。

完整业务口径见 [references/business_spec.md](references/business_spec.md)，执行步骤和交付字段见 [references/workflow.md](references/workflow.md)。

## 唯一入口

使用当前 Python 运行：

```powershell
python "$env:USERPROFILE\.codex\skills\old-leader-oversold-rebound\scripts\codex_entry.py" info
python "$env:USERPROFILE\.codex\skills\old-leader-oversold-rebound\scripts\codex_entry.py" selftest
python "$env:USERPROFILE\.codex\skills\old-leader-oversold-rebound\scripts\codex_entry.py" run --as-of 2026-07-29 --tdx C:\new_tdx_mock --fresh-limit-csv <当日涨停池.csv> --json <结果.json> --csv <结果.csv>
```

不得绕过 `scripts/codex_entry.py` 直接另写扫描逻辑。需要复核历史基准时，给 `selftest` 传入 `--tdx`、`--fresh-limit-csv` 和 `--baseline-csv`。

## 固定流程

1. 运行 `info`，确认技能版本与固定口径。
2. 运行 `run`，得到机械候选池及严格组/兼容组标记。
3. 对每个机械候选核验反弹启动日前或同期的公告、政策、行业事件和可追溯新闻。
4. 逐只写“涨停核心逻辑”，至少包含催化日期、事件、题材映射、证据来源和时序判断。
5. 按规范分为核心、观察、剔除；不得把机械入池直接等同于最终推荐。
6. 交付前检查金牛化工、赤天化：若入池，二者必须是兼容组，不得标成旧周期4连板。

## 数据边界

- 通达信日线用于历史行情和连板结构。
- 当日 `.day` 尚未落盘时，必须提供已确认的当日涨停池 CSV；不得用未经确认的盘中触板代替收盘涨停。
- 若用户要求当前结果，必须用目标交易日数据重跑，禁止沿用旧名单。
- 浏览器核验确有需要时，按本机规则只使用用户的 Google Chrome。

