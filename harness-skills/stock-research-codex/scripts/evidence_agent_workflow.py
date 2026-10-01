from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

ROLES = (
    "fundamentals",
    "market_and_technical",
    "catalyst",
    "risk",
    "valuation",
)

EVIDENCE_REQUIRED_FIELDS = (
    "evidence_id",
    "claim",
    "source",
    "source_url",
    "observed_at",
    "verification_status",
    "source_rank",
)

ROLE_REQUIRED_FIELDS = (
    "role",
    "conclusion",
    "evidence_ids",
    "confidence",
    "risks",
    "unverified_items",
)

VERIFIED_STATUSES = {"official_confirmed", "multi_source_confirmed"}
OPPOSING_STANCES = {
    ("supports", "opposes"),
    ("opposes", "supports"),
    ("positive", "negative"),
    ("negative", "positive"),
    ("bullish", "bearish"),
    ("bearish", "bullish"),
}
FORBIDDEN_EXECUTION_FIELDS = {
    "order",
    "orders",
    "broker_action",
    "execute_trade",
    "place_order",
    "trade_execution",
    "auto_trade",
    "automated_trade",
}


class EvidenceProtocolError(ValueError):
    pass


def build_evidence_set(
    evidence: Iterable[Mapping[str, Any]],
    *,
    evidence_set_id: str | None = None,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for index, raw_item in enumerate(evidence):
        if not isinstance(raw_item, Mapping):
            raise EvidenceProtocolError(f"evidence[{index}] must be a mapping")
        item = dict(raw_item)
        missing = _missing_fields(item, EVIDENCE_REQUIRED_FIELDS)
        if missing:
            raise EvidenceProtocolError(
                f"evidence[{index}] missing required fields:{','.join(missing)}"
            )
        evidence_id = str(item["evidence_id"]).strip()
        if not evidence_id:
            raise EvidenceProtocolError(f"evidence[{index}] has an empty evidence_id")
        if evidence_id in seen_ids:
            raise EvidenceProtocolError(f"duplicate evidence_id:{evidence_id}")
        item["evidence_id"] = evidence_id
        seen_ids.add(evidence_id)
        items.append(item)

    set_id = evidence_set_id or _stable_evidence_set_id(items)
    if not str(set_id).strip():
        raise EvidenceProtocolError("evidence_set_id must not be empty")
    return {
        "evidence_set_id": str(set_id).strip(),
        "evidence": items,
    }


def validate_role_output(
    output: Mapping[str, Any],
    evidence_set: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(output, Mapping):
        raise EvidenceProtocolError("role output must be a mapping")
    _reject_execution_fields(output)
    normalized = dict(output)
    missing = _missing_fields(normalized, ROLE_REQUIRED_FIELDS)
    if missing:
        raise EvidenceProtocolError(
            f"role output missing required fields:{','.join(missing)}"
        )

    role = str(normalized["role"]).strip()
    if role not in ROLES:
        raise EvidenceProtocolError(f"unsupported role:{role}")
    conclusion = str(normalized["conclusion"]).strip()
    if not conclusion:
        raise EvidenceProtocolError("role conclusion must not be empty")

    set_id, evidence_by_id = _evidence_index(evidence_set)
    supplied_set_id = normalized.get("evidence_set_id")
    if supplied_set_id is not None and str(supplied_set_id) != set_id:
        raise EvidenceProtocolError(
            f"evidence_set_id mismatch:{supplied_set_id}!={set_id}"
        )

    evidence_ids = _string_list(normalized["evidence_ids"], "evidence_ids")
    unknown = [evidence_id for evidence_id in evidence_ids if evidence_id not in evidence_by_id]
    if unknown:
        raise EvidenceProtocolError(f"unknown evidence_ids:{','.join(unknown)}")

    risks = _string_list(normalized["risks"], "risks")
    unverified_items = _string_list(
        normalized["unverified_items"], "unverified_items"
    )
    confidence = _confidence(normalized["confidence"])
    status = "accepted"
    if not evidence_ids:
        status = "degraded"
        confidence = min(confidence, 0.2)
        unverified_items = _unique(
            [*unverified_items, "conclusion_has_no_supporting_evidence"]
        )

    return {
        "role": role,
        "conclusion": conclusion,
        "evidence_ids": evidence_ids,
        "confidence": confidence,
        "risks": risks,
        "unverified_items": unverified_items,
        "evidence_set_id": set_id,
        "status": status,
    }


def arbitrate(
    role_outputs: Iterable[Mapping[str, Any]],
    evidence_set: Mapping[str, Any],
) -> dict[str, Any]:
    set_id, evidence_by_id = _evidence_index(evidence_set)
    validated = [
        validate_role_output(output, evidence_set) for output in role_outputs
    ]

    referenced_ids = _unique(
        evidence_id
        for output in validated
        for evidence_id in output["evidence_ids"]
    )
    supporting_ids = [
        evidence_id
        for evidence_id in referenced_ids
        if evidence_by_id[evidence_id]["verification_status"] in VERIFIED_STATUSES
    ]
    unverified_evidence_ids = [
        evidence_id for evidence_id in referenced_ids if evidence_id not in supporting_ids
    ]

    supported_conclusions = []
    for output in validated:
        role_verified_ids = [
            evidence_id
            for evidence_id in output["evidence_ids"]
            if evidence_id in supporting_ids
        ]
        if role_verified_ids:
            supported_conclusions.append(f"{output['role']}: {output['conclusion']}")

    synthesis = (
        " | ".join(supported_conclusions)
        if supported_conclusions
        else "No conclusion has enough verified evidence for synthesis."
    )
    conflicts = _find_conflicts(referenced_ids, evidence_by_id)
    risks = _unique(
        risk for output in validated for risk in output["risks"]
    )
    unverified_items = _unique(
        [
            *unverified_evidence_ids,
            *(
                item
                for output in validated
                for item in output["unverified_items"]
            ),
        ]
    )

    average_confidence = (
        sum(output["confidence"] for output in validated) / len(validated)
        if validated
        else 0.0
    )
    evidence_coverage = (
        len(supporting_ids) / len(referenced_ids) if referenced_ids else 0.0
    )
    unverified_penalty = max(0.5, 1.0 - 0.1 * len(unverified_items))
    conflict_penalty = 0.85 if conflicts else 1.0
    confidence = round(
        max(
            0.0,
            min(
                1.0,
                average_confidence
                * evidence_coverage
                * unverified_penalty
                * conflict_penalty,
            ),
        ),
        4,
    )

    decision_criteria = [
        "Treat only verified supporting evidence as factual.",
        "Resolve listed conflicts and unverified items before increasing conviction.",
        "Reassess the synthesis when new dated evidence changes an assumption or risk.",
    ]
    result = {
        "evidence_set_id": set_id,
        "synthesis": synthesis,
        "supporting_evidence_ids": supporting_ids,
        "conflicts": conflicts,
        "confidence": confidence,
        "risks": risks,
        "unverified_items": unverified_items,
        "decision_criteria": decision_criteria,
    }
    _reject_execution_fields(result)
    return result


def _evidence_index(
    evidence_set: Mapping[str, Any],
) -> tuple[str, dict[str, dict[str, Any]]]:
    if not isinstance(evidence_set, Mapping):
        raise EvidenceProtocolError("evidence_set must be a mapping")
    set_id = str(evidence_set.get("evidence_set_id", "")).strip()
    evidence = evidence_set.get("evidence")
    if not set_id:
        raise EvidenceProtocolError("evidence_set_id is missing")
    if not isinstance(evidence, list):
        raise EvidenceProtocolError("evidence_set.evidence must be a list")
    index = {}
    for item in evidence:
        if not isinstance(item, Mapping) or "evidence_id" not in item:
            raise EvidenceProtocolError("evidence_set contains an invalid item")
        evidence_id = str(item["evidence_id"])
        index[evidence_id] = dict(item)
    return set_id, index


def _find_conflicts(
    evidence_ids: list[str],
    evidence_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    for left_index, left_id in enumerate(evidence_ids):
        left = evidence_by_id[left_id]
        for right_id in evidence_ids[left_index + 1 :]:
            right = evidence_by_id[right_id]
            explicit = (
                right_id in _as_string_set(left.get("contradicts"))
                or left_id in _as_string_set(right.get("contradicts"))
            )
            same_topic = (
                left.get("topic")
                and left.get("topic") == right.get("topic")
            )
            opposing = (
                str(left.get("stance", "")).lower(),
                str(right.get("stance", "")).lower(),
            ) in OPPOSING_STANCES
            if explicit or (same_topic and opposing):
                conflicts.append(
                    {
                        "evidence_ids": [left_id, right_id],
                        "topic": left.get("topic") or right.get("topic"),
                        "reason": "explicit_contradiction"
                        if explicit
                        else "opposing_stances_on_same_topic",
                    }
                )
    return conflicts


def _reject_execution_fields(value: Any, path: str = "root") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized_key = str(key).strip().lower()
            if normalized_key in FORBIDDEN_EXECUTION_FIELDS:
                raise EvidenceProtocolError(
                    f"forbidden trade execution field:{path}.{normalized_key}"
                )
            _reject_execution_fields(child, f"{path}.{normalized_key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_execution_fields(child, f"{path}[{index}]")


def _missing_fields(
    value: Mapping[str, Any], required_fields: tuple[str, ...]
) -> list[str]:
    return [
        field
        for field in required_fields
        if field not in value or value[field] is None
    ]


def _string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, (list, tuple)):
        raise EvidenceProtocolError(f"{field_name} must be a list")
    return _unique(str(item).strip() for item in value if str(item).strip())


def _confidence(value: Any) -> float:
    if isinstance(value, bool):
        raise EvidenceProtocolError("confidence must be a number from 0 to 1")
    try:
        confidence = float(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceProtocolError("confidence must be a number from 0 to 1") from exc
    if confidence < 0.0 or confidence > 1.0:
        raise EvidenceProtocolError("confidence must be between 0 and 1")
    return confidence


def _unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _as_string_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value}
    if isinstance(value, (list, tuple, set)):
        return {str(item) for item in value}
    return {str(value)}


def _stable_evidence_set_id(items: list[dict[str, Any]]) -> str:
    canonical = json.dumps(
        items,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"evidence-{digest[:16]}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only evidence-agent validation and arbitration."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("smoke", help="Run a deterministic offline protocol smoke.")

    arbitrate_parser = subparsers.add_parser(
        "arbitrate", help="Arbitrate role outputs from local JSON files."
    )
    arbitrate_parser.add_argument("--evidence-file", required=True)
    arbitrate_parser.add_argument("--roles-file", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "smoke":
            evidence_set, role_outputs = _smoke_fixture()
            mode = "evidence-agent-smoke"
        else:
            evidence_payload = _read_json(Path(args.evidence_file))
            roles_payload = _read_json(Path(args.roles_file))
            if isinstance(evidence_payload, Mapping):
                evidence_set = build_evidence_set(
                    evidence_payload.get("evidence", []),
                    evidence_set_id=evidence_payload.get("evidence_set_id"),
                )
            elif isinstance(evidence_payload, list):
                evidence_set = build_evidence_set(evidence_payload)
            else:
                raise EvidenceProtocolError(
                    "evidence file must contain a list or evidence-set object"
                )
            if not isinstance(roles_payload, list):
                raise EvidenceProtocolError("roles file must contain a list")
            role_outputs = roles_payload
            mode = "evidence-agent-arbitrate"

        result = arbitrate(role_outputs, evidence_set)
        payload = {
            "status": "available",
            "mode": mode,
            "result": result,
        }
        _reject_execution_fields(payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except (EvidenceProtocolError, OSError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "mode": f"evidence-agent-{args.command}",
                    "error": f"{type(exc).__name__}:{exc}",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2


def _read_json(path: Path) -> Any:
    return json.loads(path.resolve().read_text(encoding="utf-8-sig"))


def _smoke_fixture() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    evidence_set = build_evidence_set(
        [
            {
                "evidence_id": "E1",
                "claim": "The issuer fixture reports positive revenue growth.",
                "source": "Offline issuer fixture",
                "source_url": "https://example.invalid/issuer-fixture",
                "observed_at": "2000-01-01T00:00:00Z",
                "verification_status": "official_confirmed",
                "source_rank": "S",
                "topic": "growth",
                "stance": "supports",
            },
            {
                "evidence_id": "E2",
                "claim": "The commentary fixture questions growth durability.",
                "source": "Offline commentary fixture",
                "source_url": "https://example.invalid/commentary-fixture",
                "observed_at": "2000-01-01T00:00:00Z",
                "verification_status": "single_source",
                "source_rank": "B",
                "topic": "growth",
                "stance": "opposes",
            },
        ],
        evidence_set_id="SMOKE-SET",
    )
    role_outputs = [
        _smoke_role("fundamentals", ["E1"], 0.8),
        _smoke_role("market_and_technical", ["E1"], 0.7),
        _smoke_role("catalyst", ["E2"], 0.6),
        _smoke_role("risk", ["E1", "E2"], 0.75),
        _smoke_role("valuation", ["E1"], 0.7),
    ]
    return evidence_set, role_outputs


def _smoke_role(
    role: str, evidence_ids: list[str], confidence: float
) -> dict[str, Any]:
    return {
        "role": role,
        "conclusion": f"Offline {role} protocol fixture.",
        "evidence_ids": evidence_ids,
        "confidence": confidence,
        "risks": ["offline_fixture_only"],
        "unverified_items": [],
        "evidence_set_id": "SMOKE-SET",
    }


if __name__ == "__main__":
    raise SystemExit(main())
