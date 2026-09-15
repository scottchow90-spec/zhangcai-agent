# 龙头深度研究数据合同

## 运行字段

- `workflow_name`：`龙头深度研究`
- `schema_version`：`3.2`
- `trade_date`：研究使用的交易日
- `data_mode`：`intraday` 或 `close`
- `generated_at`、`data_cutoff`：带时区时间
- `sources`、`evidence`、`stocks`、`concept_summary`
- `morning_limit_ups`、`lhb_status`、`lhb_net_buy_ge_100m`
- `report_claims`、`unresolved_critical_conflicts`
- `supplemental_context`：连板网当日情绪、题材与梯队快照，仅作补充交叉验证。

## 来源字段

每个来源包含 `source_id`、`source_name`、`provider_group`、`source_type`、`trade_date`、`fetched_at`、`locator`、`sha256`。关键事实至少两个独立 `provider_group`。

## 股票字段

每只股票包含：代码、名称、交易所、一级投资板块、细分方向、当日推动因素、分类依据、适用涨停价、截至时点是否封板、首次封板时间、截至时点最后封板时间、开板次数、连续涨停、近期涨停、换手、成交额、流通市值、性质标签、龙虎榜和证据编号。

- `primary_concept`：内部兼容字段，对外含义固定为“一级投资板块”，且只能取大消费、医药生物、大科技、高端制造、新能源、基建公用、金融地产、周期资源之一；每股只能有一个值。医药制造、医疗服务、医药商业、生物制品和医疗器械不得归入大消费。
- `secondary_concepts`：对外显示为“细分方向”，用于行业和窄题材，不参与一级板块家数统计。
- `event_drivers`：对外显示为“当日推动因素”，用于摘帽、并购重组、实控人变更、中报增长等当日事件，不参与一级板块家数统计。
- `classification_basis`：说明该股归入当前一级投资板块的事实依据，不得为空。

## 板块逻辑模型

涨停家数前三板块必须生成 `logic_model`，并由审计器根据股票明细复算。该模型至少包含：

- `logic_type`：双机制共振型、主机制集中型、高度抱团多分支并行型或多分支轮动型。
- `shared_mechanisms`：共同产业机制名称、覆盖成员数、覆盖率和具体股票代码。共同机制必须来自成员的细分方向或当日推动因素，不能凭板块名称推断。
- `common_event_evidence`：同一具体公司级事件表述覆盖至少两只成员时的事件、覆盖家数和股票代码。事件表述必须包含明确行动以及日期、金额、项目、产品、股权或控制权等可核验细节；“半年报增长”“并购重组”等通用短标签不得进入。没有满足条件的共同事件时必须为空。
- `causal_boundary`：明确区分共同产业机制、共同事件证据与已证实因果。禁止把题材共现、行业归类或封板先后直接写成外生事件造成涨停。
- `temporal_sequence`：高度锚、机制锚、时序领先个股、容量核心及领先个股后90分钟内的同题材封板数量。该字段只表达可观察顺序，不表达前者导致后者涨停。
- `validation`：成员数、连板数、10:00前封板数、零开板数、高频开板数、14:00后最终封板数、成交额和连板梯队缺口。
- `constraints`：至少一项能够削弱板块逻辑的结构事实；不得用运行失败条件或来源对账代替。
- `structural_evidence_strength`：盘面结构证据强度，只能取高、中、低。
- `structural_evidence_score`：由共同机制覆盖、连板梯队、早盘封板、零开板、90分钟同题材跟随、高频开板和梯队缺口复算的结构评分。

盘面结构证据强度只评价共同机制覆盖与盘面结构是否相互印证，不评价公司级事件真实性，不表示事件因果已被证实，也不表示未来涨跌概率。禁止使用含混的 `confidence`、`confidence_score` 或“证据完整度”表述。

`logic_summary`、`mechanism_evidence` 和 `validation_constraints` 分别是 `logic_model` 的核心逻辑、机制/事件/时序、盘面验证与约束的可见表达，三者必须与结构化模型逐字一致。仅罗列涨停家数、连板数、早盘封板数、零开板数和最高高度，不构成逻辑。

- 所有模式：`at_limit_at_cutoff=true`。
- 收盘模式：另需 `close_at_limit=true`。
- 盘中模式：不得把截至时点最后封板写成收盘最终封板。

## 龙虎榜状态

- `published`：按同股同日成交额最大记录去重，保留公开榜单席位并逐席位复算买入、卖出和净买入。
- `not_published`：名单必须为空，正文只陈述截至时点尚未发布。
- 禁止用上一交易日龙虎榜补盘中缺口。

## 新鲜度

`codex_entry.py validate` 必须实时调用双源市场状态接口，并复核 `trade_date`、`data_mode`、`data_cutoff` 和至少两个来源组的抓取时间。此检查不能由输入文件中的自报“最新日期”替代。
