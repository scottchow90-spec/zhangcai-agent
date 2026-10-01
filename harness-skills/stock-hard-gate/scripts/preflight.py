#!/usr/bin/env python3
"""
预飞检查 — 第5层防护
每次股票工具调用前必须跑此脚本
使用脚本内置的当前纠正规则，检查计划操作是否违反任何纠正
违反 → 返回非零退出码，禁止继续
"""
import json, os, sys

CORRECTIONS = {
    "session": "content-clean-current",
    "blocked_claims": [
        "起不来",
        "没运行",
        "不存在",
        "只能手工",
        "默认路径",
        "默认API",
        "大综合表",
    ],
    "formula_names": {
        "大牛线": "大牛线4.0",
        "机构自检监控": "机构资金监控",
        "机构自检": "机构资金监控",
        "庄家自检监控": "庄家资金监控",
        "庄家自检": "庄家资金监控",
        "庄家资金监控2": "庄家资金监控",
    },
    "corrections": [
        "大牛线 → 大牛线4.0",
        "飞龙在天4.0 → 禁止使用；唯一合法公式为飞龙在天",
        "机构自检监控 → 机构资金监控",
        "机构自检 → 机构资金监控",
        "庄家自检监控 → 庄家资金监控",
        "庄家自检 → 庄家资金监控",
        "庄家资金监控2 → 庄家资金监控（当前E盘运行时名）",
    ],
    "canonical_formulas": [
        "大牛线4.0",
        "飞龙在天",
        "飞龙在天选股",
        "游资资金监控",
        "机构资金监控",
        "庄家资金监控",
    ],
}

def load():
    return CORRECTIONS

def _contains_alias(text, alias, canonical):
    if not alias:
        return False
    if alias in {"大牛线", "飞龙在天"}:
        return alias in text and canonical not in text
    return alias in text

def preflight(planned_text="", planned_action=""):
    """检查计划操作，返回 (ok, warnings)"""
    data = load()
    warnings = []

    # 0. 必须显式声明已逐字回读用户原话
    replay_markers = ["逐字回读", "用户原话", "禁止默认替代"]
    missing = [marker for marker in replay_markers if marker not in planned_text]
    if missing:
        warnings.append(f"REPLAY: 缺少用户原话回读声明 {missing}")

    # 0.5 必须显式声明全错误类阻断
    hard_markers = ["禁止任务扩展", "禁止单源结论", "禁止热替换", "输出结构服从用户", "禁止缩窄范围", "禁止子代理跑偏", "禁止假交付"]
    hard_missing = [marker for marker in hard_markers if marker not in planned_text]
    if hard_missing:
        warnings.append(f"HARDCLASS: 缺少全错误类阻断声明 {hard_missing}")
    
    # 1. 检查是否包含被禁止的声明
    for blocked in data['blocked_claims']:
        if blocked in planned_text:
            warnings.append(f"BLOCKED: 计划输出包含禁止声明 '{blocked}'")
    
    # 2. 检查公式名是否正确
    for bad, good in data.get('formula_names', {}).items():
        if _contains_alias(planned_text, bad, good):
            warnings.append(f"FORMULA: 计划使用 '{bad}'，应为 '{good}'")
    
    # 3. 检查是否与用户纠正冲突
    for correction in data['corrections']:
        parts = correction.split(' → ')
        if len(parts) == 2:
            wrong, right = parts
            if wrong in planned_text and right not in planned_text:
                warnings.append(f"CORRECTION: 计划使用 '{wrong}'，用户已纠正为 '{right}'")
    
    # 4. 空操作检查（如果什么都没提供，只做基本验证）
    if not planned_text and not planned_action:
        print(json.dumps({"status": "READY", "corrections_count": len(data['corrections']), "session": data['session']}, ensure_ascii=False))
        return True, warnings
    
    ok = len(warnings) == 0
    result = {
        "status": "PASS" if ok else "BLOCKED",
        "planned": planned_text[:100],
        "warnings": warnings,
        "canonical_formulas": data.get("canonical_formulas", [])
    }
    print(json.dumps(result, ensure_ascii=False))
    return ok, warnings

if __name__ == "__main__" and os.environ.get(
    "ONESTOCK_STOCK_CANONICAL_CHILD"
) != "1":
    print(
        "canonical_stock_legacy_entry_direct_execution_blocked",
        file=sys.stderr,
    )
    raise SystemExit(2)


if __name__ == '__main__':
    text = sys.argv[1] if len(sys.argv) > 1 else ""
    action = sys.argv[2] if len(sys.argv) > 2 else ""
    ok, _ = preflight(text, action)
    sys.exit(0 if ok else 1)
