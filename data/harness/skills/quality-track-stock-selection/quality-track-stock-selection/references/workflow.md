# 优质赛道选股唯一工作流

LOCKED_ENTRY: scripts/codex_entry.py

LOCKED_EXECUTOR: scripts/codex_entry.py run

LOCKED_ACCEPTANCE: run manifest + current status readback

1. 外部只允许根入口 `info|selftest|run|status|backtest|settle`。
2. `run` 固定按事件到赛道再到核心公司的路径执行，不得临场切到热点、龙头或通用个股研究技能。
3. 所有候选、剔除理由、证据时间和评分来自同一运行标识。
4. `backtest` 与 `settle` 只处理根入口生成的既有运行，不接受手工拼接结果。
5. 状态回读、目标清单、日期和当前哈希一致后才允许通过。
