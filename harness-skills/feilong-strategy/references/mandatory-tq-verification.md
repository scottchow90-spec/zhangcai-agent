# Mandatory Local Tongdaxin Verification

This workflow is bound to the verified `飞龙在天` source and local Tongdaxin data.

## Required sequence

1. Verify the bound formula source is `references/formulas/飞龙在天.tdx.txt`.
2. Verify its SHA-256 is `AABCEC3D83B2B37D01D53BA4D9C281A745E29F53D941F3704DA95DCEA114E1E0`.
3. Read daily K-line, corporate actions, finance cache, indices and breadth only from `C:\new_tdx_mock`.
4. Execute the exact formula through the offline installed-formula replay path.
5. Record missing local files and do not impute unavailable factors.
6. Bind all outputs to the current canonical receipt before delivery.

## Hard rules

- The legacy formula name `飞龙在天4.0` is forbidden and must never be called.
- Do not use another indicator, a similar skill, web data or a guessed value as a replacement.
- Formula output is one evidence layer; factor conclusions still require sample statistics and time stability checks.
