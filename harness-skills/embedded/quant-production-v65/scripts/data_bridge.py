from __future__ import annotations

import json
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from public_data import DataError

SCHEMA = "a_share_quant_workbuddy_data_bundle_v1"
BRIDGE_EXIT_CODE = 4


def _parse_dt(v: Any) -> Optional[datetime]:
    if not v:
        return None
    s = str(v).strip().replace("Z", "+00:00")
    try:
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        return d
    except Exception:
        return None


def _provider_id(z: Any) -> str:
    if isinstance(z, dict):
        return str(z.get("provider") or z.get("source") or z.get("id") or "").strip().lower()
    return str(z or "").strip().lower()


class DataBundle:
    """WorkBuddy 外部取数桥。

    接受一个 JSON 文件，或 ZIP 中的 bundle.json。它只保存真实外部数据，绝不生成、插值或猜测缺失字段。
    """

    def __init__(self, path: str):
        self.path = Path(path)
        if not self.path.exists():
            raise DataError("数据桥文件不存在:" + str(self.path))
        self.data = self._load(self.path)
        if not isinstance(self.data, dict):
            raise DataError("数据桥根对象必须是JSON对象")
        if self.data.get("schema") != SCHEMA:
            raise DataError(f"数据桥schema不匹配:{self.data.get('schema')} != {SCHEMA}")

    @staticmethod
    def _load(path: Path) -> Dict[str, Any]:
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path, "r") as z:
                names = z.namelist()
                target = "bundle.json" if "bundle.json" in names else next((x for x in names if x.endswith("/bundle.json")), None)
                if not target:
                    raise DataError("数据桥ZIP缺少bundle.json")
                return json.loads(z.read(target).decode("utf-8"))
        return json.loads(path.read_text("utf-8"))

    @property
    def mode(self) -> str:
        return str(self.data.get("mode") or "")

    @property
    def trade_date(self) -> str:
        return str(self.data.get("trade_date") or "")

    @property
    def decision_asof(self) -> Optional[str]:
        v = self.data.get("decision_asof")
        return str(v) if v else None

    @property
    def provenance(self) -> Dict[str, Any]:
        return dict(self.data.get("provenance") or {})

    def validate(self, expected_mode: Optional[str] = None, expected_date: Optional[str] = None) -> List[str]:
        e: List[str] = []
        if self.mode not in {"after-market", "realtime"}:
            e.append("mode必须为after-market或realtime")
        if expected_mode and self.mode != expected_mode:
            e.append(f"mode不一致:{self.mode} != {expected_mode}")
        try:
            datetime.strptime(self.trade_date, "%Y-%m-%d")
        except Exception:
            e.append("trade_date格式错误")
        if expected_date and self.trade_date != expected_date:
            e.append(f"trade_date不一致:{self.trade_date} != {expected_date}")

        now = datetime.now(ZoneInfo("Asia/Shanghai"))
        generated = _parse_dt(self.data.get("generated_at"))
        if not generated:
            e.append("generated_at缺失/格式错误")
        elif generated.astimezone(ZoneInfo("Asia/Shanghai")) > now.replace(microsecond=0):
            e.append("generated_at晚于当前时间")

        prov = self.provenance
        p = _provider_id(prov.get("primary"))
        s = _provider_id(prov.get("secondary"))
        if not p:
            e.append("primary来源标识缺失")
        if self.mode == "after-market" and not s:
            e.append("secondary来源标识缺失")
        if p and s and p == s:
            e.append("主行情源与第二行情源必须独立，禁止同源冒充二源")
        for k in ("primary", "secondary"):
            x = prov.get(k)
            if isinstance(x, dict) and str(x.get("kind") or "").lower() in {"synthetic", "generated", "mock", "fixture"}:
                e.append(f"{k}来源为模拟/生成数据，生产模式禁止")

        universe = self.data.get("universe")
        if not isinstance(universe, list) or not universe:
            e.append("universe缺失")
        histories = self.data.get("histories")
        if not isinstance(histories, dict) or not histories:
            e.append("histories缺失")
        indices = self.data.get("indices")
        if not isinstance(indices, dict) or not indices.get("1.000001") or not indices.get("0.399001"):
            e.append("上证/深证指数历史缺失")
        if self.mode == "after-market" and not isinstance(self.data.get("secondary"), dict):
            e.append("secondary收盘核验数据缺失")
        return e

    def assert_valid(self, expected_mode: Optional[str] = None, expected_date: Optional[str] = None) -> None:
        e = self.validate(expected_mode, expected_date)
        if e:
            raise DataError("数据桥校验失败:" + "；".join(e))

    def universe(self) -> List[Dict[str, Any]]:
        return list(self.data.get("universe") or [])

    def kline(self, code: str, end_date: str, count_days: int = 260, market_id: Optional[int] = None) -> List[Dict[str, Any]]:
        rows = list((self.data.get("histories") or {}).get(str(code)) or [])
        rows = [x for x in rows if str(x.get("date") or "") <= str(end_date)]
        return rows[-int(count_days):]

    def index_kline(self, secid: str, end_date: str, count_days: int = 80) -> List[Dict[str, Any]]:
        rows = list((self.data.get("indices") or {}).get(str(secid)) or [])
        rows = [x for x in rows if str(x.get("date") or "") <= str(end_date)]
        return rows[-int(count_days):]

    def industry_name(self, code: str) -> Optional[str]:
        z = (self.data.get("industries") or {}).get("stock_to_name") or {}
        v = z.get(str(code))
        return str(v).strip() if v not in (None, "", "-") else None

    def industry_boards(self) -> Dict[str, str]:
        return dict(((self.data.get("industries") or {}).get("boards") or {}))

    def board_kline(self, board_code: str, end_date: str, count_days: int = 30) -> List[Dict[str, Any]]:
        rows = list((((self.data.get("industries") or {}).get("board_bars") or {}).get(str(board_code)) or []))
        rows = [x for x in rows if str(x.get("date") or "") <= str(end_date)]
        return rows[-int(count_days):]

    def board_constituents(self, board_code: str, page_size: int = 600) -> List[Dict[str, Any]]:
        return list((((self.data.get("industries") or {}).get("constituents") or {}).get(str(board_code)) or []))[:int(page_size)]

    def news_search(self, keyword: str, count: int = 30) -> List[Dict[str, Any]]:
        news = ((self.data.get("industries") or {}).get("news") or {})
        return list(news.get(str(keyword)) or [])[:int(count)]

    def news_scan_complete(self, keyword: str) -> bool:
        z = ((self.data.get("industries") or {}).get("news_scan_complete") or {})
        return bool(z.get(str(keyword)))

    def secondary_rows(self, code: str, count: int = 260) -> List[Dict[str, Any]]:
        z = (self.data.get("secondary") or {}).get(str(code))
        if isinstance(z, dict):
            return [z]
        return list(z or [])[-int(count):]

    def intraday_trends(self, code: str, market_id: Optional[int] = None) -> List[Dict[str, Any]]:
        return list(((self.data.get("intraday_trends") or {}).get(str(code)) or []))


def bridge_request_payload(mode: str, requested_date: Optional[str], reason: str, output_bundle: str) -> Dict[str, Any]:
    return {
        "schema": "a_share_quant_workbuddy_bridge_request_v1",
        "status": "DATA_BRIDGE_REQUIRED",
        "mode": mode,
        "requested_date": requested_date,
        "reason": reason,
        "required_bundle_schema": SCHEMA,
        "output_bundle": output_bundle,
        "mandatory_rules": [
            "只允许真实外部数据，禁止synthetic/generated/mock/fixture",
            "盘后主行情源与第二行情源必须独立",
            "所有行情与事件必须按decision_asof截断，不得引入未来数据",
            "股票池/历史K线/指数/行业/消息/二源任一关键数据缺失必须如实保留，不得填0或猜测",
            "完成取数后必须自动用--data-bundle重跑execute，DATA_BRIDGE_REQUIRED不是最终结果",
        ],
        "datasets": {
            "universe": "全A当前/目标时点快照：code,name,market_id,last,open,high,low,pre_close,pct,change,volume,amount,turnover,volume_ratio",
            "histories": "每只股票最多260根未复权日K；原生核心模型最低120根，250根以上启用增强结构：date,open,close,high,low,volume,amount,pct_change,change,turnover",
            "indices": "1.000001与0.399001提供足够计算市场状态的未复权日K",
            "industries.stock_to_name": "候选股票行业映射",
            "industries.boards": "行业名->行业板块代码",
            "industries.board_bars": "进入精算行业至少60根行业日K",
            "industries.constituents": "进入精算行业成分快照及涨跌/成交数据",
            "industries.news": "进入精算行业的可追溯消息/政策/产业事件",
            "industries.news_scan_complete": "每个进入精算行业必须显式true/false，失败不能伪装为无消息",
            "secondary": "盘后最终候选的独立第二来源收盘价",
            "intraday_trends": "仅realtime：潜在候选1分钟趋势，用于数分钟前稳定价",
        },
        "provenance": {
            "primary": {"provider": "必须填写真实提供方", "kind": "public_api|workbuddy_connector|browser|licensed_data", "retrieved_at": "ISO8601"},
            "secondary": {"provider": "必须与primary不同", "kind": "public_api|workbuddy_connector|browser|licensed_data", "retrieved_at": "ISO8601"},
        },
        "resume": f"python scripts/workbuddy_entry.py execute --mode {mode} --data-bundle \"{output_bundle}\"" + (f" --date {requested_date}" if requested_date else ""),
    }


def write_bridge_request(path: str, mode: str, requested_date: Optional[str], reason: str, output_bundle: Optional[str] = None) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    bundle = output_bundle or str(p.with_name("workbuddy_data_bundle.zip"))
    p.write_text(json.dumps(bridge_request_payload(mode, requested_date, reason, bundle), ensure_ascii=False, indent=2), "utf-8")
    return p


def resolve_bundle_path(cli_path: Optional[str]) -> Optional[str]:
    return cli_path or os.environ.get("WORKBUDDY_A_SHARE_DATA_BUNDLE") or None
