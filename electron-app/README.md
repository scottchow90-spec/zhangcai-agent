# 掌财智能体桌面版

`electron-app` 是当前主程序的 Electron 打包入口；网页开发版仍沿用根目录的 3003、3004、4319，桌面版使用独立的 34303/44319 端口。

桌面版的运行时约定：

- UI 首选端口 `34303`，桥接首选端口 `44319`；如果被占用，会在隔离范围内自动寻找空闲端口。
- 永不使用网页测试端口 `3003`、`3004`、`4319`。
- 桥接启动后必须通过 `health.appRoot`、`health.dataRoot` 和 `health.resourceLibrary` 身份校验，不能误连到已有网页服务。
- 首页和 `/chat` 使用同一个打包后的 Vinext 进程；桌面壳层增加首页、聊天、同步行情、打开通达信、运行环境按钮。
- Electron 默认持久化会话存储；最后访问的首页/聊天页另存为 `<EXE安装目录>\\data\\resource-library\\desktop\\last-page.json`。
- EXE 默认把运行数据、Harness 回执、报告和日志写入 `<EXE安装目录>\\data\\resource-library`；程序代码和私有 Node/Python/Harness 运行时固定在同一个主安装包的 `resources` 中。这样安装到 D 盘时，持久化数据也跟随 D 盘；NSIS 临时目录仍可能短暂使用系统临时空间，但不会作为长期数据目录。
- 安装器先让用户选择 EXE 安装目录，再让用户选择通达信目录；有效路径写入 `HKCU\\Software\\Zhangcai\\Agent4319\\TDXRoot`，并由 EXE 同步记录到资源库 `desktop/tdx-config.json`。桌面端“运行环境”面板可再次选择目录，保存后自动重启专属桥接。
- 当前 0.1.22 是白板电脑一体化安装：不需要先安装运行环境包。主安装包内置 Electron、私有 Node 24.19.0、Python 3.12.14、Vinext 生产依赖和 DeepSeek Harness 0.1.2-rc.1；安装器只检查 Windows 10/11、x64、`reg.exe`、Windows PowerShell 和通达信目录，不把客户机的全局 Node/Python/pnpm 卸载或覆盖。已经存在同一掌财私有目录时会由主安装包复用/覆盖自己的副本；后续程序更新包继续复用该运行环境，不重建它。通达信不随包分发，空目录或无效目录会打开 `https://data.tdx.com.cn/mock/new_tdx_mock.exe` 并停止主程序安装。
- Harness 密钥不打进安装包。桌面版点击“运行环境”，在未配置 Harness 时输入用户自己的 DeepSeek API 密钥；密钥只写入当前用户资源库的 `.env.local`，状态面板只显示是否配置和脱敏提示。
- `resources/zhangcai-icon.ico` 是 EXE 应用图标，保持不变；网页壳层“掌财桌面端”文字左侧的 UI 图标单独由 `public/zhangcai-icon.png` 提供。
- 发布分层：当前主安装器同时安装 Electron 外壳、页面、桥接、技能、内置公式种子和 `resources/runtime`、`resources/deepseek-harness`、`resources/app/node_modules`；后续程序更新包只替换程序层，环境层与 `data/resource-library` 均保留。
- 环境层由 `scripts/stage-desktop-runtime.ps1` 生成并写入 `resources/runtime/environment-manifest.json`。0.1.9 因修复 YAML 运行依赖裁剪问题重建一次环境基线，0.1.12 只更新程序和界面；0.1.22 程序更新继续复用 0.1.9 运行环境；之后仍作为构建缓存而不是第二个安装前置条件。程序更新包通过 `scripts/package-program-update.ps1` 构建，安装时校验现有一体化主程序的环境层。

完整数据 EXE 验证（不会把约 10GB 本地数据加入正式安装包）：

```powershell
pnpm package:build:win:dir
pnpm prepare:desktop-exe-data
pnpm verify:desktop-exe:data
```

`prepare:desktop-exe-data` 会把项目 `app-data` 全量复制到 `dist-installer\\win-unpacked\\resources\\resource-library`，`verify:desktop-exe:data` 会让 EXE 直接以这份副本作为数据根，验证首页、聊天页、动态专属桥接、资源库身份、关键全量数据文件和 Harness 凭据状态。正式 NSIS 包仍然不包含这份数据副本。

目录版构建：

```powershell
pnpm package:build:win:dir
```

生成的可执行目录位于 `dist-installer\\win-unpacked`。运行 `掌财桌面端.exe` 时必须保留同目录下的 `resources` 文件夹。

当前主程序一体化构建：

```powershell
pnpm package:build:win
pnpm package:build:win:update
```

当前发布目录的正常使用顺序是：

```text
掌财桌面端-<version>-x64.exe
掌财桌面端-程序更新-<version>-x64.exe
```

0.1.6/0.1.8/0.1.9/0.1.10/0.1.11 的运行环境相关产物保留为历史兼容版本，不参与 0.1.22 白板机安装流程；0.1.22 主安装包复用并内置已修复的运行环境。
