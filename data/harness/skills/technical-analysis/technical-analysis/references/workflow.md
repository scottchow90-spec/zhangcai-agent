# 技术分析唯一工作流

1. 通过权威股票路由绑定 `technical-analysis`。
2. 规范股票代码，并验证 `C:\new_tdx_mock`、TQ 初始化脚本和三个公式源码存在。
3. 初始化 `C:\new_tdx_mock\PYPlugins\user\tdxdata_test.py`。
4. 执行 `大牛线撑压版`：`count=600`、`dividend_type=1`。
5. 执行 `飞龙在天`：`count=0`、`dividend_type=0`。
6. 执行 `庄家资金监控`：`count=5`、`dividend_type=0`。
7. 每项均调用 `formula_set_data_info + formula_zb` 并验证必需字段。
8. 从三个专用分析器依次生成固定 `16 + 10 + 4 = 30` 行子系统结果。
9. 校验每行七个固定字段非空、身份与顺序准确、无重复，并保留指数不适用行。
10. 校验飞龙交叉状态只使用三个批准术语，且对外内容不含两个指标关系描述。
11. 只渲染一张 Markdown 总表；禁止各公式另存或输出额外对外表格。
12. 三项和 30 行合同全通过才返回 `PASS`、`analysis_complete=true` 和技术总结；
    否则返回 `BLOCKED`、`analysis_complete=false`、失败公式和非零退出码。

`NO_CROSS_JUMP=true`：禁止浏览器、网络、云端、OpenClaw、传统指标或本地 K 线模拟替代。
