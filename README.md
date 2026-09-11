# 掌财智能体独立运行时

这是“掌财智能体”的 Windows 本地应用工程。页面、行情同步、通达信读取、技能包和 DeepSeek Harness 桥接都在本地运行；运行时不需要 Codex、网页托管服务或浏览器扩展。

## 本地运行

```powershell
pnpm install
pnpm prepare:runtime
$env:DEEPSEEK_API_KEY = '你的 DeepSeek Key'
$env:ZHANGCAI_PYTHON = 'C:\\掌财智能体\\runtime\\python\\python.exe' # 开发时也可指向本机 Python
pnpm agent:dev
pnpm dev
```

Windows 本地调试也可以直接运行 `powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1`，启动器会固定前端到 `127.0.0.1:3001`，并拉起 4318 桥接服务。

浏览器访问开发服务地址。正式 EXE 的启动器将设置相同的运行时路径，并在后台拉起本地桥接服务；密钥只保存在系统环境变量或安装器的受保护配置中，绝不会写入网页文件。

## 每日首次打开更新

首页首次加载会请求本机桥接的 `POST /data/daily/start`，请求立即返回，页面可继续使用。每个自然日只运行一次，流程为：

1. 读取通达信客户端状态，并补齐本地日线。
2. 拉取需要展示的公开市场摘要。
3. 拉取东方财富 7×24 快讯，保存原始记录、请求参数、时间戳与内容哈希。
4. 将上述快照和执行状态写入本地数据目录。
5. DeepSeek Harness 读取当天上下文，输出严格 JSON 的来源、日期、条数、哈希和缺失项校验报告。

更新状态由 `GET /data/daily/status` 提供。某一步失败会保留已完成的快照和明确的失败原因，报告不会把缺失数据补写为模型结论。

桥接服务运行期间，会在每个工作日 16:50（Asia/Shanghai）静默执行同一流程。计划配置与下一次执行时间保存在 `data/harness/schedules/after-close-daily-refresh.json`；执行后由 DeepSeek Harness 生成并保存同日数据校验上下文。

## 本地目录与 EXE 打包

运行时路径均可由环境变量覆盖，因此安装后不会依赖开发工作区：

| 项目 | 默认位置 | EXE 中的用途 |
| --- | --- | --- |
| 程序根目录 | 当前安装目录 | 前端、桥接和同步脚本 |
| `harness-skills/` | 程序根目录 | 53 个随安装包复制的技能 |
| `data/` | 程序根目录 | 用户本地行情、新闻、报告、Harness 上下文和任务记录；安装器应改为 `%LOCALAPPDATA%\\掌财智能体\\data` |
| 通达信目录 | `C:\\new_tdx_mock` | 已安装通达信的日线、板块和公式文件 |
| Python | 系统 `python` | 正式包应内置 Python，并设置 `ZHANGCAI_PYTHON` |
| DeepSeek Harness | 本机 Node 运行时 | 正式包随程序安装或作为安装前置项提供 |

支持的变量为 `ZHANGCAI_APP_ROOT`、`ZHANGCAI_DATA_DIR`、`ZHANGCAI_SKILLS_DIR`、`ZHANGCAI_TDX_ROOT`、`ZHANGCAI_PYTHON`、`DEEPSEEK_API_KEY` 和 `DSH_BRIDGE_PORT`。`pnpm prepare:runtime` 只在构建阶段从迁移包复制技能；最终应用启动时只读取自己的 `harness-skills/`。

## 数据与报告

`lib/market.json` 是初始行情快照。运行时数据写入 `data/public/`、`data/news/`、`data/runtime/` 和 `data/harness/`；用户生成的报告写入应用自己的持久化存储。Harness 的输出被限制为 JSON，再由网页统一排版成文字段落、表格与图表，不直接把原始模型文本展示给用户。

公开行情快照优先使用连板网与东方财富 HTTP 源，并带有东方财富 `Referer`。若运行时安装 `requirements-data.txt` 中的 AkShare 1.18.60，会自动追加龙虎榜总览、Sina 龙虎榜、龙虎榜统计和涨停池原始记录；未安装时内置 HTTP 源仍可用，快照会明确标记 AkShare 为 unavailable。

## 验证

```powershell
node --check agent-server.mjs
pnpm build
```
