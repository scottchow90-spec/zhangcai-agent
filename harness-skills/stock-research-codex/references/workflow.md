# Canonical execution workflow

1. The only discovery and dispatch authority is
   `D:\C盘转移\日志\codex\scripts\stock_canonical_runtime.py route --query "<original request>"`,
   backed only by `stock-unified\references\stock_skill_ids.json`.
2. An exact workflow-name or `$skill-id` match must load that skill's `SKILL.md`
   and execute its `scripts\codex_entry.py` in route order. It must not enter the
   generic research executor.
3. `stock-research-codex` runs generic research only when the route reports
   `generic_default`.
4. No second alias table, catalog, contract catalog, or routing script may act
   as an authority. `stock_execution_contracts.json` is the only execution
   contract catalog.
5. The audit workload uses current local TDX data and explicit fixture
   boundaries to execute all workflow stages without presenting an investment
   report.
6. Production research must replace fixture fields with current, cited evidence
   before user delivery.
7. Acceptance uses the persisted runtime receipt and result readback.
