---
name: a-share-intraday-position-monitor
description: "本机Codex的A股盘中持仓监控方案生成技能。用于用户提出盘中实时监控持仓股、持仓预警、成本线监控、分级风险线、按股票代码/持仓成本/持股数量生成监控方案，或显式调用 $a-share-intraday-position-monitor；刷新目标股票行情与支撑压力，换算实际持仓盈亏，生成分级价位、数据故障保护和人工确认规则。只生成可执行监控方案与内部JSON/Markdown结果，不承诺收益、不自动下单，也不把未启动的实时守护程序表述为已运行。"
---

# 持仓股监控技能

用户可见名称固定为“持仓股监控技能”；内部调用标识保持 `$a-share-intraday-position-monitor`。

## 边界

- 目标系统固定为本机 Codex，不调用 OpenClaw。
- 只通过本技能 `scripts/codex_entry.py` 进入业务流程。
- 技术位置固定调用 `support-pressure-analysis-system` 的 Codex 入口，不复制或临时重写五方法算法。
- 输出是一次新鲜行情快照对应的监控方案；持续实时守护、Windows弹窗送达、券商账户联动和自动下单不在本技能已实现范围。
- 默认只在聊天中交付结论；内部 JSON/Markdown 用于持久化与读回，不直接发布为股票文件。
- 用户另行要求 DOCX、PDF、PPTX 或表格文件时，必须同时使用 `stock-delivery-risk-gate` 和相应 Office/文件技能。

## 固定入口

```powershell
python D:\C盘转移\日志\codex\skills\a-share-intraday-position-monitor\scripts\codex_entry.py info
python D:\C盘转移\日志\codex\skills\a-share-intraday-position-monitor\scripts\codex_entry.py selftest
python D:\C盘转移\日志\codex\skills\a-share-intraday-position-monitor\scripts\codex_entry.py run -- --symbol 301372 --cost 25 --shares 200000 --name 科净源
```

可选参数：

- `--benchmark`：指数代码；未传时按股票市场自动选择。
- `--name`：股票名称；建议传入，用于股票技能执行凭证的目标身份绑定。
- `--out-dir`：内部运行结果目录。
- `--run-id`：本轮运行标识。
- `--stock-attestation`：`auto|required|off`；Codex 任务内默认自动生成并登记股票技能执行凭证，正式验收使用 `required`。

## 工作流

1. 验证六位 A 股代码、正成本和正整数持股数量。
2. 选择基准指数：`300/301` 使用创业板指，`688` 使用科创50，其余深市使用深证成指，沪市使用上证指数。
3. 从 `support-pressure-analysis-system` 固定入口运行 `pressure` 模式，显式传入目标代码与基准指数。
4. 要求目标代码精确匹配、分析状态为 `PASS`、无 fallback，并读回持久化 `workflow_report.json`。
5. 读取最新价、ATR14、五方法得分、共振位、主支撑、主压力、突破线和跌破线。
6. 计算本金、市值、浮动盈亏、收益率以及每 0.01 元、每 1 元、成本 1% 对应的盈亏变化。
7. 生成下行监控线：最近共振支撑、江恩下方前两级、成本线、主结构支撑和跌破触发线；按 0.5% 容差去重。
8. 生成上行观察线：江恩上方前两级、最近高强度共振、主压力和突破触发线；按 0.5% 容差去重。
9. 加入行情不超过 5 秒、双源偏差不超过 0.3%、VWAP、成交量、持续时间、相对强弱、人工确认和不自动下单规则。
10. 写入 `monitor_result.json`、`monitor_summary.md` 与 `validation.json`，随后执行持久化读回。
11. 在 Codex 任务内生成 `stock_skill_integration_consumer.json` 和 `stock_skill_execution_receipt.json`，绑定当前任务、目标代码、最新交易日、新技能结果、支撑压力依赖结果及各自固定入口，并调用股票新鲜度门禁执行 `verify-receipt` 与 `attest`。

## 结果使用

- 将事实、计算、推断、风险和未验证项分开。
- 技术价位只作为告警锚点；单一价位不得直接等同于买卖指令。
- 当综合信号矛盾、威科夫闸门未通过或数据源异常时，提高确认要求，不给确定性方向结论。
- 若原始“第二支撑”高于最新价，判定其语义无效并排除；强共振直接读取 `confluence_zones[].count/strength`，不依赖旧 D8 字段。
- 需要解释价位来源、权重或算法时，读取 `references/methodology.md`。

## 验证

- 结构：运行 `skill-creator/scripts/quick_validate.py`。
- 静态：运行固定入口 `selftest`，必须返回 `CLEAN_PASS`。
- 业务：用用户参数从固定入口实跑，目标代码、成本、数量、结果路径和公式读回必须一致。
- 读回：运行 `scripts/verify_result.py --result <monitor_result.json> --validation <validation.json>`，必须返回 `CLEAN_PASS`。
- 安装：运行 `scripts/verify_installation.py` 绑定结构校验、自检和一份真实前向结果，必须返回 `CLEAN_PASS`。
- 完成边界：只有一次性方案生成与持久化读回可声明完成；实时守护与弹窗送达必须标记 `not verified`，除非后续单独实现并验证。
