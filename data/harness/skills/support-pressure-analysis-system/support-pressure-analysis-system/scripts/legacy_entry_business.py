#!/usr/bin/env python3
"""Compatibility alias; entry_support_resistance.py is the only business executor."""
from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("entry_support_resistance.py")), run_name="__main__")
