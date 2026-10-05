# Canonical execution workflow

1. The only external entry is `scripts/codex_entry.py`.
2. The business adapter executes the five-strategy scanner through the retained `business_entry.py` implementation.
3. Formula assets, TDX data, strategy outputs and persisted run evidence must all be present.
4. Runtime hard gate and acceptance are provided by `stock-canonical-runtime-v1`.
