---
name: big-bull-analysis-scoring-system
description: "本机通达信大牛线分析与评分统一技能。用于“大牛线”“大牛线4.0”“大牛线分析评分系统”“大牛线量化工具”“大牛线评分系统”“大牛线百分制排名”“黄金点火板块评分”等请求；支持单只股票十六项完整分析，以及通达信自定义板块百分制评分、硬条件筛选、并列排名和明亮大字八千海报。"
---

# 大牛线分析评分系统

## 统一边界

- 将原“大牛线量化工具”和“大牛线评分系统”合并为一个技能。
- `分析`模式处理单只股票，完整保留大牛线十六项固定子系统。
- `分析`模式必须在十六项证据之后给出五维综合评分、唯一市场阶段、核心矛盾、明确结论以及转强、转弱和失效条件；禁止只罗列子系统。
- 指数的“中期偏强/中期偏多/上升趋势”必须同时通过三项确认闸：至少连续两个收盘站稳EMA173/193/213全部中长期线、突破全部有效黄金分割压力、取得下降趋势线突破的可核验字段。任一项未通过或字段缺失时，必须标记“中期转强未确认”，禁止用短周期主趋势线向上或EMA内部排序代替中期突破。
- `评分`模式处理通达信自定义板块，固定使用大牛线16项、飞龙在天10项、庄家资金监控4项的30项综合评分。
- 默认运行研究型30项综合评分，默认板块为“黄金点火”，简称 `HJDH`。
- 历史五维板块评分已退出生产默认入口；只有明确提出历史兼容验证并显式提供`--legacy-five-dimension-compat`时才允许运行，禁止与30项综合评分混用或互相替代。
- 只使用本机 `ZHANGCAI_TDX_ROOT` 指向的数据与运行态，不使用网页数据替代本机公式或日线。掌财桌面端会注入实际安装路径，禁止固定写入 C 盘或开发机技能目录。
- 分析结论与评分只用于研究和候选整理，不代表未来结果。

## 固定入口

信息与自检：

```powershell
python "$($env:STOCK_SKILLS_ROOT)\big-bull-analysis-scoring-system"\scripts\codex_entry.py info
python "$($env:STOCK_SKILLS_ROOT)\big-bull-analysis-scoring-system"\scripts\codex_entry.py selftest
```

单只股票分析：

```powershell
python "$($env:STOCK_SKILLS_ROOT)\big-bull-analysis-scoring-system"\scripts\codex_entry.py run -- analyze 600519.SH
```

默认板块评分：

```powershell
python "$($env:STOCK_SKILLS_ROOT)\big-bull-analysis-scoring-system"\scripts\codex_entry.py run
```

默认入口等价于`score-research-composite`，不是历史`score-board`五维模式。

三公式综合评分历史回测与正式模型优化：

```powershell
python "$($env:STOCK_SKILLS_ROOT)\big-bull-analysis-scoring-system"\scripts\codex_entry.py run -- backtest-composite --count 1300 --max-stocks 300 --rebalance-days 5 --cost-bps 30
```

不回测的研究型综合评分：

```powershell
python "$($env:STOCK_SKILLS_ROOT)\big-bull-analysis-scoring-system"\scripts\codex_entry.py run -- score-research-composite --board-name 黄金点火 --board-code HJDH
```

三公式综合评分固定且仅包含大牛线16项、飞龙在天10项、庄家资金监控4项，共30项。禁止增加任何其他数值或非数值评分项目，禁止在报告、排名、贡献明细、海报或执行依赖中追加额外项目。

`score-research-composite`固定使用大牛线40%、飞龙在天35%、庄家资金监控25%。30项全部具有真实公式来源、有限原始值、正业务权重和逐项贡献；常量型当日观测按中点秩50分参与，不得归零。原30项只允许在所属体系内部形成各自的0至100分子分，不得跨体系直接线性相加。

总分固定采用三体系加权基础分、三体系共振加分和三体系分歧扣分，三体系权重必须严格合计100%。任何结果只要不是30项完整、16＋10＋4分组正确、三体系唯一或三体系权重合计100%，都必须停止交付。

三套公式特征与收益标签必须统一使用本机通达信前复权日线；10日标签必须在训练/验证和验证/测试边界各净化至少10个交易日。庄家公式的绘图重复行和常量100不得冒充四个子系统，固定改用原公式B2成本压力、B5资金强度、B6控盘差值和控盘程度四个真实逐日变量。

模型必须在统一评分日和固定参考母体确定后，仅使用该母体当日横截面构建。单项百分位采用中点秩；并列值共享平均名次，完全没有横截面区分度的真实常量观测映射为50分但仍保留正业务权重。任一项字段缺失、原始值非有限、权重不大于0或贡献不可复算时，必须在排名和海报写出前失败关闭。

固定30项全部通过数据闸后，三套体系信息可靠性均为1，体系内分别按16、10、4项等权。任何体系不得中性弃权或重分配顶层权重；缺一项即整单失败，禁止用零权重、固定50体系分或代理指标绕过。

预测验收只有两种终态：`PREDICTIVE_PASS`或`PREDICTIVE_REJECTED`。只有独立样本外日期不少于40、样本外明细与分期均非空、平均IC不低于0.01、成本后5日超额不低于0.10%、10日超额不低于0.15%、三项Newey-West 95%区间下界均大于0、并同时优于等权基准，且历史时点股票池与涨跌停、停牌、ST、流动性等可交易约束完整时，才允许`PREDICTIVE_PASS`。任一门槛失败必须输出`PREDICTIVE_REJECTED`，正式模型文件必须`model=null`，禁止安装、禁止用于当前评分。优化过程无法产生可评估候选、独立样本外为空或状态含糊时只能`BLOCKED`，不得以结构模型代替预测验收。

使用已通过回测验收的正式模型，对本机通达信最新统一交易日执行三体系综合评分：

```powershell
python "$($env:STOCK_SKILLS_ROOT)\big-bull-analysis-scoring-system"\scripts\codex_entry.py run -- score-composite --board-name 黄金点火 --board-code HJDH
```

生成固定30项的评分结构海报；该模式展示三体系、权重和0至100分值，但不会把未通过预测验收的当前模型伪装成已启用：

```powershell
python "$($env:STOCK_SKILLS_ROOT)\big-bull-analysis-scoring-system"\scripts\codex_entry.py run -- structure-poster --weight-source <最后一次已执行模型结果JSON>
```


评分结构海报必须同时生成`7680×4320`成品和`1920×1080`适配预览。成品最小可见字号不得低于96像素，核心正文不得低于128像素，主要定量信息不得低于136像素；预览中的对应门槛分别为24、32、34像素。背景必须明亮，且必须通过重叠、裁切、中文纯净度、固定30项完整性与三体系权重合计100%的自动门禁。若当前正式模型未通过，海报必须明确标注仅展示评分结构、不授权生产评分。

综合评分先以通达信`market=23`沪深300固定参考母体计算固定30项百分位和三套体系子分，再按三体系权重融合，最后输出指定通达信自定义板块。板块股票只作为待评分目标，不得加入或改变百分位母体。输出0至100唯一总分、三体系子分、三体系加权基础分、三体系共振加分、三体系分歧扣分、固定30项原始值、权重和逐项贡献。预测型`score-composite`的正式模型状态不是`CLEAN_PASS`、预测状态不是`PREDICTIVE_PASS`或独立样本外证据为空时必须停止；研究型`score-research-composite`不适用这些预测门槛，但必须标注`RESEARCH_ONLY`、`prediction_authorized=false`。

板块综合结论必须使用固定母体分位生成未来5至10个交易日的规则型结构预测，并逐股给出偏强、偏强震荡、震荡分化或偏弱判断及预测失效条件。所有结果必须输出`forecast_mode=RULE_BASED_STRUCTURAL_FORECAST`、`forecast_is_probability=false`和`score_is_probability=false`；方向预测不是上涨概率、收益承诺或价格目标。

评分日期使用`Asia/Shanghai`时区执行前置硬闸。北京时间星期一至星期五`09:30`后，统一评分日必须严格等于北京时间当天；`09:30`前允许使用本机最近完整交易日。例如北京时间`2026-08-13 17:30`时，`score_date=20260812`必须返回`BLOCKED`；北京时间`2026-08-18 00:32`时，允许使用本机最近完整交易日`20260817`。硬闸必须在最新排名JSON、排名CSV、30项贡献CSV和排名报告写出之前执行；除开盘前例外外，本机行情未更新到当天时禁止生成、复用或交付旧榜单。

三公式综合评分的用户可见报告必须是完整报告，不得只输出“排名、代码、总分”的摘要。完整报告必须显示股票名称和代码、板块排名、全市场排名、综合总分、三体系加权基础分、三体系共振加分、三体系分歧扣分、三套体系子分、未来5至10个交易日结构预测和失效条件，并逐只展示固定30项原始值、正权重和逐项基础贡献。任一股票缺少名称、总分拆解、预测结论、失效条件或16＋10＋4明细时，报告完整性校验必须失败并停止写出。

多板块任务完成各板评分后，必须通过固定入口执行跨板一致性门禁；评分日期、固定母体、模型、公式目录或任一共有股票的总分、三体系子分、总分拆解、30项贡献存在差异时必须阻断：

```powershell
python "$($env:STOCK_SKILLS_ROOT)\big-bull-analysis-scoring-system"\scripts\codex_entry.py run -- verify-cross-board-consistency --ranking-json <板块一排名JSON> --ranking-json <板块二排名JSON>
```

指定其他自定义板块：

```powershell
python "$($env:STOCK_SKILLS_ROOT)\big-bull-analysis-scoring-system"\scripts\codex_entry.py run -- score-research-composite --board-name <板块名称> --board-code <板块简称>
```

## 分析模式

必须完整输出以下十六项，禁止删减、合并或换序：

1. 主趋势线
2. 均线分层
3. 日线颜色信号
4. 流通市值
5. 短线动量
6. 参与与离场信号
7. 控盘程度
8. 财神短线
9. 庄进与庄出
10. 强势股识别
11. 龙头参与区
12. 龙回头
13. 点火信号
14. 起爆与题材共振
15. 布林线与多重均线
16. 核心黄金分割撑压

第十六项必须保留支撑一、支撑二、压力一、压力二和第五输出字段。

指数报告必须区分“EMA173/193/213内部排序”和“收盘站稳全部中长期线”。上方存在但尚未突破的黄金压力属于约束，不得因为“仍有上涨空间”而作为趋势加分；大牛线运行时没有提供独立下降趋势线突破字段时，必须按未核验处理，不得自行猜测已经突破。

## 历史五维兼容模式

本节仅用于旧结果复核，不是当前大牛线综合评分系统。未提供显式兼容标识时，代码硬闸必须返回`legacy_five_dimension_mode_blocked`。

- 方向位置：30分
- 上涨劲头：25分
- 当天表现：20分
- 上下空间：20分
- 额外提醒：5分

先执行硬条件，再按总分从高到低排列；同分采用并列名次。

## 参考资料

- 分析规范：`references/analysis_business_spec.md`
- 十六项说明：`references/analysis_subsystems.md`
- 评分规范：`references/scoring_business_spec.md`
- 合并流程：`references/workflow.md`

## 验收

- 技能结构必须通过技能创建器检查。
- 固定入口自检必须通过。
- 分析模式必须实跑一只股票并生成报告。
- 30项综合评分模式必须实跑“黄金点火”板块并生成排名数据、八千海报和`1920×1080`完整适配预览。
- 海报必须为 `7680 × 4320`，最小字号不低于96像素，背景明亮，无文字重叠、无裁切。
- 适配预览必须为`1920 × 1080`且实际写出；预览最小可见字号不低于24像素、核心正文不低于32像素、主要定量信息不低于34像素。
- 用户要求整个板块时，海报展示行数、评分源股票数和通达信板块成分数必须相等，且每只名称和代码均可见；禁止固定行数截断后冒充完整交付。
