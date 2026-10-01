# 执行协议

## 实战数据链

| 维度 | 强制证据 | 用途 |
|---|---|---|
| 指数环境 | 本地通达信上证指数最近两日 | 仅作日线方向；缺少五类指数分时时不得定指数周期阶段 |
| 市场宽度与流动性 | 本地通达信全部有效 A 股日线 | 涨跌家数、成交额及变化 |
| 涨跌停生态 | 短线侠与连板网 | 涨停、跌停、连板、炸板、封板率交叉验证 |
| 题材与龙头 | 连板网日期页及开放 JSON | 题材扩散、最高板、梯队 |

连板网是补充与交叉验证来源，署名“连板网”，附日期页 URL，CC BY 4.0。它不替代通达信或其他强制来源。

## 标准快照

快照必须含 `trading_date`、`market`、`topics`、`sources`、`comparisons`。`market` 必须含 `index_change_pct`、`advancers`、`decliners`、`total_amount_billion`、`amount_change_pct`、`limit_up`、`limit_down`、`consecutive`、`max_board`、`seal_rate`、`broken_board`、`topic_top_count`、`topic_count_ge3`。前一交易日涨停、跌停、连板、炸板、封板率直接使用短线侠报告值，不按价格涨幅阈值近似识别。

三源均须 `verified=true` 且 `trading_date` 完全相同。缺字段、源失败、通达信覆盖少于 3000 只或日期不一致均阻断。

## 输出

输出 `SHORT_TERM_MARKET_SENTIMENT_PDF_STRICT_V1` JSON，包含 `status`、`analysis_mode`、`single_stage_conclusion`、`short_term_stage_conclusion`、`cycles`、`observed_relationship`、`conflicts`、`evidence_limits`、`risk_boundary` 和 `sources`。`single_stage_conclusion`必须包含中级五阶段之一，`short_term_stage_conclusion`必须包含启动期至退潮期之一；两者都要有明确结论、证据、置信度、阶段级冲突清单、非空冲突说明和判定方法。没有直接冲突时也必须明确写明“未发现足以改变阶段判定的直接冲突”，禁止以空字段代替。禁止输出加权总分或把任一阶段写入选股分值。

来源间数值不一致时保留冲突说明，并以本地通达信的指数、宽度、成交额为基准，以短线侠和连板网交叉验证涨跌停生态。外部站点阶段标签只作补充观察；与引擎明确阶段不一致时必须列入冲突，不得静默覆盖内部证据结论。

## 固定入口

```powershell
python D:\C盘转移\日志\codex\skills\a-share-short-term-market-sentiment\scripts\codex_entry.py run
python D:\C盘转移\日志\codex\skills\a-share-short-term-market-sentiment\scripts\codex_entry.py authorize --receipt <runtime-receipt>
```

旧入口只接受股票统一入口设置的子进程环境，直接执行必须失败。
