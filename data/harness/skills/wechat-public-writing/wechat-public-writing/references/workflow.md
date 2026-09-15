# 公众号写作唯一工作流

LOCKED_ENTRY: scripts/codex_entry.py

LOCKED_EXECUTOR: prepare then validate

LOCKED_ACCEPTANCE: validated prepared article payload

1. 外部只调用 `scripts/codex_entry.py inspect|prepare|validate`。
2. `inspect` 回读固定语料索引、直接正文样本和写作规则的当前状态。
3. `prepare` 只接收本轮主题、证据与受众，生成结构化文章载荷；不得直接调用历史脚本或其他内容技能替写。
4. `validate` 对同一载荷检查事实与观点分层、来源、标题、结构、禁用表达和风险边界。
5. 只有 prepare 产物与 validate 回读一致才算通过；公众号发布不在本技能自动能力范围内。
