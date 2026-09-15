# 黄金点火固定工作流

`CODEX_LOCAL_ENTRY`

- 唯一外部入口：`scripts/codex_entry.py`
- 唯一业务实现：`scripts/entry_golden_ignition.py`
- 数据源：`C:\new_tdx_mock`，经 `tdx-local-hub` 读取。
- 通用范围：A股；输入可转债时自动映射正股。
- 核心公式：`CROSS(EMA(CLOSE,3),EMA(CLOSE,21))`。
- 运行态交叉验证：大牛线4.0 `OUTPUT59`、`OUTPUT60`、`OUTPUT61`。

## 顺序

1. `codex_entry.py selftest`。
2. `codex_entry.py run -- <股票或可转债代码> --lookback <1..30>`。
3. 读取命令返回的 `result_path`。
4. 核对 `input_symbol`、`analysis_symbol`、`latest_trading_date`、`signal_status`。
5. 上层工作流只消费当前结果文件及其哈希；禁止消费旧默认报告。

## 黄金点火AI回测顺序

1. 通过 `codex_entry.py run -- probe-ai --formula 黄金点火AI` 确认它是条件选股公式，并核验字段 `XG` 的真实历史日期输出。
2. 通过 `codex_entry.py run -- backtest --formula 黄金点火AI ...` 读取本机通达信真实日K线；不得直接运行内部业务脚本。
3. 固定使用训练、验证、测试时间隔离。训练集只负责短名单，验证集执行胜率与盈亏比双目标硬闸，测试集定参后只读一次。
4. 双目标候选必须在验证集至少20笔交易，并同时超过基线胜率和基线盈亏比；否则回退基线。
5. 报告列示信号集、K线清单和公式库哈希，并列出被拒绝的单目标参数及原因。
6. 仅给出纸面执行层建议，不改写通达信原公式。

## 判定

- `status=PASS, signal_status=HIT`：技能执行成功且近期点火。
- `status=PASS, signal_status=NO_SIGNAL`：技能执行成功但近期无点火。
- `status=BLOCKED`：映射、数据或公式运行失败，不得伪造信号。

国际黄金、白银期货行情不属于本技能输入或数据源。
