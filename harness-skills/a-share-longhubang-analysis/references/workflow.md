# 龙虎榜分析执行规范

## 标准分析

```powershell
python D:\C盘转移\日志\codex\skills\a-share-longhubang-analysis\scripts\codex_entry.py run -- --date 2026-08-14 --threshold-yuan 50000000
```

运行目录内生成 `longhubang-analysis.json`、`longhubang-analysis.md` 和 `delivery_manifest.json`。报告必须以“核心结论”开头，结构化结果必须含 `conclusions`，并覆盖资金集中度、主攻方向、席位风格、板块风格、持续性、触发风格和证据边界。

## 海报两阶段门槛

第一阶段生成候选和完整预览，候选不会写入交付目录：

```powershell
python D:\C盘转移\日志\codex\skills\a-share-longhubang-analysis\scripts\codex_entry.py run -- --date 2026-08-14 --poster-draft
```

逐张查看 `poster-preview/*.png` 的完整1080x608预览，先确认七类结论合计完整、每条判断有量化证据、每个游资归属有完整席位名称精确核对证据，再确认大字清晰、无裁切、无重叠、无缺字、亮色背景。任何“未识别”“其他主题”或模板式结论都必须返工，不得写入检查记录。查看后写入真实检查记录：

```powershell
python D:\C盘转移\日志\codex\skills\a-share-longhubang-analysis\scripts\poster_builder.py record-inspection --draft-manifest <poster-draft-manifest.json> --output <visual-inspection.json> --notes "完整预览逐页检查：文字清晰，无裁切、重叠和缺字，背景明亮。"
```

第二阶段使用同一数据输入重建确定性候选，以哈希核对检查记录，合格后才复制到 `artifacts`：

```powershell
python D:\C盘转移\日志\codex\skills\a-share-longhubang-analysis\scripts\codex_entry.py complete --artifact-relative artifacts/longhubang-01.png -- --date 2026-08-14 --poster-draft --inspection-json <visual-inspection.json>
```

两张海报必须分别执行工件授权；任一页不得遗漏股票，且不得生成第三张。

## 离线回归

离线夹具只用于测试和历史复现，不能冒充当前市场数据：

```powershell
python D:\C盘转移\日志\codex\skills\a-share-longhubang-analysis\scripts\codex_entry.py run -- --date 2026-08-14 --summary-fixture <summary.json> --details-fixture <details.json> --duanxianxia-fixture <dxx.json> --lianban-fixture <lianban-daily.json>
```

## 失败策略

- 东方财富汇总不可用：阻断，不能产生结论。
- 东方财富某股席位不可用：保留股票金额，席位写“席位数据缺失”，来源状态降级；有席位时必须扫描全部买卖席位并按完整规范化名称精确匹配。
- 东方财富某股精确概念不可用：阻断分析和海报，不得以宽泛行业、“其他主题”或占位词代替。
- 短线侠或连板网不可用：记录 `DEGRADED` 后继续，不得写成已验证。
- 结构化分析缺少结论、七类维度、量化证据、置信度或限制条件，或出现占位词/模板默认结论：阻断分析与海报，不允许仅交付数据表。
- 海报结论覆盖、结论哈希绑定、字号、尺寸、亮底、股票数量覆盖、完整预览或检查哈希任一失败：阻断海报交付。
