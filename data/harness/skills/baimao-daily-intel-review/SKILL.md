---
name: baimao-daily-intel-review
description: "白猫老师每日资讯及复盘报告工作流。用于A股每日早盘资讯、午盘异动推送、每日复盘报告、市场新闻、监管异动、隔夜外盘、指数情绪、板块涨跌、沪深300与微盘风格分析。触发于“白猫老师每日资讯及复盘报告”“白猫每日资讯”“早盘资讯”“午盘异动”“每日复盘报告”“A股资讯复盘”等请求。 Use only when the user explicitly invokes $baimao-daily-intel-review or names the exact workflow “白猫老师每日资讯及复盘报告”; do not use as a generic stock router."
---

# 白猫老师每日资讯及复盘报告

## 独立调用边界

- 只处理原 OpenClaw 技能 `baimao-daily-intel-review` 对应的 股票研究 业务语义。
- 仅在显式调用 `$baimao-daily-intel-review` 或用户逐字点名“白猫老师每日资讯及复盘报告”时使用。
- 目标系统是本机 Codex；禁止调用 OpenClaw 网关、OpenClaw 股票总执行器或 OpenClaw 注册表。
- 不得自动改用兄弟股票技能，也不得让通用 `stock-research-codex` 抢占该固定流程。

## 工作流

1. 先列出本技能目录中的实际参考文件，只读取清单中存在且与请求相关的文件。
2. 按 `references/` 中的业务规范和工作流执行；历史参考若与本文件冲突，以本文件为准。
3. 市场事实、行情、公告、新闻和监管信息必须使用当前回合的新鲜证据，并标注时间与来源。
4. 默认采集韭研公社热度页 `https://www.jiuyangongshe.com/study_hot`，用于昨日盘后大事、9-15 点高热新闻、事件池和主题聚类的热点文章与题材线索；不得替代公告级事实源。
5. 需要网页交互或登录态时只使用用户的 Google Chrome；不得切换到 Codex 内置浏览器，不得保存凭证。
6. 将事实、假设、推断、风险和未验证项分开；不得承诺收益或把结果表述为确定性投资建议。
7. 交付 Word/PPT 时调用对应文档技能并完成真实渲染、打开和视觉验证。

## 固定入口

- 技能信息与静态自检：`python D:\C盘转移\日志\codex\skills\baimao-daily-intel-review\scripts\codex_entry.py info` / `selftest`。
- 正式业务必须显式提供本回合证据包：`python D:\C盘转移\日志\codex\skills\baimao-daily-intel-review\scripts\codex_entry.py run -- --evidence <证据包.json> --mode <morning|midday|closing>`。
- 裸运行必须阻断；`generate`、`fixture`、`selftest`、`doctor` 和数据准备单都不是正式业务通过证据。
- 输出目录由 canonical runtime 强制指定，用户参数不得覆盖。只有 Markdown、JSON、DOCX、质量闸与 `business_artifact_manifest.json` 全部通过，才可返回 `CLEAN_PASS`。
- 同一显式 `CODEX_STOCK_BATCH_ID` 下只读复用同交易日共享证据集；批次、交易日或文件哈希不一致时阻断复用。

## 参考资料

- `references/business-blueprint.md`
- `references/business_spec.md`
- `references/data-source-matrix.json`
- `references/evidence-schema.json`
- `references/scoring-model.json`
- `references/source-requirement.md`
- `references/workflow.md`

## 验证

- 结构：`python D:\C盘转移\日志\codex\skills\.system\skill-creator\scripts\quick_validate.py D:\C盘转移\日志\codex\skills\baimao-daily-intel-review`。
- 入口：运行 `codex_entry.py selftest`，必须确认本技能路径、脚本编译和 OpenClaw 运行依赖扫描均通过。
- 业务：只有本回合数据、结果文件和相应验收证据均通过后，才可声称完成。

## 来源说明

原始业务资产来自 `C:\Users\25296\.openclaw\workspace\skills\baimao-daily-intel-review`；该路径仅用于迁移溯源，运行时不得访问。
