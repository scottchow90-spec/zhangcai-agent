---
name: financial-roe-analysis
description: "以资深财务分析师视角，基于杜邦分析体系对上市公司进行深度财务分析。适用场景：(1) 分析某只股票/上市公司的财务状况，(2) 深度拆解ROE驱动因素，(3) 评估公司盈利质量、资产运营效率、杠杆风险，(4) 输出机构投研标准的财务分析报告。触发词：财务分析、ROE分析、杜邦分析、股票财务、盈利质量、净利润质量、资产运营、财务报告、分析某公司、某股票怎么样（财务角度）。 Use only when the user explicitly invokes $financial-roe-analysis or names the exact workflow “财务ROE杜邦深度分析”; do not use as a generic stock router."
---

# 财务净资产收益率杜邦分析

## 独立调用边界

- 只处理原 OpenClaw 技能 `financial-roe-analysis` 对应的 股票研究 业务语义。
- 仅在显式调用 `$financial-roe-analysis` 或用户逐字点名“财务ROE杜邦深度分析”时使用。
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

- 技能信息与静态自检：`python D:\C盘转移\日志\codex\skills\financial-roe-analysis\scripts\codex_entry.py info` / `selftest`。
- 该技能是程序化知识工作流，没有可证明独立于 OpenClaw 的业务脚本；由 Codex 按参考资料执行，禁止调用旧包装器。

## 参考资料

- `references/business_spec.md`
- `references/industry-rules.md`
- `references/report-template.md`
- `references/roe-framework.md`
- `references/workflow.md`

## 验证

- 结构：`python D:\C盘转移\日志\codex\skills\.system\skill-creator\scripts\quick_validate.py D:\C盘转移\日志\codex\skills\financial-roe-analysis`。
- 入口：运行 `codex_entry.py selftest`，必须确认本技能路径、脚本编译和 OpenClaw 运行依赖扫描均通过。
- 业务：只有本回合数据、结果文件和相应验收证据均通过后，才可声称完成。

## 来源说明

原始业务资产来自 `C:\Users\25296\.openclaw\workspace\skills\financial-roe-analysis`；该路径仅用于迁移溯源，运行时不得访问。
