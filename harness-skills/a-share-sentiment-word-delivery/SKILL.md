---
name: a-share-sentiment-word-delivery
description: Auxiliary DOCX proof skill for an already generated A-share sentiment report. Use only when the user explicitly invokes $a-share-sentiment-word-delivery to verify a supplied DOCX; never select, route, or execute a sentiment research workflow.
---

# A股情绪文档验收

## 独立调用边界

- 仅在用户显式调用 `$a-share-sentiment-word-delivery` 且已经提供待验收 DOCX 时使用。
- 本技能只做 Word 交付验证，不采集舆情、不生成报告、不选择研究路线。
- 研究业务只有统一的 `a-share-sentiment-workflow`；“五站A股舆情研判”及 `$a-share-five-site-sentiment` 是其兼容名称/入口。本辅助技能仍不得执行或替代研究路由。
- 目标系统是本机 Codex，运行时不得访问 OpenClaw 技能目录或执行 OpenClaw 入口。

## 验证流程

1. 锁定用户提供的 DOCX 绝对路径，确认文件存在。
2. 执行 `scripts/verify_a_share_sentiment_delivery.ps1 -DocxPath <DOCX绝对路径>`。
3. 结合 `polished-word-delivery` 完成 Word 打开、页数、PDF 导出和逐页视觉检查。
4. 只有脚本验证与真实渲染均通过后才可报告完成；未验证层必须明确标注。
