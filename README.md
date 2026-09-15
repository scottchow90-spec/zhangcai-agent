# 掌财智能体：14 技能本地版（3003）

这是从原网页独立出的 14 技能工作台。原 3002 网页与 4318 桥接不在本工程的改动范围内；本工程使用 `127.0.0.1:3003` 前端和 `127.0.0.1:4319` 本地桥接。页面、技能包、行情文件、原始快照和报告均留在本机，为后续 Windows EXE 打包准备。

## 包含的技能

技能清单以 [config/skill14-catalog.json](config/skill14-catalog.json) 为唯一配置来源：个股综合分析、黄金起爆、连板晋级、龙头深度研究、短线统一评分、涨停复盘、短线爆发、情绪周期、量化生产、龙虎榜复盘、市场环境、数据能力大包、早盘计划与 WorkBuddy 演化，共 14 个导出的桌面技能包。

网页现在提供的是每个技能的本地数据预检与降级说明，而不是把未满足依赖的原始策略伪装成可执行的结论。

## 本地运行

```powershell
pnpm install
pnpm prepare:skill14     # 解压 14 个只读技能包到 app-data
pnpm data:archive        # 从通达信归档日线并写入每日数据报告
pnpm start:local         # 启动 4319 桥接与 3003 网页
```

也可分别运行 `pnpm agent:dev` 和 `pnpm dev`。运行时只监听回环地址，不向局域网暴露接口。开发环境默认从 `C:\new_tdx_mock` 读取通达信；可通过 `ZHANGCAI_TDX_ROOT` 改为实际安装目录。若系统没有 `python` 命令，运行器会使用 Codex 随附的 Python；EXE 应内置 Python 并设置 `ZHANGCAI_PYTHON`。

## 可迁移的数据目录

所有可变数据默认存放在 `app-data/`，不进入 Git，也不应放在 EXE 的只读安装目录。

| 目录 | 保存内容 |
| --- | --- |
| `market/daily/<交易日>/` | 通达信 `.day` 日线归档清单及当日 delta；完整历史聚合文件为 `market/daily/aggregate/tdx-bars.jsonl` |
| `market/security-master/` | 当前可推导的证券代码基础表 |
| `public/` | 涨停池、龙虎榜等公开来源的原始快照 |
| `evidence/` | 新闻、研究和执行证据的带时间戳快照 |
| `reports/daily/<交易日>/` | 数据归档日报、每个技能的预检 JSON 与 Markdown |
| `skills/packages/` | 14 个已解压的桌面技能包；保留原包内容以便审计 |
| `logs/` | 本地归档和桥接运行日志 |

`skill-archives/` 保存导入的 14 个 ZIP 原件及校验和；EXE 构建时可将其放在只读 resources 中。安装后的启动器应设置 `ZHANGCAI_DATA_DIR=%LOCALAPPDATA%\掌财智能体-14技能\app-data`，首次启动再将包解压至该可写目录。这样卸载或更新程序不会覆盖用户的日线、报告和证据。

## 数据降级规则

- 日线归档只读取通达信本地 `.day`，缺少日线时相应技能会被阻止运行，不会补造数据。
- 日线归档默认读取每个 TDX `.day` 文件的全部可用历史（可用 `--history-days` 显式限制窗口）；同日重复执行保持原文件和哈希不变；发现新交易日时保留旧目录，只把上次归档日之后的全部新记录追加到聚合文件，并在新交易日目录写入小型 delta，避免每天复制数 GB。自动计划由 4319 桥接进程在每个工作日 16:30（Asia/Shanghai）触发；如果通达信源目录尚未更新，应用不会伪造新日线。
- 代码表可由文件名推导，但无法可靠补齐历史名称、ST、停牌和退市字段，因此被明确标记为“降级”。
- 涨停池、龙虎榜、新闻与研究源是可选的本地快照；未落盘时预检会说明缺项并阻止依赖它的技能。
- 通达信公式仅验证本地文件/注册表存在，不能替代同花顺/通达信的实时公式执行环境。
- 每次预检将 `READY_FOR_VALIDATED_RUN`、`DEGRADED` 或 `BLOCKED` 连同缺失项和降级原因写进当日报告目录。

## 验证

```powershell
node --check agent-server.mjs
pnpm exec tsc --noEmit
pnpm build
```

启动后访问 `http://127.0.0.1:3003`。桥接健康及技能数据状态可由 `http://127.0.0.1:4319/skill14/status` 查看。
