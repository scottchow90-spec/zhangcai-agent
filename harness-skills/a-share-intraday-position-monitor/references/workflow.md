# 盘中持仓监控唯一工作流

LOCKED_ENTRY: scripts/codex_entry.py

LOCKED_EXECUTOR: scripts/monitor_workflow.py

LOCKED_ACCEPTANCE: monitor_result.json + validation.json + stock_skill_execution_receipt.json

1. 外部只调用 `scripts/codex_entry.py info|selftest|run`。
2. `run` 必须显式接收目标代码、成本和股数，不允许默认代码或默认持仓。
3. 执行器只通过 `support-pressure-analysis-system/scripts/codex_entry.py` 获取同一目标的科学支撑压力报告。
4. 下游从 `run_summary.json` 定位目标 artifact，不猜测旧产物名，不直调兄弟内部脚本。
5. 结果、支撑报告、目标、交易日和当前哈希全部进入股票技能执行收据并通过验收。
6. 本技能只生成一次性监控方案；持续守护、弹窗、券商联动和自动下单均保持 `not verified` 或 `false`。
