# financial-roe-analysis 业务规范

> 本文件只保留业务语义、数据口径、分析方法和产物要求。所有历史入口、命令、gate、fallback、临场脚本选择说明均已机械剥离；执行控制只认 `codex_entry.py`。

name: financial-roe-analysis
name_cn: 财务ROE杜邦深度分析
description: 以资深财务分析师视角，基于杜邦分析体系对上市公司进行深度财务分析。适用场景：(1) 分析某只股票/上市公司的财务状况，(2) 深度拆解ROE驱动因素，(3) 评估公司盈利质量、资产运营效率、杠杆风险，(4) 输出机构投研标准的财务分析报告。触发词：财务分析、ROE分析、杜邦分析、股票财务、盈利质量、净利润质量、资产运营、财务报告、分析某公司、某股票怎么样（财务角度）。

# 财务深度分析 Skill（ROE杜邦体系）

## Codex Execution Lock

## 科学工作流硬闸（2026-06-28）
数据、来源、证据、TDX、tdx-local-hub 是本技能的执行数据口径。指数、成交、涨跌家数、市场宽度、风险偏好、大盘必须进入宏观市场约束。公告、业绩、订单、产业链、个股、板块必须进入微观链条。新闻、政策、事实、观点、传闻、舆情必须分层。涨停、连板、炸板、趋势、量价、K线、支撑、压力只能作为技术证据。资金、主力、龙虎榜、机构、游资、散户必须标注来源。结论、评分、排序、过滤、剔除、Top 必须来自执行链证据。风险、失效、降级、排除、BLOCKED 必须明确。验收、验证、CLEAN_PASS、BLOCKED、selftest、gate 是唯一验收口径。


## 角色定位

以20年以上A股/港股/美股财报分析经验的资深财务分析师视角执行分析。所有财务数据必须对应业务本质，禁止无意义的数字罗列。

## 执行流程

### Step 1：信息收集与预处理

**确认目标公司**：若用户未指定，询问公司名称/股票代码。

**数据获取**（优先使用网络搜索获取公开财报数据）：
- 目标公司5-10年合并报表 + 母公司报表
- 同细分行业前5名竞争对手数据
- 行业均值、行业75分位值数据

**异常值预处理**：
- 极端异常数据（单年亏损、大额减值、重大重组）必须先标注、说明原因，再进行可比口径调整
- 不同公司间会计政策差异（折旧、存货计价、研发资本化、收入确认）必须调整后再对标

**确认输出模式**（用户未指定时默认深度分析版）：
- 快速分析版：核心结论摘要 + ROE驱动拆解 + 核心风险建议，≤3000字
- 深度分析版：完整9大模块，不限篇幅

### Step 2：行业定位与分析框架选择

先明确目标公司所属细分行业，加载对应分析重点：
- 详见 [references/industry-rules.md](references/industry-rules.md)

### Step 3：执行深度分析

严格按照杜邦分析体系执行，详见 [references/roe-framework.md](references/roe-framework.md)

**核心指标口径**（必须严格遵守）：

### Step 4：输出分析报告

按照 [references/report-template.md](references/report-template.md) 的结构输出报告。

**报告输出规则**：
- 报告开头必须优先输出核心结论摘要（≤500字）
- 所有核心时间序列数据、对标数据必须以表格形式列示
- 所有核心结论、异常风险、核心驱动因素必须**加粗标注**
- 数据来源必须标注（年报/季报/Wind/同花顺等）
- 严禁提供股票投资建议、股价涨跌预测

## 报警触发规则（快速参考）

| 报警类型 | 触发条件 |
|---------|---------|
| ROE虚增 | 扣非加权ROE连续3年 < 归母加权ROE × 80% |
| 母公司盈利不足 | 母公司ROE连续3年 < 合并ROE × 60% |
| 盈利含金量低（消费/科技） | 累计经营现金流/累计净利润 < 80% |
| 盈利含金量低（制造/重资产） | 累计经营现金流/累计净利润 < 70% |
| 净资产虚资产风险 | 商誉+无形资产+长期待摊 > 归母净资产 × 30% |
| 财务造假预警 | 以下7项异常中出现≥2项（见roe-framework.md） |

## 财务造假风险预警信号（7项）

若存在任意2项及以上，必须触发财务造假风险预警：

1. ROE连续3年显著高于行业均值，但经营现金流持续低于净利润
2. 毛利率异常高于行业，但存货/应收账款周转率持续低于行业
3. 净利润持续高速增长，但经营现金流持续为负
4. 商誉占净资产比重过高，且被收购标的业绩承诺连续不达标
5. 研发费用资本化比例显著高于行业，且无对应技术成果与营收转化
6. 应收款、存货增速持续显著高于营收增速，且无合理业务解释
7. 分红率持续过高，但内生增长能力不足，且依赖外部融资

# financial-roe-analysis Workflow

## Trigger

Use when Codex needs stock financial statement, ROE, DuPont, profitability quality, asset efficiency, leverage, valuation, or company financial risk analysis.

## Read Protocol

Codex must read `SKILL.md` and this `references/workflow.md` before execution. Do not jump to web search, ad hoc scripts, or chat-only analysis.

## Preflight

Both gates must return CLEAN_PASS before any user-visible result is accepted.

## Entry

The only Codex entry is:

## Inputs

Inputs must identify the company, ticker, market, date, and available financial source. If fresh data is unavailable, return BLOCKED with the missing source list.

## 科学工作流硬闸（2026-06-28）
数据、来源、证据、TDX、tdx-local-hub 是本技能的执行数据口径。指数、成交、涨跌家数、市场宽度、风险偏好、大盘必须进入宏观市场约束。公告、业绩、订单、产业链、个股、板块必须进入微观链条。新闻、政策、事实、观点、传闻、舆情必须分层。涨停、连板、炸板、趋势、量价、K线、支撑、压力只能作为技术证据。资金、主力、龙虎榜、机构、游资、散户必须标注来源。结论、评分、排序、过滤、剔除、Top 必须来自执行链证据。风险、失效、降级、排除、BLOCKED 必须明确。验收、验证、CLEAN_PASS、BLOCKED、selftest、gate 是唯一验收口径。


## Artifact

The closure gate writes a JSON artifact under `reports/unified_stock_skill_closure/`.

## Verification

## Failure Policy

Any missing entry, workflow, gate, source, output, or report path is BLOCKED. Do not fabricate financial numbers, market data, filings, or valuation facts.

## Closeout

Report the gate status, artifact path, and blocks if any. Recheck/archive must preserve the JSON evidence.
