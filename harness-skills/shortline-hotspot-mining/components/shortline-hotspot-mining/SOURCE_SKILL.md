---
name: shortline-hotspot-mining
description: "Unified A-share short-term hotspot research workflow combining theme discovery, sector rotation, daily anomaly scanning, catalysts, evidence grading, scoring, risk checks, and manual review. Use only when the user explicitly invokes $shortline-hotspot-mining or names 短线热点挖掘、热点挖掘、题材发现、板块轮动、短线热点挖掘工作流 or 每日热点挖掘; do not use as a generic stock router."
---

# 短线热点挖掘

## 统一边界

- 将原 `hotspot-mining`、`wf2-hotspot-mining`、`daily-hotspot-mine` 的有效内容统一到本技能；不得再调用三个旧目录或旧脚本。
- 目标系统是本机 Codex。不得调用 OpenClaw 网关、OpenClaw 股票总执行器或其注册表。
- 仅提供基于证据的研究支持，不承诺收益，不把候选方向表述为确定性投资建议。
- 市场事实、政策、公告、新闻、监管和日历均属时效信息；每次运行必须获取本回合的新鲜证据并标注时间与来源。
- 三种模式均默认检查韭研公社热度页 `https://www.jiuyangongshe.com/study_hot`，仅用于热点文章、题材映射和市场关注度；强事实必须回查官方或权威来源。

## 选择模式

- `完整模式`：默认。合并题材发现、板块轮动和每日异动验证，输出未来 1–10 个交易日的 Top 3–5 方向。
- `发现模式`：用户只要求题材发现、板块轮动、政策或产业催化时使用；仍需用行情、技术和资金证据验证。
- `每日模式`：用户点名每日热点、盘后扫描或已知异动排序时使用；先做本地量化扫描，再补最少必要的事件证据。

三种模式共用同一技能、同一证据口径和同一验收标准，不拆回多个技能。

## 必读资源

1. 始终读取 `references/business_spec.md` 和 `references/workflow.md`。
2. 完整模式或发现模式必须再读取 `references/scoring_and_evidence.md`。
3. 每日模式在需要最终排序、舆情判断或回测说明时再读取 `references/scoring_and_evidence.md` 的对应章节。

## 固定流程

1. 锁定模式、运行时间、市场时段、目标窗口和用户要求的交付格式。
2. 对 A 股板块池、成分股和 K 线先使用本地 TDX；远程行情只能补充本地缺失字段或交叉验证，不得静默替代。
3. 完整、发现、每日三种模式均采集韭研公社热度文章与市场观点作为热点发现线索；需要登录态时只通过用户的 Google Chrome，不保存凭证。
4. 需要确定性本地扫描时，从唯一入口执行：

   `python D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\codex_entry.py run -- --manual-confirm --mode <full|discovery|daily>`

5. 按 `references/workflow.md` 完成时间锚定、信号发现、去重过滤、候选池、两阶段评分、反向证据、窗口分档、输出和验收。
6. 将事实、假设、推断、风险和未验证项分开；任何缺失数据必须在对应维度就地声明。
7. 需要网页交互时只使用用户的 Google Chrome；不得切换到 Codex 内置浏览器。
8. 用户要求 Word/PPT 时，调用对应文档技能并完成真实打开、渲染或导出及逐页视觉检查。

## 唯一入口与检查

- 信息：`python D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\codex_entry.py info`
- 静态自检：`python D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\codex_entry.py selftest`
- 数据前检：`python D:\C盘转移\日志\codex\skills\shortline-hotspot-mining\scripts\preflight.py`
- 本地扫描：通过 `codex_entry.py run -- ...` 传递参数；不得直接改用旧技能脚本。

## 完成标准

- 只有本轮数据、候选池、评分、证据、风险、失效条件、产物路径和审计结果均可读回时，才可声称完成。
- 盘中快照必须标注为盘中；历史或补跑必须标注实际数据截止交易日。
- 任一强结论缺少来源锚点、时间或字段证据时，降级为弱结论；关键数据全部缺失时返回 `BLOCKED`。
