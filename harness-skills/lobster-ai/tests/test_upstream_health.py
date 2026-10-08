from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import socket
import sys
import unittest
import urllib.error
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("lobster_cli_under_test", SCRIPT_DIR / "lobster_cli.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class UpstreamHealthTests(unittest.TestCase):
    def test_http_502_is_upstream_5xx(self):
        error = urllib.error.HTTPError("https://example.invalid", 502, "Bad Gateway", {}, None)
        self.assertEqual(MODULE.classify_upstream_error(error), "UPSTREAM_5XX")

    def test_timeout_is_classified_without_hard_failure(self):
        probe = MODULE.probe_upstream_health(
            "market_breadth",
            lambda: (_ for _ in ()).throw(socket.timeout("timed out")),
        )
        self.assertEqual(probe["status"], "TIMEOUT")
        self.assertIn("socket.timeout", probe["error"])

    def test_degraded_upstream_does_not_pollute_local_checks(self):
        local_checks = [{"name": "service_start", "status": "PASS", "detail": "ok"}]
        probes = [
            {"name": "limit_up", "status": "UPSTREAM_5XX", "error": "HTTPError: 502"},
            {"name": "market_breadth", "status": "TIMEOUT", "error": "socket.timeout: timed out"},
        ]
        result = MODULE.build_selftest_result(
            started="2026-08-01T00:00:00+08:00",
            checks=local_checks,
            upstream_probes=probes,
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["upstream_health"]["status"], "HEALTH_DEGRADED")
        self.assertEqual(result["checks"], local_checks)


if __name__ == "__main__":
    unittest.main()
