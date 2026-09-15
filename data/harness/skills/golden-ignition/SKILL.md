---
name: golden-ignition
description: 通用黄金点火技术分析技能。用于股票、A股、可转债正股映射、黄金点火、黄金点火AI、点火信号、真实K线回测、短线启动、EMA3上穿EMA21及点火候选筛选；可独立调用，也可作为其他股票或可转债工作流中的一个通用信号模块，不得误解为国际黄金期货专属技能。
---

# 黄金点火

## 业务边界

- 将黄金点火作为通用证券技术信号模块，不限定某一行业、品种或策略。
- 股票代码直接分析；可转债代码先由本机通达信 `speckzzdata.txt` 映射到正股，再分析正股点火。
- 核心定义固定为 `CROSS(EMA(CLOSE,3),EMA(CLOSE,21))`，并读取大牛线4.0运行态 `OUTPUT59-61` 交叉验证。
- 只使用本机 Codex 与 `C:\new_tdx_mock` 数据，不访问OpenClaw运行时，不把国际黄金、白银期货涨跌当作黄金点火信号。
- 信号是技术条件，不保证收益；与选股或可转债工作流组合时仍需独立通过估值、流动性、强赎和风险门。
- 已安装的“黄金点火AI”按通达信条件选股公式调用，历史输出固定读取 `XG` 日期记录；不得把它按指标公式调用，也不得用同名EMA规则替代其真实信号。
- “黄金点火AI”回测只优化交易执行参数，并以验证集胜率和盈亏比同时超过基线作为双目标硬闸；不改写通达信原公式。

## 固定入口

- 信息：`python D:\C盘转移\日志\codex\skills\golden-ignition\scripts\codex_entry.py info`
- 自检：`python D:\C盘转移\日志\codex\skills\golden-ignition\scripts\codex_entry.py selftest`
- 股票：`python D:\C盘转移\日志\codex\skills\golden-ignition\scripts\codex_entry.py run -- 600577.SH --lookback 5`
- 可转债：`python D:\C盘转移\日志\codex\skills\golden-ignition\scripts\codex_entry.py run -- 110074.SH --lookback 5`
- 黄金点火AI历史回测：`python D:\C盘转移\日志\codex\skills\golden-ignition\scripts\codex_entry.py run -- backtest --formula 黄金点火AI --start-date 20210101 --end-date 20260814 --max-symbols 500`

必须通过 `codex_entry.py` 执行，不得直接运行内部业务脚本。读取结果JSON，核对输入标的、实际分析正股、最新交易日、信号状态和数据哈希后，才可把结果纳入上层分析。

## 工作流

1. 识别输入为股票或可转债。
2. 对可转债读取本机转债映射并锁定正股。
3. 读取正股本地日线，计算EMA3、EMA21及近期金叉。
4. 调用通达信大牛线4.0运行态，读取 `OUTPUT59-61`。
5. 输出 `PASS + HIT/NO_SIGNAL`，不得把“无信号”写成执行失败。
6. 日期不一致、映射缺失或数据不足时明确标注或 `BLOCKED`。
7. “黄金点火AI”回测使用本机真实日K线、条件选股字段 `XG`、下一交易日开盘成交和训练/验证/测试隔离；没有候选同时改善验证胜率与盈亏比时必须回退基线。

## 参考

- `references/business_spec.md`
- `references/workflow.md`

## 验证

- 结构：`python D:\C盘转移\日志\codex\skills\.system\skill-creator\scripts\quick_validate.py D:\C盘转移\日志\codex\skills\golden-ignition`
- 入口：运行 `codex_entry.py selftest`，必须为 `CLEAN_PASS`。
- 同类前向测试：至少各跑一只股票和一只可转债，股票保持原代码，可转债必须正确映射正股。
