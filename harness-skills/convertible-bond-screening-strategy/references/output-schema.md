# 持久化输出

技能根目录下的 `run/` 只保存当前固定入口产物：

- `latest_result.json`：`TDX-CONVERTIBLE-BOND-WEIGHTED-SCAN-V5`候选全集的资格评分池、硬排除池、Top 10、公告与行情来源哈希、固定12位小数业务规范排序值和风险边界。
- `latest_formula_evidence.json`：本次TQ公式原始值的紧凑证据；由当前 `run_id`、大小和SHA-256绑定到扫描结果。
- `latest_day_input_manifest.json`：`CONVERTIBLE-BOND-DAY-INPUT-MANIFEST-2`不可变日线快照清单；固定绑定实际参与评分及行业/概念热度计算的最近260条记录，记录双次稳定采集、文件大小、`mtime_ns`、尾部偏移、SHA-256、别名路由及缺失状态，主验真与状态回读均重新校验当前来源。
- `latest_verification.json`：重新读取原始通达信日线和债券条款，独立重算10项分数、行业/概念热度、总分、排序、风险、公式值和来源哈希。
- `latest_independent_heat_verification.json`：由固定入口单独启动的热度复验进程，绑定当前 `latest_result.json` 与日线清单的路径、大小和 SHA-256；对合格池与硬排除池全部已评估记录重算行业、概念、C9和总分，并仅对合格池复核排序。
- `latest_summary.json`：适合展示的Top 10及分项分数。
- `top1_fixed_skill_validation.json`：动态Top1经六个本地股票技能固定入口交叉验收的结果；固定集合为`stock-hard-gate`、`tdx-local-hub`、`golden-ignition`、`feilong-strategy`、`youzi-capital-monitoring`、`big-bull-analysis-scoring-system`，不含`stock-unified`。
- `selftest.json`：仅由生产 `run` 生成并绑定同代的`CONVERTIBLE-BOND-SCREENING-SELFTEST-2`结构、六依赖、后缀、价格倍率及V5硬排除契约回归自检。
- `selftest_standalone.json`：单独执行 `selftest` 的V2读回，不参与也不覆盖生产代际。
- `run_state.json`：当前运行的 `RUNNING`、`PASS` 或 `FAIL` 状态；启动即使旧回读失效。
- `latest_early_redemption_announcements.json`：`CNINFO-CONVERTIBLE-BOND-EARLY-REDEMPTION-SNAPSHOT-1`官方公告逐债分页快照；绑定当前 `run_id`、截止日、覆盖状态、记录哈希及公告原文链接。
- `skill_status.json`：`CONVERTIBLE-BOND-SCREENING-SKILL-STATUS-3`本次业务状态及当前生产产物的SHA-256和大小；启动和失败时同步失效旧PASS。
- `status_readback.json`：`CONVERTIBLE-BOND-SCREENING-STATUS-READBACK-3`重新读取状态、当前文件、公告快照、来源哈希和同代 `run_id` 后生成的最终验收。

当前 `speckzzdata.txt` 中公开沪深转债全部进入生产评估，固定要求 `universe_count == evaluated_count == eligible_count + hard_excluded_count`、`ranked_count == eligible_count == len(all_results)`，且`all_results`与`hard_excluded_results`无交叉、并集等于候选全集。硬排除记录保留全部命中原因，不参与Top 10。`missing_local_symbols`、`missing_local_details`和`unavailable_local_retained_count`描述的是评估记录的重叠子集，不能与池计数相加。TNF只作独立核验，TNF缺失不得改变候选数量。所有JSON均使用原子替换，避免半写文件。

所有生产JSON中的有限浮点业务值在排序和持久化前统一按固定12位小数、`ROUND_HALF_EVEN`规范化；NaN和Infinity失败关闭。不同运行面仅可排除路径、时间、性能和artifact绑定等非业务元数据，候选全集、排名、评分、风险与公告必须按规范化JSON做精确结构相等比较。

生产结果同时记录`source_binding_mode=stable_sha256_pre_and_post_run`、`day_input_binding_mode=immutable_tail_snapshot_pre_and_post`和`scan_attempt`。固定入口只在扫描器或主验真器输出精确结构化`TDX_DAY_UPDATE_RACE`事件，并且事件的schema、脚本、`run_id`和`attempt`全部匹配当前调用时，才重跑完整“扫描 -> 主验真”链路；最多3次，间隔1秒和3秒。其他失败立即阻断，任何失败尝试都不得保留可交付PASS状态。

V5评分证据中，c4只读取正股本地日线产生的`ignition_local_cross_dates_10`；`bigbull_formula_diagnostic_hits`只是大牛线诊断字段，不得贡献c4分数。c7/c8的SCR窗口必须逐项等于截止日前最近6个基准交易日，并只用该窗口首日与末日计算缩小百分点；硬排除另用末两日SCR90计算单日变化。公告快照必须以当前路径、大小、SHA-256、`run_id`和截止日绑定，并声明逐债完整；未知公告状态不得通过。

核心状态：

- `PASS`：计算链、适用公式字段覆盖与新鲜度、评分日线及热度成员日线清单、原始数据独立复验、同代 `run_id`、动态Top1技能验收及当前哈希回读均通过。
- `PARTIAL`：产生了评分数据，但TQ公式覆盖不完整；不可发布为当前完整榜单。
- `BLOCKED` / `FAIL`：没有可验收结果或结果不一致。

`execution_policy`固定包含：

- `mode=post_close_manual_decision_support`
- `automatic_order=false`
- `execution_eligible=(Top10中GREEN数量>0)`
- `strong_redemption_announcements_verified=true`

即使 `status=PASS`，也只表示计算和证据链一致；不表示任一转债适合买入。

## 个人 A 股知识库确认层

`personal_kb_confirmation_model`固定为`CB-PERSONAL-A-SHARE-KB-CONFIRMATION-1`。该确认层只采用个人 A 股投资知识数据库中已验收的类别级方法原则，不提供人物背书，且生产运行不动态依赖 SQLite。

- 确认质量不改变10项分项得分、`score_components`或`score_total_raw`。
- 确认质量只在`score_total_raw`完全相同时参与排序；低原始分不能凭确认质量超过高原始分。
- 完整排序依次为：`score_total_raw`降序、确认质量降序、大牛线红色优先、转债代码升序。
- `risk_level=RED`时确认质量最高为59，确认等级不能为`HIGH`。
- `automatic_order=false`保持不变，确认质量不构成自动交易指令。
- 主验证器和独立验证器分别从原始结果字段独立复算确认对象，不信任扫描器写入值。
