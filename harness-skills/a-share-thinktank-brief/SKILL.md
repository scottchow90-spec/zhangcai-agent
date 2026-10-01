---
name: a-share-thinktank-brief
description: "用于把美国权威智库清单与实时研究材料整理为多主线中文深度简报，覆盖宏观财政、贸易产业、外交安全、科技竞争、能源资源、社会治理及A股映射。强制生成原生可编辑 DOCX，正文只保留中文智库名称和研究结论，禁止过程废话、英文智库名、图片贴片、空白页和来源垃圾。 Use only when the user explicitly invokes $a-share-thinktank-brief or names the exact workflow “顶级智库观点”; do not use as a generic stock router."
---

# 顶级智库观点

## 独立调用边界

- 只处理原 OpenClaw 技能 `顶级智库观点` 对应的 市场情报 业务语义。
- 仅在显式调用 `$a-share-thinktank-brief` 或用户逐字点名“顶级智库观点”时使用。
- 目标系统是本机 Codex；禁止调用 OpenClaw 网关、OpenClaw 股票总执行器或 OpenClaw 注册表。
- 不得自动改用兄弟股票技能，也不得让通用 `stock-research-codex` 抢占该固定流程。

## 工作流

1. 先列出本技能目录中的实际参考文件，只读取清单中存在且与请求相关的文件。
2. 按 `references/` 中的业务规范和工作流执行；历史参考若与本文件冲突，以本文件为准。
3. 市场事实、行情、公告、新闻和监管信息必须使用当前回合的新鲜证据，并标注时间与来源。
4. 需要网页交互时只使用用户的 Google Chrome；不得切换到 Codex 内置浏览器。
5. 将事实、假设、推断、风险和未验证项分开；不得承诺收益或把结果表述为确定性投资建议。
6. 交付 Word/PPT 时调用对应文档技能并完成真实渲染、打开和视觉验证。

## 固定入口

- 技能信息与静态自检：`python D:\C盘转移\日志\codex\skills\a-share-thinktank-brief\scripts\codex_entry.py info` / `selftest`。
- 正式业务必须显式提供两份本回合输入：`python D:\C盘转移\日志\codex\skills\a-share-thinktank-brief\scripts\codex_entry.py run -- --thinktank-md <智库清单.md> --brief-md <研究材料.md>`。
- 裸运行必须阻断；`doctor`、`selftest`、canary 和无输入 `auto` 只能证明静态健康，不能作为正式业务通过。
- 输出目录由 canonical runtime 强制指定，用户参数不得覆盖。DOCX 必须符合 `references/docx-layout-template.md`，通过正文清洁度、页数、表格、链接和空白页扫描，并写入 `business_artifact_manifest.json`。
- 同一显式 `CODEX_STOCK_BATCH_ID` 下只读复用同交易日共享证据集；批次、交易日或文件哈希不一致时阻断复用。

## 参考资料

- `references/business_spec.md`
- `references/canary_brief.md`
- `references/checklist.md`
- `references/docx-layout-template.md`
- `references/workflow.md`

## 验证

- 结构：`python D:\C盘转移\日志\codex\skills\.system\skill-creator\scripts\quick_validate.py D:\C盘转移\日志\codex\skills\a-share-thinktank-brief`。
- 入口：运行 `codex_entry.py selftest`，必须确认本技能路径、脚本编译和 OpenClaw 运行依赖扫描均通过。
- 业务：只有本回合数据、结果文件和相应验收证据均通过后，才可声称完成。

## 来源说明

原始业务资产来自 `C:\Users\25296\.openclaw\workspace\skills\顶级智库观点`；该路径仅用于迁移溯源，运行时不得访问。
