# 短线热点未来预测统一流程

## 入口与来源

1. 系统统一外部入口是 `python D:\C盘转移\日志\codex\scripts\stock_canonical_runtime.py route --query "<用户原始请求>"`。
2. `route` 精确命中 `shortline-hotspot-mining` 后，由 canonical runtime 调用技能固定入口 `scripts/codex_entry.py run -- all|hotspot|leader [--date YYYYMMDD]`；`codex_entry.py` 不是系统外部唯一入口。
3. 技能顶层编排只进入 `merged_workflow.run_forecast`；三个模式是同一连续预测链的兼容视图，不是互相拼接的旧流程。
4. `components/` 只保存原始来源快照和 SHA-256 追溯证据，不得直接执行，也不得作为正常业务链的替代入口。

## 连续预测步骤

1. 解析请求日期到最近有效交易日，以本地通达信板块、冻结成分和行情文件建立点时快照，并生成唯一 `snapshot_id`。
2. 所有强结论数据必须与解析交易日一致；混合日期、未来日期、未来信息或主数据覆盖不足时返回 `BLOCKED`。
3. 从截止时点及之前的数据生成市场、板块、广度、活跃度、涨停结构、持续性、风险和缺失指示特征。
4. 使用独立窗口预测 `H1`（T+1 至 T+3）、`H2`（T+4 至 T+7）、`H3`（T+8 至 T+10）的未来热点概率，并保存基础概率、证据调整、最终概率、解释和 `forecast_status`。
5. 市场预筛后才读取截止时点前的催化证据；证据必须可追溯，污染证据不能提高概率。
6. 龙头排序只读取本轮 Top 候选和对应冻结成员；结果的板块、股票代码和 `snapshot_id` 必须能回溯到同一点时快照。
7. 最后统一生成产物、构建 `manifest.json`，再读回校验每个文件的大小和 SHA-256。

## 科学状态与执行状态

- `forecast_status` 必须是 `VALIDATED_FORECAST`、`PROVISIONAL_FORECAST`、`DEGRADED_FORECAST` 或 `BLOCKED`，并原样进入 canonical 回执。
- `CLEAN_PASS` 只证明本轮点时、预测、证据、龙头及交付链完整；它不授予科学验证状态。
- 样本外门槛不足时保留 `PROVISIONAL_FORECAST`，漂移或非关键证据缺失时保留 `DEGRADED_FORECAST`。
- `requires_research_completion=true`、日期不一致、未来信息污染、候选血缘断裂、必需产物缺失或哈希错误时必须 `BLOCKED`。

## 十项交付

完整链固定交付：

1. `forecast_snapshot.json`
2. `feature_snapshot.json`
3. `forecast_rank.csv`
4. `leader_rank.csv`
5. `evidence.json`
6. `model_card.json`
7. `backtest_report.json`
8. `audit.json`
9. `manifest.json`
10. `report.md`

所有交付必须位于本轮 canonical run directory，使用同一目标交易日和 `snapshot_id`。只有 canonical `authorize --receipt` 同时核验运行回执与产物绑定后，才可输出最终结论。
