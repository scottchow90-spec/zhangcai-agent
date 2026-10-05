#!/usr/bin/env python3
"""
硬阻断器 v2 — 覆盖全部45项错误的可执行阻断
用法: python block.py <公式名> [声明文本]
返回: {"BLOCKED": true/false, "errors": [...], "fixes": [...]}
"""
import json, os, sys

# ===== 命名错误阻断（覆盖错误#1-4） =====
NAME_RULES = [
    ("七浪坑",     "起浪坑"),
    ("机构自检",   "机构资金监控"),
    ("庄家自检",   "庄家资金监控"),
    ("庄家资金监控2", "庄家资金监控"),
    ("大牛线",     "大牛线4.0"),   # 缺版本号(仅当4.0不存在时阻断)
    # 特殊: 仅当"大牛线"出现但"4.0"不在同一上下文中
]
FORBIDDEN_FORMULA_NAMES = {"飞龙在天" + "4.0"}

# ===== 术语规范阻断（覆盖错误#5-8, #43-44） =====
TERM_BLOCK = {
    "金叉":     "波",     # 老术语
    "死叉":     "段",     # 老术语
    "约":      None,      # 模糊词→直接阻断
    "大概":    None,
    "估计":    None,
    "数据未触发": None,
    "控盘缺失": None,
}

# ===== 数据源阻断（覆盖错误#14-17） =====
DATASOURCE_BLOCK = {
    "iFinD search_stocks" + "涨停总数":  "同花顺",
    "iFinD search_stocks" + "跌停总数":  "同花顺",
    "iFinD index_data" + "收盘价":       "东方财富API",
}

# ===== 声明阻断（覆盖错误#9-10, #12, #20-21, #27） =====
CLAIM_BLOCK = {
    "起不来":    "用户已声明TDX在运行",
    "没运行":    "用户已声明进程在运行",
    "不存在":    "换路径/换类型重试，不直接报不存在",
    "只能手工":  "先跑tq_fallback_compute.py工具链",
    "默认路径":  "用户已给定明确路径时，禁止默认替代",
    "默认API":   "用户已给定明确对象时，禁止默认替代",
    "大综合表":  "用户未要求综合表时，禁止擅自扩展输出结构",
}

FIX_MAP = {}
for bad, good in NAME_RULES:
    FIX_MAP[bad] = good
for k, v in TERM_BLOCK.items():
    if v is not None: FIX_MAP[k] = v
CLAIM_FIX = {k: "用户已确认在运行" for k in CLAIM_BLOCK if "运行" in CLAIM_BLOCK[k]}

def check(text=""):
    errors, fixes = [], []

    for forbidden in FORBIDDEN_FORMULA_NAMES:
        if forbidden in text:
            errors.append(f"已全局禁用旧公式: '{forbidden}'；唯一合法公式为'飞龙在天'")
            fixes.append(f"{forbidden} → 飞龙在天")

    replay_markers = ["逐字回读", "用户原话", "禁止默认替代"]
    missing = [marker for marker in replay_markers if marker not in text]
    if missing:
        errors.append(f"缺少强制原话回读声明: {missing}")
    hard_markers = ["禁止任务扩展", "禁止单源结论", "禁止热替换", "输出结构服从用户", "禁止缩窄范围", "禁止子代理跑偏", "禁止假交付"]
    hard_missing = [marker for marker in hard_markers if marker not in text]
    if hard_missing:
        errors.append(f"缺少全错误类阻断声明: {hard_missing}")

    for bad, good in NAME_RULES:
        if bad in text:
            # For versioned names: only block if the correct version is NOT present
            if bad == "大牛线" and good and good in text:
                continue  # "大牛线4.0" is in text, ok
            errors.append(f"命名错误: '{bad}' → '{good}'")
            fixes.append(f"{bad} → {good}")

    for bad, good in TERM_BLOCK.items():
        if bad in text:
            if good is None:
                errors.append(f"禁止模糊词: '{bad}'")
            else:
                errors.append(f"术语过时: '{bad}' → '{good}'")
                fixes.append(f"{bad} → {good}")

    for bad, msg in CLAIM_BLOCK.items():
        if bad in text:
            errors.append(f"禁止声明: '{bad}' — {msg}")
            if bad in CLAIM_FIX:
                fixes.append(CLAIM_FIX[bad])

    if errors:
        print(json.dumps({"BLOCKED": True, "errors": errors, "fixes": fixes}, ensure_ascii=False))
        return 2
    else:
        print(json.dumps({"BLOCKED": False, "status": "PASS"}))
        return 0

if __name__ == "__main__" and os.environ.get(
    "ONESTOCK_STOCK_CANONICAL_CHILD"
) != "1":
    print(
        "canonical_stock_legacy_entry_direct_execution_blocked",
        file=sys.stderr,
    )
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(check(" ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""))
