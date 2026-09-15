# Task Audit Checklist

Use this checklist before delivering any stock-analysis or stock-report task.

## 1. Task framing

- Confirm the exact target: index, stock code, basket, or review date.
- Confirm the task type: stock analysis, screening, review, support/resistance, or PPT only.
- Do not mix strategy families unless the current user explicitly asks for a combined result.

## 2. Data gate

- Latest trading date is explicit.
- Quote / K-line source is explicit.
- Formula status is explicit: available, degraded, or unavailable.
- Fundamentals / news / announcements source is explicit.
- Required / optional / conditional interface status follows `interface-requirements.md`.
- If TQ returns `ErrorId=0`, zero-valued signals must stay classified as “interface succeeded, signal non-triggered”, not missing interfaces.
- If a source is stale or partial, mark it instead of silently filling the gap.

## 3. Mandatory signal check

- Run the fixed TQ verification order in `mandatory-tq-verification.md` when the task depends on formula signals.
- If one branch fails, mark that branch degraded.
- Do not convert a degraded branch into a negative signal.

## 4. Analysis structure

- Put the core conclusion first.
- State current stance, key level, and invalidation.
- Separate factual signals from AI reasoning.
- If support/resistance is used, show the key zone and why it matters.
- If a strategy score is used, explain the drivers, not just the total.

## 5. Delivery gate

- Every conclusion has source and time.
- Every risk call has an invalidation condition.
- No stale memory or old report is treated as fresh market fact.
- No read-only request expanded into cleanup, delete, restart, or config edits.
- If output is a file, the exact output path is explicit and verified.
