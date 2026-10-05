# stock-deliverable 业务规范

> 本文件只保留业务语义、数据口径、分析方法和产物要求。所有历史入口、命令、gate、fallback、临场脚本选择说明均已机械剥离；执行控制只认 `codex_entry.py`。

name: stock-deliverable
name_cn: 股票投研交付
description: "Codex 本机股票/炒股/投研交付技能。用于股票、股市、证券、A股、港股、美股、投研、研报、量化、选股、持仓、止损、止盈、K线、财报、估值、资金流、龙虎榜等任务, 尤其是要求输出 PPTX/Word/DOCX/报告/汇报/交付训练时。"

# Stock Deliverable

这是 Codex 本机股票/炒股/投研交付技能的唯一执行入口。只使用本机已有文件, 不安装外部技能。

## 强制触发

用户任务包含下列任意语义时, 必须使用本技能:

- 炒股、股票、股市、证券、A股、港股、美股、投研、研报、量化、选股、持仓、止损、止盈、K线、财报、估值、资金流、龙虎榜、交易策略。
- 同时要求 PPT、PPTX、PowerPoint、Word、DOCX、报告、汇报、精美文档、交付物、训练、闭环验收。

所有股票/投研交付任务必须调用下面这个执行器, 不得临场新写分叉脚本, 不得只在聊天中生成文本:

执行器路径:

## 唯一流程

1. 入口: 调用唯一执行器。
2. 生成: 同轮生成 PPTX 和 DOCX。
3. 验收: 执行器自动解析 PPTX/DOCX, 检查页数、段落、表格、图表、风险提示、唯一执行器标记、manifest 标记、乱码和占位符, 并用 Python 将 DOCX 内容渲染成 PNG 预览。
4. 证据: 写出 manifest JSON, 包含执行器版本、文件路径、大小、SHA256、每个检查项和 PASS/FAIL。
5. 返工: manifest 中 `validation.status` 不是 `PASS` 时, 不得交付, 必须修复后重跑。

## 唯一硬闸

交付必须同时满足:

- PPTX 存在、可解析、不少于 11 页、含至少 3 张表格和 1 个图表。
- DOCX 存在、可解析、不少于 38 个段落、含至少 4 张表。
- DOCX 必须由执行器用纯 Python 生成不少于 2 张 PNG 可视预览, 且所有预览图非空。
- 文本必须包含“不构成投资建议”、“不输出买卖指令”、“唯一执行器”、“manifest”、“PPTX”、“DOCX”。
- 文本不得包含 TODO、TBD、占位、待补、乱码替代字符或常见 mojibake 字符。
- manifest 必须存在且 `validation.status` 为 `PASS`。

## 防跑偏规则

- 搜索无结果或数据不足时, 必须明确说明数据不足, 降级为研究框架和验证清单。
- 禁止编造行情、价格、涨跌幅、资金流、公告、财报或来源。
- 禁止输出确定性买卖建议、保证收益、喊单或替用户做投资决定。
- 交付物是可打开、可解析、可验收的 PPTX 和 DOCX, 不是聊天文本摘要。

## 科学工作流硬闸（2026-06-28）

- 数据与来源：所有行情、公告、财报、估值、研报和资金数据必须有本地文件或可核验来源；不得编造来源。
- 宏观市场：交付中的市场判断必须说明指数、成交、涨跌家数、市场宽度、大盘风险偏好和宏观约束。
- 微观链条：个股结论必须覆盖公告、业绩、订单、产业链、个股和板块，不足时降级为验证清单。
- 新闻事实：新闻、公告、政策、事实、观点、传闻和舆情要区分事实与推断。
- 技术反馈：涨停、连板、炸板、趋势、量价、K线、支撑、压力只能作为证据项，不能单独推出结论。
- 资金结构：资金、主力、龙虎榜、机构、游资、散户证据必须在报告中标注口径。
- 决策输出：结论、评分、排序、过滤、剔除和 Top 列表必须来自执行器 manifest，不得手工拼接。
- 风险控制：manifest 未 PASS、模板/预览/表格/图表缺失、占位或乱码存在时必须 BLOCKED。
- 验收：只认唯一执行器生成的 manifest，PPTX、DOCX、PNG 预览和校验项全部 PASS 后才可交付。

## 验收口径

验收只认执行器输出的 manifest。没有 manifest 或 manifest 未 PASS, 就是未完成。

# Stock Deliverable Workflow

## Trigger

Use this skill when Codex needs a local stock research deliverable, especially PPTX, DOCX, report, training artifact, or manifest-validated stock output.

## Read Protocol

Codex must read `SKILL.md` and this `references/workflow.md` before execution. Do not jump directly to ad hoc scripts.

## Preflight

## Entry

The only Codex skill entry is `scripts/stock-deliverable.py`. The underlying product generator remains `D:\C盘转移\日志\codex\tools\stock-deliverable\stock_deliverable_executor.py`.

## Inputs

Required delivery inputs are `--round`, `--topic`, and `--outdir`. Inputs must be explicit and traceable; do not invent market data, prices, filings, or fund-flow facts.

## 科学工作流硬闸（2026-06-28）

1. 数据与来源：行情、公告、财报、估值、研报、资金数据必须可追溯。
2. 宏观市场：指数、成交、涨跌家数、市场宽度、大盘风险偏好和宏观约束必须进入研究框架。
3. 微观链条：公告、业绩、订单、产业链、个股和板块信息不足时，只能输出验证清单。
4. 新闻事实：新闻、公告、政策、事实、观点、传闻和舆情必须区分事实、推断和风险。
5. 技术反馈：涨停、连板、炸板、趋势、量价、K线、支撑、压力只能作为证据项。
6. 资金结构：资金、主力、龙虎榜、机构、游资和散户证据必须标注口径。
7. 决策输出：结论、评分、排序、过滤、剔除和 Top 列表必须来自 manifest 和执行器输出。
8. 风险控制：manifest、PPTX、DOCX、PNG 预览、表格、图表任一失败即 BLOCKED。
9. 验收：执行器 manifest 的 `validation.status` 必须为 PASS。

## Artifact

The executor must create PPTX, DOCX, previews, and manifest JSON under the requested output directory.

## Verification

## Failure Policy

If any gate, executor invocation, or manifest check fails, return BLOCKED. Do not provide chat-only delivery text as a substitute for files.

## Closeout

Report the manifest path, generated file paths, file sizes, SHA256 values, and validation status. Keep `庄家资金监控` outside this workflow unless a later task explicitly resumes that reserved item. Closeout audit/recheck/archive must preserve the manifest and generated artifact paths.
