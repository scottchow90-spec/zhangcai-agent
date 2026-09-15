# dragon-pullback 业务规范

> 本文件只保留业务语义、数据口径、分析方法和产物要求。所有历史入口、命令、gate、fallback、临场脚本选择说明均已机械剥离；执行控制只认 `codex_entry.py`。

name: dragon-pullback
name_cn: 龙回头
description: Clean dragon pullback workflow. Use for dragon pullback, leader pullback, second-wave launch, strong-stock pullback, 龙回头, 龙头回调, 二波启动, and pullback buy-point analysis.
data_source: tdx-local-hub

# dragon-pullback

## 执行层闭环固化（2026-06-28）

本技能内部业务执行器：`scripts/dragon-pullback.py`；唯一外部入口为 `scripts/codex_entry.py`。

强制规则：

1. Codex 后续调用本技能只能先进入 `scripts/dragon-pullback.py`。
2. `auto` 不得候选排序、不得优先跑 verifier/gate/selftest 替代固定执行脚本。
3. `SKILL.md`、`references/workflow.md`、入口脚本和闭环验收脚本必须共同指向上述两个文件。

## 科学工作流硬闸（2026-06-28）

本技能必须执行“数据 → 宏观 → 微观 → 消息政策 → 技术 → 资金 → 结论 → 风险 → 产物 → 验收”闭环，禁止只按模板填空、禁止把问题/计划/阻塞写成结果。

### A. 数据真实与可追溯

1. 行情、指数、成交额、涨跌家数、涨停池、连板、炸板、龙虎榜、资金流、公告、新闻、政策、研报、互动热度，必须优先来自本地 TDX/通达信、akshare、东方财富、同花顺、腾讯行情或已落盘 evidence/source/S 编号。
2. 数据必须写清来源、时间窗口、字段含义和采集脚本；没有源锚点的数据不得进入强结论。
3. 盘中快照只能标注为窗口期判断，不能冒充收盘结论；历史数据必须标注交易日。

### B. 科学分析链条

1. 宏观：指数、成交额、涨跌家数、市场宽度、风险偏好、大盘环境。
2. 微观：公告、订单、业绩、产业链位置、个股/板块兑现条件。
3. 消息政策：新闻、公告、政策、事实、观点、传闻必须分层，传闻不得作为强结论。
4. 技术：涨停、连板、炸板、趋势、量价、K线、支撑压力、失效位。
5. 资金：主力资金、龙虎榜、机构、游资、散户、资金流是否同向。
6. 决策：评分、排序、过滤、剔除、Top 候选必须由上面数据共同支持。
7. 风险：给出风险、失效、降级、排除条件；不满足硬闸必须 BLOCKED。

### C. 输出与验收

1. 产物必须明确为 report/报告/Word/docx/csv/json 中的一种或多种，并写清路径。
3. 禁止使用“待确认、需确认、缺数据、近似、源不足、进入观察”等词把未完成事项包装成结果；这些词只能出现在硬闸禁用清单或失败原因中。
4. 入口、workflow、gate、模板、产物验收必须指向同一条执行链；Codex 不得横跳到其它技能或旧模板。

## 执行层实质工作流硬闸（2026-06-28）
- 输出必须是数据链和结论链闭环：真实数据源 -> 宏观/微观/消息政策/技术/资金 -> 明确结论 -> 风险与无效条件 -> 验收证据。

本技能内部业务执行器：`scripts/dragon-pullback.py`；唯一外部入口为 `scripts/codex_entry.py`。

Codex 触发本技能时只能执行：

# dragon-pullback 使用工作流 v2 (2026-06-18 加固)

**TDX 本地优先**: 凡涉及 K线/涨停/板块/资金/选股的本地场景, **必须**调用 `skills/tdx-local-hub/scripts/tdx_hub.py` 或 `registry_list.py` 从 `C:\\new_tdx_mock` 读本地数据, 禁止用 外部/云端/网络/akshare/eastmoney 等。
**唯一交付目录**: `F:\\小龙虾6月交付` (禁止 `F:\\小龙虾6月交付2` / `F:\\5月小龙虾交付`)。

## 1. 前置条件 (必跑)
- [ ] 读 `C:\\Users\\25296\\.openclaw\\workspace\\skills\\dragon-pullback\\SKILL.md` 前 50 行 (frontmatter)
- [ ] 读 `C:\\Users\\25296\\.openclaw\\workspace\\skills\\dragon-pullback\\scripts\\` 下脚本 1 遍

## 2. 技能用途
dragon-pullback = 龙回头

## 3. 工作步骤
1. 前置条件 1 (read SKILL.md) -> 2 (check workflow.md) -> 3 (执行)
2. 涉及 K线/涨停/板块/选股场景:
   - 用 `from openclaw_data import tdx_hub` 或 `tdx_hub.load_ztc(date=...)` 读本地数据
   - 用 `tdx_hub.load_vipdoc(symbol, freq="day")` 读 K线

## 4. 红线 (绝对禁止)
- **DO** 读 SKILL.md + workflow.md 后再调用脚本
- **DO** 走 TDX 本地优先 读 K线/板块
- **DO** 写到 `F:\\小龙虾6月交付`
- **DON'T** 用 网络/东方财富/akshare/baostock/tushare/iFinD/Wind 替代
- **DON'T** 跳过 SKILL.md 直接写脚本或搜网页
- **DON'T** 编造数据/价格/代码

## 5. 验证 (必跑)

## 6. 排错
- 失败 1: workflow.md 小于 600 bytes -> 重跑本脚本
- 失败 3: TDX 场景被 L10 拦截 -> 回步骤 1 (前置条件) + 步骤 2 (K线/板块 读本地)
## 执行链闭环固化（2026-06-21）

每次执行本技能必须完成以下闭环，不得只停留在文件存在检查：

1. 触发绑定：通过唯一 `F:\Codex\home\skills\stock-unified\references\stock_skill_ids.json` 目录册和公共 `F:\Codex\home\scripts\stock_canonical_runtime.py` 锁定本技能，禁止自行换技能或临时脚本绕行。
2. 读取确认：先读本技能 SKILL.md 与 references/workflow.md，再进入执行。
4. 执行入口：只调用本技能 scripts/ 内入口脚本或 workflow 明确声明的依赖脚本；缺入口则 BLOCKED。
5. 输入与产物：按 workflow 指定数据源读取，产物写入 workflow 指定目录；无正式产物的任务必须写 audit/status JSON。
6. 验收闸门：运行本技能验证脚本、final gate 或 master_pre_reply_gate，记录 PASS/BLOCKED 证据。
7. 失败处置：任一环节失败即 BLOCKED，说明缺失输入、失败脚本和可恢复动作；禁止伪造数据、禁止用网页搜索替代本地数据源。
8. 复核归档：把产物路径、验证输出和失败证据写入任务产物目录或 audit_log；不自动写 memory，除非用户明确要求。

执行闭环：

1. 触发绑定到 `dragon-pullback`。
2. 读取 `SKILL.md` 与本 `workflow.md`。
4. 只从 `scripts/dragon-pullback.py` 进入。
6. 记录 `CLEAN_PASS/BLOCKED` 证据；失败必须显示阻塞项，不得伪造通过。

## 科学工作流硬闸（2026-06-28）

本技能必须执行“数据 → 宏观 → 微观 → 消息政策 → 技术 → 资金 → 结论 → 风险 → 产物 → 验收”闭环，禁止只按模板填空、禁止把问题/计划/阻塞写成结果。

### A. 数据真实与可追溯

1. 行情、指数、成交额、涨跌家数、涨停池、连板、炸板、龙虎榜、资金流、公告、新闻、政策、研报、互动热度，必须优先来自本地 TDX/通达信、akshare、东方财富、同花顺、腾讯行情或已落盘 evidence/source/S 编号。
2. 数据必须写清来源、时间窗口、字段含义和采集脚本；没有源锚点的数据不得进入强结论。
3. 盘中快照只能标注为窗口期判断，不能冒充收盘结论；历史数据必须标注交易日。

### B. 科学分析链条

1. 宏观：指数、成交额、涨跌家数、市场宽度、风险偏好、大盘环境。
2. 微观：公告、订单、业绩、产业链位置、个股/板块兑现条件。
3. 消息政策：新闻、公告、政策、事实、观点、传闻必须分层，传闻不得作为强结论。
4. 技术：涨停、连板、炸板、趋势、量价、K线、支撑压力、失效位。
5. 资金：主力资金、龙虎榜、机构、游资、散户、资金流是否同向。
6. 决策：评分、排序、过滤、剔除、Top 候选必须由上面数据共同支持。
7. 风险：给出风险、失效、降级、排除条件；不满足硬闸必须 BLOCKED。

### C. 输出与验收

1. 产物必须明确为 report/报告/Word/docx/csv/json 中的一种或多种，并写清路径。
3. 禁止使用“待确认、需确认、缺数据、近似、源不足、进入观察”等词把未完成事项包装成结果；这些词只能出现在硬闸禁用清单或失败原因中。
4. 入口、workflow、gate、模板、产物验收必须指向同一条执行链；Codex 不得横跳到其它技能或旧模板。

## 执行层实质工作流硬闸（2026-06-28）
- 输出必须是数据链和结论链闭环：真实数据源 -> 宏观/微观/消息政策/技术/资金 -> 明确结论 -> 风险与无效条件 -> 验收证据。

禁止绕过 `scripts/dragon-pullback.py` 直接临场挑脚本；禁止把模板、计划、阻塞说明、样例数据、待确认结论当成执行结果；入口、workflow、gate、模板和验收必须共同指向上述同一条执行链。
