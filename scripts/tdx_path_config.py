from __future__ import annotations

import os
from pathlib import Path


DEVELOPMENT_TDX_ROOT = r"C:\new_tdx_mock"
_UNCONFIGURED_NAME = "__tdx_root_not_configured__"


def _fallback_app_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_against(value: str | Path, base: str | Path) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = Path(base).expanduser() / candidate
    return candidate.resolve(strict=False)


def resolve_app_root(default: str | Path | None = None) -> Path:
    value = os.environ.get("ZHANGCAI_APP_ROOT") or default or _fallback_app_root()
    return _resolve_against(value, _fallback_app_root())


def resolve_tdx_root(default: str | Path | None = None) -> Path:
    """Resolve TDX from the desktop bridge environment, never from cwd.

    Packaged runs intentionally receive a non-existent sentinel path when the
    user has not selected a TDX installation. That sentinel must not fall back
    to a developer machine's C: drive.
    """
    for name in ("ZHANGCAI_TDX_ROOT", "TDX_ROOT", "BAIMAO_TDX_ROOT"):
        value = str(os.environ.get(name) or "").strip().strip('"')
        if value:
            return _resolve_against(value, resolve_app_root())

    if str(os.environ.get("ZHANGCAI_PACKAGED") or "") == "1":
        data_root = Path(
            os.environ.get("ONESTOCK_STOCK_DATA_ROOT")
            or os.environ.get("ZHANGCAI_DATA_DIR")
            or Path(__file__).resolve().parents[1] / "app-data"
        ).expanduser()
        return (data_root / "runtime" / _UNCONFIGURED_NAME).resolve(strict=False)

    value = str(os.environ.get("ZHANGCAI_DEV_TDX_ROOT") or "").strip().strip('"')
    if value:
        return _resolve_against(value, resolve_app_root())
    return _resolve_against(default or DEVELOPMENT_TDX_ROOT, resolve_app_root())


def resolve_data_root(default: str | Path | None = None) -> Path:
    """Resolve the writable app data root for reports/cache files."""
    value = (
        os.environ.get("ONESTOCK_STOCK_DATA_ROOT")
        or os.environ.get("ZHANGCAI_DATA_DIR")
        or default
        or _fallback_app_root() / "app-data"
    )
    return _resolve_against(value, resolve_app_root())


def resolve_path_from(value: str | Path, base: str | Path) -> Path:
    """Resolve a configured path against an explicit base, not process cwd."""
    return _resolve_against(value, base)


def path_is_within(candidate: str | Path, root: str | Path) -> bool:
    """Whether candidate resolves beneath root, using platform path rules."""
    try:
        Path(candidate).resolve(strict=False).relative_to(
            Path(root).resolve(strict=False)
        )
        return True
    except (OSError, ValueError):
        return False
