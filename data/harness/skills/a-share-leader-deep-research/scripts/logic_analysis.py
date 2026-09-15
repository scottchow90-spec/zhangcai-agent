from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import math
import re
from collections import defaultdict
from statistics import median
from typing import Any


THEME_RULES: tuple[tuple[str, str], ...] = (
    ("创新药与医药研发", r"创新药|CRO|CDMO|CXO|AI制药|基因修饰|重组蛋白|药物研发"),
    ("中药与医药流通", r"中药|流感|止咳|药店|医药零售|医药电商|医药流通"),
    ("医疗服务与脑机接口", r"脑机|医疗服务|医美|病理AI|高压氧|医疗健康"),
    ("机器人与具身智能", r"机器人|具身智能|宇树"),
    ("算力数据中心与通信", r"算力|液冷|数据中心|交换机|通信|物联网|端侧AI|AI应用"),
    ("芯片半导体与光电", r"芯片|半导体|光模块|光芯片|光通信|光电|PCB|先进封装"),
    ("并购重组与控制权", r"并购|收购|重组|实控人|股权转让|预重整|摘帽"),
    ("高端装备与军工", r"真空镀膜|专用设备|通用设备|机床|工业母机|航空|航天|军工|装备"),
    ("新能源与储能", r"新能源|光伏|风电|储能|锂电|固态电池|氢能|核电|充电桩"),
    ("电力电网与公用事业", r"电力|电网|特高压|热力|水务|燃气|公用事业"),
    ("乳业食品与饮品", r"乳业|食品|饮料|茶饮|黄酒|酿酒|番茄|烘焙|餐饮"),
    ("文化传媒与游戏", r"影视|传媒|文化|游戏|院线|上映|出版"),
    ("消费家电与零售", r"家电|厨卫|热泵|零售|旅游|酒店|服装|家居"),
    ("地产与基建", r"房地产|地产|物业|基建|建筑|装修|装饰|工程"),
    ("金融", r"证券|券商|银行|保险|信托|金融"),
    ("周期资源与化工", r"黄金|白银|贵金属|有色|金属|煤炭|石油|天然气|化工|钢铁|水泥"),
    ("业绩与国资事件", r"中报|年报|业绩|增长|预增|扭亏|国企改革|国资"),
)

SUPPLEMENTAL_TOPIC_ALIASES: dict[str, tuple[str, ...]] = {
    "创新药与医药研发": ("医药",),
    "中药与医药流通": ("医药",),
    "医疗服务与脑机接口": ("医药", "脑机"),
    "机器人与具身智能": ("机器人",),
    "算力数据中心与通信": ("算力", "通信", "云计算", "数据中心"),
    "芯片半导体与光电": ("芯片", "通信"),
    "新能源与储能": ("新能源", "电力", "绿色电力"),
    "电力电网与公用事业": ("电力", "绿色电力", "智能电网"),
    "乳业食品与饮品": ("大消费", "食品", "乳业"),
    "文化传媒与游戏": ("文化传媒", "游戏", "大消费"),
    "消费家电与零售": ("大消费", "家电", "零售"),
    "地产与基建": ("地产链", "基建"),
}

EVENT_SIGNAL_PATTERN = re.compile(
    r"收购|重组|合作|签约|协议|中报|半年报|年报|预增|扭亏|减亏|"
    r"上映|中选|获批|订单|招标|量产|发布|实控人|股权转让|投资人招募"
)
GENERIC_EVENT_TERMS = {
    "国企改革",
    "中报增长",
    "年报增长",
    "业绩增长",
    "创新药",
    "机器人",
    "人形机器人",
    "AI应用",
}
SPECIFIC_EVENT_DETAIL_PATTERN = re.compile(
    r"\d{1,4}年|\d{1,2}月|\d+(?:\.\d+)?(?:亿|万|%|万元|亿元)|"
    r"公告|签约仪式|战略合作|项目|产品|药物|订单|股权|控制权"
)


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def clock_seconds(value: object) -> int:
    match = re.fullmatch(r"(\d{2}):(\d{2}):(\d{2})", str(value or ""))
    if not match:
        return 24 * 60 * 60
    hour, minute, second = (int(part) for part in match.groups())
    return hour * 3600 + minute * 60 + second


def money_yi(value: object) -> str:
    return f"{float(value or 0) / 100_000_000:.2f}亿元"


def stock_theme_clusters(stock: dict[str, Any]) -> list[str]:
    text = "|".join(
        clean_text(item)
        for item in (
            *(stock.get("event_drivers") or []),
            *(stock.get("secondary_concepts") or []),
            stock.get("source_nature"),
        )
        if clean_text(item)
    )
    matched = [name for name, pattern in THEME_RULES if re.search(pattern, text, re.I)]
    substantive = [name for name in matched if name != "业绩与国资事件"]
    if substantive:
        return substantive
    if matched:
        return matched
    first_driver = clean_text((stock.get("event_drivers") or ["个股独立事件"])[0])
    return [f"个股事件：{first_driver[:18]}"]


def shared_event_evidence(
    members: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    event_codes: dict[str, set[str]] = defaultdict(set)
    for stock in members:
        code = str(stock["stock_code"])
        for raw_event in stock.get("event_drivers") or []:
            event = clean_text(raw_event)
            if (
                event
                and len(event) >= 12
                and event not in GENERIC_EVENT_TERMS
                and EVENT_SIGNAL_PATTERN.search(event)
                and SPECIFIC_EVENT_DETAIL_PATTERN.search(event)
            ):
                event_codes[event].add(code)
    rows = [
        {
            "event": event,
            "stock_count": len(codes),
            "stock_codes": sorted(codes),
        }
        for event, codes in event_codes.items()
        if len(codes) >= 2
    ]
    rows.sort(key=lambda row: (-int(row["stock_count"]), str(row["event"])))
    return rows


def _position_key(
    stock: dict[str, Any],
    *,
    mechanism_codes: set[str],
    subsequent_peer_count: int,
) -> tuple[Any, ...]:
    return (
        -int(stock.get("consecutive_limit_count") or 1),
        -int(stock.get("recent_limit_count") or 1),
        int(stock.get("open_count") or 0),
        clock_seconds(stock.get("final_limit_time")),
        -(1 if stock.get("stock_code") in mechanism_codes else 0),
        -subsequent_peer_count,
        -float(stock.get("amount") or 0),
        clock_seconds(stock.get("first_limit_time")),
        str(stock.get("stock_code") or ""),
    )


def _position_comparison(
    winner: dict[str, Any],
    loser: dict[str, Any],
    *,
    mechanism_codes: set[str],
    subsequent_peer_counts: dict[str, int],
) -> dict[str, str]:
    winner_code = str(winner["stock_code"])
    loser_code = str(loser["stock_code"])
    winner_name = str(winner["stock_name"])
    loser_name = str(loser["stock_name"])
    dimensions = (
        (
            "标准连板高度",
            int(winner.get("consecutive_limit_count") or 1),
            int(loser.get("consecutive_limit_count") or 1),
            lambda left, right: (
                f"{winner_name}标准连板{left}板，高于{loser_name}{right}板"
            ),
        ),
        (
            "近期涨停高度",
            int(winner.get("recent_limit_count") or 1),
            int(loser.get("recent_limit_count") or 1),
            lambda left, right: (
                f"标准连板相同，但{winner_name}近期{left}次涨停，"
                f"高于{loser_name}{right}次"
            ),
        ),
        (
            "开板次数",
            -int(winner.get("open_count") or 0),
            -int(loser.get("open_count") or 0),
            lambda left, right: (
                f"高度相同，但{winner_name}开板{-left}次，"
                f"少于{loser_name}{-right}次"
            ),
        ),
        (
            "最终封板时间",
            -clock_seconds(winner.get("final_limit_time")),
            -clock_seconds(loser.get("final_limit_time")),
            lambda _left, _right: (
                f"高度和开板次数相同，但{winner_name}最终"
                f"{str(winner.get('final_limit_time'))[:5]}封板，早于"
                f"{loser_name}{str(loser.get('final_limit_time'))[:5]}"
            ),
        ),
        (
            "主机制归属",
            int(winner_code in mechanism_codes),
            int(loser_code in mechanism_codes),
            lambda _left, _right: (
                f"高度与封板质量相同，但{winner_name}属于覆盖面最大的"
                f"共同机制，{loser_name}不属于"
            ),
        ),
        (
            "90分钟同题材跟随",
            int(subsequent_peer_counts[winner_code]),
            int(subsequent_peer_counts[loser_code]),
            lambda left, right: (
                f"前四项相同，但{winner_name}其后90分钟有{left}只"
                f"同题材成员封板，多于{loser_name}{right}只"
            ),
        ),
        (
            "成交容量",
            float(winner.get("amount") or 0),
            float(loser.get("amount") or 0),
            lambda left, right: (
                f"前五项相同，但{winner_name}成交{money_yi(left)}，"
                f"高于{loser_name}{money_yi(right)}"
            ),
        ),
        (
            "首次封板时间",
            -clock_seconds(winner.get("first_limit_time")),
            -clock_seconds(loser.get("first_limit_time")),
            lambda _left, _right: (
                f"前六项相同，但{winner_name}首次"
                f"{str(winner.get('first_limit_time'))[:5]}封板，早于"
                f"{loser_name}{str(loser.get('first_limit_time'))[:5]}"
            ),
        ),
    )
    for priority, (factor, winner_value, loser_value, formatter) in enumerate(
        dimensions,
        start=1,
    ):
        if winner_value != loser_value:
            return {
                "factor": factor,
                "priority": str(priority),
                "detail": formatter(winner_value, loser_value),
            }
    return {
        "factor": "股票代码稳定排序",
        "priority": "9",
        "detail": (
            f"全部业务比较项相同，{winner_name}仅按股票代码稳定排序"
            f"位于{loser_name}之前，不虚构经营或资金差异"
        ),
    }


def _position_weakness(
    stock: dict[str, Any],
    *,
    mechanism_codes: set[str],
    subsequent_peer_counts: dict[str, int],
    median_amount: float,
) -> str:
    code = str(stock["stock_code"])
    name = str(stock["stock_name"])
    open_count = int(stock.get("open_count") or 0)
    final_seconds = clock_seconds(stock.get("final_limit_time"))
    amount = float(stock.get("amount") or 0)
    if open_count >= 5:
        return (
            f"{name}开板{open_count}次，且最终"
            f"{str(stock.get('final_limit_time'))[:5]}才封住，封板韧性偏弱"
        )
    if final_seconds >= 14 * 3600:
        return (
            f"{name}最终{str(stock.get('final_limit_time'))[:5]}封板，"
            "回封偏晚"
        )
    if code not in mechanism_codes:
        return f"{name}未进入覆盖面最大的共同机制，题材直接性弱于机制内成员"
    if subsequent_peer_counts[code] == 0:
        return f"{name}其后90分钟同题材跟随为0，时序扩散不足"
    if amount < median_amount:
        return (
            f"{name}成交{money_yi(amount)}，低于板块中位数"
            f"{money_yi(median_amount)}，容量承接偏弱"
        )
    return f"{name}当日结构短板不突出，但当日排序不能替代次日晋级验证"


def _position_structure_text(
    board: str,
    position_rows: list[dict[str, Any]],
    position_order: list[dict[str, Any]],
    *,
    height_anchor_code: str,
    mechanism_anchor_code: str,
) -> str:
    first = position_order[0]
    first_name = str(first["stock_name"])
    if len(position_rows) == 1:
        return (
            f"{board}只有1只涨停样本，龙1为{first_name}；"
            f"其席位依据为{position_rows[0]['rank_driver']}，"
            "但单一样本无法形成内部竞争梯队。"
        )

    second = position_order[1]
    # The fully evaluated comparison is already stored in the row and preserves
    # the real board mechanism and following-count inputs.
    first_vs_second = position_rows[0]["rank_driver"]
    segments = [
        f"{board}龙1为{first_name}，{first_vs_second}，因此高于龙2"
        f"{second['stock_name']}"
    ]
    if len(position_rows) >= 3:
        third = position_order[2]
        segments.append(
            f"龙2{second['stock_name']}虽凭{position_rows[1]['rank_driver']}"
            f"高于龙3{third['stock_name']}，但在"
            f"{position_rows[0]['decisive_factor']}上不及龙1"
        )
        segments.append(
            f"龙3{third['stock_name']}的主要短板是"
            f"{position_rows[2]['weakness']}"
        )
    first_code = str(first["stock_code"])
    if first_code == height_anchor_code == mechanism_anchor_code:
        structure = "高度、主机制与地位合一"
    elif first_code == height_anchor_code:
        structure = "地位由高度优先项主导，但机制锚与龙1分离"
    elif first_code == mechanism_anchor_code:
        structure = "龙1处于主机制内，但板块高度由其他个股提供"
    else:
        structure = "龙1与高度锚、机制锚分离，内部角色较分散"
    segments.append(f"板块呈{structure}，最高地位不等于所有角色都由同一股承担")
    segments.append(position_rows[0]["invalidation"] + "，届时榜序重排，不机械顺延")
    return "；".join(segments) + "。"


def _cluster_rows(
    members: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, list[str]], dict[str, set[str]]]:
    cluster_codes: dict[str, list[str]] = defaultdict(list)
    stock_clusters: dict[str, set[str]] = {}
    stock_by_code = {str(stock["stock_code"]): stock for stock in members}
    for stock in members:
        code = str(stock["stock_code"])
        clusters = set(stock_theme_clusters(stock))
        stock_clusters[code] = clusters
        for cluster in clusters:
            cluster_codes[cluster].append(code)

    rows = []
    for name, codes in cluster_codes.items():
        ordered_codes = sorted(
            set(codes),
            key=lambda code: (
                clock_seconds(stock_by_code[code].get("first_limit_time")),
                code,
            ),
        )
        rows.append(
            {
                "name": name,
                "stock_count": len(ordered_codes),
                "coverage_ratio": round(len(ordered_codes) / len(members), 4),
                "stock_codes": ordered_codes,
            }
        )
    rows.sort(
        key=lambda row: (
            -int(row["stock_count"]),
            min(
                clock_seconds(stock_by_code[code].get("first_limit_time"))
                for code in row["stock_codes"]
            ),
            str(row["name"]),
        )
    )
    return rows, cluster_codes, stock_clusters


def _supplemental_matches(
    mechanism_rows: list[dict[str, Any]],
    supplemental_context: dict[str, Any] | None,
) -> list[str]:
    if not supplemental_context or supplemental_context.get("status") != "CLEAN_PASS":
        return []
    topic_names = [
        clean_text(item.get("name"))
        for item in supplemental_context.get("topics") or []
        if isinstance(item, dict)
    ]
    matched: list[str] = []
    for row in mechanism_rows:
        aliases = SUPPLEMENTAL_TOPIC_ALIASES.get(str(row["name"]), ())
        if any(alias in topic for alias in aliases for topic in topic_names):
            matched.append(str(row["name"]))
    return matched


def analyze_board(
    board: str,
    members: list[dict[str, Any]],
    *,
    lhb_codes: set[str] | None = None,
    supplemental_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not members:
        raise ValueError("board_members_empty")

    lhb_codes = lhb_codes or set()
    stock_by_code = {str(stock["stock_code"]): stock for stock in members}
    cluster_rows, _cluster_codes, stock_clusters = _cluster_rows(members)
    mechanism_rows = [
        row
        for row in cluster_rows
        if int(row["stock_count"]) >= 2
    ][:3]
    if not mechanism_rows:
        mechanism_rows = cluster_rows[:2]
    primary = mechanism_rows[0]
    mechanism_codes = set(str(code) for code in primary["stock_codes"])
    event_evidence = shared_event_evidence(members)

    subsequent_peer_counts: dict[str, int] = {}
    for stock in members:
        code = str(stock["stock_code"])
        start = clock_seconds(stock.get("first_limit_time"))
        themes = stock_clusters[code]
        subsequent_peer_counts[code] = sum(
            1
            for other in members
            if str(other["stock_code"]) != code
            and start < clock_seconds(other.get("first_limit_time")) <= start + 90 * 60
            and bool(themes & stock_clusters[str(other["stock_code"])])
        )

    height_anchor = min(
        members,
        key=lambda stock: (
            -int(stock.get("consecutive_limit_count") or 1),
            -int(stock.get("recent_limit_count") or 1),
            clock_seconds(stock.get("first_limit_time")),
            int(stock.get("open_count") or 0),
            str(stock.get("stock_code")),
        ),
    )
    mechanism_candidates = [
        stock for stock in members if str(stock["stock_code"]) in mechanism_codes
    ]
    mechanism_anchor = min(
        mechanism_candidates,
        key=lambda stock: (
            -int(stock.get("consecutive_limit_count") or 1),
            -int(stock.get("recent_limit_count") or 1),
            -subsequent_peer_counts[str(stock["stock_code"])],
            clock_seconds(stock.get("first_limit_time")),
            -float(stock.get("amount") or 0),
        ),
    )
    temporal_lead_anchor = min(
        members,
        key=lambda stock: (
            -subsequent_peer_counts[str(stock["stock_code"])],
            clock_seconds(stock.get("first_limit_time")),
            -int(stock.get("consecutive_limit_count") or 1),
        ),
    )
    capacity_anchor = max(
        members,
        key=lambda stock: (
            float(stock.get("amount") or 0),
            int(stock.get("consecutive_limit_count") or 1),
        ),
    )

    linked = sum(int(stock.get("consecutive_limit_count") or 1) >= 2 for stock in members)
    early = sum(clock_seconds(stock.get("first_limit_time")) <= 10 * 3600 for stock in members)
    zero_open = sum(int(stock.get("open_count") or 0) == 0 for stock in members)
    high_reopen = sum(int(stock.get("open_count") or 0) >= 3 for stock in members)
    late_seal = sum(clock_seconds(stock.get("final_limit_time")) >= 14 * 3600 for stock in members)
    total_amount = sum(float(stock.get("amount") or 0) for stock in members)
    max_amount = max(float(stock.get("amount") or 0) for stock in members)
    median_amount = median(float(stock.get("amount") or 0) for stock in members)
    ladder_levels = sorted(
        {
            int(stock.get("consecutive_limit_count") or 1)
            for stock in members
            if int(stock.get("consecutive_limit_count") or 1) >= 2
        }
    )
    max_level = max(ladder_levels, default=1)
    ladder_gaps = [
        level for level in range(2, max_level + 1) if level not in ladder_levels
    ]
    supplemental_matches = _supplemental_matches(mechanism_rows, supplemental_context)

    top_coverage = float(primary["coverage_ratio"])
    second_coverage = (
        float(mechanism_rows[1]["coverage_ratio"])
        if len(mechanism_rows) > 1
        else 0.0
    )
    if top_coverage >= 0.5 and second_coverage >= 0.35:
        logic_type = "双机制共振型"
    elif top_coverage >= 0.5:
        logic_type = "主机制集中型"
    elif linked >= 3:
        logic_type = "高度抱团、多分支并行型"
    else:
        logic_type = "多分支轮动型"

    temporal_lead_code = str(temporal_lead_anchor["stock_code"])
    subsequent_peer_count = subsequent_peer_counts[temporal_lead_code]
    constraints: list[str] = []
    if top_coverage < 0.5:
        constraints.append(
            f"最大共同机制仅覆盖{int(primary['stock_count'])}/{len(members)}只，板块内部一致性不足"
        )
    if ladder_gaps:
        constraints.append(
            "连板梯队缺少" + "、".join(f"{level}板" for level in ladder_gaps)
        )
    if high_reopen:
        constraints.append(f"{high_reopen}只个股开板不少于3次，分歧较大")
    if late_seal:
        constraints.append(f"{late_seal}只个股14:00后才完成最终封板")
    if str(temporal_lead_anchor["stock_code"]) not in mechanism_codes:
        constraints.append("时序领先个股与覆盖面最大的共同机制不一致，内部存在轮动")
    if not constraints:
        constraints.append(
            f"高度主要依赖{height_anchor['stock_name']}，若高度锚弱化，板块缺少同级替代"
        )

    structural_evidence_score = 0
    structural_evidence_score += 1 if top_coverage >= 0.5 else 0
    structural_evidence_score += (
        1 if linked >= max(2, math.ceil(len(members) * 0.2)) else 0
    )
    structural_evidence_score += 1 if early / len(members) >= 0.4 else 0
    structural_evidence_score += 1 if zero_open / len(members) >= 0.5 else 0
    structural_evidence_score += 1 if subsequent_peer_count >= 2 else 0
    structural_evidence_score -= 1 if high_reopen / len(members) >= 0.3 else 0
    structural_evidence_score -= 1 if ladder_gaps else 0
    structural_evidence_strength = (
        "高"
        if structural_evidence_score >= 4
        else "中"
        if structural_evidence_score >= 2
        else "低"
    )

    primary_names = "、".join(
        stock_by_code[code]["stock_name"]
        for code in primary["stock_codes"][:4]
    )
    if subsequent_peer_count:
        temporal_text = (
            f"{temporal_lead_anchor['stock_name']}于"
            f"{str(temporal_lead_anchor['first_limit_time'])[:5]}率先封板，"
            f"其后90分钟内有{subsequent_peer_count}只共享题材成员封板，"
            "形成可观察的同题材时序共振，但该先后关系不证明前者导致后者涨停"
        )
    else:
        temporal_text = "同题材个股之间未观察到清晰的90分钟后续共振"
    if event_evidence:
        common_event_names = "、".join(
            str(row["event"]) for row in event_evidence[:2]
        )
        causal_boundary = (
            f"成员中存在覆盖至少2只股票的同一事件表述：{common_event_names}；"
            "仍只将其作为共同事件证据，不单凭共现断言事件已经造成涨停。"
        )
    else:
        causal_boundary = (
            "未发现覆盖至少2只成员的同一公司级事件证据；"
            "以下解释限定为共同产业机制与盘面时序，不把题材共现等同于外生事件因果。"
        )
    logic_statement = (
        f"{logic_type}。覆盖面最大的共同机制“{primary['name']}”覆盖"
        f"{int(primary['stock_count'])}/{len(members)}只（{primary_names}）；"
        f"{mechanism_anchor['stock_name']}承担机制锚，"
        f"{height_anchor['stock_name']}以{height_anchor['recent_limit_up_label']}"
        f"、标准连板{height_anchor['consecutive_limit_count']}板提供高度。"
        f"{temporal_text}。盘面事实支持“共同机制—高度锚—时序共振”的结构解释，"
        "不支持个股之间的直接因果断言。"
        f"{causal_boundary}"
    )

    mechanism_parts = []
    for row in mechanism_rows[:3]:
        names = "、".join(
            stock_by_code[code]["stock_name"] for code in row["stock_codes"][:3]
        )
        mechanism_parts.append(
            f"{row['name']}覆盖{row['stock_count']}/{len(members)}只（{names}）"
        )
    mechanism_statement = (
        "共同机制由" + "；".join(mechanism_parts) + "构成。"
        f"其中{mechanism_anchor['stock_name']}兼具题材直接性与"
        f"{mechanism_anchor['recent_limit_up_label']}高度，"
        f"{capacity_anchor['stock_name']}以{money_yi(capacity_anchor['amount'])}"
        f"成交承担容量承接。事件证据边界：{causal_boundary}"
    )

    validation_statement = (
        f"盘面验证：{early}/{len(members)}只在10:00前首次封板，"
        f"{linked}只处于连板梯队，{zero_open}只全日零开板，"
        f"板块成交合计{money_yi(total_amount)}。"
        f"结构约束：{'；'.join(constraints[:3])}。"
        f"盘面结构证据强度为{structural_evidence_strength}，"
        "该评级只衡量共同机制覆盖、封板时序共振、梯队、开板和成交结构，"
        "不代表事件因果已被证实。"
    )

    position_order = sorted(
        members,
        key=lambda stock: _position_key(
            stock,
            mechanism_codes=mechanism_codes,
            subsequent_peer_count=subsequent_peer_counts[
                str(stock["stock_code"])
            ],
        ),
    )[:10]
    position_rows = []
    nature_rows = []
    role_by_code: dict[str, list[str]] = defaultdict(list)
    role_by_code[str(height_anchor["stock_code"])].append("高度锚")
    role_by_code[str(mechanism_anchor["stock_code"])].append("机制锚")
    if subsequent_peer_count:
        role_by_code[temporal_lead_code].append("时序领先")
    if (
        float(capacity_anchor.get("amount") or 0) >= max(300_000_000, median_amount * 1.4)
    ):
        role_by_code[str(capacity_anchor["stock_code"])].append("容量核心")
    for stock in members:
        code = str(stock["stock_code"])
        if (
            1 <= int(stock.get("open_count") or 0) <= 4
            and float(stock.get("amount") or 0) >= median_amount
            and clock_seconds(stock.get("final_limit_time")) <= 14 * 3600 + 45 * 60
        ):
            role_by_code[code].append("换手回封核心")

    comparisons = [
        _position_comparison(
            position_order[index],
            position_order[index + 1],
            mechanism_codes=mechanism_codes,
            subsequent_peer_counts=subsequent_peer_counts,
        )
        for index in range(max(0, len(position_order) - 1))
    ]
    for rank, stock in enumerate(position_order, start=1):
        code = str(stock["stock_code"])
        roles = list(dict.fromkeys(role_by_code.get(code) or []))
        previous_comparison = comparisons[rank - 2] if rank > 1 else None
        next_comparison = comparisons[rank - 1] if rank <= len(comparisons) else None
        if next_comparison:
            rank_driver = (
                f"{next_comparison['detail']}，在第{next_comparison['priority']}"
                "比较层级胜出"
            )
        elif int(stock.get("consecutive_limit_count") or 1) >= 2:
            rank_driver = (
                f"以标准连板{stock['consecutive_limit_count']}板进入当前榜序，"
                "下方无成员可作额外比较"
            )
        elif code in mechanism_codes:
            rank_driver = (
                f"位于共同机制“{primary['name']}”并完成封板，"
                "下方无成员可作额外比较"
            )
        elif int(stock.get("open_count") or 0) == 0:
            rank_driver = "全日零开板并维持涨停，下方无成员可作额外比较"
        else:
            rank_driver = "截至收盘维持涨停，下方无成员可作额外比较"

        if previous_comparison and next_comparison:
            relative_comparison = (
                f"低于龙{rank - 1}：{previous_comparison['detail']}；"
                f"高于龙{rank + 1}：{next_comparison['detail']}"
            )
        elif next_comparison:
            relative_comparison = f"高于龙{rank + 1}：{next_comparison['detail']}"
        elif previous_comparison:
            relative_comparison = (
                f"低于龙{rank - 1}：{previous_comparison['detail']}；"
                "无下位成员，不补造额外胜出理由"
            )
        else:
            relative_comparison = "板块仅1只涨停，无同板块相邻席位可比较"

        weakness = _position_weakness(
            stock,
            mechanism_codes=mechanism_codes,
            subsequent_peer_counts=subsequent_peer_counts,
            median_amount=median_amount,
        )
        if next_comparison:
            invalidation = (
                f"次日若龙{rank + 1}在{next_comparison['factor']}上反超，"
                f"且{stock['stock_name']}未形成更高优先级优势，本席位失效"
            )
        elif previous_comparison:
            invalidation = (
                f"次日若未缩小与龙{rank - 1}在"
                f"{previous_comparison['factor']}上的差距且自身未封板，"
                "本席位失效"
            )
        else:
            invalidation = "次日若不能继续封板，本席位失效，单一样本不外推"
        decisive_factor = (
            next_comparison["factor"]
            if next_comparison
            else previous_comparison["factor"]
            if previous_comparison
            else "单一样本涨停"
        )
        reason = (
            f"胜出依据：{rank_driver}。相对位置：{relative_comparison}。"
            f"主要短板：{weakness}。失效条件：{invalidation}。"
        )
        position_rows.append(
            {
                "rank": rank,
                "stock_code": code,
                "decisive_factor": decisive_factor,
                "rank_driver": rank_driver,
                "relative_comparison": relative_comparison,
                "weakness": weakness,
                "invalidation": invalidation,
                "decision_vector": {
                    "consecutive_limit_count": int(
                        stock.get("consecutive_limit_count") or 1
                    ),
                    "recent_limit_count": int(stock.get("recent_limit_count") or 1),
                    "open_count": int(stock.get("open_count") or 0),
                    "final_limit_time": str(stock.get("final_limit_time") or ""),
                    "in_primary_mechanism": code in mechanism_codes,
                    "subsequent_peer_count_90m": int(subsequent_peer_counts[code]),
                    "amount": float(stock.get("amount") or 0),
                    "lhb_net_buy_ge_100m": code in lhb_codes,
                    "first_limit_time": str(stock.get("first_limit_time") or ""),
                },
                "reason": reason,
            }
        )
        if roles:
            nature_reason_parts = []
            if "高度锚" in roles:
                nature_reason_parts.append(
                    f"以{stock['recent_limit_up_label']}、标准连板"
                    f"{stock['consecutive_limit_count']}板提供高度"
                )
            if "机制锚" in roles:
                nature_reason_parts.append(
                    f"位于共同机制“{primary['name']}”，覆盖"
                    f"{primary['stock_count']}/{len(members)}只"
                )
            if "时序领先" in roles:
                nature_reason_parts.append(
                    f"其后90分钟有{subsequent_peer_counts[code]}只"
                    "同题材成员封板"
                )
            if "容量核心" in roles:
                nature_reason_parts.append(f"成交{money_yi(stock['amount'])}为板块最大")
            if "换手回封核心" in roles:
                nature_reason_parts.append(
                    f"开板{stock['open_count']}次后于"
                    f"{str(stock['final_limit_time'])[:5]}回封"
                )
            if code in lhb_codes:
                nature_reason_parts.append("龙虎榜净买入过亿元提供资金印证")
            nature_rows.append(
                {
                    "rank": len(nature_rows) + 1,
                    "stock_code": code,
                    "nature_names": roles,
                    "reason": "；".join(nature_reason_parts) + "。",
                }
            )

    position_conclusion = _position_structure_text(
        board,
        position_rows,
        position_order,
        height_anchor_code=str(height_anchor["stock_code"]),
        mechanism_anchor_code=str(mechanism_anchor["stock_code"]),
    )

    return {
        "logic_type": logic_type,
        "shared_mechanisms": mechanism_rows,
        "common_event_evidence": event_evidence,
        "causal_boundary": causal_boundary,
        "temporal_sequence": {
            "height_anchor": str(height_anchor["stock_code"]),
            "mechanism_anchor": str(mechanism_anchor["stock_code"]),
            "temporal_lead_anchor": temporal_lead_code,
            "capacity_anchor": str(capacity_anchor["stock_code"]),
            "subsequent_peer_count_90m": subsequent_peer_count,
        },
        "validation": {
            "member_count": len(members),
            "linked_count": linked,
            "early_count": early,
            "zero_open_count": zero_open,
            "high_reopen_count": high_reopen,
            "late_seal_count": late_seal,
            "total_amount": total_amount,
            "largest_amount": max_amount,
            "ladder_levels": ladder_levels,
            "ladder_gaps": ladder_gaps,
        },
        "constraints": constraints,
        "structural_evidence_strength": structural_evidence_strength,
        "structural_evidence_score": structural_evidence_score,
        "supplemental_topic_matches": supplemental_matches,
        "logic_statement": logic_statement,
        "mechanism_statement": mechanism_statement,
        "validation_statement": validation_statement,
        "position_conclusion": position_conclusion,
        "nature_top": nature_rows,
        "position_top": position_rows,
    }
