# TDX Local Hub Source Map

## Raw Files

- Daily K-line: `$env:ZHANGCAI_TDX_ROOT\vipdoc\<market>\lday\<market><code>.day`
- 5-minute K-line: `$env:ZHANGCAI_TDX_ROOT\vipdoc\<market>\fzline\<market><code>.lc5`
- Market folders: `sh`, `sz`, `bj`; Beijing stocks may be stored under `bj` or mapped through `sz` depending on TDX cache.

## Formula Registry

The registry is built from:

- Fixed core formulas:
  - `大牛线4.0`
  - `飞龙在天`
  - `游资资金监控`
  - `机构资金监控`
  - `飞龙在天选股`
  - `15维选股选股`
- Real files under `$env:ZHANGCAI_TDX_ROOT\T0002\gs_bak\*.txt`

`15维选股选股` 是通达信中的历史公式调用名，只提供原始公式字段；它不是 `A-SHARE-STRONG-26F-100-V6.1` 评分器，也不得生成或替代 26 因子总分。全局评分契约以 `stock-unified/references/short_term_strong_stock_scoring_contract.json` 为准。

Reserved formula:

- `庄家资金监控` is retained as a reserved formula and its source is installed under `$env:ZHANGCAI_TDX_ROOT\T0002\gs_bak\庄家资金监控.txt`.
- If the native TQ formula registry has not hot-loaded this private formula, `tdx_hub.py formula 庄家资金监控 <symbol>` computes the same fields from local `$env:ZHANGCAI_TDX_ROOT\vipdoc` daily K-line data and returns the normal TQ-style result shape with `控盘程度`, `控盘度`, `OUTPUT3`, and `OUTPUT4`.

## Local News/Info Candidates

Use `news` to enumerate and preview local cache files from:

- `$env:ZHANGCAI_TDX_ROOT\T0002\msg_zx`
- `$env:ZHANGCAI_TDX_ROOT\T0002\msg_web`
- `$env:ZHANGCAI_TDX_ROOT\T0002\hq_cache`
- `$env:ZHANGCAI_TDX_ROOT\T0002\info_cache`
- `$env:ZHANGCAI_TDX_ROOT\T0002\cache`

Local cache formats vary. The hub returns file metadata and text previews when decodable; binary files are reported as metadata only.
