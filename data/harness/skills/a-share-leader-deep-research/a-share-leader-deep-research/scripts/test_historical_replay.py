from __future__ import annotations

import unittest
from pathlib import Path

from legacy_codex_entry import (
    _fact_view,
    _sha256_json,
    recompute_authorized_payload,
    synthetic_fixture,
)


class HistoricalReplayTests(unittest.TestCase):
    def test_recompute_changes_only_dynamic_logic_surface(self):
        payload = synthetic_fixture()
        concept = payload["concept_summary"][0]
        for row in concept["position_top"]:
            row.clear()
            row.update(
                {
                    "rank": 1,
                    "stock_code": "600001",
                    "reason": "属于共同机制，仅表示时序共振。",
                    "evidence_ids": ["E1", "E2"],
                }
            )
        before = _sha256_json(_fact_view(payload))

        replayed = recompute_authorized_payload(
            payload,
            Path("authorized.receipt.json"),
        )

        self.assertEqual(before, _sha256_json(_fact_view(replayed)))
        position = replayed["concept_summary"][0]["position_top"][0]
        self.assertTrue(position["rank_driver"])
        self.assertTrue(position["relative_comparison"])
        self.assertTrue(position["weakness"])
        self.assertTrue(position["invalidation"])
        self.assertNotIn("仅表示时序共振", position["reason"])
        provenance = replayed["replay_provenance"]
        self.assertEqual(
            provenance["fact_surface_sha256_before"],
            provenance["fact_surface_sha256_after"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
