from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SELECTOR = load_module(
    "oversold_first_board_selector",
    ROOT / "scripts" / "run_oversold_first_board_smoke.py",
)
ADAPTER = load_module(
    "oversold_first_board_adapter",
    ROOT / "scripts" / "canonical_business_adapter.py",
)


def make_rows(*, oversold: bool = True, prior_limit_up: bool = False) -> list[dict]:
    rows: list[dict] = []
    close = 20.0 if oversold else 10.0
    for index in range(70):
        previous_close = close
        close = round(close - 0.12, 2) if oversold else round(close + 0.01, 2)
        rows.append(
            {
                "date": f"2026{index // 28 + 1:02d}{index % 28 + 1:02d}",
                "open": previous_close,
                "high": round(max(previous_close, close) + 0.05, 2),
                "low": round(min(previous_close, close) - 0.05, 2),
                "close": close,
                "amount": 180_000_000.0,
                "volume": 12_000_000,
            }
        )
    if prior_limit_up:
        index = len(rows) - 8
        previous_close = float(rows[index - 1]["close"])
        limit_close = SELECTOR.limit_price(previous_close, 0.10)
        rows[index].update(
            open=round(previous_close * 1.02, 2),
            high=limit_close,
            low=round(previous_close * 1.01, 2),
            close=limit_close,
        )
    previous_close = float(rows[-1]["close"])
    limit_close = SELECTOR.limit_price(previous_close, 0.10)
    rows.append(
        {
            "date": "20260315",
            "open": round(previous_close * 1.03, 2),
            "high": limit_close,
            "low": round(previous_close * 1.02, 2),
            "close": limit_close,
            "amount": 360_000_000.0,
            "volume": 24_000_000,
        }
    )
    return rows


def write_report(directory: Path, *, symbol: str = "000001.SZ") -> Path:
    source = directory / "candidate.day"
    source.write_bytes(b"local-tdx-oversold-first-board")
    code, market = symbol.split(".")
    candidate = {
        "symbol": symbol,
        "code": code,
        "market": market,
        "name": "平安银行" if symbol == "000001.SZ" else "上证指数",
        "selection_status": "SIGNAL",
        "score": 82,
        "metrics": {
            "date": "20260824",
            "pre_limit_rsi14": 24.5,
            "pre_limit_drawdown_60_pct": -31.2,
            "prior_limit_up_count_20": 0,
        },
        "source": {
            "path": str(source),
            "size": source.stat().st_size,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        },
    }
    report = {
        "schema_version": 1,
        "strategy_id": "oversold-first-board-v1",
        "status": "CLEAN_PASS",
        "selection_status": "SIGNAL",
        "latest_trade_date": "20260824",
        "data_source": {"type": "local_tdx_raw_daily"},
        "universe": {
            "eligible_security_records": 5200,
            "scan_stats": {"latest_trade_date": 5100},
        },
        "selection": {"candidate_count": 1, "candidates": [candidate]},
        "validation": {
            "full_market_scan": True,
            "candidate_count_matches": True,
            "unique_stock_candidates": True,
        },
        "risk_boundary": {
            "decision_scope": "local_tdx_end_of_day_technical_selection",
            "external_event_data": "not_used_in_selection",
            "entry_timing": "not_a_trade_instruction",
            "guaranteed_profit": False,
        },
    }
    path = directory / "oversold-first-board.json"
    path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    return path


class FullMarketOversoldFirstBoardTests(unittest.TestCase):
    def test_index_is_not_a_stock_but_sz_000001_is(self) -> None:
        self.assertFalse(SELECTOR.is_a_share_stock("000001.SH"))
        self.assertTrue(SELECTOR.is_a_share_stock("000001.SZ"))

    def test_detects_oversold_first_board(self) -> None:
        result = SELECTOR.evaluate_candidate(make_rows(), "000001")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertLessEqual(result["metrics"]["pre_limit_rsi14"], 35)
        self.assertLessEqual(result["metrics"]["pre_limit_drawdown_60_pct"], -15)
        self.assertEqual(result["metrics"]["prior_limit_up_count_20"], 0)

    def test_prior_board_or_non_oversold_series_is_rejected(self) -> None:
        self.assertIsNone(SELECTOR.evaluate_candidate(make_rows(prior_limit_up=True), "000001"))
        self.assertIsNone(SELECTOR.evaluate_candidate(make_rows(oversold=False), "000001"))

    def test_payload_count_matches_candidate_list(self) -> None:
        payload = SELECTOR.build_business_payload(
            [],
            latest_trade_date="20260824",
            universe={"eligible_security_records": 5000, "scan_stats": {"latest_trade_date": 4900}},
            data_source={"type": "local_tdx_raw_daily"},
        )

        self.assertEqual(payload["selection_status"], "NO_SIGNAL")
        self.assertEqual(payload["selection"]["candidate_count"], 0)
        self.assertEqual(payload["selection"]["candidates"], [])

    def test_adapter_validates_full_market_report(self) -> None:
        with TemporaryDirectory() as temporary:
            report = write_report(Path(temporary))
            child_stdout = json.dumps({"status": "CLEAN_PASS", "report": str(report)}, ensure_ascii=False)

            result = ADAPTER.derive_validated_selection(child_stdout)

        self.assertEqual(result["strategy_id"], "oversold-first-board-v1")
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["candidates"][0]["symbol"], "000001.SZ")

    def test_adapter_rejects_index_and_old_smoke_structures(self) -> None:
        with TemporaryDirectory() as temporary:
            report = write_report(Path(temporary), symbol="000001.SH")
            stdout = json.dumps({"status": "CLEAN_PASS", "report": str(report)}, ensure_ascii=False)
            with self.assertRaisesRegex(ValueError, "index_candidate"):
                ADAPTER.derive_validated_selection(stdout)

        old_smoke = json.dumps(
            {
                "status": "CLEAN_PASS",
                "selection_status": "NO_CANDIDATES",
                "candidate_count": 1,
                "candidate": None,
            }
        )
        with self.assertRaises(ValueError):
            ADAPTER.derive_validated_selection(old_smoke)


if __name__ == "__main__":
    unittest.main(verbosity=2)
