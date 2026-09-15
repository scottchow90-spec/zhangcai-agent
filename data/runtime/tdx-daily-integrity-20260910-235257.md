# 通达信个股日线完整性报告

- 目标交易日：**20260910**
- 股票清单：**5569** 只（来源：TQ get_stock_list(market=5)）
- 已对齐：**5562** 只
- stale：**0** 只；缺失文件：**7** 只；损坏：**0** 只
- 本轮写入：**0** 条；仍未补齐：**7** 只

## 未补齐清单

| 代码 | 市场 | 状态 | 文件最后日期 |
|---|---|---|---|
| 301716.SZ | SZ | missing_file | — |
| 601091.SH | SH | missing_file | — |
| 688801.SH | SH | missing_file | — |
| 688837.SH | SH | missing_file | — |
| 920201.BJ | BJ | missing_file | — |
| 920229.BJ | BJ | missing_file | — |
| 920298.BJ | BJ | missing_file | — |

## 补齐来源与结果

每个缺口依次尝试通达信 TQ `get_market_data(period=1d)` 与带 Referer 的东方财富 `push2his` 历史 K 线。只有明确返回目标日期时才会写入 `.day`；没有返回的数据保持缺口，不用估算值。

JSON 明细：`C:\work\260907 掌财智能体\CodeX-st-wsp\zhangcai-demo\data\runtime\tdx-daily-integrity-20260910-235257.json`
