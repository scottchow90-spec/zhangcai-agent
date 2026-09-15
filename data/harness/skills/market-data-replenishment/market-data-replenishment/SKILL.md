---
name: market-data-replenishment
description: "掌财智能体的 Harness 公开市场数据补全技能源文件。"
user-invocable: true
---

此目录是未来 EXE 打包时随程序分发的 Harness 技能源。运行时副本位于 `.dsh/skills/market-data-replenishment/`。

数据补全只读取连板网、东方财富涨停池与龙虎榜的指定交易日公开数据，并将来源、时间、哈希和原始字段保存为本地快照。不得使用模型推测补充缺失行情。
