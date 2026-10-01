# 0.1.22 可审计恢复记录

恢复日期：2026-10-01（Asia/Shanghai）。分支：`recovery-0.1.22`。
基线：`web-3003-14-skill-adapters` @ `89bbbb1a05e113772e82b963751fdbfddeb964f6`。
产品版本：**0.1.22**；运行环境基线：**0.1.9**。未修改 main 或基线分支。

## 来源与核验边界

本次输入是用户提供的 `zhangcai-recovery-0.1.22-source.zip`，SHA-256：
`ee502015bcd88277d51d5f422c3547bbb1aac6c4295e60e0c192ae0d76f231e0`。
原始更新 EXE 未随本次任务提供，因此 EXE 来源、版本与哈希是恢复清单中的来源声明，不能声称本次独立验证了 EXE。
实际存在的 1,237 个 overlay 文件均独立核验大小和 SHA-256，与清单一致。
清单列出 1,266 个文件；缺少的 29 个全部为 Python __pycache__/*.pyc，未恢复或提交。

Node/Python/Electron/技能/配置层的明确内容按文件原样恢复，未生成猜测源码。
恢复脚本会删除整个 config/lib/public 目录，与用户保留未明确覆盖源码的要求冲突，故采用逐文件覆盖。
排除 69 个 reports/run 运行结果、行情快照和报告的恢复改动；已被基线跟踪的这些文件保留原字节，不新增提交其内容。
最终纳入可重复核验的恢复文件共 **1,168** 个，其中包括 60 个编译发布证据文件。
`lib/market.json` 与基线原样相同，本次未提交行情快照改动。

原始 manifest、更新包依赖清单副本、逐文件覆盖前后哈希及排除原因位于 `docs/recovery-0.1.22/`。
恢复改动中 777 个覆盖仅涉及换行字节，211 个覆盖还有其他字节差异；保留恢复包字节以便逐文件审计。

## 前端未恢复范围

以下全部 8 个 TSX 均与基线逐字节一致，仍以 0.1.18 原源码为基础：

- app/home-client.tsx
- app/chat/chat-client.tsx
- app/workspace-pages.tsx
- app/desktop-runtime-shell.tsx
- app/skill14-home.tsx
- app/page.tsx
- app/layout.tsx
- app/chat/page.tsx

更新包未提供这些页面的 0.1.22 原始 TSX 和 source map，因此不宣称前端源码已完整恢复。
`dist/` 是精确的 0.1.22 编译产物参考，用于发布证据和后续差异分析；不可把反编译结果直接视为原始源码。
移除了 59 个不属于 0.1.22 清单的旧编译文件，以使 dist 文件集合精确匹配恢复包；没有删除未被明确覆盖的源码。
本次构建生成的 dist 已丢弃并还原恢复包 dist。重新执行 `pnpm run build` 会改变 dist，不能将新构建结果当作精确 0.1.22 发布证据。

## 人工修正的版本与打包配置

- 根 package.json、packaging/runtime-app-package.json、packaging/electron/package.json 产品版本统一为 0.1.22。
- electron-builder 的 release/site-build 路径指向 0.1.22，加入 tdx-root.mjs 和 skill-archives 映射。
- electron-app/runtime-manifest.json 与 packaging/runtime-manifest.json 的当前发布引用同步至 0.1.22；历史 legacyArtifacts 保留。
- runtime-manifest 中移除与新映射矛盾的 skill-archives 排除项。
- packaging/environment-baseline-version.txt 为 `0.1.9` 并以换行结束；没有重建运行环境。
- 历史 0.1.12/0.1.18 说明与锁文件中第三方依赖 @vitejs/devtools 的 ^0.1.18 保留；不作机械替换。

人工修改原因和哈希见 audit.json 的 localChanges；其余恢复文件保持 overlay 原字节。

## 验证结果与实际缺口

| 验证 | 结果 |
| --- | --- |
| 三个指定 Node 文件的 node --check | 通过 |
| 五个指定 Python 文件的 py_compile | 通过，缓存置于仓库外 |
| pnpm install --frozen-lockfile | 通过，锁文件未改动 |
| pnpm run build | 通过，构建的是保留前端基线与恢复层的组合 |
| 独立恢复哈希、TSX 保留、dist 集合及版本检查 | 通过 |
| pnpm run package:preflight | **未执行**，本机为 macOS，无 Windows/powershell.exe/私有 Windows 运行环境 |

构建通过不证明前端源码与发布版完全相同，也不证明 Windows 安装器可发布。
恢复的 package-preflight.ps1 引用了以下未在基线或恢复包中提供的文件，未臆造其源码：

- scripts/verify_skill14_archives.py
- scripts/verify_stock_detail_skills.py
- scripts/tests/verify_stock_detail_skill_discovery.mjs
- scripts/tests/verify_skill14_packaged_runtime.mjs

此外，版本对应的 site-build staging、私有 Windows Node/Python/Harness 和通达信环境未提供。
145,649,253 字节的技能 ZIP 未包含在恢复包中，本次未上传；需取得原文件后通过 Git LFS 或 GitHub Release Asset 上传。
这些缺口意味着本分支完成的是可审计的部分源码恢复，Windows 完整打包条件尚不齐备。

可在仓库根目录执行 `python scripts/verify-recovery-0.1.22.py` 复核恢复哈希、所有保留 TSX、排除文件、精确 dist 文件集合及产品/环境版本。
验证详情见 `docs/recovery-0.1.22/validation.json`。新增提交内容已检查，未纳入 .env、API 密钥、app-data、运行结果、报告或 Python 缓存。
