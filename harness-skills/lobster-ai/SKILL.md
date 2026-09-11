---
name: lobster-ai
description: 本机 Codex 的 LOBSTER AI A股涨停监控网页面板技能。用于用户说 LOBSTER AI、龙虾AI、启动涨停监控、打开涨停网页面板、检查涨停/跌停/炸板/连板池、验证 LOBSTER 运行状态或修复该面板时；保留 Chrome 可视化面板，并通过本机 Python 同源代理读取公开行情池。
---

# 龙虾智能涨停监控

## 本机选股结果总览

- 新增独立页面 `assets/web/stock-dashboard.html`，规范地址为 `http://127.0.0.1:<port>/stock-dashboard.html`；原 `index.html` 涨停监控面板继续保留。
- `/api/stock-results` 只读取 `scripts/stock_dashboard.py` 中显式白名单列出的本机持久化业务结果，不接受浏览器传入文件路径，不把自检、预检、回退样本、错误目标或运行阻断包装成选股结论。
- 面板固定审计 18 个核心选股工作流，并分别显示严格入选、观察项、主题结果、空候选、运行阻断、仅诊断、目标不符和未落盘状态。
- 每次接口读取都把规范化快照写入 `%LOCALAPPDATA%\LOBSTER-AI\stock_dashboard_snapshot.json`，供本机回读和验收。
- 页面通过同源 Server-Sent Events 监听白名单结果文件变化，检测到变化后立即重新读取并更新；60 秒轮询只作为断线兜底，手动刷新按钮保留。选股结果仍可能受上游业务技能落盘时效影响，仅作证据化决策支持，不构成投资建议。

使用股票技能固定入口 `scripts/codex_entry.py`。`scripts/lobster_cli.py` 是网页运行辅助入口；不要直接以 `file://` 打开网页，也不要让页面直接跨站请求行情接口。

## 固定流程

1. 先运行 `python scripts/codex_entry.py info --json`，确认 Python、Chrome、网页资产和状态目录。
2. 健康检查或故障排查时运行 `python scripts/codex_entry.py selftest --json`。要求结果写入 `last_selftest.json`，并回读 `status=PASS` 后再报告可用。
3. 用户要求打开面板时运行 `python scripts/lobster_cli.py launch`。该入口只绑定 `127.0.0.1`，由本机代理访问选股宝公开池，并用 Google Chrome 打开面板。
4. 服务已在后台运行但需要重新打开页面时，运行 `python scripts/lobster_cli.py open --json`。
5. 只做后台验证时运行 `python scripts/lobster_cli.py launch --no-browser`。
6. 查看上次持久化结果时运行 `python scripts/lobster_cli.py status --json`。
7. 需要把本技能纳入股票技能执行门禁时，保持网页服务运行，并执行 `python scripts/codex_entry.py run --json`；该命令从当前涨停池选择一个沪深股票，落盘股票代码、名称和最新交易日，只做技能身份与时效绑定，不构成选股或投资建议。
8. 对用户交付时必须在其 Google Chrome 中打开并回读规范地址 `http://127.0.0.1:<port>/index.html`；地址单独成行，后面不得紧接任何中英文标点、PID 或说明文字。服务仅对历史误粘的 `index.html，...`、`index.html,...`、`index.html。...`、`index.html....` 或 `index.htmlPID...` 地址做窄范围重定向，其他未知路径仍返回 404。

## 数据与边界

- 将面板数据视为时效性市场数据；显示并核对数据日期。
- 涨停、跌停、炸板和连板使用网页注明的净口径；全市场涨跌广度来自选股宝市场指标同源代理。广度缺失、非当日或与核心池交易日不一致时，情绪周期必须自动禁用并显示降级状态。
- 规则评分未经回测，只用于观察，不把它表述为收益预测或投资建议。
- 若用户进一步要求个股研判、选股或交易建议，先使用 `$stock-hard-gate` 和匹配的本机股票业务技能；本技能不替代研究流程。
- 若要生成股票类文件，另行遵守 `$stock-delivery-risk-gate`；网页运行本身不等于股票文件交付。

## 运行资产

- `assets/web/index.html`：保留的网页可视化面板。
- `assets/web/lobster.ai.js`：面板交互与规则计算；行情入口固定为本机 `/api/pool` 和 `/api/breadth`。
- `scripts/launch_lobster.py`：本机 HTTP 服务、核心池与全市场广度同源代理、Chrome 启动与运行状态落盘。
- `scripts/lobster_cli.py`：网页运行辅助入口、结构检查、真实服务/API 自检和状态回读。
- `scripts/codex_entry.py`：股票技能规范固定入口，复用本机面板服务并持久化当前股票身份、数据交易日与门禁所需结果。
