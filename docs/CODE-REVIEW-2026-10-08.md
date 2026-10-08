# Windows 开发交付检查记录

基线：电脑安装版 0.1.22，运行环境 0.1.9；仓库整理日期 2026-10-08。旧报告归档需求未作为此次实现范围。

## 源码完整性

- 从本机原全量安装器核对 resources/app 中 agent-server、scripts、harness-skills、config、lib：共 1,152 个文件，仓库无缺失文件。
- 去除换行差异后，只发现本次维护的 5 个打包/预检/冒烟/进程清理脚本不同；业务源代码与原安装器一致。
- 从当时保留的 site-work-0.1.22 找回 8 个 TSX 和 globals.css，9 个文件通过原始 SHA-256 核验；不是猜测反编译源码。
- 117 个已存在源文件曾受 Git CRLF 转换影响，恢复到安装器中的原字节，并通过 gitattributes 保持跨电脑源码字节。没有刷新旧 source-manifest 来掩盖真实漂移。
- 14 个原始 ZIP、原安装器、程序更新器、Node/Python/Harness 开发准备输入与测试 wheel 已列入哈希清单。用户行情、报告与凭据不作为开发源码输入。

首次独立远端克隆发现 app/layout.tsx 最后一个混合换行尚未按原字节进入 Git 索引。已对设为 `-text` 的源码目录强制重建索引，使 158 个受跟踪文本的存储字节与已核对的工作区一致；`git diff --cached --ignore-space-at-eol --exit-code` 返回 0，确认此次索引修正只有换行差异，没有业务内容改写。

## 已完成检查

| 检查 | 实际结果 |
| --- | --- |
| 原安装器、工具包、14 原包、前端原始来源 | CLEAN_PASS |
| 当前源码前端生产构建 | 通过 |
| TypeScript noEmit | 通过 |
| 14 原包 CRC/哈希/安全解包 | 通过，主程序 preflight 门禁执行 |
| 14 技能真实 Harness 准备/发现/加载 | 14/14，通过，未调用模型 |
| 10 个个股技能 selftest / Harness 发现 | 10/10，通过，主程序 preflight 门禁执行 |
| Node 恢复/失败路径回归 | 8 通过、1 Windows 平台跳过、0 失败 |
| scripts/tests Python unittest | 17 通过 |
| 当前 contract / TDX 便携路径测试 | 9 通过 |
| Windows 安全启动器的完整便携测试命令 | 26 通过 |
| 桌面端隔离端口与 TDX 根目录解析 | 通过 |
| Electron win-unpacked 构建 | 通过 |
| 重建桌面程序启动 | PASS：控件 ready、首页/chat、CORS、appRoot/dataRoot 身份、34303/44319 隔离、缺凭据状态如实显示 |

完整 NSIS 安装器已实际构建成功：568,468,780 字节（验证用成品，未替换哈希锁定的原安装器）。程序更新器也已实际构建并通过载荷完整性校验：140,666,253 字节，SHA-256 为 `6103d332a4e3c962b8c16f13ae94a916fb692850840cdb9d2d4ca1aa9f9ff129`；不包含环境层，保留目标电脑的运行环境和用户数据。重建桌面冒烟再次通过，额外检查了首页和 /chat 引用的所有客户端资源。未执行对用户现有安装的安装/覆盖测试。

## 独立远端克隆复现

2026-10-08 在同一台 Windows 电脑另建 `zhangcai-desktop-main` 目录，从 GitHub 克隆 main，而非共享 Git worktree 或复制现有开发环境。完成换行修正后的源码提交为 `a3737eb393fbeaac8e7f0b63258fbbdd2e6a5525`，此节补记只修改文档。不是在另一台实体电脑上完成的测试。

| 全新目录检查 | 实际结果 |
| --- | --- |
| GitHub 远端源码 | 克隆成功，1,428 个受跟踪文件 |
| 独立 LFS 对象缓存 | 4/4 对象从 GitHub 下载，完整大小与 SHA-256 正确，git lfs fsck OK |
| 本地网络大文件超时 | 用 GitHub 官方 media CDN 分段续传；只下载远端字节，没有复制本机已存在的安装器或技能包 |
| 开发准备脚本 | Windows PowerShell 执行成功，Node 24.19.0、Python 3.12.14、pnpm 11.19.0、Harness 0.1.2-rc.1 |
| Python 测试依赖 | 从仓库固定 wheel 离线安装，未访问 PyPI |
| 空 pnpm 缓存安装 | FreshDependencyStore 成功；项目私有 store，730 下载、0 复用、730 安装 |
| verify:repository --original-release | CLEAN_PASS，14 原包、9 原始前端源码及锁定资产无错误 |
| verify:portable-tests | 26 通过 |
| TypeScript noEmit | 通过 |
| prepare:desktop-frontend | BUILT_FROM_SOURCE，生产构建完成；不是复用旧 dist |
| package:preflight | READY，0 错误、0 警告；14/14 技能准备与 Harness 发现、10/10 个股 selftest 与发现门禁通过 |
| 克隆目录 Git 状态 | 干净；运行环境、依赖、构建输出按规则忽略 |

全量安装器、程序更新器和桌面实际启动/资源冒烟使用前节的独立整理工作区完成；未在这份冷克隆里重复生成完整 NSIS 安装器。该验证覆盖远端资产获取、空开发依赖缓存、运行环境准备、源码构建与打包预检；不等于脱离 Windows/npm/GitHub 网络的完全离线复现，也不代表真实行情和模型业务研究验收。

## 保留的已知问题

完整旧 stock-unified 回归在执行 91 个用例后达到 maxfail=12：79 通过、12 失败，其余未执行。不是“所有代码测试通过”。失败类别为：

1. shortline-hotspot-mining、hotspot-leader、a-share-sentiment-workflow 的历史 source-manifest 存在哈希漂移；恢复到原安装器字节后该问题仍可复现，不能仅归因于本次复制或换行。
2. 旧目录绝对路径/元数据断言与当前便携仓库相对路径不同；若干原测试固定 D 盘路径已改成仓库解析。
3. 旧报告交付授权测试引用仓库外 fixture、全局 AGENTS.md、report_validator.py；原 0.1.22 安装器也不包含这些旧外部测试约定。未用空文件补造、未放宽安全门禁。
4. 旧 merged/lianban/contract-source 结构断言不完全符合安装版保留代码。
5. 旧 test_portable_stock_audit_runtime 的 5 个用例还引用旧 skills 目录和不在原安装版中的 stock_custom_audit_adapter.py；当前源码库存核对仍为 0 缺失。

当前交付验收入口与完整旧回归分开，旧测试原件保留以供后续修复，不通过跳过所有历史失败项宣称全量通过。

本次没有使用账户模型密钥、没有执行收费研究、没有验证真实通达信历史的业务报告，也没有上传个人数据。缺数据/缺凭据的 BLOCKED 仍是正确状态。
