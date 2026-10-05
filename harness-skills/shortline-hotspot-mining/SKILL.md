---
name: shortline-hotspot-mining
description: Use when the user names 短线热点挖掘、热点挖掘、题材发现、板块轮动、每日热点挖掘、热点龙头、主线板块或龙头股，并要求研究A股未来短线热点或候选板块内龙头。
---

# 短线热点未来预测

## 唯一边界

- 系统统一外部入口是 `python D:\C盘转移\日志\codex\scripts\stock_canonical_runtime.py route --query "<用户原始请求>"`。
- `route` 精确命中本技能后，由 canonical runtime 经本技能固定入口 `scripts/codex_entry.py run` 执行；`codex_entry.py` 是技能固定入口，不是系统外部唯一入口。
- `merged_workflow.run_forecast` 是技能内部唯一科学预测链。
- `components/` 中的旧源文件快照只用于来源追溯和完整性回归，不是可直接执行的业务入口。
- 本地通达信是板块池、冻结成分股和K线主数据；远程行情只能补充交叉验证，不能替代主数据进入候选排名。
- 新闻、政策、公告和监管证据必须在预测截止时点前已公开，并保留来源、发布时间、采集时间、反证和污染状态。
- 本技能只提供可审计的研究预测，不承诺收益，不生成买卖、仓位或自动交易指令。

## 单一连续预测链

1. 解析请求日期，冻结同一预测时点的点时快照，并生成一个 `snapshot_id`。
2. 只从快照截止时点及之前的数据生成特征；未来行情只用于训练标签和事后验真。
3. 分别预测 `H1`（T+1 至 T+3）、`H2`（T+4 至 T+7）、`H3`（T+8 至 T+10）板块进入综合活跃度前 10% 的概率。
4. 市场概率生成后才允许融合截止时点前的催化证据；低等级或污染证据不能制造高置信候选。
5. 龙头排序只能消费本轮 Top 候选板块及其冻结成员，且每条结果必须沿用同一 `snapshot_id`。
6. 点时快照、特征、预测、证据、龙头和清单由同一交付闸门核验；日期混用、未来信息、候选血缘断裂或产物哈希错误均返回 `BLOCKED`。

## 模式与固定入口

- `all`：完整预测、证据融合、候选内龙头排序和十项交付。
- `hotspot`：保留兼容名称，由同一预测链输出热点候选视图。
- `leader`：保留“热点龙头”兼容名称，龙头仍只能来自同一预测链的 Top 候选。

```text
python D:\C盘转移\日志\codex\scripts\stock_canonical_runtime.py route --query "<用户原始请求>"
python scripts/codex_entry.py run -- all [--date YYYYMMDD]
python scripts/codex_entry.py run -- hotspot [--date YYYYMMDD]
python scripts/codex_entry.py run -- leader [--date YYYYMMDD]
```

先由 `route` 精确解析技能，再由 canonical runtime 调用技能固定入口。运行前读取 `references/workflow.md`；不得直接执行 `components/` 或内部模块来绕开固定入口。

## 状态与完成闸门

- `forecast_status` 独立保留科学状态：`VALIDATED_FORECAST`、`PROVISIONAL_FORECAST`、`DEGRADED_FORECAST` 或 `BLOCKED`。
- `CLEAN_PASS` 只表示本轮预测链和交付链完整，不表示已通过样本外科学验证；不得把临时预测或降级预测改写成已验证。
- `requires_research_completion=true` 时完整模式必须阻断，不能返回 `CLEAN_PASS`。
- 最终结论必须由 canonical `authorize --receipt` 核验，不得以退出码、局部通过或文件存在代替授权。

## 十项交付

- `forecast_snapshot.json`
- `feature_snapshot.json`
- `forecast_rank.csv`
- `leader_rank.csv`
- `evidence.json`
- `model_card.json`
- `backtest_report.json`
- `audit.json`
- `manifest.json`
- `report.md`

`manifest.json` 必须绑定全部交付的路径、大小、SHA-256、目标交易日、`snapshot_id`、模型版本和 `forecast_status`。

## 验证

- 结构验证：运行技能创建器的 `quick_validate.py`。
- 科学预测回归：运行本技能 `tests/test_scientific_forecast.py`。
- 合同回归：运行统一股票技能的合并测试、合同完整性测试、全局预检及只读合同同步检查。
