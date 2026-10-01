# 龙虾AI涨停监控唯一工作流

LOCKED_ENTRY: scripts/codex_entry.py

LOCKED_EXECUTOR: scripts/stock_dashboard.py

LOCKED_ACCEPTANCE: stock_execution_result.json + API same-origin selftest

1. 外部只调用 `scripts/codex_entry.py`，不得直接启动资产目录或内部脚本。
2. `selftest` 必须验证看板、涨停、跌停、炸板和市场宽度等同源接口。
3. 业务执行只使用当前本地通达信交易日数据，目标代码、日期和结果写入固定状态文件。
4. 网页服务只绑定本机回环地址；验收读取同一服务接口与持久化结果，不以进程存活代替业务通过。
5. 自动交易不在本技能能力范围内。
