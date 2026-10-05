# stock-study 业务规范

> 本文件只保留业务语义、数据口径、分析方法和产物要求。所有历史入口、命令、gate、fallback、临场脚本选择说明均已机械剥离；执行控制只认 `codex_entry.py`。

name: stock-study
name_cn: 高级股票研究
description: Senior equity research analysis for single tickers. Use when user requests detailed stock analysis with company overview, Wall Street consensus (analyst ratings, price targets), institutional activity, and analyst upgrades/downgrades. Cite all metrics with source and date.
# Stock Study - Senior Equity Research Analyst

## Codex Execution Lock

## 科学工作流硬闸（2026-06-28）
数据、来源、证据、TDX、tdx-local-hub 是本技能的执行数据口径。指数、成交、涨跌家数、市场宽度、风险偏好、大盘必须进入宏观市场约束。公告、业绩、订单、产业链、个股、板块必须进入微观链条。新闻、政策、事实、观点、传闻、舆情必须分层。涨停、连板、炸板、趋势、量价、K线、支撑、压力只能作为技术证据。资金、主力、龙虎榜、机构、游资、散户必须标注来源。结论、评分、排序、过滤、剔除、Top 必须来自执行链证据。风险、失效、降级、排除、BLOCKED 必须明确。验收、验证、CLEAN_PASS、BLOCKED、selftest、gate 是唯一验收口径。


## Required Analysis

### Step 1 — Company Overview
- **What the company does in plain English**: 2-3 sentence business description
- **Business model and revenue streams**: Breakdown by percentage of total revenue in a table
- **Key competitive advantage**: One-sentence moat

### Step 2 — Wall Street Consensus
- Number of analysts covering this stock
- Buy / Hold / Sell breakdown with firm names
- Average, highest, and lowest price targets
- Most recent analyst upgrade or downgrade (firm name and date)

### Step 3 — Institutional Activity
- Top 5 institutional holders with position changes (QoQ)
- Notable hedge fund activity (new positions or exits with SEC filing dates)

## Format
- Clear markdown headers
- Tables for quantitative data
- Source citations immediately after each metric
- Flag any data that may be more than 30 days old

## Watchlist (for reference)
Current tickers: MIAX, YUM, GM, PENG, FUTU

# stock-study Workflow

## Trigger

Use when Codex needs a single-ticker stock study with company overview, consensus, holders, institutional activity, valuation context, risks, and dated citations.

## Read Protocol

Codex must read `SKILL.md` and this `references/workflow.md` before execution. Do not jump to web search, ad hoc scripts, or chat-only analysis.

## Preflight

Both gates must return CLEAN_PASS before any user-visible result is accepted.

## Entry

The only Codex entry is:

## Inputs

Inputs must identify ticker, market, date, and required source set. If fresh consensus or holder data is unavailable, return BLOCKED with missing-source details.

## 科学工作流硬闸（2026-06-28）
数据、来源、证据、TDX、tdx-local-hub 是本技能的执行数据口径。指数、成交、涨跌家数、市场宽度、风险偏好、大盘必须进入宏观市场约束。公告、业绩、订单、产业链、个股、板块必须进入微观链条。新闻、政策、事实、观点、传闻、舆情必须分层。涨停、连板、炸板、趋势、量价、K线、支撑、压力只能作为技术证据。资金、主力、龙虎榜、机构、游资、散户必须标注来源。结论、评分、排序、过滤、剔除、Top 必须来自执行链证据。风险、失效、降级、排除、BLOCKED 必须明确。验收、验证、CLEAN_PASS、BLOCKED、selftest、gate 是唯一验收口径。


## Artifact

The closure gate writes a JSON artifact under `reports/unified_stock_skill_closure/`.

## Verification

## Failure Policy

Any missing entry, workflow, gate, source, output, or report path is BLOCKED. Do not fabricate consensus, holders, ratings, target prices, or filing data.

## Closeout

Report the gate status, artifact path, and blocks if any. Recheck/archive must preserve the JSON evidence.
