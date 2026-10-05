# 顶级智库观点验收清单

## 结构

- [ ] 封面有清晰标题、日期、核心判断。
- [ ] 正文包含美国智库信号、宏观财政、贸易产业、外交安全、科技竞争、能源资源或社会治理中的至少四条主线，并给出A股映射、情景推演、监测清单、来源边界。
- [ ] 核心判断逐条绑定当次事实，不能由脚本默认结论、默认行业行或兜底情景补齐。
- [ ] 不存在只有文字堆积的连续长段，表格和判断块能支撑快速阅读。

## 正文清洁

- [ ] 不出现编码、读取文件、截图、脚本、工具、路径、浏览器、登录、账号、密钥、令牌等过程内容。
- [ ] 不出现“本页把”“原生可编辑”“终版”“链接保留”等交付垃圾话术。
- [ ] 不出现英文智库名、英文缩写、英文栏目标题或可见 URL。
- [ ] “美国智库信号”和来源标题全部为中文。

## Word 质量

- [ ] DOCX 可以被 `python-docx` 打开。
- [ ] `word/media` 数量为 0。
- [ ] 表格数量不少于 5。
- [ ] 隐藏超链接不少于 6。
- [ ] 页数优先由本机 Word COM 真实排版统计；不可用时才降级到 PDF 或 OOXML，且每个分页段都有足够正文。

## 门禁命令

```powershell
python D:\C盘转移\日志\codex\skills\a-share-thinktank-brief\scripts\top_thinktank_brief.py selftest
python D:\C盘转移\日志\codex\skills\a-share-thinktank-brief\scripts\top_thinktank_brief.py doctor
python D:\C盘转移\日志\codex\skills\a-share-thinktank-brief\scripts\top_thinktank_brief.py scan-docx <docx_path>
```

全部应返回 `CLEAN_PASS`，否则不得交付。
