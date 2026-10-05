# 0.1.22 可审计恢复记录

恢复日期：2026-10-01（Asia/Shanghai）。分支：`recovery-0.1.22`。
基线：`web-3003-14-skill-adapters` @ `89bbbb1a05e113772e82b963751fdbfddeb964f6`。
产品版本：**0.1.22**；运行环境基线：**0.1.9**。未修改 main 或基线分支。

## 2026-10-05 原始大技能包补齐

用户补交 `0.1.22-大文件-A股行情资讯全接口与数据能力大全.zip`。其大小 **145,649,253 字节**，SHA-256 为 `4f492bf7167cf45c523bfb533806a790b0d00ea08f9ce8eda26084944bb504e4`，均与原恢复清单一致。仅按 catalog 重命名为 `skill-archives/A股行情资讯全接口与数据能力大全_WorkBuddy电脑版_20260908-014459.zip`，ZIP 原字节不变。

仅该文件使用 Git LFS 存储，其他 13 个 ZIP 不转为 LFS、不改写既有提交历史。Git 中保存该 ZIP 的指针，实际 ZIP 由 LFS 传输；`.gitattributes` 的规则精确匹配该路径。

重新执行完整验证，14 个 ZIP 的大小、哈希、CRC、安全解压及 SKILL.md 校验均为 `CLEAN_PASS`；14 个技能的运行准备与真实 Harness 发现/加载也均为 `CLEAN_PASS`。实测结果见 `docs/recovery-0.1.22/archive-validation.json`，补交来源及前后哈希修订记录见 `completion-manifest.json`。首次恢复和 2026-10-02 的验证文件保留当时结果，不覆盖为新结果。

当前剩余缺口是私有 Windows 运行环境和通达信业务验收条件，以及 8 个页面的原始 0.1.22 TSX/source map。Windows preflight、安装器构建/安装测试、模型调用和真实行情报告验收仍未执行。产品版本继续为 0.1.22，运行环境基线继续为 0.1.9。

下载分支后，在仓库根目录安装/启用 Git LFS 并取得真实 ZIP，再执行验证；只取得 Git 指针文件时，哈希门禁会阻止打包。

```text
git lfs install
git lfs pull --include="skill-archives/A股行情资讯全接口与数据能力大全_WorkBuddy电脑版_20260908-014459.zip"
python -B scripts/verify-recovery-0.1.22.py
python -B scripts/verify_skill14_archives.py
pnpm run verify:skill14-packaged
```

## 2026-10-02 缺口补齐

根据恢复脚本的调用参数、返回值门禁和现存技能接口，新增实现了四个缺失验证入口。它们是本次编写的补齐代码，**不是从更新包恢复的原始源码**：

- `scripts/verify_skill14_archives.py`：14 个 ZIP 的清单映射、大小、SHA-256、CRC、安全解压与主 SKILL.md 校验。
- `scripts/verify_stock_detail_skills.py`：10 个现存个股技能的独立临时目录 selftest，以及实际 Harness 技能发现与加载。
- `scripts/tests/verify_stock_detail_skill_discovery.mjs`：使用锁定版本的真实 FileSystemSkillProvider 验证 10 个技能。
- `scripts/tests/verify_skill14_packaged_runtime.mjs`：调用已恢复的 `prepare-harness-skill` 命令，校验 ZIP 哈希、隔离目录及真实 Harness 加载。

新增两个配置清单分别记录 14 个 ZIP 的哈希来源与 10 个个股技能 ID；两个共享辅助模块和失败路径测试支撑上述入口。缺少 ZIP、运行环境或技能时返回 `BLOCKED` 和非零退出码，不以跳过检查获得通过。

新增 `scripts/stage-recovered-frontend.mjs`，只复制通过原始恢复清单校验的 60 个 dist 文件至 `packaging/staging/site-build-0.1.22/dist`，并校验原包中的内置公式种子。现有 staging 如果字节不同或不完整会保留并阻止打包。Windows 两个主程序打包入口在 preflight 前调用它。

修正 preflight 对用户 app-data 公式清单的依赖，使用已经恢复且有哈希证据的 `electron-app/resource-library/evidence/formulas/package`；主程序打包不再用用户目录覆盖该公式种子。同步修正依赖清单里与 builder 技能 ZIP 映射冲突的排除项，以及安装策略中的输入清单。生成的 staging 已忽略，不提交运行环境或用户数据。

| 本轮验证（macOS） | 实际结果 |
| --- | --- |
| 新增测试 | 9 个 Node 测试及其中运行的 6 个 Python 用例通过 |
| Python / Node 语法检查 | 10 / 8 个文件通过 |
| 精确 dist staging / 内置公式 | 60 / 11 个文件通过；再次运行复用 staging |
| 个股 selftest / 真实 Harness 发现与加载 | 10 / 10，通过 |
| Skill14 ZIP 校验 | 13 / 14；缺失原始大 ZIP，`BLOCKED`，退出 1 |
| Skill14 运行准备 / 真实 Harness 发现与加载 | 13 / 14；同一 ZIP 缺失，`BLOCKED`，退出 1 |
| Windows PowerShell preflight / 安装器构建 | 未执行：缺 Windows 与私有运行环境 |
| pnpm build | 本轮未重跑；首次恢复时已通过，精确发布 dist 继续保留 |

Harness 校验使用测试目录中安装的官方 `@deepseek-ai/dsh-skill-filesystem@0.1.2-rc.1`，没有重建或升级 0.1.9 运行环境；只验证离线技能发现、加载与 selftest，未调用模型、未验收真实行情或业务报告。调用接口参考 [官方 filesystem provider 文档](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md) 与安装版本实际导出。

本轮新增/修改文件的来源、原哈希与当前哈希见 `docs/recovery-0.1.22/completion-manifest.json`；实测结果见 `completion-validation.json`。原 `audit.json` 和首次 `validation.json` 保持不变，恢复核验脚本同时核验原恢复层与明确标注的新增实现。

截至 2026-10-02，剩余外部缺口为：145,649,253 字节原始技能 ZIP、私有 Windows Node/Python/Harness 与通达信验证条件、8 个页面的 0.1.22 原始 TSX/source map。未生成替代 ZIP 或猜测 TSX；全部 8 个 TSX 和精确 dist 保持原字节。补齐验证入口不等于已经满足 Windows 发布条件。

### 复核命令

在仓库根目录运行以下命令。Windows 打包默认使用 `.runtime` 和 `packaging/staging/desktop-runtime/deepseek-harness`；其他平台须将 `ZHANGCAI_RELEASE_PYTHON` 指向可执行 Python，将 `ZHANGCAI_RELEASE_DSH_ROOT` 指向含上述锁定 provider 的测试 Harness 目录，必要时设置 `ZHANGCAI_RELEASE_NODE`。测试依赖应安装在仓库外。

```text
python -B scripts/verify-recovery-0.1.22.py
pnpm run verify:recovery-completion
pnpm run prepare:recovered-frontend
python -B scripts/verify_stock_detail_skills.py
python -B scripts/verify_skill14_archives.py
pnpm run verify:skill14-packaged
```

以下为首次恢复时的来源记录和当时的验证结果；其中四个脚本及 site-build staging 缺口现已由上述新增实现补齐。

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

## 首次恢复验证结果与当时缺口（2026-10-01）

| 验证 | 结果 |
| --- | --- |
| 三个指定 Node 文件的 node --check | 通过 |
| 五个指定 Python 文件的 py_compile | 通过，缓存置于仓库外 |
| pnpm install --frozen-lockfile | 通过，锁文件未改动 |
| pnpm run build | 通过，构建的是保留前端基线与恢复层的组合 |
| 独立恢复哈希、TSX 保留、dist 集合及版本检查 | 通过 |
| pnpm run package:preflight | **未执行**，本机为 macOS，无 Windows/powershell.exe/私有 Windows 运行环境 |

构建通过不证明前端源码与发布版完全相同，也不证明 Windows 安装器可发布。
恢复的 package-preflight.ps1 引用了以下未在基线或恢复包中提供的文件，首次恢复时未生成替代源码；2026-10-02 已按调用契约新增实现，仍不宣称是原始恢复源码：

- scripts/verify_skill14_archives.py
- scripts/verify_stock_detail_skills.py
- scripts/tests/verify_stock_detail_skill_discovery.mjs
- scripts/tests/verify_skill14_packaged_runtime.mjs

此外，首次恢复时版本对应的 site-build staging、私有 Windows Node/Python/Harness 和通达信环境未提供；本轮已补齐 staging 生成与校验，其他外部条件仍缺失。
145,649,253 字节的技能 ZIP 未包含在恢复包中，本次未上传；需取得原文件后通过 Git LFS 或 GitHub Release Asset 上传。
这些缺口意味着本分支完成的是可审计的部分源码恢复，Windows 完整打包条件尚不齐备。

可在仓库根目录执行 `python scripts/verify-recovery-0.1.22.py` 复核恢复哈希、所有保留 TSX、排除文件、精确 dist 文件集合及产品/环境版本。
验证详情见 `docs/recovery-0.1.22/validation.json`。新增提交内容已检查，未纳入 .env、API 密钥、app-data、运行结果、报告或 Python 缓存。
