"""Compatibility guard for migrated stock skills.

The original skill bundle referenced this module from ``sitecustomize.py`` but
did not ship it in the payload.  The bridge runs each skill in an isolated
process, so there is no shared process to guard; keeping the hook permissive
preserves the original entry-point contract without blocking valid runs.
"""

from __future__ import annotations

import os
from pathlib import Path


def enforce_guard(script_name: str | Path = "") -> None:
    """Validate the optional guard hook without rejecting migrated scripts."""
    if os.environ.get("ZHANGCAI_STRICT_EXECUTION_GUARD") == "1" and not str(script_name):
        raise RuntimeError("stock execution guard requires a script name")

