---
name: quality-track-stock-selection
description: 本机Codex“优质赛道选股”固定执行技能。用于用户提出“优质赛道选股”“优质赛道”“赛道选股”“按事件到赛道到核心公司选股”“运行优质赛道工作流”等请求；从C:\new_tdx_mock读取完整交易日、概念成员和本地资讯，执行事件确认、赛道持续性、个股技术与流动性、主营收入、财务、估值、公告风险和纸面仓位门控，输出买入、观察或NO_TRADE。仅用于本机Codex纸面决策支持，不自动下单，不保证收益。
---

# 优质赛道选股

## 固定边界

- 目标系统是本机 Codex；不得切换到 OpenClaw 或其他选股工作流。
- 保留原图片主链：事件 → 核心要素 → 赛道 → 产业链公司 → 影响因素 → 基本面五维 → 结论。
- 只使用完整横截面交易日；盘中少量更新不得参与赛道排名。收盘后本地数据不完整时，用腾讯批量收盘行情补齐；覆盖率不足80%必须阻断。
- 不强制凑股。赛道持续性失败时，成功结果应为 `NO_TRADE`，并可返回主营已确认的观察名单。
- 实时报价、主营、财务、估值或公告任何一层缺失时失败关闭为复核或剔除。
- 所有仓位均为纸面计划；`automatic_order` 必须保持 `false`。

## 固定入口

技能根目录：`D:\C盘转移\日志\codex\skills\quality-track-stock-selection`

```powershell
python D:\C盘转移\日志\codex\skills\quality-track-stock-selection\scripts\codex_entry.py info
python D:\C盘转移\日志\codex\skills\quality-track-stock-selection\scripts\codex_entry.py selftest
python D:\C盘转移\日志\codex\skills\quality-track-stock-selection\scripts\codex_entry.py run
python D:\C盘转移\日志\codex\skills\quality-track-stock-selection\scripts\codex_entry.py run -- status
python D:\C盘转移\日志\codex\skills\quality-track-stock-selection\scripts\codex_entry.py verify --receipt <统一门面回执.json>
```

其他固定命令：

```powershell
python D:\C盘转移\日志\codex\skills\quality-track-stock-selection\scripts\codex_entry.py run -- backtest
python D:\C盘转移\日志\codex\skills\quality-track-stock-selection\scripts\codex_entry.py run -- settle
```

## 执行顺序

1. 首次使用、脚本更新或异常后先运行 `selftest`。
2. 用户要求当日选股时运行 `run`；该入口依次执行实跑、含成本无未来数据回测、回测锚点稳定性验证、纸面账本记录和状态持久化。
3. 紧接着运行 `codex_entry.py run -- status`，校验状态文件中每个结果文件的 SHA-256 和大小。
4. 从 `run/practical_selection.json` 读取业务结果，从 `run/skill_status.json` 读取技能状态；不得只依据终端退出码或 stdout。
5. 分开呈现事实、推断、风险和边界。明确说明候选是买入、观察、剔除还是空仓。
6. 回测为 `FAIL` 时，只能输出纸面观察或空仓，不得升级为真实资金建议。

## 结果判定

- `PASS`：严格赛道成立且达到最终候选数量。
- `PARTIAL_PAPER_ELIGIBLE`：严格赛道成立，但合格候选不足上限。
- `NO_PAPER_ELIGIBLE`：赛道成立，但公司级门槛全部未通过。
- `NO_TRADE`：没有赛道同时通过事件、广度和5日持续强度门槛；这是正常成功状态。
- `REVIEW` / `WATCH_ONLY`：仅观察，仓位必须为0。
- `EXCLUDE`：命中硬剔除项。

## 方法与输出

- 解释评分、硬门槛或当前候选原因时，读取 [references/methodology.md](references/methodology.md)。
- 消费持久化 JSON、编写下游脚本或做验收时，读取 [references/output-schema.md](references/output-schema.md)。
- 用户要求生成任何股票 DOCX、PDF、PPTX、XLSX、XLSM 或 XLS 时，必须另外调用 `$stock-delivery-risk-gate` 和相应文档技能；本技能不能替代文件风险门禁。

## 修复纪律

- 发现可安全修复的解析、评分、数据或持久化缺陷时，先修复，再重新运行 `selftest`、`run` 和 `status`。
- 修改必须落在本技能 `scripts/` 的同一执行栈内；不得临时改用另一套选股器绕过失败。
- 任何当前数据、外部证据或哈希读回失败都不得表述为已完成选股。
