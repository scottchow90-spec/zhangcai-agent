# 庄家资金监控固定工作流

1. 规范股票代码为 `XXXXXX.SH/SZ/BJ`。
2. 验证 `C:\new_tdx_mock`、`C:\new_tdx_mock\PYPlugins\user\tdxdata_test.py` 和公式源码存在。
3. 初始化本机 TQ。
4. 执行 `formula_set_data_info(symbol, count=5, dividend_type=0)`。
5. 执行 `formula_zb("庄家资金监控", code, xsflag=2)`。
6. 验证 `ErrorId=0`、`Value` 非空以及四个必需字段。
7. 成功返回 `PASS`；任何失败返回 `BLOCKED` 和非零退出码。

禁止批量公式接口、网页、云端行情和本地 K 线模拟回退。
