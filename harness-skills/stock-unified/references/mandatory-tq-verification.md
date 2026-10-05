# Mandatory TQ Verification

This is the fixed verification order recovered from the active `stock-unified` workflow.

## Required sequence

1. Initialize once:
   - `tq.initialize(r'$env:ZHANGCAI_TDX_ROOT\PYPlugins\user\tdxdata_test.py')`
2. Main trend filter:
   - `tq.formula_process_mul_zb('大牛线4.0', stock_list=[...], count=20, dividend_type=1)`
3. Wave / breakout state:
   - `tq.formula_process_mul_zb('飞龙在天', stock_list=[...], count=0)`
4. Hot-money branch:
   - `tq.formula_process_mul_zb('游资资金监控', stock_list=[...], count=5)`
5. Institution branch:
   - `tq.formula_process_mul_zb('机构资金监控', stock_list=[...], count=5)`
6. Dealer branch:
   - `tq.formula_process_mul_zb('庄家资金监控', stock_list=[...], count=5)`
7. Optional selection branch:
   - `tq.formula_process_mul_xg('飞龙在天选股', stock_list=[...], count=0)`
8. Close cleanly:
   - `tq.close()`

## Hard rules

- Reuse the fixed local TQ environment. Do not invent a second initialization path.
- Record which branches actually returned data.
- If a branch is degraded, mark it degraded in the analysis.
- Current D-drive runtime has verified `大牛线4.0` and `飞龙在天` as callable ZB formulas.
- Current D-drive runtime has verified `飞龙在天选股` as a callable XG formula name.
- For stock analysis, TQ verification is a gate, not the whole conclusion.
