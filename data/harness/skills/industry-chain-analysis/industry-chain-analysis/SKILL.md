---
name: industry-chain-analysis
description: "本机 Codex 的产业链深度研究技能。用于用户要求分析产业链、行业上下游、价值链利润分布、供需周期、技术路线、政策影响、核心受益环节或真伪受益公司时；也用于显式调用 $industry-chain-analysis。个股通用深度研究仍由 $stock-analysis 负责，本技能只补充产业链定位和受益逻辑核验。"
---

# 产业链深度研究

## 执行边界

- 将目标系统固定为本机 Codex，不调用 OpenClaw、NeoData 或 WeStock。
- 将本技能作为产业链研究框架和结果持久化入口，不把它冒充实时数据源。
- 用户只要求通用个股研究时，使用 `$stock-analysis`；只有需要定位产业链环节或核验受益逻辑时才同时使用本技能。
- 用户逐字点名“优质赛道选股”时，使用 `$quality-track-stock-selection`，不以本技能替代该固定选股流程。
- 用户点名其他本机股票技能时，尊重其独立入口；不得自动调用声明为“仅显式调用”的技能。
- 默认在聊天中交付。生成股票 DOCX、PDF、PPTX、XLSX、XLSM 或 XLS 时，必须同时使用 `$stock-delivery-risk-gate` 和相应 Office/PDF 技能并通过其门禁。

## 固定入口

```powershell
$skillsRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME "skills" } else { Join-Path $env:USERPROFILE ".codex\skills" }
$entry = Join-Path $skillsRoot "industry-chain-analysis\scripts\codex_entry.py"
python $entry info
python $entry selftest
python $entry tdx-smoke --symbol 600519.SH --limit 5 --user-confirmed-login
python $entry tdx-status
python $entry run --input <evidence.json>
python $entry status --scope production
python $entry status --scope test
```

- 对外只进入 `scripts/codex_entry.py`。
- `run` 只接受符合 `references/evidence_schema.md` 的证据包，并生成 `result.json`、`report.md` 和哈希绑定的状态指针。生产运行写入 `run/runs` 与 `run/latest.json`；合成测试写入 `run/test-runs` 与 `run/latest_test.json`，两者不得互相覆盖。
- `status --scope production` 必须重新计算生产结果文件的 SHA-256 与大小并写入 `status_readback.json`；`status --scope test` 对测试结果执行同样读回并写入 `test_status_readback.json`。
- `tdx-smoke` 只通过 `$tdx-local-hub` 的固定入口验证 TdxW 运行态、代码/名称/市场映射和真实本地日 K 线；`tdx-status` 对 TNF、日线和上游收据重新做哈希读回。
- 仅当用户在当前对话中明确确认通达信已登录时使用 `--user-confirmed-login`。此时持久化 `tdx_ui_login_state.status=user_confirmed` 和“通达信登录状态由用户确认”；该字段是用户陈述，不冒充程序界面检查。
- 用户没有确认时不传该参数，入口只记录 `not_assessed_by_command`，答复只能说明“本命令未判断通达信可见界面登录状态”，不得表述为“未登录”或“登录状态未验证”。
- `selftest` 的合成样例只能证明执行链可用，不能作为市场研究结论。

## 工作流

1. 首次使用、文件更新或异常后运行 `selftest`，读取持久化的 `run/selftest.json`。
2. 锁定任务类型：
   - `industry`：产业链全景、价值链、供需周期、技术路线、政策与受益环节。
   - `beneficiary-review`：核验候选公司与受益环节的主营占比、订单/产能和业绩兑现。
   - `mindset`：只提供研究纪律、风险预算和证据判断，不提供确定性交易指令。
3. 对实际股票任务先盘点本机已安装股票技能，说明本技能为何适用，并说明明显相邻技能为何未选；不得用通用流程覆盖用户点名的固定技能。
4. 按需读取参考资料：
   - 产业链主任务读取 `references/industry_chain.md`。
   - 受益公司核验读取 `references/stock.md`。
   - 研究纪律或仓位问题读取 `references/mindset.md`。
   - 数据采集和来源选择读取 `references/quantification.md`。
   - 组装入口输入前读取 `references/evidence_schema.md`。
5. A 股任务先对代表标的或受益公司运行 `tdx-smoke` 和 `tdx-status`，从 `run/tdx_smoke.json` 核验代码、公司名、市场、本地数据日期和上游收据。用户已明确确认登录时必须传入 `--user-confirmed-login` 并按用户陈述记录；不得把“程序未检查界面”偷换成“登录状态未验证”。本地数据读取可用性以日线与收据为准。
6. A 股公司进入个股深研时使用 `$stock-analysis` 的固定入口和当前回合公开证据；不得把契约自检结果当成业务报告。
7. 对价格、财报、公告、政策、新闻、产能、库存和市占率使用当前回合取得的证据。优先交易所、监管机构、政府、公司公告/财报、行业协会等一手来源；需要浏览器交互时只使用用户的 Google Chrome。
8. 把事实、推断、风险和未验证项分别写入证据包。历史案例、经验阈值和模板示例不得当作当前事实。
9. 运行固定入口 `run`，随后对实际研究运行 `status --scope production`；从 `latest.json`、`result.json` 和 `status_readback.json` 读取结论与校验状态，不以 stdout 或退出码单独判定成功。合成测试只允许读取 `latest_test.json` 和 `test_status_readback.json`。

## 输出要求

- 产业链输出依次包含：分析边界、全景与分类、价值链、上中下游、供需与周期、技术/政策、受益公司核验、结论、风险和未验证项。
- 每个重要事实都绑定证据 ID；每个推断说明推断依据。
- 受益公司使用 `SUPPORTED`、`WATCH`、`AVOID` 或 `INSUFFICIENT_EVIDENCE`，不得输出保证收益或无条件买卖指令。
- 标注数据截止时间、市场范围和来源定位；无法核验的字段必须写入“未验证”。
- 文末固定声明：`本文基于公开信息提供研究与决策支持，不构成任何投资建议；市场有风险，决策需独立审慎。`

## 完成条件

- `$skill-creator/scripts/quick_validate.py` 通过，`selftest` 持久化状态为 `PASS`。
- A 股调用时 `tdx-smoke.json` 和 `tdx_smoke_readback.json` 均为 `PASS`，且证券身份与日线来源一致。
- 实际任务使用的证据不是自测夹具，且标的、市场和时间口径匹配。
- `run` 结果存在且 `status` 对同一批产物完成当前哈希读回。
- 任何缺失层明确标为 `not verified`；仅自测通过时只能声称技能执行链可用，不能声称已完成实时产业链研究。
