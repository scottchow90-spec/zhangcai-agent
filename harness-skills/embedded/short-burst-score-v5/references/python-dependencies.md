# Python依赖

- Python >=3.10；快照分析、包校验、历史CSV描述统计和报告仅用标准库。
- 原始盘后数据标准化、行业映射、特征和席位计算：pandas>=2.2、numpy>=1.24。代码使用include_groups参数，因此旧文档的pandas>=2.0不够。
- 完整selftest还需pytest>=7；缺失或执行失败必须返回非零。
- 真实Tushare下载另需tushare>=1.4.0和环境变量TUSHARE_TOKEN。接口权限、数据完整性和真实联机连接需使用者环境验证。
- 不调用集合竞价或分钟接口，不保存密钥到技能包。
