# 四策略系统唯一工作流

LOCKED_ENTRY: scripts/codex_entry.py

LOCKED_EXECUTION: scripts/codex_entry.py run

1. 根入口读取本机 TDX 的沪、深、北日线文件。
2. 每个有效标的至少读取 120 根日线，逐一计算 MA5、MA10、MA20、MA60、量比、动量和区间高低点。
3. 按业务规范中的四组固定条件独立判定，不允许按候选顺序分配策略名称。
4. 每套策略最多保留评分最高的 10 个真实信号，并记录数据文件、交易日和失效线。
5. 四套条件均已执行但没有候选时，输出 `CLEAN_PASS + NO_SIGNAL`；不得用 fallback 候选凑数。
6. 结果固定落盘到 `reports/four-strategy-current.json`，重新解析后输出当前哈希和大小。
