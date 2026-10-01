---
name: technical-analysis
description: "本机股票技术分析强制工作流。凡请求涉及技术分析、技术面、技术指标、趋势、撑压或买卖节奏，默认必须同时真实执行大牛线撑压版、飞龙在天、庄家资金监控三个本机 TQ 公式，缺一不可。"
---

# 技术分析

掌财桌面端从 `ZHANGCAI_TDX_ROOT` 读取当前通达信目录，并从 `STOCK_SKILLS_ROOT` 定位技能；不得执行旧文档中的固定 C/D 盘路径。

## 三公式强制合同

凡涉及技术分析，必须同时执行：

1. `大牛线撑压版`
2. `飞龙在天`
3. `庄家资金监控`

三项均通过后才能形成技术分析结论。任一公式初始化失败、调用失败、返回空值或缺少
必需字段时，必须返回 `BLOCKED` 和非零退出码，且不得输出完整技术结论。

## 全子系统单表合同

每次联合分析必须穷尽并按固定顺序输出全部 `30` 行：

- `大牛线撑压版`：16 个子系统。
- `飞龙在天`：10 个子系统。
- `庄家资金监控`：4 个输出。

唯一对外表格固定列为：

`公式 | 序号 | 子系统/输出 | 当前值/证据 | 状态 | 结论 | 适用性/备注`

禁止删行、合并行、重复行、改变顺序、留空结论或拆成多张表。分析指数时，个股专属
子系统仍必须保留原行，并将状态写为 `指数不适用`。飞龙第 8 行的状态只允许
`金叉`、`未形成金叉`、`金叉状态不可判定`。

## 数据边界

- 唯一运行系统：本机 `$env:ZHANGCAI_TDX_ROOT` 与其 TQ 运行时。
- 禁止网页、东方财富、云端行情、OpenClaw 或其他系统。
- 禁止以 MA、MACD、RSI、自算 OHLCV 或其他公式替代任一必需公式。
- “庄家资金监控”只允许 `formula_set_data_info + formula_zb`，禁止批量公式接口和本地模拟回退。

## 固定入口

```powershell
python "$($env:STOCK_SKILLS_ROOT)\technical-analysis"\scripts\codex_entry.py selftest
python "$($env:STOCK_SKILLS_ROOT)\technical-analysis"\scripts\codex_entry.py run -- --code 600000.SH --json
```

业务执行器固定为 `scripts/entry_technical_analysis.py`。支持
`--test-fail-formula` 对三个公式逐项进行阻断验收。执行器必须先校验精确 `30` 行、
`16/10/4` 分组、固定身份与顺序、字段非空和唯一 Markdown 表格，再允许返回 `PASS`。

## 参考资料

- `references/business_spec.md`
- `references/workflow.md`
