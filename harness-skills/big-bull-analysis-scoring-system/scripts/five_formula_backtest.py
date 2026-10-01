"""Fail-closed scientific terminal state for the five-formula model."""

from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import five_formula_dataset


SCHEMA = "FIVE_FORMULA_SCIENTIFIC_MODEL_V1"
METHODOLOGY_VERSION = "FIVE_FORMULA_SCIENTIFIC_BACKTEST_V1"
UNAVAILABLE = "FIVE_FORMULA_FORMAL_MODEL_UNAVAILABLE"
TERMINAL_STATES = frozenset(("PREDICTIVE_PASS", "PREDICTIVE_REJECTED", "BLOCKED"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_sha256(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field}_must_be_sha256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field}_must_be_sha256") from exc
    return value.lower()


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    content = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_write_bytes(path, content)


def _positive_oos(validation: Mapping[str, Any]) -> bool:
    try:
        return int(validation.get("oos_row_count", 0)) > 0 and int(
            validation.get("oos_date_count", 0)
        ) > 0
    except (TypeError, ValueError):
        return False


def build_formal_model_payload(
    predictive_status: str,
    candidate_model: Mapping[str, Any] | None,
    predictive_validation: Mapping[str, Any],
    evidence_path: str | Path,
    protocol_sha256: str,
    catalog_sha256: str,
    *,
    methodology_version: str = METHODOLOGY_VERSION,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build exactly one of PASS, REJECTED, or BLOCKED without state promotion."""

    if predictive_status not in TERMINAL_STATES:
        raise ValueError("predictive_status_must_be_exact_terminal_state")
    if not isinstance(predictive_validation, Mapping):
        raise TypeError("predictive_validation_must_be_mapping")
    if not isinstance(methodology_version, str) or not methodology_version:
        raise ValueError("methodology_version_required")
    protocol_hash = _require_sha256(protocol_sha256, "protocol_sha256")
    catalog_hash = _require_sha256(catalog_sha256, "catalog_sha256")
    evidence = Path(evidence_path).resolve()
    if not evidence.is_file():
        raise ValueError("evidence_file_missing")

    validation = dict(predictive_validation)
    if predictive_status == "PREDICTIVE_PASS":
        if not isinstance(candidate_model, Mapping) or not candidate_model:
            raise ValueError("PREDICTIVE_PASS_requires_candidate_model")
        if validation.get("status") not in {"PASS", "PREDICTIVE_PASS"}:
            raise ValueError("PREDICTIVE_PASS_requires_validation_pass")
        if not _positive_oos(validation):
            raise ValueError("PREDICTIVE_PASS_requires_nonempty_OOS")
        model: dict[str, Any] | None = dict(candidate_model)
    else:
        if candidate_model is not None:
            raise ValueError(f"{predictive_status} must not carry model")
        if predictive_status == "PREDICTIVE_REJECTED" and validation.get("status") not in {
            "REJECTED",
            "PREDICTIVE_REJECTED",
        }:
            raise ValueError("PREDICTIVE_REJECTED_requires_rejected_validation")
        if predictive_status == "BLOCKED" and validation.get("status") not in {"NOT_RUN", "BLOCKED"}:
            raise ValueError("BLOCKED_requires_not_run_validation")
        model = None

    return {
        "schema": SCHEMA,
        "predictive_status": predictive_status,
        "methodology_version": methodology_version,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "protocol_sha256": protocol_hash,
        "catalog_sha256": catalog_hash,
        "evidence_path": str(evidence),
        "evidence_sha256": _sha256(evidence),
        "predictive_validation": validation,
        "model": model,
    }


def _validate_formal_payload(
    payload: object,
    *,
    expected_catalog_sha256: str | None = None,
    expected_methodology_version: str = METHODOLOGY_VERSION,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise ValueError("formal_model_schema_invalid")
    if payload.get("methodology_version") != expected_methodology_version:
        raise ValueError("formal_model_methodology_mismatch")
    _require_sha256(payload.get("protocol_sha256"), "protocol_sha256")
    catalog_hash = _require_sha256(payload.get("catalog_sha256"), "catalog_sha256")
    if expected_catalog_sha256 is not None and catalog_hash != _require_sha256(
        expected_catalog_sha256, "expected_catalog_sha256"
    ):
        raise ValueError("formal_model_catalog_mismatch")
    status = payload.get("predictive_status")
    if status not in TERMINAL_STATES:
        raise ValueError("formal_model_terminal_state_invalid")
    validation = payload.get("predictive_validation")
    if not isinstance(validation, dict):
        raise ValueError("formal_model_validation_invalid")
    model = payload.get("model")
    if status == "PREDICTIVE_PASS":
        if not isinstance(model, dict) or not model:
            raise ValueError("formal_model_pass_candidate_missing")
        if validation.get("status") not in {"PASS", "PREDICTIVE_PASS"} or not _positive_oos(validation):
            raise ValueError("formal_model_pass_oos_invalid")
    elif model is not None:
        raise ValueError("formal_model_nonpass_model_forbidden")
    elif status == "PREDICTIVE_REJECTED" and validation.get("status") not in {
        "REJECTED",
        "PREDICTIVE_REJECTED",
    }:
        raise ValueError("formal_model_rejected_validation_invalid")
    elif status == "BLOCKED" and validation.get("status") not in {"NOT_RUN", "BLOCKED"}:
        raise ValueError("formal_model_blocked_validation_invalid")

    evidence_path = payload.get("evidence_path")
    expected_evidence_hash = _require_sha256(payload.get("evidence_sha256"), "evidence_sha256")
    if not isinstance(evidence_path, str) or not Path(evidence_path).is_file():
        raise ValueError("formal_model_evidence_missing")
    if _sha256(Path(evidence_path)) != expected_evidence_hash:
        raise ValueError("formal_model_evidence_hash_mismatch")
    return payload


def load_formal_model(
    path: str | Path,
    *,
    expected_catalog_sha256: str | None = None,
    expected_methodology_version: str = METHODOLOGY_VERSION,
) -> dict[str, Any]:
    """Load only a complete, internally consistent terminal-state document."""

    source = Path(path).resolve()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("formal_model_unreadable") from exc
    return _validate_formal_payload(
        payload,
        expected_catalog_sha256=expected_catalog_sha256,
        expected_methodology_version=expected_methodology_version,
    )


def install_formal_model(
    source_path: str | Path,
    target_path: str | Path,
    *,
    expected_catalog_sha256: str | None = None,
    expected_methodology_version: str = METHODOLOGY_VERSION,
) -> dict[str, Any]:
    """Validate, copy, read back, and atomically replace the installed state."""

    source = Path(source_path).resolve()
    target = Path(target_path).resolve()
    load_formal_model(
        source,
        expected_catalog_sha256=expected_catalog_sha256,
        expected_methodology_version=expected_methodology_version,
    )
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False
        ) as handle:
            handle.write(source_bytes)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        if _sha256(temporary) != source_hash:
            raise ValueError("formal_model_temporary_hash_mismatch")
        load_formal_model(
            temporary,
            expected_catalog_sha256=expected_catalog_sha256,
            expected_methodology_version=expected_methodology_version,
        )
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    if _sha256(target) != source_hash:
        raise ValueError("formal_model_installed_hash_mismatch")
    return {
        "status": "INSTALLED",
        "source": str(source),
        "source_sha256": source_hash,
        "target": str(target),
        "target_sha256": source_hash,
    }


def assert_scoring_authorized(model_or_path: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    """Return the candidate model only when PASS and bound evidence remain valid."""

    try:
        if isinstance(model_or_path, Mapping):
            payload = _validate_formal_payload(dict(model_or_path))
        else:
            payload = load_formal_model(model_or_path)
        if payload.get("predictive_status") != "PREDICTIVE_PASS":
            raise ValueError("not_predictive_pass")
        model = payload.get("model")
        if not isinstance(model, dict) or not model:
            raise ValueError("model_missing")
        return model
    except Exception as exc:
        raise RuntimeError(UNAVAILABLE) from exc


def _blocked_report(evidence: Mapping[str, Any]) -> str:
    audit = evidence["capability_audit"]
    lines = [
        "# Five-formula scientific backtest",
        "",
        "- Predictive status: BLOCKED",
        "- Predictive validation: NOT_RUN",
        "- Formal model: null",
        "",
        "## Capability errors",
        "",
    ]
    lines.extend(f"- {item}" for item in audit.get("errors", []))
    lines.extend(("", "## Sources", ""))
    for name, path in audit.get("source_paths", {}).items():
        lines.append(f"- {name}: {path}; sha256={audit.get('source_sha256', {}).get(name)}")
    lines.append("")
    return "\n".join(lines)


def run_capability_backtest(
    stock_master_path: str | Path,
    st_history_path: str | Path | None,
    suspension_history_path: str | Path | None,
    delisted_master_path: str | Path | None,
    output_dir: str | Path,
    protocol_sha256: str,
    catalog_sha256: str,
) -> dict[str, Any]:
    """Audit inputs and materialize a truthful BLOCKED state when history is incomplete."""

    paths = [stock_master_path, st_history_path, suspension_history_path, delisted_master_path]
    normalized = [None if value is None else Path(value) for value in paths]
    audit = five_formula_dataset.audit_point_in_time_capabilities(
        stock_master_path=normalized[0],
        st_history_path=normalized[1],
        suspension_history_path=normalized[2],
        delisted_master_path=normalized[3],
    )
    if audit.get("status") == "PASS":
        raise RuntimeError("FIVE_FORMULA_PREDICTIVE_BACKTEST_NOT_IMPLEMENTED")

    destination = Path(output_dir).resolve()
    evidence_path = destination / "five_formula_capability_evidence.json"
    report_path = destination / "five_formula_capability_report.md"
    formal_path = destination / "five_formula_scientific_model.json"
    evidence = {
        "schema": "FIVE_FORMULA_CAPABILITY_BACKTEST_EVIDENCE_V1",
        "predictive_status": "BLOCKED",
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "protocol_sha256": _require_sha256(protocol_sha256, "protocol_sha256"),
        "catalog_sha256": _require_sha256(catalog_sha256, "catalog_sha256"),
        "capability_audit": audit,
        "predictive_validation": {
            "status": "NOT_RUN",
            "oos_row_count": 0,
            "oos_date_count": 0,
            "reason": "point_in_time_data_capability_blocked",
        },
        "model": None,
    }
    _atomic_write_json(evidence_path, evidence)
    _atomic_write_bytes(report_path, _blocked_report(evidence).encode("utf-8"))
    formal = build_formal_model_payload(
        "BLOCKED",
        None,
        evidence["predictive_validation"],
        evidence_path,
        protocol_sha256,
        catalog_sha256,
        generated_at=evidence["generated_at"],
    )
    _atomic_write_json(formal_path, formal)
    return {
        "predictive_status": "BLOCKED",
        "predictive_validation": dict(evidence["predictive_validation"]),
        "model": None,
        "capability_audit": audit,
        "evidence_path": str(evidence_path),
        "evidence_sha256": _sha256(evidence_path),
        "report_path": str(report_path),
        "report_sha256": _sha256(report_path),
        "formal_model_path": str(formal_path),
        "formal_model_sha256": _sha256(formal_path),
    }


__all__ = [
    "METHODOLOGY_VERSION",
    "assert_scoring_authorized",
    "build_formal_model_payload",
    "install_formal_model",
    "load_formal_model",
    "run_capability_backtest",
]
