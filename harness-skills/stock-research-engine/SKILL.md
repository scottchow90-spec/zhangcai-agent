---
name: stock-research-engine
description: 个股基本面深度研究引擎。仅在用户明确调用 stock-research-engine 或“个股研究引擎”时使用，不作为通用股票路由。
---

# 个股研究引擎

桌面端必须从 `STOCK_SKILLS_ROOT` 定位技能文件，不得使用旧开发机 D 盘绝对路径；通达信目录统一读取 `ZHANGCAI_TDX_ROOT`。

## 执行边界

- 目标系统固定为本机 Codex，不调用 OpenClaw 网关、注册表或旧总执行器。
- 与 `stock-analysis`、`stock-study` 分开；只有本技能根入口可以启动本技能业务链。
- 市场事实、行情、公告、新闻和监管信息必须使用当前回合的新鲜证据。
- 交付内容必须区分事实、假设、推断、风险和未验证项，不承诺收益。

## 唯一入口与唯一流程

唯一公开入口：

`python "%STOCK_SKILLS_ROOT%\stock-research-engine\scripts\codex_entry.py" run -- --symbol 600519`

执行链固定为：

`codex_entry.py` → `run_stock_research_engine.py` → 共享审计业务引擎中的 `stock-research-engine` 专属合同 → JSON 落盘 → SHA-256 与字段回读。

`scripts/run_stock_research_engine.py` 是根入口的私有委托器，不是第二个公开入口。禁止绕过根入口运行它。

## 唯一验收

- `codex_entry.py selftest` 必须为 `PASS`。
- 业务运行必须返回 `CLEAN_PASS`，结果文件必须存在并可解析。
- 结果中的 `skill` 必须精确等于 `stock-research-engine`，且六个业务章节均显示已执行。
- 业务数据与固定审计输入的边界必须在结果中明确标注；审计结果不是投资建议。

## 参考资料

- `references/analysis-framework.md`
- `references/business_spec.md`
- `references/workflow.md`
