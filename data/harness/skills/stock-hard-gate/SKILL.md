---
name: stock-hard-gate
description: "股票操作文本与公式名称的只读执行前硬闸。仅在用户显式调用 $stock-hard-gate 或逐字点名“硬闸”时使用；不作通用股票路由，不生成研究结论或候选股。"
---

# 硬闸

## 职责边界

- 只处理股票任务执行前检查：用户原话回读、范围约束、公式规范、禁止声明和假交付阻断。
- 仅在显式调用 $stock-hard-gate 或用户逐字点名“硬闸”时使用。
- 目标系统固定为本机 Codex。
- 不得自动改用兄弟股票技能，也不得让通用 stock-research-codex 抢占该固定流程。
- 易混淆但必须分开的技能：stock-deliverable、stock-unified。
- 本技能只做股票任务预飞检查，不生成研究结论或候选股。

## 唯一入口

固定公开入口：

    python D:\C盘转移\日志\codex\skills\stock-hard-gate\scripts\codex_entry.py

允许的公开动作是 info、selftest、run、verify、authorize 和 complete。业务检查必须通过 run 或 complete 进入统一股票运行时，再由合同绑定的适配器调用 scripts/preflight.py。

禁止直接执行 legacy_codex_entry.py、preflight.py 或其他内部脚本。内部脚本均默认拒绝脱离统一运行时的直接调用。

## 执行合同

1. 先通过唯一股票路由确认 stock-hard-gate 所有权。
2. 把待检查的计划文本和可选动作放在 run -- 后，不得临场改用别的技能。
3. 无显式参数时，固定适配器运行一份完整正向 canary；这只用于验证硬闸执行链，不代表完成任何股票研究。
4. 命中错误名称、禁止声明、范围缺失或回读缺失时必须返回 BLOCKED 和非零退出码。
5. 本技能没有业务降级或外部数据 fallback；失败只能修复输入、依赖或实现后重跑。
6. TdxW/tdxcef 只允许身份快照和只读数据访问。任何关闭、重启、挂起、替换或进程控制调用必须由统一运行时在调用前阻断并记录。

## 完成标准

- 正向输入必须为 CLEAN_PASS，反向输入必须为 BLOCKED。
- 回执必须通过 verify 回读，哈希合同和业务绑定必须一致。
- complete 的重试记录、最终状态和 TdxW/tdxcef 守卫证据必须可复验。

## 参考资料

- references/business_spec.md
- references/workflow.md

本技能由本机 Codex 历史备份恢复。历史来源只用于审计，运行时不得访问迁移源、WorkBuddy 目录或旧 OpenClaw 路径。
