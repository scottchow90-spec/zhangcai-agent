# 本机Codex调用工作流

唯一安装目录：F:\Codex\Home\skills\a-share-short-burst-score。股票目录/执行合同以stock-unified中的权威JSON为准，不另建路由。

所有操作使用本技能scripts/codex_entry.py run --，由stock_canonical_runtime.py调度。不可绕开入口调用workbuddy_entry.py或legacy入口。原引擎保留为适配器内部实现，评分逻辑与审计原包一致。

## 安装调试

python scripts/codex_entry.py run -- --action diagnose

该动作实际运行包校验与全部离线回归，包括原始数据审计→快照→评分命令行链路。仅标为SYNTHETIC_INTEGRATION_TEST；完成后用本次回执authorize --scope synthetic_test。不得把其当作真实行情报告。

## 真正业务

- 完整数据目录：run -- --action prepare-analyze --data-root <原始目录> --trade-date <YYYY-MM-DD> --as-of <带时区截止时间>
- 已有快照：run -- --action analyze --input <快照JSON>
- 历史标签研究：run -- --action research --events <标签CSV> --cutoff <截止日>
- 原始数据下载：run -- --action download --data-root <数据目录> --start <YYYYMMDD> --end <YYYYMMDD>

数据源要求、单位及时间规则见data-contract.md。下载默认复用本机通达信原始日线及现有公开龙虎榜入口，不要求TUSHARE_TOKEN。每次实际采集保留acquisition_manifest.json、原始来源和readiness.json；存在数据缺口时仍保留已取得的文件，明确缺项，不把单一供应商的凭据缺失当成本机没有数据。Tushare原适配器仅保留为可选内部组件。

输出在F:\Codex\Home\business_data\a-share-short-burst-score下，每次使用独立运行目录，不能污染技能代码。下载目标只能位于本次独立运行目录，可用相对目录raw-data；原始数据只读输入允许用户提供的外部目录。

原始行情必须有交易日历、日线、每日基础、复权、历史基础/ST、涨跌停价、龙虎榜主表与席位、行业历史成员；指数和事件缺失按原规则降级。默认T日候选来自龙虎榜，空榜返回空候选；明确名单通过 SHORT_BURST_FULL_SELECTED_REQUEST_V1 请求进入同一原始管线，先审计、再核验真实榜单。

业务结束核验本次回执。用户明确批准的年度历史参考指定名单模式已登记独立语义重放：再次审计实际原始输入，重建快照，逐字段复算全部评分与报告，并独立复验公告查询和已审核正文；只有上述核验通过且原始用户请求已绑定时，默认authorize --receipt才可授予该模式的workflow完成。其他模式仍最多以contract_execution授权，不能混用。历史CSV只作research_only，历史评分保持中性，核心候选仍关闭。

不要擅自关闭或重启Codex/通达信，不自动下单，不访问账户。所有安装测试都是测试数据，不表示策略已证明收益。

## 安装联调完成边界

诊断通过仅证明离线实现。下载动作必须真正调用本地/公开数据源，再执行原始数据覆盖审计；失败仍绑定已取得数据及readiness.json。下载通过也不代表评分链已完成，必须继续prepare-analyze并检查真实输入日期、覆盖及降级项。禁止以配置、承诺、模拟测试、归档替代真实联调结果；有现成数据入口未尝试时不得把取得外部密钥推给用户。

## 明确名单按完整原始管线执行

使用 analyze --input <请求JSON>，请求 schema 为 SHORT_BURST_FULL_SELECTED_REQUEST_V1，并包含 data_root、trade_date、as_of、stocks（code、name、screenshot_close）。可选 history_model 引用必须绑定实际文件。所有输入仍通过原始数据审计；失败保留请求及审计证据，禁止转用观察评分补数。审计通过才进入原 build_snapshot 与 analyze_snapshot，原配置权重保持不变。只有经独立核验通过的年度参考模式可取得对应工作流授权；历史收益生产资格边界不变。

用户明确授权的年度历史参考模式：在同一SHORT_BURST_FULL_SELECTED_REQUEST_V1中传market_reference {mode,input,sha256}、current_streaks {path,sha256,proof:{path,sha256}}、event_source_audit {path,sha256}。入口重验年度源与逐笔统计，标签和日常评分物理隔离；当日连板证据从真实封板名单连续回溯并核验T日真实限价；原始审计按此模式实际消耗的数据执行，原历史市场参考表不再作为未执行的前置要求。只作参考，不改六维计分公式。

独立核验不接受生产者自填完成标志。公告来源仅覆盖已明确查询的公司公告接口；未登记新文档解读、新历史模型及原120日默认模式不得沿用本模式授权。
