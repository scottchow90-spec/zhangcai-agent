---
name: stock-study
description: 面向单一股票的高级研究流程，覆盖公司概况、机构共识、机构活动、评级调整和风险。仅在用户明确调用 stock-study 或“高级股票研究”时使用。
---

# 高级股票研究

## 执行边界

- 目标系统固定为本机 Codex，不调用 OpenClaw 网关、注册表或旧总执行器。
- 与 `stock-analysis`、`stock-research-engine` 分开；只有本技能根入口可以启动本技能业务链。
- 市场事实、价格、评级、目标价和机构活动必须标注当前证据的来源与日期。
- 交付内容必须区分事实、假设、推断、风险和未验证项，不承诺收益。

## 唯一入口与唯一流程

唯一公开入口：

`python D:\C盘转移\日志\codex\skills\stock-study\scripts\codex_entry.py run -- --symbol 600519`

执行链固定为：

`codex_entry.py` → `run_stock_study.py` → 共享审计业务引擎中的 `stock-study` 专属合同 → JSON 落盘 → SHA-256 与字段回读。

`scripts/run_stock_study.py` 是根入口的私有委托器，不是第二个公开入口。禁止绕过根入口运行它。

## 唯一验收

- `codex_entry.py selftest` 必须为 `PASS`。
- 业务运行必须返回 `CLEAN_PASS`，结果文件必须存在并可解析。
- 结果中的 `skill` 必须精确等于 `stock-study`，且六个业务章节均显示已执行。
- 固定审计输入必须明确标注为审计样例；审计结果不是投资建议。

## 参考资料

- `references/business_spec.md`
- `references/workflow.md`
