# 支撑压力分析系统唯一工作流

CODEX_LOCAL_ENTRY

NO_REDISCOVERY: true

NO_CROSS_JUMP: true

LOCKED_ENTRY: scripts/codex_entry.py

LOCKED_EXECUTOR: scripts/scientific_engine.py

LOCKED_ACCEPTANCE: run_summary.json + target scientific report readback

## 唯一链路

1. 路由：只在明确点名本技能时进入，不设通用研究 fallback。
2. 入口：外部只允许 `scripts/codex_entry.py info|selftest|run`。
3. 执行：`run` 只能转发 `scripts/scientific_engine.py`；其他脚本均为历史资产或内部兼容资产，不是入口。
4. 数据：科学执行器通过本机 `tdx-local-hub` 获取真实日线文件中的全部记录；`--limit` 与 `--validation-limit` 必须为 `0`。报告必须绑定源文件大小、SHA-256、文件记录容量、可用记录数和实际读取数，任一数量不一致立即失败关闭。
5. 方法：艾略特子系统扫描全部输入日K并遍历全部右侧确认交替枢轴窗口，禁止最近固定枢轴截断；五套形式化理论子系统与基础因果价位共同进入候选聚类，五法共享一个证据家族，之后统一执行非重叠走前检验、距离匹配安慰剂和冻结横截面校准闸。
6. 统一结论：普通分析必须用全部五套子系统生成 `UNIFIED_FIVE_THEORY_CONCLUSION_V1`，固定输出“波浪理论、缠论、斐波那契、江恩理论、威科夫、综合结论”六段；五法缺一、未启用或状态非 `PASS` 时失败关闭。
7. 产物：每个目标一个 `*.scientific_support_pressure.json`，每轮一个 `run_summary.json`；统一结论写入后重新计算目标报告大小与 SHA-256，摘要落盘后重新绑定摘要大小与 SHA-256。
8. 验收：本轮目标、目标代码、状态、执行器版本、数据质量、统一结论状态、产物路径、当前哈希与持久化回读必须一致。
9. 五法验收：艾略特、缠论、斐波那契、江恩、威科夫必须在报告中逐项存在、状态通过、主链启用，并提供候选价位和限制说明。
10. 降级：没有建立经验优势时只允许“未验证候选区间”，不得转写为预测或交易信号。
11. 预测优势专用验收：从同一根入口传入 `--validate-five-theories`；按板块和固定 SHA-256 顺序冻结开发/留出标的，五法各自走非重叠样本外窗口并与同方向、相近距离安慰剂配对。输出 `FIVE_THEORY_REAL_KLINE_VALIDATION_V1` 与文件哈希收据。普通测试、计划完成、单标的报告、旧参数校准均不是替代证据。
12. 放行条件：只有五法开发集和冻结留出集均达到预注册阈值，且收据为 `all_subsystems_pass=true`、`predictive_claim_allowed=true`，才允许写成已建立预测优势；否则固定为未建立可靠优势并继续输出 `UNVALIDATED_CANDIDATE_ZONES_ONLY`。

## 固定最终结论格式

1. 波浪理论：已确认的浪位与趋势；证据不足时明确无法可靠编号。
2. 缠论：中枢结构、最后一笔和结构趋势。
3. 斐波那契：最近支撑与最近压力位置。
4. 江恩理论：时间窗口、周期长度或距下一窗口交易日数，且不宣称窗口必然转折。
5. 威科夫：运行阶段、区间位置和最近确认事件。
6. 综合结论：结构偏向、趋势确认状态、关键区间、触发线、失效线和预测边界。

任一段缺失、只输出支撑压力区或没有明确综合结论，均不得放行。

## 唯一命令

```powershell
python D:\C盘转移\日志\codex\skills\support-pressure-analysis-system\scripts\codex_entry.py run -- --mode pressure --symbols 600519.SH --out-dir <目录> --run-id <本轮ID>

python D:\C盘转移\日志\codex\skills\support-pressure-analysis-system\scripts\codex_entry.py run -- --validate-five-theories --validation-symbols-per-stratum 4 --validation-limit 0 --bootstrap-iterations 2000
```

下游技能必须从 `run_summary.json` 读取 artifact，再读取目标科学报告；禁止猜测旧产物名、直接调用内部脚本或临场切换执行器。
