from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import os
import runpy
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
CODEX_HOME = SCRIPT_PATH.parents[3]
CLI_PATH = SCRIPT_PATH.with_name("lobster_cli.py")


def main() -> None:
    # Task Scheduler inherits the persistent user environment, which points
    # CODEX_HOME at another installation on this machine.  The dashboard must
    # scan the Codex installation that owns this launcher and its stock skills.
    os.environ["CODEX_HOME"] = str(CODEX_HOME)
    if len(sys.argv) == 1:
        sys.argv.extend(["launch", "--no-browser", "--port", "59383"])
    sys.argv[0] = str(CLI_PATH)
    runpy.run_path(str(CLI_PATH), run_name="__main__")


if __name__ == "__main__":
    main()
