---
name: five-dimension-resonance
description: "五维共振选股执行技能。候选池固定读取通达信自定义板块“飞龙在天”（C:\\new_tdx_mock\\T0002\\blocknew\\FLZT.blk），扫描该板块个股；个股排序统一复用 A-SHARE-STRONG-26F-100-V6.1 的26因子四轴短线评分，再叠加五公式和核心主线证据，执行7条硬剔除、15项风险扣分、Top10/Top3/次日观察计划。 Use only when the user explicitly invokes $five-dimension-resonance or names the exact workflow “五维共振选股”; do not use as a generic stock router."
---

# 五维共振选股

## 独立调用边界

- 只处理原 OpenClaw 技能 `five-dimension-resonance` 对应的 选股 业务语义。
- 仅在显式调用 `$five-dimension-resonance` 或用户逐字点名“五维共振选股”时使用。
- 目标系统是本机 Codex；禁止调用 OpenClaw 网关、OpenClaw 股票总执行器或 OpenClaw 注册表。
- 不得改路由到兄弟技能或从兄弟技能公开入口交付。本技能仅可在当前顶层入口内部调用合同绑定的 V6.1 权威计算器作为评分依赖；该调用不得绕过本技能的主线证据、公式证据和本轮回执。

## 工作流

1. 先列出本技能目录中的实际参考文件，只读取清单中存在且与请求相关的文件。
2. 按 `references/` 中的业务规范和工作流执行；历史参考若与本文件冲突，以本文件为准。
3. 市场事实、行情、公告、新闻和监管信息必须使用当前回合的新鲜证据，并标注时间与来源。
4. 个股总分只接受全局机器契约 `stock-unified/references/short_term_strong_stock_scoring_contract.json` 的精确版本 `A-SHARE-STRONG-26F-100-V6.1`。必须是26因子、四轴35/35/20/10、7条硬闸、15项风险、正向权重100、基本面正向权重0；版本、哈希、因子数或候选覆盖不一致时阻断评分与排序。
5. “核心主线评分系统”继续作为五维共振的独立证据闸，不再另行加进V6.1总分，避免对主线题材重复加权。本目录 `scripts/mainline_scoring.py` 只保留兼容转发；板块或个股正宗度证据缺失时 `decision_eligible=false`，禁止用涨幅、涨停身份或默认行业替代。
6. 需要网页交互时只使用用户的 Google Chrome；不得切换到 Codex 内置浏览器。
7. 将事实、假设、推断、风险和未验证项分开；不得承诺收益或把结果表述为确定性投资建议。
8. 交付 Word/PPT 时调用对应文档技能并完成真实渲染、打开和视觉验证。
9. 通达信实时公式不可用时，只允许固定 runner 复用已登记的历史公式原始 `raw_scan` 字段；旧评分、排序、风险、主线和结论字段不得复制。复用必须重新核验同交易日、同候选顺序、每只股票输入 `.day` 指纹、公式执行器指纹、来源扫描产物、来源回执和不可变证据行；任一不一致整包拒绝。本轮 V6.1 评分仍须由权威计算器重新生成，历史评分和历史授权不得复用。

## 执行与决策状态

- `status=CLEAN_PASS` 只表示候选池、V6.1评分、五公式、风险流程和主线证据链已按固定入口真实执行并通过审计。
- `decision_status=SIGNAL_FOUND` 才表示至少一只候选通过全部主线证据与硬门槛；`NO_SIGNAL` 只允许在全部候选证据完整且全部硬门槛失败时使用。
- `decision_status=DATA_REQUIRED` 表示V6.1评分契约/覆盖或主线证据存在缺口；缺口候选不得给代理分、不得进入排序，且 `decision_eligible=false`。它不得被表述为无信号或买卖结论。

## 固定入口

- 技能信息与静态自检：`python D:\C盘转移\日志\codex\skills\five-dimension-resonance\scripts\codex_entry.py info` / `selftest`。
- 本地业务脚本：`scripts/run_feilong_block_resonance.py`；执行：`python D:\C盘转移\日志\codex\skills\five-dimension-resonance\scripts\codex_entry.py run`。
- 用户提供参数时，在 `run --` 后显式传入；不得临场改调用别的技能脚本。

## 参考资料

- `references/business_spec.md`
- `references/cloud-adaptation.md`
- `references/conflict-rules.md`
- `references/formulas-capital.md`
- `references/formulas-daniuxian.md`
- `references/formulas-feilong.md`
- `references/scoring-model.md`
- `references/tq_fallback_compute.py`
- `references/workflow-chain.md`
- `references/workflow.md`

## 验证

- 结构：`python D:\C盘转移\日志\codex\skills\.system\skill-creator\scripts\quick_validate.py D:\C盘转移\日志\codex\skills\five-dimension-resonance`。
- 入口：运行 `codex_entry.py selftest`，必须确认本技能路径、脚本编译和 OpenClaw 运行依赖扫描均通过。
- 业务：只有本回合数据、结果文件和相应验收证据均通过后，才可声称完成。
- 历史公式事实复用不豁免“本回合验收”：正式适配器必须在本回合独立重算证据清单与全部输入指纹，最终报告须显式保留现场公式失败证据、来源产物哈希、来源回执哈希和复用审计状态。

## 来源说明

原始业务资产来自 `C:\Users\25296\.openclaw\workspace\skills\five-dimension-resonance`；该路径仅用于迁移溯源，运行时不得访问。
