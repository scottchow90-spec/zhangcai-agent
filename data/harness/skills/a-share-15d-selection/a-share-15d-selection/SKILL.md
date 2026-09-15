---
name: a-share-15d-selection
description: Fixed local Codex workflow for A-share short-term strong-stock scoring from the current limit-up pool or an explicitly named local TDX custom block. The historical skill ID is retained for canonical routing, while the active V6 model uses 26 reproducible factors across breakout power, persistence, market fit, and tradability. Use when the user invokes 15维选股 or asks to audit/optimize that workflow.
---

# A股短线强势股多因子评分

## 唯一业务合同

- 候选池：默认从 `C:\new_tdx_mock\vipdoc` 的沪、深、北三地最新交易日日线全量复算真实涨停，不使用过期 `ZTC.blk`；北交所按30%涨跌幅处理。用户明确指定本机通达信自定义板块时，允许用 `--candidate-block <精确板块名>` 从 `C:\new_tdx_mock\T0002\blocknew\blocknew.cfg` 解析唯一板块文件。目录、日线或成员读取失败必须阻断，不得静默缩池。
- 排除：风险警示与退市、立案调查或财务造假、当日一字板、波大于90且无启动、近3日超过40%且无启动/资金承接、近5日超过60%或近10日超过90%且无资金承接、飞龙段缺失或大于80。禁止仅因近3日超过25%或近5日超过35%就剔除有真实启动和资金承接的强势龙头。
- 公式：大牛线4.0、飞龙在天、游资资金监控、机构资金监控为必需；庄家资金监控只保留为观察字段，不因饱和控盘度加分。
- 排名：使用 `A-SHARE-STRONG-26F-100-V6.1`。26个可复算因子分为爆发力35、持续性35、市场协同20、可交易性10；正向权重100，之后扣除15项显式风险。基本面、估值、财务质量的正向权重固定为0，只允许作为风险背景、公告催化或硬风险证据使用。
- 全局契约：机器权威固定为 `stock-unified/references/short_term_strong_stock_scoring_contract.json`；运行结果必须绑定其路径、版本和 SHA-256。任何消费者发现版本、哈希、因子数、权重或基本面政策不一致时，必须阻断评分与排序。
- 因子角色：23项是个股排序/事件证据因子；强势收盘只确认候选池资格，市场广度与涨停生态只校准市场环境，不宣称具有同日个股横截面区分力。
- 标准化：收益加速度、量能、成交额、资金、趋势斜率、趋势效率、题材和流动性等因素必须在完整评分池内按横截面分位计星；不得把同义布尔信号或相同涨幅窗口重复加分。缺证据计0且不重归一。
- 可审计性：JSON 必须持久化K线、公式标量、资讯覆盖、概念、市场收益横截面、四轴分数、覆盖率、因子诊断和前瞻评估合同。独立审计必须复算26因子、四轴、15风险、7硬闸、总分与排序。
- 科学边界：当期运行通过只证明计算和证据可复算，不证明未来收益预测能力。结果必须保留 `predictive_validation.status=UNVERIFIED_REQUIRES_POINT_IN_TIME_FORWARD_LABELS`，直至使用时点一致数据完成下一交易日开盘进入、未来1/3/5日收益、超额收益、MFE和MAE的滚动样本外检验。
- 输出：JSON 与 CSV 保留全部通过硬闸成员的完整排名，`top5` 仅为前五名；所有被排除成员逐只记录原因，完整排名加排除数必须等于候选池成员数。并列时按最终得分、正向得分、成交额、代码排序。不足五只时交付实际数量，零只时明确“本轮无候选”。
- 模板：`assets/15维选股_教学案例精美Word模板.docx`，SHA-256 必须为 `EC71F04176CB13FBF56AC73D60EE6701CCC71AB877C457D365E130A1795993F5`。模板文件名为历史兼容名，不代表当前模型仍限于15因子。

## 固定执行链

1. 唯一外部入口为 `scripts/codex_entry.py`；业务执行器为 `scripts/run_a_share_15d.py --outdir <outputs>`，可选 `--candidate-block <精确板块名>`。
2. 检查 `status=CLEAN_PASS`、沪深北范围、文件计数闭合、读取错误为0、交易日有效、候选池覆盖闭合、完整排名与前五一致。
3. 每个排名成员必须具备26因子、四轴分数、15风险、7硬闸、四个必需公式完整字段、飞龙段不大于80、因子覆盖率和V6合同。
4. `audit_engine.py` 独立复算语义、横截面、四轴、风险、硬闸、排序和JSON/CSV/DOCX身份；只接受本轮哈希绑定的干净回执。
5. DOCX 只能由内置OpenXML生成器从锁定模板产生。报告必须展示爆发力、持续性、市场协同、可交易性、因子诊断和前瞻验证边界。

不得新增临时业务脚本，不得调用兄弟选股流程，不得把结构自检、文件存在、单日相关性或旧报告冒充预测有效性。

## 评分与因子注册表

- 评分细则：`references/dimensions.md`
- 完整因子注册表：`references/factor-registry.md`
- 执行与审计：`references/workflow.md`
