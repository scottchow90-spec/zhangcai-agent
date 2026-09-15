---
name: four-strategy-system
description: 使用本机通达信日线全市场执行起浪坑、临空、接体、伏虎四套固定技术条件。仅在用户明确调用 four-strategy-system 或“四策略系统”时使用。
---

# 四策略系统

## 唯一入口

`python D:\C盘转移\日志\codex\skills\four-strategy-system\scripts\codex_entry.py run`

唯一执行链为根入口委托 `run_four_strategy_smoke.py`，扫描本机 `C:\new_tdx_mock\vipdoc` 日线，执行四组固定条件，落盘后回读。内部脚本不是第二个公开入口。

## 固定条件

- 起浪坑：60 日回撤至少 15%，距 60 日低点不超过 18%，收盘重上 MA5 且 3 日动量转正。
- 临空：收盘突破前 20 日高点，MA5 > MA10 > MA20，5 日对 20 日量比至少 1.2。
- 接体：5 日涨幅至少 8%，前一日回落，当日转强且收盘不低于 MA10。
- 伏虎：MA20 > MA60，收盘贴近 MA20 正负 3%，当日转强且 20 日低点未有效跌破 MA60。

## 唯一验收

- 四个条件必须全部执行，`strategy_count == 4`。
- 数据源必须是本机 TDX 日线，结果必须记录最新交易日。
- 有信号时为 `SIGNAL`；无信号时为真实 `NO_SIGNAL`，不得伪造候选。
- 当前 JSON 必须重新解析，并输出大小与 SHA-256。
