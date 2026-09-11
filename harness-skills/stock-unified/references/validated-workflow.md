# Validated Workflow

Recovered from the local `stock-unified` skill and the validation reports under `skills/stock-unified/reports/`.

## Canonical order

1. Classify the task into one primary domain.
2. Lock the target code set and latest trading date.
3. Run mandatory TQ verification when formula signals matter.
4. Pull quote / K-line / structure data.
5. Pull fundamentals, announcements, and news as a second layer.
6. Produce the conclusion first:
   - stance
   - current state
   - key support / resistance or screening state
   - invalidation
7. Add structured reasoning:
   - trend and formula state
   - volume / price
   - support / resistance
   - sector / theme
   - fundamentals / financial safety
   - catalyst / risk
8. Generate report or PPT only if the task asks for it.

## Validation evidence

- `skills/stock-unified/reports/openclaw-full-validation-20260521-005755.md`
- `skills/stock-unified/reports/openclaw-full-validation-20260521-010425.md`
- `skills/stock-unified/reports/openclaw-full-validation-20260521-010510.md`

## Use boundary

- Do not use stale memory or historical reports as current-market facts.
- Do not mix support/resistance-only analysis with stock-picking output unless requested.
- Do not replace missing data with guesswork.
