---
name: core-mainline-scoring-system
description: "Use when the user asks for 核心主线评分、核心主线评分系统、核心主线确定逻辑, CORE-MAINLINE-100-V2 raw scoring, or CORE-MAINLINE-CLOSE-V3 close-confirmed board-level scoring."
---

# 核心主线评分系统

本技能是板块级核心主线评分的独立所有者。它不执行个股选股，也不把候选股涨幅、涨停身份或默认行业当作板块主线证据。

## 固定业务规则

- 使用 `CORE-MAINLINE-CLOSE-V3`；其中 `CORE-MAINLINE-100-V2` 九项100分完整保留为原始候选强度层，完整规则见 `references/scoring-model.md`。
- 原始分之后必须独立执行两道硬门槛：精确3板、2板、1板同时存在；可靠匹配的本地通达信完整成分股严格大于100只。
- 两道硬门槛通过后必须执行收盘确认层：原始分、板块排名、涨停市场占比、短线侠/连板网当日样本一致性、分时样本数量与覆盖率全部达标，并且早封、零开板、尾盘回封、封单额/成交额四项相对当日全市场基线至少两项不弱。
- 必需证据缺失时为 `DEGRADED`、决策分0、不得重分配权重；收盘确认不通过时保留 `raw_score`，但标记 `CLOSE_UNCONFIRMED` 且不得入选。
- 硬门槛失败时保留 `raw_score`，但决策分与星级归零并标记 `GATE_FAILED`。
- 若收盘确认后的前两名质量信号数相同且原始分差不超过5分，必须标记 `AMBIGUOUS_CLOSE` 并放弃强行指定唯一主线。
- 市场动态数据必须在当前任务重新获取；通达信为本地主源，短线侠和连板网为补充与交叉验证来源。
- 短线侠涨停池第8列是当日成交额，第9列是流通市值；两者禁止混用。第3/4/5/12列分别用于封单额、开板次数、最终封板时刻和首次封板时刻。
- 最近交易日连板网页面的逐股题材与理由只有在快照为 `CLEAN_PASS`、交易日和原页链接完整时，才可补充个股主题正宗度。历史证据不得改写当前板块评分成员、当日连板层级、当前涨停状态、主营核验或公告核验。

## 执行

所有业务执行必须通过 `scripts/codex_entry.py run`。固定业务入口为 `scripts/run_core_mainline_scoring.py`，结果写入当前运行目录的 `core-mainline-result.json`，并由规范回执绑定。

需要8K海报时，通过规范业务参数 `--poster` 生成。海报必须遵循 `POSTER_TEMPLATE.md`，先写入候选目录，并同时通过 `scripts/poster_validator.py` 与全局浅色背景硬闸后才能进入 `deliverables`；海报哈希和验证结果写入同次 `business_result.json` 供回执授权。

读取 `references/workflow.md` 获取输入、输出和失败边界；需要核对分值时读取 `references/scoring-model.md`。

本技能只提供研究辅助，不构成确定性投资建议。
