# Canonical execution workflow

1. The only external entry is `scripts/codex_entry.py`.
2. The runtime adapter resolves the latest local TDX trade date, requires manual confirmation, then executes shortline discovery and daily limit-up mining before computing the supplement-leader result.
3. Both upstream runs and the final persisted result must pass; a missing upstream artifact blocks the skill.
4. Runtime hard gate and acceptance are provided by `stock-canonical-runtime-v1`.
