# 掌财智能体：14 技能电脑安装版 0.1.22

`main` 是正式电脑安装版主线，`web-test` 是网页测试分支。旧 3001/3002 网页保存在 `legacy-web-3001-3002`，旧 3003 和恢复过程保留原分支，未改写历史。

本仓库包含可修改的前后端源码、14 个原始技能 ZIP、10 个个股技能实现、Electron/NSIS 安装与更新脚本、公式种子、锁定依赖、原始 0.1.22 安装器和便携开发准备工具。大型二进制通过 Git LFS 获取，不能只下载 GitHub 的源码 ZIP。完整操作说明见 [DEVELOPMENT.md](DEVELOPMENT.md)。

正式安装版使用独立端口（优先 `34303` / `44319`）；网页测试使用 `3003` / `4319`，聊天测试页为 `3004`。不修改原 3002 / 4318 服务。

## 包含的技能

技能清单以 [config/skill14-catalog.json](config/skill14-catalog.json) 为唯一配置来源：个股综合分析、黄金起爆、连板晋级、龙头深度研究、短线统一评分、涨停复盘、短线爆发、情绪周期、量化生产、龙虎榜复盘、市场环境、数据能力大包、早盘计划与 WorkBuddy 演化，共 14 个导出的桌面技能包。

网页现在提供的是每个技能的本地数据预检与降级说明，而不是把未满足依赖的原始策略伪装成可执行的结论。

## 本地运行

```powershell
git lfs install
git lfs pull
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap-dev.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run verify:repository
# 两个终端分别启动桥接与网页，不需要这台电脑的 Codex 环境：
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run agent:dev
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run dev
```

开发命令统一通过 `scripts/pnpm.ps1` 使用仓库准备的 Node/Python/pnpm/Harness，不依赖 Scott 用户目录或 Codex 的运行环境。真实行情应设置 `ZHANGCAI_TDX_ROOT` 指向自己的通达信目录；模型密钥由使用者自行填写，缺少真实数据或凭据时保留阻塞状态。程序源码和开发工具可复现，不包含个人行情库、报告、密钥或保证逐字节相同的安装器重建。

修改源码后运行 `scripts/pnpm.ps1 run package:build:win:dir` 可生成并测试桌面程序；`package:build:win` 生成完整安装器，`package:build:win:update` 在当前程序构建上生成程序更新器。打包现在编译当前源码，不再复制历史 dist。

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
