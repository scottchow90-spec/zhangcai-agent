# 产业链深度研究唯一工作流

LOCKED_ENTRY: scripts/codex_entry.py

LOCKED_EXECUTOR: scripts/codex_entry.py run --input

LOCKED_ACCEPTANCE: input.json + result.json + report.md + manifest.json

1. 外部只调用根入口的 `info|selftest|tdx-smoke|tdx-status|run|status`。
2. 业务输入必须符合 `references/evidence_schema.md`；生产模式至少包含一项可核验证据，测试模式不得冒充真实研究。
3. A股任务先通过本机通达信状态和哈希回读，再执行产业链分层、价值传导、公司映射、风险及未验证项。
4. 结论只允许 `SUPPORTED`、`WATCH`、`AVOID`、`INSUFFICIENT_EVIDENCE` 或 `NOT_APPLICABLE`。
5. 唯一验收读取 manifest 绑定的输入、结果和报告当前 SHA-256 与大小；任何不一致均失败关闭。
