# 3003 本地评分适配契约

3003 的策略选股入口 `scripts/selection_score_runtime.py` 只负责把已经落盘的数据送入本技能的原始 `engine.py`，不修改四模型、行业六维或生产授权门槛。

## V6.5 行业输入

- 候选行业成员来自 `app-data/runtime/market-latest.json` 的 `allStocks`，按 TDX `industryCode` 分组；缺少代码时才回退到行业名称。
- 成员日线来自 `ZHANGCAI_TDX_ROOT/vipdoc/<market>/lday/<symbol>.day`，按目标交易日截断，不能把网页当前快照当作历史行业 K 线。
- 行业 K 线由实际成员日线构建等权归一化行业指数，仅用于行业强度计算；原始个股日线、OHLC、成交额和目标日期不被改写。
- 运行回执必须写出行业成员数、可用历史成员数、行业 K 线根数、事件覆盖状态和来源路径。

## 硬门和降级

- 行业六维至少需要 21 根行业 K 线；消息/政策/产业事件没有同日、可核验的记录时，`events_covered=false`，原始引擎返回 `UNKNOWN_ENVIRONMENT`，不得用空事件放行。
- 只有原始引擎返回 `model_labels` 且 `primary_model` 非空，才是主模型真实触发。
- `primary_model_candidate` 仅表示已通过个股核心结构、正在等待行业或其他硬门闭合，不能当作触发标签。
- `score`/`model_scores` 是原始四模型分量分数；分量分数达到阈值不等于生产授权，也不应被页面渲染成主模型触发。
- 本地数据不足时保留 `DEGRADED` 或 `UNKNOWN`，不得模拟换手率、流通市值、消息覆盖、二源核价或主模型结果。

## 页面诊断

3003 页面应同时显示：触发标签、主模型或“待闭合：模型名”、个股拒绝原因，以及每个模型的 `TRIGGERED`、`CORE_NOT_TRIGGERED`、`UNKNOWN_ENVIRONMENT`、`ENVIRONMENT_REJECTED` 或 `SCORE_NOT_REACHED` 状态，避免把不同阻断原因统一显示为“无主模型”。
