# quant-strategy-bundle-chen 业务规范

> 本文件只保留业务语义、数据口径、分析方法和产物要求。所有历史入口、命令、gate、fallback、临场脚本选择说明均已机械剥离；执行控制只认 `codex_entry.py`。

name: quant-strategy-bundle-chen
name_cn: 陈氏量化策略合集
description: Quantitative trading strategy bundle - Contains multiple verified A-stock quantitative trading strategy frameworks. Includes momentum strategies, reversal strategies, and trend strategies, with backtesting and signal generation support. Ideal for quantitative trading beginners and strategy development reference.
tags:
  - quant
  - trading
  - stock
  - strategy
  - backtest
version: 1.0.0
author: chenq

# quant-strategy-bundle

## Codex Execution Lock

## 科学工作流硬闸（2026-06-28）
数据、来源、证据、TDX、tdx-local-hub 是本技能的执行数据口径。指数、成交、涨跌家数、市场宽度、风险偏好、大盘必须进入宏观市场约束。公告、业绩、订单、产业链、个股、板块必须进入微观链条。新闻、政策、事实、观点、传闻、舆情必须分层。涨停、连板、炸板、趋势、量价、K线、支撑、压力只能作为技术证据。资金、主力、龙虎榜、机构、游资、散户必须标注来源。结论、评分、排序、过滤、剔除、Top 必须来自执行链证据。风险、失效、降级、排除、BLOCKED 必须明确。验收、验证、CLEAN_PASS、BLOCKED、selftest、gate 是唯一验收口径。


## Included Strategies

### 1. Momentum Strategy
- Principle: Buy stocks that have risen in the past
- Holding period: 5-20 days
- Best for: Bull markets

### 2. Reversal Strategy
- Principle: Buy stocks that have fallen in the past
- Holding period: 3-10 days
- Best for: Range-bound markets

### 3. Trend Strategy
- Principle: Follow the trend, buy high sell higher
- Holding period: 10-30 days
- Best for: Strong trending markets

## Usage

### Install Dependencies

### Basic Usage

## Configuration

Configure in `config.json`:
- Tushare token
- Stock pool
- Factor parameters
- Trading parameters

## Changelog

v1.0.0 - Initial release

# quant-strategy-bundle-chen Workflow

## Trigger

Use when Codex needs A-stock quantitative strategy framework selection, momentum/reversal/trend research, backtest planning, signal design, or strategy-risk review.

## Read Protocol

Codex must read `SKILL.md` and this `references/workflow.md` before execution. Do not invent a strategy run outside the locked entry.

## Preflight

Both gates must return CLEAN_PASS before any user-visible result is accepted.

## Entry

The only Codex entry is:

## Inputs

Inputs must identify stock pool, date range, factor definitions, price source, and backtest constraints. Missing data or dependencies produce BLOCKED.

## 科学工作流硬闸（2026-06-28）
数据、来源、证据、TDX、tdx-local-hub 是本技能的执行数据口径。指数、成交、涨跌家数、市场宽度、风险偏好、大盘必须进入宏观市场约束。公告、业绩、订单、产业链、个股、板块必须进入微观链条。新闻、政策、事实、观点、传闻、舆情必须分层。涨停、连板、炸板、趋势、量价、K线、支撑、压力只能作为技术证据。资金、主力、龙虎榜、机构、游资、散户必须标注来源。结论、评分、排序、过滤、剔除、Top 必须来自执行链证据。风险、失效、降级、排除、BLOCKED 必须明确。验收、验证、CLEAN_PASS、BLOCKED、selftest、gate 是唯一验收口径。


## Artifact

The closure gate writes a JSON artifact under `reports/unified_stock_skill_closure/`.

## Verification

## Failure Policy

Any missing entry, workflow, gate, source, output, backtest constraint, or report path is BLOCKED. Do not fabricate signals, returns, or model performance.

## Closeout

Report the gate status, artifact path, and blocks if any. Recheck/archive must preserve the JSON evidence.
