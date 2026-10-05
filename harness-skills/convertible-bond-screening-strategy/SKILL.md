---
name: convertible-bond-screening-strategy
description: 本机Codex“可转债筛选策略”固定执行技能。用于用户提出“可转债筛选策略”“运行可转债筛选”“转债评分Top 10”“用通达信筛选可转债”等请求；读取C:\new_tdx_mock最新完整收盘数据，先执行六类风险硬排除，再按10项软条件加权100分扫描其余公开沪深可转债，输出评分Top 10、大牛线同分偏好、风险分层和固定技能验收。仅作收盘后决策支持，不自动下单，不保证收益。
---

# 可转债筛选策略

## 固定边界

- 目标系统固定为本机 Codex 与 `C:\new_tdx_mock`；不得切换到 OpenClaw、网页选股器或历史硬条件筛选器。
- 生产运行只使用本机最新完整交易日。不得用当前成分池回填历史日期并声称无前视偏差。
- 10项均为软评分，总权重100；缺失项记0分且不重新归一化。六类风险硬排除先于评分排名执行，不占评分权重。完整规则见 [references/scoring-model.md](references/scoring-model.md)。
- 个人A股知识库确认质量不计入10项原始分，仅用于原始总分完全相同时的第一层排序；之后优先大牛线红色，最后按转债代码。确认层风险标签独立展示，`automatic_order`仍为`false`。
- 黄金点火是通用证券信号，保留可转债到正股映射，不得排除或改成黄金期货专属逻辑。
- `automatic_order` 永远为 `false`。`execution_eligible=true` 仅表示存在GREEN候选可进入人工复核，不是买入指令。
- 提前赎回必须由本次运行、同一截止日的官方公告快照逐债覆盖；已公告提前赎回者排除，公告状态未知或快照不完整者也排除。公告快照或来源核验失败时整次运行失败关闭，不得把未知当成未赎回。

## 固定入口

```powershell
python D:\C盘转移\日志\codex\skills\convertible-bond-screening-strategy\scripts\codex_entry.py info
python D:\C盘转移\日志\codex\skills\convertible-bond-screening-strategy\scripts\codex_entry.py selftest
python D:\C盘转移\日志\codex\skills\convertible-bond-screening-strategy\scripts\codex_entry.py run
python D:\C盘转移\日志\codex\skills\convertible-bond-screening-strategy\scripts\codex_entry.py status
python D:\C盘转移\日志\codex\skills\convertible-bond-screening-strategy\scripts\codex_entry.py deliver
```

## 固定评分与最终交付契约

最终回答、Word、报告和表格只能逐字段使用 `deliver` 命令返回且已验证通过的 JSON。

- 禁止重新解释、增删或改序评分因子；禁止手写、改写或临时调整权重。
- 禁止从 `run/latest_result.json` 取数；禁止混用不同 `run_id` 或不同 `market_attempt` 的产物。
- `deliver` 返回非零时只能报告 `BLOCKED`，不得人工生成、补写、重排或修改 Top10。
- 大牛线只能使用 `deliver` 中已验证的同分偏好字段，不得计入评分。
- 本契约只约束可转债筛选策略的评分和最终交付，不是全局普通任务门禁。

必须通过 `codex_entry.py` 执行。不得直接调用内部扫描器后跳过独立复验、Top1固定技能验收或状态回读。

## 执行顺序

1. 运行 `selftest`，检查脚本编译、10项权重、通达信债券后缀与价格倍率、TQ依赖、原子替换、互斥锁，以及六个日常固定技能入口。自检使用本机上证基准日线的最新交易日作为条款截止日，并回归SCR精确六交易日窗口、黄金点火独立计分、缺失日线保留、不可变日线快照和精确竞态重试。独立自检写入 `selftest_standalone.json`，不会覆盖生产代际的 `selftest.json`。
2. 运行 `run`。入口先对基准、全部转债、全部正股及行业/概念成员的日线尾部做双遍稳定捕获，并采集同一截止日的官方提前赎回公告快照；计算只读取这些不可变输入。随后依次执行全市场扫描、六类硬排除、原始通达信行情与债券条款独立重算、行业/概念热度独立重建、Top 10摘要、动态Top1固定技能验收、状态持久化和哈希回读。历史不足或未同步标的仍进入已评资格池，对应软评分记0且强制RED；命中硬排除的标的进入独立排除池，不参与Top 10。
3. 从 `run/latest_summary.json` 读取Top 10，从 `run/skill_status.json` 读取业务状态，从 `run/status_readback.json` 读取当前哈希验收。
4. 仅当扫描、独立复验、动态Top1技能验收和状态回读均为 `PASS` 时，才可交付当前榜单。
5. 展示原始Top 10及RED/YELLOW/GREEN风险；无GREEN时明确说明仅观察，不得自动下单。

## 固定依赖

- 前置：`stock-hard-gate`。
- 数据：`tdx-local-hub`。
- 信号：`golden-ignition`、`feilong-strategy`、`youzi-capital-monitoring`、`big-bull-analysis-scoring-system`。
- 日常固定入口合计六个：上述一个前置、一个数据和四个信号技能；`stock-unified`不是本策略的日常依赖或Top1验收项。
- 扫描器按320只一批读取TQ公式值并覆盖具备相应历史的标的；飞龙和大牛线固定使用经全市场等价验证的600根计算窗口，SCR必须精确对应截至截止日的最近6个基准交易日。不满足该精确窗口的转债仍进入排名，但SCR分项记0并RED提示。固定技能业务入口对每次运行的动态Top1做同标的、同交易日交叉验收，不得写死历史榜首。
- `speckzzdata.txt`是当前沪深可转债候选全集来源；TNF仅作独立名称/存在性核验。TNF缺失或本地债券/正股日线缺失不允许静默缩池，标的仍进入排名，缺失项记0并强制RED。
- 六类硬排除固定为：名称去空格后以ASCII `Z`开头；当日涨幅不低于10%且今日成交量/此前5个交易日平均成交量大于4；当日90%筹码集中度较前一交易日扩大或该日变动无法核实；近5日累计换手率严格大于1000%；转债收盘价严格大于350元；已正式公告提前赎回或公告状态无法核实。
- TQ生产扫描要求 `TdxW.exe` 已运行；连接必须以本技能扫描器的唯一 `.py` 路径作为策略身份，不得把 `C:\new_tdx_mock` 目录作为初始化路径。扫描结果保留初始化及四组公式的独立耗时。

## 输出与文件交付

- JSON字段、状态和风险含义见 [references/output-schema.md](references/output-schema.md)。
- 结果属于量化决策支持，不构成收益保证或个性化投资建议。
- 若用户要求DOCX、PDF、PPTX、XLSX、XLSM或XLS，必须另行调用 `$stock-delivery-risk-gate` 与对应文档技能；本技能不能替代股票文件门禁。

## 修复纪律

- 发现安全可修复的数据、公式、解析或持久化问题时，在本技能同一执行栈内修复，再重跑 `selftest`、`run`、`status`。
- `--skip-tq`仅可用于内部诊断，不能产生可交付PASS结果。
- 所有生产JSON必须原子替换；`run`与`status`共用生产互斥锁。外部`selftest`使用独立互斥锁且只写`selftest_standalone.json`，不触碰生产代际；崩溃后锁均由操作系统释放。
- 外部固定技能均在受控子进程树中运行；超时必须清理整个后代树并写入 `failed_stage`，不得遗留TQ或子技能进程。
- 单次生产运行必须以同一个非空 `run_id` 绑定扫描、公式原始证据、独立复算、摘要、自检、Top1交叉验收和状态；所有有限浮点业务值先按固定12位小数、`ROUND_HALF_EVEN`规范化，排名和持久化均使用该业务规范值，展示层再按既有位数格式化。
- 基准日期不同步、应有公式字段缺失或过期、来源哈希失配、跨代产物混用或固定技能目标错配均失败关闭。单只转债日线不同步不静默缩池，而是缺失项0分、风险RED并保留在排名中。
- `run_state.json` 与 `status_readback.json` 是当前状态权威；运行开始或失败时 `skill_status.json` 同步写为 `RUNNING` 或 `FAIL`，旧PASS不得继续作为当前状态。
- 子执行器失败时，`run_state.json.reason` 必须保留有界的真实子进程诊断，不能只记录退出码。
- 日线快照固定保留每个解析路径最多260条原始记录，捕获前后必须稳定，发布前按路径、大小、`mtime_ns`、尾部偏移与SHA-256逐项复核；计算过程中不得回退到实时磁盘读取。
- 只有当前子进程输出且精确绑定脚本、`run_id`与`attempt`的结构化`TDX_DAY_UPDATE_RACE`事件可触发整条市场链重跑；最多3次，间隔1秒和3秒。普通异常、旧事件、错误脚本或错误轮次均立即失败关闭，重试中不得写出短暂PASS状态。
