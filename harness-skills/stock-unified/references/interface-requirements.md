# Stock Interface Requirements

Use this file to decide which interfaces are actually missing for a given stock task.

## Rule 1

For any stock interface, classify the result into exactly one of these states:

1. **Interface missing**
   - interface was not called
   - or there is no usable response

2. **Interface failed**
   - interface was called
   - but `ErrorId != 0`
   - or target symbol is absent from the response payload

3. **Interface succeeded, signal non-triggered**
   - interface was called
   - `ErrorId = 0`
   - target symbol exists in the payload
   - signal value is `0`, `0.00`, or `XG = 0`

4. **Interface succeeded, signal triggered**
   - interface was called
   - `ErrorId = 0`
   - target symbol exists in the payload
   - signal value is non-zero or explicitly triggered

Do not collapse state 3 into state 1.

## Single-Stock Analysis

Required:

- `tdx_snapshot`
- `tdx_kline` day
- TQ ZB formulas when formula reasoning matters
- fundamentals / news / announcements status must be explicit

Optional:

- `飞龙在天选股` XG
- `tdx_kline` 5m

Conditional:

- 东方财富/公开资金流交叉验证
  - only when the answer makes a cross-source money-flow claim
  - or when TQ资金结论 needs external confirmation

## Stock Picking / Screening

Required:

- candidate pool source
- `tdx_snapshot`
- `tdx_kline` day
- XG when the strategy explicitly depends on an XG筛选分支

Optional:

- `tdx_kline` 5m

Conditional:

- 东方财富/公开资金流交叉验证 when ranking or exclusion depends on non-TQ capital-flow confirmation

## Daily Review / Limit-Up Review

Required:

- market stats
- candidate/leader pool
- formula verification status
- risk/news status

Conditional:

- 东方财富指数/资金流/涨跌停 cross-check when the output includes market-wide quantitative claims

## Hard rule

Do not ask the user to “补接口” unless you can name the exact missing interface category:

- required
- optional
- conditional

and explain why it is missing for the current task type.
