# 五维共振选股 唯一工作流

CODEX_LOCAL_ENTRY

NO_REDISCOVERY: true

NO_CROSS_JUMP: true

LOCKED_ENTRY: scripts/codex_entry.py
LOCKED_EXECUTION: scripts/codex_entry.py selftest

## 固定链路

1. 路由：按注册表唯一关键词规则选择本技能，不设 fallback。
2. 入口：只允许 `scripts/codex_entry.py run`，入口仅转交唯一执行器。
3. 前置硬闸：执行器依次运行 `skill_workflow_lock`、`stock_workflow_substantive_gate`、`stock_skill_content_gate`，任何一个不是 `CLEAN_PASS` 即 `BLOCKED`。
4. 模板：执行器读取注册表中的 `template_policy/templates` 并逐个校验存在性、字节数和 SHA-256；`none` 表示该技能不使用模板。
5. 数据：执行器直接实跑 TDX status、公式 registry 与 120 根日 K 线，并在本轮 `run_dir` 刷新短线侠、当日连板网及最近三个连板网交易日；资金扩张从通达信同一活跃股集合的今/昨日成交额计算，禁止用静态文件存在替代数据执行。
6. 业务：执行 `selection` 固定适配器，并在 full 模式运行注册表锁定的旧业务实现（若登记为 required）；禁止临场选脚本。
7. 产物：写入本轮 `business_result.json`，必须含真实数据源、最新交易日、指标、结论和风险边界；逐股结果必须包含 `mainline_scoring` 的九项板块分、两条硬门槛结果、个股正宗度和缺失证据。
8. 主线硬闸：板块评分必须绑定 `scripts/mainline_scoring.py`，个股维度取 `min(板块星级, 个股正宗度星级)`；任何必需证据缺失均归零并阻断决策资格，禁止按个股涨幅回退。
9. 验收：只允许 `scripts/codex_entry.py selftest --manifest <本轮manifest>` 调用唯一验证器；注册表摘要、入口、流程、模板、三道前闸、数据、业务产物、旧业务实现和执行器身份全部一致才返回 `CLEAN_PASS`。
10. Codex 运行时：`openclaw-stock-execution-gate-v3` 在模型调用前准备唯一 request，在工具调用时阻断旧入口，在最终回复前核对同一 request 的 manifest；没有证据只能显示 `BLOCKED`。

## 执行完成与决策授权

- 报告必须分别输出 `status` 和 `decision_status`，禁止用“是否出现可决策候选”替代“业务链是否真实执行”。
- `CLEAN_PASS + SIGNAL_FOUND`：至少一只候选的板块与个股两道证据闸门均通过。
- `CLEAN_PASS + NO_SIGNAL`：全部候选个股正宗度完整，且全部候选只因完整证据下的主线硬门槛失败而不可决策。
- `CLEAN_PASS + DATA_REQUIRED`：扫描和来源执行完整、个股正宗度完整，但仍存在板块证据缺口。只授权执行审计，不授权候选结论。
- 来源缺失、个股正宗度缺失、公式或扫描未完成时，执行状态不得为 `CLEAN_PASS`。
- 公式历史事实复用只解决 TQ 公式不可用，不复用旧业务结论或旧合同授权。登记权威为 runner 内置哈希固定的证据清单；执行器封闭清单固定包含 `tdx_hub.py`、TQ 初始化脚本、`tqcenter.py` 与保留公式源码。当前 runner 与正式适配器必须对同交易日、同候选顺序、同 K 线文件指纹、同公式执行器文件指纹、来源扫描产物哈希、来源回执哈希和不可变会话证据行哈希逐项复算；还必须从历史来源回执绑定的 `business_result.json` 读取原报告路径，并与不可变会话行记录的原路径及产物哈希交叉核对。验证通过后，当前 runner 生成确定性 `reuse_evidence_manifest`，固定 `reuse_scope=raw_scan_only` 与公式名称/顺序，且当前 `business_result.json` 内嵌清单及哈希，本轮新回执通过该 required artifact 的 SHA-256 绑定清单。只允许从已验证恢复副本读取白名单内原始 `raw_scan`；任一脱链或指纹不一致整包拒绝。旧合同哈希不用于授权本轮结论；复用后仍按当前合同重新执行主线、风险、评分、报告、回执和授权。

## 唯一命令

```powershell
python D:\C盘转移\日志\codex\skills\five-dimension-resonance\scripts\codex_entry.py run
```

其他脚本只作为注册表明确锁定的内部业务实现，不是入口，也不得由模型直接调用。

## 科学工作流硬闸（2026-06-28）

本技能的唯一执行器固定覆盖以下完整链条：

- 数据与来源证据：TDX/通达信真实数据、时间窗、路径和 SHA-256。
- 宏观：指数、成交、涨跌家数、市场宽度、大盘与风险偏好。
- 微观：公告、业绩、订单、产业链、个股与板块。
- 新闻舆情：新闻、公告、政策、事实、观点、传闻与舆情分层。
- 技术：涨停、连板、炸板、趋势、量价、K线、支撑与压力。
- 资金：资金、主力、龙虎榜、机构、游资与散户。
- 决策：结论、评分、排序、过滤、剔除与 Top 候选。
- 风险：风险、失效、降级、排除；任何缺口必须阻断决策资格，并按上面的执行/决策双状态如实归类。
- 验收：验证、selftest、gate、CLEAN_PASS/BLOCKED 和本轮 manifest。

- 复核归档：生成验收摘要与 audit 记录，完成收尾后才允许交付。
