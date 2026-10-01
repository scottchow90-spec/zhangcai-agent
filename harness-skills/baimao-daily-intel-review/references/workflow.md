# 白猫老师每日资讯及复盘报告 唯一工作流

CODEX_LOCAL_ENTRY

NO_REDISCOVERY: true

NO_CROSS_JUMP: true

LOCKED_ENTRY: scripts/codex_entry.py
LOCKED_EXECUTION: scripts/codex_entry.py selftest

## 固定链路

1. 路由：按注册表唯一关键词规则选择本技能，不设 fallback。
2. 入口：只允许 `scripts/codex_entry.py run -- --evidence <本回合证据包> --mode <模式>`；缺少 `--evidence` 的裸运行在采集前阻断。
3. 前置硬闸：执行器依次运行 `skill_workflow_lock`、`stock_workflow_substantive_gate`、`stock_skill_content_gate`，任何一个不是 `CLEAN_PASS` 即 `BLOCKED`。
4. 模板：执行器读取注册表中的 `template_policy/templates` 并逐个校验存在性、字节数和 SHA-256；`none` 表示该技能不使用模板。
5. 数据：执行器直接实跑 TDX status、公式 registry 与 120 根日 K 线，禁止用静态文件存在替代数据执行。
6. 业务：固定适配器强制执行正式 `run --evidence`，输出到 canonical run directory；禁止用 `generate`、fixture、selftest 或数据准备单替代正式报告。
7. 产物：必须生成 Markdown、JSON、DOCX，并写入含绝对路径、字节数和 SHA-256 的 `business_artifact_manifest.json`。
8. 验收：业务状态、质量闸、三类报告文件和业务产物清单必须全部 `CLEAN_PASS`；共享证据集仅允许同批次、同交易日、哈希一致的只读复用。
9. Codex 运行时：`openclaw-stock-execution-gate-v3` 在模型调用前准备唯一 request，在工具调用时阻断旧入口，在最终回复前核对同一 request 的 manifest；没有证据只能显示 `BLOCKED`。

## 唯一命令

```powershell
python D:\C盘转移\日志\codex\skills\baimao-daily-intel-review\scripts\codex_entry.py run -- --evidence <证据包.json> --mode closing
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
- 风险：风险、失效、降级、排除；任何缺口必须 BLOCKED。
- 验收：验证、selftest、gate、CLEAN_PASS/BLOCKED 和本轮 manifest。

- 复核归档：生成验收摘要与 audit 记录，完成收尾后才允许交付。
