#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)
import subprocess, sys
from pathlib import Path
if __name__ == "__main__":
    if sys.argv[1:2] == ["evidence-agent"]:
        from evidence_agent_workflow import main as evidence_agent_main

        raise SystemExit(evidence_agent_main(sys.argv[2:]))
    raise SystemExit(subprocess.run([sys.executable, str(Path.home()/'.codex'/'scripts'/'stock_audit_business.py'), '--skill', 'stock-research-codex', *sys.argv[1:]]).returncode)
