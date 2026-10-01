---
name: a-share-limit-up-leader-classification
description: A股每日涨停板龙头分类工作流。按当日主概念统计涨停家数，在每个概念内分别生成龙头性质榜和龙1至龙10地位榜，再生成上午封板时间表及当日龙虎榜净买入一亿元以上名单，最终交付经过风险首页、数据审计和逐页核验的精美Word。仅当用户明确调用$a-share-limit-up-leader-classification或点名“每日涨停板龙头分类”时使用；不得替代连板挖掘或其他具名选股流程。
---

# 每日涨停板龙头分类

## 当前状态

- 先读取 `workflow_manifest.json`。
- `live_run_allowed=false` 时只允许说明、审核、结构自检和合成数据测试；禁止采集当日行情、生成当日结论或交付实盘报告。
- 只有用户明确审核通过后，才可把该字段改为 `true` 并执行首次实跑。
- `live_run_allowed=true` 只表示审批开关已打开，不等于已有正式实跑执行器，更不等于业务完成。
- `review`、`validate`、`verify-docx`、`info` 和 `selftest` 都是辅助动作，统一执行合同必须禁止它们生成业务成功回执。
- 在固定入口提供真正的数据采集、分类、成文和交付动作之前，本技能的真实业务状态必须保持未完成；不得用辅助动作、合成样本或旧回执冒充。

## 唯一业务边界

- 目标系统：本机 Codex。
- 范围：最新已完整收盘的 A 股交易日，当日收盘仍封在适用涨停价的股票。
- 结果不是选股推荐，只做概念归类、龙头性质判断、板块地位排序、上午封板时间排序和龙虎榜净买入筛选。
- 不调用、替换或混入“连板挖掘”“连板挖掘v2”等其他具名工作流。
- 不读取旧报告正文、旧结论或旧运行数据。每次运行从空白目录开始，只允许复用样式规则和中央风险提示资源。

## 执行入口

```powershell
python D:\C盘转移\日志\codex\skills\a-share-limit-up-leader-classification\scripts\codex_entry.py info
python D:\C盘转移\日志\codex\skills\a-share-limit-up-leader-classification\scripts\codex_entry.py run -- review
python D:\C盘转移\日志\codex\skills\a-share-limit-up-leader-classification\scripts\codex_entry.py selftest
python D:\C盘转移\日志\codex\skills\a-share-limit-up-leader-classification\scripts\codex_entry.py run -- validate --input <本轮结构化结果.json>
python D:\C盘转移\日志\codex\skills\a-share-limit-up-leader-classification\scripts\codex_entry.py run -- verify-docx --file <本轮最终DOCX>
python D:\C盘转移\日志\codex\skills\a-share-limit-up-leader-classification\scripts\codex_entry.py verify --receipt <统一门面回执.json>
```

`validate` 只审计结构化结果，不代表可以交付 Word。正式交付还必须通过后述 Word 和股票文件闸门。

## 固定执行顺序

1. 读取 `references/workflow.md`，锁定交易日、运行目录、证据链和失败规则。
2. 读取 `references/data_contract.md`，采集并交叉核验涨停池、封板时间、主概念和龙虎榜数据。
3. 读取 `references/classification_rules.md`，动态生成概念、性质和地位；不预设角色一定出现，也不预设榜单数量。
4. 写出本轮结构化结果，运行 `codex_entry.py run -- validate`；任何关键冲突或数据缺口都阻止正式报告。
5. 读取 `references/report_spec.md`，用全新空白 Word 文档生成报告。正文只允许从本轮已验证数据和证据化结论生成。
6. 同时使用 `$polished-word-delivery`、`$documents` 和 `$stock-delivery-risk-gate`。第一页使用中央股票风险提示，业务内容从第二页开始。
7. Word 写出后立即运行 `codex_entry.py run -- verify-docx --file <本轮最终DOCX>`；结论必须在同一个 Word 段落中按“结论：……依据：……反证：……”呈现，结论和依据都必须含本轮数字事实。此处不通过时禁止进入耗时的导出和逐页检查。
8. 用 Word 打开、计算页数并导出 PDF；逐页检查清晰度、错页、空白页、表格截断和旧内容污染。
9. 对最终 DOCX 运行中央股票文件 `gate`，立即再运行 `verify-receipt`；只有当前文件哈希对应的 PASS 回执才允许提供链接。
10. 最终正文只要发生一次修改，步骤 7 至 9 的检查和收据全部作废并必须按原顺序重跑；禁止拿旧哈希收据交付新文件。

## 结论纪律

- 每只股票只计入一个“当日主概念”，副概念只展示、不计数，保证总数能与涨停池一一对账。
- 不使用“其他、综合概念、待定、未知”等含糊分类。无法核实主概念时，先补证据；仍无法核实时阻止正式报告。
- 龙头性质只在事实成立时出现；允许没有市场总龙头、没有情绪龙头或没有任何某类角色。
- 性质榜和地位榜每个概念最多展示 10 只；不足 10 只就展示实际数量，不补位、不凑数。
- 地位榜只能按同概念内的当日事实比较产生。证据无法拉开差距时缩短榜单并写明“证据不足，未继续强排”。
- 上午盘名单只含最终封板时间不晚于 11:30:00 且收盘仍涨停的股票，按首次封板时间从早到晚排序。
- 龙虎榜名单只含当日正式上榜、去重后净买入额不低于 100000000 元的涨停股；未上榜是“无当日龙虎榜记录”，不得写成零。
- 事实、比较判断、数据缺口分开记录；不使用收益承诺、固定措辞或脱离证据的泛化判断。
- 结论块数量等于本轮 `report_claims` 实际数量，不固定为 4 条或任何预设数量；没有符合项时也只能由本轮空结果生成带数字事实的结论。

## 数据与浏览器规则

- 行情和市场事实必须在本次运行重新获取，并保留来源、抓取时间、交易日、定位信息和文件或响应哈希。
- 同一网站的网页、接口和转接库视为同一来源组，不能冒充两个独立来源。
- 优先使用直接文件、公开接口、交易所披露和本地解析；只有确需网页交互时才使用用户的 Google Chrome，任务中不得切换浏览器表面。
- 关键字段缺少两个独立来源组或存在未解决冲突时，不得补零、猜测、沿用旧值或降级为模板结论。

## 资源

- `references/workflow.md`：完整执行与失败边界。
- `references/data_contract.md`：数据字段、来源和新鲜度规则。
- `references/classification_rules.md`：概念、性质、地位、时间和龙虎榜口径。
- `references/report_spec.md`：Word 章节、动态成文和交付验收。
- `scripts/audit_payload.py`：结构化结果硬审计。
- `scripts/codex_entry.py`：审核、自检和验证入口。

## 验证

```powershell
python D:\C盘转移\日志\codex\skills\.system\skill-creator\scripts\quick_validate.py D:\C盘转移\日志\codex\skills\a-share-limit-up-leader-classification
python D:\C盘转移\日志\codex\skills\a-share-limit-up-leader-classification\scripts\codex_entry.py selftest
```
