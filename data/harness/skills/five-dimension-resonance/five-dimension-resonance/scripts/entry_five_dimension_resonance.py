# -*- coding: utf-8 -*-
"""five-dimension-resonance compatibility entry.

The active skill execution path is the Tongdaxin custom board 飞龙在天 runner.
This entry stays only as a stable legacy command surface and delegates to the
accepted executable runner so old command invocations cannot run the retired
market-wide API path.
"""
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import sys
from pathlib import Path


def main() -> int:
    import argparse
    # 2026-06-22 加固: 支持 --help / --dry-run 快速响应 (转发给 runner, runner 已支持)
    p = argparse.ArgumentParser(description="五维共振 entry (转发到 run_feilong_block_resonance.py)")
    p.add_argument("--dry-run", action="store_true", help="转发 dry-run 到 runner")
    ns, rest = p.parse_known_args()

    script_dir = Path(__file__).resolve().parent
    runner_path = script_dir / "run_feilong_block_resonance.py"
    if not runner_path.exists() or runner_path.stat().st_size <= 0:
        raise FileNotFoundError(f"missing executable runner: {runner_path}")
    sys.path.insert(0, str(script_dir))

    # --help 由 argparse 自动处理; --dry-run 用 subprocess 转发给 runner (runner.main 不接 argv)
    if ns.dry_run:
        import subprocess
        r = subprocess.run([sys.executable, str(runner_path), "--dry-run"], capture_output=False)
        return r.returncode

    import run_feilong_block_resonance
    return int(run_feilong_block_resonance.main() or 0)


if __name__ == "__main__":
    raise SystemExit(main())
