# 可转债筛选策略唯一工作流

LOCKED_ENTRY: scripts/codex_entry.py

LOCKED_EXECUTOR: scripts/run_convertible_bond_screening.py

LOCKED_ACCEPTANCE: run/skill_status.json + run/status_readback.json + independent verification + execution receipt

1. 外部只调用 `scripts/codex_entry.py info|selftest|run|status|deliver`。其中 `selftest`、`status` 与 `deliver` 均由本技能特殊门面映射到公共股票运行时，在业务租约、受保护进程守卫、哈希合同和执行回执内调用内部固定命令；不得直接执行 `legacy_codex_entry.py`。日常固定入口只有六个：`stock-hard-gate`、`tdx-local-hub`、`golden-ignition`、`feilong-strategy`、`youzi-capital-monitoring`、`big-bull-analysis-scoring-system`；`stock-unified`不参与日常依赖或Top1验收。
2. `selftest`从本机上证基准日线取得最新交易日，将该日作为债券条款截止日，并验证SCR精确六交易日窗口、c4独立计分、缺失日线保留和日线清单布局。
3. `run`以当前 `speckzzdata.txt` 中公开沪深可转债为候选全集，先生成并锁定同运行、同截止日、逐债完整的官方提前赎回公告快照，再执行六类硬排除；只有资格池参与十项标准、总权重100分的评分。TNF只作独立名称与存在性核验；TNF或一般软评分日线缺失不得删除候选。
4. 每只候选都必须且只能进入资格排名池或硬排除池之一。固定不变量为 `universe_count == evaluated_count == eligible_count + hard_excluded_count`、`ranked_count == eligible_count == len(all_results)`；`missing_local`是已评候选的重叠子集，不是额外候选池。
5. c4只由正股本地日线计算的EMA3向上穿越EMA21触发；大牛线公式命中只作诊断证据，并仅在总分完全相同时以红色趋势优先。c7/c8只接受截至截止日、严格按基准日历排列的最近6个交易日SCR值，并比较第1日和第6日；缺日、非交易日、重复、逆序、过期或非有限值均记0分并披露。
6. 股票映射、价格、剩余规模、溢价率、正股技术条件和公式证据必须绑定同一非空 `run_id`及当前`attempt`，禁止拼接旧默认结果。计算使用每个日线解析路径最多260条记录的不可变尾部快照；快照双遍稳定捕获，发布前逐文件复核。
7. 结果必须持久化，并由独立复算验证六类硬排除、双池无交叉全覆盖、总权重、资格池排名、Top10、公告快照绑定、动态Top1六技能状态及输入哈希。仅精确绑定当前脚本、`run_id`和`attempt`的`TDX_DAY_UPDATE_RACE`允许整链最多重跑3次；其他错误立即失败。
8. `status`回读当前结果和收据；任一目标、日期、覆盖率、分区、快照当前性或哈希不一致即 `BLOCKED`。
