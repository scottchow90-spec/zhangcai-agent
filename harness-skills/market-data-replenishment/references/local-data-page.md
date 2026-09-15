# 掌财智能体本地数据落盘页

## 目的

这是 3003 网页版与未来 EXE 共用的本地数据契约。所有由网页、日线归档器、公开数据补齐器或 Harness 产生的数据，必须落在应用可写的 `data_root` 下。开发环境默认为 `app-data/`；打包后由 `ZHANGCAI_DATA_DIR` 指定每用户可写目录。不要把数据写回安装目录、通达信目录或仓库外的临时路径。

运行时索引：`harness/context/local-data-page.json`（`ZHANGCAI_LOCAL_DATA_PAGE_V1`）。状态总表：`status/current.json`。本页中的相对路径都相对于 `data_root`。

## 资产目录

| 资产 | 本地路径 | 用途与真值边界 |
| --- | --- | --- |
| `tdx_daily_history` | 以 `latest_tdx_archive.path` 为准；增量模式为 `market/daily/aggregate/tdx-bars.jsonl` | 通达信 `.day` 解码后的全部可用历史日线；历史策略、复盘和公式输入的主数据 |
| 日线清单 | `market/daily/<trade-date>/manifest.json`、`status/tdx-daily-history.json` | 同日覆盖数、归档记录数、源目录、时间、SHA-256、完整/降级状态 |
| `tdx_daily_index` | `market/daily/index/tdx-symbol-index.json` | 六位代码/市场到 TDX `.day` 的快速索引，含记录数和首尾日期 |
| `daily_data_index` | `market/daily/index/daily-data-index.json`、`market/daily/<trade-date>/daily-data-index.json` | TDX 主源与公开降级层的统一可用性、日期、记录数和字段缺失索引 |
| `tdx_daily_fallback` | `market/daily/fallback/<trade-date>/<symbol>.jsonl` | 通达信不可用或缺目标日时的公开 OHLCV 降级记录；不修改 TDX 目录，不冒充全历史 |
| `daily_jsonl_integrity` | `runtime/daily-jsonl-integrity-<trade-date>.json` | 逐行解析主 JSONL，校验必需字段、数值、记录数、标的数和日期覆盖 |
| `supplemental_market` | `evidence/supplemental/<trade-date>/market.json` | 指数日线、龙虎榜、融资融券市场快照；目标股票财务/股本在同目录按需落盘 |
| `security_master` | `market/security-master/<trade-date>.jsonl` | 代码、市场、名称、ST 标记、上市状态、行业/板块字段；未命名标的必须保持 `degraded` |
| `limit_up_pool` | `public/limit-up/<trade-date>.json` | 涨停池及连板公开原始快照，保留 provider、原始字段和来源时间 |
| `lhb_data` | `public/lhb/<trade-date>.json` | 龙虎榜公开原始快照，不得将空响应当作有数据 |
| `public_research` | `evidence/public/` | 新闻、公告、公开资讯证据；必须保留 `source_date`、抓取时间和来源哈希 |
| `tdx_tq_formula` | `evidence/formulas/` | TQ 公式现场执行回执；只有公式文件或注册表不代表公式已经现场执行 |
| `tdx_formula_source_archive` | `evidence/formulas/package/` | 可随 EXE 携带的公式注册表、`.tn6` 文件和 TQ 初始化脚本镜像；不直接替代现场执行 |
| `unified_source_manifest` | `evidence/sources/latest.json` | 所有已落盘数据、来源覆盖状态、压缩包来源映射和降级原因的统一索引 |
| `unified_source_verification` | `evidence/sources/latest-verification.json` | 最近一次本地文件/哈希校验结果；不通过时不得输出完整数据结论 |
| `package_source_inventory` | `harness/context/package-source-inventory.json` | 从行情能力压缩包整理出的 11 层、54 端点、网站和技能来源目录 |
| `execution_evidence` | `reports/daily/<trade-date>/` | 日线归档日报、14 技能预检、校验报告和其他可复核回执 |
| 市场网页快照 | `runtime/market-latest.json` | 由本地完整 TDX 日线生成的网页启动快照；只有完整本地股票集合才能替换发布基线 |
| 每日上下文 | `harness/context/latest-data.json`、`harness/context/daily-data-<date>.json` | 给 Harness 的日期、步骤、来源摘要和数据页引用 |
| 统一归档上下文 | `harness/context/latest-archive.json`、`harness/context/data-archive-<date>.json` | 所有本地数据源归档入口的统一 Harness 输入；包含路径、哈希、日期、索引、降级和步骤回执 |
| 归档校验回执 | `harness/context/data-archive-validation-<date>.json` | 对应一次归档的 Harness 校验结果；不能用历史 3002 上下文替代 |
| 任务回执 | `harness/jobs/<job-id>.json`、`harness/strategy-jobs/<job-id>.json` | 后台 Harness 与策略任务的启动、完成、失败和结构化输出 |
| 技能包清单 | `skills/manifest.json`、`skills/packages/<skill-id>/` | 14 个技能包的落盘副本及哈希；仅代表包已部署，不代表数据源已可用 |
| 3002 兼容数据 | `imported-3002/manifest.json`、`imported-3002/source-catalog.json` | 3002 的公开行情、新闻、每日上下文、运行状态和历史策略交付物；作为带日期的本地证据副本，不覆盖当前 TDX 真值 |

## Harness 读取顺序

1. 读取 `harness/context/latest-archive.json`；若不存在，再读取 `harness/context/latest-data.json`，确定最近一次归档日期、入口类型和归档状态。
2. 读取 `harness/context/local-data-page.json`，确定 `data_root` 与 `latest_tdx_trade_date`。
3. 读取 `status/current.json`，只将状态为 `available` 的必需资产作为可用输入；`degraded`、`blocked`、`missing` 必须传入降级原因。
4. 读取目标交易日的日线 `manifest.json`，再按需读取 `tdx-bars.jsonl`。同时核对 `history_scope`、`archive_mode`、`incremental_from`、`incremental_records` 和 `incremental_trade_dates`；默认 `history_scope=all_available_source_history`，`incremental_append` 表示只追加了 TDX 源中上次归档日之后的全部记录，`delta_file` 是本次新增记录，`file` 是可持续累积的聚合文件，`unchanged` 表示同日重复执行未改写文件。不要用 `runtime/market-latest.json` 的榜单子集冒充日线全量。
4. 先读 `market/daily/index/tdx-symbol-index.json` 定位主文件，再读 `market/daily/index/daily-data-index.json` 和 `runtime/daily-jsonl-integrity-<trade-date>.json`。若主文件不存在或不可读，按索引读取 `market/daily/fallback/<trade-date>/<symbol>.jsonl`；逐行核对 `date == target_date`、OHLCV、`source_date`、`status=degraded`、`source_sha256` 和 `missing_fields`，并在 Harness 结果标注 `quality=degraded`。
5. 读取 `public/`、`evidence/` 中对应日期的快照，核对来源日期和哈希；空响应只能记录为空或降级。
6. 读取 `evidence/sources/latest.json` 和对应交易日的 `manifest.json`，只使用状态为 `available` 且文件存在、日期一致的资产；`partial`、`declared_not_snapshotted`、`not_configured` 和 `blocked` 必须写入降级说明。
7. 若需要使用 3002 的其他信息源，先读 `imported-3002/source-catalog.json`，再读取其中映射的 `imported-3002/data/public/`、`imported-3002/data/news/`、`imported-3002/data/harness/context/` 或历史报告目录；必须保留其来源日期，不能直接当作当前日数据。
8. 把分析、预检和校验结果写入 `reports/daily/<trade-date>/` 或 `harness/jobs/`，保留输入日期、输入文件和 SHA-256；归档入口的 Harness 结果同时写入 `data-archive-validation-<trade-date>.json`。

## 与 14 个技能的关系

14 技能目录 `config/skill14-catalog.json` 是必需/可选资产的唯一声明。`tdx_daily_history`、`security_master`、`limit_up_pool`、`lhb_data`、`public_research`、`tdx_tq_formula`、`execution_evidence` 七类资产按该目录挂接到 14 个适配技能。原始 ZIP 中的源码、接口主机、示例或说明仅作研究参考；它们不能绕过本地数据门禁，也不能让 Harness 自动登录、读取凭据、修改 TDX 或执行交易。

## 日期、来源和降级规则

- 日线交易日以 TDX `.day` 文件中覆盖最多且达到门槛的最近日期为准，不以网页打开日期硬编码。当前页的实际日期以 `latest_tdx_trade_date` 为准。
- 每个快照应保留 `source` 或 `source_root`、`source_date`、`retrieved_at`/`fetchedAt`、`status`、`error`/`reason` 和 `sha256`；无法取得的字段留空并说明原因。
- 公开快照只能作为对应技能声明的辅助或降级数据；`public_daily_fallback` 可以补齐明确缺失的交易日 OHLCV，但不能替代 TDX 全历史或 TQ 现场公式证据。
- 公开日线优先使用东方财富历史 K 线，失败再用腾讯不复权 K 线；不保存密钥/Cookie。腾讯结果没有成交额时保留 `amount=null`，下游公式必须将其视为缺失而不是计算或填零。
- 3002 导入快照只作为历史/兼容证据；若与 3003 当前快照同日且记录更多，才可被同步到 canonical `public/latest.json` 或 `news/latest.json`，否则只从 `imported-3002/` 读取。
- 必需资产缺失时输出 `BLOCKED`；可选资产缺失时输出 `DEGRADED`；只有所有必需项现场可验证才可输出 `READY_FOR_VALIDATED_RUN`。
- Harness 的结论只能引用已传入且已核验的文件，不得把“包存在”“接口说明存在”“接口曾经成功”写成当前数据已可用。
