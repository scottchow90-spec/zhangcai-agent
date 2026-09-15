# Canonical Codex execution workflow

This skill has one executable Codex entry:

```powershell
python scripts\codex_entry.py run
```

The facade delegates only to `stock-canonical-runtime-v3`. The runtime loads this
skill's immutable contract from `stock_execution_contracts.json`, executes
`scripts\canonical_business_adapter.py`, records the real child business
process and artifacts, writes an integrity-bound receipt, and accepts the result
only after all semantic assertions and required artifacts pass.

Independent acceptance uses a new Python process:

```powershell
python scripts\codex_entry.py verify --receipt <receipt.json>
```

`info`, `selftest`, smoke, build, and legacy gate commands are not business-run
substitutes. `scripts\legacy_codex_entry.py` is retained only as the same-skill
business implementation behind the canonical adapter.
