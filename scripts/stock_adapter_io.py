#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write_bytes(path: Path, data: bytes) -> dict[str, Any]:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=target.parent,
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if temporary_path.read_bytes() != data:
            raise RuntimeError("adapter_atomic_temporary_readback_mismatch")
        os.replace(temporary_path, target)
        temporary_path = None
        readback = target.read_bytes()
        if readback != data:
            raise RuntimeError("adapter_atomic_final_readback_mismatch")
        return {
            "path": str(target),
            "size": len(readback),
            "sha256": sha256_bytes(readback),
        }
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def atomic_write_text(path: Path, text: str) -> dict[str, Any]:
    return atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: Path, payload: Any) -> dict[str, Any]:
    return atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )


def _atomic_path_write_text(
    path: Path,
    data: str,
    encoding: str | None = None,
    errors: str | None = None,
    newline: str | None = None,
) -> int:
    if not isinstance(data, str):
        raise TypeError("data must be str, not " + type(data).__name__)
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            errors=errors,
            newline=newline,
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=target.parent,
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            written = handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary_bytes = temporary_path.read_bytes()
        os.replace(temporary_path, target)
        temporary_path = None
        if target.read_bytes() != temporary_bytes:
            raise RuntimeError("adapter_path_write_final_readback_mismatch")
        return written
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def enable_atomic_path_writes() -> None:
    current = Path.write_text
    if getattr(current, "_stock_atomic_write", False):
        return
    setattr(_atomic_path_write_text, "_stock_atomic_write", True)
    Path.write_text = _atomic_path_write_text
