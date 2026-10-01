from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3] / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stock_execution_guard import enforce_guard  # noqa: E402

enforce_guard(Path(sys.argv[0]).name)
