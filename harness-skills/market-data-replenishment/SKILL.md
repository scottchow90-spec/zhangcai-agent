---
name: market-data-replenishment
description: "掌财智能体的 Harness 公开市场数据补全技能源文件。"
user-invocable: true
---

此目录是未来 EXE 打包时随程序分发的 Harness 技能源文件；运行时副本位于应用可写数据目录的 `harness/skills/market-data-replenishment/`。本技能的本地数据入口是 `harness/context/local-data-page.json`，先读本页再读资产，不要扫描或猜测路径。完整约定见 `references/local-data-page.md`。

## 本地数据落盘页

每次日线归档和数据状态更新都会生成 `ZHANGCAI_LOCAL_DATA_PAGE_V1`。它记录 `data_root`、最近完整通达信交易日、资产状态、相对路径、快照哈希和降级原因。Harness 运行时必须：

1. 读取 `harness/context/local-data-page.json`；
2. 读取 `status/current.json`、日线 `manifest.json` 及目标资产的 JSON/JSONL 快照；
3. 核对 `source`/本地源目录、`source_date`、`retrieved_at`、`status`、`error_or_reason` 和 `sha256`；
4. 将结果保存到 `reports/daily/<trade-date>/` 或对应的 `harness/jobs/<job-id>.json`。

统一数据来源清单位于 `evidence/sources/latest.json`，对应交易日的原始清单位于
`evidence/sources/<trade-date>/manifest.json`；压缩包中的接口/网站目录已整理为
`harness/context/package-source-inventory.json`。压缩包来源和当前运行时缺口的逐项绑定见
`harness/context/package-source-gap-report.json`，实际适配器、输出路径和读取顺序见
`harness/context/package-data-routing.json`。运行数据校验或策略前必须先读取这些文件，
区分 `available`、`partial`、`declared_not_snapshotted`、`not_configured` 和 `blocked`。
只有真正存在并通过哈希/日期校验的文件才能作为当前输入；“压缩包内有源码”不能升级为“当前接口已取数”。

公式类技能还必须核对 `evidence/formulas/package/manifest.json` 及其镜像文件；五公式现场结果只能引用 `evidence/formulas/<trade-date>/` 中状态为成功的 TQ 回执。公式安装包镜像用于 EXE 携带和路径恢复，不能代替现场执行回执。

## 数据真值与降级

`market/daily/<trade-date>/manifest.json` 指向的 `file`（首次通常为该目录的 `tdx-bars.jsonl`，增量模式通常为 `market/daily/aggregate/tdx-bars.jsonl`）是历史价格、复盘和公式输入的主数据；公开行情快照不能无痕替代 TDX 全历史，但可以按下述契约补齐明确缺失的交易日。包内源码、接口说明、已安装文件或成功响应都不等于接口可用，必须以本地资产现场状态为准。状态只允许使用 `available`、`degraded`、`blocked`、`missing` 等明确值；日期不一致、哈希不一致、必需字段缺失时不得补数，必须在 `cautions`/回执中说明。

## 可直接使用的日线、索引与公开降级

日线不是只有一个归档文件，而是以下可迁移的数据契约：

- `market/daily/index/tdx-symbol-index.json`：按 `sh/sz/bj+六位代码` 索引 TDX `.day` 文件，包含文件相对路径、记录数、首尾日期；它用于快速定位，不替代文件内容校验。
- `market/daily/index/daily-data-index.json`：统一可用性索引，声明每只股票的 TDX 主源、应用内降级记录、日期范围、记录数和缺失字段；交易日目录还保存 `market/daily/<trade-date>/daily-data-index.json` 便于归档检索。
- `market/daily/aggregate/tdx-bars.jsonl`：应用内唯一 TDX 全历史 canonical 主库；`market/daily/<trade-date>/` 只保存交易日 manifest 和小型 delta。`manifest.json` 的 `file` 是唯一主路径，不得硬编码文件名。
- `runtime/daily-jsonl-integrity-<trade-date>.json`：对主日线 JSONL 的逐行结构、必需字段、记录数和日期覆盖校验；需要全文件结构证据时优先读取它。
- `market/daily/fallback/<trade-date>/<symbol>.jsonl`：只存明确返回目标交易日的公开日线，统一字段为 `date/open/high/low/close/volume/amount`，同时保留 `source/source_url/source_date/retrieved_at/source_sha256/status/missing_fields`。

读取优先级固定为 `tdx_local_day → tdx_archive → public_daily_fallback`。通达信可用时，使用 TDX 全历史；通达信目录关闭、不可读或某个目标日缺失时，才读取 `daily-data-index.json` 指向的公开降级记录。降级记录的 `quality` 必须传给 Harness；`amount` 缺失就保持空值，不能用价格乘成交量估算。公开源降级只代表已核验的离散交易日，不代表完整 TDX 历史，也不能单独支持需要连续历史或 TQ 公式回执的结论。

当前公开降级脚本为 `scripts/daily_data_recovery.py`：先尝试东方财富 `push2his` 历史日线（OHLCV+成交额），再尝试腾讯 `fqkline` 不复权日线（OHLCV，成交额可能缺失）。只接受日期精确匹配的响应，结果只写入 `data_root`，绝不修改通达信源目录。TDX 不可用且未指定股票时默认限制请求数量，避免在 EXE 中无界访问公开接口；需要补齐全市场时由调用方分批传入代码并记录每批回执。网络失败、停牌、未上市和接口无目标日期都保持 `missing`，不得把失败升级成完整。

压缩包中声明的市场资讯路由由 `scripts/news_sync.py` 统一落盘：东财 7×24、新浪滚动、财联社新版签名 v1、同花顺公开快讯四路分别保存原始响应哈希、请求 URL、记录数、错误和实际发布时间，汇总文件为 `news/<trade-date>/multi-source-news-*.json`。请求日期只是证据目录和目标日期，不能覆盖源记录的实际日期；只有实际发布时间匹配目标日的记录才计入 `sameDayRecordCount`。财联社旧 `/api/cache` 返回 404/HTML 时不算成功，当前使用包内注明的 `/v1/roll/get_roll_list` 本地签名适配器。

个股财务/股本补充可用 `scripts/supplemental_data_sync.py --date <trade-date> --codes <code-list>` 批量执行：新浪三表和腾讯股本写入 `evidence/supplemental/<trade-date>/<code>.<market>.json`，指数日线、龙虎榜、融资融券只写一份 `market.json`，所有文件由 `stock_summary` 与 `package-source-gap-report.json` 索引。920xxx 必须使用 BJ 市场命名；按需批次只能标记 `partial`，不能冒充全市场覆盖。

日线归档首次读取本地 `.day` 的全部可用历史，后续由 4319 桥接在每个交易日收盘后 16:30 检查 TDX 源目录，并在同一回执中执行 `daily_data_recovery.py`。若最新交易日超过 `status/tdx-daily-history.json` 的 `trade_date`，归档器按固定 32 字节记录定位并追加上次归档日之后的全部交易日（应用离线数日也不能漏掉中间日）；同日重复执行保持文件和哈希不变。读取 `archive_mode`、`incremental_from`、`incremental_records` 和 `incremental_trade_dates` 判断本次是否发生增量，不能用模型推测新增数据。TDX 步骤失败不应阻断公开缺口层，但最终状态必须是 `partial/degraded`，不能冒充主数据完整。周末与交易所闭市日由本地交易日历跳过，服务在 16:30 后启动时会先检查当天是否已经有归档。

数据补全只读取声明的连板网、东方财富涨停池与龙虎榜公开数据，并把来源、时间、哈希和原始字段保存为本地快照。3002 的历史公开快照已通过 `imported-3002/source-catalog.json` 接入 3003；使用前必须先核对其 `source_date`、`status`、`record_count` 与 SHA-256，不能把历史导入当成当前交易日。不得读取密钥或 Cookie，不得修改通达信源目录，不得使用模型推测补充缺失行情，也不得把降级结果写成全市场或正式生产结论。

仍然缺失或受限的包内来源必须持续列在缺口清单中：IWenCai 需要显式 API key；BaoStock 尚未作为运行时依赖配置；申万行业 PIT、巨潮/交易所官方、宏观历史快照、百度 K 线、同花顺一致预期以及公开网页动态采集没有稳定的无凭据本地适配器。它们可在 Harness 路由中声明待补，不得用当前报价、模型结果或历史导入替代。

每次统一落盘还会把可用数据源索引写入 `evidence/sources/<trade-date>/manifest.json`，
并将本地检查结果写入 `evidence/sources/<trade-date>/verification.json`。4319 桥接在每个交易日收盘后
16:30 运行同一条日线、公开行情、资讯、补充数据、来源清单和 Harness 校验链；周末与交易所闭市日跳过。
数据页的手动刷新与自动任务使用同一入口，不得另起一套日期或数据源逻辑。

每一种本地归档入口都必须生成 `harness/context/data-archive-<trade-date>.json`，并更新
`harness/context/latest-archive.json`、`harness/context/latest-data.json`；其中包含 `dataRoot`、
日线清单、日线索引、逐行完整性报告、公开行情、资讯、补充数据、统一来源清单、压缩包来源缺口、
步骤回执和 Harness 校验结果。`harness/context/data-archive-validation-<trade-date>.json` 是不可覆盖的
校验副本。Harness 必须优先读取这些归档上下文，不能只读取旧的 `latest-data.json`，也不能把
`imported-3002/` 的历史证据升级为当前行情。
