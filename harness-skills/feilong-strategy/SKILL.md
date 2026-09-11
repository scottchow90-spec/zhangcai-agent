---
name: feilong-strategy
description: "Clean 飞龙 strategy workflow. Use for 飞龙, 飞龙在天, 飞龙选股, main uptrend, waveband launch, 飞龙在天, 飞龙选股, 主升浪, and 飞龙 formula interpretation. Use only when the user explicitly invokes $feilong-strategy or names the exact workflow “飞龙在天”; do not use as a generic stock router."
---

# 飞龙在天

## 独立调用边界

- 只处理原 OpenClaw 技能 `feilong-strategy` 对应的 技术分析 业务语义。
- 仅在显式调用 `$feilong-strategy` 或用户逐字点名“飞龙在天”时使用。
- 目标系统是本机 Codex；禁止调用 OpenClaw 网关、OpenClaw 股票总执行器或 OpenClaw 注册表。
- 不得自动改用兄弟股票技能，也不得让通用 `stock-research-codex` 抢占该固定流程。
- 权威公式只允许使用绑定源码 `references/formulas/飞龙在天.tdx.txt`；禁止调用、回退或引用旧公式 `飞龙在天4.0` 生成业务结果。

## 工作流

1. 先列出本技能目录中的实际参考文件，只读取清单中存在且与请求相关的文件。
2. 按 `references/` 中的业务规范和工作流执行；历史参考若与本文件冲突，以本文件为准。
3. 市场事实、行情、公告、新闻和监管信息必须使用当前回合的新鲜证据，并标注时间与来源。
4. 需要网页交互时只使用用户的 Google Chrome；不得切换到 Codex 内置浏览器。
5. 将事实、假设、推断、风险和未验证项分开；不得承诺收益或把结果表述为确定性投资建议。
6. 交付 Word/PPT 时调用对应文档技能并完成真实渲染、打开和视觉验证。

## 金叉术语硬约束

- 公式内部交叉条件面向用户统一命名为“金叉”。
- 对外只允许输出三种固定状态：`金叉`、`未形成金叉`、`金叉状态不可判定`。
- 不得使用“波”和“段”之间的大小、上下位置、穿越或差值关系替代金叉状态。

## 全子系统输出

联合技术分析时必须调用 `build_subsystem_rows()` 并完整输出固定 10 行，顺序为：

`龙头战法`、`趋势过滤/中长期均线强势条件`、
`四日实体重叠箱体/波段密码底层形态`、`首板/唯一涨停确认`、`波段密码打板`、
`量价模型/暴涨启动`、`波段随机强弱-波`、`波段随机强弱-段`、`私募秘进`、
`主升启动共振`。

禁止删行、合并行或以摘要替代。指数不适用项仍须保留原行并标记 `指数不适用`。
联合运行时不得另存飞龙独立对外报告，全部 10 行由 `technical-analysis` 并入唯一
29 行总表。

## 固定入口

- 技能信息与静态自检：`python D:\C盘转移\日志\codex\skills\feilong-strategy\scripts\codex_entry.py info` / `selftest`。
- 本地业务脚本：`scripts/feilong_realtime_report.py`；执行：`python D:\C盘转移\日志\codex\skills\feilong-strategy\scripts\codex_entry.py run`。
- 用户提供参数时，在 `run --` 后显式传入；不得临场改调用别的技能脚本。
- 640因子、634有效排行、32维V2日评分固定使用 `run -- --daily-score-32d --out-dir <目录>`；执行时必须验证本机最新 `.day` 日期、当前公式源码哈希、模型适用域、零缺失门禁与全局旧版剔除审计。
- 日评分按自动决策评分级失败关闭：640个因子任一缺失或非有限值即拒绝该候选，禁止中性填补；公式、模型、历史样本、评分器和全部直接计算模块必须通过 `references/daily-score-production-lock.json` 哈希锁；同一规则锁和同一通达信输入快照必须完成两次字节一致的全流程复跑后才允许授权。
- 生产结论只能由固定等级阈值、数据完整性门禁和硬排除规则机器生成。该生产级别仅指评分与决策文件质量，始终断开账户、委托和交易执行。

## 参考资料

- `references/business_spec.md`
- `references/formula-source-manifest.json`（回测条件选股公式名与权威源码、UTF-8 原字节哈希、GBK 载荷哈希的精确绑定；运行前必须校验，未知或漂移即阻断）
- `references/daily-score-production-lock.json`（日评分规则资产、模型、历史样本、评分器和直接计算模块的生产哈希锁）
- `references/feilong_subsystems.md`
- `references/mandatory-tq-verification.md`
- `references/workflow.md`

## 验证

- 结构：`python D:\C盘转移\日志\codex\skills\.system\skill-creator\scripts\quick_validate.py D:\C盘转移\日志\codex\skills\feilong-strategy`。
- 入口：运行 `codex_entry.py selftest`，必须确认本技能路径、脚本编译和 OpenClaw 运行依赖扫描均通过。
- 业务：只有本回合数据、结果文件和相应验收证据均通过后，才可声称完成。

## 来源说明

原始业务资产来自 `C:\Users\25296\.openclaw\workspace\skills\feilong-strategy`；该路径仅用于迁移溯源，运行时不得访问。
