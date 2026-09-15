# 执行与交付工作流

## 1. 数据准备

确定 `--as-of` 目标交易日、通达信目录和当日已确认涨停池。扫描器会忽略目标日之后的 `.day` 数据，防止历史复盘被未来数据污染。

`run` 必须显式提供 `--as-of`，禁止用固定旧日期作为默认值。通达信目录缺文件或涨停池 CSV 缺少必要表头时必须报错，不得静默输出空名单。

当日通达信数据已完整落盘时，`--fresh-limit-csv` 可省略；否则必须提供目标日涨停池 CSV。

## 2. 机械扫描

```powershell
python "$env:USERPROFILE\.codex\skills\old-leader-oversold-rebound\scripts\codex_entry.py" run `
  --as-of 2026-07-29 `
  --tdx C:\new_tdx_mock `
  --fresh-limit-csv .\fresh_zt_20260729.csv `
  --json .\old_leader_rebound_20260729.json `
  --csv .\old_leader_rebound_20260729.csv
```

输出中的 `old_class`：

- `strict_4_plus`：严格组，旧周期最高连板至少 4 板。
- `broken_4_in_10`：兼容组，10 日内至少 4 板但最高连板不足 4 板。

## 3. 催化核验

机械扫描后逐只核验，不得先写结论再找证据。证据优先级：交易所/公司公告、政府或监管文件、公司官方披露、可信财经媒体。记录最早公开时间，并与 `rebound_start` 比较。

## 4. 分类与输出

最终表至少包含：代码、名称、严格/兼容组、旧周期区间、旧周期最高连板、旧周期涨停数、累计涨幅、最大回撤、反弹形态、反弹涨停日期、催化日期、涨停核心逻辑、证据来源、时序判断、最终分类。

先列核心，再列观察，最后简述剔除项及原因。不得把无启动前/同期催化的机械候选写成核心。

## 5. 回归自检

```powershell
python "$env:USERPROFILE\.codex\skills\old-leader-oversold-rebound\scripts\codex_entry.py" selftest `
  --as-of 2026-07-29 `
  --tdx C:\new_tdx_mock `
  --fresh-limit-csv .\fresh_zt_20260729.csv `
  --baseline-csv .\audit_v6_final_20260729.csv
```

回归必须同时满足：候选总数一致、逐行逐字段一致、金牛化工和赤天化均存在且均为 `broken_4_in_10`。
