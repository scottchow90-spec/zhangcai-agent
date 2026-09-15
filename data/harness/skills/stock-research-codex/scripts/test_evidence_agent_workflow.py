from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import contextlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path

from evidence_agent_workflow import (
    EvidenceProtocolError,
    arbitrate,
    build_evidence_set,
    main,
    validate_role_output,
)


def evidence_items():
    return [
        {
            "evidence_id": "E1",
            "claim": "Revenue growth accelerated.",
            "source": "Issuer filing",
            "source_url": "https://example.test/filing",
            "observed_at": "2026-08-01T09:00:00Z",
            "verification_status": "official_confirmed",
            "source_rank": "S",
            "topic": "growth",
            "stance": "supports",
        },
        {
            "evidence_id": "E2",
            "claim": "Management guidance remains uncertain.",
            "source": "Earnings call",
            "source_url": "https://example.test/call",
            "observed_at": "2026-08-01T09:05:00Z",
            "verification_status": "single_source",
            "source_rank": "A",
            "topic": "growth",
            "stance": "opposes",
        },
    ]


def role_output(role: str, evidence_ids=None, confidence: float = 0.8):
    return {
        "role": role,
        "conclusion": f"{role} conclusion",
        "evidence_ids": list(evidence_ids if evidence_ids is not None else ["E1"]),
        "confidence": confidence,
        "risks": ["assumption risk"],
        "unverified_items": [],
    }


class EvidenceAgentWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.evidence_set = build_evidence_set(evidence_items(), evidence_set_id="SET-1")

    def test_all_roles_share_the_same_evidence_set_identifier(self) -> None:
        outputs = [
            validate_role_output(role_output("fundamentals"), self.evidence_set),
            validate_role_output(role_output("risk"), self.evidence_set),
        ]
        self.assertEqual({item["evidence_set_id"] for item in outputs}, {"SET-1"})

    def test_unknown_evidence_id_is_rejected(self) -> None:
        with self.assertRaises(EvidenceProtocolError):
            validate_role_output(role_output("valuation", ["E404"]), self.evidence_set)

    def test_missing_required_role_field_is_rejected(self) -> None:
        incomplete = role_output("catalyst")
        del incomplete["risks"]
        with self.assertRaises(EvidenceProtocolError):
            validate_role_output(incomplete, self.evidence_set)

    def test_unsupported_role_is_rejected(self) -> None:
        with self.assertRaises(EvidenceProtocolError):
            validate_role_output(role_output("trader"), self.evidence_set)

    def test_no_evidence_conclusion_is_degraded(self) -> None:
        output = validate_role_output(role_output("market_and_technical", []), self.evidence_set)
        self.assertEqual(output["status"], "degraded")
        self.assertLessEqual(output["confidence"], 0.2)
        self.assertIn("conclusion_has_no_supporting_evidence", output["unverified_items"])

    def test_unverified_evidence_does_not_become_arbitrated_fact(self) -> None:
        result = arbitrate(
            [role_output("fundamentals", ["E1"]), role_output("catalyst", ["E2"])],
            self.evidence_set,
        )
        self.assertEqual(result["supporting_evidence_ids"], ["E1"])
        self.assertIn("E2", result["unverified_items"])

    def test_conflicting_evidence_is_reported(self) -> None:
        result = arbitrate(
            [role_output("fundamentals", ["E1"]), role_output("risk", ["E2"])],
            self.evidence_set,
        )
        self.assertTrue(result["conflicts"])
        self.assertEqual(result["conflicts"][0]["evidence_ids"], ["E1", "E2"])

    def test_confidence_is_constrained_by_coverage_and_unverified_items(self) -> None:
        result = arbitrate(
            [
                role_output("fundamentals", ["E1"], confidence=0.95),
                role_output("valuation", ["E2"], confidence=0.95),
            ],
            self.evidence_set,
        )
        self.assertLess(result["confidence"], 0.95)
        self.assertGreaterEqual(result["confidence"], 0.0)

    def test_trade_execution_fields_are_rejected_and_never_emitted(self) -> None:
        unsafe = role_output("risk")
        unsafe["orders"] = [{"side": "BUY"}]
        with self.assertRaises(EvidenceProtocolError):
            validate_role_output(unsafe, self.evidence_set)

        result = arbitrate([role_output("risk")], self.evidence_set)
        forbidden = {"orders", "broker_action", "execute_trade", "place_order", "auto_trade"}
        self.assertFalse(forbidden.intersection(result))
        self.assertEqual(
            set(result),
            {
                "evidence_set_id",
                "synthesis",
                "supporting_evidence_ids",
                "conflicts",
                "confidence",
                "risks",
                "unverified_items",
                "decision_criteria",
            },
        )

    def test_cli_smoke_emits_verified_research_without_execution_fields(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            returncode = main(["smoke"])

        payload = json.loads(output.getvalue())
        serialized = json.dumps(payload, sort_keys=True)
        self.assertEqual(returncode, 0)
        self.assertEqual(payload["status"], "available")
        self.assertTrue(payload["result"]["supporting_evidence_ids"])
        for forbidden in (
            '"orders"',
            '"broker_action"',
            '"execute_trade"',
            '"place_order"',
            '"auto_trade"',
        ):
            self.assertNotIn(forbidden, serialized)

    def test_fixed_entry_dispatches_evidence_agent_smoke(self) -> None:
        entry = Path(__file__).with_name("codex_entry.py")
        completed = subprocess.run(
            [sys.executable, str(entry), "run", "--", "evidence-agent", "smoke"],
            cwd=str(entry.parents[1]),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "available")
        self.assertEqual(payload["mode"], "evidence-agent-smoke")
        self.assertTrue(payload["result"]["supporting_evidence_ids"])


if __name__ == "__main__":
    unittest.main()
