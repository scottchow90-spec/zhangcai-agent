# A股量化生产定型工程 V6.5 WorkBuddy双路容灾最终生产版

## 安装
将整个技能目录交给 WorkBuddy。无需本地通达信。V6.5提供两条正式生产路径：原生四模型路径优先，独立双源共识容灾路径负责在全市场原始数据无法完整物化时继续完成生产任务。

## 首次验收
```bash
python scripts/workbuddy_entry.py verify
python scripts/workbuddy_entry.py selftest
python scripts/workbuddy_entry.py deep-audit
python scripts/workbuddy_entry.py offline-e2e
python scripts/workbuddy_entry.py doctor
python scripts/consensus_engine.py selftest
```

## 正式盘后
优先运行：
```bash
python scripts/workbuddy_entry.py execute --mode after-market
```
若出现 `DATA_BRIDGE_REQUIRED`，这是中间状态。WorkBuddy应先尝试构建完整 `workbuddy_data_bundle.zip` 并续跑。若全市场原生日K/行业桥仍无法满足原生路径，不得停止，必须切换 `CONSENSUS_RESCUE`：用真实主模型候选、与主源独立的第二行情源和事件风险信息构建 `consensus_bundle.json`，然后：
```bash
python scripts/consensus_engine.py execute --bundle consensus_bundle.json
```

## V6.5关键纠错
- 修复“文档320根、代码260根”的历史门口径漂移；原生模型按实际依赖实行120根核心/250根增强/260根请求。
- 不再让单一全市场长历史数据源失效导致整个任务死亡。
- 共识容灾路径必须逐只二源同日核价，禁止同源、模拟或生成数据。
- 容灾路径正式候选标记为 `B_CONSENSUS_PRODUCTION`，不会冒充V6.3四模型原生标签。
- 无合格股票时仍会阻断，不为了“出结果”伪造候选。
- ZIP统一UTF-8中文文件名，跨平台解压。

## 9月11日发布验收样例
包内 `evidence/2026-09-11_consensus_bundle.json` 与 `release_validation/2026-09-11/` 保存本版发布时真实双源实跑证据和受哈希保护的结果，可用于复核，不作为未来日期缓存替代。
