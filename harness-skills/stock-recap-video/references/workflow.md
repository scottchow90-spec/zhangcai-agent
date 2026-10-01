# 股票复盘视频唯一工作流

LOCKED_ENTRY: scripts/codex_entry.py

LOCKED_EXECUTOR: Remotion template via fixed entry

LOCKED_ACCEPTANCE: video-quality receipt + central stock-risk receipt

1. `create` 从锁定 Remotion 模板创建空项目并安装同版本依赖。
2. 业务技能先生成新鲜、可绑定的数据证据；视频 metadata 必须嵌入证据 SHA-256 与交易日。
3. `voiceover` 先调用语音技能；`auto` 失败时只允许固定 Windows SAPI 降级，并记录实际 provider。
4. `render` 只通过根入口调用 Remotion；前 5 秒仅显示中央股票风险提示，配音和业务内容从 5 秒后开始。
5. `gate` 与 `verify-receipt` 验证媒体结构、快启、画面、静音边界、响度、字幕、证据哈希和视频哈希。
6. 最终 MP4 还必须通过 `stock-delivery-risk-gate gate` 与 `verify-receipt` 的 OCR、边界和新鲜度验收。
