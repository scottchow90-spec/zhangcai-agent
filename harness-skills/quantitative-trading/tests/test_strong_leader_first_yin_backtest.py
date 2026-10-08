from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import unittest
from pathlib import Path


BACKTEST_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_strong_leader_first_yin_backtest.py"
SCANNER_PATH = Path(r"D:\C盘转移\日志\codex\skills\dragon-pullback\scripts\run_strong_leader_first_yin.py")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BACKTEST = load("leader_first_yin_backtest", BACKTEST_PATH)
SCANNER = load("leader_first_yin_scanner", SCANNER_PATH)


def row(day: int, open_price: float, high: float, low: float, close: float, volume: int = 1_000_000):
    return {
        "date": f"202601{day:02d}",
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "amount": close * volume,
        "volume": volume,
    }


class BacktestTests(unittest.TestCase):
    def test_costs_reduce_return(self):
        gross = 11.0 / 10.0 - 1.0
        net = BACKTEST.net_return(10.0, 11.0, 0.0003, 0.0005, 0.0005)
        self.assertLess(net, gross)
        self.assertGreater(net, 0.09)

    def test_one_price_limit_up_is_unavailable(self):
        previous = row(1, 10.0, 10.0, 10.0, 10.0)
        current = row(2, 11.0, 11.0, 11.0, 11.0)
        self.assertTrue(BACKTEST.one_price_limit_up(SCANNER, previous, current, "002001"))

    def test_next_session_entry_prevents_same_bar_lookahead(self):
        rows = [row(index + 1, 10.0, 10.2, 9.8, 10.0) for index in range(15)]
        rows[11] = row(12, 10.0, 10.2, 9.8, 10.1)
        outcomes, reason = BACKTEST.calculate_trade_outcomes(
            SCANNER,
            rows,
            10,
            "002001",
            [1, 3],
            0.0003,
            0.0005,
            0.0005,
            3,
            {},
        )
        self.assertIsNone(reason)
        self.assertEqual(outcomes["fixed_horizons"]["1"]["entry_date"], "20260112")
        self.assertGreater(outcomes["fixed_horizons"]["1"]["entry_date"], rows[10]["date"])

    def test_large_non_board_move_is_anomaly(self):
        rows = [row(1, 10.0, 10.0, 10.0, 10.0), row(2, 7.0, 7.0, 7.0, 7.0)]
        self.assertTrue(BACKTEST.corporate_action_anomaly(SCANNER, rows, 0, 1, "002001"))


if __name__ == "__main__":
    unittest.main()
