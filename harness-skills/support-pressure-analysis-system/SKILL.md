---
name: support-pressure-analysis-system
description: "统一的支撑压力与买点区间分析技能（压力与阻力同义）。用于指数或个股关键价位、候选支撑/压力区、突破/跌破观察线与失效线；用户显式调用支撑压力分析系统、支撑压力系统、支撑阻力分析系统、$support-pressure-analysis-system 或旧入口 $support-resistance-analysis-system 时使用。"
---

# 支撑压力分析系统

## 边界

- 主名称与主入口为“支撑压力分析系统”及 `$support-pressure-analysis-system`；“支撑阻力分析系统”及 `$support-resistance-analysis-system` 是同一技能的兼容入口，不是独立技能。
- 目标系统仅为本机 Codex，不调用 OpenClaw、通用股票总执行器或兄弟技能。
- 本技能只做支撑压力技术分析，不做选股排名，不承诺收益，不自动下单。
- 历史统计没有建立相对安慰剂的预测优势时，必须输出 `UNVALIDATED_CANDIDATE_ZONES_ONLY`，不得把候选区间写成确定信号。

## 唯一入口与唯一执行器

- 唯一外部入口：`scripts/codex_entry.py`。
- 唯一业务执行器：`scripts/scientific_engine.py`，仅可由根入口转发。
- 信息：`python "$($env:STOCK_SKILLS_ROOT)\support-pressure-analysis-system"\scripts\codex_entry.py info`
- 自检：`python "$($env:STOCK_SKILLS_ROOT)\support-pressure-analysis-system"\scripts\codex_entry.py selftest`
- 执行：`python "$($env:STOCK_SKILLS_ROOT)\support-pressure-analysis-system"\scripts\codex_entry.py run -- --mode pressure --symbols 600519.SH --out-dir <目录> --run-id <本轮ID>`
- 五法真实K线验收：`python "$($env:STOCK_SKILLS_ROOT)\support-pressure-analysis-system"\scripts\codex_entry.py run -- --validate-five-theories --validation-symbols-per-stratum 4 --validation-limit 0 --bootstrap-iterations 2000`

`entry_support_resistance.py`、`support-pressure-analysis-system.py` 等历史脚本不是入口，不得由模型或下游技能直接调用。

## 固定流程

1. 从本机通达信数据通过 `tdx-local-hub` 读取目标日线文件中的全部有效记录，并绑定真实数据文件路径、大小、SHA-256、文件记录容量与实际读取数量；正式分析及五法验证的 `--limit` / `--validation-limit` 只能为 `0`，任何正数截断立即 `BLOCKED`。
2. 同时运行五套已形式化理论子系统：艾略特双向浪型、缠论确认分型/笔/中枢、方向与尺度自适应斐波那契、ATR归一化江恩、交易区间与确认型威科夫。
3. 将五法通过因果检查的价位与确认枢轴、滚动极值、均线、锚定 VWAP、日线量能代理、客观回撤和缺口共同送入候选区间聚类。
4. 五法共享一个“形式化理论证据家族”，不得把五个方法名重复计作五份独立统计证据。
5. 执行非重叠走前检验、距离匹配安慰剂对照和冻结的横截面校准闸。
6. 在报告中生成 `UNIFIED_FIVE_THEORY_CONCLUSION_V1`，按固定六段逐项输出五法结论和明确综合结论，再重新计算报告大小与 SHA-256。
7. 输出目标级 `*.scientific_support_pressure.json` 与本轮 `run_summary.json`；正式入口只打印增强后的最终摘要，并重新绑定摘要大小与 SHA-256。
8. 只有五法状态、统一结论状态、目标状态、执行器版本、数据质量和持久化回读全部一致才算业务通过。
9. 涉及“五种理论具有预测优势”的结论时，必须额外生成 `FIVE_THEORY_REAL_KLINE_VALIDATION_V1`，逐法绑定开发集、冻结留出集、通达信源文件及执行器哈希；普通单元测试、单标的主链报告和旧参数校准均不能替代。

## 五套正式理论子系统

- 艾略特波浪：必须扫描全量日K并遍历全部右侧确认后的交替枢轴窗口，支持上升与下降推动结构，逐条回读浪2、浪3、浪4、浪5规则；禁止只搜索最近固定数量枢轴。
- 缠论结构：输出确认分型、时间有序且方向交替的笔、三笔重叠中枢和结构观察状态。
- 斐波那契：按真实摆动方向计算回撤与扩展，使用 ATR/价格比例自适应聚类，禁止固定点数分桶。
- 江恩：保留九方图、ATR归一化角度和时间周期接近度；证据强度由结构计算产生，禁止固定分数。
- 威科夫：弹簧和上刺必须突破此前20根交易区间，并用后续收盘接受度确认；输出区间、事件、阶段和量价条件。

五套子系统均输出 `status`、`active_in_main_chain`、`candidate_levels`、`evidence_score_not_probability` 与 `limitations`。它们可进入正式主链，但在走前检验或横截面校准未建立优势时仍只能生成未验证候选区间。

## 统一五法最终交付硬闸

- 每次普通分析必须实际使用艾略特波浪、缠论结构、斐波那契、江恩和威科夫全部五套子系统；任一缺失、未启用或状态非 `PASS`，正式入口必须返回 `BLOCKED`。
- 通达信输入必须满足 `history_scope=FULL_LOCAL_TDX_FILE`、`full_history_verified=true`、`records_returned=source_records_available`；波浪子系统还必须满足 `input_bar_count=records_returned` 与 `search_scope=ALL_CONFIRMED_ALTERNATING_PIVOTS`，否则统一交付失败关闭。
- 最终结论固定按以下顺序输出，六段均不得为空：
  1. 波浪理论：处于第几浪及结构趋势；若完整推动浪未获右侧确认，必须写明“无法可靠编号”，不得猜测浪号。
  2. 缠论：最新确认中枢、最后一笔方向和中枢内外趋势。
  3. 斐波那契：活动摆动方向、当前价下方最近支撑和上方最近压力。
  4. 江恩理论：当前是否处于时间接近窗口、涉及周期或距下一窗口交易日数；时间窗口不得写成已确认转折。
  5. 威科夫：当前阶段、交易区间位置和最近已接受事件。
  6. 综合结论：明确当前结构偏向、趋势是否确认、主支撑/主压力、突破/跌破/失效线及预测资格边界。
- 五法属于同一形式化理论证据家族；综合结论必须披露冲突，不得把五个方法重复计为五份独立统计证据。
- 目标报告必须含 `unified_five_theory_conclusion.schema=UNIFIED_FIVE_THEORY_CONCLUSION_V1`、`status=PASS`、`all_subsystems_used=true` 及固定中文六段；`run_summary.json` 必须逐目标回读该状态并绑定增强后报告哈希。
- 只输出支撑压力区、只列问题、漏掉任一理论、没有明确综合结论或仍打印增强前旧摘要，均属于不完整交付并由正式入口失败关闭。

## 唯一验收

- 结构验收：`quick_validate.py`。
- 入口验收：根入口 `selftest`，必须校验所有活动脚本可编译、唯一执行器存在、无 OpenClaw 运行依赖。
- 子系统验收：五法专项与主链集成测试必须全部通过，且报告中的五套子系统均为 `PASS`、`active_in_main_chain=true`。
- 业务验收：`run_summary.json` 中目标为 `PASS`，其 artifact 指向的报告存在、SHA-256 当前一致、报告目标代码和状态回读一致。
- 统一交付验收：每个目标的 `unified_five_theory_conclusion_status=PASS`，报告中的六段顺序完整，报告与摘要哈希均为增强后当前值。
- 预测优势验收：机器收据必须回读为 `FIVE_THEORY_REAL_KLINE_VALIDATION_V1`，开发集与留出集不重叠，五法分别通过配对安慰剂、精确符号检验和按股票聚类的自助法区间，且 `all_subsystems_pass=true`、`predictive_claim_allowed=true`。否则只能得出“未建立可靠预测优势”，正式主链继续失败关闭为候选区间。
- 任何输入缺失、数据不足、目标错误、旧默认代码、产物缺失或哈希不一致均为 `BLOCKED`。

## 参考资料

- `references/business_spec.md`
- `references/support-pressure-deep-system.md`
- `references/support-resistance-deep-system.md`
- `references/workflow.md`
