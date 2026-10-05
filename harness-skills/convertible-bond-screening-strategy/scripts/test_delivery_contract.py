from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import copy
import json
import tempfile
import unittest
from pathlib import Path

from validate_delivery_contract import (
    AUTHORITATIVE_FILENAMES,
    SCORE_CRITERIA,
    SCORE_MODEL_VERSION,
    DeliveryContractError,
    build_delivery_payload,
)


def write_json(path: Path, payload: dict) -> bytes:
    raw = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


class DeliveryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.run_root = Path(self.temp_dir.name) / "run"
        self.run_id = "a" * 32
        self.market_attempt = 1
        self.generation_dir = (
            self.run_root
            / "generations"
            / self.run_id
            / f"attempt-{self.market_attempt}"
        )
        self.paths = self._build_valid_fixture()

    def _criteria(self) -> list[dict]:
        return [
            {
                "id": criterion_id,
                "name_zh": criterion_id,
                "weight": weight,
                "full_score_anchor": criterion_id,
            }
            for criterion_id, weight in SCORE_CRITERIA
        ]

    def _result_rows(self) -> list[dict]:
        rows = []
        for rank in range(1, 11):
            components = {}
            for criterion_id, weight in SCORE_CRITERIA:
                normalized = (11 - rank) / 10.0
                components[criterion_id] = {
                    "weight": weight,
                    "normalized_score": normalized,
                    "earned_score": weight * normalized,
                    "data_status": "AVAILABLE",
                }
            rows.append(
                {
                    "rank": rank,
                    "symbol": f"12{rank:04d}.SZ",
                    "name": f"测试转债{rank}",
                    "underlying_symbol": f"00{rank:04d}.SZ",
                    "underlying_name": f"测试正股{rank}",
                    "score_components": components,
                    "score_total_raw": sum(
                        component["earned_score"] for component in components.values()
                    ),
                    "big_bull_red_preference": rank % 2 == 0,
                    "risk_level": "GREEN",
                    "hard_exclusion_pass": True,
                    "early_redemption_status": "NO_MATCH_AS_OF_CUTOFF",
                }
            )
        return rows

    def _summary_rows(self, result_rows: list[dict]) -> list[dict]:
        return [
            {
                "rank": row["rank"],
                "bond": f'{row["name"]}（{row["symbol"]}）',
                "symbol": row["symbol"],
                "underlying": (
                    f'{row["underlying_name"]}（{row["underlying_symbol"]}）'
                ),
                "underlying_symbol": row["underlying_symbol"],
                "score": round(row["score_total_raw"], 2),
                "component_scores": {
                    criterion_id: round(
                        row["score_components"][criterion_id]["earned_score"], 2
                    )
                    for criterion_id, _weight in SCORE_CRITERIA
                },
                "big_bull_red_preference": row["big_bull_red_preference"],
                "risk_level": row["risk_level"],
            }
            for row in result_rows
        ]

    def _status_rows(self, result_rows: list[dict]) -> list[dict]:
        return [
            {
                "rank": row["rank"],
                "symbol": row["symbol"],
                "name": row["name"],
                "underlying_symbol": row["underlying_symbol"],
                "underlying_name": row["underlying_name"],
                "score": row["score_total_raw"],
                "risk_level": row["risk_level"],
                "big_bull_red_preference": row["big_bull_red_preference"],
                "hard_exclusion_pass": True,
                "early_redemption_status": "NO_MATCH_AS_OF_CUTOFF",
            }
            for row in result_rows
        ]

    def _build_valid_fixture(self) -> dict[str, Path]:
        result_rows = self._result_rows()
        score_model = {
            "version": SCORE_MODEL_VERSION,
            "criteria": self._criteria(),
            "criterion_count": 10,
            "weight_sum": 100.0,
            "tie_break_rule": (
                "score_total_raw DESC; exact ties prefer personal knowledge-base "
                "confirmation quality DESC; then big_bull_red=True; then "
                "convertible-bond symbol ASC"
            ),
            "big_bull_rule": (
                "EMA5>EMA20 is a displayed exact-tie preference only and "
                "contributes zero score"
            ),
        }
        result = {
            "schema": "TDX-CONVERTIBLE-BOND-WEIGHTED-SCAN-V5",
            "status": "PASS",
            "run_id": self.run_id,
            "market_attempt": self.market_attempt,
            "score_model": score_model,
            "personal_kb_confirmation_model": {"automatic_order": False},
            "ranking_top10": result_rows,
        }
        summary = {
            "schema": "CONVERTIBLE-BOND-SCREENING-SUMMARY-3",
            "status": "PASS",
            "run_id": self.run_id,
            "market_attempt": self.market_attempt,
            "score_model": copy.deepcopy(score_model),
            "personal_kb_confirmation_model": {"automatic_order": False},
            "top10": self._summary_rows(result_rows),
        }
        status_rows = self._status_rows(result_rows)
        run_state = {
            "schema": "CONVERTIBLE-BOND-SCREENING-RUN-STATE-1",
            "status": "PASS",
            "run_id": self.run_id,
            "market_attempt": self.market_attempt,
            "automatic_order": False,
        }
        skill_status = {
            "schema": "CONVERTIBLE-BOND-SCREENING-SKILL-STATUS-3",
            "status": "PASS",
            "run_id": self.run_id,
            "market_attempt": self.market_attempt,
            "score_model_version": SCORE_MODEL_VERSION,
            "score_criteria_count": 10,
            "score_weight_sum": 100.0,
            "automatic_order": False,
            "top10": copy.deepcopy(status_rows),
        }
        status_readback = {
            "schema": "CONVERTIBLE-BOND-SCREENING-STATUS-READBACK-3",
            "status": "PASS",
            "run_id": self.run_id,
            "market_attempt": self.market_attempt,
            "automatic_order": False,
            "top10": copy.deepcopy(status_rows),
        }

        result_path = self.generation_dir / "latest_result.json"
        generation_summary_path = self.generation_dir / "latest_summary.json"
        write_json(result_path, result)
        summary_raw = write_json(generation_summary_path, summary)

        paths = {
            "run_state": self.run_root / "run_state.json",
            "status_readback": self.run_root / "status_readback.json",
            "skill_status": self.run_root / "skill_status.json",
            "latest_summary": self.run_root / "latest_summary.json",
        }
        write_json(paths["run_state"], run_state)
        write_json(paths["status_readback"], status_readback)
        write_json(paths["skill_status"], skill_status)
        paths["latest_summary"].write_bytes(summary_raw)
        return paths

    def _load(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def _rewrite(self, path: Path, mutation) -> None:
        payload = self._load(path)
        mutation(payload)
        write_json(path, payload)

    def _rewrite_generation_pair(self, mutation) -> None:
        generation_path = self.generation_dir / "latest_summary.json"
        payload = self._load(generation_path)
        mutation(payload)
        raw = write_json(generation_path, payload)
        self.paths["latest_summary"].write_bytes(raw)

    def assert_rejected(self, action) -> None:
        with self.assertRaises(DeliveryContractError):
            action()

    def test_current_same_generation_contract_passes(self) -> None:
        delivery = build_delivery_payload(self.run_root)
        self.assertEqual(delivery["status"], "PASS")
        self.assertEqual(delivery["run_id"], self.run_id)
        self.assertEqual(delivery["score_model_version"], SCORE_MODEL_VERSION)
        self.assertEqual(delivery["criterion_count"], 10)
        self.assertEqual(delivery["weight_sum"], 100.0)
        self.assertIs(delivery["automatic_order"], False)
        self.assertIs(delivery["manual_override_allowed"], False)
        self.assertIs(delivery["cross_run_mixing_allowed"], False)
        self.assertEqual(len(delivery["top10"]), 10)
        self.assertTrue(
            all(row["run_id"] == self.run_id for row in delivery["top10"])
        )
        self.assertEqual("测试转债1", delivery["top10"][0]["name"])
        self.assertEqual("测试正股1", delivery["top10"][0]["underlying_name"])

    def test_summary_display_names_must_match_verified_result_names(self) -> None:
        self._rewrite_generation_pair(
            lambda payload: payload["top10"][0].update(
                {"bond": "错误名称（120001.SZ）"}
            )
        )
        self.assert_rejected(lambda: build_delivery_payload(self.run_root))

    def test_wrong_model_version_rejected(self) -> None:
        result_path = self.generation_dir / "latest_result.json"
        self._rewrite(
            result_path,
            lambda payload: payload["score_model"].update({"version": "DRIFTED"}),
        )
        self.assert_rejected(lambda: build_delivery_payload(self.run_root))

    def test_criterion_count_id_and_order_drift_rejected(self) -> None:
        result_path = self.generation_dir / "latest_result.json"
        cases = (
            lambda criteria: criteria.pop(),
            lambda criteria: criteria[0].update({"id": "replacement"}),
            lambda criteria: criteria.reverse(),
        )
        for mutation in cases:
            with self.subTest(mutation=mutation):
                fixture = self._load(result_path)
                mutation(fixture["score_model"]["criteria"])
                write_json(result_path, fixture)
                self.assert_rejected(lambda: build_delivery_payload(self.run_root))
                self.paths = self._build_valid_fixture()

    def test_individual_weight_drift_rejected_even_when_sum_is_100(self) -> None:
        result_path = self.generation_dir / "latest_result.json"

        def mutate(payload: dict) -> None:
            payload["score_model"]["criteria"][0]["weight"] += 1
            payload["score_model"]["criteria"][1]["weight"] -= 1
            for row in payload["ranking_top10"]:
                row["score_components"]["c1_price_activity"]["weight"] += 1
                row["score_components"]["c2_remaining_scale"]["weight"] -= 1

        self._rewrite(result_path, mutate)
        self.assert_rejected(lambda: build_delivery_payload(self.run_root))

    def test_weight_sum_drift_rejected(self) -> None:
        result_path = self.generation_dir / "latest_result.json"
        self._rewrite(
            result_path,
            lambda payload: payload["score_model"].update({"weight_sum": 99}),
        )
        self.assert_rejected(lambda: build_delivery_payload(self.run_root))

    def test_big_bull_cannot_enter_scoring_components(self) -> None:
        result_path = self.generation_dir / "latest_result.json"

        def mutate(payload: dict) -> None:
            payload["score_model"]["criteria"][-1]["id"] = "big_bull_red"
            for row in payload["ranking_top10"]:
                component = row["score_components"].pop("c11_turnover5")
                row["score_components"]["big_bull_red"] = component

        self._rewrite(result_path, mutate)
        self.assert_rejected(lambda: build_delivery_payload(self.run_root))

    def test_top10_component_keys_order_and_embedded_weight_drift_rejected(self) -> None:
        result_path = self.generation_dir / "latest_result.json"
        original = self._load(result_path)
        cases = []

        missing = copy.deepcopy(original)
        missing["ranking_top10"][0]["score_components"].pop("c1_price_activity")
        cases.append(missing)

        reordered = copy.deepcopy(original)
        components = reordered["ranking_top10"][0]["score_components"]
        reordered["ranking_top10"][0]["score_components"] = dict(
            reversed(list(components.items()))
        )
        cases.append(reordered)

        weight_changed = copy.deepcopy(original)
        weight_changed["ranking_top10"][0]["score_components"][
            "c1_price_activity"
        ]["weight"] = 7.0
        cases.append(weight_changed)

        for payload in cases:
            with self.subTest(case=list(payload["ranking_top10"][0]["score_components"])):
                write_json(result_path, payload)
                self.assert_rejected(lambda: build_delivery_payload(self.run_root))

    def test_cross_run_or_attempt_mixing_rejected(self) -> None:
        for path_key, field, value in (
            ("run_state", "run_id", "b" * 32),
            ("status_readback", "market_attempt", 2),
            ("skill_status", "run_id", "c" * 32),
        ):
            with self.subTest(path=path_key, field=field):
                self.paths = self._build_valid_fixture()
                self._rewrite(
                    self.paths[path_key],
                    lambda payload, field=field, value=value: payload.update(
                        {field: value}
                    ),
                )
                self.assert_rejected(lambda: build_delivery_payload(self.run_root))

    def test_any_non_pass_authoritative_status_rejected(self) -> None:
        for path_key in AUTHORITATIVE_FILENAMES:
            with self.subTest(path=path_key):
                self.paths = self._build_valid_fixture()
                if path_key == "latest_summary":
                    self._rewrite_generation_pair(
                        lambda payload: payload.update({"status": "FAIL"})
                    )
                else:
                    self._rewrite(
                        self.paths[path_key],
                        lambda payload: payload.update({"status": "FAIL"}),
                    )
                self.assert_rejected(lambda: build_delivery_payload(self.run_root))

    def test_automatic_order_must_be_strict_boolean_false(self) -> None:
        for value in (True, 0, None, "false"):
            with self.subTest(value=value):
                self.paths = self._build_valid_fixture()
                self._rewrite(
                    self.paths["run_state"],
                    lambda payload, value=value: payload.update(
                        {"automatic_order": value}
                    ),
                )
                self.assert_rejected(lambda: build_delivery_payload(self.run_root))

    def test_old_latest_result_and_non_whitelisted_sources_rejected(self) -> None:
        old_result = self.run_root / "latest_result.json"
        write_json(
            old_result,
            {
                "schema": "TDX-CONVERTIBLE-BOND-WEIGHTED-SCAN-V5",
                "status": "PASS",
                "run_id": "d" * 32,
            },
        )
        wrong_paths = dict(self.paths)
        wrong_paths["latest_summary"] = old_result
        self.assert_rejected(
            lambda: build_delivery_payload(
                self.run_root,
                authoritative_paths=wrong_paths,
            )
        )

    def test_published_summary_must_match_current_generation_bytes(self) -> None:
        self._rewrite(
            self.paths["latest_summary"],
            lambda payload: payload["top10"][0].update({"score": 0}),
        )
        self.assert_rejected(lambda: build_delivery_payload(self.run_root))

    def test_top10_name_order_score_and_component_summary_must_match(self) -> None:
        mutations = (
            lambda payload: payload["top10"].reverse(),
            lambda payload: payload["top10"][0].update({"symbol": "128888.SZ"}),
            lambda payload: payload["top10"][0].update({"score": 0}),
            lambda payload: payload["top10"][0]["component_scores"].update(
                {"c1_price_activity": 0}
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.paths = self._build_valid_fixture()
                self._rewrite_generation_pair(mutation)
                self.assert_rejected(lambda: build_delivery_payload(self.run_root))


if __name__ == "__main__":
    unittest.main(verbosity=2)
