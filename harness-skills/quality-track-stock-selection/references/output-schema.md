# 持久化输出

默认目录：`D:\C盘转移\日志\codex\skills\quality-track-stock-selection\run`

## practical_selection.json

- `status`：`PASS`、`PARTIAL_PAPER_ELIGIBLE`、`NO_PAPER_ELIGIBLE` 或 `NO_TRADE`。
- `freshness`：完整交易日覆盖率与盘中部分日期排除证据。
- `counts`：股票、概念、赛道、初筛、补充验证、买入和观察数量。
- `selected_sectors` / `watch_sectors`：赛道评分与每个硬门槛。
- `selected_candidates`：纸面可执行候选。
- `watch_candidates`：主营已确认但仍有复核原因的观察候选。
- `enriched_candidates`：前30名外部证据补充结果。
- `portfolio_plan`：组合暴露和风险预算。

## execution_backtest.json

- `status`：所有就绪检查同时通过才为 `PASS`。
- `metrics`：周期数、交易数、策略与基准收益、超额收益、回撤、胜率、单笔均值。
- `readiness_checks`：样本、成本、无未来数据、超额收益、回撤和胜率门槛。
- `biases` / `not_validated`：回测覆盖边界。

## paper_ledger.json

记录纸面候选或 `NO_TRADE_RECORDED`。不会连接交易账户，也不会自动下单。

## backtest_stability.json

比较当前交易日与前一交易日回测中的共同信号。共同周期和共同交易必须完全一致，用于阻断“窗口移动一天导致整套历史信号换位”的错误。

## skill_status.json

固定入口的聚合状态。包含选股状态、观察名单、回测状态、部署边界以及所有业务结果文件的当前 SHA-256 和大小。

## status_readback.json

由 `codex_entry.py status` 生成。只有 `status=PASS` 且所有哈希与大小匹配，才证明持久化结果仍与技能状态一致。
