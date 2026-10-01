# 硬闸唯一工作流

CODEX_LOCAL_ENTRY

NO_REDISCOVERY: true

NO_CROSS_JUMP: true

LOCKED_ENTRY: scripts/codex_entry.py
LOCKED_EXECUTION: scripts/codex_entry.py run

## 固定链路

1. 路由：唯一权威目录把 $stock-hard-gate 和逐字工作流名“硬闸”路由到本技能，不设 fallback。
2. 入口：只允许 scripts/codex_entry.py run 或其 complete 包装进入业务链。
3. 门面：根入口调用 D:\C盘转移\日志\codex\scripts\stock_canonical_runtime.py，获取串行业务租约并加载 TdxW/tdxcef 默认拒绝守卫。
4. 合同：统一运行时校验门面、执行器、适配器、旧入口、主脚本、说明文件和内部组件的 SHA-256。
5. 业务：合同绑定的 canonical_business_adapter.py 只调用 legacy_codex_entry.py run，后者只转交 scripts/preflight.py。
6. 输入：显式业务参数原样传给预飞脚本；无参数时运行固定正向 canary。
7. 结果：适配器写入 business_child.stdout.txt、business_child.stderr.txt 和 business_result.json。
8. 验收：统一运行时计算语义断言、必需产物、受保护进程前后身份和守卫事件，生成完整回执。
9. 失败：任何缺失、名称错误、范围错误、直接旧入口调用或受保护进程控制均为 BLOCKED；没有降级路径。

## 唯一命令

    python D:\C盘转移\日志\codex\skills\stock-hard-gate\scripts\codex_entry.py run -- <计划文本> [计划动作]

其他脚本只作为合同明确锁定的内部业务实现，不是入口，也不得由模型直接调用。

## 路由边界

- 本技能不生成选股、行情、新闻、评分、Word 或视频产物。
- 具体业务技能可以把本技能作为前置依赖，但不得重复执行其业务工作流。
- stock-unified 只做统一目录验收，不是本技能的业务 owner。
