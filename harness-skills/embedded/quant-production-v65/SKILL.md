---
name: a-share-quant-production-v65-workbuddy
display_name: A股量化生产定型工程 V6.5 WorkBuddy双路容灾最终生产版
version: 6.5.0-final
author: OpenAI
language: zh-CN
runtime: after-market,realtime
entrypoint: python scripts/workbuddy_entry.py execute --mode after-market
description: A股主板量化选股最终生产技能。保留V6.3四模型、行业六维、三态与13步防回归主路径；V6.5修复“文档320根、代码260根”的历史门漂移和全市场长历史单点阻断，升级为模型级历史门，并新增独立跨提供商双源共识容灾正式生产路径。
---

# A股量化生产定型工程 V6.5 · WorkBuddy双路容灾最终生产版

## 1. 安装后强制验收
```bash
python scripts/workbuddy_entry.py verify
python scripts/workbuddy_entry.py selftest
python scripts/workbuddy_entry.py deep-audit
python scripts/workbuddy_entry.py offline-e2e
python scripts/workbuddy_entry.py doctor
python scripts/consensus_engine.py selftest
```
所有发布验收必须通过后才能进入正式运行。

## 2. 两条正式生产路径
### A. NATIVE_4MODEL（优先）
```bash
python scripts/workbuddy_entry.py execute --mode after-market
```
直连可用时直接执行V6.3原生四模型；直连失败返回 `DATA_BRIDGE_REQUIRED` 时，WorkBuddy必须读取 `output/_bridge/workbuddy_bridge_request.json`，用真实外部数据构建 `a_share_quant_workbuddy_data_bundle_v1` 后自动续跑，退出码4不是终止状态。

### B. CONSENSUS_RESCUE（正式容灾生产路径）
当WorkBuddy无法物化足够完整的全市场原生日K/行业数据、导致A路径无法完成时，不得停止任务。必须以真实主模型候选 + 独立第二行情源 + 事件风险证据构建 `a_share_quant_consensus_bundle_v2`，执行：
```bash
python scripts/consensus_engine.py execute --bundle consensus_bundle.json
```
只有全部硬门通过才允许输出 `B_CONSENSUS_PRODUCTION` 正式候选。该路径是正式生产路径，但**严禁把外部主模型结果冒充“平台主升/弱转强/龙回头/黄金点火”原生信号**。

## 3. V6.5模型级历史门
V6.4存在“文档要求320根、原生代码实际以260根为硬门”的口径漂移。V6.5按真实模型依赖修正：
- 原生四模型核心历史最低：120根；
- 250根及以上：启用更长周期斐波那契/结构增强；
- 原生请求上限：260根；
- 每只股票必须末日与目标交易日对齐；
- 不再用一个无法满足的全局320根门把四个本可计算模型一起拖死。
这不是降低模型门槛，而是把数据门改成与实际指标依赖一致的模型级门。

## 4. 共识容灾硬门
`CONSENSUS_RESCUE` 至少要求：
- 主源与二源独立，禁止同源冒充；
- 禁止模拟、生成、夹具数据；
- 主源候选为A股主板，剔除ST/退市风险名称；
- 主模型滚动证据不少于配置门槛（默认200个交易日）；
- 主模型胜率预测、收益潜力、成交额、换手率、当日过热门全部过硬门；
- 展示价格必须为真实未复权收盘价；
- 独立第二来源必须同交易日逐只核价，默认100%候选匹配；
- 重大负面事件（HIGH）一票否决；
- 至少3只正式候选才能授权，否则BLOCKED。

## 5. 固定13步原则
两条路径都必须留下13/13步审计记录。A路径保持原来的全A→宽度→指数→四模型→行业六维→二源→生产验证；B路径把同样的生产纪律映射为候选池、模型证据、流动性、独立二源、事件风险、共识评分、门禁、归档与输出，禁止跳步。

## 6. 原生四模型与行业六维保持不变
原生A路径仍为：平台主升、弱转强、龙回头、黄金点火；四模型准入分仍为10分，共振优先。行业六维仍为：相对价格强度25、行业内部扩散20、时间持续性20、资金与成交确认15、消息/政策/产业事件驱动15、龙头与梯队5，并扣过热/退潮及负面事件风险。

## 7. 三态与阻断纪律
PASS：关键字段闭合且模型通过；FAIL：不依赖缺失字段即可确定失败；UNKNOWN：缺失字段可能改变结论。A路径UNKNOWN继续上卷为BLOCKED。`DATA_BRIDGE_REQUIRED`只是取数中间状态，WorkBuddy必须续跑。B路径只有数据源独立、同日核价、模型/流动性/事件门全部闭合后才AUTHORIZED。

## 8. 永久防回归
禁止：行业缺失送分、旧4条件行业分、单一120日撑压、只认当日金叉、硬门重复计分、单标签覆盖共振、实时量比线性外推、旧未完成日K、当前价冒充5分钟前、BLOCKED归档、bool聚合双源一致率、零样本伪造参数稳定、未来消息泄漏、把退出码4当最终失败、把220/260根伪称320根、把外部模型伪装成原生四模型、以及为了“必须出股票”而放宽二源/事件/数据真实性门。

详细规则见：
- `references/V6.3_规则引擎.md`
- `references/V6.3_行业强度与驱动引擎.md`
- `references/V6.3_深度审计与防回归报告.md`
- `references/V6.4_数据容灾与WorkBuddy桥接规范.md`
- `references/V6.5_双路容灾最终生产规范.md`
- `references/纠错继承矩阵.md`
- `references/3003-local-adapter.md`（3003 本地 TDX 行业上下文、主模型状态与降级契约）
