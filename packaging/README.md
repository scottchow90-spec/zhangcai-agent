# 掌财桌面端 Windows EXE 打包准备

这组文件是 4319 当前版本的打包准备基线。0.1.7 恢复为“一体化主安装包 + 程序更新包 + 独立数据包”结构：
白板电脑只需运行主安装包；主安装包直接包含已验证的私有运行环境。运行环境 staging 继续作为可复用构建缓存，后续程序更新不重新构建或覆盖它。

## 主程序封装硬规则

从当前版本起，主程序安装包采用“绕过独立数据包”的封装边界，规则写在
`packaging/main-installer-policy.json`，并由
`scripts/package-preflight.ps1 -MainInstaller` 在构建前阻断违规输入：

- 主程序构建不会读取、扫描、合并或要求 `dist-installer` 下的独立数据包，也不把 `app-data` 的行情归档、公开快照、报告归档或原始 `.lc5` 作为主安装包输入。
- 主程序仍然包含小型公式种子 `electron-app/resource-library`，用于首次启动时初始化代码可读的公式资源；构建时可以从 `app-data/evidence/formulas/package` 更新这一个种子，但不读取其中的行情、报告或公开数据，也不等于携带历史行情数据包。
- 已验证的基线运行环境与主程序一起封装：私有 Node.js、Python、DeepSeek Harness、裁剪后的 Vinext/前端生产依赖、运行时清单和端口隔离配置都进入主安装包。
- 程序更新包只更新页面、桥接、技能和公式种子，复用并保留主程序已经安装的基线运行环境及用户资源库。
- 独立数据包只允许作为主程序安装完成后的可选增量导入，目标固定为 `<掌财桌面端安装目录>\\data\\resource-library`，不得成为主程序构建前置条件。

因此，后续只更新页面或桥接代码时可以复用已验证的 `packaging/staging/desktop-runtime`；只有 Node.js、Python、Harness 或其生产依赖的基线版本/内容变化时，才需要重建环境层。

## 目标运行结构

```text
掌财桌面端.exe
  ├─ Electron 主进程
  │    ├─ 启动 34303 生产前端
  │    ├─ 载入 / 主工作台
  │    ├─ 载入 /chat 研究聊天页（3004 页面实现）
  │    └─ 启动和回收 44319 专属本地桥接
  └─ 44319 技能、脚本和数据适配层（不含市场数据包）
```

当前主安装包一次写入同一安装目录：

```text
主安装包
  ├─ 掌财桌面端.exe 与 Electron 外壳
  ├─ resources/app.asar
  ├─ resources/app 与 resources/app/node_modules
  ├─ resources/runtime/node/node.exe
  ├─ resources/runtime/python/
  ├─ resources/runtime/environment-manifest.json
  ├─ resources/runtime/environment-version.ini
  ├─ resources/deepseek-harness/
  ├─ resources/app/node_modules/
  └─ resources/resource-library（公式种子）
```

0.1.6 历史环境包仍可留档，但不再作为 0.1.7 主程序的安装前置条件。

正式安装目录中的程序层和环境层只由安装器管理；运行数据写入：

```text
<所选 EXE 安装目录>\data\resource-library
```

安装器先允许用户选择 EXE 安装目录，再要求选择通达信目录；有效路径写入
`HKCU\\Software\\Zhangcai\\Agent4319\\TDXRoot`。如果留空或目录无效，安装器会打开
`https://data.tdx.com.cn/mock/new_tdx_mock.exe` 并终止安装。通达信不随安装包分发。
程序只读检测 `vipdoc`、`T0002`、公式文件和 TQ/Python 环境，并根据检测结果显示
可用、降级或阻断。

## 当前技术栈

- 桌面外壳：Electron 44.4.1
- Windows 安装器：electron-builder 26.15.3 + NSIS
- 页面：当前 Vinext 1.0.0-beta.5、React 19.2.6、Vite 8.0.13
- 页面整合：34303 `/` + `/chat`，推荐单前端进程；3003/3004 仅供网页测试版使用
- 本地服务：Node.js `agent-server.mjs`，桌面版监听 `127.0.0.1:44319`；4319 不参与桌面启动
- 本地计算：程序内 Python 3.12.14
- 前端生产依赖：由 `scripts/stage-desktop-runtime.ps1` 从 `packaging/runtime-node-modules` 裁剪后随主安装包分发，不携带开发工具链
- Harness：`@deepseek-ai/dsh@0.1.2-rc.1`，生产依赖随主安装包放入 `resources/deepseek-harness`
- 安装环境：主安装包检查 x64 Windows 10/11、`reg.exe`、Windows PowerShell 和通达信目录；运行环境 staging 已验证并直接嵌入主安装包，不安装或卸载客户机全局运行时。
- 数据：TDX 本地日线/公式作为用户外部依赖，归档、回执和报告写入用户数据目录
- 数据更新：本地 TDX 优先；公开行情、新闻、日线缺口和其他来源保留为明确的按需下载入口，下载结果先落到资源库并保留来源、日期和哈希，再供 Harness 使用
- 自动计划：每个交易日 `16:30`（Asia/Shanghai）执行 TDX 日线补齐、公开行情与资讯同步、统一落盘和 Harness 校验；TDX 不可用时进入公开源降级层
- 密钥：不进入 EXE，首次启动通过安全配置注入 `DEEPSEEK_API_KEY`

## 发布层和精简规则

主安装器包含以下不可缺少的环境层：

```text
掌财桌面端安装目录\resources
  ├─ runtime\                         # 私有 Node/Python 和 environment-manifest.json
  ├─ deepseek-harness\                # 固定 0.1.2-rc.1 Harness 及生产依赖
  └─ app\node_modules\                # 裁剪后的 Vinext/页面生产依赖
```

主安装器另外写入 Electron 外壳、`app.asar`、`app`、公式种子以及上面的环境层；它不会因为目标目录此前没有运行环境而阻断。

构建时只从运行时依赖中移除不会参与启动的文件：源码映射、TypeScript 类型和源码、README/许可证、测试/示例、包管理缓存、Python 开发头文件、静态库、Tcl/Tk、pip/setuptools/wheel 和字节码缓存。Vinext 依赖包内部的运行时目录会保留；Harness 的运行依赖会单独映射，避免被 electron-builder 的根 `node_modules` 默认排除规则误删。

本轮审计数据：0.1.4 目录包约 72,560 个文件、1.48 GiB；0.1.5 精简目录包约 38,280 个文件、1.266 GiB。文件数减少约 47%，页面、Harness、公式和数据路径不变。

环境层暂存由 `scripts/stage-desktop-runtime.ps1` 生成，并输出 `manifest.json`。它是构建缓存/环境基线，不是用户数据；不同版本应复用已验证的环境层，只有 Node/Python/Harness 版本或运行依赖真的变化时才重建。

后续程序版本使用：

```powershell
pnpm run package:build:win:dir
pnpm run package:build:win:update
```

首次构建当前版本使用：

```powershell
pnpm run package:build:win
```

`package:build:win` 会先运行 `stage-desktop-runtime.ps1`；只要
`packaging/environment-baseline-version.txt` 和现有 staging 的基线一致，脚本只更新清单版本并复用原文件，不重新构建运行环境。

更新包安装前会检查目标目录是否已有 Electron、私有 Node、私有 Python、DeepSeek Harness 和 Vinext；检查不通过会停止，不会把程序更新包误安装到白板电脑。更新包只写入 `resources/app.asar`、`resources/app`（不含 `node_modules`）和内置公式种子，不删除或覆盖 `data\resource-library`。

## 当前发布前阻断

1. 需要在干净 Windows 环境启动主程序，执行真实 Harness 任务和一条本地策略回执。
2. 需要确认 DeepSeek Harness 运行时的再分发许可和固定版本。
3. 需要用真实通达信安装目录跑一次安装器页面和 TDX 数据源检查。

主安装器明确不包含完整 `app-data` 或原始 `.lc5`。主程序只创建可写的资源根：
`<所选 EXE 安装目录>\\data\\resource-library`；公开补充快照和后续数据包只能写入该资源根，不能覆盖主程序文件。NSIS 安装阶段可能短暂使用系统临时目录，但该目录不承载长期数据。

## 独立日线数据包

`pnpm run package:data` 会在 `dist-installer\\data-pack-0.1.0` 生成独立数据目录。它只保留最新已核验交易日的 canonical 日线主库、索引、最新元数据、公开降级日线、公式包证据和完整性回执；旧交易日重复的全量 JSONL 不复制，原始 `.lc5`、程序代码、运行时和凭据也不复制。数据包根目录的 `manifest.json` 记录交易日、字节数、canonical SHA-256 和导入规则，`icon.png` 使用数据包专用图标。

生成数据包 Windows 安装器：

```powershell
pnpm run package:data:installer
```

产物为 `dist-installer\\掌财桌面端-日线数据包-0.1.0-x64.exe`，它把已压缩的数据载荷和 7za 解压器一并内嵌，安装器使用数据包专用红底白色 Logo；运行时必须选择已安装的掌财桌面端目录，安装器会校验客户端 EXE 和 Electron `resources\\app.asar`（或 `resources\\app\\package.json`），然后把载荷中的
`market`、`status`、`evidence`、`runtime` 四个目录解压到该客户端实际使用的
`<所选 EXE 安装目录>\\data\\resource-library`。选择的客户端目录会写入客户端注册表记录，便于确认数据归属；数据落盘位置就是该客户端目录下的 `data` 子目录。
数据包根目录的发布清单、图标和说明不会复制到资源库，也不会覆盖资源库根目录 `manifest.json`、主程序、Harness 或运行时。

数据包安装器由用户选择掌财客户端安装目录进行校验，但固定落到客户端使用的
`<所选 EXE 安装目录>\\data\\resource-library`；手工导入时也使用该路径。导入时只合并数据文件，禁止覆盖
`resources\\app`、`resources\\deepseek-harness` 和 `resources\\runtime`。

## 运行预检

在 `zhangcai-web-3003` 目录执行：

```powershell
pnpm run package:preflight
```

该命令默认按主程序封装边界执行，明确跳过独立数据包输入。独立数据包由
`pnpm run package:data` 和 `pnpm run package:data:installer` 单独处理，不会被主程序构建脚本调用。

正式构建前执行：

```powershell
pnpm run package:build:win
```

正式构建命令会要求 Harness 已经放入预定目录；在该条件满足前不会生成“看似完整但缺 Harness”的安装包。
