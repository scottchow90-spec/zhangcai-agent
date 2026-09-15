---
name: a-share-sentiment-workflow
description: "Generate the unified A股热点舆情研判 report with mandatory eight-site sentiment collection, dynamic A-share-linked Business Society evidence, Lianban/Tongdaxin/Duanxianxia market cross-validation, daily-intel and two-level short-term-sentiment derived views, causal evidence chains, one DOCX, and machine-readable audits."
---

# A股热点舆情研判

## 调用边界

- 本组件是统一业务实现；“A股舆情分析工作流”“五站A股舆情研判”“市场情报”“三端社媒财经简报”均为兼容名称。
- 不生成独立市场情报报告、独立社媒报告或三端社媒固定模板。
- 网页交互只使用用户的 Google Chrome；程序不得读取或保存浏览器凭证。
- 唯一入口和生产命令：`python scripts/codex_entry.py run -- generate --out-dir <目录>`。

## 固定执行顺序

1. 读取 `references/business_spec.md`、`references/workflow.md` 和 `references/checklist.md`。
2. 校验固定模板、滚动 72 小时窗口、最近三个完整交易日和本地最新闭市日。
3. 强制采集淘股吧、雪球、微博、知乎、东方财富股吧、韭研公社、财联社、金十数据，每站不少于 10 条。
4. 检查每条事件的发布时间、独立 URL、来源级热度真实性、A 股映射语义、网页残留、原始/清洗计数和去重键；`重要度0`、泛化映射或计数无来源增长不得计数，任一站不合格即 `BLOCKED`。
5. 把八站有效事件纳入统一事件池；生意社本轮官方页面商品事件只有动态命中本轮 A 股主题后才能纳入。
6. 对统一事件做规范化、证据分级、跨源去重和冲突登记；重复来源只算佐证，不增加事件权重。
7. 从同一事件池派生早盘、午盘、收盘资讯视图；从同一市场验证池派生涨停家数、连板晋级、热点扩散、成交额、市场宽度五维事实，以及中级周期与短线情绪阶段，保留置信度和冲突，禁止加权总分。
8. 使用连板网、通达信、短线侠验证热点、板块、涨停、晋级、成交额；三源必须齐全且每个维度至少两源。
9. 构建触发事实、盘面确认、参与者确认和反证链，执行主题绑定、来源、唯一性、方向和评分硬闸。
10. 生成唯一 Word，并在首页写明五级短线情绪判断、五维事实、中级周期、短线阶段、置信度和冲突说明。
11. 验收全部 JSON 审计、Word 结构、Word 真实打开、页数、PDF、逐页图片、空白页、页底溢出和全页接触表；任一失败即 `BLOCKED`。

## 事实边界

- 社区和社媒观点可用于热度、关注方向、分歧、风险偏好和短线情绪。
- 社区观点不能单独证明公告、政策、监管、订单、业绩、资产注入等强事实；这些结论必须回查官方或权威财经原文。
- 榜单观察时刻不能冒充原帖发布时间。
- 不承诺收益，不触碰账户或下单接口。
- 顶级智库观点不进入事件池；黄金情报系统与比特币新闻情报技能不修改、不调用、不形成依赖。

## 必须产物

- `a_share_sentiment_event_pool.json`
- `a_share_sentiment_raw_event_pool.json`
- `a_share_sentiment_unified_event_pool.json`
- `a_share_sentiment_market_validation_pool.json`
- `a_share_sentiment_mandatory_sources_audit.json`
- `a_share_sentiment_market_cross_validation_audit.json`
- `a_share_sentiment_acquisition_audit.json`
- `a_share_sentiment_clusters.json`
- `a_share_sentiment_scores.json`
- `a_share_sentiment_audit.json`
- `a_share_sentiment_redline_audit.json`
- `a_share_sentiment_delivery_audit.json`
- `a_share_sentiment_source_integration_audit.json`
- `a_share_sentiment_daily_intel_view.json`
- `a_share_sentiment_short_term_sentiment_view.json`
- `a_share_sentiment_conflict_register.json`
- `A股三日舆情解读结果_Codex自动生成.docx`

## 完成条件

- 八站每站有效数量均不少于 10。
- 连板网、通达信、短线侠三源均存在，热点、板块、涨停、晋级、成交额每项至少两源。
- 红线审计和交付审计 `ok=true`，Word 渲染审计 `status=PASS` 且七项检查全部为真。
- 来源集成审计 `ok=true`，且无预设板块池、无排除技能运行依赖。
- 唯一 Word 包含“短线情绪判断：强势/偏强/中性分化/偏弱/退潮”之一，并写明五维事实、中级周期、短线阶段、置信度和冲突说明。
