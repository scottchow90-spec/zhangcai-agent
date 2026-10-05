# Error Prevention Register

## Repeated failure modes

### 1. Wrong task expansion

- "Check" must stay read-only.
- Do not expand audit/check/review into cleanup, delete, restart, or config edit.

### 2. Wrong path targeting

- Identify the exact target path before any state change.
- For cleanup or deletion, operate only on the intended root.

### 3. Wrong market context

- Latest trading date must be explicit.
- Historical reports are reference only, not live data.

### 4. Wrong formula interpretation

- A degraded formula branch is not a bearish signal.
- Missing branch data must stay marked as missing or degraded.

### 5. Wrong domain mixing

- Support/resistance analysis is not the same as stock-picking.
- Do not merge unrelated strategy families unless the user asks.

### 6. Placeholder recovery trap

- Do not keep "restored placeholder" files as if they were recovered knowledge.
- Rebuild from readable local evidence or remove the file.

### 7. Workspace safety

- The 2026-05-25 incident proved that cleanup/delete logic must never target `D:\C盘转移\日志\codex`.
