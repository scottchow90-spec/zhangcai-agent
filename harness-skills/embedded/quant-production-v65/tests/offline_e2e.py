from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import workbuddy_entry

raise SystemExit(0 if workbuddy_entry.offline_e2e() else 1)
