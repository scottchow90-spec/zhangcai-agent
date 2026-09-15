---
name: wechat-public-writing
description: 基于两家公众号200条公开索引记录与直接正文样本固化的公众号写作工作流。用于用户提出“公众号写作”“写公众号文章”“公众号复盘”“市场事件解读”“按已学习的逻辑和语言风格写作”或明确调用 $wechat-public-writing 时；通过固定入口生成写作简报、原创成稿并执行结构与风格验收。
---

# 公众号写作

## 固定执行路线

1. 读取 `references/style-playbook.md`；需要追溯样本时读取或检索 `references/source-corpus.json`。
2. 把用户需求写成请求 JSON，至少包含 `topic`；按需包含 `mode`、`audience`、`purpose`、`target_length`、`timeliness`、`facts` 和 `required_points`。
3. 必须运行唯一入口：

   ```powershell
   python scripts/codex_entry.py run -- prepare --request <request.json> --out <brief.json>
   ```

4. 读取生成的简报。若涉及当前行情、公司、政策、数据或新闻，先调用匹配的研究技能并核验新鲜来源；本技能不替代事实研究。
5. 按简报写原创 Markdown 文章。不得复制样本文句、固定口头禅、作者署名或可识别的人设表达，不得冒充原公众号作者。
6. 必须运行同一入口验收：

   ```powershell
   python scripts/codex_entry.py run -- validate --article <article.md> --brief <brief.json> --out <receipt.json>
   ```

7. 验收失败时修改同一篇文章并重跑，直至回执 `status=PASS`。只有 `run -- prepare` 成功、文章文件存在且 `run -- validate` 返回 PASS，才可声称使用了“公众号写作”技能。
8. 交付文章时同时报告写作模式、事实来源边界和验收回执。股票类文件仍必须遵守本机股票研究与首屏风险门禁。

## 请求格式

```json
{
  "topic": "今晚市场最值得关注的三条线索",
  "mode": "hybrid",
  "audience": "关注市场的普通投资者",
  "purpose": "盘后解读并给出次日观察条件",
  "target_length": 1200,
  "timeliness": "current",
  "facts": [
    {"claim": "已核验事实", "source": "来源链接或本地研究产物", "date": "YYYY-MM-DD"}
  ],
  "required_points": ["必须覆盖的要点"]
}
```

`mode` 只允许：

- `hybrid`：融合两家所学方法，默认使用。
- `behavioral-technical`：偏空间、时间、方向、阈值与条件分支。
- `event-market`：偏盘面快照、资金链条、消息清单与行业映射。

`timeliness` 使用 `current` 或 `evergreen`。`current` 文章必须有时间锚点和新鲜事实来源；`evergreen` 不强制“今晚/明天”等表达。

## 不可妥协规则

- 结论前置，再给证据链、条件分支、执行动作和失效风险。
- 区分事实、判断和情绪表达；没有来源的数字和事件不得写成事实。
- 使用短段落、数字锚点和自然口语，但控制夸张，不制造收益承诺。
- 保留原创作者声音，只学习抽象结构与语言特征，不进行逐句仿写。
- 不把读取本文件、生成空目录、复制语料或脚本退出码当作技能执行成功。

## 资源

- `references/style-playbook.md`：200条学习结果提炼出的写作逻辑、语言特征和组合骨架。
- `references/style-profiles.json`：固定入口读取的机器化风格规则。
- `references/source-corpus.json`：技能内部自包含的200条来源语料与分析快照。
- `references/provenance.json`：语料来源、数量、哈希和验证边界。
- `scripts/codex_entry.py`：统一门面仅公开 `info`、`selftest`、`run`、`verify`；业务动作 `inspect`、`prepare`、`validate` 必须放在 `run --` 后。

统一门面回执验证：

```powershell
python scripts/codex_entry.py verify --receipt <统一门面回执.json>
```
