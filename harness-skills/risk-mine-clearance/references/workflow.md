# 风险排雷技能唯一工作流

1. 唯一外部入口是 `scripts/codex_entry.py`。
2. 统一执行器建立本轮目录，并把业务参数交给 `scripts/audit_risk_scan.py`。
3. 业务入口按当前上海日期运行全市场证据扫描：东方财富官方重大事项公告承担诉讼域，质押按最近工作日回退，个股新闻使用本地 JSONP 解析，互动易合法空集保持成功空表；再运行 `scripts/risk_warning_overlay.py`。
4. `scripts/validate_risk_run.py` 同时验证诉讼、质押、逐股新闻深挖及原关键来源域、候选、证据和市场风险文件；读回结果不是通过状态时阻断。
5. `scripts/poster_builder.py` 按 `POSTER_TEMPLATE.md` 生成8K浅色海报、1920×1080整图预览和版式元数据，再由 `scripts/poster_validator.py` 校验尺寸、背景、字号和缺字；任何一项失败均阻断。
6. 业务入口写入 `integrated_risk_summary.json`，统一执行层再写入业务结果和收据。
7. “风险预警”及旧显式调用只路由到本技能，不保留第二个技能目录、执行契约或业务入口。
8. 格式化报告是独立锁定阶段，必须通过统一入口的 `complete` 和 `authorize` 完成收据、文件哈希、清单和交付验证。
