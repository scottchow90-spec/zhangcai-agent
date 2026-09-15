# baimao-teacher-system 业务规范

> 本文件只保留业务语义、数据口径、分析方法和产物要求。所有历史入口、命令、gate、fallback、临场脚本选择说明均已机械剥离；执行控制只认 `codex_entry.py`。

name: baimao-teacher-system
name_cn: 白猫老师六公式通达信体系
description: 白猫老师六公式通达信体系技能。用于检查、调用和说明已经转换并安装到 C:\new_tdx_mock 的六个通达信公式：白猫RSI、白猫渡劫、白猫队长、躲猫猫、黑猫白猫、平均成本线。触发于“白猫老师体系”“白猫公式”“白猫RSI”“白猫渡劫”“白猫队长”“躲猫猫”“黑猫白猫”“平均成本线”等请求。

# 白猫老师体系

## 用途

本技能封装白猫老师六个通达信公式的本地调用、资产留存、安装验收和使用说明。它只管理公式文件与本地通达信注册状态，不给出买卖指令，不连接券商交易账户，不执行真实交易。

本技能已经内置个股评分引擎：`scripts/baimao_stock_score.py`。评分引擎读取 `C:\new_tdx_mock\vipdoc` 本地日线，复刻六公式核心逻辑，输出 100 分制个股评分、模块得分、风险、关键价位、Markdown/JSON 报告。评分用于研究、观察池排序和风控提示，不等于交易指令。

## 固化公式

| 公式名 | 通达信类型 | 技能资产 |
|---|---|---|
| 白猫RSI | 副图 | `assets/formulas/baimao-rsi.tdx` |
| 白猫渡劫 | 副图 | `assets/formulas/baimao-dujie.tdx` |
| 白猫队长 | 副图 | `assets/formulas/baimao-captain.tdx` |
| 躲猫猫 | 副图 | `assets/formulas/duomaomao.tdx` |
| 黑猫白猫 | 副图 | `assets/formulas/heimao-baimao.tdx` |
| 平均成本线 | 主图叠加 | `assets/formulas/avg-cost-line.tdx` |

已安装目标为 `C:\new_tdx_mock`，通达信私有公式注册表读取位置为 `C:\new_tdx_mock\T0002\PriLoc.dat`，配套核心文件为 `PriGS.dat`、`PriCS.dat`、`PriLoc.dat`、`PriPack.dat`、`PriEx.dat`、`PriBand.dat`。

## 标准调用

- `info`：输出技能目录、入口、工作流、公式数量和本地通达信路径。
- `list`：列出六个封装公式、主图/副图类型和资产路径。
- `status`：读取 `C:\new_tdx_mock\T0002\PriLoc.dat`，返回安装命中、缺项、资产存在性和备份路径。
- `verify-installed`：作为硬验收命令，六个公式都在本地注册表中时返回 `CLEAN_PASS`。
- `score <股票代码>`：读取本地通达信日线，计算白猫老师六公式 100 分制个股评分。
- `report <股票代码>`：生成单股评分 JSON 与 Markdown 报告，默认输出到 `reports/stock_score`。
- `batch <股票代码...>`：批量评分并按总分排序，可配合 `--file` 读取股票列表。
- `scripts/baimao_workflow_acceptance.py`：机器可执行工作流验收，检查 Codex 可见性、公式安装、单股评分、报告产物、批量评分、缺失K线降级、两个硬闸，并写出验收 JSON。

个股评分命令：

## 个股评分模型

100 分由七部分组成：

- 平均成本线：25 分，主图趋势结构、MACD底部/顶部结构、短期/长期EMA骨架。
- 白猫RSI：15 分，趋势线位置、超卖修复、短线卖出线和极度风险线。
- 白猫渡劫：15 分，33日低位恐慌释放、主力捡尸、承接是否转化为价格修复。
- 白猫队长：15 分，55周期白猫数值、低位开始反弹、高位风险、指数环境共振。
- 躲猫猫：15 分，短期超跌/疑似神秘资金抄底窗口；99为超跌抄底窗口，99后转50为短线修复确认。
- 黑猫白猫：5 分，ZIG拐点辅助信号；因存在重绘/后验特征，必须降权。
- 六公式共振：10 分，统计同向模块数量，主图确认后才给高共振分。

评级：85分以上为 A 强共振，70-84 为 B 可观察，55-69 为 C 弱修复，40-54 为 D 风险偏高，40 以下为 E 排除。

## 科学工作流硬闸（2026-06-28）

本技能属于 A股、股票、通达信、TDX、技术分析、K线、趋势、量价、支撑、压力、资金、主力、机构、游资、龙虎榜、板块、热点、涨停、连板、炸板场景的公式管理技能。任何结论必须区分数据、来源、证据、事实、观点、传闻和舆情；遇到新闻、公告、政策、业绩、订单、产业链、个股、指数、成交、涨跌家数、市场宽度、风险偏好、大盘信息时，必须标明来源和时点。

使用本技能时，先完成公式注册验证，再做过滤、剔除、评分、排序、Top 输出或报告说明。若本地通达信路径、公式资产、注册表或验证命令未通过，必须返回 BLOCKED，不得以说明文字替代验收。验收通过标记为 CLEAN_PASS，并保留 selftest 与 gate 结果。所有风险、失效、降级、排除规则必须在输出中明示。

## 防错纠错、数据矩阵与交付验收

- 防错纠错：评分前必须完成任务闸门、股票身份闸门、K线数据闸门、公式版本闸门、样本规模闸门、重绘信号闸门和输出证据闸门。
- 数据接口矩阵：日K线优先读取 `C:\new_tdx_mock\vipdoc\<market>\lday\*.day`；六公式源码优先读取本技能 `assets/formulas`；事件研究优先读取 `references\kline-research-20260629.json`；公告、新闻、基本面、行业主题缺失时只能降级输出。
- 降级机制：K线缺失为 DATA_BLOCKED；K线陈旧为 DATA_STALE；公式版本冲突为 FORMULA_CONFLICT；研究样本少于1000只时禁止体系性结论；新闻/基本面缺失时只允许技术评分。
- 最新数据硬闸：当前日期为交易日或用户要求“今天/最新”时，个股评分必须使用当天最新有效交易日数据；本地K线最新日期不是当天时，必须返回 DATA_STALE，不得输出评级、买点、观察池或排除结论。
- 执行闭环：`auto` 必须间接调用 `baimao_workflow_acceptance.py`；验收产物固定为 `reports\workflow_acceptance\latest_workflow_acceptance.json`。没有该文件或状态不是 CLEAN_PASS，不得宣称工作流可执行。

## 失败处置

- `C:\new_tdx_mock` 不存在：停止调用并报告本地通达信路径不可用。
- 六个公式任一未注册：停止输出公式已安装结论，返回缺项清单。
- 资产文件任一不存在：停止技能验收，返回缺失资产路径。
- Codex 硬闸未通过：使用硬闸返回的 blocks 作为排错依据。

## 复核闭环

每次技能更新后必须执行：

最终交付只允许报告真实命令结果、技能绝对路径、公式清单和验收状态。

# 白猫老师体系工作流

## 入口锁定

推荐命令：

## 输入与数据源

固定输入来自三处：

- 技能注册表：`references/formulas.json`
- 技能公式资产：`assets/formulas/*.tdx`
- 通达信本地注册表：`C:\new_tdx_mock\T0002\PriLoc.dat`

安装目标固定为 `C:\new_tdx_mock`。已知安装备份目录为 `C:\new_tdx_mock\T0002\gs_bak\codex_install_baimao_20260629_1125`。本技能可读取 `tdx-local-hub` 作为本地通达信环境证据，但六个白猫公式的注册验收以 `PriLoc.dat` 中的公式名为准。

## 固化公式清单

| 公式名 | 类型 | 安装名 | 资产文件 |
|---|---|---|---|
| 白猫RSI | 副图 | 白猫RSI | `assets/formulas/baimao-rsi.tdx` |
| 白猫渡劫 | 副图 | 白猫渡劫 | `assets/formulas/baimao-dujie.tdx` |
| 白猫队长 | 副图 | 白猫队长 | `assets/formulas/baimao-captain.tdx` |
| 躲猫猫 | 副图 | 躲猫猫 | `assets/formulas/duomaomao.tdx` |
| 黑猫白猫 | 副图 | 黑猫白猫 | `assets/formulas/heimao-baimao.tdx` |
| 平均成本线 | 主图叠加 | 平均成本线 | `assets/formulas/avg-cost-line.tdx` |

## 执行步骤

1. 读取 `references/formulas.json`，取得六个公式的安装名、主图/副图类型、源文件路径和资产路径。
2. 检查 `C:\new_tdx_mock`、`C:\new_tdx_mock\T0002`、`PriLoc.dat` 是否存在。
3. 按通达信私有公式索引格式读取 `PriLoc.dat`：跳过 24 字节头部，后续按 56 字节记录解析，记录名前 20 字节按 GBK 解码。
4. 对比六个安装名，生成 found 与 missing 清单。
5. 检查六个 `assets/formulas/*.tdx` 是否存在且大小大于零。
8. 运行闭环验收脚本，输出 CLEAN_PASS 或 BLOCKED。

## 个股评分执行

评分脚本直接读取 `C:\new_tdx_mock\vipdoc\<market>\lday\<symbol>.day`，至少需要 90 条日线记录。输出包括 `score`、`rating`、`modules`、`strengths`、`weaknesses`、`risks`、`levels`、`data_gate`。单股报告会落盘到 `reports/stock_score`。

六公式权重固定如下：平均成本线 25 分，白猫RSI 15 分，白猫渡劫 15 分，白猫队长 15 分，躲猫猫 15 分，黑猫白猫 5 分，六公式共振 10 分。躲猫猫=99定义为短期超跌/疑似神秘资金抄底窗口，99后转50定义为短线修复确认；黑猫白猫含 ZIG 类拐点辅助，实时评分必须降权；平均成本线作为主图确认层，权重最高；顶部结构、风险信号、最佳卖出会限制共振分。

## 防错纠错机制

评分前必须通过七个闸门：任务闸门、股票身份闸门、K线数据闸门、公式版本闸门、样本规模闸门、重绘信号闸门、输出证据闸门。任何闸门失败时不得给强结论，只能返回 BLOCKED、DATA_DEGRADED 或补数清单。

常见纠错规则：

- 躲猫猫不得解释为普通防守指标，必须解释为短期超跌/疑似神秘资金抄底窗口。
- 单个公式不得直接推出买入结论，必须至少叠加承接确认和主图确认。
- K线缺失、陈旧或股票身份冲突时，禁止评分和排名。
- 黑猫白猫含 ZIG/BACKSET 类后验风险，固定低权重，只做辅助或风险项。
- 输出必须包含数据来源、公式事实、风险扣分、失效条件、降级状态和验收命令。

## 数据接口矩阵与降级机制

| 数据类别 | 主接口/路径 | 备用接口 | 失败处理 |
|---|---|---|---|
| 日K线/量价 | `C:\new_tdx_mock\vipdoc\<market>\lday\*.day` | 用户指定本地K线或TQ结构化数据 | 无K线则 DATA_BLOCKED，不评分 |
| 六公式源码 | `assets/formulas/*.tdx` | `G:\白猫老师资料\指标` | 版本冲突则 FORMULA_CONFLICT |
| 公式事件研究 | `references\kline-research-20260629.json` | `work\baimao_research\baimao_kline_research.json` | 样本少于1000只禁止体系性结论 |
| 候选股票池 | 用户代码、本地 `.blk` 文件 | 用户表格/结构化问财 | 来源不明则不排名 |
| 基本面/公告/新闻 | iFinD/交易所/公司公告 | 当前网页核验 | 缺失时只允许技术评分 |
| 行业/主题 | iFinD/本地行业映射 | 用户文件/结构化网页 | 缺失时不做题材加分 |

降级等级：L0正常；L1缺基本面/新闻但技术数据完整；L2 K线陈旧；L3公式不一致；L4研究样本不足1000；L5股票身份冲突或K线缺失硬阻断。

最新数据硬闸：用户要求“今天、最新、当前、现在”的个股评分时，必须检查本地K线最新有效交易日是否等于当天日期。若本地K线仍停留在更早交易日，返回 `DATA_STALE`，禁止输出评分评级、买点、观察池、排除结论或Word结论报告；只能输出数据过期原因、实际数据日期、要求日期和补数动作。

## 交付验收机制

机器可执行验收命令：

闭环标准：`baimao_workflow_acceptance.py` 返回 `CLEAN_PASS`，且 `baimao-teacher-system.py auto` 返回 `CLEAN_PASS/all_ok=true`。否则工作流视为未闭环。

## 科学工作流硬闸（2026-06-28）

本工作流覆盖 A股、股票、通达信、TDX、技术分析、K线、趋势、量价、支撑、压力、资金、主力、机构、游资、龙虎榜、板块、热点、涨停、连板、炸板等场景。涉及指数、成交、涨跌家数、市场宽度、风险偏好、大盘、个股、公告、业绩、订单、产业链、新闻、政策、事实、观点、传闻、舆情时，必须先区分数据和来源，再给结论。公式结果只能作为技术分析输入，不能替代风险控制。

若用于选股、过滤、剔除、评分、排序或 Top 输出，必须先完成注册验证和本地数据来源说明。输出中要列出结论、证据、风险、失效条件、降级处理、排除原因、验证命令和 selftest/gate 状态。任何未通过步骤都必须返回 BLOCKED；通过时必须标记 CLEAN_PASS。

## 产物

入口命令输出 JSON，至少包含：

- `skill`
- `tdx_root`
- `expected_count`
- `found`
- `missing`
- `assets`
- `backup_dir`
- `status`
- `checks`
- `score`
- `rating`
- `modules`
- `risks`
- `levels`

闭环脚本额外输出 Codex 硬闸结果和技能资产检查结果。

## 失败处理

路径不存在、注册缺项、资产缺项、硬闸失败、脚本异常均视为 BLOCKED。不得用人工推断替代命令结果，不得在未通过验收时说“已正常调用”。若用户要求安装或修复，应转入通达信公式安装流程，并在完成后重新执行本技能 `auto`。

## 收尾复核

收尾必须保留三项证据：技能目录绝对路径、六个公式注册命中结果、Codex 硬闸结果。回复用户时只报告实际改变、绝对路径和验证结果。
