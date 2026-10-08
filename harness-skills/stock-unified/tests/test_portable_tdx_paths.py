from __future__ import annotations

import os
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(APP_ROOT / "scripts"))

from tdx_path_config import path_is_within, resolve_data_root, resolve_tdx_root


class PortableTdxPathTests(unittest.TestCase):
    def test_packaged_tdx_root_uses_selected_d_drive_path_with_spaces(self) -> None:
        selected = r"D:\Program Files\Tongdaxin Mock"
        with patch.dict(
            os.environ,
            {
                "ZHANGCAI_PACKAGED": "1",
                "ZHANGCAI_TDX_ROOT": selected,
                "TDX_ROOT": r"C:\stale\tdx",
                "ZHANGCAI_DATA_DIR": r"D:\Zhangcai Data",
            },
            clear=True,
        ):
            self.assertEqual(resolve_tdx_root(), Path(selected).resolve())

    def test_packaged_unconfigured_root_never_falls_back_to_developer_c_drive(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ZHANGCAI_PACKAGED": "1",
                "ZHANGCAI_DATA_DIR": r"D:\Zhangcai Data",
                "ZHANGCAI_DEV_TDX_ROOT": r"C:\new_tdx_mock",
            },
            clear=True,
        ):
            self.assertEqual(
                resolve_tdx_root(),
                Path(r"D:\Zhangcai Data\runtime\__tdx_root_not_configured__").resolve(),
            )

    def test_development_default_and_data_root_remain_cwd_independent(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve_tdx_root(), Path(r"C:\new_tdx_mock").resolve())
        with patch.dict(os.environ, {"ONESTOCK_STOCK_DATA_ROOT": r"D:\Zhangcai Data"}, clear=True):
            self.assertEqual(resolve_data_root(), Path(r"D:\Zhangcai Data").resolve())

    def test_relative_tdx_and_data_paths_anchor_to_app_root_not_cwd(self) -> None:
        app_root = APP_ROOT / "custom-install"
        with patch.dict(
            os.environ,
            {
                "ZHANGCAI_PACKAGED": "1",
                "ZHANGCAI_APP_ROOT": str(app_root),
                "ZHANGCAI_TDX_ROOT": r"..\tdx-client",
                "ONESTOCK_STOCK_DATA_ROOT": "resource-library",
            },
            clear=True,
        ):
            self.assertEqual(resolve_tdx_root(), (app_root / ".." / "tdx-client").resolve())
            self.assertEqual(resolve_data_root(), (app_root / "resource-library").resolve())

    def test_containment_uses_the_selected_tdx_root(self) -> None:
        root = Path(r"D:\Program Files\Tongdaxin Mock")
        self.assertTrue(path_is_within(root / "vipdoc" / "sh" / "lday" / "sh600000.day", root / "vipdoc"))
        self.assertFalse(path_is_within(r"C:\new_tdx_mock\vipdoc\sh\lday\sh600000.day", root / "vipdoc"))

    def test_tdx_hub_paths_follow_selected_d_drive_not_legacy_cwd(self) -> None:
        selected = Path(r"D:\Program Files\Tongdaxin Mock")
        hub_path = APP_ROOT / "harness-skills" / "tdx-local-hub" / "scripts" / "tdx_hub.py"
        with patch.dict(
            os.environ,
            {
                "ZHANGCAI_PACKAGED": "1",
                "ZHANGCAI_APP_ROOT": str(APP_ROOT / "resources" / "app"),
                "ZHANGCAI_DATA_DIR": r"D:\Zhangcai Data\resource-library",
                "ONESTOCK_STOCK_DATA_ROOT": r"D:\Zhangcai Data\resource-library",
                "ZHANGCAI_TDX_ROOT": str(selected),
                "TDX_ROOT": r"C:\stale\tdx",
            },
            clear=True,
        ):
            spec = importlib.util.spec_from_file_location("portable_tdx_hub_test", hub_path)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        self.assertEqual(module.TDX_ROOT, selected)
        self.assertEqual(module.VIPDOC, selected / "vipdoc")
        self.assertEqual(module.TQ_USER_DIR, selected / "PYPlugins" / "user")
        self.assertEqual(
            module.TQ_LOCK_PATH,
            Path(r"D:\Zhangcai Data\resource-library\runtime\skills\tdx-local-hub\tq.lock"),
        )


if __name__ == "__main__":
    unittest.main()
