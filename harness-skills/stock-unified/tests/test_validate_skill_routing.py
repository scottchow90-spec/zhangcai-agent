from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_skill_routing.py"
CATALOG = ROOT / "references" / "stock_skill_ids.json"
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "stock_unified_validate_skill_routing_test",
    VALIDATOR,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ValidateSkillRoutingTests(unittest.TestCase):
    def test_compat_home_is_c_junction_to_authoritative_f_home(self) -> None:
        expected = Path(os.environ["USERPROFILE"]) / ".codex"
        self.assertEqual(MODULE.COMPAT_HOME, expected)
        self.assertTrue(MODULE.is_reparse_point(MODULE.COMPAT_HOME))
        self.assertTrue(
            MODULE.same_physical_home(MODULE.COMPAT_HOME, MODULE.CANONICAL_HOME)
        )

    def test_app_server_executable_tracks_current_desktop_runtime(self) -> None:
        with (MODULE.CANONICAL_HOME / "config.toml").open("rb") as config_file:
            config = tomllib.load(config_file)
        configured = Path(
            config["mcp_servers"]["node_repl"]["env"]["CODEX_CLI_PATH"]
        )
        mirrored = (
            MODULE.DESKTOP_RUNTIME_BIN
            / configured.parent.name
            / configured.name
        )
        expected = mirrored if mirrored.is_file() else configured
        self.assertEqual(MODULE.APP_SERVER_EXE, expected)
        self.assertTrue(MODULE.APP_SERVER_EXE.is_file())

    def test_missing_home_variables_use_verified_junction_fallback(self) -> None:
        result = MODULE.validate_home_identity(
            canonical_home=MODULE.CANONICAL_HOME,
            compat_home=MODULE.COMPAT_HOME,
            process_home=None,
            user_home=None,
        )

        self.assertEqual(result["errors"], [], result)
        self.assertTrue(result["checks"]["verified_compat_fallback"])
        self.assertEqual(
            result["checks"]["process_home_source"],
            "canonical_fallback",
        )
        self.assertEqual(
            result["checks"]["user_home_source"],
            "compatibility_junction_fallback",
        )

    def test_current_agents_semantically_declares_canonical_stock_routing(
        self,
    ) -> None:
        errors = MODULE.validate_agents_stock_routing(
            MODULE.CANONICAL_HOME / "AGENTS.md"
        )
        self.assertEqual(errors, [])

    def test_agents_routing_accepts_current_semantic_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            agents = Path(temporary) / "AGENTS.md"
            agents.write_text(
                "\n".join(
                    (*MODULE.AGENTS_STOCK_ROUTING_MARKERS, "禁止旧技能、相近技能、组件入口、备份目录或第二套路由器抢占")
                ),
                encoding="utf-8",
            )
            errors = MODULE.validate_agents_stock_routing(agents)

        self.assertEqual(errors, [])

    def test_authority_topology_ignores_test_scratch_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "Home"
            canonical_files = (
                home
                / "skills"
                / "stock-unified"
                / "references"
                / "stock_skill_ids.json",
                home
                / "skills"
                / "stock-unified"
                / "references"
                / "stock_execution_contracts.json",
                home / "scripts" / "stock_canonical_runtime.py",
            )
            for path in canonical_files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")

            for scratch_name in ("temp", "tmp"):
                scratch = home / scratch_name / "pytest-fixture"
                for path in canonical_files:
                    relative = path.relative_to(home)
                    duplicate = scratch / relative
                    duplicate.parent.mkdir(parents=True, exist_ok=True)
                    duplicate.write_text("{}\n", encoding="utf-8")

            payload = MODULE.validate_stock_authority_topology(home)

        self.assertEqual(payload["errors"], [], payload)
        self.assertEqual(
            payload["active_catalogs"],
            [str(canonical_files[0])],
        )
        self.assertEqual(
            payload["active_contracts"],
            [str(canonical_files[1])],
        )
        self.assertEqual(
            payload["active_runtimes"],
            [str(canonical_files[2])],
        )

    def test_live_validator_passes_current_authoritative_machine(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        payload = json.loads(completed.stdout)

        self.assertEqual(completed.returncode, 0, payload)
        self.assertEqual(payload["status"], "PASS", payload)
        self.assertEqual(payload["errors"], [], payload)

    def test_unified_skill_docs_do_not_duplicate_catalog_size(self) -> None:
        paths = (ROOT / "SKILL.md", ROOT / "references" / "workflow.md")
        violations = [
            str(path)
            for path in paths
            if "50" in path.read_text(encoding="utf-8-sig")
        ]
        self.assertEqual(violations, [])

    def test_manifest_size_is_derived_from_canonical_catalog(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8-sig"))
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        payload = json.loads(completed.stdout)

        self.assertEqual(payload["checks"]["stock_skill_count"], len(catalog["skills"]))
        self.assertFalse(
            any(
                error.startswith("stock skill manifest contains")
                for error in payload["errors"]
            ),
            payload["errors"],
        )

    def test_every_specialized_skill_disables_implicit_invocation(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8-sig"))
        skills_root = ROOT.parent
        violations: list[str] = []

        for skill_id in catalog["skills"]:
            metadata = skills_root / skill_id / "agents" / "openai.yaml"
            policy = MODULE.implicit_policy(metadata.read_text(encoding="utf-8-sig"))
            expected = skill_id == MODULE.DEFAULT_STOCK_SKILL
            if policy is not expected:
                violations.append(
                    f"{skill_id}: expected allow_implicit_invocation={expected}, got {policy}"
                )

        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
