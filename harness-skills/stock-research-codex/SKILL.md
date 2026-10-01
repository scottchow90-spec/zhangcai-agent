---
name: stock-research-codex
description: The single always-visible discovery and dispatch entry for local Codex stock work, with evidence-first generic stock research only as the unmatched fallback. Route exact workflow names and explicit stock skill IDs through the canonical catalog before any generic research.
---

# Stock Research Codex

## 唯一发现与分发入口

- 所有股票请求先运行唯一公共路由：
  `python D:\C盘转移\日志\codex\scripts\stock_canonical_runtime.py route --query "<用户原始请求>"`。
- 路由精确命中工作流名称或 `$skill-id` 后，按返回顺序读取对应
  `D:\C盘转移\日志\codex\skills\<skill-id>\SKILL.md`，并通过该技能唯一固定入口
  `scripts\codex_entry.py` 执行。精确命中不得进入通用研究。
- 仅当路由结果为 `generic_default` 时，本技能才执行下方通用股票研究流程。
- 不在本技能、AGENTS、其他技能或脚本中维护第二份别名表、目录册或替代路由器。
- `D:\C盘转移\日志\codex` 是唯一物理、可写的 Codex 权威根目录；
  `C:\Users\Administrator\.codex` 只能作为指向该目录的兼容 Junction，Home 身份必须使用
  `os.path.samefile` 判断，不得按字面路径认定为两套 Home。
- 精确命中和通用回退都必须经统一运行时的 `STOCK_PRODUCTION_POLICY_V1` 与 v4 回执闸门：运行前后合同表面一致、请求与输出严格校验、结论七维数据闸门、原子落盘和当前授权缺一不可。`readiness_validation` 只能证明工程就绪，不能充当股票结论。
- “自动交易级”仅表示离线研究、信号、模拟和交付链路采用失败关闭的生产可靠性标准；账户、凭据、券商、委托、撤单和实盘自动交易始终禁止。

## Operating Rules

- Keep the target system explicit: this skill is for local Codex only. Do not inspect, modify, or diagnose OpenClaw unless the user explicitly names OpenClaw in the current task.
- Treat stock work as evidence-first decision support. Separate verified facts, model assumptions, inferences, and opinions.
- Use fresh sources for current prices, market data, filings, earnings, news, regulations, rates, and analyst/company changes. Include dates, times, and source links.
- Do not rely on memory for current market facts. Memory may guide process and user preferences only.
- Do not store brokerage credentials, API keys, raw account exports, private tokens, or unnecessary sensitive financial data in memories, skills, rules, or automation prompts.
- If the user asks for a direct trade decision, convert it into scenarios, risks, invalidation points, and decision criteria. Avoid guarantees.

## Task Graph

1. **Intake**  
   Input: ticker/security, market, horizon, objective, constraints, existing thesis if any.  
   Output: clarified research question and missing inputs.

2. **Fresh Data Check**  
   Input: research question.  
   Output: one dated evidence set covering price context, filings/company materials, major news, and relevant macro or sector facts. Optional OpenBB, yfinance, or AKShare data may supplement this set; they must not replace mandatory local Tongdaxin data for A-share K-line, limit-up, sector, capital-flow, or screening work.

3. **Business And Financial Read**  
   Input: filings, earnings materials, financial data, company disclosures.  
   Output: revenue drivers, margins, balance sheet, cash flow, guidance, and trend summary.

4. **Catalysts And Risks**  
   Input: news, calendar, filings, sector context, user horizon.  
   Output: upside/downside catalysts, key risks, and thesis invalidation points.

5. **Valuation And Scenarios**  
   Input: financial read, market context, comparable metrics or model assumptions.  
   Output: base/bull/bear scenarios with assumptions made explicit.

6. **Decision Journal**  
   Input: scenarios and risk checks.  
   Output: concise thesis, conditions to act or wait, monitoring checklist, and what would change the view.

7. **Self-Check And Learning**  
   Input: final answer, user feedback, later outcomes, corrections.  
   Output: corrected answer plus compact learning event or memory update when appropriate.

## Reference Loading

- Read `references/research-framework.md` for equity research, watchlist, earnings, filing, or valuation tasks.
- Read `references/evidence-agent-protocol.md` when bounded multi-role analysis or evidence arbitration is needed.
- Read `references/risk-and-compliance.md` when the user asks about buying, selling, sizing, portfolio risk, options, leverage, or anything that could be treated as personal financial advice.
- Read `references/memory-loop.md` when the user asks Codex to learn from a result, correct a stock-research mistake, update durable behavior, or run a post-mortem.
- Run `scripts/validate_stock_skill.ps1` during maintenance to check this skill without external Python packages.

## Evidence-Agent Boundary

- Use only the five roles defined by `references/evidence-agent-protocol.md`:
  fundamentals, market and technical, catalyst, risk, and valuation.
- All roles must share one `evidence_set_id` and may cite only evidence IDs in
  that set.
- A conclusion without evidence is degraded and cannot become a verified fact.
- Only officially confirmed or multi-source-confirmed evidence may enter the
  verified synthesis. Keep all other evidence under unverified items.
- Report conflicts explicitly and constrain confidence by evidence coverage,
  unresolved conflicts, and unverified items.
- Reject order, brokerage action, trade execution, and automated-trading fields
  at every nesting level. This skill produces research decision support only.

## Evidence-Agent Fixed Entrypoint

- Run the bounded smoke case through the existing skill entrypoint: `python scripts/codex_entry.py run -- evidence-agent smoke`.
- Arbitrate supplied evidence and role files through the same entrypoint: `python scripts/codex_entry.py run -- evidence-agent arbitrate --evidence-file <path> --roles-file <path>`.
- `evidence-agent` is a subcommand under the original `codex_entry.py run --` contract, not a second public entrypoint. Do not invoke `evidence_agent_workflow.py` directly for normal skill execution.

## Output Contract

- Start with the answer or current view, then show the evidence summary.
- State "as of" date/time for time-sensitive data.
- Cite sources for current facts.
- Label uncertainty and missing verification explicitly.
- End with a short self-check: what was verified, what is inferred, and what remains unverified.
