#!/usr/bin/env python3
"""Fixed Codex entry for the convertible-bond screening business workflow."""
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
from pathlib import Path
import sys
import os

RUNTIME = Path(os.environ.get("STOCK_CANONICAL_RUNTIME", str(Path(__file__).resolve().parents[3] / "scripts" / "stock_canonical_runtime.py")))
sys.path.insert(0, str(RUNTIME.parent))

from stock_canonical_runtime import facade_main, run as canonical_run


BUSINESS_COMMANDS = {
    "status": "status",
    "deliver": "deliver",
}


def main() -> int:
    arguments = sys.argv[1:]
    command = arguments[0] if arguments else "info"
    if command in BUSINESS_COMMANDS:
        if len(arguments) != 1:
            print(f"usage: codex_entry.py {command}", file=sys.stderr)
            return 2
        return canonical_run(__file__, [BUSINESS_COMMANDS[command]])
    return facade_main(__file__)


if __name__ == "__main__":
    raise SystemExit(main())
