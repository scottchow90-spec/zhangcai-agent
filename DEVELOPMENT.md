# 在另一台电脑完整开发与修改

正式基线：14 技能 Windows x64 电脑安装版 0.1.22；环境基线 0.1.9。此文档只整理源码与开发交付，不增加历史报告归档功能。

## 分支和内容

| 分支 | 用途 |
| --- | --- |
| main | 正式电脑安装版；新电脑默认克隆此分支 |
| web-test | 同一源码的网页测试线；实验修改在此提交，通过后合并回 main |
| legacy-web-3001-3002 | 旧主网页保留快照；3001 和 3002 为同一版本迁移端口 |
| web-3003-14-skill-adapters | 原 3003 上传基线，历史保留 |
| recovery-0.1.22 | 2026-10-01 至 10-05 恢复证据与精确历史 dist，历史保留 |

main 和 web-test 初始化为同一提交，不人为删去桌面源码；二者通过分支及运行命令区分用途。保留旧分支而非改写 Git 历史。

## 1. 新电脑准备

需要 Windows 10/11 x64、Git for Windows（含 Git LFS）、网络与可写磁盘。首次准备约需数 GB 空间。依赖安装和 Electron/NSIS 下载需要访问 npm registry 与 GitHub；Python 开发测试 wheel 已随仓库提供，不需要访问 PyPI。不是完全离线安装。无需安装 Codex，也无需手动配置 Node、Python、pnpm 或 Harness。

```powershell
git lfs install
git clone --branch main https://github.com/scottchow90-spec/zhangcai-agent.git
cd zhangcai-agent
git lfs pull
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap-dev.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run verify:repository
```

不要使用 GitHub 的 Download ZIP 代替 clone + LFS。Git 普通提交保存大型文件指针，LFS 保存真正文件；缺少 LFS 对象会在大小/SHA-256 门禁被阻止。bootstrap 校验 0.1.22 原安装器和工具包，从安装器中**解压**自带的 Node/Python/Harness/生产依赖（不执行安装器），然后按 pnpm-lock.yaml 安装开发依赖。工具链锁定：Node 24.19.0、Python 3.12.14、pnpm 11.19.0、Harness 0.1.2-rc.1。第三方许可证随工具包保留。

已准备的环境可重复运行 bootstrap；不匹配或不完整的既存运行环境会阻止覆盖，应保留原目录并用独立干净 checkout 重新准备。`-SkipInstall` 只准备运行环境，不能替代完整依赖安装。

如需验证完全不复用本机 npm 缓存，在没有 node_modules 的新 checkout 第一次运行 bootstrap 时加 `-FreshDependencyStore`；该参数将开发依赖下载到项目私有缓存，不适用于已准备过依赖的目录。

## 2. 运行、编辑和检查

复制 `.env.example` 为本机 `.env.local` 并填入自己的模型凭据；或使用桌面界面的凭据设置。真实业务研究需要自己的通达信安装和完整日线等数据。可以在启动前设置：

```powershell
$env:ZHANGCAI_TDX_ROOT = 'D:\your-tdx'
```

不配置凭据/行情仍可检查界面、代码和离线技能加载，但不会获得真实研究报告。缺数据时显示 BLOCKED/降级，不能把演示 seed 当作真实行情。

网页测试建议先 `git switch web-test`。在两个终端中分别执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run agent:dev
# 另一个终端：
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run dev
# 可选聊天前端（第三个终端）：
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run dev:chat
```

网页入口 http://127.0.0.1:3003/ ，桥接 http://127.0.0.1:4319/health ，聊天测试 http://127.0.0.1:3004/chat 。不要在另一份 checkout 占用这些端口时启动。电脑安装版由 Electron 自行选择隔离端口，优先 34303/44319。

编辑入口：`app/` 为界面；`agent-server.mjs` 为本地 API/任务调度；`scripts/` 为数据适配与工具；`harness-skills/` 为可修改技能实现；`config/skill14-catalog.json` 为 14 技能目录；`skill-archives/` 为原始技能包；`electron-app/` 为桌面主进程、安装与资源配置。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run verify:repository
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 exec tsc --noEmit
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run verify:desktop-ports
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run verify:tdx-paths
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run verify:skill14-packaged
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run verify:stock-detail-discovery
```

`verify:repository --original-release` 的前端原字节校验只用于交付基线，不适用于已经修改的源码或不同 Git 换行策略。普通 verify:repository 检查构建输入存在和二进制/技能原包哈希。

Python 开发测试依赖由 requirements-dev.txt 固定；原始 wheel 及 SHA-256 锁文件一并提交，bootstrap 从仓库离线安装这些 wheel，不依赖本机代理或 PyPI。执行 `scripts/pnpm.ps1 run verify:portable-tests` 验证当前开发交付。运行时业务依赖随原始环境提取，requirements-data.txt 中的可选行情扩展不是启动前提。

整个旧 stock-unified 回归套件**尚未全绿**：还包括旧 Codex 全局 AGENTS/报告验证器约定、已过期的 source-manifest 和旧目录结构断言。这些问题在代码检查记录中单独列出，未删除测试、未关闭业务门禁，也不冒充真实行情/模型验收通过。完整历史套件可用 `.runtime/python/python.exe -B -m pytest harness-skills/stock-unified/tests` 重现。

## 3. 从修改后的源码打包

```powershell
# 构建可执行目录并进行不调用模型的桌面冒烟检查
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run package:build:win:dir
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run verify:desktop-exe
# 完整安装器
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run package:build:win
# 基于当前 win-unpacked 构建程序更新器，复用目标电脑已安装的环境层
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pnpm.ps1 run package:build:win:update
```

输出为 `dist-installer/releases/<package.json版本>/`。`stage-desktop-frontend.mjs` 在隔离源码目录构建当前前端，记录源码哈希和构建来源；源码变化会重新构建，不复用旧网页 dist。完整安装器内置运行环境、14 原始技能 ZIP、可运行技能与公式种子，不依赖额外个人数据包。

发布目录不可覆盖：重新发布前提升 package.json 中的产品版本并提交；不要修改 environment-baseline-version.txt，除非明确升级环境层。同一版本已有安装器或 win-unpacked 时会拒绝覆写。完整安装器构建后会准备 electron-builder 的 NSIS/7zip 缓存，更新器再使用该缓存；新电脑请按上述顺序构建。新版本前端映射和默认输出使用 `${version}`，不需要手动改成旧的 0.1.22 路径。

`release-assets/0.1.22/` 中两个 EXE 是本机原有 0.1.22 成品，非本次重建；SHA-256/大小及原始前端来源见 `development-assets/manifest.json`。原始 TSX 来自当时保留的 site-work-0.1.22，而非从压缩 bundle 猜测反编译。构建时间、平台路径和工具缓存可能改变生成物，不承诺新安装器与旧安装器逐字节一致。

## 4. 保存修改

```powershell
git switch web-test
# 修改并完成上述检查后：
git status --short
git add <明确修改的源码路径>
git commit -m "Describe your tested change"
git push origin web-test
# 经检查后将 web-test 合并到 main 再推送；不要强制覆盖 main。
```

Git 跟踪源码、配置、测试、文档、技能原件和锁定工具资产。`.runtime/`、`node_modules/`、`packaging/staging/`、dist、缓存、日志、历史报告和本机数据不在 main 的当前源码树。整理只取消它们的 Git 跟踪，本机原文件与旧分支快照保留。

个人通达信行情、DeepSeek 密钥、用户报告不应上传 GitHub；如需跨机转移用户数据，请另做私有备份。此处“完整复现”指项目开发/修改/构建闭环，不代表可从仓库凭空恢复个人行情和账户权限。
