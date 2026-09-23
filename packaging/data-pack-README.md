# 掌财桌面端独立日线数据包

本目录是掌财桌面端的独立日线数据包，发布时同时生成对应的 Windows NSIS 安装器
`掌财桌面端-日线数据包-0.1.0-x64.exe`。它包含当前已核验的最新交易日日线主库、TDX 股票索引、按股票定位的全历史索引、元数据、公开降级日线和公式证据；原始 `.lc5` 分钟线、DeepSeek 密钥、程序代码和 Node/Python/Harness 运行时不在这里。

本数据包是主程序安装完成后的可选增量导入，不是主程序安装包的构建输入。主程序安装器不会读取、合并或等待本目录；主程序已经把基线 Node.js、Python、DeepSeek Harness、页面生产依赖和公式种子一起封装。数据包只能写入客户端的可写资源库，不能替代主程序或运行环境。

优先运行 Windows 安装器。载荷已经内嵌在
`掌财桌面端-日线数据包-0.1.0-x64.exe` 中，不需要另带 `.7z` 文件；安装器会要求选择已安装的掌财桌面端目录，校验其中存在
桌面端 EXE 以及 `resources\\app.asar`（或 `resources\\app\\package.json`），然后把数据写入该客户端实际使用的可写资源库。

## 导入位置

将本目录中的数据文件合并到：

`<掌财桌面端安装目录>\data\resource-library`

数据安装器选择的客户端目录用于确认“这份数据属于哪个掌财桌面端”，并记录到
`HKCU\Software\Zhangcai\Agent4319`；实际数据目标是该目录下的 `data\resource-library`。这样不会把运行时数据写进
Electron 的只读 `resources\app`，安装到 D 盘时也不会把长期数据悄悄写到 C 盘。

如果使用资源管理器导入，请只合并 `market`、`status`、`evidence`、`public`、`runtime` 五个数据目录。数据包根目录的 `manifest.json`、`icon.png` 和 `README.md` 是发布说明文件，不要复制它们去覆盖资源库根目录的同名文件；也不要覆盖 EXE 安装目录下的 `resources\app`、`resources\deepseek-harness` 或 `resources\runtime`。安装器也不会修改通达信源目录。

`manifest.json` 是本数据包的校验清单，记录最新交易日、canonical 日线 SHA-256、文件数、字节数和排除项；`icon.png` 是数据包图标。

数据包采用“一个 canonical 全历史主库 + 按股票字节范围定位索引 + 小型元数据/降级层”结构，不复制旧交易日的重复全量 JSONL。安装后点击桌面端“初始化并重建全量索引”可以按当前通达信目录强制复核并重建两类索引；分钟数据仍由通达信目录按需读取。
