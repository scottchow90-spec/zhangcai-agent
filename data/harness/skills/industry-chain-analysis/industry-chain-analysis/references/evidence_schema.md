# 证据输入契约

`scripts/codex_entry.py run --input <evidence.json>` 接受 UTF-8 JSON。

## 结构

```json
{
  "schema": "INDUSTRY-CHAIN-ANALYSIS-INPUT-1",
  "mode": "industry",
  "subject": "示例产业链",
  "as_of": "2026-07-22T18:00:00+08:00",
  "market_scope": "A-share",
  "test_mode": false,
  "evidence": [
    {
      "id": "E1",
      "claim": "可由来源直接支持的事实",
      "source_name": "来源主体",
      "source_date": "2026-07-22",
      "retrieved_at": "2026-07-22T18:00:00+08:00",
      "source_locator": "https://example.org/source"
    }
  ],
  "sections": [
    {
      "title": "产业链全景",
      "content": ["分析或推断"],
      "evidence_ids": ["E1"]
    }
  ],
  "conclusion": {
    "stance": "WATCH",
    "summary": "结论及成立条件"
  },
  "risks": ["风险一"],
  "unverified": ["尚未核验的字段"]
}
```

## 约束

- `mode` 只允许 `industry`、`beneficiary-review` 或 `mindset`。
- `stance` 只允许 `SUPPORTED`、`WATCH`、`AVOID`、`INSUFFICIENT_EVIDENCE` 或 `NOT_APPLICABLE`。
- 所有 `sections[].evidence_ids` 必须引用存在的证据 ID。
- 实际研究时 `test_mode` 必须为 `false`，证据列表不得为空，且每项证据必须包含来源日期、当前回合获取时间和定位信息。
- `test_mode: true` 只允许合成自测。入口会在报告和 JSON 中明确标注，只能更新 `run/latest_test.json`，不得覆盖生产 `run/latest.json`，也不得将其当作市场研究结果。
- `risks` 和 `unverified` 必须显式存在；没有已知缺口时可写“未发现，但不代表不存在”。
- A 股本地行情事实应把 `run/tdx_smoke.json` 作为本地证据来源，并在 `source_locator` 写明对应的 `C:\new_tdx_mock\vipdoc` 文件和交易日期；该证据只覆盖身份与行情，不覆盖财报、公告或产业结论。
