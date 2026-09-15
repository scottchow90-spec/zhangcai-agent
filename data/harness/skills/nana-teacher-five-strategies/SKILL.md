---
name: nana-teacher-five-strategies
description: "娜娜老师5策略的本机Codex固定执行技能，覆盖元宝藏金、地极破晓、游龙吸水、负阴抱阳、黄金双响五套通达信选股策略。Use when the user explicitly says 娜娜老师5策略、娜娜5策略、运行娜娜五策略、导出娜娜策略包，或要求按这五套策略扫描、复跑、查看工作流与独立证据；不得作为通用股票路由器。"
---

# 娜娜老师5策略

## 固定边界

- 只处理元宝藏金、地极破晓、游龙吸水、负阴抱阳、黄金双响五套策略。
- 目标系统为本机 Codex 与 `C:\new_tdx_mock` 本地行情；禁止切换到 OpenClaw 或其他股票技能代跑。
- 所有执行必须进入 `scripts/codex_entry.py`，不得只读取公式后临场重写扫描逻辑。
- 把本地日线扫描结果、通达信公式管理器编译结果和交易建议分开；扫描命中不等于买入建议。
- GUI 编译、导入或通达信内部批量选股只有在取得对应界面回执后才能声称通过；本技能的本地扫描不能替代该回执。

## 固定入口

```powershell
python D:\C盘转移\日志\codex\skills\nana-teacher-five-strategies\scripts\codex_entry.py info
python D:\C盘转移\日志\codex\skills\nana-teacher-five-strategies\scripts\codex_entry.py selftest
python D:\C盘转移\日志\codex\skills\nana-teacher-five-strategies\scripts\codex_entry.py run -- run --output-dir <输出目录>
python D:\C盘转移\日志\codex\skills\nana-teacher-five-strategies\scripts\codex_entry.py run -- export --output-dir <交付目录>
python D:\C盘转移\日志\codex\skills\nana-teacher-five-strategies\scripts\codex_entry.py verify --receipt <统一门面回执.json>
```

`run` 默认从 `C:\new_tdx_mock\vipdoc` 推断覆盖充分的最新交易日；本地日线落后于市场最新交易日时，固定入口自动抓取并校验当天行情后拼接。也可显式传入 `--target-date YYYYMMDD --quote-json <文件>`；外部行情若成交额/成交量量纲不一致会被机械阻断。输出固定包含扫描 JSON、当日候选 CSV 和哈希回执 JSON。原公式命中后按策略近80日表现、趋势结构、流动性和失效位距离计算技术质量分；60分为质量门槛、75分为优先复核，原始命中仍完整保留，不以放宽公式凑票。

`export` 输出 5 个公式、5 个工作流、5 个独立证据、总索引和导出回执；目标目录非空时必须显式传入 `--force`。

## 执行流程

1. 运行 `selftest`，确认五套资产、当前哈希、脚本编译和 `C:\new_tdx_mock` 数据目录全部通过。
2. 读取 `references/strategy_registry.json` 确认五套映射；只按用户点名的策略缩小解释范围，扫描器仍保持同一固定实现。
3. 运行 `run`；检查退出码、扫描结果 `status`、覆盖股票数、五套历史信号数及输出回执哈希。
4. 按对应 `assets/workflows/` 文件完成公告、板块、流动性、失效位复核；明确区分事实、推断、风险和未验证项。
5. 需要交付资产时运行 `export`，不得手工拼凑成不完整的四套或漏掉独立证据。

## 资源路由

- 策略映射、源材料哈希和公式关键标记：`references/strategy_registry.json`
- 公式：`assets/formulas/`
- 工作流：`assets/workflows/`
- 独立证据快照：`assets/evidence/`
- 固定扫描器：`scripts/nana_five_strategy_scanner.py`

只有用户点名具体策略或需要解释公式时才读取对应工作流、公式和证据文件；不要一次性加载全部大文件。

## 验收

- 结构验证：`python D:\C盘转移\日志\codex\skills\.system\skill-creator\scripts\quick_validate.py D:\C盘转移\日志\codex\skills\nana-teacher-five-strategies`
- 入口验证：`codex_entry.py selftest`
- 业务验证：至少实跑一次 `run` 并读取输出回执；只运行 `info` 或 `selftest` 不能证明选股扫描成功。
- 交付验证：运行 `export` 后读取导出回执，必须为 5 个公式、5 个工作流、5 个证据且所有哈希匹配。
