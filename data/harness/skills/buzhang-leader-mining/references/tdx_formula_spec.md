# 通达信排序指标规格

## Level2 无自定义板块版本

跨电脑交付采用一个 TN6、三个同类技术指标公式：`BZSTL2`、`BZSECL2`、`补涨龙头排序`。该版本只读取通达信 Level2 系统概念集合，并在系统概念内做板块与个股排序；禁止读取或同步任何自定义板块，公式源内不得出现 `INBLOCK`。

`BZSTL2` 保留补涨个股评分的原始赋值链，核心分仍为：

```text
CORE0:=(MOMN0+MAPN0+LADN0+CAPN0+POSN0)/5
```

风险调整排序仍为 `CORE0*RISKN0/100`。Level2 版本只把原自定义板块热点闸门替换为系统概念全局前三与概念内部前三，不得修改上述评分或风险调整排序表达式。

固定只读验收入口：

```powershell
python D:\C盘转移\日志\codex\skills\buzhang-leader-mining\scripts\codex_entry.py run -- tdx-formula -- level2-package --manifest <formula_sources_manifest.json> --canonical <canonical_v17.txt> --native-readback <isolated_native_import_report.json> --runtime-readback <live_level2_runtime_report.json> --package <package.tn6> --out <acceptance_dir>
```

该入口不生成 TN6、不导入或修改活动通达信，只读取并绑定输入。它独立复核：

- 公式名称恰好为三个且各一个；
- 所有公式均不含 `INBLOCK`；
- 原评分赋值链逐项不变，风险调整排序表达式不变；
- 隔离原生导入后恰好增加三个 kind-0 公式、源回读精确、非法公式被拒绝；
- Level2 活动运行态识别三个公式，且至少存在非零热点板块码与非零排序键。

缺少原生或运行态回读时只返回 `OBSERVE`；任何提供的回读不满足契约返回 `BLOCKED`；所有层均通过才返回 `PASS`。业务结果固定持久化为 `level2_package_acceptance.json`。

## 输出列

- `热点闸门`：是否同时进入系统概念热点前三和概念内部补涨前三。
- `热点强度`：对应系统概念板块强度。
- `补涨总分`：原 100 分制补涨评分。
- `龙位编码`：1/2/3 对应概念内部排序的龙1/龙2/龙3，0 为未入选。
- `龙1候选`、`龙2候选`、`龙3候选`：对应角色的排序值。
- `热点板块码`：1/2/3 为全局热点方向顺序，0 为未进入前三。
- `排序键`：原风险调整排序值经 Level2 热点和角色闸门后的最终排序列。

## 旧版边界

`build`、`install`、`sync-block`、`rank-block` 是旧的本机自定义板块路线，不得用于“Level2 无自定义板块、跨电脑直接导入”交付。
