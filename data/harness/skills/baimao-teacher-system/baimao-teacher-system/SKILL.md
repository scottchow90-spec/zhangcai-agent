---
name: baimao-teacher-system
description: "白猫老师六公式通达信体系技能。用于检查、调用和说明已经转换并安装到 C:\\\\new_tdx_mock 的六个通达信公式：白猫RSI、白猫渡劫、白猫队长、躲猫猫、黑猫白猫、平均成本线。触发于“白猫老师体系”“白猫公式”“白猫RSI”“白猫渡劫”“白猫队长”“躲猫猫”“黑猫白猫”“平均成本线”等请求。 Use only when the user explicitly invokes $baimao-teacher-system or names the exact workflow “白猫老师六公式通达信体系”; do not use as a generic stock router."
---

# 白猫老师六公式通达信体系

## 独立调用边界

- 只处理原 OpenClaw 技能 `baimao-teacher-system` 对应的 量化与策略 业务语义。
- 仅在显式调用 `$baimao-teacher-system` 或用户逐字点名“白猫老师六公式通达信体系”时使用。
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

- 技能信息与静态自检：`python D:\C盘转移\日志\codex\skills\baimao-teacher-system\scripts\codex_entry.py info` / `selftest`。
- 本地业务脚本：`scripts/baimao-teacher-system.py`；执行：`python D:\C盘转移\日志\codex\skills\baimao-teacher-system\scripts\codex_entry.py run  # 默认参数：auto`。
- 用户提供参数时，在 `run --` 后显式传入；不得临场改调用别的技能脚本。

## 参考资料

- `references/business_spec.md`
- `references/formulas.json`
- `references/kline-research-20260629.json`
- `references/workflow.md`

## 验证

- 结构：`python D:\C盘转移\日志\codex\skills\.system\skill-creator\scripts\quick_validate.py D:\C盘转移\日志\codex\skills\baimao-teacher-system`。
- 入口：运行 `codex_entry.py selftest`，必须确认本技能路径、脚本编译和 OpenClaw 运行依赖扫描均通过。
- 业务：只有本回合数据、结果文件和相应验收证据均通过后，才可声称完成。

## 来源说明

原始业务资产来自 `C:\Users\25296\.openclaw\workspace\skills\baimao-teacher-system`；该路径仅用于迁移溯源，运行时不得访问。
