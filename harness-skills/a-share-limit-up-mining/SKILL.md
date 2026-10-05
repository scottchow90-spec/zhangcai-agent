---
name: a-share-limit-up-mining
description: "统一、审计后的 A 股妖股挖掘工作流。以原连板挖掘为唯一底座，吸收连板挖掘V2的本地 TDX 最新交易日解析与失败阻断能力，以及连板龙头选股、连板龙头选股工作流、每日连板龙头中经验证合理的两连板复算、5维快筛、8因子研究、风险组合规则、LHBFP/QSGFX/QSYB/RDXZ 证据链与 Word 硬闸。Use only when the user explicitly invokes $a-share-limit-up-mining or names 妖股挖掘、连板挖掘、连板挖掘V2、连板龙头选股、连板龙头选股工作流、每日连板龙头; do not use as a generic stock router."
---

# 妖股挖掘

## 唯一边界

- 本技能用户可见名称为“妖股挖掘”，是“连板挖掘”“连板挖掘V2”“连板龙头选股”“连板龙头选股工作流”“每日连板龙头”的唯一合并入口。
- 以本目录原“连板挖掘”的数据采集、递进筛选、模板和 G1-G17 硬闸为底座；其他三项仅按 `references/capability_audit.md` 吸收通过审计的能力。
- 原“连板挖掘V2”的本地 TDX 最新交易日解析与失败阻断能力已正式并入；“连板挖掘V2”仅作为兼容触发词路由到本技能，不再存在独立 V2 技能或执行入口。
- 目标系统为本机 Codex。禁止依赖旧技能目录、旧包装器、OpenClaw 网关、股票总执行器或外部自动任务。
- NO_REDISCOVERY：先运行本技能入口和读取本技能参考文件；禁止重新猜测四个旧技能的目录或混用其脚本。

## 三种模式

1. `daily`：盘后每日快筛。采用 5 维 100 分模型，输出候选池、评分、文字报告和审计日志。
2. `research`：严格研究。使用本地 TDX K 线复算、8 因子 100 分模型、风险 A-E 组合规则和证据归档。
3. `full`：完整交付。沿用原连板挖掘的 LHBFP/QSGFX/QSYB/RDXZ 递进分析、精品/狙击分类、DOCX 模板和 G1-G17 硬闸。

三种模式共享以下硬约束：

- 当日执行必须显式 `--manual-confirm`；当日 15:05 前拒绝出最终结论。
- 未显式指定 `--date` 时，必须从本地 TDX `.day` 文件解析最新交易日；解析失败立即阻断，禁止回退到系统日期。
- 本地 ZTC 只证明“在本地涨停池”，不能凭空补成二连板、封单、资金或行业字段。
- 二连板严格模式必须同时验证 D、D-1 涨停阈值和 `HIGH == CLOSE`；数据缺失不得进入最终候选。
- 当日龙虎榜为空时可记录带日期的历史上下文，但不得冒充当日资金或进入当日资金加分。
- 主数据源失败且备用源未真实提供等价字段时，不生成正式 Top/Word；修复数据链后重跑。
- 市场事实、公告、新闻、研报和监管信息必须使用本回合的新鲜证据并记录日期、来源和 `evidence_id`。
- 事实、推断、风险、缺失项分开；结果只作研究支持，不承诺收益。

## 固定入口

```powershell
python D:\C盘转移\日志\codex\skills\a-share-limit-up-mining\scripts\codex_entry.py info
python D:\C盘转移\日志\codex\skills\a-share-limit-up-mining\scripts\codex_entry.py selftest
python D:\C盘转移\日志\codex\skills\a-share-limit-up-mining\scripts\codex_entry.py run -- --mode daily --date YYYYMMDD --manual-confirm
python D:\C盘转移\日志\codex\skills\a-share-limit-up-mining\scripts\codex_entry.py run -- --mode research --date YYYYMMDD --manual-confirm --k-line-mode connected
python D:\C盘转移\日志\codex\skills\a-share-limit-up-mining\scripts\codex_entry.py run -- --mode full --date YYYYMMDD --manual-confirm
```

- 只允许通过 `scripts/codex_entry.py` 对外执行；它按模式进入唯一对应执行器。
- 未指定模式时默认 `full`，保持原“连板挖掘”语义。
- Word 交付必须继续执行模板构建、Word 硬闸和模板差异闸；不得用手写报告替代。

## 执行顺序

1. 读取 `references/workflow.md`，锁定 13 步统一流程和所需模式。
2. 读取 `references/business_spec.md`，执行该模式的数据、评分、风险和交付约束。
3. 长期运行或复评时再读取 `references/long_run_checklist.md`；不得自动创建定时任务或新任务。
4. 运行入口；任何失败只说明该步骤失败，修复同一路径后继续，不把问题当交付。
5. 按模式读回 CSV/JSON/Markdown/DOCX 及对应审计证据；只有硬闸全部通过才能声称完成。

## 参考资料

- `references/workflow.md`：13 步统一主流程及模式路由。
- `references/business_spec.md`：数据、评分、风险、证据和 Word 硬闸规范。
- `references/full_workflow.md`：严格研究与完整交付的详细执行约束。
- `references/long_run_checklist.md`：样本外验证、影子测试和手动复评清单。
- `references/capability_audit.md`：四个原技能逐项吸收、修改、废弃的审计结论。

## 验证

- 结构验证：`python D:\C盘转移\日志\codex\skills\.system\skill-creator\scripts\quick_validate.py D:\C盘转移\日志\codex\skills\a-share-limit-up-mining`。
- 静态自检：`codex_entry.py selftest` 必须返回 `status=PASS`。
- 业务验证：`daily/research/full --help` 必须可达；实际运行须读回对应产物和审计日志。
- 完整模式：G1-G17、Word 渲染和模板差异闸缺一不可。
