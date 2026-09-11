# Support Resistance Deep System

## Purpose

Use this reference when the task is to identify support, resistance, buy-point zones, invalidation lines, or confluence areas for an index or stock.

## Inputs

- latest trading date
- recent K-line structure
- major swing high / low
- current trend state
- whether the task is index-level or single-stock

## Five-method framework

### 1. Elliott wave

- Use wave position only to describe trend stage and probable continuation or correction.
- Do not force an exact count when the structure is ambiguous.
- If the dominant reading remains a downside-wave structure, exclude the candidate from buy-point selection.

### 2. Chan structure

- Use central zones, break structure, and buy/sell-point logic to judge whether price is still inside structure or already leaving it.
- A Chan buy point is not valid without bottom-fractal confirmation when the user requires strict confirmation.

### 3. Fibonacci

- Mark retracement and extension levels from the active swing.
- Treat repeated overlap with other methods as a higher-value zone.

### 4. Gann

- Use angle or cycle logic only as a secondary timing/pressure aid.
- Never let Gann levels override current price structure by themselves.

### 5. Wyckoff

- Use accumulation / markup / distribution / markdown language to explain whether a level is likely to hold or fail.
- For candidate selection, require all of the following:
  - accumulation or re-accumulation is visible
  - markup or launch attempt is visible
  - pullback is low-volume
  - breakout is volume-confirmed
  - follow-through / acceptance exists
  - overall volume-price structure is healthy
- Do not reduce this gate to a loose partial score such as 3/5.

## Output format

- primary support zone
- secondary support zone
- primary resistance zone
- breakout / breakdown trigger
- invalidation line
- main scenario
- alternate scenario

## Confluence rule

- A level is high-conviction only when at least two methods overlap.
- A level is strongest when structure, retracement, and volume/behavior context agree.

## Candidate-selection hard gate

Apply this section only when the user is using support/resistance analysis to select names.

1. Exclude any candidate still dominated by a downside-wave structure.
2. Exclude any candidate without Chan bottom-fractal confirmation when the claimed buy point depends on Chan logic.
3. Exclude any candidate failing the full Wyckoff gate above.
4. Run risk scan before final inclusion:
   - fundamentals
   - news / announcements
   - industry risk
   - obvious event risk
5. If the user requires hotspot alignment, exclude non-hotspot names instead of soft-matching them.

## Local reference base

- `elliott-wave-principle.pdf`
- `make_shanghai_ppt.py`
- `memory/技能学习库.md`
