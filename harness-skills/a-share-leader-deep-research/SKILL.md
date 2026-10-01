---
name: a-share-leader-deep-research
description: 龙头深度研究/龙头深度分析的A股涨停板研究与Word交付技能。按当前市场状态抓取最新交易日数据，使用东方财富为业务行情源、短线侠为补充交叉验证源，并记录本地通达信涨停池状态；将涨停股唯一归入八类一级投资板块，生成动态性质榜、龙1至龙10地位榜、封板时间、龙虎榜和正式大字版Word报告。点名“龙头深度研究”“龙头深度分析”或“龙头分析”时使用，不得路由为热点龙头或通用研究。
---

# 龙头深度研究

## 唯一执行入口

先按权威股票路由确认技能，再通过固定入口执行：

```powershell
python D:\C盘转移\日志\codex\scripts\stock_canonical_runtime.py route --query "<用户原话>"
python D:\C盘转移\日志\codex\skills\a-share-leader-deep-research\scripts\codex_entry.py run -- run --output <最终DOCX>
```

默认 canonical 执行必须进入真实 `run`，禁止以 `info`、静态说明、自造临时生成器或旧 DOCX 代替业务运行。

历史收盘报告因逻辑代码修订需要重算时，只允许使用 `replay`：输入必须是本技能权威运行目录内、已由干净结论回执和结论授权共同绑定的 `leader_payload.json`；当前证据集批次、证据集 ID 和交易日必须与原回执完全一致。重算只允许改动逻辑模型、性质榜、地位榜和对应角色，事实层指纹前后必须一致。禁止把任意旧 JSON、旧 DOCX 或跨交易日实时数据送入历史重算。

```powershell
$env:CODEX_STOCK_BATCH_ID='<原授权证据批次>'
python D:\C盘转移\日志\codex\skills\a-share-leader-deep-research\scripts\codex_entry.py run -- replay --input <已授权leader_payload.json>
```

## 端到端顺序

1. 由腾讯与新浪双源行情确定最新交易日和市场阶段，禁止人工指定旧日期。
2. 在本轮新目录实时抓取东方财富涨停池、龙虎榜和短线侠 `ztpool/ztplate/ztcount`。
3. 东方财富与短线侠涨停代码集合必须逐只一致；不一致立即非零退出。本地通达信 `ZTC.blk` 同日时作为本地旁证，过期时明确记录降级状态，不冒充当前来源。
4. 依据 `references/classification_rules.md` 唯一归入八类一级投资板块，细分方向和当日推动因素分开记录。
5. 对前三板块建立“共同产业机制、共同事件证据、因果边界、机制锚与高度锚、时序共振、盘面验证、结构约束”模型；只罗列数量不构成逻辑，题材共现和封板先后不得冒充因果。
6. 生成结构化结果并通过 `audit_payload.py` 与实时新鲜度复核；逻辑模型的覆盖成员、锚点、梯队和封板统计必须可复算。
   历史重算改用原结论回执、结论授权、证据集三重绑定和事实层指纹复核，不用当前盘中行情替换历史事实。
7. 仅使用技能内 `scripts/report_builder.py` 和 `references/report_template_contract.json` 生成 Word。
8. 仅使用 `scripts/word_com_render.py` 调用 Microsoft Word COM 重开 DOCX、导出 PDF 和逐页 PNG；禁止调用 LibreOffice、`soffice` 或通用 `render_docx.py`。随后由 `scripts/report_validator.py` 检查页面顺序、字体、表格结构、机器标记、内容完整性、逻辑有效性和页面密度。
9. 任何阶段失败均返回 `BLOCKED` 和非零退出码，不生成可交付结论。

## 正式 Word 模板

- 默认正式交付文件名固定为 `龙头深度研究_YYYY-MM-DD.docx`，日期必须是本轮最新交易日；禁止使用英文测试名、英文草稿名或英文报告名作为用户可见文件名。
- 第一页直接进入业务封面与当日核心判断，不设置独立风险教学页。
- 正文固定微软雅黑 11 磅；标题阶梯为 30/21/16/13 磅；表格文字不小于 9.5 磅。
- 页面顺序固定为：业务封面与当日核心判断、一页看懂、市场高度、八类全景、前三板块深析、上午封板、龙虎榜。
- 禁止用大量 1×1 表格拼页面，禁止缩小字体压页，禁止把全量数据拆成碎片化卡片。
- 正式报告只展示市场结论和个股事实；运行规则、来源对账、失败条件、审计过程、差异处理、本地旁证和筛选门槛解释只能保留在内部运行证据中，禁止进入可见正文。
- 正式 Word 必须通过内容身份硬闸：核心标题和主题须指向龙头深度研究业务报告，正文须达到实质内容下限并覆盖本轮足量股票代码；说明、核验、审计、机制或纠错文档不得替代正式业务交付。
- DOCX 必须写入本轮数据 SHA-256、模板合同 SHA-256 和 `STOCK_DATA_TRADE_DATE=YYYY-MM-DD`。

## 研究边界

- 一级投资板块只能是大消费、医药生物、大科技、高端制造、新能源、基建公用、金融地产、周期资源；每股只能归入一类。
- 性质榜回答“当天承担什么作用”；地位榜回答“板块内排第几”。两榜最多 10 只，证据不足即缩短，不补位。
- 地位榜必须逐席位解释排序逻辑：龙1、龙2至少写明相对下一席位的首个有效差异项，龙3写明相对上席位的主要落后项；每席同时给出可复算硬指标、相对比较、主要短板和失效条件。仅罗列共同机制、封板时点、跟随数或开板次数，不构成地位依据。
- 地位结论必须概括前三席位的胜负链和板块结构是否分离；固定套话、高相似度理由、把性质锚点替代地位排序，均由审计与 Word 验收直接阻断。
- 板块逻辑回答“共同产业机制、机制锚、高度锚与同题材时序共振如何形成可观察的盘面结构，并由哪些事实验证、受到哪些结构短板约束”。共同事件证据必须单列；没有覆盖多只成员的同一可核验事件时，必须明确写出因果边界，禁止把题材共现、行业归类或封板先后称为事件催化或因果带动。
- 性质榜与地位榜独立生成。地位排名不能自动产生“板块龙头”性质，性质标签也不能反过来决定排名。
- 盘中只陈述截至当前时点状态；收盘后使用最新已完成交易日收盘数据。
- 龙虎榜仅展示研究日公开数据中去重后净买入不低于 1 亿元且席位明细可复算的涨停股。
- 所有结论必须由本轮数字事实动态生成，禁止旧结论、固定结论和预测性荐股措辞。

## 独立验证

```powershell
python D:\C盘转移\日志\codex\skills\a-share-leader-deep-research\scripts\codex_entry.py run -- selftest
python D:\C盘转移\日志\codex\skills\.system\skill-creator\scripts\quick_validate.py D:\C盘转移\日志\codex\skills\a-share-leader-deep-research
```

已生成文件可通过真实业务验收器复核：

```powershell
python D:\C盘转移\日志\codex\skills\a-share-leader-deep-research\scripts\codex_entry.py run -- verify-report --file <DOCX> --input <结构化结果JSON> --manifest <本轮manifest> --render-dir <逐页PNG目录>
```
