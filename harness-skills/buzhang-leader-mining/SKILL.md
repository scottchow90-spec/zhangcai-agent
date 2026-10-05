---
name: buzhang-leader-mining
description: "A股短线补涨龙头实战挖掘技能：先确认当日短线主线，再从主线内部剔除空间高标，筛选低位、直接映射、资金承接和次日可执行的补涨龙1/龙2/龙3。用于补涨龙、补涨龙头、主线补涨、低位补涨、补涨挖掘、补涨梯队、每日补涨股等请求；不用于泛行业研究或长期投资。"
---

# 补涨龙头挖掘

## 目标

从已经被当日盘面验证的短线主线中，寻找尚未成为空间高标、但具备直接题材映射、梯队位置、成交承接和次日执行条件的补涨龙头。输出每条合格主线的补涨龙1/龙2/龙3；证据不足时输出缺位或 `BLOCKED`，禁止凑数。

这是研究支持流程，不保证收益、不保证预测准确率，不代替用户下单。

## 唯一入口

执行器为 `scripts/codex_entry.py`，禁止绕过入口临时调用旧脚本：

```powershell
python D:\C盘转移\日志\codex\skills\buzhang-leader-mining\scripts\codex_entry.py info
python D:\C盘转移\日志\codex\skills\buzhang-leader-mining\scripts\codex_entry.py selftest
python D:\C盘转移\日志\codex\skills\buzhang-leader-mining\scripts\codex_entry.py run -- --date YYYYMMDD --manual-confirm --research-evidence <candidate_research.json> --out <output_dir>
```

通达信排序指标入口（只交付排序指标，禁止生成或交付副图）：

```powershell
python D:\C盘转移\日志\codex\skills\buzhang-leader-mining\scripts\codex_entry.py run -- tdx-formula -- build --out <formula_output_dir>
python D:\C盘转移\日志\codex\skills\buzhang-leader-mining\scripts\codex_entry.py run -- tdx-formula -- install --manual-confirm --out <formula_output_dir>
python D:\C盘转移\日志\codex\skills\buzhang-leader-mining\scripts\codex_entry.py run -- tdx-formula -- sync-block --manual-confirm --result <buzhang_result.json> --out <formula_output_dir>
python D:\C盘转移\日志\codex\skills\buzhang-leader-mining\scripts\codex_entry.py run -- tdx-formula -- rank-block --manual-confirm --out <formula_output_dir>
```

`rank-block` 读取全部 `GN_` 概念板块及本地通达信日线，对板块涨幅中枢、5日持续性、上涨广度、涨停密度、量能和成交额活跃度做当日横截面百分位计算。七项等权平均后，只有通过当日动态热点资格闸门的板块才进入 `热点方向第1名/第2名/第3名`；不足三个就留空，不凑数。排序公式的 `热点板块码` 只输出上述动态名次 1/2/3，未通过热点闸门输出 0。

`tdx_sort_formula.txt` 是唯一数值排序源。禁止生成、构建、安装或交付副图公式，避免覆盖同名排序公式。`sync-block` 会把全部 `GN_` 概念成分写入 `主线龙头挖掘`，把当前主线匹配到的概念成分写入 `热点主线龙头挖掘`，并维护 `补涨龙1/2/3` 角色块。排序器按 `排序键` 降序，同一热点池前 3 行分别作为龙1、龙2、龙3；通达信原生编译和排序器可见性必须另行验收，未验收时状态保持 `OBSERVE`。

正式结果必须在收盘后运行，并显式带 `--manual-confirm`。未到15:05、缺少日期或缺少人工确认时，返回 `BLOCKED`。

## 固定执行链

### Level2 无自定义板块 TN6 固定验收入口

当用户明确要求 Level2、跨电脑导入或禁止依赖自定义板块时，只使用以下只读验收入口；不得运行旧版 `sync-block` / `rank-block`：

```powershell
python D:\C盘转移\日志\codex\skills\buzhang-leader-mining\scripts\codex_entry.py run -- tdx-formula -- level2-package --manifest <formula_sources_manifest.json> --canonical <canonical_v17.txt> --native-readback <isolated_native_import_report.json> --runtime-readback <live_level2_runtime_report.json> --package <package.tn6> --out <acceptance_dir>
```

该入口只读验证一个 TN6 内恰好包含 `BZSTL2`、`BZSECL2`、`补涨龙头排序` 三公式；公式不得含 `INBLOCK`。原补涨评分赋值链与 `CORE0*RISKN0/100` 风险调整排序不得修改。入口不操作活动通达信，验收结果固定写入 `level2_package_acceptance.json`；原生隔离导入与 Level2 活动运行态回读全部通过才允许 `PASS`。

1. 通过 `shortline-hotspot-mining` 的 `full` 模式生成市场层并交叉校验当日事件。
2. 通过 `a-share-limit-up-mining` 的 `daily` 模式复核涨停、连板、封板质量和资金字段。
3. 通过 `hotspot-leader` 的日期化入口读取当日涨停行业宽度，只作交叉校验，不把行业标签当作短线主线。
4. 通过本技能 `rank-block` 读取全部 `GN_` 概念板块和同一交易日本地日线，严格动态选出真实热点方向；禁用相对补位，不足三条就留空。
5. 在每条动态概念主线内部读取排序指标横截面候选池，剔除3板及以上空间高标、重复股票、错配题材和硬风险股，再按动态分项排序。
6. 把逐股研究证据送回同一固定入口；缺少题材、催化、资金、硬风险或次日条件的候选不得占据龙位。
7. 写出 `buzhang_result.json`、`buzhang_candidates.csv`、`audit.json` 和 `report.md`，并读回交易日、状态、热点方向、九只候选和研究闭环状态。

逐股研究证据必须使用 `BUZHANG-CANDIDATE-RESEARCH-V1` 结构回填到同一固定入口。动态排序中实际进入最低门槛的候选，都必须具备直接映射、当日触发、至少两条可追溯证据、六项硬风险检查、次日确认和失效条件；少一项就保持 `OBSERVE`。完成逐股核验后，合格股不足九只允许龙位缺位，不得把上游的待研究标记直接当成交付结论。

TDX/本地K线优先；AKShare或公开来源只能补齐字段和交叉验证，不能覆盖本地交易日期。详细评分和输出字段见 [references/spec.md](references/spec.md)。

## 补涨资格硬闸门

主线必须先满足：

- 当日市场层产物存在且交易日一致；
- 主线至少有3只有效成分股、至少2只强响应股；
- 至少一个1/2板或趋势核心和至少两个助攻；
- 题材名称能落到具体事件、产品或产业链节点，不能只写“大科技”“新能源”等泛行业；
- 关键催化有时间、来源和 `evidence_id`；
- 无ST、退市、停牌、重大监管、重大减持、严重财务或流动性硬风险。

候选补涨股必须：

- 与已确认主线存在直接映射；
- 通常处于首板、二板或尚未充分加速的早期位置；
- 不是该方向的最高空间龙；
- 有可复核的成交额、换手、封板时间、炸板次数或趋势突破字段；
- 能给出次日确认条件和失效条件。

## 补涨评分（100分）

- 主线同步强度：25分；
- 题材直接映射：20分；
- 梯队/首封质量：20分；
- 成交与资金承接：20分；
- 相对位置和补涨空间：10分；
- 风险与可执行性：5分。

统一最低门槛为65分；硬风险命中即剔除。通过同一门槛的合格股按当日动态总分从高到低依次命名补涨龙1、补涨龙2、补涨龙3；不足三只的剩余龙位必须缺位，禁止用不同门槛制造“龙1空缺、唯一合格股却叫龙3”的错位。

## 角色定义

- 补涨龙1：主线内最强低位承接者，直接映射、封板/突破质量和资金承接综合第一。
- 补涨龙2：次强换手承接者，位置低于龙1，具备独立成交和次日接力条件。
- 补涨龙3：扩散弹性者，仍未过热，但必须有直接映射和明确触发线。

## 输出要求

每条主线固定输出：

`主线 | 补涨龙1 | 补涨龙2 | 补涨龙3 | 评分 | 题材映射 | 当日证据 | 次日确认 | 失效条件 | 风险 | evidence_id`

不得把高标本身改名为补涨龙；不得把只有一只股票的题材写成主线；不得用旧日期数据补齐当日字段。少于3只合格候选时明确写“龙位缺位”。

## 状态与验收

- `PASS`：三条执行链均成功，交易日一致，关键JSON/CSV可读回，至少有一条主线通过补涨硬闸门。
- `OBSERVE`：市场层成功，但题材映射、资金或风险字段尚未闭环；不得写成正式补涨龙。
- `BLOCKED`：关键来源失败、日期冲突、产物缺失、硬风险未复核或运行时间不合规。

最终回复必须有独立的“证据”段，说明实际产物路径、交易日、状态、候选数量、数据缺口和未验证层。任何缺口不得包装成完成。
