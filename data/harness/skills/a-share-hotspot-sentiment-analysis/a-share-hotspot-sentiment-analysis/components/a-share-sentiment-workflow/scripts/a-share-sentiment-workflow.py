#!/usr/bin/env python
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
# -*- coding: utf-8 -*-
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import warnings
try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass
from collections import Counter, defaultdict
from email.utils import parsedate_to_datetime
from functools import lru_cache
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus, urljoin, urlparse


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SOURCE_SKILL.md"
WORKFLOW = ROOT / "references" / "workflow.md"
CHECKLIST = ROOT / "references" / "checklist.md"
WORKSPACE = ROOT.parents[1]
SHARED_SCRIPTS = WORKSPACE / "scripts"
if str(SHARED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SHARED_SCRIPTS))
from sentiment_quality_contracts import (
    REQUIRED_CAPTURE_FILES,
    validate_capture_accounting,
    validate_sentiment_record,
)
WORKFLOW_LOCK = WORKSPACE / "hooks" / "skill_workflow_lock.py"
SUBSTANTIVE_GATE = WORKSPACE / "hooks" / "stock_workflow_substantive_gate.py"
LOCKED_EXECUTION = ROOT / "scripts" / "a-share-sentiment-workflow_closure_gate.py"
PYTHON_EXE = sys.executable
DEFAULT_REPORT_DIR = ROOT.parents[1] / "reports" / "a-share-sentiment" if len(ROOT.parents) >= 2 else ROOT / "reports"
LOCAL_REVIEW_DIR = Path(r"D:\C盘转移\日志\codex\reports\20260630_limit_up_review_closed_loop")
LOCKED_TEMPLATE = WORKSPACE / "assets" / "a-share-sentiment-report-template.docx"
LOCKED_TEMPLATE_SHA256 = "e16ab8b9448b49ef66afec40a0015dfcf194771db639d5eae2f2382cd2dde68c"
LOCKED_TEMPLATE_PARAGRAPHS = 43
LOCKED_TEMPLATE_TABLES = 25
LOCKED_TEMPLATE_SHAPES = [
    [6, 6], [1, 1], [2, 2], [6, 5], [2, 2], [1, 1], [15, 5],
    [1, 1], [6, 2], [1, 1], [10, 5], [1, 1], [6, 2], [1, 1],
    [7, 5], [1, 1], [6, 2], [1, 1], [6, 5], [1, 1], [6, 2],
    [1, 1], [10, 5], [4, 4], [5, 2],
]
OUTPUT_PARAGRAPHS = LOCKED_TEMPLATE_PARAGRAPHS
OUTPUT_TABLES = LOCKED_TEMPLATE_TABLES
INTEGRATION_RUNTIME = ROOT.parents[1] / "scripts" / "a_share_sentiment_integrator.py"
WORD_RENDER_VALIDATOR = WORKSPACE / "scripts" / "word_render_validator.py"


@lru_cache(maxsize=1)
def load_integration_runtime():
    if not INTEGRATION_RUNTIME.is_file():
        raise RuntimeError(f"BLOCKED integration runtime missing: {INTEGRATION_RUNTIME}")
    spec = importlib.util.spec_from_file_location("a_share_sentiment_integrator", INTEGRATION_RUNTIME)
    if spec is None or spec.loader is None:
        raise RuntimeError("BLOCKED integration runtime import specification unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _windows_io_path(path):
    path = Path(path)
    absolute = str(path.absolute())
    if os.name == "nt" and len(absolute) >= 260 and not absolute.startswith("\\\\?\\"):
        return Path("\\\\?\\" + absolute)
    return path


def write_text_file(path, content):
    return _windows_io_path(path).write_text(content, encoding="utf-8")


def write_json_text(path, payload):
    return write_text_file(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2),
    )

LABEL_GROUNDING_MIN_HITS = 2
MIN_CLUSTER_SOURCES = 3
MIN_CLUSTER_SOURCE_LAYERS = 3
MIN_DIRECTION_STOCKS = 3
MIN_CAUSAL_CATALYSTS = 1
MIN_CAUSAL_MARKET_FEEDBACK = 1
MIN_CAUSAL_PARTICIPANT_FEEDBACK = 1
MIN_REPORT_CAUSAL_CHAINS = 2
ALLOWED_CAUSAL_METHODS = {"event_text_exact_theme_role_chain_v1"}
ALLOWED_CAUSAL_STANCES = {"增强", "转弱", "分歧"}
CHINA_TZ = timezone(timedelta(hours=8))
EVENT_WINDOW_HOURS = 72
EVENT_WINDOW_TYPE = "event_72h"
MARKET_VALIDATION_WINDOW_TYPE = "market_validation_3_trading_days"
CHROME_ONLY_ACQUISITION = True
CHROME_CAPTURE_REQUIRED_MESSAGE = "BLOCKED: production acquisition requires the logged-in Google Chrome capture bridge; direct HTTP/web requests are mechanically disabled"
AS_OF_ENV = "A_SHARE_SENTIMENT_AS_OF"
LIANBAN_STATUS_ENV = "CODEX_LIANBAN_STATUS"
LIANBAN_SNAPSHOT_ENV = "CODEX_LIANBAN_SNAPSHOT"
DUANXIANXIA_SNAPSHOT_ENV = "CODEX_DUANXIANXIA_SNAPSHOT"
TDX_ROOT = Path(r"C:\new_tdx_mock")
TDX_BLOCK_ROOT = TDX_ROOT / "T0002" / "blocknew"
TDX_DAY_RECORD = struct.Struct("<IIIIIfII")

SOURCE_LAYERS = {
    "官方公告": {"国家医保局", "教育部", "中科院合肥物质院", "交易所公告", "公司公告"},
    "主流财经": {"财联社", "金十数据", "东方财富", "同花顺", "中国经济网", "大智慧", "腾讯网", "中国新闻网", "证券时报", "中国证券报", "上海证券报", "新浪财经", "主流财经", "财闻", "财经平台", "指数宽度", "市场情绪", "主线热点"},
    "交易复盘": {"交易复盘", "涨停复盘", "龙虎榜"},
    "机构渠道": {"机构调研", "券商研报", "融资数据", "财闻数据"},
    "游资社区": {"淘股吧", "短线复盘"},
    "散户社区": {"雪球", "微博", "知乎", "东方财富股吧", "同花顺热榜"},
    "研究社区": {"韭研公社"},
    "海外映射": {"港股市场", "海外映射", "新浪财经"},
    "风险公告": {"风险公告", "公司公告", "交易所公告"},
    "产业数据": {"生意社"},
}

REQUIRED_SENTIMENT_SOURCES = [
    "淘股吧",
    "雪球",
    "微博",
    "知乎",
    "东方财富股吧",
    "韭研公社",
    "财联社",
    "金十数据",
]
MANDATORY_SENTIMENT_MIN_PER_SOURCE = 10
MANDATORY_SENTIMENT_CHANNEL = "mandatory_eight_site_sentiment"
# Compatibility names for historical callers. These sources are mandatory and
# participate in the unified event pool; they are no longer supplemental.
REQUIRED_SOCIAL_PLATFORMS = REQUIRED_SENTIMENT_SOURCES
SUPPLEMENTAL_FIVE_SITE_CHANNEL = MANDATORY_SENTIMENT_CHANNEL
SUPPLEMENTAL_PUBLIC_READONLY_CHANNEL = MANDATORY_SENTIMENT_CHANNEL
CHROME_CAPTURE_ENV = "A_SHARE_CHROME_CAPTURE_DIR"
BUSINESS_SOCIETY_CAPTURE_FILE = "business_society.json"
PUBLIC_READONLY_FALLBACK_ENV = "A_SHARE_SENTIMENT_ALLOW_PUBLIC_READONLY_FALLBACK"
PUBLIC_READONLY_FALLBACK_CHANNEL = "public_readonly_fallback"
CHROME_CAPTURE_MAX_AGE_MINUTES = 45
REQUIRED_PRIMARY_SOURCE_LAYERS = {"主流财经", "交易复盘", "机构渠道"}
MANDATORY_SENTIMENT_CAPTURE_FILES = {
    "tgb": "淘股吧",
    "xueqiu": "雪球",
    "weibo": "微博",
    "zhihu": "知乎",
    "guba": "东方财富股吧",
    "jiuyangongshe": "韭研公社",
    "cls": "财联社",
    "jin10": "金十数据",
}
FIVE_SITE_CAPTURE_FILES = MANDATORY_SENTIMENT_CAPTURE_FILES
FIVE_SITE_MIN_CLEAN_PER_SITE = MANDATORY_SENTIMENT_MIN_PER_SOURCE
FIVE_SITE_CHANNEL_MIN_CLEAN = {
    PUBLIC_READONLY_FALLBACK_CHANNEL: MANDATORY_SENTIMENT_MIN_PER_SOURCE,
}
FIVE_SITE_MIN_EVENT_POOL_PER_SITE = MANDATORY_SENTIMENT_MIN_PER_SOURCE
FIVE_SITE_CAPTURE_ROOTS = [
    WORKSPACE / "reports" / "five-site-a-share",
    WORKSPACE / "reports" / "五站A股舆情研判",
]
MANDATORY_PARTICIPANT_LAYERS = {"机构渠道"}
MANDATORY_FEEDBACK_LAYERS = {"交易复盘"}

REQUIRED_LABELS = [
    "明确结论",
    "事实证据",
    "逻辑分析",
    "情绪与资金行为",
    "产业链与观察标的",
    "下一步观察",
    "失效风险",
]

EVIDENCE_HEADERS = ["序号", "来源", "日期", "事件", "市场含义"]
EVIDENCE_TABLE_INDEXES = [6, 10, 14, 18, 22]

FORBIDDEN_TERMS = [
    "移动版", "网页版", "首页", "快讯", "新闻", "要闻", "金融", "评论", "产经", "创投", "滚动",
    "视频", "直播", "路演", "投资", "新股", "基金", "港美股", "数据资讯", "盯盘面", "看资",
    "责编", "责任编辑", "证券时报网", "客户端", "APP", "更多", "星期", "http", ".cn", ".com",
    "col", "index", "html", "关于我们", "测试", "平台", "验证", "机制", "红包", "责任编辑",
    "Copyright", "Hithink", "Flush", "手机用户", "点击", "下载", "登录", "注册",
    "主管主办", "法定信息披露", "习近平主持",
]

# 兼容早期函数名；真实运行只从 dynamic_source_urls() 的入口页发现本轮文章。
# 禁止在技能源码中锁定带日期的历史文章 URL，避免旧文章被误当作本轮证据。
SOURCE_URLS = []

MARKET_WIDE_QUERY_TERMS = (
    "A股", "股市", "股票", "大盘", "行情",
    "指数", "上证指数", "深证成指", "创业板指", "科创50",
    "成交额", "成交量", "放量", "缩量",
    "主力资金", "资金流向", "净流入", "净流出", "融资",
    "上涨家数", "下跌家数", "涨跌比", "涨停", "跌停",
    "市场情绪", "赚钱效应", "风险偏好", "热点", "龙头", "概念", "产业链",
    "盘中", "收评", "复盘", "盘前", "盘后",
)
MARKET_WIDE_QUERY_GROUP_SIZE = 6

NATIVE_DISCOVERY_URLS = (
    ("财联社", "https://www.cls.cn/telegraph"),
    ("财联社", "https://www.cls.cn/stock"),
    ("东方财富", "https://finance.eastmoney.com/a/cgsxw.html"),
    ("东方财富", "https://finance.eastmoney.com/"),
    ("同花顺", "https://stock.10jqka.com.cn/fupan/"),
    ("同花顺", "https://stock.10jqka.com.cn/"),
    ("同花顺热榜", "https://stock.10jqka.com.cn/hotstock/"),
    ("证券时报", "https://www.stcn.com/article/list/kx.html"),
    ("证券时报", "https://www.stcn.com/stock/"),
    ("中国证券报", "https://www.cs.com.cn/"),
    ("上海证券报", "https://www.cnstock.com/"),
    ("新浪财经", "https://finance.sina.com.cn/stock/"),
    ("机构调研", "https://data.eastmoney.com/jgdy/"),
    ("融资数据", "https://data.eastmoney.com/rzrq/"),
    ("韭研公社", "https://www.jiuyangongshe.com/study_hot"),
    ("金十数据", "https://www.jin10.com/"),
    ("港股市场", "https://stock.finance.sina.com.cn/hkstock/quotes/HSI.html"),
    ("交易所公告", "https://www.sse.com.cn/disclosure/listedinfo/announcement/"),
    ("交易所公告", "https://www.szse.cn/disclosure/listed/notice/index.html"),
)

FIVE_SITE_NATIVE_DISCOVERY = (
    ("淘股吧", "https://www.tgb.cn/", "tgb.cn"),
    ("雪球", "https://xueqiu.com/today", "xueqiu.com"),
    ("微博", "https://s.weibo.com/top/summary?cate=finance", "weibo.com"),
    ("知乎", "https://www.zhihu.com/hot", "zhihu.com"),
    ("东方财富股吧", "https://guba.eastmoney.com/", "guba.eastmoney.com"),
    ("韭研公社", "https://www.jiuyangongshe.com/study_hot", "jiuyangongshe.com"),
    ("财联社", "https://www.cls.cn/telegraph", "cls.cn"),
    ("金十数据", "https://www.jin10.com/", "jin10.com"),
)
FIVE_SITE_WIDE_TERMS = ("A股", "复盘", "市场情绪", "热点", "龙头", "产业链")
FIVE_SITE_MARKET_TERMS = tuple(dict.fromkeys((*MARKET_WIDE_QUERY_TERMS, "市场", "板块", "题材", "主线", "反弹", "支撑")))

# 历史搜索入口永久停用；真实采集查询只由 36 个宽口径词和交易日期生成。
SEARCH_QUERIES = []

VALUE_SIGNAL_WORDS = [
    "A股", "三大指数", "指数", "大盘", "板块", "题材", "主线", "热点", "情绪",
    "政策", "监管", "交易所", "公告", "澄清", "风险", "问询", "减持", "业绩",
    "涨停", "跌停", "连板", "成交额", "放量", "缩量", "反弹", "回调", "分歧",
    "融资", "机构调研", "龙虎榜", "北向", "基金", "游资", "散户", "股吧", "复盘",
    "产业链", "订单", "供给", "需求", "产能", "库存", "价格", "涨价", "出海",
    "港股", "美股", "海外", "商品", "汇率", "利率",
]

MARKET_IMPACT_WORDS = [
    "A股", "三大指数", "指数", "大盘", "科创", "创业板", "成交额", "放量", "缩量",
    "涨停", "跌停", "连板", "龙虎榜", "融资", "机构调研", "游资", "散户", "股吧",
    "短线", "情绪", "主线", "热点", "题材", "分歧", "反弹", "回落",
    "涨超", "走强", "活跃", "拉升", "融资净买入", "机构买入", "净买入",
]

IMPORTANT_EVENT_WORDS = [
    "政策", "监管", "目录", "公告", "澄清", "风险", "问询", "减持", "业绩",
    "订单", "中标", "合同", "签约", "交付", "涨价", "降价", "调价", "产能", "供给", "需求", "库存",
    "并购", "重组", "回购", "增持", "获批", "扩容", "实施", "落地", "商业化", "投产", "停产", "试验",
]

INDUSTRY_CHAIN_SIGNAL_WORDS = [
    "产业链", "订单", "供给", "需求", "产能", "库存", "价格", "涨价", "客户",
    "产品", "材料", "设备", "渠道", "支付", "商业化", "出海", "上游", "下游",
]

STOP_WORDS = set(FORBIDDEN_TERMS + [
    "来源", "日期", "事件", "市场", "公司", "股份", "集团", "证券", "显示", "表示", "相关",
    "今日", "昨日", "今天", "昨天", "明天", "记者", "多个", "进行", "成为", "发布", "获得", "今年", "中国", "北京",
    "上海", "深圳", "万元", "亿元", "近日", "产业", "板块", "方向", "资金", "交易", "公告",
    "财联社", "证券时报", "东方财富", "同花顺", "中国证券报", "新浪", "新浪财经", "淘股吧",
    "交易所", "教育部", "国家医保局", "中科院", "时报", "时报网", "文章", "专题", "正文",
    "点击", "查看", "下载", "登录", "注册", "责任编辑", "动态", "财经", "服务", "清单",
    "打赏", "回复", "转发", "关注", "点赞", "浏览", "阅读", "分享", "收藏",
    "col", "index", "html", "SZ", "SH", "官方", "关于我们", "数据", "行情", "股票",
    "多只", "强势", "活跃", "盘面上", "测试", "平台", "验证", "机制", "红包", "日讯",
    "日上午", "日下午", "2026年", "2025年", "2024年", "0日", "李在明",
])

BAD_LABEL_WORDS = STOP_WORDS | {
    "官方", "关于我们", "数据", "行情", "股票", "测试", "平台", "验证", "机制", "红包",
    "更多", "责任编辑", "动态", "盘面上", "多只", "强势", "活跃", "收评", "午评",
    "声明", "换一换", "自选股", "股海", "辣眼睛", "半场", "关于", "我们", "客户端",
    "登录", "注册", "账户", "评论", "收藏", "分享", "摘要", "导读", "栏目", "频道",
    "正文", "首页", "快讯", "专题", "博客", "论坛", "网友", "浏览", "阅读",
    "行业", "个股", "三大", "A股", "涨停", "科技", "指数", "大盘", "港股", "美股",
    "期货", "成交额", "市场", "热点", "题材", "情绪", "存在", "提示", "风险",
    "创业板", "科创板", "主板", "北交所", "信披", "深股通", "沪股通", "全部",
    "地方", "截至", "指涨", "指跌", "收盘", "集体", "上涨", "下跌", "反弹",
    "翻红", "探底", "回升", "波动", "需求", "情形", "过热", "逻辑", "领涨",
    "深证", "机构", "换手率", "未来", "较大", "持续", "周期",
}

GENERIC_LABEL_WORDS = {
    "A股", "涨停", "科技", "指数", "大盘", "港股", "美股", "期货", "成交额",
    "市场", "热点", "题材", "情绪", "存在", "提示", "风险", "资金", "反弹",
    "强势", "活跃", "板块", "方向", "个股", "设备", "通用设备", "专用设备",
    "交易反馈事实", "资金流事实", "披露", "机构席位事实", "商业",
    "创业板", "科创板", "主板", "北交所", "信披", "深股通", "沪股通", "全部",
    "地方", "截至", "指涨", "指跌", "收盘", "集体", "上涨", "下跌", "翻红",
    "探底", "回升", "波动", "需求", "情形", "过热", "逻辑", "领涨",
    "深证", "机构", "换手率", "未来", "较大", "持续", "周期",
}

SPECIFIC_LABEL_HINTS = {
    # 原有线索词
    "硬件", "算力", "液冷", "存储", "设备", "材料", "电子", "芯片", "半导体",
    "机器人", "医保", "创新药", "药品", "目录", "教育", "订单", "价格", "涨价",
    "物流", "仓储", "光伏", "煤电", "电力", "核聚变", "特气", "封装", "HBM",
    "CPO", "服务器", "电源", "功率", "模拟", "器件",
    "光学", "光电", "通信", "专用设备", "通用设备", "汽车零部", "医疗器械",
    "化学制品", "电池", "风电", "基础建设", "元件", "消费电子",
    # 从 DOMAIN_PHRASES 同步的具体词（2026-07-08 修复 cluster name 噪声）
    "算力硬件", "半导体设备", "半导体材料", "光学光电", "通信设备",
    "存储芯片", "汽车零部件", "医保目录", "商保创新药",
    "化学制品", "电池", "风电设备", "电子特气", "功率半导体", "模拟芯片",
    "先进封装", "光通信", "算力", "芯片", "医药", "CRO", "PCB", "电子布",
    "MLCC", "固态电池", "商业航天", "低空经济", "有色金属", "稀土",
    "创新", "新药", "机械", "航天", "通信", "钢铁", "煤炭", "石化", "化工",
    "银行", "保险", "地产", "汽车", "家电", "食品", "饮料", "纺织", "服装",
    "传媒", "互联网", "软件", "数据库", "服务器", "网络安全", "信息安全",
    "人工智能", "数字化", "云计算", "大数据", "物联网", "区块链", "数字孪生",
    "新能源", "储能", "充电", "氢能", "核电", "水电", "太阳能", "风电",
}

DOMAIN_PHRASES = [
    "AI硬件", "算力硬件", "半导体设备", "半导体材料", "光学光电", "通信设备",
    "存储芯片", "液冷", "机器人", "通用设备", "专用设备", "汽车零部件",
    "创新药", "医保目录", "商保创新药", "医疗器械", "化学制品", "电池",
    "风电设备", "电子特气", "功率半导体", "模拟芯片", "先进封装",
    "光通信", "算力", "芯片", "半导体", "医药", "CRO", "PCB", "电子布",
    "MLCC", "固态电池", "商业航天", "低空经济", "有色金属", "稀土",
]

NOISE_WORDS = BAD_LABEL_WORDS | {
    "免责声明", "风险提示", "版权", "版权声明", "广告", "客服", "隐私", "换一换",
    "我的自选", "加自选", "客户端下载", "二维码", "扫一扫", "返回顶部",
    "Copyright", "认知升级", "习近平主持", "普通者", "对话风雨看盘",
    "主管主办", "法定信息披露", "电子报", "登录", "注册",
}

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "zh-CN,zh;q=0.9"}


def read_text(path):
    return path.read_text(encoding="utf-8")


def file_sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def template_profile(path):
    from docx import Document
    doc = Document(str(path))
    return {
        "sha256": file_sha256(path),
        "paragraphs": len(doc.paragraphs),
        "tables": len(doc.tables),
        "table_shapes": [[len(t.rows), len(t.columns)] for t in doc.tables],
    }


def verify_locked_template():
    if not LOCKED_TEMPLATE.exists():
        print(f"BLOCKED locked template missing: {LOCKED_TEMPLATE}")
        return None
    profile = template_profile(LOCKED_TEMPLATE)
    if profile["sha256"] != LOCKED_TEMPLATE_SHA256:
        print("BLOCKED locked template sha256 mismatch")
        print(f"expected={LOCKED_TEMPLATE_SHA256}")
        print(f"actual={profile['sha256']}")
        return None
    if profile["paragraphs"] != LOCKED_TEMPLATE_PARAGRAPHS or profile["tables"] != LOCKED_TEMPLATE_TABLES:
        print("BLOCKED locked template structure mismatch")
        print(json.dumps(profile, ensure_ascii=False, indent=2))
        return None
    if profile["table_shapes"] != LOCKED_TEMPLATE_SHAPES:
        print("BLOCKED locked template table-shape mismatch")
        print(json.dumps(profile["table_shapes"], ensure_ascii=False))
        return None
    return profile


def verify_output_skeleton(path, quiet=False):
    from docx import Document
    doc = Document(str(path))
    shapes = [[len(t.rows), len(t.columns)] for t in doc.tables]
    reasons = []
    if len(doc.paragraphs) != OUTPUT_PARAGRAPHS:
        reasons.append(f"output_paragraph_count={len(doc.paragraphs)} expected={OUTPUT_PARAGRAPHS}")
    if len(doc.tables) != OUTPUT_TABLES:
        reasons.append(f"output_table_count={len(doc.tables)} expected={OUTPUT_TABLES}")
    if shapes != LOCKED_TEMPLATE_SHAPES:
        reasons.append("output_table_shapes_changed=" + json.dumps(shapes, ensure_ascii=False))
    if reasons:
        if not quiet:
            print("BLOCKED output skeleton changed")
            for reason in reasons:
                print(reason)
        return 2
    return 0


def clean_text(text):
    text = str(text)
    for term in FORBIDDEN_TERMS:
        text = text.replace(term, "")
    text = re.sub(r"\b(col|index|html|SZ|SH)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _page_publication_metadata_text(soup):
    values = []
    for tag in soup.find_all("meta"):
        key = " ".join([
            str(tag.get("property", "")),
            str(tag.get("name", "")),
            str(tag.get("itemprop", "")),
        ]).lower()
        if any(marker in key for marker in ["publish", "date", "time", "created", "modified"]):
            value = tag.get("content") or tag.get("value")
            if value:
                values.append(str(value))
    for tag in soup.find_all("time"):
        value = tag.get("datetime") or tag.get_text(" ", strip=True)
        if value:
            values.append(str(value))
    for tag in soup.select('script[type="application/ld+json"]'):
        text = tag.get_text(" ", strip=True)
        for match in re.findall(r'"(?:datePublished|dateCreated|dateModified)"\s*:\s*"([^"]+)"', text):
            values.append(match)
    return " ".join(values)


def fetch_text(url, *, with_metadata=False, now=None):
    if CHROME_ONLY_ACQUISITION:
        raise RuntimeError(CHROME_CAPTURE_REQUIRED_MESSAGE)
    import requests
    from bs4 import BeautifulSoup
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8, stream=True)
        resp.raise_for_status()
        chunks = []
        size = 0
        max_bytes = 600_000
        for chunk in resp.iter_content(chunk_size=16384):
            if not chunk:
                continue
            chunks.append(chunk)
            size += len(chunk)
            if size >= max_bytes:
                break
        if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding
        html = b"".join(chunks).decode(resp.encoding or "utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        publication_metadata = _page_publication_metadata_text(soup)
        for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
            tag.decompose()
        for tag in soup.find_all(["header", "footer", "nav", "aside"]):
            tag.decompose()
        blocks = []
        for tag in soup.find_all(["h1", "h2", "h3", "p", "li", "td"]):
            text = clean_text(tag.get_text(" ", strip=True))
            if len(text) >= 18 and not is_noise_chunk(text):
                blocks.append(text)
        if len(" ".join(blocks)) >= 120:
            text = clean_text(" ".join(blocks))
        else:
            text = clean_text(soup.get_text(" ", strip=True))
        if not with_metadata:
            return text
        publication = extract_publication(publication_metadata, url, now)
        publication_source = "page_metadata"
        if not publication:
            publication = extract_publication(text[:1200], url, now)
            publication_source = "visible_page_text"
        return {
            "text": text,
            "publication": publication,
            "publication_source": publication_source if publication else "missing",
        }
    except Exception:
        return {"text": "", "publication": None, "publication_source": "fetch_error"} if with_metadata else ""


def fetch_soup(url):
    if CHROME_ONLY_ACQUISITION:
        raise RuntimeError(CHROME_CAPTURE_REQUIRED_MESSAGE)
    import requests
    from bs4 import BeautifulSoup
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding
        return BeautifulSoup(resp.text, "html.parser")
    except Exception:
        return None


def source_name_from_url(url):
    host = urlparse(url).netloc.lower()
    mapping = [
        ("cls.cn", "财联社"),
        ("jin10.com", "金十数据"),
        ("stcn.com", "证券时报"),
        ("caiwennews", "财闻"),
        ("jiuyangongshe.com", "韭研公社"),
        ("guba.eastmoney", "东方财富股吧"),
        ("data.eastmoney", "机构调研"),
        ("eastmoney", "东方财富"),
        ("weibo.com", "微博"),
        ("zhihu.com", "知乎"),
        ("10jqka", "同花顺"),
        ("xueqiu", "雪球"),
        ("sina.com", "新浪财经"),
        ("cs.com.cn", "中国证券报"),
        ("cnstock", "上海证券报"),
        ("tgb.cn", "淘股吧"),
        ("szse.cn", "交易所公告"),
        ("sse.com.cn", "交易所公告"),
        ("nhsa.gov.cn", "国家医保局"),
        ("moe.gov.cn", "教育部"),
        ("cas.cn", "中科院"),
    ]
    for key, name in mapping:
        if key in host:
            return name
    return "财经平台"


def source_layer(source):
    if str(source).endswith("·市场复盘"):
        return "交易复盘"
    for layer, names in SOURCE_LAYERS.items():
        if source in names:
            return layer
    return "其他来源"


def source_layers(sources):
    return {source_layer(source) for source in sources}


def item_evidence_sources(item):
    sources = {clean_text(str(item.get("source", "")))}
    explicit = item.get("evidence_sources")
    if isinstance(explicit, list):
        sources.update(clean_text(str(value)) for value in explicit)
    provenance = item.get("provenance")
    if isinstance(provenance, list):
        sources.update(
            clean_text(str(row.get("source", "")))
            for row in provenance if isinstance(row, dict)
        )
    return {source for source in sources if source}


def items_evidence_sources(items):
    return set().union(*(item_evidence_sources(item) for item in items)) if items else set()


def is_five_site_supplemental(item_or_source):
    return False


def primary_events(pool):
    return [item for item in pool if isinstance(item, dict)]


def supplemental_five_site_events(pool):
    return [
        item for item in pool
        if isinstance(item, dict)
        and item.get("source") in REQUIRED_SENTIMENT_SOURCES
    ]


def primary_source_layer_counts(pool):
    return Counter(source_layer(item.get("source", "")) for item in primary_events(pool))


def five_site_event_counts(pool):
    counts = Counter(item.get("source", "") for item in supplemental_five_site_events(pool))
    return dict(sorted((name, counts.get(name, 0)) for name in REQUIRED_SENTIMENT_SOURCES))


def mandatory_sentiment_source_audit(events, now=None):
    now = _china_datetime(now)
    source_counts = {}
    source_invalid_counts = {}
    source_duplicate_counts = {}
    source_quality_rejections = {}
    reasons = []
    required_fields = (
        "published_at",
        "url",
        "heat_evidence",
        "a_share_mapping",
    )
    for source in REQUIRED_SENTIMENT_SOURCES:
        valid = []
        invalid = 0
        duplicates = 0
        quality_rejections = Counter()
        seen = set()
        for item in events:
            if not isinstance(item, dict) or item.get("source") != source:
                continue
            event = clean_text(str(item.get("event", "")))
            missing = [
                field for field in required_fields
                if not clean_text(str(item.get(field, "")))
            ]
            url = str(item.get("url", "")).strip()
            key = (
                url,
                re.sub(r"\W+", "", event).casefold()[:220],
            )
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            if (
                missing
                or len(event) < 18
                or not url.startswith(("http://", "https://"))
                or not _is_current_event(item, now)
                or item.get("timestamp_kind") == "hotlist_observed_at"
                or social_ui_noise_hits(event)
            ):
                invalid += 1
                continue
            quality = validate_sentiment_record(
                source=source,
                event=event,
                heat_evidence=item.get("heat_evidence"),
                a_share_mapping=item.get("a_share_mapping"),
                rank=item.get("rank"),
            )
            if not quality["ok"]:
                invalid += 1
                quality_rejections.update(quality["reasons"])
                continue
            valid.append(item)
        source_counts[source] = len(valid)
        source_invalid_counts[source] = invalid
        source_duplicate_counts[source] = duplicates
        source_quality_rejections[source] = dict(quality_rejections)
        if len(valid) < MANDATORY_SENTIMENT_MIN_PER_SOURCE:
            reasons.append(f"{source}:valid_count_lt_{MANDATORY_SENTIMENT_MIN_PER_SOURCE}")
    return {
        "ok": not reasons,
        "window_hours": EVENT_WINDOW_HOURS,
        "required_sources": list(REQUIRED_SENTIMENT_SOURCES),
        "minimum_per_source": MANDATORY_SENTIMENT_MIN_PER_SOURCE,
        "source_counts": source_counts,
        "invalid_counts": source_invalid_counts,
        "duplicate_counts": source_duplicate_counts,
        "quality_rejections": source_quality_rejections,
        "reasons": reasons,
    }


def _market_validation_dimensions(item):
    explicit = item.get("validation_dimensions")
    if isinstance(explicit, list):
        return {
            str(value) for value in explicit
            if str(value) in {"热点", "板块", "涨停", "晋级", "成交额"}
        }
    text = clean_text(str(item.get("event", "")))
    dimensions = set()
    if any(term in text for term in ("热点", "主题", "概念", "主线", "方向")):
        dimensions.add("热点")
    if any(term in text for term in ("板块", "概念", "行业", "方向")):
        dimensions.add("板块")
    if "涨停" in text:
        dimensions.add("涨停")
    if any(term in text for term in ("晋级", "连板", "进2", "进3", "进4", "进5", "进6", "进7")):
        dimensions.add("晋级")
    if any(term in text for term in ("成交额", "成交总额", "两市成交")):
        dimensions.add("成交额")
    return dimensions


def market_cross_validation_audit(events):
    source_channels = {
        "连板网": "lianban_daily_market_cross_validation",
        "通达信": "tdx_local_market_cross_validation",
        "短线侠": "duanxianxia_market_cross_validation",
    }
    present_sources = []
    source_dimensions = {}
    for source, channel in source_channels.items():
        matching = [
            item for item in events
            if isinstance(item, dict)
            and (
                item.get("source_channel") == channel
                or str(item.get("source", "")).startswith(source)
            )
        ]
        if matching:
            present_sources.append(source)
        source_dimensions[source] = sorted(set().union(
            *(_market_validation_dimensions(item) for item in matching)
        ) if matching else set())
    missing_sources = [
        source for source in source_channels if source not in present_sources
    ]
    required_dimensions = ["热点", "板块", "涨停", "晋级", "成交额"]
    dimension_sources = {
        dimension: [
            source for source in source_channels
            if dimension in source_dimensions[source]
        ]
        for dimension in required_dimensions
    }
    weak_dimensions = [
        dimension for dimension, sources in dimension_sources.items()
        if len(sources) < 2
    ]
    reasons = [f"missing_source:{source}" for source in missing_sources]
    reasons.extend(
        f"{dimension}:cross_validation_source_count_lt_2"
        for dimension in weak_dimensions
    )
    return {
        "ok": not reasons,
        "present_sources": present_sources,
        "missing_sources": missing_sources,
        "source_dimensions": source_dimensions,
        "dimension_sources": dimension_sources,
        "weak_dimensions": weak_dimensions,
        "reasons": reasons,
    }


@lru_cache(maxsize=1)
def known_stock_names():
    import csv
    names = set()
    files = [
        "ak_stock_zt_pool_em_20260630.csv",
        "ak_stock_lhb_detail_em_20260630.csv",
        "limitup_lhb_intersection_20260630.csv",
        "push2_fund_flow_resolved_20260630.csv",
    ]
    for filename in files:
        path = LOCAL_REVIEW_DIR / filename
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                name = str(row.get("名称", "")).strip()
                if len(name) >= 2 and not any(bad in name for bad in ["主力", "超大单", "榜单", "今日", "昨日"]):
                    names.add(name)
    return names


def _historical_discover_urls_disabled(max_urls=16):
    raise RuntimeError("historical URL discovery is permanently disabled")
    import requests
    from bs4 import BeautifulSoup
    urls = []
    seen = {url for _source, url in SOURCE_URLS}
    blocked_hosts = ("bing.com", "microsoft.com", "baidu.com")
    for query in SEARCH_QUERIES:
        search_url = "https://www.bing.com/search?q=" + quote_plus(query)
        try:
            resp = requests.get(search_url, headers=HEADERS, timeout=12)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception:
            continue
        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            if not href.startswith("http"):
                continue
            host = urlparse(href).netloc.lower()
            if any(bad in host for bad in blocked_hosts):
                continue
            if href in seen:
                continue
            if not any(key in host for key in ["cls", "stcn", "eastmoney", "10jqka", "xueqiu", "sina", "cs.com", "cnstock", "tgb", "sse", "szse", "nhsa", "moe", "cas"]):
                continue
            seen.add(href)
            urls.append((source_name_from_url(href), href))
            if len(urls) >= max_urls:
                return urls
        time.sleep(0.1)
    return urls


def _historical_collect_search_result_events_disabled():
    raise RuntimeError("historical non-whitelisted search queries are permanently disabled")
    import requests
    from bs4 import BeautifulSoup
    events = []
    query_specs = []
    for day in recent_trading_dates():
        date_text = f"{day.year}年{day.month}月{day.day}日"
        query_specs.extend([
            (f"{date_text} A股 收评 成交额 涨跌家数", "主流财经"),
            (f"{date_text} A股 涨停复盘 连板 情绪", "交易复盘"),
            (f"{date_text} A股 龙虎榜 机构调研 融资", "机构调研"),
            (f"{date_text} A股 公告 业绩 订单 产业链", "主流财经"),
        ])
    for query, source_hint in query_specs:
        try:
            resp = requests.get("https://www.bing.com/search?q=" + quote_plus(query), headers=HEADERS, timeout=12)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception:
            continue
        for item in soup.select("li.b_algo")[:8]:
            title = clean_text(item.get_text(" ", strip=True))
            if len(title) < 30:
                continue
            link = item.find("a", href=True)
            url = link["href"] if link else ""
            source = source_hint or (source_name_from_url(url) if url else "主流财经")
            if event_importance_score(title, source) < 35:
                continue
            events.append({
                "source": source,
                "date": extract_recent_date(title, url) or cn_date(recent_trading_dates()[-1]),
                "event": title[:180],
                "url": url,
            })
        time.sleep(0.1)
    return events


def _historical_discover_source_article_urls_disabled(max_per_source=10):
    raise RuntimeError("historical article discovery is permanently disabled")
    urls = []
    seen = {url for _source, url in SOURCE_URLS}
    article_markers = [
        "202606", "2026-06", "/a/2026", "/doc-", "/commonDetail/", "/topicDetail/",
        "/article/detail/", "/c677", "/bbs/",
    ]
    for source, entry_url in SOURCE_URLS:
        soup = fetch_soup(entry_url)
        if not soup:
            continue
        picked = 0
        for tag in soup.find_all("a", href=True):
            title = clean_text(tag.get_text(" ", strip=True))
            if len(title) < 8 or is_noise_chunk(title):
                continue
            href = urljoin(entry_url, tag["href"])
            host = urlparse(href).netloc.lower()
            if not host or href in seen:
                continue
            if not any(marker in href for marker in article_markers):
                continue
            if not any(key in host for key in ["cls", "stcn", "eastmoney", "10jqka", "xueqiu", "sina", "cs.com", "cnstock", "tgb", "sse", "szse", "nhsa", "moe", "cas"]):
                continue
            if value_signal_score(title) < 1:
                continue
            seen.add(href)
            urls.append((source_name_from_url(href) if source == "财经平台" else source, href))
            picked += 1
            if picked >= max_per_source:
                break
        time.sleep(0.1)
    return urls


def extract_chunks(text, source="", max_chunks=22):
    parts = re.split(r"(?<=[。！？；])\s*", text)
    expanded_parts = []
    for part in parts:
        if len(part) > 260:
            expanded_parts.extend(re.split(r"(?<=[，,])\s*", part))
        else:
            expanded_parts.append(part)
    chunks = []
    low_threshold_sources = {"国家医保局", "教育部", "中科院合肥物质院", "交易所公告", "淘股吧", "雪球", "东方财富股吧", "同花顺热榜", "港股市场"}
    for part in expanded_parts:
        part = clean_text(part)
        if len(part) < 25:
            continue
        if is_noise_chunk(part):
            continue
        threshold = 35 if source in low_threshold_sources else 28
        score = event_importance_score(part, source)
        if score >= threshold or (len(part) >= 120 and score >= threshold - 12):
            chunks.append(part[:180])
        if len(chunks) >= max_chunks:
            break
    return chunks


def value_signal_score(text):
    groups = [
        ["A股", "三大指数", "指数", "大盘", "板块", "题材", "主线", "热点", "情绪"],
        ["政策", "政策解读", "监管", "交易所", "公告", "澄清", "风险", "问询", "减持", "业绩"],
        ["涨停", "跌停", "连板", "成交额", "放量", "缩量", "反弹", "回调", "分歧"],
        ["融资", "机构调研", "龙虎榜", "北向", "游资", "散户", "股吧", "复盘"],
        ["产业链", "订单", "供给", "需求", "产能", "库存", "价格", "涨价", "调价", "出海"],
        ["港股", "美股", "海外", "商品", "汇率", "利率"],
    ]
    return sum(1 for group in groups if any(word in text for word in group))


def event_importance_score(text, source=""):
    text = clean_text(text)
    score = 0
    market_hits = sum(1 for w in MARKET_IMPACT_WORDS if w in text)
    important_hits = sum(1 for w in IMPORTANT_EVENT_WORDS if w in text)
    chain_hits = sum(1 for w in INDUSTRY_CHAIN_SIGNAL_WORDS if w in text)
    if market_hits:
        score += min(35, market_hits * 7)
    if important_hits:
        score += min(35, important_hits * 6)
    if chain_hits:
        score += min(20, chain_hits * 5)
    if source_layer(source) in {"交易复盘", "机构渠道", "游资社区", "散户社区"}:
        score += 10
    if source_layer(source) in {"官方公告", "风险公告"} and any(w in text for w in ["政策", "目录", "公告", "澄清", "风险", "问询"]):
        score += 10
    if len(text) < 35:
        score -= 20
    if not any(w in text for w in ["A股", "涨停", "成交额", "龙虎榜", "资金", "情绪", "产业链", "订单", "政策", "公告", "风险", "板块", "指数", "调研", "股吧", "短线"]):
        score -= 30
    return max(0, score)


def is_noise_chunk(text):
    residue_hits = sum(text.count(str(w)) for w in NOISE_WORDS)
    value_hits = sum(text.count(w) for w in VALUE_SIGNAL_WORDS)
    if any(str(w) in text for w in NOISE_WORDS) and value_hits <= 2:
        return True
    return residue_hits >= 2 and value_hits <= 1


def normalize_label_word(word):
    word = clean_text(word)
    word = re.sub(r"[：:，,。；;！!？?\[\]【】（）()“”\"'、/\\|]+", "", word)
    word = re.sub(r"[-_.…]+", "", word)
    return word.strip()


def _historical_collect_event_pool_disabled():
    raise RuntimeError("historical static-source collector is permanently disabled")
    now = datetime.now(timezone(timedelta(hours=8)))
    pool = []
    seen = set()
    source_urls = SOURCE_URLS + discover_source_article_urls() + discover_urls()
    for source, url in source_urls:
        page = fetch_text(url)
        if not page:
            continue
        for chunk in extract_chunks(page, source=source):
            key = re.sub(r"\W+", "", chunk)[:80]
            if key in seen:
                continue
            seen.add(key)
            date = "6月30日"
            if "2026-06-30" in page or "6月30" in chunk:
                date = "6月30日"
            elif "2026-06-29" in page or "6月29" in chunk:
                date = "6月29日"
            if "2026-06-28" in page or "6月28" in chunk:
                date = "6月28日"
            if "2026-06-27" in page or "6月27" in chunk:
                date = "6月27日"
            pool.append({"source": source, "date": date, "event": chunk, "url": url})
        time.sleep(0.1)
    pool.extend(collect_search_result_events())
    pool.extend(collect_local_trade_review_events(now))
    return pool


def collect_local_trade_review_events(now):
    import csv
    events = []
    industry_path = LOCAL_REVIEW_DIR / "industry_limitup_stats_20260630.csv"
    lhb_path = LOCAL_REVIEW_DIR / "limitup_lhb_intersection_20260630.csv"
    zt_path = LOCAL_REVIEW_DIR / "ak_stock_zt_pool_em_20260630.csv"
    name_industry = {}
    industry_names = defaultdict(list)
    for map_path in [zt_path, lhb_path]:
        if map_path.exists():
            with map_path.open("r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    name = row.get("名称", "")
                    industry = row.get("所属行业", "") or row.get("行业", "")
                    if name and industry:
                        name_industry[name] = industry
                        if name not in industry_names[industry]:
                            industry_names[industry].append(name)
    if industry_path.exists():
        with industry_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in list(csv.DictReader(f))[:18]:
                industry = row.get("行业", "")
                count = row.get("涨停数", "")
                if industry and count:
                    events.append({
                        "source": "交易复盘",
                        "date": "6月30日",
                        "event": f"6月30日交易复盘显示，{industry}方向涨停数为{count}家，属于当日资金实际交易反馈。",
                        "url": str(industry_path),
                    })
    if lhb_path.exists():
        with lhb_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in list(csv.DictReader(f))[:40]:
                name = row.get("名称", "")
                industry = row.get("所属行业", "")
                amount = row.get("成交额", "")
                turnover = row.get("换手率", "")
                if name and industry:
                    events.append({
                        "source": "龙虎榜",
                        "date": "6月30日",
                        "event": f"{name}进入涨停与龙虎榜交集，所属环节为{industry}，成交额{amount}，换手率{turnover}，显示资金对该环节有交易反馈。",
                        "url": str(lhb_path),
                    })
    lhb_detail_path = LOCAL_REVIEW_DIR / "ak_stock_lhb_detail_em_20260630.csv"
    if lhb_detail_path.exists():
        with lhb_detail_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in list(csv.DictReader(f))[:80]:
                name = row.get("名称", "")
                reason = row.get("上榜原因", "")
                interp = row.get("解读", "")
                net = row.get("龙虎榜净买额", "")
                amount = row.get("龙虎榜成交额", "")
                if name and (reason or interp):
                    src = "机构调研" if "机构" in interp else "短线复盘"
                    industry = name_industry.get(name, "")
                    industry_text = f"所属环节为{industry}，" if industry else ""
                    events.append({
                        "source": src,
                        "date": "6月30日",
                        "event": f"{name}龙虎榜上榜，{industry_text}原因是{reason}，席位解读为{interp}，净买额{net}，榜单成交额{amount}，反映机构或短线资金对该产业链环节的真实博弈。",
                        "url": str(lhb_detail_path),
                    })
    fund_path = LOCAL_REVIEW_DIR / "push2_fund_flow_resolved_20260630.csv"
    if fund_path.exists():
        with fund_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in list(csv.DictReader(f))[:80]:
                name = row.get("名称", "")
                main = row.get("主力净流入", "")
                super_big = row.get("超大单净流入", "")
                pct = row.get("主力净占比", "")
                change = row.get("涨跌幅", "")
                if name and main:
                    industry = name_industry.get(name, "")
                    industry_text = f"所属环节为{industry}，" if industry else ""
                    events.append({
                        "source": "融资数据",
                        "date": "6月30日",
                        "event": f"{name}资金流显示{industry_text}主力净流入{main}，超大单净流入{super_big}，主力净占比{pct}，涨跌幅{change}，反映机构化大单资金对该产业链环节的参与强度。",
                        "url": str(fund_path),
                    })
    if zt_path.exists():
        with zt_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in list(csv.DictReader(f))[:60]:
                name = row.get("名称", "")
                industry = row.get("所属行业", "")
                board = row.get("连板数", "") or row.get("连续涨停", "")
                if name and industry:
                    events.append({
                        "source": "涨停复盘",
                        "date": "6月30日",
                        "event": f"{name}涨停，所属环节为{industry}，连板信息{board}，提供短线热点和产业链映射证据。",
                        "url": str(zt_path),
                    })
    for industry, names in sorted(industry_names.items(), key=lambda item: len(item[1]), reverse=True)[:18]:
        if len(names) < 3:
            continue
        sample = "、".join(names[:8])
        events.append({
            "source": "短线复盘",
            "date": "6月30日",
            "event": f"短线复盘显示，{industry}方向出现{len(names)}只涨停或龙虎榜反馈标的，代表样本包括{sample}，说明该方向并非单一个股异动，而是有行业样本集中和短线资金辨识度。",
            "url": str(zt_path),
        })
    return events


def keyword_label(items, topn=4):
    text = clean_text(" ".join(x["event"] for x in items))
    phrase_counter = Counter()
    for phrase in DOMAIN_PHRASES:
        count = text.count(phrase)
        if count:
            phrase_counter[phrase] += count + 3
    words = []
    try:
        import jieba
        import jieba.analyse
        jieba.setLogLevel(20)
        words.extend(jieba.analyse.extract_tags(text, topK=45, withWeight=False))
        words.extend(jieba.lcut(text))
    except Exception:
        pass
    words.extend(re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]{2,8}", text))
    counter = Counter()
    for word in words:
        word = normalize_label_word(word)
        if word in STOP_WORDS or word in BAD_LABEL_WORDS:
            continue
        if word.lower() in {str(x).lower() for x in STOP_WORDS}:
            continue
        if any(bad in word for bad in BAD_LABEL_WORDS):
            continue
        if any(term in word for term in FORBIDDEN_TERMS):
            continue
        if re.fullmatch(r"[A-Za-z]{3,}", word):
            continue
        if re.fullmatch(r"[-_.…]+", word):
            continue
        if re.search(r"20\d{2}|^\d+日$|^\d+月$|^\d+年$|^\d+月\d+日$", word):
            continue
        if len(word) < 2 or len(word) > 10:
            continue
        if re.fullmatch(r"\d+", word):
            continue
        if value_signal_score(word) == 0 and not any(w in text for w in [word]):
            continue
        counter[word] += 1
    picked = []
    for word, _count in phrase_counter.most_common(20):
        if word in BAD_LABEL_WORDS or word in GENERIC_LABEL_WORDS:
            continue
        picked.append(word)
        if len(picked) >= topn:
            return " / ".join(picked)
    for word, _count in counter.most_common(40):
        if any(word in old or old in word for old in picked):
            continue
        picked.append(word)
        if len(picked) >= topn:
            break
    return " / ".join(picked) if picked else "自然聚类方向"


def label_is_clean(label):
    tokens = [x.strip() for x in label.split("/")]
    meaningful = 0
    generic = 0
    specific = 0
    for token in tokens:
        if not token:
            continue
        if token in BAD_LABEL_WORDS:
            return False
        if token in GENERIC_LABEL_WORDS:
            generic += 1
            continue
        if any(bad in token for bad in BAD_LABEL_WORDS):
            return False
        if re.search(r"20\d{2}|^\d+日$|^\d+月$|^\d+年$|^\d+月\d+日$", token):
            return False
        if re.search(r"[-_.…]{2,}", token) or token in {"--", "...", "——"}:
            return False
        if token in SPECIFIC_LABEL_HINTS or any(hint in token for hint in SPECIFIC_LABEL_HINTS):
            specific += 1
        meaningful += 1
    if meaningful == 1 and specific == 1 and generic == 0:
        return True
    return meaningful >= 2 and meaningful > generic and specific >= 1


def _historical_kmeans_cluster_and_score_disabled(pool):
    raise RuntimeError("historical KMeans clustering is permanently disabled")
    if len(pool) < 3:
        return []
    try:
        from sklearn.cluster import KMeans
        from sklearn.feature_extraction.text import TfidfVectorizer
    except Exception as exc:
        print(f"BLOCKED sklearn unavailable: {exc}")
        return []

    docs = [clean_text(item["event"]) for item in pool]
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1, max_features=5000)
    matrix = vectorizer.fit_transform(docs)
    cluster_count = min(9, max(4, len(pool) // 24))
    labels = KMeans(n_clusters=cluster_count, n_init=20, random_state=20260630).fit_predict(matrix)

    grouped = defaultdict(list)
    for label, item in zip(labels, pool):
        grouped[int(label)].append(item)

    clusters = []
    for _label, items in grouped.items():
        sources = items_evidence_sources(items)
        if len(sources) < MIN_CLUSTER_SOURCES:
            continue
        layers = source_layers(sources)
        if len(layers) < MIN_CLUSTER_SOURCE_LAYERS:
            continue
        if not (layers & MANDATORY_FEEDBACK_LAYERS):
            continue
        if not (layers & MANDATORY_PARTICIPANT_LAYERS):
            continue
        merged = " ".join(x["event"] for x in items)
        chain_hits = sum(merged.count(word) for word in INDUSTRY_CHAIN_SIGNAL_WORDS)
        source_score = min(30, len(sources) * 6)
        heat_score = min(28, len(items) * 3)
        feedback_score = min(22, sum(merged.count(w) for w in ["涨停", "成交额", "融资", "调研", "龙虎榜", "热度", "反弹", "澄清", "风险"]) * 3)
        chain_score = min(15, chain_hits * 1.8)
        freshness_score = min(5, sum(1 for x in items if x["date"] in ["6月29日", "6月28日"]) * 0.8)
        score = int(min(100, source_score + heat_score + feedback_score + chain_score + freshness_score))
        if len(items) < 2 and score < 60:
            continue
        if score < 45:
            continue
        name = keyword_label(items)
        if not label_is_clean(name):
            continue
        quality = direction_evidence_quality({"items": items})
        if not quality["is_direction_level"]:
            continue
        clusters.append({
            "name": name,
            "items": items,
            "sources": sources,
            "score": score,
            "keywords": keyword_label(items, topn=8).split(" / "),
            "direction_quality": quality,
        })
    clusters.extend(keyword_group_clusters(pool))
    clusters = dedupe_clusters(clusters)
    clusters.sort(key=lambda x: x["score"], reverse=True)
    return clusters


def event_theme_keys(event):
    text = event["event"]
    keys = []
    for phrase in DOMAIN_PHRASES:
        if phrase in text:
            keys.append(phrase)
    if not keys:
        return []
    return keys[:3]


def keyword_group_clusters(pool):
    return []


def dedupe_clusters(clusters):
    deduped = []
    seen = set()
    for c in sorted(clusters, key=lambda x: (x["score"], len(x["items"]), len(x["sources"])), reverse=True):
        key = tuple(c.get("keywords", [])[:2]) or (c["name"],)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)
    return deduped


def _historical_score_breakdown_disabled(cluster):
    raise RuntimeError("historical non-causal scoring is permanently disabled")
    items = cluster["items"]
    sources = {x["source"] for x in items}
    merged = " ".join(x["event"] for x in items)
    impact = min(30, len(sources) * 5 + sum(1 for w in ["指数", "大盘", "政策", "监管", "海外", "产业链"] if w in merged) * 4)
    heat = min(25, len(items) * 2 + sum(merged.count(w) for w in ["涨停", "热度", "反弹", "成交额", "连板"]) * 3)
    fund = min(20, sum(merged.count(w) for w in ["资金", "龙虎榜", "融资", "调研", "成交额", "放量", "涨停"]) * 3)
    chain = min(15, sum(merged.count(w) for w in INDUSTRY_CHAIN_SIGNAL_WORDS) * 2)
    evidence = min(10, len(sources) * 2)
    fresh = min(10, sum(1 for x in items if x["date"] in ["6月30日", "6月29日", "6月28日"]) * 1)
    total = min(100, impact + heat + fund + chain + evidence + fresh)
    return {
        "direction": cluster["name"],
        "impact_scope": impact,
        "market_heat": heat,
        "fund_feedback": fund,
        "industry_chain_mapping": chain,
        "evidence_strength": evidence,
        "freshness": fresh,
        "total": total,
        "events": len(items),
        "sources": sorted(sources),
        "source_layers": sorted(source_layers(sources)),
        "keywords": cluster.get("keywords", []),
    }


def has_preset_board_bias(cluster):
    items = cluster.get("items", [])
    if not items:
        return True
    label_tokens = []
    for raw in re.split(r"[/、\s]+", cluster.get("name", "")):
        token = clean_theme_term(raw.strip())
        if token and token not in GENERIC_LABEL_WORDS:
            label_tokens.append(token)
    if len(label_tokens) < 1:
        return True
    item_texts = [clean_text(x.get("event", "")) for x in items]
    # Active causal labels must be grounded in repeated current-event text. A preset
    # dictionary entry is never accepted as a substitute for event-level grounding.
    grounded_tokens = 0
    for token in label_tokens:
        hits = sum(1 for text in item_texts if token in text)
        if hits >= LABEL_GROUNDING_MIN_HITS:
            grounded_tokens += 1
    if grounded_tokens < 1:
        return True
    merged = " ".join(item_texts)
    evidence_hits = value_signal_score(merged)
    chain_hits = sum(merged.count(w) for w in INDUSTRY_CHAIN_SIGNAL_WORDS)
    return evidence_hits < 2 and chain_hits < 1


def write_audit_files(out_dir, pool, clusters):
    now = _china_datetime()
    event_window_start, event_window_end = event_window_bounds(now)
    event_pool = [item for item in pool if _is_current_event(item, now)]
    market_validation_pool = [item for item in pool if _is_market_validation_event(item, now)]
    score_rows = [score_breakdown(c) for c in clusters]
    layer_counts = Counter(source_layer(x["source"]) for x in pool)
    audit = {
        "locked_template": str(LOCKED_TEMPLATE),
        "locked_template_sha256": LOCKED_TEMPLATE_SHA256,
        "event_pool_count": len(pool),
        "source_count": len({x["source"] for x in pool}),
        "source_layer_count": len(layer_counts),
        "source_layer_counts": dict(sorted(layer_counts.items())),
        "five_site_capture": five_site_capture_profile(),
        "five_site_event_counts_in_pool": dict(sorted(Counter(x["source"] for x in pool if x.get("source") in REQUIRED_SOCIAL_PLATFORMS).items())),
        "cluster_count": len(clusters),
        "generation_order": [
            "collect_recent_72h_full_source_event_pool",
            "write_event_pool_before_analysis",
            "deduplicate_and_filter_events",
            "discover_exact_themes_from_current_event_clauses",
            "build_catalyst_market_participant_counterevidence_chains",
            "apply_causal_grounding_uniqueness_and_direction_gates",
            "score_only_delivery_ready_causal_chains",
            "render_to_locked_template",
        ],
        "preset_board_pool_used": False,
        "blocked_if_preset_board_bias": True,
        "causal_method": "event_text_exact_theme_role_chain_v1",
        "causal_cluster_quality": [causal_chain_quality(c) for c in clusters[:5]],
        "red_line": "事件池先落盘；只对同主题触发、盘面、参与者和反证闭环评分；禁止预设板块、跨池补证据和模板补栏。",
    }
    write_json_text(out_dir / "a_share_sentiment_scores.json", score_rows)
    write_json_text(out_dir / "a_share_sentiment_audit.json", audit)


FIXED_DELIVERY_PHRASES = [
    "确认资金反馈和短线情绪强弱。",
    "确认政策预期和产业约束变化。",
    "提示题材证据链和高位风险再定价。",
    "确认产业链传导和受益方向。",
    "补充该方向的情绪、产业或交易证据。",
]

GENERIC_DELIVERY_PHRASES = [
    "重要方向",
    "看成交额",
    "涨停扩散",
    "核心容量票",
    "资金会优先",
    "资金偏好集中",
    "用于校验",
    "盘面观察",
    "重要/风险观察",
    "成交缩量",
    "公告澄清",
    "强势方向",
    "高频热词",
    "短线资金更偏向",
    "核心主线",
    "主线集中度高",
    "垃圾",
]

PROCESS_NARRATION_TERMS = [
    "正向解释",
    "反向解释",
    "每个信号",
    "必须同时",
    "最终落到",
    "把结论变成",
    "可验证条件",
    "用数据验证",
    "如何读",
    "说明性",
    "过程说明",
    "报告禁止",
    "本文用于",
    "报告用于",
    "本文来自",
    "数据口径",
    "限制说明",
    "自动事件池",
    "动态采集",
    "程序证明",
    "自我说明",
    "返工",
    "模板",
]

TEMPLATE_CONCLUSION_TERMS = [
    "默认结论",
    "固定措辞",
    "兜底判断",
    "旧数据",
    "旧版本结论",
    "模板默认",
    "看好",
    "看空",
    "五站热度不是单一方向的信号",
    "市场宽度信号",
    "分数0",
]

DELIVERY_NOISE_TERMS = [
    "所属环节为",
    "原因为",
    "成功率",
    "自动化设备备",
    "移动版",
    "网页版",
    "责任编辑",
    "http",
    ".com",
    ".cn",
] + PROCESS_NARRATION_TERMS + TEMPLATE_CONCLUSION_TERMS + FIXED_DELIVERY_PHRASES + GENERIC_DELIVERY_PHRASES

BANNED_REPORT_PHRASES = [
    "因果链待确认",
    "当前为待确认状态",
    "本轮未形成",
    "不输出板块",
    "只观察",
    "风险偏好链",
]

BANNED_REPORT_PATTERNS = {
    "不输出.*推荐": re.compile(r"不输出[^。；\n]{0,80}推荐"),
}


def report_banned_phrase_hits(text):
    text = str(text or "")
    hits = [phrase for phrase in BANNED_REPORT_PHRASES if phrase in text]
    hits.extend(name for name, pattern in BANNED_REPORT_PATTERNS.items() if pattern.search(text))
    return sorted(set(hits))


def read_json_or_none(path):
    try:
        io_path = _windows_io_path(path)
        if not io_path.exists():
            return None
        return json.loads(io_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def file_profile(path):
    path = Path(path)
    if not path.exists():
        return {"path": str(path), "exists": False}
    stat = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "size": stat.st_size,
        "mtime": datetime.fromtimestamp(stat.st_mtime, timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
        "sha256": file_sha256(path),
    }


def docx_visible_text(path):
    from docx import Document
    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts), doc


def _parse_iso_datetime(value):
    if not value:
        return None
    try:
        value = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(value)
        return _china_datetime(parsed)
    except Exception:
        return None


def _date_from_capture_time(value, collected_at=None):
    collected = _parse_iso_datetime(collected_at)
    base = collected.date() if collected else datetime.now(timezone(timedelta(hours=8))).date()
    text = str(value or "")
    if "前天" in text:
        return cn_date(base - timedelta(days=2))
    if "昨天" in text:
        return cn_date(base - timedelta(days=1))
    if any(token in text for token in ["刚刚", "秒前", "分钟前", "小时前", "今天", "修改于"]):
        return cn_date(base)
    month_day = re.search(r"(?P<m>\d{1,2})[月/-](?P<d>\d{1,2})", text)
    if month_day:
        try:
            return f"{int(month_day.group('m'))}月{int(month_day.group('d'))}日"
        except Exception:
            pass
    return cn_date(base)


SOCIAL_UI_NOISE_TERMS = [
    "打赏",
    "点赞",
    "查看对话",
    "只看TA",
    "Ta 回复",
    "垃圾",
    "删自选",
    "自选",
]

SOCIAL_UI_NOISE_PATTERNS = [
    r"第\d+楼\s*·",
    r"\d{1,2}:\d{2}\s+只看TA",
]

def sanitize_five_site_event_text(text):
    text = sanitize_delivery_residue(text)
    cut_positions = []
    for term in SOCIAL_UI_NOISE_TERMS:
        idx = text.find(term)
        if idx >= 12:
            cut_positions.append(idx)
    for pattern in SOCIAL_UI_NOISE_PATTERNS:
        match = re.search(pattern, text)
        if match and match.start() >= 12:
            cut_positions.append(match.start())
    if cut_positions:
        text = text[:min(cut_positions)]
    text = re.sub(r"\s+", " ", text)
    return text.strip(" #·，。； ")


def compose_visible_capture_event(title, body):
    """Keep the visible article headline once; Chrome cards often repeat it."""
    title = clean_text(title)
    body = clean_text(body)
    if title:
        while body.startswith(title):
            body = body[len(title):].strip(" -|：:，,。")
    return sanitize_five_site_event_text(" ".join(part for part in [title, body] if part))[:900]


def social_ui_noise_hits(text):
    text = str(text or "")
    hits = {term for term in SOCIAL_UI_NOISE_TERMS if term and term in text}
    hits.update(pattern for pattern in SOCIAL_UI_NOISE_PATTERNS if re.search(pattern, text))
    return hits


def _capture_matches_review_window(collected_dt, expected_ymd):
    if not collected_dt or not expected_ymd:
        return False
    collected_ymd = collected_dt.strftime("%Y%m%d")
    if collected_ymd == expected_ymd:
        return True
    try:
        review_day = datetime.strptime(expected_ymd, "%Y%m%d").date()
    except ValueError:
        return False
    next_morning_cutoff = datetime.combine(
        review_day + timedelta(days=1),
        datetime.strptime("09:30", "%H:%M").time(),
        tzinfo=timezone(timedelta(hours=8)),
    )
    return collected_dt.date() == review_day + timedelta(days=1) and collected_dt < next_morning_cutoff


def _site_payload_clean_count(payload):
    if not isinstance(payload, dict):
        return 0
    if isinstance(payload.get("cleanCount"), int):
        return payload["cleanCount"]
    clean = payload.get("clean")
    return len(clean) if isinstance(clean, list) else 0


def _five_site_minimum_for_payload(payload):
    if not isinstance(payload, dict):
        return FIVE_SITE_MIN_CLEAN_PER_SITE, "default_strict"
    channel = str(payload.get("channel") or "").strip()
    if (
        payload.get("schema") == "A_SHARE_PUBLIC_READONLY_CAPTURE_V1"
        and channel in FIVE_SITE_CHANNEL_MIN_CLEAN
    ):
        return FIVE_SITE_CHANNEL_MIN_CLEAN[channel], "channel_specific"
    return FIVE_SITE_MIN_CLEAN_PER_SITE, "default_strict"


def _candidate_five_site_dirs():
    candidates = []
    for root in FIVE_SITE_CAPTURE_ROOTS:
        if not root.exists():
            continue
        if all((root / f"{site}.json").exists() for site in FIVE_SITE_CAPTURE_FILES):
            candidates.append(root)
        for child in root.iterdir():
            if child.is_dir() and all((child / f"{site}.json").exists() for site in FIVE_SITE_CAPTURE_FILES):
                candidates.append(child)
    return sorted(set(candidates), key=lambda p: p.stat().st_mtime, reverse=True)


def five_site_capture_profile(capture_dir=None):
    capture_dir = capture_dir or os.environ.get(CHROME_CAPTURE_ENV, "").strip()
    capture_path = Path(capture_dir) if capture_dir else None
    if not capture_path:
        dirs = _candidate_five_site_dirs()
        capture_path = dirs[0] if dirs else None
    reasons = []
    sites = {}
    expected_ymd = _expected_review_ymd() if "_expected_review_ymd" in globals() else _today_ymd()
    if not capture_path or not capture_path.exists():
        return {
            "ok": False,
            "capture_dir": "",
            "expected_review_ymd": expected_ymd,
            "min_clean_per_site": FIVE_SITE_MIN_CLEAN_PER_SITE,
            "minimum_rule": "channel_specific",
            "sites": {},
            "reasons": ["five_site_capture_dir_missing"],
        }
    for site, source_name in FIVE_SITE_CAPTURE_FILES.items():
        path = capture_path / f"{site}.json"
        payload = read_json_or_none(path)
        count = _site_payload_clean_count(payload)
        required_count, minimum_rule = _five_site_minimum_for_payload(payload)
        channel = str(payload.get("channel") or "") if isinstance(payload, dict) else ""
        collected_at = payload.get("collectedAt", "") if isinstance(payload, dict) else ""
        collected_dt = _parse_iso_datetime(collected_at)
        collected_ymd = collected_dt.strftime("%Y%m%d") if collected_dt else ""
        capture_window_ok = _capture_matches_review_window(collected_dt, expected_ymd)
        site_reasons = []
        if not path.exists():
            site_reasons.append("missing_json")
        if count < required_count:
            site_reasons.append(f"clean_count_lt_{required_count}")
        if not capture_window_ok:
            site_reasons.append(f"collected_ymd_{collected_ymd or 'missing'}_ne_expected_{expected_ymd}")
        sites[source_name] = {
            "site_key": site,
            "path": str(path),
            "exists": path.exists(),
            "ok": not site_reasons,
            "channel": channel,
            "minimum_rule": minimum_rule,
            "required_clean_count": required_count,
            "clean_count": count,
            "raw_count": payload.get("rawCount", 0) if isinstance(payload, dict) else 0,
            "collected_at": collected_at,
            "collected_ymd": collected_ymd,
            "capture_window_ok": capture_window_ok,
            "sha256": file_sha256(path) if path.exists() else "",
            "reasons": site_reasons,
        }
        reasons.extend(f"{source_name}:{r}" for r in site_reasons)
    return {
        "ok": not reasons,
        "capture_dir": str(capture_path),
        "expected_review_ymd": expected_ymd,
        "review_window_rule": "采集日等于复盘锚点，或在复盘锚点次日09:30前完成采集，均视为当前复盘窗口。",
        "min_clean_per_site": FIVE_SITE_MIN_CLEAN_PER_SITE,
        "minimum_rule": "channel_specific",
        "required_platforms": REQUIRED_SOCIAL_PLATFORMS,
        "sites": sites,
        "reasons": reasons,
    }


def _historical_collect_five_site_chrome_events_disabled(now=None):
    raise RuntimeError("manual five-site capture injection is disabled; production uses automatic native-page and 36-term discovery")
    profile = five_site_capture_profile()
    if not profile["capture_dir"]:
        return []
    capture_dir = Path(profile["capture_dir"])
    pool = []
    seen = set()
    for site, source_name in FIVE_SITE_CAPTURE_FILES.items():
        payload = read_json_or_none(capture_dir / f"{site}.json") or {}
        clean_items = payload.get("clean") if isinstance(payload, dict) else []
        if not isinstance(clean_items, list):
            continue
        collected_at = payload.get("collectedAt", "")
        for item in clean_items:
            if not isinstance(item, dict):
                continue
            title = clean_text(item.get("title", ""))
            body = clean_text(item.get("text", ""))
            event = sanitize_five_site_event_text(f"{title} {body}")
            if social_ui_noise_hits(event):
                continue
            has_market_fact = any(term in event for term in FIVE_SITE_MARKET_TERMS)
            if len(event) < 18 or (event_importance_score(event, source_name) < 3 and not has_market_fact):
                continue
            href = item.get("href") or item.get("capturedUrl") or ""
            key = re.sub(r"\W+", "", f"{source_name}{href}{event}")[:180]
            if key in seen:
                continue
            seen.add(key)
            pool.append({
                "source": source_name,
                "date": _date_from_capture_time(item.get("time", ""), collected_at),
                "event": event[:520],
                "url": href,
                "theme_terms": derive_theme_terms(event, topn=6),
                "source_channel": SUPPLEMENTAL_FIVE_SITE_CHANNEL,
            })
    return pool


REPORT_METADATA_PATTERN = (
    r"事件窗口：\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+至\s+"
    r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}；"
    r"盘面验证日：\d{1,2}月\d{1,2}日(?:、\d{1,2}月\d{1,2}日)*"
)


def sanitize_delivery_residue(text):
    protected_report_metadata = []

    def protect_report_metadata(match):
        token = f"PROTECTEDREPORTMETADATA{len(protected_report_metadata)}TOKEN"
        protected_report_metadata.append((token, match.group(0)))
        return token

    text = re.sub(REPORT_METADATA_PATTERN, protect_report_metadata, str(text or ""), count=1)
    text = clean_text(text)
    text = re.sub(r"\s+来源[:：]\s*[^，。；]{2,24}", " ", text)
    text = re.sub(
        r"(多家机构|机构|券商|分析师|市场|投资者|资金)看好([^，。；]{1,40})",
        r"\1对\2持积极观点",
        text,
    )
    text = re.sub(
        r"(?:另有)?观点看空([^，。；]{1,40})",
        r"对\1持谨慎观点",
        text,
    )
    text = re.sub(
        r"(多家机构|机构|券商|分析师|市场|投资者|资金)看空([^，。；]{1,40})",
        r"\1对\2持谨慎观点",
        text,
    )
    text = text.replace("看好", "观点偏积极")
    text = text.replace("看空", "观点偏谨慎")
    text = text.replace("所属环节为", "所属行业为")
    text = re.sub(r"原因为\s*", "上榜原因：", text)
    text = re.sub(r"(?:，|,)?\s*成功率\s*[:：]?\s*\d+(?:\.\d+)?\s*%?", "", text)
    text = text.replace("成功率", "命中比例")
    text = text.replace("来源层", "公开信息")
    text = text.replace("涨停扩散", "涨停家数集中")
    text = text.replace("核心容量票", "高成交样本")
    text = text.replace("核心主线", "事实证据项")
    text = text.replace("主线集中度高", "同类事件样本集中")
    text = text.replace("垃圾", "")
    text = text.replace("删自选了", "")
    text = text.replace("删自选", "")
    text = text.replace("重要方向", "事实证据项")
    text = text.replace("看成交额", "成交额读数")
    text = text.replace("用于校验", "帮助核对")
    text = text.replace("盘面观察", "盘面跟踪")
    text = text.replace("重要/风险观察", "重点风险跟踪")
    text = text.replace("成交缩量", "成交额下降")
    text = text.replace("公告澄清", "澄清公告")
    text = text.replace("强势方向", "高分方向")
    text = text.replace("高频热词", "高频主题词")
    text = text.replace("短线资金更偏向", "短线资金集中在")
    text = re.sub(
        r"[\u4e00-\u9fa5A-Za-z0-9_\[\]【】]{2,40}\s+"
        r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?\b",
        " ",
        text,
    )
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?\b", " ", text)
    text = re.sub(r"[\u4e00-\u9fa5A-Za-z0-9_]{2,24}\s+\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{1,2}(?:\s+\d+){0,3}", " ", text)
    text = re.sub(r"\b\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{1,2}\b", " ", text)
    text = re.sub(r"\b\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{1,2}", " ", text)
    text = re.sub(r"\b\d{1,2}[-/]\d{1,2}\b", " ", text)
    text = re.sub(r"\b\d{4,}\s+\d{1,3}\b", " ", text)
    text = re.sub(r"股友[A-Za-z0-9]+", " ", text)
    text = re.sub(r"[A-Za-z]\d{6,}[A-Za-z0-9]*", " ", text)
    text = re.sub(r"阅读 标题 作者 最后更新", " ", text)
    text = re.sub(r"[，,]\s*[，,]+", "，", text)
    text = re.sub(r"[，,]\s*。", "。", text)
    text = re.sub(r"\s+", " ", text).strip(" ，。；")
    for token, value in protected_report_metadata:
        text = text.replace(token, value)
    return text


def run_word_render_validation(report_path, artifact_dir):
    report_path = Path(report_path)
    artifact_dir = Path(artifact_dir)
    audit_path = artifact_dir / "a_share_sentiment_word_render_audit.json"
    render_dir = artifact_dir / "a_share_sentiment_word_pages"
    pdf_path = artifact_dir / "A股三日舆情解读结果_Codex自动生成.pdf"
    if not WORD_RENDER_VALIDATOR.is_file():
        raise RuntimeError(f"BLOCKED Word render validator missing: {WORD_RENDER_VALIDATOR}")
    completed = subprocess.run(
        [
            sys.executable,
            str(WORD_RENDER_VALIDATOR),
            "--docx",
            str(report_path),
            "--output",
            str(audit_path),
            "--render-dir",
            str(render_dir),
            "--pdf",
            str(pdf_path),
        ],
        cwd=str(WORKSPACE),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
    )
    audit = read_json_or_none(audit_path) or {}
    if completed.returncode != 0 or audit.get("status") != "PASS":
        details = ",".join(str(value) for value in audit.get("errors", [])[:8])
        raise RuntimeError(f"BLOCKED Word render validation failed: {details or completed.stderr[-600:]}")
    return audit


def strip_allowed_report_metadata(text):
    return re.sub(REPORT_METADATA_PATTERN, "", str(text or ""), count=1)


def delivery_focus_terms(text, theme="", limit=2):
    merged = clean_text(f"{theme} {text}")
    terms = []
    for phrase in DOMAIN_PHRASES + sorted(SPECIFIC_LABEL_HINTS, key=len, reverse=True):
        phrase = normalize_delivery_label(phrase)
        if phrase and phrase not in terms and phrase in merged and phrase not in GENERIC_LABEL_WORDS:
            terms.append(phrase)
        if len(terms) >= limit:
            return terms
    for token in re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]{2,12}", merged):
        token = normalize_delivery_label(token)
        if (
            token
            and token not in terms
            and token not in STOP_WORDS
            and token not in BAD_LABEL_WORDS
            and token not in GENERIC_LABEL_WORDS
            and not any(noise in token for noise in NOISE_WORDS)
        ):
            terms.append(token)
        if len(terms) >= limit:
            break
    return terms


def evidence_meaning(theme, event):
    item = event if isinstance(event, dict) else {}
    text = sanitize_delivery_residue(item.get("event", event if isinstance(event, str) else ""))
    source = item.get("source", "")
    layer = source_layer(source) if source else ""
    focus_terms = delivery_focus_terms(text, theme, 1)
    focus = "、".join(focus_terms) if focus_terms else (clean_text(theme).replace(" / ", "、") or "该方向")
    source_hint = source or layer or "事件"
    date_hint = item.get("date", "")
    anchor = f"{source_hint}{date_hint}" if date_hint else source_hint
    if any(w in text for w in ["涨停", "成交额", "反弹", "融资", "调研", "龙虎榜", "净流入"]):
        return f"{anchor}显示{focus}出现交易活跃信号，后续关注量价承接与资金延续。"
    if any(w in text for w in ["医保", "政策", "目录", "教育部", "国家", "监管", "交易所"]):
        return f"{anchor}把{focus}纳入政策或监管事实，后续判断以同一事项是否继续出现落地公告为准。"
    if any(w in text for w in ["公告", "澄清", "风险", "减持", "问询", "异动"]):
        return f"{anchor}暴露{focus}的公告或异动风险，本行对结论的作用是降低无公告支撑叙事的权重。"
    if any(w in text for w in INDUSTRY_CHAIN_SIGNAL_WORDS):
        return f"{anchor}指向{focus}产业链映射，本行证据对应价格、订单、产能或下游需求中的实际线索。"
    if layer == "散户社区":
        return f"{anchor}讨论集中在{focus}，本行只作为情绪样本，需与交易复盘或公告样本并列使用。"
    if layer == "游资社区":
        return f"{anchor}把{focus}纳入短线复盘语境，本行证明游资样本中出现同类主题。"
    if layer == "机构渠道":
        return f"{anchor}提供{focus}基本面信息，本行证据对应调研、融资或业绩兑现线索。"
    return f"{anchor}围绕{focus}形成新增信息点，后续关注相关催化是否延续。"


def supplemental_report_clusters(pool, needed):
    raise RuntimeError("scientific gate: template sections must never be filled with supplemental observations")


def _width_source_key(item):
    aliases = {
        "jiuyangongshe": "jiuyangongshe.com",
        "jiuyangongshe.com": "jiuyangongshe.com",
        "www.jiuyangongshe.com": "jiuyangongshe.com",
    }
    explicit = str(item.get("source_key", "") or "").strip().lower()
    if explicit:
        if "://" in explicit:
            normalized = urlparse(explicit).netloc.lower()
        else:
            normalized = explicit.split("/", 1)[0]
        normalized = normalized.removeprefix("www.").rstrip(".")
        return aliases.get(normalized, normalized)
    host = urlparse(str(item.get("url", ""))).netloc.lower().removeprefix("www.")
    if "jiuyangongshe.com" in host:
        return "jiuyangongshe.com"
    if "scol.com.cn" in host:
        return "scol.com.cn"
    if "eastmoney.com" in host:
        return "eastmoney.com"
    if host:
        return host
    return ""


def _parse_width_candidate(item):
    text = clean_text(str(item.get("event", "")))
    matches = [
        re.search(r"上涨(?:家数)?\s*(\d+)\s*(?:家|只)?.*?下跌(?:家数)?\s*(\d+)\s*(?:家|只)?", text),
        re.search(r"(\d+)\s*(?:家|只)(?:股票|个股)?上涨.*?(\d+)\s*(?:家|只)(?:股票|个股)?下跌", text),
    ]
    match = next((value for value in matches if value), None)
    if not match:
        return None
    up, down = int(match.group(1)), int(match.group(2))
    if up <= 0 or down <= 0 or up + down < 3000:
        return None
    scope = "全市场" if "全市场" in text else ("两市" if "两市" in text else "未注明口径")
    turnover_match = re.search(r"成交(?:额)?\s*([0-9.]+)\s*(万亿元|亿元)", text)
    turnover = f"{turnover_match.group(1)}{turnover_match.group(2)}" if turnover_match else ""
    return {
        "up": up,
        "down": down,
        "date": clean_text(str(item.get("date", ""))),
        "scope": scope,
        "turnover": turnover,
        "source": clean_text(str(item.get("source", ""))),
        "source_key": _width_source_key(item),
        "url": str(item.get("url", "")),
    }


def _is_structured_width_observation(text):
    text = clean_text(str(text or ""))
    if _parse_width_candidate({"event": text}):
        return True
    match = re.search(
        r"(?:全市场|两市).{0,10}?(?:约|超)?\s*(\d{3,5})\s*只(?:股票|个股)?下跌",
        text,
    )
    return bool(match and int(match.group(1)) >= 1000)


def _market_width_anchor_date(now=None):
    """Return the latest completed session breadth facts may describe."""
    now = now or _china_datetime()
    if now.weekday() < 5 and now.hour >= 16:
        return now.date()
    completed_dates = [
        value for value in recent_trading_dates(now) if value < now.date()
    ]
    return completed_dates[-1] if completed_dates else now.date()


def parse_width_fact(items):
    # Before the opening auction there is no current-session breadth.  Use the
    # latest completed session so an overnight run cannot relabel yesterday's
    # close as a missing current-day observation.
    now = _china_datetime()
    anchor = _market_width_anchor_date(now)
    latest_date = cn_date(anchor)
    candidates = [
        candidate
        for item in items
        for candidate in [_parse_width_candidate(item)]
        if candidate and candidate["date"] == latest_date
    ]
    explicit_scopes = defaultdict(set)
    for candidate in candidates:
        if candidate["scope"] != "未注明口径":
            explicit_scopes[
                (candidate["date"], candidate["up"], candidate["down"])
            ].add(candidate["scope"])
    for candidate in candidates:
        if candidate["scope"] != "未注明口径":
            continue
        scopes = explicit_scopes.get(
            (candidate["date"], candidate["up"], candidate["down"]),
            set(),
        )
        if len(scopes) == 1:
            candidate["scope"] = next(iter(scopes))
    grouped = defaultdict(list)
    for candidate in candidates:
        grouped[(candidate["date"], candidate["scope"], candidate["up"], candidate["down"])].append(candidate)
    # Exact breadth must be independently repeated.  A second source can also
    # corroborate the downside count as an explicitly approximate market-wide
    # statement; that still does not turn its unreported up-count into a fact.
    verified = []
    for key, rows in grouped.items():
        source_keys = {row["source_key"] for row in rows if row["source_key"]}
        if len(source_keys) >= 2:
            verified.append((key, rows, source_keys, "exact"))
    if not verified:
        down_only = []
        for item in items:
            if clean_text(str(item.get("date", ""))) != latest_date:
                continue
            text = clean_text(str(item.get("event", "")))
            match = re.search(r"(?:全市场|两市).{0,10}?(?:约|超)?\s*(\d{3,5})\s*只(?:股票|个股)?下跌", text)
            if match:
                valid_match = re.search(r"有效样本\s*(\d{3,5})\s*只", text)
                down_only.append({
                    "down": int(match.group(1)), "source": clean_text(str(item.get("source", "")),),
                    "valid": int(valid_match.group(1)) if valid_match else 0,
                    "source_key": _width_source_key(item), "url": str(item.get("url", "")),
                })
        for key, rows in grouped.items():
            date, scope, up, down = key
            keys = {row["source_key"] for row in rows if row["source_key"]}
            if not keys:
                continue
            corroborators = [
                row for row in down_only
                if row["source_key"] not in keys
                and (
                    abs(row["down"] - down) <= max(80, int(down * 0.03))
                    or (
                        row["valid"] >= 3000
                        and row["down"] <= row["valid"]
                        and abs(
                            row["down"] / row["valid"]
                            - down / (up + down)
                        ) <= 0.015
                    )
                )
            ]
            if corroborators:
                verified.append((key, rows + [{"source": x["source"], "source_key": x["source_key"], "url": x["url"], "turnover": ""} for x in corroborators], keys | {x["source_key"] for x in corroborators}, "downside_approx"))
    if len(verified) != 1:
        return None
    (date, scope, up, down), rows, source_keys, corroboration_mode = verified[0]
    ratio = round(up * 100 / max(1, up + down), 1)
    label = "个股普涨、结构分化" if ratio >= 60 else "个股偏弱、风险偏好回落"
    turnovers = sorted({row["turnover"] for row in rows if row["turnover"]})
    return {
        "up": str(up),
        "down": str(down),
        "ratio": f"{ratio}%",
        "label": label,
        "date": date,
        "scope": scope,
        "turnover": turnovers[0] if len(turnovers) == 1 else "",
        "cross_source_count": len(source_keys),
        "cross_source_mode": corroboration_mode,
        "sources": sorted({row["source"] for row in rows if row["source"]}),
        "source_keys": sorted(source_keys),
        "urls": sorted({row["url"] for row in rows if row["url"]}),
    }


def market_width_sentence(pool):
    width = parse_width_fact(pool)
    if not width:
        raise RuntimeError("scientific gate: verified market breadth is required")
    return (
        f"大盘风向：{width['date']}{width['scope']}上涨家数{width['up']}、下跌家数{width['down']}、"
        f"上涨占比{width['ratio']}，{width['label']}；该读数已由{width['cross_source_count']}个独立来源交叉确认。"
    )


SHORT_TERM_DIMENSION_RULES = {
    "limit_up": ("涨停家数", ("涨停",)),
    "promotion": ("连板晋级", ("晋级", "连板", "进2", "进3", "进4", "进5", "进6", "进7")),
    "hotspot_spread": ("热点扩散", ("热点", "主线", "题材扩散", "方向扩散")),
    "turnover": ("成交额", ("成交额", "成交总额", "两市成交", "放量", "缩量")),
    "market_width": ("市场宽度", ("上涨家数", "下跌家数", "上涨占比", "个股普涨", "个股偏弱")),
}


def _short_term_dimension_facts(pool, width=None):
    dimensions = {}
    target_date = clean_text(str((width or {}).get("date", "")))
    eligible = [
        item
        for item in pool
        if isinstance(item, dict)
        and (
            not target_date
            or clean_text(str(item.get("date", ""))) == target_date
        )
    ]

    def missing(key):
        return {
            "label": SHORT_TERM_DIMENSION_RULES[key][0],
            "status": "missing",
            "value": "",
            "source": "",
            "date": target_date,
            "url": "",
            "evidence_count": 0,
            "quality_contract": "exact_numeric_market_fact_only",
        }

    def fact_row(key, value, rows, status="verified", metrics=None):
        sources = list(dict.fromkeys(
            clean_text(str(item.get("source", "")))
            for item in rows
            if clean_text(str(item.get("source", "")))
        ))
        urls = list(dict.fromkeys(
            str(item.get("url", ""))
            for item in rows
            if str(item.get("url", ""))
        ))
        return {
            "label": SHORT_TERM_DIMENSION_RULES[key][0],
            "status": status,
            "value": value,
            "source": "、".join(sources),
            "date": target_date or clean_text(str(rows[0].get("date", ""))),
            "url": "；".join(urls),
            "evidence_count": len(rows),
            "metrics": metrics or {},
            "quality_contract": "exact_numeric_market_fact_only",
        }

    limit_rows = []
    for item in eligible:
        event = clean_text(str(item.get("event", "")))
        match = re.search(
            r"(?:涨停家数|涨停池ZTC共|涨停计数|(?<!连续两日)(?<!只)涨停)\s*(\d+)\s*(?:家|只)?",
            event,
        )
        if match and int(match.group(1)) > 0:
            limit_rows.append((item, int(match.group(1))))
    if limit_rows:
        limit_values = sorted({value for _item, value in limit_rows})
        conflict = len(limit_values) > 1 and (
            limit_values[-1] - limit_values[0] > max(5, round(limit_values[-1] * 0.08))
        )
        limit_value = (
            f"{limit_values[0]}家"
            if len(limit_values) == 1
            else f"{limit_values[0]}—{limit_values[-1]}家（不同复盘口径）"
        )
        dimensions["limit_up"] = fact_row(
            "limit_up",
            limit_value,
            [item for item, _value in limit_rows],
            status="conflict" if conflict else "verified",
            metrics={"reported_counts": limit_values},
        )
    else:
        dimensions["limit_up"] = missing("limit_up")

    promotion_rows = []
    promotion_counts = []
    promotion_rates = []
    max_boards = []
    for item in eligible:
        event = clean_text(str(item.get("event", "")))
        counts = [
            int(value)
            for value in re.findall(
                r"(?:连板晋级样本|连续两日涨停|二连板池ELB共)\s*(\d+)\s*(?:家|只)",
                event,
            )
        ]
        rates = [
            float(value)
            for value in re.findall(r"晋级率\s*(\d+(?:\.\d+)?)%", event)
        ]
        boards = [
            int(value)
            for value in re.findall(r"最高(?:连板)?\s*(\d+)\s*板", event)
        ]
        if counts or rates or boards:
            promotion_rows.append(item)
            promotion_counts.extend(value for value in counts if value > 0)
            promotion_rates.extend(value for value in rates if 0 <= value <= 100)
            max_boards.extend(value for value in boards if value > 0)
    if promotion_rows:
        parts = []
        if promotion_counts:
            counts = sorted(set(promotion_counts))
            parts.append(
                f"晋级样本{counts[0]}家"
                if len(counts) == 1
                else f"晋级样本{counts[0]}—{counts[-1]}家"
            )
        if promotion_rates:
            rates = sorted(set(promotion_rates))
            parts.append("晋级率" + "/".join(f"{value:g}%" for value in rates))
        if max_boards:
            parts.append(f"最高{max(max_boards)}板")
        dimensions["promotion"] = fact_row(
            "promotion",
            "；".join(parts),
            promotion_rows,
            metrics={
                "promotion_counts": sorted(set(promotion_counts)),
                "promotion_rates": sorted(set(promotion_rates)),
                "max_boards": sorted(set(max_boards)),
            },
        )
    else:
        dimensions["promotion"] = missing("promotion")

    direct_spread_rows = []
    direct_spread_counts = []
    theme_rows = []
    themes = []
    for item in eligible:
        event = clean_text(str(item.get("event", "")))
        direct = re.search(
            r"(?:热点|题材|方向)(?:扩散)?(?:至|到|为)?\s*(\d+)\s*个(?:方向|板块|题材)",
            event,
        )
        if direct and int(direct.group(1)) > 0:
            direct_spread_rows.append(item)
            direct_spread_counts.append(int(direct.group(1)))
        theme = re.search(
            r"所属概念为([^，。；]+)[^。；]*?共有\s*(\d+)\s*只涨停",
            event,
        )
        if theme and int(theme.group(2)) > 0:
            theme_rows.append(item)
            themes.append((clean_text(theme.group(1)), int(theme.group(2))))
    if direct_spread_rows:
        spread_counts = sorted(set(direct_spread_counts))
        dimensions["hotspot_spread"] = fact_row(
            "hotspot_spread",
            (
                f"{spread_counts[0]}个方向"
                if len(spread_counts) == 1
                else f"{spread_counts[0]}—{spread_counts[-1]}个方向"
            ),
            direct_spread_rows,
            metrics={"reported_direction_counts": spread_counts},
        )
    elif theme_rows:
        ordered_themes = []
        for name, count in sorted(set(themes), key=lambda row: (-row[1], -len(row[0]), row[0])):
            if any(
                count == existing_count
                and (name in existing_name or existing_name in name)
                for existing_name, existing_count in ordered_themes
            ):
                continue
            ordered_themes.append((name, count))
        if len(ordered_themes) >= 2:
            summary = "、".join(
                f"{name}{count}家" for name, count in ordered_themes[:5]
            )
            dimensions["hotspot_spread"] = fact_row(
                "hotspot_spread",
                f"{len(ordered_themes)}个涨停扩散方向（{summary}）",
                theme_rows,
                metrics={"themes": [
                    {"name": name, "limit_up_count": count}
                    for name, count in ordered_themes
                ]},
            )
        else:
            dimensions["hotspot_spread"] = missing("hotspot_spread")
    else:
        dimensions["hotspot_spread"] = missing("hotspot_spread")

    turnover_rows = []
    turnover_values = []
    for item in eligible:
        event = clean_text(str(item.get("event", "")))
        match = re.search(
            r"成交(?:总)?额(?:合计|最后读数)?(?:为|达到|约)?\s*(\d+(?:\.\d+)?)\s*(万亿元|万亿|亿元|亿)",
            event,
        )
        if not match:
            continue
        number = float(match.group(1))
        amount_yi = number * 10000 if match.group(2).startswith("万亿") else number
        if amount_yi > 0:
            turnover_rows.append(item)
            turnover_values.append(round(amount_yi, 2))
    if turnover_rows:
        amounts = sorted(set(turnover_values))
        conflict = len(amounts) > 1 and (
            amounts[-1] - amounts[0] > max(100, amounts[-1] * 0.05)
        )
        turnover_value = (
            f"{amounts[0]:g}亿元"
            if len(amounts) == 1
            else f"{amounts[0]:g}—{amounts[-1]:g}亿元（不同复盘口径）"
        )
        dimensions["turnover"] = fact_row(
            "turnover",
            turnover_value,
            turnover_rows,
            status="conflict" if conflict else "verified",
            metrics={"reported_amount_yi": amounts},
        )
    else:
        dimensions["turnover"] = missing("turnover")

    if width:
        dimensions["market_width"] = {
            "label": SHORT_TERM_DIMENSION_RULES["market_width"][0],
            "status": "verified",
            "value": f"上涨{width['up']}家、下跌{width['down']}家、上涨占比{width['ratio']}",
            "source": "、".join(width.get("sources", [])),
            "date": width.get("date", ""),
            "url": "；".join(width.get("urls", [])),
            "evidence_count": int(width.get("cross_source_count", 0) or 0),
            "metrics": {
                "up": int(width["up"]),
                "down": int(width["down"]),
                "ratio": width["ratio"],
            },
            "quality_contract": "exact_numeric_market_fact_only",
        }
    else:
        dimensions["market_width"] = missing("market_width")
    return dimensions


def short_term_sentiment_assessment(pool, clusters=None):
    width = parse_width_fact(pool)
    dimensions = _short_term_dimension_facts(pool, width)
    ratio = 0.5
    if width:
        try:
            ratio = float(str(width.get("ratio", "")).rstrip("%")) / 100
        except (TypeError, ValueError):
            ratio = 0.5
    text = " ".join(clean_text(str(item.get("event", ""))) for item in pool)
    explicit_stage = ""
    for stage in ("退潮期", "冰点期", "修复期", "分歧期", "上升期", "高潮期"):
        if stage in text:
            explicit_stage = stage
            break
    clusters = list(clusters or [])
    stances = Counter(cluster.get("stance", "") for cluster in clusters)
    if explicit_stage in {"退潮期", "冰点期"} or ratio <= 0.30:
        label = "退潮"
    elif ratio <= 0.43 or stances.get("转弱", 0) > stances.get("增强", 0):
        label = "偏弱"
    elif explicit_stage == "高潮期" and ratio >= 0.65:
        label = "强势"
    elif ratio >= 0.62 and stances.get("增强", 0) >= stances.get("分歧", 0):
        label = "偏强"
    else:
        label = "中性分化"
    evidence = []
    if width:
        evidence.append(
            f"全市场上涨占比{width.get('ratio', '')}，上涨{width.get('up', '')}家、下跌{width.get('down', '')}家"
        )
    if explicit_stage:
        evidence.append(f"复盘情绪阶段为{explicit_stage}")
    if clusters:
        evidence.append(
            f"因果主线状态为增强{stances.get('增强', 0)}条、分歧{stances.get('分歧', 0)}条、转弱{stances.get('转弱', 0)}条"
        )
    if not evidence:
        evidence.append("市场宽度与主线状态证据不足")
    if ratio <= 0.30:
        intermediate_cycle = "亏钱效应炸裂"
    elif ratio <= 0.43:
        intermediate_cycle = "亏钱效应出现"
    elif ratio >= 0.68 and stances.get("增强", 0) > stances.get("分歧", 0):
        intermediate_cycle = "赚钱效应高潮"
    elif ratio >= 0.55 and stances.get("增强", 0) >= stances.get("转弱", 0):
        intermediate_cycle = "赚钱效应回暖"
    else:
        intermediate_cycle = "赚钱效应低迷"
    explicit_to_short_stage = {
        "修复期": "启动期",
        "上升期": "发酵期",
        "高潮期": "高潮期",
        "分歧期": "分歧期",
        "退潮期": "退潮期",
        "冰点期": "退潮期",
    }
    if explicit_stage:
        short_term_stage = explicit_to_short_stage.get(explicit_stage, "确认期")
    elif ratio <= 0.30:
        short_term_stage = "退潮期"
    elif ratio <= 0.43 or stances.get("转弱", 0) > stances.get("增强", 0):
        short_term_stage = "分歧期"
    elif ratio >= 0.68 and stances.get("增强", 0) > stances.get("分歧", 0):
        short_term_stage = "高潮期"
    elif ratio >= 0.60:
        short_term_stage = "加速期"
    elif ratio >= 0.52:
        short_term_stage = "发酵期"
    else:
        short_term_stage = "确认期"
    conflicts = []
    if ratio >= 0.60 and stances.get("转弱", 0) > stances.get("增强", 0):
        conflicts.append("市场宽度偏强，但因果主线转弱数量更多")
    if ratio <= 0.43 and stances.get("增强", 0) > stances.get("转弱", 0):
        conflicts.append("市场宽度偏弱，但局部因果主线仍在增强")
    if explicit_stage == "高潮期" and ratio < 0.55:
        conflicts.append("复盘文本称高潮期，但全市场宽度未同步确认")
    if explicit_stage in {"退潮期", "冰点期"} and ratio > 0.55:
        conflicts.append("复盘文本偏退潮，但全市场宽度仍偏强")
    verified_dimension_count = sum(
        row.get("status") == "verified" for row in dimensions.values()
    )
    if verified_dimension_count == len(SHORT_TERM_DIMENSION_RULES) and width and clusters and not conflicts:
        confidence = "高"
    elif verified_dimension_count >= 4 and clusters:
        confidence = "中"
    else:
        confidence = "低"
    conflict_statement = "；".join(conflicts) if conflicts else "未发现直接冲突；仍保留次日盘面反证检查。"
    return {
        "label": label,
        "evidence": "；".join(evidence) + "。",
        "explicit_stage": explicit_stage,
        "width": width,
        "stance_counts": dict(stances),
        "intermediate_cycle": intermediate_cycle,
        "short_term_stage": short_term_stage,
        "confidence": confidence,
        "dimensions": dimensions,
        "verified_dimension_count": verified_dimension_count,
        "dimension_gate_passed": verified_dimension_count == len(SHORT_TERM_DIMENSION_RULES),
        "conflicts": conflicts,
        "conflict_statement": conflict_statement,
        "weighted_total_score": None,
        "method": "five_exact_numeric_market_dimensions_multi_cycle_without_weighted_score_v3",
    }


def cluster_fact_profile(cluster):
    items = cluster.get("items", [])
    sources = sorted(cluster.get("sources") or {x.get("source", "") for x in items})
    layers = sorted(source_layers(sources))
    dq = cluster.get("direction_quality") or direction_evidence_quality(cluster)
    raw_terms = candidate_terms_from_text(" ".join(x.get("event", "") for x in items), topn=14)
    raw_terms.extend(cluster.get("keywords", []))
    raw_terms.extend(cluster.get("name", "").split(" / "))
    terms = []
    for raw in raw_terms:
        term = clean_theme_term(raw)
        if not term:
            continue
        try:
            is_specific = _is_specific_label_token(term)
        except NameError:
            is_specific = True
        if is_specific and term not in terms:
            terms.append(term)
    stocks = dq.get("stocks", [])[:6]
    evidence = select_evidence(cluster, 10)
    evidence_sources = sorted({x.get("source", "") for x in evidence})
    return {
        "name": cluster.get("name", ""),
        "score": cluster.get("score"),
        "events": len(items),
        "sources": sources,
        "layers": layers,
        "terms": terms[:5] or cluster.get("keywords", [])[:5],
        "stock_count": dq.get("stock_count", 0),
        "stocks": stocks,
        "non_stock_events": dq.get("non_stock_events", 0),
        "evidence_rows": len(evidence),
        "evidence_sources": evidence_sources,
    }


def clean_join(values, sep="、"):
    values = [clean_text(str(v)).strip(" ，。；") for v in values if str(v).strip()]
    return sep.join(values)


def score_text(score):
    return "未评分" if score is None else str(score)


def cluster_fact_rows(cluster):
    causal = cluster.get("causal") or {}
    catalyst_item = _first_role_item(cluster.get("items", []), "catalyst") or {}
    variable = catalyst_item.get("causal_variable", "")
    stocks = clean_join((cluster.get("direction_quality") or {}).get("stocks", [])[:8])
    observation_scope = (
        f"本轮盘面验证标的包括{stocks}。"
        if stocks
        else "观察范围仅限本轮已验证的板块级样本。"
    )
    return [
        ("明确结论", causal.get("conclusion", "")),
        (
            "逻辑分析",
            clean_text(
                f"{causal.get('catalyst_fact', '')}"
                + (f" 作用变量为{variable}。" if variable else "")
                + f" {causal.get('mechanism', '')}"
            ),
        ),
        (
            "情绪与资金行为",
            clean_text(
                f"{causal.get('market_feedback', '')} "
                f"{causal.get('participant_feedback', '')}"
            ),
        ),
        (
            "产业链与观察标的",
            f"主线主题为{cluster.get('name', '')}；{observation_scope}",
        ),
        ("下一步观察", causal.get("next_check", "")),
        ("失效风险", causal.get("invalidation", "")),
    ]


def cluster_role_text(cluster):
    stance = cluster.get("stance", "")
    if stance not in ALLOWED_CAUSAL_STANCES:
        raise RuntimeError(f"scientific gate: invalid causal stance for {cluster.get('name', '')}: {stance or 'missing'}")
    return f"因果链{stance}"


def summary_risk_text(cluster):
    return (cluster.get("causal") or {}).get("counterevidence", "")


def cluster_analysis_rows(cluster):
    return cluster_fact_rows(cluster)


UI_NOISE_FRAGMENTS = [
    "免责声明", "风险提示", "版权", "版权声明", "广告", "客服", "隐私",
    "换一换", "我的自选", "加自选", "客户端下载", "二维码", "扫一扫",
    "返回顶部", "Copyright", "认知升级", "对话风雨看盘", "习近平主持",
    "普通者", "主管主办", "法定信息披露", "电子报", "登录", "注册",
    "关于我们", "打赏", "点赞", "查看对话", "只看TA", "Ta 回复",
]


def is_delivery_evidence_candidate(item):
    event = clean_text(item.get("event", ""))
    source = item.get("source", "")
    if len(event) < 26:
        return False
    if any(noise in event for noise in UI_NOISE_FRAGMENTS):
        return False
    if any(term in event for term in ["认知升级", "对话风雨看盘", "习近平主持", "Copyright", "封板成功率", "主管主办", "法定信息披露", "电子报", "登录", "注册"]):
        return False
    if not is_non_stock_direction_event(item):
        # 主数据源中的龙虎榜/资金流/机构样本可以作为受限证据行；
        # 方向级成立仍由红线里的非个股事件和单股占比共同约束。
        if not (
            is_single_stock_trade_feedback(item)
            and not is_five_site_supplemental(item)
            and source_layer(source) in {"交易复盘", "机构渠道"}
        ):
            return False
    if "交易复盘显示" in event or "短线复盘显示" in event:
        return True
    return event_importance_score(event, item.get("source", "")) >= 5


def select_evidence(cluster, limit=10):
    if cluster.get("causal_method") not in ALLOWED_CAUSAL_METHODS:
        return []
    theme = cluster.get("name", "")
    candidates = [
        item for item in cluster.get("items", [])
        if theme
        and _causal_item_theme_grounded(theme, item)
        and item.get("causal_roles")
        and item.get("meaning")
    ]
    selected = []
    seen = set()
    source_counts = Counter()
    single_stock_count = 0
    max_single_stock = max(1, int(limit * 0.30))

    def add(item):
        nonlocal single_stock_count
        key = _event_identity(item)
        if key in seen or source_counts[item.get("source", "")] >= 2:
            return False
        if is_single_stock_trade_feedback(item):
            if single_stock_count >= max_single_stock:
                return False
            single_stock_count += 1
        seen.add(key)
        source_counts[item.get("source", "")] += 1
        selected.append(item)
        return True

    def finalize():
        nonlocal single_stock_count
        while selected and single_stock_count / len(selected) > 0.30:
            role_counts = Counter(
                role
                for item in selected
                for role in item.get("causal_roles", [])
            )
            removable = [
                index
                for index, item in enumerate(selected)
                if is_single_stock_trade_feedback(item)
                and all(
                    role_counts[role] > 1
                    for role in item.get("causal_roles", [])
                    if role in CAUSAL_ROLE_ORDER
                )
            ]
            if not removable:
                removable = [
                    index
                    for index, item in enumerate(selected)
                    if is_single_stock_trade_feedback(item)
                ]
            index = removable[-1]
            item = selected.pop(index)
            seen.discard(_event_identity(item))
            source_counts[item.get("source", "")] -= 1
            single_stock_count -= 1

        for item in sorted(candidates, key=is_single_stock_trade_feedback):
            if len(selected) >= limit:
                break
            if is_single_stock_trade_feedback(item):
                continue
            add(item)
        return selected

    for role in CAUSAL_ROLE_ORDER:
        role_items = [item for item in candidates if role in item.get("causal_roles", [])]
        role_items.sort(key=lambda item: (
            source_layer(item.get("source", "")) == "机构渠道",
            source_layer(item.get("source", "")) == "交易复盘",
            item.get("source_channel") == "primary_chrome_visible",
            not is_single_stock_trade_feedback(item),
        ), reverse=True)
        for item in role_items:
            if add(item):
                break
        if len(selected) >= limit:
            return finalize()
    for item in sorted(candidates, key=is_single_stock_trade_feedback):
        if add(item) and len(selected) >= limit:
            break
    return finalize()


def evidence_source_count(cluster, limit=10):
    return len(items_evidence_sources(select_evidence(cluster, limit)))


def has_multi_source_evidence(cluster, limit=10):
    evidence = select_evidence(cluster, limit)
    if not evidence:
        return False
    evidence_sources = items_evidence_sources(evidence)
    layers = source_layers(evidence_sources)
    ok = (
        evidence_source_count(cluster, limit) >= MIN_CLUSTER_SOURCES
        and len(layers) >= MIN_CLUSTER_SOURCE_LAYERS
        and bool(layers & MANDATORY_FEEDBACK_LAYERS)
        and bool(layers & MANDATORY_PARTICIPANT_LAYERS)
    )
    return ok


def extract_stock_names_from_event(text):
    names = set()
    known_names = known_stock_names()
    for name in known_names:
        if name and name in text:
            names.add(name)
    for match in re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]{2,12}(?:涨停|龙虎榜|资金流|上榜|成交额|净流入)", text):
        name = re.sub(r"(涨停|龙虎榜|资金流|上榜|成交额|净流入)$", "", match)
        name = name.replace("进入", "").replace("显示", "")
        if name.endswith("龙虎榜"):
            name = name[:-3]
        bad_fragments = ["所属环节", "方向", "主力", "超大单", "榜单", "今日", "昨日", "查看个股", "开盘继续"]
        if name in known_names and not any(w in name for w in bad_fragments):
            names.add(name)
    for match in re.finditer(
        r"(?:^|[，。；;\s])([*A-Za-z0-9\u4e00-\u9fa5]{2,8}?)(?=涨停|龙虎榜(?:上榜)?)",
        text,
    ):
        name = match.group(1)
        bad_fragments = ["所属", "方向", "主力", "榜单", "今日", "昨日", "板块", "行业", "概念"]
        if not any(fragment in name for fragment in bad_fragments):
            names.add(name)
    return names


def is_single_stock_trade_feedback(item):
    event = item.get("event", "")
    source = item.get("source", "")
    if source in {"龙虎榜", "融资数据", "涨停复盘"} and len(extract_stock_names_from_event(event)) == 1:
        return True
    return bool(
        len(extract_stock_names_from_event(event)) == 1
        and any(w in event for w in ["资金流显示", "进入涨停与龙虎榜交集", "龙虎榜上榜", "涨停，所属环节为"])
    )


def is_non_stock_direction_event(item):
    event = item.get("event", "")
    source = item.get("source", "")
    if is_single_stock_trade_feedback(item):
        return False
    broad_patterns = [
        "交易复盘显示",
        "方向涨停数",
        "方向出现",
        "涨停或龙虎榜反馈标的",
        "指数宽度",
        "市场宽度",
        "上涨家数",
        "下跌家数",
        "宽度标签",
        "宽度阶段",
        "宽度读数",
        "市场阶段为",
        "板块级",
        "板块聚合",
        "板块为",
        "主线判定",
        "主线评级",
        "属于板块级",
        "非个股",
        "非个股层面",
        "政策",
        "目录",
        "行业",
        "产业链",
        "板块",
        "厂商",
        "调价",
        "涨价",
        "ETF",
        "机构调研密度",
        "公告提示风险",
    ]
    return any(w in event for w in broad_patterns)


def direction_evidence_quality(cluster):
    stock_names = set()
    non_stock_events = 0
    single_stock_trade_feedback_events = 0
    for item in cluster.get("items", []):
        event = item.get("event", "")
        stock_names |= extract_stock_names_from_event(event)
        if is_single_stock_trade_feedback(item):
            single_stock_trade_feedback_events += 1
        if is_non_stock_direction_event(item):
            non_stock_events += 1
    return {
        "stock_count": len(stock_names),
        "stocks": sorted(stock_names),
        "non_stock_events": non_stock_events,
        "single_stock_trade_feedback_events": single_stock_trade_feedback_events,
        "is_direction_level": (
            non_stock_events >= 2
            or (len(stock_names) >= MIN_DIRECTION_STOCKS and non_stock_events >= 1)
        ),
    }


def evidence_delivery_quality(cluster, limit=10):
    evidence = select_evidence(cluster, limit)
    sources = items_evidence_sources(evidence)
    layers = source_layers(sources)
    direction_quality = cluster.get("direction_quality") or _causal_direction_quality(evidence)
    causal_quality = causal_chain_quality(cluster) if cluster.get("causal_method") else {"ready": False, "role_counts": {}}
    return {
        "direction": cluster["name"],
        "evidence_rows": len(evidence),
        "source_count": len(sources),
        "sources": sorted(sources),
        "source_layers": sorted(layers),
        "direction_quality": direction_quality,
        "causal_quality": causal_quality,
        "is_delivery_ready": (
            causal_quality["ready"]
            and len(evidence) >= 3
            and len(sources) >= MIN_CLUSTER_SOURCES
            and len(layers) >= MIN_CLUSTER_SOURCE_LAYERS
        ),
    }


def build_report(clusters, out_path, pool, integrated_short_term_sentiment=None):
    from docx import Document
    from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE
    from docx.enum.text import WD_LINE_SPACING
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt

    def set_para(index, text):
        para = doc.paragraphs[index]
        text = sanitize_delivery_residue(text)
        if para.runs:
            para.runs[0].text = text
            for run in para.runs[1:]:
                run.text = ""
        else:
            para.text = text

    def set_cell(table_index, row, col, text):
        doc.tables[table_index].rows[row].cells[col].text = sanitize_delivery_residue(text)

    def set_row(table_index, row, values):
        for col, value in enumerate(values):
            set_cell(table_index, row, col, value)

    def report_clip(value, limit=64):
        value = sanitize_delivery_residue(str(value or "")).strip()
        if len(value) <= limit:
            return value
        return value[:limit].rstrip("，；。 ") + "。"

    def clear_row_height(table_row):
        tr_pr = table_row._tr.get_or_add_trPr()
        for element in list(tr_pr):
            if element.tag == qn("w:trHeight"):
                tr_pr.remove(element)
        table_row.height = None
        table_row.height_rule = None

    def clear_row(table_index, row, compact=False):
        table_row = doc.tables[table_index].rows[row]
        clear_row_height(table_row)
        for cell in table_row.cells:
            cell.text = ""
            tc_pr = cell._tc.get_or_add_tcPr()
            shading = tc_pr.find(qn("w:shd"))
            if shading is None:
                shading = OxmlElement("w:shd")
                tc_pr.append(shading)
            shading.set(qn("w:fill"), "FFFFFF")
            shading.set(qn("w:val"), "clear")
            borders = tc_pr.find(qn("w:tcBorders"))
            if borders is None:
                borders = OxmlElement("w:tcBorders")
                tc_pr.append(borders)
            for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
                border = borders.find(qn(f"w:{edge}"))
                if border is None:
                    border = OxmlElement(f"w:{edge}")
                    borders.append(border)
                border.set(qn("w:val"), "nil")
            margins = tc_pr.find(qn("w:tcMar"))
            if margins is None:
                margins = OxmlElement("w:tcMar")
                tc_pr.append(margins)
            for edge in ("top", "left", "bottom", "right"):
                margin = margins.find(qn(f"w:{edge}"))
                if margin is None:
                    margin = OxmlElement(f"w:{edge}")
                    margins.append(margin)
                margin.set(qn("w:w"), "0")
                margin.set(qn("w:type"), "dxa")
            for para in cell.paragraphs:
                run = para.runs[0] if para.runs else para.add_run()
                run.text = " "
                run.font.size = Pt(1)
                run.font.hidden = True
                para.paragraph_format.space_before = Pt(0)
                para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.line_spacing = Pt(1)
                para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        if compact:
            table_row.height = Pt(1)
            table_row.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY

    def clear_table(table_index, compact=False):
        table = doc.tables[table_index]
        for row in range(len(table.rows)):
            clear_row(table_index, row, compact=compact)
        if compact:
            tbl_pr = table._tbl.tblPr
            borders = tbl_pr.first_child_found_in("w:tblBorders")
            if borders is None:
                borders = OxmlElement("w:tblBorders")
                tbl_pr.append(borders)
            for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
                border = borders.find(qn(f"w:{edge}"))
                if border is None:
                    border = OxmlElement(f"w:{edge}")
                    borders.append(border)
                border.set(qn("w:val"), "nil")
            table.autofit = False

    def fill_evidence_table(table_index, cluster):
        set_row(table_index, 0, EVIDENCE_HEADERS)
        for row in range(1, len(doc.tables[table_index].rows)):
            clear_row(table_index, row, compact=True)
        evidence = select_evidence(cluster, len(doc.tables[table_index].rows) - 1)
        for row, item in enumerate(evidence, 1):
            clear_row_height(doc.tables[table_index].rows[row])
            set_row(table_index, row, [
                f"({row})",
                item["source"],
                item["date"],
                delivery_event_text(item),
                item.get("meaning") or evidence_meaning(cluster["name"], item),
            ])

    def add_row_flag(row, tag, value=None):
        tr_pr = row._tr.get_or_add_trPr()
        if tr_pr.find(qn(tag)) is not None:
            return
        element = OxmlElement(tag)
        if value is not None:
            element.set(qn("w:val"), value)
        tr_pr.append(element)

    def remove_row_flag(row, tag):
        tr_pr = row._tr.get_or_add_trPr()
        for element in list(tr_pr):
            if element.tag == qn(tag):
                tr_pr.remove(element)

    def polish_tables():
        repeat_header_tables = {0, 6, 10, 14, 18, 22, 23, 24}
        evidence_label_tables = {5, 9, 13, 17, 21}
        for table_index, table in enumerate(doc.tables):
            for row_index, row in enumerate(table.rows):
                add_row_flag(row, "w:cantSplit")
                for cell in row.cells:
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if table_index in repeat_header_tables and table.rows:
                add_row_flag(table.rows[0], "w:tblHeader", "true")
                for cell in table.rows[0].cells:
                    for para in cell.paragraphs:
                        para.paragraph_format.keep_with_next = True
            if table_index in evidence_label_tables and table.rows:
                for cell in table.rows[0].cells:
                    for para in cell.paragraphs:
                        para.paragraph_format.keep_with_next = True

    def sanitize_paragraph(para):
        cleaned = sanitize_delivery_residue(para.text)
        if cleaned == para.text:
            return
        if para.runs:
            para.runs[0].text = cleaned
            for run in para.runs[1:]:
                run.text = ""
        else:
            para.text = cleaned

    def sanitize_document_text():
        for para in doc.paragraphs:
            sanitize_paragraph(para)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        sanitize_paragraph(para)

    def compact_hidden_tail_paragraph(index):
        para = doc.paragraphs[index]
        para.style = doc.styles["Normal"]
        p_pr = para._p.get_or_add_pPr()
        for tag in ("w:numPr", "w:pBdr", "w:pageBreakBefore", "w:keepNext", "w:keepLines"):
            for element in list(p_pr):
                if element.tag == qn(tag):
                    p_pr.remove(element)
        for run in para.runs:
            run.text = ""
        run = para.runs[0] if para.runs else para.add_run()
        run.text = " "
        run.font.size = Pt(1)
        run.font.hidden = True
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.line_spacing = Pt(1)
        para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY

    primary_pool = primary_events(pool)
    ready_clusters = [
        c for c in clusters
        if c.get("causal_method") in ALLOWED_CAUSAL_METHODS
        and causal_chain_quality(c)["ready"]
    ]
    industry_top = [
        c for c in ready_clusters
        if c.get("causal_method") == "event_text_exact_theme_role_chain_v1"
    ]
    if len(industry_top) < MIN_REPORT_CAUSAL_CHAINS:
        raise RuntimeError("scientific gate: insufficient independently evidenced industry causal chains")
    shutil.copy2(LOCKED_TEMPLATE, out_path)
    doc = Document(str(out_path))
    real_top = (industry_top + [c for c in ready_clusters if c not in industry_top])[:5]
    top = real_top + [None] * (5 - len(real_top))
    width = parse_width_fact(primary_pool)
    if not width:
        raise RuntimeError("scientific gate: verified market breadth is required before rendering")
    zero_chain_summary = (
        f"{width['date']}{width['scope']}上涨家数{width['up']}、下跌家数{width['down']}、"
        f"上涨占比{width['ratio']}，{width['label']}；"
        "达到三重证据标准的行业因果主线为0条。"
    )

    window = _expected_recent_window_dates()
    window_text = "、".join(cn_date(day) for day in window)
    event_window_start, event_window_end = event_window_bounds()
    event_window_text = (
        f"{event_window_start.strftime('%Y-%m-%d %H:%M')} 至 "
        f"{event_window_end.strftime('%Y-%m-%d %H:%M')}"
    )
    set_para(0, "A股热点舆情研判")
    set_para(1, "市场方向、热点强度、资金确认与次日条件")
    set_para(2, f"观察窗口：{event_window_text}；最新完整盘面：{width['date']}")
    set_para(3, "一、核心结论")
    core_names = [c["name"] for c in real_top[:3]]
    short_term_sentiment = (
        integrated_short_term_sentiment
        or short_term_sentiment_assessment(primary_pool, real_top)
    )
    short_term_dimensions = short_term_sentiment.get("dimensions") or {}
    dimension_summary = "；".join(
        f"{row.get('label', key)}：{row.get('value') or '证据缺失'}"
        for key, row in short_term_dimensions.items()
    )
    set_para(
        4,
        f"总判断：短线情绪判断：{short_term_sentiment['label']}，"
        f"中级周期处于{short_term_sentiment.get('intermediate_cycle', '证据不足')}，"
        f"短线处于{short_term_sentiment.get('short_term_stage', '证据不足')}。"
        f"{width['date']}上涨{width['up']}家、下跌{width['down']}家、上涨占比{width['ratio']}，"
        f"属于{width['label']}；五维事实：{dimension_summary}；"
        f"置信度：{short_term_sentiment.get('confidence', '低')}；"
        f"冲突说明：{short_term_sentiment.get('conflict_statement', '证据不足')}。"
        "结论含义：市场有赚钱效应，但加速阶段只按次日量化条件确认，不把高热度直接等同于趋势延续。",
    )
    set_para(5, market_width_sentence(primary_pool))
    market_ladder = _market_theme_breadth_snapshot(primary_pool, width["date"])
    ladder_text = "、".join(f"{name}{count}家" for name, count in market_ladder[:6]) or "未形成可量化梯队"
    unclosed = next((
        (name, count) for name, count in market_ladder
        if not any(name in core or core in name for core in core_names)
    ), None)
    set_para(
        6,
        f"热点强度：{ladder_text}。"
        + (
            f"主线排序为{'＞'.join(core_names)}，这些方向同时具备事件催化、板块宽度和资金确认；"
            if core_names else "当前没有同时通过事件、板块宽度和资金确认的方向；"
        )
        + (
            f"{unclosed[0]}虽有{unclosed[1]}家涨停，但证据闭环不足，只列高热观察，不进入主线排序。"
            if unclosed else "未发现需要单列的高热未闭环方向。"
        ),
    )
    set_para(
        7,
        "六项结论："
        f"市场方向：{width['label']}，上涨{width['up']}家、下跌{width['down']}家；"
        + (
            f"最强主题：{real_top[0]['name']}（{real_top[0]['stance']}）；"
            f"第二主题：{real_top[1]['name']}（{real_top[1]['stance']}）；"
            f"主要风险：{report_clip((real_top[0].get('causal') or {}).get('invalidation', ''), 46)}；"
            f"资金行为：{report_clip((real_top[0].get('causal') or {}).get('participant_feedback', ''), 46)}；"
            f"下一步观察：{report_clip((real_top[0].get('causal') or {}).get('next_check', ''), 46)}"
            if len(real_top) >= 2
            else (
                f"最强主题：{real_top[0]['name']}（{real_top[0]['stance']}）；"
                "第二主题：暂无第二条通过三重证据标准的主题；"
                f"主要风险：{report_clip((real_top[0].get('causal') or {}).get('invalidation', ''), 46)}；"
                f"资金行为：{report_clip((real_top[0].get('causal') or {}).get('participant_feedback', ''), 46)}；"
                f"下一步观察：{report_clip((real_top[0].get('causal') or {}).get('next_check', ''), 46)}"
                if real_top
                else (
                    "最强主题：暂无；第二主题：暂无；"
                    "主要风险：市场尚未形成可验证的行业因果主线；"
                    "资金行为：未出现达到三重证据标准的主题资金反馈；"
                    "下一步观察：等待新触发事实获得盘面与参与者共同确认"
                )
            )
        ),
    )

    set_para(8, "二、因果主线排序")
    set_row(0, 0, ["序号", "因果主线", "触发事实", "传导与交叉检验", "当前状态", "失效条件"])

    for i, c in enumerate(top[:5], 1):
        if c is None:
            clear_row(0, i, compact=True)
            continue
        causal = c.get("causal") or {}
        set_row(0, i, [
            str(i),
            c["name"],
            report_clip(causal.get("catalyst_fact", ""), 48),
            report_clip(f"盘面：{causal.get('market_feedback', '')}；资金：{causal.get('participant_feedback', '')}", 72),
            cluster_role_text(c),
            summary_risk_text(c),
        ])

    theme_table_sets = [
        (1, 2, 3, 4, 5, 6, top[0]),
        (7, 8, None, None, 9, 10, top[1]),
        (11, 12, None, None, 13, 14, top[2]),
        (15, 16, None, None, 17, 18, top[3]),
        (19, 20, None, None, 21, 22, top[4]),
    ]
    set_para(10, "三、因果主线深度分析")
    for title_table, kv_table, layer_table, watch_table, evidence_label_table, evidence_table, c in theme_table_sets:
        if c is None:
            for table_index in [title_table, kv_table, layer_table, watch_table, evidence_label_table, evidence_table]:
                if table_index is not None:
                    clear_table(table_index, compact=True)
            continue
        set_cell(title_table, 0, 0, c["name"])
        set_cell(evidence_label_table, 0, 0, "事实证据")
        kv_rows = cluster_fact_rows(c)
        for row in range(len(doc.tables[kv_table].rows)):
            clear_row(kv_table, row)
        max_rows = min(len(doc.tables[kv_table].rows), len(kv_rows))
        for row in range(max_rows):
            set_row(kv_table, row, kv_rows[row])
        if layer_table is not None:
            causal = c.get("causal") or {}
            catalyst_item = _first_role_item(c.get("items", []), "catalyst", c.get("name", "")) or {}
            variable = catalyst_item.get("causal_variable", "")
            deep_rows = [
                ["链路环节", "核心事实", "作用变量", "交叉检验", "反证或失效"],
                ["触发事实", causal.get("catalyst_fact", ""), variable, causal.get("market_feedback", ""), causal.get("counterevidence", "")],
                ["传导逻辑", causal.get("mechanism", ""), variable, causal.get("participant_feedback", ""), causal.get("invalidation", "")],
                ["盘面确认", causal.get("market_feedback", ""), c.get("name", ""), cluster_role_text(c), causal.get("counterevidence", "")],
                ["参与者确认", causal.get("participant_feedback", ""), c.get("name", ""), cluster_role_text(c), causal.get("invalidation", "")],
                ["反证与失效", causal.get("counterevidence", ""), c.get("name", ""), causal.get("next_check", ""), causal.get("invalidation", "")],
            ]
            for row, values in enumerate(deep_rows):
                set_row(layer_table, row, values)
        if watch_table is not None:
            fact_rows = cluster_fact_rows(c)
            set_row(watch_table, 0, fact_rows[4])
            set_row(watch_table, 1, fact_rows[5])
        fill_evidence_table(evidence_table, c)

    set_row(23, 0, ["参与者", "可观察事实", "一致或分歧", "对结论影响"])
    participant_rows = []
    participant_specs = [
        ("机构", {"机构渠道"}),
        ("短线资金", {"交易复盘", "游资社区"}),
        ("公开情绪样本", {"散户社区"}),
    ]
    for label, wanted_layers in participant_specs:
        match = next((
            item
            for c in real_top
            for item in c.get("items", [])
            if "participant" in item.get("causal_roles", [])
            and source_layer(item.get("source", "")) in wanted_layers
        ), None)
        if match:
            participant_rows.append([
                label,
                _short_causal_fact(match),
                "与主线同向" if match.get("causal_polarity") != "negative" else "与主线存在分歧",
                match.get("meaning", ""),
            ])
        else:
            participant_rows.append([label, "本轮没有可进入主线的独立样本。", "不计入主线", "不提高也不降低结论强度。"])
    for row, values in enumerate(participant_rows, 1):
        set_row(23, row, values)

    first_causal = (
        real_top[0].get("causal") or {}
        if real_top
        else {
            "conclusion": zero_chain_summary,
            "counterevidence": "未通过三重证据标准的事件不进入行业结论。",
            "next_check": "继续核验新触发事实是否同时获得盘面与参与者确认。",
            "market_feedback": (
                f"{width['date']}上涨{width['up']}家、下跌{width['down']}家，"
                f"上涨占比{width['ratio']}，{width['label']}。"
            ),
            "participant_feedback": "达到参与者确认标准的行业主线为0条。",
        }
    )
    role_totals = Counter(
        role for c in real_top for item in c.get("items", []) for role in item.get("causal_roles", [])
    )
    set_row(24, 0, ["结论检验", "判断依据"])
    set_row(24, 1, ["核心结论", first_causal.get("conclusion", "")])
    set_row(24, 2, ["证据闭环", f"触发事实{role_totals['catalyst']}条、盘面确认{role_totals['market']}条、参与者确认{role_totals['participant']}条。"])
    set_row(24, 3, ["最大反证", first_causal.get("counterevidence", "")])
    set_row(24, 4, ["下一步观察", first_causal.get("next_check", "")])

    set_para(30, f"情绪与资金行为：{first_causal.get('market_feedback', '')} 参与者资金证据：{first_causal.get('participant_feedback', '')}")
    if len(industry_top) > 1:
        second_cluster = industry_top[1]
        second_stocks = clean_join((second_cluster.get("direction_quality") or {}).get("stocks", [])[:6])
        if not second_stocks:
            second_stocks = "该产业链的方向级交易样本"
        set_para(
            31,
            f"产业链与观察标的：第二条产业链为{second_cluster['name']}，当前状态为{second_cluster['stance']}；"
            f"观察对象包括{second_stocks}，用于检验触发事实、盘面反馈与参与者证据能否继续同向。",
        )
    elif real_top:
        set_para(31, "产业链与观察标的：仅保留已通过三重证据标准的行业主线，不补充第二条主线。")
    else:
        set_para(31, "产业链与观察标的：行业主线通过数为0，仅保留市场宽度与已落盘事实。")

    set_para(33, "四、参与者证据")
    set_para(
        34,
        "情绪与资金行为观察：淘股吧、雪球、微博、知乎、东方财富股吧、韭研公社反映短线交易者与散户分歧；"
        "财联社、金十数据承接主流财经与海外映射。社区热度只用于情绪确认，结论以公告、监管和盘面交叉证据为准。",
    )
    set_para(35, "五、下一步观察计划")
    for paragraph_index in range(36, 39):
        c = real_top[paragraph_index - 36] if paragraph_index - 36 < len(real_top) else None
        if c:
            set_para(paragraph_index, f"{c['name']}：{(c.get('causal') or {}).get('next_check', '')}")
        else:
            set_para(paragraph_index, "")
            compact_hidden_tail_paragraph(paragraph_index)
    set_para(39, f"市场宽度：{width['date']}上涨{width['up']}家、下跌{width['down']}家，上涨占比{width['ratio']}，{width['label']}。")
    set_para(40, "六、风险边界")
    set_para(41, "共同失效边界：热点宽度快速收缩、核心标的同步转弱、参与者资金由同向转为净流出，或出现重大澄清与风险公告。")
    set_para(42, "")
    compact_hidden_tail_paragraph(42)
    for paragraph_index in range(11, 33):
        if not doc.paragraphs[paragraph_index].text.strip():
            compact_hidden_tail_paragraph(paragraph_index)

    sanitize_document_text()
    compact_hidden_tail_paragraph(42)
    polish_tables()
    doc.save(out_path)


USER_TEMPLATE_FALLBACK = LOCKED_TEMPLATE


def _historical_recent_calendar_dates_disabled(now=None):
    raise RuntimeError("historical calendar-day window is permanently disabled")
    now = now or datetime.now(timezone(timedelta(hours=8)))
    return [(now.date() - timedelta(days=offset)) for offset in range(2, -1, -1)]


def cn_date(d):
    return f"{d.month}月{d.day}日"


def ymd_date(d):
    return d.strftime("%Y%m%d")


def _china_datetime(value=None):
    if value is None:
        override = os.environ.get(AS_OF_ENV, "").strip()
        if override:
            try:
                value = datetime.fromisoformat(override.replace("Z", "+00:00"))
            except ValueError as exc:
                raise RuntimeError(f"invalid {AS_OF_ENV}: {override}") from exc
        else:
            value = datetime.now(CHINA_TZ)
    if value.tzinfo is None:
        return value.replace(tzinfo=CHINA_TZ)
    return value.astimezone(CHINA_TZ)


def event_window_bounds(now=None):
    end = _china_datetime(now)
    return end - timedelta(hours=EVENT_WINDOW_HOURS), end


def event_window_calendar_dates(now=None):
    start, end = event_window_bounds(now)
    days = []
    cursor = start.date()
    while cursor <= end.date():
        days.append(cursor)
        cursor += timedelta(days=1)
    return days


def _publication_record(value, *, precision, evidence, now=None):
    start, end = event_window_bounds(now)
    value = _china_datetime(value)
    if precision == "date" and value.date() == start.date():
        return None
    if value < start or value > end:
        return None
    return {
        "published_at": value.isoformat(timespec="seconds"),
        "date": cn_date(value.date()),
        "time_precision": precision,
        "time_evidence": evidence,
        "age_hours": round(max(0.0, (end - value).total_seconds() / 3600), 2),
    }


def extract_publication(text, url="", now=None):
    now = _china_datetime(now)
    haystack = f"{url} {text or ''}".strip()
    if not haystack:
        return None

    raw = str(text or "").strip()
    if raw and len(raw) <= 80:
        try:
            parsed = parsedate_to_datetime(raw)
            if parsed:
                return _publication_record(parsed, precision="second", evidence="rfc_datetime", now=now)
        except Exception:
            pass

    epoch_match = re.fullmatch(r"\s*(\d{10}|\d{13})\s*", raw)
    if epoch_match:
        stamp = int(epoch_match.group(1))
        if len(epoch_match.group(1)) == 13:
            stamp /= 1000
        try:
            parsed = datetime.fromtimestamp(stamp, CHINA_TZ)
            return _publication_record(parsed, precision="second", evidence="epoch_timestamp", now=now)
        except Exception:
            pass

    # Several native finance pages encode an article's publication day as the
    # leading YYYYMMDD component of its article URL.  Treat that as date-only
    # evidence, never as an inferred intraday time, and still apply the exact
    # 72-hour boundary in _publication_record.
    compact_url_date = re.search(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)", str(url or ""))
    if compact_url_date:
        try:
            parsed = datetime(
                int(compact_url_date.group(1)), int(compact_url_date.group(2)), int(compact_url_date.group(3)),
                tzinfo=CHINA_TZ,
            )
            return _publication_record(parsed, precision="date", evidence=compact_url_date.group(0), now=now)
        except ValueError:
            pass

    relative_rules = [
        (r"(\d+)\s*分钟(?:以)?前", "minutes"),
        (r"(\d+)\s*小时(?:以)?前", "hours"),
        (r"(\d+)\s*天(?:以)?前", "days"),
        (r"(\d+)\s*(?:minutes?|mins?)\s+ago", "minutes"),
        (r"(\d+)\s*(?:hours?|hrs?)\s+ago", "hours"),
        (r"(\d+)\s*days?\s+ago", "days"),
    ]
    for pattern, unit in relative_rules:
        match = re.search(pattern, haystack, flags=re.IGNORECASE)
        if match:
            amount = int(match.group(1))
            parsed = now - timedelta(**{unit: amount})
            return _publication_record(parsed, precision="relative", evidence=match.group(0), now=now)
    if "刚刚" in haystack:
        return _publication_record(now, precision="relative", evidence="刚刚", now=now)

    full_date = re.search(
        r"(?P<y>20\d{2})[年\-/.](?P<m>\d{1,2})[月\-/.](?P<d>\d{1,2})日?"
        r"(?:[ T\u00a0]*(?P<h>\d{1,2})[:：](?P<mi>\d{2})(?::(?P<s>\d{2}))?)?",
        haystack,
    )
    if full_date:
        has_time = full_date.group("h") is not None
        try:
            parsed = datetime(
                int(full_date.group("y")), int(full_date.group("m")), int(full_date.group("d")),
                int(full_date.group("h") or 0), int(full_date.group("mi") or 0), int(full_date.group("s") or 0),
                tzinfo=CHINA_TZ,
            )
            return _publication_record(
                parsed,
                precision="second" if full_date.group("s") else ("minute" if has_time else "date"),
                evidence=full_date.group(0),
                now=now,
            )
        except ValueError:
            pass

    for fmt in ["%b %d, %Y %H:%M", "%b %d, %Y", "%B %d, %Y %H:%M", "%B %d, %Y"]:
        english = re.search(r"[A-Za-z]{3,9}\s+\d{1,2},\s+20\d{2}(?:\s+\d{1,2}:\d{2})?", haystack)
        if not english:
            break
        try:
            parsed = datetime.strptime(english.group(0), fmt).replace(tzinfo=CHINA_TZ)
            precision = "minute" if ":" in english.group(0) else "date"
            return _publication_record(parsed, precision=precision, evidence=english.group(0), now=now)
        except ValueError:
            continue

    relative_day = re.search(r"(今天|今日|昨天|昨日|前天)(?:\s*(\d{1,2})[:：](\d{2}))?", haystack)
    if relative_day:
        offsets = {"今天": 0, "今日": 0, "昨天": 1, "昨日": 1, "前天": 2}
        day = now.date() - timedelta(days=offsets[relative_day.group(1)])
        has_time = relative_day.group(2) is not None
        parsed = datetime.combine(
            day,
            datetime.strptime(f"{relative_day.group(2) or 0}:{relative_day.group(3) or 0}", "%H:%M").time(),
            tzinfo=CHINA_TZ,
        )
        return _publication_record(
            parsed,
            precision="minute" if has_time else "date",
            evidence=relative_day.group(0),
            now=now,
        )

    month_day = re.search(
        r"(?<!\d)(?P<m>\d{1,2})[月\-/.](?P<d>\d{1,2})日?"
        r"(?:\s*(?P<h>\d{1,2})[:：](?P<mi>\d{2}))?",
        haystack,
    )
    if month_day:
        has_time = month_day.group("h") is not None
        try:
            parsed = datetime(
                now.year, int(month_day.group("m")), int(month_day.group("d")),
                int(month_day.group("h") or 0), int(month_day.group("mi") or 0), tzinfo=CHINA_TZ,
            )
            if parsed > now + timedelta(days=1):
                parsed = parsed.replace(year=now.year - 1)
            return _publication_record(
                parsed,
                precision="minute" if has_time else "date",
                evidence=month_day.group(0),
                now=now,
            )
        except ValueError:
            pass
    return None


def recent_date_tokens(now=None):
    tokens = []
    for d in event_window_calendar_dates(now):
        tokens.extend([
            d.strftime("%Y%m%d"),
            d.strftime("%Y-%m-%d"),
            d.strftime("%Y/%m/%d"),
            f"{d.year}年{d.month}月{d.day}日",
            f"{d.month}月{d.day}日",
            f"{d.month:02d}月{d.day:02d}日",
            f"/{d.strftime('%Y%m%d')}/",
            f"/{d.strftime('%Y/%m/%d')}/",
        ])
    return tokens


def extract_recent_date(text, url="", now=None):
    publication = extract_publication(text, url, now)
    return publication["date"] if publication else ""


def has_recent_date(text, url="", now=None):
    return bool(extract_recent_date(text, url, now))


def has_event_window_calendar_date(text, url="", now=None):
    haystack = f"{url} {text}"
    return any(token in haystack for token in recent_date_tokens(now))


def verify_locked_template():
    global LOCKED_TEMPLATE, LOCKED_TEMPLATE_SHA256
    candidates = [
        ("locked_user_g_template", LOCKED_TEMPLATE, LOCKED_TEMPLATE_SHA256),
    ]
    errors = []
    for label, path, expected_sha in candidates:
        if not path.exists():
            errors.append(f"{label} missing: {path}")
            continue
        profile = template_profile(path)
        if expected_sha and profile["sha256"] != expected_sha:
            errors.append(f"{label} sha256 mismatch: {profile['sha256']}")
            continue
        if profile["paragraphs"] != LOCKED_TEMPLATE_PARAGRAPHS or profile["tables"] != LOCKED_TEMPLATE_TABLES:
            errors.append(f"{label} structure mismatch: {json.dumps(profile, ensure_ascii=False)}")
            continue
        if profile["table_shapes"] != LOCKED_TEMPLATE_SHAPES:
            errors.append(f"{label} table-shape mismatch: {json.dumps(profile['table_shapes'], ensure_ascii=False)}")
            continue
        LOCKED_TEMPLATE = path
        LOCKED_TEMPLATE_SHA256 = profile["sha256"]
        profile["template_label"] = label
        return profile
    print("BLOCKED locked template unavailable")
    for err in errors:
        print(err)
    return None


def dynamic_source_urls():
    return list(NATIVE_DISCOVERY_URLS)


def discover_source_article_urls(max_per_source=18):
    urls = []
    seen = {url for _source, url in dynamic_source_urls()}
    allowed_hosts = ["cls", "stcn", "eastmoney", "10jqka", "xueqiu", "weibo", "zhihu", "sina", "cs.com", "cnstock", "tgb", "jiuyangongshe", "sse", "szse"]
    date_markers = recent_date_tokens()
    article_markers = date_markers + ["/article/detail/", "/a/2026", "/c677", "/doc-", "/bbs/", "/a/", "/news,", "/commonDetail/", "/topicDetail/"]
    for source, entry_url in dynamic_source_urls():
        soup = fetch_soup(entry_url)
        if not soup:
            continue
        picked = 0
        for tag in soup.find_all("a", href=True):
            title = clean_text(tag.get_text(" ", strip=True))
            href = urljoin(entry_url, tag["href"])
            host = urlparse(href).netloc.lower()
            if not host or href in seen:
                continue
            if not any(key in host for key in allowed_hosts):
                continue
            combined = f"{title} {href}"
            if not any(marker in combined for marker in article_markers):
                continue
            if not has_event_window_calendar_date(combined, href) and source_layer(source) not in {"游资社区", "散户社区", "研究社区"}:
                continue
            if len(title) >= 8 and value_signal_score(title) < 1 and source_layer(source) in {"主流财经", "海外映射"}:
                continue
            seen.add(href)
            urls.append((source_name_from_url(href) if source == "财经平台" else source, href))
            picked += 1
            if picked >= max_per_source:
                break
        time.sleep(0.08)
    return urls


def _market_query_date_labels(now=None):
    return [f"{d.year}年{d.month}月{d.day}日" for d in event_window_calendar_dates(now)]


def dynamic_search_queries(now=None):
    labels = _market_query_date_labels(now)
    date_scope = " ".join(labels)
    terms = list(MARKET_WIDE_QUERY_TERMS)
    queries = []
    for index in range(0, len(terms), MARKET_WIDE_QUERY_GROUP_SIZE):
        group = terms[index:index + MARKET_WIDE_QUERY_GROUP_SIZE]
        scoped_group = group if "A股" in group else ["A股", *group]
        queries.append(f"{date_scope} {' '.join(scoped_group)}")
    return queries


def five_site_wide_search_specs(now=None):
    date_scope = " ".join(_market_query_date_labels(now))
    terms = list(FIVE_SITE_WIDE_TERMS)
    return [
        {
            "source": source,
            "native_url": native_url,
            "domain": domain,
            "terms": terms,
            "query": f"{date_scope} site:{domain} {' '.join(terms)}",
        }
        for source, native_url, domain in FIVE_SITE_NATIVE_DISCOVERY
    ]


def acquisition_query_audit(now=None):
    now = _china_datetime(now)
    event_window_start, event_window_end = event_window_bounds(now)
    terms = list(MARKET_WIDE_QUERY_TERMS)
    labels = _market_query_date_labels(now)
    groups = [terms[index:index + MARKET_WIDE_QUERY_GROUP_SIZE] for index in range(0, len(terms), MARKET_WIDE_QUERY_GROUP_SIZE)]
    expected_queries = [
        f"{' '.join(labels)} {' '.join(group if 'A股' in group else ['A股', *group])}"
        for group in groups
    ]
    actual_queries = dynamic_search_queries(now)
    native_urls = dynamic_source_urls()
    five_site_specs = five_site_wide_search_specs(now)
    reasons = []
    if len(terms) != 36:
        reasons.append(f"market_wide_term_count={len(terms)} expected=36")
    if len(set(terms)) != len(terms):
        reasons.append("market_wide_terms_not_unique")
    if any(len(group) != MARKET_WIDE_QUERY_GROUP_SIZE for group in groups):
        reasons.append(f"market_wide_group_size_not_{MARKET_WIDE_QUERY_GROUP_SIZE}")
    if actual_queries != expected_queries:
        reasons.append("search_queries_not_exactly_generated_from_36_market_wide_terms")
    if native_urls != list(NATIVE_DISCOVERY_URLS):
        reasons.append("native_discovery_urls_contain_derived_or_mutated_entries")
    if any(
        set(spec.get("terms", [])) != set(FIVE_SITE_WIDE_TERMS)
        or not set(spec.get("terms", [])).issubset(set(MARKET_WIDE_QUERY_TERMS))
        or spec.get("source") not in REQUIRED_SOCIAL_PLATFORMS
        for spec in five_site_specs
    ):
        reasons.append("five_site_queries_not_generated_from_market_wide_terms")
    return {
        "ok": not reasons,
        "reasons": reasons,
        "event_window_hours": EVENT_WINDOW_HOURS,
        "event_window_start": event_window_start.isoformat(timespec="seconds"),
        "event_window_end": event_window_end.isoformat(timespec="seconds"),
        "event_window_calendar_dates": [cn_date(day) for day in event_window_calendar_dates(now)],
        "market_validation_trading_dates": [cn_date(day) for day in recent_trading_dates(now)],
        "market_wide_term_count": len(terms),
        "market_wide_terms": terms,
        "query_count": len(actual_queries),
        "queries": actual_queries,
        "native_discovery_urls": [{"source": source, "url": url} for source, url in native_urls],
        "five_site_native_discovery_urls": [
            {"source": source, "url": native_url, "domain": domain}
            for source, native_url, domain in FIVE_SITE_NATIVE_DISCOVERY
        ],
        "five_site_queries": five_site_specs,
        "derived_stock_or_theme_entry_count": 0 if native_urls == list(NATIVE_DISCOVERY_URLS) else None,
    }


def chrome_discovery_metadata_ok(item, now=None):
    mode = clean_text(str(item.get("discovery_mode", "")))
    if mode == "native_page":
        entry_url = str(item.get("discovery_entry_url", ""))
        return entry_url in {url for _source, url in NATIVE_DISCOVERY_URLS}
    if mode != "market_wide_query":
        return False
    # Query validation must preserve explicit trading-date tokens. clean_text()
    # intentionally removes dates for article cleanup and therefore cannot be used here.
    query = re.sub(r"\s+", " ", str(item.get("discovery_query", ""))).strip()
    terms = item.get("discovery_terms")
    if not isinstance(terms, list) or len(terms) < 2 or len(terms) != len(set(terms)):
        return False
    allowed_terms = set(MARKET_WIDE_QUERY_TERMS)
    if any(not isinstance(term, str) or term not in allowed_terms for term in terms):
        return False
    tokens = query.split()
    date_labels = set(_market_query_date_labels(now))
    query_terms = [token for token in tokens if token in allowed_terms]
    query_dates = [token for token in tokens if token in date_labels]
    if any(token not in allowed_terms and token not in date_labels for token in tokens):
        return False
    return set(query_terms) == set(terms) and bool(query_dates)


def _sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _chrome_capture_datetime(value):
    parsed = _parse_iso_datetime(value)
    if not parsed:
        return None
    return _china_datetime(parsed)


def _canonical_chrome_capture_source(file_name, payload, item):
    capture_label = clean_text(str(item.get("label") or payload.get("site") or ""))
    canonical_source = FIVE_SITE_CAPTURE_FILES.get(Path(file_name).stem, capture_label)
    if (
        Path(file_name).stem == "primary"
        and source_layer(canonical_source) == "其他来源"
        and (
            "新浪" in capture_label
            or capture_label in {"环球市场播报", "市场资讯"}
        )
    ):
        canonical_source = "新浪财经"
    return canonical_source, capture_label


FOREIGN_PRIMARY_SOURCE_MARKERS = ("港股", "美股", "环球市场", "海外市场")
FOREIGN_PRIMARY_URL_MARKERS = ("/hkstock/", "/usstock/", "/forex/", "/global/")
A_SHARE_PRIMARY_SIGNAL_TERMS = (
    "A股", "上证指数", "沪指", "深证成指", "深成指", "创业板指", "科创50", "北证50", "北交所",
)


def _primary_capture_is_a_share_relevant(item, event, url, origin_source):
    label = clean_text(str(origin_source or ""))
    normalized_url = str(url or "").lower()
    explicitly_foreign = (
        any(marker in label for marker in FOREIGN_PRIMARY_SOURCE_MARKERS)
        or any(marker in normalized_url for marker in FOREIGN_PRIMARY_URL_MARKERS)
    )
    if not explicitly_foreign:
        return True
    return bool(
        clean_text(str(item.get("a_share_mapping", "")))
        or any(term in event for term in A_SHARE_PRIMARY_SIGNAL_TERMS)
        or extract_stock_names_from_event(event)
    )


def collect_chrome_capture_events(now=None):
    """Read this run's explicitly authorized file-fed acquisition artifacts."""
    now = _china_datetime(now)
    capture_dir_value = os.environ.get(CHROME_CAPTURE_ENV, "").strip()
    if not capture_dir_value:
        raise RuntimeError(f"BLOCKED {CHROME_CAPTURE_ENV} is required for production acquisition")
    capture_dir = Path(capture_dir_value)
    required_files = required_acquisition_capture_files()
    missing = [name for name in required_files if not (capture_dir / name).is_file()]
    if missing:
        raise RuntimeError("BLOCKED acquisition capture incomplete: missing=" + ",".join(missing))

    events, seen, manifests = [], set(), []
    for file_name in [name for name in required_files if name != BUSINESS_SOCIETY_CAPTURE_FILE]:
        path = capture_dir / file_name
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"BLOCKED invalid acquisition capture {path.name}: {type(exc).__name__}:{exc}") from exc
        channel = str(payload.get("channel", ""))
        is_public_fallback = channel == PUBLIC_READONLY_FALLBACK_CHANNEL
        if is_public_fallback and os.environ.get(PUBLIC_READONLY_FALLBACK_ENV) != "1":
            raise RuntimeError(f"BLOCKED public fallback is not enabled: {path.name}")
        if not is_public_fallback and channel != "Chrome logged-in visible pages only":
            raise RuntimeError(f"BLOCKED unsupported acquisition channel: {path.name}")
        collected_at = _chrome_capture_datetime(payload.get("collectedAt"))
        if not collected_at:
            raise RuntimeError(f"BLOCKED capture timestamp missing: {path.name}")
        capture_age_minutes = (now - collected_at).total_seconds() / 60
        if capture_age_minutes < -5 or capture_age_minutes > CHROME_CAPTURE_MAX_AGE_MINUTES:
            raise RuntimeError(f"BLOCKED stale acquisition capture: {path.name} age_minutes={capture_age_minutes:.1f}")
        items = payload.get("clean")
        if not isinstance(items, list):
            raise RuntimeError(f"BLOCKED clean capture list missing: {path.name}")
        is_five_site = file_name != "primary.json"
        raw_count = int(payload.get("rawCount", 0) or 0)
        diagnostics = payload.get("collectionDiagnostics")
        supplemented_count = (
            max(0, int(diagnostics.get("snapshot_supplemented", 0) or 0))
            if isinstance(diagnostics, dict)
            else 0
        )
        if is_five_site:
            accounting = validate_capture_accounting(
                raw_count=raw_count,
                clean_count=len(items),
                clean_rows=items,
                supplemented_count=supplemented_count,
            )
            if not accounting["ok"]:
                raise RuntimeError(
                    f"BLOCKED invalid capture accounting: {path.name}:"
                    + ",".join(accounting["reasons"])
                )
        manifests.append({
            "file": path.name,
            "sha256": _sha256_file(path),
            "site": str(payload.get("site", "")),
            "collected_at": collected_at.isoformat(timespec="seconds"),
            "age_minutes": round(capture_age_minutes, 2),
            "clean_count": len(items),
            "raw_count": raw_count,
            "errors": len(payload.get("errors", []) if isinstance(payload.get("errors"), list) else []),
            "channel": channel,
            "source_url": str(payload.get("source_url", "")),
        })
        for item in items:
            if not isinstance(item, dict):
                continue
            captured_at = _chrome_capture_datetime(item.get("capturedAt"))
            if not captured_at or abs((captured_at - collected_at).total_seconds()) > 300:
                continue
            title = clean_text(str(item.get("title", "")))
            body = clean_text(str(item.get("text", "")))
            event = compose_visible_capture_event(title, body)
            source, origin_source = _canonical_chrome_capture_source(file_name, payload, item)
            url = str(item.get("href") or item.get("capturedUrl") or "")
            if not is_five_site and not _primary_capture_is_a_share_relevant(
                item,
                event,
                url,
                origin_source,
            ):
                continue
            if is_public_fallback and item.get("observation_time_only"):
                publication = _publication_record(
                    captured_at,
                    precision="capture",
                    evidence="public_readonly_observation",
                    now=now,
                )
            else:
                publication = extract_publication(str(item.get("time", "")), url, now=now)
            visible_quote_observation = (
                source == "雪球"
                and any(index_name in event for index_name in ["上证指数", "深证成指", "创业板指", "科创50"])
                and any(ch.isdigit() for ch in event)
            )
            structured_width_observation = (
                not is_five_site and _is_structured_width_observation(event)
            )
            if not publication and visible_quote_observation:
                publication = _publication_record(
                    captured_at,
                    precision="capture",
                    evidence="chrome_visible_quote_capture",
                    now=now,
                )
            if not source or not event or not publication or (
                len(event) < 25
                and not visible_quote_observation
                and not structured_width_observation
            ) or social_ui_noise_hits(event):
                continue
            importance = event_importance_score(event, source)
            if is_five_site and importance < 3 and not visible_quote_observation:
                continue
            institutional_observation = (
                not is_five_site
                and source in {"机构调研", "融资数据"}
                and any(word in event for word in ["融资", "两融", "调研", "资金"])
            )
            if (
                not is_five_site
                and importance < 3
                and len(event) < 40
                and not institutional_observation
                and not structured_width_observation
            ):
                continue
            market_feedback_markers = ["午评", "收评", "盘中", "复盘", "涨停", "跌停", "成交额", "上涨", "下跌"]
            is_browser_market_validation = not is_five_site and (
                structured_width_observation
                or sum(marker in event for marker in market_feedback_markers) >= 2
            )
            if is_browser_market_validation:
                source = f"{origin_source}·市场复盘"
            key = re.sub(r"\W+", "", f"{source}{url}{event}")[:260]
            if key in seen:
                continue
            heat_evidence = (
                clean_text(str(item.get("heat_evidence", "")))
                or (
                    f"站内高热榜第{item.get('rank')}位"
                    if item.get("rank") not in (None, "")
                    else clean_text(str(item.get("heat", "")))
                )
            ) if is_five_site else ""
            a_share_mapping = (
                clean_text(str(item.get("a_share_mapping", "")))
                or (
                    "直接涉及A股个股、板块、指数、资金或市场情绪。"
                    if (
                        any(term in event for term in FIVE_SITE_MARKET_TERMS)
                        or bool(extract_stock_names_from_event(event))
                    )
                    else ""
                )
            ) if is_five_site else ""
            record_quality = None
            if is_five_site:
                record_quality = validate_sentiment_record(
                    source=source,
                    event=event,
                    heat_evidence=heat_evidence,
                    a_share_mapping=a_share_mapping,
                    rank=item.get("rank"),
                )
                if not record_quality["ok"]:
                    continue
            seen.add(key)
            events.append({
                "source": source,
                "origin_source": origin_source,
                "date": publication["date"],
                "published_at": publication["published_at"],
                "time_precision": publication["time_precision"],
                "time_evidence": publication["time_evidence"],
                "timestamp_kind": (
                    "hotlist_observed_at"
                    if is_five_site and is_public_fallback and item.get("observation_time_only")
                    else "published_at"
                ),
                "window_type": MARKET_VALIDATION_WINDOW_TYPE if is_browser_market_validation else EVENT_WINDOW_TYPE,
                "event": event[:900],
                "url": url,
                "theme_terms": derive_theme_terms(event, topn=6),
                "source_channel": (
                    MANDATORY_SENTIMENT_CHANNEL
                    if is_five_site
                    else "primary_public_readonly_fallback"
                    if is_public_fallback
                    else "primary_chrome_automatic"
                ),
                "discovery_mode": "native_page",
                "discovery_entry_url": str(item.get("capturedUrl", "")),
                "browser_capture_file": path.name,
                "browser_capture_sha256": manifests[-1]["sha256"],
                "capture_file": path.name,
                "capture_sha256": manifests[-1]["sha256"],
                "acquisition_channel": channel,
                "source_key": str(item.get("source_key", "")),
                "source_url": str(item.get("source_url", "") or payload.get("source_url", "")),
                "captured_at": captured_at.isoformat(timespec="seconds"),
                "observation_type": (
                    "market_breadth"
                    if structured_width_observation
                    else "visible_quote_not_causal_event"
                    if visible_quote_observation
                    else "event"
                ),
                "heat_evidence": heat_evidence,
                "a_share_mapping": a_share_mapping,
                "a_share_relevance": (
                    {
                        "status": "accepted",
                        "score": record_quality["relevance_score"],
                        "reasons": [
                            "来源级高热证据通过",
                            "A股映射与事件文本语义落地",
                            "网页残留检查通过",
                        ],
                        "quality_contract": "A_SHARE_SENTIMENT_RECORD_QUALITY_V1",
                    }
                    if record_quality is not None
                    else None
                ),
            })
    globals()["chrome_capture_manifest"] = manifests
    return events


def discover_urls(max_urls=28):
    if CHROME_ONLY_ACQUISITION:
        raise RuntimeError(CHROME_CAPTURE_REQUIRED_MESSAGE)
    import requests
    from bs4 import BeautifulSoup
    urls = []
    seen = {url for _source, url in dynamic_source_urls()}
    blocked_hosts = ("bing.com", "microsoft.com", "baidu.com")
    allowed_hosts = ["cls", "stcn", "eastmoney", "10jqka", "xueqiu", "weibo", "zhihu", "sina", "cs.com", "cnstock", "tgb", "sse", "szse"]
    for query in dynamic_search_queries():
        search_url = "https://www.bing.com/search?q=" + quote_plus(query)
        try:
            resp = requests.get(search_url, headers=HEADERS, timeout=12)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception:
            continue
        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            host = urlparse(href).netloc.lower()
            if not href.startswith("http") or any(bad in host for bad in blocked_hosts):
                continue
            if href in seen or not any(key in host for key in allowed_hosts):
                continue
            title = clean_text(tag.get_text(" ", strip=True))
            if not has_event_window_calendar_date(f"{title} {href}", href):
                continue
            seen.add(href)
            urls.append((source_name_from_url(href), href))
            if len(urls) >= max_urls:
                return urls
        time.sleep(0.08)
    return urls


def collect_search_result_events(now=None):
    if CHROME_ONLY_ACQUISITION:
        raise RuntimeError(CHROME_CAPTURE_REQUIRED_MESSAGE)
    import requests
    from bs4 import BeautifulSoup
    now = _china_datetime(now)
    events = []
    for query in dynamic_search_queries(now):
        try:
            resp = requests.get("https://www.bing.com/search?q=" + quote_plus(query), headers=HEADERS, timeout=12)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception:
            continue
        for item in soup.select("li.b_algo")[:8]:
            title = clean_text(item.get_text(" ", strip=True))
            link = item.find("a", href=True)
            url = link["href"] if link else ""
            publication = extract_publication(title, url, now)
            if not publication or len(title) < 30:
                continue
            source = source_name_from_url(url) if url else "主流财经"
            if source in REQUIRED_SOCIAL_PLATFORMS:
                continue
            if event_importance_score(title, source) < 35:
                continue
            discovery_terms = [term for term in MARKET_WIDE_QUERY_TERMS if term in query.split()]
            events.append({
                "source": source,
                "date": publication["date"],
                "published_at": publication["published_at"],
                "time_precision": publication["time_precision"],
                "time_evidence": publication["time_evidence"],
                "window_type": EVENT_WINDOW_TYPE,
                "event": title[:180],
                "url": url,
                "source_channel": "primary_search_result",
                "discovery_mode": "market_wide_query",
                "discovery_query": query,
                "discovery_terms": discovery_terms,
            })
        time.sleep(0.08)
    return events


def collect_five_site_public_events(now=None):
    if CHROME_ONLY_ACQUISITION:
        raise RuntimeError(CHROME_CAPTURE_REQUIRED_MESSAGE)
    import requests
    from bs4 import BeautifulSoup

    now = _china_datetime(now)
    events = []
    seen = set()

    def append_event(source, publication, event, url, *, mode, query="", terms=None, entry_url=""):
        event = sanitize_five_site_event_text(event)
        if not publication or len(event) < 25 or social_ui_noise_hits(event):
            return
        market_hits = sum(1 for term in FIVE_SITE_MARKET_TERMS if term in event)
        if event_importance_score(event, source) < 25 and market_hits < 2:
            return
        key = re.sub(r"\W+", "", f"{source}{url}{event}")[:220]
        if key in seen:
            return
        seen.add(key)
        events.append({
            "source": source,
            "date": publication["date"],
            "published_at": publication["published_at"],
            "time_precision": publication["time_precision"],
            "time_evidence": publication["time_evidence"],
            "window_type": EVENT_WINDOW_TYPE,
            "event": event[:520],
            "url": url,
            "theme_terms": derive_theme_terms(event, topn=6),
            "source_channel": SUPPLEMENTAL_FIVE_SITE_CHANNEL,
            "discovery_mode": mode,
            "discovery_query": query,
            "discovery_terms": list(terms or []),
            "discovery_entry_url": entry_url,
        })

    for source, native_url, _domain in FIVE_SITE_NATIVE_DISCOVERY:
        page_record = fetch_text(native_url, with_metadata=True, now=now)
        page = page_record.get("text", "")
        if not page:
            continue
        page_publication = page_record.get("publication")
        for chunk in extract_chunks(page, source=source, max_chunks=12):
            publication = extract_publication(chunk, native_url, now) or page_publication
            append_event(source, publication, chunk, native_url, mode="native_page", entry_url=native_url)

    for spec in five_site_wide_search_specs(now):
        try:
            resp = requests.get(
                "https://www.bing.com/search?q=" + quote_plus(spec["query"]),
                headers=HEADERS,
                timeout=12,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception:
            continue
        for item in soup.select("li.b_algo")[:10]:
            link = item.find("a", href=True)
            url = link["href"] if link else ""
            if spec["domain"] not in urlparse(url).netloc.lower():
                continue
            event = clean_text(item.get_text(" ", strip=True))
            publication = extract_publication(event, url, now)
            append_event(
                spec["source"],
                publication,
                event,
                url,
                mode="market_wide_query",
                query=spec["query"],
                terms=spec["terms"],
            )
        time.sleep(0.08)
    return events


REVIEW_STEM_ALIASES = {
    "industry_limitup_stats": ["industry_limitup_stats", "verified_limitup_union", "final_limitup_union_strict", "ak_stock_zt_pool_em"],
    "limitup_lhb_intersection": ["limitup_lhb_intersection", "final_limitup_union_strict", "verified_limitup_union"],
    "ak_stock_lhb_detail_em": ["ak_stock_lhb_detail_em", "ak_stock_lhb_detail_daily_sina"],
    "push2_fund_flow_resolved": ["push2_fund_flow_resolved"],
    "ak_stock_zt_pool_em": ["ak_stock_zt_pool_em", "verified_limitup_union", "final_limitup_union_strict"],
    "verified_limitup_union": ["verified_limitup_union", "final_limitup_union_strict", "ak_stock_zt_pool_em"],
    "final_limitup_union_strict": ["final_limitup_union_strict", "verified_limitup_union", "ak_stock_zt_pool_em"],
}

REVIEW_CORE_REQUIREMENTS = {
    "limitup_pool": ["ak_stock_zt_pool_em", "verified_limitup_union", "final_limitup_union_strict"],
    "lhb_detail": ["ak_stock_lhb_detail_em", "ak_stock_lhb_detail_daily_sina"],
    "fund_flow": ["push2_fund_flow_resolved"],
    "verified_union": ["verified_limitup_union", "final_limitup_union_strict", "ak_stock_zt_pool_em"],
}


def _existing_review_file(review_dir, stem, ymd):
    if not review_dir or not ymd:
        return None
    direct = review_dir / f"{stem}_{ymd}.csv"
    if direct.exists():
        return direct
    matches = sorted(review_dir.glob(f"{stem}_*.csv"))
    return matches[-1] if matches else None


def _first_review_file(review_dir, stems, ymd):
    for stem in stems:
        found = _existing_review_file(review_dir, stem, ymd)
        if found:
            return found
    return None


def local_review_data_profile(review_dir, ymd):
    found = {}
    missing = []
    for key, stems in REVIEW_CORE_REQUIREMENTS.items():
        path = _first_review_file(review_dir, stems, ymd)
        if path:
            found[key] = str(path)
        else:
            missing.append(key)
    return {
        "review_dir": str(review_dir) if review_dir else "",
        "review_ymd": ymd,
        "core_count": len(found),
        "found": found,
        "missing": missing,
        "is_usable": len(found) >= 3 and "limitup_pool" in found and "lhb_detail" in found and "fund_flow" in found,
    }


def latest_local_review_dir(now=None):
    root = Path(r"D:\C盘转移\日志\codex\reports")
    if not root.exists():
        return None, _expected_review_ymd()
    candidates = []
    for path in root.glob("*_limit_up_review_closed_loop"):
        match = re.match(r"(\d{8})_limit_up_review_closed_loop$", path.name)
        if not match:
            continue
        ymd = match.group(1)
        expected_ymd = _expected_review_ymd()
        if ymd > expected_ymd and ymd != _today_ymd():
            continue
        profile = local_review_data_profile(path, ymd)
        if profile["is_usable"]:
            # 周末执行的实时快照读取最近闭市日行情；用闭市日作为报告锚点，保留文件原名以便审计。
            effective_ymd = expected_ymd if ymd > expected_ymd else ymd
            candidates.append((effective_ymd, profile["core_count"], path))
    if not candidates:
        return None, _expected_review_ymd()
    ymd, _core_count, path = sorted(candidates)[-1]
    return path, ymd


def recent_trading_dates(now=None):
    now = _china_datetime(now)
    # A current weekday is the active market-validation anchor.  Historical
    # local review files are used only when the market is closed, preventing a
    # stale local snapshot from displacing a live Chrome-verified session.
    if now.weekday() < 5:
        anchor = now.date()
    else:
        _review_dir, review_ymd = latest_local_review_dir(now)
        anchor = datetime.strptime(review_ymd, "%Y%m%d").date() if review_ymd else now.date()
    dates = []
    cursor = anchor
    while len(dates) < 3:
        if cursor.weekday() < 5:
            dates.append(cursor)
        cursor -= timedelta(days=1)
    return list(reversed(dates))


def _review_file(review_dir, stem, ymd):
    if not review_dir:
        return Path("__missing__")
    stems = REVIEW_STEM_ALIASES.get(stem, [stem])
    found = _first_review_file(review_dir, stems, ymd)
    return found if found else review_dir / f"{stem}_{ymd}.csv"


@lru_cache(maxsize=1)
def known_stock_names():
    import csv
    review_dir, ymd = latest_local_review_dir()
    names = set()
    for stem in ["ak_stock_zt_pool_em", "ak_stock_lhb_detail_em", "limitup_lhb_intersection", "push2_fund_flow_resolved"]:
        path = _review_file(review_dir, stem, ymd)
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                name = str(row.get("名称", "") or row.get("股票名称", "")).strip()
                if len(name) >= 2 and not any(bad in name for bad in ["主力", "超大单", "榜单", "今日", "昨日"]):
                    names.add(name)
    return names


def collect_local_trade_review_events(now):
    import csv
    events = []
    review_dir, ymd = latest_local_review_dir(now)
    if not review_dir:
        return events
    date_text = cn_date(datetime.strptime(ymd, "%Y%m%d").date())
    industry_path = _review_file(review_dir, "industry_limitup_stats", ymd)
    lhb_path = _review_file(review_dir, "limitup_lhb_intersection", ymd)
    zt_path = _review_file(review_dir, "ak_stock_zt_pool_em", ymd)
    lhb_detail_path = _review_file(review_dir, "ak_stock_lhb_detail_em", ymd)
    fund_path = _review_file(review_dir, "push2_fund_flow_resolved", ymd)
    name_industry = {}
    industry_names = defaultdict(list)
    for map_path in [zt_path, lhb_path]:
        if map_path.exists():
            with map_path.open("r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    name = row.get("名称", "")
                    industry = row.get("所属行业", "") or row.get("行业", "")
                    if name and industry and industry != "未分类":
                        name_industry[name] = industry
                        if name not in industry_names[industry]:
                            industry_names[industry].append(name)
    if industry_path.exists():
        with industry_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in list(csv.DictReader(f))[:28]:
                industry = row.get("行业", "")
                count = row.get("涨停数", "")
                if industry and industry != "未分类" and count:
                    events.append({"source": "交易复盘", "date": date_text, "event": f"{date_text}交易复盘显示，{industry}方向涨停数为{count}家，属于当日资金实际交易反馈。", "url": str(industry_path)})
    if lhb_path.exists():
        with lhb_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in list(csv.DictReader(f))[:55]:
                name = row.get("名称", "")
                industry = row.get("所属行业", "")
                amount = row.get("成交额", "")
                turnover = row.get("换手率", "")
                board = row.get("连板数", "") or row.get("涨停统计", "")
                if name and industry:
                    events.append({"source": "龙虎榜", "date": date_text, "event": f"{name}进入涨停与龙虎榜交集，所属环节为{industry}，成交额{amount}，换手率{turnover}，连板信息{board}，显示短线资金对该环节有真实交易反馈。", "url": str(lhb_path)})
    if lhb_detail_path.exists():
        with lhb_detail_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in list(csv.DictReader(f))[:95]:
                name = row.get("名称", "")
                reason = row.get("上榜原因", "")
                interp = row.get("解读", "")
                net = row.get("龙虎榜净买额", "")
                amount = row.get("龙虎榜成交额", "")
                if name and (reason or interp):
                    src = "机构调研" if "机构" in interp else "短线复盘"
                    industry = name_industry.get(name, "")
                    industry_text = f"所属环节为{industry}，" if industry else ""
                    events.append({"source": src, "date": date_text, "event": f"{name}龙虎榜上榜，{industry_text}原因为{reason}，席位解读为{interp}，净买额{net}，榜单成交额{amount}，反映机构或短线资金对该产业链环节的博弈。", "url": str(lhb_detail_path)})
    if fund_path.exists():
        with fund_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in list(csv.DictReader(f))[:110]:
                name = row.get("名称", "")
                main = row.get("主力净流入", "")
                super_big = row.get("超大单净流入", "")
                pct = row.get("主力净占比", "")
                change = row.get("涨跌幅", "")
                if name and main:
                    industry = name_industry.get(name, "")
                    industry_text = f"所属环节为{industry}，" if industry else ""
                    events.append({"source": "融资数据", "date": date_text, "event": f"{name}资金流显示，{industry_text}主力净流入{main}，超大单净流入{super_big}，主力净占比{pct}，涨跌幅{change}，反映大单资金对该产业链环节的参与强度。", "url": str(fund_path)})
    if zt_path.exists():
        with zt_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in list(csv.DictReader(f))[:80]:
                name = row.get("名称", "")
                industry = row.get("所属行业", "")
                board = row.get("连板数", "") or row.get("涨停统计", "")
                amount = row.get("成交额", "")
                seal = row.get("封板资金", "")
                if name and industry:
                    events.append({"source": "涨停复盘", "date": date_text, "event": f"{name}涨停，所属环节为{industry}，连板信息{board}，成交额{amount}，封板资金{seal}，提供短线热点和产业链映射证据。", "url": str(zt_path)})
    for industry, names in sorted(industry_names.items(), key=lambda item: len(item[1]), reverse=True)[:24]:
        if len(names) < 3:
            continue
        sample = "、".join(names[:8])
        events.append({"source": "短线复盘", "date": date_text, "event": f"短线复盘显示，{industry}方向出现{len(names)}只涨停或龙虎榜反馈标的，代表样本包括{sample}，说明该方向并非单一个股异动，而是有行业样本集中和短线资金辨识度。", "url": str(zt_path)})
    for prev_date in [ymd]:
        breadth_candidates = [review_dir / f"market_breadth_{prev_date}.json"]
        breadth_candidates.extend(sorted(review_dir.glob("market_breadth_*.json"), reverse=True))
        breadth_path = next((path for path in breadth_candidates if path.exists()), None)
        if breadth_path:
            try:
                bdata = json.loads(breadth_path.read_text(encoding="utf-8"))
                if bdata.get("status") in {"BLOCKED", "FAIL", "ERROR"}:
                    raise ValueError("blocked market breadth snapshot")
                nested_rows = bdata.get("evidence") or bdata.get("sources") or []
                nested_events = []
                if isinstance(nested_rows, list):
                    for index, row in enumerate(nested_rows, start=1):
                        if not isinstance(row, dict):
                            continue
                        source = clean_text(str(row.get("source", ""))) or f"指数宽度来源{index}"
                        row_date = clean_text(str(row.get("date", ""))) or date_text
                        event = clean_text(str(row.get("event", "") or row.get("text", "")))
                        up = row.get("up_count", "")
                        down = row.get("down_count", "")
                        turnover = clean_text(str(row.get("turnover", "") or row.get("turnover_amount", "")))
                        if not event and str(up).isdigit() and str(down).isdigit():
                            turnover_text = f"，成交额{turnover}" if turnover else ""
                            event = f"{row_date}两市上涨家数{up}、下跌家数{down}{turnover_text}。"
                        elif not event and str(down).isdigit():
                            event = f"{row_date}两市约{down}只个股下跌。"
                        if not event:
                            continue
                        nested_events.append({
                            "source": source,
                            "source_key": clean_text(str(row.get("source_key", ""))),
                            "date": row_date,
                            "event": event,
                            "url": str(row.get("url", "") or breadth_path),
                        })
                if nested_events:
                    events.extend(nested_events)
                else:
                    up = bdata.get("up_count", "")
                    down = bdata.get("down_count", "")
                    if not str(up).isdigit() or not str(down).isdigit() or int(up) <= 0 or int(down) <= 0:
                        raise ValueError("invalid market breadth counts")
                    ratio = bdata.get("up_ratio", "")
                    label = bdata.get("breadth_label", "")
                    stage = bdata.get("stage", "")
                    sentiment = f"{date_text}指数宽度读数：上涨家数{up}、下跌家数{down}，上涨占比{ratio}，市场宽度标注为{label}，对应市场阶段为{stage}。"
                    events.append({"source": "指数宽度", "date": date_text, "event": sentiment, "url": str(breadth_path)})
                label = bdata.get("breadth_label", "")
                stage = bdata.get("stage", "")
                if label or stage:
                    events.append({"source": "市场情绪", "date": date_text, "event": f"{date_text}市场宽度阶段为{stage}，宽度标签{label}，属于指数层面政策/资金/情绪共振信号，非个股层面反馈。", "url": str(breadth_path)})
            except Exception:
                pass
        truth_path = review_dir / f"final_evidence.json"
        if truth_path.exists():
            try:
                tdata = json.loads(truth_path.read_text(encoding="utf-8"))
                snap = tdata.get("truth_snapshot", {}) or {}
                mainline = snap.get("mainline", "")
                rating = snap.get("mainline_rating", "")
                if mainline:
                    events.append({"source": "主线热点", "date": date_text, "event": f"{date_text}盘后主线判定为{mainline}，主线评级为{rating}，属于板块级产业链主线归类，非个股新闻。", "url": str(truth_path)})
                breadth_snap = snap.get("market_breadth", {}) or {}
                if breadth_snap:
                    events.append({"source": "指数宽度", "date": date_text, "event": f"{date_text}市场宽度快照：上涨{breadth_snap.get('up_count','?')}只，下跌{breadth_snap.get('down_count','?')}只，宽度标签{breadth_snap.get('breadth_label','?')}，对应主线热点 {mainline or '未明'}。", "url": str(truth_path)})
            except Exception:
                pass
        csv_path = review_dir / f"final_limitup_union_strict_{prev_date}.csv"
        if csv_path.exists():
            try:
                industry_counter = Counter()
                with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
                    for row in csv.DictReader(f):
                        ind = row.get("所属行业", "") or row.get("行业", "")
                        if ind and ind != "未分类":
                            industry_counter[ind] += 1
                top = industry_counter.most_common(8)
                if top:
                    top_text = "、".join(f"{ind}({cnt})" for ind, cnt in top)
                    events.append({"source": "交易复盘", "date": date_text, "event": f"{date_text}全量涨停严格集合按行业聚合，前 8 大板块为{top_text}，属于板块级行业聚合证据。", "url": str(csv_path)})
            except Exception:
                pass
    for event in events:
        event["theme_terms"] = derive_theme_terms(event.get("event", ""), topn=6)
    return events


def _load_lianban_snapshot(now=None):
    if os.environ.get(LIANBAN_STATUS_ENV) != "CLEAN_PASS":
        return None
    snapshot_value = os.environ.get(LIANBAN_SNAPSHOT_ENV, "").strip()
    if not snapshot_value:
        return None
    snapshot = read_json_or_none(Path(snapshot_value))
    if not isinstance(snapshot, dict):
        return None
    if (
        snapshot.get("schema") != "LIANBAN_DAILY_SNAPSHOT_V1"
        or snapshot.get("status") != "CLEAN_PASS"
        or snapshot.get("source_role")
        != "supplemental_event_theme_sentiment_cross_validation"
    ):
        return None
    target_date = str(snapshot.get("target_date") or "")
    if target_date not in {day.isoformat() for day in recent_trading_dates(now)}:
        return None
    return snapshot


def _lianban_topic_aliases(topic):
    topic = clean_text(str(topic or ""))
    aliases = [topic]
    if topic.endswith("概念"):
        aliases.append(topic[:-2])
    if topic.endswith("应用"):
        aliases.extend([topic[:-2], "AI" if topic.startswith("AI") else ""])
    if topic == "通信":
        aliases.extend(["通信设备", "光通信"])
    if topic == "芯片":
        aliases.extend(["半导体", "存储芯片"])
    if topic == "地产链":
        aliases.extend(["房地产", "房地产开发", "装修装饰", "物业服务"])
    return [alias for alias in dict.fromkeys(aliases) if alias]


def _lianban_topic_stock_names(snapshot):
    mapping = defaultdict(list)
    for row in (snapshot.get("page_details") or {}).get("stock_items") or []:
        if not isinstance(row, dict):
            continue
        name = clean_text(str(row.get("name") or ""))
        labels = [
            clean_text(str(row.get("board") or "")),
            clean_text(str(row.get("theme") or "")),
        ]
        if not name:
            continue
        for label in labels:
            for topic in _lianban_topic_aliases(label):
                if name not in mapping[topic]:
                    mapping[topic].append(name)
    return mapping


def collect_lianban_market_validation_events(now=None, local_events=None):
    now = _china_datetime(now)
    snapshot = _load_lianban_snapshot(now)
    if not snapshot:
        return []
    local_events = list(local_events or [])
    target_date = datetime.fromisoformat(str(snapshot["target_date"])).date()
    date_text = cn_date(target_date)
    page_url = str(
        (snapshot.get("sources") or {}).get("page", {}).get("url") or ""
    )
    stock_map = _lianban_topic_stock_names(snapshot)
    market = snapshot.get("market") or {}
    summary_parts = []
    if market.get("limit_up") not in (None, ""):
        summary_parts.append(f"涨停{market.get('limit_up')}家")
    if market.get("consecutive") not in (None, ""):
        summary_parts.append(f"连板晋级样本{market.get('consecutive')}家")
    if market.get("max_board") not in (None, ""):
        summary_parts.append(f"最高{market.get('max_board')}板")
    if market.get("emotion_stage"):
        summary_parts.append(f"情绪阶段{clean_text(str(market.get('emotion_stage')))}")
    events = [{
        "source": "连板网·市场复盘",
        "date": date_text,
        "market_date": date_text,
        "published_at": now.isoformat(timespec="seconds"),
        "time_precision": "market_close",
        "time_evidence": str(snapshot["target_date"]),
        "window_type": MARKET_VALIDATION_WINDOW_TYPE,
        "event": (
            f"{date_text}连板网复盘："
            + "、".join(summary_parts)
            + "；热点与板块结构以当日主题统计和逐股涨停原因核对。"
        ),
        "url": page_url,
        "source_channel": "lianban_daily_market_cross_validation",
        "validation_dimensions": ["热点", "板块", "涨停", "晋级"],
        "attribution": "连板网",
    }]
    topic_counts = {}
    for row in snapshot.get("topics") or []:
        if not isinstance(row, dict):
            continue
        raw_topic = clean_text(str(row.get("name") or ""))
        try:
            count = int(row.get("count") or 0)
        except (TypeError, ValueError):
            count = 0
        if not raw_topic or count < MIN_DIRECTION_STOCKS:
            continue
        topic_counts[raw_topic] = count
        aliases = _lianban_topic_aliases(raw_topic)
        for topic in aliases:
            names = list(dict.fromkeys(
                name
                for alias in aliases
                for name in stock_map.get(alias, [])
            ))
            if len(names) < MIN_DIRECTION_STOCKS:
                continue
            sample = "、".join(names[:8])
            events.append({
                "source": "连板网·市场复盘",
                "date": date_text,
                "market_date": date_text,
                "published_at": now.isoformat(timespec="seconds"),
                "time_precision": "market_close",
                "time_evidence": str(snapshot["target_date"]),
                "window_type": MARKET_VALIDATION_WINDOW_TYPE,
                "event": (
                    f"{date_text}交易复盘显示，所属概念为{topic}，"
                    f"该方向共有{count}只涨停，"
                    f"代表标的包括{sample}，说明该方向出现板块级涨停扩散。"
                ),
                "url": page_url,
                "source_channel": "lianban_daily_market_cross_validation",
                "theme_terms": [topic],
                "validation_dimensions": ["热点", "板块", "涨停"],
                "attribution": "连板网",
            })

            participant_items = [
                item
                for item in local_events
                if source_layer(item.get("source", "")) == "机构渠道"
                and any(
                    name in clean_text(item.get("event", ""))
                    for name in names
                )
                and any(
                    word in item.get("event", "")
                    for word in CAUSAL_PARTICIPANT_WORDS
                )
            ]
            participant_names = sorted({
                name
                for item in participant_items
                for name in names
                if name in clean_text(item.get("event", ""))
            })
            if not participant_items or not participant_names:
                continue
            participant_facts = [
                clean_text(item.get("event", "")).strip("。")
                for item in participant_items[:6]
                if clean_text(item.get("event", ""))
            ]
            events.append({
                "source": "融资数据",
                "date": date_text,
                "market_date": date_text,
                "published_at": now.isoformat(timespec="seconds"),
                "time_precision": "market_close",
                "time_evidence": str(snapshot["target_date"]),
                "window_type": MARKET_VALIDATION_WINDOW_TYPE,
                "event": (
                    f"所属概念为{topic}，该方向参与者确认：代表标的"
                    f"{'、'.join(participant_names[:8])}出现机构、融资或主力资金记录。"
                    + " ".join(participant_facts)
                )[:900],
                "url": str(participant_items[0].get("url", "")),
                "source_channel": "local_participant_topic_aggregation",
                "theme_terms": [topic],
                "supporting_event_ids": [
                    _event_identity(item) for item in participant_items[:6]
                ],
            })
    globals()["lianban_market_validation_profile"] = {
        "status": "PASS",
        "snapshot": os.environ.get(LIANBAN_SNAPSHOT_ENV, ""),
        "target_date": str(snapshot.get("target_date", "")),
        "topic_counts": topic_counts,
        "generated_event_count": len(events),
    }
    return events


def _read_tdx_block_symbols(stem):
    path = TDX_BLOCK_ROOT / f"{stem}.blk"
    if not path.is_file() or path.stat().st_size <= 0:
        return path, []
    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    symbols = [
        line.strip() for line in text.replace("\r", "\n").splitlines()
        if line.strip()
    ]
    return path, symbols


def _tdx_common_a_share_code(path):
    match = re.fullmatch(r"(sh|sz|bj)(\d{6})\.day", path.name.casefold())
    if not match:
        return None
    market, code = match.groups()
    if market == "sh" and code.startswith(("600", "601", "603", "605", "688")):
        return market, code
    if market == "sz" and code.startswith(("000", "001", "002", "003", "300", "301")):
        return market, code
    if market == "bj" and code.startswith("920"):
        return market, code
    return None


def _tdx_limit_up_price(close_value, rate_percent):
    return (int(close_value) * (100 + int(rate_percent)) + 50) // 100


def _tdx_row_is_limit_up(current, previous, rate_percent):
    if not current or not previous:
        return False
    expected = _tdx_limit_up_price(previous[4], rate_percent)
    return current[4] == expected and current[2] >= expected and current[5] > 0


def _tdx_excluded_common_a_share_codes():
    excluded = set()
    source_files = []
    for market, filename in (("sh", "shs.tnf"), ("sz", "szs.tnf")):
        path = TDX_ROOT / "T0002" / "hq_cache" / filename
        if not path.is_file() or path.stat().st_size < 50 + 360:
            continue
        source_files.append(path)
        data = path.read_bytes()
        for offset in range(50, len(data) - 360 + 1, 360):
            record = data[offset : offset + 360]
            code = record[:6].split(b"\x00", 1)[0].decode(
                "ascii", errors="ignore"
            )
            name = record[31:49].split(b"\x00", 1)[0].decode(
                "gbk", errors="ignore"
            ).strip()
            if (
                len(code) == 6
                and code.isdigit()
                and re.search(r"(?:\*?ST|退市|^N|^C)", name, re.I)
            ):
                excluded.add(f"{market}{code}")
    return excluded, source_files


def _latest_tdx_turnover(target_date=None):
    target_int = int(target_date.strftime("%Y%m%d")) if target_date else None
    roots = [
        TDX_ROOT / "vipdoc" / market / "lday"
        for market in ("sh", "sz", "bj")
    ] + [
        TDX_ROOT / "vipdoc" / "xinzeng" / market / "lday"
        for market in ("sh", "sz", "bj")
    ]
    excluded_codes, security_name_files = _tdx_excluded_common_a_share_codes()
    security_name_hashes = {
        str(path): file_sha256(path) for path in security_name_files
    }
    amounts = defaultdict(float)
    matched = defaultdict(int)
    limit_up_counts = defaultdict(int)
    two_day_limit_up_counts = defaultdict(int)
    advancer_counts = defaultdict(int)
    decliner_counts = defaultdict(int)
    flat_counts = defaultdict(int)
    limit_up_samples = defaultdict(list)
    two_day_limit_up_samples = defaultdict(list)
    snapshot_fingerprints = defaultdict(list)
    source_dirs = defaultdict(set)
    seen_names = set()
    newest_mtimes = defaultdict(float)
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.glob("*.day"):
            code_info = _tdx_common_a_share_code(path)
            if (
                code_info is None
                or path.name in seen_names
                or path.stat().st_size < TDX_DAY_RECORD.size * 2
            ):
                continue
            seen_names.add(path.name)
            try:
                record_count = min(3, path.stat().st_size // TDX_DAY_RECORD.size)
                with path.open("rb") as handle:
                    handle.seek(-TDX_DAY_RECORD.size * record_count, os.SEEK_END)
                    raw = handle.read(TDX_DAY_RECORD.size * record_count)
                rows = [
                    TDX_DAY_RECORD.unpack(
                        raw[offset : offset + TDX_DAY_RECORD.size]
                    )
                    for offset in range(0, len(raw), TDX_DAY_RECORD.size)
                ]
                current = rows[-1]
                date_value = current[0]
                row_amount = current[5]
            except Exception:
                continue
            if (
                (target_int is not None and date_value != target_int)
                or not isinstance(row_amount, float)
                or row_amount <= 0
            ):
                continue
            amounts[date_value] += float(row_amount)
            matched[date_value] += 1
            market, code = code_info
            previous = rows[-2] if len(rows) >= 2 else None
            if previous and int(previous[4]) > 0 and int(current[4]) > 0:
                if int(current[4]) > int(previous[4]):
                    advancer_counts[date_value] += 1
                elif int(current[4]) < int(previous[4]):
                    decliner_counts[date_value] += 1
                else:
                    flat_counts[date_value] += 1
            excluded_from_limit_pool = f"{market}{code}" in excluded_codes
            if market == "bj":
                rate_percent = 30
            elif code.startswith(("300", "301", "688")):
                rate_percent = 20
            else:
                rate_percent = 10
            is_limit_up = bool(
                not excluded_from_limit_pool
                and _tdx_row_is_limit_up(
                    current,
                    rows[-2] if len(rows) >= 2 else None,
                    rate_percent,
                )
            )
            is_two_day_limit_up = bool(
                is_limit_up
                and len(rows) >= 3
                and _tdx_row_is_limit_up(rows[-2], rows[-3], rate_percent)
            )
            if is_limit_up:
                limit_up_counts[date_value] += 1
                if len(limit_up_samples[date_value]) < 20:
                    limit_up_samples[date_value].append(f"{code}.{market.upper()}")
            if is_two_day_limit_up:
                two_day_limit_up_counts[date_value] += 1
                if len(two_day_limit_up_samples[date_value]) < 20:
                    two_day_limit_up_samples[date_value].append(
                        f"{code}.{market.upper()}"
                    )
            snapshot_fingerprints[date_value].append(
                f"{path.name}|{current[0]}|{current[4]}|{float(current[5]):.6f}"
            )
            source_dirs[date_value].add(str(root))
            newest_mtimes[date_value] = max(
                newest_mtimes[date_value],
                path.stat().st_mtime,
            )
    selected_date = target_int
    if selected_date is None and matched:
        selected_date = max(matched)
    amount = amounts[selected_date] if selected_date is not None else 0.0
    stock_count = matched[selected_date] if selected_date is not None else 0
    fingerprints = (
        sorted(snapshot_fingerprints[selected_date])
        if selected_date is not None
        else []
    )
    fingerprints.extend(
        f"name_file|{path}|{digest}"
        for path, digest in sorted(security_name_hashes.items())
    )
    return {
        "target_date": str(selected_date or ""),
        "amount_yuan": amount,
        "amount_yi": round(amount / 100_000_000, 2) if amount else 0,
        "stock_count": stock_count,
        "advancer_count": (
            advancer_counts[selected_date] if selected_date is not None else 0
        ),
        "decliner_count": (
            decliner_counts[selected_date] if selected_date is not None else 0
        ),
        "flat_count": flat_counts[selected_date] if selected_date is not None else 0,
        "newest_mtime": newest_mtimes[selected_date] if selected_date is not None else 0.0,
        "limit_up_count": (
            limit_up_counts[selected_date] if selected_date is not None else 0
        ),
        "two_day_limit_up_count": (
            two_day_limit_up_counts[selected_date]
            if selected_date is not None
            else 0
        ),
        "limit_up_sample": (
            limit_up_samples[selected_date] if selected_date is not None else []
        ),
        "two_day_limit_up_sample": (
            two_day_limit_up_samples[selected_date]
            if selected_date is not None
            else []
        ),
        "source_mode": "tdx_lday_market_rebuild",
        "source_files": (
            sorted(source_dirs[selected_date])
            + [str(path) for path in security_name_files]
            if selected_date is not None
            else []
        ),
        "excluded_security_name_count": len(excluded_codes),
        "security_name_file_sha256": security_name_hashes,
        "source_snapshot_sha256": (
            hashlib.sha256("\n".join(fingerprints).encode("utf-8")).hexdigest()
            if fingerprints
            else ""
        ),
    }


def collect_tdx_market_validation_events(now=None):
    now = _china_datetime(now)
    ztc_path, ztc_symbols = _read_tdx_block_symbols("ZTC")
    elb_path, elb_symbols = _read_tdx_block_symbols("ELB")
    turnover = _latest_tdx_turnover()
    target_ymd = str(turnover.get("target_date") or "")
    if len(target_ymd) != 8 or not target_ymd.isdigit():
        return []
    target_date = datetime.strptime(target_ymd, "%Y%m%d").date()
    trading_dates = recent_trading_dates(now)
    completed_dates = [
        value
        for value in trading_dates
        if value < now.date()
        or (value == now.date() and now.hour >= 16)
    ]
    if not completed_dates or target_date != completed_dates[-1]:
        return []
    date_text = cn_date(target_date)
    block_mtimes = [
        datetime.fromtimestamp(path.stat().st_mtime, CHINA_TZ)
        for path in (ztc_path, elb_path)
        if path.is_file()
    ]
    target_close = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        15,
        0,
        tzinfo=CHINA_TZ,
    )
    fresh_block_files = not (
        len(block_mtimes) != 2
        or any(
            value < target_close or value > now + timedelta(minutes=5)
            for value in block_mtimes
        )
        or not ztc_symbols
        or not elb_symbols
    )
    rebuilt_latest_day = bool(
        turnover.get("source_mode") == "tdx_lday_market_rebuild"
        and int(turnover.get("limit_up_count") or 0) > 0
        and int(turnover.get("two_day_limit_up_count") or 0) >= 0
        and (
            turnover.get("source_snapshot_sha256")
            or turnover.get("source_files")
        )
    )
    if not fresh_block_files and not rebuilt_latest_day:
        return []
    if turnover["stock_count"] < 3000 or turnover["amount_yi"] <= 0:
        return []
    if fresh_block_files:
        pool_mode = "tdx_fresh_block_files"
        limit_up_count = len(ztc_symbols)
        two_day_limit_up_count = len(elb_symbols)
        event_text = (
            f"{date_text}通达信本地数据：涨停池ZTC共{limit_up_count}只，"
            f"二连板池ELB共{two_day_limit_up_count}只，"
            f"本地日线{turnover['stock_count']}只普通A股成交额合计约"
            f"{turnover['amount_yi']}亿元；全市场约"
            f"{turnover['decliner_count']}只个股下跌（有效样本"
            f"{turnover['advancer_count'] + turnover['decliner_count'] + turnover['flat_count']}只）。"
        )
        source_files = [str(ztc_path), str(elb_path)]
        source_file_sha256 = {
            "ZTC": file_sha256(ztc_path),
            "ELB": file_sha256(elb_path),
        }
        source_file_mtimes = {
            "ZTC": block_mtimes[0].isoformat(timespec="seconds"),
            "ELB": block_mtimes[1].isoformat(timespec="seconds"),
        }
        tdx_mapping = {"ZTC": "涨停池", "ELB": "二连板"}
    else:
        pool_mode = "tdx_lday_market_rebuild"
        limit_up_count = int(turnover["limit_up_count"])
        two_day_limit_up_count = int(turnover["two_day_limit_up_count"])
        event_text = (
            f"{date_text}通达信本地日线普通A股全量复算"
            f"{turnover['stock_count']}只：涨停{limit_up_count}只，"
            f"连续两日涨停{two_day_limit_up_count}只，成交额合计约"
            f"{turnover['amount_yi']}亿元；全市场约"
            f"{turnover['decliner_count']}只个股下跌（有效样本"
            f"{turnover['advancer_count'] + turnover['decliner_count'] + turnover['flat_count']}只）。"
        )
        source_files = list(turnover.get("source_files") or [])
        source_file_sha256 = {
            "tdx_lday_snapshot": str(turnover.get("source_snapshot_sha256") or "")
        }
        source_file_mtimes = {
            "tdx_lday_newest": datetime.fromtimestamp(
                float(turnover.get("newest_mtime") or 0), CHINA_TZ
            ).isoformat(timespec="seconds")
        }
        tdx_mapping = {
            "latest_day_limit_up": "涨停池",
            "two_day_limit_up": "二连板晋级",
        }
    event = {
        "source": "通达信·市场复盘",
        "source_key": "local-tdx",
        "date": date_text,
        "market_date": date_text,
        "published_at": now.isoformat(timespec="seconds"),
        "time_precision": "market_close",
        "time_evidence": target_date.isoformat(),
        "window_type": MARKET_VALIDATION_WINDOW_TYPE,
        "event": event_text,
        "url": source_files[0] if source_files else str(TDX_ROOT),
        "source_channel": "tdx_local_market_cross_validation",
        "validation_dimensions": ["涨停", "晋级", "成交额", "市场宽度"],
        "source_files": source_files,
        "source_file_sha256": source_file_sha256,
        "source_file_mtimes": source_file_mtimes,
        "tdx_mapping": tdx_mapping,
        "tdx_pool_mode": pool_mode,
        "turnover": turnover,
    }
    globals()["tdx_market_validation_profile"] = {
        "status": "PASS",
        "target_date": target_date.isoformat(),
        "ztc_count": limit_up_count,
        "elb_count": two_day_limit_up_count,
        "tdx_pool_mode": pool_mode,
        "turnover": turnover,
        "files": source_files,
        "source_file_mtimes": source_file_mtimes,
    }
    return [event]


def _load_duanxianxia_snapshot(now=None):
    value = os.environ.get(DUANXIANXIA_SNAPSHOT_ENV, "").strip()
    if not value:
        return None
    path = Path(value)
    snapshot = read_json_or_none(path)
    if not isinstance(snapshot, dict):
        return None
    generated = _parse_iso_datetime(snapshot.get("generated_at"))
    if not generated:
        return None
    now = _china_datetime(now)
    if abs((now - generated).total_seconds()) > 3600:
        return None
    required = {"hotlist", "jinjidata", "ztlive", "ztplate", "ztcount", "ztpool", "amount"}
    datasets = snapshot.get("datasets") or {}
    if any(
        not isinstance(datasets.get(name), dict)
        or datasets[name].get("success") is not True
        for name in required
    ):
        return None
    return snapshot


def collect_duanxianxia_market_validation_events(now=None):
    now = _china_datetime(now)
    snapshot = _load_duanxianxia_snapshot(now)
    if not snapshot:
        return []
    datasets = snapshot.get("datasets") or {}
    hotlist = ((datasets.get("hotlist") or {}).get("data") or {}).get("stock_topic") or []
    plates = ((datasets.get("ztplate") or {}).get("data") or {}).get("list") or []
    live = ((datasets.get("ztlive") or {}).get("data") or {}).get("list") or []
    pool = ((datasets.get("ztpool") or {}).get("data") or {}).get("list") or []
    count_value = (((datasets.get("ztcount") or {}).get("data") or {}).get("count"))
    promotion_html = str(((datasets.get("jinjidata") or {}).get("data") or {}).get("html") or "")
    amount_last = (((datasets.get("amount") or {}).get("data") or {}).get("last") or {})
    amount_value = ""
    if isinstance(amount_last, dict):
        numeric = [
            (str(key), value) for key, value in amount_last.items()
            if str(key).isdigit() and str(value).replace(".", "", 1).isdigit()
        ]
        if numeric:
            amount_value = sorted(numeric, key=lambda row: int(row[0]))[-1][1]
    topics = [
        clean_text(str(item.get("title") or ""))
        for item in hotlist[:10]
        if isinstance(item, dict) and clean_text(str(item.get("title") or ""))
    ]
    plate_names = [
        clean_text(str(item.get("plate") or ""))
        for item in plates[:20]
        if isinstance(item, dict) and clean_text(str(item.get("plate") or ""))
    ]
    promotion_rows = len(re.findall(r"\d+进\d+", promotion_html))
    target_date = recent_trading_dates(now)[-1]
    date_text = cn_date(target_date)
    event = {
        "source": "短线侠·市场复盘",
        "date": date_text,
        "market_date": date_text,
        "published_at": now.isoformat(timespec="seconds"),
        "time_precision": "market_close",
        "time_evidence": target_date.isoformat(),
        "window_type": MARKET_VALIDATION_WINDOW_TYPE,
        "event": (
            f"{date_text}短线侠公开数据：热点前列包括{'、'.join(topics[:5]) or '无'}；"
            f"涨停板块包括{'、'.join(dict.fromkeys(plate_names[:8])) or '无'}；"
            f"涨停计数{count_value or len(live) or len(pool)}，"
            f"晋级梯队记录{promotion_rows}档，"
            f"两市成交额最后读数{amount_value or '缺失'}亿元。"
        ),
        "url": str(snapshot.get("source_page") or "https://duanxianxia.com/web/main"),
        "source_channel": "duanxianxia_market_cross_validation",
        "validation_dimensions": ["热点", "板块", "涨停", "晋级", "成交额"],
        "snapshot_path": os.environ.get(DUANXIANXIA_SNAPSHOT_ENV, ""),
        "snapshot_sha256": file_sha256(Path(os.environ[DUANXIANXIA_SNAPSHOT_ENV])),
        "dataset_counts": {
            "hotlist": len(hotlist),
            "ztplate": len(plates),
            "ztlive": len(live),
            "ztpool": len(pool),
            "promotion_rows": promotion_rows,
        },
    }
    globals()["duanxianxia_market_validation_profile"] = {
        "status": "PASS",
        "snapshot": os.environ.get(DUANXIANXIA_SNAPSHOT_ENV, ""),
        "dataset_counts": event["dataset_counts"],
        "amount": amount_value,
    }
    return [event]


EXTRA_LABEL_STOPS = {
    "龙虎榜", "涨停", "复盘", "主力", "资金", "净流入", "成交额", "换手率", "连板", "上榜", "今日", "今天", "昨日", "昨天",
    "方向", "显示", "所属", "环节", "交易", "反馈", "产业链", "市场", "事件", "公司", "个股",
    "成功率", "价格涨跌幅", "涨跌幅限", "原因为有", "所属环节为", "封板资金", "榜单成交额",
    "价格", "振幅", "限制", "日收盘", "前五只证券", "证券", "收盘", "涨幅", "偏离值",
    "短线", "信息", "交集", "真实", "达到", "反映", "原因", "席位", "资讯", "标题", "作者",
    "最后更新", "股吧", "点赞", "郑重声明", "声明", "阅读", "评论", "浏览", "积分", "用户",
    "打赏", "回复", "转发", "关注", "分享", "收藏",
    "20%", "15%", "10%", "5%", "ST",
    "当日", "属于", "实际", "数为", "提供", "证据", "映射", "进入", "虎榜交集", "有真实交易反馈",
    "显示短线资金对该环节", "反映大单资金对该产业", "链环节的参与强度", "解读", "博弈",
    "反映机构或短线资金对", "该产业链环节的博弈", "买入", "卖出", "五只", "普通", "大单", "超大",
    "资金流", "封板", "财富网", "举报", "帖子", "返回", "东方财富网股吧",
    "7月6日交易复盘显示", "属于当日资金实际交易", "连板信息1", "连板信息2", "连板信息3",
    "涨跌幅", "提供短线热点和", "连续", "偏离", "收盘价格", "的前5只证券", "到7", "跌幅",
    "IT", "股友", "音频", "梭哈", "大笑", "明天", "今夜", "暂未", "收获", "股票交易", "一主买",
    "强度", "参与", "三个", "交易日", "累计", "主力净占比", "来自", "个人观点", "追加", "网站",
    "涨幅达", "跌幅达", "涨幅偏", "跌幅偏",
    "制品", "财富", "社区", "映射证据", "零部", "榜交集", "一主卖", "一主买", "内容", "本金",
    "东方财富", "自动化", "发表", "所有", "转发",
    "包括", "限于", "文字",
}
BAD_LABEL_SUBSTRINGS = ["所属环节", "原因为", "成功率", "涨跌幅限", "价格振幅", "净买额", "净流入", "榜单", "席位解读", "前五只证券", "郑重声明", "真实交易反馈", "反映机构", "映机构", "反映大单", "制的日收盘", "主力净占比"]


def clean_theme_term(term):
    term = normalize_label_word(term)
    term = term.replace("汽车零部", "汽车零部件").replace("自动化设", "自动化设备").replace("房地产开", "房地产开发")
    term = term.replace("汽车零部件件", "汽车零部件").replace("自动化设备备", "自动化设备")
    term = term.replace("房地产开发发", "房地产开发")
    term = re.sub(r"(板块|概念|方向|赛道|产业链|环节)$", "", term)
    term = term.replace("Ⅱ", "").replace("Ⅰ", "")
    if len(term) < 2 or len(term) > 10:
        return ""
    if term in EXTRA_LABEL_STOPS or term in STOP_WORDS or term in BAD_LABEL_WORDS or term in GENERIC_LABEL_WORDS:
        return ""
    if any(bad in term for bad in BAD_LABEL_SUBSTRINGS):
        return ""
    if "%" in term or re.search(r"\d", term) or re.fullmatch(r"\d+(\.\d+)?", term):
        return ""
    stock_names = known_stock_names()
    if term in stock_names or any(
        name in term
        for name in stock_names
        if len(name) >= 3 and len(term) > len(name)
    ):
        return ""
    return term


def derive_theme_terms(text, topn=8):
    terms = []
    patterns = [
        r"所属环节为([^，。；;]+)",
        r"([\u4e00-\u9fa5A-Za-z0-9]{2,10})方向涨停数",
        r"([\u4e00-\u9fa5A-Za-z0-9]{2,10})(?:板块|概念|赛道|产业链)",
        r"([\u4e00-\u9fa5A-Za-z0-9]{2,10})(?:需求|订单|涨价|景气|供应链)",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text):
            term = clean_theme_term(match)
            if term and term not in terms:
                terms.append(term)
    for term in candidate_terms_from_text(text, topn=topn * 2):
        term = clean_theme_term(term)
        if term and term not in terms:
            terms.append(term)
        if len(terms) >= topn:
            break
    return terms[:topn]


def candidate_terms_from_text(text, topn=40):
    terms = []
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)
            import jieba
            import jieba.analyse
        jieba.setLogLevel(20)
        terms.extend(jieba.analyse.extract_tags(text, topK=topn * 2, withWeight=False))
        terms.extend(jieba.lcut(text))
    except Exception:
        pass
    terms.extend(re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]{2,10}", text))
    counts = Counter()
    stock_names = known_stock_names()
    for raw in terms:
        word = normalize_label_word(raw)
        if len(word) < 2 or len(word) > 10:
            continue
        if word in STOP_WORDS or word in BAD_LABEL_WORDS or word in GENERIC_LABEL_WORDS or word in EXTRA_LABEL_STOPS:
            continue
        if any(bad in word for bad in BAD_LABEL_SUBSTRINGS):
            continue
        if word in stock_names or any((word in name or name in word) for name in stock_names if len(name) >= 3 and len(word) >= 2):
            continue
        if re.fullmatch(r"\d+(\.\d+)?%?", word) or "%" in word:
            continue
        if any(term in word for term in FORBIDDEN_TERMS):
            continue
        counts[word] += 1
    return [w for w, _ in counts.most_common(topn)]


def _is_specific_label_token(token):
    """A token is acceptable for cluster label only if it is a real industry/board word.
    2026-07-08: reject jieba TF-IDF noise like '样本 / 辨识 / 扩散 / 辨识成功率'.
    Strict match: token MUST equal a SPECIFIC_LABEL_HINTS entry, OR a DOMAIN_PHRASE
    must equal / contain / be contained by token. We do NOT use substring scan over
    SPECIFIC_LABEL_HINTS because that lets single-char hints leak into noise tokens
    (e.g. '功率' inside '辨识成功率').
    """
    if not token or len(token) < 2 or len(token) > 10:
        return False
    if token in SPECIFIC_LABEL_HINTS:
        return True
    for phrase in DOMAIN_PHRASES:
        if token == phrase or phrase in token or token in phrase:
            return True
    return False


def _clean_label_fallback(items, topn=4):
    """Pick tokens from text that are real SPECIFIC_LABEL_HINTS / DOMAIN_PHRASES.
    Used when jieba candidates get filtered out, to avoid noise like '样本/辨识/扩散'.
    """
    text = clean_text(" ".join(x["event"] for x in items))
    chosen = []
    for phrase in DOMAIN_PHRASES:
        if phrase in text:
            chosen.append(phrase)
        if len(chosen) >= topn:
            return " / ".join(chosen[:topn])
    tokens = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]{2,10}", text)
    for token in tokens:
        # 2026-07-08 evening: drop tokens containing any BAD_LABEL_SUBSTRINGS fragment
        # (e.g. `所属环节为通信设备`) so the final cluster label never carries scan-docx noise.
        # Also drop sentence-fragment tokens like `钟K线看半导体和通信`.
        is_label_like = (
            not re.search(r"[A-Za-z]", token)
            and not any(con in token for con in [
                "看", "和", "与", "的", "至", "被", "让", "到", "时", "把", "啊", "说",
                "就", "才", "却", "因", "为", "以", "及", "或", "但", "而", "从", "向",
                "于", "按", "使", "要", "可", "将", "应", "也", "还", "用", "对", "系",
                "在", "里", "上", "下", "出", "这", "那", "么", "们", "者", "事",
                "有", "无", "会", "成", "为", "件", "块", "种", "属", "议", "热", "期",
                "近", "度", "流", "续", "始", "国", "率", "表", "幅",
            ])
            and len(token) <= 8
        )
        if _is_specific_label_token(token) and token not in chosen and not any(bad in token for bad in BAD_LABEL_SUBSTRINGS) and is_label_like:
            chosen.append(token)
        if len(chosen) >= topn:
            break
    if chosen:
        return " / ".join(chosen[:topn])
    return "方向级事实主线"


def keyword_label(items, topn=4):
    text = clean_text(" ".join(x["event"] for x in items))
    theme_counter = Counter()
    for item in items:
        for term in item.get("theme_terms") or derive_theme_terms(item.get("event", ""), topn=4):
            term = clean_theme_term(term)
            if term:
                theme_counter[term] += 3
    selected = []
    # 2026-07-08: do NOT early-return on theme_counter hits before noise filter.
    # Some theme_counter tokens are jieba TF-IDF noise like '辨识 / 样本 / 扩散'.
    for term, _count in theme_counter.most_common(topn * 8):
        if term not in selected:
            selected.append(term)
    terms = candidate_terms_from_text(text, topn=topn * 8)
    if len(terms) < topn:
        fallback = [w for w in re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]{2,8}", text) if w not in STOP_WORDS and w not in EXTRA_LABEL_STOPS]
        terms.extend(fallback)
    for term in terms:
        term = clean_theme_term(term)
        if term and term not in selected:
            selected.append(term)
    # 2026-07-08 filter: drop jieba TF-IDF noise tokens like '样本/辨识/扩散'.
    # ALSO require token to actually appear in cluster text (grounding check) so that
    # tokens like '电源/零部件' (which jieba extracted but are absent from items) get rejected.
    filtered = [t for t in selected if _is_specific_label_token(t) and (t in text or any(t in ev.get("event", "") for ev in items))]
    # 2026-07-08 evening: `_is_specific_label_token` accepts `所属环节为通信设备` because
    # `通信设备 ∈ DOMAIN_PHRASES` and `phrase in token` (substring) is True. Strip tokens
    # that contain any BAD_LABEL_SUBSTRINGS fragment (e.g. `所属环节`, `原因为`, `成功率`).
    # This prevents `所属环节为...` from leaking into cluster["keywords"] and the rendered DOCX,
    # which scan-docx explicitly rejects via delivery_noise_terms.
    filtered = [t for t in filtered if not any(bad in t for bad in BAD_LABEL_SUBSTRINGS)]
    # 2026-07-08 evening v2: also drop sentence-fragment tokens like `钟K线看半导体和通信`
    # that mix Chinese + ASCII and survive `_is_specific_label_token` only because a
    # DOMAIN_PHRASE substring like `通信设备` matches. Real industry labels are <=6 chars;
    # anything longer with Latin-letter content or a connector word is treated as noise.
    def _is_short_label_like(t):
        if re.search(r"[A-Za-z]", t):
            return False
        if any(con in t for con in [
            "看", "和", "与", "的", "至", "被", "让", "到", "时", "把", "啊", "说",
            "就", "才", "却", "因", "为", "以", "及", "或", "但", "而", "从", "向",
            "于", "按", "使", "要", "可", "将", "应", "都", "也", "还", "用", "对", "系",
            "在", "里", "上", "下", "出", "这", "那", "么", "们", "里", "者", "事",
            "有", "无", "会", "成", "为", "件", "块", "种", "属", "议", "热", "期",
            "近", "度", "流", "续", "始", "续", "国", "率", "表", "幅",
        ]):
            return False
        if len(t) > 8:
            return False
        return True
    filtered = [t for t in filtered if _is_short_label_like(t)]
    if not filtered:
        return _clean_label_fallback(items, topn=topn)
    if len(filtered) < topn:
        extra = _clean_label_fallback(items, topn=topn).split(" / ")
        for t in extra:
            if t and t not in filtered and _is_specific_label_token(t) and (t in text or any(t in ev.get("event", "") for ev in items)) and not any(bad in t for bad in BAD_LABEL_SUBSTRINGS):
                filtered.append(t)
            if len(filtered) >= topn:
                break
    if not filtered:
        return "方向级事实主线"
    return " / ".join(filtered[:topn])


def label_is_clean(label):
    if any(bad in label for bad in BAD_LABEL_SUBSTRINGS):
        return False
    tokens = [x.strip() for x in label.split("/")]
    meaningful = 0
    generic = 0
    specific = 0
    for token in tokens:
        if not token:
            continue
        if token in BAD_LABEL_WORDS or token in EXTRA_LABEL_STOPS:
            return False
        if token in GENERIC_LABEL_WORDS:
            generic += 1
            continue
        if any(bad in token for bad in BAD_LABEL_WORDS) or any(term in token for term in FORBIDDEN_TERMS):
            return False
        if re.search(r"20\d{2}|^\d+日$|^\d+月$|^\d+年$|^\d+月\d+日$", token):
            return False
        if re.search(r"[-_.…]{2,}", token) or token in {"--", "...", "——"}:
            return False
        if token in SPECIFIC_LABEL_HINTS or any(hint in token for hint in SPECIFIC_LABEL_HINTS):
            specific += 1
        meaningful += 1
    if meaningful < 1 or specific < 1:
        return False
    # 2026-07-08 hard gate: every token must be a real industry word. Reject jieba TF-IDF noise like '样本/辨识/扩散'.
    for token in tokens:
        if token and not _is_specific_label_token(token):
            return False
    return meaningful > generic


def amount_to_cn(value):
    try:
        num = float(str(value).replace(",", ""))
    except Exception:
        return str(value)
    sign = "-" if num < 0 else ""
    num = abs(num)
    if num >= 100000000:
        return f"{sign}{num / 100000000:.2f}亿元"
    if num >= 10000:
        return f"{sign}{num / 10000:.0f}万元"
    return f"{sign}{num:.0f}元"


def short_reason(text):
    text = re.sub(r"有价格涨跌幅限制的日收盘价格涨幅达到15%的前五只证券", "日内大涨异动", text)
    text = re.sub(r"有价格涨跌幅限制的日收盘价格涨幅偏离值达到7%的前五只证券", "涨幅偏离异动", text)
    text = re.sub(r"有价格涨跌幅限制的日收盘价格跌幅偏离值达到7%的前五只证券", "跌幅偏离异动", text)
    text = re.sub(r"非ST、\*ST和S证券连续三个交易日内收盘价格涨幅偏离值累计达到20%", "连续涨幅异动", text)
    text = re.sub(r"日涨幅达到15%的前5只证券", "日内大涨异动", text)
    text = re.sub(r"日振幅值达到15%的前5只证券", "日内振幅异动", text)
    text = text.replace("自动化设", "自动化设备")
    return text


def normalize_delivery_label(value):
    value = clean_text(value)
    exact = {
        "自动化设": "自动化设备",
        "汽车零部": "汽车零部件",
        "房地产开": "房地产开发",
    }
    if value in exact:
        return exact[value]
    return (
        value
        .replace("自动化设备备", "自动化设备")
        .replace("汽车零部件件", "汽车零部件")
        .replace("房地产开发发", "房地产开发")
    )


def delivery_event_text(item):
    text = sanitize_delivery_residue(item.get("event", ""))
    text = text.replace("自动化设", "自动化设备").replace("自动化设备备", "自动化设备")
    source = item.get("source", "")
    if "进入涨停与龙虎榜交集" in text:
        name = re.match(r"(.+?)进入涨停", text)
        industry = re.search(r"所属(?:环节|行业)为([^，]+)", text)
        turnover = re.search(r"换手率([-\d.]+)", text)
        board = re.search(r"连板信息([^，]+)", text)
        parts = [f"{name.group(1)}涨停并进入龙虎榜" if name else "个股涨停并进入龙虎榜"]
        if industry:
            parts.append(f"映射{normalize_delivery_label(industry.group(1))}")
        if turnover:
            parts.append(f"换手率{float(turnover.group(1)):.1f}%")
        if board:
            parts.append(f"连板信息{board.group(1)}")
        parts.append("形成短线资金反馈")
        return "，".join(parts) + "。"
    if "资金流显示" in text:
        name = re.match(r"(.+?)资金流显示", text)
        industry = re.search(r"所属(?:环节|行业)为([^，]+)", text)
        main = re.search(r"主力净流入([-\d.]+)", text)
        big = re.search(r"超大单净流入([-\d.]+)", text)
        parts = [f"{name.group(1)}资金流" if name else "资金流"]
        if industry:
            parts.append(f"映射{normalize_delivery_label(industry.group(1))}")
        if main:
            parts.append(f"主力{amount_to_cn(main.group(1))}")
        if big:
            parts.append(f"超大单{amount_to_cn(big.group(1))}")
        parts.append("说明大单资金有参与痕迹")
        return "，".join(parts) + "。"
    if "龙虎榜上榜" in text:
        name = re.match(r"(.+?)龙虎榜上榜", text)
        industry = re.search(r"所属(?:环节|行业)为([^，]+)", text)
        reason = re.search(r"上榜原因[:：]?([^，]+)", text)
        interp = re.search(r"席位解读为([^，]+)", text)
        parts = [f"{name.group(1)}龙虎榜上榜" if name else "个股龙虎榜上榜"]
        if industry:
            parts.append(f"映射{normalize_delivery_label(industry.group(1))}")
        if reason:
            parts.append(short_reason(reason.group(1)))
        if interp:
            parts.append(re.sub(r"，?成功率\d+(\.\d+)?%", "", interp.group(1)))
        parts.append("体现机构或短线资金博弈")
        return "，".join(parts) + "。"
    if re.search(r"涨停，所属(?:环节|行业)为", text):
        name = re.match(r"(.+?)涨停", text)
        industry = re.search(r"所属(?:环节|行业)为([^，]+)", text)
        board = re.search(r"连板信息([^，]+)", text)
        amount = re.search(r"成交额([-\d.]+)", text)
        seal = re.search(r"封板资金([-\d.]+)", text)
        parts = [f"{name.group(1)}涨停" if name else "个股涨停"]
        if industry:
            parts.append(f"映射{normalize_delivery_label(industry.group(1))}")
        if board:
            parts.append(f"{board.group(1)}连板")
        if amount:
            parts.append(f"成交额{amount_to_cn(amount.group(1))}")
        if seal:
            parts.append(f"封板资金{amount_to_cn(seal.group(1))}")
        parts.append("提供短线资金确认")
        return "，".join(parts) + "。"
    text = sanitize_delivery_residue(text)
    text = re.sub(r"\b\d+\s+\d+\s+", "", text)
    text = re.sub(r"成功率\d+(\.\d+)?%", "", text)
    text = re.sub(r"榜单成交额[-\d.]+", "", text)
    text = re.sub(r"净买额[-\d.]+", "", text)
    text = re.sub(r"\s+", " ", text).strip(" ，。")
    if len(text) > 95:
        text = text[:95].rstrip("，；、 ") + "。"
    elif text and not text.endswith("。"):
        text += "。"
    return text


LEGACY_CLUSTER_AND_SCORE_DISABLED = None


def _legacy_single_theme_clusters_disabled(pool):
    raise RuntimeError("legacy keyword-cooccurrence clustering is permanently disabled")
    """Rebuild directions from themes that actually occur in the event pool.

    This is a split step, not a preset board pool: a candidate exists only when
    the same concrete term is present in the current event text and independently
    clears the existing multi-source and direction-level evidence gates.
    """
    candidates = Counter()
    for item in pool:
        for raw in item.get("theme_terms") or derive_theme_terms(item.get("event", ""), topn=8):
            term = clean_theme_term(raw)
            if term and label_is_clean(term):
                candidates[term] += 1
    rebuilt = []
    diagnostics = []
    for term, _count in candidates.most_common():
        items = [
            item for item in pool
            if term in item.get("event", "") or term in (item.get("theme_terms") or [])
        ]
        sources = items_evidence_sources(items)
        layers = source_layers(sources)
        if not cluster_has_strong_shape(items, sources, layers):
            if _count >= 2 and len(sources) >= 2:
                diagnostics.append(f"{term}({len(items)} events/{len(sources)} sources/{','.join(sorted(layers))})")
            continue
        quality = direction_evidence_quality({"items": items})
        if not quality["is_direction_level"]:
            continue
        merged = " ".join(item.get("event", "") for item in items)
        score = int(min(100,
            min(30, len(sources) * 6)
            + min(28, len(items) * 3)
            + min(22, sum(merged.count(word) for word in ["涨停", "成交额", "融资", "调研", "龙虎榜", "反弹", "风险"]) * 3)
            + min(15, sum(merged.count(word) for word in INDUSTRY_CHAIN_SIGNAL_WORDS) * 1.8)
        ))
        rebuilt.append({
            "name": term,
            "items": items,
            "sources": sources,
            "score": score,
            "keywords": [term],
            "direction_quality": quality,
        })
    if diagnostics:
        print("single_theme_rejected=" + " | ".join(diagnostics[:20]))
    return rebuilt


def _legacy_cluster_and_score_disabled(pool):
    raise RuntimeError("legacy KMeans and keyword-relabel path is permanently disabled")
    clusters = LEGACY_CLUSTER_AND_SCORE_DISABLED(pool)
    cleaned = []
    for c in clusters:
        # 2026-07-08: regenerate cluster name through the late keyword_label (jieba-noise filter).
        # BASE_CLUSTER_AND_SCORE used the early keyword_label which still emits noise like '样本/辨识/扩散'.
        # Only overwrite name when new_name passes label_is_clean; otherwise keep original.
        try:
            # A report direction must name one concrete industry theme.  Combining
            # several industries from a market-wide recap produces a false causal
            # relationship, even when every token is individually valid.
            new_name = keyword_label(c.get("items", []), topn=1)
            if label_is_clean(new_name):
                c["name"] = new_name
                c["keywords"] = [new_name]
        except Exception:
            pass
        if not label_is_clean(c.get("name", "")):
            continue
        layers = source_layers(c.get("sources", []))
        rank_bonus = 0
        if "主流财经" in layers:
            rank_bonus += 8
        if "散户社区" in layers:
            rank_bonus += 6
        if "游资社区" in layers:
            rank_bonus += 4
        rank_bonus += min(8, len(layers) * 2)
        delivery = evidence_delivery_quality(c, 10)
        if delivery["is_delivery_ready"]:
            rank_bonus += 20
        c["_rank_score"] = c.get("score", 0) + rank_bonus
        cleaned.append(c)
    # A retained slash label is proof that the legacy broad-cluster path failed
    # to isolate one industry; exclude it instead of relabeling its mixed items.
    cleaned = [
        c for c in cleaned
        if "/" not in c.get("name", "") and label_is_clean(c.get("name", ""))
    ]
    rebuilt = _legacy_single_theme_clusters_disabled(pool)
    cleaned.extend(rebuilt)
    cleaned = dedupe_clusters(cleaned)
    cleaned.sort(key=lambda x: (
        evidence_delivery_quality(x, 10)["is_delivery_ready"],
        x.get("_rank_score", x.get("score", 0)),
        len(source_layers(x.get("sources", []))),
        len(x.get("sources", [])),
        len(x.get("items", [])),
    ), reverse=True)
    unique = []
    seen_signatures = []
    for c in cleaned:
        c.pop("_rank_score", None)
        keywords = {clean_theme_term(k) for k in c.get("keywords", []) if clean_theme_term(k)}
        item_ids = {id(x) for x in c.get("items", [])}
        is_duplicate = False
        for old_keywords, old_item_ids in seen_signatures:
            keyword_overlap = len(keywords & old_keywords) / max(1, min(len(keywords), len(old_keywords)))
            item_overlap = len(item_ids & old_item_ids) / max(1, min(len(item_ids), len(old_item_ids)))
            if keyword_overlap >= 0.80 and item_overlap >= 0.55:
                is_duplicate = True
                break
        if is_duplicate:
            continue
        unique.append(c)
        seen_signatures.append((keywords, item_ids))
    return unique


CAUSAL_ROLE_ORDER = ["catalyst", "market", "participant", "counter"]
CAUSAL_ROLE_CN = {
    "catalyst": "触发事实",
    "market": "盘面确认",
    "participant": "参与者确认",
    "counter": "反证",
}
CAUSAL_VARIABLE_RULES = [
    (("模型更新", "模型升级", "模型发布", "版本更新", "版本升级", "性能提升"), "产品能力、成本效率与应用预期"),
    (("目录", "准入", "获批", "审批", "医保", "补贴", "政策", "规划", "规范", "需求"), "准入范围与需求预期"),
    (("订单", "中标", "合同", "签约", "交付"), "订单可见度与收入兑现"),
    (("价格", "涨价", "降价", "报价", "成本", "库存", "供需"), "供需、成本与盈利预期"),
    (("产能", "投产", "扩产", "停产", "供应", "产量"), "供给能力与行业景气"),
    (("发射", "回收", "试验", "测试", "验证", "量产", "技术"), "工程可行性与商业化节奏"),
    (("业绩", "利润", "营收", "预告", "增长", "亏损"), "业绩兑现与估值锚"),
    (("举牌", "增持", "回购", "定增", "募资"), "资本承诺、所有权结构与融资预期"),
    (("监管", "问询", "澄清", "减持", "处罚", "退市", "风险"), "监管约束与风险溢价"),
]
CAUSAL_MARKET_WORDS = {
    "板块", "方向", "领涨", "走强", "活跃", "上涨", "下跌", "回落", "涨停", "跌停",
    "连板", "成交额", "放量", "缩量", "封板", "炸板", "龙虎榜", "指数", "涨跌家数",
}
CAUSAL_PARTICIPANT_WORDS = {
    "机构", "调研", "融资", "主力", "超大单", "净流入", "净流出", "席位", "龙虎榜", "游资", "资金流",
}
CAUSAL_POSITIVE_WORDS = {
    "领涨", "走强", "活跃", "上涨", "涨停", "反弹", "回升", "扩容", "获批", "中标", "增长",
    "净流入", "净买入", "净买额", "成功", "落地", "提升", "放量", "扩散", "涨幅", "连板", "封板",
}
CAUSAL_NEGATIVE_WORDS = {
    "下跌", "回落", "走弱", "退潮", "跌停", "净流出", "减持", "问询", "处罚", "亏损", "下滑",
    "失败", "风险", "澄清", "炸板", "缩量", "分歧",
}
CAUSAL_TERM_EXCLUSIONS = {
    "设备", "公司", "股份", "科技", "市场", "指数", "资金", "交易", "行业", "方向", "产业链",
    "主线", "主题", "热点", "板块", "个股", "机构", "龙虎榜", "涨停", "复盘", "样本", "事件",
    "A股", "今日", "当日", "近期", "证券", "数据", "消息", "政策", "风险", "公告", "业绩", "出现",
}


def required_acquisition_capture_files():
    """Single source of truth shared by preflight and formal ingestion."""
    return list(REQUIRED_CAPTURE_FILES)
CAUSAL_CANONICAL_THEME_RULES = {
    "AI": (
        ("人工智能", "大模型", "模型更新", "模型升级", "Qwen", "AI应用", "AI影视", "AI手机", "AI服务器"),
    ),
    "中报增长": (
        ("中报", "半年报", "半年度报告"),
        ("增长", "预增", "扭亏"),
    ),
}


def _current_event_dates(now=None):
    return {cn_date(day) for day in event_window_calendar_dates(now)}


def _is_current_event(item, now=None):
    if not isinstance(item, dict) or item.get("window_type") != EVENT_WINDOW_TYPE:
        return False
    published = _parse_iso_datetime(item.get("published_at"))
    if not published:
        return False
    start, end = event_window_bounds(now)
    return start <= published <= end


def filter_current_event_pool(events, now=None):
    anchor = _china_datetime(now)
    return [item for item in events if _is_current_event(item, anchor)]


def _is_market_validation_event(item, now=None):
    if not isinstance(item, dict) or item.get("window_type") != MARKET_VALIDATION_WINDOW_TYPE:
        return False
    return clean_text(str(item.get("date", ""))) in {cn_date(day) for day in recent_trading_dates(now)}


def _is_valid_causal_input(item, now=None):
    return _is_current_event(item, now) or _is_market_validation_event(item, now)


def causal_label_is_clean(label):
    raw = clean_text(str(label or "")).strip()
    if not raw or "/" in raw or "、" in raw or re.search(r"\d", raw):
        return False
    term = clean_theme_term(raw)
    return bool(term) and term == raw and term not in CAUSAL_TERM_EXCLUSIONS


def _event_identity(item):
    return "|".join([
        clean_text(str(item.get("source", ""))),
        clean_text(str(item.get("date", ""))),
        re.sub(r"\s+", "", clean_text(str(item.get("event", ""))))[:180],
    ])


def _canonical_theme_clause_matches(theme, clause):
    rule = CAUSAL_CANONICAL_THEME_RULES.get(theme)
    if not rule:
        return False
    probe = clean_text(clause)
    # Mapping appendices can mention an adjacent theme (for example "AI制药")
    # even when the underlying event is purely medical.  Theme grounding must
    # come from the event fact itself, not from that appended routing hint.
    if theme == "AI":
        probe = re.split(r"A股映射[:：]", probe, maxsplit=1)[0]
    return all(any(marker in probe for marker in marker_group) for marker_group in rule)


def _explicit_theme_terms(clause):
    terms = set()
    patterns = [
        r"所属(?:环节|概念|行业)为([^，。；\r\n]{2,24})",
        r"([\u4e00-\u9fa5A-Za-z0-9]{2,12}(?:[与和及或、/+][\u4e00-\u9fa5A-Za-z0-9]{2,12}){0,3})(?:板块|概念|赛道|产业链)",
    ]
    for pattern in patterns:
        for raw in re.findall(pattern, clean_text(clause)):
            candidates = [raw]
            candidates.extend(re.split(r"[与和及或、/+]+", raw))
            for candidate in candidates:
                term = clean_theme_term(candidate)
                if term:
                    terms.add(term)
    return terms


def _theme_context(text, theme):
    clauses = [clean_text(x) for x in re.split(r"(?<=[。！？；])|[\r\n]+", clean_text(text)) if clean_text(x)]
    if theme == "AI":
        hits = [clause for clause in clauses if _canonical_theme_clause_matches(theme, clause)]
    else:
        hits = [clause for clause in clauses if theme and theme in clause]
    if not hits and theme in CAUSAL_CANONICAL_THEME_RULES:
        hits = [
            clause for clause in clauses
            if _canonical_theme_clause_matches(theme, clause)
        ]
    return " ".join(hits[:2]) if hits else ""


def _causal_variable(text):
    for markers, variable in CAUSAL_VARIABLE_RULES:
        if any(marker in text for marker in markers):
            return variable
    return ""


def _event_polarity(text):
    positive = sum(text.count(word) for word in CAUSAL_POSITIVE_WORDS)
    negative = sum(text.count(word) for word in CAUSAL_NEGATIVE_WORDS)
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    return "neutral"


def _causal_roles(item, theme, bridge_stocks=None):
    event = clean_text(item.get("event", ""))
    context = _theme_context(event, theme)
    layer = source_layer(item.get("source", ""))
    is_event_72h = _is_current_event(item)
    is_market_validation = _is_market_validation_event(item)
    grounding = "direct_theme"
    if not context and bridge_stocks:
        matched = sorted(set(extract_stock_names_from_event(event)) & set(bridge_stocks))
        if len(matched) >= 2 and layer in {"官方公告", "主流财经", "风险公告", "海外映射"}:
            context = event
            grounding = "multi_stock_bridge:" + "、".join(matched)
    if not context:
        return [], "", "", ""
    if theme not in context and _canonical_theme_clause_matches(theme, context):
        grounding = f"canonical_theme:{theme}"
    variable = _causal_variable(context)
    roles = []
    is_market_roundup = any(marker in event for marker in ("竞价看龙头", "盘面直击", "午间涨停分析"))
    if (
        variable
        and is_event_72h
        and layer in {"官方公告", "主流财经", "风险公告", "海外映射"}
        and not is_single_stock_trade_feedback(item)
        and not is_market_roundup
    ):
        roles.append("catalyst")
    if (
        is_market_validation
        and layer == "交易复盘"
        and any(word in context for word in CAUSAL_MARKET_WORDS)
    ):
        roles.append("market")
    if (is_event_72h or is_market_validation) and layer == "机构渠道" and any(word in context for word in CAUSAL_PARTICIPANT_WORDS):
        roles.append("participant")
    polarity = _event_polarity(context)
    if polarity == "negative" or layer == "风险公告":
        roles.append("counter")
    return list(dict.fromkeys(roles)), context, variable, grounding


def _causal_item_theme_grounded(theme, item):
    context = clean_text(item.get("causal_context", ""))
    if theme and theme in context:
        return True
    grounding = str(item.get("causal_grounding", ""))
    if grounding.startswith("multi_stock_bridge:") or grounding.startswith("market_state_bridge:"):
        return True
    if grounding == f"canonical_theme:{theme}":
        return _canonical_theme_clause_matches(theme, context)
    return False


def _causal_term_ok(term, clause):
    term = clean_theme_term(term)
    canonical_context = _canonical_theme_clause_matches(term, clause)
    if not term or (term not in clause and not canonical_context) or not (2 <= len(term) <= 8):
        return False
    if term in CAUSAL_TERM_EXCLUSIONS or term in known_stock_names():
        return False
    if re.search(r"\d", term) or any(bad in term for bad in BAD_LABEL_SUBSTRINGS):
        return False
    if not (
        canonical_context
        or _is_specific_label_token(term)
        or term in _explicit_theme_terms(clause)
    ):
        return False
    return causal_label_is_clean(term)


def _structured_causal_terms(clause):
    terms = []
    for theme in CAUSAL_CANONICAL_THEME_RULES:
        if _canonical_theme_clause_matches(theme, clause) and theme not in terms:
            terms.append(theme)
    for term in sorted(_explicit_theme_terms(clause), key=len, reverse=True):
        if _causal_term_ok(term, clause) and term not in terms:
            terms.append(term)
    for match in re.findall(r"所属(?:环节|概念|行业)为([^，。；\r\n]{2,24})", clean_text(clause)):
        for raw in re.split(r"[/、|]", match):
            term = clean_theme_term(raw)
            if term and _causal_term_ok(term, clause) and term not in terms:
                terms.append(term)
    for raw in re.findall(
        r"(?:A股映射[:：]|[；;])\s*([^，。；;\r\n（）()]{2,8})板块",
        clean_text(clause),
    ):
        term = normalize_label_word(raw)
        if (
            term in SPECIFIC_LABEL_HINTS
            and term not in CAUSAL_TERM_EXCLUSIONS
            and term not in terms
        ):
            terms.append(term)
    return terms


def causal_candidate_terms(pool):
    term_events = defaultdict(set)
    term_sources = defaultdict(set)
    term_layers = defaultdict(set)
    term_current_events = defaultdict(set)
    for item in pool:
        if is_five_site_supplemental(item) or not _is_valid_causal_input(item):
            continue
        is_current = _is_current_event(item)
        event = clean_text(item.get("event", ""))
        clauses = [clean_text(x) for x in re.split(r"(?<=[。！？；])|[\r\n]+", event) if clean_text(x)]
        for clause in clauses:
            raw_terms = _structured_causal_terms(clause)
            if is_current:
                raw_terms.extend(derive_theme_terms(clause, topn=10))
                raw_terms.extend(candidate_terms_from_text(clause, topn=18))
            for raw in raw_terms:
                term = clean_theme_term(raw)
                if not _causal_term_ok(term, clause):
                    continue
                key = _event_identity(item)
                term_events[term].add(key)
                term_sources[term].add(item.get("source", ""))
                term_layers[term].add(source_layer(item.get("source", "")))
                if is_current:
                    term_current_events[term].add(key)
    candidates = [
        term for term in term_events
        if len(term_events[term]) >= 3
        and len(term_sources[term]) >= MIN_CLUSTER_SOURCES
        and len(term_layers[term]) >= 2
        and term_current_events[term]
    ]
    candidates.sort(key=lambda term: (
        len(term_layers[term]), len(term_sources[term]), len(term_events[term]), len(term)
    ), reverse=True)
    return candidates


def _causal_direction_quality(items):
    stocks = sorted({
        stock
        for item in items
        for stock in extract_stock_names_from_event(item.get("event", ""))
    })
    market_items = [item for item in items if "market" in (item.get("causal_roles") or [])]
    market_stocks = sorted({
        stock
        for item in market_items
        for stock in extract_stock_names_from_event(item.get("event", ""))
    })
    market_non_stock = sum(1 for item in market_items if is_non_stock_direction_event(item))
    single_stock = sum(1 for item in items if is_single_stock_trade_feedback(item))
    return {
        "stock_count": len(stocks),
        "stocks": stocks,
        "market_stock_count": len(market_stocks),
        "market_stocks": market_stocks,
        "market_role_event_count": len(market_items),
        "market_role_non_stock_events": market_non_stock,
        "stock_level_market_breadth_ready": len(market_stocks) >= MIN_DIRECTION_STOCKS,
        "non_stock_events": market_non_stock,
        "single_stock_trade_feedback_events": single_stock,
        "is_direction_level": market_non_stock >= 1 or len(market_stocks) >= MIN_DIRECTION_STOCKS,
    }


def _short_causal_fact(item, limit=78):
    text = sanitize_delivery_residue(clean_text(item.get("causal_context") or item.get("event", ""))).strip(" ，。；")
    if len(text) > limit:
        text = text[:limit].rstrip("，；、 ")
    return text + ("。" if text and not text.endswith("。") else "")


def _causal_role_meaning(theme, item):
    return _short_causal_fact(item)


def _causal_stance(items):
    market_items = [item for item in items if "market" in (item.get("causal_roles") or [])]
    positive = sum(item.get("causal_polarity") == "positive" for item in market_items)
    negative = sum(item.get("causal_polarity") == "negative" for item in market_items)
    if positive and negative:
        return "分歧"
    if positive > negative:
        return "增强"
    if negative > positive:
        return "转弱"
    return "待确认"


def _theme_specificity_score(theme, item):
    event = re.split(r"A股映射[:：]", clean_text(item.get("event", "")), maxsplit=1)[0]
    markers = [theme]
    for group in CAUSAL_CANONICAL_THEME_RULES.get(theme, ()):
        markers.extend(group)
    return sum(event.count(marker) for marker in set(markers) if marker)


def _first_role_item(items, role, theme=""):
    candidates = [item for item in items if role in (item.get("causal_roles") or [])]
    if not candidates:
        return None
    if role == "catalyst" and theme:
        return max(candidates, key=lambda item: (
            _theme_specificity_score(theme, item),
            bool(item.get("causal_variable")),
            source_layer(item.get("source", "")) in {"官方公告", "主流财经"},
            clean_text(item.get("published_at", "")),
        ))
    return candidates[0]


def _market_role_baseline(theme, items):
    market = _first_role_item(items, "market", theme)
    if not market:
        return {"count": 0, "date": "", "stocks": []}
    event = clean_text(market.get("event", ""))
    count_match = re.search(r"共有\s*(\d+)\s*只涨停", event)
    stock_match = re.search(r"代表标的包括([^，。；]{2,100})", event)
    stocks = []
    if stock_match:
        for stock in re.split(r"[、,，]", stock_match.group(1)):
            stock = clean_text(stock)
            if stock and stock not in stocks:
                stocks.append(stock)
    return {
        "count": int(count_match.group(1)) if count_match else 0,
        "date": clean_text(market.get("date", "")),
        "stocks": stocks[:4],
    }


def _market_theme_breadth_snapshot(pool, date_label):
    counts = {}
    for item in pool:
        if clean_text(item.get("date", "")) != clean_text(date_label):
            continue
        event = clean_text(item.get("event", ""))
        match = re.search(r"所属概念为([^，。；]{1,16})，该方向共有\s*(\d+)\s*只涨停", event)
        if not match:
            continue
        theme = clean_theme_term(match.group(1))
        if theme:
            counts[theme] = max(counts.get(theme, 0), int(match.group(2)))
    return sorted(counts.items(), key=lambda row: (row[1], len(row[0])), reverse=True)


def _causal_chain_text(theme, items, stance):
    if stance not in ALLOWED_CAUSAL_STANCES:
        raise RuntimeError(f"scientific gate: invalid causal stance for {theme}: {stance or 'missing'}")
    catalyst = _first_role_item(items, "catalyst", theme)
    market = _first_role_item(items, "market", theme)
    participant = _first_role_item(items, "participant", theme)
    counter = _first_role_item(items, "counter", theme)
    catalyst_fact = _short_causal_fact(catalyst) if catalyst else ""
    market_fact = _short_causal_fact(market) if market else ""
    participant_fact = _short_causal_fact(participant) if participant else ""
    counter_fact = _short_causal_fact(counter) if counter else ""
    counterevidence = counter_fact or "本轮证据中未检出直接反向事实。"
    variable = catalyst.get("causal_variable", "") if catalyst else ""
    baseline = _market_role_baseline(theme, items)
    baseline_count = baseline["count"]
    breadth_floor = max(2, (baseline_count + 1) // 2) if baseline_count else 2
    stock_text = "、".join(baseline["stocks"][:3]) or f"{theme}核心标的"
    baseline_text = (
        f"{baseline['date']}板块有{baseline_count}只涨停，代表标的为{stock_text}"
        if baseline_count else market_fact.rstrip("。")
    )
    mechanism_map = {
        "产品能力、成本效率与应用预期": "模型能力和使用成本改善，会先抬升应用渗透与算力需求预期，再由板块宽度和资金承接验证是否从消息走向交易主线",
        "准入范围与需求预期": "政策或准入变化先提高需求可见度，只有板块宽度和资金承接同步扩大，才说明预期开始进入交易定价",
        "订单可见度与收入兑现": "订单与交付提升收入可见度，盘面宽度和参与者资金用于判断市场是否认可兑现节奏",
        "供需、成本与盈利预期": "供需和价格变化先影响盈利预期，随后必须看到板块扩散与资金承接，才能排除单一消息脉冲",
        "供给能力与行业景气": "产能与供给变化影响景气判断，盘面宽度和资金承接决定该变化是否形成持续主线",
        "工程可行性与商业化节奏": "技术或量产进展改善商业化预期，板块宽度和资金承接决定预期能否继续扩散",
        "业绩兑现与估值锚": "业绩变化重估盈利与估值锚，随后由板块宽度和资金承接验证持续性",
    }
    mechanism = mechanism_map.get(
        variable,
        f"触发事实先改变{variable or '需求与盈利预期'}，再由板块宽度和参与者资金验证是否形成持续交易主线",
    ) + "。"
    next_check = (
        f"次日强势成立条件（研究规则）：{theme}涨停家数≥{breadth_floor}家；"
        f"{stock_text}中至少1只保持强承接；参与者资金证据不转弱。"
    )
    invalidation = counter_fact or (
        f"失效条件（研究规则）：{theme}涨停家数<{breadth_floor}家，"
        f"或{stock_text}全部转弱且参与者资金同步转弱；出现重大澄清或风险公告时立即重估。"
    )
    return {
        "conclusion": (
            f"{theme}列入高优先级主线：触发变量为{variable or '需求与盈利预期'}；"
            f"{baseline_text}；参与者资金证据同向。当前状态为{stance}，但必须满足次日量化条件才延续。"
        ),
        "catalyst_fact": catalyst_fact,
        "mechanism": mechanism,
        "market_feedback": baseline_text + "。",
        "participant_feedback": participant_fact,
        "counterevidence": counterevidence,
        "next_check": next_check,
        "invalidation": invalidation,
    }


def causal_chain_quality(cluster):
    items = cluster.get("items", [])
    role_counts = Counter(role for item in items for role in (item.get("causal_roles") or []))
    sources = items_evidence_sources(items)
    layers = source_layers(sources)
    direction = _causal_direction_quality(items)
    stored_direction = cluster.get("direction_quality")
    unique_events = {_event_identity(item) for item in items}
    stale_events = [item for item in items if not _is_valid_causal_input(item)]
    catalyst_window_errors = [item for item in items if "catalyst" in (item.get("causal_roles") or []) and not _is_current_event(item)]
    market_window_errors = [item for item in items if "market" in (item.get("causal_roles") or []) and not _is_market_validation_event(item)]
    role_event_ids = {
        role: {_event_identity(item) for item in items if role in (item.get("causal_roles") or [])}
        for role in ("catalyst", "market", "participant")
    }
    primary_role_ids = set().union(*role_event_ids.values())
    theme = cluster.get("name", "")
    ungrounded = [
        item.get("source", "") for item in items
        if not _causal_item_theme_grounded(theme, item)
    ]
    stance = cluster.get("stance", "")
    computed_stance = _causal_stance(items)
    stance_ready = (
        stance in ALLOWED_CAUSAL_STANCES
        and computed_stance in ALLOWED_CAUSAL_STANCES
        and stance == computed_stance
    )
    ready = (
        role_counts["catalyst"] >= MIN_CAUSAL_CATALYSTS
        and role_counts["market"] >= MIN_CAUSAL_MARKET_FEEDBACK
        and role_counts["participant"] >= MIN_CAUSAL_PARTICIPANT_FEEDBACK
        and len(sources) >= MIN_CLUSTER_SOURCES
        and len(layers) >= MIN_CLUSTER_SOURCE_LAYERS
        and "交易复盘" in layers
        and "机构渠道" in layers
        and direction["is_direction_level"]
        and len(unique_events) == len(items)
        and not stale_events
        and not catalyst_window_errors
        and not market_window_errors
        and len(primary_role_ids) >= 3
        and not (role_event_ids["catalyst"] & role_event_ids["market"])
        and not (role_event_ids["catalyst"] & role_event_ids["participant"])
        and not (role_event_ids["market"] & role_event_ids["participant"])
        and not ungrounded
        and stance_ready
    )
    return {
        "ready": ready,
        "stance": stance,
        "computed_stance": computed_stance,
        "stance_ready": stance_ready,
        "role_counts": dict(role_counts),
        "source_count": len(sources),
        "source_layers": sorted(layers),
        "unique_event_count": len(unique_events),
        "event_count": len(items),
        "stale_event_count": len(stale_events),
        "catalyst_outside_72h_count": len(catalyst_window_errors),
        "market_outside_three_trading_day_validation_count": len(market_window_errors),
        "primary_role_distinct_event_count": len(primary_role_ids),
        "primary_role_event_counts": {role: len(ids) for role, ids in role_event_ids.items()},
        "ungrounded_sources": ungrounded,
        "direction_quality": direction,
        "stored_direction_quality_matches": stored_direction in (None, direction),
    }


def _causal_score_components(items):
    sources = items_evidence_sources(items)
    role_counts = Counter(role for item in items for role in (item.get("causal_roles") or []))
    now = _china_datetime()
    catalyst_ages = []
    for item in items:
        if "catalyst" not in (item.get("causal_roles") or []) or not _is_current_event(item, now):
            continue
        published = _parse_iso_datetime(item.get("published_at"))
        if published:
            catalyst_ages.append(max(0.0, (now - published).total_seconds() / 3600))
    newest_catalyst_age = min(catalyst_ages) if catalyst_ages else None
    if newest_catalyst_age is None:
        freshness = 0
    elif newest_catalyst_age <= 24:
        freshness = 10
    elif newest_catalyst_age <= 48:
        freshness = 7
    else:
        freshness = 4
    components = {
        "impact_scope": min(30, len(source_layers(sources)) * 9),
        "market_heat": min(25, role_counts["market"] * 10),
        "fund_feedback": min(20, role_counts["participant"] * 10),
        "industry_chain_mapping": min(15, role_counts["catalyst"] * 12),
        "evidence_strength": 0,
        "freshness": freshness,
    }
    components["total"] = min(100, sum(components.values()))
    return components


def _build_causal_cluster(theme, pool):
    pool = [item for item in pool if _is_valid_causal_input(item)]
    items = []
    seen = set()
    direct_items = [item for item in pool if theme in clean_text(item.get("event", ""))]
    bridge_stocks = sorted({
        stock
        for item in direct_items
        for stock in extract_stock_names_from_event(item.get("event", ""))
    })
    if len(bridge_stocks) < MIN_DIRECTION_STOCKS:
        bridge_stocks = []
    for raw in pool:
        roles, context, variable, grounding = _causal_roles(raw, theme, bridge_stocks)
        if not roles:
            continue
        key = _event_identity(raw)
        if key in seen:
            continue
        seen.add(key)
        item = dict(raw)
        item["causal_roles"] = roles
        item["causal_context"] = context
        item["causal_variable"] = variable
        item["causal_grounding"] = grounding
        item["causal_polarity"] = _event_polarity(context)
        item["meaning"] = _causal_role_meaning(theme, item)
        items.append(item)
    direction = _causal_direction_quality(items)
    sources = items_evidence_sources(items)
    stance = _causal_stance(items)
    narrative = _causal_chain_text(theme, items, stance) if items and stance in ALLOWED_CAUSAL_STANCES else {}
    role_counts = Counter(role for item in items for role in item.get("causal_roles", []))
    cluster = {
        "name": theme,
        "items": items,
        "sources": sources,
        "score": 0,
        "keywords": [theme],
        "direction_quality": direction,
        "stance": stance,
        "causal": narrative,
        "causal_method": "event_text_exact_theme_role_chain_v1",
    }
    cluster["score_components"] = _causal_score_components(items)
    cluster["score"] = cluster["score_components"]["total"]
    cluster["causal_quality"] = causal_chain_quality(cluster)
    return cluster


def _build_market_state_cluster(pool):
    return None


def cluster_and_score(pool):
    pool = [item for item in primary_events(pool) if _is_valid_causal_input(item)]
    clusters = []
    for theme in causal_candidate_terms(pool):
        cluster = _build_causal_cluster(theme, pool)
        if cluster["score"] < 60 or not cluster["causal_quality"]["ready"]:
            continue
        clusters.append(cluster)
    clusters.sort(key=lambda c: (
        _market_role_baseline(c["name"], c.get("items", []))["count"],
        c["score"],
        c["causal_quality"]["source_count"],
        c["causal_quality"]["role_counts"].get("catalyst", 0),
        len(c["name"]),
    ), reverse=True)
    unique = []
    for cluster in clusters:
        cluster_ids = {_event_identity(item) for item in cluster["items"]}
        duplicate = False
        for kept in unique:
            kept_ids = {_event_identity(item) for item in kept["items"]}
            overlap = len(cluster_ids & kept_ids) / max(1, min(len(cluster_ids), len(kept_ids)))
            names_overlap = cluster["name"] in kept["name"] or kept["name"] in cluster["name"]
            if names_overlap and overlap >= 0.75:
                duplicate = True
                break
        if not duplicate:
            unique.append(cluster)
    return unique


def event_theme_keys(event):
    return (event.get("theme_terms") or derive_theme_terms(event.get("event", ""), topn=5))[:3]


def cluster_label_from_anchor(anchor, items, topn=4):
    anchor = clean_theme_term(anchor)
    merged = " ".join(x.get("event", "") for x in items)
    terms = []
    if anchor:
        terms.append(anchor)
    for item in items:
        for term in item.get("theme_terms") or derive_theme_terms(item.get("event", ""), topn=6):
            term = clean_theme_term(term)
            if term and term not in terms:
                terms.append(term)
    for term in candidate_terms_from_text(merged, topn=24):
        term = clean_theme_term(term)
        if term and term not in terms:
            terms.append(term)
    label = " / ".join(terms[:topn])
    if label_is_clean(label):
        return label, terms[:topn]
    fallback = keyword_label(items, topn=topn)
    return fallback, fallback.split(" / ")


def cluster_has_strong_shape(items, sources, layers):
    if len(items) < 3:
        return False
    if len(sources) < MIN_CLUSTER_SOURCES or len(layers) < MIN_CLUSTER_SOURCE_LAYERS:
        return False
    if not (layers & MANDATORY_FEEDBACK_LAYERS) or not (layers & MANDATORY_PARTICIPANT_LAYERS):
        return False
    if not direction_evidence_quality({"items": items})["is_direction_level"]:
        return False
    merged = " ".join(x.get("event", "") for x in items)
    return value_signal_score(merged) >= 3 or sum(merged.count(word) for word in INDUSTRY_CHAIN_SIGNAL_WORDS) >= 2


def keyword_group_clusters(pool):
    term_map = defaultdict(list)
    for item in pool:
        for key in event_theme_keys(item):
            term_map[key].append(item)
    clusters = []
    for key, items in term_map.items():
        if len(items) < 3:
            continue
        expanded_items = list(items)
        key_terms = {
            clean_theme_term(term)
            for term in candidate_terms_from_text(" ".join(x["event"] for x in items), topn=12)
        }
        key_terms = {term for term in key_terms if term}
        if clean_theme_term(key):
            key_terms.add(clean_theme_term(key))
        for extra in pool:
            if extra in expanded_items:
                continue
            extra_terms = {
                clean_theme_term(term)
                for term in (extra.get("theme_terms") or derive_theme_terms(extra.get("event", ""), topn=6))
            }
            extra_terms |= {clean_theme_term(term) for term in candidate_terms_from_text(extra["event"], topn=8)}
            extra_terms = {term for term in extra_terms if term}
            overlap = key_terms & extra_terms
            if clean_theme_term(key) in extra_terms or len(overlap) >= 2:
                expanded_items.append(extra)
            if len(expanded_items) >= len(items) + 18:
                break
        items = expanded_items
        sources = items_evidence_sources(items)
        layers = source_layers(sources)
        if not cluster_has_strong_shape(items, sources, layers):
            continue
        if len(sources) < MIN_CLUSTER_SOURCES or len(layers) < MIN_CLUSTER_SOURCE_LAYERS:
            continue
        if not (layers & MANDATORY_FEEDBACK_LAYERS) or not (layers & MANDATORY_PARTICIPANT_LAYERS):
            continue
        merged = " ".join(x["event"] for x in items)
        chain_hits = sum(merged.count(word) for word in INDUSTRY_CHAIN_SIGNAL_WORDS)
        score = int(min(100,
            min(30, len(sources) * 6)
            + min(28, len(items) * 3)
            + min(22, sum(merged.count(w) for w in ["涨停", "成交额", "融资", "调研", "龙虎榜", "热度", "反弹", "澄清", "风险"]) * 3)
            + min(15, chain_hits * 1.8)
            + min(5, sum(1 for x in items if x.get("date") in [cn_date(d) for d in recent_trading_dates()]) * 0.5)
        ))
        name, keywords = cluster_label_from_anchor(key, items)
        if not label_is_clean(name):
            continue
        quality = direction_evidence_quality({"items": items})
        if not quality["is_direction_level"]:
            continue
        clusters.append({"name": name, "items": items, "sources": sources, "score": score, "keywords": keywords, "direction_quality": quality})
    return clusters


def score_breakdown(cluster):
    items = cluster["items"]
    sources = items_evidence_sources(items)
    role_counts = Counter(role for item in items for role in item.get("causal_roles", []))
    quality = causal_chain_quality(cluster)
    components = _causal_score_components(items)
    return {
        "direction": cluster["name"],
        **components,
        "events": len(items),
        "sources": sorted(sources),
        "source_layers": sorted(source_layers(sources)),
        "keywords": cluster.get("keywords", []),
        "causal_role_counts": dict(role_counts),
        "causal_ready": quality["ready"],
        "causal_method": cluster.get("causal_method", ""),
    }


def cluster_analysis_rows(cluster):
    rows = cluster_fact_rows(cluster)
    return rows[1:4]


def _historical_collect_chrome_visible_events_disabled(now):
    raise RuntimeError("manual Chrome event injection is disabled; generate must collect its own event pool")
    raw_path = os.environ.get("A_SHARE_CHROME_VISIBLE_EVENTS", "").strip()
    if not raw_path:
        return []
    path = Path(raw_path)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    allowed_dates = {cn_date(day) for day in recent_trading_dates(now)}
    events = []
    for item in payload if isinstance(payload, list) else []:
        if not isinstance(item, dict):
            continue
        source = clean_text(str(item.get("source", "")))
        date = clean_text(str(item.get("date", "")))
        event = clean_text(str(item.get("event", "")))
        if (
            not source
            or not event
            or date not in allowed_dates
            or source in REQUIRED_SOCIAL_PLATFORMS
            or not chrome_discovery_metadata_ok(item, now)
        ):
            continue
        events.append({
            "source": source,
            "date": date,
            "event": event,
            "url": str(item.get("url", "")),
            "theme_terms": derive_theme_terms(event, topn=6),
            "source_channel": "primary_chrome_visible",
            "discovery_mode": str(item.get("discovery_mode", "")),
            "discovery_query": str(item.get("discovery_query", "")),
            "discovery_terms": list(item.get("discovery_terms", [])),
            "discovery_entry_url": str(item.get("discovery_entry_url", "")),
        })
    return events


def _load_public_readonly_fallback_module():
    module_path = ROOT.parents[1] / "scripts" / "public_readonly_fallback.py"
    spec = importlib.util.spec_from_file_location(
        "a_share_hotspot_public_readonly_fallback",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"BLOCKED public fallback loader unavailable: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_public_readonly_capture(out_dir):
    capture_dir_value = os.environ.get(CHROME_CAPTURE_ENV, "").strip()
    required_files = required_acquisition_capture_files()
    if capture_dir_value:
        capture_dir = Path(capture_dir_value)
        if all((capture_dir / name).is_file() for name in required_files):
            return {
                "status": "PASS",
                "capture_dir": str(capture_dir),
                "mode": "configured_capture",
            }
    capture_dir = Path(out_dir) / "_public_readonly_capture"
    module = _load_public_readonly_fallback_module()
    manifest = module.collect_and_write_sentiment(capture_dir)
    if manifest.get("status") != "PASS":
        raise RuntimeError(
            "BLOCKED public read-only acquisition fallback failed: "
            + json.dumps(manifest, ensure_ascii=False)
        )
    os.environ[CHROME_CAPTURE_ENV] = str(capture_dir)
    os.environ[PUBLIC_READONLY_FALLBACK_ENV] = "1"
    duanxianxia_snapshot = manifest.get("duanxianxia_snapshot", "")
    if duanxianxia_snapshot and Path(duanxianxia_snapshot).is_file():
        os.environ[DUANXIANXIA_SNAPSHOT_ENV] = str(duanxianxia_snapshot)
    globals()["public_readonly_fallback_manifest"] = manifest
    return {
        "status": "PASS",
        "capture_dir": str(capture_dir),
        "mode": PUBLIC_READONLY_FALLBACK_CHANNEL,
        "manifest": manifest.get("manifest", ""),
    }


def collect_event_pool(now=None):
    now = _china_datetime(now)
    if CHROME_ONLY_ACQUISITION:
        return [
            item for item in collect_chrome_capture_events(now)
            if item.get("window_type") == EVENT_WINDOW_TYPE
        ]
    pool = []
    seen = set()
    print(f"[collect_event_pool] start at {now.isoformat()}", flush=True)
    print(f"[collect_event_pool] dynamic_source_urls...", flush=True)
    urls1 = dynamic_source_urls()
    print(f"[collect_event_pool] dynamic_source_urls -> {len(urls1)}", flush=True)
    print(f"[collect_event_pool] discover_source_article_urls...", flush=True)
    urls2 = discover_source_article_urls(max_per_source=4)
    print(f"[collect_event_pool] discover_source_article_urls -> {len(urls2)}", flush=True)
    print(f"[collect_event_pool] discover_urls...", flush=True)
    urls3 = discover_urls(max_urls=10)
    print(f"[collect_event_pool] discover_urls -> {len(urls3)}", flush=True)
    source_urls = urls1 + urls2 + urls3
    print(f"[collect_event_pool] total source_urls={len(source_urls)}", flush=True)
    fetched_ok = 0
    fetched_fail = 0
    last_log = time.time()
    deadline_ts = time.time() + 240
    for i, (source, url) in enumerate(source_urls):
        if source in REQUIRED_SOCIAL_PLATFORMS:
            continue
        if time.time() > deadline_ts:
            print(f"[collect_event_pool] global_deadline reached at {i+1}/{len(source_urls)}", flush=True)
            break
        page_record = fetch_text(url, with_metadata=True, now=now)
        page = page_record.get("text", "")
        if not page:
            fetched_fail += 1
            continue
        fetched_ok += 1
        page_publication = page_record.get("publication")
        if not page_publication and source_layer(source) not in {"游资社区", "散户社区", "机构渠道"}:
            continue
        for chunk in extract_chunks(page, source=source):
            event = sanitize_five_site_event_text(chunk)
            if len(event) < 18 or social_ui_noise_hits(event):
                continue
            if source in REQUIRED_SOCIAL_PLATFORMS and not any(term in event for term in FIVE_SITE_MARKET_TERMS):
                continue
            publication = extract_publication(chunk, url, now) or page_publication
            if not publication:
                continue
            if event_importance_score(event, source) < 25 and source_layer(source) in {"主流财经", "海外映射"}:
                continue
            key = re.sub(r"\W+", "", source + event)[:120]
            if key in seen:
                continue
            seen.add(key)
            pool.append({
                "source": source,
                "date": publication["date"],
                "published_at": publication["published_at"],
                "time_precision": publication["time_precision"],
                "time_evidence": publication["time_evidence"],
                "window_type": EVENT_WINDOW_TYPE,
                "event": event,
                "url": url,
                "theme_terms": derive_theme_terms(event, topn=6),
                "source_channel": "primary_public_web",
                "publication_source": page_record.get("publication_source", ""),
            })
        time.sleep(0.08)
        now_log = time.time()
        if now_log - last_log > 5 or (i + 1) % 20 == 0:
            print(f"[collect_event_pool] progress {i+1}/{len(source_urls)} ok={fetched_ok} fail={fetched_fail} pool={len(pool)}", flush=True)
            last_log = now_log
    print(f"[collect_event_pool] fetch_done ok={fetched_ok} fail={fetched_fail} pool={len(pool)}", flush=True)
    pool.extend(collect_search_result_events(now))
    print(f"[collect_event_pool] after_search pool={len(pool)}", flush=True)
    five_site_events = collect_five_site_public_events(now)
    pool.extend(five_site_events)
    print(f"[collect_event_pool] after_automatic_five_site pool={len(pool)} five_site_events={len(five_site_events)}", flush=True)
    deduped = []
    seen = set()
    for item in pool:
        if not _is_current_event(item, now):
            continue
        if "theme_terms" not in item:
            item["theme_terms"] = derive_theme_terms(item.get("event", ""), topn=6)
        key = re.sub(r"\W+", "", item.get("event", ""))[:90]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def collect_market_validation_pool(now=None):
    now = _china_datetime(now)
    chrome_events = [
        item for item in collect_chrome_capture_events(now)
        if item.get("window_type") == MARKET_VALIDATION_WINDOW_TYPE
    ] if CHROME_ONLY_ACQUISITION else []
    local_events = collect_local_trade_review_events(now)
    lianban_events = collect_lianban_market_validation_events(now, local_events)
    tdx_events = collect_tdx_market_validation_events(now)
    duanxianxia_events = collect_duanxianxia_market_validation_events(now)
    validation = []
    seen = set()
    for raw in chrome_events + local_events + lianban_events + tdx_events + duanxianxia_events:
        item = dict(raw)
        item["window_type"] = MARKET_VALIDATION_WINDOW_TYPE
        item.setdefault("source_channel", "primary_local_trade_review")
        item["market_date"] = item.get("date", "")
        if not _is_market_validation_event(item, now):
            continue
        if "theme_terms" not in item:
            item["theme_terms"] = derive_theme_terms(item.get("event", ""), topn=6)
        key = _event_identity(item)
        if key in seen:
            continue
        seen.add(key)
        validation.append(item)
    return validation


def write_audit_files(out_dir, pool, clusters):
    now = _china_datetime()
    event_window_start, event_window_end = event_window_bounds(now)
    event_pool = [item for item in pool if item.get("window_type") == EVENT_WINDOW_TYPE]
    market_validation_pool = [item for item in pool if item.get("window_type") == MARKET_VALIDATION_WINDOW_TYPE]
    score_rows = [score_breakdown(c) for c in clusters]
    layer_counts = Counter(source_layer(x["source"]) for x in pool)
    primary_pool = primary_events(pool)
    primary_layer_counts = primary_source_layer_counts(pool)
    five_site_pool = supplemental_five_site_events(pool)
    review_dir, review_ymd = latest_local_review_dir()
    capture_manifest = globals().get("chrome_capture_manifest", [])
    capture_channels = sorted({
        str(item.get("channel", ""))
        for item in capture_manifest
        if item.get("channel")
    })
    public_fallback_used = PUBLIC_READONLY_FALLBACK_CHANNEL in capture_channels
    audit = {
        "locked_template": str(LOCKED_TEMPLATE),
        "locked_template_sha256": LOCKED_TEMPLATE_SHA256,
        "event_window_hours": EVENT_WINDOW_HOURS,
        "event_window_start": event_window_start.isoformat(timespec="seconds"),
        "event_window_end": event_window_end.isoformat(timespec="seconds"),
        "event_window_calendar_dates": [cn_date(d) for d in event_window_calendar_dates(now)],
        "market_validation_trading_dates": [cn_date(d) for d in recent_trading_dates(now)],
        "event_pool_strict_72h_count": len(event_pool),
        "market_validation_pool_count": len(market_validation_pool),
        "event_pool_count": len(pool),
        "primary_event_pool_count": len(primary_pool),
        "mandatory_sentiment_event_count": len(five_site_pool),
        "source_count": len({x["source"] for x in pool}),
        "source_layer_count": len(layer_counts),
        "source_layer_counts": dict(sorted(layer_counts.items())),
        "primary_source_count": len({x["source"] for x in primary_pool}),
        "primary_source_layer_counts": dict(sorted(primary_layer_counts.items())),
        "mandatory_sentiment_source_counts": five_site_event_counts(pool),
        "mandatory_sentiment_source_audit": mandatory_sentiment_source_audit(event_pool, now),
        "market_cross_validation_audit": market_cross_validation_audit(market_validation_pool),
        "mandatory_sentiment_role": "required_unified_event_pool_and_sentiment_input",
        "chrome_only_acquisition": CHROME_ONLY_ACQUISITION and not public_fallback_used,
        "acquisition_channels": capture_channels,
        "public_readonly_fallback_used": public_fallback_used,
        "direct_http_web_requests": (
            "controlled_public_readonly_fallback"
            if public_fallback_used
            else "mechanically_blocked"
        ),
        "chrome_capture_manifest": capture_manifest,
        "public_readonly_fallback_manifest": globals().get("public_readonly_fallback_manifest", {}),
        "lianban_market_validation_profile": globals().get("lianban_market_validation_profile", {}),
        "tdx_market_validation_profile": globals().get("tdx_market_validation_profile", {}),
        "duanxianxia_market_validation_profile": globals().get("duanxianxia_market_validation_profile", {}),
        "cluster_count": len(clusters),
        "local_trade_review_dir": str(review_dir) if review_dir else "",
        "local_trade_review_date": review_ymd,
        "generation_order": [
            "collect_recent_72h_full_source_event_pool",
            "deduplicate_and_filter_events",
            "cluster_by_event_text_industry_terms_market_feedback_fund_heat",
            "score_by_heat_impact_fund_feedback_industry_mapping_evidence_freshness",
            "render_to_locked_template",
        ],
        "preset_board_pool_used": False,
        "cluster_labels_derived_from_event_text": True,
        "blocked_if_preset_board_bias": True,
        "redline_hard_gate_required_for_delivery": True,
        "red_line": "先生成最近72小时全源事件池，再聚类、评分、自然归类；禁止预设板块。",
    }
    write_json_text(out_dir / "a_share_sentiment_scores.json", score_rows)
    write_json_text(out_dir / "a_share_sentiment_audit.json", audit)


def _load_delivery_artifacts(artifact_dir):
    artifact_dir = Path(artifact_dir)
    return {
        "event_pool": read_json_or_none(artifact_dir / "a_share_sentiment_event_pool.json"),
        "market_validation_pool": read_json_or_none(artifact_dir / "a_share_sentiment_market_validation_pool.json"),
        "mandatory_sentiment_sources": read_json_or_none(
            artifact_dir / "a_share_sentiment_mandatory_sources_audit.json"
        ),
        "market_cross_validation": read_json_or_none(
            artifact_dir / "a_share_sentiment_market_cross_validation_audit.json"
        ),
        "clusters": read_json_or_none(artifact_dir / "a_share_sentiment_clusters.json"),
        "report_sections": read_json_or_none(artifact_dir / "a_share_sentiment_report_sections.json"),
        "scores": read_json_or_none(artifact_dir / "a_share_sentiment_scores.json"),
        "audit": read_json_or_none(artifact_dir / "a_share_sentiment_audit.json"),
        "redline": read_json_or_none(artifact_dir / "a_share_sentiment_redline_audit.json"),
    }


def _cluster_names_from_artifacts(clusters):
    names = []
    for c in clusters or []:
        if isinstance(c, dict) and c.get("name"):
            names.append(str(c["name"]))
    return names


def _evidence_rows_from_artifacts(clusters):
    total = 0
    rows = []
    for c in clusters or []:
        if not isinstance(c, dict):
            continue
        delivery_quality = c.get("delivery_quality") or {}
        count = delivery_quality.get("evidence_rows")
        if count is None:
            selected = c.get("select_evidence") or c.get("evidence") or []
            count = len(selected) if isinstance(selected, list) else 0
        try:
            count = int(count)
        except Exception:
            count = 0
        total += count
        rows.append({"name": c.get("name", ""), "evidence_rows": count})
    return total, rows


def delivery_report_audit(report_path, artifact_dir=None, pool=None, clusters=None, write=True):
    report_path = Path(report_path)
    artifact_dir = Path(artifact_dir) if artifact_dir else report_path.parent
    reasons = []
    artifact_files = {
        "event_pool": artifact_dir / "a_share_sentiment_event_pool.json",
        "market_validation_pool": artifact_dir / "a_share_sentiment_market_validation_pool.json",
        "mandatory_sentiment_sources": artifact_dir / "a_share_sentiment_mandatory_sources_audit.json",
        "market_cross_validation": artifact_dir / "a_share_sentiment_market_cross_validation_audit.json",
        "clusters": artifact_dir / "a_share_sentiment_clusters.json",
        "report_sections": artifact_dir / "a_share_sentiment_report_sections.json",
        "scores": artifact_dir / "a_share_sentiment_scores.json",
        "audit": artifact_dir / "a_share_sentiment_audit.json",
        "redline": artifact_dir / "a_share_sentiment_redline_audit.json",
    }
    artifacts = _load_delivery_artifacts(artifact_dir)
    report_text = ""
    doc_profile = {"paragraphs": 0, "tables": 0, "table_shapes": []}
    try:
        report_text, doc = docx_visible_text(report_path)
        doc_profile = {
            "paragraphs": len(doc.paragraphs),
            "tables": len(doc.tables),
            "table_shapes": [[len(table.rows), len(table.columns)] for table in doc.tables],
        }
    except Exception as exc:
        reasons.append(f"docx_read_error={type(exc).__name__}:{exc}")
    try:
        locked_profile = template_profile(LOCKED_TEMPLATE)
    except Exception as exc:
        locked_profile = {"path": str(LOCKED_TEMPLATE), "error": f"{type(exc).__name__}:{exc}"}
        reasons.append(f"locked_template_read_error={type(exc).__name__}:{exc}")
    else:
        if locked_profile.get("sha256") != LOCKED_TEMPLATE_SHA256:
            reasons.append(f"locked_template_sha256_mismatch={locked_profile.get('sha256', '')}")
        if (
            locked_profile.get("paragraphs") != LOCKED_TEMPLATE_PARAGRAPHS
            or locked_profile.get("tables") != LOCKED_TEMPLATE_TABLES
            or locked_profile.get("table_shapes") != LOCKED_TEMPLATE_SHAPES
        ):
            reasons.append("locked_template_structure_mismatch")
    if doc_profile["paragraphs"] != OUTPUT_PARAGRAPHS:
        reasons.append(f"report_paragraph_count={doc_profile['paragraphs']} expected={OUTPUT_PARAGRAPHS}")
    if doc_profile["tables"] != OUTPUT_TABLES:
        reasons.append(f"report_table_count={doc_profile['tables']} expected={OUTPUT_TABLES}")
    if doc_profile["table_shapes"] != LOCKED_TEMPLATE_SHAPES:
        reasons.append("report_table_shapes_mismatch")
    banned_hits = sorted({term for term in DELIVERY_NOISE_TERMS if term and term in report_text})
    banned_hits = sorted(set(banned_hits + report_banned_phrase_hits(report_text)))
    if banned_hits:
        reasons.append("banned_delivery_terms=" + ",".join(banned_hits[:20]))

    missing_platform_names = [
        name for name in REQUIRED_SENTIMENT_SOURCES if name not in report_text
    ]
    if missing_platform_names:
        reasons.append(
            "mandatory_sentiment_source_names_missing_from_report="
            + ",".join(missing_platform_names)
        )

    missing_artifacts = [name for name, path in artifact_files.items() if not path.exists()]
    if missing_artifacts:
        reasons.append("missing_current_run_artifacts=" + ",".join(missing_artifacts))

    artifact_profiles = {name: file_profile(path) for name, path in artifact_files.items()}
    report_profile = file_profile(report_path)
    if report_profile.get("exists"):
        report_mtime = report_path.stat().st_mtime
        stale_inputs = [
            name for name, path in artifact_files.items()
            if path.exists() and path.stat().st_mtime - report_mtime > 2
        ]
        if stale_inputs:
            reasons.append("report_older_than_current_artifacts=" + ",".join(stale_inputs))

    if pool is not None:
        effective_pool = pool
    else:
        effective_pool = (artifacts.get("event_pool") or []) + (artifacts.get("market_validation_pool") or [])
    if not isinstance(effective_pool, list):
        effective_pool = []
    effective_primary_pool = primary_events(effective_pool)
    effective_primary_layers = primary_source_layer_counts(effective_pool)
    missing_primary_layers = sorted(REQUIRED_PRIMARY_SOURCE_LAYERS - set(effective_primary_layers))
    if missing_primary_layers:
        reasons.append("missing_primary_source_layers=" + ",".join(missing_primary_layers))
    if len(effective_primary_pool) < 80:
        reasons.append(f"primary_event_pool_too_small={len(effective_primary_pool)}")
    market_width = parse_width_fact(effective_primary_pool)
    if not market_width:
        reasons.append("verified_market_breadth_missing")
    effective_clusters = clusters if clusters is not None else (artifacts.get("report_sections") or artifacts.get("clusters"))
    if not isinstance(effective_clusters, list):
        effective_clusters = []
    industry_clusters = [
        cluster for cluster in effective_clusters
        if isinstance(cluster, dict)
        and cluster.get("causal_method") == "event_text_exact_theme_role_chain_v1"
    ]
    if len(industry_clusters) < MIN_REPORT_CAUSAL_CHAINS:
        reasons.append(f"insufficient_industry_causal_clusters={len(industry_clusters)}")

    causal_quality_rows = []
    for cluster in effective_clusters[:5]:
        if clusters is not None:
            quality = causal_chain_quality(cluster)
        else:
            quality = cluster.get("causal_quality") or {}
        causal_quality_rows.append({"name": cluster.get("name", ""), "quality": quality})
        if cluster.get("causal_method") not in ALLOWED_CAUSAL_METHODS:
            reasons.append(f"causal_method_invalid={cluster.get('name', '')}")
        if not quality.get("ready"):
            reasons.append(f"causal_chain_not_ready={cluster.get('name', '')}")
        stance = cluster.get("stance", quality.get("stance", ""))
        computed_stance = quality.get("computed_stance", "")
        if (
            stance not in ALLOWED_CAUSAL_STANCES
            or computed_stance not in ALLOWED_CAUSAL_STANCES
            or stance != computed_stance
            or not quality.get("stance_ready")
        ):
            reasons.append(
                f"causal_stance_invalid_or_mismatched={cluster.get('name', '')}:{stance}:{computed_stance}"
            )
        evidence_items = select_evidence(cluster, 10) if clusters is not None else (cluster.get("evidence") or [])
        evidence_keys = [_event_identity(item) for item in evidence_items]
        if len(evidence_keys) != len(set(evidence_keys)):
            reasons.append(f"duplicate_evidence={cluster.get('name', '')}")
        if any(
            not _causal_item_theme_grounded(cluster.get("name", ""), item)
            for item in evidence_items
        ):
            reasons.append(f"ungrounded_evidence={cluster.get('name', '')}")

    event_pool_ui_noise_hits = set()
    for item in effective_pool:
        if not isinstance(item, dict):
            continue
        event = str(item.get("event", ""))
        event_pool_ui_noise_hits.update(social_ui_noise_hits(event))
    event_pool_ui_noise_hits = sorted(event_pool_ui_noise_hits)
    if event_pool_ui_noise_hits:
        reasons.append("event_pool_ui_noise=" + ",".join(event_pool_ui_noise_hits[:20]))

    event_pool_for_audit = [
        item for item in effective_pool
        if isinstance(item, dict) and item.get("window_type") == EVENT_WINDOW_TYPE
    ]
    market_pool_for_audit = [
        item for item in effective_pool
        if isinstance(item, dict)
        and item.get("window_type") == MARKET_VALIDATION_WINDOW_TYPE
    ]
    mandatory_sources = (
        mandatory_sentiment_source_audit(event_pool_for_audit)
        if pool is not None
        else artifacts.get("mandatory_sentiment_sources")
    ) or {}
    market_cross_validation = (
        market_cross_validation_audit(market_pool_for_audit)
        if pool is not None
        else artifacts.get("market_cross_validation")
    ) or {}
    if not mandatory_sources.get("ok"):
        reasons.append(
            "mandatory_sentiment_sources_not_ok="
            + ",".join(mandatory_sources.get("reasons", [])[:8])
        )
    if not market_cross_validation.get("ok"):
        reasons.append(
            "market_cross_validation_not_ok="
            + ",".join(market_cross_validation.get("reasons", [])[:8])
        )
    short_term_sentiment = short_term_sentiment_assessment(
        effective_primary_pool,
        effective_clusters,
    )
    if short_term_sentiment.get("label") not in {
        "强势",
        "偏强",
        "中性分化",
        "偏弱",
        "退潮",
    }:
        reasons.append("short_term_sentiment_label_invalid")
    if "短线情绪判断：" not in report_text:
        reasons.append("short_term_sentiment_conclusion_missing")
    if not short_term_sentiment.get("dimension_gate_passed"):
        missing_dimensions = [
            key
            for key, row in (short_term_sentiment.get("dimensions") or {}).items()
            if row.get("status") != "verified"
        ]
        reasons.append(
            "short_term_sentiment_dimensions_incomplete="
            + ",".join(missing_dimensions)
        )
    for required_term in ("五维事实：", "涨停家数：", "连板晋级：", "热点扩散：", "成交额：", "市场宽度：", "置信度：", "冲突说明："):
        if required_term not in report_text:
            reasons.append(f"short_term_sentiment_report_field_missing={required_term}")

    cluster_names = _cluster_names_from_artifacts(effective_clusters)
    missing_cluster_names = [name for name in cluster_names[:5] if name and name not in report_text]
    if missing_cluster_names:
        reasons.append("cluster_names_missing_from_report=" + ",".join(missing_cluster_names))

    evidence_rows_total, evidence_rows_by_cluster = _evidence_rows_from_artifacts(effective_clusters)
    if clusters is not None:
        evidence_rows_by_cluster = []
        evidence_rows_total = 0
        for c in clusters[:5]:
            count = len(select_evidence(c, 10))
            evidence_rows_total += count
            evidence_rows_by_cluster.append({"name": c.get("name", ""), "evidence_rows": count})
    weak_evidence_tables = [row for row in evidence_rows_by_cluster if row.get("evidence_rows", 0) < 3]
    if weak_evidence_tables:
        reasons.append(f"evidence_rows_lt_3={weak_evidence_tables}")
    if evidence_rows_total < len(effective_clusters) * 3:
        reasons.append(f"evidence_rows_below_causal_minimum={evidence_rows_total}")

    redline = artifacts.get("redline")
    if isinstance(redline, dict) and not redline.get("ok", False):
        reasons.append("redline_audit_not_ok=" + ",".join(redline.get("reasons", [])[:8]))
    elif redline is None and pool is None:
        reasons.append("redline_audit_missing")

    audit = {
        "ok": not reasons,
        "skill": ROOT.name,
        "audit_type": "delivery_dynamic_conclusion_gate",
        "report": report_profile,
        "doc_profile": doc_profile,
        "locked_template_profile": locked_profile,
        "artifact_dir": str(artifact_dir),
        "artifacts": artifact_profiles,
        "primary_event_pool_count": len(effective_primary_pool),
        "primary_source_layer_counts": dict(sorted(effective_primary_layers.items())),
        "required_primary_source_layers": sorted(REQUIRED_PRIMARY_SOURCE_LAYERS),
        "market_width": market_width,
        "mandatory_sentiment_role": "required_unified_event_pool_and_sentiment_analysis_input",
        "mandatory_sentiment_sources": mandatory_sources,
        "market_cross_validation": market_cross_validation,
        "short_term_sentiment": short_term_sentiment,
        "mandatory_sentiment_sources_in_report": {
            name: name in report_text for name in REQUIRED_SENTIMENT_SOURCES
        },
        "missing_mandatory_sentiment_source_names_in_report": missing_platform_names,
        "banned_phrase_hits": banned_hits,
        "event_pool_ui_noise_hits": event_pool_ui_noise_hits,
        "cluster_names": cluster_names[:8],
        "report_section_count_for_delivery": len(effective_clusters),
        "cluster_names_in_report": {name: (name in report_text) for name in cluster_names[:8]},
        "evidence_rows_total": evidence_rows_total,
        "evidence_rows_by_cluster": evidence_rows_by_cluster,
        "causal_methods_allowed": sorted(ALLOWED_CAUSAL_METHODS),
        "causal_stances_allowed": sorted(ALLOWED_CAUSAL_STANCES),
        "minimum_industry_causal_chains": MIN_REPORT_CAUSAL_CHAINS,
        "causal_quality": causal_quality_rows,
        "reasons": reasons,
    }
    if write:
        write_json_text(artifact_dir / "a_share_sentiment_delivery_audit.json", audit)
    return audit


def _expected_recent_window_dates():
    return recent_trading_dates()


def _today_ymd():
    return _china_datetime().strftime("%Y%m%d")


def _expected_review_ymd():
    now = _china_datetime()
    anchor = now.date()
    # A 股当日复盘闭环通常在收盘后生成；16:00 前使用上一交易日锚点。
    if now.hour < 16:
        anchor = anchor - timedelta(days=1)
    while anchor.weekday() >= 5:
        anchor = anchor - timedelta(days=1)
    return anchor.strftime("%Y%m%d")


FALLBACK_LABEL_NAMES = {
    "交易新规 / 指数宽度 / 风险偏好",
    "业绩预告 / 中报预喜 / 资金再定价",
    "风险公告 / 异动监管 / 高位退潮",
    "涨停扩散 / 龙虎榜 / 情绪博弈",
    "交易制度 / 盘后定价 / 退市约束",
}

def _is_fallback_label(name):
    compact = re.sub(r"\s+", "", name or "")
    for banned in FALLBACK_LABEL_NAMES:
        if re.sub(r"\s+", "", banned) == compact:
            return True
    return False


def _is_preset_or_generic_label(name):
    tokens = [x.strip() for x in re.split(r"[/、\s]+", name or "") if x.strip()]
    if not tokens:
        return True
    generic_count = sum(1 for token in tokens if token in GENERIC_LABEL_WORDS)
    if generic_count >= max(1, len(tokens) // 2 + 1):
        return True
    return False


def _single_stock_trade_feedback_share(cluster, limit=10):
    evidence = select_evidence(cluster, limit)
    if not evidence:
        return 1.0, 0
    bad = sum(1 for item in evidence if is_single_stock_trade_feedback(item))
    return bad / max(1, len(evidence)), len(evidence)


def _redline_hard_gate_ok(pool, clusters, *, review_dir=None, review_ymd=None):
    if review_dir is None or review_ymd is None:
        review_dir, review_ymd = latest_local_review_dir()
    reasons = []
    now = _china_datetime()
    event_window_start, event_window_end = event_window_bounds(now)
    today = _today_ymd()
    window = [cn_date(d) for d in recent_trading_dates(now)]
    expected_window = [cn_date(d) for d in _expected_recent_window_dates()]
    expected_ymd = _expected_review_ymd()
    if review_ymd != expected_ymd:
        reasons.append(f"latest_local_review_ymd={review_ymd!r} expected={expected_ymd!r}")
    if set(expected_window) - set(window):
        reasons.append(f"recent_window={window} missing={sorted(set(expected_window) - set(window))}")
    acquisition_audit = acquisition_query_audit()
    if not acquisition_audit["ok"]:
        reasons.append(f"acquisition_query_audit_failed={acquisition_audit['reasons']}")
    primary_pool = primary_events(pool)
    event_pool = [item for item in pool if item.get("window_type") == EVENT_WINDOW_TYPE]
    market_validation_pool = [item for item in pool if item.get("window_type") == MARKET_VALIDATION_WINDOW_TYPE]
    invalid_event_window_items = [item for item in event_pool if not _is_current_event(item, now)]
    invalid_market_window_items = [item for item in market_validation_pool if not _is_market_validation_event(item, now)]
    unclassified_window_items = [item for item in pool if item.get("window_type") not in {EVENT_WINDOW_TYPE, MARKET_VALIDATION_WINDOW_TYPE}]
    if invalid_event_window_items:
        reasons.append(f"event_items_outside_strict_72h={len(invalid_event_window_items)}")
    if invalid_market_window_items:
        reasons.append(f"market_validation_items_outside_three_trading_days={len(invalid_market_window_items)}")
    if unclassified_window_items:
        reasons.append(f"unclassified_window_items={len(unclassified_window_items)}")
    if len(primary_events(event_pool)) < 30:
        reasons.append(f"strict_72h_primary_event_pool_too_small={len(primary_events(event_pool))}")
    layer_counts = primary_source_layer_counts(pool)
    present_layers = set(layer_counts)
    required_layers = REQUIRED_PRIMARY_SOURCE_LAYERS
    missing_required = sorted(required_layers - present_layers)
    if missing_required:
        reasons.append(f"missing_primary_source_layers={missing_required} present={sorted(present_layers)}")
    if len(primary_pool) < 80:
        reasons.append(f"primary_event_pool_too_small={len(primary_pool)}")
    width = parse_width_fact(primary_pool)
    if not width:
        reasons.append("verified_market_breadth_missing")
    if len(clusters) < MIN_REPORT_CAUSAL_CHAINS:
        reasons.append(f"insufficient_causal_clusters={len(clusters)}")
    mandatory_sources = mandatory_sentiment_source_audit(event_pool, now)
    if not mandatory_sources["ok"]:
        reasons.extend(
            f"mandatory_sentiment_source:{reason}"
            for reason in mandatory_sources["reasons"]
        )
    market_cross_validation = market_cross_validation_audit(market_validation_pool)
    if not market_cross_validation["ok"]:
        reasons.extend(
            f"market_cross_validation:{reason}"
            for reason in market_cross_validation["reasons"]
        )
    fallback_hits = [c["name"] for c in clusters if _is_fallback_label(c.get("name", ""))]
    if fallback_hits:
        reasons.append(f"fallback_label_clusters={fallback_hits}")
    preset_hits = [c["name"] for c in clusters if _is_preset_or_generic_label(c.get("name", ""))]
    if preset_hits:
        reasons.append(f"preset_or_generic_label_clusters={preset_hits}")
    bad_labels = [c["name"] for c in clusters if not causal_label_is_clean(c.get("name", ""))]
    if bad_labels:
        reasons.append(f"noisy_cluster_labels={bad_labels}")
    weak_evidence = []
    heavy_single_stock = []
    no_direction_level = []
    broken_causal_chains = []
    duplicate_evidence = []
    score_mismatches = []
    for c in clusters[:5]:
        evidence_count = len(select_evidence(c, 10))
        if evidence_count < MIN_CLUSTER_SOURCES:
            weak_evidence.append(f"{c['name']}(evidence={evidence_count})")
        share, _ev_total = _single_stock_trade_feedback_share(c, 10)
        if share > 0.30:
            heavy_single_stock.append(f"{c['name']}(single_stock_share={share:.0%})")
        quality = c.get("direction_quality") or _causal_direction_quality(c.get("items", []))
        if not quality["is_direction_level"]:
            no_direction_level.append(f"{c['name']}(stocks={quality['stock_count']} non_stock={quality['non_stock_events']})")
        causal_quality = causal_chain_quality(c)
        if c.get("causal_method") not in ALLOWED_CAUSAL_METHODS or not causal_quality["ready"]:
            broken_causal_chains.append({"name": c.get("name", ""), "quality": causal_quality})
        evidence_keys = [_event_identity(item) for item in select_evidence(c, 10)]
        if len(evidence_keys) != len(set(evidence_keys)):
            duplicate_evidence.append(c.get("name", ""))
        if c.get("score") != score_breakdown(c).get("total"):
            score_mismatches.append({"name": c.get("name", ""), "cluster_score": c.get("score"), "breakdown_total": score_breakdown(c).get("total")})
    if weak_evidence:
        reasons.append(f"weak_evidence_clusters={weak_evidence}")
    if heavy_single_stock:
        reasons.append(f"single_stock_trade_feedback_dominant={heavy_single_stock}")
    if no_direction_level:
        reasons.append(f"non_direction_level_clusters={no_direction_level}")
    if broken_causal_chains:
        reasons.append(f"broken_causal_chains={broken_causal_chains}")
    if duplicate_evidence:
        reasons.append(f"duplicate_evidence_clusters={duplicate_evidence}")
    if score_mismatches:
        reasons.append(f"score_breakdown_mismatches={score_mismatches}")
    return {
        "ok": not reasons,
        "reasons": reasons,
        "review_ymd": review_ymd,
        "expected_ymd": expected_ymd,
        "event_window_hours": EVENT_WINDOW_HOURS,
        "event_window_start": event_window_start.isoformat(timespec="seconds"),
        "event_window_end": event_window_end.isoformat(timespec="seconds"),
        "event_window_calendar_dates": [cn_date(day) for day in event_window_calendar_dates(now)],
        "strict_72h_event_pool_count": len(event_pool),
        "market_validation_window": window,
        "expected_market_validation_window": expected_window,
        "market_validation_pool_count": len(market_validation_pool),
        "source_layer_counts": dict(sorted(layer_counts.items())),
        "primary_event_pool_count": len(primary_pool),
        "mandatory_sentiment_sources": mandatory_sources,
        "market_cross_validation": market_cross_validation,
        "event_pool_count": len(pool),
        "cluster_count": len(clusters),
        "market_width": width,
        "acquisition_query_audit": acquisition_audit,
        "causal_method_required": "event_text_exact_theme_role_chain_v1",
        "causal_cluster_quality": [causal_chain_quality(c) for c in clusters[:5]],
    }


def generate(args):
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    acquisition_preflight = ensure_public_readonly_capture(out_dir)
    write_json_text(
        out_dir / "a_share_sentiment_acquisition_preflight.json",
        acquisition_preflight,
    )
    template_profile = verify_locked_template()
    if template_profile is None:
        return 2
    out_path = out_dir / "A股三日舆情解读结果_Codex自动生成.docx"
    raw_event_path = out_dir / "a_share_sentiment_raw_event_pool.json"
    event_path = out_dir / "a_share_sentiment_event_pool.json"
    unified_event_path = out_dir / "a_share_sentiment_unified_event_pool.json"
    market_validation_path = out_dir / "a_share_sentiment_market_validation_pool.json"
    mandatory_sources_path = out_dir / "a_share_sentiment_mandatory_sources_audit.json"
    market_cross_validation_path = out_dir / "a_share_sentiment_market_cross_validation_audit.json"
    cluster_path = out_dir / "a_share_sentiment_clusters.json"
    acquisition_audit = acquisition_query_audit()
    acquisition_path = out_dir / "a_share_sentiment_acquisition_audit.json"
    write_json_text(acquisition_path, acquisition_audit)
    if not acquisition_audit["ok"]:
        print("BLOCKED acquisition query audit failed")
        return 2
    event_pool = collect_event_pool()
    market_validation_pool = collect_market_validation_pool()
    write_json_text(raw_event_path, event_pool)
    write_json_text(market_validation_path, market_validation_pool)
    mandatory_sources_audit = mandatory_sentiment_source_audit(event_pool)
    write_json_text(mandatory_sources_path, mandatory_sources_audit)
    if not mandatory_sources_audit["ok"]:
        redline = {
            "ok": False,
            "reasons": mandatory_sources_audit["reasons"],
            "mandatory_sources_audit": mandatory_sources_audit,
        }
        write_json_text(out_dir / "a_share_sentiment_redline_audit.json", redline)
        print("BLOCKED mandatory eight-site sentiment source audit failed:")
        for reason in mandatory_sources_audit["reasons"]:
            print(f"  - {reason}")
        return 2
    market_cross_validation = market_cross_validation_audit(market_validation_pool)
    write_json_text(market_cross_validation_path, market_cross_validation)
    if not market_cross_validation["ok"]:
        redline = {
            "ok": False,
            "reasons": market_cross_validation["reasons"],
            "market_cross_validation_audit": market_cross_validation,
        }
        write_json_text(out_dir / "a_share_sentiment_redline_audit.json", redline)
        print("BLOCKED Lianban/Tongdaxin/Duanxianxia cross-validation audit failed:")
        for reason in market_cross_validation["reasons"]:
            print(f"  - {reason}")
        return 2
    capture_dir_value = os.environ.get(CHROME_CAPTURE_ENV, "").strip()
    try:
        integration = load_integration_runtime().integrate(
            event_pool,
            market_validation_pool,
            capture_dir_value,
            _china_datetime(),
        )
    except Exception as exc:
        integration_failure = {
            "schema": "A_SHARE_SENTIMENT_INTEGRATION_V1",
            "ok": False,
            "reasons": [f"{type(exc).__name__}:{exc}"],
            "runtime": str(INTEGRATION_RUNTIME),
        }
        write_json_text(out_dir / "a_share_sentiment_source_integration_audit.json", integration_failure)
        write_json_text(out_dir / "a_share_sentiment_redline_audit.json", integration_failure)
        print(f"BLOCKED optimized source integration failed: {type(exc).__name__}:{exc}")
        return 2
    event_pool = integration["event_pool"]
    market_validation_pool = integration["market_pool"]
    integration_audit = integration["audit"]
    write_json_text(event_path, event_pool)
    write_json_text(unified_event_path, event_pool)
    write_json_text(market_validation_path, market_validation_pool)
    write_json_text(out_dir / "a_share_sentiment_source_integration_audit.json", integration_audit)
    write_json_text(out_dir / "a_share_sentiment_daily_intel_view.json", integration["daily_intel_view"])
    write_json_text(out_dir / "a_share_sentiment_conflict_register.json", integration["conflict_register"])
    if not integration_audit.get("ok"):
        write_json_text(out_dir / "a_share_sentiment_redline_audit.json", integration_audit)
        print("BLOCKED source integration audit failed")
        return 2
    pool = event_pool + market_validation_pool
    primary_pool = primary_events(pool)
    if not parse_width_fact(primary_pool):
        redline = {"ok": False, "reasons": ["verified_market_breadth_missing"], "event_pool_count": len(pool)}
        write_json_text(out_dir / "a_share_sentiment_redline_audit.json", redline)
        print("BLOCKED verified market breadth missing")
        return 2
    clusters = cluster_and_score(primary_pool)
    review_dir, review_ymd = latest_local_review_dir()
    redline = _redline_hard_gate_ok(pool, clusters, review_dir=review_dir, review_ymd=review_ymd)
    write_json_text(out_dir / "a_share_sentiment_redline_audit.json", redline)
    if not redline["ok"]:
        print("BLOCKED redline hard gate failed:")
        for r in redline["reasons"]:
            print(f"  - {r}")
        print(f"redline_audit={out_dir / 'a_share_sentiment_redline_audit.json'}")
        return 2
    source_count = len(items_evidence_sources(primary_pool))
    strict_event_primary_count = len(primary_events(event_pool))
    ready_industry_clusters = [
        c for c in clusters
        if c.get("causal_method") == "event_text_exact_theme_role_chain_v1"
        and causal_chain_quality(c)["ready"]
    ]
    if strict_event_primary_count < 30 or len(primary_pool) < 80 or source_count < 6 or len(ready_industry_clusters) < MIN_REPORT_CAUSAL_CHAINS:
        print(
            "BLOCKED insufficient automatic inputs: "
            f"strict_72h_primary_events={strict_event_primary_count} "
            f"combined_primary_evidence={len(primary_pool)} sources={source_count} "
            f"industry_causal_chains={len(ready_industry_clusters)}"
        )
        return 2
    preset_bias = [c["name"] for c in clusters if has_preset_board_bias(c)]
    if preset_bias:
        print("BLOCKED preset-board bias detected: " + " | ".join(preset_bias))
        return 2
    bad_labels = [
        c["name"] for c in clusters
        if not causal_label_is_clean(c["name"])
        or any(term.lower() in c["name"].lower() for term in FORBIDDEN_TERMS)
        or any(term in c["name"] for term in ["责任编辑", "时报网", "客户端", "更多", "动态"])
    ]
    if bad_labels:
        print("BLOCKED noisy cluster labels: " + " | ".join(bad_labels))
        return 2
    weak_source_clusters = [
        f"{c['name']}({len(c['sources'])} sources/{evidence_source_count(c, 10)} evidence sources)"
        for c in clusters[:5]
        if not has_multi_source_evidence(c, 10)
    ]
    if weak_source_clusters:
        print("BLOCKED single-source or weak-source evidence clusters: " + " | ".join(weak_source_clusters))
        return 2
    weak_delivery = [
        q for q in [evidence_delivery_quality(c, 10) for c in clusters[:5]]
        if not q["is_delivery_ready"]
    ]
    if weak_delivery:
        print("BLOCKED weak direction-level evidence in delivery tables:")
        for item in weak_delivery:
            dq = item["direction_quality"]
            print(
                f"{item['direction']}: sources={item['source_count']} layers={','.join(item['source_layers'])} "
                f"stocks={dq['stock_count']} non_stock_events={dq['non_stock_events']}"
            )
        return 2
    report_clusters = (
        ready_industry_clusters
        + [c for c in clusters if c not in ready_industry_clusters and causal_chain_quality(c)["ready"]]
    )[:5]
    if len(ready_industry_clusters) < MIN_REPORT_CAUSAL_CHAINS:
        print("BLOCKED insufficient independently evidenced industry causal chains")
        print("cluster_candidates=" + " | ".join(
            f"{c.get('name', '')}({len(c.get('items', []))} events/{len(c.get('sources', []))} sources)"
            for c in clusters
        ))
        return 2
    integrated_short_term_sentiment = short_term_sentiment_assessment(primary_pool, report_clusters)
    short_term_view = {
        "schema": "A_SHARE_SHORT_TERM_SENTIMENT_DERIVED_VIEW_V1",
        "rule": "统一市场验证池派生两层周期结论；保留冲突，不生成加权总分",
        **integrated_short_term_sentiment,
    }
    write_json_text(out_dir / "a_share_sentiment_short_term_sentiment_view.json", short_term_view)
    integration_audit["derived_view_checks"] = {
        "daily_intel_view": True,
        "short_term_market_sentiment_view": bool(
            integrated_short_term_sentiment.get("intermediate_cycle")
            and integrated_short_term_sentiment.get("short_term_stage")
            and integrated_short_term_sentiment.get("conflict_statement")
            and integrated_short_term_sentiment.get("weighted_total_score") is None
        ),
    }
    integration_audit["ok"] = all(integration_audit["derived_view_checks"].values())
    write_json_text(out_dir / "a_share_sentiment_source_integration_audit.json", integration_audit)
    if not integration_audit["ok"]:
        print("BLOCKED derived source view audit failed")
        return 2
    write_json_text(out_dir / "a_share_sentiment_report_sections.json", [
        {
            "name": c["name"],
            "score": c.get("score"),
            "events": len(c.get("items", [])),
            "sources": sorted(c.get("sources", [])),
            "source_layers": sorted(source_layers(c.get("sources", []))),
            "causal_method": c.get("causal_method", ""),
            "stance": c.get("stance", ""),
            "causal": c.get("causal", {}),
            "causal_quality": causal_chain_quality(c),
            "delivery_quality": evidence_delivery_quality(c, 10),
        }
        for c in report_clusters
    ])
    write_json_text(cluster_path, [
        {
            "name": c["name"],
            "score": c["score"],
            "events": len(c["items"]),
            "sources": sorted(c["sources"]),
            "source_layers": sorted(source_layers(c["sources"])),
            "direction_quality": c.get("direction_quality", _causal_direction_quality(c.get("items", []))),
            "causal_method": c.get("causal_method", ""),
            "stance": c.get("stance", ""),
            "causal": c.get("causal", {}),
            "causal_quality": causal_chain_quality(c),
            "evidence": [
                {
                    "source": item.get("source", ""),
                    "date": item.get("date", ""),
                    "event": item.get("event", ""),
                    "causal_context": item.get("causal_context", ""),
                    "causal_roles": item.get("causal_roles", []),
                    "causal_polarity": item.get("causal_polarity", "neutral"),
                    "meaning": item.get("meaning", ""),
                }
                for item in select_evidence(c, 10)
            ],
            "delivery_quality": evidence_delivery_quality(c, 10),
        }
        for c in clusters
    ])
    write_audit_files(out_dir, pool, clusters)
    build_report(report_clusters, out_path, pool, integrated_short_term_sentiment)
    skeleton_code = verify_output_skeleton(out_path)
    if skeleton_code != 0:
        return skeleton_code
    delivery_audit = delivery_report_audit(out_path, artifact_dir=out_dir, pool=pool, clusters=report_clusters, write=True)
    if not delivery_audit.get("ok"):
        print("BLOCKED delivery dynamic conclusion audit failed:")
        for reason in delivery_audit.get("reasons", []):
            print(f"  - {reason}")
        print(f"delivery_audit={out_dir / 'a_share_sentiment_delivery_audit.json'}")
        return 2
    scan_args = argparse.Namespace(path=str(out_path), artifact_dir=str(out_dir))
    code = scan_docx(scan_args)
    if code != 0:
        return code
    try:
        word_render_audit = run_word_render_validation(out_path, out_dir)
    except RuntimeError as exc:
        print(str(exc))
        return 2
    print(f"event_pool={event_path}")
    print(f"unified_event_pool={unified_event_path}")
    print(f"source_integration_audit={out_dir / 'a_share_sentiment_source_integration_audit.json'}")
    print(f"market_validation_pool={market_validation_path}")
    print(f"clusters={cluster_path}")
    print(f"scores={out_dir / 'a_share_sentiment_scores.json'}")
    print(f"audit={out_dir / 'a_share_sentiment_audit.json'}")
    print(f"delivery_audit={out_dir / 'a_share_sentiment_delivery_audit.json'}")
    print(f"word_render_audit={out_dir / 'a_share_sentiment_word_render_audit.json'}")
    print(f"word_pages={word_render_audit.get('page_count', 0)}")
    print(f"report={out_path}")
    return 0


def _scientific_canary_failures():
    failures = []
    now = _china_datetime()
    market_date_text = cn_date(recent_trading_dates(now)[-1])
    width_market_date_text = cn_date(_market_width_anchor_date(now))
    current_publication = now - timedelta(hours=6)
    event_date_text = cn_date(current_publication.date())
    theme = "量子玻璃"
    event_base = {
        "date": event_date_text,
        "published_at": current_publication.isoformat(timespec="seconds"),
        "time_precision": "minute",
        "time_evidence": "canary_timestamp",
        "window_type": EVENT_WINDOW_TYPE,
        "source_channel": "canary",
    }
    market_base = {
        "date": market_date_text,
        "market_date": market_date_text,
        "window_type": MARKET_VALIDATION_WINDOW_TYPE,
        "source_channel": "canary",
    }
    good_pool = [
        dict(event_base, source="主流财经", event=f"{theme}产业链订单增长，供需改善并改变盈利预期。"),
        dict(event_base, source="交易所公告", event=f"{theme}产业链关键材料许可落地，新增产能改变供给预期。"),
        dict(event_base, source="港股市场", event=f"{theme}产业链订单扩张，需求增长并带动盈利预期。"),
        dict(market_base, source="交易复盘", event=f"{theme}板块走强并出现涨停扩散，成交额同步放大。"),
        dict(market_base, source="融资数据", event=f"{theme}板块融资资金参与度上升，主力净流入增加。"),
    ]
    good_clusters = cluster_and_score(good_pool)
    good = next((cluster for cluster in good_clusters if cluster.get("name") == theme), None)
    if not good or not causal_chain_quality(good)["ready"]:
        failures.append("valid_causal_chain_rejected")
    elif len(select_evidence(good, 10)) < 3 or len({_event_identity(item) for item in select_evidence(good, 10)}) != len(select_evidence(good, 10)):
        failures.append("valid_causal_evidence_not_unique")
    else:
        if good.get("score") != score_breakdown(good).get("total"):
            failures.append("cluster_score_breakdown_mismatch")
        main_item = next((item for item in good["items"] if item.get("source") == "主流财经"), {})
        trade_item = next((item for item in good["items"] if item.get("source") == "交易复盘"), {})
        institution_item = next((item for item in good["items"] if item.get("source") == "融资数据"), {})
        if main_item.get("causal_roles") != ["catalyst"]:
            failures.append("catalyst_improperly_doubles_as_market_confirmation")
        if "market" not in trade_item.get("causal_roles", []) or "participant" not in institution_item.get("causal_roles", []):
            failures.append("causal_roles_not_bound_to_trade_and_institution_layers")
        if good.get("stance") != "增强":
            failures.append("positive_market_stance_not_enhanced")

    normalized_five_site_sources = {
        _canonical_chrome_capture_source(
            f"{stem}.json",
            {"site": "污染站点名"},
            {"label": "被正文污染的内容标签"},
        )[0]
        for stem in FIVE_SITE_CAPTURE_FILES
    }
    if normalized_five_site_sources != set(REQUIRED_SOCIAL_PLATFORMS):
        failures.append("five_site_capture_filename_source_normalization_failed")
    if _canonical_chrome_capture_source(
        "tgb.json",
        {"site": "污染站点名"},
        {"label": "被正文污染的内容标签"},
    )[1] != "被正文污染的内容标签":
        failures.append("five_site_capture_origin_label_not_preserved")

    structured_industry = f"风范股份涨停，所属行业为{theme}，涨幅10%，封板资金充足。"
    structured_concept = f"四方股份龙虎榜上榜，所属概念为{theme}，机构净买额增加。"
    if theme not in _structured_causal_terms(structured_industry):
        failures.append("structured_industry_theme_not_extracted")
    if theme not in _structured_causal_terms(structured_concept):
        failures.append("structured_concept_theme_not_extracted")

    stock_market_items = [
        dict(market_base, source="涨停复盘", event=f"风范股份涨停，所属行业为{theme}，涨幅10%，封板资金充足。"),
        dict(market_base, source="龙虎榜", event=f"四方股份龙虎榜上榜，所属概念为{theme}，净买额增加并封板。"),
        dict(market_base, source="交易复盘", event=f"顺钠股份涨停，所属环节为{theme}，形成连板并维持涨幅。"),
    ]
    structured_pool = [
        dict(event_base, source="主流财经", event=f"资本增持计划落地，所属行业为{theme}，改变所有权结构与融资预期。"),
        *stock_market_items,
        dict(market_base, source="融资数据", event=f"{theme}融资资金净流入增加，机构参与度上升。"),
    ]
    structured_clusters = cluster_and_score(structured_pool)
    structured = next((cluster for cluster in structured_clusters if cluster.get("name") == theme), None)
    if not structured or not causal_chain_quality(structured)["ready"]:
        failures.append("three_stock_direction_level_market_confirmation_rejected")
    elif causal_chain_quality(structured)["direction_quality"].get("market_stock_count") != 3:
        failures.append("market_stock_breadth_not_recomputed")

    two_stock_pool = [structured_pool[0], *stock_market_items[:2], structured_pool[-1]]
    weak_direction_cluster = _build_causal_cluster(theme, two_stock_pool)
    if causal_chain_quality(weak_direction_cluster)["ready"]:
        failures.append("two_stock_direction_level_market_confirmation_accepted")
    forged_direction_cluster = dict(weak_direction_cluster)
    forged_direction_cluster["direction_quality"] = {
        "is_direction_level": True,
        "market_stock_count": 99,
    }
    if causal_chain_quality(forged_direction_cluster)["ready"]:
        failures.append("forged_stored_direction_quality_accepted")

    if _causal_stance([{"causal_roles": ["market"], "causal_polarity": "negative"}]) != "转弱":
        failures.append("negative_market_stance_not_weakened")
    if _causal_stance([
        {"causal_roles": ["market"], "causal_polarity": "positive"},
        {"causal_roles": ["market"], "causal_polarity": "negative"},
    ]) != "分歧":
        failures.append("mixed_market_stance_not_divergent")
    neutral_items = [{"causal_roles": ["market"], "causal_polarity": "neutral"}]
    if _causal_stance(neutral_items) != "待确认":
        failures.append("neutral_market_stance_canary_invalid")
    try:
        _causal_chain_text(theme, neutral_items, "待确认")
        failures.append("pending_causal_narrative_not_blocked")
    except RuntimeError:
        pass
    try:
        cluster_role_text({"name": theme, "stance": "待确认"})
        failures.append("pending_cluster_role_not_blocked")
    except RuntimeError:
        pass
    if good:
        mismatched = dict(good)
        mismatched["stance"] = "转弱"
        if causal_chain_quality(mismatched)["ready"]:
            failures.append("stored_computed_stance_mismatch_accepted")

    if verify_output_skeleton(LOCKED_TEMPLATE, quiet=True) != 0:
        failures.append("locked_template_output_skeleton_rejected")
    try:
        from docx import Document
        with tempfile.TemporaryDirectory(prefix="a_share_sentiment_canary_") as temp_dir:
            truncated_path = Path(temp_dir) / "truncated.docx"
            truncated_doc = Document(str(LOCKED_TEMPLATE))
            table_element = truncated_doc.tables[-1]._tbl
            table_element.getparent().remove(table_element)
            truncated_doc.save(truncated_path)
            if verify_output_skeleton(truncated_path, quiet=True) == 0:
                failures.append("truncated_docx_skeleton_accepted")
    except Exception as exc:
        failures.append(f"docx_skeleton_canary_error={type(exc).__name__}")
    banned_canary_text = "因果链待确认；本轮未形成第二条主线，因此不输出板块或个股推荐，只观察风险偏好链。"
    expected_banned = {"因果链待确认", "本轮未形成", "不输出板块", "只观察", "风险偏好链", "不输出.*推荐"}
    if not expected_banned.issubset(set(report_banned_phrase_hits(banned_canary_text))):
        failures.append("banned_report_phrase_scan_incomplete")

    no_catalyst_pool = [
        dict(event_base, source="主流财经", event=f"{theme}相关信息在盘中被提及。"),
        dict(event_base, source="交易所公告", event=f"{theme}相关信息进入公开列表。"),
        dict(event_base, source="港股市场", event=f"{theme}相关信息被市场讨论。"),
        dict(market_base, source="交易复盘", event=f"{theme}板块走强并出现涨停。"),
        dict(market_base, source="融资数据", event=f"{theme}板块融资资金参与度上升，主力净流入增加。"),
    ]
    if any(cluster.get("name") == theme for cluster in cluster_and_score(no_catalyst_pool)):
        failures.append("cooccurrence_without_catalyst_accepted")

    stale_publication = now - timedelta(hours=EVENT_WINDOW_HOURS + 1)
    stale_pool = [
        dict(
            item,
            date=cn_date(stale_publication.date()),
            published_at=stale_publication.isoformat(timespec="seconds"),
        ) if item.get("window_type") == EVENT_WINDOW_TYPE else dict(item)
        for item in good_pool
    ]
    if cluster_and_score(stale_pool):
        failures.append("stale_causal_chain_accepted")
    if not _is_current_event(good_pool[0], now) or _is_current_event(stale_pool[0], now):
        failures.append("strict_rolling_72h_event_gate_failed")
    _window_start, cutoff = event_window_bounds(now)
    at_cutoff = dict(
        event_base,
        date=cn_date(cutoff.date()),
        published_at=cutoff.isoformat(timespec="seconds"),
    )
    after_cutoff = dict(
        at_cutoff,
        published_at=(cutoff + timedelta(seconds=1)).isoformat(timespec="seconds"),
    )
    if not _is_current_event(at_cutoff, now) or _is_current_event(after_cutoff, now):
        failures.append("strict_event_cutoff_gate_failed")
    if _publication_record(
        cutoff + timedelta(seconds=1),
        precision="second",
        evidence="canary_after_cutoff",
        now=now,
    ) is not None:
        failures.append("publication_after_cutoff_accepted")

    one_item = dict(good_pool[0])
    one_item.update({
        "causal_context": one_item["event"],
        "causal_roles": ["catalyst"],
        "causal_variable": "供需、成本与盈利预期",
        "causal_polarity": "positive",
        "meaning": "该事实构成结论链起点。",
    })
    isolated = {
        "name": theme,
        "items": [one_item, one_item],
        "_pool": [dict(market_base, source="交易复盘", event="无关主题板块上涨。")],
        "causal_method": "event_text_exact_theme_role_chain_v1",
    }
    isolated_selected = select_evidence(isolated, 10)
    if len(isolated_selected) != 1 or any("无关主题" in item.get("event", "") for item in isolated_selected):
        failures.append("cross_theme_pool_backfill_or_duplicate")

    try:
        supplemental_report_clusters(good_pool, 1)
        failures.append("supplemental_template_filler_not_blocked")
    except RuntimeError:
        pass
    if LEGACY_CLUSTER_AND_SCORE_DISABLED is not None:
        failures.append("legacy_cluster_callable_still_exposed")
    try:
        _legacy_cluster_and_score_disabled(good_pool)
        failures.append("legacy_kmeans_path_not_blocked")
    except RuntimeError:
        pass
    try:
        _historical_collect_chrome_visible_events_disabled(datetime.now(timezone(timedelta(hours=8))))
        failures.append("manual_chrome_event_injection_not_blocked")
    except RuntimeError:
        pass
    try:
        _historical_collect_five_site_chrome_events_disabled()
        failures.append("manual_five_site_injection_not_blocked")
    except RuntimeError:
        pass
    try:
        market_width_sentence(good_pool)
        failures.append("missing_market_breadth_not_blocked")
    except RuntimeError:
        pass
    width_pool = [
        {"source": "主流财经", "date": width_market_date_text, "event": "全市场上涨家数3772、下跌家数1678，成交额34107亿元。", "url": "https://market-a.example/a"},
        {"source": "东方财富", "date": width_market_date_text, "event": "全市场3772只个股上涨、1678只下跌，成交34107亿元。", "url": "https://eastmoney.com/b"},
    ]
    width = parse_width_fact(width_pool)
    if not width or width.get("cross_source_count") != 2:
        failures.append("cross_source_market_width_rejected")
    if parse_width_fact(width_pool[:1]) is not None:
        failures.append("single_source_market_width_accepted")
    downside_pool = [
        {"source": "韭研公社", "source_key": "jiuyangongshe.com", "date": width_market_date_text, "event": "两市上涨家数3406、下跌家数1664，成交额2.23万亿元。", "url": "https://www.jiuyangongshe.com/a"},
        {"source": "韭研公社·市场复盘", "source_key": "jiuyangongshe", "date": width_market_date_text, "event": "两市上涨家数3406、下跌家数1664，成交额2.23万亿元。", "url": "https://www.jiuyangongshe.com/b"},
        {"source": "本地通达信", "source_key": "local-tdx", "date": width_market_date_text, "event": "两市约1664只个股下跌；本地通达信可比样本上涨3404只、平盘127只。", "url": "file:///C:/new_tdx_mock/vipdoc"},
    ]
    if _width_source_key({"source_key": "jiuyangongshe"}) != "jiuyangongshe.com":
        failures.append("jiuyangongshe_source_alias_not_normalized")
    downside_width = parse_width_fact(downside_pool)
    if (
        not downside_width
        or downside_width.get("cross_source_mode") != "downside_approx"
        or downside_width.get("cross_source_count") != 2
        or downside_width.get("up") != "3406"
        or downside_width.get("down") != "1664"
        or downside_width.get("source_keys") != ["jiuyangongshe.com", "local-tdx"]
    ):
        failures.append("downside_corroborated_market_width_rejected")
    sanitized_lhb = sanitize_delivery_residue("光迅科技龙虎榜上榜，所属环节为通信设备，原因为日涨幅偏离值达到7%的前5只证券，席位解读为3家机构买入，成功率29.34%，净买额424554487.06")
    if "原因为" in sanitized_lhb or "成功率" in sanitized_lhb:
        failures.append("delivery_noise_terms_not_sanitized")
    metadata_text = (
        "事件窗口：2026-08-01 23:59 至 2026-08-04 23:59；"
        "盘面验证日：7月31日、8月3日、8月4日"
    )
    if sanitize_delivery_residue(metadata_text) != metadata_text:
        failures.append("report_metadata_corrupted_by_delivery_sanitizer")
    forum_metadata_text = sanitize_delivery_residue(
        "三时三岛[早晚9点更] 2026-08-04 20:58:58 20260804复盘：科技线全面高潮"
    )
    if "三时三岛" in forum_metadata_text or "2026-08-04 20:58:58" in forum_metadata_text:
        failures.append("forum_author_timestamp_not_sanitized")
    if strip_allowed_report_metadata(metadata_text).strip():
        failures.append("report_metadata_not_exempted_from_delivery_scan")
    scan_residue = strip_allowed_report_metadata(metadata_text + " 正文验证 8-4 12:30")
    if "正文验证" not in scan_residue or "8-4 12:30" not in scan_residue:
        failures.append("report_metadata_scan_exemption_too_broad")
    conflicting_width_pool = width_pool + [
        {"source": "证券时报", "date": width_market_date_text, "event": "全市场上涨家数3600、下跌家数1800。", "url": "https://stcn.com/c"},
        {"source": "中国证券报", "date": width_market_date_text, "event": "全市场3600只个股上涨、1800只下跌。", "url": "https://cs.com.cn/d"},
    ]
    if parse_width_fact(conflicting_width_pool) is not None:
        failures.append("conflicting_market_width_groups_accepted")
    acquisition = acquisition_query_audit()
    if not acquisition["ok"] or acquisition["market_wide_term_count"] != 36:
        failures.append("market_wide_36_term_acquisition_gate_failed")
    valid_query = dynamic_search_queries()[0]
    valid_terms = [token for token in valid_query.split() if token in set(MARKET_WIDE_QUERY_TERMS)]
    metadata = {"discovery_mode": "market_wide_query", "discovery_query": valid_query, "discovery_terms": valid_terms}
    if not chrome_discovery_metadata_ok(metadata):
        failures.append("market_wide_discovery_metadata_rejected")
    invalid_metadata = dict(metadata, discovery_query=valid_query + " 某具体方向")
    if chrome_discovery_metadata_ok(invalid_metadata):
        failures.append("non_whitelisted_specific_query_term_accepted")
    return failures


def selftest(_args):
    missing = [str(p) for p in [SKILL, WORKFLOW, CHECKLIST] if not p.exists()]
    if missing:
        print("BLOCKED missing files:")
        for item in missing:
            print(item)
        return 2
    skill_text = read_text(SKILL)
    required = [
        f"name: {ROOT.name}",
        "每站不少于 10 条",
        "连板网、通达信、短线侠",
        "短线情绪判断",
        "唯一入口",
        "触发事实",
        "社区观点不能单独证明",
        "a_share_sentiment_delivery_audit.json",
    ]
    absent = [item for item in required if item not in skill_text]
    if absent:
        print("BLOCKED missing required skill text:")
        for item in absent:
            print(item)
        return 2
    workflow_text = read_text(WORKFLOW)
    jiuyangongshe_url = "https://www.jiuyangongshe.com/study_hot"
    source_contract_failures = []
    if ("韭研公社", jiuyangongshe_url) not in NATIVE_DISCOVERY_URLS:
        source_contract_failures.append("missing_jiuyangongshe_native_discovery_source")
    if source_name_from_url(jiuyangongshe_url) != "韭研公社":
        source_contract_failures.append("jiuyangongshe_domain_mapping_invalid")
    if source_layer("韭研公社") != "研究社区":
        source_contract_failures.append("jiuyangongshe_source_layer_invalid")
    if REQUIRED_SENTIMENT_SOURCES != [
        "淘股吧",
        "雪球",
        "微博",
        "知乎",
        "东方财富股吧",
        "韭研公社",
        "财联社",
        "金十数据",
    ]:
        source_contract_failures.append("mandatory_eight_site_contract_changed")
    if MANDATORY_SENTIMENT_MIN_PER_SOURCE != 10:
        source_contract_failures.append("mandatory_eight_site_minimum_changed")
    if not all(
        term in skill_text and term in workflow_text
        for term in ["韭研公社", "财联社", "金十数据", "强事实"]
    ):
        source_contract_failures.append("mandatory_eight_site_instruction_boundary_missing")
    if source_contract_failures:
        print("BLOCKED source contracts failed:")
        for item in source_contract_failures:
            print(item)
        return 2
    canary_failures = _scientific_canary_failures()
    if canary_failures:
        print("BLOCKED scientific canaries failed:")
        for item in canary_failures:
            print(item)
        return 2
    print(f"CLEAN_PASS {ROOT.name} selftest")
    print(f"skill={SKILL}")
    print(f"workflow={WORKFLOW}")
    print(f"checklist={CHECKLIST}")
    return 0


def checklist(_args):
    print(read_text(CHECKLIST))
    return 0


def five_site_profile_cmd(args):
    profile = five_site_capture_profile(getattr(args, "capture_dir", "") or None)
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    return 0 if profile.get("ok") else 2


def doctor(_args):
    template_profile = verify_locked_template()
    review_dir, review_ymd = latest_local_review_dir()
    core_stems = [
        "industry_limitup_stats",
        "limitup_lhb_intersection",
        "ak_stock_lhb_detail_em",
        "push2_fund_flow_resolved",
        "ak_stock_zt_pool_em",
    ]
    review_core_files = []
    if review_dir and review_ymd:
        review_core_files = [
            str(_review_file(review_dir, stem, review_ymd))
            for stem in core_stems
            if _review_file(review_dir, stem, review_ymd).exists()
        ]
    instruction_text = "\n".join(read_text(p) for p in [SKILL, WORKFLOW, CHECKLIST] if p.exists())
    required_instruction_terms = [
        "唯一入口",
        "三个交易日",
        "因果链",
        "36 个市场宽口径词",
        "滚动 72 小时",
        "a_share_sentiment_event_pool.json",
        "a_share_sentiment_market_validation_pool.json",
        "a_share_sentiment_mandatory_sources_audit.json",
        "a_share_sentiment_market_cross_validation_audit.json",
        "a_share_sentiment_clusters.json",
        "a_share_sentiment_scores.json",
        "a_share_sentiment_delivery_audit.json",
        "淘股吧、雪球、微博、知乎、东方财富股吧、韭研公社、财联社、金十数据",
        "每站不少于 10 条",
        "连板网、通达信、短线侠",
        "短线情绪判断",
        "BLOCKED",
    ]
    missing_instruction_terms = [term for term in required_instruction_terms if term not in instruction_text]
    stale_instruction_terms = [
        "F:\\小龙虾精品\\A股舆情解读工作流_三日重要事件版.docx",
        "793ba5957cc614257721a8032aafb8c79b92af38fbbfdbaf8e406e35fcab2bdb",
    ]
    stale_hits = [term for term in stale_instruction_terms if term in instruction_text]
    today = _today_ymd()
    expected_review_ymd = _expected_review_ymd()
    latest_ok = bool(review_ymd) and review_ymd == expected_review_ymd
    canary_failures = _scientific_canary_failures()
    acquisition_audit = acquisition_query_audit()
    ok = bool(template_profile) and len(review_core_files) >= 4 and not missing_instruction_terms and not stale_hits and latest_ok and not canary_failures and acquisition_audit["ok"]
    print(json.dumps({
        "skill": ROOT.name,
        "mode": "doctor",
        "status": "CLEAN_PASS" if ok else "BLOCKED",
        "entry": str(Path(__file__).resolve()),
        "locked_template": str(LOCKED_TEMPLATE),
        "locked_template_sha256": LOCKED_TEMPLATE_SHA256,
        "template_profile": template_profile,
        "local_trade_review_dir": str(review_dir) if review_dir else "",
        "local_trade_review_date": review_ymd,
        "today_ymd": today,
        "expected_review_ymd": expected_review_ymd,
        "latest_review_anchor_ok": latest_ok,
        "scientific_canary_failures": canary_failures,
        "acquisition_query_audit": acquisition_audit,
        "review_core_file_count": len(review_core_files),
        "event_window": acquisition_audit.get("event_window_start", "") + " -> " + acquisition_audit.get("event_window_end", ""),
        "event_window_calendar_dates": [cn_date(d) for d in event_window_calendar_dates()],
        "market_validation_trading_dates": [cn_date(d) for d in recent_trading_dates()],
        "expected_market_validation_trading_dates": [cn_date(d) for d in _expected_recent_window_dates()],
        "required_output_files": [
            "a_share_sentiment_event_pool.json",
            "a_share_sentiment_market_validation_pool.json",
            "a_share_sentiment_mandatory_sources_audit.json",
            "a_share_sentiment_market_cross_validation_audit.json",
            "a_share_sentiment_acquisition_audit.json",
            "a_share_sentiment_clusters.json",
            "a_share_sentiment_scores.json",
            "a_share_sentiment_audit.json",
            "a_share_sentiment_redline_audit.json",
            "a_share_sentiment_delivery_audit.json",
            "A股三日舆情解读结果_Codex自动生成.docx",
        ],
        "red_lines": {
            "preset_board_pool_allowed": False,
            "specific_theme_or_stock_query_allowed": False,
            "market_wide_query_term_count": 36,
            "manual_event_injection_allowed": False,
            "must_collect_event_pool_first": True,
            "strict_rolling_72h_event_timestamps_required": True,
            "three_trading_days_validation_only": True,
            "must_block_on_weak_sources_or_noise": True,
            "must_block_on_latest_data_anchor_mismatch": True,
            "must_block_on_single_stock_trade_feedback_dominant": True,
            "must_block_on_fallback_or_preset_labels": True,
            "must_block_on_stale_or_template_conclusions": True,
            "mandatory_eight_site_minimum_per_source": MANDATORY_SENTIMENT_MIN_PER_SOURCE,
            "mandatory_eight_site_in_unified_analysis": True,
            "community_opinion_cannot_replace_strong_facts": True,
            "lianban_tdx_duanxianxia_cross_validation_required": True,
            "explicit_short_term_sentiment_required": True,
            "must_write_delivery_dynamic_conclusion_audit": True,
            "auto_is_fast_health_gate": True,
            "generate_is_report_production": True,
        },
        "missing_instruction_terms": missing_instruction_terms,
        "stale_instruction_hits": stale_hits,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 2


def _is_zero_qualified_report(artifact_dir, text):
    marker = "达到三重证据标准的行业因果主线为0条"
    if marker not in text:
        return False
    artifact_dir = Path(artifact_dir)
    names = (
        "a_share_sentiment_clusters.json",
        "a_share_sentiment_report_sections.json",
        "a_share_sentiment_scores.json",
    )
    payloads = []
    for name in names:
        try:
            payloads.append(json.loads((artifact_dir / name).read_text(encoding="utf-8")))
        except Exception:
            return False
    return all(isinstance(payload, list) and not payload for payload in payloads)


def scan_docx(args):
    try:
        from docx import Document
    except Exception as exc:
        print(f"BLOCKED python-docx unavailable: {exc}")
        return 2
    path = Path(args.path)
    if not path.exists():
        print(f"BLOCKED docx not found: {path}")
        return 2
    text, doc = docx_visible_text(path)
    scan_text = strip_allowed_report_metadata(text)
    artifact_dir = Path(getattr(args, "artifact_dir", "") or path.parent)
    zero_qualified_report = _is_zero_qualified_report(artifact_dir, text)
    missing_labels = (
        []
        if zero_qualified_report
        else [label for label in REQUIRED_LABELS if label not in text]
    )
    missing_headers = (
        []
        if zero_qualified_report
        else [header for header in EVIDENCE_HEADERS if header not in text]
    )
    forbidden = [term for term in FORBIDDEN_TERMS if term in scan_text]
    delivery_noise = [term for term in DELIVERY_NOISE_TERMS if term in scan_text]
    banned_report_phrases = report_banned_phrase_hits(scan_text)
    delivery_noise_patterns = {
        "forum_time": r"\b\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{1,2}",
        "forum_date_dash": r"\b\d{1,2}[-/]\d{1,2}\b",
    }
    for name, pattern in delivery_noise_patterns.items():
        if re.search(pattern, scan_text):
            delivery_noise.append(name)
    if missing_labels or missing_headers or forbidden or delivery_noise or banned_report_phrases:
        print("BLOCKED docx scan failed")
        if missing_labels:
            print("missing_labels=" + ",".join(missing_labels))
        if missing_headers:
            print("missing_evidence_headers=" + ",".join(missing_headers))
        if forbidden:
            print("forbidden_terms=" + ",".join(forbidden))
        if delivery_noise:
            print("delivery_noise=" + ",".join(delivery_noise))
        if banned_report_phrases:
            print("banned_report_phrases=" + ",".join(banned_report_phrases))
        return 2
    delivery_audit = delivery_report_audit(path, artifact_dir=artifact_dir, write=True)
    if not delivery_audit.get("ok"):
        print("BLOCKED delivery dynamic conclusion audit failed")
        for reason in delivery_audit.get("reasons", []):
            print(f"  - {reason}")
        print(f"delivery_audit={artifact_dir / 'a_share_sentiment_delivery_audit.json'}")
        return 2
    size = path.stat().st_size
    print("CLEAN_PASS docx scan")
    print(f"path={path}")
    print(f"size={size}")
    print(f"paragraphs={len(doc.paragraphs)}")
    print(f"tables={len(doc.tables)}")
    return 0


def run_capture(cmd, timeout=240):
    try:
        r = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
        )
        return {
            "ok": r.returncode == 0,
            "exit": r.returncode,
            "cmd": cmd,
            "stdout_tail": r.stdout[-1800:],
            "stderr_tail": r.stderr[-900:],
        }
    except Exception as exc:
        return {"ok": False, "cmd": cmd, "error": f"{type(exc).__name__}: {exc}"}


def auto(_args):
    steps = []
    for name, cmd in [
        ("entry_selftest", [PYTHON_EXE, str(Path(__file__).resolve()), "selftest"]),
        ("entry_doctor", [PYTHON_EXE, str(Path(__file__).resolve()), "doctor"]),
    ]:
        result = run_capture(cmd, timeout=300)
        result["step"] = name
        steps.append(result)
    ok = all(step.get("ok") for step in steps)
    print(json.dumps({
        "skill": ROOT.name,
        "mode": "auto",
        "entry": str(Path(__file__).resolve()),
        "locked_execution": str(LOCKED_EXECUTION),
        "status": "CLEAN_PASS" if ok else "BLOCKED",
        "all_ok": ok,
        "steps": steps,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description="A-share sentiment workflow guard and checklist.")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("selftest")
    sub.add_parser("checklist")
    sub.add_parser("doctor")
    sub.add_parser("auto")
    fsp = sub.add_parser("five-site-profile")
    fsp.add_argument("--capture-dir", default="")
    scan = sub.add_parser("scan-docx")
    scan.add_argument("path")
    scan.add_argument("--artifact-dir", default="")
    gen = sub.add_parser("generate")
    gen.add_argument("--out-dir", default=str(DEFAULT_REPORT_DIR))
    args = parser.parse_args(argv)
    if args.cmd == "selftest":
        return selftest(args)
    if args.cmd == "checklist":
        return checklist(args)
    if args.cmd == "doctor":
        return doctor(args)
    if args.cmd == "auto":
        return auto(args)
    if args.cmd == "five-site-profile":
        return five_site_profile_cmd(args)
    if args.cmd == "scan-docx":
        return scan_docx(args)
    if args.cmd == "generate":
        return generate(args)
    parser.print_help()
    return 0


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
