---
name: zhuangjia-capital-monitoring
description: "本机通达信/TQ“庄家资金监控”公式独立执行技能。用于庄家资金监控、控盘程度、控盘度等请求；只读取 C:\\new_tdx_mock 已安装公式，禁止网页、云端行情或本地 OHLCV 模拟替代。"
---

# 庄家资金监控

## 固定边界

- 唯一数据与公式系统：本机 `C:\new_tdx_mock`。
- 唯一公式：TQ 注册名 `庄家资金监控`。
- 唯一调用方法：先执行 `formula_set_data_info`，再执行 `formula_zb`。
- 固定参数：`N=35`、`M=0`、`N1=3`，公式源码位于 `C:\new_tdx_mock\T0002\gs_bak\庄家资金监控.txt`。
- 禁止 `formula_process_mul_zb`，禁止根据本地 K 线重新计算或模拟公式结果，禁止网络或云端数据源替代。

## 固定入口

```powershell
python D:\C盘转移\日志\codex\skills\zhuangjia-capital-monitoring\scripts\codex_entry.py selftest
python D:\C盘转移\日志\codex\skills\zhuangjia-capital-monitoring\scripts\codex_entry.py run -- --code 600000.SH --json
```

业务执行器为 `scripts/call_zhuangjia_tq.py`。正常结果必须为 `PASS`，并包含
`OUTPUT3`、`OUTPUT4`、`控盘程度`、`控盘度` 四个字段；任一步失败或字段缺失都必须
返回 `BLOCKED` 和非零退出码。

## 全输出单表合同

联合技术分析时必须调用 `build_subsystem_rows()`，按固定顺序保留四行：
`OUTPUT3`、`OUTPUT4`、`控盘程度`、`控盘度`。禁止合并、去重或遗漏绘图输出行。
四行由 `technical-analysis` 并入唯一 29 行总表；不得另建第二张对外表格。

## 解释口径

- `控盘程度`、`控盘度` 是本公式的资金监控字段。
- `OUTPUT3`、`OUTPUT4` 是公式绘图输出，与前述字段存在重复表达，不得解释成额外独立资金指标。

## 参考资料

- `references/workflow.md`
- `references/formula-map.md`
- `references/business_spec.md`
