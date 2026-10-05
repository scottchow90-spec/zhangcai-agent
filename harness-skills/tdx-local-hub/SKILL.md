---
name: tdx-local-hub
description: "Direct local Tongdaxin access from the configured ZHANGCAI_TDX_ROOT, including TQ real-time data, local K-line files, block pools, layouts, formulas, and local caches. Use only when the user explicitly requests the Tongdaxin local workflow."
---

# 通达信本地中枢

## 桌面端路径约定

掌财桌面端通过 `ZHANGCAI_TDX_ROOT` 和 `STOCK_SKILLS_ROOT` 注入本机绝对路径。运行时必须以这两个值定位通达信与技能文件；文档或旧回执中的 `C:\\new_tdx_mock`、`D:\\C盘转移...` 只是历史来源示例，不能作为当前安装路径使用。

## 独立边界

- 只处理 `ZHANGCAI_TDX_ROOT` 指向目录中的行情、TQ、K线、板块、版面、公式和本地缓存。
- 不调用 OpenClaw，不混用云端股票、开盘啦或通用股票技能。
- 需要浏览器时只使用用户的 Google Chrome；本地通达信任务优先使用文件、API和进程内接口。

## 工作流

1. 先读取 `references/workflow.md` 以及与任务直接相关的参考文件。
2. 行情、涨停、板块、选股优先读取当前 `ZHANGCAI_TDX_ROOT` 数据，盘中数据注明采集时间。
3. 使用 `scripts/tdx_hub.py` 处理通用本地数据；TQ实时任务使用 `scripts/tq_dynamic_bridge.py` 或 `${ZHANGCAI_TDX_ROOT}\PYPlugins\user\tqcenter.py` 的公开接口。
4. 只修改任务明确要求的文件，保持幂等，不生成执行回执、证明账本或验收清单。
5. 完成后做一次与结果直接相关的读取或运行验证。

## 固定入口

- 直接入口：`python payload/skills/tdx-local-hub/scripts/codex_entry.py run -- <tdx_hub arguments>`（安装包中由 `STOCK_SKILLS_ROOT` 定位）
- 业务脚本：`scripts/tdx_hub.py`
- TQ公式桥接：`scripts/tq_dynamic_bridge.py`

## 参考资料

- `references/business_spec.md`
- `references/source-map.md`
- `references/workflow.md`
